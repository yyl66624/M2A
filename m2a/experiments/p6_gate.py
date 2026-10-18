"""Phase VI gate: exactness of the Poisson tail, the slope estimator, and the S3 derivation.
Must pass before any Phase VI result is read."""
from __future__ import annotations

import sys
from math import exp

import numpy as np

from p5b_instrument import DTHETA_FACTOR, MAX_GRID, grid_spec
from p6_systems import (Z95, loglog_slope, poisson_cdf_grid, poisson_sf, s2_critical_rho,
                        s2_window_exists, s3_critical_beta, s3_prediction, s3_window_exists,
                        _sf_from_cdf)

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# K1 Poisson tail: closed form at m=1, and grid recurrence vs log-space direct sum.
# Convention under test: sf[m] = P(N >= m) = 1 - cdf[m-1]  (P6-A4)
d1 = abs(poisson_sf(1, 2.0) - (1.0 - exp(-2.0)))
cross = 0.0
for m, lam in [(3, 5.0), (10, 8.0), (40, 30.0), (100, 90.0), (60, 1000.0), (1030, 1000.0)]:
    grid = _sf_from_cdf(poisson_cdf_grid(lam, m + 1))
    cross = max(cross, abs(grid[m] - poisson_sf(m, lam)))
check("K1_poisson_exactness", d1 <= 1e-12 and cross <= 1e-9
      and poisson_sf(0, 5.0) == 1.0 and poisson_sf(5, 0.0) == 0.0,
      f"m=1 err {d1:.1e}, grid-vs-direct max {cross:.1e}")

# K2 the slope estimator recovers exact power laws
s_m1 = loglog_slope([0.2, 0.35, 0.5, 0.7, 0.9], [7.0 / x for x in (0.2, 0.35, 0.5, 0.7, 0.9)])
s_m2 = loglog_slope([0.2, 0.35, 0.5, 0.7, 0.9], [7.0 / x ** 2 for x in (0.2, 0.35, 0.5, 0.7, 0.9)])
check("K2_loglog_slope_exact", abs(s_m1 + 1.0) < 1e-9 and abs(s_m2 + 2.0) < 1e-9,
      f"{s_m1:.6f} / {s_m2:.6f}")

# K3 S3 derivation self-consistency: {1,0} and {0,1} are the same multiset of levels
a = s3_prediction("logistic", [1.0, 0.0])
bq = s3_prediction("logistic", [0.0, 1.0])
na = s3_critical_beta("logistic", 2, "hard", 0.0)
nb = s3_critical_beta("logistic", 2, "one_weak", 0.0)
check("K3_s3_multiset_invariance", abs(a["pred"] - bq["pred"]) < 1e-12
      and abs(na["beta"] - nb["beta"]) < 1e-3, f"pred {a['pred']:.4f}, beta {na['beta']:.4f}/{nb['beta']:.4f}")

# K4 S2 INSTRUMENT ONLY (P6-A6): the returned rho* must be the exact switch point of the
# registered condition -- feasible at rho*, infeasible just below it. Science criteria (slope,
# asymptotic accuracy) are judged by run_phase6, NOT here: putting them in the gate turned every
# hand-check failure into pressure to loosen a registered tolerance.
r = s2_critical_rho(0.5, 1.0)
r_wide = s2_critical_rho(0.25, 1.0)
feas_at, m_at = s2_window_exists(r["rho"], 0.5, 1.0)
feas_below, _ = s2_window_exists(r["rho"] * (1.0 - 1e-3), 0.5, 1.0)
check("K4_s2_switch_point_is_exact",
      feas_at and (not feas_below) and r["m_star"] == m_at and r_wide["rho"] < r["rho"],
      f"rho*={r['rho']:.4f} feasible with m*={m_at}; infeasible at {r['rho']*(1-1e-3):.4f}; "
      f"gap .75 -> {r_wide['rho']:.2f} < gap .5 -> {r['rho']:.2f}")

# K5 S3: analytic vs numeric within the registered 0.05 on one cell
c = s3_critical_beta("logistic", 3, "all_weak", 0.5)
check("K5_s3_hand_value", c["measurable"] and abs(c["beta"] - c["pred"]) <= 0.05,
      f"beta*={c['beta']:.4f} pred={c['pred']:.4f} a_f={c['alpha_f']:.5f} a_s={c['alpha_s']:.5f}")

# K6 grid cap respected for the smallest gap in the run set
worst = max(grid_spec(g)[1] for g in (0.2, 0.25, 0.3, 0.5, 1.0))
check("K6_grid_within_cap", worst <= MAX_GRID, f"largest grid {worst} points (cap {MAX_GRID})")

# K7 determinism
x1 = s2_critical_rho(0.4, 1.0)["rho"]
x2 = s2_critical_rho(0.4, 1.0)["rho"]
check("K7_determinism", x1 == x2, f"{x1:.6f}")

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> Phase VI must not run]"))
sys.exit(1 if n_bad else 0)
