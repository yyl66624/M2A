"""Run Phase VI: three structurally different synthetic systems against the gap threshold law."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p4_mechanisms import SUBSTRATES, predicted_threshold
from p5_mechanisms import critical_beta, gap_for, tnorm, channels
from p6_systems import Z95, loglog_slope, s2_critical_rho, s3_critical_beta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
S_S2 = (0.25, 0.4, 0.5, 0.6, 0.75, 0.8)
S_SLOPE = (0.25, 0.5, 0.75)
SLOPE_TOL = 0.15


def run_s1(prev_v2):
    cells = []
    for kind in SUBSTRATES:
        for name in ("product", "lukasiewicz", "godel"):
            key = f"{kind}|{name}|3|all_weak|0.5"
            num = critical_beta(kind, tnorm(name, channels(3, "all_weak", 0.5)), 1.0)
            cells.append({"kind": kind, "tnorm": name, "numeric": num,
                          "phase5": prev_v2[key]["numeric_beta"],
                          "abs_diff_vs_phase5": abs(num - prev_v2[key]["numeric_beta"])})
    slopes = {}
    for kind in SUBSTRATES:
        gaps, betas = [], []
        for s in S_SLOPE:
            g = gap_for("product", 3, "all_weak", s)
            gaps.append(g)
            betas.append(critical_beta(kind, tnorm("product", channels(3, "all_weak", s)), 1.0))
        slopes[kind] = loglog_slope(gaps, betas)
    checks = {"S1_matches_phase5": all(c["abs_diff_vs_phase5"] <= 1e-3 for c in cells),
              "S1_slope_minus_one": all(abs(slopes[k] + 1.0) <= SLOPE_TOL for k in slopes)}
    return {"rows": cells, "slope_by_substrate": slopes, "checks": checks}


def run_s2():
    rows = []
    for s in S_S2:
        r = s2_critical_rho(s, 1.0)
        rows.append({"s": s, "gap": 1.0 - s, "rho_numeric": r["rho"], "rho_pred": r["pred"],
                     "rel_diff": abs(r["rho"] - r["pred"]) / r["pred"], "m_star": r.get("m_star"),
                     "reason": r["reason"]})
    finite = [r for r in rows if np.isfinite(r["rho_numeric"])]
    slope = loglog_slope([r["gap"] for r in finite], [r["rho_numeric"] for r in finite])
    mono = all(finite[i]["rho_numeric"] >= finite[i + 1]["rho_numeric"] for i in range(len(finite) - 1))
    by_lambda = sorted(finite, key=lambda r: r["rho_numeric"])          # Lambda_hi = rho (drive_hi=1)
    e_lo, e_hi = by_lambda[0]["rel_diff"], by_lambda[-1]["rel_diff"]    # smallest vs largest Lambda
    asym_b = all(by_lambda[i]["rel_diff"] >= by_lambda[i + 1]["rel_diff"] - 1e-12
                 for i in range(len(by_lambda) - 1))
    asym_decay = e_lo >= 2.0 * e_hi                                     # P6-A6: decay >= 2x, no constant
    checks = {"S2_slope_minus_two": abs(slope + 2.0) <= SLOPE_TOL,
              "S2_error_nonincreasing_in_Lambda": asym_b,
              "S2_error_decays_at_least_2x": asym_decay,
              "S2_monotone_in_gap": mono}
    return {"rows": rows, "slope": slope, "rel_err_smallest_Lambda": e_lo,
            "rel_err_largest_Lambda": e_hi, "checks": checks}


def run_s3():
    rows = []
    for kind in ("logistic", "probit"):
        for n in (2, 3, 4):
            c = s3_critical_beta(kind, n, "hard", 0.0)
            rows.append({"kind": kind, "n": n, "pattern": "hard", "s": 0.0,
                         "beta_numeric": c["beta"], "beta_pred": c["pred"],
                         "abs_diff": abs(c["beta"] - c["pred"]), "alpha_f": c["alpha_f"],
                         "alpha_s": c["alpha_s"], "n_points": c["n_points"],
                         "measurable": c["measurable"]})
    slopes = {}
    for kind in ("logistic", "probit"):
        gs, bs = [], []
        for s in S_SLOPE:
            c = s3_critical_beta(kind, 3, "all_weak", s)
            gs.append(1.0 - s)
            bs.append(c["beta"])
        slopes[kind] = loglog_slope(gs, bs)
    meas = [r for r in rows if r["measurable"]]
    checks = {"S3_abs_within_005": len(meas) == len(rows) and all(r["abs_diff"] <= 0.05 for r in meas),
              "S3_slope_minus_one": all(abs(slopes[k] + 1.0) <= SLOPE_TOL for k in slopes)}
    return {"rows": rows, "slope_by_substrate": slopes, "checks": checks}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p6_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    prev_v2 = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V2"]["rows"]
    payload = {"schema": "m2a.phase6.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE6_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "alpha": 0.05, "slope_tolerance": SLOPE_TOL,
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}
    payload["S1"] = run_s1(prev_v2)
    payload["S2"] = run_s2()
    payload["S3"] = run_s3()

    s1_ok = all(payload["S1"]["checks"].values())
    s2_ok = all(payload["S2"]["checks"].values())
    s3_ok = all(payload["S3"]["checks"].values())
    slopes = {"S1": payload["S1"]["slope_by_substrate"]["logistic"],
              "S2": payload["S2"]["slope"],
              "S3": payload["S3"]["slope_by_substrate"]["logistic"]}
    additive = [k for k, v in slopes.items() if abs(v + 1.0) <= SLOPE_TOL]
    if not s1_ok:
        outcome = "NOT_VALID (S1 reference does not reproduce Phase V)"
    elif all(abs(v + 1.0) <= SLOPE_TOL for v in slopes.values()):
        outcome = "O-INVARIANT"
    elif len(additive) == 2 and "S2" not in additive and s2_ok and s3_ok:
        outcome = "O-FORM-CHANGES"
    else:
        outcome = "O-REFUTED"
    payload["slopes"] = slopes
    payload["outcome"] = outcome
    payload["verdict"] = "SUPPORTED" if (s1_ok and s2_ok and s3_ok and outcome != "O-REFUTED") else "REFUTED"
    json.dump(payload, open(HERE / "phase6_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("slopes:", {k: round(v, 4) for k, v in slopes.items()})
    print("S1:", payload["S1"]["checks"], "| S2:", payload["S2"]["checks"],
          "| S3:", payload["S3"]["checks"])
    print("outcome:", outcome, "verdict:", payload["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
