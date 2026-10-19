"""Validate the section <-> page score reconciliation: re-extract the numbers by a second path, then
prove that the rules deciding its single hard verdict can actually fire.

What the artifact claims (see `build_section_page_reconciliation.py`): a page states an instrument score
`n/n` that this repository cannot support - not under the strict window, not under the loose one, with no
effective erratum - and that is a transcription error or an invention. Everything else it reports is
history or editing: a page carrying `7/7` for a suite that later gained a rule is *stale*, not wrong, and a
page naming fewer instruments than its sections is *compressed*. This suite therefore has to show the hard
verdict is sensitive to a fabricated score, that the support tiers can only ever remove findings, and that
an erratum row does not silence anything until the correction is actually on the page.

Three things make the suite worth running at all:
  * every number is re-extracted by a **different algorithm** (find the `n/n` token, then look back along
    the same line for a `.py` name) instead of the deriver's forward regex. If the two paths disagree, one
    of them is inventing or dropping claims, and the disagreement is the finding;
  * the verdict is computed from the **live inputs** (capture bytes plus this suite's own repo scan), not
    from the artifact's fields, because the first mutation probe here crashed the generator, left the
    committed artifact in place, and every artifact-trusting rule stayed green over a changed page;
  * controls use **computed** sentinels, because §46's control went vacuous when it hard-coded the section
    number 46 that later came to exist (X-84).

Checks touch instruments only (R2): no scientific criterion, no round verdict, no publishing, no network.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

import build_section_page_reconciliation as B

M = pathlib.Path(__file__).resolve().parent.parent
W = M.parent.parent
GOV = M / "governance"
GEN = GOV / "build_section_page_reconciliation.py"
ART = GOV / "section_page_reconciliation_v1.json"
MD = GOV / "SECTION_PAGE_RECONCILIATION_v1.md"
SYNC = GOV / "wiki_sync_map_v1.json"
REPORT = M / "M2A_FINAL_REPORT.md"
LOG = GOV / "NEGATIVE_AND_NULL_EVIDENCE_LOG.md"
CACHE = W / "feishu_wiki_fetches"
DRAFTS = W / "feishu_wiki_drafts"

SELF2 = re.compile(r"(?<!\d)(\d+)/(\d+)(?!\d)")
NAME2 = re.compile(r"[A-Za-z0-9_]+\.py")
HEAD = re.compile(r"^#{2,3} (\d+) ")

results = []
tally = {"printed": 0, "printed_pass": 0}
_sc = {}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


# ---- the second extraction path ------------------------------------------------------
def strip_lines(text: str) -> str:
    text = re.sub(r"<[^>]{1,60}>", "", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(a, b)
    return "\n".join(" ".join(re.sub(r"\*+", "", ln.replace("`", "")).split())
                     for ln in text.splitlines())


def page_body(tok: str) -> str:
    return strip_lines(text_of(CACHE / (tok + ".txt")))


def text_of(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def claims2(text: str):
    """Strict: instrument -> {n/n} where the name is the last name before the score and within three
    characters of it, on the same line."""
    out = {}
    for m in SELF2.finditer(text):
        if m.group(1) != m.group(2):
            continue
        head = text[:m.start()].split("\n")[-1]
        f = re.search(r"([A-Za-z0-9_]+\.py)[^\n]{0,3}$", head)
        if f:
            out.setdefault(f.group(1), set()).add(m.group(1) + "/" + m.group(2))
    return out


def claims_loose2(text: str):
    """Loose: the last file name before the score anywhere on the same line. Support only, never an claim."""
    out = {}
    for ln in text.splitlines():
        events = sorted([(m.start(), 0, m.group(0)) for m in NAME2.finditer(ln)] +
                        [(m.start(), 1, m.group(1) + "/" + m.group(2)) for m in SELF2.finditer(ln)
                         if m.group(1) == m.group(2)])
        name = None
        for _, kind, val in events:
            if kind == 0:
                name = val
            elif name:
                out.setdefault(name, set()).add(val)
    return out


def scanned(rel: str):
    key = "s:" + rel
    if key not in _sc:
        p = M / rel
        _sc[key] = claims2(strip_lines(text_of(p))) if p.exists() else {}
    return _sc[key]


def repo_oracle():
    """This suite's own two-tier answer to "which scores does the repository support?", from a scan that
    excludes the artifact it is checking (a derived file must not attest its own numbers, R8)."""
    if "oracle" not in _sc:
        strict, loose, srcs = {}, {}, {}
        for p in sorted(M.rglob("*.md")) + sorted(M.rglob("*.json")):
            if p.name in (ART.name, MD.name):
                continue
            rel = str(p.relative_to(M))
            for f, v in scanned(rel).items():
                strict.setdefault(f, set()).update(v)
                for val in v:
                    srcs.setdefault((f, val), set()).add(rel)
            if not B.LOOSE_SRC.search(rel):
                continue
            body = strip_lines(text_of(p))
            for f, v in claims_loose2(body).items():
                loose.setdefault(f, set()).update(v)
        _sc["oracle"] = (strict, loose, srcs)
    return _sc["oracle"]


def erratum_cover(rows, f, vals, page, strict_map):
    """An erratum silences the verdict only if the correction is really on the page and the number it
    points to is really printed in the repo."""
    row = rows.get(f)
    if not row or row["quoted"] not in vals:
        return set()
    if row["marker"] not in page or row["replacement"] not in strict_map.get(f, set()):
        return set()
    return {row["quoted"]}


def report_blocks() -> dict:
    """The report split by walking line offsets - a different mechanism from the deriver's finditer."""
    lines = text_of(REPORT).splitlines(keepends=True)
    marks = [(int(HEAD.match(ln).group(1)), i) for i, ln in enumerate(lines) if HEAD.match(ln)]
    return {num: "".join(lines[li:marks[j + 1][1] if j + 1 < len(marks) else len(lines)])
            for j, (num, li) in enumerate(marks)}


