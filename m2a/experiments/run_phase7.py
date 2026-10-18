"""Run Phase VII: S4(k,m) mixed aggregation -- worst-case enumeration vs the closed form."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p4_mechanisms import predicted_threshold
from p6_systems import loglog_slope
from p7_systems import (critical_beta_s4, predicted_beta, predicted_beta_binding_config)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
KINDS = ("logistic", "probit")
KS = (1, 2, 3)
MS = (1, 2, 3)
S_GRADED = (0.5, 0.75)
TOL = {"V7_1": 0.05, "V7_2": 0.005, "V7_3_abs": 0.05, "V7_3_slope": 0.15, "V7_4a": 0.005}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p7_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1

    rows = {}
    for kind in KINDS:
        for k in KS:
            for m in MS:
                rows[f"{kind}|{k}|{m}|hard"] = critical_beta_s4(kind, k, m, 0.0)
                for s in S_GRADED:
                    rows[f"{kind}|{k}|{m}|graded{s}"] = critical_beta_s4(kind, k, m, s)

    hard = [r for r in rows.values() if r["s"] == 0.0 and r["measurable"]]
    graded = [r for r in rows.values() if r["s"] > 0.0 and r["measurable"]]
    v7_1 = len(hard) == 18 and all(r["abs_diff"] <= TOL["V7_1"] for r in hard)

    spread = {}
    for kind in KINDS:
        for k in KS:
            for fam, pool in (("hard", hard), ("graded0.5", graded), ("graded0.75", graded)):
                vals = [r["beta"] for r in pool if r["kind"] == kind and r["k"] == k
                        and (r["s"] == 0.0 if fam == "hard" else r["s"] == float(fam[6:]))]
                if len(vals) == len(MS):
                    spread[f"{kind}|k={k}|{fam}"] = max(vals) - min(vals)
    v7_2 = len(spread) == len(KINDS) * len(KS) * 3 and all(v <= TOL["V7_2"] for v in spread.values())

    slopes = {}
    for kind in KINDS:
        for k in KS:
            for m in MS:
                bs = [rows[f"{kind}|{k}|{m}|graded{s}"]["beta"] for s in S_GRADED]
                gaps = [1.0 - s for s in S_GRADED]
                slopes[f"{kind}|{k}|{m}"] = loglog_slope(gaps, bs)
    v7_3_abs = all(r["abs_diff"] <= TOL["V7_3_abs"] for r in graded)
    v7_3_slope = all(abs(v + 1.0) <= TOL["V7_3_slope"] for v in slopes.values())
    v7_3 = v7_3_abs and v7_3_slope

    v7_4a = all(abs(rows[f"{kind}|1|{m}|hard"]["beta"] - predicted_threshold(kind)) <= TOL["V7_4a"]
                for kind in KINDS for m in MS)

    p6 = json.loads((HERE / "phase6_results.json").read_text(encoding="utf-8"))["S3"]["rows"]
    # P7-A3: the diagnostic is defined only on the overlap of the two k grids (Phase VI used n in
    # {2,3,4}, this round registers k in {1,2,3}) -> compare only where both exist.
    diag = []
    ok_dir = True
    for r in p6:
        if r["pattern"] != "hard" or r["n"] not in KS:
            continue
        n = r["n"]
        s4 = rows[f"{r['kind']}|{n}|1|hard"]["beta"]
        s3_r = predicted_beta_binding_config(r["kind"], n, 0.0, n - 1)
        ok_dir = ok_dir and (s4 > s3_r + 1e-9) and abs(s3_r - r["beta_pred"]) <= 1e-9
        diag.append({"kind": r["kind"], "k=n": n, "phase6_S3_pred": r["beta_pred"],
                     "phase6_S3_numeric": r["beta_numeric"], "r_of_k_minus_1_formula": s3_r,
                     "phase7_S4_worst_case": s4, "gap": s4 - r["beta_numeric"]})

    v7_5 = all(r["worst_silent_stages"] == 1 for r in hard + graded)
    checks = {"V7_1_closed_form_hard": v7_1, "V7_2_m_invariance": v7_2,
              "V7_3_graded_abs_and_slope": v7_3, "V7_4a_k1_reduction": v7_4a,
              "V7_4b_direction_and_formula": ok_dir, "V7_5_binding_config_is_r1": v7_5}
    if not v7_4a:
        exit_ = "E4 CONTRADICTION (k=1 does not reduce to kappa_F -> this round is NOT_VALID)"
    elif v7_1 and v7_2 and v7_3 and v7_5 and checks["V7_4b_direction_and_formula"]:
        exit_ = "E1 CONFIRMED"
    elif v7_1 and not (v7_2 and v7_5):
        exit_ = "E2 PARTIAL"
    elif not v7_1:
        exit_ = "E3 NO-COMPOSITION"
    else:
        exit_ = "E2 PARTIAL"
    payload = {"schema": "m2a.phase7.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE7_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "alpha": 0.05, "tolerances": TOL, "rows": rows, "m_spread": spread,
               "graded_slopes": slopes, "V7_4b_diagnostic": diag, "checks": checks,
               "exit": exit_, "verdict": "SUPPORTED" if exit_ == "E1 CONFIRMED" else "QUALIFIED",
               "phase6_verdict_unchanged": "S2 REFUTED / S3 numeric-vs-analytic agreement stands "
                                           "(both used the r=n-1 config, see P7-A2)",
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}
    json.dump(payload, open(HERE / "phase7_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("checks:", checks)
    print("exit:", exit_)
    print("m-spread max:", round(max(spread.values()), 8), "| slope range:",
          round(min(slopes.values()), 4), "..", round(max(slopes.values()), 4))
    for kind in KINDS:
        print(f"  {kind}: " + "  ".join(
            f"k={k} beta*={rows[f'{kind}|{k}|1|hard']['beta']:.4f}(pred {rows[f'{kind}|{k}|1|hard']['pred']:.4f})"
            for k in KS))
    print("  P7-A2 diagnostic (S4 worst-case vs Phase VI S3):")
    for d in diag[:4]:
        print(f"    {d['kind']} k={d['k=n']}: S3 {d['phase6_S3_numeric']:.4f} -> "
              f"S4 {d['phase7_S4_worst_case']:.4f}  (+{d['gap']:.4f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
