"""Phase XXII gate: instruments only (R2), including family identities and the cross-round tie."""
from __future__ import annotations

import json
import math
import pathlib
import sys

import p20_filter as p20
import p21_integral as p21
import p22_powerlaw as p22

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    src = (HERE / "p22_powerlaw.py").read_text(encoding="utf-8")
    check("G1_no_stochastic_stream", all(tok not in src for tok in ("random", "default_rng", "np.seed")), "no RNG")

    a = p22.reading("F1.5", 11, 0.8, True)
    check("G2_determinism", a == p22.reading("F1.5", 11, 0.8, True), f"F1.5(n=11,c=0.8) = {a!r}")

    worst, where = 0.0, None
    for cls in p22.CLASSES:
        for n in p20.NS:
            for c in p20.CS:
                for st in (False, True):
                    diff = abs(p22.loop(cls, n, c, st) - p22.reading(cls, n, c, st))
                    if diff > worst:
                        worst, where = diff, (cls, n, c, st)
    check("G3_two_paths_agree_all_classes", worst <= p20.TOL,
          f"worst abs diff {worst:.3e} at {where} (tol {p20.TOL:.0e}); R7 ratio tol/observed = "
          f"{'undefined (observed 0)' if worst == 0 else format(p20.TOL / worst, ',.1f')}")

    idn = max(abs(p22.reading("N0", n, c, st) - p20.reading("M1", n, c, st))
              for n in p20.NS for c in p20.CS for st in (False, True))
    idf = max(abs(p22.reading("F0", n, c, st) - p20.reading("M3", n, c, st))
              for n in p20.NS for c in p20.CS for st in (False, True))
    check("G4_family_endpoints_are_known_classes", idn <= p20.TOL and idf <= p20.TOL,
          f"N(0) vs M1 max diff {idn:.1e}; F(0) vs M3 max diff {idf:.1e}")

    fine = p22.reading("F1", 10 ** 6, 1.0, False)
    check("G5_lambda_to_one_guard", math.isfinite(fine) and abs(fine - p21.integral_limit()) <= p21.bound_limit(),
          f"F1(n=1e6)={fine:.10f} vs integral {p21.integral_limit():.10f} (bound {p21.bound_limit():.1e})")

    d21 = json.loads((HERE / "phase21_results.json").read_text(encoding="utf-8"))["spreads"]
    cl = p21.classify5()
    deltas = {m: max(abs(cl[m][k + "_spread"] - d21[m][k + "_spread"]) for k in ("A", "S", "V")) for m in p20.MECHS}
    check("G6_cross_round_XXI_tie", all(v == 0.0 for v in deltas.values()),
          f"max delta over M1-M5 = {max(deltas.values()):.1e} (must be exactly 0)")

    vals = [p22.reading(c, n, cc, st) for c in p22.CLASSES for n in p20.NS for cc in p20.CS for st in (False, True)]
    check("G7_ranges_and_finiteness", all(math.isfinite(v) for v in vals) and min(vals) > 0.0,
          f"{len(vals)} readings in [{min(vals):.4e}, {max(vals):.4e}]")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rc = main()
    if rc:
        print("gate refused the run", file=sys.stderr)
    sys.exit(rc)
