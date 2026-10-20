"""§50 validator for the value-provenance table: V1-V18 plus 2 self-counts, 20 printed verdict lines, and
every rule is asked whether it can actually fire.

What this layer claims is refutable, so this suite is the instrument that has to prove it:

* the readings are reproducible, but the validator never adopts the generator's fresh bytes (X-91) - a mismatch
  is reported and the committed bytes stay on disk so the red can still be inspected;
* every verdict in the artifact is recomputed here from *live* inputs by a second path (a fresh population A
  plus an inline copy of the exit logic), so a stored verdict cannot be an unfalsifiable field;
* the amendments that made the layer usable (A1 sign normalisation, A2/A4/A6 reference shapes, A3 hex
  fragments, A7/A11 numeric tier matching, A9 case-insensitive families) are each proved load-bearing by a
  control that shows what the layer would have said without them - a rule that only ever agrees with itself
  measures nothing;
* each of the six exits, the three hard ones included, is fired on a synthetic line built from derived
  sentinels (`max(rounds)+1`, `max(recorded)+1`), never from a hard-coded number that could fall inside the
  population's own range (X-84);
* cross-layer cycles are checked rather than assumed: the peer layers must declare this layer's two outputs as
  transcriptions, must register this suite as unmeasured, and the governance-table population must partition
  into measured / declared / self-output with no silent remainder (X-94, X-95).
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
ART = GOV / "value_provenance_v1.json"
MD = GOV / "VALUE_PROVENANCE_v1.md"
GEN = GOV / "build_value_provenance.py"

sys.path.insert(0, str(GOV))
import build_value_provenance as B  # noqa: E402
import build_suite_score_registry as S48  # noqa: E402
import build_label_provenance as S49  # noqa: E402

VIDS = ["V%d" % i for i in range(1, 19)]
SELF_SUITE = "value_provenance_gate.py"
KINDS = ["append_only", "derived_summary", "regenerated", "run_record"]
_ok = 0
_n = 0
_verdicts = []


def report(tag, cond, detail=""):
    global _ok, _n
    _n += 1
    _verdicts.append((tag, bool(cond)))
    _ok += int(cond)
    print(("PASS " if cond else "FAIL ") + tag + " " + (detail if detail else ""))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def live_lines():
    out = {}
    for p, _kind in B.corpus():
        out[str(p.relative_to(M))] = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return out


def decide(line, values, kind, arts, rounds):
    """An inline second copy of the exit logic, run against freshly computed inputs (V8). It mirrors
    `classify` branch for branch - including its value order and its first-attested-tier rule - because a
    paraphrase of the decision is not a second path, it is a second opinion."""
    fam, phan = B.anchors_of(line, rounds)
    if phan and not fam:
        return "anchor_without_records"
    if not fam:
        return "criterion_without_anchor"
    where = {v: B.tier_of(v, fam, arts) for v in values}
    missing = [v for v in values if not where[v]]
    nowhere = [v for v in missing if not B.other_rounds(v, rounds, arts)]
    if missing and not nowhere:
        return "value_of_other_round"
    if nowhere:
        return "stale_value_in_register" if kind == "regenerated" else "value_unattested_in_repo"
    if any(where[v] and next(iter(where[v].values())) == "transcription" for v in values):
        return "value_only_in_transcription"
    return "matches_round_records"


def main() -> int:
    if not (ART.exists() and MD.exists()):
        print("artifact missing - run build_value_provenance.py first", file=sys.stderr)
        return 2
    before_json, before_md = ART.read_bytes(), MD.read_bytes()
    d = json.loads(before_json.decode("utf-8"))
    rows, c = d["rows"], d["counts"]
    arts = B.population_a()
    rounds = {k for k in arts if isinstance(k, int)}
    lines = live_lines()

    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_json = ART.read_bytes()
    report("V1 the generator reproduces the committed JSON",
           r1.returncode == 0 and fresh_json == before_json,
           "exit=%d bytes %d -> %d" % (r1.returncode, len(before_json), len(fresh_json)))
    if fresh_json != before_json:
        ART.write_bytes(before_json)  # X-91: a red must survive the validator that found it
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_md = MD.read_bytes()
    report("V2 the generator reproduces the committed Markdown",
           r2.returncode == 0 and fresh_md == before_md,
           "exit=%d bytes %d -> %d" % (r2.returncode, len(before_md), len(fresh_md)))
    if fresh_md != before_md:
        MD.write_bytes(before_md)
    report("V3 both generator runs exited 0 and the validator leaves the bytes it found",
           r1.returncode == 0 and r2.returncode == 0 and ART.read_bytes() == before_json
           and MD.read_bytes() == before_md,
           "json %s md %s" % (sha(ART)[:10], sha(MD)[:10]))

    reg, hard = d["registered_exits"], d["hard_exits"]
    emitted = sorted({r["verdict"] for r in rows})
    report("V4 every emitted verdict is a registered exit and the hard set is exactly the three frozen",
           set(emitted) <= set(reg) and hard == reg[:3]
           and set(c) >= set(reg) and len(reg) == len(set(reg)) == 7,
           "emitted %d of %s | hard %s" % (len(emitted), ",".join(reg), ",".join(hard)))
    part = sum(c[v] for v in reg)
    report("V5 the partition sums over every verdict including the hard ones and equals the rows",
           part == len(rows) == c["hard_findings"] + sum(c[v] for v in reg[3:])
           and c["hard_findings"] == sum(1 for r in rows if r["verdict"] in hard),
           "sum %d rows %d | hard %d enumerated %d" % (part, len(rows), c["hard_findings"],
                                                       sum(1 for r in rows if r["verdict"] in hard)))
    report("V6 every headline aggregate equals the rows it summarises",
           c["claim_values"] == sum(len(r["values"]) for r in rows)
           and c["claim_documents"] == len({r["document"] for r in rows})
           and c["corpus_documents"] == len(B.corpus())
           and c["round_families"] == len(arts),
           "values %d | docs %d | corpus %d | families %d" % (c["claim_values"], c["claim_documents"],
                                                             len(B.corpus()), len(arts)))

    bad_line, bad_excerpt = [], []
    for r in rows:
        ln = lines.get(r["document"], [None] * r["line"])[r["line"] - 1] \
            if r["document"] in lines and len(lines[r["document"]]) >= r["line"] else None
        if ln is None:
            bad_line.append((r["document"], r["line"], "line gone"))
            continue
        norm = ln.translate({ord(ch): "-" for ch in B.MINUS})
        for v in r["values"]:
            if v.lstrip("-+") not in norm:
                bad_line.append((r["document"], r["line"], v))
        if ln.strip()[:150] != r["excerpt"]:
            bad_excerpt.append((r["document"], r["line"]))
    report("V7 every claim value and every excerpt is really on the line it cites, in the live file",
           not bad_line and not bad_excerpt,
           "offending lines %d | offending excerpts %d" % (len(bad_line), len(bad_excerpt)))

    live_rows = []
    for r in rows:
        ln = lines[r["document"]][r["line"] - 1]
        live_rows.append((r, decide(ln, r["values"], r["kind"], arts, rounds)))
    disagree = [(r["document"], r["line"], r["verdict"], v) for r, v in live_rows if r["verdict"] != v]
    hard_live = sum(1 for _r, v in live_rows if v in hard)
    report("V8 recomputing every verdict from live inputs leaves the verdicts and the hard count unchanged",
           not disagree and hard_live == c["hard_findings"],
           "disagreements %d | hard live %d vs %d" % (len(disagree), hard_live, c["hard_findings"]),)

    # A1: sign normalisation. Without it a slope written with U+2212 is not the artifact's ASCII '-'.
    a1 = 0
    for r in rows:
        ln = lines[r["document"]][r["line"] - 1]
        if any(ch in ln for ch in B.MINUS):
            fam, _p = B.anchors_of(ln, rounds)
            for raw in [t for t in re.findall(r"[%s][\d.]+(?:[eE][-+]?\d+)?" % B.MINUS, ln)]:
                if not B.tier_of(raw, fam, arts) and B.tier_of(raw.translate(
                        {ord(ch): "-" for ch in B.MINUS}), fam, arts):
                    a1 += 1
    report("V9 A1 sign normalisation is load-bearing: a U+2212 value is attested only after it is applied",
           a1 > 0, "values recovered %d" % a1)

    # A2/A4/A6: reference and version shapes; A3: hex fragments. Probes plus a corpus-wide control. The
    # section-number rule is *per document*, so the probe must pin the deriver's own section global
    # (B.DOC_SECTIONS) or the "15.2 is a reference of this file" expectation is simply false.
    probes = [("### 10.6 复现（Phase V） 0.5", "10.6", True), ("§4.1 的 0.25", "4.1", True),
              ("python 3.10.12 起步", "3.10", True), ("15.2 的锚定要求 0.05", "15.2", True),
              ("容差 0.05 判定", "0.05", False), ("阈值 0.5 与 15.2 两行", "0.5", False)]
    saved_sections = set(B.DOC_SECTIONS)
    B.DOC_SECTIONS = saved_sections | {"15.2"}
    try:
        shape_ok = all(B.looks_like_reference(t, t.index(v), t.index(v) + len(v), v) is want
                       for t, v, want in probes)
    finally:
        B.DOC_SECTIONS = saved_sections
    orig = B.looks_like_reference
    try:
        B.looks_like_reference = lambda *a: False
        loose = B.claims(rounds)
    finally:
        B.looks_like_reference = orig
    strict = {r["document"] for r in rows}
    heads = len([1 for txt in lines.values() for ln in txt
                 if re.match(r"^\s*#+\s*\d+(\.\d+)*\s", ln) or "§" in ln])
    report("V10 A2/A4/A6 exclusions are probes-true and load-bearing: disabling them grows the claim set",
           shape_ok and len(loose) > len(rows) and heads > 0,
           "probes %s | claims without the rule %d vs %d | reference shapes in corpus %d"
           % (shape_ok, len(loose), len(rows), heads))

    hex_hits = []
    for r in rows:
        ln = lines[r["document"]][r["line"] - 1]
        for v in r["values"]:
            for m in re.finditer(r"[0-9a-f]{12,}", ln):
                if v.lstrip("-+").replace(".", "") and v.lstrip("-+") in m.group(0):
                    hex_hits.append((r["document"], r["line"], v))
    a3_probe = not B.criterion_values("prereg_sha256 `5aa2e338c1b2d4e6f7089`")
    report("V11 A3 keeps hex fragments out of the claim set: no value sits inside a longer hex run",
           not hex_hits and a3_probe and "2e338" not in B.criterion_values("sha 5aa2e338c1b2"),
           "hex-embedded claims %d | sha-prefix probe clean %s" % (len(hex_hits), a3_probe))

    empty_art = [k for k, v in arts.items() if not v["artifact"]]
    no_prereg = [k for k, v in arts.items() if isinstance(k, int) and not v["prereg"]]
    tiers = sum(1 for v in arts.values() if v["prereg"] and v["artifact"])
    a9_probe = (B.family_of_name("PHASE13_PREREGISTRATION.md") == 13
               and B.family_of_name("phase13_results.json") == 13)
    report("V12 A9 loads all three attestation tiers per family: a tier that loads nothing is not a tier",
           a9_probe and not empty_art and len(no_prereg) <= 3 and tiers >= 15,
           "families %d | artifact-empty %s | prereg-empty %s | both-tiers %d"
           % (len(arts), empty_art, no_prereg, tiers))

    float_only, rounded_not_exact = [], []
    for r in rows:
        fam, _p = B.anchors_of(lines[r["document"]][r["line"] - 1], rounds)
        for pv in r["per_value"]:
            for a, tier in pv["attested_in"].items():
                key = int(a) if re.match(r"^\d+$", a) else a
                dfa = arts[key]
                fv = B.as_float(pv["value"])
                if tier in ("prereg", "artifact", "transcription"):
                    if pv["value"] not in dfa[tier] and fv in dfa[tier + "_floats"]:
                        float_only.append((r["document"], r["line"], pv["value"], tier))
                elif tier == "rounded":
                    if fv in dfa["floatset"] or B.tolerance(pv["value"]) == 0.0:
                        rounded_not_exact.append((r["document"], r["line"], pv["value"]))
    report("V13 A11's float branch fires (token text differs, quantity matches) and no `rounded` row is exact",
           len(float_only) > 0 and not rounded_not_exact,
           "float-only matches %d | rounded-but-exact %d" % (len(float_only), len(rounded_not_exact)))

    tol_probes = [("0.005", 0.0005), ("8.1e-5", 0.5e-6), ("1.0001", 0.00005), ("3", 0.0),
                  ("-2.0620", 0.00005), ("5.1e-12", 0.05e-12)]
    tol_ok = all(abs(B.tolerance(t) - want) <= 1e-18 + abs(want) * 1e-9 for t, want in tol_probes)
    mono = all(B.near(t, [v + B.tolerance(t) * 0.4]) and not B.near(t, [v + B.tolerance(t) * 4.0])
               for t, v in [("0.5", 0.5), ("1.25", 1.25), ("8.1e-5", 8.1e-5)])
    rounded_cnt = sum(1 for r in rows for pv in r["per_value"]
                      if list(pv["attested_in"].values()) == ["rounded"])
    report("V14 the rounding math is the registered half-unit and the counts agree with it",
           tol_ok and mono and rounded_cnt == c["rounded_matches"],
           "tolerance probes %s | monotone %s | rounded %d vs %d"
           % (tol_ok, mono, rounded_cnt, c["rounded_matches"]))

    # V15 teeth: every exit, hard ones included, must be reachable. Sentinels are derived, never typed.
    all_f = [f for v in arts.values() for f in v["floats"]]
    sentinel = None
    for cand in [7.77777, 8.88889, 9.99991, 6.66667, 5.55557, 4.44443]:
        if not any(abs(cand - f) <= 0.000005 for f in all_f):
            sentinel = "%.5f" % cand
            break
    other_val, other_pair = None, None
    for x in sorted(k for k in rounds):
        for v in arts[x]["artifact"]:
            fv = B.as_float(v)
            if v in arts[x]["prereg"] or "." not in v:
                continue
            for y in sorted(k for k in rounds):
                if y == x:
                    continue
                dy = arts[y]
                if v not in dy["artifact"] and v not in dy["prereg"] and v not in dy["transcription"] \
                        and (fv is None or fv not in dy["floatset"]) and not B.near(v, dy["floats"]):
                    other_val, other_pair = (v, (y, x))
                    break
            if other_val:
                break
        if other_val:
            break
    anchor_val = next((v for k in sorted(rounds) for v in arts[k]["prereg"]
                       if B.as_float(v) is not None and "." in v), None)
    anchor_round = next(k for k in sorted(rounds) if anchor_val in arts[k]["prereg"])
    phantom_round = max(rounds) + 1
    probes15 = [
        ("anchor_without_records", {"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                                    "values": [sentinel], "excerpt": "", "per_value": [],
                                    "_line": "Phase %d 的容差 %s 判负" % (phantom_round, sentinel)}),
        ("value_unattested_in_repo", {"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                                      "values": [sentinel], "excerpt": "", "per_value": [],
                                      "_line": "Phase %d 的容差 %s 判负" % (anchor_round, sentinel)}),
        ("stale_value_in_register", {"document": "governance/OBLIGATION_REGISTRY.md", "kind": "regenerated",
                                     "line": 1, "values": [sentinel], "excerpt": "", "per_value": [],
                                     "_line": "台账：Phase %d 的容差 %s" % (anchor_round, sentinel)}),
        ("value_of_other_round", {"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                                  "values": [other_val], "excerpt": "", "per_value": [],
                                  "_line": "Phase %d 沿用 %s 作为容差" % (other_pair[0], other_val)}),
        ("matches_round_records", {"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                                   "values": [anchor_val], "excerpt": "", "per_value": [],
                                   "_line": "Phase %d 注册容差 %s" % (anchor_round, anchor_val)}),
        ("criterion_without_anchor", {"document": "M2A_FINAL_REPORT.md", "kind": "append_only", "line": 1,
                                      "values": ["0.00123"], "excerpt": "", "per_value": [],
                                      "_line": "全局容差 0.00123 适用于所有轮次"})]
    fired = []
    for want, probe in probes15:
        got = [r["verdict"] for r in B.classify([dict(probe)], arts)]
        fired.append((want, got[0] == want))
    report("V15 each of the six exits fires on a synthetic line built from derived sentinels",
           all(ok for _w, ok in fired) and sentinel and other_val and anchor_val
           and phantom_round not in rounds,
           "fired %s | sentinel %s | cross-round %s | phantom round %d"
           % ([w for w, ok in fired if ok], sentinel, other_val, phantom_round))

    self_names = sorted(B.SELF_OUT)
    inside = [r["document"] for r in rows if pathlib.Path(r["document"]).name in self_names]
    peers = sorted(set(S48.LAYER_TRANSCRIPTIONS) & set(self_names))
    report("V16 this layer never attests itself: no row is one of its own outputs and the peers declare it",
           not inside and peers == self_names and MD.name in S49.TRANSCRIBED
           and SELF_SUITE in S48.UNMEASURED and all(S48.LAYER_TRANSCRIPTIONS[k] for k in peers)
           and all(S48.UNMEASURED[SELF_SUITE]) and all(S49.TRANSCRIBED.values()),
           "self rows %d | declared in §48 %s | in §49 %s | unmeasured %s"
           % (len(inside), peers, MD.name in S49.TRANSCRIBED, SELF_SUITE in S48.UNMEASURED))
    tables = sorted(p.name for p in GOV.glob("*_v*.md"))
    unaccounted = [n for n in tables if n not in self_names and n not in B.LAYER_TRANSCRIPTIONS
                   and n not in {p.name for p, _k in B.corpus()}]
    report("V17 the governance tables partition into measured / declared / self with no silent remainder",
           not unaccounted and len(tables) >= 5,
           "tables %d | unaccounted %s" % (len(tables), unaccounted))

    gp = d["generator"]
    kinds = sorted({r["kind"] for r in rows})
    report("V18 the generator's hash, its exclusions and its document kinds still match today's bytes",
           gp["sha256"] == sha(GEN) and gp["file"] == str(GEN.relative_to(M))
           and d["self_excluded"] == self_names
           and set(d["declared_transcriptions"]) >= {"SUITE_SCORE_REGISTRY_v1.md", "LABEL_PROVENANCE_v1.md",
                                                     "SECTION_PAGE_RECONCILIATION_v1.md"}
           and all(v for v in B.LAYER_TRANSCRIPTIONS.values())
           and set(B.LAYER_TRANSCRIPTIONS) == set(d["declared_transcriptions"])
           and kinds == KINDS,
           "gen %s | transcriptions %d | kinds %s" % (gp["sha256"][:12], len(d["declared_transcriptions"]),
                                                      kinds))

    ids = [re.match(r"V\d+", tag).group(0) for tag, _ in _verdicts]
    report("SUITE_accounting every declared rule id was recorded exactly once",
           sorted(ids) == sorted(VIDS) and len(ids) == len(set(ids)) == len(VIDS),
           "ids=%d vids=%d" % (len(ids), len(VIDS)))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _t, v in _verdicts if v),
           "recorded=%d passed=%d targets=%d rules=%d" % (_n, _ok, len(VIDS), len(_verdicts) - len(VIDS)))
    print("%d/%d checks passed" % (_ok, len(_verdicts)))
    return 0 if _ok == len(_verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
