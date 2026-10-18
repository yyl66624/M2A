"""Phase XVII: refine BOTH discretisation layers (theta truncation interval AND node density) before
judging cross-k consistency - the layer X-50 showed the density-only shift cannot see.

The predicate here is written independently of p14_ratelaw (P17-A2), so that reproducing the committed
readings at (h=1.0, n=20001) is a cross-path check rather than a self-check.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

import numpy as np

from p4_mechanisms import cdf
from p5_mechanisms import ALPHA

CENTER = 0.5                      # midpoint of the committed interval [-0.5, 1.5]
HS = (0.5, 1.0, 2.0)              # half-widths; h=1.0 IS the committed interval
NS = (20001, 40001)
JS = (10, 20, 40, 100, 200, 400, 800)
KINDS = ("logistic", "probit", "gumbel")
KS = (2, 3, 4)
BISECT_TOL = 1e-9
BISECT_LO, BISECT_HI = 0.02, 400.0
H_PRIM, N_PRIM = 2.0, 40001       # primary reading: least-truncated and densest (P17-A1)
ANCHOR_TOL = 1e-15
SUP = 0.5                         # the band supremum L used by the committed rounds


@lru_cache(maxsize=32)
def nodes(h: float, n: int):
    """Descending node order, matching the committed p11/p14 instrument."""
    return np.linspace(CENTER + h, CENTER - h, n)


def level(J: int) -> float:
    """The committed rounded level from p13.levels_gap, re-derived: round(x, 12) of 0.5 - 0.5/(J+1)."""
    return round(0.5 - 0.5 / (J + 1.0), 12)


def feasible(kind: str, beta: float, lo: float, k: int, h: float, n: int, alpha: float = ALPHA) -> bool:
    th = nodes(h, n)
    f = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
    silent = np.asarray(cdf(beta * (lo - th), kind), dtype=float) * f ** (k - 1)
    return bool(np.any((f ** k >= 1.0 - alpha) & (silent <= alpha)))


def beta_star(kind: str, k: int, lo: float, h: float, n: int, tol: float = BISECT_TOL) -> float:
    lo_b, hi_b = BISECT_LO, BISECT_HI
    if not feasible(kind, hi_b, lo, k, h, n):
        return float("inf")
    while hi_b - lo_b > tol:
        mid = 0.5 * (lo_b + hi_b)
        if feasible(kind, mid, lo, k, h, n):
            hi_b = mid
        else:
            lo_b = mid
    return float(hi_b)


def delta_at(kind: str, k: int, J: int, h: float, n: int, closure: float):
    b = beta_star(kind, k, level(J), h, n)
    return (closure - b) / closure, b


def sweep(kind: str, k: int) -> dict:
    """All six configs, with the closure always taken at the same config as beta_J (P17-A1)."""
    configs = ((1.0, 20001), (1.0, 40001), (H_PRIM, N_PRIM))
    cl = {(h, n): beta_star(kind, k, SUP, h, n) for h, n in configs}
    rows = []
    for J in JS:
        d = {}
        b = {}
        for (h, n), c in cl.items():
            d[(h, n)], b[(h, n)] = delta_at(kind, k, J, h, n, c)
        d[(0.5, 20001)] = delta_at(kind, k, J, 0.5, 20001, cl[(1.0, 20001)])[0]
        l2 = abs(d[(1.0, 40001)] - d[(1.0, 20001)])
        l1 = abs(d[(H_PRIM, N_PRIM)] - d[(1.0, 40001)])
        rows.append({"J": int(J), "lo": float(level(J)),
                     "delta_committed": float(d[(1.0, 20001)]),
                     "delta_h1_n40001": float(d[(1.0, 40001)]),
                     "delta_primary": float(d[(H_PRIM, N_PRIM)]),
                     "delta_h05": float(d[(0.5, 20001)]),
                     "beta_committed": float(b[(1.0, 20001)]),
                     "beta_primary": float(b[(H_PRIM, N_PRIM)]),
                     "closure_committed": float(cl[(1.0, 20001)]),
                     "closure_primary": float(cl[(H_PRIM, N_PRIM)]),
                     "L_density": float(l2), "L_trunc": float(l1), "L_total": float(l1 + l2),
                     "L_trunc_narrow": float(abs(d[(1.0, 20001)] - d[(0.5, 20001)])),
                     "delta_exact": float(1.0 / (J + 2.0))})
    return {"kind": kind, "k": int(k), "rows": rows}


def committed_reference():
    """(kind, k, J) -> the committed delta_coarse of the density-only instrument, for the cross-path anchor."""
    exp = pathlib.Path(__file__).resolve().parent
    out = {}
    p14 = json.loads((exp / "phase14_results.json").read_text(encoding="utf-8"))["per_kind"]
    for kind, g in p14.items():
        for r in g["rows"]:
            out[(kind, int(g["k"]), int(r["J"]))] = float(r["delta_coarse"])
    p16 = json.loads((exp / "phase16_results.json").read_text(encoding="utf-8"))["groups"]
    for name, g in p16.items():
        for r in g["rows"]:
            out[(g["kind"], int(g["k"]), int(r["J"]))] = float(r["delta_coarse"])
    return out
