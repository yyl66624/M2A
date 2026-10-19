"""Give the ten instruments §42 found unmeasured at least one check with a FALSIFIABLE input.

Scope and reason. `governance/build_coverage_map.py` (§42) enumerated imported mechanism functions that
no round gate measures: 7 `never_reached` + 3 `only_self_comparison`. The disposition for those gaps
belongs to future rounds, and old gates will not be rewritten (R6). But leaving them unmeasured is not
the only option available today: this suite measures them at the governance layer, with expected values
computed INDEPENDENTLY of the module under test - a hand-typed closed form, a literal vector, a
degenerate limit, or a binomial bound - so none of these checks is the instrument comparing itself with
itself (R8). What changes is the existence of an instrument, not any round's verdict.

The list of things to cover is READ from the committed coverage map, not retyped here, and the suite
fails if the map grows a gap with no check or if a check here points at an instrument the map no longer
lists. That way §42's inventory and this instrument cannot drift apart silently.

Coverage: p5b_gate{gap_for, channels, tnorm, chain_polarity}, p10_gate{rho_smooth},
p13_gate{rho_exact, rho_smooth}, p8_gate{rho_exact}, p5d_gate{readout_d}, phase2_gate{e1_rates}.

Checks only touch instruments (R2): no effect size, no scientific criterion, no round verdict.

Two expectations were wrong in the first draft of this file and are recorded here so the correction is
visible rather than silent. (i) `gap_for` is ANTITONE in `s`, not monotone: `s` is the level the silent
side RETAINS, so a larger `s` shrinks the drive gap - the analytic law is `1 - s**n` for product/all_weak.
(ii) Comparing `rho_exact` to the c1=0 normal form "within the bisection tolerance" was a category error:
the tolerance controls how well the search converged, not where the discrete critical rho sits relative
to a continuous approximation, and that distance is legitimately ~68x the tolerance at s=0.9. What is
true - and what is checked instead - is an ORDERING bracket by two independently hand-typed closed forms.
(iii) `readout_d` is read at a single seed, while Phase V-d's registered 0.008 is a criterion on the
10-seed MEAN, so applying it to a single reading was a scale transplant (R9). The bands used here are
derived from the round's own committed per-seed dispersion instead of being borrowed.
A bisection-convergence check (window holds at the returned rho, fails one tolerance below) was
considered and deliberately NOT added: `p6_gate.py:54-55` already runs it against the same predicate,
so repeating it here would be the instrument confirming itself (R8) with no new information.
"""
from __future__ import annotations

import itertools
import json
import math
import pathlib
import sys

M = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(M / "experiments"))

from m2a_mechanisms import e1_rates, p_action          # noqa: E402
from p5_mechanisms import chain_polarity, channels, gap_for, tnorm  # noqa: E402
from p5d_confirm import ARMS_D, SEEDS_D, closed, readout_d  # noqa: E402
from p6_systems import Z95, s2_critical_rho            # noqa: E402
from p8_smooth import rho_exact, rho_normal_only, rho_smooth  # noqa: E402

ROWS_5D = json.loads((M / "experiments/phase5d_results.json").read_text(encoding="utf-8"))["rows"]

# (gate file, instrument) -> the check ids that give it a falsifiable input
COVERS = {
    ("p5b_gate.py", "tnorm"): ["U01_tnorm_known_answers", "U02_tnorm_all_ones_identity",
                              "U03_tnorm_unknown_name_raises"],
    ("p5b_gate.py", "channels"): ["U04_channels_literal_vectors", "U05_channels_unknown_pattern_raises"],
    ("p5b_gate.py", "gap_for"): ["U06_gap_for_analytic_values", "U07_gap_for_abs_polarity_law",
                                "U08_gap_for_full_channels_is_zero", "U09_gap_for_antitone_in_s"],
    ("p5b_gate.py", "chain_polarity"): ["U10_chain_polarity_known_products"],
    ("p8_gate.py", "rho_exact"): ["U13_rho_exact_moves_with_input",
                                 "U14_rho_exact_bracketed_by_two_closed_forms",
                                 "U15_rho_exact_degenerate_gap_is_infinite"],
    ("p10_gate.py", "rho_smooth"): ["U11_c1_off_reduces_to_phase_vi_curve", "U12_rho_smooth_limits_and_monotone"],
    ("p13_gate.py", "rho_exact"): ["U13_rho_exact_moves_with_input",
                                  "U14_rho_exact_bracketed_by_two_closed_forms",
                                  "U15_rho_exact_degenerate_gap_is_infinite"],
    ("p13_gate.py", "rho_smooth"): ["U11_c1_off_reduces_to_phase_vi_curve", "U12_rho_smooth_limits_and_monotone"],
    ("p5d_gate.py", "readout_d"): ["U16_readout_d_reproduces_the_committed_pool_mean",
                                  "U17_readout_d_in_unit_interval_and_differs_by_arm",
                                  "U22_readout_d_out_of_pool_seed_within_committed_sd"],
    ("phase2_gate.py", "e1_rates"): ["U18_e1_rates_within_4sd_of_closed_form",
                                    "U19_e1_rates_negative_control_no_action",
                                    "U20_e1_rates_interaction_zero_for_additive_arch"],
}

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def close(a, b, tol=1e-12):
    return abs(a - b) <= tol


