"""Phase XII: fit the additive constant of the smooth counting law against the committed EXACT
instrument, then ask whether the exponent is -2 at that empirically located constant.

The large branch of the smoothed feasibility equation is used throughout, because e0 < 0 makes the
truncation declare a second, low-rate feasible branch (P10-O1 asks exactly whether that branch is an
artefact of the expansion or a real window - the discriminator is the exact instrument).
"""
from __future__ import annotations

from math import sqrt

import numpy as np

from p6_systems import Z95, loglog_slope
from p8_smooth import C1, rho_exact

E0_CANDIDATES = {"cornish_fisher_2sided": 2.0 * ((Z95 ** 2 - 1.0) / 6.0),
                 "cf_minus_lattice_2sided": 2.0 * ((Z95 ** 2 - 1.0) / 6.0 - 0.5),
                 "phase8_2sided": 2.0 * C1}
E0_GRID = np.round(np.arange(-2.0, 3.0 + 1e-9, 0.001), 6)
LAMBDA_CUTS = (10.0, 20.0, 50.0, 100.0, 200.0)


def B(s: float) -> float:
    return Z95 * (1.0 + sqrt(s))


def Bs(s: float) -> float:
    return Z95 / (2.0 * sqrt(s))


def _g(R: float, s: float, e0: float, e1: float) -> float:
    return (1.0 - s) * R * R - B(s) * R - e0 - (e1 / R if R > 0 else 0.0)


def root_large(s: float, e0: float, e1: float = 0.0):
    """Largest positive root of the smoothed feasibility equation, or None when there is none."""
    delta = 1.0 - s
    if delta <= 0.0:
        return None
    if e1 == 0.0:
        disc = B(s) ** 2 + 4.0 * delta * e0
        if disc < 0.0:
            return None
        return (B(s) + sqrt(disc)) / (2.0 * delta)
    hi = B(s) / delta + (abs(e0) + abs(e1) + 1.0) / delta
    for _ in range(400):
        if _g(hi, s, e0, e1) > 0.0 and 2.0 * delta * hi - B(s) + e1 / (hi * hi) > 0.0:
            break
        hi *= 2.0
    lo = hi
    for _ in range(4000):
        lo *= 0.5
        if lo < 1e-15:
            return hi if _g(hi, s, e0, e1) > 0 else None
        if _g(lo, s, e0, e1) < 0.0:
            break
    else:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _g(mid, s, e0, e1) < 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-16 * max(hi, 1.0):
            break
    return 0.5 * (lo + hi)


def root_small(s: float, e0: float) -> float | None:
    """The second (low-rate) branch, present only when e0 < 0 and the discriminant is positive."""
    delta = 1.0 - s
    if delta <= 0.0 or e0 >= 0.0:
        return None
    disc = B(s) ** 2 + 4.0 * delta * e0
    if disc <= 0.0:
        return None
    lo = (B(s) - sqrt(disc)) / (2.0 * delta)
    return lo if lo > 0.0 else None


def rho_smooth(e0: float, s: float, e1: float = 0.0):
    R = root_large(s, e0, e1)
    return None if R is None else R * R


def slope_large(s: float, e0: float, e1: float = 0.0):
    """(diamond) evaluated at the large branch."""
    R = root_large(s, e0, e1)
    if R is None or R <= 0.0:
        return None
    return -2.0 * (1.0 - s) * (R + Bs(s)) / (B(s) + 2.0 * e0 / R + 3.0 * e1 / (R * R))


def num_slope_large(s: float, e0: float, e1: float = 0.0, rel: float = 1e-4):
    def once(rr):
        d = 1.0 - s
        rp, rm = rho_smooth(e0, 1.0 - d * (1 + rr), e1), rho_smooth(e0, 1.0 - d * (1 - rr), e1)
        return (np.log(rp) - np.log(rm)) / (np.log(d * (1 + rr)) - np.log(d * (1 - rr)))
    return (4.0 * once(rel / 2.0) - once(rel)) / 3.0


def subset(s_grid, lam, cut: float):
    return [s for s in s_grid if lam[str(s)] >= cut]


def exponent(e0: float, ss, e1: float = 0.0) -> float:
    return loglog_slope([1.0 - s for s in ss], [rho_smooth(e0, s, e1) for s in ss])


def track_error(e0: float, ss, lam) -> float:
    vals = [rho_smooth(e0, s) for s in ss]
    if any(v is None for v in vals):
        return float("inf")
    return max(abs(v / lam[str(s)] - 1.0) for v, s in zip(vals, ss))


def fit_e0(s_grid, lam, cut: float = 100.0):
    ss = subset(s_grid, lam, cut)
    errs = np.array([track_error(e0, ss, lam) for e0 in E0_GRID])
    j = int(np.nanargmin(errs))
    return float(E0_GRID[j]), float(errs[j]), ss, {
        "grid_step": float(E0_GRID[1] - E0_GRID[0]),
        "objective_change_per_step": float(abs(errs[j] - errs[max(j - 1, 0)])),
        "at_boundary": j == 0 or j == len(E0_GRID) - 1,
        "n_finite": int(np.isfinite(errs).sum())}
