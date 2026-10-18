"""Run Phase XV: information content of the joint (e0, e1) fit - closing P13-O2 without a finer grid.

Gate first (R2). C1 compares the committed D1 gap against a tie floor that is the search instrument's own
one-step change; C2/C3 are structural (boundary minimum, monotone profile) rather than threshold-chosen;
C4 uses a different functional (large-end chord exponent) at P8-1's tolerance verbatim (R8, R11).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import p12_lattice as p12
import p13_closeout as p13
import p15_identifiability as p15

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
PREREG = "PHASE15_PREREGISTRATION.md"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> int:
    r = subprocess.run([sys.executable, "p15_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def main() -> int:
    t0 = time.time()
    if run_gate() != 0:
        print("GATE FAILED - refusing to run Phase XV (R2)")
        return 1

    c = p15.committed()
    s_grid, lam = c["s_grid"], c["lam"]
    T = p15.tie_floor(c)
    delta = abs(c["joint_rms"] - c["single_rms"])

    # XV-1 anchor: re-run the committed searches, require bit-level agreement (1e-12)
    e0j, e1j, rmsj, _ = p13.fit_joint(s_grid, lam)
    pr0, e0p = p15.profile_e0(0.0, s_grid, lam)
    anchor_rel = max(abs(rmsj - c["joint_rms"]) / c["joint_rms"], abs(e0j - c["joint_e0"]),
                     abs(pr0 - c["single_rms"]) / c["single_rms"], abs(e0p - c["single_e0"]))
    xv1 = bool(anchor_rel <= p15.ANCHOR_TOL)

    # the registered e1 profile
    prof = []
    for e1 in p15.E1_GRID:
        v, e0 = p15.profile_e0(e1, s_grid, lam)
        prof.append({"e1": float(e1), "profile_rms": float(v), "argmin_e0": e0,
                     "excess_over_joint": float(v - c["joint_rms"])})
    argmin_e1 = min(prof, key=lambda r: r["profile_rms"])["e1"]
    steps = [b["profile_rms"] - a["profile_rms"] for a, b in zip(prof, prof[1:])]
    c3 = bool(all(d >= 0.0 for d in steps))

    e1_max, unbounded, violator, viol_val = p15.e1_identified_set(c, T)
    c2 = bool(argmin_e1 == 0.0 and not unbounded)

    # C4: the exponent at both ends of the identified set, same subset, P8-1 tolerance verbatim
    big = p12.subset(s_grid, lam, p15.BIG_FROM)
    exp_lo, e0_at_lo, _ = p15.exponent_at(0.0, s_grid, lam)
    exp_hi, e0_at_hi, _ = p15.exponent_at(e1_max, s_grid, lam)
    exp_committed_reproduced = float(p12.exponent(c["joint_e0"], big, c["joint_e1"]))
    c4 = bool(abs(exp_hi - exp_lo) <= p15.EXP_TOL)
    anchor_exp = abs(exp_committed_reproduced - c["exp_joint_big"])

    jac = p15.jacobian_diagnostics(c)

    closed = {"C1 GAP-IS-NOISE": bool(delta < T), "C2 ONE-SIDED-BOUND": c2,
              "C3 PROFILE-MONOTONE": c3, "C4 OUTPUT-INVARIANT": c4}
    if not xv1:
        exit_name = "E0 ANCHOR-BROKEN"
    else:
        exit_name = " | ".join(f"E{k[1]}" for k, v in closed.items() if v) or "E-UNMAPPED"
    n_closed = sum(closed.values())
    o2_closed = bool(closed["C1 GAP-IS-NOISE"] and c2 and c4)

    res = {
        "schema": "m2a.phase15.results.v1",
        "prereg_sha256": sha256(HERE / PREREG),
        "inputs_from_committed_artifacts": {
            "joint_rms": c["joint_rms"], "single_rms": c["single_rms"], "joint_e0": c["joint_e0"],
            "joint_e1": c["joint_e1"], "single_e0": c["single_e0"], "d_e0": c["d_e0"], "d_e1": c["d_e1"],
            "terminal_steps": [p15.STEP_E0, p15.STEP_E1], "exp_joint_big": c["exp_joint_big"],
            "p8_1_slope": c["p8_slope"]},
        "tie_floor": {"T": T, "derivation": "P15-A3/R11: max of the committed one-step changes at the joint optimum",
                      "delta_D1_gap": delta, "ratio_delta_over_T": delta / T},
        "xv1_anchor": {"max_rel": float(anchor_rel), "tol": p15.ANCHOR_TOL, "pass": xv1},
        "profile": {"grid": [float(e) for e in p15.E1_GRID], "rows": prof,
                    "argmin_e1": float(argmin_e1), "consecutive_steps": [float(d) for d in steps],
                    "min_step": float(min(steps))},
        "identified_set": {"e1_max": float(e1_max), "unbounded_in_box": bool(unbounded),
                           "first_violating_grid_point": None if violator is None else float(violator),
                           "violator_excess": None if viol_val is None else float(viol_val - c["joint_rms"]),
                           "bisect_tol_absolute": p15.BISECT_TOL_E1,
                           "registered_box": [0.0, float(p15.E1_GRID[-1])]},
        "c4_exponent": {"at_e1_0": exp_lo, "at_e1_max": exp_hi, "abs_difference": abs(exp_hi - exp_lo),
                        "tolerance_reused_verbatim": p15.EXP_TOL, "tolerance_source": "Phase VIII P8-1",
                        "committed_reproduced": exp_committed_reproduced, "anchor_abs_err": anchor_exp,
                        "e0_at_0": e0_at_lo, "e0_at_max": e0_at_hi},
        "jacobian_diagnostics": {k: (float(v) if isinstance(v, (int, float)) else v)
                                 for k, v in jac.items()},
        "criteria": closed,
        "exits": {"E0 ANCHOR-BROKEN": not xv1, "E1 GAP-IS-NOISE": closed["C1 GAP-IS-NOISE"],
                  "E2 ONE-SIDED-BOUND": c2, "E3 PROFILE-MONOTONE": c3, "E4 OUTPUT-INVARIANT": c4,
                  "E-UNMAPPED": xv1 and n_closed == 0},
        "exit": exit_name,
        "n_closed": int(n_closed),
        "verdict": f"{n_closed}/4 closed",
        "P13-O2": {"closed": o2_closed, "condition": "C1 and C2 and C4 (registered before any reading)"},
        "runtime_s": round(time.time() - t0, 2),
    }
    (HERE / "phase15_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"\ntie floor T = {T:.6e}; D1 gap Δ = {delta:.6e}; Δ/T = {delta / T:.4f} -> C1 {closed['C1 GAP-IS-NOISE']}")
    print(f"anchor max rel {anchor_rel:.2e} -> XV-1 {xv1}")
    print(f"profile argmin e1 = {argmin_e1}; monotone {c3}")
    print(f"identified set e1_max = {e1_max:.9f}, unbounded_in_box {unbounded}, "
          f"first violator {violator}")
    print(f"exponent at e1=0 {exp_lo:.9f}, at e1_max {exp_hi:.9f}, |diff| {abs(exp_hi - exp_lo):.3e} "
          f"(tol {p15.EXP_TOL}) -> C4 {c4}; committed reproduced {exp_committed_reproduced:.9f} "
          f"(anchor {anchor_exp:.2e})")
    print(f"jacobian: corr {jac['corr']:.6f}, kappa {jac['kappa']:.3e} (no threshold, diagnostic only)")
    print(f"\ncriteria {closed} -> exit {exit_name} | verdict {res['verdict']} | P13-O2 closed {o2_closed}")
    print(f"runtime {res['runtime_s']}s | prereg sha256 {res['prereg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
