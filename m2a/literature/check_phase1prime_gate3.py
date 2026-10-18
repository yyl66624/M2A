"""Phase I-prime gate 3: does the vote count actually agree with the conclusions it supports?

The plan (§1, row I') makes gate 3 two things: a machine-readable registry with a coverage matrix
carrying the *evidence-type x verification-level* dimensions, and "计票结果与报告结论一致性检查通过".
`PHASE1PRIME_STATUS.md` marked gate 3 green on the strength of the artifacts existing. This script
performs the check that was asserted but never run: it re-derives the matrix with both dimensions
and compares every machine-readable number in `PRELIMINARY_CONCLUSIONS_V2.md` against
`synthesis_v2.json`, and reports the verification-level arithmetic across the documents.

Read-only. Writes `phase1prime_gate3_check.json`. Nothing in Phase I / I' assets is modified.
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "phase1prime_gate3_check.json"
CONCLUSIONS = HERE / "PRELIMINARY_CONCLUSIONS_V2.md"
STATUS_DOC = HERE / ".." / "PHASE1PRIME_STATUS.md"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def expansion_cluster_map():
    """Reuse the builder's own tables and cluster rule instead of inventing a second one.
    The builder only touches disk inside main(), which has a __main__ guard, so importing it
    is side-effect free."""
    sys.path.insert(0, str(HERE))
    try:
        import build_registry_and_synthesis as b
    except Exception as exc:  # noqa: BLE001 - a moved table must stop the check, not guess
        raise SystemExit("cannot import the builder to reuse its cluster table: " + repr(exc))
    return dict(b.EXP_CLUSTER), b.cluster_of


def level_of(rid, review_ids, unavailable, registry_level):
    base = re.split(r"[（;；]", registry_level)[0].strip()
    if rid in unavailable:
        return "OA_UNAVAILABLE(reason recorded)"
    if rid in review_ids:
        return "FULLTEXT_REVIEWED"
    return base


def main():
    reg = load("registry.json")["records"]
    exp = load("expansion_registry.json")["records"]
    sv = load("synthesis_v2.json")
    man = load("fulltext_manifest.json")["records"]
    rev = load("fulltext_review.json")["records"]
    review_ids = set(rev)
    fetched = {k for k, v in man.items() if v["status"] == "fetched"}
    failed = {k for k, v in man.items() if v["status"] == "failed"}
    expc, _cluster_of = expansion_cluster_map()

    # ---- G3-1 coverage matrix with the two dimensions -------------------------
    log = (HERE / "fulltext_review_log.md").read_text(encoding="utf-8")
    unavailable = {m.group(1) for m in re.finditer(r"^\|\s*`([^`]+)`[^|]*\|.*不可得", log, re.M)}
    cube = {}
    rows = 0
    unknown_cluster = []
    for r in reg:
        for fam in r["k_all"]:
            ev = r.get("evidence") or "UNKNOWN"
            lv = level_of(r["id"], review_ids, unavailable, r.get("verification") or "UNKNOWN")
            cube.setdefault(fam, {}).setdefault(r["cluster"], {}).setdefault(ev, {}).setdefault(lv, 0)
            cube[fam][r["cluster"]][ev][lv] += 1
            rows += 1
    for r in exp:
        cl = expc.get(r["id"], "G?")
        if cl == "G?":
            unknown_cluster.append(r["id"])
        ev = r.get("evidence") or "UNKNOWN"
        lv = level_of(r["id"], review_ids, unavailable, "IDENTITY_VERIFIED")
        cube.setdefault(r["family"], {}).setdefault(cl, {}).setdefault(ev, {}).setdefault(lv, 0)
        cube[r["family"]][cl][ev][lv] += 1
        rows += 1

    # ---- G3-2 every machine-readable number in the conclusions doc ------------
    text = CONCLUSIONS.read_text(encoding="utf-8")
    lines = text.splitlines()
    votes, mat = sv["votes"], sv["matrix"]
    claims, unchecked = [], []
    FAM = re.compile(r"\bK(\d{1,2})\b")
    COV = re.compile(r"(\d)/8\s*集群")
    ANN = re.compile(r"(\d+)\s*条(?:\s*\*\*)?\s*标注")
    DIR = re.compile(r"D\+\s*(\d+)\s*/\s*D−\s*(\d+)\s*/\s*混合\s*(\d+)")
    CLUS = "G1 G2 G3 G4 G5 G6 G7 G8".split()
    ANN2 = re.compile(r"总标注\s*\**(\d+)\**\s*条")
    VAL = re.compile(r"另有\s*\**(\d+)\**\s*条仅价值")
    RISE = re.compile(r"从\s*\**(\d)/8\**\s*提到\s*\**(\d)/8")
    DIR2 = re.compile(r"D\+\s*(\d+)\s*/\s*混合\s*(\d+)")
    TBL = re.compile(r"^\|\s*K(\d{1,2})[^|]*\|\s*\**(\d+)\**\s*\|\s*\**(\d+)\**\s*\|\s*\**(\d+)\**")
    ASIDE_PAIR = re.compile(r"K(\d{1,2})(?!\d)\s+\**(\d+)\**")

    def cov(f):
        return sum(1 for c in CLUS if mat[f].get(c, 0) > 0)

    def ann(f):
        return sum(votes.get(f, {}).values())

    def dirs(f):
        v = votes.get(f, {})
        return (v.get("D+", 0), v.get("D-", 0), v.get("mixed", 0)), v.get("value-only", 0)

    def add(f, kind, doc, comp, ln, line):
        if f in mat:
            claims.append((f, kind, doc, comp, "L" + str(ln), re.sub(r"\s+", " ", line.strip())[:90]))

    for ln, line in enumerate(lines, 1):
        if "不可换算" in line:
            unchecked.append(("L" + str(ln), "口径声明行，文档自身声明两套数字不可换算，不进入计票核对："
                              + re.sub(r"\s+", " ", line.strip())[:70]))
            continue
        if not any(p.search(line) for p in (COV, ANN, ANN2, RISE, DIR, DIR2, VAL)) and not TBL.match(line):
            continue
        subject = "K" + FAM.search(line).group(1)
        body = re.sub(r"（[^（）]*）", "", line)
        for pg in re.findall(r"（([^（）]*)）", line):
            for m in ASIDE_PAIR.finditer(pg):
                f = "K" + m.group(1)
                add(f, "annotations-aside", int(m.group(2)), ann(f), ln, line)
        for m in COV.finditer(body):
            add(subject, "coverage", int(m.group(1)), cov(subject), ln, line)
        for m in RISE.finditer(body):
            add(subject, "coverage-after-rise", int(m.group(2)), cov(subject), ln, line)
            unchecked.append(("L" + str(ln), subject + " 扩充前 " + m.group(1)
                              + "/8 无法核对：synthesis_v2 只有扩充后的 8 集群口径，Phase I 是 16 格口径"))
        for m in ANN.finditer(body):
            add(subject, "annotations", int(m.group(1)), ann(subject), ln, line)
        for m in ANN2.finditer(body):
            add(subject, "annotations", int(m.group(1)), ann(subject), ln, line)
        for m in DIR.finditer(body):
            d3, _ = dirs(subject)
            add(subject, "direction", (int(m.group(1)), int(m.group(2)), int(m.group(3))), d3, ln, line)
        for m in DIR2.finditer(body):
            d3, _ = dirs(subject)
            add(subject, "direction-noDminus", (int(m.group(1)), int(m.group(2))), (d3[0], d3[2]), ln, line)
        for m in VAL.finditer(line):
            add(subject, "value-only", int(m.group(1)), dirs(subject)[1], ln, line)
    # table rows of the form "| K2 门控 | 6 | **7** | **9** |"
    for ln, line in enumerate(lines, 1):
        m = TBL.match(line)
        if m:
            f = "K" + m.group(1)
            add(f, "direction-table", (int(m.group(2)), int(m.group(3)), int(m.group(4))),
                dirs(f)[0], ln, line)

    fails = [c for c in claims if c[2] != c[3]]

    levels_seen = sorted({lv for f in cube.values() for c in f.values() for e in c.values() for lv in e})
    ev_seen = {ev for f in cube.values() for c in f.values() for ev in c}
    struct = [
        ("every record carries an evidence type", "UNKNOWN" not in ev_seen),
        ("every family x cluster cell carries a verification level",
         all(e for f in cube.values() for c in f.values() for e in c.values())),
        ("no expansion record left with an unresolved cluster", not unknown_cluster),
        ("the join actually promotes records to FULLTEXT_REVIEWED (else the level axis is hollow)",
         any("FULLTEXT_REVIEWED" in e for f in cube.values() for c in f.values() for e in c.values())),
        ("the 7 documented-unavailable records show up as their own level",
         any("OA_UNAVAILABLE" in lv for lv in levels_seen) and len(unavailable) == len(failed)),
        ("no family in the join is absent from synthesis_v2", set(cube) <= set(mat)),
    ]
    struct_bad = [n for n, ok in struct if not ok]

    # ---- G3-3 verification-level arithmetic across documents ------------------
    reg_levels = {}
    for r in reg:
        reg_levels[re.split(r"[（;；]", r.get("verification") or "?")[0].strip()] = \
            reg_levels.get(re.split(r"[（;；]", r.get("verification") or "?")[0].strip(), 0) + 1
    status_text = STATUS_DOC.read_text(encoding="utf-8")
    claimed_reviewed = re.findall(r"\*\*(\d+) 条\*\*全文", status_text)
    account = {
        "registry_records": len(reg), "expansion_records": len(exp),
        "registry_verification_levels": reg_levels,
        "fulltext_review_entries": len(rev), "manifest_fetched": len(fetched),
        "manifest_failed_with_reason": len(failed),
        "log_unavailable_rows_parsed": len(unavailable),
        "status_doc_claimed_fulltext": claimed_reviewed,
        "note": "registry.json keeps Phase I levels untouched (plan §5 forbids rewriting them); "
                "the full-text disposition lives in fulltext_review_log.md, so any count that reads "
                "only registry.json reports 0 FULLTEXT_REVIEWED, as PRELIMINARY_CONCLUSIONS_V2 line 5 says",
    }

    out = {
        "schema": "m2a.phase1prime.gate3check.v1",
        "generated_from": {p.name: sha(p) for p in
                           [CONCLUSIONS, HERE / "synthesis_v2.json", HERE / "registry.json",
                            HERE / "expansion_registry.json", HERE / "fulltext_review.json",
                            HERE / "fulltext_manifest.json", HERE / "fulltext_review_log.md",
                            STATUS_DOC]},
        "G3_1_two_dimension_matrix": {
            "family_cluster_evidence_level_cells": sum(len(c) for f in cube.values() for c in f.values()),
            "annotation_rows_joined": rows,
            "families": len(cube),
            "expansion_ids_without_cluster": sorted(unknown_cluster),
            "structural_checks": [{"check": n, "passed": bool(ok)} for n, ok in struct],
            "structural_failures": struct_bad,
            "levels_seen": sorted({lv for f in cube.values() for c in f.values()
                                   for e in c.values() for lv in e}),
            "evidence_types_seen": len({ev for f in cube.values() for c in f.values() for ev in c}),
        },
        "G3_2_vote_consistency": {
            "claims_checked": len(claims),
            "claims_failed": len(fails),
            "verdict": "PASS" if claims and not fails and not struct_bad
                       else ("FAIL" if (fails or struct_bad) else "NO_CLAIMS_PARSED"),
            "failures": [f"{c[0]} {c[1]} doc={c[2]} computed={c[3]} at {c[4]}: {c[5]}" for c in fails],
            "claims": [f"{c[0]} {c[1]} = {c[2]} (computed {c[3]}) {c[4]}" for c in claims],
        },
        "G3_3_level_accounting": account,
        "G3_2_not_checkable_claims": [ln + ": " + txt for ln, txt in unchecked],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    g1 = out["G3_1_two_dimension_matrix"]
    g2 = out["G3_2_vote_consistency"]
    print("G3-1 cells", g1["family_cluster_evidence_level_cells"], "| rows", g1["annotation_rows_joined"],
          "| levels", len(g1["levels_seen"]), "| evidence types", g1["evidence_types_seen"],
          "| unresolved clusters", g1["expansion_ids_without_cluster"])
    n_claims = g2["claims_checked"]
    n_struct = len(struct)
    passed = (n_claims - len(fails)) + (n_struct - len(struct_bad))
    print("G3-2", g2["verdict"], "claims", n_claims, "failed", len(fails),
          "| structural", n_struct - len(struct_bad), "/", n_struct)
    for f in g2["failures"]:
        print("   FAIL", f)
    print("G3-3 registry", out["G3_3_level_accounting"]["registry_verification_levels"],
          "| review", out["G3_3_level_accounting"]["fulltext_review_entries"],
          "| fetched", out["G3_3_level_accounting"]["manifest_fetched"],
          "| failed+reason", out["G3_3_level_accounting"]["manifest_failed_with_reason"],
          "| log rows", out["G3_3_level_accounting"]["log_unavailable_rows_parsed"],
          "| status doc claims", out["G3_3_level_accounting"]["status_doc_claimed_fulltext"])
    print("not checkable", len(unchecked))
    for ln, txt in unchecked:
        print("   NC", ln, txt)
    print("wrote", OUT)
    for n in struct_bad:
        print("   STRUCT FAIL", n)
    print(f"{passed}/{n_claims + n_struct} checks passed")
    return 0 if passed == n_claims + n_struct else 1


if __name__ == "__main__":
    sys.exit(main())
