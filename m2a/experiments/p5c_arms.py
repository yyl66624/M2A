"""Phase V-c arms: every behaviour policy is made time-homogeneous so each arm has a
pre-declared exact dual (the visit-weighted fixed point of its own update operator).

Reuses Phase III/V code read-only (P5c-F5). No arm edits p3_mechanisms or p5_mechanisms.
"""
from __future__ import annotations

from p3_mechanisms import cue_sensitivity, train_cue_agent
from p5_mechanisms import dp_sensitivity_only, key5, train_arm
from p5_v1_posthoc import visit_weighted  # registered as the A3 claim in PHASE5C_PREREGISTRATION.md §2

# name: (source, steps, sampler kwargs, dp kwargs, dp_declared_faithful)
ARMS_C = {
    "annealed_base": ("p3", 100000, {}, dict(first="uniform", bootstrap="max", eps=0.02), False),
    "base_c": ("p3", 100000, {"eps_start": 0.02, "eps_end": 0.02},
               dict(first="uniform", bootstrap="max", eps=0.02), True),
    "base_long_c": ("p3", 400000, {"eps_start": 0.02, "eps_end": 0.02},
                    dict(first="uniform", bootstrap="max", eps=0.02), True),
    "noexplore_c": ("p3", 100000, {"eps_start": 0.0, "eps_end": 0.0},
                    dict(first="uniform", bootstrap="max", eps=0.0), True),
    "greedy_first_c": ("p5", 100000, {"first": "greedy", "eps_start": 0.02, "eps_end": 0.02},
                       dict(first="greedy", bootstrap="max", eps=0.02), True),
    "sarsa_c": ("p5", 100000, {"bootstrap": "expectation", "eps_start": 0.02, "eps_end": 0.02},
                dict(first="uniform", bootstrap="expectation", eps=0.02), True),
    "eps30_c": ("p3", 100000, {"eps_start": 0.3, "eps_end": 0.3},
                dict(first="uniform", bootstrap="max", eps=0.3), True),
}
QS_C = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
MID_C = [0.6, 0.7, 0.8, 0.9]


def train_cue_c(q: float, steps: int, seed: int, arm: str) -> dict:
    src, _, kw, _, _ = ARMS_C[arm]
    if src == "p3":
        return train_cue_agent(q, steps, seed, **kw)
    return train_arm(q, steps, seed, **kw)


def readout_c(q: float, seed: int, arm: str) -> float:
    return cue_sensitivity(train_cue_c(q, ARMS_C[arm][1], seed, arm))


def dp_c(q: float, arm: str) -> float:
    return dp_sensitivity_only(q, **ARMS_C[arm][3])


def law_half(q: float) -> float:
    from p5_mechanisms import law
    return law(q)


__all__ = ["ARMS_C", "QS_C", "MID_C", "train_cue_c", "readout_c", "dp_c", "visit_weighted",
           "law_half", "key5"]
