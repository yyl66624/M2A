"""Phase XVI gate: instruments only (R2) - the round changes k, and must prove it changed nothing else.

Every agreement reports the smallest difference it could distinguish (R7), and the anchor is the
committed Phase XIV reading, not a fresh calculation of the same object.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from p5b_instrument import DTHETA_FACTOR
import p14_ratelaw as p14

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
KS = (3, 4)
ANCHOR_TOL = 1e-15
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    committed = json.loads((HERE / "phase14_results.json").read_text(encoding="utf-8"))
    pk14 = committed["per_kind"]

    # G1 the k=2 closure this round anchors to is the committed one, bit for bit
    rel = {kind: abs(p14.closures(kind, 2)["coarse"] - pk14[kind]["closure_coarse"]) / pk14[kind]["closure_coarse"]
           for kind in p14.KINDS}
    check("G1_anchor_reproduces_committed_phase14", all(v <= ANCHOR_TOL for v in rel.values()),
          "rel " + ", ".join(f"{k}={v:.2e}" for k, v in rel.items()) + f" (tol {ANCHOR_TOL:.0e})")

    # G2 the level set and the analytic target are the committed ones, unchanged
    same = all(r["lo"] == p14.level(r["J"]) and r["delta_exact"] == p14.exact_delta(r["J"])
               for kind in p14.KINDS for r in pk14[kind]["rows"])
    check("G2_levels_and_analytic_target_unchanged", same,
          "every committed (kind, J) row's lo and delta_exact re-derived identically")

    # G3 no inf/nan path at the bisection cap for the new k values
    feas = [p14.feasible(kind, 400.0, p14.level(J), k, p14.N_COARSE)
            for k in KS for kind in p14.KINDS for J in p14.JS]
    check("G3_closure_reachable_at_cap_for_new_k", all(feas), f"{sum(feas)}/{len(feas)} (kind, J, k) cells")

    # G4 the bisection still returns a straddling bracket at k = 3, 4
    straddle = []
    for k in KS:
        for kind in p14.KINDS:
            lo_b, hi_b, tol = p14.bracket(kind, k, p14.SUP, p14.N_COARSE)
            straddle.append(p14.feasible(kind, hi_b, p14.SUP, k, p14.N_COARSE)
                            and not p14.feasible(kind, lo_b, p14.SUP, k, p14.N_COARSE)
                            and hi_b - lo_b <= tol + 1e-18)
    check("G4_bisection_brackets_straddle_for_new_k", all(straddle), f"{sum(straddle)}/{len(straddle)} brackets")

    # G5 the grid this round reads on is the committed grid, derived again from the registered factor
    n_expected = int(np.ceil((p14.THETA_HI - p14.THETA_LO) / (DTHETA_FACTOR * (1.0 - p14.SUP)))) + 1
    check("G5_grid_unchanged", n_expected == p14.N_COARSE
          and np.array_equal(p14.thetas(p14.N_COARSE), np.linspace(p14.THETA_HI, p14.THETA_LO, p14.N_COARSE)),
          f"n from DTHETA_FACTOR {n_expected}, committed n {p14.N_COARSE}")

    # G6 R7: the resolution floor at the new k, stated before any verdict can lean on it
    floors = {}
    for k in KS:
        c = p14.closures("logistic", k)["coarse"]
        floors[k] = p14.BISECT_TOL / c
    smallest_effect = min(p14.exact_delta(J) for J in p14.JS)
    check("G6_resolution_floor_reported", all(v < 1e-9 for v in floors.values()),
          "relative beta floor " + ", ".join(f"k={k}: {v:.2e}" for k, v in floors.items())
          + f"; smallest effect measured {smallest_effect:.1e}")

    # G7 determinism at the new k
    a = p14.beta_star("logistic", 3, p14.level(40), p14.N_FINE)
    b = p14.beta_star("logistic", 3, p14.level(40), p14.N_FINE)
    check("G7_determinism", a == b, f"beta*(J=40, k=3) = {a!r} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
