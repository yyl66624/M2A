"""L-02 representation addendum: code the representation-layer definitions recovered from the PDF.

`L02-O2` was left open because the HTML extraction used by Round L-02 dropped inline math, so the cone's
dimension and RCO's convergence condition were never coded (`ROUND_L02_RESULTS.md` §5/§8). This instrument
re-extracts the same paper from the hash-pinned PDF in reading order, freezes the quotation and absence rules
in `L02_REPRESENTATION_ADDENDUM.md`, and emits one row per registered definitional item.

It writes only after the addendum's SHA-256 agrees on two channels - the bytes on disk and the `git show HEAD:`
object - because an artifact that claims a binding it does not carry is the defect `L02-A6` already registered
once in this round family. `--check` prints the digest and writes nothing.

Run from anywhere: `python3 literature/l02_representation_coding.py [--check]`.
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
PREREG = LIT / "L02_REPRESENTATION_ADDENDUM.md"
OUT = LIT / "L02_representation_coding.json"
PDF = REPO.parent / "_m2a_ft" / "L02_C-04_v2.pdf"
PDF_SHA = "998a608e506b286ddb047996add9eb86aeca51afa36f3eba125089607249d534"
PDF_BYTES = 3261118
EXTRACTOR = "pdftotext -raw"
NORMALIZATION = "CRLF/CR folded to LF; '-\\n' at a word break removed; whitespace collapsed; ends stripped"
FIVE = ("SUPPORTED", "REFUTED", "NULL", "INDETERMINATE", "NOT_IDENTIFIED")
EXITS = ("REPRESENTATION_CODED", "REPRESENTATION_PARTIAL",
         "REPRESENTATION_SOURCE_MISMATCH", "REPRESENTATION_SOURCE_MISSING")
FROZEN = {"literature/L02_PREREGISTRATION.md": None, "literature/L02_coding.json": None}

# Each quote was read off the normalised text. The contract is mechanical: 20-400 characters, present exactly
# once, offset and sha16 checkable. A quote that fails any of those is an instrument defect, never a finding.
ITEMS: list[dict] = [
    {"id": "R-1", "criterion": "cone definition and the concept-cone identity",
     "kind": "quote", "quotes": [
         "For this, we optimize an orthonormal basis B = [b1, . . . , bN ] spanning an N-dimensional "
         "polyhedral cone RN = { PN i=1 λibi | λi ≥ 0}\\{0}, where all directions r ∈ RN satisfy the "
         "refusal properties (Theorem 4.1).",
         "Since all directions in the cone correspond to the same refusal concept, we also refer to this as "
         "a concept cone."]},
    {"id": "R-2", "criterion": "observed cone dimensionality (up to five; plateau at four)",
     "kind": "quote", "quotes": [
         "we identify refusal–mediating cones with dimensions up to five across all tested models.",
         "Figure 19 reveals that ASR increases with cone dimensionality but plateaus at four dimensions."]},
    {"id": "R-3", "criterion": "RCO projects the basis back with Gram-Schmidt",
     "kind": "quote", "quotes": [
         "we project the basis back onto the cone using the Gram–Schmidt orthogonalization procedure"]},
    {"id": "R-4", "criterion": "Representational Independence, Definition 6.1",
     "kind": "quote", "quotes": [
         "Definition 6.1. The directions λ, µ ∈ Rd are representationally independent (under directional "
         "ablation) with respect to the activations x of a model in a set of layers l ∈ L if:"]},
    {"id": "R-5", "criterion": "explicit RCO convergence criterion", "kind": "absence",
     "regions": [
         {"name": "A2_BODY", "start": "Algorithm 2 Refusal Cone Optimization (RCO)",
          "end": "1: function SAMPLE(B)"},
         {"name": "A2_PROSE", "start": "In Algorithm 2, we describe the procedure",
          "end": "Can we find refusal concept cones?"},
     ],
     "tokens": ["tol", "tolerance", "threshold", "patience", "max_iter", "max iter", "max-iter",
                "epsilon", "convergence criterion", "stopping criterion", "relative change",
                "gradient norm"],
     "probe_phrase": "while not converged do"},
    {"id": "R-6", "criterion": "orthogonality does not guarantee independence",
     "kind": "quote", "quotes": [
         "This effect is reciprocal, suggesting that orthogonality alone does not guarantee independence "
         "throughout the network."]},
]

NUMERIC_CRITERION = re.compile(r"\b\d+(?:\.\d+)?\s*(?:e-?\d+|%)\b|\b10\s*\^?\s*-?\s*\d+\b", re.I)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"-\n(?=\w)", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract() -> tuple[str, dict]:
    """Re-extract from the PDF every run, so the text the codes hit is the text the pinned file yields."""
    if not PDF.exists():
        return "", {"record": "MISSING", "file": str(PDF)}
    st = subprocess.run([EXTRACTOR.split()[0], "-raw", str(PDF), "-"], capture_output=True)
    meta = {"record": "EXTRACTED", "file": str(PDF), "extractor": EXTRACTOR,
            "extractor_version": subprocess.run(["pdftotext", "-v"], capture_output=True,
                                                text=True).stderr.splitlines()[0].strip(),
            "pdf_bytes": PDF.stat().st_size, "pdf_sha256": sha(PDF.read_bytes()),
            "normalization": NORMALIZATION, "outside_repository": True,
            "returncode": st.returncode}
    if st.returncode != 0:
        meta["record"] = "EXTRACTION_FAILED"
        return "", meta
    text = norm(st.stdout.decode("utf-8", "replace"))
    meta.update({"text_chars": len(text), "text_sha256": sha(text.encode("utf-8"))})
    return text, meta


def git_head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def bind(prereg: pathlib.Path = PREREG) -> dict:
    rel = str(prereg.resolve().relative_to(REPO)) if prereg.resolve().is_relative_to(REPO) else ""
    disk = prereg.read_bytes() if prereg.exists() else b""
    head = git_head_bytes(rel) if rel else b""
    return {"path": rel, "disk_sha256": sha(disk) if disk else "",
            "git_head_sha256": sha(head) if head else "",
            "two_channel_match": bool(disk) and sha(disk) == sha(head)}


def code(text: str) -> dict:
    items, unlocatable = [], []
    for spec in ITEMS:
        row = {"id": spec["id"], "criterion": spec["criterion"], "kind": spec["kind"]}
        if spec["kind"] == "quote":
            quotes = []
            for q in spec["quotes"]:
                n = text.count(q)
                quotes.append({"quote": q, "chars": len(q), "occurrences": n,
                               "offset": text.index(q) if n == 1 else None,
                               "quote_sha16": sha(q.encode("utf-8"))[:16],
                               "in_contract": 20 <= len(q) <= 400})
            ok = all(x["occurrences"] == 1 and x["in_contract"] for x in quotes)
            row.update({"status": "STATED" if ok else "UNLOCATABLE", "quotes": quotes})
            if not ok:
                unlocatable.append(spec["id"])
        else:
            regions, hits_total, numeric_total, markers_ok = [], 0, 0, True
            for rg in spec["regions"]:
                s_n, e_n = text.count(rg["start"]), text.count(rg["end"])
                block = ""
                if s_n == 1 and e_n == 1:
                    start = text.index(rg["start"])
                    block = text[start:text.index(rg["end"], start)]
                else:
                    markers_ok = False
                hits = {tok: len(re.findall(r"\b" + re.escape(tok) + r"\b", block, re.I))
                        for tok in spec["tokens"]}
                numeric = NUMERIC_CRITERION.findall(block)
                hits_total += sum(hits.values())
                numeric_total += len(numeric)
                regions.append({"name": rg["name"], "start": rg["start"], "end": rg["end"],
                                "start_occurrences": s_n, "end_occurrences": e_n,
                                "chars": len(block), "block_sha256": sha(block.encode("utf-8")),
                                "token_hits": hits, "numeric_hits": numeric})
            probe_all = text.count(spec["probe_phrase"])
            probe_body = 0
            if markers_ok:
                _s = text.index(spec["regions"][0]["start"])
                probe_body = text[_s:text.index(spec["regions"][0]["end"], _s)].count(spec["probe_phrase"])
            resolved = markers_ok and probe_body == 1
            row.update({"status": ("NOT_STATED" if hits_total + numeric_total == 0 else "STATED") if resolved
                                  else "UNLOCATABLE",
                        "regions": regions, "token_hits_total": hits_total,
                        "numeric_hits_total": numeric_total,
                        "probe_phrase": spec["probe_phrase"],
                        "probe_occurrences_document": probe_all, "probe_occurrences_in_A2_BODY": probe_body,
                        "decision_rule": "NOT_STATED iff both regions resolve, every registered token and "
                                         "numeric pattern has zero hits, and the loop phrase occurs once in "
                                         "A2_BODY; otherwise STATED or UNLOCATABLE"})
            if not resolved:
                unlocatable.append(spec["id"])
        items.append(row)
    return {"items": items, "unlocatable": unlocatable}


def exit_of(meta: dict, coded: dict) -> tuple[str, str]:
    if meta.get("record") == "MISSING":
        return "REPRESENTATION_SOURCE_MISSING", "NULL"
    if meta.get("pdf_sha256") != PDF_SHA or meta.get("pdf_bytes") != PDF_BYTES:
        return "REPRESENTATION_SOURCE_MISMATCH", "NULL"
    if coded["unlocatable"]:
        return "REPRESENTATION_PARTIAL", "NOT_IDENTIFIED"
    gaps = [r["id"] for r in coded["items"] if r["status"] == "NOT_STATED"]
    return "REPRESENTATION_CODED", "REFUTED" if gaps else "SUPPORTED"


def would_write(binding: dict) -> bool:
    return bool(binding.get("two_channel_match"))


def build() -> dict:
    text, meta = extract()
    coded = code(text)
    binding = bind()
    frozen = {rel: sha((M / rel).read_bytes()) for rel in FROZEN if (M / rel).exists()}
    exit_code, label = exit_of(meta, coded)
    stated = [r["id"] for r in coded["items"] if r["status"] == "STATED"]
    gaps = [r["id"] for r in coded["items"] if r["status"] == "NOT_STATED"]
    tool = pathlib.Path(__file__).resolve()
    doc = {
        "schema": "m2a.roundL02.representation.v1",
        "sid": "C-04",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
        "prereg_binding": binding,
        "source": dict(meta, identity={
            "paper": "The Geometry of Refusal in Large Language Models: Concept Cones and Representational "
                     "Independence",
            "arxiv": "2502.17420v2", "first_author": "Tom Wollschläger"}),
        "frozen_inputs_sha256": frozen,
        "items": coded["items"],
        "summary": {"items": len(coded["items"]), "stated": len(stated), "not_stated": len(gaps),
                    "unlocatable": len(coded["unlocatable"]), "stated_ids": stated,
                    "not_stated_ids": gaps, "unlocatable_ids": coded["unlocatable"],
                    "refuting_items": gaps},
        "exit": exit_code, "label_r17": label,
        "label_derivation": "the conjunctive claim H-R fails if any item is NOT_STATED (REFUTED); all STATED "
                            "would be SUPPORTED; an unresolvable item is an instrument defect and takes exit 2",
        "zero_test_status": "descriptive_only: the text was acquired before the addendum (L02-REP-0), so this "
                            "round can describe the source but cannot confirm any cross-domain claim",
        "instrument_sha256": {str(tool.relative_to(M)): sha(tool.read_bytes())},
        "no_new_experiment": True,
    }
    return doc


def main() -> int:
    gate = LIT / "l02_representation_gate.py"
    pre = subprocess.run([sys.executable, str(gate), "--pre"], capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d) - refusing to write" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH disk %s git %s - refusing to write"
              % (doc["prereg_binding"]["disk_sha256"][:16] or "absent",
                 doc["prereg_binding"]["git_head_sha256"][:16] or "absent"))
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    digest = sha(payload.encode("utf-8"))
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | items %d | stated %d | not_stated %s | text_sha256 %s | "
              "binding match" % (digest[:16], doc["exit"], doc["label_r17"], doc["summary"]["items"],
                                 doc["summary"]["stated"], doc["summary"]["not_stated_ids"] or "none",
                                 doc["source"].get("text_sha256", "")[:16]))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    print("wrote %s | exit %s (%s) | items %d | stated %d | not_stated %s | text_sha256 %s | binding match"
          % (OUT.name, doc["exit"], doc["label_r17"], doc["summary"]["items"], doc["summary"]["stated"],
             doc["summary"]["not_stated_ids"] or "none", doc["source"].get("text_sha256", "")[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
