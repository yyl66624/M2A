"""Validate the suite-score registry: prove the pins are current, re-extract the quotes by a second path,
and prove every verdict - hard ones included - can actually fire.

Why the checks are shaped this way. The artifact's authority is a *run*: the stored `n/n` is what each suite
printed when the deriver executed it, so "re-derive and compare bytes" would mean running 36 suites again
inside the closing audit (the discrimination suite alone is ~5 minutes). The registered substitute, written
into the deriver's docstring before the first run, is: pin each suite's source SHA-256 (a changed instrument
is visible without running it), re-run a deterministic sample, and require the population to equal the
audit's own collection rule. Everything else here is checked by re-computation, not by trusting fields.

Hard verdicts (frozen): `live_unavailable`, `phantom_suite`, `stale_in_register`, `impossible_growth`,
`unexplained_gap`. Disclosed-but-legal: `paired_correction` (the same line also prints today's value) and
`possible_history` (a smaller number in an append-only document - the rule cannot tell history from a stale
figure cited as current, which is why §47's ERRATA register stays human).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

import build_suite_score_registry as B

M = pathlib.Path(__file__).resolve().parent.parent
GOV = M / "governance"
GEN = GOV / "build_suite_score_registry.py"
ART = GOV / "suite_score_registry_v1.json"
MD = GOV / "SUITE_SCORE_REGISTRY_v1.md"
SELF_SUITE = "suite_score_registry_gate.py"
SELF_OUT = {ART.name, MD.name}
HARD = ("live_unavailable", "phantom_suite", "stale_in_register", "impossible_growth", "unexplained_gap")

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def text_of(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def strip_lines(text: str) -> str:
    text = re.sub(r"<[^>]{1,60}>", "", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(a, b)
    return "\n".join(" ".join(re.sub(r"\*+", "", ln.replace("`", "")).split())
                     for ln in text.splitlines())


def claims_back(text: str):
    """Second path: find the fraction first, then look back up to three characters for a gate name."""
    out = []
    for ln_no, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"(?<!\d)(\d+)/(\d+)(?![-\d])", line):
            if m.group(1) != m.group(2):
                continue
            head = line[:m.start()]
            f = re.search(r"([A-Za-z0-9_]*gate[A-Za-z0-9_]*\.py)[^\n]{0,3}$", head)
            if f:
                out.append((f.group(1), m.group(1) + "/" + m.group(2), ln_no))
    return out


def scan_corpus(include_self_outputs=False):
    """The deriver's own corpus definition, so a namespace cannot be dropped from one path and kept in the
    other (the identifier-space lesson of X-81: compare resolved paths, never basenames)."""
    paths = [p for p, _ in B.corpus()]
    if include_self_outputs:
        paths = paths + [p for p in (ART, MD) if p.exists()]
    return sorted(set(paths))


def kinds():
    return {kind for _, kind in B.corpus()}


def main() -> int:
    if not (ART.exists() and MD.exists()):
        print("artifact missing - run build_suite_score_registry.py first", file=sys.stderr)
        return 2
    d = json.loads(ART.read_text(encoding="utf-8"))
    c, rows, live = d["counts"], d["rows"], d["live"]

    src = text_of(GEN)
    report("Q1 the frozen criteria are still in the deriver (E1-E7 and the exit order were written first)",
           all(k in src for k in ("E1 `live_unavailable`", "E2 `phantom_suite`", "E3 `stale_in_register`",
                                 "E4 `impossible_growth`", "E5 `paired_correction`", "E6 `possible_history`",
                                 "E7 `matches_live`", "Exit order", "Stop rule"))
           and "SELF_SUITE" in src and d["schema"] == "m2a.suite_score_registry.v1",
           "criteria tokens present")

    sha_bad = [n for n, v in live.items() if not (M / v["file"]).exists()
               or hashlib.sha256((M / v["file"]).read_bytes()).hexdigest() != v["sha256"]]
    report("Q2 every stored live value is pinned to the suite's bytes on disk right now",
           not sha_bad, "changed or missing: " + (", ".join(sha_bad[:4]) or "none") +
           " | pinned suites %d" % len(live))

    glob_set = {p.name for p in list(M.glob("experiments/*gate*.py")) + list(M.glob("literature/*gate*.py"))
                + list(M.glob("governance/*gate*.py"))} - {SELF_SUITE}
    unm = getattr(B, "UNMEASURED", {})
    report("Q3 the run population equals the audit's collection rule minus the registered exclusions",
           set(live) == glob_set - {SELF_SUITE} - set(unm) and SELF_SUITE not in live
           and set(unm) <= glob_set and all(r.strip() for r in unm.values())
           and all((M / "governance" / n).exists() for n in unm),
           "live %d | audit glob %d | registered exclusions %s"
           % (len(live), len(glob_set), sorted(unm) or "none"))

    # Q4 the headline numbers must equal what can be enumerated from the rows (X-84), including the hard
    # category and the disclosure categories
    dist = {}
    for r in rows:
        dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
    part = sum(dist.values())
    report("Q4 counts equal enumerable rows: partition over all verdicts, hard set, distribution",
           part == c["quote_rows"] == len(rows)
           and c["hard_findings"] == len([r for r in rows if r["verdict"] in HARD]) == len(d["hard_findings"])
           and {"verdict_" + k: v for k, v in dist.items()} ==
               {k: v for k, v in c.items() if k.startswith("verdict_")}
           and d["verdict_distribution"] == dist
           and c["suites_run"] == len(live)
           and c["suites_live_green"] == sum(1 for v in live.values() if v["live"]),
           "rows %d partition %d | hard %d | suites %d/%d"
           % (len(rows), part, c["hard_findings"], c["suites_live_green"], c["suites_run"]))

    # Q5 the quotes are re-extracted here by a different algorithm and the same documents
    re_rows = {}
    for p in scan_corpus():
        for f, v, ln in claims_back(strip_lines(text_of(p))):
            re_rows.setdefault((p.name, f, v), ln)
    art_rows = {(r["document"], r["instrument"], r["quoted"]): r["line"] for r in rows}
    missing = sorted(set(art_rows) - set(re_rows))[:4]
    added = sorted(set(re_rows) - set(art_rows))[:4]
    report("Q5 a second extraction path over the same corpus reproduces every quote row",
           not missing and not added and c["quote_rows"] == len(art_rows) == len(re_rows),
           "artifact %d | re-extracted %d | missing %s | extra %s"
           % (len(art_rows), len(re_rows), missing or "none", added or "none"))

    bad_live = [r for r in rows if r["verdict"] != "self_reference"
                if (r["verdict"] == "phantom_suite") != (r["instrument"] not in live)
                or (r["live"] is not None and not re.fullmatch(r"(\d+)/\1", r["live"]))
                or (r["live"] is None and r["verdict"] not in
                    ("phantom_suite", "live_unavailable", "unmeasured_by_registration"))]
    report("Q6 each row's instrument is either a live-pinned suite or explicitly a phantom",
           not bad_live, "offenders: " + (["%s %s %s" % (b["instrument"], b["quoted"], b["verdict"])
                                          for b in bad_live[:3]] or "none"))

    # Q7 every verdict is recomputed here, with the precedence frozen in the deriver's docstring
    corpus = {p.name: strip_lines(text_of(p)).splitlines() for p in scan_corpus()}

    def verdict2(r, live_map, line=""):
        if r["instrument"] == SELF_SUITE:
            return "self_reference"
        if r["instrument"] in getattr(B, "UNMEASURED", {}):
            return "unmeasured_by_registration"
        info = live_map.get(r["instrument"])
        if info is None:
            return "phantom_suite"
        if info["live"] is None:
            return "live_unavailable"
        q, l = int(r["quoted"].split("/")[0]), info["live"][0]
        if q == l:
            return "matches_live"
        if "%d/%d" % (l, l) in line:
            return "paired_correction"
        if r["doc_kind"] == "regenerated":
            return "stale_in_register"
        return "impossible_growth" if q > l else "possible_history"

    def line_of(r):
        ls = corpus.get(r["document"], [])
        return ls[r["line"] - 1] if 0 < r["line"] <= len(ls) else ""

    v2 = [r for r in rows if verdict2(r, live, line_of(r)) != r["verdict"]]
    report("Q7 the reimplemented verdict equals the artifact on every row (precedence included)",
           not v2, "offenders: " + (["%s %s %s->%s" % (b["document"][:14], b["instrument"], b["quoted"],
                                                       verdict2(b, live, line_of(b))) for b in v2[:3]]
                                   or "none"))

    sample = sorted(live)[:3]
    mismatch = []
    for name in sample:
        r = subprocess.run([sys.executable, str(M / live[name]["file"])], cwd=M,
                           capture_output=True, text=True, timeout=1200)
        m = re.search(r"^(\d+)/(\d+) checks passed", r.stdout.strip(), re.M)
        got = (int(m.group(1)), int(m.group(2))) if m and r.returncode == 0 else None
        if got != tuple(live[name]["live"]):
            mismatch.append("%s re-ran %s stored %s" % (name, got, tuple(live[name]["live"])))
    report("Q8 a deterministic sample of suites re-run here reproduces its stored line",
           len(sample) == 3 and not mismatch, "sample %s | offenders %s"
           % (sample, mismatch or "none"))

    self_quotes = [r for r in rows if r["instrument"] == SELF_SUITE]
    report("Q9 the step's own validator is never run by its deriver and every quote of it is disclosed",
           SELF_SUITE not in live and all(r["verdict"] == "self_reference" for r in self_quotes)
           and c["self_reference_quotes"] == len(self_quotes)
           and all(r["live"] == "-" or r["live"] is None for r in self_quotes),
           "quotes of self %d | stored count %d" % (len(self_quotes), c["self_reference_quotes"]))

    # Q10 the claim corpus is justified rather than accidental: every file in the repository that really
    # carries an adjacent `gate*.py` + `n/n` pair is either in the corpus or is this step's own output.
    # Basenames are not an identifier space here (X-81): the comparison is on resolved paths.
    candidates = [p.resolve() for p in list(M.rglob("*.md")) + list(M.rglob("*.json"))]
    carriers = [p for p in candidates if claims_back(strip_lines(text_of(p)))]
    scanned = {p.resolve() for p in scan_corpus()}
    unscanned = [p for p in carriers if p not in scanned]
    report("Q10 every file carrying a quotable score is in the corpus, this step's own output, or a declared transcription",
           carriers and all(p.name in SELF_OUT or p.name in B.LAYER_TRANSCRIPTIONS
                            for p in unscanned)
           and {p.name for p in unscanned} == {n for n in SELF_OUT
                                               if (GOV / n).exists()
                                               and claims_back(strip_lines(text_of(GOV / n)))}
                                              | ({p.name for p in carriers}
                                                 & set(B.LAYER_TRANSCRIPTIONS))
           and all(reason.strip() for reason in B.LAYER_TRANSCRIPTIONS.values())
           and len(B.LAYER_TRANSCRIPTIONS) >= 1
           and scanned and all(p.exists() for p in scanned)
           and not (SELF_OUT & {p.name for p in scanned}),
           "carriers %d | in corpus %d | excluded %s"
           % (len(carriers), len([p for p in carriers if p in scanned]),
              sorted(p.name for p in unscanned) or "none"))

    # Q11 the self-exclusion has teeth: admitted, the step's own outputs would add rows; excluded, none of
    # their keys appear in the artifact. Proven by driving the extractor over both corpora, not by zero.
    own = [p for p in (ART, MD) if p.exists()]
    own_pairs = sum(len(claims_back(strip_lines(text_of(p)))) for p in own)
    base_keys = {(r["document"], r["instrument"], r["quoted"]) for r in rows}
    grown = {(p.name, f, v) for p in scan_corpus(include_self_outputs=True)
             for f, v, _ in claims_back(strip_lines(text_of(p)))}
    added = sorted(grown - base_keys)
    report("Q11 the step's own outputs would be quoted, and the exclusion keeps them out of the claims",
           own_pairs > 0 and added and all(k[0] in SELF_OUT for k in added)
           and not any(r["document"] in SELF_OUT for r in rows) and "SELF_OUT" in text_of(GEN)
           and all(name in text_of(GEN) and reason
                   for name, reason in B.LAYER_TRANSCRIPTIONS.items()),
           "own quotable pairs %d | rows admission would add %d | artifact rows from them %d"
           % (own_pairs, len(added), sum(1 for r in rows if r["document"] in SELF_OUT)))

    max_live = max(v["live"][0] for v in live.values() if v["live"])
    sentinel_val = "%d/%d" % (max_live + 1, max_live + 1)
    ghost = "zz_unregistered_%d_gate.py" % (max_live + 1)
    assert sentinel_val not in {r["quoted"] for r in rows} and ghost not in live
    real = sorted(n for n, v in live.items() if v["live"] and v["live"][0] > 1)[0]
    today = "%d/%d" % (live[real]["live"][0], live[real]["live"][0])
    red_map = dict(live, **{real: dict(live[real], live=None)})
    base = {"instrument": real, "doc_kind": "append_only", "document": "-", "line": 1}
    shapes = {
        "phantom instrument": verdict2(dict(base, instrument=ghost, quoted="3/3"), live),
        "suite that does not print green today": verdict2(dict(base, quoted="2/2"), red_map),
        "same line also prints today's value": verdict2(dict(base, quoted="2/2"), live,
                                                        "text %s text" % today),
        "stale number inside a regenerated document": verdict2(
            dict(base, quoted="2/2", doc_kind="regenerated"), live, "no number here"),
        "a number larger than the suite ever printed": verdict2(
            dict(base, quoted=sentinel_val), live, "no number here"),
        "smaller number in an append-only document": verdict2(
            dict(base, quoted="%d/%d" % (live[real]["live"][0] - 1, live[real]["live"][0] - 1)),
            live, "no number here"),
        "today's value quoted exactly": verdict2(dict(base, quoted=today), live, "no number here"),
    }
    live_hard = [r for r in rows if r["verdict"] in HARD]
    report("Q12 every hard verdict fires on injected drift, and the live corpus is measured honestly",
           shapes["phantom instrument"] == "phantom_suite"
           and shapes["suite that does not print green today"] == "live_unavailable"
           and shapes["same line also prints today's value"] == "paired_correction"
           and shapes["stale number inside a regenerated document"] == "stale_in_register"
           and shapes["a number larger than the suite ever printed"] == "impossible_growth"
           and shapes["smaller number in an append-only document"] == "possible_history"
           and shapes["today's value quoted exactly"] == "matches_live"
           and len(live_hard) == c["hard_findings"]
           and all(r["verdict"] in HARD for r in d["hard_findings"]),
           "shapes %s | live hard rows %d | sentinel %s / %s"
           % (list(shapes.values()), len(live_hard), sentinel_val, ghost))

    hist = [r for r in rows if r["verdict"] == "possible_history"]
    report("Q13 the disclosed history tier really holds only smaller numbers in append-only documents",
           all(int(r["quoted"].split("/")[0]) < live[r["instrument"]]["live"][0] and
               r["doc_kind"] in ("append_only", "derived_summary") for r in hist)
           and dist.get("possible_history", 0) == len(hist),
           "history rows %d | max gap %s" % (len(hist),
                                             max([(live[r["instrument"]]["live"][0] -
                                                  int(r["quoted"].split("/")[0])) for r in hist], default=0)))

    pairs_now = sum(1 for p in scan_corpus() for _ in claims_back(strip_lines(text_of(p))))
    report("Q14 the quote count equals what the corpus yields right now (no silent drop between runs)",
           pairs_now == c["quotes_found"],
           "re-counted %d | stored %d" % (pairs_now, c["quotes_found"]))

    # Q15 the two amended namespaces really contribute rows (an amendment that only edits a docstring is a
    # comment, not a corpus change): run records and the derived governance tables each have claim rows.
    rr = [p for p, k in B.corpus() if k == "run_record"]
    ds = [p for p, k in B.corpus() if k == "derived_summary"]
    n_rr = sum(1 for r in rows if r["doc_kind"] == "run_record")
    n_ds = sum(1 for r in rows if r["doc_kind"] == "derived_summary")
    rr_pairs = sum(len(claims_back(strip_lines(text_of(p)))) for p in rr)
    tbl_pairs = sum(len(claims_back(strip_lines(text_of(p)))) for p in ds if p.parent == GOV)
    report("Q15 amendments A1/A2 moved rows: run records and governance tables are claim sources today",
           rr_pairs > 0 and n_rr > 0 and tbl_pairs > 0 and n_ds > 0
           and n_rr <= rr_pairs and len(rr) == len(list((M / "experiments").glob("*.md"))
                                                   + list((M / "literature").glob("*.md"))),
           "run-record docs %d pairs %d rows %d | table pairs %d rows %d"
           % (len(rr), rr_pairs, n_rr, tbl_pairs, n_ds))

    # Q16 E5 has power and a limit: printing today's value on the same line is what makes a stale or inflated
    # number a correction rather than a finding - and removing that pairing makes the same row hard again.
    big = "%d/%d" % (max_live + 1, max_live + 1)
    bare = verdict2(dict(base, quoted=big, doc_kind="derived_summary"), live, "no number here")
    paired = verdict2(dict(base, quoted=big, doc_kind="derived_summary"), live, "text %s text" % today)
    hard_now = [r for r in rows if r["doc_kind"] in ("run_record", "derived_summary") and r["verdict"] in HARD]
    report("Q16 the paired-correction tier is load-bearing and the amended kinds carry no hard row",
           bare == "impossible_growth" and paired == "paired_correction" and not hard_now
           and dist.get("paired_correction", 0) == len([r for r in rows if r["verdict"] == "paired_correction"]),
           "unpaired %s | paired %s | hard rows in amended kinds %d" % (bare, paired, len(hard_now)))

    # Q17 every kind the corpus uses is named in the frozen register, so a namespace cannot be introduced by
    # code alone (the one-entity-one-identifier lesson applied to document classes).
    report("Q17 each corpus document kind is named in the deriver's frozen register",
           kinds() == {"append_only", "regenerated", "derived_summary", "run_record"}
           and all('`%s`' % k in src for k in kinds()),
           "kinds %s" % sorted(kinds()))

    # Q18 the artifact records which code produced it and how wide the corpus was then: population B is a
    # property of the generator, so narrowing `corpus()` would otherwise shrink the live re-extraction and the
    # artifact together and stay self-consistent while covering less (the A1 failure mode, made loud).
    # an artifact written by an older generator has no pin at all: that is a FAIL, never a crash, because the
    # X-85 lesson is that a crash leaves the committed artifact in place and every artifact-reading rule above
    # stays green over it.
    gen_sha = hashlib.sha256(GEN.read_bytes()).hexdigest()
    gp, pin_c, pin_k = d.get("generator", {}), c.get("corpus_documents"), c.get("claim_documents")
    report("Q18 the deriver's bytes and corpus size are pinned in the artifact and still true",
           gp.get("sha256") == gen_sha and gp.get("file") == str(GEN.relative_to(M))
           and isinstance(pin_c, int) and pin_c == len(B.corpus()) and pin_c > 0
           and isinstance(pin_k, int) and pin_k <= pin_c,
           "generator %s | corpus then %s now %d | claim docs %s"
           % (str(gp.get("sha256"))[:12], pin_c, len(B.corpus()), pin_k))

    names = [n for n, _ in results]
    report("SUITE_accounting", len(names) == len(set(names)) and len(names) >= 14,
           "%d rules, all distinct" % len(names))
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    n_pass = sum(1 for _, p in results if p)
    print("%d/%d checks passed" % (n_pass, len(results)))
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
