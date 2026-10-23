"""Gate for Round L-05 (second-coder audit): instrument-only checks, 10 rules plus 2 self-counts.

It checks the 21-paper population, both code sets, the closed vocabulary, the agreement arithmetic,
the exit re-derivation, the write barrier and determinism. It never judges whether a paper merits S or C.

Run from anywhere: `python3 literature/l05_gate.py`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import tempfile

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L05_PREREGISTRATION.md"
ART = LIT / "L05_SECOND_CODER.json"
RUNNER = LIT / "l05_second_coder.py"
FULLTEXTS = LIT / "fulltext_review.json"

sys.path.insert(0, str(LIT))
import l05_second_coder as C  # noqa: E402

RULES = ["G%d" % i for i in range(1, 11)]
_verdicts = []
_n = 0
_ok = 0


def report(tag, cond, detail=""):
    global _n, _ok
    _n += 1
    cond = bool(cond)
    _verdicts.append((tag, cond))
    _ok += int(cond)
    print(("PASS " if cond else "FAIL ") + tag + " " + (detail if detail else ""))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    keys = list(json.loads(FULLTEXTS.read_text(encoding="utf-8"))["records"])
    doc = C.build()
    binding = C.bind()
    head = C.git_head(str(PREREG.relative_to(REPO)))
    art = json.loads(ART.read_text(encoding="utf-8")) if ART.exists() else None

    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(head) and sha(PREREG.read_bytes()) == sha(head) and binding["two_channel_match"],
           "disk %s git %s" % (binding["disk_sha256"][:16], binding["git_head_sha256"][:16] or "absent"))
    report("G2 the population is the 21 full-text review records and every row has a primary code",
           len(keys) == 21 and len(doc["rows"]) == 21 and set(r["paper"] for r in doc["rows"]) == set(keys),
           "keys %d rows %d" % (len(keys), len(doc["rows"])))
    report("G3 the primary code vocabulary is closed and covers every paper exactly once",
           all(r["primary"] in C.CODES for r in doc["rows"])
           and len({r["paper"] for r in doc["rows"]}) == 21,
           "primary codes %s" % sorted({r["primary"] for r in doc["rows"]}))
    second_ok = doc["second_file"]["exists"] and all(r["second"] in C.CODES for r in doc["rows"])
    report("G4 the second coder's file exists, covers every paper and uses the closed vocabulary",
           second_ok, "file %s | second codes %s"
           % (doc["second_file"]["exists"], sorted({str(r["second"]) for r in doc["rows"]})))
    matches = sum(1 for r in doc["rows"] if r["agree"])
    report("G5 the agreement is derived from the rows and the kappa is reported or explicitly undefined",
           doc["agreement"]["matches"] == matches
           and doc["agreement"]["raw"] == round(matches / 21, 4)
           and (doc["agreement"]["cohen_kappa"] == "UNDEFINED"
                or isinstance(doc["agreement"]["cohen_kappa"], float)),
           "matches %d raw %s kappa %s" % (matches, doc["agreement"]["raw"],
                                           doc["agreement"]["cohen_kappa"]))
    if not second_ok:
        want = ("L05_SECOND_CODER_MISSING", "NULL")
    elif all(r["primary"] == "NEITHER" and r["second"] == "NEITHER" for r in doc["rows"]):
        want = ("L05_DENOMINATOR_EMPTY", "REFUTED")
    elif any(r["agree"] and r["primary"] in ("S_ONLY", "C_ONLY", "S_PLUS_C") for r in doc["rows"]):
        want = ("L05_DENOMINATOR_NONEMPTY", "SUPPORTED")
    else:
        want = ("L05_PARTIAL_AGREEMENT", "INDETERMINATE")
    report("G6 the exit and five-value label are re-derived from the two code sets",
           (doc["exit"], doc["label_r17"]) == want, "derived %s vs %s" % (want, (doc["exit"], doc["label_r17"])))
    src = RUNNER.read_text(encoding="utf-8")
    report("G7 no new data: the audit reads only the 21-record population, the prereg and the second file",
           "urllib" not in src and "requests" not in src and "fulltext_review.json" in src
           and "l05_second.md" in src, "sources named: fulltext_review + second file")
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "prereg.md"
        tmp.write_bytes(PREREG.read_bytes() + b"\n")
        tampered = C.bind(tmp)
    report("G8 the write barrier rejects a binding mismatch and sits before the write",
           tampered["two_channel_match"] is False
           and src.index("binding MISMATCH") < src.index("OUT.write_text"),
           "tampered %s" % (tampered["disk_sha256"][:16] or "absent"))
    again = C.build()
    report("G9 the audit is deterministic: two builds produce identical rows and agreement",
           json.dumps(doc["rows"], sort_keys=True) == json.dumps(again["rows"], sort_keys=True)
           and doc["agreement"] == again["agreement"], "rows %d" % len(doc["rows"]))
    report("G10 the artifact's rows, agreement and exit equal the recomputed values",
           bool(art) and art["rows"] == doc["rows"] and art["agreement"] == doc["agreement"]
           and art["exit"] == doc["exit"] and art["label_r17"] == doc["label_r17"]
           and art["prereg_binding"]["two_channel_match"] is True,
           "artifact %s (%s)" % (art["exit"], art["label_r17"]) if art else "artifact absent")
    got = [re.match(r"G\d+", t).group(0) for t, _ in _verdicts]
    report("SUITE_accounting every declared rule was recorded exactly once",
           sorted(got) == sorted(RULES) and len(got) == len(set(got)),
           "ids=%d declared=%d" % (len(got), len(RULES)))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _, v in _verdicts if v)
           and len(_verdicts) == len(RULES) + 1,
           "recorded=%d passed=%d rules=%d" % (_n, _ok, len(RULES)))
    print("%d/%d checks passed" % (_ok, _n))
    return 0 if _ok == _n else 1


if __name__ == "__main__":
    sys.exit(main())
