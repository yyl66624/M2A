"""Run Phase IV: cross-substrate invariance of L1/L2 and cross-estimator invariance of L3."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p3_mechanisms import cue_sensitivity, train_cue_agent
from p4_mechanisms import (SUBSTRATES, bayes_sensitivity, cdf, critical_beta, gate_curve,
                           predicted_threshold, quantile)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
STEPS = 100000
SEEDS = list(range(10))


def mc(p, n, rng):
    return float(np.mean(rng.rand(n) < p))


def run_l1():
    rng = np.random.RandomState(0)
    rows = {}
    for k in SUBSTRATES:
        pred = predicted_threshold(k)
        crit = critical_beta(k)
        beta = crit + 1.0
        lo = -quantile(0.05, k) / beta
        hi = 1.0 - quantile(0.95, k) / beta
        rows[k] = {
            "predicted_threshold": pred, "numeric_threshold": crit,
            "abs_diff": abs(crit - pred),
            "window_at_beta_plus_1": [float(lo), float(hi)],
            "single_at_lo": mc(cdf(beta * (0 - lo), k), 20000, rng),
            "joint_at_hi": mc(cdf(beta * (1 - hi), k), 20000, rng),
            "single_far": mc(cdf(beta * (0 - (lo + 0.2)), k), 20000, rng),
            "joint_far": mc(cdf(beta * (1 - (hi - 0.2)), k), 20000, rng),
        }
    checks = {
        "thresholds_match": all(rows[k]["abs_diff"] <= 0.05 for k in SUBSTRATES),
        "constants_distinct": len({round(rows[k]["numeric_threshold"], 2) for k in SUBSTRATES}) == 3,
        "boundary_single": all(abs(rows[k]["single_at_lo"] - 0.05) <= 0.005 for k in SUBSTRATES),
        "boundary_joint": all(abs(rows[k]["joint_at_hi"] - 0.95) <= 0.005 for k in SUBSTRATES),
        "far_inside": all(rows[k]["single_far"] < 0.02 and rows[k]["joint_far"] > 0.98 for k in SUBSTRATES),
    }
    return {"rows": rows, "checks": checks,
            "verdict": "SUPPORTED" if all(checks.values()) else "REFUTED"}


def run_l2():
    xs = np.linspace(0, 1, 101)
    rows = {}
    ok = True
    for k in SUBSTRATES:
        r = {}
        for o in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = gate_curve(k, xs, o)
            r[str(o)] = {"delta": float(y[-1] - y[0]),
                         "max_step": float(np.max(np.abs(np.diff(y))))}
            if o < 0.5 and not (y[-1] < y[0]):
                ok = False
            if o > 0.5 and not (y[-1] > y[0]):
                ok = False
            if o == 0.5 and r[str(o)]["max_step"] > 1e-12:
                ok = False
        rows[k] = r
    return {"rows": rows, "checks": {"sign_law_all_substrates": ok},
            "verdict": "SUPPORTED" if ok else "REFUTED"}


def run_l3():
    qs = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    rows = {}
    for q in qs:
        qvals = np.array([cue_sensitivity(train_cue_agent(q, STEPS, s)) for s in SEEDS])
        bvals = np.array([bayes_sensitivity(q, seed=s) for s in range(20)])
        pred = 0.36 * (2 * q - 1)
        rows[str(q)] = {"q_learning": {"mean": float(qvals.mean()), "sd": float(qvals.std(ddof=1))},
                        "bayes": {"mean": float(bvals.mean()), "sd": float(bvals.std(ddof=1))},
                        "pred": pred,
                        "q_abs_diff": float(abs(qvals.mean() - pred)),
                        "b_abs_diff": float(abs(bvals.mean() - pred)),
                        "cross_estimator_diff": float(abs(qvals.mean() - bvals.mean()))}
    checks = {
        "q_learning_within_003": all(r["q_abs_diff"] <= 0.03 for r in rows.values()),
        "bayes_within_003": all(r["b_abs_diff"] <= 0.03 for r in rows.values()),
        "estimators_agree_003": all(r["cross_estimator_diff"] <= 0.03 for r in rows.values()),
        "never_informative_zero": rows["0.5"]["q_learning"]["mean"] <= 0.01
                                  and rows["0.5"]["bayes"]["mean"] <= 0.01,
    }
    return {"rows": rows, "checks": checks,
            "verdict": "SUPPORTED" if all(checks.values()) else "REFUTED"}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p4_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    payload = {"schema": "m2a.phase4.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE4_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "substrates": list(SUBSTRATES), "steps_l3": STEPS, "seeds": SEEDS,
               "L1": run_l1(), "L2": run_l2(), "L3": run_l3()}
    payload["verdicts"] = {k: payload[k]["verdict"] for k in ("L1", "L2", "L3")}
    json.dump(payload, open(HERE / "phase4_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for k in ("L1", "L2", "L3"):
        print(f"{k}: {payload[k]['verdict']}  {payload[k]['checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