# ------------------------------------------------------------------ t-norms and channel patterns
report("U01_tnorm_known_answers",
       close(tnorm("product", [0.5, 0.4]), 0.2)
       and close(tnorm("lukasiewicz", [0.5, 0.4]), 0.0)          # 0.9 - 1 < 0 -> floor at 0
       and close(tnorm("lukasiewicz", [0.9, 0.9, 0.9]), 0.7)     # 2.7 - 2
       and close(tnorm("godel", [0.5, 0.4, 0.6]), 0.4),
       "hand values for the three aggregation families")

report("U02_tnorm_all_ones_identity",
       all(close(tnorm(n, [1.0] * k), 1.0) for n in ("product", "lukasiewicz", "godel") for k in (1, 3, 7)),
       "conjunction of full channels is 1 for every family")

try:
    tnorm("hamacher", [0.5, 0.5])
    raised = False
except ValueError:
    raised = True
report("U03_tnorm_unknown_name_raises", raised, "negative control: an unregistered t-norm must not pass")

report("U04_channels_literal_vectors",
       channels(3, "hard", 0.5) == [1.0, 0.0, 0.0]
       and channels(3, "one_weak", 0.5) == [0.5, 1.0, 1.0]
       and channels(4, "all_weak", 0.25) == [0.25, 0.25, 0.25, 0.25],
       "the three silent-side configurations as literally registered in Phase V")

try:
    channels(3, "two_weak", 0.5)
    raised = False
except ValueError:
    raised = True
report("U05_channels_unknown_pattern_raises", raised, "negative control on the pattern vocabulary")

report("U06_gap_for_analytic_values",
       close(gap_for("product", 3, "all_weak", 0.5), 1.0 - 0.5 ** 3)          # 0.875
       and close(gap_for("godel", 3, "hard", 0.5), 1.0)                        # min silent = 0
       and close(gap_for("lukasiewicz", 2, "one_weak", 0.5), 0.5),             # 1 - max(0,1.5-1)
       "Delta = tnorm(all ones) - tnorm(silent config)")

report("U07_gap_for_abs_polarity_law",
       close(gap_for("product", 3, "all_weak", 0.5, -2.0),
             gap_for("product", 3, "all_weak", 0.5, 2.0))
       and close(gap_for("product", 3, "all_weak", 0.5, 2.0),
                 2.0 * gap_for("product", 3, "all_weak", 0.5)),
       "the serial factor enters through |chain_polarity| only")

report("U08_gap_for_full_channels_is_zero",
       all(close(gap_for(n, 4, "all_weak", 1.0), 0.0) for n in ("product", "lukasiewicz", "godel")),
       "degenerate control: s=1 means nothing degrades, so Delta must vanish")

sweep = [gap_for("product", 3, "all_weak", s) for s in (0.1, 0.3, 0.5, 0.7, 0.9)]
report("U09_gap_for_antitone_in_s",
       all(b < a for a, b in zip(sweep, sweep[1:]))
       and all(close(v, 1.0 - s ** 3) for v, s in zip(sweep, (0.1, 0.3, 0.5, 0.7, 0.9))),
       "s is the level the silent side RETAINS, so Delta = 1 - s**n falls as s rises: "
       + ", ".join(f"{v:.4f}" for v in sweep))

report("U10_chain_polarity_known_products",
       close(chain_polarity([1.0, 1.0]), 1.0)
       and close(chain_polarity([0.0, 1.0]), -1.0)
       and close(chain_polarity([0.5, 1.0]), 0.0)
       and close(chain_polarity([0.0, 0.0]), 1.0),          # two inversions cancel
       "prod(2o-1), including the even-inversion identity")

