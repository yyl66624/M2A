"""Round L-03 gate: instrument-only checks, 13 pre-flight rules plus 7 artifact rules.

What it refuses to do (R2): it never asks whether the CONFIRMED/REVISED readings are scientifically right. It
checks the binding, the frozen inputs, the acquisition record, the identity, byte-located quotes, the exit
table's reachability, the field contract, determinism, the no-full-text-in-repo rule, and - in full mode - that
the artifact's summary fields equal its rows and its exit is the one the registered table derives.

`--pre` is the runner's write barrier: it must pass before `L03_coding.json` may be created. With no argument
the gate runs full mode, so the audit suite gets the artifact checks too.

Run from anywhere: `python3 literature/l03_gate.py [--pre|--full]`.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L03_PREREGISTRATION.md"
TEXT = REPO.parent / "_m2a_ft" / "L03_R13-N15.txt"
ACQ = REPO.parent / "_m2a_ft" / "L03_R13-N15.acquire.json"
ART = LIT / "L03_coding.json"
L01 = LIT / "L01_coding.json"
FLOOR = 21224
SID = "R13-N15"
FROZEN = ["literature/L01_coding.json", "literature/L01_fulltexts.json", "literature/L01_channels.json",
          "literature/L01_CODING_PROTOCOL.md", "literature/ROUND_L01_RESULTS.md"]
REQUIRED_FIELDS = ["case_id", "reference", "verification_level", "evidence_type", "provenance",
                   "description_scope", "motion_source", "mechanism", "layers", "agency_class",
                   "event_grammar", "contradiction_ref"]
ALIAS = {"case_id": ("case_id", "sid"), "reference": ("reference", "title")}
NULLABLE = ("contradiction_ref",)
EXITS = ["FULLTEXT_CONFIRMS", "FULLTEXT_REVISES", "FULLTEXT_PARTIAL", "FULLTEXT_REFUTES",
         "FULLTEXT_BELOW_FLOOR", "FULLTEXT_IDENTITY_MISMATCH", "FULLTEXT_NOT_OBTAINED"]

sys.path.insert(0, str(LIT))
import l03_coding as C  # noqa: E402

_n = 0
_ok = 0


def report(tag: str, cond, detail: str = "") -> None:
    global _n, _ok
    _n += 1
    cond = bool(cond)
    _ok += int(cond)
    print(("PASS " if cond else "FAIL ") + tag + (" " + detail if detail else ""))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def has(rec: dict, field: str) -> bool:
    return any(rec.get(n) not in (None, "") for n in ALIAS.get(field, (field,)))


def main() -> int:
    full = "--full" in sys.argv or "--pre" not in sys.argv
    pre_disk = PREREG.read_bytes()
    pre_git = C.git_show(C.PREREG_REL)
    text = TEXT.read_text(encoding="utf-8")
    acq = json.loads(ACQ.read_text(encoding="utf-8"))
    l01_all = json.loads(L01.read_text(encoding="utf-8"))
    l01 = l01_all["records"][SID]
    before_art = sha(ART.read_bytes()) if ART.exists() else None
    prereg_text = pre_disk.decode("utf-8")

    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(pre_git) and sha(pre_disk) == sha(pre_git),
           "disk %s git %s" % (sha(pre_disk)[:12], sha(pre_git)[:12]))

    drift = [f for f in FROZEN if sha((M / f).read_bytes()) != sha(head_bytes("m2a/" + f))]
    report("G2 every frozen upstream L-01 artifact still matches its committed bytes (R6 inputs untouched)",
           not drift, "drifted: " + (", ".join(drift) if drift else "none"))

    attempts = acq.get("attempts") or []
    cli_c1 = any(a.get("order") == "C1" and a.get("route") == "command_line" and a.get("status") == 429
                 and not a.get("accepted") for a in attempts)
    browser_c1 = any(a.get("order") == "C1" and a.get("route") == "in_app_browser" and a.get("status") == 200
                     and a.get("accepted") for a in attempts)
    side_ok = (acq.get("accepted") is True and acq.get("text_sha256") == sha(text.encode("utf-8"))
               and acq.get("chars") == len(text) and acq.get("bytes") == len(text.encode("utf-8"))
               and acq.get("identity", {}).get("title") == l01["title"]
               and acq.get("identity", {}).get("doi") == C.DOI)
    report("G3 the acquisition sidecar matches the text and records both C1 readings (rule 1, L03-A1)",
           side_ok and cli_c1 and browser_c1,
           "accepted %s | C1 CLI 429 %s | C1 browser 200 %s | attempts %d"
           % (acq.get("accepted"), cli_c1, browser_c1, len(attempts)))

    outside = not str(TEXT.resolve()).startswith(str(REPO.resolve()) + os.sep)
    norm_ok = ("\r" not in text and all(ln == ln.rstrip() for ln in text.split("\n"))
               and "\n\n\n" not in text)
    report("G4 the full text is outside the repository, above the derived floor, and normalized as registered",
           outside and len(text) >= FLOOR and norm_ok,
           "outside %s | chars %d | floor %d | LF-only/no-trailing-ws/no-triple-newline %s"
           % (outside, len(text), FLOOR, norm_ok))

    ident = C.identity_check(text, l01["title"])
    report("G5 identity passes on DOI, normalized title and all three surnames",
           ident["all_pass"] and ident["overlap"] == 1.0 and ident["doi_in_text"] and all(ident["surnames"].values()),
           "title %r | overlap %s | surnames %s" % (ident["title_in_text"][:52], ident["overlap"],
                                                     ident["surnames"]))

    verified, bad = 0, []
    for spec in C.MECHANISMS:
        for label in ("quote", "supporting_quote"):
            q = spec.get(label)
            if not q:
                continue
            try:
                got = C.locate(text, q)
            except ValueError as e:
                bad.append("%s/%s: %s" % (spec["k"], label, e))
                continue
            if text[got["quote_offset"]:got["quote_offset"] + len(q)] == q and got["quote_sha16"] == C.sha16(q):
                verified += 1
            else:
                bad.append("%s/%s: offset or hash mismatch" % (spec["k"], label))
    report("G6 every primary and supporting quote is unique, 20-400 chars, and hits at its recorded offset/hash",
           not bad and verified == 6, "verified %d | bad %s" % (verified, bad[:2] or "none"))

    rows = re.findall(r"^\| (\d) \| `([A-Z_]+)` \|", prereg_text, re.M)
    names = [n for _, n in rows]
    synthetic = [
        ((3, 0, 0, 0, True, True, FLOOR + 1, True), "FULLTEXT_CONFIRMS"),
        ((2, 1, 0, 0, True, True, FLOOR + 1, True), "FULLTEXT_REVISES"),
        ((2, 0, 1, 0, True, True, FLOOR + 1, True), "FULLTEXT_PARTIAL"),
        ((2, 0, 0, 1, True, True, FLOOR + 1, True), "FULLTEXT_REFUTES"),
        ((2, 1, 0, 0, True, True, FLOOR - 1, True), "FULLTEXT_BELOW_FLOOR"),
        ((2, 1, 0, 0, True, False, FLOOR + 1, True), "FULLTEXT_IDENTITY_MISMATCH"),
        ((2, 1, 0, 0, False, True, FLOOR + 1, True), "FULLTEXT_NOT_OBTAINED"),
    ]
    reached = []
    for (c, r, u, f, obtained, id_ok, chars, q_ok), want in synthetic:
        got, _ = C.exit_for(c, r, u, f, obtained=obtained, identity_ok=id_ok, chars=chars, quotes_ok=q_ok)
        reached.append(got == want)
    rejects = 0
    for bad_counts in [(2, 0, 0, 0), (4, 0, 0, 0), (-1, 1, 0, 3)]:
        try:
            C.exit_for(*bad_counts)
        except ValueError:
            rejects += 1
    report("G7 the registered seven-row exit table is present and every row is reachable from exit_for",
           names == EXITS and all(reached) and rejects == 3,
           "rows %d | names %s | reachable %d/%d | invalid counts rejected %d/3"
           % (len(rows), ",".join(names), sum(reached), len(reached), rejects))

    l01_mech = {m["k"]: m for m in l01["mechanism"]}
    core = [e for e in C.MECHANISMS if e["core_class"] == "CORE"]
    additional = [e for e in C.MECHANISMS if e["core_class"] == "ADDITIONAL"]
    core_ok = (sorted(e["k"] for e in core) == ["K10", "K5", "K7"]
               and all(e["role"] == l01_mech[e["k"]]["role"] and e["d_axis"] == l01_mech[e["k"]]["d_axis"]
                       and e["v_axis"] == l01_mech[e["k"]]["v_axis"] for e in core))
    rel_ok = all(e["relation"] in C.RELATIONS for e in core + additional)
    counts_ok = (len(core) == 3 and len(additional) == 2
                 and sum(e["relation"] == "CONFIRMED" for e in core)
                 + sum(e["relation"] == "REVISED" for e in core)
                 + sum(e["relation"] == "UNSUPPORTED" for e in core)
                 + sum(e["relation"] == "REFUTED" for e in core) == 3)
    report("G8 the core set is exactly L-01's K5/K7/K10 with unchanged roles/axes; extras are ADDITIONAL and "
           "do not enter c/r/u/f",
           core_ok and rel_ok and counts_ok,
           "core %s | additional %d | relations closed %s"
           % (",".join(e["k"] for e in core), len(additional), rel_ok))

    art = C.build(text, acq, pre_disk, pre_git)
    rec = art["record"]
    holes = [f for f in REQUIRED_FIELDS if not has(rec, f) and f not in NULLABLE]
    keyless = [f for f in REQUIRED_FIELDS if not any(n in rec for n in ALIAS.get(f, (f,)))]
    mech_ok = bool(rec.get("mechanism")) and all(
        all(k in m for k in ("k", "role", "d_axis", "v_axis", "quote", "quote_offset", "quote_sha16"))
        for m in rec["mechanism"])
    report("G9 the new record clears the L-01 field contract, layers included, and keeps the full quote fields",
           not holes and not keyless and mech_ok and rec["verification_level"] == "FULLTEXT_REVIEWED",
           "missing %s | keyless %s | mechanism rows %d | level %s"
           % (holes or "none", keyless or "none", len(rec.get("mechanism") or []), rec.get("verification_level")))

    a, b = C.build(text, acq, pre_disk, pre_git), C.build(text, acq, pre_disk, pre_git)
    stable = C.digest(a) == C.digest(b) and a == b and sha(text.encode("utf-8")) == acq["text_sha256"]
    report("G10 the builder is deterministic and leaves the text bytes unchanged",
           stable, "digest %s | text %s" % (C.digest(a), acq["text_sha256"][:12]))

    text_hash, hits = sha(text.encode("utf-8")), []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in (".git", "scratch", "__pycache__", "node_modules")]
        for fn in files:
            p = pathlib.Path(root) / fn
            try:
                if sha(p.read_bytes()) == text_hash:
                    hits.append(str(p.relative_to(REPO)))
            except OSError:
                continue
    report("G11 the full text appears in no repository file (third-party body stays outside)",
           not hits, "files with the text hash: " + (", ".join(hits[:3]) if hits else "none"))

    report("G12 this gate wrote nothing (pre-flight is a barrier, not a writer)",
           (sha(ART.read_bytes()) if ART.exists() else None) == before_art,
           "artifact %s" % ("unchanged" if ART.exists() else "absent"))

    clauses = ["FULLTEXT_NOT_OBTAINED", "L01-O5", "L03-O1", "21 224", "FULLTEXT_REVISES", "r ≥ 1", "f = 0",
               "保持开放", "停"]
    report("G13 the preregistration still contains the halt rules, the floor, the revision row and the two "
           "obligation names",
           all(s in prereg_text for s in clauses),
           "missing: " + (",".join(s for s in clauses if s not in prereg_text) or "none"))

    if full:
        art_ok = ART.exists()
        report("G14 the artifact exists and parses as JSON", art_ok, "file %s" % ART.name)
        loaded = {}
        if art_ok:
            try:
                loaded = json.loads(ART.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                loaded = {}
        binding_ok = (loaded.get("prereg_sha256") == sha(pre_disk)
                      and loaded.get("prereg_binding", {}).get("disk_sha256") == sha(pre_disk)
                      and loaded.get("prereg_binding", {}).get("git_sha256") == sha(pre_git)
                      and loaded.get("prereg_binding", {}).get("match") is True)
        report("G15 the artifact is bound to the preregistration on both channels",
               binding_ok, "prereg %s | disk %s | git %s | match %s"
               % ((loaded.get("prereg_sha256") or "?")[:12],
                  (loaded.get("prereg_binding", {}).get("disk_sha256") or "?")[:12],
                  (loaded.get("prereg_binding", {}).get("git_sha256") or "?")[:12],
                  loaded.get("prereg_binding", {}).get("match")))

        rebuilt = C.build(text, acq, pre_disk, pre_git)
        written = dict(loaded)
        written.pop("written_at", None)
        same = written == rebuilt and loaded.get("fulltext", {}).get("text_sha256") == acq["text_sha256"]
        report("G16 every artifact field equals an independent rebuild from the text and sidecar (exit included)",
               same, "artifact digest %s | rebuild digest %s"
               % (C.digest(written) if written else "?", C.digest(rebuilt)))

        gen_ok = loaded.get("generator", {}).get("sha256") == sha((LIT / "l03_coding.py").read_bytes())
        report("G17 the generator hash names the coding module that is on disk now",
               gen_ok, "artifact %s | disk %s"
               % ((loaded.get("generator", {}).get("sha256") or "?")[:12],
                  sha((LIT / "l03_coding.py").read_bytes())[:12]))

        rows = loaded.get("record", {}).get("mechanism") or []
        core_rows = [e for e in rows if e.get("core_class") == "CORE"]
        add_rows = [e for e in rows if e.get("core_class") == "ADDITIONAL"]
        cnt = loaded.get("counts", {})
        c = sum(e.get("relation") == "CONFIRMED" for e in core_rows)
        r = sum(e.get("relation") == "REVISED" for e in core_rows)
        u = sum(e.get("relation") == "UNSUPPORTED" for e in core_rows)
        f = sum(e.get("relation") == "REFUTED" for e in core_rows)
        summary_ok = (cnt.get("core_total") == len(core_rows) == 3 and cnt.get("confirmed") == c
                      and cnt.get("revised") == r and cnt.get("unsupported") == u and cnt.get("refuted") == f
                      and cnt.get("additional") == len(add_rows)
                      and cnt.get("mechanism_total") == len(rows)
                      and cnt.get("quotes_primary") == len(rows)
                      and cnt.get("quotes_total") == len(rows) + sum(1 for e in rows if e.get("supporting_quote")))
        report("G18 the artifact's summary counts equal its own rows (X-84), not a separately typed tally",
               summary_ok, "rows c=%d r=%d u=%d f=%d add=%d | summary %s"
               % (c, r, u, f, len(add_rows), json.dumps({k: cnt.get(k) for k in
                  ("core_total", "confirmed", "revised", "unsupported", "refuted", "additional",
                   "mechanism_total", "quotes_total")}, ensure_ascii=False)))

        exit_ok = (loaded.get("exit_q1") in EXITS
                   and C.LABELS[loaded.get("exit_q1")] == loaded.get("exit_q1_label_r17"))
        closed = loaded.get("exit_q1") in ("FULLTEXT_CONFIRMS", "FULLTEXT_REVISES", "FULLTEXT_PARTIAL",
                                           "FULLTEXT_REFUTES")
        ob_ok = ((loaded.get("l01_o5", {}).get("status") == ("CLOSED" if closed else "OPEN"))
                 and (loaded.get("l03_o1", {}).get("status") ==
                      ("OPEN" if loaded.get("exit_q1") in ("FULLTEXT_REVISES", "FULLTEXT_PARTIAL",
                                                          "FULLTEXT_REFUTES") else "NONE")))
        report("G19 the exit carries its registered five-value label and the L01-O5/L03-O1 states follow 5.2",
               exit_ok and ob_ok, "exit %s | label %s | L01-O5 %s | L03-O1 %s"
               % (loaded.get("exit_q1"), loaded.get("exit_q1_label_r17"),
                  loaded.get("l01_o5", {}).get("status"), loaded.get("l03_o1", {}).get("status")))

        report("G20 reading the artifact did not rewrite it (a validator may not write what it validates)",
               (sha(ART.read_bytes()) if ART.exists() else None) == before_art,
               "artifact %s" % ("unchanged" if ART.exists() else "absent"))

    print("%d/%d checks passed" % (_ok, _n))
    return 0 if _ok == _n else 1


if __name__ == "__main__":
    raise SystemExit(main())
