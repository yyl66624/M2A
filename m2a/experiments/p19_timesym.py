"""Phase XIX instrument: three memory mechanisms under thinning (A) and time rescaling (B).

Deterministic by construction -- no RNG is imported anywhere in this module. See
PHASE19_PREREGISTRATION.md for the frozen criteria, tolerances and exit table.
"""
from __future__ import annotations

import math

ETA = 0.1
TAU = 1.0
T = 10.0
NS = (1, 2, 5, 10, 20)
CS = (0.5, 1.0, 2.0)
TOL = 1e-12          # registered absolute tolerance, fixed before the run
V0 = 1.0


def recurrence(n: int, c: float = 1.0) -> dict:
    """Terminal state of each mechanism for a schedule of n pairings over duration T, scaled by c."""
    dt = c * T / n                      # interval in scaled time
    lam = math.exp(-dt / (c * TAU))     # decay per interval; tau scales with the axis (covariant)
    m1 = n * ETA                                     # trial count only, time plays no role
    m2 = V0 * math.exp(-(c * T) / TAU)               # pure time trace, events never write
    m3 = ETA * (1.0 - lam ** n) / (1.0 - lam) if lam < 1.0 else n * ETA
    return {"dt": dt, "lambda": lam, "M1": m1, "M2": m2, "M3": m3,
            "closed_M1": n * ETA, "closed_M2": V0 * math.exp(-(c * T) / TAU),
            "closed_M3": m3}


def thinning_at_fixed_T(c: float = 1.0) -> list[dict]:
    """Operation A: total scaled duration held at c*T while n varies. Returns per-n readings."""
    out = []
    for n in NS:
        r = recurrence(n, c)
        out.append({"n": n, "c": c, **r})
    return out


def rescale_at_fixed_n(n: int) -> list[dict]:
    """Operation B: n held fixed while the whole time axis is multiplied by c."""
    return [{"n": n, "c": c, **recurrence(n, c)} for c in CS]


def passes_A(rows: list[dict], mech: str) -> tuple[bool, float]:
    """A is passed when the terminal state is unchanged across n at fixed total duration."""
    vals = [r[mech] for r in rows]
    spread = max(vals) - min(vals)
    return spread <= TOL, spread


def passes_B(rows: list[dict], mech: str) -> tuple[bool, float]:
    """B is passed when the reading at scaled axis c equals the unscaled reading at the
    correspondingly scaled clock -- here that means invariance of V to c for a mechanism whose
    own time constant is scaled along with the axis (the covariance requirement of R15)."""
    vals = [r[mech] for r in rows]
    spread = max(vals) - min(vals)
    return spread <= TOL, spread


def patterns() -> dict:
    """(passA, passB) per mechanism class, exactly as the criteria define them."""
    a_rows = thinning_at_fixed_T()
    out = {}
    for mech in ("M1", "M2", "M3"):
        ok_a, spread_a = passes_A(a_rows, mech)
        out[mech] = {"pass_A": ok_a, "spread_A": spread_a,
                     "pass_B": {}, "spread_B": {}}
        for n in NS:
            ok_b, spread_b = passes_B(rescale_at_fixed_n(n), mech)
            out[mech]["pass_B"][n] = ok_b
            out[mech]["spread_B"][n] = spread_b
    return out
