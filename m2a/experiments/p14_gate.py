"""Phase XIV gate: instruments only (R2). Every agreement reports the smallest difference it could
have distinguished (R7), because this round's whole point is that a tolerance must come from the
instrument rather than from the author.
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
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    committed = json.loads((HERE / "phase13_results.json").read_text(encoding="utf-8"))
    pk = committed["B"]["per_kind"]

    # G1 the anchor path is the committed path: same function, same k, same lo, bit-level agreement
    rel = {kind: abs(p14.closures(kind)["p13"] - pk[kind]["closure_beta"]) / pk[kind]["closure_beta"]
           for kind in p14.KINDS}
    check("G1_anchor_reproduces_committed_phase13", all(v <= 1e-9 for v in rel.values()),
          "rel " + ", ".join(f"{k}={v:.2e}" for k, v in rel.items()) + " (tol 1e-9)")

    # G2 the rate law as ALGEBRA, from the level definition alone: no measurement enters here.
    #    The committed p13.levels_gap rounds each level to 12 decimals, so the exact identity is only
    #    reachable to |d lo| <= 5e-13 and |d delta| <= 5e-13 * max(0.5/(1-lo)^2) = 1e-12 - six orders of
    #    magnitude below the smallest effect this round measures (1.25e-3 at J=800).
    e_lvl = max(abs(p14.level(J) - p14.level_closed_form(J)) for J in p14.JS)
    e_del = max(abs(p14.algebra_delta(J) - p14.exact_delta(J)) for J in p14.JS)
    check("G2_rate_law_is_an_algebraic_identity", e_lvl <= 5e-13 and e_del <= 1e-12,
          f"level err {e_lvl:.2e} (tol 5e-13, from round(.,12) in levels_gap), "
          f"delta err {e_del:.2e} (derived tol 1e-12)")

    # G3 the fixed grid at n=20001 IS the committed lo=0.50 grid, so the two instruments share their nodes
    n_expected = int(np.ceil((p14.THETA_HI - p14.THETA_LO) / (DTHETA_FACTOR * (1.0 - p14.SUP)))) + 1
    same = n_expected == p14.N_COARSE and np.array_equal(
        p14.thetas(p14.N_COARSE), np.linspace(p14.THETA_HI, p14.THETA_LO, p14.N_COARSE))
    check("G3_fixed_grid_matches_committed_sup_grid", same,
          f"n from DTHETA_FACTOR {n_expected}, registered n {p14.N_COARSE}")

    # G4 the bisection returns a straddling bracket, not an arbitrary point
    lo_b, hi_b, tol = p14.bracket("logistic", p14.K_ANCHOR, p14.SUP, p14.N_COARSE)
    check("G4_bisection_bracket_straddles",
          p14.feasible("logistic", hi_b, p14.SUP, p14.K_ANCHOR, p14.N_COARSE)
          and not p14.feasible("logistic", lo_b, p14.SUP, p14.K_ANCHOR, p14.N_COARSE)
          and hi_b - lo_b <= tol + 1e-18,
          f"bracket [{lo_b:.9f}, {hi_b:.9f}] width {hi_b - lo_b:.2e} (floor {tol:.0e})")

    # G5 the tightened instrument lands on the committed closure inside the ENVELOPE the two registered
    #    bisection floors imply (P14-A4 ii) - disclosure, not a scientific test
    worst, envelope = 0.0, {}
    for kind in p14.KINDS:
        c = p14.closures(kind)
        d = abs(c["coarse"] - c["p13"])
        envelope[kind] = c["p13_bisect_tol"]
        worst = max(worst, d - c["p13_bisect_tol"])
    check("G5_tightened_closure_inside_derived_envelope", worst <= 0.0,
          "max |delta| minus envelope " + f"{worst:.3e}, bisect floors "
          + ", ".join(f"{k}={v:.2e}" for k, v in envelope.items()))

    # G6 R7: state what each instrument can distinguish, before any verdict can lean on it
    c = p14.closures("logistic")
    floor_tight = p14.BISECT_TOL / c["coarse"]
    floor_committed = c["p13_bisect_tol"] / c["p13"]
    check("G6_resolution_floor_reported", floor_tight < floor_committed,
          f"relative beta floor: tightened {floor_tight:.2e} vs committed {floor_committed:.2e}; "
          f"smallest delta this round can distinguish is O({floor_tight:.1e}), "
          f"vs the smallest effect measured (J=800) {p14.exact_delta(800):.1e}")

    # G7 determinism
    a = p14.beta_star("logistic", p14.K_ANCHOR, p14.SUP, p14.N_FINE)
    b = p14.beta_star("logistic", p14.K_ANCHOR, p14.SUP, p14.N_FINE)
    check("G7_determinism", a == b, f"closure = {a!r} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
