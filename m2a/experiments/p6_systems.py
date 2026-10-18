"""Phase VI: the gap threshold law in three structurally different synthetic systems.

S1 additive scalar unit (the Phase IV/V reference), S2 Poisson counting system, S3 conjunctive
cascade of noisy per-channel decisions. Everything here is exact arithmetic -- no sampling.
"""
from __future__ import annotations

from math import ceil, exp, lgamma, log, sqrt

import numpy as np

from p4_mechanisms import cdf, quantile
from p5_mechanisms import ALPHA, channels
from p5b_instrument import BISECT_FACTOR, DTHETA_FACTOR, MAX_GRID

Z95 = 1.6448536269514722          # q_{0.95} of the standard normal


# ---------------------------------------------------------------- S2: exact Poisson tail
def poisson_cdf_grid(lam: float, m_max: int) -> np.ndarray:
    """cdf[k] = P(N <= k) for N ~ Poisson(lam), k = 0..m_max.

    P6-A4: the naive recurrence starts at term = exp(-lam), which underflows to 0 for lam > ~745
    and silently turns the whole tail into zeros. The pmf is therefore built in log space with the
    maximum term factored out, and normalised over a window wide enough (lam + 12*sqrt(lam)) that
    the omitted mass is below 1e-15.
    """
    if lam <= 0.0:
        return np.ones(m_max + 1)
    K = int(max(m_max, ceil(lam + 12.0 * sqrt(max(lam, 1.0)) + 30.0)))
    logt = np.array([k * log(lam) - lgamma(k + 1) for k in range(K + 1)])
    w = np.exp(logt - logt.max())
    cdf_all = np.cumsum(w) / w.sum()
    return cdf_all[:m_max + 1]


def poisson_sf(m: int, lam: float) -> float:
    """P(N >= m) for N ~ Poisson(lam); log-space direct sum, used for point checks."""
    if m <= 0:
        return 1.0
    if lam <= 0.0:
        return 0.0
    terms = [k * log(lam) - lgamma(k + 1) for k in range(m)]
    shift = max(terms)
    total = sum(exp(t - shift) for t in terms) * exp(shift - lam)
    return float(min(1.0, max(0.0, 1.0 - total)))


def _sf_from_cdf(cdf_vals: np.ndarray) -> np.ndarray:
    """sf[m] = P(N >= m) = 1 - P(N <= m-1); sf[0] = 1 by definition."""
    sf = np.ones_like(cdf_vals)
    sf[1:] = 1.0 - cdf_vals[:-1]
    return np.clip(sf, 0.0, 1.0)


def s2_window_exists(rho: float, drive_lo: float, drive_hi: float, tau: float = 1.0,
                     alpha: float = ALPHA):
    a, b = rho * tau * drive_lo, rho * tau * drive_hi
    if b <= a:
        return False, None
    m_max = int(ceil(b + 8.0 * sqrt(max(b, 1.0)) + 20.0))
    sf_lo = _sf_from_cdf(poisson_cdf_grid(a, m_max))
    sf_hi = _sf_from_cdf(poisson_cdf_grid(b, m_max))
    ms = np.arange(m_max + 1)
    ok = (sf_lo <= alpha) & (sf_hi >= 1.0 - alpha) & (ms >= 1)
    if not ok.any():
        return False, None
    return True, int(ms[ok][0])


def s2_critical_rho(drive_lo: float, drive_hi: float, tau: float = 1.0,
                    alpha: float = ALPHA, lo=1e-3, hi=2000.0) -> dict:
    gap = drive_hi - drive_lo
    if gap <= 0.0:
        return {"rho": float("inf"), "measurable": True, "reason": "zero gap"}
    pred = Z95 ** 2 * (sqrt(drive_lo) + sqrt(drive_hi)) ** 2 / gap ** 2
    tol = max(BISECT_FACTOR * pred, 2e-4)
    ok, _ = s2_window_exists(hi, drive_lo, drive_hi, tau, alpha)
    if not ok:
        return {"rho": float("inf"), "measurable": True, "pred": pred,
                "reason": "no threshold even at rho=2000"}
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if s2_window_exists(mid, drive_lo, drive_hi, tau, alpha)[0]:
            hi = mid
        else:
            lo = mid
    ok, m_star = s2_window_exists(hi, drive_lo, drive_hi, tau, alpha)
    return {"rho": float(hi), "measurable": True, "pred": pred, "m_star": m_star, "reason": "ok"}


# ---------------------------------------------------------------- S3: cascade of noisy decisions
def s3_window_exists(kind, beta, silent_xs, thetas, alpha=ALPHA) -> bool:
    """Vectorised: channels sharing a level are folded into a power, so the cost is one cdf per level."""
    counts = {}
    for x in silent_xs:
        counts[round(float(x), 12)] = counts.get(round(float(x), 12), 0) + 1
    silent = np.ones_like(thetas)
    for level, cnt in counts.items():
        silent = silent * cdf(beta * (level - thetas), kind) ** cnt
    fire = cdf(beta * (1.0 - thetas), kind) ** len(silent_xs)
    return bool(np.any((silent <= alpha) & (fire >= 1.0 - alpha)))


def s3_prediction(kind: str, silent_xs, alpha: float = ALPHA) -> dict:
    """P6-A1 general form. k = channels still full in the silent config, s' = degraded level."""
    n = len(silent_xs)
    full = [x for x in silent_xs if x >= 1.0 - 1e-12]
    deg = [x for x in silent_xs if x < 1.0 - 1e-12]
    k, m = len(full), len(deg)
    s_deg = max(deg) if deg else 1.0
    gap = (1.0 - s_deg) if m else 1.0
    a_f = 1.0 - (1.0 - alpha) ** (1.0 / n)
    if m == 0:
        a_s = alpha
    else:
        a_s = (alpha / (1.0 - a_f) ** k) ** (1.0 / m)
    pred = (quantile(1.0 - a_f, kind) - quantile(a_s, kind)) / gap
    return {"pred": float(pred), "n": n, "k_full": k, "m_degraded": m,
            "alpha_f": a_f, "alpha_s": a_s, "gap": float(gap)}


def s3_critical_beta(kind, n, pattern, s, alpha=ALPHA) -> dict:
    silent_xs = channels(n, pattern, s)
    spec = s3_prediction(kind, silent_xs, alpha)
    gap = spec["gap"]
    dtheta = DTHETA_FACTOR * max(gap, 1e-6)
    n_pts = int(ceil(2.0 / dtheta)) + 1
    if n_pts > MAX_GRID or not np.isfinite(spec["pred"]):
        return {"beta": float("inf"), "measurable": False, **spec, "n_points": n_pts}
    thetas = np.linspace(-0.5, 1.5, n_pts)
    lo, hi = 0.02, 400.0
    if not s3_window_exists(kind, hi, silent_xs, thetas, alpha):
        return {"beta": float("inf"), "measurable": True, "n_points": n_pts,
                "reason": "no window even at beta=400", **spec}
    tol = max(BISECT_FACTOR * spec["pred"], 1e-4)
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if s3_window_exists(kind, mid, silent_xs, thetas, alpha):
            hi = mid
        else:
            lo = mid
    return {"beta": float(hi), "measurable": True, "n_points": n_pts, "reason": "ok", **spec}


# ---------------------------------------------------------------- slope fitting (no sampling)
def loglog_slope(xs, ys):
    x = np.log(np.asarray(xs, dtype=float))
    y = np.log(np.asarray(ys, dtype=float))
    return float(np.polyfit(x, y, 1)[0])
