"""Run Phase X: can higher-order additive smoothing restore the exponent -2 (P8-O1), and what
diagnostic detects the working-range drift (P8-O2)?

Tolerances copied from PHASE10_PREREGISTRATION.md (with its P10-A1..A6 pre-run registrations);
they must not be edited after running. The gate runs first and a failure refuses the round.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

from math import sqrt

import p10_exponent as p10

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

TAU_X1 = 1e-8           # analytic vs Richardson numerical slope, relative
TAU_X1b = 1e-12         # analytic vs its e1=0 corollary
TAU_X2a = 1e-9          # rho vs committed rho_smooth, relative
TAU_X2b = 1e-3          # chord slope vs committed -2.0620
MINIMAX_FLOOR = 0.01    # X-4: below this the family CAN be homogenised
ALIAS_CHORD = 1e-3      # X-5a chord tolerance
ALIAS_DEV = 0.01        # X-5a local deviation that must remain
NEST_GAP = 0.005        # X-5b nested chord difference
COEFFS = ((p10.E0_PHASE8, 0.0), (p10.E0_PHASE8, 120.0), (5.0, 0.0), (2.0, 400.0), (0.4, 780.0))


def run_x1_x3(committed):
    rows, x1, x1b, x3 = {}, [], [], []
    for e0, e1 in COEFFS:
        for s in p10.S_GRID:
            a = p10.local_slope(s, e0, e1)
            n = p10.num_slope(s, e0, e1)
            x1.append(abs(a - n) / abs(a))
            if str(s) in committed["rows"] and abs(e0 - p10.E0_PHASE8) < 1e-12 and e1 == 0.0:
                got = p10.rho(s, e0, e1)
                x2 = abs(got - committed["rows"][str(s)]["rho_smooth"]) / \
                    committed["rows"][str(s)]["rho_smooth"]
            else:
                x2 = None
            if e1 == 0.0:
                x1b.append(abs(a - p10.local_slope_simplified(s, e0)))
                R = p10.root_R(s, e0, 0.0)
                lhs = abs(a) - 2.0
                rhs = p10.Bs(s) / R - e0 / ((1.0 - s) * R * R)
                x3.append((lhs >= 0.0) == (rhs >= 0.0))
            rows[f"{e0}|{e1}|{s}"] = {"analytic": a, "numeric": n,
                                       "rho": p10.rho(s, e0, e1),
                                       "vs_committed_rho": x2}
    chord = p10.chord(p10.BIG, p10.E0_PHASE8, 0.0)
    return rows, {"max_rel_slope": max(x1), "max_simplified_gap": max(x1b),
                  "x3_sign_agreement": all(x3), "x3_cells": len(x3),
                  "chord_big": chord, "chord_committed": committed["P8_1_slope"],
                  "chord_abs_diff": abs(chord - committed["P8_1_slope"]),
                  "n_rho_anchors": sum(1 for v in rows.values()
                                       if v["vs_committed_rho"] is not None),
                  "max_rho_vs_committed": max([v["vs_committed_rho"] for v in rows.values()
                                               if v["vs_committed_rho"] is not None] or [float("nan")])}


def run_x4_x5():
    e0m, e1m, val, meta = p10.minimax_deviation()
    full = p10.deviation(e0m, e1m, p10.S_GRID)
    tuned = p10.tune_e0_for_chord(-2.0, p10.BIG)
    alias = None
    if tuned is not None:
        alias = {"e0": tuned, "e1": 0.0,
                 "chord_big": p10.chord(p10.BIG, tuned, 0.0),
                 "max_local_dev_big": p10.deviation(tuned, 0.0, p10.BIG)}
    ca = p10.chord(p10.NEST_A, p10.E0_PHASE8, 0.0)
    cb = p10.chord(p10.NEST_B, p10.E0_PHASE8, 0.0)
    return {"minimax": {"e0": e0m, "e1": e1m, "value": val, "value_on_full_grid": full,
                        "search": meta, "floor": MINIMAX_FLOOR},
            "alias": alias, "nested": {"chord_3pt": ca, "chord_2pt": cb, "gap": abs(ca - cb),
                                       "floor": NEST_GAP}}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p10_gate.py")], capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    committed = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    t0 = time.time()
    rows, w = run_x1_x3(committed)
    t1 = time.time()
    rest = run_x4_x5()
    t2 = time.time()
    checks = {
        "X1_analytic_slope_matches_numeric": w["max_rel_slope"] <= TAU_X1,
        "X1b_simplified_form_matches": w["max_simplified_gap"] <= TAU_X1b,
        "X2a_rho_reproduces_committed_phase8": (w["n_rho_anchors"] == len(p10.S_GRID)
                                           and w["max_rho_vs_committed"] <= TAU_X2a),
        "X2b_chord_reproduces_committed_slope": w["chord_abs_diff"] <= TAU_X2b,
        "X3_two_correction_sign_law": w["x3_sign_agreement"],
        "X4_no_two_parameter_homogenisation": rest["minimax"]["value"] >= MINIMAX_FLOOR,
        "X5a_chord_can_be_faked": (rest["alias"] is not None
                                   and abs(rest["alias"]["chord_big"] + 2.0) <= ALIAS_CHORD
                                   and rest["alias"]["max_local_dev_big"] >= ALIAS_DEV),
        "X5b_nested_chords_differ": rest["nested"]["gap"] >= NEST_GAP,
    }
    core = all(checks[k] for k in ("X1_analytic_slope_matches_numeric",
                                   "X1b_simplified_form_matches",
                                   "X2a_rho_reproduces_committed_phase8",
                                   "X2b_chord_reproduces_committed_slope",
                                   "X3_two_correction_sign_law"))
    if not core:
        exit_label, why = "E4 FORMULA-WRONG", "X-1/X-2/X-3 failed: the closed form or the " \
                                            "reproduction of the committed readings is wrong"
    elif not checks["X4_no_two_parameter_homogenisation"]:
        exit_label, why = "E2 SMOOTHING-HOMOGENISES", "minimax below 0.01: a two-parameter " \
                                                      "additive law does flatten the exponent"
    elif not (checks["X5a_chord_can_be_faked"] and checks["X5b_nested_chords_differ"]):
        exit_label, why = "E3 NO-ALIASING", "X-5 failed: the chord exponent cannot be faked, " \
                                            "so P8-1 was a stronger test than assumed"
    elif all(checks.values()):
        exit_label, why = "E1 CONFIRMED", "X1-X5 all pass"
    else:
        exit_label, why = "E-UNMAPPED", "combination not covered by the registered exit table"
    payload = {"schema": "m2a.phase10.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE10_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "coeffs": COEFFS, "s_grid": list(p10.S_GRID), "big": list(p10.BIG),
               "nested": [list(p10.NEST_A), list(p10.NEST_B)],
               "tolerances": {"X1": TAU_X1, "X1b": TAU_X1b, "X2a": TAU_X2a, "X2b": TAU_X2b,
                              "X4_minimax_floor": MINIMAX_FLOOR, "X5a_chord": ALIAS_CHORD,
                              "X5a_dev_floor": ALIAS_DEV, "X5b_nested_gap": NEST_GAP},
               "rows": rows, "worst": w, "search": rest, "checks": checks,
               "exit": exit_label, "exit_reason": why,
               "verdict": "SUPPORTED" if exit_label.startswith("E1") else
                          ("QUALIFIED" if exit_label.startswith("E2") or
                                        exit_label.startswith("E3") else "REFUTED"),
               "runtime": {"seconds_x1_x3": round(t1 - t0, 1), "seconds_x4_x5": round(t2 - t1, 1),
                           "sampling": "none (closed form, bracketed roots, nested grid search)"}}
    json.dump(payload, open(HERE / "phase10_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nX1-X3 worst: {json.dumps({k: (round(v, 12) if isinstance(v, float) else v) for k, v in w.items()}, ensure_ascii=False)}")
    print(f"X4 minimax: value={rest['minimax']['value']:.6f} at (e0,e1)=({rest['minimax']['e0']}, "
          f"{rest['minimax']['e1']}) floor={MINIMAX_FLOOR} full_grid={rest['minimax']['value_on_full_grid']:.4f}")
    print(f"X5 alias: {json.dumps(rest['alias'], ensure_ascii=False)}")
    print(f"X5 nested: chord3={rest['nested']['chord_3pt']:.6f} chord2={rest['nested']['chord_2pt']:.6f} "
          f"gap={rest['nested']['gap']:.6f}")
    print(f"\nCHECKS: {json.dumps(checks)}")
    print(f"EXIT: {exit_label}  ({why})  verdict={payload['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
