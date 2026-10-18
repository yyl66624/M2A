"""Phase XX instrument: the B-07 filter restated as three separate conditions (A, S, V).

Deterministic; imports no RNG. See PHASE20_PREREGISTRATION.md for the frozen definitions.
"""
from __future__ import annotations

import math

ETA = 0.1
TAU = 1.0
T = 10.0
V0 = 1.0
NS = (1, 2, 5, 10, 20)
CS = (0.5, 1.0, 2.0)
TOL = 1e-12   # registered: float-only error source, exact grid points
SENS = 1e-9   # registered: worst accumulated float error ~4.4e-15, six orders of margin
MECHS = ("M1", "M2", "M3")


def reading(mech: str, n: int, c: float, scale_tau: bool) -> float:
    """Terminal state. scale_tau=True means the mechanism's own clock is scaled with the axis."""
    tau = c * TAU if scale_tau else TAU
    if mech == "M1":
        return n * ETA                                    # no time variable at all
    if mech == "M2":
        return V0 * math.exp(-(c * T) / tau)              # pure duration
    dt = c * T / n
    lam = math.exp(-dt / tau)
    return n * ETA if lam >= 1.0 else ETA * (1.0 - lam ** n) / (1.0 - lam)


def loop(mech: str, n: int, c: float, scale_tau: bool) -> float:
    """Independent numerical path: event-by-event accumulation, never the closed form."""
    tau = c * TAU if scale_tau else TAU
    dt = c * T / n
    v = 0.0
    if mech == "M1":
        for _ in range(n):
            v = v + ETA
        return v
    if mech == "M2":
        steps = c * T / n                                  # the scaled duration is walked, not divided
        v = V0
        for _ in range(n):
            v = v * math.exp(-steps / tau)
        return v
    lam = math.exp(-dt / tau)
    for _ in range(n):
        v = lam * v + ETA
    return v


def spread(values: list[float]) -> float:
    return max(values) - min(values)


def thinning_spread(mech: str) -> float:
    """A: total duration fixed, n varies, no axis scaling."""
    return spread([reading(mech, n, 1.0, False) for n in NS])


def sensitivity_spread(mech: str) -> float:
    """S: n fixed, axis scaled, mechanism clock held fixed. Maximized over n."""
    return max(spread([reading(mech, n, c, False) for c in CS]) for n in NS)


def covariance_spread(mech: str) -> float:
    """V: n fixed, axis and mechanism clock scaled together. Maximized over n."""
    return max(spread([reading(mech, n, c, True) for c in CS]) for n in NS)


def classify() -> dict:
    out = {}
    for m in MECHS:
        a, s, v = thinning_spread(m), sensitivity_spread(m), covariance_spread(m)
        out[m] = {"A_spread": a, "S_spread": s, "V_spread": v,
                  "A_pass": a <= TOL, "S_pass": s >= SENS, "V_pass": v <= TOL}
    return out
