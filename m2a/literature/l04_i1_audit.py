"""Round L-04: paper-level audit of I1's evidence chain over the 17 committed L-01 rows.

I1 claims that omission is a conjunction of S (selective non-response) and C (counterfactual
availability representation). Reviewer 2's R2-M1 is that the evidence mixes a 21-paper full-text
review population with I1-specific support and never gives a paper-level denominator. This round
re-codes only the 17 committed rows, one code per row, from the committed `claim`/`quote` text.
No new text is fetched and no existing artifact is modified.

Run from anywhere: `python3 literature/l04_i1_audit.py [--check]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L04_PREREGISTRATION.md"
L01 = LIT / "L01_coding.json"
FULLTEXTS = LIT / "fulltext_review.json"
OUT = LIT / "L04_I1_AUDIT.json"
CODES = {"S_ONLY", "C_ONLY", "S_PLUS_C", "NEITHER", "UNDECIDABLE"}
EXITS = ("I1_CONJUNCTION_OBSERVED", "I1_LAYERS_SEPARABLE", "I1_CONJUNCTION_NOT_OBSERVED",
         "I1_EVIDENCE_INSUFFICIENT", "I1_AUDIT_INVALID")

# One code per committed row. The rationale and the mechanism keys are the audit trail; the gate
# checks that every listed key exists in that row and that the code vocabulary is closed.
CODED: dict[str, dict] = {
    "G5-03-N1": {"code": "NEITHER", "evidence_k": ["K1"],
                 "rationale": "Trigger and cross-domain misalignment only; no omission or availability claim."},
    "G5-03-N2": {"code": "NEITHER", "evidence_k": ["K2"],
                 "rationale": "Intent-gated refusal, not selective non-response or a representation of skipped options."},
    "G5-03-N4": {"code": "S_ONLY", "evidence_k": ["K9"],
                 "rationale": "Reasoned abstention with a confidence threshold; no description of representing the skipped answer."},
    "G5-03-N6": {"code": "NEITHER", "evidence_k": ["K2"],
                 "rationale": "Refusal representation and multi-dimensional gate; neither omission nor availability of omitted options."},
    "G5-03": {"code": "NEITHER", "evidence_k": ["K2"],
              "rationale": "A single necessary-and-sufficient refusal direction; not an omission claim."},
    "R13-N15": {"code": "NEITHER", "evidence_k": ["K5"],
                "rationale": "Delayed reinforcement and phase-reversed switch; not omission or counterfactual availability."},
    "R13-N16": {"code": "NEITHER", "evidence_k": ["K2"],
                "rationale": "GIPR suppression of inflammation-derived aversion is a gate, not omission."},
    "R13-N17": {"code": "NEITHER", "evidence_k": ["K11"],
                "rationale": "Motivational intensity and effort; no selective non-response or availability representation."},
    "R13-N2": {"code": "S_PLUS_C", "evidence_k": ["K2", "K5"],
               "rationale": "Feeding is stopped by cell-type-specific gates (S) and novel flavours activate/reactivate amygdala representations (C)."},
    "R13-N3": {"code": "C_ONLY", "evidence_k": ["K5"],
               "rationale": "Predictive allostatic model (C); no selective non-response is described."},
    "R13-N8": {"code": "S_PLUS_C", "evidence_k": ["K6", "K5"],
               "rationale": "Restrictive eating/abstention is self-reinforcing (S) and the amygdala is experience-driven and represents food cues (C)."},
    "R13": {"code": "S_PLUS_C", "evidence_k": ["K2", "K5"],
            "rationale": "Novelty gates the delayed signal (S) and malaise reactivates neural representations of novel flavours (C)."},
    "R14-N1": {"code": "NEITHER", "evidence_k": ["K2"],
               "rationale": "Dopamine contingency tracking; not an omission or availability claim."},
    "R14-N4": {"code": "NEITHER", "evidence_k": ["K5"],
               "rationale": "Statistical analysis of within-trial signals; not omission."},
    "R14-N7": {"code": "NEITHER", "evidence_k": ["K5"],
               "rationale": "Learning rate as a function of temporal separation; not omission."},
    "R14-N8": {"code": "NEITHER", "evidence_k": ["K5"],
               "rationale": "Dopamine ramps and intertrial interval; not omission."},
    "R14": {"code": "NEITHER", "evidence_k": ["K5"],
            "rationale": "Reward duration sets the learning rate; not omission or counterfactual availability."},
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


def counts_of(rows: list[dict]) -> dict:
    n = {k: sum(1 for r in rows if r["code"] == k) for k in
         ("S_ONLY", "C_ONLY", "S_PLUS_C", "NEITHER", "UNDECIDABLE")}
    n["rows"] = len(rows)
    n["i1_relevant"] = n["S_ONLY"] + n["C_ONLY"] + n["S_PLUS_C"]
    return n


def exit_of(c: dict, invalid: bool = False) -> tuple[str, str]:
    if invalid:
        return "I1_AUDIT_INVALID", "NULL"
    if c["S_PLUS_C"] >= 1 and c["S_ONLY"] == 0 and c["C_ONLY"] == 0:
        return "I1_CONJUNCTION_OBSERVED", "SUPPORTED"
    if c["S_PLUS_C"] >= 1 and (c["S_ONLY"] >= 1 or c["C_ONLY"] >= 1):
        return "I1_LAYERS_SEPARABLE", "INDETERMINATE"
    if c["S_PLUS_C"] == 0 and c["i1_relevant"] >= 3:
        return "I1_CONJUNCTION_NOT_OBSERVED", "REFUTED"
    return "I1_EVIDENCE_INSUFFICIENT", "NOT_IDENTIFIED"


def build() -> dict:
    l01 = json.loads(L01.read_text(encoding="utf-8"))["records"]
    ft = json.loads(FULLTEXTS.read_text(encoding="utf-8"))["records"]
    missing = sorted(set(l01) - set(CODED))
    extra = sorted(set(CODED) - set(l01))
    rows, defects = [], []
    for sid, spec in CODED.items():
        rec = l01.get(sid)
        if rec is None:
            defects.append("missing:%s" % sid)
            continue
        mechs = {m.get("k"): m for m in rec.get("mechanism", [])}
        ks = spec["evidence_k"]
        bad_k = [k for k in ks if k not in mechs]
        if bad_k:
            defects.append("evidence_k:%s:%s" % (sid, bad_k))
        if spec["code"] not in CODES:
            defects.append("code:%s:%s" % (sid, spec["code"]))
        first = mechs.get(ks[0], {}) if ks else {}
        rows.append({"sid": sid, "code": spec["code"], "rationale": spec["rationale"],
                     "evidence_k": ks, "claim_excerpt": (first.get("claim") or "")[:160],
                     "quote_sha16": sha((first.get("quote") or "").encode("utf-8"))[:16] if first else "",
                     "quote_chars": len(first.get("quote") or "")})
    c = counts_of(rows)
    exit_code, label = exit_of(c, invalid=bool(defects or missing or extra))
    return {
        "schema": "m2a.roundL04.i1audit.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
        "prereg_binding": bind(),
        "source": {"l01": str(L01.relative_to(M)), "l01_sha256": sha(L01.read_bytes()),
                   "fulltext_review": str(FULLTEXTS.relative_to(M)),
                   "fulltext_review_records": len(ft),
                   "denominator_is_i1_specific": False},
        "rows": rows, "counts": c,
        "missing_rows": missing, "extra_rows": extra, "defects": defects,
        "exit": exit_code, "label_r17": label,
        "zero_test_status": "reanalysis_only: cannot confirm I1; only refute or narrow it",
        "single_coder": True,
        "no_new_data": True,
        "boundary": "17 committed L-01 rows; the 21-record full-text review population is not an I1 denominator; "
                    "no second coder; non-constructive S-only arm not run",
    }


def main() -> int:
    pre = subprocess.run([sys.executable, str(LIT / "l04_i1_gate.py"), "--pre"],
                         capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | rows %d | S %d C %d SC %d neither %d | binding match"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"], doc["counts"]["rows"],
                 doc["counts"]["S_ONLY"], doc["counts"]["C_ONLY"], doc["counts"]["S_PLUS_C"],
                 doc["counts"]["NEITHER"]))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    print("wrote %s | exit %s (%s) | rows %d | S %d C %d SC %d neither %d | binding match"
          % (OUT.name, doc["exit"], doc["label_r17"], doc["counts"]["rows"],
             doc["counts"]["S_ONLY"], doc["counts"]["C_ONLY"], doc["counts"]["S_PLUS_C"],
             doc["counts"]["NEITHER"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
