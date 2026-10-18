"""Phase VIII gate: instrument-only checks for the smooth/ exact Poisson threshold machinery."""
from __future__ import annotations

import sys
from math import sqrt

from p6_systems import Z95
from p8_smooth import C1, poisson_quantile, rho_exact, rho_normal_only, rho_smooth

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


check("J1_c1_off_reduces_to_phase6_form",
      all(abs(rho_smooth(s, with_c1=False) - rho_normal_only(s)) <= 1e-9 for s in (0.25, 0.5, 0.8)),
      f"s=0.5: smooth-no-c1 {rho_smooth(0.5, False):.6f} vs phase6 form {rho_normal_only(0.5):.6f}")

check("J2_zero_gap_no_solution", rho_smooth(1.0) == float("inf"), "Delta=0 -> inf")

check("J3_c1_hand_value", abs(C1 - (Z95 ** 2 - 1.0) / 3.0) < 1e-15 and abs(C1 - 0.5685144) < 1e-6,
      f"c1 = {C1:.7f}")

q95 = poisson_quantile(30.0, 0.95)
approx = 30.0 + Z95 * sqrt(30.0) + C1
check("J4_edgeworth_quantile_within_one_count", abs(q95 - approx) <= 1.0,
      f"exact q0.95(Pois(30)) = {q95}, normal+skew = {approx:.3f}")

a1, a2 = rho_exact(0.6), rho_exact(0.6)
check("J5_exact_instrument_determinism", a1 == a2, f"rho*(s=0.6) = {a1:.6f}")

# P8-A1: rho* must INCREASE with s (larger s = smaller drive gap = harder to separate).
# Monotonicity in the gap Delta = 1 - s is the same statement read the other way, so one check suffices.
seq = [rho_smooth(s) for s in (0.2, 0.4, 0.6, 0.8, 0.9)]
check("J6_smooth_monotone_in_gap", all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)),
      "rho*(s=0.2,0.4,0.6,0.8,0.9) = " + ", ".join(f"{v:.2f}" for v in seq))

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> Phase VIII must not run]"))
sys.exit(1 if n_bad else 0)
