"""Pre-run gate for Phase IV: quantiles, predicted thresholds, sign law, Bayes estimator."""
from __future__ import annotations

import sys

import numpy as np

from p4_mechanisms import (SUBSTRATES, bayes_sensitivity, critical_beta, gate_curve, predicted_threshold,
                           quantile)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


# C1 known quantiles
known = {"logistic": (abs(quantile(0.05, "logistic") + 2.9444) < 0.005,
                      abs(quantile(0.95, "logistic") - 2.9444) < 0.005),
         "probit": (abs(quantile(0.05, "probit") + 1.6449) < 0.005,
                    abs(quantile(0.95, "probit") - 1.6449) < 0.005),
         "gumbel": (abs(quantile(0.05, "gumbel") + 1.0972) < 0.005,
                    abs(quantile(0.95, "gumbel") - 2.9702) < 0.005)}
check("C1_quantiles_known", all(all(v) for v in known.values()),
      "; ".join(f"{k}: {tuple(round(quantile(a, k), 4) for a in (0.05, 0.95))}" for k in SUBSTRATES))

# C2 predicted thresholds and numeric critical beta
pred = {k: predicted_threshold(k) for k in SUBSTRATES}
crit = {k: critical_beta(k) for k in SUBSTRATES}
check("C2_critical_beta_matches_prediction",
      all(abs(crit[k] - pred[k]) <= 0.05 for k in SUBSTRATES),
      "; ".join(f"{k}: numeric {crit[k]:.3f} vs predicted {pred[k]:.3f}" for k in SUBSTRATES))

# C3 the three constants are genuinely different
diffs = [abs(pred["logistic"] - pred["probit"]), abs(pred["logistic"] - pred["gumbel"]),
         abs(pred["probit"] - pred["gumbel"])]
check("C3_constants_are_distinct", all(d > 0.5 for d in diffs),
      f"predicted thresholds {[round(pred[k], 3) for k in SUBSTRATES]}")

# C4 gate sign law in each substrate
xs = np.linspace(0, 1, 51)
sign_ok = True
flat_ok = True
for k in SUBSTRATES:
    for o, want in ((0.0, -1), (0.25, -1), (0.75, +1), (1.0, +1)):
        y = gate_curve(k, xs, o)
        sign_ok = sign_ok and (np.sign(y[-1] - y[0]) == want)
    flat_ok = flat_ok and float(np.max(np.abs(np.diff(gate_curve(k, xs, 0.5))))) < 1e-12
check("C4_gate_sign_law_substrate_independent", sign_ok and flat_ok,
      f"signs correct: {sign_ok}; neutral point flat: {flat_ok}")

# C5 Bayes estimator hand values
b1 = bayes_sensitivity(1.0, seed=0)
b08 = bayes_sensitivity(0.8, seed=0)
b05 = bayes_sensitivity(0.5, seed=0)
check("C5_bayes_estimator_hand_values",
      abs(b1 - 0.36) < 0.01 and abs(b08 - 0.216) < 0.01 and abs(b05) < 0.01,
      f"q=1: {b1:.3f}, q=0.8: {b08:.3f}, q=0.5: {b05:.3f}")

bad = [n for n, ok_, _ in checks if not ok_]
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
