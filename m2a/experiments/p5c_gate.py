"""Phase V-c gate: instrument-only self-checks (no science criteria in here -- P6-A6 lesson)."""
from __future__ import annotations

import json
import pathlib
import sys

from p5c_arms import ARMS_C, QS_C, dp_c, law_half, readout_c, visit_weighted

HERE = pathlib.Path(__file__).resolve().parent
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# C1 arm set matches the pre-registration exactly (guards A0/A1 against silent drift)
PRE_REG_ARMS = {"annealed_base", "base_c", "base_long_c", "noexplore_c", "greedy_first_c",
               "sarsa_c", "eps30_c"}
check("C1_arm_set_matches_prereg", set(ARMS_C) == PRE_REG_ARMS,
      f"{sorted(ARMS_C)}")

# C2 A0 is wired to real committed numbers, not to an absent key
prev = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V1"]["rows"]
keys = [f"base|{q}" for q in QS_C]
check("C2_anchor_keys_present", all(k in prev and "mc_mean" in prev[k] for k in keys),
      f"{len(keys)} keys")

# C3 determinism on two arms
a = readout_c(0.8, 3, "base_c")
b = readout_c(0.8, 3, "base_c")
g1 = readout_c(0.8, 3, "greedy_first_c")
g2 = readout_c(0.8, 3, "greedy_first_c")
check("C3_determinism", a == b and g1 == g2, f"base_c {a:.6f}, greedy_first_c {g1:.6f}")

# C4 DP known answers (same hand values Phase V used)
d1 = dp_c(1.0, "base_c")
d05 = dp_c(0.5, "base_c")
check("C4_dp_known_answers", abs(d1 - law_half(1.0)) <= 0.005 and d05 <= 0.005,
      f"q=1 dp={d1:.4f} law={law_half(1.0):.3f}; q=0.5 dp={d05:.4f}")

# C5 closed form and the exact operator are two independent computations of the SAME estimand
cf = visit_weighted(0.8)
dpe = dp_c(0.8, "base_c")
check("C5_closed_form_vs_dp", abs(cf - dpe) <= 1e-6, f"closed {cf:.8f} dp {dpe:.8f}")

# C6 the tie-collapse negative control still holds with zero exploration
n1 = readout_c(0.7, 0, "noexplore_c")
n2 = readout_c(0.8, 1, "noexplore_c")
check("C6_noexploration_tie_collapse", abs(n1) <= 0.002 and abs(n2) <= 0.002,
      f"q=0.7 {n1:.4f}, q=0.8 {n2:.4f}")

# C7 eps enters the DP ONLY through whether the option value ever gets updated:
# eps=0.02 vs eps=0.30 must be identical (max bootstrap), eps=0 must differ.
e02, e30, e00 = dp_c(0.8, "base_c"), dp_c(0.8, "eps30_c"), dp_c(0.8, "noexplore_c")
check("C7_eps_channel_is_as_derived", abs(e02 - e30) < 1e-12 and abs(e02 - e00) > 0.05,
      f"eps .02 {e02:.4f} = eps .30 {e30:.4f}; eps 0 {e00:.4f}")

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> Phase V-c must not run]"))
sys.exit(1 if n_bad else 0)
