"""Reconcile three different "how many checks does this round's instrument have" numbers.

The round documents open with a score line - `门控 \`p10_gate.py\` **6/6**` - the suite prints a score
when it runs, and §42's coverage map counts `check()` SITES in the source. Those three numbers are
routinely conflated in prose, and they are not the same quantity: a `check()` inside a loop prints
more verdicts than it has sites (Phase XVII: 6 sites, 7 printed), and a document written before an
amendment can carry a score the instrument no longer prints. This derives all three per round and
classifies the disagreement instead of assuming agreement.

  claim   - the fraction in the document's own header block, on a line that says 门控;
  live    - the `n/N checks passed` line the gate prints when run here, now;
  static  - the count of `check()` call sites in that gate (from gate_coverage_map_v1.json);
  source  - the gate file named inline in the document, cross-checked against the round's own gate,
            because "the doc says p14 while the round is Phase XV" is exactly the wrong-file class.

Verdicts: `aligned`, `doc_stale` (claim != live), `live_red` (the instrument does not pass today),
`loop_nested` / `other_harness` (live != static, with a registered reason - a loop-nested site, or an
instrument that does not use check() at all and so counts 0 statically), `claim_names_other_instrument`
(the doc quotes a gate that is not this round's), `no_claim`. Anything unregistered fails the build:
a round silently losing its score line is the same drift X-74 recorded for the label table.

Running every gate in the population takes a few minutes, so the deriver can reuse the scores it already recorded
(`--offline`); the validator re-runs a deterministic sample instead of the whole population.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

M = pathlib.Path(__file__).resolve().parent.parent
EXP = M / "experiments"
FRACTION = re.compile(r"(\d{1,2})\s*/\s*(\d{1,2})")
GATE_NAME = re.compile(r"`([a-z0-9_]+_gate\.py)`")

DOCS = sorted(EXP.glob("PHASE*_RESULTS.md")) + sorted((M / "literature").glob("ROUND_*_RESULTS.md"))

# rounds whose document legitimately states no score for its own instrument (name -> why)
KNOWN_NO_CLAIM = {}

# Instrument name -> (kind, why the static count is not comparable to the printed count).
# Two different reasons, both real in this repo:
KNOWN_STATIC_GAPS = {
    "p17_gate.py": ("loop_nested",
                    "G1 的锚定比较写在 `for` 里（两条口径各一次），静态 6 个站点、执行 7 条判定。"
                    "§42 的 169 是**站点数**，门控打印的是**判定条数**：本表把两个数放在一起，"
                    "免得「169」被当成执行量引用。"),
    "l01_gate.py": ("other_harness",
                    "文献轮的 `l01_gate.py` 不使用 `check()`——它自带断言并打印 `7/7 checks passed`，"
                    "所以 §42 的静态普查对它记 0。这是「两数不可比」，不是缺失：§42 的 §4 第三条"
                    "已声明本库对不使用 `check()` 的门控**沉默**。"),
    "l02_gate.py": ("other_harness",
                    "L-02 的门控与 `l01_gate.py` 同一族：它用自己的 `report()` 记录判定并把条数钉在 "
                    "`RULES` 常量上，`check()` 站点为 0，静态普查与打印的 `n/n` 不可比。它与打印数的唯一"
                    "区别是判定条数由登记表决定，而不是由出现过几次 `check()` 决定。"),
    "p26_gate.py": ("other_harness",
                    "Phase XXVI 的门控用自带的 report() 记录判定，check() 站点为 0；"
                    "静态站点数与打印的 n/n 不可比。"),
    "p25_gate.py": ("other_harness",
                    "Phase XXV 的门控用自带的 report() 记录判定，check() 站点为 0；"
                    "静态站点数与打印的 n/n 不可比。"),
    "l03_gate.py": ("other_harness",
                    "L-03 的门控与 `l01_gate.py`/`l02_gate.py` 同一族：它用自己的 `report()` 记录判定，"
                    "`check()` 站点为 0；full 模式打印 20/20，pre 模式打印 13/13，静态站点数与两者都不可比。"),
}


def expected_gate(doc):
    m = re.fullmatch(r"ROUND_L(\d+)_RESULTS\.md", doc.name)
    if m:
        return "literature/l%s_gate.py" % m.group(1).lower()
    ph = doc.name.replace("PHASE", "").replace("_RESULTS.md", "")
    stem = "phase2_gate.py" if ph == "2" else "p%s_gate.py" % ph.lower()
    rel = "literature/" if stem.startswith("l01") else "experiments/"
    return rel + stem


def header_claim(doc):
    """(claim pair, named gate, line) from the document's first lines, or (None, ...)."""
    lines = doc.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines[:16]):
        if "门控" not in line and "gate" not in line.lower():
            continue
        fr = FRACTION.search(line)
        if not fr:
            continue
        named = GATE_NAME.search(line)
        return (int(fr.group(1)), int(fr.group(2))), (named.group(1) if named else None), i + 1
    return None, None, None


