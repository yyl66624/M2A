"""Phase V: L1 extended to multi-channel and soft (t-norm) conjunction, L2 extended to serial
gates, and an exact fixed-point account of the residual L3 learner bias.

Nothing here edits Phase III/IV code: the base learner arm is p3_mechanisms.train_cue_agent called
with its own arguments, and the substrate CDFs/quantiles are imported from p4_mechanisms.
"""
from __future__ import annotations

from collections import defaultdict
from math import prod

import numpy as np

from m2a_mechanisms import COST
from p3_mechanisms import cue_sensitivity, key3, train_cue_agent
from p4_mechanisms import cdf, predicted_threshold, quantile

ALPHA = 0.05
GAMMA = 0.9
QS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


# ------------------------------------------------------------------ V2 / V3: drive gap and window
def tnorm(name: str, xs) -> float:
    xs = [float(x) for x in xs]
    n = len(xs)
    if name == "product":
        return float(prod(xs))
    if name == "lukasiewicz":
        return max(0.0, sum(xs) - (n - 1))
    if name == "godel":
        return min(xs)
    raise ValueError(name)


def channels(n: int, pattern: str, s: float):
    """The silent-side input configuration; the firing side is always all ones."""
    if pattern == "hard":                      # at most one channel driven
        return [1.0] + [0.0] * (n - 1)
    if pattern == "one_weak":                  # n-1 channels full, one degraded to s
        return [s] + [1.0] * (n - 1)
    if pattern == "all_weak":                  # every channel degraded to s
        return [s] * n
    raise ValueError(pattern)


def gap_for(name: str, n: int, pattern: str, s: float, chain_polarity: float = 1.0) -> float:
    """Delta = drive(fire) - drive(silent), including a serial-gate attenuation factor."""
    lo = tnorm(name, channels(n, pattern, s))
    hi = tnorm(name, [1.0] * n)
    return (hi - lo) * abs(chain_polarity)


def window_exists(kind: str, beta: float, drive_lo: float, drive_hi: float,
                  alpha: float = ALPHA, grid=4001) -> bool:
    if drive_hi - drive_lo <= 0.0:
        return False
    thetas = np.linspace(drive_lo - 0.5, drive_hi + 0.5, grid)
    silent = cdf(beta * (drive_lo - thetas), kind)
    fire = cdf(beta * (drive_hi - thetas), kind)
    return bool(np.any((silent <= alpha) & (fire >= 1.0 - alpha)))


def critical_beta(kind: str, drive_lo: float, drive_hi: float, alpha: float = ALPHA,
                  lo=0.02, hi=400.0, tol=1e-3) -> float:
    if drive_hi - drive_lo <= 0.0:
        return float("inf")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if window_exists(kind, mid, drive_lo, drive_hi, alpha):
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return float(hi)


def predicted_critical(kind: str, gap: float, alpha: float = ALPHA) -> float:
    """The threshold law:  beta * gap >= q_{1-alpha}(F) - q_alpha(F)."""
    if gap <= 0.0:
        return float("inf")
    return predicted_threshold(kind, alpha) / gap


def window_bounds(kind: str, beta: float, drive_lo: float, drive_hi: float, alpha: float = ALPHA):
    """The two boundary thresholds of the window at this beta."""
    return (drive_hi - quantile(1.0 - alpha, kind) / beta,
            drive_lo - quantile(alpha, kind) / beta)


def chain_polarity(openness) -> float:
    return float(prod(2.0 * float(o) - 1.0 for o in openness))


def chain_curve(kind: str, openness, xs, beta=6.0, theta=0.5):
    xs = np.asarray(xs, dtype=float)
    return cdf(beta * (xs * chain_polarity(openness) - theta), kind)


# ------------------------------------------------------------------ V1: exact behaviour-operator DP
def enumerate_draws(q: float):
    """The CueBandit generative law as a finite weighted list of (prob, v, mask, cue).

    P5-A2: the mask is drawn as randint(0,2,size=2) and, if all-zero, ONE index is forced to 1.
    That is NOT uniform over the three non-zero masks: P([1,0]) = P([0,1]) = 3/8, P([1,1]) = 1/4.
    Consequently P(B available | max=0.9) = (1/4)/(1/4+3/8) = 2/5, not the 1/2 used by the
    Phase III readout law and by the Phase IV "independent" Bayes estimator.
    """
    out = []
    for v, p_v in ((np.array([0.9, 0.5]), 0.8), (np.array([0.05, 0.1]), 0.2)):
        for mask, p_m in (((1, 0), 3.0 / 8.0), ((0, 1), 3.0 / 8.0), ((1, 1), 1.0 / 4.0)):
            b = mask[1]
            for cue, p_c in ((b, q), (1 - b, 1.0 - q)):
                if p_c > 0.0:
                    out.append((p_v * p_m * p_c, v, np.array(mask), cue))
    return out


