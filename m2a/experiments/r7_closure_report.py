"""R7 closure report: the smallest difference each committed anchor check could actually distinguish.

Rule R7 (M2A_PROGRAM_PLAN.md section 6) requires every instrument check that compares against a
known value or a committed artifact to report the ratio tolerance / observed difference. Phase XIII
(W2, W5) and Phase XVIII (G1, G2) ran such comparisons but reported only the raw gap or the spare,
so the ratio was never stated. This script re-derives the quantities from the same instrument
modules the gates used -- it changes no verdict, it only supplies the missing disclosure.
"""
from __future__ import annotations

import json
import pathlib

import p13_closeout as p13
import p12_lattice as p12
import p18_stagger as p18
from p5_mechanisms import ALPHA
from p8_smooth import C1, poisson_quantile

EXP = pathlib.Path(__file__).resolve().parent
rows = []


def add(name, round_id, tol, actual, unit, floor_value, floor_label, note):
    ratio = (tol / actual) if actual else None
    rows.append({
        "check": name, "round": round_id, "tolerance": tol, "observed_max_difference": actual,
        "unit": unit, "ratio_tol_over_observed": ratio,
        "instrument_own_floor": floor_value, "floor_label": floor_label,
        "floor_over_tol_abs": (floor_value / tol) if tol else None, "note": note,
    })


# ---- Phase XIII W2: continuous quantile vs the committed discrete helper -----
gaps = [abs(p13.q_cont(l) - poisson_quantile(l, 1.0 - ALPHA)) for l in p13.LAMBDAS]
add("W2_q_cont_vs_committed_discrete_quantile", "Phase XIII", 1.0, max(gaps), "count",
    1.0, "one lattice step of the committed discrete helper",
    "tolerance equals the lattice step, so a variant off by exactly one count also passes; "
    "spare margin is only " + format(1.0 - max(gaps), ".4f") + " counts")

# ---- Phase XIII W5: smooth-anchor bit-exactness ------------------------------
committed8 = json.loads((EXP / "phase8_results.json").read_text(encoding="utf-8"))
rel_w5 = max(abs(p12.rho_smooth(2 * C1, s) - committed8["rows"][str(s)]["rho_smooth"])
                / committed8["rows"][str(s)]["rho_smooth"] for s in committed8["s_grid"])
add("W5_rho_smooth_anchor_bit_exact", "Phase XIII", 1e-9, rel_w5,
    f"relative over {len(committed8['s_grid'])} s-grid points", 1e-9,
    "absolute tolerance of the anchor path",
    ("observed difference is exactly zero, so the ratio is undefined and -- per R14 -- a zero "
     "difference on a displacement ruler is not evidence of zero error; the honest statement is "
     "the floor itself: deviations below 1e-9 relative are invisible to this check")
    if rel_w5 == 0.0 else
    f"ratio tol/observed = {1e-9 / rel_w5:.4f}: the check would still pass a deviation "
    f"{1e-9 / rel_w5:.2f} times larger than what it actually saw")

# ---- Phase XVIII G1 / G2: three-layer instrument vs committed artifacts ------
ref_a, ref_b = p18.committed_reference_all()
sweeps = {(kind, k): p18.sweep(kind, k) for k in p18.KS for kind in p18.KINDS}
rel_a, rel_b = [], []
for (kind, k), g in sweeps.items():
    for r in g["rows"]:
        key = (kind, k, r["J"])
        if key in ref_a:
            rel_a.append(abs(r["delta_committed"] - ref_a[key]) / abs(ref_a[key]))
        if key in ref_b:
            rel_b.append(abs(r["delta_revert_stagger"] - ref_b[key]) / abs(ref_b[key]))
tol = p18.ANCHOR_TOL
l3 = max(r["L3"] for g in sweeps.values() for r in g["rows"])
scale = max(abs(v) for v in ref_a.values())
for name, rels, cfg in (("G1_anchor_vs_committed_phase14_phase16", rel_a, "h=1.0, n=20001, sigma=0"),
                        ("G2_anchor_vs_committed_phase17_primary", rel_b, "h=2.0, n=40001, sigma=0")):
    add(name, "Phase XVIII", tol, max(rels), "relative over " + str(len(rels)) + " cells (" + cfg + ")",
        l3, "largest three-layer displacement the same instrument reports (L3 max)",
        "the anchor can only flag a relative deviation above 1e-15; on the round's own scale "
        "(max |delta| = " + format(scale, ".4e") + ") that is "
        + format(tol * scale, ".4e") + " absolute, i.e. the anchor is "
        + format(l3 / (tol * scale), ".2e") + " times finer than the displacement floor it certifies: "
        "it certifies wiring, not accuracy")
    rows[-1]["delta_scale_max"] = scale
    rows[-1]["tolerance_absolute_equiv"] = tol * scale
    rows[-1]["floor_over_tolerance_at_scale"] = l3 / (tol * scale)

out = {"schema": "m2a.r7_closure.v1",
       "rule": "R7 (report smallest distinguishable difference for known-value comparisons)",
       "registered_before_run": False,
       "status": "zero-test disclosure re-analysis; no verdict of any round is altered",
       "checks": rows}
(EXP / "r7_closure_report.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

for r in rows:
    ratio = "undefined (observed difference is 0)" if r["ratio_tol_over_observed"] is None \
        else format(r["ratio_tol_over_observed"], ".4f")
    print(f"{r['check']:<44} tol={r['tolerance']:.1e} observed={r['observed_max_difference']:.2e} ratio={ratio}")
    print(f"{'':<44} instrument floor {r['floor_label']} = {r['instrument_own_floor']:.4e}; {r['note']}")
print("\nwrote", EXP / "r7_closure_report.json")
