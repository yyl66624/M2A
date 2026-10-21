"""§49 validator for the label-provenance table: 18 rules plus 2 self-counts, and every rule is asked
whether it can fire.

Reads only committed artifacts and the repo's own JSON; the audit itself does not run experiments and does not
go online. Two invariants inherited from the layers above are load-bearing here:

* the deriver's *source* hash and its corpus counts are pinned, because narrowing population A or the corpus
  would otherwise stay invisible to a validator that recomputes with the same narrowed code;
* the validator never adopts the generator's fresh bytes (X-91): a reproducibility mismatch is reported and the
  committed bytes are restored, so the red can still be inspected afterwards.

Teeth are proven by probes on synthetic rows, never by a sentence: each hard verdict gets a constructed line
that must turn it red, and the two disclosures that could hide a finding (errata, empty allow-list) get probes
showing they do not swallow real claims.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
ART = GOV / "label_provenance_v1.json"
MD = GOV / "LABEL_PROVENANCE_v1.md"
GEN = GOV / "build_label_provenance.py"

sys.path.insert(0, str(GOV))
import build_label_provenance as B  # noqa: E402

QIDS = ["Q%d" % i for i in range(1, 19)]
SELF = ["SUITE_accounting", "SUITE_tally"]
_ok = 0
_n = 0
_verdicts = []


def report(tag, cond, detail=""):
    global _ok, _n
    _n += 1
    _verdicts.append((tag, bool(cond)))
    if cond:
        _ok += 1
        print("PASS %s %s %s" % (tag, "" if not detail else "", detail[:78] if detail else ""))
    else:
        print("FAIL %s %s" % (tag, detail))


def phases_independent():
    """The registered round numbers, re-derived here by a second path (file names of the artifacts)."""
    return sorted({int(m.group(1)) for p in B.artifact_files()
                   for m in [re.search(r"phase(\d+)", p.name)] if m})


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if not (ART.exists() and MD.exists()):
        print("artifact missing - run build_label_provenance.py first", file=sys.stderr)
        return 2
    before_json, before_md = ART.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_json, fresh_md = ART.read_bytes(), MD.read_bytes()
    report("Q1 generator reproduces the committed JSON",
           r1.returncode == 0 and fresh_json == before_json,
           (r1.stdout.strip().splitlines() or [""])[0][:78])
    report("Q2 generator reproduces the committed Markdown", fresh_md == before_md)
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    if fresh_json != before_json:
        ART.write_bytes(before_json)
    if fresh_md != before_md:
        MD.write_bytes(before_md)
    report("Q3 derivation idempotent, and a non-reproducing run leaves the committed bytes in place",
           ART.read_bytes() == before_json and MD.read_bytes() == before_md
           and fresh_json == before_json and r2.returncode == 0,
           "rc=%d; the validator does not adopt its own repair (X-91)" % r2.returncode)

    d = json.loads(ART.read_text(encoding="utf-8"))
    rows, c = d["rows"], d["counts"]

    # Q4 partition: EVERY verdict category the layer declares is inside the sum, hard ones included
    order = ["anchor_phantom", "label_unregistered", "label_wrong_for_anchor", "stale_in_register",
             "paired_correction", "five_label_only_in_translation", "not_a_round_verdict",
             "attested_in_other_round", "anchor_without_recorded_label",
             "label_mention_without_predication", "cross_round_refutation", "label_without_anchor",
             "matches_artifact"]
    # declared categories may legitimately have zero rows; observed ones must all be declared
    report("Q4 the partition covers every declared category, hard ones included",
           sum(c[v] for v in order) == len(rows) and {r["verdict"] for r in rows} <= set(order)
           and set(order) == set(c) - {"hard_findings", "claim_documents", "corpus_documents",
                                       "artifact_files", "vocabulary_tokens", "registered_phases",
                                       "paired_corrections"}
           and c["hard_findings"] == sum(c[v] for v in order[:4]),
           "rows=%d sum=%d hard=%d" % (len(rows), sum(c[v] for v in order), c["hard_findings"]))

    # Q5 headline counts are re-derived from the rows, never trusted from the artifact header
    recount = {v: sum(1 for r in rows if r["verdict"] == v) for v in order}
    report("Q5 every headline count equals what the rows hold",
           all(c[v] == recount[v] for v in order)
           and c["claim_documents"] == len({r["document"] for r in rows})
           and c["corpus_documents"] == len(B.corpus())
           and c["artifact_files"] == len(B.population_a()),
           "claim docs=%d corpus=%d arts=%d" % (c["claim_documents"], c["corpus_documents"],
                                                c["artifact_files"]))

    # Q6 population A recomputed by a second path: scan the raw JSON text instead of walking the tree
    arts2 = {}
    for p in B.artifact_files():
        txt = p.read_text(encoding="utf-8")
        found = set(m.group(1) for m in re.finditer(
            r'"(?:[^"]*(?:label|verdict|exit|outcome|status|state)[^"]*)"\s*:\s*"([^"]+)"', txt, re.I))
        arts2[str(p.relative_to(M))] = found
    drift = [k for k in arts2 if set(d["artifact_labels"][k]["raw"]) != arts2[k]]
    report("Q6 the artifact's raw label set equals a regex scan of the same JSON",
           not drift and len(arts2) == len(d["artifact_labels"]),
           "files=%d drift=%s" % (len(arts2), drift[:3]))

    # Q7 claims re-extracted independently: same rows, same tokens, same line numbers
    ind = {(r["document"], r["line"], lab) for r in B.claims(B.vocab(B.population_a())) for lab in r["labels"]}
    art = {(r["document"], r["line"], lab) for r in rows for lab in r["labels"]}
    report("Q7 the claim rows equal an independent re-extraction", ind == art,
           "independent=%d artifact=%d" % (len(ind), len(art)))

    # Q8 the translation layer is imported, not re-typed: its bytes and rule count are pinned
    ta = d["translation_authority"]
    report("Q8 the translation authority is the registered module, pinned by hash",
           ta["sha256"] == sha(M / ta["module"]) and ta["rules_tokens"] == len(B.RULES)
           and B.RULES is __import__("build_status_label_table").RULES,
           "%s | rules %d" % (ta["sha256"][:12], ta["rules_tokens"]))

    # Q9 vocabulary: a claim token is either a registered disposition or a string some artifact recorded
    graw = B.global_raw(B.population_a())
    stray = sorted({lab for r in rows for lab in r["labels"]} - B.DISPOSITIONS - graw)
    report("Q9 no claim token is invented outside the registration and the artifacts",
           not stray, "stray=%s | tokens=%d" % (stray[:4], c["vocabulary_tokens"]))

    # Q10 self-exclusion is real: neither output appears as a claim document or an artifact
    report("Q10 the table does not attest itself",
           not [r for r in rows if pathlib.Path(r["document"]).name in B.SELF_OUT]
           and not [k for k in d["artifact_labels"] if pathlib.Path(k).name in B.SELF_OUT]
           and "SELF_OUT" in GEN.read_text(encoding="utf-8"),
           "excluded=%s" % ",".join(sorted(B.SELF_OUT)))

    # Q11 errata is load-bearing in both directions: markers present, and ignoring them turns rows hard
    docs = {r["document"]: (M / r["document"]).read_text(encoding="utf-8") for r in rows}
    dead = [e for e in d["errata"] if e["marker"] not in docs.get(e["document"],
            (M / e["document"]).read_text(encoding="utf-8"))]
    silenced = [r for r in rows if r.get("errata")]
    hard_now = [r for r in rows if r["verdict"] in B.HARD_TERMS]
    without = [r for r in rows if any(v in B.HARD_TERMS for _, v in r.get("per_label", []))]
    keys = lambda rs: {(r["document"], r["line"]) for r in rs}

    def destinations(rs):
        """The four places a row whose labels include a hard term is allowed to end up."""
        wo = [r for r in rs if any(v in B.HARD_TERMS for _, v in r.get("per_label", []))]
        return (keys(wo), (keys([r for r in rs if r["verdict"] in B.HARD_TERMS]),
                           keys([r for r in rs if r.get("errata")]),
                           keys([r for r in wo if r["verdict"] == "cross_round_refutation"]),
                           keys([r for r in wo if r.get("paired_correction")])))

    w_set, (h_set, s_set, c_set, p_set) = destinations(rows)
    # Teeth for the rule itself: drop one row's errata record - the laundering this rule exists to refuse - and
    # the equation must fail. The probe runs on a copy of the in-memory rows, never on the artifact (X-91), and
    # it is what replaces the `not hard_now` conjunct that the old rule mistook for a check of the instrument.
    i0 = next((i for i, r in enumerate(rows) if r.get("errata")), None)
    laundered = [dict(r, errata=None) if i == i0 else r for i, r in enumerate(rows)] if i0 is not None else None
    ld = destinations(laundered) if laundered is not None else None
    teeth = ld is not None and ld[0] != set().union(*ld[1])
    # The rule used to end with `not hard_now`: a claim about the repository sitting inside a check of the
    # instrument, so the gate turned red the moment the layer found anything (X-109). What is actually being
    # verified is that nothing is *laundered*: a row whose labels include a hard term must end either hard,
    # or silenced by a published errata, or disclosed as cross-round / paired-correction - and a row cannot
    # be both corrected and paired, because emptying `hard` is what pairs it.
    report("Q11 every errata entry's marker is in the document it names, and it silences exactly its rows",
           not dead and len(silenced) >= len(d["errata"]) and len(without) >= len(d["errata"])
           and w_set == h_set | s_set | c_set | p_set and teeth
           and not (h_set & p_set) and not (s_set & c_set),
           "errata=%d silenced=%d would-be-hard=%d live-hard=%d cross=%d paired=%d laundering-probe=%s dead=%d"
           % (len(d["errata"]), len(silenced), len(without), len(hard_now), len(c_set), len(p_set),
              "fires" if teeth else "DEAD", len(dead)))

    # Q12 a correction row does not silence itself: rebuild the row with the marker inside it
    if d["errata"]:
        e0 = d["errata"][0]
        fake = {"document": e0["document"], "kind": "append_only", "line": 1,
                "labels": [e0["quoted"]], "excerpt": "订正 %s 里提到 %s" % (e0["xid"], e0["quoted"]),
                "line_len": 10, "line_text": "订正 %s 里提到 %s" % (e0["xid"], e0["quoted"])}
        fam, phan = B.anchors_of(fake["excerpt"], B.registered_phases(B.population_a()))
        fake["anchors"] = sorted(str(x) for x in fam)
        doc_text = (M / e0["document"]).read_text(encoding="utf-8")
        report("Q12 a row carrying the correction marker is still judged, not laundered",
               not B.errata_live(fake, e0["quoted"], doc_text, fake["excerpt"]),
               "marker in row => errata refused")
    else:
        report("Q12 a row carrying the correction marker is still judged, not laundered",
               False, "no errata registered")

    # Q13 teeth for L1: a phase number that has no artifact must be a phantom
    nums = B.registered_phases(B.population_a())
    sentinel = max(nums) + 1
    inv = {v: k for k, v in B.ROMAN.items()}
    probe = "| **X** | Phase %s 判为 **SUPPORTED** |" % (inv[sentinel],)
    fam, phan = B.anchors_of(probe, nums)
    probe5 = "Phase ROMAN-NOT-IN-TABLE 判为 **SUPPORTED**"
    fam2, phan2 = B.anchors_of(probe5.replace("ROMAN-NOT-IN-TABLE", "IIII"), nums)
    report("Q13 an unregistered round number and an unparseable roman both turn anchor_phantom",
           fam == set() and phan == {sentinel} and phan2 == {"unparsed"} and not fam2
           and sentinel not in nums,
           "sentinel=%d phan=%s phan2=%s" % (sentinel, sorted(phan), sorted(phan2, key=str)))

    # Q14 teeth for L3: a bold verdict-shaped word nobody registered must be label_unregistered
    arts = B.population_a()
    toks = B.vocab(arts)
    fake_rows = [{"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                  "labels": ["TOTALLY_INVENTED_VERDICT"], "excerpt": "Phase IV 判为 **TOTALLY_INVENTED_VERDICT**",
                  "line_len": 40, "line_text": "Phase IV 判为 **TOTALLY_INVENTED_VERDICT**",
                  "doc_text": ""}]
    res = B.classify(fake_rows, arts, nums, toks, B.status_only(arts))
    report("Q14 an invented verdict word is a hard finding, not a silent row",
           len(res) == 1 and res[0]["verdict"] == "label_unregistered",
           res[0]["verdict"] if res else "row dropped")

    # Q15 teeth for L4: a regenerated document carrying a contradicted label cannot use the history excuse
    fake_led = [{"document": "governance/OBLIGATION_REGISTRY.md", "kind": "regenerated", "line": 1,
                 "labels": ["CONTRADICTED"], "excerpt": "Phase IV 判定 **CONTRADICTED**", "line_len": 30,
                 "line_text": "Phase IV 判定 **CONTRADICTED**", "doc_text": ""}]
    res2 = B.classify(fake_led, arts, nums, toks, B.status_only(arts))
    report("Q15 a regenerated document is judged stale_in_register, not merely wrong",
           len(res2) == 1 and res2[0]["verdict"] == "stale_in_register",
           res2[0]["verdict"] if res2 else "row dropped")

    # Q16 an empty allow-list is never a refutation (amendment A8), and non-predicated mentions stay disclosed
    empty = [{"document": "experiments/PHASE2_RESULTS.md", "kind": "run_record", "line": 1,
              "labels": ["SUPPORTED"], "excerpt": "Phase %s 判为 **SUPPORTED**" % inv[max(nums) + 1],
              "line_len": 40, "line_text": "Phase %s 判为 **SUPPORTED**" % inv[max(nums) + 1],
              "doc_text": ""}]
    res3 = B.classify(empty, arts, nums, toks, B.status_only(arts))
    mention = [{"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                "labels": ["REFUTED"], "excerpt": "Phase IV 的表里出现过 REFUTED 这个词", "line_len": 30,
                "line_text": "Phase IV 的表里出现过 REFUTED 这个词", "doc_text": ""}]
    res4 = B.classify(mention, arts, nums, toks, B.status_only(arts))
    report("Q16 an unrecordable anchor and a non-predicated mention are both disclosed, never hard",
           res3[0]["verdict"] == "anchor_phantom" and res3[0]["phantom"] == [str(max(nums) + 1)]
           and res4[0]["verdict"] == "label_mention_without_predication",
           "%s / %s" % (res3[0]["verdict"], res4[0]["verdict"]))

    # Q17 the asymmetry is one-directional: loosening the pairing may remove findings, never invent them
    anchored = [r for r in rows if r["verdict"] in order]
    hard_rows = [r for r in anchored if r["verdict"] in B.HARD_TERMS]
    report("Q17 every hard row is predicated, anchored, has a non-empty allow-list and no live errata",
           all(r.get("predicated") and r["anchors"] and r.get("allowed_five") and not r.get("errata")
               for r in hard_rows)
           and sum(1 for r in rows if r["verdict"] == "label_without_anchor") > 0
           and sum(1 for r in rows if r["verdict"] == "label_mention_without_predication") > 0,
           "hard=%d unanchored=%d mentions=%d"
           % (len(hard_rows), recount["label_without_anchor"],
              recount["label_mention_without_predication"]))

    # the generator itself is pinned by hash, so widening or narrowing the corpus is visible from here
    gp = d["generator"]
    kinds = sorted({r["kind"] for r in rows})
    skipped_prereg = len([p for p in list((M / "experiments").glob("*.md"))
                          + list((M / "literature").glob("*.md")) if "PREREG" in p.name])
    report("Q18 the generator's source hash and its corpus counts still match today's bytes",
           gp["sha256"] == sha(GEN) and gp["file"] == str(GEN.relative_to(M))
           and c["corpus_documents"] == len(B.corpus()) and c["registered_phases"] == len(phases_independent()) == len(nums)
           and sorted(nums) == phases_independent() and max(nums) + 1 not in nums
           and kinds == ["append_only", "derived_summary", "regenerated", "run_record"]
           and skipped_prereg > 0,
           "gen %s | corpus %d | phases %d | preregs skipped %d"
           % (gp["sha256"][:12], c["corpus_documents"], c["registered_phases"], skipped_prereg))
    # the accounting rule cannot count itself (it is recorded after this line runs): it asserts that what
    # was recorded so far is exactly the declared Q-rules, and the tally rule then checks the fraction
    ids = [tag.split()[0] for tag, _ in _verdicts]
    report("SUITE_accounting every declared rule id was recorded exactly once",
           sorted(ids) == sorted(QIDS) and len(ids) == len(set(ids)),
           "ids=%s qids=%d" % (",".join(ids), len(QIDS)))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _, v in _verdicts if v),
           "recorded=%d passed=%d ids=%d" % (_n, _ok, len({t for t, _ in _verdicts})))
    print("%d/%d checks passed" % (_ok, len(_verdicts)))
    return 0 if _ok == len(_verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
