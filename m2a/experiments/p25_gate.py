"""Gate for Phase XXV (real-data S-only arm): instrument-only checks, 10 rules plus 2 self-counts.

It checks the prereg binding, the OBD identity, the policy definitions, the split, the derived
estimates and the exit; it does not judge whether the real-system operationalization is a good
proxy for I1. `--pre` is the runner's barrier; full mode adds the artifact rules.

Run from anywhere: `python3 experiments/p25_gate.py [--pre]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
PREREG = EXP / "PHASE25_PREREGISTRATION.md"
ART = EXP / "phase25_results.json"
RUNNER = EXP / "run_phase25.py"
ZIP = REPO.parent / "_m2a_data" / "open_bandit_dataset.zip"

sys.path.insert(0, str(EXP))
import run_phase25 as R  # noqa: E402

PRE = "--pre" in sys.argv
RULES_FULL = ["G%d" % i for i in range(1, 11)]
RULES_PRE = ["G1", "G2", "G3", "G4", "G7", "G8"]
RULES = RULES_PRE if PRE else RULES_FULL

_v, _n, _ok = [], 0, 0


def report(tag, cond, detail=""):
    global _n, _ok
    _n += 1
    cond = bool(cond)
    _v.append((tag, cond))
    _ok += int(cond)
    print(("PASS " if cond else "FAIL ") + tag + " " + (detail if detail else ""))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    head = R.git_head(str(PREREG.relative_to(REPO)))
    binding = R.bind()
    art = json.loads(ART.read_text(encoding="utf-8")) if ART.exists() else None
    zip_bytes = ZIP.read_bytes() if ZIP.exists() else b""
    zip_ok = bool(zip_bytes) and sha(zip_bytes) == R.ZIP_SHA and len(zip_bytes) == R.ZIP_BYTES

    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(head) and sha(PREREG.read_bytes()) == sha(head) and binding["two_channel_match"],
           "disk %s git %s" % (binding["disk_sha256"][:16], binding["git_head_sha256"][:16] or "absent"))
    report("G2 the OBD zip is outside the repository and matches the pinned SHA-256 and size",
           zip_ok and not str(ZIP.resolve()).startswith(str(REPO.resolve()) + "/"),
           "sha %s bytes %s outside %s" % (sha(zip_bytes)[:16] if zip_bytes else "", len(zip_bytes),
                                           not str(ZIP.resolve()).startswith(str(REPO.resolve()) + "/")))
    src = RUNNER.read_text(encoding="utf-8")
    report("G3 the runner fixes the split and both policies by construction",
           "TRAIN_FRAC = 0.70" in src and "S_MOD = 3" in src and "MIN_ITEM_SHOWS = 100" in src
           and "skip iff position % 3 == 0" in src and "skip iff item training CTR" in src,
           "split/policies named in the runner")
    probes = [
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"delta_s": 0.1, "delta_s_ci95": [0.05, 0.15], "contrast": 0.1,
                   "contrast_ci95": [0.05, 0.15], "s_skip_label_click_rate": 0.1,
                   "s_take_label_click_rate": 0.1}, True)[0],
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"delta_s": 0.1, "delta_s_ci95": [0.05, 0.15], "contrast": 0.0,
                   "contrast_ci95": [-0.01, 0.01], "s_skip_label_click_rate": 0.1,
                   "s_take_label_click_rate": 0.1}, True)[0],
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"delta_s": 0.0, "delta_s_ci95": [-0.01, 0.01], "contrast": 0.0,
                   "contrast_ci95": [-0.01, 0.01], "s_skip_label_click_rate": 0.0,
                   "s_take_label_click_rate": 0.0}, True)[0],
        R.exit_of({"click_violations": 1, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"delta_s": 0.1, "delta_s_ci95": [0.05, 0.15], "contrast": 0.1,
                   "contrast_ci95": [0.05, 0.15], "s_skip_label_click_rate": 0.1,
                   "s_take_label_click_rate": 0.1}, True)[0],
    ]
    report("G4 all four registered exits are reachable and the vocabulary is exactly those four",
           probes == list(R.EXITS) and set(R.EXITS) == {
               "S_ONLY_NONZERO_AND_C_BETTER", "S_ONLY_NONZERO_C_NOT_BETTER",
               "S_ONLY_ZERO_OR_NEGLIGIBLE", "DATA_IDENTITY_MISMATCH"},
           "probes %s" % (probes,))
    if art is None:
        report("G5 the artifact records a non-empty scan and a 70/30 split", False, "artifact absent")
        report("G6 every estimate is derived from the recorded counts", False, "artifact absent")
    else:
        sc, ev = art["scan"], art["estimates"]
        report("G5 the artifact records a non-empty scan and a 70/30 split",
               sc["total_rows"] > 0 and ev["train_rows"] + ev["test_rows"] == sc["total_rows"]
               and sc["click_violations"] == 0 and sc["position_violations"] == 0
               and sc["timestamp_violations"] <= R.TS_TOL * sc["total_rows"],
               "rows %d train %d test %d" % (sc["total_rows"], ev["train_rows"], ev["test_rows"]))
        d_s = ev["s_take_clicks"] / ev["s_take_n"] if ev["s_take_n"] else 0.0
        d_c = ev["c_take_clicks"] / ev["c_take_n"] if ev["c_take_n"] else 0.0
        report("G6 every estimate is derived from the recorded counts",
               abs(ev["delta_s"] - d_s) < 1e-12 and abs(ev["delta_c"] - d_c) < 1e-12
               and abs(ev["contrast"] - (d_c - d_s)) < 1e-12
               and ev["delta_s_ci95"][0] <= ev["delta_s"] <= ev["delta_s_ci95"][1]
               and ev["contrast_ci95"][0] <= ev["contrast"] <= ev["contrast_ci95"][1],
               "S %.6f C %.6f contrast %.6f" % (ev["delta_s"], ev["delta_c"], ev["contrast"]))
    report("G7 no new data: the runner reads only the OBD zip and the prereg, and fetches nothing",
           "urllib" not in src and "requests" not in src and "open_bandit_dataset.zip" in src
           and str(ZIP) not in src, "data path is outside the repo")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "prereg.md"
        tmp.write_bytes(PREREG.read_bytes() + b"\n")
        tampered = R.bind(tmp)
    report("G8 the write barrier rejects a binding mismatch and sits before the write",
           tampered["two_channel_match"] is False
           and src.index("binding MISMATCH") < src.index("OUT.write_text"),
           "tampered %s" % (tampered["disk_sha256"][:16] or "absent"))
    if not PRE:
        report("G9 the artifact's exit and criteria equal the recomputed ones",
               bool(art) and art["prereg_binding"]["two_channel_match"] is True
               and art["prereg_sha256"] == sha(PREREG.read_bytes())
               and (art["exit"], art["label_r17"]) == R.exit_of(art["scan"], art["estimates"], True)
               and art["criteria"]["C1_delta_s"] == (art["estimates"]["delta_s"] > 0 and art["estimates"]["delta_s_ci95"][0] > 0),
               art["exit"] if art else "absent")
        report("G10 the bootstrap seed is fixed and the exit is stable under a second evaluation",
               bool(art) and art["bootstrap"]["seed"] == R.SEED
               and R.exit_of(art["scan"], art["estimates"], True) == (art["exit"], art["label_r17"]),
               "seed %s" % (art["bootstrap"]["seed"] if art else "?"))
    got = [re.match(r"G\d+", t).group(0) for t, _ in _v]
    report("SUITE_accounting every declared rule was recorded exactly once",
           sorted(got) == sorted(RULES) and len(got) == len(set(got)),
           "ids=%d declared=%d pre=%s" % (len(got), len(RULES), PRE))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_v) and _ok == sum(1 for _, c in _v if c) and len(_v) == len(RULES) + 1,
           "recorded=%d passed=%d rules=%d" % (_n, _ok, len(RULES)))
    print("%d/%d checks passed" % (_ok, _n))
    return 0 if _ok == _n else 1


if __name__ == "__main__":
    sys.exit(main())
