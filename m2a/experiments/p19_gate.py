"""Phase XIX gate: instruments only (R2). No slope, effect size or scientific claim lives here.

Runs before the round is allowed to execute; failure refuses the run.
"""
from __future__ import annotations

import math
import pathlib
import sys

import p19_timesym as p19

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def loop_m3(n: int, dt: float, c: float) -> float:
    """Independent cross-path implementation: accumulate the trace event by event.

    Same clock convention as the module: the axis scale c multiplies both the interval and the
    mechanism's own time constant, so lambda is the one the module reports.
    """
    v = 0.0
    lam = math.exp(-dt / (c * p19.TAU))
    for _ in range(n):
        v = lam * v + p19.ETA
    return v


def main() -> int:
    src = (HERE / "p19_timesym.py").read_text(encoding="utf-8")
    check("G1_no_stochastic_stream", all(tok not in src for tok in ("random", "default_rng", "np.seed")),
          "module imports no RNG; seed pool disjoint from prior rounds by non-use")

    a = p19.recurrence(7, 1.3)
    b = p19.recurrence(7, 1.3)
    check("G2_determinism", a == b, f"M3(n=7,c=1.3) = {a['M3']!r} twice identical")

    # G3 cross-path anchor (R8): geometric closed form vs event-by-event loop, never self-compared
    worst, worst_cell, obs = 0.0, None, []
    for n in p19.NS:
        for c in p19.CS:
            r = p19.recurrence(n, c)
            diff = abs(loop_m3(n, r["dt"], c) - r["closed_M3"])
            obs.append(diff)
            if diff > worst:
                worst, worst_cell = diff, (n, c)
    tol = p19.TOL
    check("G3_m3_two_paths_agree", worst <= tol,
          f"worst abs diff {worst:.3e} at n,c={worst_cell} (tol {tol:.0e}); "
          f"R7 ratio tol/observed = {'undefined (observed 0)' if worst == 0.0 else format(tol / worst, '.4f')}; "
          f"median observed diff {sorted(obs)[len(obs)//2]:.2e}")

    r1 = p19.recurrence(1, 1.0)
    check("G4_degenerate_n_equals_one", abs(r1["M1"] - p19.ETA) <= 1e-15
          and abs(r1["M3"] - p19.ETA) <= 1e-15, f"M1=M3=eta={r1['M1']:.3f}")

    big = p19.recurrence(10 ** 6, 1.0)
    check("G5_lambda_to_one_guard", math.isfinite(big["M3"]) and big["M3"] > 0.0,
          f"n=1e6 gives lambda={big['lambda']:.6f}, M3={big['M3']:.6f} finite")

    vals = [v for r in [p19.recurrence(n, c) for n in p19.NS for c in p19.CS] for v in (r["M1"], r["M2"], r["M3"])]
    check("G6_ranges_and_finiteness", all(math.isfinite(v) for v in vals)
          and min(vals) >= 0.0 and max(vals) <= 20 * p19.ETA + 1e-12,
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
