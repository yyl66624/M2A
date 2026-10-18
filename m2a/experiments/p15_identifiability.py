"""Phase XV: how much INFORMATION the joint (e0, e1) fit actually carries, instead of a finer grid.

The tie floor is the committed search instrument's own one-step change (P15-A3: taken as stored, never
re-measured), the e1 identified set is bracketed on the committed search box rather than on one grid step
(P15-A4 withdrew the endpoint-only search because it let the instrument's own domain satisfy the criterion),
and the scientific check is a different functional - the large-end chord exponent at P8-1's tolerance verbatim.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np

import p12_lattice as p12
import p13_closeout as p13

HERE = pathlib.Path(__file__).resolve().parent
E0_GRID = np.arange(-2.0, 3.0 + 1e-9, 0.001)          # the committed single-parameter grid
E1_GRID = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 100.0, 300.0)
STEP_E0, STEP_E1 = 2e-05, 0.01                        # committed terminal steps of fit_joint
EXP_TOL = 0.05                                        # Phase VIII P8-1, reused verbatim
ANCHOR_TOL = 1e-12
BISECT_TOL_E1 = 1e-6
BIG_FROM = 100.0                                      # committed large-end subset cut


def committed():
    p13j = json.loads((HERE / "phase13_results.json").read_text(encoding="utf-8"))
    p8j = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    s_grid = p8j["s_grid"]
    lam = {k: v["lambda_hi"] for k, v in p8j["rows"].items()}
    d = p13j["D"]
    return {"p13": p13j, "s_grid": s_grid, "lam": lam, "joint_rms": d["joint"]["rms_full_curve"],
            "single_rms": d["single"]["rms_full_curve"], "single_e0": d["single"]["e0"],
            "joint_e0": d["joint"]["e0"],
            "joint_e1": d["joint"]["e1"], "d_e0": d["joint"]["flatness"]["d_e0"],
            "d_e1": d["joint"]["flatness"]["d_e1"], "exp_joint_big": d["exponent_joint_big"],
            "p8_slope": p8j["P8_1_slope"]}


def tie_floor(c) -> float:
    return max(c["d_e0"], c["d_e1"])


def profile_e0(e1: float, s_grid, lam):
    """min over the committed e0 grid of the full-curve RMS, holding e1 fixed."""
    vals = [p13.rms_error(float(e), e1, s_grid, lam) for e in E0_GRID]
    j = int(np.argmin(vals))
    return float(vals[j]), float(E0_GRID[j])


def e1_identified_set(c, T):
    """sup{e1 : profile(e1) - joint_rms <= T}, bracketed on the committed search box [0, 300] (P15-A4).

    Returns (e1_max, unbounded_in_box, first_violator, profile_at_first_violator).
    """
    joint = c["joint_rms"]
    s_grid, lam = c["s_grid"], c["lam"]
    prev = 0.0
    violator = None
    for e1 in E1_GRID:
        if e1 == 0.0:
            continue
        v, _ = profile_e0(e1, s_grid, lam)
        if v - joint > T:
            violator, viol_val = e1, v
            break
        prev = e1
    if violator is None:
        return E1_GRID[-1], True, None, None
    lo, hi = prev, violator
    while hi - lo > BISECT_TOL_E1:
        mid = 0.5 * (lo + hi)
        v, _ = profile_e0(mid, s_grid, lam)
        if v - joint <= T:
            lo = mid
        else:
            hi = mid
    return lo, False, float(violator), float(viol_val)


def exponent_at(e1: float, s_grid, lam):
    best_rms, e0 = profile_e0(e1, s_grid, lam)
    big = p12.subset(s_grid, lam, BIG_FROM)
    return float(p12.exponent(e0, big, e1)), e0, best_rms


def jacobian_diagnostics(c):
    """d rho / d(e0, e1) over the committed s grid, Richardson-differenced (P10-A5 convention).

    Reported only: correlation and condition number carry no threshold this round.
    """
    s_grid, lam = c["s_grid"], c["lam"]
    e0, e1 = c["joint_e0"], c["joint_e1"]

    def rho_matrix(e0v, e1v):
        out = []
        for s in s_grid:
            v = p12.rho_smooth(e0v, s, e1v)
            out.append(np.nan if v is None else v)
        return np.array(out, dtype=float)

    def deriv(step, axis):
        def once(h):
            a = [e0, e1]
            b = [e0, e1]
            a[axis] += h
            b[axis] -= h
            return (rho_matrix(*a) - rho_matrix(*b)) / (2.0 * h)
        return (4.0 * once(step / 2.0) - once(step)) / 3.0

    j0, j1 = deriv(1e-4, 0), deriv(1e-4, 1)
    good = np.isfinite(j0) & np.isfinite(j1)
    j0, j1 = j0[good], j1[good]
    n0, n1 = float(np.linalg.norm(j0)), float(np.linalg.norm(j1))
    corr = float(j0 @ j1 / (n0 * n1)) if n0 > 0 and n1 > 0 else float("nan")
    gram = np.array([[j0 @ j0, j0 @ j1], [j1 @ j0, j1 @ j1]])
    ev = np.linalg.eigvalsh(gram)[::-1]
    kappa = float(ev[0] / ev[-1]) if ev[-1] > 0 else float("inf")
    return {"corr": corr, "kappa": kappa, "eigs": [float(v) for v in ev],
            "norms": [n0, n1], "n_points": int(good.sum())}
