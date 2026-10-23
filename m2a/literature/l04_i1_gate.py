"""Gate for Round L-04 (I1 paper-level audit): instrument-only checks, 12 rules plus 2 self-counts.

It never judges whether a row was coded S or C. It checks the denominator, the closed vocabulary,
the evidence keys, the derived counts, the exit re-derivation, the write barrier and determinism.
`--pre` is the runner's barrier; with no argument it runs full, so the closing audit gets the artifact rules.

Run from anywhere: `python3 literature/l04_i1_gate.py [--pre]`.
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
PREREG = LIT / "L04_PREREGISTRATION.md"
ART = LIT / "L04_I1_AUDIT.json"
RUNNER = LIT / "l04_i1_audit.py"
L01 = LIT / "L01_coding.json"

sys.path.insert(0, str(LIT))
import l04_i1_audit as C  # noqa: E402

PRE = "--pre" in sys.argv
RULES_FULL = ["G%d" % i for i in range(1, 13)]
RULES_PRE = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G11", "G12"]
RULES = RULES_PRE if PRE else RULES_FULL

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
    l01 = json.loads(L01.read_text(encoding="utf-8"))["records"]
    ft = json.loads((LIT / "fulltext_review.json").read_text(encoding="utf-8"))["records"]
    doc = C.build()
    binding = C.bind()
    head = C.git_head(str(PREREG.relative_to(REPO)))
    art = json.loads(ART.read_text(encoding="utf-8")) if ART.exists() else None

    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(head) and sha(PREREG.read_bytes()) == sha(head) and binding["two_channel_match"],
           "disk %s git %s" % (binding["disk_sha256"][:16], binding["git_head_sha256"][:16] or "absent"))
    report("G2 the denominator is exactly the 17 committed L-01 rows, with no missing or extra row",
           len(doc["rows"]) == 17 and not doc["missing_rows"] and not doc["extra_rows"]
           and set(r["sid"] for r in doc["rows"]) == set(l01),
           "rows %d missing %s extra %s" % (len(doc["rows"]), doc["missing_rows"], doc["extra_rows"]))
    report("G3 the code vocabulary is closed, every row has a rationale and at least one evidence key",
           all(r["code"] in C.CODES for r in doc["rows"])
           and all(r["rationale"].strip() for r in doc["rows"])
           and all(r["evidence_k"] for r in doc["rows"]),
           "codes %s" % sorted({r["code"] for r in doc["rows"]}))
    c = doc["counts"]
    recomputed = {k: sum(1 for r in doc["rows"] if r["code"] == k) for k in
                  ("S_ONLY", "C_ONLY", "S_PLUS_C", "NEITHER", "UNDECIDABLE")}
    report("G4 every count is derived from the rows, including the I1-relevant subtotal",
           c["rows"] == len(doc["rows"]) and all(c[k] == v for k, v in recomputed.items())
           and c["i1_relevant"] == c["S_ONLY"] + c["C_ONLY"] + c["S_PLUS_C"],
           "counts %s" % recomputed)
    bad_k = []
    for r in doc["rows"]:
        mechs = {m.get("k") for m in l01[r["sid"]].get("mechanism", [])}
        bad_k += [k for k in r["evidence_k"] if k not in mechs]
    report("G5 every evidence key exists in the L-01 row it is cited from",
           not bad_k, "bad %s" % (bad_k or "none"))
    bad_q = [r["sid"] for r in doc["rows"]
             if not (20 <= r["quote_chars"] <= 400) or len(r["quote_sha16"]) != 16]
    report("G6 every cited quote is inside the L-01 20-400 character contract and has a sha16",
           not bad_q, "bad %s" % (bad_q or "none"))
    src = RUNNER.read_text(encoding="utf-8")
    report("G7 no new data: the audit reads only the committed coding and the prereg, and fetches nothing",
           "urllib" not in src and "requests" not in src and "_m2a_ft" not in src
           and "L01_coding.json" in src and "fulltext_review.json" in src,
           "sources named: L01 + fulltext_review")
    probes = [
        C.exit_of({"S_PLUS_C": 1, "S_ONLY": 0, "C_ONLY": 0, "i1_relevant": 1})[0],
        C.exit_of({"S_PLUS_C": 1, "S_ONLY": 1, "C_ONLY": 0, "i1_relevant": 2})[0],
        C.exit_of({"S_PLUS_C": 0, "S_ONLY": 1, "C_ONLY": 1, "i1_relevant": 3})[0],
        C.exit_of({"S_PLUS_C": 0, "S_ONLY": 1, "C_ONLY": 0, "i1_relevant": 1})[0],
        C.exit_of({"S_PLUS_C": 0, "S_ONLY": 0, "C_ONLY": 0, "i1_relevant": 0}, invalid=True)[0],
    ]
    report("G8 all five registered exits are reachable and the vocabulary is exactly those five",
           probes == list(C.EXITS) and set(C.EXITS) == {
               "I1_CONJUNCTION_OBSERVED", "I1_LAYERS_SEPARABLE", "I1_CONJUNCTION_NOT_OBSERVED",
               "I1_EVIDENCE_INSUFFICIENT", "I1_AUDIT_INVALID"},
           "probes %s" % (probes,))
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "prereg.md"
        tmp.write_bytes(PREREG.read_bytes() + b"\n")
        tampered = C.bind(tmp)
    report("G11 the write barrier rejects a binding mismatch and sits before the write",
           tampered["two_channel_match"] is False
           and src.index("binding MISMATCH") < src.index("OUT.write_text"),
           "tampered %s" % (tampered["disk_sha256"][:16] or "absent"))
    again = C.build()
    report("G12 the audit is deterministic: two builds produce identical rows and counts",
           json.dumps(doc["rows"], sort_keys=True) == json.dumps(again["rows"], sort_keys=True)
           and doc["counts"] == again["counts"], "rows %d" % len(doc["rows"]))
    if not PRE:
        if art is None:
            report("G9 the artifact's counts equal the rows it summarises", False, "artifact absent")
        else:
            report("G9 the artifact's counts equal the rows it summarises",
                   art["counts"] == doc["counts"] and art["exit"] == doc["exit"]
                   and art["label_r17"] == doc["label_r17"],
                   "artifact %s (%s) vs computed %s (%s)" % (art["exit"], art["label_r17"], doc["exit"], doc["label_r17"]))
        report("G10 the artifact's exit and label are re-derived from its own counts",
               bool(art) and C.exit_of(art["counts"]) == (art["exit"], art["label_r17"])
               and art["prereg_binding"]["two_channel_match"] is True
               and art["prereg_sha256"] == sha(PREREG.read_bytes()),
               "second path %s" % (C.exit_of(art["counts"]) if art else None,))
    got = [re.match(r"G\d+", t).group(0) for t, _ in _verdicts]
    report("SUITE_accounting every rule declared for this mode was recorded exactly once",
           sorted(got) == sorted(RULES) and len(got) == len(set(got)),
           "ids=%d declared=%d pre=%s" % (len(got), len(RULES), PRE))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _, v in _verdicts if v)
           and len(_verdicts) == len(RULES) + 1,
           "recorded=%d passed=%d rules=%d" % (_n, _ok, len(RULES)))
    print("%d/%d checks passed" % (_ok, _n))
    return 0 if _ok == _n else 1


if __name__ == "__main__":
    sys.exit(main())
