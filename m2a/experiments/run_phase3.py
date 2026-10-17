"""Run Phase III (L1 conjunction window, L2 gate sign law, L3 representation-quality law)."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p3_mechanisms import (conjunction_window, cue_sensitivity, p_and, p_gate, p_or,
                           predicted_cue_sensitivity, theta_j, theta_s, train_cue_agent)
from m2a_mechanisms import spearman

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
STEPS = 100000
SEEDS = list(range(10))


def mc_rate(p: float, n: int, rng) -> float:
    return float(np.mean(rng.rand(n) < p))


def run_l1():
    rng = np.random.RandomState(0)
    rows = {}
    for beta in (2, 4, 6, 8, 10):
        win = conjunction_window(beta)
        row = {"theta_s": float(theta_s(beta)), "theta_j": float(theta_j(beta)),
               "window": None if win is None else [float(win[0]), float(win[1])],
               "width_pred": None if win is None else float(win[1] - win[0])}
        if win is not None:
            lo, hi = win
            # P3-C1: the first version tested 0.01 inside the boundary, where the analytic value is
            # 0.0473 against a threshold of 0.05 - a gap of 0.0027 with a Monte-Carlo standard error
            # of 0.0015. That test cannot resolve what it asserts. Replaced by (i) the boundary
            # identity (at theta_s the rate must equal alpha within 3 SE) and (ii) a well-inside test
            # 0.05 away from the boundary, where the analytic value is far from the threshold.
            row["single_at_boundary"] = mc_rate(p_and(1, 0, beta, lo), 20000, rng)
            row["joint_at_boundary"] = mc_rate(p_and(1, 1, beta, hi), 20000, rng)
            # P3-C2: a 0.05 shift only moves the rate from 0.05 to ~0.038 (the sigmoid is shallow
            # there), so a "below 0.02" assertion at that distance was arithmetically impossible.
            # A 0.2 shift gives sigma(-|logit 0.05| - 0.2*beta) ~ 0.016 at beta = 6.
            row["single_far_inside"] = mc_rate(p_and(1, 0, beta, lo + 0.2), 20000, rng)
            row["joint_far_inside"] = mc_rate(p_and(1, 1, beta, hi - 0.2), 20000, rng)
        else:
            row["gap_theta_s_minus_theta_j"] = float(theta_s(beta) - theta_j(beta))
        rows[beta] = row
    # duality MC check
    dual = {}
    for beta in (6, 8):
        for theta in (0.3, 0.5, 0.7):
            a = mc_rate(p_and(1, 1, beta, theta), 20000, rng)
            b = mc_rate(p_or(1, 0, beta, theta), 20000, rng)
            dual[f"beta{beta}_theta{theta}"] = abs(a - b)
    checks = {
        "no_window_for_beta_2_4": all(rows[b]["window"] is None and rows[b]["gap_theta_s_minus_theta_j"] > 0
                                      for b in (2, 4)),
        "window_for_beta_6_8_10": all(rows[b]["window"] is not None for b in (6, 8, 10)),
        "single_boundary_equals_alpha": all(abs(rows[b]["single_at_boundary"] - 0.05) <= 0.005
                                            for b in (6, 8, 10)),
        "joint_boundary_equals_095": all(abs(rows[b]["joint_at_boundary"] - 0.95) <= 0.005
                                         for b in (6, 8, 10)),
        "single_far_inside_below_002": all(rows[b]["single_far_inside"] < 0.02 for b in (6, 8, 10)),
        "joint_far_inside_above_098": all(rows[b]["joint_far_inside"] > 0.98 for b in (6, 8, 10)),
        "duality_mc_within_002": all(v < 0.02 for v in dual.values()),
    }
    verdict = "SUPPORTED" if all(checks.values()) else "REFUTED"
    return {"rows": rows, "duality_mc_abs_diff": dual, "checks": checks, "verdict": verdict}


def run_l2():
    xs = np.linspace(0, 1, 201)
    out = {}
    for o in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = p_gate(xs, o)
        out[str(o)] = {"rho": spearman(y), "p0": float(y[0]), "p1": float(y[-1]),
                       "max_step": float(np.max(np.abs(np.diff(y))))}
    # saturation masking: o=0.25, theta=0.2, look at x > 0.8
    y_sat = p_gate(xs, 0.25, theta=0.2)
    sat_slope = float(np.max(np.abs(np.diff(y_sat[xs > 0.8]))))
    checks = {
        "o1_positive": out["1.0"]["rho"] > 0.99,
        "o075_positive": out["0.75"]["rho"] > 0.99,
        "o025_negative": out["0.25"]["rho"] < -0.99,
        "o0_negative": out["0.0"]["rho"] < -0.99,
        "o05_flat": out["0.5"]["max_step"] < 0.01,
        "saturation_masks_flip": sat_slope < 0.02,
    }
    verdict = "SUPPORTED" if all(checks.values()) else "REFUTED"
    return {"curves": out, "sat_slope": sat_slope, "checks": checks, "verdict": verdict}


def run_l3():
    qs = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    rows = {}
    for q in qs:
        vals = [cue_sensitivity(train_cue_agent(q, STEPS, s)) for s in SEEDS]
        vals = np.array(vals)
        pred = predicted_cue_sensitivity(q)
        rows[str(q)] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)),
                        "pred": pred, "abs_diff": float(abs(vals.mean() - pred))}
    means = [rows[str(q)]["mean"] for q in qs]
    checks = {
        "within_tol_all_q": all(r["abs_diff"] <= 0.03 for r in rows.values()),
        "q05_near_zero": rows["0.5"]["mean"] <= 0.01,
        "monotone_in_q": abs(spearman(means) - 1.0) < 1e-9,
    }
    verdict = "SUPPORTED" if all(checks.values()) else "REFUTED"
    return {"rows": rows, "checks": checks, "verdict": verdict}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p3_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    payload = {"schema": "m2a.phase3.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE3_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "steps_l3": STEPS, "seeds": SEEDS,
               "L1": run_l1(), "L2": run_l2(), "L3": run_l3()}
    payload["verdicts"] = {k: payload[k]["verdict"] for k in ("L1", "L2", "L3")}
    json.dump(payload, open(HERE / "phase3_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for k in ("L1", "L2", "L3"):
        print(f"{k}: {payload[k]['verdict']}  {payload[k]['checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
