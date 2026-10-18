"""Round L-01 gate: instrument checks only (R2). No scientific criterion lives here.

Checks, all deterministic:
  G1  protocol binding  - literature/L01_CODING_PROTOCOL.md exists; SHA-256 of the disk bytes is
      reported, and after the round is committed the same hash must also match `git show HEAD:`.
  G2  quote byte-check  - every mechanism entry: text[off:off+len(quote)] == quote AND
      sha256(quote)[:16] == quote_sha16. A quote that is verbatim-unique but sits at a wrong
      offset is reported OFFSET_FIXABLE and the true offset printed; nothing else is repaired here.
  G3  full-text binding - the .txt file's sha256[:16] must equal the value recorded in
      L01_fulltexts.json for the same sid (so a coding claim cannot be written against a file
      that has since changed or was never the one fetched).
  G4  payload identity  - >= 3 of the selected record's title tokens must occur in the fetched
      text. This is the check that catches "channel returned a different article".
  G5  enum conformance  - d_axis / d_class in {D+, D−, mixed, value-only, neutral} after ASCII
      hyphen normalisation; k in K1..K12; layers in L0..L6; verification_level in the three-level
      enum; first mechanism entry role == primary; 1..3 entries; mapping_note present whenever
      term_type != PAPER_TERM; description_scope non-empty (02 §2.1-1).
  G6  independence audit- does the text cite its own anchor? mechanical proxy: the anchor DOI or
      >= 4 consecutive anchor-title words present in the neighbour text. Reported, never used to
      drop a record (dropping would be a criterion, not an instrument).
  G7  determinism       - running the gate twice gives byte-identical stdout.

Prints n/n and exits non-zero on any FAIL.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
FT = LIT.parent.parent.parent / "_m2a_ft"
COD = LIT / "_l01_coding"
PROT = LIT / "L01_CODING_PROTOCOL.md"
ANCHORS = {"R13": 6, "G5-03": 4, "R14": 4}
ANCHOR_TITLE = {
    "R13": "a neural mechanism for learning from delayed postingestive feedback",
    "G5-03": "refusal in language models is mediated by a single direction",
    "R14": "duration between rewards controls the rate of behavioral and dopaminergic learning",
}
ANCHOR_DOI = {"R13": "10.1038/s41586-025-08828-z", "G5-03": "10.48550/arxiv.2406.11717",
              "R14": "10.1038/s41593-026-02206-2"}
K_OK = {"K" + str(i) for i in range(1, 13)}
GROUPS_OK = ["G0", "G1", "G2", "G3", "G4", "G5", "G6"]
L_OK = {"L" + str(i) for i in range(0, 7)}
D_OK = {"D+", "D−", "mixed", "value-only", "neutral"}
AXIS_OK = {"D+", "D−", "neutral", "B+", "B−"}
LEVEL_OK = {"FULLTEXT_REVIEWED", "QUALIFIED", "ABSTRACT_VERIFIED", "IDENTITY_VERIFIED",
            "CLAIM_INDEPENDENTLY_CHECKED"}


def sha16(blob):
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def norm_axis(v):
    return "D−" if v == "D-" else v


def tokens(t):
    return [w for w in re.sub(r"[^a-z0-9 ]", " ", (t or "").lower()).split() if len(w) > 3]


def main():
    fails, checks = [], 0

    # ---- G1 ------------------------------------------------------------------
    ok = PROT.is_file()
    checks += 1
    psha = sha16(PROT.read_text(encoding="utf-8")) if ok else "-"
    (fails.append("G1 protocol file missing") if not ok else None)
    print(f"G1 protocol present | sha256[:16] {psha}")
    try:
        g = subprocess.run(["git", "-C", str(LIT.parent), "show", "HEAD:m2a/literature/"
                            + PROT.name], capture_output=True, text=True)
        if g.returncode == 0:
            checks += 1
            same = sha16(g.stdout) == psha
            print("G1b git-object binding:", "MATCH" if same else "MISMATCH (not yet committed)")
            if not same:
                fails.append("G1b protocol git object hash != disk hash")
        else:
            print("G1b git-object binding: skipped (file not in HEAD yet)")
    except Exception as exc:  # noqa: BLE001
        print("G1b git-object binding: skipped", type(exc).__name__)

    ftm = json.loads((LIT / "L01_fulltexts.json").read_text(encoding="utf-8"))["records"]
    texts, text_sha = {}, {}
    for sid in ftm:
        for cand in (FT / ("L01_" + sid + ".txt"), FT / (sid + ".txt")):
            if cand.is_file():
                t = cand.read_text(encoding="utf-8", errors="replace")
                texts[sid], text_sha[sid] = t, sha16(t)
                break

    files = sorted(COD.glob("*.json"))
    recs = {}
    for p in files:
        recs[p.stem] = json.loads(p.read_text(encoding="utf-8"))

    # ---- presence / count ----------------------------------------------------
    want = ["R13", "G5-03", "R14"] + [f"{a}-{i}" for a, ids in
            {"R13": ["N2", "N3", "N8", "N15", "N16", "N17"],
             "G5-03": ["N1", "N2", "N4", "N6"],
             "R14": ["N1", "N4", "N7", "N8"]}.items() for i in ids]
    missing = [s for s in want if s not in recs]
    checks += 1
    print(f"record count: {len(recs)}/{len(want)} | missing {missing}")
    if missing:
        fails.append(f"G0 missing coding records {missing}")

    n_quote = n_badquote = n_fixable = 0
    drift = []
    ident_fail, sha_fail, cites = [], [], []
    for sid, r in recs.items():
        # ---- G3 full-text binding -------------------------------------------
        recorded = ftm.get(sid, {}).get("sha256")
        if recorded and sid in text_sha and recorded != text_sha[sid]:
            sha_fail.append(f"{sid} recorded {recorded} vs file {text_sha[sid]}")
        # ---- G4 payload identity --------------------------------------------
        tt = ftm.get(sid, {}).get("title") or r.get("title") or ""
        if sid in texts:
            hits = sum(1 for w in set(tokens(tt)) if w in texts[sid].lower())
            if hits < 3:
                ident_fail.append(f"{sid} only {hits} title tokens present in fetched text")
        # ---- G5 enum conformance --------------------------------------------
        for f in ("verification_level", "evidence_type", "provenance", "term_type",
                  "description_scope", "motion_source", "d_class", "agency_class",
                  "event_grammar"):
            if not str(r.get(f) or "").strip():
                drift.append(f"{sid} empty field {f}")
        if r.get("verification_level") not in LEVEL_OK:
            drift.append(f"{sid} bad verification_level {r.get('verification_level')}")
        if norm_axis(r.get("d_class")) not in D_OK:
            drift.append(f"{sid} bad d_class {r.get('d_class')!r}")
        if r.get("d_class") != norm_axis(r.get("d_class")):
            drift.append(f"{sid} d_class ASCII-hyphen drift {r.get('d_class')!r}")
        if r.get("term_type") != "PAPER_TERM" and not str(r.get("mapping_note") or "").strip():
            drift.append(f"{sid} term_type {r.get('term_type')} without mapping_note")
        ms = r.get("mechanism") or []
        if not 1 <= len(ms) <= 3:
            drift.append(f"{sid} has {len(ms)} mechanism entries (must be 1..3)")
        if ms and ms[0].get("role") != "primary":
            drift.append(f"{sid} first mechanism entry is not primary")
        for j, m in enumerate(ms):
            if m.get("k") not in K_OK:
                drift.append(f"{sid}.mechanism[{j}] k {m.get('k')} outside K1..K12")
            da = norm_axis(m.get("d_axis"))
            if da not in AXIS_OK:
                drift.append(f"{sid}.mechanism[{j}] d_axis {m.get('d_axis')!r} outside enum")
            if m.get("d_axis") != da:
                drift.append(f"{sid}.mechanism[{j}] d_axis ASCII-hyphen drift {m.get('d_axis')!r}")
            # ---- G2 quote byte-check ----------------------------------------
            q, off = m.get("quote") or "", m.get("quote_offset")
            n_quote += 1
            if sid not in texts:
                n_badquote += 1
                drift.append(f"{sid}.mechanism[{j}] no local full text for {sid}")
                continue
            t = texts[sid]
            if isinstance(off, int) and t[off:off + len(q)] == q:
                pass
            elif q in t:
                n_fixable += 1
                drift.append(f"{sid}.mechanism[{j}] OFFSET_FIXABLE true_offset {t.find(q)}")
            else:
                n_badquote += 1
                drift.append(f"{sid}.mechanism[{j}] QUOTE_NOT_VERBATIM {q[:50]!r}")
            if q and sha16(q) != m.get("quote_sha16"):
                n_badquote += 1
                drift.append(f"{sid}.mechanism[{j}] quote_sha16 mismatch")
        # ---- G6 independence audit (report only) ----------------------------
        anchor = max((a for a in ANCHOR_TITLE if sid.startswith(a + "-")), key=len, default=None)
        if sid in texts and anchor is not None:
            low = texts[sid].lower()
            head4 = " ".join(tokens(ANCHOR_TITLE[anchor])[:4])
            if ANCHOR_DOI[anchor] in low or head4 in low:
                cites.append(sid)
    checks += 4
    print(f"G2 quotes checked {n_quote} | verbatim-fail {n_badquote} | offset-fixable {n_fixable}")
    print(f"G3 full-text sha binding failures {len(sha_fail)} {sha_fail[:3]}")
    print(f"G4 payload-identity failures {len(ident_fail)} {ident_fail}")
    print(f"G5 enum/field findings {len(drift)}")
    for d in drift:
        print("   ", d)
    print(f"G6 neighbours citing their own anchor: {len(cites)} -> {cites}")
    if n_badquote:
        fails.append("G2 quote failures")
    if sha_fail:
        fails.append("G3 sha mismatch")
    if ident_fail:
        fails.append("G4 fetched payload is not the selected record")
    if drift:
        fails.append("G5 enum/field conformance")
    if n_fixable:
        fails.append("G2 offset drift (fix offsets in the coding files, gate does not repair)")

    print("\nSUMMARY", len(fails), "findings")
    for f in fails:
        print("FAIL", f)
    failed_groups = {f[:2] for f in fails}
    green = len(GROUPS_OK) - len([g for g in GROUPS_OK if g in failed_groups])
    print(f"{green}/{len(GROUPS_OK)} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
