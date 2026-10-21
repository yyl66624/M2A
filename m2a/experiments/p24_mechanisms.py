"""Phase XXIV design instruments (pure): a weight-decayed L3 learner and its exact DP operator.

This module is the *instrument* for the regularization round. It writes nothing and reads nothing at
import time. The λ=0 path is byte-for-byte the Phase III learner and the Phase V visit-weighted DP;
the gate proves both identities before any run. The scientific criterion lives in
PHASE24_PREREGISTRATION.md and is evaluated by the future runner, never here.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from m2a_mechanisms import COST
from p3_mechanisms import CueBandit, cue_sensitivity, key3
from p5_mechanisms import GAMMA, _policy, enumerate_draws, key5

LAMBDAS = (0.0, 0.1, 0.2, 0.4)
QS = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SEEDS = tuple(range(4000, 4010))
CONFIRM_SEEDS = tuple(range(4010, 4020))
STEPS = 100000
EPS_OP = 0.008          # Phase V-d D1, reused unchanged
EPS_REPAIR = 0.008      # a repair must exceed the same instrument tolerance
REPAIR_QS = QS          # C2 is evaluated on every q; q=0.5 is a no-cue control


def old_law(q: float) -> float:
    return 0.36 * (2.0 * q - 1.0)


def old_deviation(delta: float, q: float) -> float:
    return abs(float(delta) - old_law(q))


def train_cue_agent_reg(q: float, steps: int, seed: int, lam: float,
                        alpha=0.1, gamma=0.9, eps_start=0.3, eps_end=0.02) -> dict:
    """p3_mechanisms.train_cue_agent with weight decay: Q += step*(target - (1+lam)Q).

    The RNG call sequence, the uniform first action, the epsilon-greedy second action and the
    max-tie rule are copied literally; at lam=0 the Q table is identical to the Phase III learner.
    """
    rng = np.random.RandomState(seed)
    env = CueBandit(rng, q)
    Q = {}
    N = {}

    def qv(s, a):
        return Q.setdefault((s, a), 0.0)

    def update(s, a, target):
        N[(s, a)] = N.get((s, a), 0) + 1
        step_size = 1.0 / (1.0 + N[(s, a)])
        Q[(s, a)] = Q.get((s, a), 0.0) + step_size * (
            target - (1.0 + lam) * Q.get((s, a), 0.0))

    for t in range(steps):
        eps = eps_start + (eps_end - eps_start) * t / max(steps - 1, 1)
        v, mask, cue = env.sample()
        remaining = mask.copy()
        for step in (1, 2):
            s = key3(v, remaining, cue, step)
            avail = [0] + [i + 1 for i in range(2) if remaining[i]]
            if step == 1:
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
            s2 = key3(v, remaining, cue, step + 1)
            target = r + (gamma * max(qv(s2, aa) for aa in nxt) if nxt else 0.0)
            update(s, a, target)
            if len(nxt) <= 1:
                break
    return Q


def dp_sensitivity_reg(q: float, lam: float, first="uniform", bootstrap="max", eps=0.02,
                       gamma=GAMMA, iters=6000, tol=1e-13):
    """Fixed point of the visit-weighted operator with the same weight decay.

    The sampled update converges to E[target] - (1+lam)Q = 0, so the operator iteration is
    Q <- (1-eta)Q + eta * (E[target](Q) / (1+lam)). At lam=0 this is exactly p5_mechanisms.
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
                    W[(s1, a)] += p * pa
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
                W[(s1, a)] += p * pa
                T[(s1, a)] += p * pa * target
                if len(nxt) <= 1:
                    continue
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
                    w2 = p * pa * pa2
                    W[(s2, a2)] += w2
                    T[(s2, a2)] += w2 * t2
        if not W:
            break
        new = {k: T[k] / W[k] for k in W}
        tgt = {k: new[k] / (1.0 + lam) for k in new}
        eta = 0.25
        nxt_Q = {k: (1.0 - eta) * Q.get(k, 0.0) + eta * tgt[k] for k in tgt}
        delta = max(abs(nxt_Q[k] - Q.get(k, 0.0)) for k in nxt_Q)
        Q = nxt_Q
        if delta < tol:
            break
    probe = np.array([0.9, 0.5])
    full = np.array([1, 1])
    s0 = key5(probe, full, 0, 1)
    s1 = key5(probe, full, 1, 1)
    return float(abs(Q.get((s0, 1), 0.0) - Q.get((s1, 1), 0.0))), Q


def sensitivity_reg(q: float, steps: int, seed: int, lam: float) -> float:
    return cue_sensitivity(train_cue_agent_reg(q, steps, seed, lam))


EXIT_LABELS = ("ANCHOR-BROKEN", "INDETERMINATE", "OPERATOR-MISMATCH",
               "REGULARIZATION-REPAIRS", "REGULARIZATION-DOES-NOT-REPAIR", "O-NONE")


def classify(m: dict) -> str:
    """The registered exit order; first true exit wins. Metrics are filled by the runner."""
    if not m.get("anchor_ok", False):
        return "ANCHOR-BROKEN"
    if not m.get("resolution_ok", False):
        return "INDETERMINATE"
    if not m.get("operator_ok", False):
        return "OPERATOR-MISMATCH"
    if m.get("repair_found", False):
        return "REGULARIZATION-REPAIRS"
    if m.get("clean", False):
        return "REGULARIZATION-DOES-NOT-REPAIR"
    return "O-NONE"
