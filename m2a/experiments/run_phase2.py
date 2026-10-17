"""Run Phase II (E1, E1b, E2) exactly as pre-registered; write JSON + verdicts.

Refuses to run unless phase2_gate.py exits 0 (invoked here as a subprocess) and the pre-registration
file is present. Thresholds are read from the pre-registration constants below and must not be edited
after a run.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from m2a_mechanisms import (availability_sensitivity, e1_rates, e1b_curve, proxy_sensitivity,
                            spearman, state_key, train_agent)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
STEPS = 20000
SEEDS = list(range(10))
N_TRIALS = 20000

# Pre-registered thresholds (PHASE2_PREREGISTRATION.md)
E1 = dict(single_max=0.05, joint=0.90, interaction=0.80, or_single=0.90, or_interaction=0.05)
E1B = dict(rho_exact=1.0, flip=0.05, sat_slope=0.02)
E2 = dict(abstain=0.30, s_only_max=0.05, s_plus_c_min=0.30)


def agg(vals):
    a = np.asarray(vals, dtype=float)
    return {"mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
            "min": float(a.min()), "max": float(a.max())}


def run_e1():
    out = {}
    for arch in ("single", "and", "or"):
        for noise in (0.0, 0.1):
            cells = {"11": [], "10": [], "01": [], "00": [], "I": [], "single": []}
            for s in SEEDS:
                r = e1_rates(arch, N_TRIALS, s, noise=noise)
                cells["11"].append(r[(1, 1)]); cells["10"].append(r[(1, 0)])
                cells["01"].append(r[(0, 1)]); cells["00"].append(r[(0, 0)])
                cells["I"].append(r["interaction"]); cells["single"].append(r["single_max"])
            out[f"{arch}_noise{noise}"] = {k: agg(v) for k, v in cells.items()}
    a = out["and_noise0.0"]; o = out["or_noise0.0"]
    checks = {
        "and_single_below": a["single"]["mean"] < E1["single_max"],
        "and_joint_above": a["11"]["mean"] > E1["joint"],
        "and_interaction_above": a["I"]["mean"] > E1["interaction"],
        "or_single_above": o["single"]["mean"] > E1["or_single"],
        "or_interaction_below": o["I"]["mean"] < E1["or_interaction"],
    }
    if all(v for k, v in checks.items() if k.startswith("and")):
        verdict = "SUPPORTED" if checks["or_single_above"] and checks["or_interaction_below"] else "UNDECIDABLE"
    else:
        verdict = "REFUTED"
    return {"cells": out, "checks": checks, "verdict": verdict}


def run_e1b():
    xs = np.linspace(0.0, 1.0, 21)
    curves = {
        "trigger": e1b_curve("trigger", xs),
        "gate_plus": e1b_curve("gate", xs, polarity=1),
        "gate_minus": e1b_curve("gate", xs, polarity=-1),
        "constraint": e1b_curve("constraint", xs),
    }

    def has_flip(y):
        return any(y[j] < y[i] - E1B["flip"] for i in range(len(y)) for j in range(i + 1, len(y)))

    sat = xs >= 0.7
    sat_slope = float(np.max(np.abs(np.diff(curves["constraint"][sat])))) if sat.sum() > 1 else 1.0
    checks = {
        "trigger_monotone": abs(spearman(curves["trigger"]) - 1.0) < 1e-9,
        "trigger_no_flip": not has_flip(curves["trigger"]),
        "gate_plus_increasing": spearman(curves["gate_plus"]) > 0.99,
        "gate_minus_decreasing": spearman(curves["gate_minus"]) < -0.99,
        "constraint_saturates": sat_slope < E1B["sat_slope"],
    }
    verdict = "SUPPORTED" if all(checks.values()) else (
        "UNDECIDABLE" if checks["trigger_monotone"] and checks["trigger_no_flip"] and
        checks["gate_plus_increasing"] and checks["gate_minus_decreasing"] else "REFUTED")
    return {"xs": xs.tolist(),
            "curves": {k: v.tolist() for k, v in curves.items()},
            "rho": {k: spearman(v) for k, v in curves.items()},
            "sat_slope": sat_slope, "checks": checks, "verdict": verdict}


def e2_metrics(kind: str, seed: int):
    Q = train_agent(kind, steps=STEPS, seed=seed)
    # S_proxy is probed on the cue (exploratory, P2-C2); the two behavioural agents on availability.
    delta = proxy_sensitivity(Q) if kind == "S_proxy" else availability_sensitivity(Q, kind)
    low = state_key(kind, np.array([0.05, 0.1]), np.array([1, 1]))
    greedy = max([0, 1, 2], key=lambda a: Q.get((low, a), 0.0))
    return delta, (1.0 if greedy == 0 else 0.0)


def run_e2():
    out = {}
    # S_proxy is WITHDRAWN (P2-C3): after taking the lower-value action its state key (max, cue) does
    # not change, so the Q update bootstraps from the same state - a self-loop that makes the learned
    # values an artefact. Its first reading (delta ~ 0.007) is therefore not interpretable as
    # "a correlated cue is insufficient", and it is excluded from the verdict. The pre-registered
    # verdict never depended on it.
    for kind in ("S_only", "S_plus_C"):
        d, ab = [], []
        for s in SEEDS:
            delta, abst = e2_metrics(kind, s)
            d.append(delta); ab.append(abst)
        out[kind] = {"delta": agg(d), "abstention": agg(ab)}
    checks = {
        "s_layer_both_abstain": (out["S_only"]["abstention"]["mean"] > E2["abstain"]
                                 and out["S_plus_C"]["abstention"]["mean"] > E2["abstain"]),
        "s_only_insensitive": out["S_only"]["delta"]["mean"] < E2["s_only_max"],
        "s_plus_c_sensitive": out["S_plus_C"]["delta"]["mean"] > E2["s_plus_c_min"],
    }
    if checks["s_layer_both_abstain"] and checks["s_plus_c_sensitive"] and checks["s_only_insensitive"]:
        verdict = "SUPPORTED"
    elif not checks["s_only_insensitive"]:
        verdict = "REFUTED"
    else:
        verdict = "UNDECIDABLE"
    return {"agents": out, "checks": checks, "verdict": verdict,
            "withdrawn": {"S_proxy": "ill-posed self-loop in the state key (P2-C3)"}}


def main() -> int:
    prereg = HERE / "PHASE2_PREREGISTRATION.md"
    gate = subprocess.run([sys.executable, str(HERE / "phase2_gate.py")],
                          capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    payload = {
        "schema": "m2a.phase2.results.v1",
        "prereg_sha256": hashlib.sha256(prereg.read_bytes()).hexdigest(),
        "seeds": SEEDS, "steps_e2": STEPS, "trials_e1": N_TRIALS,
        "E1": run_e1(), "E1b": run_e1b(), "E2": run_e2(),
    }
    payload["verdicts"] = {k: payload[k]["verdict"] for k in ("E1", "E1b", "E2")}
    json.dump(payload, open(HERE / "phase2_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for k in ("E1", "E1b", "E2"):
        print(f"{k}: {payload[k]['verdict']}  {payload[k]['checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
