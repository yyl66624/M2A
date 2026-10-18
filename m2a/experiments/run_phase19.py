"""Phase XIX runner: gate first, then the registered criteria, then take exits in registered order.

Nothing here may redefine a tolerance; C19-* read straight from PHASE19_PREREGISTRATION.md section 2.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys

import p19_timesym as p19

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE / "PHASE19_PREREGISTRATION.md"
TOL = p19.TOL


def main() -> int:
    gate = subprocess.run([sys.executable, "p19_gate.py"], cwd=HERE, capture_output=True, text=True)
    print(gate.stdout.strip())
    if gate.returncode != 0:
        print("REFUSED: gate did not pass, the round does not run", file=sys.stderr)
        return 2

    # C19-1 instrument anchor: recurrence vs an independent numerical path, no scaling, n = 20
    n, c = 20, 1.0
    r = p19.recurrence(n, c)
    m1_loop = sum(p19.ETA for _ in range(n))
    steps = c * p19.T / n
    m2_int = p19.V0
    for _ in range(n):
        m2_int *= math.exp(-steps / p19.TAU)
    m3_loop = 0.0
    lam = r["lambda"]
    for _ in range(n):
        m3_loop = lam * m3_loop + p19.ETA
    anchor = {"M1": abs(m1_loop - r["M1"]), "M2": abs(m2_int - r["M2"]), "M3": abs(m3_loop - r["M3"])}
    worst_anchor = max(anchor.values())
    c1 = worst_anchor <= TOL

    pat = p19.patterns()
    pass_a = {m: pat[m]["pass_A"] for m in pat}
    pass_b = {m: all(pat[m]["pass_B"].values()) for m in pat}
    modes = {(pass_a[m], pass_b[m]) for m in pat}
    c2 = (any(pass_a[m] and not pass_b[m] for m in pat)
          and any(not pass_a[m] for m in pat)
          and len(modes) >= 2)

    c3 = pass_a["M3"] and pass_b["M3"]

    m1_A = [row["M1"] for row in p19.thinning_at_fixed_T()]
    m1_min_step = min(b - a for a, b in zip(m1_A, m1_A[1:]))
    m2_B = [row["M2"] for row in p19.rescale_at_fixed_n(p19.NS[0])]
    m2_B_spread = max(m2_B) - min(m2_B)
    c4 = m1_min_step > 0 and m2_B_spread > TOL

    exits = {
        "E0 ANCHOR-BROKEN": not c1,
        "E1 TEST-DISCRIMINATES": c1 and c2 and c3 and c4,
        "E4 DIRECTION-BROKEN": c1 and not c4,
        "E2 TEST-VACUOUS": c1 and not c2,
        "E3 TEST-UNSATISFIABLE": c1 and c2 and not c3,
    }
    order = ["E0 ANCHOR-BROKEN", "E1 TEST-DISCRIMINATES", "E4 DIRECTION-BROKEN",
             "E2 TEST-VACUOUS", "E3 TEST-UNSATISFIABLE"]
    exit_name = next((k for k in order if exits[k]), "E-UNMAPPED")
    n_closed = sum(1 for v in exits.values() if v) + (1 if exit_name == "E-UNMAPPED" else 0)

    out = {
        "schema": "m2a.phase19.results.v1",
        "prereg_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "tolerance": TOL,
        "criteria": {"C19-1 ANCHOR": c1, "C19-2 TEST-DISCRIMINATES": c2,
                    "C19-3 HYBRID-PASSES-BOTH": c3, "C19-4 DIRECTION": c4},
        "anchor": {"worst_abs_diff": worst_anchor, "per_mechanism": anchor,
                   "r7_ratio_tol_over_observed": None if worst_anchor == 0.0 else TOL / worst_anchor},
        "pass_matrix": {m: {"A": pass_a[m], "B": pass_b[m],
                            "spread_A": pat[m]["spread_A"],
                            "max_spread_B": max(pat[m]["spread_B"].values())} for m in pat},
        "patterns": sorted([list(t) for t in modes]),
        "direction": {"M1_min_step_over_n": m1_min_step, "M2_spread_over_c": m2_B_spread},
        "exits": exits, "exit": exit_name,
        "prior_predictions_refuted": {
            "M3_passes_A": {"predicted_before_run": True, "observed": pass_a["M3"]},
            "M3_passes_B": {"predicted_before_run": True, "observed": pass_b["M3"]}},
        "exit_flags_true": n_closed, "verdict": exit_name,
    }
    (HERE / "phase19_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nC19-1 anchor {c1} (worst {worst_anchor:.3e}, tol {TOL:.0e}, "
          f"R7 ratio {'undefined: observed is 0' if worst_anchor == 0 else format(TOL / worst_anchor, '.4f')})")
    for m in ("M1", "M2", "M3"):
        print(f"   {m}: A {'pass' if pass_a[m] else 'FAIL'} (spread {pat[m]['spread_A']:.3e})  "
              f"B {'pass' if pass_b[m] else 'FAIL'} (max spread {max(pat[m]['spread_B'].values()):.3e})")
    print(f"C19-2 discriminates {c2} | C19-3 hybrid both {c3} | C19-4 direction {c4}")
    print(f"EXIT -> {exit_name}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
