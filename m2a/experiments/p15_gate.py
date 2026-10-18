"""Phase XV gate: instruments only (R2), and the floor this round judges against must be shown to be
the quantity its own name claims (G3), not a number copied out of context.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

import p12_lattice as p12
import p13_closeout as p13
import p15_identifiability as p15

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    c = p15.committed()
    s_grid, lam = c["s_grid"], c["lam"]

    # G1 anchor: re-running the committed joint search must land on the committed optimum bit-for-bit
    e0j, e1j, rmsj, _ = p13.fit_joint(s_grid, lam)
    rel = max(abs(rmsj - c["joint_rms"]) / c["joint_rms"], abs(e0j - c["joint_e0"]), abs(e1j - c["joint_e1"]))
    check("G1_joint_search_reproduces_committed_optimum", rel <= p15.ANCHOR_TOL,
          f"max rel {rel:.2e} (tol 1e-12) at e0={e0j:.9f} e1={e1j} rms={rmsj:.12f}")

    # G2 the two code paths for the same object agree: profile at e1=0 IS the committed single fit
    pr, e0p = p15.profile_e0(0.0, s_grid, lam)
    check("G2_profile_at_zero_equals_committed_single_fit",
          abs(pr - c["single_rms"]) / c["single_rms"] <= p15.ANCHOR_TOL and
          abs(e0p - c["single_e0"]) <= 1e-9,
          f"profile min {pr:.12f} vs committed single {c['single_rms']:.12f}, e0 {e0p:.9f}")

    # G3 the derived tie floor means what it says: recompute both one-step changes at the stored optimum
    d0 = abs(p13.rms_error(c["joint_e0"] + p15.STEP_E0, c["joint_e1"], s_grid, lam) - c["joint_rms"])
    d1 = abs(p13.rms_error(c["joint_e0"], c["joint_e1"] + p15.STEP_E1, s_grid, lam) - c["joint_rms"])
    worst = max(abs(d0 - c["d_e0"]) / c["d_e0"], abs(d1 - c["d_e1"]) / c["d_e1"])
    check("G3_tie_floor_is_the_committed_one_step_change", worst <= 1e-9,
          f"recomputed d_e0={d0:.6e} d_e1={d1:.6e} vs stored {c['d_e0']:.6e} {c['d_e1']:.6e} "
          f"(max rel {worst:.2e})")

    # G4 the C4 functional is anchored to the committed exponent, same subset and implementation
    exp_at_stored = float(p12.exponent(c["joint_e0"], p12.subset(s_grid, lam, p15.BIG_FROM), c["joint_e1"]))
    check("G4_chord_exponent_reproduces_committed_reading",
          abs(exp_at_stored - c["exp_joint_big"]) <= p15.ANCHOR_TOL,
          f"{exp_at_stored:.12f} vs committed {c['exp_joint_big']:.12f}")

    # G5 determinism of the two instruments the verdicts lean on
    a = p15.profile_e0(0.02, s_grid, lam)[0]
    b = p15.profile_e0(0.02, s_grid, lam)[0]
    e_a = p15.exponent_at(0.0, s_grid, lam)[0]
    e_b = p15.exponent_at(0.0, s_grid, lam)[0]
    check("G5_determinism", a == b and e_a == e_b, f"profile {a!r} and exponent {e_a!r} twice identical")

    # G6 R7: what is the smallest difference each of the two instruments could distinguish?
    T = p15.tie_floor(c)
    tiny = abs(p12.exponent(c["joint_e0"], p12.subset(s_grid, lam, p15.BIG_FROM), c["joint_e1"] + 1e-9) -
               exp_at_stored)
    check("G6_both_floors_reported", T > 0 and bool(np.isfinite(tiny)) and exp_at_stored < 0.0,
          f"RMS floor T = {T:.6e}; exponent instrument moves {tiny:.3e} for a 1e-9 nudge in e1 "
          f"(scientific tol {p15.EXP_TOL})")

    # G7 P15-A4: the bracket must be genuine, otherwise the endpoint would satisfy the criterion by
    #    construction - the exact R8 failure mode this amendment was written to remove
    val, unbounded, violator, viol_val = p15.e1_identified_set(c, T)
    genuine = (not unbounded) and violator is not None and 0.0 < val < violator
    check("G7_identified_set_bracket_is_genuine", genuine,
          f"e1_max = {val:.9f}, first violating grid point = {violator}, its profile - joint = "
          f"{None if viol_val is None else format(viol_val - c['joint_rms'], '.3e')} vs T = {T:.3e}")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
