"""Phase XI gate: instrument only (section 5 of PHASE11_PREREGISTRATION.md).

Per P10-O3 every agreement check also reports the smallest difference it could have distinguished,
so a passing check states whether it had the power to fail.
"""
from __future__ import annotations

import sys

import numpy as np

import p9_aggregation as p9
import p11_softband as p11

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


def main() -> int:
    # Y1 endpoints, the empty-band path and the zero-gap path
    e = [p11.L_tau("product", 2, 0.0) == 0.0,
         p11.L_tau("nilpotent", 2, 0.3) == 0.0,
         abs(p11.L_tau("stepped", 2, 0.3) - 0.25) < 1e-12,
         p11.predicted("logistic", 2, 1.0) == float("inf"),
         p11.beta_star_band("logistic", 2, 1.0)["measurable"] is False,
         np.isfinite(p11.beta_star_band("logistic", 2, 0.0)["beta"])]
    check("Y1_endpoints_and_zero_gap", all(e), f"{sum(e)}/{len(e)} paths ok")

    # Y2 surjective aggregators: enumerated reachable sup must equal the band edge
    worst = 0.0
    for name in p11.SURJECTIVE:
        for m in (2, 3):
            for tau in (0.3, 0.55, 0.7):
                worst = max(worst, abs(p11.L_tau(name, m, tau) - tau))
    half_step = 0.5 / (p11.N_AXIS - 1)
    check("Y2_surjective_L_equals_tau", worst <= half_step + 1e-12,
          f"max |L_tau - tau| = {worst:.4f}; smallest distinguishable difference = "
          f"{abs(half_step - worst):.4f} (grid half-step {half_step:.4f})")

    # Y3 regression anchor: the band instrument must reproduce the committed Phase IX beta*
    worst = 0.0
    for kind in ("logistic", "probit", "gumbel"):
        for k in (2, 3):
            for s in (0.3, 0.5, 0.7):
                got = p11.beta_star_band(kind, k, s)["beta"]
                ref = p9.critical_beta_agg(kind, k, 2, s, "product")["beta"]
                worst = max(worst, abs(got - ref) / ref)
    check("Y3_band_instrument_reproduces_committed_phase9", worst <= 1e-6,
          f"max rel diff = {worst:.2e} over 18 cells; smallest distinguishable difference = "
          f"{1e-6 - worst:.2e}")

    # Y4 fixed-point residual: rho0 * P(rho0) must equal alpha
    worst = 0.0
    for kind in ("logistic", "probit", "gumbel"):
        for los in ((0.5,), (0.3, 0.55, 0.7)):
            beta = p11.predicted(kind, len(los), max(los)) * 1.05
            P, rho0, _, _ = p11.fixed_point_P(kind, beta, list(los))
            worst = max(worst, abs(rho0 * P - p11.ALPHA))
    check("Y4_fixed_point_residual", worst <= 1e-9,
          f"max |rho0*P - alpha| = {worst:.2e}; smallest distinguishable difference = {1e-9 - worst:.2e}")

    # Y5 determinism of the enumeration and of the search
    a = p11.beta_star_band("probit", 3, 0.55)["beta"]
    b = p11.beta_star_band("probit", 3, 0.55)["beta"]
    check("Y5_determinism", a == b, f"beta* = {a:.6f} twice identical")

    # Y6 the random control is reproducible on the registered pool
    beta = p11.beta_star_band("logistic", 3, 0.5)["beta"]
    h1 = p11.random_control("logistic", 1.05 * beta, [0.5] * 3, p11.SEEDS_XI[:3], 2000)
    h2 = p11.random_control("logistic", 1.05 * beta, [0.5] * 3, p11.SEEDS_XI[:3], 2000)
    check("Y6_random_control_reproducible", h1 == h2, f"hits {h1} == {h2} on 3 seeds")

    n_ok = sum(1 for _, o, _ in CHECKS if o)
    print(f"\n{n_ok}/{len(CHECKS)} checks passed")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
