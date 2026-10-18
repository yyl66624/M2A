"""Post-hoc decomposition of the Phase V / V1 result (does NOT gate any verdict).

Registered in PHASE5_RESULTS.md as post_hoc_descriptive: true. It answers one question only:
how much of the Phase III/IV "L3 learner bias" is the learner, and how much is the analytic law's
own conditioned prior.
"""
from __future__ import annotations

import json
import pathlib

import numpy as np

from p4_mechanisms import bayes_sensitivity
from p5_mechanisms import QS, dp_sensitivity_only, law, law_prior

HERE = pathlib.Path(__file__).resolve().parent
PRIOR_TRUE = 0.4      # P(B available | max=0.9) under the actual mask draw (3/8, 3/8, 1/4)
GAMMA, V_B, C = 0.9, 0.5, 0.1


def state_posterior(q: float, prior=PRIOR_TRUE) -> tuple:
    p1 = prior * q / (prior * q + (1.0 - prior) * (1.0 - q))
    p0 = prior * (1.0 - q) / (prior * (1.0 - q) + (1.0 - prior) * q)
    return p1, p0


def visit_weighted(q: float, prior=PRIOR_TRUE) -> float:
    """What the sampler converges to: the first action is uniform over avail, so a state with only
    A available is sampled into the probe cell at weight 1/2 while a both-available state gets 1/3."""
    p1, p0 = state_posterior(q, prior)
    w = lambda p: (p / 3.0) / (p / 3.0 + (1.0 - p) / 2.0)  # noqa: E731
    return GAMMA * (V_B - C) * (w(p1) - w(p0))


def main() -> int:
    committed = json.loads((HERE / "phase5_results.json").read_text(encoding="utf-8"))["V1"]["rows"]
    rows = {}
    for q in QS:
        d = committed[f"base|{q}"]
        p1, p0 = state_posterior(q)
        rows[str(q)] = {
            "law_prior_1_2": law(q),
            "law_prior_2_5_state_level": law_prior(q, prior=PRIOR_TRUE),
            "visit_weighted_closed_form": visit_weighted(q),
            "dp_exact_operator": d["dp"],
            "mc_mean_10_seeds": d["mc_mean"],
            "posterior_B_given_cue": {"cue_0": p0, "cue_1": p1},
            "gap_law_minus_visit_weighted": law(q) - visit_weighted(q),
            "gap_visit_weighted_minus_dp": visit_weighted(q) - d["dp"],
            "gap_dp_minus_mc": d["dp"] - d["mc_mean"],
        }
    b = float(np.mean([bayes_sensitivity(0.8, seed=s) for s in range(5)]))
    out = {
        "schema": "m2a.phase5.v1.posthoc.v1",
        "gates_the_verdict": False,
        "registered_before_run": False,
        "question": "how much of the L3 residual is the learner and how much is the law's prior",
        "rows": rows,
        "p4_bayes_estimator_at_q_0p8": b,
        "p4_bayes_hardcodes_prior_one_half": True,
        "note": ("p4_mechanisms.bayes_sensitivity samples B-availability as rng.rand() < 0.5, so its "
                 "agreement with the Phase III law is a shared assumption, not an independent check. "
                 "The environment's conditioned prior is 2/5."),
    }
    out["closed_form_matches_dp_max_abs_diff"] = max(
        abs(r["visit_weighted_closed_form"] - r["dp_exact_operator"]) for r in rows.values())
    json.dump(out, open(HERE / "p5_v1_posthoc.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for q in QS:
        r = rows[str(q)]
        print(f"q={q}: law(1/2)={r['law_prior_1_2']:.4f} law(2/5)={r['law_prior_2_5_state_level']:.4f} "
              f"visit-wtd={r['visit_weighted_closed_form']:.4f} dp={r['dp_exact_operator']:.4f} "
              f"mc={r['mc_mean_10_seeds']:.4f}")
    print("closed form vs DP max abs diff:", out["closed_form_matches_dp_max_abs_diff"])
    print("p4 Bayes estimator at q=0.8:", b, "(law 1/2 = 0.2160)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
