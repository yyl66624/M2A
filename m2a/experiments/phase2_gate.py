"""Pre-run gate for Phase II: determinism, known answers, structural facts, negative control.

No experiment may run unless every check passes. Each check is a known answer, not a preference.
"""
from __future__ import annotations

import sys

import numpy as np

from m2a_mechanisms import (availability_sensitivity, e1_rates, p_action, sigmoid, spearman,
                            state_key, train_agent)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


# C1 determinism
r1 = e1_rates("and", 2000, seed=3)
r2 = e1_rates("and", 2000, seed=3)
check("C1_determinism", r1 == r2, "same seed -> identical cell rates")

# C2 analytic known answers
known = {
    ("and", 1, 1): float(sigmoid(6 * (1 * 1 - 0.5))),
    ("and", 1, 0): float(sigmoid(6 * (0 - 0.5))),
    ("or", 1, 0): float(sigmoid(6 * (1 - 0.5))),
    ("single", 0, 1): float(sigmoid(6 * (0 - 0.5))),
}
ok = all(abs(p_action(a, x1, x2) - v) < 1e-12 for (a, x1, x2), v in known.items())
check("C2_analytic_probabilities", ok,
      f"and(1,1)={p_action('and',1,1):.4f}, and(1,0)={p_action('and',1,0):.4f}, "
      f"or(1,0)={p_action('or',1,0):.4f}")

# C3 negative control: no mechanism -> no action
check("C3_negative_control_no_action", p_action("none", 1, 1) == 0.0,
      "arch 'none' returns p=0 for a fully driven input")

# C4 E2 known answer: with values fixed at [0.9, 0.5], Q(A | {A}) = 0.9 and
# Q(A | {A,B}) = 0.9 + gamma * 0.5 = 1.35, so the difference is exactly gamma * 0.5 = 0.45.
Q = train_agent("S_plus_C", steps=20000, seed=0)
d_c = availability_sensitivity(Q, "S_plus_C")
check("C4_S_plus_C_sensitivity_near_gamma_vB", 0.28 <= d_c <= 0.44,
      f"learned |Q(A|A) - Q(A|A,B)| = {d_c:.3f} (hand value gamma*(v_B - c) = 0.36)")

# C5 structural fact: the matched pair collapses for S_only and separates for S_plus_C
v = np.array([0.9, 0.5])
same_s = state_key("S_only", v, np.array([1, 0])) == state_key("S_only", v, np.array([1, 1]))
diff_c = state_key("S_plus_C", v, np.array([1, 0])) != state_key("S_plus_C", v, np.array([1, 1]))
check("C5_state_identifiability", same_s and diff_c,
      f"S_only states identical: {same_s}; S_plus_C states distinct: {diff_c}")

# C6 learning sanity: on a one-step trivial bandit Q(A) should approach 0.9
Q6 = train_agent("S_plus_C", steps=8000, seed=1)
qA = Q6.get(((9, 1), 1), 0.0)   # discretised max 9 (=0.9), only A available, action A
check("C6_Q_converges_to_value_for_single_action", abs(qA - 0.8) < 0.15,
      f"Q(A | state 0.9, only A) = {qA:.3f} (target 0.9 - cost 0.1 = 0.8)")

# C7 spearman sanity
check("C7_spearman_monotone", abs(spearman([0, 1, 2, 3]) - 1.0) < 1e-9
      and abs(spearman([3, 2, 1, 0]) + 1.0) < 1e-9, "monotone and reversed sequences")

bad = [n for n, ok_, _ in checks if not ok_]
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
