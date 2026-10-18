"""Phase XXI gate: instruments only (R2), plus the cross-round identity the preregistration demands."""
from __future__ import annotations

import json
import math
import pathlib
import sys

import p20_filter as p20
import p21_integral as p21

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    src = (HERE / "p21_integral.py").read_text(encoding="utf-8")
    check("G1_no_stochastic_stream", all(tok not in src for tok in ("random", "default_rng", "np.seed")),
          "no RNG in the extended instrument")

    a = p21.reading("M5", 9, 0.7, True)
    check("G2_determinism", a == p21.reading("M5", 9, 0.7, True), f"M5(n=9,c=0.7,scale_tau) = {a!r}")

    worst, where = 0.0, None
    for m in p21.MECHS5:
        for n in p20.NS:
            for c in p20.CS:
                for st in (False, True):
                    diff = abs(p21.loop(m, n, c, st) - p21.reading(m, n, c, st))
                    if diff > worst:
                        worst, where = diff, (m, n, c, st)
    check("G3_two_paths_agree_five_mechs", worst <= p20.TOL,
          f"worst abs diff {worst:.3e} at {where} (tol {p20.TOL:.0e}); "
          f"R7 ratio tol/observed = {'undefined (observed 0)' if worst == 0 else format(p20.TOL / worst, ',.1f')}")

    m4_1 = p21.reading("M4", 1, 1.0, False)
    m5_1 = p21.reading("M5", 1, 1.0, False)
    check("G4_degenerate_n_equals_one", abs(m4_1 - p20.ETA * p20.T) <= 1e-15 and abs(m5_1 - p20.ETA * p20.T) <= 1e-15,
          f"M4=M5=eta*T={p20.ETA * p20.T:.3f}")

    lam1 = p21.reading("M5", p21.N_LIMIT, 1.0, False)
    # with n = T/dt, lambda^n -> exp(-T/tau) (not 0), so the sum scales as 1/dt and V -> the integral.
    # The lambda -> 1 branch matching M4 only holds at fixed n, i.e. as total duration -> 0.
    check("G5_fine_grained_limit_converges_to_integral", math.isfinite(lam1)
          and abs(lam1 - p21.integral_limit()) <= p21.bound_limit(),
          f"M5(n=1e6)={lam1:.10f} vs integral={p21.integral_limit():.10f}, gap "
          f"{abs(lam1 - p21.integral_limit()):.3e} <= derived bound {p21.bound_limit():.3e}")

    d19_20 = json.loads((HERE / "phase20_results.json").read_text(encoding="utf-8"))["spreads"]
    cl = p21.classify5()
    deltas = {m: abs(cl[m][k + "_spread"] - d19_20[m][k + "_spread"]) for m in p20.MECHS for k in ("A", "S", "V")}
    check("G6_cross_round_identical_spreads", all(v == 0.0 for v in deltas.values()),
          f"max delta over M1-M3 x A/S/V = {max(deltas.values()):.1e} (must be exactly 0)")

    bound = p21.bound_limit()
    recomputed = p20.ETA * (p20.T / p21.N_LIMIT) * (1.0 - math.exp(-p20.T / p20.TAU))
    check("G7_bound_limit_is_the_derived_formula", abs(bound - recomputed) <= 1e-18
          and bound > p20.TOL, f"BOUND_LIMIT={bound:.4e} (analytic monotone-Riemann bound, 6 orders above TOL)")

    vals = [p21.reading(m, n, c, st) for m in p21.MECHS5 for n in p20.NS for c in p20.CS for st in (False, True)]
    check("G8_ranges_and_finiteness", all(math.isfinite(v) for v in vals) and min(vals) >= 0.0
          and max(vals) <= 20 * p20.ETA + p20.ETA * p20.T + 1e-12,
          f"{len(vals)} readings in [{min(vals):.4f}, {max(vals):.4f}]")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rc = main()
    if rc:
        print("gate refused the run", file=sys.stderr)
    sys.exit(rc)
