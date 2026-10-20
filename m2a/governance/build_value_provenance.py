"""§50 - reconcile the *criterion values* written in prose against the round's own records.

GOVERNANCE_ARTIFACT. No experiment is run, no round verdict or registered criterion is altered (R6).

QUESTION (the only one with authority). §48 refutes a suite score a sentence quotes; §49 refutes a verdict
label it predicates. Neither looks at the numbers the discipline is actually about: tolerances, thresholds,
exponents, grid steps, seed counts. This repo has been bitten by exactly that family - R16 (a three-layer
tolerance larger than the two-layer one, so the decidable range narrowed), R9 (a coefficient moved between
scales that the target instrument already contained), X-83 (a tolerance registered for a 10-seed mean used to
judge a single-seed residual, and a `0.005` typed from memory where the round registered `0.008`). Those were
caught by hand. Here is the instrument: **a criterion value a sentence attributes to a round - is that number
in that round's own records at all?**

POPULATION A (authoritative, per round family). For a round number N, the union of:
  - every numeric token in `experiments/phaseN*.json` / `literature/*N*.json` values (what the round recorded),
  - every numeric token in `experiments/PHASE<N>_PREREGISTRATION.md` (what the round froze before running),
  - every numeric token in that round's committed run records (`experiments/PHASE<N>_RESULTS.md`,
    `literature/ROUND_*.md`) - a TRANSCRIPTION tier, so a value that only the run record ever wrote is disclosed
    as `value_only_in_transcription` rather than silently accepted.
Round families come from the artifact file names, sub-rounds belong to their parent (5b -> 5).

POPULATION B (claims). Prose lines from the same document kinds as §48/§49 (`append_only` report + negative
log, `regenerated` ledger, `derived_summary` `report/*.md` + governance `*_v*.md`, `run_record`
`experiments/*.md` + `literature/*.md`, `*PREREG*.md` excluded) that carry BOTH a round anchor and a
criterion-shaped number. A number is criterion-shaped when it has a decimal point or exponent, or sits within
three characters of a criterion marker (`≤ ≥ ± δ Δ tolerance 容差 阈值 门槛 精度 步长 网格 种子`); bare integers
(dates, `243 格`, section numbers) are not claims, because treating them as such would make the layer judge
its own parsing instead of the repository.

VERDICTS - registered exit order, frozen before the first run:
  E1 `anchor_without_records`   HARD - the line attributes a criterion value to a round number that has
                                      neither a preregistration nor an artifact.
  E2 `value_unattested_in_repo`   HARD - the anchor resolves, but the number appears in none of that round's
                                      records: not frozen in its prereg, not printed in its artifact, not even
                                      transcribed in its run record.
  E3 `stale_value_in_register`   HARD - same as E2 where the document is `regenerated` (OBLIGATION_REGISTRY.md):
                                      a file rewritten from rows has no history excuse.
  disclosed: `value_of_other_round` (the number IS registered - by another round: R9's scale-transfer family),
             `value_only_in_transcription` (only the round's prose ever wrote it),
             `matches_round_records`, `criterion_without_anchor`.
  A10 the exit list first named `matches_prereg` / `matches_artifact` as two row-level exits and `self_reference`
      as a third verdict. Neither survived the implementation and the register text is what is wrong, not the
      readings: the tier is a property of a *value*, and one line can carry values frozen in the prereg and
      values only printed by the run, so a row-level exit had to be the disjunction (`matches_round_records`)
      with the per-value tiers kept in `per_value.attested_in`; and self-reference is an exclusion rule applied
      when the corpus is built (this layer's own two output files are never read as A or B), so it can never be
      a verdict about a repository claim. No threshold, tolerance, or hard class changed, and no reading exists
      under the earlier names - the first real run came after this edit.
STOP RULE: a hard finding that cannot be removed by an appended correction is registered as a finding and
reported as-is. Criteria are never relaxed, a preregistration is never edited after the fact, and no historical
document is rewritten.

ASYMMETRY, one-directional by construction. The attestation base is deliberately wide (three tiers) and the
claim shape deliberately narrow: widening support can only remove findings, and narrowing the claim pattern can
only remove findings. Nothing here can invent a red.

SELF-REFERENCE. This layer writes `value_provenance_v1.json` and `VALUE_PROVENANCE_v1.md`; neither is ever
read as population A or B (an artifact must not attest its own drift), and the validator's own name is kept
out of any live population - §48's `UNMEASURED` lesson: running a validator that re-derives a layer reading
this table would make a single closing audit unorderable (X-94).

COST. Every prose iteration costs a full re-scan of the artifact JSON and the round records (seconds: no suite
is run). Pinning bytes is not pinning verdicts, so there is no cache.

AMENDMENTS (all made during the R1 pre-run check, before anything was written, so no reading ever existed
under the earlier shapes):
  A1 the repository writes minus as U+2212 (`−2.062033944485`); the artifacts store ASCII `-`. Without
     normalising, every slope and offset quoted in prose looked invented.
  A2 a decimal preceded by `§`, heading a line, or one link of a longer dotted chain (`3.10.12`, `15.2`,
     `§4.1`) is a document reference, not a criterion value.
  A3 the exponent pattern needed byte boundaries: unanchored, it cut `2e338` out of the sha256 prefix
     `5aa2e338...` and `308e35498` out of `d93fe308e35498c9...` - hashes are not measurements.
  A4 environment versions (`python`, `numpy`) are excluded for the same reason as A2.
  A5 prose quotes at its own precision: `−2.062033944485` appears as `−2.0620`, `8.1334e-5` as `8.1e-5`.
     Exact token equality called 88 lines invented; attestation now also accepts a value within half a unit
     of the last written digit, and that tier is counted and disclosed as `rounded`, never merged into the
     exact tiers.
  A8 the hard verdict is "no committed record ANYWHERE contains this value", not "the anchored round does
     not". A round-level test alone called 26 lines invented, and most of them were a value quoted about one
     round while recorded by the round that actually measured it - that is §49's cross-round shape, and the
     answer is disclosure with the holder listed, not a red. The anchored-mismatch is still visible: it is
     exactly the `value_of_other_round` population.
  A7 recorded numerically rather than as text: `1e-9` in prose and `1e-09` in JSON are the same quantity.
  A9 round families are matched case-insensitively: two of the three attestation tiers had been empty all
     along because the artifact names are lowercase and the documents uppercase. A tier that loads nothing is
     not a tier, and the hard verdict was firing on values the round's own preregistration does contain.
  A6 a number that names a section of the document it appears in (headings and §-references of that same
     file) is a reference: `### 10.6 复现（Phase V）` and `15.2 的锚定要求` were being read as quantities.
  A11 found by this layer's own validator, not by hand: the A7 numeric comparison was written as
     `v in d["prereg_floats"]`, a *string* against a list of *floats*, so the branch could never be true and
     the tier that was supposed to implement "recorded numerically, not as text" silently never ran - the
     only thing catching such a value was the `rounded` tier, which is a weaker claim than the one registered.
     Corrected to compare floats. Measured delta of the fix alone, same corpus and same rows:
     `matches_round_records` 39 → 51, `value_only_in_transcription` 43 → 33, `value_of_other_round` 45 → 43,
     `rounded_matches` 40 → 29, hard findings 6 → 6 (the hard base is repo-wide, so no finding could be lost).
  A12 the arabic round anchor `phase(13)` was matched case-sensitively while prose writes `Phase 13`, so those
     lines got no anchor at all and were disclosed as `criterion_without_anchor` instead of being checked.
     Widening the anchor set moves lines from "not checked" into "checked": it can add findings and can never
     remove one. Measured delta: `criterion_without_anchor` 724 → 720, hard findings 6 → 6.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
JSON_OUT = GOV / "value_provenance_v1.json"
MD_OUT = GOV / "VALUE_PROVENANCE_v1.md"
REPORT = M / "M2A_FINAL_REPORT.md"
LOG = GOV / "NEGATIVE_AND_NULL_EVIDENCE_LOG.md"
LEDGER = GOV / "OBLIGATION_REGISTRY.md"
RUNS_DIR = M / "report"
RECORD_DIRS = (M / "experiments", M / "literature")

SELF_OUT = {JSON_OUT.name, MD_OUT.name}
SELF_SUITE = "value_provenance_gate.py"
# declared transcriptions: derived tables of other layers whose rows are copies of the claims below
LAYER_TRANSCRIPTIONS = {"SUITE_SCORE_REGISTRY_v1.md": "another layer's table of suite scores (X-94)",
                        "suite_score_registry_v1.json": "same, machine form",
                        "LABEL_PROVENANCE_v1.md": "another layer's table of verdict labels (X-94)",
                        "label_provenance_v1.json": "same, machine form",
                        "SECTION_PAGE_RECONCILIATION_v1.md": "page-vs-repo table, derived",
                        "section_page_reconciliation_v1.json": "same, machine form"}

NUM = re.compile(r"(?<![\w.])([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?![\w.])")
# A1 the repository writes minus as U+2212, so a slope quoted as −2.062033944485 never matched the
#    artifact's -2.062033944485: sign-normalise before comparing, or the layer judges its own encoding.
MINUS = "\u2212\u2013\u2014"
MARKER = re.compile(r"[≤≥±]|(?:δ|Δ|eps|tol|tolerance|容差|阈值|门槛|精度|步长|网格|种子)[^\n]{0,3}?")
MEASURE = re.compile(r"(?<![\w.])[-+]?\d+\.\d+(?:[eE][-+]?\d+)?(?![\w.])"
                     r"|(?<![\w.])[-+]?\d+[eE][-+]?\d+(?![\w.])")
GOV_TABLE = re.compile(r"_v\d+\.md$")
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18,
         "XIX": 19, "XX": 20, "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25}


def artifact_files():
    return sorted(set(list((M / "experiments").glob("phase*.json"))
                      + list((M / "literature").glob("*.json"))
                      + list((M / "report").glob("*.json"))))


def numbers_in(text: str) -> set:
    return set(NUM.findall(text.translate({ord(c): "-" for c in MINUS})))


def family_of_name(name: str):
    # A9 the pattern was case-sensitive, so PHASE13_PREREGISTRATION.md and PHASE13_RESULTS.md never joined
    # their round: the "frozen before running" and "transcription" tiers were empty for every family, and the
    # layer was silently one-tier (artifact only) while claiming three.
    m = re.search(r"phase(\d+)", name, re.I)
    if m:
        return int(m.group(1))
    return None


def population_a():
    """Per round: the three attestation tiers, kept separate because they justify different verdicts."""
    fam = {}
    for p in artifact_files():
        n = family_of_name(p.name)
        if n is None:
            continue
        d = fam.setdefault(n, {"artifact": set(), "prereg": set(), "transcription": set(), "files": []})
        d["artifact"] |= numbers_in(json.dumps(json.loads(p.read_text(encoding="utf-8"))))
        d["files"].append(str(p.relative_to(M)))
    for p in sorted((M / "experiments").glob("PHASE*_PREREGISTRATION.md")):
        n = family_of_name(p.name)
        if n is None:
            continue
        d = fam.setdefault(n, {"artifact": set(), "prereg": set(), "transcription": set(), "files": []})
        d["prereg"] |= numbers_in(p.read_text(encoding="utf-8"))
    for p in sorted((M / "experiments").glob("PHASE*_RESULTS.md")):
        n = family_of_name(p.name)
        if n is None:
            continue
        d = fam.setdefault(n, {"artifact": set(), "prereg": set(), "transcription": set(), "files": []})
        d["transcription"] |= numbers_in(p.read_text(encoding="utf-8"))
    for p in sorted((M / "literature").glob("ROUND_*.md")):
        d = fam.setdefault("L01", {"artifact": set(), "prereg": set(), "transcription": set(), "files": []})
        d["transcription"] |= numbers_in(p.read_text(encoding="utf-8"))
    for p in artifact_files():
        if p.name.startswith("L01") or "phase1prime" in p.name:
            d = fam.setdefault("L01", {"artifact": set(), "prereg": set(), "transcription": set(), "files": []})
            d["artifact"] |= numbers_in(json.dumps(json.loads(p.read_text(encoding="utf-8"))))
            d["files"].append(str(p.relative_to(M)))
    out = {}
    for k, v in fam.items():
        fl = []
        for tok in set(v["artifact"]) | set(v["prereg"]) | set(v["transcription"]):
            try:
                fl.append(float(tok))
            except ValueError:
                pass
        bytier = {}
        for tier in ("artifact", "prereg", "transcription"):
            s = set()
            for tok in v[tier]:
                f = as_float(tok)
                if f is not None:
                    s.add(f)
            bytier[tier + "_floats"] = sorted(s)
        out[k] = {"artifact": sorted(v["artifact"]), "prereg": sorted(v["prereg"]),
                  "transcription": sorted(v["transcription"]), "files": sorted(set(v["files"])),
                  "floats": sorted(set(fl)), "floatset": frozenset(fl),
                  "prereg_values": len(v["prereg"]), "artifact_values": len(v["artifact"]),
                  "transcription_values": len(v["transcription"]),
                  "files": sorted(set(v["files"]))}
        out[k].update(bytier)
    return out


def corpus():
    docs = [(REPORT, "append_only"), (LOG, "append_only"), (LEDGER, "regenerated")]
    tables = [p for p in sorted(GOV.glob("*.md")) if GOV_TABLE.search(p.name)
              and p.name not in SELF_OUT and p.name not in LAYER_TRANSCRIPTIONS]
    docs += [(p, "derived_summary") for p in sorted(RUNS_DIR.glob("*.md")) + tables]
    docs += [(p, "run_record") for d in RECORD_DIRS for p in sorted(d.glob("*.md"))
             if not re.search(r"PREREG", p.name)]
    return [(p, kind) for p, kind in docs if p.exists() and p.name not in SELF_OUT]


def anchors_of(line, rounds):
    fam, phan = set(), set()
    line = line.translate({ord(c): "-" for c in MINUS})
    for m in re.finditer(r"Phase\s+([IVX]+)(?:′|')?(\s*[–—-]\s*(?:Phase\s+)?([IVX]+))?", line):
        ns = []
        for r in [m.group(1), m.group(3)]:
            if r is None:
                continue
            n = ROMAN.get(r)
            if n is None:
                phan.add("unparsed")
            else:
                ns.append(n)
        if len(ns) == 2 and None not in ns and ns[1] > ns[0]:
            ns = list(range(ns[0], ns[1] + 1))
        for n in ns:
            (fam if n in rounds else phan).add(n)
    for m in re.finditer(r"\bphase\s*(\d+)[a-z]?(?![A-Za-z0-9])", line, re.I):
        # A12 the arabic form was matched case-sensitively AND only glued to the word (`phase13`, the file
        #    naming style), while prose writes `Phase 13` with a space, so those lines carried no anchor at all and
        # the line was disclosed as
        # `criterion_without_anchor` instead of being checked, and the validator's synthetic probes - which
        # write round numbers in the same arabic form a reader would - refused to fire. A widening of the
        # anchor set can only move lines from "not checked" to "checked", so it can add findings but never
        # remove one; the delta is printed by the re-derivation and disclosed in the report.
        n = int(m.group(1))
        (fam if n in rounds else phan).add(n)
    if re.search(r"\bL01\b|\bPhase I′\b", line):
        fam.add("L01")
    return fam, phan


def section_numbers(text: str):
    """Every section number this document itself uses: headings plus §-references inside it."""
    nums = set(re.findall(r"^\s*#+\s*(\d+(?:\.\d+)*)", text, re.M))
    nums |= set(re.findall(r"§\s*(\d+(?:\.\d+)*)", text))
    return {n for n in nums if any(c.isdigit() for c in n)}


def looks_like_reference(line: str, start: int, end: int, tok: str):
    """A2/A3: section references and version strings are not criterion values.

    `§4.1`, `### 10.6`, `15.2 的清单` reference prose, not a registered quantity; `python 3.10.12`,
    `numpy 2.2.6` are environment strings, and an unanchored exponent regex also cut `2e338` out of a
    sha256 prefix. Each of these produced hard findings in the pre-run probe, so the shape rule rejects
    them: a decimal is a reference if it heads its line/heading or follows §, if it is one link of a
    longer dotted chain, or if it is the section number of the document it appears in.
    """
    head = line[:start]
    if re.search(r"§\s*$|§\s*$|第\s*$", head[-3:]):
        return True
    if re.match(r"^\s*#+\s*\d+(\.\d+)*\s", line):        # "### 10.6 复现（Phase V）"
        return True
    if tok in DOC_SECTIONS:                                   # 15.2 / 15.4 name sections of this file
        return True
    if head.endswith(".") and re.search(r"\d\.$", head):          # 15.2 written as "15." + "2"
        return True
    if start and line[start - 1] in ".":
        return True
    if end < len(line) and line[end] == ".":
        return True
    if re.search(r"(python|numpy|版本|v\d)\s*$", head, re.I):
        return True
    return False


def criterion_values(line: str):
    line = line.translate({ord(c): "-" for c in MINUS})
    out = set()
    for m in MEASURE.finditer(line):
        if not looks_like_reference(line, m.start(), m.end(), m.group(0)):
            out.add(m.group(0))
    for m in NUM.finditer(line):
        head = line[max(0, m.start() - 3):m.start()]
        if (re.search(r"[≤≥±]|\d$", head) and MARKER.search(line[max(0, m.start() - 40):m.start()])
                and not looks_like_reference(line, m.start(), m.end(), m.group(1))):
            out.add(m.group(1))
    return {v for v in out if v not in ("", ".")}


DOC_SECTIONS = set()


def claims(rounds):
    global DOC_SECTIONS
    rows = []
    for p, kind in corpus():
        rel = str(p.relative_to(M))
        text = p.read_text(encoding="utf-8", errors="replace")
        DOC_SECTIONS = section_numbers(text)
        for i, line in enumerate(text.splitlines(), 1):
            vals = criterion_values(line)
            if not vals:
                continue
            rows.append({"document": rel, "kind": kind, "line": i,
                         "values": sorted(vals), "excerpt": line.strip()[:150],
                         "_line": line})
    return rows


def decimals_of(tok: str):
    m = re.match(r"^([-+]?\d*)(?:\.(\d*))?(?:[eE]([-+]?\d+))?$", tok)
    if not m:
        return None
    ip, fp, ep = m.groups()
    if not fp:
        return None
    return len(fp), (int(ep) if ep else 0)


def tolerance(tok: str):
    d = decimals_of(tok)
    if d is None:
        return 0.0
    dec, exp = d
    return 0.5 * 10 ** (exp - dec)


def near(tok, floats):
    """A5: does the round hold this number at the precision the prose writes it?

    Prose rounds: `−2.062033944485` is quoted as `−2.0620`, `8.1334e-5` as `8.1e-5`. Token equality would
    call every one of those invented, which is the layer judging its own rounding instead of the repository.
    A value counts as near when some recorded number falls within half a unit of the last written digit.
    """
    tol = tolerance(tok)
    if tol == 0.0:
        return False
    try:
        v = float(tok)
    except ValueError:
        return False
    return any(abs(f - v) <= tol for f in floats)


def as_float(tok):
    try:
        return float(tok)
    except ValueError:
        return None


def tier_of(v, fam, arts):
    """A7: recorded numerically, not as text - the same quantity prints as `1e-9` in prose and `1e-09` in
    JSON, and an equality test on those strings measures formatting, not the repository.
    A11: the comparison has to be made against the tier's *float* list, and `as_float` is the only safe way to
    get there. Written as `v in d["prereg_floats"]` (a str against a list of floats) the branch can never be
    true, so A7 was silently not running and the only tier left to catch such a value was `rounded`."""
    fv = as_float(v)
    where = {}
    for a in fam:
        d = arts.get(a, {"artifact": [], "prereg": [], "transcription": [], "floats": [],
                         "artifact_floats": [], "prereg_floats": [], "transcription_floats": []})
        exact = fv is not None and fv in d["floatset"]
        if v in d["prereg"] or (exact and fv in d["prereg_floats"]):
            where[a] = "prereg"
        elif v in d["artifact"] or (exact and fv in d["artifact_floats"]):
            where[a] = "artifact"
        elif v in d["transcription"] or (exact and fv in d["transcription_floats"]):
            where[a] = "transcription"
        elif near(v, d["floats"]):
            where[a] = "rounded"
    return where


def other_rounds(v, rounds, arts):
    fv = as_float(v)
    out = []
    for a in rounds:
        d = arts[a]
        if v in d["prereg"] or v in d["artifact"] or (fv is not None and fv in d["floatset"]) \
                or near(v, d["floats"]):
            out.append(a)
    return out


def classify(rows, arts):
    rounds = set(k for k in arts if isinstance(k, int))
    out = []
    for r in rows:
        fam, phan = anchors_of(r["_line"], rounds)
        entry = {k: v for k, v in r.items() if k != "_line"}
        entry["anchors"] = sorted(str(x) for x in fam)
        entry["phantom"] = sorted(str(x) for x in phan)
        per = []
        for v in r["values"]:
            where = tier_of(v, fam, arts)
            elsewhere = other_rounds(v, rounds, arts)
            per.append({"value": v, "attested_in": {str(k): vv for k, vv in where.items()},
                        "registered_by_other_round": sorted(str(x) for x in elsewhere)})
        entry["per_value"] = per
        if phan and not fam:
            entry["verdict"] = "anchor_without_records"
        elif not fam:
            entry["verdict"] = "criterion_without_anchor"
        else:
            missing = [p for p in per if not p["attested_in"]]
            nowhere = [p for p in missing if not p["registered_by_other_round"]]
            if missing and not nowhere:
                entry["verdict"] = "value_of_other_round"
            elif nowhere:
                entry["verdict"] = ("stale_value_in_register" if r["kind"] == "regenerated"
                                    else "value_unattested_in_repo")
            elif any(list(p["attested_in"].values())[0] == "transcription" for p in per):
                entry["verdict"] = "value_only_in_transcription"
            else:
                entry["verdict"] = "matches_round_records"
        out.append(entry)
    return out


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    arts = population_a()
    rows = classify(claims(set(k for k in arts if isinstance(k, int))), arts)
    order = ["anchor_without_records", "value_unattested_in_repo", "stale_value_in_register",
             "value_of_other_round", "value_only_in_transcription", "matches_round_records",
             "criterion_without_anchor"]
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in order}
    counts["hard_findings"] = sum(counts[v] for v in order[:3])
    counts["rounded_matches"] = sum(1 for r in rows for p in r["per_value"]
                                    if list(p["attested_in"].values()) == ["rounded"])
    counts["claim_values"] = sum(len(r["values"]) for r in rows)
    counts["claim_documents"] = len({r["document"] for r in rows})
    counts["corpus_documents"] = len(corpus())
    counts["round_families"] = len(arts)
    doc = {
        "schema": "value_provenance_v1",
        "question": "is a criterion value attributed to a round present in that round's own records",
        "claim_shape": "a number with a decimal/exponent, or within three characters of a criterion marker, "
                       "on a line that also names a round",
        "attestation_tiers": ["prereg (frozen before running)", "artifact (recorded by the run)",
                              "run_record (transcription, disclosed)"],
        "asymmetry": "wide support, narrow claims: every relaxation here can only remove findings",
        "registered_exits": order,
        "hard_exits": order[:3],
        "attestation_tiers_used": ["prereg", "artifact", "transcription", "rounded"],
        "generator": {"file": str(pathlib.Path(__file__).resolve().relative_to(M)),
                      "sha256": sha(pathlib.Path(__file__).read_bytes())},
        "self_excluded": sorted(SELF_OUT),
        "declared_transcriptions": sorted(LAYER_TRANSCRIPTIONS),
        "counts": counts,
        "round_records": {str(k): {"files": v["files"], "prereg_values": len(v["prereg"]),
                                   "artifact_values": len(v["artifact"]),
                                   "transcription_values": len(v["transcription"])}
                          for k, v in sorted(arts.items(), key=lambda x: str(x[0]))},
        "rows": rows,
    }
    JSON_OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 判定容差↔轮次记录对账 v1（VALUE_PROVENANCE_v1）", "",
             "问题：散文归给某一轮的判据数值（容差、阈值、指数、步长、种子数），在那一轮自己的记录里存在吗？"
             "（GOVERNANCE_ARTIFACT，不跑实验、不改任何注册判据）", "",
             "生成本表的推导器源码 SHA-256：`%s`；轮次家族 %d 个，语料文档 %d 份，主张行 %d 行 / 数值 %d 个 / "
             "承载文档 %d 份。" % (doc["generator"]["sha256"][:16], len(arts), counts["corpus_documents"],
                             len(rows), counts["claim_values"], counts["claim_documents"]),
             "", "| 判定 | 条数 |", "|---|---|"]
    for v in order:
        lines.append("| `%s` | %d |" % (v, counts[v]))
    lines.append("| **硬伤合计** | **%d** |" % counts["hard_findings"])
    lines += ["", "主张口径（写死）：带小数点或指数的数，或距判据标记（≤ ≥ ± δ 容差 阈值 门槛 精度 步长 网格 种子）"
              "三个字符以内的数；日期与「243 格」这类裸整数不算主张，否则本层判的就是自己的解析而不是仓库。", ""]
    lines += ["硬伤逐条：", ""]
    for r in rows:
        if r["verdict"] in order[:3]:
            lines.append("- `%s:%d` %s → %s ｜ 摘录：%s"
                         % (r["document"], r["line"], r["verdict"],
                            json.dumps([p["value"] for p in r["per_value"] if not p["attested_in"]],
                                       ensure_ascii=False), r["excerpt"][:90]))
    lines += ["", "跨轮搬运（只披露，不判红：数值确实注册过，但注册它的是别的轮次——R9 的形状）：", ""]
    for r in rows:
        if r["verdict"] == "value_of_other_round":
            mv = [(p["value"], p["registered_by_other_round"]) for p in r["per_value"]
                  if not p["attested_in"] and p["registered_by_other_round"]]
            lines.append("- `%s:%d` 锚点 %s ｜ %s ｜ %s" % (r["document"], r["line"],
                                                        ",".join(r["anchors"]), mv, r["excerpt"][:80]))
    lines.append("")
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote value_provenance_v1.json | rows %d values %d hard %d dist %s"
          % (len(rows), counts["claim_values"], counts["hard_findings"],
             json.dumps({v: counts[v] for v in order}, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
