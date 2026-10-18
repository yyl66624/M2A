"""Phase V-d gate: wiring and known answers only (no science criteria)."""
from __future__ import annotations

import json
import pathlib
import sys

from p5d_confirm import (ARMS_D, LEGACY_SEEDS, QS_D, SEEDS_D, closed, dp_d, law_old, readout_d)

HERE = pathlib.Path(__file__).resolve().parent
checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + detail if detail else ""))


check("G1_seed_pool_disjoint", set(SEEDS_D).isdisjoint(LEGACY_SEEDS) and len(SEEDS_D) == 10,
      f"{SEEDS_D[0]}..{SEEDS_D[-1]} vs legacy 0..{LEGACY_SEEDS[-1]}")

cf05, cf10 = closed(0.5), closed(1.0)
check("G2_closed_form_endpoints", abs(cf05) < 1e-12 and abs(cf10 - 0.36) < 1e-12,
      f"q=0.5 {cf05:.3e}, q=1.0 {cf10:.6f}")

a = readout_d(0.8, 101, "confirm_const02")
b = readout_d(0.8, 101, "confirm_const02")
check("G3_determinism", a == b, f"{a:.6f}")

d1, d05 = dp_d(1.0), dp_d(0.5)
check("G4_dp_known_answers", abs(d1 - 0.36) <= 0.005 and d05 <= 0.005, f"{d1:.4f} / {d05:.4f}")

sep = abs(law_old(0.8) - closed(0.8))
check("G5_the_two_laws_are_distinguishable", sep >= 0.015,
      f"|law(1/2) - closed| at q=0.8 = {sep:.4f}")

prev = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V1"]["rows"]
check("G6_D4_wiring_present", all(f"base|{q}" in prev for q in QS_D), f"{len(QS_D)} q keys")

check("G7_arms_match_prereg", set(ARMS_D) == {"confirm_annealed", "confirm_const02"},
      f"{sorted(ARMS_D)}")

n_bad = sum(1 for _, ok, _ in checks if not ok)
print(f"\n{len(checks) - n_bad}/{len(checks)} checks passed"
      + ("" if n_bad == 0 else "  [FAILED -> Phase V-d must not run]"))
sys.exit(1 if n_bad else 0)
