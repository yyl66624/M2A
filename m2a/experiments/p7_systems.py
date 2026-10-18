"""Phase VII: the mixed aggregation system S4(k,m) -- k cascaded stages, m conjunctive channels each.

The instrument enumerates every input configuration over the alphabet {s, 1} (s = 0 gives the hard
binary case) and takes the MAXIMUM failing-configuration probability as the silent side. The
prediction (PHASE7_PREREGISTRATION.md as amended by P7-A1) is derived against that same enumeration,
so V7-1 is a real test rather than a restatement. No sampling anywhere in this module.

Enumeration is folded into drive-COUNT vectors: p(config) = prod_d F(beta*(d-theta))^{count_d},
so the cost per beta is (m+1) CDF evaluations on the theta grid, not one per configuration.
"""
from __future__ import annotations

import itertools
import math
from collections import Counter

import numpy as np

from p4_mechanisms import cdf, quantile
from p5_mechanisms import ALPHA
from p5b_instrument import BISECT_FACTOR, DTHETA_FACTOR, MAX_GRID


def stage_configs(k: int, m: int, s: float):
    """Distinct per-stage drive multisets (as sorted tuples) reachable over the alphabet {s, 1}."""
    per_stage = sorted({round(math.prod(t), 12) for t in itertools.product([s, 1.0], repeat=m)})
    out = set()
    for combo in itertools.combinations_with_replacement(per_stage, k):
        out.add(tuple(combo))
    return sorted(out, key=lambda d: (min(d), sum(d)), reverse=True)


def drive_counts(configs):
    """(levels, count_matrix) -- count_matrix[j, i] = how many stages of config j sit at level i."""
    levels = sorted({d for cfg in configs for d in cfg}, reverse=True)
    idx = {lv: i for i, lv in enumerate(levels)}
    mat = np.zeros((len(configs), len(levels)), dtype=int)
    for j, cfg in enumerate(configs):
        for lv, cnt in Counter(cfg).items():
            mat[j, idx[round(lv, 12)]] = cnt
    return levels, mat


def _log_probs(F_by_level, mat):
    """log p(config) per theta = sum_i count[j,i] * log F_i(theta)."""
    with np.errstate(divide="ignore"):
        logs = np.log(np.clip(F_by_level, 1e-300, 1.0))         # (n_levels, n_theta)
    return mat.astype(float) @ logs                              # (n_cfg, n_theta)


def silent_side(kind, beta, thetas, configs, alpha=ALPHA):
    levels, mat = drive_counts(configs)
    F_by_level = np.vstack([np.asarray(cdf(beta * (lv - thetas), kind), dtype=float) for lv in levels])
    logp = _log_probs(F_by_level, mat)
    best = np.exp(logp.max(axis=0))
    arg = np.argmax(logp, axis=0)
    who = [configs[int(a)] for a in arg]
    return best, who


def fire_prob(kind, beta, thetas, k):
    return np.asarray(cdf(beta * (1.0 - thetas), kind), dtype=float) ** k


def predicted_beta(kind: str, k: int, s: float, alpha: float = ALPHA) -> float:
    """P7-A1: beta* = (q_phi - q_psi)/(1 - s), phi = (1-alpha)^{1/k}, psi = alpha/(1-alpha)^{(k-1)/k}."""
    phi = (1.0 - alpha) ** (1.0 / k)
    psi = alpha / (1.0 - alpha) ** ((k - 1.0) / k)
    gap = 1.0 if s >= 1.0 else (1.0 - s)
    return (quantile(phi, kind) - quantile(psi, kind)) / gap


def predicted_beta_binding_config(kind: str, k: int, s: float, r: int, alpha: float = ALPHA) -> float:
    """The same derivation but forcing the silent side to be the config with exactly r failing stages.

    p_silent = F(u)^{k-r} F(v)^{r} <= alpha, with F(u) pinned at its firing boundary phi, gives
    F(v) <= (alpha / phi^{k-r})^{1/r}.  r = 1 is the binding (worst) case; r = k-1 is what Phase VI's
    S3 actually measured -- the exponent 1/r is what makes the two differ (P7-A2).
    """
    phi = (1.0 - alpha) ** (1.0 / k)
    psi = (alpha / phi ** (k - r)) ** (1.0 / r)
    gap = 1.0 if s >= 1.0 else (1.0 - s)
    return (quantile(phi, kind) - quantile(psi, kind)) / gap


def window_feasible(kind, beta, thetas, silent_cfgs, k, alpha=ALPHA):
    silent, who = silent_side(kind, beta, thetas, silent_cfgs, alpha)
    return (silent <= alpha) & (fire_prob(kind, beta, thetas, k) >= 1.0 - alpha), silent, who


def critical_beta_s4(kind: str, k: int, m: int, s: float, alpha: float = ALPHA) -> dict:
    all_cfgs = stage_configs(k, m, s)
    silent_cfgs = [c for c in all_cfgs if min(c) < 1.0 - 1e-12]
    pred = predicted_beta(kind, k, s, alpha)
    base = {"kind": kind, "k": k, "m": m, "s": s, "pred": pred,
            "n_configs": len(silent_cfgs), "n_levels": len({d for c in all_cfgs for d in c})}
    if not silent_cfgs:
        return {**base, "beta": float("inf"), "measurable": True,
                "reason": "no failing configuration exists (s=1): nothing to silence"}
    gap = 1.0 if s >= 1.0 else (1.0 - s)
    dtheta = DTHETA_FACTOR * gap
    n_pts = int(math.ceil(2.0 / dtheta)) + 1
    if n_pts > MAX_GRID:
        return {**base, "beta": float("inf"), "measurable": False, "n_points": n_pts,
                "reason": "NOT_MEASURABLE: grid cap"}
    thetas = np.linspace(-0.5, 1.5, n_pts)
    lo, hi = 0.02, 400.0
    feas, _, _ = window_feasible(kind, hi, thetas, silent_cfgs, k, alpha)
    if not feas.any():
        return {**base, "beta": float("inf"), "measurable": True, "n_points": n_pts,
                "reason": "no window even at beta=400", "n_grid": n_pts}
    tol = max(BISECT_FACTOR * pred, 1e-4)
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        f, _, _ = window_feasible(kind, mid, thetas, silent_cfgs, k, alpha)
        if f.any():
            hi = mid
        else:
            lo = mid
    feas, silent, who = window_feasible(kind, hi, thetas, silent_cfgs, k, alpha)
    cand = np.nonzero(feas)[0]
    i = int(cand[np.argmax(silent[cand])])
    cfg = who[i]
    return {**base, "beta": float(hi), "measurable": True, "abs_diff": abs(float(hi) - pred),
            "n_points": n_pts, "worst_silent_drives": list(cfg),
            "worst_silent_stages": sum(1 for d in cfg if d < 1.0 - 1e-12), "reason": "ok"}
