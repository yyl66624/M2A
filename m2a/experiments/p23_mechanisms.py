"""Phase XXIII (AO measurement) design instruments: exact separability gap and its finite-sample estimator.

Pure module. The exact measure comes from `ao_opp`; this file adds only the signed gap
G = 1 - I - Z and the multinomial estimator. No scientific criterion is evaluated here.
"""
from __future__ import annotations

import numpy as np

import ao_opp as ao

THETAS = (0.1, 0.25, 0.5, 0.75, 0.9)
THETA_STAR = 0.1                 # argmax of the exact gap over THETAS, fixed before the run
MULTI = ("two_windows", "adjacent")
SINGLE = ("gate_upper", "gate_upper_half")
SEEDS = tuple(range(5000, 5010))
CONFIRM_SEEDS = tuple(range(5010, 5020))
N_SAMPLES = 6_000_000
MEASURE_TOL = 1e-12
PREFLIGHT_TOL = 8.425e-04        # AO §7's three-grid-knob reduction tolerance


def exact_gap(model, theta, **kw):
    mu = model.mu(theta, **kw)
    return 1.0 - ao.issuance(mu) - ao.silence(mu), mu


def grid_tol(model, theta=THETA_STAR):
    base = exact_gap(model, theta, n=2001, offset=0.0)[0]
    knobs = (dict(n=4001), dict(n=2001, offset=0.5), dict(n=2001, offset=1.0))
    return sum(abs(exact_gap(model, theta, **kw)[0] - base) for kw in knobs), base


def window_sensitivity(model, theta=THETA_STAR):
    base = exact_gap(model, theta, n=2001, offset=0.0)[0]
    return abs(exact_gap(model, theta, n=2001, h=2.0)[0] - base)


def plan_se(gap, n=N_SAMPLES):
    return float(np.sqrt(gap * (1.0 - gap) / n))


def sample_gap(mu, n, seed):
    """Multinomial draw from the exact measure; returns (G_hat, I_hat, Z_hat, old_G_hat)."""
    keys = sorted(mu)
    probs = np.array([mu[k] for k in keys], dtype=float)
    counts = np.random.RandomState(seed).multinomial(n, probs)
    est = counts / float(n)
    p = dict(zip(keys, est))
    cats = [v for k, v in p.items() if k != ao.NONE]
    i_hat = max(cats) if cats else 0.0
    z_hat = p.get(ao.NONE, 0.0)
    return 1.0 - i_hat - z_hat, i_hat, z_hat, 0.0


EXITS = ("AO-COLLAPSES", "SAMPLING-UNDERPOWERED", "OLD-COMPLEMENT-ALSO-SEPARATES",
         "AO-SEPARATES", "O-NONE")


def classify(m):
    if not m.get("exact_ok", False):
        return "AO-COLLAPSES"
    if not m.get("resolution_ok", False):
        return "SAMPLING-UNDERPOWERED"
    if m.get("old_separates", False):
        return "OLD-COMPLEMENT-ALSO-SEPARATES"
    if m.get("clean", False):
        return "AO-SEPARATES"
    return "O-NONE"
