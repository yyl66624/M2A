"""Phase XII gate: instrument only. Reports the smallest difference each check could distinguish (R7)."""
from __future__ import annotations

import json
import pathlib
import sys

from p8_smooth import C1
import p12_lattice as p12

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    committed = json.loads((HERE / "phase8_results.json").read_text(encoding="utf-8"))
    s_grid, rows = committed["s_grid"], committed["rows"]
    lam = {k: v["lambda_hi"] for k, v in rows.items()}

    e = [p12.root_large(1.0, 2 * C1) is None,
         all(p12.root_small(s, 0.0) is None for s in s_grid),
         p12.root_small(0.9, -3.0) is None or p12.root_small(0.9, -3.0) > 0.0]
    closed = max(abs(p12.rho_smooth(1.137, s) -
                     ((p12.B(s) + (p12.B(s) ** 2 + 4 * (1 - s) * 1.137) ** 0.5) /
                      (2 * (1 - s))) ** 2) / p12.rho_smooth(1.137, s) for s in s_grid)
    e.append(closed <= 1e-12)
    check("Z1_endpoints_and_closed_form_branch", all(e),
          f"{sum(e)}/{len(e)} paths ok; bisection vs explicit quadratic root max rel {closed:.2e} "
          f"(tol 1e-12, spare {1e-12 - closed:.2e})")

    worst = max(abs(p12.rho_smooth(2 * C1, s) - rows[str(s)]["rho_smooth"]) /
                rows[str(s)]["rho_smooth"] for s in s_grid)
    exp_big = p12.exponent(2 * C1, p12.subset(s_grid, lam, 100.0))
    check("Z2_e0_phase8_reproduces_committed_readings", worst <= 1e-9
          and abs(exp_big - committed["P8_1_slope"]) <= 1e-9,
          f"rho max rel {worst:.2e} (tol 1e-9, spare {1e-9 - worst:.2e}); "
          f"chord {exp_big:.12f} vs committed {committed['P8_1_slope']:.12f}")

    e0s = p12.fit_e0(s_grid, lam)
    check("Z3_fit_objective_well_posed", e0s[3]["n_finite"] == len(p12.E0_GRID)
          and not e0s[3]["at_boundary"],
          f"finite {e0s[3]['n_finite']}/{len(p12.E0_GRID)}, interior {not e0s[3]['at_boundary']}, "
          f"objective change per grid step {e0s[3]['objective_change_per_step']:.2e} "
          f"(smallest e0 shift this grid can distinguish: {e0s[3]['grid_step']})")

    a = p12.root_large(0.75, -0.4315, 60.0)
    b = p12.root_large(0.75, -0.4315, 60.0)
    check("Z4_determinism", a == b, f"large branch R = {a:.9f} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
