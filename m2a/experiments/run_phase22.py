"""Phase XXII runner: gate first, then C22-1..4, then exits in the registered order."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import p20_filter as p20
import p22_powerlaw as p22
from p6_systems import loglog_slope

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE / "PHASE22_PREREGISTRATION.md"
SLOPE_TOL = 1e-9    # registered in C22-4
PREDICTED_A_PASS = {"M2", "N1"}


def main() -> int:
    gate = subprocess.run([sys.executable, "p22_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSED: gate did not pass, the round does not run", file=sys.stderr)
        return 2

    anchor = {f"{c}|{'V' if st else 'S'}": abs(p22.loop(c, 20, 1.0, st) - p22.reading(c, 20, 1.0, st))
              for c in p22.CLASSES for st in (False, True)}
    worst = max(anchor.values())
    c1 = worst <= p20.TOL

    cl = p22.classify_all()
    a_pass = {c for c in p22.CLASSES if cl[c]["A_pass"]}
    f_a_pass = {c for c in a_pass if c.startswith("F")}
    c2 = a_pass == PREDICTED_A_PASS and not f_a_pass

    all3 = {c for c in p22.CLASSES if cl[c]["A_pass"] and cl[c]["S_pass"] and cl[c]["V_pass"]}
    c3 = all3 == {"M2"}

    slopes = {}
    for p in p22.PS:
        ys = p22.n_series(p)
        slopes[f"N{p:g}"] = {"observed": loglog_slope(list(p20.NS), ys), "analytic": 1.0 - p}
    slopes_ok = all(abs(s["observed"] - s["analytic"]) <= SLOPE_TOL for s in slopes.values())
    v_by_p = [cl[p22.label_of("N", p)]["V_spread"] for p in p22.PS]
    v_mono = all(b > a for a, b in zip(v_by_p, v_by_p[1:]))
    c4 = slopes_ok and v_mono

    exits = {
        "E0 ANCHOR-BROKEN": not c1,
        "E1 FAMILY-MAP-AS-PREDICTED": c1 and c2 and c3 and c4,
        "E2 A-MISCLAIMS-BROADER": c1 and (a_pass - PREDICTED_A_PASS or bool(f_a_pass)),
        "E3 UNIQUENESS-LOST": c1 and c2 and all3 != {"M2"},
        "E4 DIRECTION-BROKEN": c1 and not c4,
    }
    order = ["E0 ANCHOR-BROKEN", "E1 FAMILY-MAP-AS-PREDICTED", "E2 A-MISCLAIMS-BROADER",
             "E3 UNIQUENESS-LOST", "E4 DIRECTION-BROKEN"]
    exit_name = next((k for k in order if exits[k]), "E-UNMAPPED")

    out = {
        "schema": "m2a.phase22.results.v1",
        "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "tolerance": {"TOL": p20.TOL, "SENS": p20.SENS, "SLOPE_TOL": SLOPE_TOL},
        "classes": list(p22.CLASSES), "p_grid": list(p22.PS),
        "criteria": {"C22-1 ANCHOR": c1, "C22-2 A-COVER-AS-PREDICTED": c2,
                     "C22-3 UNIQUENESS-ACROSS-FAMILY": c3, "C22-4 POWER-LAW-DIRECTION": c4},
        "anchor": {"worst_abs_diff": worst, "per_class": anchor,
                   "r7_ratio_tol_over_observed": None if worst == 0.0 else p20.TOL / worst},
        "spreads": {c: {k + "_spread": cl[c][k + "_spread"] for k in ("A", "S", "V")} for c in p22.CLASSES},
        "modes": {c: [cl[c]["A_pass"], cl[c]["S_pass"], cl[c]["V_pass"]] for c in p22.CLASSES},
        "a_passing_classes": sorted(a_pass), "predicted_a_passing": sorted(PREDICTED_A_PASS),
        "all_three_passing": sorted(all3),
        "slope_check": slopes, "N_family_v_spreads_by_p": v_by_p, "N_v_spread_strictly_increasing": v_mono,
        "exits": exits, "exit": exit_name,
    }
    (HERE / "phase22_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nC22-1 anchor {c1} (worst {worst:.3e}, R7 ratio "
          f"{'undefined' if worst == 0 else format(p20.TOL / worst, ',.1f')})")
    for c in p22.CLASSES:
        print(f"   {c:<5} A {cl[c]['A_spread']:.3e} {'pass' if cl[c]['A_pass'] else 'FAIL'} | "
              f"S {cl[c]['S_spread']:.3e} {'pass' if cl[c]['S_pass'] else 'FAIL'} | "
              f"V {cl[c]['V_spread']:.3e} {'pass' if cl[c]['V_pass'] else 'FAIL'}")
    print(f"C22-2 A-cover as predicted {c2} (A-passing {sorted(a_pass)}) | C22-3 uniqueness {c3} (all-three {sorted(all3)})")
    print(f"C22-4 direction {c4} (slopes ok {slopes_ok}, N V-spreads increasing {v_mono})")
    print(f"EXIT -> {exit_name}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
