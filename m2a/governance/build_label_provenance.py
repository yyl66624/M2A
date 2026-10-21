"""§49 - build the label-provenance table: can a verdict label written in prose be refuted by the
artifact of the round it talks about?

GOVERNANCE_ARTIFACT. No experiment is run, no round verdict is altered, nothing frozen is touched (R6).

QUESTION (the only one with authority). Rule 7 requires every round to distinguish SUPPORTED /
CONTRADICTED / NULL / INDETERMINATE / NOT_IDENTIFIED. The artifacts were written under four older label
systems, so every prose sentence that says 「Phase XII: SUPPORTED」 leans on a translation. §37's table is
instrumented for its own counts and G8 checks prose-against-prose suite scores, but nothing so far pairs a
quoted label with the artifact of the round the sentence names. Here it is.

POPULATION A (authoritative, read-only). Every JSON in `experiments/phase*.json`,
`experiments/p5_v1_posthoc.json`, `literature/*.json`, `report/*.json`. A label is a string stored under one
of the registered keys: `verdict`, `exit`, `status`, `outcome`, `exit_reason`, or any key beginning `label`
or ending `_label`. Per file we keep the raw strings and the five-label set obtained by applying
`build_status_label_table.RULES` - the same registered mapping the §37 layer uses, imported, never re-typed,
so this step cannot quietly widen what counts as a translation.

POPULATION B (claims). Prose lines carrying a label-shaped token, from the same document kinds as §48:
`append_only` (final report, negative log), `regenerated` (obligation ledger), `derived_summary`
(`report/*.md` + governance `*_v*.md` tables), `run_record` (`experiments/*.md`, `literature/*.md`). The
label vocabulary is FIVE plus the registered RULES tokens plus artifact raw labels that look like verdict
tokens (`^[A-Z][A-Z0-9_-]{3,}$`); nothing else is treated as a claim, so no sentence is judged by a word that
was never a verdict.

ANCHOR. A line is paired with a round only when it names one: `Phase <roman>` / `Phase I′` / `phase<N>` in a
code span / a literature round written `L02` **or** `L-02`. The literature families are derived from the
artifacts that exist (`literature/L<nn>_*`), not from a list (A12). Resolution is by registered phase number
(derived from the artifact file names, not typed).

VERDICTS - the registered exit order, frozen before the first run:
  L1 `anchor_phantom`        HARD  - the line names a phase number outside the registered set, yet states a
                                      verdict for it: a judgement about a round that has no artifact.
  L2 `label_wrong_for_anchor` HARD  - the anchor resolves, but the label's five-value is not among the values
                                      that round's artifacts record.
  L3 `label_unregistered`     HARD  - the token is neither FIVE, nor a RULES key, nor a raw label of that
                                      round: a verdict word nobody registered.
  L4 `stale_in_register`      HARD  - same as L2 but the document is `regenerated` (OBLIGATION_REGISTRY.md):
                                      no history excuse exists for a file that is rewritten from rows.
  L5 `label_without_anchor`   disclosed - a label token on a line that names no round: listed, not judged.
  L6 `five_label_only_in_translation` disclosed - the quote is FIVE and matches the round's five-value, but the
                                      round's artifacts never write that word literally (the NULL /
                                      NOT_IDENTIFIED gap §37 registered).
  `matches_artifact`          disclosed-clean.
STOP RULE: a hard finding that cannot be removed by an appended correction or by regenerating a derived
document is registered as a finding and reported as-is. The criteria are not relaxed and no historical
document is rewritten.

ASymmetry that keeps this honest (deliberate, and weaker-on-purpose): pairing is at ROUND level, not arm
level. A round that records `E1 CONFIRMED` and `E2 ...` accepts either, so arm-level disagreement cannot
manufacture a red here; it can only be missed. Same direction as §47's tier asymmetry: looseness may remove
findings, never invent them.

SELF-REFERENCE. `build_label_provenance.py` writes both outputs of this table; neither is ever read as
population A or B (an artifact must not attest its own drift). The validator's own name is kept out of any
suite-score machinery; §48 owns scores, this layer owns labels.

COST. Every prose iteration costs a full corpus re-scan (seconds - no suite is run), and population A is
re-read from JSON on every derivation.

AMENDMENTS made after §49's first readings, each one a widening or a fix of this instrument
and none a relaxation of any round's judgement (R6):
  A12 the anchor set is derived (every `literature/L<nn>_*` family) and accepts the hyphenated prose form.
     X-105 registered the hole: the anchor was the literal `\bL01\b`, so a verdict sentence about L-02 - and
     most sentences about L-01, which the report writes 「Round L-01」 / 「L-01」 - had no anchor at all. That
     is what made `label_without_anchor` the largest tier (411 of 639 rows) and the least informative.
  A13 a label counts as a claim about the anchored round only when a verdict predicate is in the SAME clause
     as it (no clause boundary, no other vocabulary token between). Without this, A12 would mint refutations:
     a register row that explains the rho -> five-value mapping by listing four tokens in one cell would be
     read as judging each of them of that round. Narrowing only - it can remove hardings, never add them.
  A14 `family_artifacts` receives the anchor strings stored in an entry, and `family_of` compared
     `int(...) == anchor`, so every numeric anchor resolved to no artifacts there and the declared
     `cross_round_refutation` tier could never fire - a rule with no teeth (X-51's shape, found here because
     A12 made the same expression a family lookup).
  A15 (after the readings, dated 订正 X-110) two of the three hardings A12 produced are this repository's
     own wording: a count of the §37 table's prose-only rows, written as though it were a round's judgement.
     They are re-attributed by an errata whose marker string must be present in the log to count. The third
     sits in `literature/ROUND_L01_RESULTS.md`, a frozen input of `literature/l02_gate.py` G2 (X-108), so it
     cannot be appended to and is reported as-is - the stop rule's own case, not an exemption.
  A16 (after the readings, same step as A13) the `NOT_RESOLVABLE`/Phase XIV errata entry leaves the list:
     under A13 that label is no longer predicated in the same clause as the round it names, so the entry had
     no row left to silence. Q11's "no registered correction points at nothing" conjunct is the reason this
     is visible at all - a padding errata would look exactly like a vestigial one. The published correction
     stays in the log text (R6); only the instrument's registration list changes.
BEFORE THE FIRST RUN:
  A1 population A also reads `exits[taken_first_exit]` and any key naming a label/verdict/exit/outcome/status.
     The first key set was typed from five names and missed that field, which made Phase XV/XVII look
     label-less - a false `label_wrong_for_anchor`, and an empty allow-list is never a refutation.
  A2 the claim vocabulary is the registered dispositions plus label strings artifacts actually recorded.
     Instrument states (`PASS`, `IDENTITY_VERIFIED`) are recorded but are not round verdicts: treating them
     as verdicts produced 16 false hardings, so they get their own disclosed category instead.
  A4 the key scan was anchored (`.match`), so `exits[taken_first_exit]` stayed invisible even after A1
     said to read it, cell-level `state` fields were not read at all, and `Phase XIX-XXII` resolved to
     round 19 alone - three ways of inventing a refutation by looking at too little.
  A5 `*PREREG*.md` leaves the claim population: a registered exit name in a document written before the
     reading is not a claim about a verdict, and the file is frozen anyway (R6).
  A6 registered dispositions that carry no five-value (`MANUAL_REVIEW`, `COUNT_NOT_STATUS`,
     `ZERO_TEST_REANALYSIS`) are `not_a_round_verdict`: §37's own disposition words were being judged as
     if they were round verdicts.
  A7 a row that both matches and contradicts its round is `paired_correction` (disclosed): the contradicted
     label is quoted as the retracted one, exactly §48's E5 shape.
  A8 an anchored round whose artifacts record no five-value at all yields `anchor_without_recorded_label`
     (disclosed). An empty allow-list is not a refutation.
  A9 a quoted label is a claim only when the FULL line (not the display excerpt - the first pass truncated
     at 160 characters and thereby lost both the refuting round and the predicate in long table rows)
     predicates it of the round (判为/记为/判定/出口/verdict/label_reported). Otherwise a cell-state NAME mentioned while comparing two rounds reads as a
     verdict about the wrong one, and the instrument would be judging its own parsing, not the repository.
     Narrowing only: it can remove hardings, never add them.
  A10 cross-round refutation is disclosed, not judged: 「Phase IV 的形式不变在跨系统层面被否证」 is true, and
     the refuting reading belongs to the later round's artifact. A round-level pairing cannot express
     "round A's claim, refuted by round B", so the row is listed under its own category rather than forced
     into a mismatch - and the wording of the claim, not its truth, is what this layer is measuring.
  A11 the two rows that stayed hard are corrections, not relaxations: the negative log predicates
     `REFUTED` of Phase IV and `NOT_RESOLVABLE` of Phase XIV while those rounds' artifacts record
     `SUPPORTED` and lowercase cell booleans. A hard row may only fall silent when an ERRATA entry names
     it AND its marker string is present in that document, so the correction has to be published to be
     counted (X-85's precedent: an appended correction, never a rewritten history).
  A3 a quoted word that some artifact records, but not the anchored round, is `attested_in_other_round`
     (disclosed) rather than "a verdict word nobody registered". Only a BOLD verdict-shaped token that no
     artifact and no registration knows is `label_unregistered`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
JSON_OUT = GOV / "label_provenance_v1.json"
MD_OUT = GOV / "LABEL_PROVENANCE_v1.md"
REPORT = M / "M2A_FINAL_REPORT.md"
LOG = GOV / "NEGATIVE_AND_NULL_EVIDENCE_LOG.md"
LEDGER = GOV / "OBLIGATION_REGISTRY.md"
RUNS_DIR = M / "report"
RECORD_DIRS = (M / "experiments", M / "literature")

SELF_OUT = {JSON_OUT.name, MD_OUT.name}
# Cycle prevention, registered before this layer's first re-derivation (X-95, following X-94). The value
# layer's table is built from the *same* prose corpus as this one and its rows are excerpts of claims this
# layer already finds in the source document. Scanning it would (a) duplicate every transcribed claim into a
# new row whose document is a derived table, and (b) make the two layers each re-derive the other's corpus,
# which is the shape that made a single closing audit unorderable in X-94.
TRANSCRIBED = {"VALUE_PROVENANCE_v1.md": "the value layer's table; its rows are excerpts of claims found here",
               "value_provenance_v1.json": "same, machine form"}
KEYS = ("verdict", "exit", "status", "outcome", "exit_reason")
LABEL_KEY = re.compile(r"(label|verdict|exit|outcome|status|state)", re.I)
VERDICT_TOKEN = re.compile(r"^[A-Z][A-Z0-9_-]{3,}$")
# A hard row is silenced only by a correction that is really in the document: the errata table names what
# it re-attributes, and the marker string must occur in that file (§47's route, not a whitelist in code only).
ERRATA = [{"xid": 92, "document": "governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md",
           "quoted": "REFUTED", "anchor": "4", "marker": "订正 X-92",
           "replacement": "由 Phase VI 的跨系统复验否证"},
          {"xid": 110, "document": "governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md",
           "quoted": "NULL", "anchor": "L01", "marker": "订正 X-110",
           "replacement": "那一句说的是 §37 口径表里「仅出现在文档措辞中」的那一行计数，不是 L-01 的判定"},
          {"xid": 110, "document": "governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md",
           "quoted": "PARTIALLY_IDENTIFIED", "anchor": "L01", "marker": "订正 X-110",
           "replacement": "那一句说的是该标签在语料里没有指称对象，不是把该标签判给任何一轮"}]


def errata_live(entry, label, doc_text, full=""):
    """A correction silences the row it corrects, never itself: the row that carries the marker is the
    claim being audited too, so applying the errata to it would launder the correction into evidence."""
    return [e for e in ERRATA if e["marker"] in doc_text and e["marker"] not in full
            and e["document"] == entry["document"]
            and e["quoted"] == label and e["anchor"] in entry["anchors"]]


PREDICATE = re.compile(r"判为|记为|判定|出口|verdict|label_reported|判\s*\*\*|→\s*\*\*")
CROSS = re.compile(r"跨系统|跨 `k`|cross-system")
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18,
         "XIX": 19, "XX": 20, "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25}

sys.path.insert(0, str(GOV))
import build_status_label_table as T  # noqa: E402  the registered translation layer, imported not re-typed

FIVE = list(T.FIVE)
RULES = T.RULES


def is_label_key(k: str) -> bool:
    return k in KEYS or bool(LABEL_KEY.search(k))


def artifact_files():
    return sorted(set(list((M / "experiments").glob("phase*.json"))
                      + list((M / "experiments").glob("p5_v1_posthoc.json"))
                      + list((M / "literature").glob("*.json"))
                      + list((M / "report").glob("*.json")))
                  - {JSON_OUT})


def walk_labels(node, sink):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and is_label_key(k):
                sink.append((k, v))
            elif isinstance(v, (dict, list)):
                walk_labels(v, sink)
    elif isinstance(node, list):
        for v in node:
            walk_labels(v, sink)


def population_a():
    """One row per artifact: raw label strings and the five-values the registered mapping yields for them."""
    out = {}
    for p in artifact_files():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        sink = []
        walk_labels(d, sink)
        raw = {}
        five = set()
        for k, v in sink:
            raw.setdefault(v, []).append(k)
            fv = five_of(v)
            if fv:
                five.add(fv)
        out[str(p.relative_to(M))] = {"raw": raw, "five": sorted(five)}
    return out


def five_of(label: str):
    """Translate a raw label into a five-value using ONLY the registered mapping (exact token, then the
    longest registered token that the label contains - exit strings like 'E1 RATE-LAW EXACT')."""
    up = label.strip().upper()
    if label in FIVE:
        return label
    if label in RULES:
        return RULES[label][0]
    if up in FIVE:
        return up
    if up in RULES:
        return RULES[up][0]
    # containment must be a whole component: "UNSUPPORTED-TOKEN".upper() contains "SUPPORTED" as a
    # substring, and translating it would invent a verdict the artifact never recorded.
    parts = [q for q in re.split(r"[^A-Z0-9-]+", up) if q]
    parts += [q for p in parts for q in p.split("-") if q]
    best = None
    for tok in RULES:
        if tok in parts and (best is None or len(tok) > len(best)):
            best = tok
    return RULES[best][0] if best else None


def registered_phases(arts):
    """Phase numbers that really have an artifact, derived from the file names."""
    nums = set()
    for rel in arts:
        m = re.search(r"phase(\d+)", rel)
        if m:
            nums.add(int(m.group(1)))
    return nums


def family_of(anchor_num, arts):
    """Artifacts belonging to a round family: phase12_results.json, and phase5b for anchor 5 (sub-rounds).

    The coercion is the cross-round fix (A14): callers that pass the anchors read back out of an entry hand
    over strings, and `int(...) == "4"` is never true, so a numeric anchor silently resolved to no artifacts.
    An anchor that is not a phase number yields no artifacts - an empty allow-list, which the classifier
    reports as `anchor_without_recorded_label` rather than as a refutation."""
    try:
        anchor_num = int(anchor_num)
    except (TypeError, ValueError):
        return []
    hits = []
    for rel in arts:
        m = re.search(r"phase(\d+)", rel)
        if m and int(m.group(1)) == anchor_num:
            hits.append(rel)
    return hits


LIT = re.compile(r"\bL[-–]?(\d\d)(?![A-Za-z0-9])")
CLAUSE = re.compile(r"[，,。；;、！!？?|/／]")
# The families are the ones that actually have artifacts, derived from the artifact paths - the same lesson
# §52 applied to the obligation ledger (X-107): an enumerated namespace is a list the next round is not on.
# Computed at import so a validator that calls classify() directly sees exactly what the deriver sees.
def lit_families(arts):
    return {"L" + m.group(1) for m in (re.match(r"literature/L(\d\d)_", r) for r in arts) if m}


LIT_FAMS = lit_families(population_a())
# L-01's artifacts quote five-value words for the rounds being translated rather than the round being judged,
# so a cross-round test that let L01 into the union would call a correct L-02 reading a refutation of L-01.
# The exemption predates this amendment; it is named here instead of buried in a comparison.
CROSS_EXEMPT = {"L01"}


def predicate_attaches(line, lab, toks):
    """A label is a claim about the anchored round only when a verdict predicate sits in the SAME clause as
    it: no clause boundary and no other vocabulary token between. A line that merely enumerates the
    vocabulary (a row explaining the rho -> five-value mapping lists several tokens in one cell) therefore
    predicates nothing of any round. Narrowing only: it can remove hardings, never add them."""
    others = [t for t in toks if t != lab]
    other = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(others, key=len, reverse=True))
                       + r")\b") if others else None
    for pm in PREDICATE.finditer(line):
        for lm in re.finditer(r"\b" + re.escape(lab) + r"\b", line):
            lo, hi = (pm.end(), lm.start()) if pm.end() <= lm.start() else (lm.end(), pm.start())
            if lo > hi:
                continue          # an inverted region means the two spans overlap: ambiguous, not attached
            seg = line[lo:hi]
            if other and other.search(seg):
                continue
            if not CLAUSE.search(seg):
                return True
    return False


def anchors_of(line, nums):
    """Return (resolved families, phantom numbers) mentioned by this line."""
    fam, phan = set(), set()
    for m in re.finditer(r"Phase\s+([IVX]+)(?:′|')?(\s*[–—-]\s*(?:Phase\s+)?([IVX]+))?", line):
        romans = [m.group(1)]
        if m.group(3):
            romans.append(m.group(3))
        ns = [ROMAN.get(r) for r in romans]
        if None not in ns and len(ns) == 2 and ns[1] > ns[0]:
            ns = list(range(ns[0], ns[1] + 1))
        for n in ns:
            # a roman the table cannot parse is still a round the prose is judging: phantom, not noise
            if n is None or n not in nums:
                phan.add(n if n is not None else "unparsed")
            else:
                fam.add(n)
    for m in re.finditer(r"\bphase(\d+)[a-z]?(?![A-Za-z0-9])", line):
        n = int(m.group(1))
        (fam if n in nums else phan).add(n)
    for m in LIT.finditer(line):
        if "L" + m.group(1) in LIT_FAMS:
            fam.add("L" + m.group(1))
    return fam, phan


def family_artifacts(anchor, arts):
    anchor = str(anchor)
    if anchor in LIT_FAMS:
        hits = [r for r in arts if r.startswith("literature/" + anchor)]
        if anchor == "L01":
            hits += [r for r in arts if r == "literature/phase1prime_gate3_check.json"]
        return hits
    return family_of(anchor, arts)


DISPOSITIONS = (set(FIVE) | {v[0] for v in RULES.values()}
                | {k for k in RULES if VERDICT_TOKEN.match(k)}
                | {"MANUAL_REVIEW", "ZERO_TEST_REANALYSIS", "COUNT_NOT_STATUS"})


def vocab(arts):
    """Claim tokens are the registered dispositions plus every label string some artifact actually
    recorded. Instrument states (PASS, IDENTITY_VERIFIED) are recorded, so they are quotable - but they
    pair to nothing, and the classifier says so instead of judging them wrong."""
    toks = set(DISPOSITIONS)
    for a in arts.values():
        toks |= {r for r in a["raw"] if VERDICT_TOKEN.match(r)}
    return toks


def global_raw(arts):
    return {r for a in arts.values() for r in a["raw"]}


def status_only(arts):
    return {r for a in arts.values() for r, ks in a["raw"].items()
            if all(k == "status" for k in ks)}


def corpus():
    docs = [(REPORT, "append_only"), (LOG, "append_only"), (LEDGER, "regenerated")]
    tables = [p for p in sorted(GOV.glob("*.md"))
              if re.search(r"_v\d+\.md$", p.name) and p.name not in SELF_OUT and p.name not in TRANSCRIBED]
    docs += [(p, "derived_summary") for p in sorted(RUNS_DIR.glob("*.md")) + tables]
    docs += [(p, "run_record") for d in RECORD_DIRS for p in sorted(d.glob("*.md"))
             if not re.search(r"PREREG", p.name)]
    return [(p, kind) for p, kind in docs if p.exists() and p.name not in SELF_OUT]


def claims(toks):
    """One row per (document, line, label token) in the prose corpus. `*PREREG*.md` is excluded: a
    registered exit name in a document that precedes the reading is not a claim about a verdict, and the
    file is frozen anyway (R6)."""
    pat = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(toks, key=len, reverse=True)) + r")\b")
    rows = []
    for p, kind in corpus():
        rel = str(p.relative_to(M))
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            found = sorted(set(pat.findall(line)))
            if not found:
                continue
            # anchors and predication are tested on the WHOLE line: a long table row can name the
            # refuting round, or predicate the label, well past any display truncation
            rows.append({"document": rel, "kind": kind, "line": i,
                         "labels": found, "excerpt": line.strip()[:160],
                         "line_len": len(line)})
    return rows


BOLD = re.compile(r"\*\*[A-Z][A-Z0-9_-]{3,}\*\*")


HARD_TERMS = ("label_unregistered", "label_wrong_for_anchor", "stale_in_register")


def classify(rows, arts, nums, toks, state_words=None):
    state_words = state_words or set()
    out = []
    cache = {}
    for r in rows:
        if r.get("line_text") is not None:
            full = r["line_text"]
        else:
            key = r["document"]
            if key not in cache:
                cache[key] = (M / r["document"]).read_text(encoding="utf-8").splitlines()
            full = cache[key][r["line"] - 1]
        fam, phan = anchors_of(full, nums)
        entry = dict(r)
        entry["anchors"] = sorted(str(x) for x in fam)
        entry["phantom"] = sorted(str(x) for x in phan)
        if phan:
            entry["verdict"] = "anchor_phantom"
            out.append(entry)
            continue
        if not fam:
            entry["verdict"] = "label_without_anchor"
            out.append(entry)
            continue
        state_words = state_words or set()
        allowed, literal = set(), set()
        for a in fam:
            for rel in family_artifacts(a, arts):
                allowed |= set(arts[rel]["five"])
                literal |= set(arts[rel]["raw"])
        entry["allowed_five"] = sorted(allowed)
        entry["artifact_raw"] = sorted(literal)
        att = [lab for lab in r["labels"] if predicate_attaches(full, lab, toks)]
        entry["predicated"] = bool(att)
        entry["attested_labels"] = att
        if not entry["predicated"]:
            entry["verdict"] = "label_mention_without_predication"
            out.append(entry)
            continue
        if not allowed:
            # an anchored round that records no five-value at all cannot refute anything: an empty
            # allow-list is never a refutation (the generalised lesson of amendment A1)
            entry["verdict"] = "anchor_without_recorded_label"
            out.append(entry)
            continue
        per = []
        for lab in r["labels"]:
            if lab not in att:
                # on the line, but not what that line's predicate was about
                per.append((lab, "label_mention_without_predication"))
                continue
            fv = five_of(lab)
            if fv is None and lab in DISPOSITIONS:
                per.append((lab, "not_a_round_verdict"))
            elif fv is None and lab in state_words:
                per.append((lab, "not_a_round_verdict"))
            elif fv is None and lab in global_raw(arts):
                per.append((lab, "attested_in_other_round" if lab not in literal
                            else "matches_artifact"))
            elif fv is None and BOLD.search(r["excerpt"]):
                per.append((lab, "label_unregistered"))
            elif fv is None:
                per.append((lab, "matches_artifact"))
            elif fv not in allowed:
                per.append((lab, "stale_in_register" if r["kind"] == "regenerated"
                            else "label_wrong_for_anchor"))
            elif lab not in literal and lab in FIVE:
                per.append((lab, "five_label_only_in_translation"))
            else:
                per.append((lab, "matches_artifact"))
        entry["per_label"] = per
        hard = [v for _, v in per if v in HARD_TERMS]
        # a row that both matches the round and contradicts it is quoting the contradicted label as the
        # retracted one - §48's paired_correction shape, derived from the row rather than from heuristics
        if hard and CROSS.search(full) and any(
                five_of(lab) in set().union(*[set(arts[x]["five"]) for x in family_artifacts(a, arts)]
                                            if family_artifacts(a, arts) else [set()])
                for lab in r["labels"] for a in entry["anchors"] if a not in CROSS_EXEMPT):
            entry["verdict"] = "cross_round_refutation"
            out.append(entry)
            continue
        doc_text = r.get("doc_text", (M / r["document"]).read_text(encoding="utf-8"))
        entry["errata"] = [{"quoted": lab, "xid": e["xid"], "marker": e["marker"]}
                           for lab, v in per if v in HARD_TERMS
                           for e in errata_live(entry, lab, doc_text, full)]
        hard = [v for lab, v in per
                if v in HARD_TERMS and not errata_live(entry, lab, doc_text, full)]
        if hard and any(v == "matches_artifact" for _, v in per):
            entry["paired_correction"] = True
            hard = []
        entry["verdict"] = hard[0] if hard else (
            "five_label_only_in_translation" if any(v == "five_label_only_in_translation" for _, v in per)
            else "matches_artifact" if att else "label_mention_without_predication")
        out.append(entry)
    return out


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    arts = population_a()
    nums = registered_phases(arts)
    toks = vocab(arts)
    rows = classify(claims(toks), arts, nums, toks, status_only(arts))
    order = ["anchor_phantom", "label_unregistered", "label_wrong_for_anchor", "stale_in_register",
             "paired_correction", "five_label_only_in_translation", "not_a_round_verdict",
             "attested_in_other_round", "anchor_without_recorded_label",
             "label_mention_without_predication", "cross_round_refutation", "paired_correction",
             "label_without_anchor",
             "matches_artifact"]
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in order}
    counts["hard_findings"] = sum(counts[v] for v in order[:4])
    counts["paired_corrections"] = sum(1 for r in rows if r.get("paired_correction"))
    counts["claim_documents"] = len({r["document"] for r in rows})
    counts["corpus_documents"] = len(corpus())
    counts["artifact_files"] = len(arts)
    counts["vocabulary_tokens"] = len(toks)
    counts["registered_phases"] = len(nums)
    doc = {
        "schema": "label_provenance_v1",
        "question": "can a verdict label written in prose be refuted by the artifact of the round it names",
        "five_labels": FIVE,
        "translation_authority": {"module": "governance/build_status_label_table.py",
                                  "sha256": sha256((GOV / "build_status_label_table.py").read_bytes()),
                                  "rules_tokens": len(RULES)},
        "label_keys": list(KEYS) + ["label*", "*_label"],
        "generator": {"file": str(pathlib.Path(__file__).resolve().relative_to(M)),
                      "sha256": sha256(pathlib.Path(__file__).read_bytes())},
        "self_excluded": sorted(SELF_OUT),
        "declared_transcriptions": dict(TRANSCRIBED),
        "errata": ERRATA,
        "asymmetry": "pairing is at round level, never arm level: looseness can only remove findings",
        "counts": counts,
        "artifact_labels": {k: {"five": v["five"], "raw": sorted(v["raw"])} for k, v in arts.items()},
        "rows": rows,
    }
    JSON_OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# 判定标签↔工件对账 v1（LABEL_PROVENANCE_v1）", "",
             "问题：散文写下的判定标签，能不能被它所说那一轮的工件推翻？（GOVERNANCE_ARTIFACT，不跑实验、"
             "不改任何轮次判定）", "",
             "翻译权威：`governance/build_status_label_table.py` 的注册映射（源码 SHA-256 `%s`，登记 %d 个词）；"
             "本表不重新定义任何翻译。" % (doc["translation_authority"]["sha256"][:16], len(RULES)),
             "生成本表的推导器源码 SHA-256：`%s`；工件文件 %d 份，注册轮次数 %d，标签词表 %d 个，"
             "语料文档 %d 份，产出主张行 %d 行（文档 %d 份）。"
             % (doc["generator"]["sha256"][:16], len(arts), len(nums), len(toks),
                counts["corpus_documents"], len(rows), counts["claim_documents"]),
             "", "| 判定 | 条数 |", "|---|---|"]
    for v in order:
        lines.append("| `%s` | %d |" % (v, counts[v]))
    lines.append("| **硬伤合计** | **%d** |" % counts["hard_findings"])
    lines += ["", "硬伤逐条（只列本层判据认定的，不解释成对旧轮的重判）：", ""]
    for r in rows:
        if r["verdict"] in order[:4]:
            lines.append("- `%s:%d` %s → 允许的五值 `%s` ｜ 摘录：%s"
                         % (r["document"], r["line"], r["verdict"],
                            ",".join(r.get("allowed_five", [])) or "-", r["excerpt"][:90]))
    lines += ["", "口径不对称（写死，供复核）：配对只在**轮次**层，不在臂层；一轮同时记录 E1/E2 时本表接受其一。"
              "本表的两个输出不参与语料（工件不给自己背书）。", ""]
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote label_provenance_v1.json | rows %d hard %d dist %s"
          % (len(rows), counts["hard_findings"],
             json.dumps({v: counts[v] for v in order}, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