# ------------------------------------------------------------------ Phase VIII / X / XIII curves
report("U11_c1_off_reduces_to_phase_vi_curve",
       all(close(rho_smooth(s, with_c1=False),
                 Z95 ** 2 * (1.0 + math.sqrt(s)) ** 2 / (1.0 - s) ** 2, 1e-12)
           for s in (0.25, 0.5, 0.75, 0.9))
       and close(rho_normal_only(0.5), Z95 ** 2 * (1.0 + math.sqrt(0.5)) ** 2 / 0.25, 1e-12),
       "c1=0 must reproduce the Phase VI closed form, typed here independently")

limits = [rho_smooth(1.0), rho_smooth(1.4)]
grid = [rho_smooth(s) for s in (0.2, 0.4, 0.6, 0.8)]
report("U12_rho_smooth_limits_and_monotone",
       all(math.isinf(v) for v in limits) and all(b > a for a, b in zip(grid, grid[1:])),
       "Delta<=0 gives inf; the curve is strictly increasing on 0<s<1")

r_lo, r_hi = rho_exact(0.6), rho_exact(0.75)
report("U13_rho_exact_moves_with_input",
       math.isfinite(r_lo) and math.isfinite(r_hi) and r_lo != r_hi and r_hi > r_lo,
       f"rho_exact(0.6)={r_lo:.6f} vs rho_exact(0.75)={r_hi:.6f} - the falsifiable input J5 lacked")

bracket, margins = [], []
for s in (0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9):
    lower, upper, got = rho_normal_only(s), rho_smooth(s), rho_exact(s)
    bracket.append(lower < got < upper)
    margins.append((min(got - lower, upper - got) / min(lower, upper), s))
tightest = min(margins)
report("U14_rho_exact_bracketed_by_two_closed_forms",
       all(bracket),
       "the discrete Poisson critical rho must exceed the c1=0 normal form (an integer threshold costs "
       "extra) and stay below the Edgeworth-corrected smooth curve; held at all 7 points, tightest "
       "relative margin %.4f at s=%.2f (R7: the bracket detects a mis-placed curve only that finely)"
       % (tightest[0], tightest[1]))

report("U15_rho_exact_degenerate_gap_is_infinite",
       math.isinf(rho_exact(1.0)) and s2_critical_rho(1.0, 1.0)["reason"] == "zero gap",
       "zero drive gap has no critical rho (also proves the reason field is live)")

# ------------------------------------------------------------------ readouts and the generator
q_cell, arm_cell = 0.8, "confirm_annealed"
pool_mean = sum(readout_d(q_cell, sd, arm_cell) for sd in SEEDS_D) / len(SEEDS_D)
drift = abs(pool_mean - ROWS_5D[f"{arm_cell}|{q_cell}"]["mc_mean"])
report("U16_readout_d_reproduces_the_committed_pool_mean", drift <= 1e-12,
       "mean over the committed seed pool vs phase5d_results.json: |diff| = %.1e on a reading of "
       "%.6f (R7: smallest relative drift it can see %.1e)" % (drift, pool_mean, 1e-12 / max(pool_mean, 1e-9)))

resid, agrees = [], []
FRESH = (200, 201)
disjoint = not set(FRESH) & set(SEEDS_D)               # the draw must really be out-of-sample
for arm in ARMS_D:
    for q in (0.5, 0.8):
        row = ROWS_5D[f"{arm}|{q}"]
        agrees.append(close(closed(q), row["closed"], 1e-12))
        for seed in FRESH:                             # outside the registered pool 100-109
            resid.append(abs(readout_d(q, seed, arm) - row["closed"]) / (4.0 * row["mc_sd"]))
worst = max(resid)
report("U22_readout_d_out_of_pool_seed_within_committed_sd",
       worst <= 1.0 and all(agrees) and disjoint,
       "a fresh draw must fall inside 4 sigma of the committed per-seed dispersion (the 0.008 registered "
       "for the pool MEAN would have been the wrong scale here): worst %.2f of the band over %d cells, "
       "closed form matches the committed field, seeds %s disjoint from pool %s - fires only above 4 "
       "sigma and is blind below it" % (worst, len(resid), FRESH, (SEEDS_D[0], SEEDS_D[-1])))

