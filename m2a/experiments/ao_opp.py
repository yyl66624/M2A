"""Action Opportunity instrument: the measure algebra of AO protocol §2, nothing more.

Kept separate from `ao_preflight_gate.py` so the gate can be read as an instrument check. No
scientific criterion lives in either file (R2): this module can tell you whether `I(o)` and `Z(o)`
were computed correctly, and says nothing about whether an effect exists.

Reading of §4-P2 recorded here because the protocol's wording is ambiguous: "NONE 与任何 a ∈ A 不同
时为正" cannot mean probabilities, since two outcomes of one trial may both carry positive probability
- a measure with mu(NONE) = 0.2 and mu(a) = 0.3 would be called illegal. It is implemented at the
event level: no node of the grid may belong to NONE and to a category at once. The pre-registration
has to fix this before any reading is taken.
"""
from __future__ import annotations

import math

NONE = "NONE"
TOLM = 1e-12              # the protocol's own measure-axiom tolerance (AO §4 P1)
THETAS = (0.1, 0.25, 0.5, 0.75, 0.9)
LAM = 1.0                 # exponential tilt of the latent density; fixed here, not fitted


def nodes(n, h=1.0, offset=0.0):
    """n+1 nodes on [0, h], shifted by `offset` grid steps. Deterministic - no RNG (R1)."""
    step = h / n
    return [i * step + offset * step for i in range(n + 1)]


def weights(xs):
    """Unnormalised density exp(-LAM x) on the nodes; normalisation happens in `mass`."""
    return [math.exp(-LAM * x) for x in xs]


def mass(xs, ws, bounds):
    """Label every node once, then aggregate weight per label.

    Returns (mu, clashes): `mu` maps label -> probability, `clashes` counts nodes carrying more than
    one label. A node in no interval is NONE by the event definition, not by subtraction - that is
    the whole point of the new analysis unit (§2), and the reason Z is never 1 - sum(p_a)."""
    total = math.fsum(ws)
    mu, clashes = {}, 0
    for x, w in zip(xs, ws):
        owners = [name for name, (lo, hi) in bounds.items() if lo <= x < hi]
        label = owners[0] if len(owners) == 1 else (NONE if not owners else owners[0])
        if len(owners) > 1:
            clashes += 1
        mu[label] = mu.get(label, 0.0) + w / total
    mu.setdefault(NONE, 0.0)
    return mu, clashes


class Model:
    """One action opportunity: a subject, a window, and the categories available in it."""

    def __init__(self, name, bounds, n=2001, h=1.0, offset=0.0):
        self.name, self.bounds, self.n, self.h, self.offset = name, bounds, n, h, offset

    def grid(self, n=None, h=None, offset=None):
        xs = nodes(self.n if n is None else n, self.h if h is None else h,
                   self.offset if offset is None else offset)
        return xs, weights(xs)

    def mu(self, theta, **kw):
        bounds = self.moving(theta)
        xs, ws = self.grid(**kw)
        mu, _ = mass(xs, ws, bounds)
        return mu

    def assign(self, theta, **kw):
        xs, ws = self.grid(**kw)
        _, clashes = mass(xs, ws, self.moving(theta))
        return clashes

    def moving(self, theta):
        """Bounds with the gate threshold folded in (the one-parameter family the knobs move)."""
        out = {}
        for k, (lo, hi) in self.bounds.items():
            out[k] = (max(lo, theta), hi) if k.startswith("a") else (lo, hi)
        return out


# |A| = 1 models: the degenerate case where the old and new units must agree exactly.
ONE_CATEGORY = {
    "gate_upper": Model("gate_upper", {"a1": (0.0, 1.0)}),
    "gate_upper_half": Model("gate_upper_half", {"a1": (0.0, 0.5)}),
}
MULTI = {
    "two_windows": Model("two_windows", {"a1": (0.0, 0.3), "a2": (0.6, 1.0)}),
    "adjacent": Model("adjacent", {"a1": (0.0, 0.4), "a2": (0.4, 0.8)}),
}


def degenerate_models():
    return dict(ONE_CATEGORY)


def fixtures():
    """Measure vectors the checks read: model-generated plus exact hand-built ones."""
    out = {}
    for name, m in list(ONE_CATEGORY.items()) + list(MULTI.items()):
        for th in THETAS:
            mu, _ = mass(*m.grid(), m.moving(th))
            out[f"{name}@{th}"] = mu
    out["certain_action"] = {"a1": 0.5, "a2": 0.5, NONE: 0.0}
    out["certain_none"] = {"a1": 0.0, "a2": 0.0, NONE: 1.0}
    out["half_none"] = {"a1": 0.4, "a2": 0.2, NONE: 0.4}
    out["single"] = {"a1": 0.3, NONE: 0.7}
    return out


def measure_defect(mu):
    return abs(math.fsum(mu.values()) - 1.0)


def issuance(mu):
    """I(o) = max over the available categories. Written as an explicit loop: the sorted-max
    reimplementation in `issuance_alt` is the second code path P6 compares against."""
    best = 0.0
    for k in mu:
        if k == NONE:
            continue
        if mu[k] > best:
            best = mu[k]
    return best


