"""Round L-03: code the R13-N15 full text against the L-01 abstract-level record.

The preregistration (`literature/L03_PREREGISTRATION.md`) was committed as 77c4bb1 before the body text was
accepted. This module only builds the artifact in memory; `run_L03.py` runs the pre-gate first and writes the
artifact only if the two-channel binding holds. The full text lives outside the repository
(`workshop/_m2a_ft/L03_R13-N15.txt`); the repository keeps only its hash, length and quoted sentences.

Run as a dry-run (no artifact written): `python3 literature/l03_coding.py`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
WORK = REPO.parent
PREREG = LIT / "L03_PREREGISTRATION.md"
L01 = LIT / "L01_coding.json"
TEXT = WORK / "_m2a_ft" / "L03_R13-N15.txt"
ACQ = WORK / "_m2a_ft" / "L03_R13-N15.acquire.json"
OUT = LIT / "L03_coding.json"
FLOOR = 21224
SID = "R13-N15"
PREREG_REL = "m2a/literature/L03_PREREGISTRATION.md"
DOI = "10.1101/2025.10.21.683769"
SURNAMES = ("Senapati", "Treiber", "Waddell")

# The three core rows are exactly L-01's K5/K7/K10. K7 is registered REVISED rather than CONFIRMED because
# the full text replaces the abstract's "discrete phase-reversed switch, not a gradual decline" with a rapid
# decline within 120 min and a 24 h choice driven by a parallel safety memory for CS-. The direction and the
# consolidation-window dependence are retained; the temporal shape and the scope of "avoidance" differ.
MECHANISMS = [
    {
        "k": "K5",
        "core_class": "CORE",
        "role": "primary",
        "d_axis": "D−",
        "v_axis": "B-",
        "relation": "CONFIRMED",
        "claim": "Delayed post-ingestive reinforcement is credited back to earlier odor memories by updating "
                 "them during the consolidation window: the sugar reward memory for the toxin-paired odor is "
                 "cancelled by the delayed post-ingestive aversive reinforcement while the memory is still "
                 "labile.",
        "quote": "This SA memory timeline is consistent with flies forming a sugar reward memory that is "
                 "cancelled by delayed post-ingestive aversive reinforcement.",
        "search_terms": ["credit assignment", "delayed", "post-ingestive", "consolidation", "update"],
        "note": "The full text supports the credit-assignment/updating mechanism and its consolidation-window "
                "timing. The abstract's phrase 'turns approach into avoidance' is not counted as part of K5 "
                "here; the full text's behavioural qualification of that phrase is recorded under K7's REVISED "
                "difference.",
    },
    {
        "k": "K7",
        "core_class": "CORE",
        "role": "auxiliary",
        "d_axis": "D−",
        "v_axis": "B-",
        "relation": "REVISED",
        "claim": "The same training first produces conditioned approach and later a relative avoidance of the "
                 "food-paired odor. The full text reports a rapid decline within 120 min followed by conversion "
                 "to avoidance by 6 h, and attributes the 24 h choice to a parallel safety memory for the "
                 "non-food odor rather than to an absolute aversive memory of CS+.",
        "quote": "In contrast, SA trained flies initially showed strong approach to the previously food-paired "
                 "odor which rapidly declined within the first 120 min after training and converted to "
                 "avoidance by 6 h that persisted for at least 24 h.",
        "supporting_quote": "24 h after training behavior appears to be solely directed by a safety memory for "
                            "the non-food paired odor – no CS+ approach or avoidance was evident at this time.",
        "search_terms": ["switch", "switches", "reversal", "avoidance", "approach", "consolidation"],
        "difference": "L-01 describes a discrete phase-reversed switch, explicitly 'not a gradual decline', "
                      "whose direction is an absolute switch of the CS+ response to avoidance. The full text "
                      "reports a rapid decline of CS+ approach within the first 120 min and conversion to "
                      "avoidance by 6 h in the CS+ vs CS- choice, but a CS+ vs novel-odor test shows no "
                      "preference by 2 h, and the 24 h behaviour is attributed to a safety memory for CS-: "
                      "'no CS+ approach or avoidance was evident at this time'. The approach-to-relative-"
                      "avoidance direction and the consolidation-window dependence are retained; the temporal "
                      "shape and the scope of the avoidance differ.",
        "retained": "approach-to-relative-avoidance direction and consolidation-window dependence",
    },
    {
        "k": "K10",
        "core_class": "CORE",
        "role": "auxiliary",
        "d_axis": "D+",
        "v_axis": "B+",
        "relation": "CONFIRMED",
        "claim": "The malaise signal suppresses consolidation of the initial odor-sugar memory and forms a "
                 "parallel safety memory for the odor experienced without food, through serotonergic modulation "
                 "of distinct dopaminergic subtypes. Full text: DPM output 15-30 min after training is required "
                 "for both the suppression and the CS- approach memory.",
        "quote": "The DPM blocking experiments therefore demonstrate that 15-30 min after training is a "
                 "critical time for malaise information to both suppress sugar-rewarded CS+ approach memory "
                 "and form a CS- approach memory.",
        "search_terms": ["serotonin", "serotonergic", "dopaminergic", "safety", "suppress", "invert"],
        "note": "The full text also identifies the receptor/Toll combinations in specific DAN subtypes; that "
                "detail is carried as an ADDITIONAL K10 entry and does not enter the core counts.",
    },
    {
        "k": "K5",
        "core_class": "ADDITIONAL",
        "role": "additional",
        "d_axis": "D−",
        "v_axis": "B-",
        "relation": "CONFIRMED",
        "claim": "DPM-released 5-HT extends the effective inter-stimulus interval after feeding into the "
                 "consolidation window, allowing post-ingestive reinforcement to be integrated.",
        "quote": "Our work here suggests that DPM neuron released 5-HT can extend the effective ISI much "
                 "further after a feeding event into the consolidation window so that post-ingestive "
                 "reinforcement can be integrated.",
        "search_terms": ["credit assignment", "delayed", "post-ingestive", "consolidation", "update"],
        "note": "ADDITIONAL: supports the K5 family's timing claim but is not part of L-01's core set.",
    },
    {
        "k": "K10",
        "core_class": "ADDITIONAL",
        "role": "additional",
        "d_axis": "D+",
        "v_axis": "B+",
        "relation": "CONFIRMED",
        "claim": "Specific 5-HT receptor and Toll combinations in PAM-γ3, PAM-β'2mp and PAM-γ5 DANs are "
                 "required for the 24 h CS- approach memory.",
        "quote": "Development of 24 h CS- approach required excitatory 5-HT7 receptors in PAM-γ3, 5-HT7 and "
                 "Toll-6 in PAM-β'2mp, and inhibitory 5-HT1A and Toll-1 in PAM-γ5 DANs.",
        "search_terms": ["serotonin", "serotonergic", "dopaminergic", "safety", "suppress", "invert"],
        "note": "ADDITIONAL: subtype-level support for K10, not part of L-01's core set.",
    },
]

RELATIONS = ("CONFIRMED", "REVISED", "UNSUPPORTED", "REFUTED")
LABELS = {"FULLTEXT_CONFIRMS": "SUPPORTED", "FULLTEXT_REVISES": "INDETERMINATE",
          "FULLTEXT_PARTIAL": "NOT_IDENTIFIED", "FULLTEXT_REFUTES": "CONTRADICTED",
          "FULLTEXT_BELOW_FLOOR": "NOT_IDENTIFIED", "FULLTEXT_IDENTITY_MISMATCH": "NOT_IDENTIFIED",
          "FULLTEXT_NOT_OBTAINED": "NULL"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha16(s: str) -> str:
    return sha(s.encode("utf-8"))[:16]


def tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())}


def normalize_title(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    return s.strip(" \t.,;:!?\"'“”‘’()[]")


def git_show(rel: str) -> bytes:
    p = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("git show failed for %s: %s" % (rel, p.stderr.decode("utf-8", "replace")[:120]))
    return p.stdout


def identity_check(text: str, registered_title: str) -> dict:
    norm = normalize_title(registered_title)
    title_line = ""
    for line in text.split("\n")[:60]:
        if normalize_title(line) == norm:
            title_line = line.strip()
            break
    doi_in_text = DOI in text
    surnames = {n: (n.lower() in text.lower()) for n in SURNAMES}
    t_reg, t_line = tokens(registered_title), tokens(title_line)
    overlap = round(len(t_reg & t_line) / len(t_reg | t_line), 4) if t_reg and t_line else 0.0
    all_pass = bool(title_line) and doi_in_text and all(surnames.values())
    return {"registered_title": registered_title, "title_in_text": title_line,
            "title_equal_after_normalization": bool(title_line), "doi": DOI, "doi_in_text": doi_in_text,
            "surnames": surnames, "overlap": overlap, "all_pass": all_pass}


def locate(text: str, quote: str) -> dict:
    if not isinstance(quote, str) or not 20 <= len(quote) <= 400:
        raise ValueError("quote length outside 20-400: %r" % (quote[:40],))
    n = text.count(quote)
    if n != 1:
        raise ValueError("quote occurs %d times, expected exactly 1: %r" % (n, quote[:40]))
    return {"quote_offset": text.index(quote), "quote_sha16": sha16(quote), "quote_chars": len(quote)}


def search_hits(text: str, terms: list[str]) -> dict[str, int]:
    low = text.lower()
    return {t: low.count(t.lower()) for t in terms}


def exit_for(c: int, r: int, u: int, f: int, *, obtained: bool = True, identity_ok: bool = True,
             chars: int = 0, quotes_ok: bool = True) -> tuple[str, str]:
    if min(c, r, u, f) < 0 or c + r + u + f != 3:
        raise ValueError("core relation counts must be non-negative and sum to 3: %r" % ((c, r, u, f),))
    if not obtained:
        return "FULLTEXT_NOT_OBTAINED", LABELS["FULLTEXT_NOT_OBTAINED"]
    if not identity_ok:
        return "FULLTEXT_IDENTITY_MISMATCH", LABELS["FULLTEXT_IDENTITY_MISMATCH"]
    if chars < FLOOR or not quotes_ok:
        return "FULLTEXT_BELOW_FLOOR", LABELS["FULLTEXT_BELOW_FLOOR"]
    if f >= 1:
        return "FULLTEXT_REFUTES", LABELS["FULLTEXT_REFUTES"]
    if r >= 1:
        return "FULLTEXT_REVISES", LABELS["FULLTEXT_REVISES"]
    if u >= 1:
        return "FULLTEXT_PARTIAL", LABELS["FULLTEXT_PARTIAL"]
    if c == 3:
        return "FULLTEXT_CONFIRMS", LABELS["FULLTEXT_CONFIRMS"]
    raise ValueError("no registered exit matches counts %r" % ((c, r, u, f),))


def build(text: str, acq: dict, prereg_disk: bytes, prereg_git: bytes) -> dict:
    if acq.get("accepted") is not True:
        raise ValueError("acquisition sidecar is not accepted")
    if acq.get("chars") != len(text) or acq.get("bytes") != len(text.encode("utf-8")):
        raise ValueError("sidecar length does not match the text")
    if acq.get("text_sha256") != sha(text.encode("utf-8")):
        raise ValueError("sidecar hash does not match the text")
    l01 = json.loads(L01.read_text(encoding="utf-8"))["records"][SID]
    ident = identity_check(text, l01["title"])

    entries = []
    for spec in MECHANISMS:
        e = dict(spec)
        e.update(locate(text, spec["quote"]))
        if spec.get("supporting_quote"):
            sup = locate(text, spec["supporting_quote"])
            e["supporting_quote_offset"] = sup["quote_offset"]
            e["supporting_quote_sha16"] = sup["quote_sha16"]
            e["supporting_quote_chars"] = sup["quote_chars"]
        e["search_hits"] = search_hits(text, spec["search_terms"])
        entries.append(e)

    core = [e for e in entries if e["core_class"] == "CORE"]
    additional = [e for e in entries if e["core_class"] == "ADDITIONAL"]
    if sorted(e["k"] for e in core) != ["K10", "K5", "K7"]:
        raise ValueError("core set is not exactly K5/K7/K10")
    c = sum(e["relation"] == "CONFIRMED" for e in core)
    r = sum(e["relation"] == "REVISED" for e in core)
    u = sum(e["relation"] == "UNSUPPORTED" for e in core)
    f = sum(e["relation"] == "REFUTED" for e in core)
    exit_q1, label = exit_for(c, r, u, f, obtained=True, identity_ok=ident["all_pass"], chars=len(text),
                              quotes_ok=True)
    primary_lens = [len(e["quote"]) for e in entries]
    supporting_lens = [len(e["supporting_quote"]) for e in entries if e.get("supporting_quote")]
    all_lens = primary_lens + supporting_lens
    headings = ["Abstract", "Introduction", "Results", "Discussion", "Methods", "References"]
    record = {
        "case_id": SID,
        "sid": SID,
        "reference": l01["title"],
        "title": l01["title"],
        "year": l01["year"],
        "verification_level": "FULLTEXT_REVIEWED",
        "identity_check": "Full text retrieved from Europe PMC (PPR1106376) contains DOI %s, the title line "
                          "%r (normalized equality), and the surnames %s; all three identity criteria pass."
                          % (DOI, ident["title_in_text"], "/".join(SURNAMES)),
        "evidence_type": l01["evidence_type"],
        "provenance": "PAPER_CLAIM",
        "term_type": "PAPER_TERM",
        "mapping_note": "term_type PAPER_TERM: the full text uses the mechanism words mapped here - delayed "
                        "post-ingestive reinforcement/cancellation (K5), the approach-to-relative-avoidance "
                        "switch (K7), and serotonergic suppression plus safety memory (K10). Our contribution "
                        "is only the family labels and the CONFIRMED/REVISED comparison.",
        "description_scope": l01["description_scope"],
        "motion_source": l01["motion_source"],
        "mechanism": entries,
        "d_class": l01["d_class"],
        "agency_class": l01["agency_class"],
        "event_grammar": l01["event_grammar"],
        "contradiction_ref": None,
        "anchor_concordance": l01["anchor_concordance"],
        "notes": "Level FULLTEXT_REVIEWED: the normalized Europe PMC body is %d characters, above the "
                 "registered floor of %d. The preprint was posted 2025-10-22 and is not peer reviewed; the "
                 "supplementary figures were not independently coded. The L-01 record is untouched: this is a "
                 "new, parallel record. K7 is REVISED because the full text reports a rapid decline and a "
                 "CS- safety-memory account rather than a discrete absolute switch to CS+ avoidance; K5 and "
                 "K10 are CONFIRMED at the mechanism-family level."
                 % (len(text), FLOOR),
        "layers": l01["layers"],
        "layers_provenance": l01["layers_provenance"],
    }
    differences = [{"k": e["k"], "l01_claim": {m["k"]: m for m in l01["mechanism"]}[e["k"]]["claim"],
                    "fulltext_claim": e["claim"], "difference": e["difference"],
                    "retained": e["retained"]}
                   for e in core if e["relation"] == "REVISED"]
    closed = exit_q1 in ("FULLTEXT_CONFIRMS", "FULLTEXT_REVISES", "FULLTEXT_PARTIAL", "FULLTEXT_REFUTES")
    return {
        "schema": "m2a.literature.round_l03.v1",
        "round": "L-03",
        "sid": SID,
        "preregistration": {"path": "literature/L03_PREREGISTRATION.md", "commit": "77c4bb1",
                            "sha256": sha(prereg_disk)},
        "prereg_sha256": sha(prereg_disk),
        "prereg_binding": {"disk_sha256": sha(prereg_disk), "git_sha256": sha(prereg_git),
                           "git_ref": "HEAD:" + PREREG_REL, "match": sha(prereg_disk) == sha(prereg_git)},
        "reference": {"sid": SID, "title": l01["title"], "year": l01["year"], "doi": DOI,
                      "authors": ["Bhagyashree Senapati", "Christoph D. Treiber", "Scott Waddell"],
                      "posted": "2025-10-22", "peer_reviewed": False},
        "identity": ident,
        "obtain_attempts": acq.get("attempts") or [],
        "acquisition": acq,
        "fulltext": {
            "file": str(TEXT), "outside_repository": True, "chars": len(text),
            "bytes": len(text.encode("utf-8")), "text_sha256": sha(text.encode("utf-8")),
            "verification_level": "FULLTEXT_REVIEWED", "floor_derived": FLOOR,
            "above_floor": len(text) >= FLOOR,
            "headings_checked": headings,
            "headings_present": [h for h in headings if h in text],
            "normalization_checks": {"no_cr": "\r" not in text,
                                     "no_trailing_whitespace": all(ln == ln.rstrip() for ln in text.split("\n")),
                                     "no_triple_newline": "\n\n\n" not in text},
        },
        "record": record,
        "counts": {
            "core_total": len(core), "confirmed": c, "revised": r, "unsupported": u, "refuted": f,
            "additional": len(additional), "mechanism_total": len(entries),
            "quotes_primary": len(primary_lens), "quotes_supporting": len(supporting_lens),
            "quotes_total": len(all_lens), "quote_chars_min": min(all_lens), "quote_chars_max": max(all_lens),
            "fulltext_chars": len(text), "floor": FLOOR, "above_floor": len(text) >= FLOOR,
        },
        "exit_q1": exit_q1,
        "exit_q1_label_r17": label,
        "differences": differences,
        "l01_o5": {"status": "CLOSED" if closed else "OPEN",
                   "basis": "exit %s closes L01-O5 as 'full text retrieved and coded under the registered "
                            "criteria'; the L-01 record and level are not rewritten" % exit_q1},
        "l03_o1": ({"status": "OPEN",
                    "reason": "exit %s means the full-text coding differs from the abstract-level record; the "
                              "difference is recorded here and in ROUND_L03_RESULTS.md, not written back to "
                              "L-01" % exit_q1}
                   if exit_q1 in ("FULLTEXT_REVISES", "FULLTEXT_PARTIAL", "FULLTEXT_REFUTES")
                   else {"status": "NONE"}),
        "stop_rule": "prereg 5: exits 5/6/7 halt without coding; exits 1-4 close L01-O5; exits 2/3/4 open "
                     "L03-O1; no write-back to L-01.",
        "asymmetry": "prereg 6: confirmation is internal to one preprint (abstract-level vs full-text-level "
                     "coding); it does not establish the paper's mechanism, upgrade the preprint to peer "
                     "review, or code the supplementary figures.",
        "amendments": [
            {"id": "L03-A1", "when": "before coding", "what": "the acquisition sidecar's `attempts` field was "
             "null; the five channel readings (C1 CLI 429, C2 403, C3 browser ERR_FAILED, C4 429, C1 browser "
             "200) were added before any coding reading", "effect": "the text hash, character count and all "
             "registered criteria are unchanged; rule 1's two C1 readings are now recorded"}
        ],
        "generator": {"name": "literature/l03_coding.py", "sha256": sha(pathlib.Path(__file__).read_bytes())},
    }


def digest(art: dict) -> str:
    return sha(json.dumps(art, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))[:16]


def main() -> int:
    text = TEXT.read_text(encoding="utf-8")
    acq = json.loads(ACQ.read_text(encoding="utf-8"))
    art = build(text, acq, PREREG.read_bytes(), git_show(PREREG_REL))
    print("L03 dry-run: exit %s | label %s | core c=%d r=%d u=%d f=%d | additional %d | quotes %d | "
          "chars %d | digest %s"
          % (art["exit_q1"], art["exit_q1_label_r17"], art["counts"]["confirmed"], art["counts"]["revised"],
             art["counts"]["unsupported"], art["counts"]["refuted"], art["counts"]["additional"],
             art["counts"]["quotes_total"], art["counts"]["fulltext_chars"], digest(art)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
