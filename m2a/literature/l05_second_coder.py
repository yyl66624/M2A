"""Round L-05: two-coder audit of the 21 full-text review population against I1.

The primary codes are frozen here before the second coder's file is read. The second coder works in an
isolated context and writes `scratch/l05_second.md`; this script only parses it and compares. The audit
asks whether the 21-record population is an I1 evidence base at all, not whether I1 is true.

Run from anywhere: `python3 literature/l05_second_coder.py [--check]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L05_PREREGISTRATION.md"
FULLTEXTS = LIT / "fulltext_review.json"
SECOND = REPO.parent / "scratch" / "l05_second.md"
OUT = LIT / "L05_SECOND_CODER.json"
CODES = {"S_ONLY", "C_ONLY", "S_PLUS_C", "NEITHER", "UNDECIDABLE"}
EXITS = ("L05_DENOMINATOR_EMPTY", "L05_DENOMINATOR_NONEMPTY", "L05_PARTIAL_AGREEMENT",
         "L05_SECOND_CODER_MISSING")

# Primary coder, frozen before the second file is read. Strict I1 construct; exclusions in the prereg.
PRIMARY: dict[str, tuple[str, str]] = {
    "R01": ("NEITHER", "FrameNet lexicon construction; no action omission."),
    "R02": ("NEITHER", "AMR omits linguistic phenomena in its guidelines; excluded by the rule."),
    "R05": ("NEITHER", "Thermodynamics review; 'skipped' is reading advice."),
    "R06": ("NEITHER", "Self-replication entropy bound; no omission or availability claim."),
    "R09": ("NEITHER", "T-cell co-stimulation; 'availability' is tryptophan supply."),
    "R13": ("NEITHER", "Delayed postingestive learning; no selective action omission or unchosen-option representation."),
    "R14": ("NEITHER", "Reward omission, explicitly excluded by the rule."),
    "R15": ("NEITHER", "Time-scale invariance; 'availability' is data availability."),
    "R17": ("NEITHER", "Behaviour-change wheel; no omission."),
    "R20": ("NEITHER", "Control barrier functions; 'omit' is expository."),
    "R24": ("NEITHER", "Safety-critical control; no omission."),
    "G6-07": ("NEITHER", "Implementation science; 'availability' is a programme name."),
    "G8-01": ("NEITHER", "PropBank; 'omitted' is table notation."),
    "G8-03": ("NEITHER", "Universal Dependencies; 'omission' is linguistic subject omission, excluded."),
    "G8-04": ("NEITHER", "Annotation survey; 'availability' is corpus availability."),
    "G8-05": ("NEITHER", "Gene Ontology; 'availability' is data access."),
    "G8-08": ("NEITHER", "Narrative event chains; no omission."),
    "X-K4-01": ("NEITHER", "IL-12/B7 synergy in T cells; no omission."),
    "X-K4-02": ("NEITHER", "TLR/CD40 synergy; no omission."),
    "X-K4-05": ("NEITHER", "Biofilm quorum sensing; no omission."),
    "X-K4-07": ("NEITHER", "Coincidence detectors; no omission."),
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_head(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def bind(prereg: pathlib.Path = PREREG) -> dict:
    rel = str(prereg.resolve().relative_to(REPO)) if prereg.resolve().is_relative_to(REPO) else ""
    disk = prereg.read_bytes() if prereg.exists() else b""
    head = git_head(rel)
    return {"path": rel, "disk_sha256": sha(disk) if disk else "",
            "git_head_sha256": sha(head) if head else "",
            "two_channel_match": bool(disk) and sha(disk) == sha(head)}


def parse_second() -> tuple[dict, list[str]]:
    if not SECOND.exists():
        return {}, ["second coder file missing: " + str(SECOND)]
    rows, defects = {}, []
    for line in SECOND.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Za-z0-9\-]+)\s*\|\s*([A-Z_]+)\s*\|\s*(.*?)\s*\|\s*$", line)
        if not m:
            continue
        pid, code, why = m.group(1), m.group(2), m.group(3)
        if pid in ("paper", "---"):
            continue
        if code not in CODES:
            defects.append("code:%s:%s" % (pid, code))
        if pid in rows:
            defects.append("duplicate:" + pid)
        rows[pid] = {"code": code, "rationale": why}
    return rows, defects


def kappa(a: list[str], b: list[str]) -> float | str:
    n = len(a)
    labels = sorted(set(a) | set(b))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(k) / n) * (b.count(k) / n) for k in labels)
    if pe >= 1.0:
        return "UNDEFINED"
    return round((po - pe) / (1 - pe), 4)


def build() -> dict:
    keys = list(json.loads(FULLTEXTS.read_text(encoding="utf-8"))["records"])
    second, defects = parse_second()
    rows = []
    for pid in keys:
        pcode, pwhy = PRIMARY.get(pid, ("UNDECIDABLE", "primary code missing"))
        scode = second.get(pid, {}).get("code")
        rows.append({"paper": pid, "primary": pcode, "primary_rationale": pwhy,
                     "second": scode, "second_rationale": second.get(pid, {}).get("rationale", ""),
                     "agree": scode == pcode})
    matches = sum(1 for r in rows if r["agree"])
    agreement = round(matches / len(rows), 4) if rows else 0.0
    k = kappa([r["primary"] for r in rows], [r["second"] for r in rows]) if second else "UNDEFINED"
    if not second:
        exit_code, label = "L05_SECOND_CODER_MISSING", "NULL"
    elif all(r["primary"] == "NEITHER" and r["second"] == "NEITHER" for r in rows):
        exit_code, label = "L05_DENOMINATOR_EMPTY", "REFUTED"
    elif any(r["agree"] and r["primary"] in ("S_ONLY", "C_ONLY", "S_PLUS_C") for r in rows):
        exit_code, label = "L05_DENOMINATOR_NONEMPTY", "SUPPORTED"
    else:
        exit_code, label = "L05_PARTIAL_AGREEMENT", "INDETERMINATE"
    return {
        "schema": "m2a.roundL05.secondcoder.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
        "prereg_binding": bind(),
        "population": {"source": str(FULLTEXTS.relative_to(M)), "papers": len(keys)},
        "primary_frozen_before_second": True,
        "second_file": {"path": str(SECOND), "exists": SECOND.exists(),
                        "sha256": sha(SECOND.read_bytes()) if SECOND.exists() else ""},
        "rows": rows,
        "agreement": {"matches": matches, "n": len(rows), "raw": agreement,
                      "cohen_kappa": k,
                      "kappa_note": "UNDEFINED means both margins have zero variance; it is not 1.0"},
        "defects": defects, "exit": exit_code, "label_r17": label,
        "single_round": True, "no_new_data": True,
        "boundary": "21 full-text review records; two AI contexts, not two human coders; the result audits the "
                    "population, not I1 itself",
    }


def main() -> int:
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | agree %d/%d kappa %s"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc["agreement"]["matches"], doc["agreement"]["n"], doc["agreement"]["cohen_kappa"]))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    print("wrote %s | exit %s (%s) | agree %d/%d | raw %s | kappa %s"
          % (OUT.name, doc["exit"], doc["label_r17"], doc["agreement"]["matches"],
             doc["agreement"]["n"], doc["agreement"]["raw"], doc["agreement"]["cohen_kappa"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