def issuance_alt(mu):
    vals = sorted((mu[k] for k in mu if k != NONE), reverse=True)
    return vals[0] if vals else 0.0


def silence(mu):
    """Z(o) = mu(NONE), read off the measure. Never 1 - sum(p_a): that is the collapse §1-§2 exists
    to remove, and using it here would let the instrument certify its own failure (R8)."""
    return mu.get(NONE, 0.0)


def scan_none_mass(model, theta, **kw):
    """Independent route to Z: walk the nodes and accumulate the weight of every node that lies in
    no category interval. Shares no code with `silence`, which reads an aggregated dict (R8)."""
    xs, ws = model.grid(**kw)
    bounds = model.moving(theta)
    total = math.fsum(ws)
    acc = 0.0
    for x, w in zip(xs, ws):
        if not any(lo <= x < hi for lo, hi in bounds.values()):
            acc += w
    return acc / total


def legacy_issuance(model, theta):
    """The old unit, computed the old way: 1 - P(T(X) <= theta), where the first-firing time is found
    by scanning upward and the surviving mass is accumulated from that index. Same registered
    half-open convention as the new unit - mixing `>=` and `>` between the two paths would just buy
    a one-node artefact and then 'tolerate' it (R9)."""
    xs, ws = model.grid()
    total = math.fsum(ws)
    bounds = model.moving(theta)
    lo_all = min(lo for lo, _ in bounds.values())
    hi_all = max(hi for _, hi in bounds.values())
    acc, firing = 0.0, False
    for x, w in zip(xs, ws):
        if not firing and x >= lo_all and x < hi_all:
            firing = True
        if firing and lo_all <= x < hi_all:
            acc += w
        if firing and x >= hi_all:
            break
    return acc / total


def knob_displacements(n_small=2001, n_big=4001):
    """Displacement of the reading under three **grid-only** knobs (R13/R18's third knob).

    The window W itself is deliberately not a knob here. Extending `h` changes what is measured -
    the density renormalises over a longer support, so `I` moves by ~1e-1 - and using that as an
    error bar for a reduction identity would buy a tolerance four orders of magnitude larger than
    the quantity it is supposed to bound. That conflation is the R9 class of trap (carrying a
    coefficient into a scale that already contains it), so `window_sensitivity` is reported
    separately and excluded from the derived tolerance by construction."""
    th = 0.5
    base = issuance(ONE_CATEGORY["gate_upper"].mu(th, n=n_small, offset=0.0))
    out = {
        "density": abs(issuance(ONE_CATEGORY["gate_upper"].mu(th, n=n_big)) - base),
        "half_shift": abs(issuance(ONE_CATEGORY["gate_upper"].mu(th, n=n_small, offset=0.5)) - base),
        "full_shift": abs(issuance(ONE_CATEGORY["gate_upper"].mu(th, n=n_small, offset=1.0)) - base),
    }
    wide = issuance(ONE_CATEGORY["gate_upper"].mu(th, n=n_small, h=2.0))
    out["window_sensitivity"] = abs(wide - base)
    return out


def exclusivity_report():
    """Nodes that carry more than one label. This is the event-level reading of §4-P2 (see module
    docstring): probabilities of NONE and a category may both be positive, so the check belongs at
    the assignment level or it would reject every ordinary measure."""
    out = {}
    for name, m in list(ONE_CATEGORY.items()) + list(MULTI.items()):
        out[name] = max(m.assign(th) for th in THETAS)
    return out


def independent_path_gap(fixs, models):
    worst = 0.0
    for mu in fixs.values():
        worst = max(worst, abs(issuance(mu) - issuance_alt(mu)))
    for name, m in models.items():
        for th in THETAS:
            worst = max(worst, abs(silence(m.mu(th)) - scan_none_mass(m, th)))
    return worst


def silence_by_complement(mu):
    """The forbidden old-unit reading, kept deliberately: the probe needs both definitions."""
    return 1.0 - sum(v for k, v in mu.items() if k != NONE)


def definition_probe():
    """Where do 'Z is its own event' and 'Z is the complement' actually differ?

    On every *normalised* measure they coincide - `1 - sum(p_a)` is exactly `mu(NONE)` - so a check
    that only reads normalised measures cannot tell the two apart, and passing it proves nothing
    (this is what made the first version of this gate survive mutating `silence` into the forbidden
    definition). They diverge only when mass is unaccounted for: a measure whose categories and NONE
    do not exhaust 1. The event definition reports the NONE slot; the complement definition silently
    absorbs the gap, which is precisely the collapse §2 exists to remove.
    """
    normalised = {"a1": 0.5, "a2": 0.2, NONE: 0.3}
    unaccounted = {"a1": 0.5, "a2": 0.0, NONE: 0.4}      # fsum = 0.9, 0.1 unmodelled
    return {
        "normalised": (silence(normalised), silence_by_complement(normalised)),
        "unaccounted": (silence(unaccounted), silence_by_complement(unaccounted)),
    }


def model_separability():
    """Separability measured over a theta sweep rather than asserted from a category count."""
    out = {}
    for name, m in list(ONE_CATEGORY.items()) + list(MULTI.items()):
        resid = max(abs(issuance(m.mu(th)) + silence(m.mu(th)) - 1.0) for th in THETAS)
        out[name] = resid
    return out
