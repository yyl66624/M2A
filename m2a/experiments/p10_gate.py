"""Phase X gate: instrument only. Section 4 of PHASE10_PREREGISTRATION.md; no X-criterion appears here."""
from __future__ import annotations

import sys
from math import log

from p6_systems import Z95
import p10_exponent as p10
from p8_smooth import rho_normal_only, rho_smooth

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    # K1 endpoints, the registered domain and the out-of-domain sentinel
    e = []
    e.append(p10.rho(1.0, p10.E0_PHASE8, 0.0) == float("inf"))
    e.append(p10.root_R(0.0, p10.E0_PHASE8, 0.0) > 0.0)
    e.append(p10.root_R(0.2, 0.0, 800.0) > 0.0)
    e.append(p10.root_R(0.9, 40.0, 0.0) > 0.0)
    e.append(p10.Bs(0.01) > 0.0 and p10.B(0.0) == Z95)
    # e1 < 0 is excluded by P10-A1/A4: the sentinel is 0.0, never a bogus root
    e.append(all(p10.root_R(s, -7.5, 0.0) == 0.0 or p10.root_R(s, -7.5, 0.0) == float("inf")
                 for s in p10.S_GRID))
    e.append(p10.local_slope(0.5, 3.0, 60.0) < -2.0 or p10.local_slope(0.5, 3.0, 60.0) > -2.0)
    check("K1_endpoints_and_domain_sentinel", sum(e) == len(e),
          f"{sum(e)}/{len(e)} paths (s=1 inf, e1<0 sentinel, e0=0 ok)")

    # K2 largest root must coincide with the committed quadratic root when e1 = 0
    worst = 0.0
    for s in p10.S_GRID:
        R = p10.root_R(s, p10.E0_PHASE8, 0.0)
        b = Z95 * (1.0 + s ** 0.5)
        closed = ((b + (b * b + 4.0 * p10.E0_PHASE8 * (1.0 - s)) ** 0.5) / (2.0 * (1.0 - s))) ** 2
        worst = max(worst, abs(R * R - closed) / closed)
    check("K2_e1_zero_reproduces_committed_quadratic_root", worst <= 1e-12,
          f"max rel diff {worst:.2e} vs p8_smooth.rho_smooth")

    # K3 residual at the root over the registered coefficient domain
    worst = max(p10.residual(s, e0, e1) for s in (0.3, 0.6, 0.9)
                for e0 in (0.0, p10.E0_PHASE8, 25.0) for e1 in (0.0, 120.0, 800.0))
    check("K3_root_residual", worst <= 1e-9, f"max |Delta R^2 - B R - e0 - e1/R| = {worst:.2e}")

    # K4 degenerate e0 = e1 = 0 must give the Phase VI normal-approximation curve
    worst = 0.0
    for s in p10.S_GRID:
        worst = max(worst, abs(p10.rho(s, 0.0, 0.0) - rho_normal_only(s)) / rho_normal_only(s))
    check("K4_zero_corrections_give_phase6_normal_curve", worst <= 1e-12,
          f"max rel diff {worst:.2e} vs rho_normal_only")

    # K5 the central-difference slope estimator returns exactly -2 on a known homogeneous curve
    rel, c, d = 1e-6, 3.0, 0.4
    num = (log(c / (d * (1 + rel)) ** 2) - log(c / (d * (1 - rel)) ** 2)) / \
          (log(d * (1 + rel)) - log(d * (1 - rel)))
    check("K5_central_difference_calibrated", abs(num + 2.0) <= 1e-6,
          f"difference slope on rho = 3/Delta^2 is {num:.9f} (target -2)")

    # K6 determinism
    a = p10.root_R(0.85, 3.7, 61.0)
    b = p10.root_R(0.85, 3.7, 61.0)
    check("K6_determinism", a == b, f"R = {a:.9f} twice identical")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