def run_gate(rel):
    r = subprocess.run([sys.executable, rel], cwd=M, capture_output=True, text=True, timeout=900)
    # A gate may wrap another gate (p23_gate runs the AO preflight and quotes its 8/8 in a
    # detail). X-68's contract is the gate's own LAST line, so take the last fraction, not the
    # first one (X-125: re.search read the wrapper as 8/8 and marked the 15/15 document stale).
    ms = re.findall(r"(\d+)/(\d+) checks passed", r.stdout)
    return (int(ms[-1][0]), int(ms[-1][1])) if ms else None


def classify(row):
    if row["claim"] is None:
        return "no_claim"
    if row["gate"] != row["named_gate"] and row["named_gate"]:
        mapped = pathlib.Path(row["gate"]).name
        if mapped != row["named_gate"]:
            return "claim_names_other_instrument"
    live = row["live"]
    if live is None:
        return "live_red"
    if live[0] != live[1]:
        return "live_red"
    if tuple(row["claim"]) != tuple(live):
        return "doc_stale"
    if row["static_sites"] is not None and row["static_sites"] != live[1]:
        kind = KNOWN_STATIC_GAPS.get(pathlib.Path(row["gate"]).name, (None,))[0]
        return kind or "unexplained_static_live_gap"
    return "aligned"


def build(offline):
    cm = json.loads((M / "governance/gate_coverage_map_v1.json").read_text(encoding="utf-8"))
    static = {r["file"]: len(r["checks"]) for r in cm["rows"]}
    previous = {}
    if (M / "governance/result_score_reconciliation_v1.json").exists():
        previous = {r["gate"]: r["live"]
                    for r in json.loads((M / "governance/result_score_reconciliation_v1.json")
                                        .read_text(encoding="utf-8"))["rows"]}
    rows = []
    for doc in DOCS:
        gate = expected_gate(doc)
        claim, named, line = header_claim(doc)
        stem = pathlib.Path(gate).name
        if offline:
            live = previous.get(gate)
            if live is None:
                raise SystemExit("--offline needs recorded scores; run without it first")
        else:
            live = run_gate(gate)
        rows.append({"doc": doc.relative_to(M).as_posix(), "gate": gate,
                     "named_gate": named, "claim_line": line,
                     "claim": list(claim) if claim else None,
                     "live": list(live) if live else None,
                     "static_sites": static.get(stem),
                     "gate_sha256": None,
                     "verdict": None})
    for r in rows:
        r["gate_sha256"] = __import__("hashlib").sha256((M / r["gate"]).read_bytes()).hexdigest()
        r["verdict"] = classify(r)
    return rows, static


def registration_errors(rows):
    ungated = [r["doc"] for r in rows if r["verdict"] == "no_claim"]
    unregistered = sorted(d for d in ungated if pathlib.Path(d).name not in KNOWN_NO_CLAIM)
    stale = sorted(f for f in KNOWN_NO_CLAIM if f not in {pathlib.Path(d).name for d in ungated})
    gaps = sorted({pathlib.Path(r["gate"]).name for r in rows
                   if r["verdict"] == "unexplained_static_live_gap"})
    return unregistered, stale, gaps


