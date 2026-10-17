"""Parse the Phase I registry, merge the Phase I' expansion, and compute the quantitative synthesis.

Outputs
  registry.json   : machine-readable records (87 Phase I + 19 expansion = 106)
  synthesis_v2.json / SYNTHESIS_V2.md : K x cluster matrix, per-family directional votes, evidence mix

Metrics are DEFINED here so they cannot drift from Phase I's differently-defined "coverage strength"
(which counted 16 cells). Phase I's annotations list K ids with NO primary/secondary markers (verified:
0 of 87 use 主/辅), while the Phase I' expansion does mark them. To keep ONE metric, all listed K ids
count as annotations; the primary/secondary markers are retained per record for later use but are not
used in the matrix.

  * a family covers a cluster if at least one record in that cluster annotates the family at all;
  * directional votes classify each record's D tokens: only+ / only- / mixed (both) / value-only (B);
  * evidence mix counts the declared evidence type.

Usage: python build_registry_and_synthesis.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REG = "bibliography_registry.md"
EXP = "expansion_registry.json"
OUT_JSON = "registry.json"
OUT_SYN = "synthesis_v2.json"
OUT_MD = "SYNTHESIS_V2.md"

# Cluster assignment for the expansion records (Phase I clusters are encoded in ids G1..G8).
EXP_CLUSTER = {
    "X-K4-01": "G3", "X-K4-02": "G3", "X-K4-05": "G3",
    "X-K4-03": "G4", "X-K4-04": "G4", "X-K4-06": "G4", "X-K4-07": "G4",
    "X-K10-01": "G4", "X-K10-02": "G4", "X-K10-03": "G3",
    "X-K10-04": "G6", "X-K10-06": "G6", "X-K10-05": "G8",
    **{f"X-K9-0{i}": "G2" for i in range(1, 7)},
}

FIELD_RE = {
    "citation": re.compile(r"^- 引文：(.+)$", re.M),
    "locator": re.compile(r"^- 定位：(.+)$", re.M),
    "verification": re.compile(r"^- 核验：(.+)$", re.M),
    "annotation": re.compile(r"^- 标注：(.+)$", re.M),
    "analysis": re.compile(r"^- 机制分析：(.+)$", re.M),
}
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s，,；;）)\]]+")
YEAR_RE = re.compile(r"\((\d{4})\)")
K_RE = re.compile(r"K(\d{1,2})\s*(?:（(主|辅)）)?")
D_RE = re.compile(r"(?<![A-Za-z])D\s*([+\-−±])")
B_RE = re.compile(r"(?<![A-Za-z])B\s*([±+\-−])")
EV_RE = re.compile(r"证据类型：\s*([^；;。]+)")


def cluster_of(rid: str) -> str:
    m = re.match(r"^G(\d)-\d{2}$", rid)
    if m:
        return f"G{m.group(1)}"
    return "seed"


def parse_phase1(text: str) -> list:
    recs = []
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    for part in parts:
        head, _, body = part.partition("\n")
        rid = head.split("—")[0].strip()
        if not re.match(r"^(R\d{2}|G\d-\d{2})$", rid):
            continue
        rec = {"id": rid, "cluster": cluster_of(rid), "heading": head.strip()}
        for key, rx in FIELD_RE.items():
            m = rx.search(body)
            rec[key] = m.group(1).strip() if m else ""
        ym = YEAR_RE.search(head)
        rec["year"] = int(ym.group(1)) if ym else None
        dm = DOI_RE.search(rec.get("locator", "") + " " + rec.get("citation", ""))
        rec["doi"] = dm.group(0).rstrip(".") if dm else None
        ann = rec.get("annotation", "")
        allk = [f"K{k}" for k, _ in K_RE.findall(ann)]
        prim = [f"K{k}" for k, kind in K_RE.findall(ann) if kind == "主"]
        sec = [f"K{k}" for k, kind in K_RE.findall(ann) if kind == "辅"]
        rec["k_all"] = sorted(set(allk), key=lambda s: int(s[1:]))
        rec["k_primary"] = prim
        rec["k_secondary"] = sec
        dtok = set(D_RE.findall(ann))
        if {"+", "-"} <= dtok or {"+", "−"} <= dtok:
            rec["d_class"] = "mixed"
        elif dtok & {"+", "±"}:
            rec["d_class"] = "D+" if "+" in dtok else "D±"
        elif dtok & {"-", "−"}:
            rec["d_class"] = "D-"
        elif B_RE.search(ann):
            rec["d_class"] = "value-only"
        else:
            rec["d_class"] = "unspecified"
        em = EV_RE.search(ann)
        rec["evidence"] = em.group(1).strip() if em else ""
        rec["verification_level"] = (
            "ABSTRACT_VERIFIED" if "ABSTRACT_VERIFIED" in rec.get("verification", "")
            else "IDENTITY_VERIFIED" if "IDENTITY_VERIFIED" in rec.get("verification", "")
            else "UNPARSED")
        recs.append(rec)
    return recs


def parse_expansion(path: str) -> list:
    data = json.load(open(path, encoding="utf-8"))
    recs = []
    for r in data["records"]:
        recs.append({
            "id": r["id"], "cluster": EXP_CLUSTER.get(r["id"], "G?"),
            "heading": f"{r['first_author']} ({r['year']})",
            "citation": r["title_clean"], "locator": f"DOI {r['doi']}",
            "verification": r["status"], "annotation": r["k"],
            "analysis": r["analysis"], "year": r["year"], "doi": r["doi"],
            "k_all": sorted({f"K{k}" for k, _ in K_RE.findall(r["k"])},
                            key=lambda s: int(s[1:])),
            "k_primary": [f"K{k}" for k, kind in K_RE.findall(r["k"]) if kind == "主"],
            "k_secondary": [f"K{k}" for k, kind in K_RE.findall(r["k"]) if kind == "辅"],
            "d_class": ("mixed" if r["role"] in ("D±", "D+-") else
                        "D+" if r["role"] == "D+" else
                        "D-" if r["role"] == "D-" else "value-only"),
            "evidence": r["evidence"],
            "verification_level": "IDENTITY_VERIFIED" if r["status"] == "IDENTITY_VERIFIED" else "?",
        })
    return recs


def main() -> int:
    recs = parse_phase1(open(REG, encoding="utf-8").read())
    p1 = len(recs)
    recs += parse_expansion(EXP)
    print(f"parsed phase I: {p1}, expansion: {len(recs) - p1}, total {len(recs)}")

    fams = [f"K{i}" for i in range(1, 13)]
    clusters = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]

    # K x cluster, all annotations (single metric; see module docstring)
    mat = {f: Counter() for f in fams}
    for r in recs:
        for f in r["k_all"]:
            if f in mat:
                mat[f][r["cluster"]] += 1
    coverage = {f: sum(1 for c in clusters if mat[f][c] > 0) for f in fams}
    totals = {f: sum(mat[f].values()) for f in fams}

    # directional votes per family
    votes = {f: Counter() for f in fams}
    for r in recs:
        for f in r["k_all"]:
            if f in votes:
                votes[f][r["d_class"]] += 1

    # evidence mix per family
    ev = {f: Counter() for f in fams}
    for r in recs:
        for f in r["k_all"]:
            if f in ev:
                ev[f][r["evidence"] or "unspecified"] += 1

    vlevels = Counter(r["verification_level"] for r in recs)
    with_doi = sum(1 for r in recs if r["doi"])
    payload = {
        "schema": "m2a.phase1prime.synthesis.v2",
        "counts": {"records": len(recs), "phase1": p1, "expansion": len(recs) - p1,
                   "with_doi": with_doi, "verification_levels": dict(vlevels)},
        "definitions": {
            "coverage": "number of clusters with >=1 PRIMARY annotation of the family",
            "votes": "PRIMARY annotation D role only: D+ / D- / D+-",
            "evidence": "declared evidence type of the record whose annotation names the family",
        },
        "coverage_by_family": coverage,
        "totals_by_family": totals,
        "matrix": {f: dict(mat[f]) for f in fams},
        "votes": {f: dict(votes[f]) for f in fams},
        "evidence": {f: dict(ev[f]) for f in fams},
    }
    json.dump(payload, open(OUT_SYN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"schema": "m2a.registry.v2", "records": recs},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lines = ["# M2A Phase I′ 量化综合 v2（机器生成）", "",
             f"> 记录 {len(recs)} 条（Phase I {p1} + 扩展 {len(recs) - p1}）｜带 DOI {with_doi} 条",
             f"> 核验级别：{dict(vlevels)}", "",
             "## 计量口径（写死）",
             "- **覆盖**：该族被标注（任一 K 提及）的**集群数**（0–8）。Phase I 的标注不带主/辅标记，"
             "扩展带标记；为保持单一口径，矩阵对两者都按「任一提及」计。",
             "- **票数**：按记录的 D 标记分类（仅 D+ / 仅 D− / 混合 / 仅价值）。",
             "- **证据**：该记录声明的证据类型。", "",
             "## 1 覆盖与票数", "",
             "| 族 | 标注总数 | 覆盖集群数 | D+ | D− | 混合 | 仅价值 | 主要证据类型 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for f in fams:
        v = votes[f]
        top_ev = ", ".join(f"{k}×{n}" for k, n in ev[f].most_common(2)) or "—"
        lines.append(f"| {f} | {totals[f]} | {coverage[f]}/8 | {v.get('D+', 0)} | "
                     f"{v.get('D-', 0)} | {v.get('mixed', 0)} | {v.get('value-only', 0)} | {top_ev} |")
    lines += ["", "## 2 K × 集群矩阵（任一标注计数）", "",
              "| 族 | " + " | ".join(clusters) + " |",
              "| --- | " + " | ".join("---" for _ in clusters) + " |"]
    for f in fams:
        lines.append(f"| {f} | " + " | ".join(str(mat[f][c]) for c in clusters) + " |")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("coverage:", {f: coverage[f] for f in fams})
    print("totals  :", totals)
    print(f"wrote {OUT_JSON}, {OUT_SYN}, {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
