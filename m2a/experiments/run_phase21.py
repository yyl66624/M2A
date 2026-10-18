"""Phase XXI runner: gate first, then C21-1..4, then exits in the registered order."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import p20_filter as p20
import p21_integral as p21

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE / "PHASE21_PREREGISTRATION.md"

PRIOR = {"M1": [False, False, True], "M2": [True, True, True], "M3": [False, True, True],
         "M4": [True, True, False], "M5": [False, True, False]}


def main() -> int:
    gate = subprocess.run([sys.executable, "p21_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSED: gate did not pass, the round does not run", file=sys.stderr)
        return 2

    anchor = {f"{m}|{'V' if st else 'S'}": abs(p21.loop(m, 20, 1.0, st) - p21.reading(m, 20, 1.0, st))
              for m in p21.MECHS5 for st in (False, True)}
    worst = max(anchor.values())
    c1 = worst <= p20.TOL

    cl = p21.classify5()
    modes = {m: (cl[m]["A_pass"], cl[m]["S_pass"], cl[m]["V_pass"]) for m in p21.MECHS5}
    distinct = len(set(modes.values())) == 5
    pairwise = all(any(modes[a][i] != modes[b][i] for i in range(3))
                   for i, a in enumerate(p21.MECHS5) for b in p21.MECHS5[i + 1:])
    c2 = distinct and pairwise

    all_pass = [m for m in p21.MECHS5 if all(modes[m])]
    a_passers = [m for m in p21.MECHS5 if modes[m][0]]
    c3 = len(all_pass) == 1

    m4_c = [p21.reading("M4", 5, c, False) for c in p20.CS]
    m4_mono = all(b > a for a, b in zip(m4_c, m4_c[1:]))
    dev = p21.m5_deviation_series()
    dev_mono = all(b < a for a, b in zip(dev, dev[1:]))
    lim_gap = abs(p21.reading("M5", p21.N_LIMIT, 1.0, False) - p21.integral_limit())
    bound = p21.bound_limit()
    c4 = m4_mono and dev_mono and lim_gap <= bound

    exits = {
        "E0 ANCHOR-BROKEN": not c1,
        "E1 UNIQUE-AND-SEPARABLE": c1 and c2 and c3 and c4,
        "E2 NOT-UNIQUE": c1 and c2 and not c3,
        "E4 DIRECTION-BROKEN": c1 and not c4,
        "E3 FILTER-COLLAPSED": c1 and not c2,
    }
    order = ["E0 ANCHOR-BROKEN", "E1 UNIQUE-AND-SEPARABLE", "E2 NOT-UNIQUE",
             "E4 DIRECTION-BROKEN", "E3 FILTER-COLLAPSED"]
    exit_name = next((k for k in order if exits[k]), "E-UNMAPPED")

    out = {
        "schema": "m2a.phase21.results.v1",
        "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "tolerance": {"TOL": p20.TOL, "SENS": p20.SENS, "BOUND_LIMIT": bound},
        "criteria": {"C21-1 ANCHOR": c1, "C21-2 FILTER-SEPARATES": c2,
                     "C21-3 UNIQUENESS-OF-ALL-PASS": c3, "C21-4 DIRECTION": c4},
        "anchor": {"worst_abs_diff": worst, "per_path": anchor,
                   "r7_ratio_tol_over_observed": None if worst == 0.0 else p20.TOL / worst},
        "spreads": {m: {k + "_spread": cl[m][k + "_spread"] for k in ("A", "S", "V")} for m in p21.MECHS5},
        "modes": {m: list(modes[m]) for m in p21.MECHS5},
        "all_pass_classes": all_pass, "a_passing_classes": a_passers,
        "direction": {"M4_readings_over_c": m4_c, "M4_strictly_monotone": m4_mono,
                      "M5_deviation_series": dev, "M5_deviation_strictly_decreasing": dev_mono,
                      "M5_limit_gap": lim_gap, "limit_gap_within_bound": lim_gap <= bound},
        "prior_predictions_written_before_run": {
            m: {"predicted": PRIOR[m], "observed": list(modes[m]), "confirmed": list(modes[m]) == PRIOR[m]}
            for m in p21.MECHS5},
        "exits": exits, "exit": exit_name,
    }
    (HERE / "phase21_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nC21-1 anchor {c1} (worst {worst:.3e}, R7 ratio "
          f"{'undefined' if worst == 0 else format(p20.TOL / worst, ',.1f')})")
    for m in p21.MECHS5:
        print(f"   {m}: A {cl[m]['A_spread']:.3e} {'pass' if cl[m]['A_pass'] else 'FAIL'} | "
              f"S {cl[m]['S_spread']:.3e} {'pass' if cl[m]['S_pass'] else 'FAIL'} | "
              f"V {cl[m]['V_spread']:.3e} {'pass' if cl[m]['V_pass'] else 'FAIL'} "
              f"| prior confirmed {list(modes[m]) == PRIOR[m]}")
    print(f"C21-2 separates {c2} | all-pass classes {all_pass} | A-passing classes {a_passers}")
    print(f"C21-4 direction {c4} (M4 monotone {m4_mono}, M5 dev decreasing {dev_mono}, "
          f"limit gap {lim_gap:.3e} <= bound {bound:.3e})")
    print(f"EXIT -> {exit_name}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
