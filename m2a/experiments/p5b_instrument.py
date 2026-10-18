"""Phase V-b instrument: the same threshold search as Phase V, with the theta-grid density
DERIVED from the science tolerance instead of fixed at 4001 points. See PHASE5B_PREREGISTRATION.md.
"""
from __future__ import annotations

import math

import numpy as np

from p4_mechanisms import cdf
from p5_mechanisms import ALPHA, predicted_critical

MAX_GRID = 200_001
DTHETA_FACTOR = 0.0002          # dtheta <= 0.001 * gap  => discretisation shifts beta* by <= 0.1%
BISECT_FACTOR = 0.0002         # bisection tolerance <= 0.0002 * predicted beta*


def grid_spec(gap: float):
    """(dtheta, n_points, measurable) from the pre-registered derivation."""
    span = gap + 1.0                       # theta is searched over [lo-0.5, hi+0.5]
    dtheta = DTHETA_FACTOR * gap
    n = int(math.ceil(span / dtheta)) + 1
    return dtheta, n, n <= MAX_GRID


def window_exists_grid(kind: str, beta: float, drive_lo: float, drive_hi: float,
                       thetas, alpha: float = ALPHA) -> bool:
    silent = cdf(beta * (drive_lo - thetas), kind)
    fire = cdf(beta * (drive_hi - thetas), kind)
    return bool(np.any((silent <= alpha) & (fire >= 1.0 - alpha)))


def critical_beta_adaptive(kind: str, drive_lo: float, drive_hi: float,
                           alpha: float = ALPHA) -> dict:
    gap = drive_hi - drive_lo
    if gap <= 0.0:
        return {"gap": 0.0, "numeric_beta": float("inf"), "measurable": True,
                "dtheta": None, "n_points": 0, "reason": "zero gap: no window at any beta"}
    pred = predicted_critical(kind, gap, alpha)
    dtheta, n, measurable = grid_spec(gap)
    if not measurable:
        return {"gap": gap, "numeric_beta": float("inf"), "measurable": False,
                "dtheta": dtheta, "n_points": n, "reason": "NOT_MEASURABLE: grid cap reached"}
    thetas = np.linspace(drive_lo - 0.5, drive_hi + 0.5, n)
    tol = BISECT_FACTOR * pred
    lo, hi = 0.02, 400.0
    if not window_exists_grid(kind, hi, drive_lo, drive_hi, thetas, alpha):
        return {"gap": gap, "numeric_beta": float("inf"), "measurable": True,
                "dtheta": dtheta, "n_points": n, "reason": "no window even at beta=400"}
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if window_exists_grid(kind, mid, drive_lo, drive_hi, thetas, alpha):
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-12:
            break
    return {"gap": gap, "numeric_beta": float(hi), "measurable": True,
            "dtheta": dtheta, "n_points": int(n), "predicted_beta": pred, "reason": "ok"}
