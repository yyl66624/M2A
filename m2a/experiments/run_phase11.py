"""Run Phase XI: soft failure bands (XA1-XA4) and k=3 free thresholds (XB1-XB4).

Tolerances come from PHASE11_PREREGISTRATION.md as amended by P11-A1/A2/A3; they must not be edited
after running. The gate runs first and a failure refuses the round.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

from p5_mechanisms import ALPHA
import p11_softband as p11

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

KINDS = ("logistic", "probit", "gumbel")
MS = (2, 3)
KS = (2, 3)
TAUS = (0.3, 0.55, 0.7)
TAU_A = 0.002
SEP_NILPOTENT = 0.15         # half of the analytic 30% separation (P11-A2)
SEP_STEPPED = 0.03           # half of the analytic 6.67% separation
TAU_XB1 = 0.004
FLOOR_XB2 = 0.02
TAU_XB4 = 0.005
HETERO = [(0.3, 0.55, 0.7), (0.3, 0.3, 0.7), (0.3, 0.55, 0.55)]
N_DRAWS = 20_000


def analytic_L(name: str, tau: float) -> float:
    if name in p11.SURJECTIVE:
        return tau
    if name == "nilpotent":
        return 0.0 if tau <= 0.5 else tau
    return float(np.floor(tau / p11.STEP) * p11.STEP)


def run_a():
    rows, spread, skipped = {}, {}, []
    for kind in KINDS:
        for name in p11.AGGS:
            for m in MS:
                for k in KS:
                    for tau in TAUS:
                        L = p11.L_tau(name, m, tau)
                        r = p11.beta_star_band(kind, k, L)
                        naive = p11.predicted(kind, k, tau)
                        key = f"{kind}|{name}|{m}|{k}|{tau}"
                        if not r["measurable"]:
                            skipped.append({"cell": key, "reason": r["reason"]})
                            continue
                        rows[key] = {"L": L, "beta": r["beta"], "pred": r["pred"],
                                     "rel_vs_reachable": r["rel_diff"],
                                     "rel_vs_naive_tau": abs(r["beta"] - naive) / naive,
                                     "n_points": r["n_points"], "agg": name, "m": m, "k": k,
                                     "tau": tau, "kind": kind}
    for kind in KINDS:
        for k in KS:
            for tau in TAUS:
                cells = [v for v in rows.values() if v["agg"] in p11.SURJECTIVE
                         and v["kind"] == kind and v["k"] == k and v["tau"] == tau]
                b = [c["beta"] for c in cells]
                spread[f"{kind}|{k}|{tau}"] = {"n": len(b), "spread": float(max(b) - min(b)),
                                               "tol": TAU_A * float(np.mean([c["pred"] for c in cells]))}
    surj = [v for v in rows.values() if v["agg"] in p11.SURJECTIVE]
    sep = {"nilpotent|0.3": None, "stepped|0.3": None}
    for key, want in (("nilpotent|0.3", SEP_NILPOTENT), ("stepped|0.3", SEP_STEPPED)):
        name, tau = key.split("|")
        vals = [v for v in rows.values() if v["agg"] == name and v["tau"] == float(tau)]
        sep[key] = {"cells": len(vals), "max_rel_vs_reachable": max(v["rel_vs_reachable"] for v in vals),
                    "min_rel_vs_naive": min(v["rel_vs_naive_tau"] for v in vals), "floor": want,
                    "pass": (max(v["rel_vs_reachable"] for v in vals) <= TAU_A
                             and min(v["rel_vs_naive_tau"] for v in vals) >= want)}
    L_err = max(abs(p11.L_tau(name, m, tau) - analytic_L(name, tau))
                for name in p11.AGGS for m in MS for tau in TAUS)
    checks = {
        "XA1_band_tracks_reachable_sup": all(v["rel_vs_reachable"] <= TAU_A for v in surj),
        "XA2_spread_over_surjective_aggs": all(d["n"] >= 2 and d["spread"] <= d["tol"]
                                               for d in spread.values()),
        "XA3_enumerated_L_matches_analytic_range": L_err <= 0.01,
        "XA4_naive_tau_and_reachable_sup_separated": all(s["pass"] for s in sep.values()),
    }
    return {"rows": rows, "spread": spread, "sep": sep, "L_max_error": L_err,
            "n_cells": len(rows), "n_skipped": len(skipped), "skipped": skipped,
            "worst": {"XA1": max(v["rel_vs_reachable"] for v in surj),
                      "XA2_max_spread_ratio": max(d["spread"] / d["tol"] for d in spread.values()),
                      "XA3": L_err,
                      "nilpotent_rel_vs_naive": sep["nilpotent|0.3"]["min_rel_vs_naive"],
                      "stepped_rel_vs_naive": sep["stepped|0.3"]["min_rel_vs_naive"]},
            "checks": checks}


def run_b():
    rows = {}
    for kind in KINDS:
        for tau in TAUS:                                     # XB1 symmetric, k=3
            los = [tau] * 3
            shared = p11.beta_star_band(kind, 3, tau)["beta"]
            f = p11.beta_star_free(kind, los)
            rows[f"{kind}|sym|{tau}"] = {"kind": kind, "mode": "sym", "los": los,
                                         "beta_shared": shared, "beta_free": f["beta"],
                                         "rel": abs(f["beta"] - shared) / shared,
                                         "rho": f.get("rho"), "r": f.get("r")}
        for los in HETERO:                                   # XB2/XB3/XB4 heterogeneous
            f = p11.beta_star_free(kind, list(los))
            hi = max(los)
            shared = p11.beta_star_band(kind, 3, hi)["beta"]
            beta = f["beta"]
            # P11-A4: the optimum moves by ~0.02*(1-tau) when beta moves 2%, so the local box must
            # be several times that wide; 10*dtheta (=0.0002*(1-tau)*10) would miss it by design.
            half = 2.0 * 0.02 * (1.0 - hi)
            neg = p11.random_control(kind, 0.98 * beta, list(los), p11.SEEDS_XI, N_DRAWS)
            pos = p11.random_control(kind, 1.02 * beta, list(los), p11.SEEDS_XI, N_DRAWS,
                                     center=f["thetas"], half=half)
            rows[f"{kind}|het|{los[0]}|{los[1]}|{los[2]}"] = {
                "kind": kind, "mode": "het", "los": list(los), "beta_shared": shared,
                "beta_free": beta, "gain": shared - beta,
                "floor": max(FLOOR_XB2, 5 * TAU_XB1 * shared), "rho": f.get("rho"),
                "r": f.get("r"), "thetas": f.get("thetas"),
                "max_r_gap": float(max(abs(np.array(f["r"]) - f["rho"]))),
                "hits_below": neg, "hits_above": pos, "half_box": half}
    sym = [v for v in rows.values() if v["mode"] == "sym"]
    het = [v for v in rows.values() if v["mode"] == "het"]
    checks = {
        "XB1_k3_symmetric_free_equals_shared": all(v["rel"] <= TAU_XB1 for v in sym),
        "XB2_k3_heterogeneous_free_is_better": all(v["gain"] >= v["floor"] for v in het),
        "XB3_random_control_confirms_window_edge": all(v["hits_below"] == 0 and v["hits_above"] >= 1
                                                      for v in het),
        "XB4_k3_ratio_equalisation": all(v["max_r_gap"] <= TAU_XB4 for v in het),
    }
    return {"rows": rows, "checks": checks,
            "worst": {"XB1_max_rel": max(v["rel"] for v in sym),
                      "XB2_min_gain": min(v["gain"] for v in het),
                      "XB2_max_floor": max(v["floor"] for v in het),
                      "XB3_max_hits_below": max(v["hits_below"] for v in het),
                      "XB3_min_hits_above": min(v["hits_above"] for v in het),
                      "XB4_max_r_gap": max(v["max_r_gap"] for v in het)},
            "seed_pool": p11.SEEDS_XI,
            "seed_pool_disjoint": not set(p11.SEEDS_XI) & set(sum(p11.PRIOR_SEED_POOLS, []))}


def decide(A, B):
    if not (A["checks"]["XA1_band_tracks_reachable_sup"]
            and A["checks"]["XA2_spread_over_surjective_aggs"]
            and A["checks"]["XA3_enumerated_L_matches_analytic_range"]):
        return "E-ALPHA BROKEN", "XA1/XA2/XA3 failed: the soft-band reduction itself does not hold"
    if not A["checks"]["XA4_naive_tau_and_reachable_sup_separated"]:
        return "E2 NAIVE-TAU-WINS", "XA4 failed: discontinuous aggregators still follow the band edge"
    a_ok = all(A["checks"].values())
    if a_ok and not B["checks"]["XB1_k3_symmetric_free_equals_shared"]:
        return "E4 FREEDOM-K3-CHANGES", "XB1 failed with A intact"
    if a_ok and all(B["checks"][k] for k in ("XB1_k3_symmetric_free_equals_shared",
                                             "XB2_k3_heterogeneous_free_is_better")) \
            and not (B["checks"]["XB3_random_control_confirms_window_edge"]
                     and B["checks"]["XB4_k3_ratio_equalisation"]):
        return "E-UNMAPPED", "XB3/XB4 failed while XB1/XB2 passed - not covered by the table"
    if a_ok and all(B["checks"].values()):
        return "E1 CONFIRMED", "A and B groups all pass"
    return "E3 REACHABLE-SUP CONFIRMED", "XA4 passes but group B is not decisive"


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p11_gate.py")], capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    if not (set(p11.SEEDS_XI) & set(sum(p11.PRIOR_SEED_POOLS, []))):
        print("seed pool 2000-2019 asserted disjoint from prior pools (R4)")
    else:
        print("REFUSING TO RUN: seed pool overlaps a prior round")
        return 1
    t0 = time.time()
    A = run_a()
    t_a = time.time() - t0
    B = run_b()
    t_b = time.time() - t0 - t_a
    exit_label, why = decide(A, B)
    payload = {"schema": "m2a.phase11.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE11_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "alpha": ALPHA, "kinds": list(KINDS), "aggregators": list(p11.AGGS),
               "ms": list(MS), "ks": list(KS), "taus": list(TAUS), "n_axis": p11.N_AXIS,
               "tolerances": {"XA1": TAU_A, "XA2": TAU_A, "XA3": 0.01,
                              "XA4_nilpotent_floor": SEP_NILPOTENT, "XA4_stepped_floor": SEP_STEPPED,
                              "XB1": TAU_XB1, "XB2_floor": FLOOR_XB2, "XB4": TAU_XB4},
               "A": A, "B": B, "checks": {"A": A["checks"], "B": B["checks"]},
               "exit": exit_label, "exit_reason": why,
               "verdict": "SUPPORTED" if exit_label in ("E1 CONFIRMED", "E3 REACHABLE-SUP CONFIRMED")
                          else ("QUALIFIED" if exit_label.startswith("E4") else "REFUTED"),
               "runtime": {"seconds_a": round(t_a, 1), "seconds_b": round(t_b, 1),
                           "seed_pool": p11.SEEDS_XI, "n_draws": N_DRAWS}}
    json.dump(payload, open(HERE / "phase11_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nA: {A['n_cells']} cells (skipped {A['n_skipped']})  {A['checks']}")
    print(f"   worst={json.dumps({k: round(v, 6) for k, v in A['worst'].items()})}")
    print(f"B: {len(B['rows'])} cells  {B['checks']}")
    print(f"   worst={json.dumps({k: round(v, 6) for k, v in B['worst'].items()})} "
          f"seed_disjoint={B['seed_pool_disjoint']}")
    print(f"\nEXIT: {exit_label}  ({why})  verdict={payload['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
