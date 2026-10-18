"""Phase IX gate: instrument only. No science criterion from PHASE9_PREREGISTRATION.md appears here.

The checks are the four R1 items plus the wiring of the two k=2 theta_2 bisections:
compile/endpoints, level-set algebra against hand-computed multisets, agreement of the folded
count-matrix enumeration with a naive per-configuration loop, cross-artifact equality with the
committed single-channel law, monotonicity of the predicates the bisection assumes, that the free
instrument admits the known shared-threshold solution, and determinism.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

from p4_mechanisms import cdf, quantile
from p5_mechanisms import ALPHA, predicted_critical
from p7_systems import silent_side
import p9_aggregation as p9

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    # G1 endpoints and division-by-zero paths
    e = []
    e.append(p9.largest_subunit_level("product", 1, 0.0) == 0.0)
    e.append(p9.largest_subunit_level("godel", 1, 1.0) is None)
    e.append(p9.predicted_beta_agg("logistic", 2, 2, 1.0, "godel") == float("inf"))
    r = p9.critical_beta_agg("logistic", 2, 2, 1.0, "godel")
    e.append(r["beta"] == float("inf") and "nothing to silence" in r["reason"])
    r0 = p9.critical_beta_agg("logistic", 2, 1, 0.0, "product")
    e.append(np.isfinite(r0["beta"]) and r0["measurable"])
    e.append(p9.predicted_beta_agg("logistic", 2, 1, 0.0, "product")
             == (quantile((1 - ALPHA) ** 0.5, "logistic") - quantile(ALPHA / (1 - ALPHA) ** 0.5,
                                                                     "logistic")))
    check("G1_endpoints_and_divzero", all(e), f"{sum(e)}/{len(e)} endpoint paths ok "
                                             f"(s=1 unmeasurable-by-design, s=0 finite)")

    # G2 level-set multiset algebra against hand values
    hand = {("lukasiewicz", 3, 0.3): [0.0, 0.3, 1.0],
            ("godel", 4, 0.3): [0.3, 1.0],
            ("product", 3, 0.5): [0.125, 0.25, 0.5, 1.0],
            ("mean", 4, 0.5): [0.5, 0.625, 0.75, 0.875, 1.0]}
    bad = [(k, p9.agg_levels(*k), v) for k, v in hand.items() if p9.agg_levels(*k) != v]
    check("G2_level_set_algebra", not bad, f"4 hand multisets; mismatches {len(bad)}")

    # G3 folded enumeration == naive per-configuration product (independent code path)
    worst = 0.0
    for kind in ("logistic", "probit", "gumbel"):
        cfgs = p9.stage_configs_agg("product", 3, 2, 0.3)
        silent_cfgs = [c for c in cfgs if min(c) < 1.0 - 1e-12]
        thetas = np.linspace(-0.5, 1.5, 211)
        best, _ = silent_side(kind, 7.3, thetas, silent_cfgs, ALPHA)
        naive = np.max(np.vstack([
            np.prod(np.stack([np.asarray(cdf(7.3 * (d - thetas), kind), dtype=float)
                              for d in cfg], axis=0), axis=0)
            for cfg in silent_cfgs]), axis=0)
        worst = max(worst, float(np.max(np.abs(best - naive))))
    check("G3_count_fold_matches_naive_enumeration", worst <= 1e-14,
          f"max abs diff {worst:.2e} over 3 substrates")

    # G4 cross-artifact: k=1 must reduce to the committed Phase V single-channel law
    worst = 0.0
    for kind in ("logistic", "probit", "gumbel"):
        for s in (0.3, 0.5, 0.7):
            a = p9.predicted_beta_agg(kind, 1, 2, s, "lukasiewicz")
            b = predicted_critical(kind, 1.0 - s, ALPHA)
            worst = max(worst, abs(a - b) / b)
    check("G4_k1_reduces_to_committed_single_channel_law", worst <= 1e-12,
          f"max relative diff {worst:.2e} vs p5_mechanisms.predicted_critical")

    # G5 predicates the theta_2 bisection assumes are monotone on the box
    ok, beta = True, 12.0
    th = np.linspace(p9.THETA_LO, p9.THETA_HI, 4001)
    for kind in ("logistic", "probit", "gumbel"):
        u = np.asarray(cdf(beta * (1.0 - th), kind), dtype=float)
        v = np.asarray(cdf(beta * (0.3 - th), kind), dtype=float)
        if np.any(np.diff(u) > 1e-15) or np.any(np.diff(v) > 1e-15):
            ok = False
    check("G5_theta2_predicates_monotone", ok, "u2 and v2 non-increasing in theta_2 at beta=12")

    # G6 the free instrument admits the shared-threshold solution and its returned point really
    # satisfies all three constraints (recomputed independently)
    ok, worst = True, 0.0
    for kind in ("logistic", "probit", "gumbel"):
        for s in (0.3, 0.5, 0.7):
            shared = p9.shared_beta_numeric(kind, s, 2)
            th1 = np.linspace(p9.THETA_LO, p9.THETA_HI, 5001)
            det = p9._free_interval(kind, 1.1 * shared, th1, s, s, ALPHA)
            if det is None:
                ok = False
                continue
            u1 = float(cdf(1.1 * shared * (1.0 - det["theta1"]), kind))
            u2 = float(cdf(1.1 * shared * (1.0 - det["theta2"]), kind))
            v1 = float(cdf(1.1 * shared * (s - det["theta1"]), kind))
            v2 = float(cdf(1.1 * shared * (s - det["theta2"]), kind))
            worst = max(worst, abs(u1 * u2 - det["P"]), abs(v1 * u2 - det["r1"] * det["P"]))
            if not (u1 * u2 >= 1 - ALPHA - 1e-12 and v1 * u2 <= ALPHA + 1e-12
                    and v2 * u1 <= ALPHA + 1e-12):
                ok = False
    check("G6_free_instrument_admits_shared_solution", ok,
          f"reported P and r reproduce from theta at worst abs {worst:.2e}")

    # G7 determinism
    a = p9.critical_beta_agg("probit", 3, 2, 0.5, "lukasiewicz")["beta"]
    b = p9.critical_beta_agg("probit", 3, 2, 0.5, "lukasiewicz")["beta"]
    check("G7_determinism", a == b, f"{a:.6f} twice identical")

    # G8 regression anchor: product aggregation must reproduce the committed Phase VII readings
    import json
    committed = json.loads((pathlib.Path(__file__).resolve().parent /
                            "phase7_results.json").read_text(encoding="utf-8"))["rows"]
    worst, n_cells = 0.0, 0
    for key, row in committed.items():
        if not key.endswith("|graded0.5") or row["m"] != 2:
            continue
        got = p9.critical_beta_agg(row["kind"], row["k"], 2, 0.5, "product")["beta"]
        worst, n_cells = max(worst, abs(got - row["beta"])), n_cells + 1
    check("G8_product_cells_reproduce_committed_phase7", n_cells >= 3 and worst <= 1e-3,
          f"{n_cells} shared cells, max abs diff {worst:.2e}")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
