"""Round L-02 Q3: obtain, verify the identity of, and code the competing theory registered as C-04.

Prereg §3 Q3, verbatim: exit 1 `COMPETING_CODED` needs (i) identity verified against the title registered in
`L01_channels.json` with token overlap 1.0, (ii) extracted text at least 21 224 characters (the floor L-02 §2.3
derived from L-01's own coded set), and (iii) at least 3 mechanism entries, each carrying a 20-400 character
verbatim quote whose offset and hash are checkable against the extracted file. Otherwise exit 2
`COMPETING_IDENTITY_ONLY` or exit 3 `COMPETING_NOT_OBTAINED` - and an abstract is never passed off as a full
text (L01-O5).

Channel order is disclosed, not hidden: arXiv's own abs page for identity, then arXiv's LaTeXML HTML rendering
for the body. The extracted text is written outside the repository (`workshop/_m2a_ft/`) because third-party
full texts are not committed; only its hash, length and the quoted sentences are. Re-running with the file
present does not touch the network as long as the recorded hash still matches the bytes on disk.

Run from anywhere: `python3 literature/l02_coding.py [--extract]`. `--extract` stops after the text and manifest
are written, before any coding is done.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
PREREG = LIT / "L02_PREREGISTRATION.md"
CHANNELS = LIT / "L01_channels.json"
CODING = LIT / "L01_coding.json"
OUT = LIT / "L02_coding.json"
FT_DIR = pathlib.Path("/media/leonyao/新加卷/workshop/_m2a_ft")
TEXT = FT_DIR / "L02_C-04.txt"
ACQ = FT_DIR / "L02_C-04.acquire.json"
ABS_URL = "https://arxiv.org/abs/2502.17420v2"
HTML_URL = "https://arxiv.org/html/2502.17420v2"
FLOOR = 21224
SID = "C-04"
UA = {"User-Agent": "M2A-literature-coding/1.0 (research, deterministic fetch)"}

# Coded by reading the extracted text. Each entry is a dict with k / role / d_axis / v_axis / quote / anchor /
# rho / rho_basis. The quote must appear exactly once in the extracted file, so an offset is a fact about the
# text rather than a claim about it; rho is registered in prereg §2.1 and is judged against the anchor's own
# committed quotes, never against a re-fetch of the anchor.
MECHANISMS: list[dict] = [
    {"k": "K2", "role": "primary", "d_axis": "mixed", "v_axis": "neutral", "anchor": "G5-03",
     "rho": "REFUTES", "rho_basis": "prereg §2.1 REFUTES covers 「非单方向」「多维表征」 explicitly; this entry "
                                    "asserts refusal is better described by cones than by one linear direction",
     "claim": "Refusal is mediated by high-dimensional polyhedral cones in activation space, not by a single "
              "linear direction.",
     "quote": "We establish that refusal behaviors can be better understood via high-dimensional polyhedral "
              "cones in activation space rather than a single linear direction, highlighting their complex "
              "spatial structures."},
    {"k": "K3", "role": "primary", "d_axis": "mixed", "v_axis": "neutral", "anchor": "G5-03",
     "rho": "REFUTES", "rho_basis": "the paper's own framing sentence denying the single-direction reading; "
                                    "several independent directions and cones all mediate refusal",
     "claim": "Multiple independent directions - and multi-dimensional concept cones - mediate refusal.",
     "quote": "Contrary to prior work, we uncover multiple independent directions and even multi-dimensional "
              "concept cones that mediate refusal."},
    {"k": "K4", "role": "auxiliary", "d_axis": "mixed", "v_axis": "neutral", "anchor": "G5-03",
     "rho": "REFUTES", "rho_basis": "distinct mechanisms behind each independent direction contradicts the "
                                    "necessity-and-sufficiency of one direction (the anchor's own coded claim)",
     "claim": "Within the space of representationally independent directions, several refusal directions exist "
              "and correspond to distinct mechanisms.",
     "quote": "Additionally, we introduce representational independence and show that within this space of "
              "independent directions multiple refusal directions exist and correspond to distinct mechanisms."},
    {"k": "K10", "role": "auxiliary", "d_axis": "value-only", "v_axis": "neutral", "anchor": "G5-03",
     "rho": "UNDECIDABLE", "rho_basis": "the quote alone settles nothing about the *number* of refusal "
                                        "directions; it attacks the inference from orthogonality to independence, "
                                        "so under §2.1 it is recorded UNDECIDABLE rather than counted as a "
                                        "direction vote",
     "claim": "Orthogonality of activation directions does not license a causal-independence conclusion under "
              "intervention; an explicit independence notion is needed.",
     "quote": "Moreover, we show that orthogonality alone does not imply independence under intervention, "
              "motivating the notion of representational independence that accounts for both linear and "
              "non-linear effects."},
]

# The paper's own characterisation of the claim it argues against. Coded outside `mechanism` on purpose: it
# reports the anchor's position, it does not assert a competing one, so minting a rho for it would invent a
# relation the sentence does not state (X-85(g): a row may not create the claim it registers).
TARGET_CHARACTERIZATION = ("Prior work suggests that a single refusal direction in the model’s activation space "
                           "determines whether an LLM refuses a request.")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.status, r.read()


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())}


def overlap(a, b) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def abs_title(blob: bytes) -> str:
    m = re.search(r"<title>\s*\[[0-9a-z./]+\s*\]\s*(.*?)</title>", blob.decode("utf-8", "replace"), re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def html_text(blob: bytes) -> str:
    s = blob.decode("utf-8", "replace")
    s = re.sub(r"(?is)<(script|style|noscript|svg|math)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<(p|div|section|h\d|li|tr|figcaption)\b[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#101;", "e")
    s = re.sub(r"&#[0-9]+;|&[a-z]+;", " ", s)
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip() + "\n"


def git_head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(M.parent), "show", "HEAD:" + rel], capture_output=True).stdout


def obtain() -> dict:
    """Identity is fetched every run; the body may come from the local copy, but its acquisition must be named.

    `local_cache` without an acquisition record is not a provenance: the artifact would say "the text is here"
    and nothing about how it got here. So the sidecar is written when the body is fetched, and a local-cache run
    that has no sidecar re-fetches once and only accepts the cache if the hash still agrees.
    """
    attempts = []
    try:
        st, blob = get(ABS_URL)
        attempts.append({"url": ABS_URL, "status": st, "bytes": len(blob), "role": "identity"})
        title = abs_title(blob)
    except Exception as e:  # noqa: BLE001 - the exit table needs the channel named, not a traceback
        attempts.append({"url": ABS_URL, "error": type(e).__name__ + ": " + str(e)[:80], "role": "identity"})
        return {"channel": "FAILED", "attempts": attempts, "title": ""}
    pinned = ""
    if OUT.exists():
        m = re.search(r'"text_sha256": "([0-9a-f]{64})"', OUT.read_text(encoding="utf-8"))
        pinned = m.group(1) if m else ""
    if TEXT.exists() and pinned and sha(TEXT.read_bytes()) == pinned:
        chars = len(TEXT.read_text(encoding="utf-8"))
        acq = read_acquisition()
        if acq is None:
            acq = reacquire(pinned)
        return {"channel": "local_cache", "attempts": attempts, "title": title, "chars": chars,
                "acquisition": acq}
    body = None
    try:
        st2, blob2 = get(HTML_URL)
        attempts.append({"url": HTML_URL, "status": st2, "bytes": len(blob2), "role": "body"})
        body = html_text(blob2)
    except Exception as e:  # noqa: BLE001
        attempts.append({"url": HTML_URL, "error": type(e).__name__ + ": " + str(e)[:80], "role": "body"})
    if body is None:
        return {"channel": "IDENTITY_ONLY", "attempts": attempts, "title": title}
    TEXT.write_text(body, encoding="utf-8")
    acq = {"channel": "arxiv_html", "url": HTML_URL, "status": st2, "html_bytes": len(blob2),
           "text_sha256": sha(TEXT.read_bytes()), "chars": len(body),
           "written_to": str(TEXT), "outside_repository": True}
    ACQ.write_text(json.dumps(acq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"channel": "arxiv_html", "attempts": attempts, "title": title, "chars": len(body), "acquisition": acq}


def read_acquisition():
    if ACQ.exists():
        try:
            return json.loads(ACQ.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"record": "UNREADABLE", "file": str(ACQ)}
    return None


def reacquire(pinned: str) -> dict:
    """Recover the acquisition record for a cached body whose sidecar was lost, without changing the bytes."""
    try:
        st, blob = get(HTML_URL)
    except Exception as e:  # noqa: BLE001
        return {"record": "ABSENT", "why": "sidecar missing and the body could not be re-fetched: "
                                           + type(e).__name__ + ": " + str(e)[:60], "url": HTML_URL}
    body = html_text(blob)
    same = sha(body.encode("utf-8")) == pinned
    acq = {"channel": "arxiv_html", "url": HTML_URL, "status": st, "html_bytes": len(blob),
           "text_sha256": pinned, "chars": len(body), "written_to": str(TEXT),
           "outside_repository": True, "record": "RESTORED_BY_REFETCH" if same else "DIVERGED",
           "refetch_matches_pinned_hash": same}
    if same:
        ACQ.write_text(json.dumps(acq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return acq


def q3_exit(overlap_ok: bool, channel: str, chars: int, entries: int, unlocatable: int,
            rhos: list[str]) -> tuple[str, str]:
    """The registered exit table, with the label taken from the five-value vocabulary R17 requires (L02-A8)."""
    if channel == "FAILED":
        return "COMPETING_NOT_OBTAINED", "NULL"
    if not overlap_ok:
        # A fetch that returns a *different* paper is not a failed fetch, and folding it into exit 3 would let
        # the wrong selector look like an honest NULL. Registered as L02-A10; this row was never triggered.
        return "COMPETING_IDENTITY_MISMATCH", "NULL"
    if chars < FLOOR or entries < 3 or unlocatable or not rhos:
        return "COMPETING_IDENTITY_ONLY", "NOT_IDENTIFIED"
    # §2.1 gives UNDECIDABLE/UNRELATED no direction, so they cannot dilute the vote; the label is read off the
    # entries that actually take a side (L02-A8), and the inputs of that derivation are printed, not implied.
    directional = [r for r in rhos if r in ("SUPPORTS", "EXTENDS", "REFUTES")]
    if not directional:
        return "COMPETING_CODED", "NOT_IDENTIFIED"
    if set(directional) == {"REFUTES"}:
        return "COMPETING_CODED", "CONTRADICTED"
    if set(directional) <= {"SUPPORTS", "EXTENDS"}:
        return "COMPETING_CODED", "SUPPORTED"
    return "COMPETING_CODED", "INDETERMINATE"


def main() -> int:
    channels = json.loads(CHANNELS.read_text(encoding="utf-8"))
    registered = channels["competing_theory_L01_A1"]["title"]
    got = obtain()
    if "--extract" in sys.argv:
        print("extract | channel %s | title %s | chars %s | attempts %d | acquisition %s"
              % (got["channel"], (got.get("title") or "")[:60], got.get("chars", 0), len(got["attempts"]),
                 (got.get("acquisition") or {}).get("record", "written" if got.get("acquisition") else "none")))
        return 0
    ov = round(overlap(registered, got.get("title", "")), 4)
    text = TEXT.read_text(encoding="utf-8") if TEXT.exists() else ""
    entries, missing = [], []
    for spec in MECHANISMS:
        q = spec["quote"]
        n = text.count(q)
        if n != 1:
            missing.append((spec["k"], n))
            continue
        e = dict(spec)
        e.update({"quote_offset": text.index(q), "quote_sha16": sha(q.encode("utf-8"))[:16],
                  "quote_chars": len(q)})
        entries.append(e)
    bad_rho = [e["k"] for e in entries if e["rho"] not in
               ("SUPPORTS", "EXTENDS", "REFUTES", "UNRELATED", "UNDECIDABLE")]
    bad_anchor = [e["k"] for e in entries if e["anchor"] not in json.loads(CODING.read_text(encoding="utf-8"))["exit_table"]]
    short = [e["k"] for e in entries if not 20 <= e["quote_chars"] <= 400]
    dir_votes = [e["rho"] for e in entries if e["rho"] in ("SUPPORTS", "EXTENDS", "REFUTES")]
    exit_q3, label = q3_exit(ov == 1.0 and not bad_rho and not bad_anchor and not short, got["channel"],
                              len(text), len(entries), len(missing), [e["rho"] for e in entries])
    tgt_n = text.count(TARGET_CHARACTERIZATION)
    record = {
        "sid": SID, "reference": registered, "year": channels["competing_theory_L01_A1"].get("year"),
        "verification_level": "FULLTEXT_REVIEWED" if len(text) >= FLOOR else "EXTRACTION_INCOMPLETE",
        "identity_check": "abs page title %r overlaps the C-04 registered title at %s; first author %s"
                          % (got.get("title", "")[:70], ov,
                             channels["competing_theory_L01_A1"].get("first_author")),
        "evidence_type": "causal_intervention", "provenance": "PAPER_CLAIM", "term_type": "MAPPING",
        "d_class": "mixed",
        "mapping_note": "paper's 'refusal direction / concept cone' -> our K2 gate (L2 representational "
                        "mediation), its 'multiple independent directions with distinct mechanisms' -> K3 "
                        "competition and K4 conjunction; 'orthogonality does not imply independence' -> K10 "
                        "role re-ordering of the independence criterion (MAPPING: the paper never uses our "
                        "vocabulary).",
        "description_scope": "Judged as a claim about which representation-level structures gate emission of a "
                             "harmful completion; it is not a claim about behaviour rates, so no action-level "
                             "d_axis is coded.",
        "motion_source": "L2 - geometry of residual-stream activation directions (gradient-optimised directions "
                         "and cones), not a behaviour measurement.",
        "agency_class": "RESPONSIVE",
        "event_grammar": "[MOTION] harmful vs harmless prompt forms a separable activation structure --> "
                         "[GATE] any direction inside a multi-dimensional cone (not one vector) can strengthen "
                         "or weaken refusal --> [ACTION/INACTION] emission is gated along several independent "
                         "mechanisms at once",
        "layers": ["L2"],
        "contradiction_ref": "C-04",
        "mechanism": entries,
    }
    doc = {
        "schema": "m2a.roundL02.competing.v1",
        "sid": SID,
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "reference": registered,
        "identity": {"abs_title": got.get("title", ""), "registered": registered, "overlap": ov,
                     "channel": got["channel"], "arxiv": "2502.17420v2",
                     "first_author": channels["competing_theory_L01_A1"].get("first_author")},
        "obtain_attempts": got["attempts"],
        "acquisition": got.get("acquisition") or {"record": "ABSENT", "why": "no sidecar and no fetch happened"},
        "fulltext": {"file": str(TEXT), "chars": len(text), "bytes": len(TEXT.read_bytes()) if text else 0,
                     "text_sha256": sha(TEXT.read_bytes()) if text else "",
                     "verification_level": "FULLTEXT_REVIEWED" if len(text) >= FLOOR else "EXTRACTION_INCOMPLETE",
                     "floor_derived": FLOOR},
        "mechanism": entries,
        "record": record,
        "target_characterization": {"quote": TARGET_CHARACTERIZATION,
                                    "occurrences_in_text": tgt_n,
                                    "quote_offset": text.index(TARGET_CHARACTERIZATION) if tgt_n == 1 else None,
                                    "coded_as_mechanism": False,
                                    "why": "it reports the anchor's position rather than asserting a competing "
                                           "one, so no rho is minted for it"},
        "directional_votes": dir_votes,
        "label_derivation": "R17 label read only off entries whose rho takes a side (§2.1 leaves UNDECIDABLE and "
                            "UNRELATED directionless); all REFUTES => CONTRADICTED",
        "extraction_note": "the body comes from arXiv's LaTeXML HTML; inline math is dropped by tag stripping, so "
                           "quotes are chosen from sentences that contain no math and a quote is accepted only "
                           "when it occurs exactly once",
        "mechanisms_unlocatable": missing,
        "coding_defects": {"rho_outside_vocabulary": bad_rho, "anchor_not_registered": bad_anchor,
                           "quote_outside_20_400": short},
        "exit_q3": exit_q3, "exit_q3_label_r17": label,
        "stop_rule": "identity or extraction short => the exit table decides; no third channel is tried in "
                     "this round (prereg §4.2), L01-O4 stays open",
        "asymmetry": "the competing theory's reading is appended to C-04 and never rewrites an earlier anchor "
                     "verdict (R6); quotes are located by offset+hash, an offset that misses is an instrument "
                     "defect, not evidence",
    }
    disk = sha(PREREG.read_bytes())
    head = sha(git_head_bytes("m2a/literature/L02_PREREGISTRATION.md"))
    doc["prereg_binding"] = {"disk": disk, "git_head": head, "two_channel_match": disk == head}
    if disk != head:
        print("PREREG NOT COMMITTED: disk %s git %s" % (disk[:12], head[:12]), file=sys.stderr)
        return 4
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote L02_coding.json | exit_q3 %s (%s) | overlap %s | channel %s | chars %d | entries %d "
          "| directional votes %s | unlocatable %s | target quote occurrences %d | acquisition %s"
          % (exit_q3, label, ov, got["channel"], len(text), len(entries),
             ",".join(dir_votes) or "none", missing or "none", tgt_n,
             (got.get("acquisition") or {}).get("record", "written")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