vals = {arm: readout_d(0.8, 7, arm) for arm in ARMS_D}
report("U17_readout_d_in_unit_interval_and_differs_by_arm",
       all(0.0 <= v <= 1.0 for v in vals.values()) and len({round(v, 12) for v in vals.values()}) == len(vals),
       " ".join(f"{a}={v:.6f}" for a, v in vals.items()))

SD_MULT = 4.0
n_cells = 4000
rates = e1_rates("and", n_cells, 7)
dev = []
for x1, x2 in itertools.product([0, 1], repeat=2):
    p = p_action("and", x1, x2)
    sd = math.sqrt(max(p * (1.0 - p), 1e-12) / n_cells)
    dev.append(abs(rates[(x1, x2)] - p) / (SD_MULT * sd))
report("U18_e1_rates_within_4sd_of_closed_form",
       max(dev) <= 1.0,
       "worst cell deviation in 4-sigma units: %.2f (n=%d per cell)" % (max(dev), n_cells))

none_rates = e1_rates("none", 500, 11)
report("U19_e1_rates_negative_control_no_action",
       all(none_rates[c] == 0.0 for c in itertools.product([0, 1], repeat=2)),
       "the no-mechanism architecture must emit no action at all")

single = e1_rates("single", n_cells, 13)
sd_single = math.sqrt(0.25 / n_cells) * SD_MULT
report("U20_e1_rates_interaction_zero_for_additive_arch",
       abs(single["interaction"]) <= 3 * sd_single,
       "interaction=%.4f vs bound %.4f (single-input rule has no synergy)"
       % (single["interaction"], 3 * sd_single))

# ------------------------------------------------------------------ coverage against the map
d = json.loads((M / "governance/gate_coverage_map_v1.json").read_text(encoding="utf-8"))
gap_pairs = {(pathlib.Path(g["gate"]).name, g["name"]) for cat in d["gaps"].values() for g in cat}
passed = {n for n, ok in results if ok}
uncovered = sorted(gap_pairs - set(COVERS))
dangling = sorted(set(COVERS) - gap_pairs)
missing_checks = sorted({c for pair in COVERS for c in COVERS[pair] if c not in passed})
report("U21_every_unmeasured_instrument_in_the_map_has_a_falsifiable_check_here",
       not uncovered and not dangling and not missing_checks,
       f"map gaps {len(gap_pairs)} | covered {len(COVERS)} | uncovered {uncovered} "
       f"| dangling {dangling} | failing checks {missing_checks}")

def coverage_fails(pairs, covers, recorded):
    ok_ids = {n for n, ok in recorded if ok}
    un = sorted(pairs - set(covers))
    dan = sorted(set(covers) - pairs)
    mis = sorted({c for p in covers for c in covers[p] if c not in ok_ids})
    return bool(un or dan or mis)


ONE = ("p5b_gate.py", "tnorm")
mut = {
    "map gains a gap with no check": coverage_fails(gap_pairs | {("p8_gate.py", "not_a_real_instrument")},
                                                    COVERS, results),
    "COVERS registers an instrument the map dropped": coverage_fails(gap_pairs - {ONE}, COVERS, results),
    "a listed check id does not exist here": coverage_fails(gap_pairs,
                                                            {**COVERS, ONE: ["U99_not_a_real_check"]}, results),
    "a listed check fails": coverage_fails(gap_pairs, COVERS,
                                           [(n, n != "U01_tnorm_known_answers") for n, _ in results]),
}
report("U23_coverage_rule_bites_in_both_directions",
       not coverage_fails(gap_pairs, COVERS, results) and all(mut.values()),
       "baseline silent, each of the four drift shapes loud: "
       + " ".join(f"{k}={v}" for k, v in mut.items()))

rule_names = [n for n, _ in results]
report("SUITE_accounting", len(rule_names) == len(set(rule_names)) and len(rule_names) >= 22,
       f"{len(rule_names)} rules, all distinct")
report("SUITE_tally", tally["printed"] == len(results)
       and tally["printed_pass"] == sum(1 for _, p in results if p),
       "lines printed equal rules recorded")
# the headline fraction is derived AFTER the last report(): the first draft summed before appending
# SUITE_accounting and printed "19/23" over twenty-two recorded rules (the X-78b / X-80b family).
n_pass = sum(1 for _, p in results if p)
print(f"{n_pass}/{len(results)} checks passed")
raise SystemExit(0 if n_pass == len(results) else 1)
