"""Phase XVII gate: instruments only (R2). The anchor must be cross-path (P17-A2) and the resolution
statement must cover BOTH layers, since the point of this round is that a density-only shift miscounted.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

import p14_ratelaw as p14
import p17_twolayer as p17

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    ref = p17.committed_reference()
    sweeps = {(kind, k): p17.sweep(kind, k) for k in p17.KS for kind in p17.KINDS}

    # G1+G2 the new independent implementation degenerates to the committed readings bit for bit
    for label, ks in (("G1_anchor_k2_vs_committed_phase14", (2,)),
                      ("G2_anchor_k3k4_vs_committed_phase16", (3, 4))):
        rels, n = [], 0
        for k in ks:
            for kind in p17.KINDS:
                for r in sweeps[(kind, k)]["rows"]:
                    key = (kind, k, r["J"])
                    if key in ref:
                        n += 1
                        rels.append(abs(r["delta_committed"] - ref[key]) / abs(ref[key]))
        worst = max(rels) if rels else float("inf")
        check(label, worst <= p17.ANCHOR_TOL,
              f"{n} cells compared across code paths, worst rel {worst:.2e} (tol {p17.ANCHOR_TOL:.0e})")

    # G3 at h = 1.0 the node set IS the committed instrument's node set, exactly
    same = all(np.array_equal(p17.nodes(1.0, n), p14.thetas(n)) for n in p17.NS)
    check("G3_nodes_at_committed_halfwidth_identical", same,
          "np.array_equal against p14_ratelaw.thetas for n = 20001 and 40001")

    # G4 no infinite path at the primary config: the cap is feasible everywhere
    feas = [p17.feasible(kind, 400.0, p17.level(J), k, p17.H_PRIM, p17.N_PRIM)
            for k in p17.KS for kind in p17.KINDS for J in p17.JS]
    check("G4_cap_feasible_at_primary_config", all(feas), f"{sum(feas)}/{len(feas)} cells")

    # G5 the bisection still returns a straddling bracket at the primary config, for every (kind, k)
    strad = []
    for k in p17.KS:
        for kind in p17.KINDS:
            c = sweeps[(kind, k)]["rows"][0]["closure_primary"]
            strad.append(p17.feasible(kind, c, p17.SUP, k, p17.H_PRIM, p17.N_PRIM)
                         and not p17.feasible(kind, c - 2e-9, p17.SUP, k, p17.H_PRIM, p17.N_PRIM))
    check("G5_bracket_straddles_at_primary_config", all(strad), f"{sum(strad)}/{len(strad)} (kind,k) closures")

    # G6 R7: state both layers' smallest distinguishable difference before any verdict leans on them
    spac = {(h, n): 2.0 * h / (n - 1) for h in p17.HS for n in p17.NS}
    check("G6_both_layer_floors_reported", spac[(1.0, 40001)] < spac[(1.0, 20001)]
          and spac[(2.0, 40001)] < spac[(2.0, 20001)],
          "dtheta " + ", ".join(f"h{h}/n{n}={v:.1e}" for (h, n), v in sorted(spac.items()))
          + f"; beta floor 1e-9 absolute (rel ~{1e-9/14.5:.1e})")

    # G7 determinism
    a = p17.beta_star("logistic", 3, p17.level(40), p17.H_PRIM, p17.N_PRIM)
    b = p17.beta_star("logistic", 3, p17.level(40), p17.H_PRIM, p17.N_PRIM)
    check("G7_determinism", a == b, f"beta_primary(J=40,k=3) = {a!r} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
