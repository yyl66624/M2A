"""Pre-run gate for Phase III: analytic identities, boundary formulas, hand-computed agent values."""
from __future__ import annotations

import sys

import numpy as np

from p3_mechanisms import (conjunction_window, cue_sensitivity, key3, p_and, p_gate, p_or,
                           predicted_cue_sensitivity, theta_j, theta_s, train_cue_agent)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


# C1 analytic duality identity
worst = 0.0
for beta in (2, 4, 6, 8, 10):
    for theta in (0.2, 0.5, 0.9):
        worst = max(worst, abs(p_and(1, 1, beta, theta) - p_or(1, 0, beta, theta)))
check("C1_and_joint_equals_or_single", worst < 1e-12, f"max |p_and(1,1) - p_or(1,0)| = {worst:.2e}")

# C2 boundary formulas
ok = all(abs(p_and(1, 0, b, theta_s(b)) - 0.05) < 1e-12
         and abs(p_and(1, 1, b, theta_j(b)) - 0.95) < 1e-12 for b in (6, 8, 10))
check("C2_boundary_formulas", ok,
      f"theta_s(6)={theta_s(6):.4f}, theta_j(6)={theta_j(6):.4f}; "
      f"p_and(1,0;theta_s)=0.05 and p_and(1,1;theta_j)=0.95")

# C3 window existence threshold
no_win = all(conjunction_window(b) is None for b in (2, 4))
win6 = conjunction_window(6)
width_ok = win6 is not None and abs((win6[1] - win6[0]) - (1 - 2 * abs(np.log(0.05 / 0.95)) / 6)) < 1e-12
check("C3_window_exists_iff_gain_large_enough", no_win and width_ok,
      f"no window for beta=2,4; window for beta=6: {tuple(round(x, 4) for x in win6)}")

# C4 gate sign law (analytic)
xs = np.linspace(0, 1, 21)
up = p_gate(xs, 1.0)[-1] - p_gate(xs, 1.0)[0]
down = p_gate(xs, 0.0)[-1] - p_gate(xs, 0.0)[0]
flat = float(np.max(np.abs(np.diff(p_gate(xs, 0.5)))))
check("C4_gate_openness_sign", up > 0 and down < 0 and flat < 1e-12,
      f"o=1: {up:+.4f}, o=0: {down:+.4f}, o=0.5 max|dp|: {flat:.2e}")

# C5 L3 hand values (learned at the 100k-step convergence budget): q=1 -> 0.36, q=0.8 -> 0.216, q=0.5 -> 0
d1 = cue_sensitivity(train_cue_agent(1.0, 100000, 0))
d08 = cue_sensitivity(train_cue_agent(0.8, 100000, 0))
d05 = cue_sensitivity(train_cue_agent(0.5, 100000, 0))
check("C5_cue_sensitivity_hand_values",
      abs(d1 - predicted_cue_sensitivity(1.0)) < 0.03
      and abs(d08 - predicted_cue_sensitivity(0.8)) < 0.03
      and d05 < 0.01,
      f"q=1: {d1:.3f} (pred {predicted_cue_sensitivity(1.0):.3f}); "
      f"q=0.8: {d08:.3f} (pred {predicted_cue_sensitivity(0.8):.3f}); q=0.5: {d05:.3f}")

# C6 no self-loop: the state changes after taking the lower action
k1 = key3(np.array([0.9, 0.5]), np.array([1, 1]), 1, 1)
k2 = key3(np.array([0.9, 0.5]), np.array([0, 1]), 1, 2)
check("C6_step_in_state_kills_self_loop", k1 != k2, f"step-1 {k1} vs step-2 {k2}")

# C7 determinism
a = cue_sensitivity(train_cue_agent(0.8, 4000, 3))
b = cue_sensitivity(train_cue_agent(0.8, 4000, 3))
check("C7_determinism", a == b, f"same seed -> {a:.3f}")

bad = [n for n, ok_, _ in checks if not ok_]
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
