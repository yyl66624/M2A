"""Phase XXI instrument: the Phase XX filter extended to interval-weighted memory.

A/S/V and both tolerances are imported from p20_filter and never redefined here, so the
cross-round comparison is by construction and not by reimplementation.
"""
from __future__ import annotations

import math

import p20_filter as p20

MECHS5 = p20.MECHS + ("M4", "M5")
N_LIMIT = 10 ** 6


def reading(mech: str, n: int, c: float, scale_tau: bool) -> float:
    if mech in p20.MECHS:
        return p20.reading(mech, n, c, scale_tau)
    dt = c * p20.T / n
    if mech == "M4":
        return p20.ETA * dt * n                       # interval-weighted writes, no forgetting
    tau = c * p20.TAU if scale_tau else p20.TAU
    lam = math.exp(-dt / tau)
    if lam >= 1.0:
        return p20.ETA * dt * n
    return p20.ETA * dt * (1.0 - lam ** n) / (1.0 - lam)   # closed geometric sum; loop() is the other path


def loop(mech: str, n: int, c: float, scale_tau: bool) -> float:
    if mech in p20.MECHS:
        return p20.loop(mech, n, c, scale_tau)
    dt = c * p20.T / n
    if mech == "M4":
        acc = 0.0
        for _ in range(n):
            acc = acc + p20.ETA * dt
        return acc
    tau = c * p20.TAU if scale_tau else p20.TAU
    lam = math.exp(-dt / tau)
    acc = 0.0
    for _ in range(n):
        acc = lam * acc + p20.ETA * dt
    return acc


def spread(vals: list[float]) -> float:
    return max(vals) - min(vals)


def a_spread(mech: str) -> float:
    return spread([reading(mech, n, 1.0, False) for n in p20.NS])


def s_spread(mech: str) -> float:
    return max(spread([reading(mech, n, c, False) for c in p20.CS]) for n in p20.NS)


def v_spread(mech: str) -> float:
    return max(spread([reading(mech, n, c, True) for c in p20.CS]) for n in p20.NS)


def integral_limit() -> float:
    """Analytic value of eta * integral_0^T exp(-(T-t)/tau) dt."""
    return p20.ETA * p20.TAU * (1.0 - math.exp(-p20.T / p20.TAU))


def bound_limit() -> float:
    """Registered P21-A1: monotone-Riemann bound eta * dt_limit * (1 - exp(-T/tau))."""
    return p20.ETA * (p20.T / N_LIMIT) * (1.0 - math.exp(-p20.T / p20.TAU))


def m5_deviation_series() -> list[float]:
    """|V(n) - integral| over the registered n grid, used by the monotone-decreasing clause."""
    lim = integral_limit()
    return [abs(reading("M5", n, 1.0, False) - lim) for n in p20.NS]


def classify5() -> dict:
    out = {}
    for m in MECHS5:
        a, s, v = a_spread(m), s_spread(m), v_spread(m)
        out[m] = {"A_spread": a, "S_spread": s, "V_spread": v,
                  "A_pass": a <= p20.TOL, "S_pass": s >= p20.SENS, "V_pass": v <= p20.TOL}
    return out
