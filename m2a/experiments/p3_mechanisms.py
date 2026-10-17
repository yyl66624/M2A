"""Phase III mechanism implementations: the conjunction window (L1), gate openness (L2) and the
representation-quality agent (L3).

L3 fixes the Phase II self-loop by putting the STEP NUMBER in the state, so taking the lower-value
action changes the state key and the Q update can bootstrap properly.
"""
from __future__ import annotations

import numpy as np

from m2a_mechanisms import COST, sigmoid

LOGIT05 = float(np.log(0.05 / 0.95))   # -2.9444...


# ---------------------------------------------------------------- L1
def p_and(x1, x2, beta, theta):
    return float(sigmoid(beta * (x1 * x2 - theta)))


def p_or(x1, x2, beta, theta):
    return float(sigmoid(beta * (x1 + x2 - theta)))


def theta_s(beta, alpha=0.05):
    """Single-path silencing boundary: p_and(1,0) = alpha  =>  theta = |logit alpha| / beta."""
    return abs(LOGIT05) / beta


def theta_j(beta, alpha=0.05):
    """Joint firing boundary: p_and(1,1) = 1 - alpha  =>  theta = 1 - |logit alpha| / beta."""
    return 1.0 - abs(LOGIT05) / beta


def conjunction_window(beta, alpha=0.05):
    lo, hi = theta_s(beta, alpha), theta_j(beta, alpha)
    return (lo, hi) if lo <= hi else None


# ---------------------------------------------------------------- L2
def p_gate(x, o, beta=6.0, theta=0.5):
    x = np.asarray(x, dtype=float)
    return sigmoid(beta * (x * (2.0 * o - 1.0) - theta))


# ---------------------------------------------------------------- L3
class CueBandit:
    """Two-step availability bandit with a noisy cue about the second action's availability."""

    def __init__(self, rng, q: float):
        self.rng = rng
        self.q = q

    def sample(self):
        v = np.array([0.9, 0.5]) if self.rng.rand() < 0.8 else np.array([0.05, 0.1])
        mask = self.rng.randint(0, 2, size=2)
        if mask.sum() == 0:
            mask[self.rng.randint(2)] = 1
        cue = int(mask[1] if self.rng.rand() < self.q else 1 - mask[1])
        return v, mask, cue


def key3(v, mask, cue, step):
    avail = [i for i in range(2) if mask[i]]
    mx = int(round(max(v[i] for i in avail) * 10)) if avail else 0
    return (mx, int(step), int(cue))


def train_cue_agent(q: float, steps: int, seed: int, alpha=0.1, gamma=0.9,
                    eps_start=0.3, eps_end=0.02) -> dict:
    rng = np.random.RandomState(seed)
    env = CueBandit(rng, q)
    Q = {}
    N = {}

    def qv(s, a):
        return Q.setdefault((s, a), 0.0)

    def update(s, a, target):
        # P3-A4: a CONSTANT alpha leaves a moving average whose variance is ~ SD(target)/sqrt(1/alpha)
        # - at alpha=0.1 that is about 0.057 here, which showed up as a spurious 0.061 difference
        # between two states that must be identical when the cue is uninformative. The 1/(1+n) rate
        # makes the estimate converge to the target mean instead of tracking recent samples.
        N[(s, a)] = N.get((s, a), 0) + 1
        step_size = 1.0 / (1.0 + N[(s, a)])
        Q[(s, a)] = Q.get((s, a), 0.0) + step_size * (target - Q.get((s, a), 0.0))

    for t in range(steps):
        eps = eps_start + (eps_end - eps_start) * t / max(steps - 1, 1)
        v, mask, cue = env.sample()
        remaining = mask.copy()
        for step in (1, 2):
            s = key3(v, remaining, cue, step)
            avail = [0] + [i + 1 for i in range(2) if remaining[i]]
            # COVERAGE (P3-A2): the first action is sampled UNIFORMLY, not epsilon-greedily. Under a
            # greedy first action, A is taken almost only when B is unavailable, so the update target
            # at state (max, 1, cue) is drawn from a behaviour-biased distribution and Q(A) converges
            # to the wrong value (0.8 instead of the posterior-weighted 1.12). Q-learning may learn
            # off-policy, but only if the behaviour policy covers the state-action space.
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


def cue_sensitivity(Q: dict) -> float:
    v = np.array([0.9, 0.5])
    s0 = key3(v, np.array([1, 1]), cue=0, step=1)
    s1 = key3(v, np.array([1, 1]), cue=1, step=1)
    return float(abs(Q.get((s0, 1), 0.0) - Q.get((s1, 1), 0.0)))


def predicted_cue_sensitivity(q: float, gamma=0.9, v_b=0.5, c=COST) -> float:
    """Sensitivity law (P3-A3). At the probe state the max is 0.9, which can only come from masks
    [1,0] or [1,1]; conditioning on it makes the prior P(B available) = 1/2, so the posterior
    difference is exactly (2q - 1) and the law is Delta = gamma*(v_B - c)*(2q - 1).

    The earlier version used the UNCONDITIONED prior 2/3, which is wrong at the probe state; the
    conditioned prior halves it and the two forms differ by a factor."""
    return gamma * (v_b - c) * (2.0 * q - 1.0)
