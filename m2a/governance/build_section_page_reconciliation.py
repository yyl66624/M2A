"""Reconcile the `n/n` scores published on the wiki against the record kept in this repository.

Why. §46's sync map proves a section *has* a page; it does not say whether the page tells the same
story. The owner reads the page, the repo keeps the record, and they are written at different moments.
The dangerous question is narrow: **does a page state an instrument score that this repository never
printed?** That is a transcription error or an invention. Everything weaker is history or editing:
suites gain rules, so an older page legitimately carries an older score (7/7 before G8 made the
registry gate 8/8; 17/17 before the coverage validator grew a rule - X-83), and pages are summaries,
so they name fewer instruments than the sections they came from.

Three modelling choices, each bought by a wrong first draft of this file:
  * the pair is {the sections a page carries} <-> {that page}. Section-by-section comparison produced
    nine false "page adds claims" because §39-§41 share one page;
  * a value counts as printed if it is attested **anywhere in the repo** (report, results documents,
    the negative log, committed artifacts such as `literature/L01_coding.json`), not only inside one
    section. Attesting against a single section turned three legitimate historical scores into "hard
    findings" that I would then have had to correct;
  * normalization keeps line structure and is applied to both sides. The claim window is
    `[^\n]{0,3}`, so collapsing newlines let it reach across a sentence and pair `l01_gate.py` with a
    "42" that belonged to a count of quotations.

Three more, bought by the first mutation probe of this suite (`scratch/probe_step47.py`):
  * the repo scan **excludes the two files this step writes**. Reading them back would have made every
    score the artifact once recorded self-attesting, so a drift could never be flagged twice - R8;
  * attestation has two resolutions. The strict 3-character window says "the repository printed this for
    this instrument"; the loose one (nearest preceding name on the same line, any distance) supports a
    page claim in the form `python3 governance/x.py   # 59/59 checks passed`, which the strict window
    cannot see. The asymmetry is deliberate: the loose tier can only ever *remove* a hard finding;
  * a published page cannot be edited, so an unsupported number on one needs an explicit **erratum row**
    (quoted value, attested replacement, negative-log X-id, and the marker text that must be on the page)
    before the verdict may stand down. Without the marker on the page the row does nothing.

Inputs: `wiki_sync_map_v1.json` for the join, the repo tree, and the capture cache
`feishu_wiki_fetches/<node_token>.txt` produced by `capture_wiki_pages.py` outside the closing audit,
so this suite never touches the network. Read-only for the repo.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent      # m2a/
W = M.parent.parent
GOV = M / "governance"
SYNC = GOV / "wiki_sync_map_v1.json"
JSON_OUT = GOV / "section_page_reconciliation_v1.json"
MD_OUT = GOV / "SECTION_PAGE_RECONCILIATION_v1.md"
CACHE = W / "feishu_wiki_fetches"
DRAFTS = W / "feishu_wiki_drafts"

CLAIM_RE = re.compile(r"([A-Za-z0-9_]+\.py)[^\n]{0,3}?(?<!\d)(\d+)/(\d+)(?!\d)")
SELF_RE = re.compile(r"(?<!\d)(\d+)/(\1)(?!\d)")
NAME_RE = re.compile(r"[A-Za-z0-9_]+\.py")
DOC_RE = re.compile(r"^#{2,3} (\d+) ", re.M)
# a derived artifact must not attest the scores it reports: reading its own output back would launder any
# drift recorded once into "attested in the repository" forever, which is the R8 self-verification hole.
SELF_OUT = {JSON_OUT.name, MD_OUT.name}
# The loose tier is a sentence-level guess, so it is only honoured where a document quotes a run's own
# printed line: the final report and the per-round result documents. Not the negative log or the ledger -
# writing a drift into the log would otherwise create the support that hides it (X-85).
LOOSE_SRC = re.compile(r"(^M2A_FINAL_REPORT\.md$|_RESULTS\.md$)")
# Registration documents transcribe what other artifacts said. They still count as sources for the strict
# tier (a log row that copies `python3 x.py # 59/59 checks passed` really does record that the suite printed
# it), but every score whose ONLY support is a transcription is counted and listed, because the same channel
# can upgrade a number from "unsupported" to "supported" - which is exactly what the X-85 row did to 59/59.
REGISTRATION = {"governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md", "governance/OBLIGATION_REGISTRY.md"}

# Published pages can only be appended to, so a number that turns out to be unsupported stays on the page
# as quoted text. An erratum row declares exactly that: this value was published, it is retracted, and the
# replacement is attested. Hand-kept like §42/§43's KNOWN tables, and the validator proves all four parts
# of every row (the quoted value really is on the page, the replacement really is printed in the repo, the
# correction marker really is on the page, the X-id really exists in the negative log).
ERRATA = {
    "E79DwZ1REi97XNkUzf2cb5OBnGb": {
        "l01_gate.py": {"quoted": "6/6", "replacement": "7/7", "xid": 85, "marker": "订正 X-85"},
    },
}


def norm(text: str) -> str:
    """Strip HTML tags and markdown emphasis line by line, keeping line breaks intact."""
    text = re.sub(r"<[^>]{1,60}>", "", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(a, b)
    text = text.replace("`", "")
    text = re.sub(r"\*\*?", "", text)
    return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines())


def claims(text: str):
    """instrument -> values attached to it; a value counts only when self-equal (n/n)."""
    out, odd = {}, {}
    for f, a, b in CLAIM_RE.findall(text):
        (out if a == b else odd).setdefault(f, set()).add(a + "/" + b)
    return out, odd


def claims_loose(text: str):
    """Second resolution: same line, nearest preceding file name, any distance. This sees the command-line
    form the 3-character window misses - `python3 governance/x.py   # 59/59 checks passed`. Used ONLY to
    support a page claim, never to make one, so the asymmetry can weaken the verdict but not manufacture
    it. That is a disclosed limit, not a silent one."""
    out = {}
    for ln in text.splitlines():
        names = [(m.start(), m.group(0)) for m in NAME_RE.finditer(ln)]
        for m in SELF_RE.finditer(ln):
            prev = [n for pos, n in names if pos < m.start()]
            if prev:
                out.setdefault(prev[-1], set()).add(m.group(1) + "/" + m.group(1))
    return out


def merge(a: dict, b: dict) -> dict:
    m = {k: set(v) for k, v in a.items()}
    for k, v in b.items():
        m.setdefault(k, set()).update(v)
    return m


def repo_record() -> tuple:
    """Every instrument score this repository prints, with the files that attest it; the loose-resolution
    support set; the subset printed inside the report; and the newest report section naming each instrument."""
    attest, attest_loose, latest, rep_values = {}, {}, {}, {}
    for p in sorted(M.rglob("*.md")) + sorted(M.rglob("*.json")):
        if p.name in SELF_OUT:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        n = norm(body)
        cl, _ = claims(n)
        rel = str(p.relative_to(M))
        for f, v in cl.items():
            a = attest.setdefault(f, {})
            for val in v:
                a.setdefault(val, []).append(rel)
        for f, v in claims_loose(n).items():
            if LOOSE_SRC.search(rel):
                attest_loose.setdefault(f, set()).update(v)
        if p.name == "M2A_FINAL_REPORT.md":
            for f, v in claims(n)[0].items():
                rep_values[f] = sorted(v)
            heads = [(int(x.group(1)), x.start()) for x in DOC_RE.finditer(body)]
            for i, (num, pos) in enumerate(heads):
                end = heads[i + 1][1] if i + 1 < len(heads) else len(body)
                for f in claims(norm(body[pos:end]))[0]:
                    latest[f] = max(latest.get(f, 0), num)
    return attest, {f: sorted(v) for f, v in attest_loose.items()}, latest, rep_values


def section_blocks(rep: str) -> dict:
    heads = [(int(m.group(1)), m.start()) for m in DOC_RE.finditer(rep)]
    out = {}
    for i, (n, pos) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else len(rep)
        out[n] = rep[pos:end]
    return out


def main() -> int:
    if not SYNC.exists():
        print("run build_wiki_sync_map.py first", file=sys.stderr)
        return 2
    sync = json.loads(SYNC.read_text(encoding="utf-8"))
    rep = (M / "M2A_FINAL_REPORT.md").read_text(encoding="utf-8")
    blocks = section_blocks(rep)
    gov = {p["node_token"]: p for p in sync["pages"]}
    attest, attest_loose, latest, rep_values = repo_record()

    groups = {}
    for c in sync["claims"]:
        if c["section"] in blocks:
            groups.setdefault(c["node_token"], []).append(c["section"])

    pages, uncaptured = [], []
    for tok, secs in sorted(groups.items(), key=lambda kv: min(kv[1])):
        title = next(c["title"] for c in sync["claims"] if c["node_token"] == tok)
        sec_claims = {}
        for s in secs:
            sec_claims = merge(sec_claims, claims(norm(blocks[s]))[0])
        cachef = CACHE / (tok + ".txt")
        if not cachef.exists():
            uncaptured.append(tok)
            pages.append({"node_token": tok, "title": title, "sections": sorted(secs),
                          "verdict": "no_capture", "unattested": {}, "superseded": {},
                          "loosely_attested": {}, "erratum": {},
                          "multi_value": {}, "not_on_page": [], "page_claims": {},
                          "attestation": {}, "page_sha256": None, "page_chars": None,
                          "draft_vs_page": {"verdict": "no_capture", "disagree": {}}})
            continue
        raw = cachef.read_text(encoding="utf-8")
        page_claims, page_odd = claims(norm(raw))
        err = ERRATA.get(tok, {})
        unattested, loosely, erratum = {}, {}, {}
        for f, v in page_claims.items():
            strict = set(attest.get(f, {}))
            supported = set(attest_loose.get(f, ()))
            marker_ok = (f in err and err[f]["marker"] in norm(raw)
                         and err[f]["replacement"] in strict)
            covered = {err[f]["quoted"]} if marker_ok and f in err and err[f]["quoted"] in v else set()
            if f in err and err[f]["quoted"] in v:
                erratum[f] = dict(err[f], marker_on_page=bool(marker_ok))
            rest, half = v - strict - covered - supported, (v & supported) - strict
            if half:
                loosely[f] = sorted(half)
            if rest:
                unattested[f] = sorted(rest)
        # superseded: the page's value for f is not what the newest citing section used
        superseded = {}
        for f, v in page_claims.items():
            newest = latest.get(f)
            if newest is None or newest <= max(secs):
                continue
            if v - set(rep_values.get(f, ())):
                superseded[f] = {"page": sorted(v), "newest_section": newest,
                                 "report_values": rep_values.get(f, [])}
        not_on_page = sorted(f for f in sec_claims if f not in page_claims)
        multi = {f: sorted(v) for f, v in page_claims.items() if len(v) > 1}
        verdict = ("score_unattested_in_repo" if unattested else
                   "compressed" if not_on_page else
                   "page_superseded" if superseded else "aligned")
        drow = {"verdict": "not_a_governance_page", "disagree": {}}
        if tok in gov:
            d = DRAFTS / gov[tok]["draft"]
            if d.exists():
                dc, _ = claims(norm(d.read_text(encoding="utf-8")))
                dis = {f: {"draft": sorted(dc.get(f, set())),
                           "page": sorted(page_claims.get(f, set()))}
                       for f in set(dc) | set(page_claims)
                       if dc.get(f, set()) != page_claims.get(f, set())}
                # the page is append-only: what the draft claimed must all be on the page, but a later
                # correction block legitimately leaves the page claiming more than the pinned draft.
                lost = {f: r for f, r in dis.items()
                        if not set(r["draft"]) <= set(r["page"])}
                drow = ({"verdict": "page_and_draft_disagree", "disagree": dis} if lost else
                        {"verdict": "page_grew_after_publication", "disagree": dis} if dis else
                        {"verdict": "aligned", "disagree": {}})
            else:
                drow = {"verdict": "draft_missing", "disagree": {}}
        pages.append({"node_token": tok, "title": title, "sections": sorted(secs), "verdict": verdict,
                      "unattested": unattested, "superseded": superseded, "multi_value": multi,
                      "loosely_attested": loosely, "erratum": erratum,
                      "not_on_page": not_on_page,
                      "section_claims": {f: sorted(v) for f, v in sorted(sec_claims.items())},
                      "page_claims": {f: sorted(v) for f, v in sorted(page_claims.items())},
                      "attestation": {f: {val: files[:2] for val, files in
                                          sorted(attest.get(f, {}).items())}
                                      for f in sorted(page_claims)},
                      "prose_slashes_ignored": {f: sorted(v) for f, v in sorted(page_odd.items())},
                      "page_chars": len(raw),
                      "page_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                      "draft_vs_page": drow})

    hard = [p for p in pages if p["verdict"] == "score_unattested_in_repo"] + \
           [p for p in pages if p["draft_vs_page"]["verdict"] in ("page_and_draft_disagree",
                                                                  "draft_missing")]
    repo_files = set(attest)
    page_files = {f for p in pages for f in p["page_claims"]}
    sec_files = {f for p in pages for f in p["section_claims"]}
    c = {"pages_reconciled": len(pages),
         "sections_covered": sum(len(p["sections"]) for p in pages),
         "claims_rows_in_sync_map": len(sync["claims"]),
         "score_unattested_in_repo": len([p for p in pages if p["verdict"] == "score_unattested_in_repo"]),
         "page_superseded": len([p for p in pages if p["verdict"] == "page_superseded"]),
         "pairs_aligned": len([p for p in pages if p["verdict"] == "aligned"]),
         "pairs_compressed": len([p for p in pages if p["verdict"] == "compressed"]),
         "pairs_no_capture": len([p for p in pages if p["verdict"] == "no_capture"]),
         "values_loosely_attested_only": sum(len(v) for p in pages for v in p["loosely_attested"].values()),
         "erratum_rows": sum(len(p["erratum"]) for p in pages),
         "erratum_rows_effective": sum(1 for p in pages for v in p["erratum"].values()
                                       if v["marker_on_page"]),
         "values_attested_only_in_registration":
             sum(1 for f in repo_files for v, files in attest[f].items()
                 if set(files) and set(files) <= REGISTRATION),
         "errata_not_effective":
             sum(1 for tok, rows in ERRATA.items() for f in rows
                 if not any(p["node_token"] == tok and p["erratum"].get(f, {}).get("marker_on_page")
                            for p in pages)),
         "draft_page_hard": len([p for p in pages if p["draft_vs_page"]["verdict"] in
                                 ("page_and_draft_disagree", "draft_missing")]),
         "draft_page_aligned": len([p for p in pages if p["draft_vs_page"]["verdict"] == "aligned"]),
         "draft_page_grew": len([p for p in pages
                                 if p["draft_vs_page"]["verdict"] == "page_grew_after_publication"]),
         "instruments_attested_in_repo": len(repo_files),
         "instruments_named_on_pages": len(page_files),
         "instruments_named_in_sections": len(sec_files),
         "instruments_only_on_pages": sorted(page_files - sec_files),
         "instruments_missing_from_pages": sorted(sec_files - page_files),
         "instrument_claims_sections": sum(len(p["section_claims"]) for p in pages),
         "instrument_claims_pages": sum(len(p["page_claims"]) for p in pages),
         "prose_slashes_ignored": sum(len(p["prose_slashes_ignored"]) for p in pages),
         "hard_findings": len(hard)}
    reg_only = [{"instrument": f, "value": v, "files": files}
                for f in sorted(attest) for v, files in sorted(attest[f].items())
                if files and set(files) <= REGISTRATION]
    data = {"schema": "m2a.section_page_reconciliation.v1", "counts": c,
            "attested_only_in_registration": reg_only,
            "repo_attestation": {f: {v: files[:2] for v, files in sorted(attest[f].items())}
                                 for f in sorted(page_files | sec_files)},
            "repo_attestation_loose": {f: v for f, v in sorted(attest_loose.items())},
            "errata": {t: {f: v for f, v in sorted(r.items())} for t, r in sorted(ERRATA.items())},
            "report_values_by_instrument": {f: v for f, v in sorted(rep_values.items())},
            "newest_section_by_instrument": {f: n for f, n in sorted(latest.items())},
            "uncaptured_tokens": uncaptured,
            "hard_findings": [{"where": p["title"][:48], "sections": p["sections"],
                               "verdict": p["verdict"], "unattested": p["unattested"],
                               "draft": p["draft_vs_page"]} for p in hard],
            "pages": pages}
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    lines = ["# 节 ↔ 页面 分数对账 v1（由工件推导）", "",
             "> 推导器 `governance/build_section_page_reconciliation.py`，校验器",
             "> `governance/section_page_reconciliation_gate.py`。承接关系取自 §46 的同步表；页面正文读自",
             "> `feishu_wiki_fetches/<node_token>.txt`（抓取在收尾审计之外进行，审计本身不联网）。",
             "> 判据只有一个硬的：页面上某仪器的 `n/n` 在**整个仓库**里既没有被严格印过、也没有被宽松读到过，",
             "> 而且没有订正登记 ⇒ 抄错或凭空。严格口径是名字后三个字符内；宽松口径是同一行内最近的前置名字，",
             "> 只用来**支持**页面的说法，不用来制造说法（口径不对称只会让判据更弱，不会凭空判红）。",
             "> 派生工件自身不在出处扫描里：给自己背书会让一次漂移永久变成「仓库里印过」（R8）。",
             "> 分数被后续轮次追上（页面写 7/7 而该套件今天印 8/8）记为 `page_superseded`，是事实陈年而非缺陷；",
             "> 页面少点名若干仪器记为 `compressed`，是摘要取舍。",
             "",
             "| 列 | 数 |", "| --- | --- |",
             "| 对账的页面 | %d |" % c["pages_reconciled"],
             "| 覆盖的步骤节 | %d（同步表登记 %d） |" % (c["sections_covered"], c["claims_rows_in_sync_map"]),
             "| **页面上的分数在仓库里查无出处** | %d |" % c["score_unattested_in_repo"],
             "| 仅由宽松口径支持的页面分数 | %d |" % c["values_loosely_attested_only"],
             "| 只由登记处转写支持的分数（洗白通道，逐条列出） | %d |"
             % c["values_attested_only_in_registration"],
             "| 已登记的订正（页面上引用为错误的数字） | %d（生效 %d） |" % (c["erratum_rows"],
                                                            c["erratum_rows_effective"]),
             "| 订正已登记但尚未生效（页面缺该数字或缺订正标记） | %d |" % c["errata_not_effective"],
             "| 页面分数已被后来的节追上 | %d |" % c["page_superseded"],
             "| 页面压缩（节里有、页里没有） | %d |" % c["pairs_compressed"],
             "| 完全一致 | %d |" % c["pairs_aligned"],
             "| 无抓取可比 | %d |" % c["pairs_no_capture"],
             "| 草稿 ↔ 页面不一致（草稿的说法页面上没有） | %d |" % c["draft_page_hard"],
             "| 页面在发布之后又追加了内容（草稿是子集） | %d |" % c["draft_page_grew"],
             "| 仓库里被印过的仪器 | %d 台 |" % c["instruments_attested_in_repo"],
             "| 页面点名 / 节点名 | %d 台 / %d 台 |" % (c["instruments_named_on_pages"],
                                                       c["instruments_named_in_sections"]),
             "| 页面分数条数 / 节分数条数 | %d / %d |" % (c["instrument_claims_pages"],
                                                        c["instrument_claims_sections"]),
             "| 只在页面出现（节里没点名） | %s |" % (", ".join(c["instruments_only_on_pages"]) or "-"),
             "| 只在节里出现（页面压缩掉） | %s |" % (", ".join(c["instruments_missing_from_pages"]) or "-"),
             "",
             "## 逐页", "",
             "| 节 | 页面（截断） | 判定 | 页面分数条数 | 仅宽松支持 | 订正 | 页面没写 | 被追上 | 草稿↔页 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for p in pages:
        lines.append("| %s | %s | %s | %d | %s | %s | %s | %s | %s |" % (
            ",".join(str(s) for s in p["sections"]), p["title"][:22], p["verdict"],
            len(p["page_claims"]),
            ", ".join("%s %s" % (f, "/".join(v)) for f, v in sorted(p["loosely_attested"].items())) or "-",
            ", ".join("%s %s→%s" % (f, v["quoted"], v["replacement"])
                      for f, v in sorted(p["erratum"].items())) or "-",
            ", ".join(p["not_on_page"]) or "-",
            ", ".join("%s %s" % (f, "/".join(v["page"])) for f, v in p["superseded"].items()) or "-",
            p["draft_vs_page"]["verdict"]))
    lines += ["", "## 每条页面分数的仓库出处（`attest`）", "",
              "| 仪器 | 页面上的分数 | 仓库里印过它的文件 | 节里最新引用它的节号 |",
              "| --- | --- | --- | --- |"]
    for p in pages:
        for f, v in sorted(p["page_claims"].items()):
            src = sorted({x for val in v for x in p["attestation"].get(f, {}).get(val, [])})[:3]
            lines.append("| `%s` | %s | %s | §%s |" % (
                f, "/".join(v), ", ".join("`%s`" % s for s in src) or "-无-", latest.get(f, "-")))
    lines += ["", "**能看见与看不见**：只比 `n/n` 头条，且只有一条硬判据。它不比句子、判据数值、容差阶梯与",
              "结论措辞；陈年分数与摘要压缩都如实列出而不判红（本项目规矩是历史陈述不回写，更正出现在新节）；",
              "抓取不重新联网，其时刻证据是 `feishu_wiki_fetches/` 的文件指纹；抓取脚本本身不在同步表钉住的",
              "工具之列（钉住的是数字复核器、发布器与台账），这是已知缺口。出处扫描**排除本工件自己写出的",
              "两个文件**（`section_page_reconciliation_v1.json`、`SECTION_PAGE_RECONCILIATION_v1.md`）：",
              "派生工件若给自己背书，一次漂移被记进工件后就永远“在仓库里印过”，判据从此打不响（R8）。",
              "它也不排除台账与负面日志那类转写件——转写错误若进了它们，仍会被当成出处，这是有意保留的宽松。", ""]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote %s | pages %d sections %d unattested %d loose %d errata %d/%d superseded %d "
          "compressed %d aligned %d draft_hard %d" % (
              JSON_OUT.name, c["pages_reconciled"], c["sections_covered"], c["score_unattested_in_repo"],
              c["values_loosely_attested_only"], c["erratum_rows_effective"], c["erratum_rows"],
              c["page_superseded"], c["pairs_compressed"], c["pairs_aligned"], c["draft_page_hard"]))
    return 0 if not hard and not uncaptured and not c["errata_not_effective"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
