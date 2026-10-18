"""Phase V gate: run BEFORE any Phase V result is read. Determinism, known answers, negative controls."""
from __future__ import annotations

import sys

import numpy as np

from p5_mechanisms import (ARMS, DP_SPEC, QS, chain_curve, chain_polarity, critical_beta,
                           dp_sensitivity_only, gap_for, law, predicted_critical,
                           predicted_threshold, run_cue, tnorm, window_exists)

SUBSTRATES = ("logistic", "probit", "gumbel")
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# C1 determinism: same (arm, q, steps, seed) -> identical readout
a1 = run_cue(0.8, 20000, 3, "base")
a2 = run_cue(0.8, 20000, 3, "base")
b1 = run_cue(0.8, 20000, 3, "sarsa")
b2 = run_cue(0.8, 20000, 3, "sarsa")
check("C1_determinism", a1 == a2 and b1 == b2, f"base {a1:.4f}, sarsa {b1:.4f}")

# C2 analytic known answer for a soft multi-channel conjunction
kappa = predicted_threshold("logistic")
silent = tnorm("product", [0.5, 0.5, 0.5])
pred = predicted_critical("logistic", 1.0 - silent)
num = critical_beta("logistic", silent, 1.0)
check("C2_soft_conjunction_hand_value",
      abs(kappa - 5.889) <= 1e-3 and abs(num - pred) <= 0.02 and abs(silent - 0.125) < 1e-12,
      f"kappa={kappa:.3f} silent={silent} predicted={pred:.3f} numeric={num:.3f}")

# C3 reduction to Phase IV: hard AND, any n, any of the three t-norms -> the logistic constant
red = [critical_beta("logistic", tnorm(t, [1.0] + [0.0] * (n - 1)), 1.0)
       for n in (2, 3, 4) for t in ("product", "lukasiewicz", "godel")]
check("C3_reduces_to_phase4_constant",
      all(abs(r - 5.889) <= 0.005 for r in red), f"range {min(red):.3f}-{max(red):.3f}")

# C4 dead gate: an o=0.5 stage zeroes the drive -> flat curve, no gap, no window at beta<=200
pol = chain_polarity([0.75, 0.5])
xs = np.linspace(0, 1, 101)
flat = float(np.max(np.abs(np.diff(chain_curve("logistic", [0.75, 0.5], xs)))))
check("C4_dead_gate_flat_and_no_window",
      pol == 0.0 and flat < 1e-12 and not window_exists("logistic", 200.0, 0.0, 0.0)
      and critical_beta("logistic", 0.0, 0.0) == float("inf"),
      f"polarity={pol} max|dp|={flat:.1e}")

# C5 negative control: no degradation (s=1) means no separation, so no window at any gain
g1 = gap_for("product", 3, "all_weak", 1.0)
check("C5_no_gap_no_window", g1 == 0.0 and predicted_critical("gumbel", g1) == float("inf"),
      f"gap={g1}")

# C6 the exact operator reproduces the hand values at the two clean ends of q
d1 = dp_sensitivity_only(1.0)
d05 = dp_sensitivity_only(0.5)
check("C6_dp_known_answers", abs(d1 - law(1.0)) <= 0.005 and d05 <= 0.005,
      f"q=1 dp={d1:.4f} law={law(1.0):.3f}; q=0.5 dp={d05:.4f}")

# C7 DP vs MC on a config whose behaviour policy is time-homogeneous (constant eps = 0.02)
vals = [run_cue(0.8, 100000, s, "base") for s in (0, 1, 2)]
# same trainer with the annealing switched off, so the DP's constant-eps assumption holds exactly
from p3_mechanisms import cue_sensitivity, train_cue_agent  # noqa: E402
flat_eps = [cue_sensitivity(train_cue_agent(0.8, 100000, s, eps_start=0.02, eps_end=0.02))
            for s in (0, 1, 2)]
dpe = dp_sensitivity_only(0.8, eps=0.02)
check("C7_dp_matches_constant_eps_mc", abs(np.mean(flat_eps) - dpe) <= 0.01,
      f"mc={np.mean(flat_eps):.4f} dp={dpe:.4f} (annealed reference mc={np.mean(vals):.4f})")

# C8 t-norm algebra and the one-weak invariance across the three aggregations
one = [gap_for(t, 4, "one_weak", 0.3) for t in ("product", "lukasiewicz", "godel")]
check("C8_tnorm_algebra",
      abs(tnorm("lukasiewicz", [0.5, 0.5, 0.5])) < 1e-12
      and abs(tnorm("godel", [0.2, 0.9]) - 0.2) < 1e-12
      and max(one) - min(one) < 1e-12 and abs(one[0] - 0.7) < 1e-12,
      f"one_weak gaps={one}")

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else f"  [{n_bad} FAILED -> Phase V must not run]"))
sys.exit(1 if n_bad else 0)
