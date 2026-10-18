"""Phase IX: (A) aggregation immunity of the composition law, (B) free per-stage thresholds.

No sampling anywhere: every reading is a deterministic function evaluation, a theta grid or a
vectorised bisection. Definitions and tolerances follow PHASE9_PREREGISTRATION.md (as amended by
its own P9 pre-run registrations); the numbers in run_phase9.py must not be edited afterwards.

Part A enumerates every stage-level multiset over the alphabet {s, 1} for four aggregators and
takes the maximum failing-configuration probability, exactly as Phase VII's instrument does, so the
L-reduction (prediction) is tested against the enumeration rather than assumed by it.

Part B solves the k=2 system with two independent thresholds. The brute-force instrument never uses
the ratio reduction: for each theta_1 on the grid it locates the feasible theta_2 interval by three
monotone bisections. The fixed-point instrument implements section 1.3 of the pre-registration and
exists only as a second, independent implementation.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

from p4_mechanisms import cdf, quantile
from p5_mechanisms import ALPHA, tnorm
from p5b_instrument import BISECT_FACTOR, DTHETA_FACTOR, MAX_GRID
from p7_systems import fire_prob, silent_side

THETA_LO, THETA_HI = -0.5, 1.5
BISECT_STEPS = 30                  # theta_2 brackets span 2.0 -> 1.9e-9 resolution
AGGREGATORS = ("product", "godel", "lukasiewicz", "mean")
TNORMS = ("product", "godel", "lukasiewicz")
DTHETA_FACTOR_B = 0.002            # see P9-B1 registration


# ------------------------------------------------------------------ level sets
def agg_value(name: str, xs) -> float:
    xs = [float(x) for x in xs]
    if name == "mean":
        return sum(xs) / len(xs)
    return tnorm(name, xs)


def agg_levels(name: str, m: int, s: float):
    """Distinct per-stage drives over the alphabet {s, 1}. All four aggregators are symmetric,
    so the level depends only on j = number of failing channels."""
    return sorted({round(agg_value(name, [s] * j + [1.0] * (m - j)), 12) for j in range(m + 1)})


def largest_subunit_level(name: str, m: int, s: float):
    sub = [x for x in agg_levels(name, m, s) if x < 1.0 - 1e-12]
    return max(sub) if sub else None


def stage_configs_agg(name: str, k: int, m: int, s: float):
    lv = agg_levels(name, m, s)
    return sorted(set(itertools.combinations_with_replacement(lv, k)),
                  key=lambda d: (min(d), sum(d)), reverse=True)


# ------------------------------------------------------------------ part A
def predicted_beta_agg(kind: str, k: int, m: int, s: float, name: str,
                       alpha: float = ALPHA) -> float:
    L = largest_subunit_level(name, m, s)
    if L is None:
        return float("inf")
    phi = (1.0 - alpha) ** (1.0 / k)
    psi = alpha / (1.0 - alpha) ** ((k - 1.0) / k)      # same float expression as p7_systems
    return (quantile(phi, kind) - quantile(psi, kind)) / (1.0 - L)


def _thetas_for(gap: float):
    """Grid over the registered box [THETA_LO, THETA_HI] at the derived resolution dtheta=gap*factor."""
    span = THETA_HI - THETA_LO
    dtheta = DTHETA_FACTOR * gap
    n = int(math.ceil(span / dtheta)) + 1
    if n > MAX_GRID:
        return None, n, dtheta
    return np.linspace(THETA_LO, THETA_HI, n), n, dtheta


def pointwise_reduction_error(kind: str, beta: float, thetas, silent_cfgs, k: int, L: float,
                              alpha: float = ALPHA) -> float:
    """max over theta of |enumerated silent side - F(beta(1-th))^(k-1) F(beta(L-th))|."""
    best, _ = silent_side(kind, beta, thetas, silent_cfgs, alpha)
    closed = np.asarray(cdf(beta * (1.0 - thetas), kind), dtype=float) ** (k - 1) * \
        np.asarray(cdf(beta * (L - thetas), kind), dtype=float)
    return float(np.max(np.abs(best - closed)))


def critical_beta_agg(kind: str, k: int, m: int, s: float, name: str,
                      alpha: float = ALPHA) -> dict:
    cfgs = stage_configs_agg(name, k, m, s)
    silent_cfgs = [c for c in cfgs if min(c) < 1.0 - 1e-12]
    L = largest_subunit_level(name, m, s)
    pred = predicted_beta_agg(kind, k, m, s, name, alpha)
    base = {"kind": kind, "k": k, "m": m, "s": s, "agg": name, "L": L, "pred": pred,
            "n_configs": len(silent_cfgs), "levels": agg_levels(name, m, s)}
    if not silent_cfgs:
        return {**base, "beta": float("inf"), "measurable": True,
                "reason": "no failing configuration exists (s=1): nothing to silence"}
    gap = 1.0 - L
    thetas, n, dtheta = _thetas_for(gap)
    if thetas is None:
        return {**base, "beta": float("inf"), "measurable": False, "n_points": n,
                "reason": "NOT_MEASURABLE: grid cap"}
    lo, hi = 0.02, 400.0
    feas, _, _ = _window_feasible(kind, hi, thetas, silent_cfgs, k, alpha)
    if not bool(feas.any()):
        return {**base, "beta": float("inf"), "measurable": True, "n_points": n,
                "reason": "no window even at beta=400"}
    tol = max(BISECT_FACTOR * pred, 1e-6)
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if bool(_window_feasible(kind, mid, thetas, silent_cfgs, k, alpha)[0].any()):
            hi = mid
        else:
            lo = mid
    feas, silent, who = _window_feasible(kind, hi, thetas, silent_cfgs, k, alpha)
    cand = np.nonzero(feas)[0]
    i = int(cand[np.argmax(silent[cand])])
    red = pointwise_reduction_error(kind, hi, thetas, silent_cfgs, k, L)
    return {**base, "beta": float(hi), "measurable": True, "n_points": int(n),
            "rel_diff": abs(float(hi) - pred) / pred,
            "worst_stages": sum(1 for d in who[i] if d < 1.0 - 1e-12),
            "worst_level": min(who[i]), "reduction_error": red, "reason": "ok"}


def _window_feasible(kind, beta, thetas, silent_cfgs, k, alpha):
    """Returns the per-theta feasibility MASK (not a scalar) plus the silent side and who holds it."""
    silent, who = silent_side(kind, beta, thetas, silent_cfgs, alpha)
    fire = fire_prob(kind, beta, thetas, k)
    return (silent <= alpha) & (fire >= 1.0 - alpha), silent, who


# ------------------------------------------------------------------ part B: brute force
def _free_interval(kind, beta, th1, s1, s2, alpha):
    """Feasible theta_2 interval for each theta_1; returns the widest-slack point or None.

    Each of the three constraints is monotone in theta_2 because u2 and v2 both decrease there, so
    the bracketed bound is found by bisection on the predicate itself - the ratio reduction of
    section 1.3 is never used here, which is what makes this instrument independent of it.
    """
    u1 = np.asarray(cdf(beta * (1.0 - th1), kind), dtype=float)
    v1 = np.asarray(cdf(beta * (s1 - th1), kind), dtype=float)

    def bound(pred, keep_low):
        """last theta_2 with pred true (keep_low) / first theta_2 with pred true (not keep_low)."""
        lo = np.full(th1.shape, THETA_LO)
        hi = np.full(th1.shape, THETA_HI)
        for _ in range(BISECT_STEPS):
            mid = 0.5 * (lo + hi)
            ok = pred(mid)
            if keep_low:
                lo = np.where(ok, mid, lo)
                hi = np.where(ok, hi, mid)
            else:
                hi = np.where(ok, mid, hi)
                lo = np.where(ok, lo, mid)
        return lo if keep_low else hi

    def u2_of(t2):
        return np.asarray(cdf(beta * (1.0 - t2), kind), dtype=float)

    def v2_of(t2):
        return np.asarray(cdf(beta * (s2 - t2), kind), dtype=float)

    t_fire = bound(lambda t2: u1 * u2_of(t2) >= 1.0 - alpha, True)
    t_c = bound(lambda t2: v2_of(t2) * u1 <= alpha, False)
    t_a = bound(lambda t2: v1 * u2_of(t2) <= alpha, False)
    lo_b = np.maximum(t_a, t_c)
    if not bool((lo_b <= t_fire).any()):
        return None
    slack = t_fire - lo_b
    j = int(np.argmax(np.where(lo_b <= t_fire, slack, -np.inf)))
    th2 = float(0.5 * (lo_b[j] + t_fire[j]))
    u2 = float(u2_of(np.array([th2]))[0])
    v2 = float(v2_of(np.array([th2]))[0])
    P = float(u1[j] * u2)
    r1 = float(v1[j] / u1[j]) if u1[j] > 0 else float("inf")
    r2 = float(v2 / u2) if u2 > 0 else float("inf")
    return {"theta1": float(th1[j]), "theta2": th2, "P": P, "r1": r1, "r2": r2,
            "slack": float(slack[j]), "max_r": max(r1, r2), "alpha_over_P": alpha / P}


def critical_beta_free(kind, s1, s2, pred_lo: float, alpha: float = ALPHA) -> dict:
    """Smallest beta admitting a feasible (theta_1, theta_2)."""
    gap = 1.0 - max(s1, s2)
    if gap <= 0:
        return {"beta": float("inf"), "measurable": True, "reason": "both stages silent-free"}
    dtheta = DTHETA_FACTOR_B * gap
    n1 = int(math.ceil((THETA_HI - THETA_LO) / dtheta)) + 1
    if n1 > MAX_GRID:
        return {"beta": float("inf"), "measurable": False, "n_points": n1,
                "reason": "NOT_MEASURABLE: grid cap"}
    th1 = np.linspace(THETA_LO, THETA_HI, n1)
    tol = max(BISECT_FACTOR * pred_lo, 1e-6)
    lo, hi = 0.02, 400.0
    det = _free_interval(kind, hi, th1, s1, s2, alpha)
    if det is None:
        return {"beta": float("inf"), "measurable": True, "n_points": n1,
                "reason": "no window even at beta=400"}
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if _free_interval(kind, mid, th1, s1, s2, alpha) is not None:
            hi = mid
        else:
            lo = mid
    det = _free_interval(kind, hi, th1, s1, s2, alpha)
    return {"beta": float(hi), "measurable": True, "n_points": n1, "dtheta": dtheta,
            "reason": "ok", **det}


# ------------------------------------------------------------------ part B: fixed point
def _u_of_ratio(kind, beta, s_i, rho):
    """max F(beta(1-th)) subject to F(beta(s_i-th))/F(beta(1-th)) <= rho, theta in the box."""
    def r(th):
        u = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
        v = np.asarray(cdf(beta * (s_i - th), kind), dtype=float)
        return np.where(u > 0, v / np.maximum(u, 1e-300), np.inf)
    lo = np.full_like(rho, THETA_LO)
    hi = np.full_like(rho, THETA_HI)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        too_big = r(mid) > rho                  # raise theta to lower the ratio
        lo = np.where(too_big, mid, lo)
        hi = np.where(too_big, hi, mid)
    th = hi
    u = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
    return np.where(r(th) <= rho + 1e-15, u, 0.0), th


def critical_beta_free_fixedpoint(kind, s1, s2, pred_lo: float, alpha: float = ALPHA) -> dict:
    """P7-O2 as a fixed point: rho0 solves rho*Q(rho)=alpha, window exists iff Q(rho0) >= 1-alpha."""
    def P_at(beta):
        rho = np.array([1e-6])
        # rho*Q(rho) is strictly increasing in rho: bisect the root at alpha
        lo, hi = 1e-9, alpha / (1.0 - alpha)
        for _ in range(80):
            mid = np.array([0.5 * (lo + hi)])
            u1, _ = _u_of_ratio(kind, beta, s1, mid)
            u2, _ = _u_of_ratio(kind, beta, s2, mid)
            q = float(u1[0] * u2[0])
            if mid[0] * q > alpha:
                hi = mid[0]
            else:
                lo = mid[0]
        rho0 = 0.5 * (lo + hi)
        u1, t1 = _u_of_ratio(kind, beta, s1, np.array([rho0]))
        u2, t2 = _u_of_ratio(kind, beta, s2, np.array([rho0]))
        return float(u1[0] * u2[0]), float(rho0), float(t1[0]), float(t2[0])
    lo, hi = 0.02, 400.0
    p, *_ = P_at(hi)
    if p < 1.0 - alpha:
        return {"beta": float("inf"), "reason": "no window even at beta=400"}
    tol = max(BISECT_FACTOR * pred_lo, 1e-6)
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if P_at(mid)[0] >= 1.0 - alpha:
            hi = mid
        else:
            lo = mid
    p, rho0, t1, t2 = P_at(hi)
    return {"beta": float(hi), "P": p, "rho": rho0, "theta1": t1, "theta2": t2, "reason": "ok"}


def shared_beta_numeric(kind, s_hi, k: int, alpha: float = ALPHA) -> float:
    """Shared-threshold value for the heterogeneous pair: the binding stage is the one with the
    larger s, so the system reduces to the homogeneous one at s = max(s1, s2)."""
    cfgs = stage_configs_agg("product", k, 1, s_hi)
    silent = [c for c in cfgs if min(c) < 1.0 - 1e-12]
    thetas, n, _ = _thetas_for(1.0 - s_hi)
    lo, hi = 0.02, 400.0
    pred = predicted_beta_agg(kind, k, 1, s_hi, "product", alpha)
    if not bool(_window_feasible(kind, hi, thetas, silent, k, alpha)[0].any()):
        return float("inf")
    tol = max(BISECT_FACTOR * pred, 1e-6)
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if bool(_window_feasible(kind, mid, thetas, silent, k, alpha)[0].any()):
            hi = mid
        else:
            lo = mid
    return float(hi)
