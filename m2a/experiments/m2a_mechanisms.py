"""Minimal mechanism implementations for M2A Phase II (E1, E1b, E2).

Everything here is synthetic and deterministic given a seed. Definitions follow
PHASE2_PREREGISTRATION.md; thresholds live in run_phase2.py and must not be edited after running.
"""
from __future__ import annotations

import itertools

import numpy as np


# ---------------------------------------------------------------- E1: conjunction
def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def p_action(arch: str, x1: float, x2: float, beta: float = 6.0, theta: float = 0.5) -> float:
    if arch == "none":
        return 0.0
    if arch == "single":
        z = x1 - theta
    elif arch == "and":
        z = x1 * x2 - theta
    elif arch == "or":
        z = x1 + x2 - theta
    else:
        raise ValueError(arch)
    return float(sigmoid(beta * z))


def e1_rates(arch: str, n: int, seed: int, noise: float = 0.0) -> dict:
    """Empirical P(action) for the four input cells, with optional input flip noise."""
    rng = np.random.RandomState(seed)
    rates = {}
    for x1, x2 in itertools.product([0.0, 1.0], repeat=2):
        p = p_action(arch, x1, x2)
        xs = []
        for _ in range(n):
            a, b = x1, x2
            if noise > 0:
                if rng.rand() < noise:
                    a = 1.0 - a
                if rng.rand() < noise:
                    b = 1.0 - b
            xs.append(1 if rng.rand() < p_action(arch, a, b) else 0)
        rates[(int(x1), int(x2))] = float(np.mean(xs))
    rates["interaction"] = (rates[(1, 1)] - rates[(1, 0)] - rates[(0, 1)] + rates[(0, 0)])
    rates["single_max"] = max(rates[(1, 0)], rates[(0, 1)])
    return rates


# ---------------------------------------------------------------- E1b: trigger vs gate vs constraint
def e1b_curve(kind: str, xs, beta: float = 6.0, theta: float = 0.5,
              polarity: int = 1, cap: float = 0.6) -> np.ndarray:
    xs = np.asarray(xs, dtype=float)
    if kind == "trigger":
        return sigmoid(beta * (xs - theta))
    if kind == "gate":
        return sigmoid(beta * (polarity * xs - theta))
    if kind == "constraint":
        return np.minimum(sigmoid(beta * (xs - theta)), cap)
    raise ValueError(kind)


def spearman(y) -> float:
    y = np.asarray(y, dtype=float)
    x = np.arange(len(y), dtype=float)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


# ---------------------------------------------------------------- E2: omission, S vs C
COST = 0.1   # action cost: taking an action yields value - COST (pre-run amendment P2-A2)


class AvailabilityBandit:
    """Two-step episode: up to two available actions may be taken, each yielding its value.

    Availability matters through the FUTURE (taking A leaves B available), so an agent whose state
    does not encode availability cannot learn the difference between {A} and {A,B} when the maximum
    is the same. That is exactly the S/C distinction under test.
    """

    def __init__(self, rng: np.random.RandomState):
        self.rng = rng

    def sample(self):
        # FIXED values per regime on purpose (pre-run amendments P2-A1/A2). Randomised values would
        # make (max, mask) insufficient to determine the future, so the hand values would not be
        # sharp. The low regime exists so that abstention can be optimal once the action cost is
        # charged: its gross values are below COST, so net value is negative.
        v = np.array([0.9, 0.5]) if self.rng.rand() < 0.8 else np.array([0.05, 0.1])
        mask = self.rng.randint(0, 2, size=2)  # 0/1 availability per action
        if mask.sum() == 0:
            mask[self.rng.randint(2)] = 1
        return v, mask


def state_key(kind: str, v: np.ndarray, mask: np.ndarray, cue: int = 0):
    avail = [i for i in range(2) if mask[i]]
    mx = int(round(max(v[i] for i in avail) * 10)) if avail else 0
    if kind == "S_only":
        return (mx,)
    if kind == "S_plus_C":
        return (mx, int(mask[0]) * 1 + int(mask[1]) * 2)
    if kind == "S_proxy":
        return (mx, cue)
    raise ValueError(kind)


def train_agent(kind: str, steps: int, seed: int, alpha=0.1, gamma=0.9,
                eps_start=0.3, eps_end=0.02) -> dict:
    rng = np.random.RandomState(seed)
    env = AvailabilityBandit(rng)
    Q = {}

    def q(s, a):
        return Q.setdefault((s, a), 0.0)

    for t in range(steps):
        eps = eps_start + (eps_end - eps_start) * t / max(steps - 1, 1)
        v, mask = env.sample()
        cue = int(mask[1] if rng.rand() < 0.8 else 1 - mask[1])
        remaining = mask.copy()
        for _ in range(2):
            s = state_key(kind, v, remaining, cue)
            avail_actions = [0] + [i + 1 for i in range(2) if remaining[i]]
            if rng.rand() < eps:
                a = avail_actions[rng.randint(len(avail_actions))]
            else:
                a = max(avail_actions, key=lambda x: q(s, x))
            if a == 0:
                # Abstaining ENDS the episode: the target is the immediate reward (0), not a bootstrap.
                Q[(s, a)] = Q.get((s, a), 0.0) + alpha * (0.0 - Q.get((s, a), 0.0))
                break
            idx = a - 1
            r = float(v[idx]) - COST
            remaining = remaining.copy()
            remaining[idx] = 0
            nxt = [0] + [i + 1 for i in range(2) if remaining[i]]
            s2 = state_key(kind, v, remaining, cue)
            target = r + (gamma * max(q(s2, aa) for aa in nxt) if nxt else 0.0)
            Q[(s, a)] = Q.get((s, a), 0.0) + alpha * (target - Q.get((s, a), 0.0))
            if len(nxt) <= 1:
                break
    return Q


def availability_sensitivity(Q: dict, kind: str, v_a=0.9, v_b=0.5) -> float:
    """Matched pair: {A} versus {A,B}; read Q(A) in each state."""
    v = np.array([v_a, v_b])
    s_alone = state_key(kind, v, np.array([1, 0]))
    s_both = state_key(kind, v, np.array([1, 1]))
    qa = Q.get((s_alone, 1), 0.0)
    qb = Q.get((s_both, 1), 0.0)
    return float(abs(qa - qb))


def proxy_sensitivity(Q: dict) -> float:
    """Exploratory probe for the cue-based agent: the two states share the maximum and differ only in
    the cue. The original probe compared a state with itself here (P2-C2), which is why the first run
    reported a hard zero."""
    s0 = state_key("S_proxy", np.array([0.9, 0.5]), np.array([1, 1]), cue=0)
    s1 = state_key("S_proxy", np.array([0.9, 0.5]), np.array([1, 1]), cue=1)
    return float(abs(Q.get((s0, 1), 0.0) - Q.get((s1, 1), 0.0)))


def abstention_rate(kind: str, steps: int, seed: int, theta=0.5) -> float:
    """S layer: with both actions available and max value below theta, how often does it abstain?"""
    Q = train_agent(kind, steps, seed)
    v = np.array([0.05, 0.1])   # gross values below COST -> net negative -> abstain is optimal
    s = state_key(kind, v, np.array([1, 1]))
    avail = [0, 1, 2]
    best = max(avail, key=lambda a: Q.get((s, a), 0.0))
    return 1.0 if best == 0 else 0.0
