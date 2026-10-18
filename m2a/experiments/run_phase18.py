"""Run Phase XVIII: judge cross-k consistency once aliasing has its own knob (closes P14-O1 / P17-O1).

Gate first (R2). Zero-bound cells are NOT floored and NOT excluded (P18-A2) - a bound of zero that a
reading difference violates is recorded as a failure, which is the conservative registered choice.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import p18_stagger as p18

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
PREREG = "PHASE18_PREREGISTRATION.md"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> int:
    r = subprocess.run([sys.executable, "p18_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def main() -> int:
    t0 = time.time()
    if run_gate() != 0:
        print("GATE FAILED - refusing to run Phase XVIII (R2)")
        return 1

    ref_a, ref_b = p18.committed_reference_all()
    sweeps = {(kind, k): p18.sweep(kind, k) for k in p18.KS for kind in p18.KINDS}
    rels = []
    for (kind, k), g in sweeps.items():
        for r in g["rows"]:
            key = (kind, k, r["J"])
            if key in ref_a:
                rels.append(abs(r["delta_committed"] - ref_a[key]) / abs(ref_a[key]))
            if key in ref_b:
                rels.append(abs(r["delta_revert_stagger"] - ref_b[key]) / abs(ref_b[key]))
    c18_1 = bool(rels and max(rels) <= p18.ANCHOR_TOL)

    all_rows = [(kind, k, r) for (kind, k), g in sweeps.items() for r in g["rows"]]
    L3_max = max(r["L3"] for _, _, r in all_rows)
    T18 = 3.0 * L3_max

    c2_cells, unresolvable = [], []
    for kind, k, r in all_rows:
        r["abs_err_primary"] = float(abs(r["delta_primary"] - r["delta_exact"]))
        ok = T18 <= r["delta_exact"]
        r["resolvable"] = bool(ok)
        (c2_cells if ok else unresolvable).append(r["abs_err_primary"] <= T18)
    c18_2 = "NOT_RESOLVED" if not c2_cells else ("PASS" if all(c2_cells) else "FAIL")

    c3_cells, zero_bound = [], []
    for kind, k, r in sorted(all_rows, key=lambda x: (x[0], x[1], x[2]["J"])):
        if k == 2:
            continue
        base = next(x for kk, k2, x in all_rows if kk == kind and k2 == 2 and x["J"] == r["J"])
        bound = 3.0 * (r["L3"] + base["L3"])
        gap = abs(r["delta_primary"] - base["delta_primary"])
        ok = bool(gap <= bound)
        r["cross_k"] = {"gap_vs_k2": float(gap), "bound_three_layer": float(bound),
                        "ratio": float(gap / bound) if bound > 0 else None, "ok": ok}
        c3_cells.append(ok)
        if bound == 0.0:
            zero_bound.append([f"{kind}@k{k}", int(r["J"]), float(gap)])

    c4 = {}
    for (kind, k), g in sweeps.items():
        d = [r["delta_primary"] for r in g["rows"]]
        b = [r["beta_primary"] for r in g["rows"]]
        c4[f"{kind}@k{k}"] = bool(all(y < x for x, y in zip(d, d[1:]))
                                 and all(x < r["closure_primary"] for x, r in zip(b, g["rows"])))
    c18_4 = all(c4.values())
    ratios = [r["cross_k"]["ratio"] for _, k, r in all_rows
              if k != 2 and "cross_k" in r and r["cross_k"]["ratio"] is not None]
    c18_3 = all(c3_cells) if c3_cells else False

    if not c18_1:
        exit_name = "E0 ANCHOR-BROKEN"
    elif c18_2 == "PASS" and c18_3 and c18_4:
        exit_name = "E1 LAW-K-INVARIANT-UNDER-3LAYER"
    elif not c18_4:
        exit_name = "E4 DIRECTION-BROKEN"
    elif c18_2 == "FAIL":
        exit_name = "E3 LAW-FAILS-AT-PRIMARY"
    elif c18_2 == "PASS" and c18_4 and not c18_3:
        exit_name = "E2 ALIASING-BOUNDS-FAIL"
    else:
        exit_name = "E-UNMAPPED"

    n_closed = sum([c18_1, c18_2 == "PASS", c18_3, c18_4])
    res = {
        "schema": "m2a.phase18.results.v1",
        "prereg_sha256": sha256(HERE / PREREG),
        "configs": {"center": p18.CENTER, "primary": list(p18.PRIMARY),
                    "revert_density": list(p18.REVERT_DENSITY), "revert_trunc": list(p18.REVERT_TRUNC),
                    "revert_stagger": list(p18.REVERT_STAGGER), "committed": list(p18.COMMITTED),
                    "bisect_tol": p18.BISECT_TOL, "js": list(p18.JS), "ks": list(p18.KS)},
        "anchor": {"comparisons": len(rels), "max_rel": float(max(rels)), "tol": p18.ANCHOR_TOL,
                   "pass": c18_1, "note": "cross-path against phase14/16 (sigma=0,h=1) and phase17 primary"},
        "tolerance": {"max_L_density": float(max(r["L_density"] for _, _, r in all_rows)),
                      "max_L_trunc": float(max(r["L_trunc"] for _, _, r in all_rows)),
                      "max_L_stagger": float(max(r["L_stagger"] for _, _, r in all_rows)),
                      "max_L3": float(L3_max), "T18": float(T18),
                      "derivation": "3 * max over all (kind,k,J) of (L_density + L_trunc + L_stagger)"},
        "sweeps": {f"{kind}@k{k}": g for (kind, k), g in sweeps.items()},
        "c18_2": {"status": c18_2, "n_tested": len(c2_cells), "n_not_resolvable": len(unresolvable),
                  "max_abs_err": float(max(r["abs_err_primary"] for _, _, r in all_rows))},
        "c18_3": {"pass": c18_3, "n_cells": len(c3_cells), "n_failed": sum(1 for x in c3_cells if not x),
                  "worst_ratio": max(ratios) if ratios else None,
                  "zero_bound_cells": zero_bound},
        "c18_4": {"per_group": c4, "pass": c18_4},
        "criteria": {"C18-1 ANCHOR": c18_1, "C18-2 LAW-HOLDS": c18_2 == "PASS",
                     "C18-3 CROSS-K-CONSISTENT": c18_3, "C18-4 DIRECTION": c18_4},
        "exits": {"E0 ANCHOR-BROKEN": not c18_1, "E1 LAW-K-INVARIANT-UNDER-3LAYER": exit_name.startswith("E1"),
                  "E2 ALIASING-BOUNDS-FAIL": exit_name.startswith("E2"),
                  "E3 LAW-FAILS-AT-PRIMARY": exit_name.startswith("E3"),
                  "E4 DIRECTION-BROKEN": exit_name.startswith("E4"),
                  "E-UNMAPPED": exit_name == "E-UNMAPPED"},
        "exit": exit_name,
        "n_closed": int(n_closed),
        "verdict": f"{n_closed}/4 closed",
        "P14-O1": {"closed": bool(exit_name.startswith("E1")), "condition": "E1 registered before the run"},
        "runtime_s": round(time.time() - t0, 2),
    }
    (HERE / "phase18_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    tc = res["tolerance"]
    print(f"\nanchor: {len(rels)} cross-path comparisons, max rel {max(rels):.2e} -> C18-1 {c18_1}")
    print(f"layer magnitudes: density {tc['max_L_density']:.3e}  trunc {tc['max_L_trunc']:.3e}  "
          f"stagger {tc['max_L_stagger']:.3e}  L3 {tc['max_L3']:.3e} -> T18 = {T18:.3e}")
    print(f"C18-2 {c18_2} ({len(c2_cells)} tested, {len(unresolvable)} not resolvable), "
          f"max abs err {res['c18_2']['max_abs_err']:.3e}")
    print(f"C18-3 {c18_3}: {res['c18_3']['n_failed']}/{len(c3_cells)} over the three-layer bound, "
          f"worst ratio {res['c18_3']['worst_ratio']}, zero-bound cells {len(zero_bound)}")
    print(f"C18-4 {c18_4}")
    print(f"exit {exit_name} | verdict {res['verdict']} | P14-O1 closed {res['P14-O1']['closed']}")
    print(f"runtime {res['runtime_s']}s | prereg sha256 {res['prereg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
