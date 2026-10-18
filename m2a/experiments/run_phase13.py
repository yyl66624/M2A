"""Run Phase XIII: convention bracket (A), unattained supremum (B), k=4 freedom (C), joint fit (D).

Criteria as registered in PHASE13_PREREGISTRATION.md with P13-A1..A5 applied. Exits are reported
independently (closed count / 4) rather than as one conjunction - the X-11 lesson.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

from p4_mechanisms import quantile
from p5_mechanisms import ALPHA
from p6_systems import Z95
from p8_smooth import C1
import p11_softband as p11
import p12_lattice as p12
import p13_closeout as p13

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

CF = (Z95 ** 2 - 1.0) / 6.0
A1_BAND = (1.0, 2.0)
A2_FLAT = 0.01
A3_BAND = 0.05
B1_TOL = 0.002
B3_TOL = 0.002
C1_TOL = 0.004
C4_TOL = 5e-4
D3_FLOOR = 0.05
D4_TOL = 1e-9
JS = (1, 2, 5, 10, 20, 40, 100, 200)
KINDS = ("logistic", "probit", "gumbel")


def run_a():
    rows = {}
    for l in p13.LAMBDAS:
        D, C = p13.offsets(l)
        rows[str(l)] = {"m_ge": p13.m_ge(l), "q_cont": p13.q_cont(l), "D": D, "C": C,
                        "D_minus_C": D - C, "in_band": bool(A1_BAND[0] <= D - C < A1_BAND[1]),
                        "C_vs_cf_minus_half": abs(C - (CF - 0.5))}
    Cs = [v["C"] for v in rows.values()]
    fitted_per_side = 0.53 / 2.0
    return {"rows": rows, "A1": bool(all(v["in_band"] for v in rows.values())),
            "A2_spread": float(max(Cs) - min(Cs)), "A2": bool((max(Cs) - min(Cs)) <= A2_FLAT),
            "A3_max_err": max(v["C_vs_cf_minus_half"] for v in rows.values()),
            "A3": bool(max(v["C_vs_cf_minus_half"] for v in rows.values()) <= A3_BAND),
            "A4_disclose": {"cf_2sided": 2 * CF, "cf_minus_lattice_2sided": 2 * (CF - 0.5),
                            "phase8_2sided": 2 * C1,
                            "fitted_per_side": fitted_per_side,
                            "dist_to_cf": abs(fitted_per_side - CF),
                            "dist_to_cf_minus_half": abs(fitted_per_side - (CF - 0.5))},
            "band": list(A1_BAND), "a2_floor": A2_FLAT, "a3_band": A3_BAND}


def run_b():
    out = {}
    for kind in KINDS:
        closure = p11.beta_star_band(kind, 2, p13.SUP)
        seq = []
        for J in JS:
            lo = p13.attained_lo(J)
            r = p11.beta_star_band(kind, 2, lo)
            seq.append({"J": J, "lo": lo, "beta": r["beta"], "gap_to_closure": closure["beta"] - r["beta"]})
        mono = all(b["beta"] >= a["beta"] - 1e-12 for a, b in zip(seq, seq[1:]))
        conv = abs(seq[-1]["beta"] - closure["beta"]) / closure["beta"] <= B1_TOL
        strict = [not p13.feasible_at(kind, s["beta"], p13.SUP, 2) for s in seq[1:]]
        b3 = abs(closure["beta"] - closure["pred"]) / closure["pred"] <= B3_TOL
        out[kind] = {"closure_beta": closure["beta"], "closure_pred": closure["pred"],
                    "seq": seq, "B1_monotone_nondec": mono, "B1_converged_within_0002": conv,
                    "B2_closure_infeasible_at_attained": all(strict), "B3_formula": b3}
    return {"per_kind": out,
            "B1": all(v["B1_monotone_nondec"] and v["B1_converged_within_0002"] for v in out.values()),
            "B2": all(v["B2_closure_infeasible_at_attained"] for v in out.values()),
            "B3": all(v["B3_formula"] for v in out.values())}


def run_c():
    rows = {}
    for kind in KINDS:
        for tau in p13.TAUS:
            los = [tau] * 4
            f = p11.beta_star_free(kind, los)
            shared = p11.beta_star_band(kind, 4, tau)["beta"]
            rows[f"{kind}|sym|{tau}"] = {"mode": "sym", "los": los, "beta_free": f["beta"],
                                         "beta_shared": shared,
                                         "rel_free_vs_shared": abs(f["beta"] - shared) / shared,
                                         "rho": f.get("rho"), "r": f.get("r")}
        for los in p13.K4_HETERO:
            f = p11.beta_star_free(kind, list(los))
            hi = max(los)
            shared = p11.beta_star_band(kind, 4, hi)["beta"]
            beta = f["beta"]
            half = 2.0 * 0.02 * (1.0 - hi)
            neg = p11.random_control(kind, 0.98 * beta, list(los), p13.SEEDS_XIII, p13.N_DRAWS)
            pos = p11.random_control(kind, 1.02 * beta, list(los), p13.SEEDS_XIII, p13.N_DRAWS,
                                     center=f["thetas"], half=half)
            rows[f"{kind}|het|{los}"] = {"mode": "het", "los": list(los), "beta_free": beta,
                                         "beta_shared": shared, "gain": shared - beta,
                                         "floor": max(0.02, 0.02 * shared), "rho": f.get("rho"),
                                         "r": f.get("r"), "hits_below": neg, "hits_above": pos,
                                         "half_box": half}
    sym = [v for v in rows.values() if v["mode"] == "sym"]
    het = [v for v in rows.values() if v["mode"] == "het"]
    c4 = max(v["rel_free_vs_shared"] for v in sym)
    return {"rows": rows,
            "C1": all(v["rel_free_vs_shared"] <= C1_TOL for v in sym),
            "C2": all(v["gain"] >= v["floor"] for v in het),
            "C3": all(v["hits_below"] == 0 and v["hits_above"] >= 1 for v in het),
            "C4_dual_within_5e-4": c4 <= C4_TOL,
            "worst": {"C1_max_rel": max(v["rel_free_vs_shared"] for v in sym),
                      "C4_max_rel": c4, "C2_min_gain": min(v["gain"] for v in het),
                      "C3_max_hits_below": max(v["hits_below"] for v in het),
                      "C3_min_hits_above": min(v["hits_above"] for v in het),
                      "max_r_gap_het": max(float(max(abs(np.array(v["r"]) - v["rho"]))) for v in het)},
            "seed_pool": p13.SEEDS_XIII,
            "seed_disjoint": not set(p13.SEEDS_XIII) & set(sum(p13.PRIOR_POOLS, []))}


def run_d(s_grid, lam, committed, rows8):
    e0j, e1j, rmsj, flat = p13.fit_joint(s_grid, lam)
    e0s = np.arange(-2.0, 3.0 + 1e-9, 0.001)
    rms_single = [p13.rms_error(float(e), 0.0, s_grid, lam) for e in e0s]
    j = int(np.argmin(rms_single))
    single = (float(e0s[j]), 0.0, float(rms_single[j]))
    big = p12.subset(s_grid, lam, 100.0)
    exp_joint = p12.exponent(e0j, big, e1j)
    anchor_rho = max(abs(p12.rho_smooth(2 * C1, s) - rows8[str(s)]["rho_smooth"]) /
                     rows8[str(s)]["rho_smooth"] for s in s_grid)
    anchor_exp = abs(p12.exponent(2 * C1, big) - committed["P8_1_slope"])
    return {"joint": {"e0": e0j, "e1": e1j, "rms_full_curve": rmsj, "flatness": flat},
            "single": {"e0": single[0], "e1": 0.0, "rms_full_curve": single[2]},
            "exponent_joint_big": exp_joint,
            "D1": rmsj <= single[2] + 1e-12,
            "D3": abs(exp_joint + 2.0) >= D3_FLOOR,
            "D4": anchor_rho <= D4_TOL and anchor_exp <= D4_TOL,
            "worst": {"D4_rho": anchor_rho, "D4_chord": anchor_exp}}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p13_gate.py")], capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    if set(p13.SEEDS_XIII) & set(sum(p13.PRIOR_POOLS, [])):
        print("REFUSING TO RUN: seed pool overlaps")
        return 1
    print("seed pool 3000-3009 asserted disjoint (R4)")
    committed = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    s_grid, rows8 = committed["s_grid"], committed["rows"]
    lam = {k: v["lambda_hi"] for k, v in rows8.items()}
    t0 = time.time()
    A, B, C = run_a(), run_b(), run_c()
    D = run_d(s_grid, lam, committed, rows8)
    secs = round(time.time() - t0, 1)

    e0_broken = (not D["D4"]) or (not A["A2"])
    closed = {"E1 CONVENTION RECONCILED": A["A1"] and A["A3"],
              "E2 DEGENERACY CONFIRMED": B["B1"] and B["B2"] and B["B3"],
              "E3 K4 CONFIRMED": C["C1"] and C["C2"] and C["C3"] and C["C4_dual_within_5e-4"],
              "E4 JOINT FIT": D["D1"] and D["D3"]}
    n_closed = sum(closed.values())
    if e0_broken:
        exit_label = "E0 ANCHOR-BROKEN"
        verdict = "REFUTED (instrument-level; no scientific conclusion this round)"
    else:
        exit_label = " / ".join(k for k, v in closed.items() if v) or "E5 PARTIAL (none closed)"
        verdict = f"{n_closed}/4 closed"

    payload = {"schema": "m2a.phase13.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE13_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "A": A, "B": B, "C": C, "D": D, "exits": closed, "n_closed": n_closed,
               "exit": exit_label, "verdict": verdict,
               "e0_anchor_broken": e0_broken,
               "runtime": {"seconds": secs, "sampling": "none (deterministic; random control is a search)"}}
    json.dump(payload, open(HERE / "phase13_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nA: A1 {A['A1']} band {A['band']}; A2 spread {A['A2_spread']:.5f}; "
          f"A3 max err {A['A3_max_err']:.5f}; A4 {json.dumps({k: round(v,4) for k,v in A['A4_disclose'].items() if isinstance(v,float)})}")
    print(f"B: B1 {B['B1']} B2 {B['B2']} B3 {B['B3']} "
          f"(logistic closure {B['per_kind']['logistic']['closure_beta']:.5f}, "
          f"J=200 {B['per_kind']['logistic']['seq'][-1]['beta']:.5f})")
    print(f"C: C1 {C['C1']} C2 {C['C2']} C3 {C['C3']} C4 {C['C4_dual_within_5e-4']} "
          f"worst={json.dumps({k: round(v,6) for k,v in C['worst'].items()})}")
    print(f"D: joint e0={D['joint']['e0']:.6f} e1={D['joint']['e1']:.4f} rms={D['joint']['rms_full_curve']:.6f} "
          f"single e0={D['single']['e0']} rms={D['single']['rms_full_curve']:.6f} "
          f"exp_joint={D['exponent_joint_big']:.6f} D1 {D['D1']} D3 {D['D3']} D4 {D['D4']}")
    print(f"   flatness {json.dumps({k: (round(v,8) if isinstance(v,float) else v) for k,v in D['joint']['flatness'].items() if k in ('d_e0','d_e1','terminal_steps')})}")
    print(f"\nEXITS: {json.dumps(closed)}  -> {n_closed}/4")
    print(f"EXIT: {exit_label}  verdict={verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
