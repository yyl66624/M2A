"""Run Phase XII: locate the additive constant against the exact instrument, then test homogeneity.

Criteria and tolerances are copied from PHASE12_PREREGISTRATION.md; not editable after running.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

from p8_smooth import C1
import p12_lattice as p12

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

CAND_BAND = 0.30
EXP_FLOOR = 0.05
TAU_ANCHOR = 1e-9
TAU_XC6 = 1e-8
GAP_XC5 = 0.002
E1_GRID = (0.0, 40.0, 200.0)


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p12_gate.py")], capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    committed = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    s_grid, rows = committed["s_grid"], committed["rows"]
    lam = {k: v["lambda_hi"] for k, v in rows.items()}
    t0 = time.time()

    e0_star, err_star, big, meta = p12.fit_e0(s_grid, lam)
    dists = {k: abs(e0_star - v) for k, v in p12.E0_CANDIDATES.items()}
    nearest = min(dists, key=dists.get)

    exp_star = p12.exponent(e0_star, big)
    exp_phase8 = p12.exponent(2 * C1, big)
    anchor_rho = max(abs(p12.rho_smooth(2 * C1, s) - rows[str(s)]["rho_smooth"]) /
                     rows[str(s)]["rho_smooth"] for s in s_grid)
    anchor_exp = abs(exp_phase8 - committed["P8_1_slope"])

    branch = []
    for s in s_grid:
        rs = p12.root_small(s, e0_star)
        branch.append({"s": s, "present": rs is not None,
                       "rho_low": None if rs is None else rs * rs,
                       "rho_exact": lam[str(s)],
                       "below_exact": None if rs is None else bool(rs * rs < lam[str(s)])})
    no_branch = not any(b["present"] for b in branch)
    branch_ok = no_branch or all(b["below_exact"] for b in branch if b["present"])

    cuts = []
    for cut in p12.LAMBDA_CUTS:
        ss = p12.subset(s_grid, lam, cut)
        if len(ss) >= 2:
            cuts.append({"lambda_min": cut, "n": len(ss),
                         "exp_phase8": p12.exponent(2 * C1, ss),
                         "exp_fitted": p12.exponent(e0_star, ss)})
    mono = {"phase8": all(cuts[i + 1]["exp_phase8"] > cuts[i]["exp_phase8"] and
                          abs(cuts[i + 1]["exp_phase8"] - cuts[i]["exp_phase8"]) >= GAP_XC5
                          for i in range(len(cuts) - 1)),
            "fitted": all(cuts[i + 1]["exp_fitted"] > cuts[i]["exp_fitted"] and
                          abs(cuts[i + 1]["exp_fitted"] - cuts[i]["exp_fitted"]) >= GAP_XC5
                          for i in range(len(cuts) - 1))}
    below_minus_two = all(c["exp_phase8"] < -2.0 and c["exp_fitted"] < -2.0 for c in cuts)

    xc6 = []
    for e0 in (2 * C1, e0_star):
        for e1 in E1_GRID:
            for s in s_grid:
                a, n = p12.slope_large(s, e0, e1), p12.num_slope_large(s, e0, e1)
                if a is None:
                    continue
                xc6.append(abs(a - n) / abs(a))
    xc6_max = float(max(xc6))

    checks = {
        "XC1_fitted_constant_matches_a_candidate": dists[nearest] <= CAND_BAND,
        "XC2_exponent_at_fitted_constant_not_minus_two": abs(exp_star + 2.0) >= EXP_FLOOR,
        "XC3_low_branch_is_artefact_or_absent": branch_ok,
        "XC4_anchor_reproduces_phase8": anchor_rho <= TAU_ANCHOR and anchor_exp <= TAU_ANCHOR,
        "XC5_nested_drift_monotone": mono["phase8"] and mono["fitted"] and below_minus_two,
        "XC6_diamond_extends_to_e1": xc6_max <= TAU_XC6,
    }
    if not checks["XC4_anchor_reproduces_phase8"]:
        exit_label, why = "E4 INSTRUMENT-MISMATCH", "XC4 failed: the e0 family is not on Phase VIII's footing"
    elif not checks["XC1_fitted_constant_matches_a_candidate"]:
        exit_label, why = "E2 NO-CANDIDATE-EXPLAINS", f"e0* = {e0_star}, nearest candidate {nearest} at {dists[nearest]:.3f} > 0.30"
    elif not checks["XC2_exponent_at_fitted_constant_not_minus_two"]:
        exit_label, why = "E3 HOMOGENISES-AT-FITTED", f"exponent at e0* is {exp_star:.6f}, within -2 +- 0.05"
    elif not checks["XC3_low_branch_is_artefact_or_absent"]:
        exit_label, why = "E5 BRANCH-UNDECLARED", "a low-rate branch is not refuted by the exact instrument"
    elif not checks["XC6_diamond_extends_to_e1"]:
        exit_label, why = "E-UNMAPPED", "XC6 failed while XC1-XC4 passed - not covered by the table"
    else:
        exit_label, why = "E1 CONFIRMED", "XC1-XC4 and XC6 pass; XC5 recorded as a finding"

    payload = {"schema": "m2a.phase12.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE12_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "candidates": p12.E0_CANDIDATES, "candidate_band": CAND_BAND,
               "fit": {"e0_star": e0_star, "max_track_error": err_star, "distances": dists,
                       "nearest": nearest, "big_family": big, "meta": meta},
               "exponents": {"at_fitted": exp_star, "at_phase8": exp_phase8,
                             "committed_phase8": committed["P8_1_slope"]},
               "anchors": {"rho_max_rel": anchor_rho, "chord_abs_diff": anchor_exp},
               "branch": {"cells": branch, "no_second_branch": no_branch},
               "nested": {"cuts": cuts, "monotone": mono, "all_below_minus_two": below_minus_two},
               "xc6_max_rel": xc6_max, "checks": checks,
               "exit": exit_label, "exit_reason": why,
               "verdict": "SUPPORTED" if exit_label == "E1 CONFIRMED" else
                          ("REFUTED" if exit_label.startswith("E4") else "QUALIFIED"),
               "runtime": {"seconds": round(time.time() - t0, 1),
                           "sampling": "none (closed forms, committed exact instrument)"}}
    json.dump(payload, open(HERE / "phase12_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nXC1 fit: e0* = {e0_star} (max track error {err_star:.4%}); "
          f"distances {json.dumps({k: round(v,4) for k,v in dists.items()})} nearest={nearest}")
    print(f"XC2 exponent at e0*: {exp_star:.6f} (floor |exp+2| >= {EXP_FLOOR}); "
          f"at phase8 e0: {exp_phase8:.6f}")
    print(f"XC3 second branch present: {any(b['present'] for b in branch)} "
          f"all below exact: {all(b['below_exact'] for b in branch if b['present'])}")
    print(f"XC4 anchors: rho {anchor_rho:.2e}, chord {anchor_exp:.2e}")
    print("XC5 nested cuts:")
    for c in cuts:
        print(f"   Lambda_min={c['lambda_min']:6.1f} n={c['n']} "
              f"exp(phase8)={c['exp_phase8']:.6f} exp(fitted)={c['exp_fitted']:.6f}")
    print(f"   monotone phase8={mono['phase8']} fitted={mono['fitted']} all<-2={below_minus_two}")
    print(f"XC6 max rel (analytic vs Richardson, e1 up to 200): {xc6_max:.2e}")
    print(f"\nCHECKS: {json.dumps(checks)}")
    print(f"EXIT: {exit_label}  ({why})  verdict={payload['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
