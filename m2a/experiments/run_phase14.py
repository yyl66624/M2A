"""Run Phase XIV: is the unattained-supremum degeneracy governed by the exact rate law delta(J)=1/(J+2)?

Gate first (R2), then the registered criteria with P14-A1..A6 applied. The tolerance is the instrument's
own grid-refinement shift times three, never a number chosen after seeing the residuals. Exits are
reported independently, with a NOT_RESOLVED guard so a zero-cell test cannot buy E1 or E2 (P14-A6).
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
PREREG = "PHASE14_PREREGISTRATION.md"
ANCHOR_TOL = 1e-9


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> int:
    r = subprocess.run([sys.executable, "p14_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def main() -> int:
    t0 = time.time()
    code = run_gate()
    if code != 0:
        print("GATE FAILED - refusing to run Phase XIV (R2)")
        return 1

    committed = json.loads((HERE / "phase13_results.json").read_text(encoding="utf-8"))
    pk = committed["B"]["per_kind"]

    groups = {}
    for kind in p14.KINDS:
        g = {k: v for k, v in p14.grid_pair(kind).items()}
        g["rows"] = [dict(r) for r in g["rows"]]
        anchor_rel = abs(g["closure_p13"] - pk[kind]["closure_beta"]) / pk[kind]["closure_beta"]
        cross = abs(g["closure_coarse"] - g["closure_p13"])
        g["anchor_rel"] = float(anchor_rel)
        g["anchor_pass"] = bool(anchor_rel <= ANCHOR_TOL)
        g["cross_shift"] = float(cross)
        g["cross_within_envelope"] = bool(cross <= g["p13_bisect_tol"])
        groups[kind] = g

    max_shift = float(max(r["shift"] for g in groups.values() for r in g["rows"]))
    tol = 3.0 * max_shift

    resolvable, not_resolvable, xiv1_cells = [], [], []
    for kind, g in groups.items():
        for r in g["rows"]:
            ok = tol <= r["delta_exact"]
            r["resolvable"] = bool(ok)
            r["abs_err_over_tol"] = float(r["abs_err_coarse"] / tol)
            (resolvable if ok else not_resolvable).append((kind, r["J"]))
            if ok:
                xiv1_cells.append(r["abs_err_coarse"] <= tol)

    x1_n = len(xiv1_cells)
    x1 = "NOT_RESOLVED" if x1_n == 0 else ("PASS" if all(xiv1_cells) else "FAIL")

    x2_kinds, x3_kinds = {}, {}
    for kind, g in groups.items():
        d = [r["delta_coarse"] for r in g["rows"]]
        b = [r["beta_J_coarse"] for r in g["rows"]]
        x2_kinds[kind] = bool(all(y < x for x, y in zip(d, d[1:])) and all(y >= x for x, y in zip(b, b[1:])))
        x3_kinds[kind] = bool(all(r["beta_J_coarse"] < r["closure_coarse"] for r in g["rows"]))
    x2 = all(x2_kinds.values())
    x3 = all(x3_kinds.values())
    x4 = all(g["anchor_pass"] for g in groups.values())

    if not x4:
        exit_name = "E0 ANCHOR-BROKEN"
    elif x1 == "PASS" and x2 and x3:
        exit_name = "E1 RATE-LAW EXACT"
    elif (x2 and x3) and x1 == "FAIL":
        exit_name = "E2 RATE-LAW-WRONG"
    elif not (x2 and x3):
        exit_name = "E3 NON-MONOTONE"
    else:
        exit_name = "E-UNMAPPED"

    n_closed = sum([x1 == "PASS", x2, x3, x4])
    res = {
        "schema": "m2a.phase14.results.v1",
        "prereg_sha256": sha256(HERE / PREREG),
        "k": p14.K_ANCHOR,
        "grids": {"n_coarse": p14.N_COARSE, "n_fine": p14.N_FINE,
                  "theta_lo": p14.THETA_LO, "theta_hi": p14.THETA_HI,
                  "bisect_tol": p14.BISECT_TOL, "js": list(p14.JS)},
        "tolerance": {"max_grid_shift": max_shift, "xiv1_tol": tol,
                      "derivation": "P14-A1: 3 * max over all (kind, J) cells of |delta(20001) - delta(40001)|",
                      "anchor_tol": ANCHOR_TOL},
        "per_kind": groups,
        "xiv1": {"status": x1, "n_tested": int(x1_n),
                 "n_not_resolvable": len(not_resolvable),
                 "not_resolvable": [[k, int(j)] for k, j in not_resolvable],
                 "max_abs_err": float(max(r["abs_err_coarse"] for g in groups.values() for r in g["rows"])),
                 "max_abs_err_resolvable": float(max([r["abs_err_coarse"] for g in groups.values()
                                                      for r in g["rows"] if r["resolvable"]], default=0.0))},
        "xiv2": {"per_kind": x2_kinds, "pass": bool(x2)},
        "xiv3": {"per_kind": x3_kinds, "pass": bool(x3)},
        "xiv4": {"anchor_rel_per_kind": {k: float(g["anchor_rel"]) for k, g in groups.items()},
                 "cross_instrument": {k: {"shift": float(g["cross_shift"]),
                                          "derived_envelope": float(g["p13_bisect_tol"]),
                                          "inside": g["cross_within_envelope"]} for k, g in groups.items()},
                 "pass": bool(x4)},
        "exits": {"E0 ANCHOR-BROKEN": not x4, "E1 RATE-LAW EXACT": exit_name.startswith("E1"),
                  "E2 RATE-LAW-WRONG": exit_name.startswith("E2"), "E3 NON-MONOTONE": exit_name.startswith("E3"),
                  "E-UNMAPPED": exit_name == "E-UNMAPPED"},
        "exit": exit_name,
        "n_closed": int(n_closed),
        "verdict": f"{n_closed}/4 closed",
        "phase13_reference": {"closure_beta": {k: float(pk[k]["closure_beta"]) for k in p14.KINDS},
                              "B1_pass": bool(committed["B"]["B1"]),
                              "revives": "P13-O1"},
        "runtime_s": round(time.time() - t0, 2),
    }
    (HERE / "phase14_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    for kind, g in groups.items():
        print(f"\n{kind}: closure coarse {g['closure_coarse']:.9f} fine {g['closure_fine']:.9f} "
              f"committed {g['closure_p13']:.9f} (anchor rel {g['anchor_rel']:.2e})")
        for r in g["rows"]:
            print(f"  J={r['J']:4d} lo={r['lo']:.12f} beta_J={r['beta_J_coarse']:.9f} "
                  f"delta_hat={r['delta_coarse']:.9f} exact={r['delta_exact']:.9f} "
                  f"err={r['abs_err_coarse']:.3e} shift={r['shift']:.3e} "
                  f"{'OK' if r['resolvable'] else 'NOT_RESOLVABLE'}")
    print(f"\ntolerance: max grid shift {max_shift:.3e} -> XIV-1 tol {tol:.3e}")
    print(f"XIV-1 {x1} ({x1_n} tested, {len(not_resolvable)} not resolvable), "
          f"XIV-2 {x2}, XIV-3 {x3}, XIV-4 {x4}")
    print(f"exit {exit_name} | verdict {res['verdict']} | runtime {res['runtime_s']}s")
    print(f"prereg sha256 {res['prereg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
