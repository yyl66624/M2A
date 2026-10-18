"""Phase XVIII: add the third approximation knob - sliding the whole node set by sigma*dtheta while
keeping spacing and interval fixed - so aliasing of the max-type predicate becomes measurable at all.

Written independently of p14/p17 (anchor C18-1 is a cross-path check); sigma=0 must reproduce them
bit for bit, which is what makes sigma=0.5 a clean single-variable probe.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

import numpy as np

from p4_mechanisms import cdf
from p5_mechanisms import ALPHA

CENTER = 0.5
JS = (10, 20, 40, 100, 200, 400, 800)
KINDS = ("logistic", "probit", "gumbel")
KS = (2, 3, 4)
SUP = 0.5
BISECT_TOL = 1e-9
BISECT_LO, BISECT_HI = 0.02, 400.0
ANCHOR_TOL = 1e-15

PRIMARY = (2.0, 40001, 0.5)
REVERT_DENSITY = (2.0, 20001, 0.5)
REVERT_TRUNC = (1.0, 40001, 0.5)
REVERT_STAGGER = (2.0, 40001, 0.0)
COMMITTED = (1.0, 20001, 0.0)
CONFIGS = (PRIMARY, REVERT_DENSITY, REVERT_TRUNC, REVERT_STAGGER, COMMITTED)


def dtheta(h: float, n: int) -> float:
    return 2.0 * h / (n - 1)


@lru_cache(maxsize=32)
def nodes(h: float, n: int, sigma: float):
    return np.linspace(CENTER + h, CENTER - h, n) - sigma * dtheta(h, n)


def level(J: int) -> float:
    return round(0.5 - 0.5 / (J + 1.0), 12)


def feasible(kind: str, beta: float, lo: float, k: int, cfg, alpha: float = ALPHA) -> bool:
    h, n, s = cfg
    th = nodes(h, n, s)
    f = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
    silent = np.asarray(cdf(beta * (lo - th), kind), dtype=float) * f ** (k - 1)
    return bool(np.any((f ** k >= 1.0 - alpha) & (silent <= alpha)))


def beta_star(kind: str, k: int, lo: float, cfg, tol: float = BISECT_TOL) -> float:
    lo_b, hi_b = BISECT_LO, BISECT_HI
    if not feasible(kind, hi_b, lo, k, cfg):
        return float("inf")
    while hi_b - lo_b > tol:
        mid = 0.5 * (lo_b + hi_b)
        if feasible(kind, mid, lo, k, cfg):
            hi_b = mid
        else:
            lo_b = mid
    return float(hi_b)


def sweep(kind: str, k: int) -> dict:
    cl = {cfg: beta_star(kind, k, SUP, cfg) for cfg in CONFIGS}
    rows = []
    for J in JS:
        d = {}
        b = {}
        for cfg in CONFIGS:
            beta = beta_star(kind, k, level(J), cfg)
            d[cfg] = (cl[cfg] - beta) / cl[cfg]
            b[cfg] = beta
        l_den = abs(d[PRIMARY] - d[REVERT_DENSITY])
        l_tru = abs(d[PRIMARY] - d[REVERT_TRUNC])
        l_sta = abs(d[PRIMARY] - d[REVERT_STAGGER])
        rows.append({"J": int(J), "lo": float(level(J)),
                     "delta_primary": float(d[PRIMARY]),
                     "delta_committed": float(d[COMMITTED]),
                     "delta_revert_stagger": float(d[REVERT_STAGGER]),
                     "delta_revert_density": float(d[REVERT_DENSITY]),
                     "delta_revert_trunc": float(d[REVERT_TRUNC]),
                     "beta_primary": float(b[PRIMARY]), "closure_primary": float(cl[PRIMARY]),
                     "L_density": float(l_den), "L_trunc": float(l_tru), "L_stagger": float(l_sta),
                     "L3": float(l_den + l_tru + l_sta), "delta_exact": float(1.0 / (J + 2.0))})
    return {"kind": kind, "k": int(k), "rows": rows}


def committed_reference_all():
    """(kind, k, J) -> (phase14/16 committed delta at h1n20001, phase17 primary delta at h2n40001)."""
    exp = pathlib.Path(__file__).resolve().parent
    a, b = {}, {}
    p14 = json.loads((exp / "phase14_results.json").read_text(encoding="utf-8"))["per_kind"]
    for kind, g in p14.items():
        for r in g["rows"]:
            a[(kind, int(g["k"]), int(r["J"]))] = float(r["delta_coarse"])
    p16 = json.loads((exp / "phase16_results.json").read_text(encoding="utf-8"))["groups"]
    for name, g in p16.items():
        for r in g["rows"]:
            a[(g["kind"], int(g["k"]), int(r["J"]))] = float(r["delta_coarse"])
    p17 = json.loads((exp / "phase17_results.json").read_text(encoding="utf-8"))["sweeps"]
    for name, g in p17.items():
        for r in g["rows"]:
            b[(g["kind"], int(g["k"]), int(r["J"]))] = float(r["delta_primary"])
    return a, b
