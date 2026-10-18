"""Run Phase V: V1 (L3 residual attribution), V2 (multi-channel / soft conjunction),
V3 (serial gates). The gate must pass before anything is read, and thresholds live here only.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p4_mechanisms import SUBSTRATES, cdf, predicted_threshold
from p5_mechanisms import (ALPHA, ARMS, DP_SPEC, QS, chain_curve, chain_polarity, channels,
                           critical_beta, dp_sensitivity_only, gap_for, law, mc_prob,
                           predicted_critical, run_cue, tnorm, window_bounds, window_exists)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
SEEDS = list(range(10))
MID_Q = [0.6, 0.7, 0.8, 0.9]
TNORMS = ("product", "lukasiewicz", "godel")
NS = (2, 3, 4)
SS = (0.0, 0.25, 0.5, 0.75)
PATTERNS = ("hard", "one_weak", "all_weak")


# ----------------------------------------------------------------- V1
def run_v1():
    rows = {}
    for arm in ARMS:
        steps = ARMS[arm][1]
        for q in QS:
            vals = np.array([run_cue(q, steps, s, arm) for s in SEEDS])
            dp = dp_sensitivity_only(q, **DP_SPEC[arm])
            rows[f"{arm}|{q}"] = {
                "steps": steps, "mc_mean": float(vals.mean()), "mc_sd": float(vals.std(ddof=1)),
                "mc_se": float(vals.std(ddof=1) / len(SEEDS) ** 0.5), "dp": dp, "law": law(q),
                "mc_minus_dp": float(abs(vals.mean() - dp)),
                "dp_minus_law": float(abs(dp - law(q))),
                "mc_minus_law": float(abs(vals.mean() - law(q))),
            }

    anchor = json.loads((HERE / "phase4_results.json").read_text(encoding="utf-8"))["L3"]["rows"]
    a0 = {str(q): {"committed": anchor[str(q)]["q_learning"]["mean"],
                   "this_run": rows[f"base|{q}"]["mc_mean"],
                   "abs_diff": abs(anchor[str(q)]["q_learning"]["mean"] - rows[f"base|{q}"]["mc_mean"])}
          for q in QS}
    a0_ok = all(v["abs_diff"] <= 0.005 for v in a0.values())

    mid = lambda arm, key: max(rows[f"{arm}|{q}"][key] for q in MID_Q)  # noqa: E731
    a1_ok = all(r["mc_minus_dp"] <= 0.008 for r in rows.values())
    a2_ratio = (mid("base", "dp_minus_law") / mid("base", "mc_minus_law")
                if mid("base", "mc_minus_law") > 1e-9 else float("nan"))

    base_bias = mid("base", "mc_minus_law")
    ratios = {arm: (mid(arm, "mc_minus_law") / base_bias if base_bias > 1e-9 else float("nan"))
              for arm in ("long", "noexplore", "greedy_first", "sarsa")}
    dp_matches_law = all(rows[f"base|{q}"]["dp_minus_law"] <= 0.005 for q in QS)

    if not a0_ok:
        attribution = "NOT_VALID (V1-A0 anchor failed)"
    elif a1_ok and a2_ratio >= 0.75 and ratios["long"] >= 0.5:
        attribution = "J_FIXED_POINT"
    elif dp_matches_law and ratios["long"] < 0.5:
        attribution = "J_TRANSIENT"
    elif ratios["noexplore"] <= 0.2 and all(ratios[a] >= 0.7 for a in ("long", "greedy_first", "sarsa")):
        attribution = "J_EXPLORATION"
    else:
        attribution = "J_NOT_DECISIVE"

    checks = {"V1_A0_anchor": a0_ok, "V1_A1_dp_adequacy": a1_ok,
              "V1_A2_ratio_ge_075": bool(a2_ratio == a2_ratio and a2_ratio >= 0.75)}
    return {"rows": rows, "anchor": a0, "mid_bias_ratios_by_arm": ratios,
            "a2_ratio": (float(a2_ratio) if a2_ratio == a2_ratio else None),
            "checks": checks, "attribution": attribution,
            "verdict": ("SUPPORTED" if a0_ok and attribution != "J_NOT_DECISIVE"
                        else "NOT_EXPLAINED")}


# ----------------------------------------------------------------- V2
def run_v2():
    rng = np.random.RandomState(0)
    rows, cells = {}, []
    for kind in SUBSTRATES:
        for name in TNORMS:
            for n in NS:
                for pattern in PATTERNS:
                    for s in ([0.0] if pattern == "hard" else SS):
                        lo = tnorm(name, channels(n, pattern, s))
                        hi = tnorm(name, [1.0] * n)
                        gap = hi - lo
                        num = critical_beta(kind, lo, hi)
                        pred = predicted_critical(kind, gap_for(name, n, pattern, s))
                        rel = abs(num - pred) / pred if pred not in (0.0, float("inf")) else 0.0
                        rec = {"kind": kind, "tnorm": name, "n": n, "pattern": pattern, "s": s,
                               "drive_silent": lo, "gap": gap, "numeric_beta": num,
                               "predicted_beta": pred, "abs_diff": abs(num - pred), "rel_diff": rel}
                        if gap > 0.0:
                            beta = num + 1.0
                            th_j, th_s = window_bounds(kind, beta, lo, hi)
                            rec["mc_silent_at_boundary"] = mc_prob(
                                float(cdf(beta * (lo - th_s), kind)), 20000, rng)
                            rec["mc_fire_at_boundary"] = mc_prob(
                                float(cdf(beta * (hi - th_j), kind)), 20000, rng)
                        rows[f"{kind}|{name}|{n}|{pattern}|{s}"] = rec
                        cells.append(rec)

    finite = [c for c in cells if c["gap"] > 0.0]
    b1 = all(c["abs_diff"] <= 0.05 and c["rel_diff"] <= 0.02 for c in finite)
    hard = {(c["kind"], c["n"]): c["numeric_beta"] for c in cells if c["pattern"] == "hard"}
    b2 = all(abs(hard[(k, n)] - hard[(k, 2)]) <= 0.02
             for k in SUBSTRATES for n in NS)                      # n-invariance of the hard AND
    b3, b3_detail = True, {}
    for kind in SUBSTRATES:
        for n in (3, 4):
            for s in (0.25, 0.5, 0.75):
                vals = {name: next(c["numeric_beta"] for c in cells if c["kind"] == kind
                                   and c["tnorm"] == name and c["n"] == n
                                   and c["pattern"] == "all_weak" and c["s"] == s)
                        for name in TNORMS}
                ok = vals["godel"] >= vals["product"] >= vals["lukasiewicz"] - 1e-9
                b3 = b3 and ok
                b3_detail[f"{kind}|n={n}|s={s}"] = vals
    b4 = all(abs(c["mc_silent_at_boundary"] - ALPHA) <= 0.005
             and abs(c["mc_fire_at_boundary"] - (1 - ALPHA)) <= 0.005
             for c in finite if "mc_silent_at_boundary" in c)
    return {"rows": rows, "n_cells": len(cells),
            "checks": {"V2_B1_gap_law": b1, "V2_B2_hard_and_n_invariance": b2,
                       "V2_B3_tnorm_ordering": b3, "V2_B4_mc_boundaries": b4},
            "tnorm_order_detail": b3_detail,
            "worst_abs_diff": max(c["abs_diff"] for c in finite),
            "verdict": "SUPPORTED" if (b1 and b2 and b3 and b4) else "REFUTED"}


# ----------------------------------------------------------------- V3
def run_v3():
    rng = np.random.RandomState(1)
    xs = np.linspace(0, 1, 101)
    rows = {}
    c1 = c2 = True
    combos = {(1.0,), (0.75,), (0.25,), (0.75, 0.75), (0.75, 0.25), (0.25, 0.25),
              (1.0, 0.75), (1.0, 0.5), (0.75, 0.75, 0.75), (0.75, 0.75, 0.25)}
    for kind in SUBSTRATES:
        for op in combos:
            pol = chain_polarity(op)
            y = chain_curve(kind, op, xs)
            slope_sign = 0 if pol == 0 else (1 if y[-1] > y[0] else -1)
            flat = float(np.max(np.abs(np.diff(y))))
            rec = {"substrate": kind, "openness": list(op), "polarity": pol,
                   "endpoint_delta": float(y[-1] - y[0]), "max_step": flat,
                   "slope_sign": slope_sign}
            if pol != 0:
                rec["sign_ok"] = (slope_sign == (1 if pol > 0 else -1))
                c1 = c1 and rec["sign_ok"]
            else:
                rec["flat_ok"] = flat < 1e-12 and not window_exists(kind, 200.0, 0.0, 0.0)
                c2 = c2 and rec["flat_ok"]
            rows[f"{kind}|{','.join(str(o) for o in op)}"] = rec

    c3 = abs(critical_beta("logistic", 0.0, 1.0) - predicted_threshold("logistic")) <= 0.005

    chain_cells = []
    for kind in SUBSTRATES:
        for op in ((0.75,), (0.75, 0.75), (0.25,), (0.75, 0.75, 0.75)):
            for name, n, pattern, s in (("product", 2, "hard", 0.0),
                                        ("product", 3, "all_weak", 0.5),
                                        ("godel", 3, "all_weak", 0.5)):
                lo = tnorm(name, channels(n, pattern, s))
                gap = gap_for(name, n, pattern, s, chain_polarity(op))
                num = critical_beta(kind, lo * abs(chain_polarity(op)), abs(chain_polarity(op))) \
                    if gap > 0 else float("inf")
                pred = predicted_critical(kind, gap)
                rel = abs(num - pred) / pred if pred not in (0.0, float("inf")) else 0.0
                chain_cells.append({"kind": kind, "openness": list(op), "tnorm": name, "n": n,
                                    "pattern": pattern, "s": s, "gap": gap,
                                    "numeric_beta": num, "predicted_beta": pred,
                                    "abs_diff": abs(num - pred), "rel_diff": rel})
    c4 = all(cc["abs_diff"] <= 0.05 and cc["rel_diff"] <= 0.02 for cc in chain_cells)

    checks = {"V3_C1_polarity_product": c1, "V3_C2_dead_gate": c2,
              "V3_C3_reduces_to_phase4": c3, "V3_C4_chain_threshold_law": c4}
    return {"rows": rows, "chain_rows": chain_cells, "checks": checks,
            "worst_chain_abs_diff": max(cc["abs_diff"] for cc in chain_cells),
            "verdict": "SUPPORTED" if all(checks.values()) else "REFUTED"}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p5_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1
    payload = {"schema": "m2a.phase5.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE5_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "seeds": SEEDS, "alpha": ALPHA, "substrates": list(SUBSTRATES),
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}
    payload["V1"] = run_v1()
    print("V1:", payload["V1"]["verdict"], payload["V1"]["attribution"], flush=True)
    payload["V2"] = run_v2()
    print("V2:", payload["V2"]["verdict"], payload["V2"]["checks"], flush=True)
    payload["V3"] = run_v3()
    print("V3:", payload["V3"]["verdict"], payload["V3"]["checks"], flush=True)
    payload["verdicts"] = {k: payload[k]["verdict"] for k in ("V1", "V2", "V3")}
    json.dump(payload, open(HERE / "phase5_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
