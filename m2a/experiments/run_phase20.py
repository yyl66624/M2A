"""Phase XX runner: gate first, then the registered criteria, then exits in registered order."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import p20_filter as p20

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE / "PHASE20_PREREGISTRATION.md"


def main() -> int:
    gate = subprocess.run([sys.executable, "p20_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSED: gate did not pass, the round does not run", file=sys.stderr)
        return 2

    anchor = {}
    for m in p20.MECHS:
        for st in (False, True):
            anchor[f"{m}|{'V' if st else 'S'}"] = abs(p20.loop(m, 20, 1.0, st) - p20.reading(m, 20, 1.0, st))
    worst = max(anchor.values())
    c1 = worst <= p20.TOL

    cl = p20.classify()
    modes = {m: (cl[m]["A_pass"], cl[m]["S_pass"], cl[m]["V_pass"]) for m in p20.MECHS}
    distinct = len(set(modes.values())) == 3
    pairwise = all(any(modes[a][i] != modes[b][i] for i in range(3))
                   for a in p20.MECHS for b in p20.MECHS if a < b)
    c2 = distinct and pairwise
    c3 = any(cl[m]["A_pass"] and cl[m]["S_pass"] and cl[m]["V_pass"] for m in p20.MECHS)

    m1_A = [p20.reading("M1", n, 1.0, False) for n in p20.NS]
    min_step = min(b - a for a, b in zip(m1_A, m1_A[1:]))
    c4 = (min_step > 0 and cl["M2"]["S_spread"] >= p20.SENS and cl["M3"]["V_spread"] <= p20.TOL)

    exits = {
        "E0 ANCHOR-BROKEN": not c1,
        "E1 FILTER-USABLE": c1 and c2 and c3 and c4,
        "E4 DIRECTION-BROKEN": c1 and not c4,
        "E2 FILTER-INSENSIBLE": c1 and not c2,
        "E3 TEST-UNSATISFIABLE": c1 and c2 and not c3,
    }
    order = ["E0 ANCHOR-BROKEN", "E1 FILTER-USABLE", "E4 DIRECTION-BROKEN",
             "E2 FILTER-INSENSIBLE", "E3 TEST-UNSATISFIABLE"]
    exit_name = next((k for k in order if exits[k]), "E-UNMAPPED")

    out = {
        "schema": "m2a.phase20.results.v1",
        "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "tolerance": {"tol": p20.TOL, "sens": p20.SENS},
        "criteria": {"C20-1 ANCHOR": c1, "C20-2 FILTER-SEPARATES": c2,
                     "C20-3 TEST-SATISFIABLE": c3, "C20-4 DIRECTION": c4},
        "anchor": {"worst_abs_diff": worst, "per_path": anchor,
                   "r7_ratio_tol_over_observed": None if worst == 0.0 else p20.TOL / worst},
        "spreads": {m: {k: cl[m][k] for k in ("A_spread", "S_spread", "V_spread")} for m in p20.MECHS},
        "modes": {m: list(modes[m]) for m in p20.MECHS},
        "distinct_modes": len(set(modes.values())),
        "pairwise_separable": pairwise,
        "direction": {"M1_min_step_over_n": min_step,
                      "M2_S_spread_over_sens": cl["M2"]["S_spread"] / p20.SENS,
                      "M3_V_spread": cl["M3"]["V_spread"]},
        "prior_predictions_written_before_run": {
            m: {"predicted": {"M1": [False, False, True], "M2": [True, True, True],
                              "M3": [False, True, True]}[m],
                "observed": list(modes[m]),
                "confirmed": list(modes[m]) == {"M1": [False, False, True], "M2": [True, True, True],
                                                "M3": [False, True, True]}[m]} for m in p20.MECHS},
        "exits": exits, "exit": exit_name,
    }
    (HERE / "phase20_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nC20-1 anchor {c1} (worst {worst:.3e}, R7 ratio "
          f"{'undefined' if worst == 0 else format(p20.TOL / worst, ',.1f')})")
    for m in p20.MECHS:
        print(f"   {m}: A {cl[m]['A_spread']:.3e} {'pass' if cl[m]['A_pass'] else 'FAIL'} | "
              f"S {cl[m]['S_spread']:.3e} {'pass' if cl[m]['S_pass'] else 'FAIL'} | "
              f"V {cl[m]['V_spread']:.3e} {'pass' if cl[m]['V_pass'] else 'FAIL'}")
    print(f"C20-2 separates {c2} (distinct modes {len(set(modes.values()))}, pairwise {pairwise}) | "
          f"C20-3 satisfiable {c3} | C20-4 direction {c4}")
    print(f"EXIT -> {exit_name}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
