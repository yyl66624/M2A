"""Run Phase V-d: confirmation of the L3 closed form on the fresh seed pool 100-109."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p5d_confirm import ARMS_D, QS_D, SEEDS_D, STEPS_D, closed, dp_d, law_old, readout_d

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
MID_D = [0.6, 0.7, 0.8, 0.9]
TOL = {"D1": 0.008, "D3": 0.008, "D4": 0.008}


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p5d_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1

    committed = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V1"]["rows"]
    rows = {}
    for arm in ARMS_D:
        for q in QS_D:
            vals = np.array([readout_d(q, s, arm) for s in SEEDS_D])
            rows[f"{arm}|{q}"] = {
                "steps": STEPS_D, "mc_mean": float(vals.mean()), "mc_sd": float(vals.std(ddof=1)),
                "mc_se": float(vals.std(ddof=1) / len(SEEDS_D) ** 0.5),
                "closed": closed(q), "law_old": law_old(q), "dp": dp_d(q),
                "mc_minus_closed": float(abs(vals.mean() - closed(q))),
                "mc_minus_law": float(abs(vals.mean() - law_old(q))),
                "mc_minus_dp": float(abs(vals.mean() - dp_d(q))),
            }

    d1 = {a: max(rows[f"{a}|{q}"]["mc_minus_closed"] for q in QS_D) for a in ARMS_D}
    d3 = {a: max(rows[f"{a}|{q}"]["mc_minus_dp"] for q in QS_D) for a in ARMS_D}
    d4 = {str(q): abs(rows[f"confirm_annealed|{q}"]["mc_mean"] - committed[f"base|{q}"]["mc_mean"])
          for q in QS_D}
    d2_items = [q for q in MID_D
                if rows[f"confirm_annealed|{q}"]["mc_mean"] < law_old(q)
                and rows[f"confirm_annealed|{q}"]["mc_minus_law"] > rows[f"confirm_annealed|{q}"]["mc_minus_closed"]]
    checks = {"D1_closed_form": all(v <= TOL["D1"] for v in d1.values()),
              "D2_two_laws_distinguishable": len(d2_items) >= 3,
              "D3_dp_agreement": all(v <= TOL["D3"] for v in d3.values()),
              "D4_cross_seed_reproducibility": all(v <= TOL["D4"] for v in d4.values())}
    outcome = "CONFIRMED" if (checks["D1_closed_form"] and checks["D3_dp_agreement"]
                             and checks["D4_cross_seed_reproducibility"]) else "NOT_CONFIRMED"
    payload = {"schema": "m2a.phase5d.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE5D_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "seeds": SEEDS_D, "legacy_seeds_excluded": True, "steps": STEPS_D,
               "tolerances": TOL, "rows": rows,
               "D1_worst_by_arm": d1, "D3_worst_by_arm": d3, "D4_by_q": d4,
               "D2_q_count": len(d2_items), "D2_q_values": d2_items,
               "checks": checks, "outcome": outcome,
               "stop_rule": "this is the third and final round on the L3 residual (PHASE5D §5)",
               "prior_rounds_unchanged": {"V1": "J_NOT_DECISIVE", "V-c": "J_NOT_DECISIVE"},
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}
    json.dump(payload, open(HERE / "phase5d_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("D1 worst |MC-closed| by arm:", {k: round(v, 4) for k, v in d1.items()})
    print("D3 worst |MC-dp| by arm:", {k: round(v, 4) for k, v in d3.items()})
    print("D4 by q:", {k: round(v, 4) for k, v in d4.items()})
    print("D2:", len(d2_items), d2_items)
    print("checks:", checks)
    print("outcome:", outcome)
    for q in QS_D:
        r = rows[f"confirm_annealed|{q}"]
        print(f"  q={q}: MC {r['mc_mean']:.4f} (sd {r['mc_sd']:.4f}) closed {r['closed']:.4f} "
              f"law_old {r['law_old']:.4f} dp {r['dp']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
