"""Phase VII gate: enumeration and instrument self-checks only (no science criteria)."""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from p4_mechanisms import cdf, predicted_threshold
from p5b_instrument import MAX_GRID
from p7_systems import (critical_beta_s4, drive_counts, predicted_beta,
                        predicted_beta_binding_config, silent_side, stage_configs, fire_prob)

HERE = pathlib.Path(__file__).resolve().parent
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


# H1 enumeration: k=2,m=2 over {0,1} gives stage-drive multisets {(1,1),(1,0),(0,0)}
cfg = stage_configs(2, 2, 0.0)
check("H1_enumeration", cfg == [(1.0, 1.0), (0.0, 1.0), (0.0, 0.0)], f"{cfg}")

# H2 the binding silent config is r=1 (exactly one failing stage), i.e. max over configs
th = np.linspace(-0.5, 1.5, 20001)
silent, who = silent_side("logistic", 12.0, th, [c for c in cfg if min(c) < 1.0])
i = int(np.argmax(silent))
check("H2_worst_config_is_r1", who[i] == (0.0, 1.0), f"argmax config at theta={th[i]:.3f}: {who[i]}")

# H3 reduction k=1 is exactly the Phase IV/V constant (no new freedom)
red = all(abs(predicted_beta(kind, 1, 0.0) - predicted_threshold(kind)) <= 1e-12
          for kind in ("logistic", "probit", "gumbel"))
check("H3_k1_reduction_exact", red,
      f"logistic k=1: {predicted_beta('logistic',1,0.0):.6f} vs kappa {predicted_threshold('logistic'):.6f}")

# H4 the r=k-1 formula reproduces what Phase VI's S3 actually measured
p6 = json.loads((HERE / "phase6_results.json").read_text(encoding="utf-8"))["S3"]["rows"]
bad = []
for r in p6:
    if r["pattern"] != "hard":
        continue
    mine = predicted_beta_binding_config(r["kind"], r["n"], 0.0, r["n"] - 1)
    if abs(mine - r["beta_pred"]) > 1e-9:
        bad.append((r["kind"], r["n"], mine, r["beta_pred"]))
check("H4_phase6_s3_formula_is_r_of_k_minus_1", not bad, f"mismatches {bad[:2]}")

# H5 grid stays under the cap for the whole run set (worst case graded s=0.75 -> gap 0.25)
worst = int(np.ceil(2.0 / (0.0002 * 0.25))) + 1
check("H5_grid_within_cap", worst <= MAX_GRID, f"{worst} points vs cap {MAX_GRID}")

# H6 determinism on a real cell
a = critical_beta_s4("logistic", 2, 2, 0.0)
b = critical_beta_s4("logistic", 2, 2, 0.0)
check("H6_determinism", a == b, f"beta*={a['beta']:.4f} pred={a['pred']:.4f} worst={a['worst_silent_stages']}")

# H7 negative control: s=1 leaves no failing configuration -> the instrument must refuse
z = critical_beta_s4("logistic", 2, 2, 1.0)
check("H7_no_failing_config_refused", z["beta"] == float("inf") and "no failing" in z["reason"], z["reason"])

# H8 fold equivalence: count-based log-prob equals the direct per-config product
lv, mat = drive_counts(cfg[1:])
th2 = np.linspace(0.2, 0.8, 7)
fold = np.exp(mat.astype(float) @ np.log(np.clip(
    np.vstack([np.asarray(cdf(9.0 * (l - th2), "logistic"), dtype=float)
               for l in lv]), 1e-300, 1.0)))
direct = np.array([[np.prod([float(cdf(9.0 * (d - t), "logistic")) for d in c]) for t in th2]
                   for c in cfg[1:]])
check("H8_count_fold_equivalence", float(np.max(np.abs(fold - direct))) < 1e-12,
      f"max abs {float(np.max(np.abs(fold - direct))):.2e}")

# H9 fire side is F(beta(1-theta))^k
f9 = fire_prob("logistic", 9.0, th2, 3)
check("H9_fire_side", abs(float(f9[0]) - float(np.prod([cdf(9.0 * (1.0 - th2[0]), "logistic")] * 3))) < 1e-12,
      f"{float(f9[0]):.6f}")

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> Phase VII must not run]"))
sys.exit(1 if n_bad else 0)
