"""Phase V-b gate: instrument self-checks. Must pass before the re-test is read."""
from __future__ import annotations

import sys

from p4_mechanisms import predicted_threshold
from p5_mechanisms import chain_polarity, gap_for, tnorm, channels, window_exists
from p5b_instrument import DTHETA_FACTOR, critical_beta_adaptive, grid_spec

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# G1 the spec is what the pre-registration derives: dtheta = 0.0002*gap, points = ceil(span/dtheta)+1
d, n, ok = grid_spec(0.0625)
check("G1_grid_derivation", abs(d - 0.0002 * 0.0625) < 1e-18 and n == 85001 and ok,
      f"dtheta={d:.3e} points={n}")

# G2 reduction to the Phase IV constant, with the adaptive grid
b = critical_beta_adaptive("logistic", 0.0, 1.0)
check("G2_reduces_to_phase4", abs(b["numeric_beta"] - predicted_threshold("logistic")) <= 0.005,
      f"{b['numeric_beta']:.4f} points={b['n_points']}")

# G3 negative control: zero gap has no window at any gain (and the old instrument agrees)
z = critical_beta_adaptive("gumbel", 0.3, 0.3)
check("G3_zero_gap_no_window", z["numeric_beta"] == float("inf")
      and not window_exists("gumbel", 200.0, 0.3, 0.3), z["reason"])

# G4 monotonicity in the gap: a smaller gap must cost more gain
lo_gap = critical_beta_adaptive("gumbel", 0.0, 0.0625)["numeric_beta"]
hi_gap = critical_beta_adaptive("gumbel", 0.0, 0.25)["numeric_beta"]
check("G4_gap_monotone", lo_gap > hi_gap > 0, f"gap 0.0625 -> {lo_gap:.2f}, gap 0.25 -> {hi_gap:.2f}")

# G5 the adaptive grid beats the old discretisation on the two failing cells:
# its own bias bound must be at most 0.02% of beta*
d2, n2, _ = grid_spec(0.0625)
bound = predicted_threshold("gumbel", 0.05) * d2 / (0.0625 ** 2)
check("G5_resolution_bound", bound / (predicted_threshold("gumbel") / 0.0625) <= 0.0002 * (1 + 1e-9),
      f"abs bias bound {bound:.5f}, beta* {predicted_threshold('gumbel')/0.0625:.2f}")

# G6 determinism: identical call twice
r1 = critical_beta_adaptive("probit", 0.5, 1.0)
r2 = critical_beta_adaptive("probit", 0.5, 1.0)
check("G6_determinism", r1 == r2, f"{r1['numeric_beta']:.6f}")

n_bad = sum(1 for _, ok_, _ in checks if not ok_)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> V-b must not run]"))
sys.exit(1 if n_bad else 0)
