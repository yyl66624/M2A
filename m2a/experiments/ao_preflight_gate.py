"""Action Opportunity pre-flight gate: instruments only (R2), no scientific criterion.

Owner decision 2026-10-18 item 1 authorises the *model definition and the gated pre-checks*, and
explicitly does not authorise running the experiment. This file is that pre-check: `report/
AO_MEASUREMENT_PROTOCOL_v1.md` §4 lists P1-P6 as prose, and until now nothing implemented them, so
the protocol could not be executed even in principle - the same "artifact exists, check was never
run" failure as X-68.

What is verified is the measure algebra of §2, nothing else. Slope directions, effect sizes and any
question of whether an effect exists are outside this file by construction (R2).

The protocol's own tolerance is used where it states one (P1: 1e-12). The reduction tolerance is not
chosen: it is derived from the three discretisation knobs P5 measures (interval, density, offset),
which is R5 - resolution fixed by derivation before any reading is taken.

`experiments/ao_opp.py` holds the instrument; this file only checks it.
"""
from __future__ import annotations

import itertools

import ao_opp as ao

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


def main() -> int:
    fixtures = ao.fixtures()

    # P1 measure axiom: sum over A union {NONE} is 1. Reported with the smallest difference the
    # check can actually distinguish (R7), because a pass at a loose tolerance proves nothing.
    worst, where, seen = 0.0, None, 0
    for name, mu in fixtures.items():
        seen += 1
        d = ao.measure_defect(mu)
        if d > worst:
            worst, where = d, name
    ratio = "undefined (observed 0)" if worst == 0 else format(ao.TOLM / worst, ",.1f")
    check("P1_measure_axiom", worst <= ao.TOLM,
          f"{seen} fixtures, worst |sum-1| = {worst:.3e}, tol {ao.TOLM:.0e}, "
          f"R7 tol/observed = {ratio}")

    # P2 category exclusivity, at the event level (a node may not carry two labels). Read as
    # probabilities the protocol's wording would reject every ordinary measure; see ao_opp docstring.
    clashes = ao.exclusivity_report()
    check("P2_categories_exclusive", all(v == 0 for v in clashes.values()),
          "max multi-labelled nodes per model: "
          + ", ".join(f"{k}={v}" for k, v in sorted(clashes.items())))

    # P5 before P3: the reduction tolerance must come from the grid knobs, not from the size of the
    # disagreement it is about to accept (R5). Moving the window W itself is measured but excluded -
    # it changes the measurand, and folding it in would buy a tolerance ~1e-1 for a 1e-15 identity.
    disp = ao.knob_displacements()
    grid_knobs = ("density", "half_shift", "full_shift")
    tol_red = sum(disp[k] for k in grid_knobs)
    check("P5_three_grid_knobs", all(disp[k] >= 0 for k in grid_knobs) and tol_red > 0,
          "density {:.3e} + half_shift {:.3e} + full_shift {:.3e} => reduction tol {:.3e} "
          "(derived, R5/R13). Window W moved separately: {:.3e}, excluded by construction"
          .format(disp["density"], disp["half_shift"], disp["full_shift"], tol_red,
                  disp["window_sensitivity"]))

    # P3 degenerate reduction: with |A| = 1 the new protocol must reproduce the old quantity,
    # computed by an independent legacy route. Anchored, not asserted in prose.
    worst_r, where_r = 0.0, None
    for name, model in ao.degenerate_models().items():
        for theta in ao.THETAS:
            d = abs(ao.issuance(model.mu(theta)) - ao.legacy_issuance(model, theta))
            if d > worst_r:
                worst_r, where_r = d, (name, theta)
    # R14: a disagreement this small is float accumulation, not agreement "to zero". Saying so keeps
    # the ratio honest instead of letting 1e-15 be read as an exact reduction - and states plainly
    # that a tolerance of ~8e-4 cannot resolve a convention error smaller than that.
    rounding = worst_r <= 1e-14
    check("P3_reduces_to_legacy_at_|A|1", worst_r <= tol_red,
          f"worst |I_new - legacy| = {worst_r:.3e} at {where_r}"
          + (" - float accumulation, not exact equality" if rounding else "")
          + f"; tol/observed = {tol_red / max(worst_r, 2.3e-16):,.3g} (R7). The derived grid "
            f"tolerance is {tol_red:.1e}, so this check cannot resolve a half-node convention error "
            f"smaller than that scale")

    # P4 label permutation invariance: I and Z are functionals of the measure, not of the names.
    # Only the category keys are permuted - permuting NONE as well would move its mass into a
    # category and then re-add it, i.e. the test would check a different measure (found on the
    # pre-run code check, not by running).
    bad = []
    for name, mu in fixtures.items():
        cats = sorted(k for k in mu if k != ao.NONE)
        if len(cats) < 2:
            continue
        base = (ao.issuance(mu), ao.silence(mu))
        for perm in itertools.permutations(cats):
            shuffled = dict(zip(perm, [mu[k] for k in cats]))
            shuffled[ao.NONE] = mu[ao.NONE]
            if (ao.issuance(shuffled), ao.silence(shuffled)) != base:
                bad.append(name)
                break
    n_perm = sum(1 for mu in fixtures.values() if len([k for k in mu if k != ao.NONE]) >= 2)
    check("P4_permutation_invariant", not bad,
          f"{n_perm} fixtures with |A| >= 2 permuted, moved: " + (", ".join(sorted(set(bad))) or "none"))

    # P6 independent instruments: I and Z each recomputed by a second code path that shares no
    # function body with the first (R8), and the identity construction must be refused, not passed.
    # The two paths accumulate in different orders (per-node division then sum, versus sum-then-
    # divide), so demanding bit-equality was my error, not an instrument fault: it would have made
    # the check unpassable by construction. The criterion is the registered measure tolerance, and
    # the observed gap is reported against the grid scale it would have to reach to matter (R7).
    models = dict(ao.ONE_CATEGORY, **ao.MULTI)
    two = ao.independent_path_gap(fixtures, models)
    check("P6a_second_code_paths", two <= ao.TOLM,
          f"max gap between the two implementations over {len(fixtures)} measures and "
          f"{len(models)} models x {len(ao.THETAS)} thetas = {two:.3e}; tol {ao.TOLM:.0e}, "
          f"R7 tol/observed = {'undefined (observed 0)' if two == 0 else format(ao.TOLM / two, ',.1f')}"
          f"; grid scale is {tol_red:.1e}, i.e. the gap is {tol_red / max(two, 1e-300):.0e}x smaller "
          f"than what this instrument resolves (R8)")
    resid = ao.model_separability()
    pinned = sorted(k for k, v in resid.items() if v <= ao.TOLM)
    expected = sorted(ao.ONE_CATEGORY)
    check("P6b_identity_construction_refused", pinned == expected,
          f"models pinned to I+Z=1 (hence NOT_DISTINGUISHABLE, not a pass): {pinned}; "
          f"separable: {sorted(k for k in resid if k not in pinned)} "
          f"(max residual on the line: {max(resid[k] for k in expected):.1e})")

    # P6c: does this instrument actually separate the two definitions of Z, or does it only
    # certify an identity? Adding this check turned the gate from decoration into a test: with
    # `silence` mutated into the forbidden complement reading, P6c is the check that fails.
    probe = ao.definition_probe()
    gap_unacc = abs(probe["unaccounted"][0] - probe["unaccounted"][1])
    gap_norm = abs(probe["normalised"][0] - probe["normalised"][1])
    check("P6c_definitions_are_distinguishable", gap_unacc >= 0.05,
          f"unaccounted-mass measure: event definition {probe['unaccounted'][0]:.3f} vs complement "
          f"{probe['unaccounted'][1]:.3f} -> gap {gap_unacc:.3f}; normalised measure gap "
          f"{gap_norm:.1e} (the two definitions COINCIDE on every normalised measure, so agreement "
          f"there is not evidence - R7/R8)")

    print(f"{sum(1 for _, o, _ in CHECKS if o)}/{len(CHECKS)} checks passed")
    return 0 if all(ok for _, ok, _ in CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