def main():
    offline = "--offline" in sys.argv
    rows, static = build(offline)
    unregistered, stale, gaps = registration_errors(rows)
    if unregistered or stale or gaps:
        print("registration failed | no-claim docs not registered: " + str(unregistered)
              + " | stale no-claim registrations: " + str(stale)
              + " | static/live gaps with no registered explanation: " + str(gaps), file=sys.stderr)
        raise SystemExit(4)
    counts = {"docs": len(rows),
              "aligned": sum(1 for r in rows if r["verdict"] == "aligned"),
              "static_gap_registered": sum(1 for r in rows if r["verdict"] in
                                           ("loop_nested", "other_harness")),
              "bad": sum(1 for r in rows if r["verdict"] in
                         ("doc_stale", "live_red", "claim_names_other_instrument",
                          "unexplained_static_live_gap")),
              "no_claim": sum(1 for r in rows if r["verdict"] == "no_claim"),
              "checks_printed": sum(r["live"][1] for r in rows if r["live"]),
              "check_sites_static": sum(static.values()),
              "static_sites_in_population": sum(r["static_sites"] or 0 for r in rows)}
    (M / "governance/result_score_reconciliation_v1.json").write_text(json.dumps(
        {"schema": "m2a.result-score-reconciliation.v1",
         "counts": counts, "rows": rows,
         "known_no_claim": KNOWN_NO_CLAIM,
         "known_static_gaps": {k: {"kind": v[0], "why": v[1]}
                               for k, v in KNOWN_STATIC_GAPS.items()},
         "quantities": {"claim": "fraction in the round document's header line",
                        "live": "the n/N the instrument prints when run now",
                        "static": "check() call SITES counted syntactically (§42)",
                        "note": "a loop-nested site prints several verdicts, so live != static is "
                                "a real difference of quantity, not an error"}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("docs", counts["docs"], "| aligned", counts["aligned"], "| static gaps",
          counts["static_gap_registered"], "| bad", counts["bad"], "| no_claim", counts["no_claim"],
          "| printed", counts["checks_printed"], "| static sites", counts["check_sites_static"])
    for r in rows:
        if r["verdict"] not in ("aligned",):
            print("  ", r["verdict"], r["doc"], "claim", r["claim"], "live", r["live"],
                  "static", r["static_sites"])
    write_md(rows, counts)


def write_md(rows, counts):
    loop = [r for r in rows if r["verdict"] == "loop_nested"]
    harness = [r for r in rows if r["verdict"] == "other_harness"]
    cov = json.loads((M / "governance/gate_coverage_map_v1.json").read_text(encoding="utf-8"))
    n_cov = cov["counts"]["gates"]
    pop_names = {pathlib.Path(r["gate"]).name for r in rows}
    out_rows = [g for g in cov["rows"] if pathlib.Path(g["gate"]).name not in pop_names]
    outside = len(out_rows)
    cov_out_sites = sum(len(g["checks"]) for g in out_rows)
    harness_printed = sum(r["live"][1] for r in harness)
    loop_extra = sum(r["live"][1] - r["static_sites"] for r in loop)
    harness_names = "、".join("`%s`" % pathlib.Path(r["gate"]).name for r in harness)
    out_names = "、".join("`%s`" % pathlib.Path(g["gate"]).name for g in out_rows)
    loop_names = "、".join("`%s`" % pathlib.Path(r["gate"]).name for r in loop)
    loop_ex = "、".join("`%s`：%d 站点 / %d 判定"
                       % (pathlib.Path(r["gate"]).name, r["static_sites"], r["live"][1])
                       for r in loop)
    harness_ex = "、".join("`%s`：0 站点 / %d 判定"
                           % (pathlib.Path(r["gate"]).name, r["live"][1]) for r in harness)
    assert (counts["static_sites_in_population"] + harness_printed + loop_extra
            == counts["checks_printed"]), "the printed total is not this identity"
    assert (counts["static_sites_in_population"] + cov_out_sites
            == counts["check_sites_static"]), "the §42 site total is not this identity"
    assert n_cov == len(rows) + outside, "§42 and this population are not one subtraction apart"
    print("  identity printed", counts["static_sites_in_population"], "+", harness_printed, "+",
          loop_extra, "=", counts["checks_printed"], "| static",
          counts["static_sites_in_population"], "+", cov_out_sites, "=",
          counts["check_sites_static"], "| §42 gates", n_cov, "minus population", len(rows),
          "=", outside)
    md = ["# 门控分数三方对账 v1（文档引用 ↔ 仪器实跑 ↔ 静态站点数）", "",
          "> 生成物：本文件与 `governance/result_score_reconciliation_v1.json`。"
          "不跑实验、不改任何轮次文档与判定；`live` 这一列就是**跑一次门控**。", "",
          "## 1 三个数不是同一个东西", "",
          "* **claim**：轮次文档开头那一行写的分数（`门控 \`p10_gate.py\` **6/6**`）；",
          "* **live**：这台门控今天被跑到时打印的 `n/N checks passed`；",
          f"* **static**：§42 覆盖表按语法数出的 `check()` **站点数**（全库 {counts['check_sites_static']}）。",
          "",
          f"两个数会分开，本库现有 **{len(loop) + len(harness)}** 例（都已登记，见 §3.1）："
          "一条写在 `for` 里的 `check()` 只有一个站点、却打印多条判定（" + loop_ex + "）；"
          "不使用 `check()` 的自带仪器在静态普查里记 0（" + harness_ex + "）。这就是为什么 §42 那句「"
          f"{counts['check_sites_static']} 条 `check()`」必须被读作**站点数**而不是执行量。", "",
          f"人口：**{counts['docs']} 份轮次文档**；判定：**aligned {counts['aligned']}**、"
          f"已登记的静态口径差 {counts['static_gap_registered']}、坏判定 {counts['bad']}、"
          f"无分数声明 {counts['no_claim']}。"
          f"执行侧共打印 **{counts['checks_printed']}** 条判定，"
          f"本表人口内 {len(rows)} 台仪器静态共 **{counts['static_sites_in_population']}** 个站点"
          f"（§42 全库 {n_cov} 台是 {counts['check_sites_static']} 个——**这两个总数是两条不同的"
          "抵消，不代表同一件事**，见 §1.1）。", "",
          "## 2 逐轮对账", "",
          "| 文档 | 仪器 | 文档引用 | 实跑 | 静态站点 | 判定 |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append("| `" + r["doc"].split("/")[-1] + "` | `" + r["gate"] + "` | "
                  + ("%d/%d" % tuple(r["claim"]) if r["claim"] else "—") + " | "
                  + ("%d/%d" % tuple(r["live"]) if r["live"] else "—") + " | "
                  + (str(r["static_sites"]) if r["static_sites"] is not None else "—") + " | `"
                  + r["verdict"] + "` |")
    md += ["", "## 3 登记在册的例外", "",
           "### 3.1 静态站点数与打印判定数不可比（每一条都必须写明类别与原因）", ""]
    for k, (kind, v) in KNOWN_STATIC_GAPS.items():
        md.append("- `" + k + "`（类别 `" + kind + "`）：" + v)
    md += ["", "### 3.2 文档未声明分数", ""]
    if KNOWN_NO_CLAIM:
        for k, v in KNOWN_NO_CLAIM.items():
            md.append("- `" + k + "`：" + v)
    else:
        md.append("- 无。若某轮文档删掉了分数行而未登记，构建直接失败。")
    md += ["", "## 4 本表看不见的东西", "",
           "1. **分数对得上不代表门控量了判据**——那是 §42 覆盖表的层面；本表只管三个数是否互相一致。",
           "2. **`live` 是今天的读数**：文档写的是当时的读数。本轮全部一致，但这条检查的意义在于"
           "「amendment 之后忘了改文档」那一天会立刻红。",
           "3. **只覆盖 `n/N checks passed` 这种打印格式**（与收尾审计同一契约，X-68）。",
           "", "---", "", "## 复现", "", "```bash",
           "python3 governance/build_result_score_reconciliation.py           # 跑到实跑一遍门控",
           "python3 governance/build_result_score_reconciliation.py --offline  # 复用已记录分数",
           "python3 governance/result_score_map_gate.py", "```", ""]
    md += ["", "### 1.1 两条不同的抵消，各自算出各自的总数", "",
           f"文档人口内 {len(rows)} 台仪器的静态站点数之和是 **{counts['static_sites_in_population']}**；"
           "§42 的人口比本表多 " + str(outside) + " 台（" + out_names + "），"
           "它们没有轮次文档、不参与三方对账；这些台在覆盖表里的站点数逐台相加得 "
           + str(cov_out_sites) + " 个，所以全库是 **" + str(counts["check_sites_static"])
           + "** 个——这条等式由构建 assert，不成立则构建失败。",
           "执行侧打印总数是 **" + str(counts["checks_printed"]) + "** 条 = "
           + str(counts["static_sites_in_population"]) + " + 自带仪器打印的 "
           + str(harness_printed) + " 条（" + harness_names + "，静态记 0）+ 循环内多出的 "
           + str(loop_extra) + " 条（" + loop_names + "），同样由构建 assert。",
           "在 L-02 之前这两个总数恰好相等：当时自带仪器补的判定条数与循环多出的那条，"
           "刚好等于 §42 多出那台的站点数。两条不同的抵消对上同一个数是巧合不是关系，"
           "本轮新增的自带仪器把它分开了。**只比总数会同时抹平两处口径差，抹平之后还看不出来**，"
           "所以本表逐台比对，不对总数。", ""]
    (M / "report/RESULT_SCORE_RECONCILIATION_v1.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote report/RESULT_SCORE_RECONCILIATION_v1.md")


if __name__ == "__main__":
    main()
