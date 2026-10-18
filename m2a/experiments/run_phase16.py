"""Run Phase XVI: measure the rate law delta(J)=1/(J+2) at k = 3 and 4 (closes P14-O1).

Same instrument code as the committed Phase XIV round, same grids, same tolerance rule; only k changes.
C4 compares each cell against the committed k=2 reading using the two rounds' own refinement shifts,
so cross-k agreement is something the instruments have to earn rather than a restatement of the algebra.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import p14_ratelaw as p14

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
PREREG = "PHASE16_PREREGISTRATION.md"
KS = (3, 4)
ANCHOR_TOL = 1e-15


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> int:
    r = subprocess.run([sys.executable, "p16_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def main() -> int:
    t0 = time.time()
    if run_gate() != 0:
        print("GATE FAILED - refusing to run Phase XVI (R2)")
        return 1

    c14 = json.loads((HERE / "phase14_results.json").read_text(encoding="utf-8"))["per_kind"]

    anchor_rel = {kind: abs(p14.closures(kind, 2)["coarse"] - c14[kind]["closure_coarse"]) / c14[kind]["closure_coarse"]
                  for kind in p14.KINDS}
    xiv1 = bool(all(v <= ANCHOR_TOL for v in anchor_rel.values()))

    groups = {}
    for k in KS:
        for kind in p14.KINDS:
            g = {key: val for key, val in p14.grid_pair(kind, k).items()}
            g["rows"] = [dict(r) for r in g["rows"]]
            groups[f"{kind}@k{k}"] = g

    max_shift = float(max(r["shift"] for g in groups.values() for r in g["rows"]))
    T = 3.0 * max_shift

    resolvable, not_resolvable, c1_cells, c4_cells = [], [], [], []
    for name, g in groups.items():
        kind = g["kind"]
        for r in g["rows"]:
            ok = T <= r["delta_exact"]
            r["resolvable"] = bool(ok)
            (resolvable if ok else not_resolvable).append(name)
            if ok:
                c1_cells.append(r["abs_err_coarse"] <= T)
            ref = next(x for x in c14[kind]["rows"] if x["J"] == r["J"])
            bound = 3.0 * (r["shift"] + ref["shift"])
            gap = abs(r["delta_coarse"] - ref["delta_coarse"])
            r["cross_k"] = {"k2_delta": float(ref["delta_coarse"]), "k2_shift": float(ref["shift"]),
                            "gap": float(gap), "bound": float(bound), "ok": bool(gap <= bound)}
            c4_cells.append(gap <= bound)

    c1_n = len(c1_cells)
    c1 = "NOT_RESOLVED" if c1_n == 0 else ("PASS" if all(c1_cells) else "FAIL")
    c2, c3 = {}, {}
    for name, g in groups.items():
        d = [r["delta_coarse"] for r in g["rows"]]
        b = [r["beta_J_coarse"] for r in g["rows"]]
        c2[name] = bool(all(y < x for x, y in zip(d, d[1:])) and all(y >= x for x, y in zip(b, b[1:])))
        c3[name] = bool(all(r["beta_J_coarse"] < r["closure_coarse"] for r in g["rows"]))
    c2_all = all(c2.values())
    c3_all = all(c3.values())
    c4_all = all(c4_cells)

    if not xiv1:
        exit_name = "E0 ANCHOR-BROKEN"
    elif c1 == "PASS" and c2_all and c3_all and c4_all:
        exit_name = "E1 RATE-LAW-K-INVARIANT"
    elif c2_all and c3_all:
        exit_name = "E2 K-DEPENDENT-RESIDUAL"
    else:
        exit_name = "E3 NON-MONOTONE"
    n_closed = sum([c1 == "PASS", c2_all, c3_all, c4_all])
    ratios = [r["cross_k"]["gap"] / r["cross_k"]["bound"] for g in groups.values() for r in g["rows"]
              if r["cross_k"]["bound"] > 0.0]
    n_zero_bound = sum(1 for g in groups.values() for r in g["rows"] if r["cross_k"]["bound"] == 0.0)

    res = {
        "schema": "m2a.phase16.results.v1",
        "prereg_sha256": sha256(HERE / PREREG),
        "ks": list(KS),
        "grids": {"n_coarse": p14.N_COARSE, "n_fine": p14.N_FINE, "bisect_tol": p14.BISECT_TOL,
                  "js": list(p14.JS), "instrument": "p14_ratelaw.grid_pair (unchanged code path)"},
        "xiv1_anchor": {"rel_per_kind": {k: float(v) for k, v in anchor_rel.items()},
                        "tol": ANCHOR_TOL, "pass": xiv1},
        "tolerance": {"max_grid_shift": max_shift, "c1_tol": T,
                      "derivation": "3 * max shift over all (kind, k, J) cells of this round (P14-A1 rule)"},
        "groups": groups,
        "c1": {"status": c1, "n_tested": int(c1_n), "n_not_resolvable": len(not_resolvable),
               "not_resolvable": sorted(set(not_resolvable)),
               "max_abs_err": float(max(r["abs_err_coarse"] for g in groups.values() for r in g["rows"]))},
        "c2": {"per_group": c2, "pass": c2_all},
        "c3": {"per_group": c3, "pass": c3_all},
        "c4": {"pass": c4_all, "n_cells": len(c4_cells),
               "max_gap": float(max(r["cross_k"]["gap"] for g in groups.values() for r in g["rows"])),
               "max_gap_over_bound": float(max(ratios)) if ratios else None,
               "n_cells_zero_bound": int(n_zero_bound)},
        "criteria": {"C1 RATE-LAW-HOLDS": c1 == "PASS", "C2 MONOTONE": c2_all,
                     "C3 CONSERVATIVE": c3_all, "C4 CROSS-K-CONSISTENT": c4_all},
        "exits": {"E0 ANCHOR-BROKEN": not xiv1, "E1 RATE-LAW-K-INVARIANT": exit_name.startswith("E1"),
                  "E2 K-DEPENDENT-RESIDUAL": exit_name.startswith("E2"),
                  "E3 NON-MONOTONE": exit_name.startswith("E3"), "E-UNMAPPED": exit_name == "E-UNMAPPED"},
        "exit": exit_name,
        "n_closed": int(n_closed),
        "verdict": f"{n_closed}/4 closed",
        "P14-O1": {"closed": bool(exit_name.startswith("E1")),
                   "condition": "E1 registered before the run"},
        "runtime_s": round(time.time() - t0, 2),
    }
    (HERE / "phase16_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    for name, g in groups.items():
        print(f"\n{name}: closure {g['closure_coarse']:.9f} (fine {g['closure_fine']:.9f})")
        for r in g["rows"]:
            print(f"  J={r['J']:4d} delta_hat={r['delta_coarse']:.9f} exact={r['delta_exact']:.9f} "
                  f"err={r['abs_err_coarse']:.3e} shift={r['shift']:.3e} "
                  f"cross_k gap={r['cross_k']['gap']:.3e}/bound {r['cross_k']['bound']:.3e} "
                  f"{'OK' if r['resolvable'] else 'NOT_RESOLVABLE'}")
    print(f"\nanchor rel {max(anchor_rel.values()):.2e} -> XVI-1 {xiv1}")
    print(f"tolerance: max shift {max_shift:.3e} -> T = {T:.3e}")
    print(f"C1 {c1} ({c1_n} tested, {len(not_resolvable)} not resolvable), C2 {c2_all}, C3 {c3_all}, "
          f"C4 {c4_all} (max gap {res['c4']['max_gap']:.3e}, worst gap/bound {res['c4']['max_gap_over_bound']:.3f})")
    print(f"exit {exit_name} | verdict {res['verdict']} | P14-O1 closed {res['P14-O1']['closed']}")
    print(f"runtime {res['runtime_s']}s | prereg sha256 {res['prereg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
