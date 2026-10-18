"""Phase XX gate: instruments only (R2). Runs before the round; failure refuses the run."""
from __future__ import annotations

import json
import math
import pathlib
import sys

import p20_filter as p20

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    src = (HERE / "p20_filter.py").read_text(encoding="utf-8")
    check("G1_no_stochastic_stream", all(tok not in src for tok in ("random", "default_rng", "np.seed")),
          "no RNG anywhere in the instrument; seed pool disjoint by non-use")

    a = p20.reading("M3", 7, 1.3, True)
    check("G2_determinism", a == p20.reading("M3", 7, 1.3, True), f"M3(n=7,c=1.3,scale_tau) = {a!r}")

    worst, where = 0.0, None
    for m in p20.MECHS:
        for n in p20.NS:
            for c in p20.CS:
                for st in (False, True):
                    diff = abs(p20.loop(m, n, c, st) - p20.reading(m, n, c, st))
                    if diff > worst:
                        worst, where = diff, (m, n, c, st)
    check("G3_two_paths_agree_all_mechs", worst <= p20.TOL,
          f"worst abs diff {worst:.3e} at {where} (tol {p20.TOL:.0e}); "
          f"R7 ratio tol/observed = {'undefined (observed 0)' if worst == 0 else format(p20.TOL / worst, ',.1f')}")

    check("G4_degenerate_n_equals_one", abs(p20.reading("M1", 1, 1.0, False) - p20.ETA) <= 1e-15
          and abs(p20.reading("M3", 1, 1.0, False) - p20.ETA) <= 1e-15,
          f"M1=M3=eta={p20.reading('M1', 1, 1.0, False):.3f}")

    big = p20.reading("M3", 10 ** 6, 1.0, False)
    check("G5_lambda_to_one_guard", math.isfinite(big) and big > 0.0, f"n=1e6 gives M3={big:.4f} finite")

    vals = [p20.reading(m, n, c, st) for m in p20.MECHS for n in p20.NS for c in p20.CS for st in (False, True)]
    check("G6_ranges_and_finiteness", all(math.isfinite(v) for v in vals) and min(vals) >= 0.0
          and max(vals) <= 20 * p20.ETA + 1e-12, f"{len(vals)} readings in [{min(vals):.4f}, {max(vals):.4f}]")

    d19 = json.loads((HERE / "phase19_results.json").read_text(encoding="utf-8"))["pass_matrix"]
    cl = p20.classify()
    same_a = {m: abs(cl[m]["A_spread"] - d19[m]["spread_A"]) for m in p20.MECHS}
    check("G7_cross_round_A_consistency", all(v <= 1e-15 for v in same_a.values()),
          "A spreads vs phase19_results.json deltas " + str({m: format(v, ".1e") for m, v in same_a.items()}))

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rc = main()
    if rc:
        print("gate refused the run", file=sys.stderr)
    sys.exit(rc)
