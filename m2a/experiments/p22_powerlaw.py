"""Phase XXII instrument: interval-weighted write families N(p) and F(p) under the A/S/V filter.

Tolerances and the three conditions are imported and never redefined here.
"""
from __future__ import annotations

import math

import p20_filter as p20

PS = (0.0, 0.5, 1.0, 1.5, 2.0)
FAMILIES = ("N", "F")
CLASSES = ("M2",) + tuple(f"{fam}{p:g}" for fam in FAMILIES for p in PS)


def label_of(fam: str, p: float) -> str:
    return f"{fam}{p:g}"


def reading(cls: str, n: int, c: float, scale_tau: bool) -> float:
    if cls == "M2":
        return p20.reading("M2", n, c, scale_tau)
    fam, p = cls[0], float(cls[1:])
    dt = c * p20.T / n
    weight = p20.ETA * dt ** p
    if fam == "N":
        return n * weight
    tau = c * p20.TAU if scale_tau else p20.TAU
    lam = math.exp(-dt / tau)
    return n * weight if lam >= 1.0 else weight * (1.0 - lam ** n) / (1.0 - lam)


def loop(cls: str, n: int, c: float, scale_tau: bool) -> float:
    if cls == "M2":
        return p20.loop("M2", n, c, scale_tau)
    fam, p = cls[0], float(cls[1:])
    dt = c * p20.T / n
    weight = p20.ETA * dt ** p
    acc = 0.0
    if fam == "N":
        for _ in range(n):
            acc = acc + weight
        return acc
    tau = c * p20.TAU if scale_tau else p20.TAU
    lam = math.exp(-dt / tau)
    for _ in range(n):
        acc = lam * acc + weight
    return acc


def spread(vals: list[float]) -> float:
    return max(vals) - min(vals)


def a_spread(cls: str) -> float:
    return spread([reading(cls, n, 1.0, False) for n in p20.NS])


def s_spread(cls: str) -> float:
    return max(spread([reading(cls, n, c, False) for c in p20.CS]) for n in p20.NS)


def v_spread(cls: str) -> float:
    return max(spread([reading(cls, n, c, True) for c in p20.CS]) for n in p20.NS)


def classify_all() -> dict:
    out = {}
    for cls in CLASSES:
        a, s, v = a_spread(cls), s_spread(cls), v_spread(cls)
        out[cls] = {"A_spread": a, "S_spread": s, "V_spread": v,
                    "A_pass": a <= p20.TOL, "S_pass": s >= p20.SENS, "V_pass": v <= p20.TOL}
    return out


def n_series(p: float) -> list[float]:
    """Terminal states of N(p) over n at c = 1, for the power-law slope check."""
    return [reading(label_of("N", p), n, 1.0, False) for n in p20.NS]
