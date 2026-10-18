"""Phase XIV: does the unattained-supremum convergence follow the exact rate law delta(J) = 1/(J+2)?

Every band level shares one theta grid (P14-A1) so the discretisation bias is common-mode, the beta
bisection is tightened to 1e-9 absolute, and the criterion's tolerance comes from the instrument's own
grid-refinement shift instead of a hand-picked number. P14-A4 splits the anchor into a same-instrument
reproduction and a cross-instrument disclosure.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np


from p4_mechanisms import cdf
from p5_mechanisms import ALPHA
from p5b_instrument import BISECT_FACTOR
import p11_softband as p11
import p13_closeout as p13

THETA_LO, THETA_HI = -0.5, 1.5
JS = (10, 20, 40, 100, 200, 400, 800)
KINDS = ("logistic", "probit", "gumbel")
N_COARSE, N_FINE = 20001, 40001
BISECT_TOL = 1e-9
K_ANCHOR = 2
SUP = p13.SUP
BISECT_LO, BISECT_HI = 0.02, 400.0


@lru_cache(maxsize=4)
def thetas(n: int):
    """Same node ordering as the committed p11 instrument, so a grid size is the only degree of freedom."""
    return np.linspace(THETA_HI, THETA_LO, n)


def feasible(kind: str, beta: float, lo: float, k: int, n: int, alpha: float = ALPHA) -> bool:
    th = thetas(n)
    f = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
    silent = np.asarray(cdf(beta * (lo - th), kind), dtype=float) * f ** (k - 1)
    return bool(np.any((f ** k >= 1.0 - alpha) & (silent <= alpha)))


def bracket(kind: str, k: int, lo: float, n: int, tol: float = BISECT_TOL):
    """Final bisection bracket (lo_b, hi_b, tol); the instrument's own resolution floor is tol."""
    lo_b, hi_b = BISECT_LO, BISECT_HI
    if not feasible(kind, hi_b, lo, k, n):
        return lo_b, float("inf"), tol
    while hi_b - lo_b > tol:
        mid = 0.5 * (lo_b + hi_b)
        if feasible(kind, mid, lo, k, n):
            hi_b = mid
        else:
            lo_b = mid
    return lo_b, hi_b, tol


def beta_star(kind: str, k: int, lo: float, n: int, tol: float = BISECT_TOL) -> float:
    return bracket(kind, k, lo, n, tol)[1]


def p13_bisect_tol(kind: str, lo: float = SUP, k: int = K_ANCHOR) -> float:
    """The bisection floor the committed Phase XIII reading was taken at (P14-A4(ii))."""
    return max(BISECT_FACTOR * p11.predicted(kind, k, lo), 1e-6)


def level(J: int) -> float:
    return p13.attained_lo(J)


def level_closed_form(J: int) -> float:
    return SUP - 0.5 / (J + 1.0)


def exact_delta(J: int) -> float:
    return 1.0 / (J + 2.0)


def algebra_delta(J: int) -> float:
    """delta implied by the closed form beta* = kappa/(1-lo); kappa cancels, so this is pure algebra."""
    return 1.0 - (1.0 - SUP) / (1.0 - level(J))


@lru_cache(maxsize=8)
def closures(kind: str, k: int = K_ANCHOR) -> dict:
    """Closure-level readings only, so the gate can wire the instrument without touching a J cell."""
    return {"coarse": beta_star(kind, k, SUP, N_COARSE), "fine": beta_star(kind, k, SUP, N_FINE),
            "p13": p11.beta_star_band(kind, k, SUP)["beta"], "pred": p11.predicted(kind, k, SUP),
            "p13_bisect_tol": p13_bisect_tol(kind, SUP, k)}


def grid_pair(kind: str, k: int = K_ANCHOR) -> dict:
    cl_c, cl_f = closures(kind, k)["coarse"], closures(kind, k)["fine"]
    rows = []
    for J in JS:
        lo = level(J)
        b_c = beta_star(kind, k, lo, N_COARSE)
        b_f = beta_star(kind, k, lo, N_FINE)
        d_c = (cl_c - b_c) / cl_c
        d_f = (cl_f - b_f) / cl_f
        rows.append({"J": int(J), "lo": float(lo), "beta_J_coarse": float(b_c),
                     "beta_J_fine": float(b_f), "closure_coarse": float(cl_c),
                     "closure_fine": float(cl_f), "delta_coarse": float(d_c),
                     "delta_fine": float(d_f), "delta_exact": float(exact_delta(J)),
                     "shift": float(abs(d_c - d_f)),
                     "abs_err_coarse": float(abs(d_c - exact_delta(J))),
                     "abs_err_fine": float(abs(d_f - exact_delta(J)))})
    c = closures(kind, k)
    return {"kind": kind, "k": int(k), "n_coarse": N_COARSE, "n_fine": N_FINE,
            "closure_coarse": float(cl_c), "closure_fine": float(cl_f),
            "closure_p13": float(c["p13"]), "closure_pred": float(c["pred"]),
            "p13_bisect_tol": float(c["p13_bisect_tol"]), "rows": rows}
