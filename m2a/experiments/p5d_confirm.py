"""Phase V-d: confirm the L3 closed form on a fresh seed pool (never used in Phases III/IV/V/V-c)."""
from __future__ import annotations

from p3_mechanisms import cue_sensitivity, train_cue_agent
from p5_mechanisms import dp_sensitivity_only
from p5_v1_posthoc import visit_weighted

SEEDS_D = list(range(100, 110))
LEGACY_SEEDS = list(range(10))
QS_D = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
STEPS_D = 100000
ARMS_D = {
    "confirm_annealed": {},                                                  # eps 0.3 -> 0.02
    "confirm_const02": {"eps_start": 0.02, "eps_end": 0.02},                 # time-homogeneous
}


def readout_d(q: float, seed: int, arm: str) -> float:
    return cue_sensitivity(train_cue_agent(q, STEPS_D, seed, **ARMS_D[arm]))


def closed(q: float) -> float:
    return visit_weighted(q)


def dp_d(q: float) -> float:
    return dp_sensitivity_only(q, first="uniform", bootstrap="max", eps=0.02)


def law_old(q: float) -> float:
    from p5_mechanisms import law
    return law(q)
