"""Phase XVIII gate: instruments only (R2). The whole point of the stagger knob is that sigma=0 must be
the committed instrument, so the anchors are cross-path against three prior rounds' stored readings.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

import p17_twolayer as p17
import p18_stagger as p18

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    ref_a, ref_b = p18.committed_reference_all()
    sweeps = {(kind, k): p18.sweep(kind, k) for k in p18.KS for kind in p18.KINDS}

    rels_a, rels_b = [], []
    for (kind, k), g in sweeps.items():
        for r in g["rows"]:
            key = (kind, k, r["J"])
            if key in ref_a:
                rels_a.append(abs(r["delta_committed"] - ref_a[key]) / abs(ref_a[key]))
            if key in ref_b:
                rels_b.append(abs(r["delta_revert_stagger"] - ref_b[key]) / abs(ref_b[key]))
    check("G1_anchor_vs_committed_phase14_phase16", bool(rels_a) and max(rels_a) <= p18.ANCHOR_TOL,
          f"{len(rels_a)} cells at (h=1.0, n=20001, sigma=0), worst rel {max(rels_a):.2e} (tol 1e-15)")
    check("G2_anchor_vs_committed_phase17_primary", bool(rels_b) and max(rels_b) <= p18.ANCHOR_TOL,
          f"{len(rels_b)} cells at (h=2.0, n=40001, sigma=0), worst rel {max(rels_b):.2e} (tol 1e-15)")

    # G3 sigma really is the only thing that moves: the shifted set is the unshifted set minus sigma*dtheta
    ok = all(np.array_equal(p18.nodes(h, n, 0.0), p17.nodes(h, n)) for h in (1.0, 2.0) for n in (20001, 40001))
    ok = ok and all(np.max(np.abs(p18.nodes(h, n, 0.5) - (p18.nodes(h, n, 0.0) - 0.5 * p18.dtheta(h, n)))) == 0.0
                   for h in (1.0, 2.0) for n in (20001, 40001))
    check("G3_stagger_is_a_pure_translation", bool(ok),
          "sigma=0 arrays equal p17.nodes, and sigma=0.5 equals sigma=0 shifted by dtheta/2 exactly")

    feas = [p18.feasible(kind, 400.0, p18.level(J), k, p18.PRIMARY)
            for k in p18.KS for kind in p18.KINDS for J in p18.JS]
    check("G4_cap_feasible_at_primary_config", all(feas), f"{sum(feas)}/{len(feas)} cells")

    strad = []
    for k in p18.KS:
        for kind in p18.KINDS:
            c = p18.beta_star(kind, k, p18.SUP, p18.PRIMARY)
            strad.append(p18.feasible(kind, c, p18.SUP, k, p18.PRIMARY)
                         and not p18.feasible(kind, c - 2e-9, p18.SUP, k, p18.PRIMARY))
    check("G5_bracket_straddles_at_primary_config", all(strad), f"{sum(strad)}/{len(strad)} closures")

    floors = {(h, n): p18.dtheta(h, n) for h in (1.0, 2.0) for n in (20001, 40001)}
    check("G6_layer_floors_reported", all(v > 0 for v in floors.values()),
          "dtheta " + ", ".join(f"h{h}/n{n}={v:.2e}" for (h, n), v in sorted(floors.items()))
          + f"; shift probe = dtheta/2; beta floor 1e-9 absolute")

    a = p18.beta_star("logistic", 3, p18.level(40), p18.PRIMARY)
    b = p18.beta_star("logistic", 3, p18.level(40), p18.PRIMARY)
    check("G7_determinism", a == b, f"beta_primary(J=40,k=3) = {a!r} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
