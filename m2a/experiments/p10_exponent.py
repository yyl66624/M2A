"""Phase X: local-slope closed form for the additive-quantile smoothing family, and the aliasing test.

No sampling. (star) is  Delta*R^2 - B(s)*R - e0 - e1/R = 0  with R = sqrt(rho*). For e1 != 0 the left
side is NOT monotone (P10-A1), so the instrument takes the LARGEST positive root - that is where
feasibility flips - by bracketing from above. The analytic local slope (diamond) is verified against
a central difference of the same root, and against the committed Phase VIII readings.
"""
from __future__ import annotations

from math import log, sqrt

import numpy as np

from p6_systems import Z95, loglog_slope
from p8_smooth import C1

# copied verbatim from phase8_results.json (s_grid, lambda_big_cut = 100.0)
S_GRID = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9)
BIG_CUT = 100.0
BIG = (0.7, 0.75, 0.8, 0.85, 0.9)
NEST_A = (0.8, 0.85, 0.9)
NEST_B = (0.85, 0.9)
E0_PHASE8 = 2.0 * C1


def B(s: float) -> float:
    return Z95 * (1.0 + sqrt(s))


def Bs(s: float) -> float:
    """dB/ds."""
    return Z95 / (2.0 * sqrt(s))


def _f(R: float, s: float, e0: float, e1: float) -> float:
    delta = 1.0 - s
    return delta * R * R - B(s) * R - e0 - (e1 / R if R > 0.0 else 0.0)


def _fp(R: float, s: float, e1: float) -> float:
    return 2.0 * (1.0 - s) * R - B(s) + (e1 / (R * R) if e1 != 0.0 else 0.0)


def root_R(s: float, e0: float, e1: float) -> float:
    """Onset root of (star): the smallest R where the family becomes feasible (f >= 0).

    Registered domain is e1 >= 0 (P10-A1/P10-A4): (star) times R is the cubic
    g(R) = Delta R^3 - B R^2 - e0 R - e1 with g(0) = -e1 <= 0 and g' having a single positive zero,
    so g decreases then increases and has exactly one positive root - the threshold. For e1 < 0 the
    cubic is positive at R -> 0+, i.e. the expansion claims feasibility at arbitrarily small rates,
    which is outside the asymptotic regime; that region is excluded rather than silently traversed.
    """
    delta = 1.0 - s
    if delta <= 0.0:
        return float("inf")
    if _f(1e-9, s, e0, e1) >= 0.0:
        return 0.0                       # degenerate / outside the registered domain
    hi = max(B(s) / delta, 1.0) + (abs(e0) + abs(e1) + 1.0) / delta
    for _ in range(400):
        if _f(hi, s, e0, e1) >= 0.0:
            break
        hi *= 2.0
    else:
        return float("inf")
    lo = 1e-9
    for _ in range(400):                 # geometric march to the first sign change
        mid = 0.5 * (lo + hi)
        if _f(mid, s, e0, e1) < 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-16 * max(hi, 1.0):
            break
    return 0.5 * (lo + hi)


def rho(s: float, e0: float, e1: float) -> float:
    R = root_R(s, e0, e1)
    return R * R


def residual(s: float, e0: float, e1: float) -> float:
    return abs(_f(root_R(s, e0, e1), s, e0, e1))


def local_slope(s: float, e0: float, e1: float) -> float:
    """(diamond) d ln rho / d ln Delta along the smoothing family."""
    delta, R = 1.0 - s, root_R(s, e0, e1)
    if not (R > 0.0) or R == float("inf"):
        return float("nan")
    return -2.0 * delta * (R + Bs(s)) / (B(s) + 2.0 * e0 / R + 3.0 * e1 / (R * R))


def local_slope_simplified(s: float, e0: float) -> float:
    """The e1 = 0 corollary of section 1.2, written as the ratio of the two competing corrections."""
    R = root_R(s, e0, 0.0)
    return -2.0 * (1.0 + Bs(s) / R) / (1.0 + e0 / ((1.0 - s) * R * R))


def _num_slope_once(s: float, e0: float, e1: float, rel: float) -> float:
    d = 1.0 - s
    rp, rm = rho(1.0 - d * (1.0 + rel), e0, e1), rho(1.0 - d * (1.0 - rel), e0, e1)
    return (log(rp) - log(rm)) / (log(d * (1.0 + rel)) - log(d * (1.0 - rel)))


def num_slope(s: float, e0: float, e1: float, rel: float = 1e-4) -> float:
    """Richardson-extrapolated central difference (P10-A5): the raw O(rel^2) truncation at rel=1e-4
    leaves ~1e-8 disagreement with the analytic slope, which is the size of the X-1 tolerance itself."""
    return (4.0 * _num_slope_once(s, e0, e1, rel / 2.0) - _num_slope_once(s, e0, e1, rel)) / 3.0


def chord(ss, e0: float, e1: float) -> float:
    gaps = [1.0 - s for s in ss]
    vals = [rho(s, e0, e1) for s in ss]
    return loglog_slope(gaps, vals)


def deviation(e0: float, e1: float, grid=S_GRID) -> float:
    """max |local slope + 2| over the grid; non-finite readings score 1e9 so the search cannot
    exploit a coefficient pair where the family stops being measurable."""
    vals = [abs(local_slope(s, e0, e1) + 2.0) for s in grid]
    vals = [v if np.isfinite(v) else 1e9 for v in vals]
    return max(vals)


# ------------------------------------------------------------------ X-4 nested search
E0_COARSE_STEP, E1_COARSE_STEP = 2.0, 40.0
REFINE_LEVELS, REFINE_SHRINK, REFINE_HALF = 3, 10.0, 2


def minimax_deviation(e0_lo=0.0, e0_hi=40.0, e1_lo=0.0, e1_hi=800.0, grid=BIG):
    """Coarse grid then REFINE_LEVELS nested neighbourhood contraction (P10-A2), objective max
    |local slope + 2| over `grid` = the same working interval P8-1 fitted (P10-A6)."""
    best = (None, None, float("inf"))
    n_coarse = 0
    e0 = e0_lo
    while e0 <= e0_hi + 1e-9:
        e1 = e1_lo
        while e1 <= e1_hi + 1e-9:
            v = deviation(e0, e1, grid)
            n_coarse += 1
            if v < best[2]:
                best = (e0, e1, v)
            e1 += E1_COARSE_STEP
        e0 += E0_COARSE_STEP
    trace = [list(best) + [n_coarse]]
    step0, step1 = E0_COARSE_STEP, E1_COARSE_STEP
    for _ in range(REFINE_LEVELS):
        step0 /= REFINE_SHRINK
        step1 /= REFINE_SHRINK
        b0, b1, bv = best
        for i in range(-REFINE_HALF, REFINE_HALF + 1):
            for j in range(-REFINE_HALF, REFINE_HALF + 1):
                v = deviation(b0 + i * step0, b1 + j * step1, grid)
                if v < bv:
                    bv = v
                    best = (b0 + i * step0, b1 + j * step1, bv)
        trace.append([best[0], best[1], bv, (2 * REFINE_HALF + 1) ** 2])
    return best[0], best[1], best[2], {"trace": trace, "terminal_steps": [step0, step1],
                                       "n_coarse_evals": n_coarse}


# ------------------------------------------------------------------ X-5 aliasing
def tune_e0_for_chord(target: float, ss=BIG, e1: float = 0.0, lo=0.0, hi=200.0):
    """One knob only (P10-A3): bisect e0 so that the chord exponent over `ss` equals `target`."""
    f = lambda x: chord(ss, x, e1) - target
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
