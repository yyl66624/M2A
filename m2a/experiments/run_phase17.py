"""Run Phase XVII: judge the rate law and cross-k consistency under a tolerance that counts BOTH
discretisation layers (theta truncation and node density) - the requirement R13 turned into a runnable.

Gate first (R2). The anchor is cross-path by construction (P17-A2); the tolerance T17 is the instrument's
own two-layer shift times three; nothing here re-judges Phase XIV or XVI (R6).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import p17_twolayer as p17

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
PREREG = "PHASE17_PREREGISTRATION.md"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> int:
    r = subprocess.run([sys.executable, "p17_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def main() -> int:
    t0 = time.time()
    if run_gate() != 0:
        print("GATE FAILED - refusing to run Phase XVII (R2)")
        return 1

    ref = p17.committed_reference()
    sweeps = {(kind, k): p17.sweep(kind, k) for k in p17.KS for kind in p17.KINDS}

    anchor_rels = []
    for (kind, k), g in sweeps.items():
        for r in g["rows"]:
            key = (kind, k, r["J"])
            if key in ref:
                anchor_rels.append(abs(r["delta_committed"] - ref[key]) / abs(ref[key]))
    c17_1 = bool(anchor_rels and max(anchor_rels) <= p17.ANCHOR_TOL)

    all_rows = [(kind, k, r) for (kind, k), g in sweeps.items() for r in g["rows"]]
    L_max = max(r["L_total"] for _, _, r in all_rows)
    T17 = 3.0 * L_max

    c2_cells, unresolvable = [], []
    for kind, k, r in all_rows:
        ok = T17 <= r["delta_exact"]
        r["resolvable"] = bool(ok)
        r["abs_err_primary"] = float(abs(r["delta_primary"] - r["delta_exact"]))
        (c2_cells if ok else unresolvable).append(r["abs_err_primary"] <= T17)
        if not ok:
            r["abs_err_primary_over_T17"] = float(r["abs_err_primary"] / T17)
    c17_2 = "NOT_RESOLVED" if not c2_cells else ("PASS" if all(c2_cells) else "FAIL")

    c3_cells = []
    for kind, k, r in sorted(all_rows, key=lambda x: (x[0], x[1], x[2]["J"])):
        if k == 2:
            continue
        base = next(x for kk, k2, x in all_rows if kk == kind and k2 == 2 and x["J"] == r["J"])
        bound = 3.0 * (r["L_total"] + base["L_total"])
        gap = abs(r["delta_primary"] - base["delta_primary"])
        r["cross_k"] = {"gap_vs_k2": float(gap), "bound_two_layer": float(bound),
                        "ratio": float(gap / bound) if bound > 0 else None,
                        "ok": bool(gap <= bound)}
        c3_cells.append(gap <= bound)
    c17_3 = all(c3_cells) if c3_cells else False

    ratios = [r["cross_k"]["ratio"] for _, k, r in all_rows
              if k != 2 and "cross_k" in r and r["cross_k"]["ratio"] is not None]

    c4 = {}
    for (kind, k), g in sweeps.items():
        d = [r["delta_primary"] for r in g["rows"]]
        b = [r["beta_primary"] for r in g["rows"]]
        c4[f"{kind}@k{k}"] = bool(all(y < x for x, y in zip(d, d[1:]))
                                 and all(x < r["closure_primary"] for x, r in zip(b, g["rows"])))
    c17_4 = all(c4.values())

    if not c17_1:
        exit_name = "E0 ANCHOR-BROKEN"
    elif c17_2 == "PASS" and c17_3 and c17_4:
        exit_name = "E1 LAW-K-INVARIANT-UNDER-2LAYER"
    elif not c17_4:
        exit_name = "E4 DIRECTION-BROKEN"
    elif c17_2 == "FAIL":
        exit_name = "E3 LAW-WAS-AN-ARTIFACT"
    elif c17_2 == "PASS" and c17_4 and not c17_3:
        exit_name = "E2 TRUNCATION-NOT-THE-CULPRIT"
    else:
        exit_name = "E-UNMAPPED"

    n_closed = sum([c17_2 == "PASS", c17_3, c17_4, c17_1])
    res = {
        "schema": "m2a.phase17.results.v1",
        "prereg_sha256": sha256(HERE / PREREG),
        "configs": {"center": p17.CENTER, "halfwidths": list(p17.HS), "densities": list(p17.NS),
                    "primary": [p17.H_PRIM, p17.N_PRIM], "bisect_tol": p17.BISECT_TOL,
                    "js": list(p17.JS), "ks": list(p17.KS), "kinds": list(p17.KINDS)},
        "anchor": {"cells_compared": len(anchor_rels), "max_rel": float(max(anchor_rels)),
                   "tol": p17.ANCHOR_TOL, "pass": c17_1,
                   "note": "cross-path: independent p17 predicate vs committed p14/p16 readings (P17-A2)"},
        "tolerance": {"max_L_density": float(max(r["L_density"] for _, _, r in all_rows)),
                      "max_L_trunc": float(max(r["L_trunc"] for _, _, r in all_rows)),
                      "max_L_trunc_narrow": float(max(r["L_trunc_narrow"] for _, _, r in all_rows)),
                      "max_L_total": float(L_max), "T17": float(T17),
                      "derivation": "3 * max over all (kind,k,J) of (L_trunc + L_density), both layers (R13)"},
        "sweeps": {f"{kind}@k{k}": g for (kind, k), g in sweeps.items()},
        "c17_2": {"status": c17_2, "n_tested": len(c2_cells), "n_not_resolvable": len(unresolvable),
                  "max_abs_err": float(max(r["abs_err_primary"] for _, _, r in all_rows))},
        "c17_3": {"pass": c17_3, "n_cells": len(c3_cells),
                  "worst_ratio": max(ratios) if ratios else None,
                  "n_failed": sum(1 for x in c3_cells if not x)},
        "c17_4": {"per_group": c4, "pass": c17_4},
        "criteria": {"C17-1 ANCHOR": c17_1, "C17-2 LAW-HOLDS": c17_2 == "PASS",
                     "C17-3 CROSS-K-CONSISTENT": c17_3, "C17-4 DIRECTION": c17_4},
        "exits": {"E0 ANCHOR-BROKEN": not c17_1,
                  "E1 LAW-K-INVARIANT-UNDER-2LAYER": exit_name.startswith("E1"),
                  "E2 TRUNCATION-NOT-THE-CULPRIT": exit_name.startswith("E2"),
                  "E3 LAW-WAS-AN-ARTIFACT": exit_name.startswith("E3"),
                  "E4 DIRECTION-BROKEN": exit_name.startswith("E4"),
                  "E-UNMAPPED": exit_name == "E-UNMAPPED"},
        "exit": exit_name,
        "n_closed": int(n_closed),
        "verdict": f"{n_closed}/4 closed",
        "P14-O1": {"closed": bool(exit_name.startswith("E1")), "condition": "E1 registered before the run"},
        "runtime_s": round(time.time() - t0, 2),
    }
    (HERE / "phase17_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"\nanchor: {len(anchor_rels)} cells cross-path, max rel {max(anchor_rels):.2e} -> C17-1 {c17_1}")
    tc = res["tolerance"]
    print(f"layer magnitudes: density {tc['max_L_density']:.3e}  trunc(widen) {tc['max_L_trunc']:.3e}  "
          f"trunc(narrow) {tc['max_L_trunc_narrow']:.3e}  total {tc['max_L_total']:.3e} -> T17 = {T17:.3e}")
    print(f"C17-2 {c17_2} ({len(c2_cells)} tested, {len(unresolvable)} not resolvable), "
          f"max abs err {res['c17_2']['max_abs_err']:.3e}")
    print(f"C17-3 {c17_3}: {res['c17_3']['n_failed']}/{len(c3_cells)} cells over the two-layer bound, "
          f"worst ratio {res['c17_3']['worst_ratio']}")
    print(f"C17-4 {c17_4}")
    print(f"exit {exit_name} | verdict {res['verdict']} | P14-O1 closed {res['P14-O1']['closed']}")
    print(f"runtime {res['runtime_s']}s | prereg sha256 {res['prereg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
