"""Phase XIII close-out: convention offset (A), unattained supremum (B), k=4 freedom (C), joint fit (D).

Reuses the committed instruments: p6_systems.poisson_cdf_grid (log-space weights, no underflow),
p11_softband.beta_star_band / beta_star_free / random_control, p12_lattice.rho_smooth / exponent.
"""
from __future__ import annotations

from math import sqrt

import numpy as np

from p4_mechanisms import quantile
from p5_mechanisms import ALPHA
from p5b_instrument import DTHETA_FACTOR
from p6_systems import Z95, poisson_cdf_grid
import p11_softband as p11
import p12_lattice as p12

LAMBDAS = (30.0, 100.0, 400.0, 1600.0, 6400.0)
TAUS = (0.3, 0.55, 0.7)
K4_HETERO = [(0.3, 0.55, 0.7, 0.7), (0.3, 0.3, 0.55, 0.7), (0.3, 0.55, 0.55, 0.7)]
SEEDS_XIII = list(range(3000, 3010))
PRIOR_POOLS = [list(range(0, 10)), list(range(100, 110)), list(range(2000, 2020))]
N_DRAWS = 20_000
SUP = 0.5


def sf_grid(lam: float):
    """sf[m] = P(N >= m) for N ~ Pois(lam), from the committed log-space CDF grid."""
    hi = int(lam + 12.0 * sqrt(max(lam, 1.0)) + 60.0)
    cdf = np.asarray(poisson_cdf_grid(lam, hi), dtype=float)
    return np.concatenate(([1.0], 1.0 - cdf[:-1])), cdf


def m_ge(lam: float, alpha: float = ALPHA) -> int:
    sf, _ = sf_grid(lam)
    idx = int(np.argmax(sf <= alpha))
    return int(idx) if bool(sf[idx] <= alpha) else -1


def q_cont(lam: float, p: float = 1.0 - ALPHA) -> float:
    _, cdf = sf_grid(lam)
    idx = int(np.argmax(cdf >= p))
    prev = float(cdf[idx - 1]) if idx > 0 else 0.0
    frac = (p - prev) / max(float(cdf[idx]) - prev, 1e-300)
    return float(idx - 1.0 + frac)


def offsets(lam: float):
    base = lam + sqrt(lam) * Z95
    return float(m_ge(lam) - base), float(q_cont(lam) - base)


# ------------------------------------------------------------------ B
def levels_gap(J: int):
    """Reachable set whose band supremum SUP is NOT attained for finite J."""
    return np.array(sorted({0.0, 1.0} | {round(SUP - 0.5 / (j + 1.0), 12) for j in range(J + 1)}))


def attained_lo(J: int) -> float:
    lv = levels_gap(J)
    in_band = lv[lv <= SUP + 1e-12]
    return float(in_band[-1])


def feasible_at(kind: str, beta: float, lo: float, k: int, alpha: float = ALPHA) -> bool:
    dtheta = DTHETA_FACTOR * (1.0 - lo)
    n = int(np.ceil(2.0 / dtheta)) + 1
    thetas = np.linspace(p11.THETA_LO, p11.THETA_HI, n)
    f = np.asarray(p11.__dict__["cdf"](beta * (1.0 - thetas), kind), dtype=float)
    silent = np.asarray(p11.__dict__["cdf"](beta * (lo - thetas), kind), dtype=float) * f ** (k - 1)
    return bool(np.any((f ** k >= 1.0 - alpha) & (silent <= alpha)))


# ------------------------------------------------------------------ D
def rms_error(e0: float, e1: float, s_grid, lam) -> float:
    vals = [p12.rho_smooth(e0, s, e1) for s in s_grid]
    if any(v is None for v in vals):
        return float("inf")
    rel = np.array([v / lam[str(s)] - 1.0 for v, s in zip(vals, s_grid)])
    return float(np.sqrt(np.mean(rel ** 2)))


def fit_joint(s_grid, lam, e0_step=0.02, e1_step=10.0, levels=3, shrink=10.0):
    """Coarse grid then nested refinement (P13-A2); returns (e0, e1, rms, meta)."""
    e0s = np.arange(-2.0, 3.0 + 1e-9, e0_step)
    e1s = np.arange(0.0, 300.0 + 1e-9, e1_step)
    best = (None, None, float("inf"))
    for e0 in e0s:
        for e1 in e1s:
            v = rms_error(e0, e1, s_grid, lam)
            if v < best[2]:
                best = (float(e0), float(e1), v)
    trace = [list(best)]
    for _ in range(levels):
        e0_step /= shrink
        e1_step /= shrink
        b0, b1, bv = best
        for i in range(-2, 3):
            for j in range(-2, 3):
                v = rms_error(b0 + i * e0_step, max(0.0, b1 + j * e1_step), s_grid, lam)
                if v < bv:
                    bv = v
                    best = (b0 + i * e0_step, max(0.0, b1 + j * e1_step), bv)
        trace.append(list(best))
    flat = {"d_e0": abs(rms_error(best[0] + e0_step, best[1], s_grid, lam) - best[2]),
            "d_e1": abs(rms_error(best[0], best[1] + e1_step, s_grid, lam) - best[2]),
            "terminal_steps": [e0_step, e1_step], "n_coarse": len(e0s) * len(e1s),
            "trace": trace}
    return best[0], best[1], best[2], flat
