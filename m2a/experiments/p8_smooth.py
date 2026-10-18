"""Phase VIII: the smooth (Edgeworth-corrected) threshold law for the Poisson counting system.

Exact side reuses Phase VI's instrument unchanged; the smooth side is closed form. No sampling.
"""
from __future__ import annotations

from math import sqrt

from p6_systems import Z95, s2_critical_rho

C1 = (Z95 ** 2 - 1.0) / 3.0          # skewness (Edgeworth first-order) quantile correction


def rho_smooth(s: float, with_c1: bool = True) -> float:
    """Positive root of  Delta*r - z(1+sqrt(s)) sqrt(r) - 2*c1 = 0,  Delta = 1 - s."""
    delta = 1.0 - s
    if delta <= 0.0:
        return float("inf")
    b = Z95 * (1.0 + sqrt(s))
    c = 2.0 * C1 if with_c1 else 0.0
    root = (b + sqrt(b * b + 4.0 * c * delta)) / (2.0 * delta)
    return root * root


def rho_exact(s: float) -> float:
    return s2_critical_rho(s, 1.0)["rho"]


def rho_normal_only(s: float) -> float:
    """The Phase VI closed form: z^2 (1+sqrt(s))^2 / Delta^2  (i.e. c1 = 0)."""
    return Z95 ** 2 * (1.0 + sqrt(s)) ** 2 / (1.0 - s) ** 2


def poisson_quantile(lam: float, p: float) -> int:
    """Smallest integer x with P(N <= x) >= p for N ~ Pois(lam), by term recurrence (no scipy)."""
    from math import exp
    from p6_systems import poisson_cdf_grid
    if lam <= 0.0:
        return 0
    hi = int(lam + 12.0 * sqrt(max(lam, 1.0)) + 40.0)
    cdf = poisson_cdf_grid(lam, hi)
    idx = int(next(i for i, v in enumerate(cdf) if v >= p))
    return idx
