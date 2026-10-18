"""Post-run re-analysis of the committed Phase VI readings (zero new test status).

Documents P6-A7 (criterion-3 direction bug) and P6-A8 (incomplete outcome table) on the
already-committed rows, without re-judging S2 and without altering phase6_results.json.
"""
from __future__ import annotations
import json, hashlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
p = json.loads((HERE / "phase6_results.json").read_text(encoding="utf-8"))
rows = p["S2"]["rows"]
by_gap = sorted(rows, key=lambda r: r["gap"])                       # Delta ascending
rho = [r["rho_numeric"] for r in by_gap]
crit3_holds = all(rho[i] >= rho[i + 1] - 1e-9 for i in range(len(rho) - 1))   # rho* non-increasing in Delta
out = {
    "schema": "m2a.phase6.reanalysis.v1",
    "gates_the_verdict": False,
    "registered_before_run": False,
    "source_artifact_sha256": hashlib.sha256((HERE / "phase6_results.json").read_bytes()).hexdigest(),
    "P6_A7_criterion3_direction_bug_in_runner": {
        "runner_reported": p["S2"]["checks"]["S2_monotone_in_gap"],
        "recomputed_on_committed_rows": crit3_holds,
        "reading": "rho* 随 Delta 增大而单调不增（Delta 0.20->250.245, 0.75->11.844），注册表述成立",
        "consequence": "runner 的 False 是假阴性；不据此改判 S2",
    },
    "P6_A8_outcome_table_incomplete": {
        "runner_label": p["outcome"],
        "correct_label": "O-NONE (three registered exits all inapplicable)",
        "reason": "S2 的不符发生在幂指数与近似单调性上，不构成 O-REFUTED 所要求的符号/单调性矛盾",
    },
    "S2_verdict_unchanged": p["S2"]["checks"],
    "what_this_document_adds": "nothing -- zero test status, no new cells, no re-judgement",
}
json.dump(out, open(HERE / "phase6_reanalysis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("criterion3 recomputed on committed rows:", crit3_holds)
print("runner had reported:", p["S2"]["checks"]["S2_monotone_in_gap"])
print("outcome label: runner", p["outcome"], "-> corrected label O-NONE (S2 verdict unchanged)")