def key5(v, mask, cue, step):
    """Same readout as p3_mechanisms.key3 (kept as a separate name so the DP stays readable)."""
    return key3(v, mask, int(cue), int(step))


def _greedy(avail, Q, s):
    return max(avail, key=lambda a: Q.get((s, a), 0.0))


def _policy(avail, Q, s, first: str, eps: float):
    if first == "uniform":
        return {a: 1.0 / len(avail) for a in avail}
    g = _greedy(avail, Q, s)
    return {a: (eps / len(avail) + (1.0 - eps) if a == g else eps / len(avail)) for a in avail}


def dp_sensitivity(q: float, first="uniform", bootstrap="max", eps=0.02, gamma=GAMMA,
                   iters=6000, tol=1e-13) -> float:
    """Fixed point of the EXACT visit-weighted update operator of the sampled pipeline.

    Q(s,a) under Robbins-Monro averaging converges to E[target | (s,a) visited], and the visit
    weights are behaviour-policy weights, not state-conditional weights. That distinction is what
    this function exists to measure. States the behaviour never updates stay at 0.0, mirroring the
    sampler (the step-3 bootstrap state is never written).
    """
    draws = enumerate_draws(q)
    Q: dict = {}
    for _ in range(iters):
        W = defaultdict(float)
        T = defaultdict(float)
        for p, v, mask, cue in draws:
            s1 = key5(v, mask, cue, 1)
            avail1 = [0] + [i + 1 for i in range(2) if mask[i]]
            for a, pa in _policy(avail1, Q, s1, first, eps).items():
                if pa <= 0.0:
                    continue
                if a == 0:
                    w = p * pa
                    W[(s1, a)] += w
                    continue
                idx = a - 1
                r = float(v[idx]) - COST
                rem = mask.copy()
                rem[idx] = 0
                nxt = [0] + [i + 1 for i in range(2) if rem[i]]
                s2 = key5(v, rem, cue, 2)
                if bootstrap == "max":
                    boot = max(Q.get((s2, aa), 0.0) for aa in nxt)
                else:
                    pol2 = _policy(nxt, Q, s2, "eps_greedy", eps)
                    boot = sum(pp * Q.get((s2, aa), 0.0) for aa, pp in pol2.items())
                target = r + gamma * boot
                w = p * pa
                W[(s1, a)] += w
                T[(s1, a)] += w * target
                if len(nxt) <= 1:
                    continue                      # the sampler breaks here
                for a2, pa2 in _policy(nxt, Q, s2, "eps_greedy", eps).items():
                    if pa2 <= 0.0:
                        continue
                    if a2 == 0:
                        t2 = 0.0
                    else:
                        j = a2 - 1
                        rr = float(v[j]) - COST
                        rem2 = rem.copy()
                        rem2[j] = 0
                        nxt2 = [0] + [i + 1 for i in range(2) if rem2[i]]
                        s3 = key5(v, rem2, cue, 3)
                        t2 = rr + gamma * max(Q.get((s3, aa), 0.0) for aa in nxt2)
                    w2 = w * pa2
                    W[(s2, a2)] += w2
                    T[(s2, a2)] += w2 * t2
        if not W:
            break
        new = {k: T[k] / W[k] for k in W}
        eta = 0.25
        nxt_Q = {k: (1.0 - eta) * Q.get(k, 0.0) + eta * new[k] for k in new}
        delta = max(abs(nxt_Q[k] - Q.get(k, 0.0)) for k in nxt_Q)
        Q = nxt_Q
        if delta < tol:
            break
    probe = np.array([0.9, 0.5])
    full = np.array([1, 1])
    s0 = key5(probe, full, 0, 1)
    s1 = key5(probe, full, 1, 1)
    return float(abs(Q.get((s0, 1), 0.0) - Q.get((s1, 1), 0.0))), Q


def dp_sensitivity_only(q: float, **kw) -> float:
    return dp_sensitivity(q, **kw)[0]


def law(q: float, gamma=GAMMA, v_b=0.5, c=COST) -> float:
    return gamma * (v_b - c) * (2.0 * q - 1.0)