def decide(page_claims, sec_claims, strict_map, loose_map, rep_values, latest, secs, body, rows=None):
    """The artifact's decision surface reimplemented: unattested / loose-only / erratum / superseded /
    compressed, with the precedence the deriver documents. `body` is the stripped page text, passed in so
    a control can simulate a page whose correction has not been published yet."""
    rows = rows or {}
    unatt, only_loose, errata = {}, {}, {}
    for f, v in page_claims.items():
        covered = erratum_cover(rows, f, v, body, strict_map)
        if covered:
            errata[f] = sorted(covered)
        half = (v & loose_map.get(f, set())) - strict_map.get(f, set())
        rest = v - strict_map.get(f, set()) - loose_map.get(f, set()) - covered
        if half:
            only_loose[f] = sorted(half)
        if rest:
            unatt[f] = sorted(rest)
    sup = {f: latest[f] for f, v in page_claims.items()
           if f in latest and latest[f] > max(secs) and v - set(rep_values.get(f, ()))}
    missing = sorted(f for f in sec_claims if f not in page_claims)
    verdict = ("score_unattested_in_repo" if unatt else "compressed" if missing else
               "page_superseded" if sup else "aligned")
    return {"unattested": unatt, "loose": only_loose, "errata": errata, "superseded": sup,
            "not_on_page": missing, "verdict": verdict}


