"""Derive which report step-section was published to the owner's wiki, and pin the tools that guard it.

Why this exists. The standing instruction is 「后续更新每一步写入飞书，按照wiki模式」 - every step must be
written into the wiki. Until now that obligation was carried only by prose and by three files that live
OUTSIDE this repository (`check_step_draft_numbers.py`, `publish_wiki_steps.py`, `feishu_wiki_nodes.json`
at the workshop root). Nothing inside the repo could say whether the newest section had been published,
or whether the guard that decides that had itself been edited. This map makes both derived facts that
the closing audit runs.

Population and joins:
  * sections: every `### N` / `## N` heading in `M2A_FINAL_REPORT.md` with N >= 31, i.e. the work done
    after the wiki channel was established on 2026-10-18;
  * pages: every entry of the workshop ledger that carries a node token, split by whether its title is
    in the publisher's PAGES manifest (governance-era: each must be claimed by a section) or belongs to
    the first batch driver (pinned by count instead);
  * the section -> page join is a REGISTERED table keyed on node tokens, because the prose will not
    support a reliable derivation: sections cite X-ids in five different phrasings, and one page carries
    several sections. The table is small and hand-kept - like the KNOWN tables of §42/§43 - and a typo in
    it fails loudly (dangling claim) rather than silently. Everything else here is computed from disk.

Read-only: writes only the two derived files, never calls lark-cli, never publishes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent      # m2a/
W = M.parent.parent                                     # workshop root, holds the guard tooling
GOV = M / "governance"
JSON_OUT = GOV / "wiki_sync_map_v1.json"
MD_OUT = GOV / "WIKI_SYNC_MAP_v1.md"
LEDGER = W / "feishu_wiki_nodes.json"
CHECKER = W / "check_step_draft_numbers.py"
PUBLISHER = W / "publish_wiki_steps.py"
DRAFTS = W / "feishu_wiki_drafts"
FIRST_BATCH_COUNT = 12                                  # pages written by publish_wiki_pages.py
BASE_SECTION = 31                                       # first section made after the channel opened

# section number -> node_token of the page that carries it (tokens read from feishu_wiki_nodes.json)
PUBLISH_MAP = {
    31: "QdMtweKnXi7ehikF6DUczQ4anng",   # Phase I' gate (3) recomputed for real
    32: "E79DwZ1REi97XNkUzf2cb5OBnGb",   # literature round L-01
    33: "PkCzw0RaWis8wnkjT3ZcIDncnnb",   # mechanism vocabulary v1
    34: "VUsPwexuyirFzhkASR5cVUFuned",   # five-label table v1 -> v2
    35: "P1FfwvlBGiyndek4vHlcBEcwn5c",   # ledger namespaces
    36: "P1FfwvlBGiyndek4vHlcBEcwn5c",   # claim-level reanalysis, same page
    37: "VUsPwexuyirFzhkASR5cVUFuned",   # table v2 corrects section 34, same page
    38: "AqqSwOrEmiD6iskeZ0EcQ6B0ntg",   # AO pre-flight as instrument
    39: "PvbywrdZiiSsUmkTdQbcsFMPndh",   # gate discrimination audit
    40: "PvbywrdZiiSsUmkTdQbcsFMPndh",   # its generalisation, same page
    41: "PvbywrdZiiSsUmkTdQbcsFMPndh",   # whole-repo floor, same page
    42: "D04twrA8UifjkEkAZGZcjM51nVl",   # instrument coverage map
    43: "TqFzw3ElRiuEJ8k2goXciGU8nnc",   # runner enforcement map
    44: "VgUswpUdMi7RUckLFu9cMo9Wnmb",   # three-way score reconciliation
    45: "MrE5wnDKoiJgTukBIqBcuHPsnae",   # governance-layer measurement of the 10 gaps
    46: "IVrAw0pvoiJlSXkHMUGcc4Lon8d",   # this map, published before it could be registered
    47: "KDnUwL1XYi262wkzkonc0UvZnsb",   # the score reconciliation page, published before it could be registered
    48: "QuO5w9vGFiikp1kSKbgcrh1jnnb",   # the suite-score registry page, published before it could be registered
    49: "Vftbwqe4QiQZdEk2fhOcSvDbnie",   # the label-provenance page, published before it could be registered
    50: "D99TwpMdKiqui7kK3eNciniWnhe",   # the value-provenance page, published before it could be registered
    51: "X36OwMb29id4hJk0LRHcN37SnBh",   # the Round L-02 page, published before it could be registered
    52: "KCMhwheuIiKKUjkmHjBcNaHtnHb",   # the Round L-02 page, published before it could be registered
    53: "Cyx3wvKSOimovIkm9T9cxLTCnCe",   # the label-provenance widening page, published before it could be registered
    54: "RSUQwO0FsiwASnkYsc6cSJq2nua",   # the frozen-input map page, published before it could be registered
}

SECTION_RE = r"^#{2,3} (\d+) (.*)$"


def sha256(path: pathlib.Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def manifest_entries() -> list:
    """Titles, draft names and markers read out of the publisher's PAGES list by AST, not by regex."""
    tree = ast.parse(PUBLISHER.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PAGES":
            for el in node.value.elts:
                out.append({"title": el.elts[0].value, "draft": el.elts[1].value,
                            "markers": [v.value for v in el.elts[2].elts]})
    return out


def sections(text: str) -> list:
    heads = [(int(m.group(1)), m.group(2).strip(), m.start())
             for m in re.finditer(SECTION_RE, text, re.M)]
    rows = []
    for i, (num, title, pos) in enumerate(heads):
        end = heads[i + 1][2] if i + 1 < len(heads) else len(text)
        body = text[pos:end]
        if num >= BASE_SECTION:
            # deliberately no character count: the section's own audit line is filled after this
            # artifact is derived, so a length column would make byte-reproducibility fail for a
            # reason that has nothing to do with the invariant the map guards.
            rows.append({"section": num, "title": title[:70],
                         "xids_named": sorted({int(x) for x in re.findall(r"X-(\d+)", body)})})
    return rows


def main() -> int:
    missing = [str(p) for p in (LEDGER, CHECKER, PUBLISHER) if not p.exists()]
    if missing:
        print("guard tooling absent: " + ", ".join(missing), file=sys.stderr)
        return 2

    rep = (M / "M2A_FINAL_REPORT.md").read_text(encoding="utf-8")
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    parent = led["parent_node_token"]
    man = manifest_entries()
    pages = [p for p in led.get("pages", []) if p.get("node_token")]
    by_token = {p["node_token"]: p for p in pages}

    sec_rows = sections(rep)
    pop = {r["section"] for r in sec_rows}
    # claims are a first-class row: a section may be carried by a first-batch page too, and if the
    # artifact only enumerated manifest pages then `counts` and the enumerable rows disagreed (the
    # validator's independent path found exactly that on the first build: 15 claimed, 14 listed).
    claim_rows = [{"section": n, "node_token": t, "title": (by_token.get(t) or {}).get("page"),
                   "in_ledger": t in by_token,
                   "draft": next((e["draft"] for e in man if e["title"] ==
                                  (by_token.get(t) or {}).get("page")), None)}
                  for n, t in sorted(PUBLISH_MAP.items())]
    unclaimed = sorted(pop - set(PUBLISH_MAP))
    stale_claims = sorted(set(PUBLISH_MAP) - pop)
    dangling = sorted(str(r["section"]) for r in claim_rows if not r["in_ledger"])
    claimed_titles = {r["title"] for r in claim_rows if r["title"]}
    orphan = sorted(e["title"] for e in man if e["title"] not in claimed_titles)

    page_rows = []
    for e in man:
        p = by_token.get(next((r["node_token"] for r in claim_rows if r["title"] == e["title"]), ""), {})
        draft = DRAFTS / e["draft"]
        page_rows.append({"title": e["title"], "draft": e["draft"], "markers": e["markers"],
                          "node_token": p.get("node_token"), "obj_token": p.get("obj_token"),
                          "markers_ok_recorded": p.get("markers_ok"),
                          "read_back_chars_recorded": p.get("read_back_chars"),
                          "draft_sha256": sha256(draft),
                          "draft_chars": len(draft.read_text(encoding="utf-8")) if draft.exists() else None,
                          "sections": sorted(r["section"] for r in claim_rows if r["title"] == e["title"])})

    manifest_titles = {e["title"] for e in man}
    first_batch = sorted(p["page"] for p in pages if p["page"] not in manifest_titles)
    c = {
        "report_sections_in_population": len(sec_rows),
        "sections_claimed": len([r for r in claim_rows if r["in_ledger"] and r["section"] in pop]),
        "sections_unclaimed": len(unclaimed),
        "claims_dangling": len(dangling),
        "claims_stale": len(stale_claims),
        "governance_pages": len(page_rows),
        "governance_pages_unclaimed": len(orphan),
        "ledger_pages_with_node": len(pages),
        "first_batch_pages": len(first_batch),
        "first_batch_off_pin": len(first_batch) - FIRST_BATCH_COUNT,
        "first_batch_pages_claimed_by_a_section": len([r for r in claim_rows
                                                       if r["title"] and r["title"] not in manifest_titles]),
    }

    data = {"schema": "m2a.wiki_sync_map.v1", "base_section": BASE_SECTION,
            "first_batch_expected": FIRST_BATCH_COUNT, "wiki_parent_node_token": parent,
            "counts": c, "unclaimed_sections": unclaimed, "dangling_claims": dangling,
            "stale_claims": stale_claims, "orphan_pages": orphan, "first_batch_pages": first_batch,
            "tools": [{"file": str(p.relative_to(W)), "sha256": sha256(p),
                       "bytes": p.stat().st_size if p.exists() else None}
                      for p in (CHECKER, PUBLISHER, LEDGER)],
            "sections": sec_rows, "claims": claim_rows, "pages": page_rows}
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    lines = ["# Wiki 同步表 v1（由工件推导）", "",
             "> 推导器 `governance/build_wiki_sync_map.py`，校验器 `governance/wiki_sync_map_gate.py`。",
             "> 人口：`M2A_FINAL_REPORT.md` 中编号 >= %d 的步骤节（wiki 通道 2026-10-18 建立之后做的事），"
             "以及工坊根 `feishu_wiki_nodes.json` 中带 node_token 的页面。父节点 `%s`。" % (BASE_SECTION, parent),
             "",
             "| 列 | 数 |", "| --- | --- |",
             "| 人口内步骤节 | %d |" % c["report_sections_in_population"],
             "| 已被页面承接 | %d |" % c["sections_claimed"],
             "| **未承接（本步未发布即为红）** | %d |" % c["sections_unclaimed"],
             "| 指向不存在页面的承接 | %d |" % c["claims_dangling"],
             "| 承接了已不在人口内的旧节（陈旧） | %d |" % c["claims_stale"],
             "| 治理期页面（PAGES manifest） | %d |" % c["governance_pages"],
             "| 未被任何节认领的治理期页面 | %d |" % c["governance_pages_unclaimed"],
             "| 台账中带 node_token 的页面 | %d |" % c["ledger_pages_with_node"],
             "| 首批驱动页面（按 %d 条钉住） | %d |" % (FIRST_BATCH_COUNT, c["first_batch_pages"]),
             "",
             "## 每一节由哪一页承载", "",
             "| 节 | 标题（截断） | 承接页面的 node_token | 该节点名的 X-id |",
             "| --- | --- | --- | --- |"]
    by_section = {r["section"]: r for r in claim_rows}
    for r in sec_rows:
        cl = by_section.get(r["section"]) or {}
        lines.append("| %d | %s | `%s` %s | %s |" % (
            r["section"], r["title"][:30], (cl.get("node_token") or "-未承接-")[:24],
            (cl.get("title") or "")[:22],
            ", ".join("X-%d" % x for x in r["xids_named"][-4:]) or "-"))
    lines += ["", "## 每一页的草稿指纹", "",
              "| 页面（截断） | 草稿（截断） | 草稿 sha256（前 12） | 读回字符 | markers 复核 |",
              "| --- | --- | --- | --- | --- |"]
    for p in page_rows:
        lines.append("| %s | %s | `%s` | %s | %s |" % (
            p["title"][:26], p["draft"][:30], (p["draft_sha256"] or "缺文件")[:12],
            p["read_back_chars_recorded"], p["markers_ok_recorded"]))
    lines += ["", "## 守门工具的指纹", "", "| 工具 | sha256（前 12） | 字节 |", "| --- | --- | --- |"]
    for t in data["tools"]:
        lines.append("| `%s` | `%s` | %s |" % (t["file"], (t["sha256"] or "缺文件")[:12], t["bytes"]))
    lines += ["", "**这张表能看见什么、看不见什么**：它在四件事上立刻变红——新步骤节没有对应页面；",
              "页面草稿在发布后被改写（sha 变了）；守门脚本被改写；首批页面数目偏离钉住的 %d。" % FIRST_BATCH_COUNT,
              "它**不能**证明发布动作今天仍然成功，也不能证明读回内容在语义上正确——那由发布器自己的",
              "precondition（先跑数字复核）与 `docs +fetch` 的标记串负责。「节 → 页」的对应是登记表",
              "（散文里 X-id 的措辞有五种、一页可载多节，故不做推导），其余数字均从磁盘推导。", ""]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote %s | sections %d claimed %d unclaimed %d | governance pages %d | first_batch %d (pin %d)" % (
        JSON_OUT.name, c["report_sections_in_population"], c["sections_claimed"], c["sections_unclaimed"],
        c["governance_pages"], c["first_batch_pages"], FIRST_BATCH_COUNT))
    return 0 if not unclaimed and not dangling and not orphan and not stale_claims else 1


if __name__ == "__main__":
    raise SystemExit(main())