def law_prior(q: float, prior=0.4, gamma=GAMMA, v_b=0.5, c=COST) -> float:
    """P5-A3: the same readout with an explicit conditioned prior on B-availability.

    prior = 1/2 reproduces p3_mechanisms.predicted_cue_sensitivity (the Phase III law);
    prior = 2/5 is what CueBandit's mask draw actually implies. Descriptive only.
    """
    if q == 1.0:
        return gamma * (v_b - c)
    p1 = prior * q / (prior * q + (1.0 - prior) * (1.0 - q))
    p0 = prior * (1.0 - q) / (prior * (1.0 - q) + (1.0 - prior) * q)
    return gamma * (v_b - c) * (p1 - p0)


ARMS = {
    # arm: (trainer source, steps, kwargs)  -- base/long/noexplore reuse p3_mechanisms unchanged
    "base": ("p3", 100000, {}),
    "long": ("p3", 400000, {}),
    "noexplore": ("p3", 100000, {"eps_start": 0.0, "eps_end": 0.0}),
    "greedy_first": ("p5", 100000, {"first": "greedy"}),
    "sarsa": ("p5", 100000, {"bootstrap": "expectation"}),
}
DP_SPEC = {
    "base": dict(first="uniform", bootstrap="max", eps=0.02),
    "long": dict(first="uniform", bootstrap="max", eps=0.02),
    "noexplore": dict(first="uniform", bootstrap="max", eps=0.0),
    "greedy_first": dict(first="greedy", bootstrap="max", eps=0.02),
    "sarsa": dict(first="uniform", bootstrap="expectation", eps=0.02),
}


def train_arm(q: float, steps: int, seed: int, first="uniform", bootstrap="max",
              eps_start=0.3, eps_end=0.02) -> dict:
    """The two arms p3_mechanisms cannot express: a greedy FIRST action, and an expectation
    bootstrap. The RNG call sequence differs from p3 by construction (registered in §1.2)."""
    rng = np.random.RandomState(seed)
    v_hi = np.array([0.9, 0.5])
    v_lo = np.array([0.05, 0.1])
    Q: dict = {}
    N: dict = {}

    def qv(s, a):
        return Q.setdefault((s, a), 0.0)

    def update(s, a, target):
        N[(s, a)] = N.get((s, a), 0) + 1
        step_size = 1.0 / (1.0 + N[(s, a)])
        Q[(s, a)] = Q.get((s, a), 0.0) + step_size * (target - Q.get((s, a), 0.0))

    for t in range(steps):
        eps = eps_start + (eps_end - eps_start) * t / max(steps - 1, 1)
        v = v_hi if rng.rand() < 0.8 else v_lo
        mask = rng.randint(0, 2, size=2)
        if mask.sum() == 0:
            mask[rng.randint(2)] = 1
        cue = int(mask[1] if rng.rand() < q else 1 - mask[1])
        remaining = mask.copy()
        for step in (1, 2):
            s = key5(v, remaining, cue, step)
            avail = [0] + [i + 1 for i in range(2) if remaining[i]]
            if step == 1 and first == "uniform":
                a = avail[rng.randint(len(avail))]
            elif rng.rand() < eps:
                a = avail[rng.randint(len(avail))]
            else:
                a = max(avail, key=lambda x: qv(s, x))
            if a == 0:
                update(s, a, 0.0)
                break
            idx = a - 1
            r = float(v[idx]) - COST
            remaining = remaining.copy()
            remaining[idx] = 0
            nxt = [0] + [i + 1 for i in range(2) if remaining[i]]
            s2 = key5(v, remaining, cue, step + 1)
            if bootstrap == "max":
                boot = max(qv(s2, aa) for aa in nxt)
            else:
                pol = {aa: (eps / len(nxt) + (1.0 - eps) if aa == max(
                    nxt, key=lambda x: qv(s2, x)) else eps / len(nxt)) for aa in nxt}
                boot = sum(pp * qv(s2, aa) for aa, pp in pol.items())
            update(s, a, r + GAMMA * boot)
            if len(nxt) <= 1:
                break
    return Q


def run_cue(q: float, steps: int, seed: int, arm: str) -> float:
    src, default_steps, kw = ARMS[arm]
    if src == "p3":
        Q = train_cue_agent(q, steps, seed, **kw)
        return cue_sensitivity(Q)
    Q = train_arm(q, steps, seed, **kw)
    return cue_sensitivity(Q)


def mc_prob(p: float, n: int, rng) -> float:
    return float(np.mean(rng.rand(n) < p))
