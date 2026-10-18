"""Run Phase VIII: does a smooth (Edgeworth) closed form remove the sawtooth of the counting system?"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from math import sqrt

from p6_systems import loglog_slope
from p8_smooth import C1, Z95, poisson_quantile, rho_exact, rho_normal_only, rho_smooth

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
S_GRID = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9)
LAMBDA_BIG = 100.0
P6_S = (0.25, 0.4, 0.5, 0.6, 0.75, 0.8)


def main() -> int:
    gate = subprocess.run([sys.executable, str(HERE / "p8_gate.py")], capture_output=True, text=True)
    print(gate.stdout)
    if gate.returncode != 0:
        print("REFUSING TO RUN: gate failed")
        return 1

    rows = {}
    for s in S_GRID:
        ex, sm, nm = rho_exact(s), rho_smooth(s), rho_normal_only(s)
        rows[str(s)] = {"gap": 1.0 - s, "rho_exact": ex, "rho_smooth": sm, "rho_normal_only": nm,
                        "lambda_hi": ex, "rel_exact_vs_smooth": abs(ex / sm - 1.0),
                        "rel_exact_vs_normal": abs(ex / nm - 1.0),
                        "deviation": ex - sm, "deviation_times_sqrt_lambda": (ex - sm) * sqrt(ex)}

    big = [r for r in rows.values() if r["lambda_hi"] >= LAMBDA_BIG]
    small = [r for r in rows.values() if r["lambda_hi"] < LAMBDA_BIG]
    p8_1_slope = loglog_slope([r["gap"] for r in big], [r["rho_smooth"] for r in big]) if len(big) >= 3 else None
    p8_1 = p8_1_slope is not None and abs(p8_1_slope + 2.0) <= 0.05
    p8_2 = all(r["rel_exact_vs_smooth"] <= 0.01 for r in big)
    devs = sorted(rows.values(), key=lambda r: r["lambda_hi"])
    lo, hi = devs[0]["deviation_times_sqrt_lambda"], devs[-1]["deviation_times_sqrt_lambda"]
    p8_3 = abs(lo / hi - 1.0) <= 0.25 if (hi and lo and hi > 0) else False
    p8_4a = all(abs(rho_smooth(s, with_c1=False) - rho_normal_only(s)) <= 1e-9 for s in (0.25, 0.5, 0.8))
    p8_4b = rho_smooth(1.0) == float("inf")
    p8_4c = all(abs(poisson_quantile(lam, 0.95) - (lam + Z95 * sqrt(lam) + C1)) <= 1.0
                for lam in (10.0, 30.0, 100.0))
    p8_4 = p8_4a and p8_4b and p8_4c

    committed = {r["s"]: r["rho_numeric"]
                 for r in json.loads((HERE / "phase6_results.json").read_text(encoding="utf-8"))
                 ["S2"]["rows"]}
    p8_5_detail = {str(s): {"phase6": committed[s], "this_round": rows[str(s)]["rho_exact"],
                            "abs_diff": abs(committed[s] - rows[str(s)]["rho_exact"])}
                   for s in P6_S if str(s) in rows}
    p8_5 = bool(p8_5_detail) and all(v["abs_diff"] <= 1e-6 for v in p8_5_detail.values())

    checks = {"P8_1_smooth_slope_minus_two": bool(p8_1), "P8_2_smooth_tracks_exact": bool(p8_2),
              "P8_3_sawtooth_scales_as_lambda_minus_half": bool(p8_3), "P8_4_reductions": bool(p8_4),
              "P8_5_reproduces_phase6": bool(p8_5)}
    if not (p8_4 and p8_5):
        exit_ = "E4 NOT-VALID (instrument disagrees with the committed Phase VI readings)"
    elif p8_1 and p8_2:
        exit_ = "E1 SMOOTH-LAW"
    elif not p8_1:
        exit_ = "E2 EXPONENT-NOT-MINUS-TWO"
    else:
        exit_ = "E3 NO-SMOOTH-CLOSURE"

    payload = {"schema": "m2a.phase8.results.v1",
               "prereg_sha256": hashlib.sha256(
                   (HERE / "PHASE8_PREREGISTRATION.md").read_bytes()).hexdigest(),
               "alpha": 0.05, "c1": C1, "s_grid": list(S_GRID), "lambda_big_cut": LAMBDA_BIG,
               "rows": rows, "n_big_lambda_cells": len(big), "n_small_lambda_cells": len(small),
               "P8_1_slope": p8_1_slope, "P8_3_deviation_scaled": {"smallest_Lambda": lo, "largest_Lambda": hi},
               "P8_5_detail": p8_5_detail, "checks": checks, "exit": exit_,
               "verdict": "SUPPORTED" if exit_ == "E1 SMOOTH-LAW" else "QUALIFIED",
               "phase6_verdict_unchanged": "S2 stays REFUTED (P8-F4); this round only explains its readings",
               "runtime": {"python": sys.version.split()[0]}}
    json.dump(payload, open(HERE / "phase8_results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("P8-1 slope of smooth curve (Lambda>=100):", None if p8_1_slope is None else round(p8_1_slope, 4),
          f"(n={len(big)} cells)")
    print("P8-2 max rel exact-vs-smooth on that subfamily:",
          round(max(r['rel_exact_vs_smooth'] for r in big), 5) if big else None)
    print("P8-3 deviation*sqrt(Lambda):", round(lo, 5), "vs", round(hi, 5))
    print("P8-5 max abs diff vs committed Phase VI:",
          max(v["abs_diff"] for v in p8_5_detail.values()) if p8_5_detail else None)
    print("checks:", checks)
    print("exit:", exit_)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
