"""Run Phase V-c: time-homogeneous arms, per-arm declared DP duals, and the registered A3 closed form."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np

from p5c_arms import ARMS_C, MID_C, QS_C, dp_c, law_half, readout_c, visit_weighted

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
SEEDS = list(range(10))


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p5c_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1

    prev = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V1"]["rows"]
    rows = {}
    for arm, (_src, steps, _kw, _dp, faithful) in ARMS_C.items():
        for q in QS_C:
            vals = np.array([readout_c(q, s, arm) for s in SEEDS])
            d = dp_c(q, arm)
            rows[f"{arm}|{q}"] = {
                "steps": steps, "dp_faithful_declared": faithful,
                "mc_mean": float(vals.mean()), "mc_sd": float(vals.std(ddof=1)),
                "mc_se": float(vals.std(ddof=1) / len(SEEDS) ** 0.5),
                "dp": d, "law_half": law_half(q), "closed_form": visit_weighted(q),
                "mc_minus_dp": float(abs(vals.mean() - d)),
                "dp_minus_law": float(abs(d - law_half(q))),
                "mc_minus_law": float(abs(vals.mean() - law_half(q))),
                "mc_minus_closed": float(abs(vals.mean() - visit_weighted(q))),
            }

    anchor = {str(q): {"phase5_committed": prev[f"base|{q}"]["mc_mean"],
                       "this_run": rows[f"annealed_base|{q}"]["mc_mean"],
                       "abs_diff": abs(prev[f"base|{q}"]["mc_mean"] - rows[f"annealed_base|{q}"]["mc_mean"])}
              for q in QS_C}
    a0 = all(v["abs_diff"] <= 0.005 for v in anchor.values())
    faithful = [a for a, (_s, _st, _k, _d, f) in ARMS_C.items() if f]
    a1_detail = {a: max(rows[f"{a}|{q}"]["mc_minus_dp"] for q in QS_C) for a in faithful}
    a1 = all(v <= 0.008 for v in a1_detail.values())
    mid = lambda a, key: max(rows[f"{a}|{q}"][key] for q in MID_C)  # noqa: E731
    denom = mid("base_c", "mc_minus_law")
    a2 = (mid("base_c", "dp_minus_law") / denom) if denom > 1e-9 else float("nan")
    a3 = all(rows[f"base_c|{q}"]["mc_minus_closed"] <= 0.008 for q in QS_C)
    transient = mid("base_long_c", "mc_minus_law") < 0.5 * denom

    if not a0:
        outcome = "NOT_VALID (A0 anchor failed)"
    elif a1 and a3:
        outcome = "J_LAW_PRIOR"
    elif a1 and (a2 == a2 and a2 >= 0.75):
        outcome = "J_FIXED_POINT"
    elif a1 and transient:
        outcome = "J_TRANSIENT"
    else:
        outcome = "J_NOT_DECISIVE"

    checks = {"A0_anchor": a0, "A1_per_arm_dp_fidelity": a1,
              "A2_ratio_ge_075": bool(a2 == a2 and a2 >= 0.75), "A3_closed_form": a3,
              "transient_test": transient}
    verdict = "SUPPORTED" if outcome in ("J_LAW_PRIOR", "J_FIXED_POINT") else "NOT_EXPLAINED"
    payload = {"schema": "m2a.phase5c.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE5C_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "seeds": SEEDS, "tolerances": {"A0": 0.005, "A1": 0.008, "A2": 0.75, "A3": 0.008},
               "rows": rows, "anchor": anchor, "a1_worst_by_arm": a1_detail,
               "a2_ratio": float(a2) if a2 == a2 else None, "checks": checks,
               "outcome": outcome, "verdict": verdict,
               "v1_verdict_unchanged": "J_NOT_DECISIVE (registered in Phase V; P5c-F4)",
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}
    json.dump(payload, open(HERE / "phase5c_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("A1 worst |MC-DP| by arm:", {k: round(v, 4) for k, v in a1_detail.items()})
    print("A2 ratio:", round(a2, 4), "| A3:", a3, "| transient:", transient)
    print("outcome:", outcome, "verdict:", verdict)
    for q in QS_C:
        r = rows[f"base_c|{q}"]
        print(f"  q={q}: MC {r['mc_mean']:.4f} closed {r['closed_form']:.4f} dp {r['dp']:.4f} "
              f"law {r['law_half']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
