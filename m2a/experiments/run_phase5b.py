"""Run Phase V-b: the same 36 chain-conjunction cells as Phase V 3.2, on the resolution-derived grid.
Scientific tolerance is unchanged (relative <= 2%); V3's verdict is NOT re-judged by this round.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p4_mechanisms import SUBSTRATES, predicted_threshold
from p5_mechanisms import ALPHA, chain_polarity, channels, gap_for, predicted_critical, tnorm
from p5b_instrument import critical_beta_adaptive

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent

# cell set copied verbatim from run_phase5.py run_v3() -- no additions, no removals
OPS = ((0.75,), (0.75, 0.75), (0.25,), (0.75, 0.75, 0.75))
CONJ = (("product", 2, "hard", 0.0), ("product", 3, "all_weak", 0.5), ("godel", 3, "all_weak", 0.5))
OLD_GRID_POINTS = 4001


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p5b_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1

    prev = {(c["kind"], tuple(c["openness"]), c["tnorm"], c["n"], c["pattern"], c["s"]): c
            for c in json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))
            ["V3"]["chain_rows"]}
    rows = []
    for kind in SUBSTRATES:
        for op in OPS:
            for name, n, pattern, s in CONJ:
                key = (kind, op, name, n, pattern, s)
                assert key in prev, f"cell set drifted: {key}"
                lo_conj = tnorm(name, channels(n, pattern, s))
                pol = abs(chain_polarity(op))
                gap = gap_for(name, n, pattern, s, chain_polarity(op))
                r = critical_beta_adaptive(kind, lo_conj * pol, pol)
                pred = predicted_critical(kind, gap)
                old = prev[key]["numeric_beta"]
                dtheta_old = (gap + 1.0) / (OLD_GRID_POINTS - 1)
                bias_old = predicted_threshold(kind, ALPHA) * dtheta_old / (gap ** 2) if gap > 0 else 0.0
                rows.append({"kind": kind, "openness": list(op), "tnorm": name, "n": n,
                             "pattern": pattern, "s": s, "gap": gap,
                             "predicted_beta": pred, "numeric_beta": r["numeric_beta"],
                             "measurable": r["measurable"], "dtheta": r["dtheta"],
                             "n_points": r["n_points"],
                             "abs_diff": abs(r["numeric_beta"] - pred),
                             "rel_diff": (abs(r["numeric_beta"] - pred) / pred
                                          if pred not in (0.0, float("inf")) else 0.0),
                             "phase5_numeric_beta": old,
                             "shift_vs_phase5": abs(r["numeric_beta"] - old),
                             "phase5_discretisation_bound": bias_old})

    meas = [r for r in rows if r["measurable"]]
    vb1 = all(r["rel_diff"] <= 0.02 for r in meas)
    vb2 = abs(critical_beta_adaptive("logistic", 0.0, 1.0)["numeric_beta"]
              - predicted_threshold("logistic")) <= 0.005
    # VB-3: the pre-registered chain cell set contains no o=0.5 stage, so the dead-gate control is
    # run against the instrument itself on every substrate (zero gap => no window at any gain).
    from p5_mechanisms import window_exists
    vb3 = all(critical_beta_adaptive(k, 0.0, 0.0)["numeric_beta"] == float("inf")
              and not window_exists(k, 200.0, 0.0, 0.0) for k in SUBSTRATES)
    vb4 = all(r["shift_vs_phase5"] <= r["phase5_discretisation_bound"] + 1e-9 for r in meas)
    checks = {"VB1_relative_law": vb1, "VB2_reduction": vb2, "VB3_no_zero_gap": vb3,
              "VB4_shift_explained_by_resolution": vb4}
    verdict = "SUPPORTED" if (len(meas) == len(rows) and all(checks.values())) else "REFUTED"
    payload = {"schema": "m2a.phase5b.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE5B_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "note": "re-test of V3-C4 on a resolution-derived grid; does not re-judge Phase V",
               "alpha": ALPHA, "n_cells": len(rows), "rows": rows, "checks": checks,
               "worst_rel_diff": max(r["rel_diff"] for r in meas),
               "worst_abs_diff": max(r["abs_diff"] for r in meas),
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
               "verdict": verdict}
    json.dump(payload, open(HERE / "phase5b_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("V3-b:", verdict, checks)
    print("worst rel", round(payload["worst_rel_diff"], 6), "worst abs",
          round(payload["worst_abs_diff"], 5))
    for r in sorted(meas, key=lambda z: -z["rel_diff"])[:4]:
        print(f"  {r['kind']} o={r['openness']} {r['tnorm']} gap={r['gap']:.4f} "
              f"num={r['numeric_beta']:.4f} pred={r['predicted_beta']:.4f} "
              f"rel={r['rel_diff']:.2e} phase5={r['phase5_numeric_beta']:.4f} "
              f"shift={r['shift_vs_phase5']:.4f} bound={r['phase5_discretisation_bound']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
