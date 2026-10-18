"""Phase XI: soft failure bands. The threshold constant should track the aggregator's REACHABLE
supremum inside the band L_tau (diamond-diamond), not the band edge tau itself.

Aggregators include two deliberately non-surjective ones (nilpotent minimum, stepped minimum) so the
competing hypotheses "depends on tau" and "depends on L_tau" are separated by 133% and 6.7% at
tau = 0.3 - the criteria are not restatements of the reduction. Group B extends the free-threshold
fixed point to k = 3 and checks it with an out-of-sample random control (R4, seeds 2000-2019).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from p4_mechanisms import cdf, quantile
from p5_mechanisms import ALPHA
from p5b_instrument import BISECT_FACTOR, DTHETA_FACTOR, MAX_GRID

THETA_LO, THETA_HI = -0.5, 1.5
N_AXIS = 101
AGGS = ("product", "min", "lukasiewicz", "nilpotent", "stepped")
SURJECTIVE = ("product", "min", "lukasiewicz")
STEP = 0.25


def agg(name: str, x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if name == "product":
        return np.prod(x, axis=-1)
    if name == "min":
        return np.min(x, axis=-1)
    if name == "lukasiewicz":
        m = x.shape[-1]
        return np.maximum(0.0, np.sum(x, axis=-1) - (m - 1))
    if name == "nilpotent":                      # min if min > 0.5 else 0  -> range {0} u (0.5,1]
        mn = np.min(x, axis=-1)
        return np.where(mn > 0.5, mn, 0.0)
    if name == "stepped":                        # floor(min / h) * h
        return np.floor(np.min(x, axis=-1) / STEP) * STEP
    raise ValueError(name)


@lru_cache(maxsize=None)
def levels(name: str, m: int):
    """Sorted unique reachable stage drives of the aggregator over an N_AXIS^n grid."""
    grid = np.linspace(0.0, 1.0, N_AXIS)
    mesh = np.array(np.meshgrid(*([grid] * m), indexing="ij")).reshape(m, -1).T
    vals = np.round(agg(name, mesh), 10)
    return np.unique(vals)


def L_tau(name: str, m: int, tau: float) -> float:
    lv = levels(name, m)
    in_band = lv[lv <= tau + 1e-12]
    return float(in_band[-1]) if in_band.size else float("nan")


def phi_psi(k: int, alpha: float = ALPHA):
    phi = (1.0 - alpha) ** (1.0 / k)
    psi = alpha / (1.0 - alpha) ** ((k - 1.0) / k)
    return phi, psi


def predicted(kind: str, k: int, lo: float, alpha: float = ALPHA) -> float:
    phi, psi = phi_psi(k, alpha)
    gap = 1.0 - lo
    if gap <= 0.0:
        return float("inf")
    return (quantile(phi, kind) - quantile(psi, kind)) / gap


def beta_star_band(kind: str, k: int, lo: float, alpha: float = ALPHA) -> dict:
    """Window search: fire = F(beta(1-th))^k >= 1-alpha, silent = F(beta(lo-th))F(beta(1-th))^(k-1) <= alpha."""
    pred = predicted(kind, k, lo, alpha)
    base = {"kind": kind, "k": k, "lo": lo, "pred": pred}
    if not np.isfinite(lo) or 1.0 - lo <= 0.0:
        return {**base, "beta": float("inf"), "measurable": False, "reason": "no usable band level"}
    dtheta = DTHETA_FACTOR * (1.0 - lo)
    n = int(math.ceil((THETA_HI - THETA_LO) / dtheta)) + 1
    if n > MAX_GRID:
        return {**base, "beta": float("inf"), "measurable": False, "n_points": n,
                "reason": "NOT_MEASURABLE: grid cap"}
    thetas = np.linspace(THETA_HI, THETA_LO, n)          # descending keeps the arrays aligned

    def feasible(beta):
        f = np.asarray(cdf(beta * (1.0 - thetas), kind), dtype=float)
        fire = f ** k
        silent = np.asarray(cdf(beta * (lo - thetas), kind), dtype=float) * f ** (k - 1)
        return bool(np.any((fire >= 1.0 - alpha) & (silent <= alpha)))

    lo_b, hi_b = 0.02, 400.0
    if not feasible(hi_b):
        return {**base, "beta": float("inf"), "measurable": True, "n_points": n,
                "reason": "no window even at beta=400"}
    tol = max(BISECT_FACTOR * pred, 1e-6)
    while hi_b - lo_b > tol:
        mid = 0.5 * (lo_b + hi_b)
        if feasible(mid):
            hi_b = mid
        else:
            lo_b = mid
    return {**base, "beta": float(hi_b), "measurable": True, "n_points": int(n),
            "rel_diff": abs(float(hi_b) - pred) / pred, "reason": "ok"}


# ------------------------------------------------------------------ B: k=3 free thresholds
def _u_of_ratio(kind, beta, lo_i, rho):
    """max F(beta(1-th)) with F(beta(lo_i-th))/F(beta(1-th)) <= rho, theta in the box."""
    def r(th):
        u = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
        v = np.asarray(cdf(beta * (lo_i - th), kind), dtype=float)
        return np.where(u > 0, v / np.maximum(u, 1e-300), np.inf)
    lo = np.full_like(rho, THETA_LO)
    hi = np.full_like(rho, THETA_HI)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        too_big = r(mid) > rho
        lo = np.where(too_big, mid, lo)
        hi = np.where(too_big, hi, mid)
    u = np.asarray(cdf(beta * (1.0 - hi), kind), dtype=float)
    return np.where(r(hi) <= rho + 1e-15, u, 0.0), hi


def fixed_point_P(kind, beta, los, alpha: float = ALPHA):
    """Solve rho * prod_i U_i(rho) = alpha; return (P, rho, thetas)."""
    lo, hi = 1e-9, alpha / (1.0 - alpha)
    for _ in range(80):
        mid = np.array([0.5 * (lo + hi)])
        us = [_u_of_ratio(kind, beta, li, mid)[0][0] for li in los]
        q = float(np.prod(us))
        if mid[0] * q > alpha:
            hi = mid[0]
        else:
            lo = mid[0]
    rho0 = 0.5 * (lo + hi)
    arr = np.array([rho0])
    us, ths = [], []
    for li in los:
        u, th = _u_of_ratio(kind, beta, li, arr)
        us.append(float(u[0]))
        ths.append(float(th[0]))
    return float(np.prod(us)), float(rho0), ths, us


def beta_star_free(kind, los, alpha: float = ALPHA, tol: float = None) -> dict:
    pred = predicted(kind, len(los), max(los), alpha)
    lo, hi = 0.02, 400.0
    if fixed_point_P(kind, hi, los, alpha)[0] < 1.0 - alpha:
        return {"beta": float("inf"), "reason": "no window even at beta=400", "pred": pred}
    t = tol if tol is not None else max(BISECT_FACTOR * pred, 1e-6)
    while hi - lo > t:
        mid = 0.5 * (lo + hi)
        if fixed_point_P(kind, mid, los, alpha)[0] >= 1.0 - alpha:
            hi = mid
        else:
            lo = mid
    P, rho0, ths, us = fixed_point_P(kind, hi, los, alpha)
    rs = []
    for li, th in zip(los, ths):
        u = float(cdf(hi * (1.0 - th), kind))
        v = float(cdf(hi * (li - th), kind))
        rs.append(v / u if u > 0 else float("inf"))
    return {"beta": float(hi), "P": P, "rho": rho0, "thetas": ths, "u": us, "r": rs,
            "pred_shared": pred, "reason": "ok"}


def random_control(kind, beta, los, seeds, n_draws, alpha: float = ALPHA, center=None,
                   half=None):
    """Global control below beta* (must find nothing); local control above it (P11-A1)."""
    hits = 0
    for sd in seeds:
        rng = np.random.RandomState(sd)
        if center is None:
            th = rng.uniform(THETA_LO, THETA_HI, size=(n_draws, len(los)))
        else:
            w = np.array(center)
            th = rng.uniform(w - half, w + half, size=(n_draws, len(los)))
        f = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
        v = np.asarray(cdf(beta * (np.array(los)[None, :] - th), kind), dtype=float)
        fire = np.prod(f, axis=1)
        silent = fire * np.max(v / np.maximum(f, 1e-300), axis=1)   # worst stage per draw
        hits += int(np.count_nonzero((fire >= 1.0 - alpha) & (silent <= alpha)))
    return hits


PRIOR_SEED_POOLS = [list(range(0, 10)), list(range(100, 110))]
SEEDS_XI = list(range(2000, 2020))