def main() -> int:
    if not (ART.exists() and MD.exists() and SYNC.exists()):
        print("artifact missing - run build_wiki_sync_map.py, then build_section_page_reconciliation.py",
              file=sys.stderr)
        return 2
    before_json, before_md = ART.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("P1 generator reproduces the committed JSON",
           r1.returncode == 0 and ART.read_bytes() == before_json,
           (r1.stdout.strip().splitlines() or ["", ""])[0][:78])
    report("P2 generator reproduces the committed Markdown", MD.read_bytes() == before_md)
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("P3 derivation idempotent (second run, byte-identical)",
           ART.read_bytes() == before_json and MD.read_bytes() == before_md and r2.returncode == 0,
           "rc=%d, and the generator must exit 0: a crash leaves the committed artifact in place"
           % r2.returncode)

    d = json.loads(ART.read_text(encoding="utf-8"))
    sync = json.loads(SYNC.read_text(encoding="utf-8"))
    c, pages = d["counts"], d["pages"]
    attest_map = {f: set(v) for f, v in d["repo_attestation"].items()}
    rep_values = {f: set(v) for f, v in d["report_values_by_instrument"].items()}
    latest = d["newest_section_by_instrument"]
    gov_tokens = {q["node_token"]: q for q in sync["pages"]}

    pairs_art = {(s, p["node_token"]) for p in pages for s in p["sections"]}
    pairs_sync = {(r["section"], r["node_token"]) for r in sync["claims"] if r["title"]}
    report("P4 every page-section pair is a sync-map claim row and no section is carried twice",
           pairs_art == pairs_sync and len({s for s, _ in pairs_art}) == len(pairs_art)
           and c["sections_covered"] == len(pairs_art),
           "artifact %d | sync %d | distinct sections %d"
           % (len(pairs_art), len(pairs_sync), len({s for s, _ in pairs_art})))

    # P5 a summary field must equal the rows it summarizes (X-84) - and the partition must include the
    # hard category, which this file's first version omitted, making the sum equal the page count exactly
    # when nothing was wrong: a check that is vacuous by construction.
    part = (c["pairs_aligned"] + c["pairs_compressed"] + c["page_superseded"]
            + c["pairs_no_capture"] + c["score_unattested_in_repo"])
    draft_rows = sum(1 for p in pages if p["node_token"] in gov_tokens)
    report("P5 counts equal enumerable rows: partition (hard category included), unattested, draft side",
           part == c["pages_reconciled"] == len(pages)
           and c["score_unattested_in_repo"] == sum(1 for p in pages if p["unattested"])
           and c["values_loosely_attested_only"] == sum(len(v) for p in pages
                                                        for v in p["loosely_attested"].values())
           and c["erratum_rows"] == sum(len(p["erratum"]) for p in pages)
           and c["erratum_rows_effective"] == sum(1 for p in pages for v in p["erratum"].values()
                                                  if v["marker_on_page"])
           and c["draft_page_hard"] + c["draft_page_aligned"] + c["draft_page_grew"] == draft_rows \
           == len(gov_tokens)
           and c["hard_findings"] == sum(1 for p in pages if p["unattested"]) + c["draft_page_hard"],
           "partition %d pages %d | unattested %d | loose %d | errata %d/%d"
           % (part, c["pages_reconciled"], c["score_unattested_in_repo"],
              c["values_loosely_attested_only"], c["erratum_rows_effective"], c["erratum_rows"]))

    bad_prov = ["%s %s in %s" % (f, val, rel)
                for f, vals in d["repo_attestation"].items() for val, files in vals.items()
                for rel in files if val not in scanned(rel).get(f, set())]
    report("P6 every attestation pointer resolves to a file that really prints that score",
           not bad_prov, "offending: " + ("; ".join(bad_prov[:4]) or "none") +
           " | triples %d" % sum(len(v) for v in d["repo_attestation"].values()))

    # P7 the hard verdict computed from live inputs only: capture bytes + this suite's own repo scan
    strict, loose, srcs = repo_oracle()
    live_un = {}
    for p in pages:
        cf = CACHE / (p["node_token"] + ".txt")
        if not cf.exists():
            live_un[p["title"][:14]] = ["no capture"]
            continue
        body = strip_lines(text_of(cf))
        for f, v in claims2(body).items():
            miss = sorted(v - strict.get(f, set()) - loose.get(f, set())
                          - erratum_cover(B.ERRATA.get(p["node_token"], {}), f, v, body, strict))
            if miss:
                live_un.setdefault(p["title"][:14], []).extend(miss)
    report("P7 no page states a score the repo cannot support (live recompute, artifact not trusted)",
           not live_un and c["score_unattested_in_repo"] == 0 and not any(p["unattested"] for p in pages)
           and not d["hard_findings"],
           "live offenders %s | instruments strict %d loose %d" % (live_un, len(strict), len(loose)))

    sup_bad = [f for p in pages for f, s in p["superseded"].items()
               if not set(s["page"]) <= attest_map.get(f, set())
               or set(s["page"]) & rep_values.get(f, set())
               or not s["newest_section"] > max(p["sections"])]
    n_sup = sum(len(p["superseded"]) for p in pages)
    report("P8 every superseded page score is attested history with a genuinely later section",
           not sup_bad and n_sup == c["page_superseded"]
           and c["page_superseded"] == sum(1 for p in pages if p["verdict"] == "page_superseded"),
           "superseded rows %d | offenders %s" % (n_sup, sup_bad or "none"))

    draft_bad, n_draft = [], 0
    for p in pages:
        q = gov_tokens.get(p["node_token"])
        if not q:
            continue
        n_draft += 1
        dp = DRAFTS / q["draft"]
        if not dp.exists():
            draft_bad.append(q["draft"][:20] + " draft absent")
            continue
        dc = claims2(strip_lines(text_of(dp)))
        pc = claims2(page_body(p["node_token"]))
        # append-only: a draft value missing from the page is hard; a page claiming more is a published
        # correction and stays informational (the draft bytes are pinned by §46's map and cannot change)
        lost = {f: sorted(dc[f] - pc.get(f, set())) for f in dc if dc[f] - pc.get(f, set())}
        if lost:
            draft_bad.append("%s draft-only %s" % (q["draft"][:18], lost))
    report("P9 every draft score is on the published page (second-path extraction, append-only)",
           not draft_bad and n_draft == len(gov_tokens) and c["draft_page_hard"] == 0
           and c["draft_page_grew"] == sum(1 for p in pages
                                          if p["draft_vs_page"]["verdict"] ==
                                          "page_grew_after_publication"),
           "governance rows %d | offenders %s | grew %d" % (n_draft, draft_bad[:2] or "none",
                                                            c["draft_page_grew"]))

    cap_bad = []
    for p in pages:
        cf = CACHE / (p["node_token"] + ".txt")
        if not cf.exists() or p["page_sha256"] is None:
            cap_bad.append(p["title"][:16] + " no capture")
        else:
            if hashlib.sha256(cf.read_bytes()).hexdigest() != p["page_sha256"]:
                cap_bad.append(p["title"][:16] + " sha")
            if len(text_of(cf)) != p["page_chars"]:
                cap_bad.append("%s chars %s!=%d" % (p["title"][:12], p["page_chars"], len(text_of(cf))))
    report("P10 capture fingerprints match the artifact and page_chars is characters not bytes",
           not cap_bad and not d["uncaptured_tokens"],
           "offenders: " + ("; ".join(cap_bad[:3]) or "none"))

    cap_tokens = {f.stem for f in CACHE.glob("*.txt")}
    art_tokens = {p["node_token"] for p in pages}
    report("P11 captured set == reconciled set == claimed set",
           cap_tokens == art_tokens == {t for _, t in pairs_art},
           "cache %d | artifact %d | claims %d" % (len(cap_tokens), len(art_tokens), len(pairs_art)))

    blocks = report_blocks()
    path_bad = []
    for p in pages:
        if {f: sorted(v) for f, v in claims2(page_body(p["node_token"])).items()} != p["page_claims"]:
            path_bad.append(p["title"][:14] + " page")
        sec = {}
        for s in p["sections"]:
            for f, v in claims2(strip_lines(blocks.get(s, ""))).items():
                sec.setdefault(f, set()).update(v)
        if {f: sorted(v) for f, v in sec.items()} != p["section_claims"]:
            path_bad.append(p["title"][:14] + " sections")
    report("P12 a different extraction algorithm reproduces every page row and section row",
           not path_bad and c["instrument_claims_pages"] == sum(len(p["page_claims"]) for p in pages)
           and c["instrument_claims_sections"] == sum(len(p["section_claims"]) for p in pages),
           "offenders: " + ("; ".join(path_bad[:4]) or "none"))

    dec_bad = []
    for p in pages:
        pc = {f: set(v) for f, v in p["page_claims"].items()}
        got = decide(pc, {f: set(v) for f, v in p["section_claims"].items()},
                     strict, loose, rep_values, latest, p["sections"],
                     page_body(p["node_token"]), B.ERRATA.get(p["node_token"], {}))
        if (got["unattested"] != p["unattested"] or got["verdict"] != p["verdict"]
                or got["not_on_page"] != p["not_on_page"] or got["loose"] != p["loosely_attested"]
                or set(got["superseded"]) != set(p["superseded"])):
            dec_bad.append("%s %s/%s loose %s/%s" % (p["title"][:12], got["verdict"], p["verdict"],
                                                     got["loose"], p["loosely_attested"]))
    report("P13 the reimplemented two-tier decision equals the artifact on all live pages", not dec_bad,
           "offenders: " + ("; ".join(dec_bad[:3]) or "none"))

    # P14 line discipline: the window must never reach across a line, on either path. Both first drafts of
    # this instrument broke here, and one of them invented `l01_gate.py 42/42` out of a quotation count.
    probe = "l01_gate.py\n42/42 mentions 42 quotes"
    probe_html = "<p>a</p>\n<p>`b` **c**</p>"
    m0 = max(int(v.split("/")[0]) for vals in list(strict.values()) + list(loose.values()) for v in vals)
    sentinel_val = "%d/%d" % (m0 + 1, m0 + 1)
    ghost_file = "zz_unattested_instrument_%d.py" % (m0 + 1)
    all_vals = {v for vals in list(strict.values()) + list(loose.values()) for v in vals}
    assert sentinel_val not in all_vals
    assert ghost_file not in strict and ghost_file not in loose and ghost_file not in latest
    bodies = [text_of(CACHE / (pages[0]["node_token"] + ".txt"))[:4000], text_of(REPORT)[:4000]]
    report("P14 the claim window cannot cross a newline on either path and normalization keeps line count",
           claims2(probe) == {} and B.claims(B.norm(probe))[0] == {}
           and claims_loose2(probe) == {}
           and len(strip_lines(probe_html).splitlines()) == len(probe_html.splitlines())
           and len(B.norm(probe_html).splitlines()) == len(probe_html.splitlines())
           and all(len(strip_lines(x).splitlines()) == len(x.splitlines()) for x in bodies),
           "probe %s | max attested %d | sentinel %s | ghost %s" % (claims2(probe), m0,
                                                                    sentinel_val, ghost_file))

    unit = "gap_for.py 5/6 and gate_discrimination_gate.py 59/59 with 3/4 coverage"
    du, do = B.claims(B.norm(unit))
    report("P15 only a self-equal n/n counts as a score, a mixed fraction is ignored on both paths",
           du == {"gate_discrimination_gate.py": {"59/59"}} and "5/6" in do.get("gap_for.py", set())
           and claims2(B.norm(unit)) == {"gate_discrimination_gate.py": {"59/59"}}
           and claims_loose2(B.norm(unit)) == {"gate_discrimination_gate.py": {"59/59"}}
           and c["prose_slashes_ignored"] == sum(len(p["prose_slashes_ignored"]) for p in pages),
           "unit %s | odd %s | live prose rows %d" % (du, do, c["prose_slashes_ignored"]))

    # P17 both derived tables are what this suite's own scan says they are. They are what every other rule
    # reads, so a table that quietly lost an instrument would either fire P7 on legitimate history or hide a
    # fabricated score by leaving its instrument out of the population.
    orc_shared = {f: strict[f] for f in attest_map if f in strict}
    rep_orc = claims2(strip_lines(text_of(REPORT)))
    art_rep = {f: set(v) for f, v in d["report_values_by_instrument"].items()}
    bad_attest = sorted(f for f in set(orc_shared) | set(attest_map)
                        if attest_map.get(f, set()) != orc_shared.get(f, set()))
    bad_rep = sorted(f for f in set(art_rep) | set(rep_orc)
                     if art_rep.get(f, set()) != rep_orc.get(f, set()))
    bad_loose = sorted(f for f, v in d["repo_attestation_loose"].items()
                       if set(v) - loose.get(f, set()) - strict.get(f, set()))
    report("P17 attestation and report tables equal this suite's own repo scan, population included",
           not bad_attest and not bad_rep and not bad_loose
           and len(strict) == c["instruments_attested_in_repo"],
           "repo instruments %d/%d | loose instruments %d | attest %s | report %s | loose %s"
           % (len(strict), c["instruments_attested_in_repo"], len(loose),
              bad_attest[:4] or "none", bad_rep[:4] or "none", bad_loose[:4] or "none"))

    # P18 every erratum row is proven on four parts, and no declared row is inert. This is what stops the
    # errata table from becoming a place to hide a wrong number: a row only silences the verdict once the
    # correction is on the page, the replacement is printed in the repo, and the X-id exists in the log.
    lg = {int(x) for x in re.findall(r"^\| X-(\d+) \|", text_of(LOG), re.M)}
    bad_err = []
    for tok, rows in B.ERRATA.items():
        page = next((p for p in pages if p["node_token"] == tok), None)
        if page is None:
            bad_err.append("%s page not reconciled" % tok[:8])
            continue
        body = page_body(tok)
        for f, r in rows.items():
            if r["quoted"] not in page["page_claims"].get(f, []):
                bad_err.append("%s %s quoted value not on page" % (tok[:8], f))
            if r["marker"] not in body:
                bad_err.append("%s %s marker not on page" % (tok[:8], f))
            if r["replacement"] not in strict.get(f, set()):
                bad_err.append("%s %s replacement not printed in repo" % (tok[:8], f))
            if r["xid"] not in lg:
                bad_err.append("%s %s X-%d not in negative log" % (tok[:8], f, r["xid"]))
    inert = [f for p in pages for f, v in p["erratum"].items() if not v["marker_on_page"]]
    report("P18 every erratum row is proven (on page, marker published, replacement printed, X-id exists)",
           not bad_err and c["errata_not_effective"] == len(inert)
           and c["erratum_rows"] == sum(len(r) for r in B.ERRATA.values()),
           "offenders %s | inert %s | declared %d | on-page rows %d"
           % (bad_err[:4] or "none", inert or "none",
              sum(len(r) for r in B.ERRATA.values()), c["erratum_rows"]))

    # P19 the loose tier's source list is load-bearing, not decorative: the negative-log row that *reports*
    # the L-01 drift also prints the number as a sentence, so a same-line rule over the whole repo would
    # have manufactured the support that hides it. X-85 is the record of that laundering path.
    log_loose = claims_loose2(strip_lines(text_of(LOG)))
    l01_row = next((p for p in pages if p["node_token"] in B.ERRATA), None)
    report("P19 the log would launder its own finding, and the loose tier really excludes it",
           "6/6" in log_loose.get("l01_gate.py", set())
           and "6/6" not in set(d["repo_attestation_loose"].get("l01_gate.py", []))
           and "6/6" not in strict.get("l01_gate.py", set())
           and not any("6/6" in p["loosely_attested"].get("l01_gate.py", []) for p in pages)
           and l01_row is not None
           and l01_row["erratum"].get("l01_gate.py", {}).get("quoted") == "6/6"
           and l01_row["erratum"]["l01_gate.py"]["marker_on_page"] is True,
           "log prints %s | repo tiers %s / %s | silenced only by the published erratum %s"
           % (sorted(log_loose.get("l01_gate.py", set())), sorted(strict.get("l01_gate.py", set())),
              d["repo_attestation_loose"].get("l01_gate.py"),
              l01_row["verdict"] if l01_row else None))

    # P20 the transcription channel is disclosed, not absorbed: recompute from this suite's own scan which
    # scores are supported ONLY by a registration document, and require the artifact to say the same.
    reg_only = ["%s %s" % (f, v) for (f, v) in sorted(srcs) if srcs[(f, v)] <= B.REGISTRATION]
    report("P20 the registration-transcription channel is counted and listed, not silently absorbed",
           c["values_attested_only_in_registration"] == len(reg_only)
           and sorted("%s %s" % (r["instrument"], r["value"])
                      for r in d["attested_only_in_registration"]) == reg_only,
           "transcription-only scores %d | %s" % (len(reg_only), reg_only[:4] or "none"))

    sec_f = sorted({f for p in pages for f in p["section_claims"]})
    stale = sorted((f, v) for f, vs in strict.items() for v in vs if v not in rep_values.get(f, set()))
    loose_only = sorted((f, v) for f in loose for v in loose[f] - strict.get(f, set()))
    assert sec_f and stale and loose_only and latest
    real_f = sorted(f for f in strict if strict[f])[0]
    live_shapes = {"unattested": [], "superseded": [], "compressed": []}
    for p in pages:
        got = decide({f: set(v) for f, v in p["page_claims"].items()},
                     {f: set(v) for f, v in p["section_claims"].items()},
                     strict, loose, rep_values, latest, p["sections"],
                     page_body(p["node_token"]), B.ERRATA.get(p["node_token"], {}))
        live_shapes["unattested"] += list(got["unattested"])
        live_shapes["superseded"] += list(got["superseded"])
        live_shapes["compressed"] += got["not_on_page"]
    sf, sv = stale[0]
    syn = {real_f: {"quoted": sentinel_val, "replacement": sorted(strict[real_f])[0],
                    "xid": 85, "marker": "ZZ-marker-not-published"}}
    ctrl = {
        "invented value for a real instrument":
            decide({real_f: {sentinel_val}}, {}, strict, loose, rep_values, latest, [1], "", {})["unattested"]
            .get(real_f, []),
        "instrument the repo never printed":
            list(decide({ghost_file: {"7/7"}}, {}, strict, loose, rep_values, latest, [1], "", {})["unattested"]),
        "attested but stale, newer section cites it":
            list(decide({sf: {sv}}, {}, strict, loose, rep_values, {sf: 99}, [1], "", {})["superseded"]),
        "section names an instrument the page omits":
            decide({}, {sec_f[0]: {"9/9"}}, strict, loose, rep_values, latest, [1], "", {})["not_on_page"],
        "loose tier supports what the strict window missed":
            decide({loose_only[0][0]: {loose_only[0][1]}}, {}, strict, loose,
                   rep_values, latest, [1], "", {}),
        "erratum declared but its correction not on the page":
            decide({real_f: {sentinel_val}}, {}, strict, loose, rep_values, latest, [1], "", syn)
            ["unattested"],
        "the same erratum with its correction on the page":
            decide({real_f: {sentinel_val}}, {}, strict, loose, rep_values, latest, [1],
                   "ZZ-marker-not-published", syn)["unattested"],
    }
    report("P16 the decision fires on every drift shape, the loose tier only removes, and live data agrees",
           ctrl["invented value for a real instrument"] == [sentinel_val]
           and ctrl["instrument the repo never printed"] == [ghost_file]
           and ctrl["attested but stale, newer section cites it"] == [sf]
           and not decide({sf: {sv}}, {}, strict, loose, rep_values, {sf: 99}, [1], "", {})["unattested"]
           and ctrl["section names an instrument the page omits"] == [sec_f[0]]
           and ctrl["loose tier supports what the strict window missed"]["unattested"] == {}
           and ctrl["loose tier supports what the strict window missed"]["loose"]
           == {loose_only[0][0]: [loose_only[0][1]]}
           and ctrl["erratum declared but its correction not on the page"]
           == {real_f: [sentinel_val]}
           and ctrl["the same erratum with its correction on the page"] == {}
           and ctrl["erratum declared but its correction not on the page"]
           == {real_f: [sentinel_val]}
           and len(live_shapes["unattested"]) == c["score_unattested_in_repo"]
           and len(live_shapes["superseded"]) == c["page_superseded"]
           and len(live_shapes["compressed"]) == c["pairs_compressed"],
           "shapes %s | live %s | stale row %s %s | loose-only row %s"
           % ([bool(v) for v in ctrl.values()], {k: len(v) for k, v in live_shapes.items()}, sf, sv,
              loose_only[0]))

    names = [n for n, _ in results]
    report("SUITE_accounting", len(names) == len(set(names)) and len(names) >= 18,
           "%d rules, all distinct" % len(names))
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    n_pass = sum(1 for _, p in results if p)
    print("%d/%d checks passed" % (n_pass, len(results)))
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
