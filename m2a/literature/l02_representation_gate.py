"""Gate for the L-02 representation addendum: instrument-only checks, 12 pre-flight or 14 full rules.

It refuses (R2) to judge whether a `NOT_STATED` is the right reading of the paper. What it checks is that the
source is the pinned file, that the extraction is deterministic, that every quote is inside the 20-400 character
contract and hits exactly once, that the absence regions resolve to unique markers with zero registered token
hits, that the exit table can reach all four exits, that the artifact's summary equals its rows, that the write
barrier sits before the write, and that the exit is re-derived by a second path. `--pre` is the runner's write
barrier; with no argument it runs full, so the closing audit gets the artifact rules too.

Run from anywhere: `python3 literature/l02_representation_gate.py [--pre]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L02_REPRESENTATION_ADDENDUM.md"
ART = LIT / "L02_representation_coding.json"
RUNNER = LIT / "l02_representation_coding.py"
L02_PREREG = LIT / "L02_PREREGISTRATION.md"
L02_RUN = LIT / "L02_reanalysis.json"
L02_CODING = LIT / "L02_coding.json"

sys.path.insert(0, str(LIT))
import l02_representation_coding as C  # noqa: E402

PRE = "--pre" in sys.argv
RULES_FULL = ["G%d" % i for i in range(1, 15)]
RULES_PRE = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G11", "G12", "G14"]
RULES = RULES_PRE if PRE else RULES_FULL
REQUIRED_IDS = ["R-1", "R-2", "R-3", "R-4", "R-5", "R-6"]
STATUSES = {"STATED", "NOT_STATED", "UNLOCATABLE"}

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


def head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def main() -> int:
    text, meta = C.extract()
    coded = C.code(text)
    addendum = PREREG.read_text(encoding="utf-8")
    binding = C.bind()
    rel = str(PREREG.relative_to(REPO))
    head = head_bytes(rel)
    art = json.loads(ART.read_text(encoding="utf-8")) if ART.exists() else None

    report("G1 the addendum is committed and its disk bytes equal the git object",
           bool(head) and sha(PREREG.read_bytes()) == sha(head) and binding["two_channel_match"],
           "disk %s git %s" % (binding["disk_sha256"][:16], binding["git_head_sha256"][:16] or "absent"))
    report("G2 the source is the pinned PDF, outside the repository, and the addendum names the same bytes",
           meta.get("record") == "EXTRACTED" and meta.get("pdf_sha256") == C.PDF_SHA
           and meta.get("pdf_bytes") == C.PDF_BYTES
           and not str(C.PDF.resolve()).startswith(str(REPO.resolve()) + "/")
           and C.PDF_SHA in addendum and str(C.PDF_BYTES) in addendum,
           "sha %s bytes %s outside %s" % (meta.get("pdf_sha256", "")[:16], meta.get("pdf_bytes"),
                                           not str(C.PDF.resolve()).startswith(str(REPO.resolve()) + "/")))
    text2, meta2 = C.extract()
    report("G3 extraction is deterministic on the pinned bytes and the normalisation is declared",
           bool(text) and meta.get("text_sha256") == meta2.get("text_sha256")
           and meta.get("text_chars") == len(text) and "LF" in C.NORMALIZATION
           and meta.get("extractor_version", "").startswith("pdftotext version"),
           "chars %d sha %s" % (len(text), meta.get("text_sha256", "")[:16]))
    l02_pre = json.loads(L02_RUN.read_text(encoding="utf-8")) if L02_RUN.exists() else {}
    l02_coding = json.loads(L02_CODING.read_text(encoding="utf-8")) if L02_CODING.exists() else {}
    frozen_ok = (l02_pre.get("prereg_sha256") == sha(L02_PREREG.read_bytes())
                 and l02_coding.get("prereg_sha256") == sha(L02_PREREG.read_bytes()))
    report("G4 the parent round's frozen inputs are unchanged: both artifacts still bind the L-02 prereg",
           frozen_ok, "L02 prereg %s" % sha(L02_PREREG.read_bytes())[:16])
    lit_hashes = {sha(p.read_bytes()) for p in LIT.glob("*") if p.is_file()}
    report("G5 no third-party full text is inside the repository",
           C.PDF_SHA not in lit_hashes and meta.get("text_sha256", "") not in lit_hashes
           and not str(C.PDF.resolve()).startswith(str(REPO.resolve()) + "/"),
           "literature files hashed %d" % len(lit_hashes))
    bad_q = []
    for row in coded["items"]:
        for q in row.get("quotes", []):
            if q["occurrences"] != 1 or not q["in_contract"] or q["quote_sha16"] != sha(q["quote"].encode("utf-8"))[:16]:
                bad_q.append(row["id"])
    report("G6 every coded quote is 20-400 characters, unique in the text, and its offset and sha16 check out",
           not bad_q and all(20 <= len(q["quote"]) <= 400 for r in coded["items"] for q in r.get("quotes", [])),
           "quotes %d | violations %s" % (sum(len(r.get("quotes", [])) for r in coded["items"]), bad_q or "none"))
    ids = [r["id"] for r in coded["items"]]
    report("G7 the vocabulary is closed: six registered ids, quote or absence kinds, three possible statuses",
           ids == REQUIRED_IDS and all(r["kind"] in {"quote", "absence"} for r in coded["items"])
           and all(r["status"] in STATUSES for r in coded["items"])
           and sum(1 for r in coded["items"] if r["kind"] == "absence") == 1,
           "ids %s statuses %s" % (ids, [r["status"] for r in coded["items"]]))
    abs_rows = [r for r in coded["items"] if r["kind"] == "absence"]
    abs_ok = bool(abs_rows) and abs_rows[0]["token_hits_total"] == 0 and abs_rows[0]["numeric_hits_total"] == 0 \
        and abs_rows[0]["probe_occurrences_in_A2_BODY"] == 1 \
        and all(r["start_occurrences"] == 1 and r["end_occurrences"] == 1 for r in abs_rows[0]["regions"])
    report("G8 the absence check is re-derivable: both regions resolve, every registered token and numeric form is "
           "absent, and the loop phrase is present once",
           abs_ok, "hits %s + %s | probe %s | regions %s"
           % (abs_rows[0]["token_hits_total"] if abs_rows else "?",
              abs_rows[0]["numeric_hits_total"] if abs_rows else "?",
              abs_rows[0]["probe_occurrences_in_A2_BODY"] if abs_rows else "?",
              [(r["start_occurrences"], r["end_occurrences"]) for r in abs_rows[0]["regions"]] if abs_rows else "?"))
    probes = []
    for meta_p, rows, want in [
        ({"record": "MISSING"}, [], "REPRESENTATION_SOURCE_MISSING"),
        ({"record": "EXTRACTED", "pdf_sha256": "0" * 64, "pdf_bytes": C.PDF_BYTES}, [], "REPRESENTATION_SOURCE_MISMATCH"),
        ({"record": "EXTRACTED", "pdf_sha256": C.PDF_SHA, "pdf_bytes": C.PDF_BYTES},
         [{"id": "R-1", "status": "UNLOCATABLE"}], "REPRESENTATION_PARTIAL"),
        ({"record": "EXTRACTED", "pdf_sha256": C.PDF_SHA, "pdf_bytes": C.PDF_BYTES},
         [{"id": "R-1", "status": "STATED"}], "REPRESENTATION_CODED"),
        ({"record": "EXTRACTED", "pdf_sha256": C.PDF_SHA, "pdf_bytes": C.PDF_BYTES},
         [{"id": "R-1", "status": "STATED"}, {"id": "R-5", "status": "NOT_STATED"}], "REPRESENTATION_CODED"),
    ]:
        got = C.exit_of(meta_p, {"items": rows, "unlocatable": [r["id"] for r in rows if r["status"] == "UNLOCATABLE"]})
        probes.append(got[0])
    report("G9 all four registered exits are reachable and no fifth exit can be constructed",
           probes == ["REPRESENTATION_SOURCE_MISSING", "REPRESENTATION_SOURCE_MISMATCH",
                      "REPRESENTATION_PARTIAL", "REPRESENTATION_CODED", "REPRESENTATION_CODED"]
           and set(C.EXITS) == {"REPRESENTATION_CODED", "REPRESENTATION_PARTIAL",
                                "REPRESENTATION_SOURCE_MISMATCH", "REPRESENTATION_SOURCE_MISSING"},
           "probes %s" % (probes,))
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "addendum.md"
        tmp.write_bytes(PREREG.read_bytes() + b"\n")
        barrier = C.bind(tmp)
        ordering = RUNNER.read_text(encoding="utf-8")
        report("G11 the write barrier rejects a binding mismatch and sits before the write",
               barrier["two_channel_match"] is False and C.would_write(barrier) is False
               and C.would_write(binding) is True
               and ordering.index("binding MISMATCH") < ordering.index("OUT.write_text"),
               "tampered disk %s git %s" % (barrier["disk_sha256"][:16], barrier["git_head_sha256"] or "absent"))
    again = C.code(text2)
    report("G12 coding is deterministic: two extractions produce identical rows",
           json.dumps(coded, sort_keys=True) == json.dumps(again, sort_keys=True),
           "items %d" % len(coded["items"]))
    if not PRE:
        if art is None:
            report("G10 the artifact's summary equals the rows it summarises", False, "artifact absent: " + ART.name)
        else:
            rows = art.get("items", [])
            stated = [r["id"] for r in rows if r.get("status") == "STATED"]
            gaps = [r["id"] for r in rows if r.get("status") == "NOT_STATED"]
            unl = [r["id"] for r in rows if r.get("status") == "UNLOCATABLE"]
            s = art.get("summary", {})
            report("G10 the artifact's summary equals the rows it summarises",
                   s.get("items") == len(rows) and s.get("stated") == len(stated)
                   and s.get("not_stated") == len(gaps) and s.get("unlocatable") == len(unl)
                   and s.get("stated_ids") == stated and s.get("not_stated_ids") == gaps
                   and s.get("unlocatable_ids") == unl and s.get("refuting_items") == gaps,
                   "rows %d stated %d gaps %d unlocatable %d" % (len(rows), len(stated), len(gaps), len(unl)))
        exit_code = art.get("exit") if art else None
        label = art.get("label_r17") if art else None
        recomputed = C.exit_of({"record": "EXTRACTED", "pdf_sha256": art.get("source", {}).get("pdf_sha256"),
                                "pdf_bytes": art.get("source", {}).get("pdf_bytes")},
                               {"items": art.get("items", []),
                                "unlocatable": art.get("summary", {}).get("unlocatable_ids", [])}) if art else None
        report("G13 the artifact's exit and five-value label are re-derived by a second path",
               bool(art) and recomputed == (exit_code, label) and label in C.FIVE
               and art.get("prereg_binding", {}).get("two_channel_match") is True
               and art.get("prereg_sha256") == sha(PREREG.read_bytes())
               and art.get("source", {}).get("text_sha256") == meta.get("text_sha256"),
               "second path %s vs artifact %s (%s)" % (recomputed, exit_code, label))
    rows_for_evidence = art.get("items", []) if (art and not PRE) else coded["items"]
    self_ref = [r["id"] for r in rows_for_evidence
                if ART.name in json.dumps(r, ensure_ascii=False) or "L02_representation_coding.json" in json.dumps(r)]
    located = all(20 <= q.get("chars", 0) <= 400 and q.get("occurrences") == 1
                  and isinstance(q.get("offset"), int)
                  and text[q["offset"]:q["offset"] + q["chars"]] == q["quote"]
                  for r in rows_for_evidence for q in r.get("quotes", []))
    report("G14 every item's evidence is located in the source itself, never in an artifact",
           located and not self_ref and bool(rows_for_evidence),
           "rows %d self-referencing %s" % (len(rows_for_evidence), self_ref or "none"))

    got_ids = [re.match(r"G\d+", tag).group(0) for tag, _ in _verdicts]
    report("SUITE_accounting every rule declared for this mode was recorded exactly once",
           sorted(got_ids) == sorted(RULES) and len(got_ids) == len(set(got_ids)),
           "ids=%d declared=%d pre=%s" % (len(got_ids), len(RULES), PRE))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _, v in _verdicts if v)
           and len(_verdicts) == len(RULES) + 1,
           "recorded=%d passed=%d rules=%d" % (_n, _ok, len(RULES)))
    print("%d/%d checks passed" % (_ok, _n))
    return 0 if _ok == _n else 1


if __name__ == "__main__":
    sys.exit(main())
