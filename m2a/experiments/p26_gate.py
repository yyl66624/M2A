"""Gate for Phase XXVI (context-model C policy): instrument-only checks, 10 rules plus 2 self-counts.

Run from anywhere: `python3 experiments/p26_gate.py [--pre]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import tempfile

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
PREREG = EXP / "PHASE26_PREREGISTRATION.md"
ART = EXP / "phase26_results.json"
RUNNER = EXP / "run_phase26.py"
ZIP = REPO.parent / "_m2a_data" / "open_bandit_dataset.zip"

sys.path.insert(0, str(EXP))
import run_phase26 as R  # noqa: E402

PRE = "--pre" in sys.argv
RULES_FULL = ["G%d" % i for i in range(1, 11)]
RULES_PRE = ["G1", "G2", "G3", "G4", "G8", "G9"]
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
    zb = ZIP.read_bytes() if ZIP.exists() else b""
    zip_ok = bool(zb) and sha(zb) == R.ZIP_SHA and len(zb) == R.ZIP_BYTES
    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(head) and sha(PREREG.read_bytes()) == sha(head) and binding["two_channel_match"],
           "disk %s git %s" % (binding["disk_sha256"][:16], binding["git_head_sha256"][:16] or "absent"))
    report("G2 the OBD zip is outside the repository and matches the pinned SHA-256 and size",
           zip_ok and not str(ZIP.resolve()).startswith(str(REPO.resolve()) + "/"),
           "sha %s bytes %s" % (sha(zb)[:16] if zb else "", len(zb)))
    src = RUNNER.read_text(encoding="utf-8")
    report("G3 the model specification is fixed by construction",
           "N_AFF = 80" in src and "N_ITEM = 80" in src and "TRAIN_SAMPLE = 200000" in src
           and "EPOCHS = 5" in src and "SEED = 20261024" in src and "LR = 0.1" in src,
           "160 features, 200k sample, 5 epochs")
    probes = [
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"log_loss": 0.1, "base_log_loss": 0.2, "auc": 0.6, "contrast": 0.1,
                   "contrast_ci95": [0.05, 0.15]}, True)[0],
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"log_loss": 0.1, "base_log_loss": 0.2, "auc": 0.6, "contrast": 0.0,
                   "contrast_ci95": [-0.01, 0.01]}, True)[0],
        R.exit_of({"click_violations": 0, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"log_loss": 0.2, "base_log_loss": 0.2, "auc": 0.5, "contrast": 0.1,
                   "contrast_ci95": [0.05, 0.15]}, True)[0],
        R.exit_of({"click_violations": 1, "position_violations": 0, "timestamp_violations": 0, "total_rows": 1000},
                  {"log_loss": 0.1, "base_log_loss": 0.2, "auc": 0.6, "contrast": 0.1,
                   "contrast_ci95": [0.05, 0.15]}, True)[0],
    ]
    report("G4 all four registered exits are reachable and the vocabulary is exactly those four",
           probes == list(R.EXITS) and set(R.EXITS) == {
               "CONTEXT_C_BETTER", "CONTEXT_C_NOT_BETTER", "CONTEXT_MODEL_UNINFORMATIVE",
               "DATA_IDENTITY_MISMATCH"}, "probes %s" % (probes,))
    if not PRE:
        if art is None:
            report("G5 the artifact records the model, the test rows and the discrimination metrics", False, "absent")
            report("G6 every estimate is derived from the recorded counts", False, "absent")
        else:
            md, ev = art["model"], art["estimates"]
            report("G5 the artifact records the model, the test rows and the discrimination metrics",
                   md["features"] == 160 and md["train_sample"] == R.TRAIN_SAMPLE
                   and ev["test_rows"] > 0 and 0 <= ev["auc"] <= 1
                   and ev["log_loss"] > 0 and ev["base_log_loss"] > 0,
                   "rows %d auc %.4f" % (ev["test_rows"], ev["auc"]))
            ds = ev["s_take_clicks"] / ev["s_take_n"] if ev["s_take_n"] else 0.0
            dc = ev["c_take_clicks"] / ev["c_take_n"] if ev["c_take_n"] else 0.0
            report("G6 every estimate is derived from the recorded counts",
                   abs(ev["delta_s"] - ds) < 1e-12 and abs(ev["delta_c"] - dc) < 1e-12
                   and abs(ev["contrast"] - (dc - ds)) < 1e-12
                   and ev["contrast_ci95"][0] <= ev["contrast"] <= ev["contrast_ci95"][1],
                   "S %.6f C %.6f" % (ev["delta_s"], ev["delta_c"]))
    if not PRE:
        report("G7 the exit and label are re-derived from the artifact's own metrics",
               art is not None and R.exit_of(art["scan"], art["estimates"], True)
               == (art["exit"], art["label_r17"]),
               art["exit"] if art else "absent")
    report("G8 no new data: the runner reads only the OBD zip and the prereg, and fetches nothing",
           "urllib" not in src and "requests" not in src and "open_bandit_dataset.zip" in src
           and str(ZIP) not in src, "sources: OBD + prereg")
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "prereg.md"
        tmp.write_bytes(PREREG.read_bytes() + b"\n")
        tampered = R.bind(tmp)
    report("G9 the write barrier rejects a binding mismatch and sits before the write",
           tampered["two_channel_match"] is False
           and src.index("binding MISMATCH") < src.index("OUT.write_text"),
           "tampered %s" % (tampered["disk_sha256"][:16] or "absent"))
    if not PRE:
        report("G10 the model seed is fixed and the exit is stable under a second evaluation",
               bool(art) and art["model"]["seed"] == R.SEED
               and R.exit_of(art["scan"], art["estimates"], True) == (art["exit"], art["label_r17"]),
               "seed %s" % (art["model"]["seed"] if art else "?"))
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
