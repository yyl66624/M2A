"""Run Phase IX: aggregation immunity of the composition law (A) and free per-stage thresholds (B).

Every tolerance below is copied from PHASE9_PREREGISTRATION.md (as amended by P9-A1..P9-A4) and must
not be edited after running. The gate runs first and a failure refuses the round.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

from p5_mechanisms import ALPHA
from p4_mechanisms import quantile
import p9_aggregation as p9

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

KINDS = ("logistic", "probit", "gumbel")
KS = (2, 3, 4)
MS = (1, 2, 3, 4)
SS = (0.3, 0.5, 0.7)
TNORMS = ("product", "godel", "lukasiewicz")
TAU_A1 = 0.002          # relative, A1
TAU_A2 = 0.002          # relative spread, A2
TAU_A3 = 1e-12          # pointwise identity, A3
TAU_A5 = 0.002          # relative, A5
RATIO_A5 = (1.99, 2.01)
TAU_B1 = 0.004          # relative, B1
TAU_B3 = 0.004          # relative, B3
TAU_B4 = 0.005          # absolute on ratio differences, B4
FLOOR_B2 = 0.02         # absolute effect-size floor, B2
HETERO = ((0.3, 0.7), (0.2, 0.6), (0.4, 0.6))


def _phi_psi(k):
    phi = (1.0 - ALPHA) ** (1.0 / k)
    psi = ALPHA / (1.0 - ALPHA) ** ((k - 1.0) / k)
    return phi, psi


def run_a():
    rows, skipped = {}, []
    for kind in KINDS:
        for k in KS:
            for T in TNORMS:
                for m in MS:
                    for s in SS:
                        key = f"{kind}|{T}|{k}|{m}|{s}"
                        r = p9.critical_beta_agg(kind, k, m, s, T)
                        if not r["measurable"] or "rel_diff" not in r:
                            skipped.append({"cell": key, "reason": r["reason"]})
                            continue
                        # A3: pointwise identity of the enumerated silent side at three working betas
                        cfgs = p9.stage_configs_agg(T, k, m, s)
                        silent_cfgs = [c for c in cfgs if min(c) < 1.0 - 1e-12]
                        thetas, _, _ = p9._thetas_for(1.0 - r["L"])
                        if thetas is None:
                            skipped.append({"cell": key, "reason": "NOT_MEASURABLE at reduction"})
                            continue
                        red = max(p9.pointwise_reduction_error(kind, f * r["pred"], thetas,
                                                              silent_cfgs, k, r["L"])
                                  for f in (0.5, 1.0, 2.0))
                        rows[key] = {
                            "pred": r["pred"], "beta": r["beta"], "rel_diff": r["rel_diff"],
                            "L": r["L"], "reduction_error": red, "levels": r["levels"],
                            "n_configs": r["n_configs"], "n_points": r["n_points"],
                            "worst_stages": r["worst_stages"]}
    spread = {}
    for kind in KINDS:
        for k in KS:
            for s in SS:
                # keys are "kind|agg|k|m|s"; filter by position so m=2 cannot be read as k=2
                cells = [v for key, v in rows.items()
                         if (lambda q: q[0] == kind and q[2] == str(k) and q[4] == str(s))(key.split("|"))]
                vals = [v["beta"] for v in cells]
                preds = [v["pred"] for v in cells]
                spread[f"{kind}|{k}|{s}"] = {"n": len(vals), "spread": float(max(vals) - min(vals)),
                                             "tol": TAU_A2 * float(np.mean(preds))}
    mean_rows, mean_ratio = {}, {}
    for kind in KINDS:
        for s in (0.3, 0.7):
            for m in MS:
                r = p9.critical_beta_agg(kind, 2, m, s, "mean")
                if not r["measurable"] or "rel_diff" not in r:
                    skipped.append({"cell": f"{kind}|mean|2|{m}|{s}", "reason": r["reason"]})
                    mean_rows[f"{kind}|mean|2|{m}|{s}"] = {"pred": r["pred"], "beta": r["beta"],
                                                           "rel_diff": float("nan"), "L": r["L"],
                                                           "measurable": False}
                    continue
                mean_rows[f"{kind}|mean|2|{m}|{s}"] = {"pred": r["pred"], "beta": r["beta"],
                                                       "rel_diff": r["rel_diff"], "L": r["L"],
                                                       "measurable": True}
            b1 = mean_rows[f"{kind}|mean|2|1|{s}"]["beta"]
            b2 = mean_rows[f"{kind}|mean|2|2|{s}"]["beta"]
            mean_ratio[f"{kind}|{s}"] = {"ratio_m2_over_m1": b2 / b1,
                                         "in_band": bool(RATIO_A5[0] <= b2 / b1 <= RATIO_A5[1])}
    L_alg = []
    for T in TNORMS:
        for m in MS:
            for s in SS:
                L_alg.append(abs(p9.largest_subunit_level(T, m, s) - s))
    for m in MS:
        for s in (0.0,) + SS:
            L_alg.append(abs(p9.largest_subunit_level("mean", m, s) - (1.0 - (1.0 - s) / m)))
    checks = {
        "A1_prediction_matches_enumeration": all(v["rel_diff"] <= TAU_A1 for v in rows.values()),
        "A2_spread_over_agg_and_m": all(d["n"] >= 2 and d["spread"] <= d["tol"]
                                        for d in spread.values()),
        "A3_pointwise_level_dominance": all(v["reduction_error"] <= TAU_A3 for v in rows.values()),
        "A4_L_algebra": max(L_alg) <= 1e-12,
        "A5_mean_control_shifts_with_L": (all(v["rel_diff"] <= TAU_A5 for v in mean_rows.values())
                                          and all(r["in_band"] for r in mean_ratio.values())),
    }
    worst = {"A1_max_rel_diff": max(v["rel_diff"] for v in rows.values()),
             "A2_max_spread_ratio": max(d["spread"] / d["tol"] for d in spread.values()),
             "A3_max_reduction_error": max(v["reduction_error"] for v in rows.values()),
             "A4_max_L_error": max(L_alg),
             "A5_max_rel_diff": max(v["rel_diff"] for v in mean_rows.values()),
             "A5_min_ratio": min(r["ratio_m2_over_m1"] for r in mean_ratio.values()),
             "A5_max_ratio": max(r["ratio_m2_over_m1"] for r in mean_ratio.values())}
    return {"rows": rows, "spread": spread, "mean_rows": mean_rows, "mean_ratio": mean_ratio,
            "n_cells": len(rows), "n_skipped": len(skipped), "skipped": skipped,
            "worst": worst, "checks": checks}


def run_b():
    rows = {}
    for kind in KINDS:
        for s in SS:                                   # B1: symmetric
            phi, psi = _phi_psi(2)
            law = (quantile(phi, kind) - quantile(psi, kind)) / (1.0 - s)
            f = p9.critical_beta_free(kind, s, s, law)
            fp = p9.critical_beta_free_fixedpoint(kind, s, s, law)
            rows[f"{kind}|sym|{s}"] = {"kind": kind, "mode": "sym", "s1": s, "s2": s,
                                       "law_shared": law, "beta_free": f["beta"],
                                       "beta_fp": fp["beta"], "rel_vs_law": abs(f["beta"] - law) / law,
                                       "rel_two_instruments": abs(f["beta"] - fp["beta"]) / law,
                                       "n_points": f.get("n_points"), "reason": f["reason"]}
        for (s1, s2) in HETERO:                        # B2/B3/B4: heterogeneous
            hi = max(s1, s2)
            phi, psi = _phi_psi(2)
            law = (quantile(phi, kind) - quantile(psi, kind)) / (1.0 - hi)
            shared = p9.shared_beta_numeric(kind, hi, 2)
            f = p9.critical_beta_free(kind, s1, s2, law)
            fp = p9.critical_beta_free_fixedpoint(kind, s1, s2, law)
            rows[f"{kind}|het|{s1}|{s2}"] = {
                "kind": kind, "mode": "het", "s1": s1, "s2": s2, "law_shared": law,
                "beta_shared_numeric": shared, "beta_free": f["beta"], "beta_fp": fp["beta"],
                "gain": shared - f["beta"], "floor": max(FLOOR_B2, 5 * TAU_B1 * shared),
                "rel_two_instruments": abs(f["beta"] - fp["beta"]) / law,
                "theta1": f.get("theta1"), "theta2": f.get("theta2"), "P": f.get("P"),
                "r1": f.get("r1"), "r2": f.get("r2"), "max_r": f.get("max_r"),
                "alpha_over_P": f.get("alpha_over_P"),
                "abs_r1_minus_r2": abs(f.get("r1", np.nan) - f.get("r2", np.nan)),
                "abs_maxr_minus_alpha_over_P": abs(f.get("max_r", np.nan) -
                                                   f.get("alpha_over_P", np.nan)),
                "reason": f["reason"]}
    het = [v for v in rows.values() if v["mode"] == "het"]
    sym = [v for v in rows.values() if v["mode"] == "sym"]
    checks = {
        "B1_symmetric_free_equals_shared_law": all(v["rel_vs_law"] <= TAU_B1 for v in sym),
        "B2_heterogeneous_free_is_strictly_better": all(v["gain"] >= v["floor"] for v in het),
        "B3_two_instruments_agree": all(v["rel_two_instruments"] <= TAU_B3 for v in rows.values()),
        "B4_ratio_equalisation_at_optimum": all(v["abs_r1_minus_r2"] <= TAU_B4
                                                and v["abs_maxr_minus_alpha_over_P"] <= TAU_B4
                                                for v in het),
    }
    worst = {"B1_max_rel_vs_law": max(v["rel_vs_law"] for v in sym),
             "B2_min_gain": min(v["gain"] for v in het),
             "B2_max_floor": max(v["floor"] for v in het),
             "B3_max_rel_two_instruments": max(v["rel_two_instruments"] for v in rows.values()),
             "B4_max_abs_r_difference": max(v["abs_r1_minus_r2"] for v in het),
             "B4_max_abs_binding_error": max(v["abs_maxr_minus_alpha_over_P"] for v in het)}
    return {"rows": rows, "checks": checks, "worst": worst,
            "tolerances": {"B1": TAU_B1, "B2_floor": FLOOR_B2, "B3": TAU_B3, "B4": TAU_B4}}


def decide(A, B) -> tuple:
    """Exit table of PHASE9_PREREGISTRATION.md section 3, applied in the registered order."""
    a_ok = all(A["checks"].values())
    b1, b2 = B["checks"]["B1_symmetric_free_equals_shared_law"], \
        B["checks"]["B2_heterogeneous_free_is_strictly_better"]
    b34 = B["checks"]["B3_two_instruments_agree"] and B["checks"]["B4_ratio_equalisation_at_optimum"]
    if a_ok and b1 and b2 and b34:
        return "E1 CONFIRMED", "a_all_and_b_all"
    if not a_ok:
        return "E2 AGGREGATION-MATTERS", "failing: " + ",".join(
            k for k, v in A["checks"].items() if not v)
    if not b1:
        return "E3 FREEDOM-MATTERS", "B1 fails with A intact"
    if not b2:
        return "E4 NO-ASYMMETRY-GAIN", "B2 fails with A and B1 intact"
    if not b34:
        return "E5 INSTRUMENT-DIVERGENCE", "B3 or B4 fails with A, B1, B2 intact"
    return "E-UNMAPPED", "criteria combination not covered by the registered exit table"


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p9_gate.py")], capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    t0 = time.time()
    A = run_a()
    t_a = time.time() - t0
    B = run_b()
    t_b = time.time() - t0 - t_a
    exit_label, why = decide(A, B)
    payload = {"schema": "m2a.phase9.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE9_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "alpha": ALPHA, "kinds": list(KINDS), "ks": list(KS), "ms": list(MS),
               "ss": list(SS), "aggregators": list(p9.AGGREGATORS),
               "resolution": {"dtheta_factor_A": p9.DTHETA_FACTOR,
                              "dtheta_factor_B": p9.DTHETA_FACTOR_B,
                              "bisect_factor": p9.BISECT_FACTOR,
                              "theta_box": [p9.THETA_LO, p9.THETA_HI]},
               "A": A, "B": B, "checks": {"A": A["checks"], "B": B["checks"]},
               "exit": exit_label, "exit_reason": why,
               "verdict": "SUPPORTED" if exit_label.startswith("E1") else
                          ("QUALIFIED" if exit_label.startswith("E5") else "REFUTED"),
               "runtime": {"seconds_a": round(t_a, 1), "seconds_b": round(t_b, 1),
                           "sampling": "none (deterministic functions, grids and bisections)"}}
    json.dump(payload, open(HERE / "phase9_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nA: {A['n_cells']} cells, skipped {A['n_skipped']}  checks={A['checks']}")
    print(f"   worst={ {k: (f'{v:.3e}' if isinstance(v, float) else v) for k, v in A['worst'].items()} }")
    print(f"B: {len(B['rows'])} cells  checks={B['checks']}")
    print(f"   worst={ {k: round(v, 6) for k, v in B['worst'].items()} }")
    print(f"\nEXIT: {exit_label}  ({why})  verdict={payload['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
