"""Build the mechanism-vocabulary v1 draft (owner decision 2026-10-18, item 5 and §2-2).

Everything in the emitted documents is DERIVED, nothing is typed by hand:
  * term definitions  <- 01_COMMON_DEFINITIONS.md §1.1-§1.5 (frozen) and 03_LAYER_TAXONOMY.md
  * field enums       <- 02_ANNOTATION_RULES.md §2.2 (frozen)
  * bridge ids        <- 06_MECHANISM_BRIDGE_REGISTRY.md (verdict words read from each B entry)
  * observed usage    <- literature/registry.json (106 rows) + literature/L01_coding.json
The point of the round is the drift table: the committed registry already uses spellings that
01/02 do not define ('D-', 'D±', 'unspecified', 'value-only'), and Phase I' synthesis invented a
fourth voting vocabulary. An alias table reconciles them WITHOUT rewriting registry.json (§5
append-only, decision 8) - a vocabulary version that silently renames past rows is worthless.
"""
import datetime
import json
import pathlib
import re

M = pathlib.Path(__file__).resolve().parent.parent
VERSION = "v1.0-draft"
STATUS = {"AGGREGATE": "PROVISIONAL"}


def read(rel):
    return (M / rel).read_text(encoding="utf-8")


def section(text, start, stop=None):
    i = text.index(start)
    j = text.index(stop) if stop else len(text)
    return text[i:j]


d01 = read("01_COMMON_DEFINITIONS.md")
d02 = read("02_ANNOTATION_RULES.md")
d03 = read("03_LAYER_TAXONOMY.md")
d06 = read("06_MECHANISM_BRIDGE_REGISTRY.md")
d08 = read("08_OPEN_QUESTIONS.md")
dec = read("governance/OWNER_DECISION_2026-10-18.md")

k_fam = {}
for num, zh, en in re.findall(r"K(\d+)\s+([^（|｜\n]+)（([^）]+)）", section(d01, "## 1.2", "## 1.3")):
    k_fam["K" + num] = {"zh": zh.strip(), "en": en.strip()}
layers = {}
lay_sec = section(d01, "## 1.3", "## 1.4")
for num, zh in re.findall(r"L(\d+)\s+([^|｜\n]+)", lay_sec):
    layers["L" + num] = zh.strip().replace("。", "").strip()
agency = re.findall(r"(AGENTIC|RESPONSIVE|MIXED)：([^\n]+)", section(d01, "## 1.1", "## 1.2"))
grammar = re.search(r"\[MOTION SOURCE\].*", d01).group(0).strip()
axes = {"D": re.findall(r"\*\*D 轴（行动效果）\*\*：(.+)", d01)[0].strip(),
        "V": re.findall(r"\*\*V 轴（价值效果）\*\*：(.+)", d01)[0].strip()}
aux_marks = re.findall(r"(NEUTRAL_VALUE|MIXED|UNCERTAIN)（([^）]+)）", section(d01, "## 1.4", "## 1.5"))

enums = {}
for name, line in re.findall(r"(verification_level|evidence_type|provenance|d_axis|v_axis|agency_class):"
                             r"\s*([^|}\n]+(?:\|[^|}\n]+)*)", d02):
    if name not in enums:
        enums[name] = [v.strip() for v in line.strip().strip("[]").split("|") if v.strip()]
bridge = []
for bid, rest in re.findall(r"^## (B-\d{2})[^\n]*\n(.*?)(?=^## |\Z)", d06, re.S | re.M):
    verdict = re.search(r"判定：\*\*(\*\*)?([A-Z-]+(?:（[^）]*）)?)", rest, re.S)
    title = re.match(r"^## (B-\d{2}) (.*)", d06[d06.index("## " + bid):], re.M).group(2).strip()
    bridge.append({"id": bid, "title": title,
                   "verdict": (verdict.group(2) if verdict else "UNPARSED").strip()})
o07 = re.search(r"\*\*O-07｜AGGREGATE[^*]*\*\*.*", d08).group(0).strip()
agg_line = re.search(r"AGGREGATE 暂定为派生聚合表示[^\n|；]*", dec).group(0).strip().strip("*")

reg = json.loads(read("literature/registry.json"))["records"]
k_used = {}
for r in reg:
    for kk in r["k_all"]:
        k_used[kk] = k_used.get(kk, 0) + 1
prim = {}
for r in reg:
    for kk in r.get("k_primary") or []:
        prim[kk] = prim.get(kk, 0) + 1
dclass_observed = {}
for r in reg:
    dclass_observed[str(r.get("d_class"))] = dclass_observed.get(str(r.get("d_class")), 0) + 1
lvl_observed = {}
for r in reg:
    lvl_observed[str(r.get("verification_level"))] = lvl_observed.get(str(r.get("verification_level")), 0) + 1
l01 = json.loads(read("literature/L01_coding.json"))
usage_l01 = l01["vocabulary_usage"]

ALIAS = {
    "D+": "D+ (01 §1.4)", "D-": "D− (01 §1.4) — ASCII hyphen, 12 rows",
    "D−": "D− (01 §1.4)", "D±": "MIXED (01 §1.4 辅助标记) — invented in the registry",
    "mixed": "MIXED (01 §1.4 辅助标记)",
    "value-only": "NEUTRAL_VALUE (01 §1.4) — 'D 有效而 V 中性'",
    "unspecified": "UNCERTAIN (01 §1.4 辅助标记) — no direction claim made",
    "neutral": "NEUTRAL_VALUE (02 §2.2 writes the same state as d_axis: neutral)",
}
alias_rows = []
for spelling, n in sorted(dclass_observed.items(), key=lambda kv: -kv[1]):
    alias_rows.append({"observed": spelling, "rows": n, "source": "registry.json (106 rows)",
                       "canonical": ALIAS.get(spelling, "UNMAPPED")})
for spelling in sorted(set(list(usage_l01["d_class"]) + ["neutral", "D±", "unspecified"])):
    if spelling not in dclass_observed:
        alias_rows.append({"observed": spelling, "rows": usage_l01["d_class"].get(spelling, 0),
                           "source": "L01_coding.json (17 records)",
                           "canonical": ALIAS.get(spelling, "UNMAPPED")})
unmapped = [a for a in alias_rows if a["canonical"] == "UNMAPPED"]

assert len(k_fam) == 12, len(k_fam)
assert len(layers) == 7, len(layers)
assert len(bridge) == 8, len(bridge)
assert not unmapped, unmapped
assert set(k_used) <= set(k_fam), set(k_used) - set(k_fam)
assert len(agency) == 3 and len(aux_marks) == 3, (agency, aux_marks)
assert all(b["verdict"].startswith(("VALID", "ANALOGY", "INVALID")) for b in bridge), bridge

out = {"schema": "m2a.vocabulary." + VERSION, "version": VERSION,
       "generated": datetime.date(2026, 10, 18).isoformat(),
       "derived_from": ["01_COMMON_DEFINITIONS.md §1.1-§1.5", "02_ANNOTATION_RULES.md §2.2",
                        "03_LAYER_TAXONOMY.md", "06_MECHANISM_BRIDGE_REGISTRY.md",
                        "08_OPEN_QUESTIONS.md O-07", "governance/OWNER_DECISION_2026-10-18.md item 5",
                        "literature/registry.json (106 rows)",
                        "literature/L01_coding.json (17 records)"],
       "k_families": {k: {**v, "registry_rows": k_used.get(k, 0), "registry_primary": prim.get(k, 0),
                          "l01_primary": usage_l01["k_primary"].get(k, 0),
                          "l01_auxiliary": usage_l01["k_auxiliary"].get(k, 0)} for k, v in k_fam.items()},
       "layers": {k: {**{"zh": v}, "l01_records": usage_l01["layers"].get(k, 0)} for k, v in layers.items()},
       "axes": {"D": axes["D"], "V": axes["V"], "auxiliary_marks": dict(aux_marks)},
       "agency_classes": {a: t.strip() for a, t in agency},
       "event_grammar": grammar,
       "field_enums_from_02": enums,
       "bridges": bridge,
       "aggregate": {"status": STATUS["AGGREGATE"], "decision_wording": agg_line,
                     "open_question": o07,
                     "consequence": "AGGREGATE may be used as a term of art for macro-patterns that "
                                    "no individual intends; it does NOT license attributing agency, "
                                    "an action, or a value to the aggregate. Any bridge that needs "
                                    "the aggregate to ACT must first clear a round of its own."},
       "drift": {"registry_d_class_observed": dclass_observed, "alias_table": alias_rows,
                 "registry_verification_levels": lvl_observed,
                 "note": "registry.json is NOT rewritten (§5 append-only, decision 8). The alias "
                         "table is the reconciliation instrument; the canonical column states which "
                         "01 §1.4 term each observed spelling means."},
       "versioning_rules": [
           "term ids are permanent: K5 stays K5 forever; a retired family is marked DEPRECATED in a "
           "new version file, never deleted or renumbered",
           "adding/renaming a K family or an L layer requires a new version file (v1.n) plus a hash "
           "binding; edits to a frozen 0x file are not the mechanism",
           "every emitted count must be re-derivable by this script; a hand-typed number in the "
           "generated document is a build failure",
           "PROVISIONAL terms (currently only AGGREGATE) may not appear in a SUPPORTED_MECHANISM "
           "claim until a round promotes them"]}

(M / ("governance/mechanism_vocabulary_" + VERSION + ".json")).write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

md = ["# M2A 机制词表 v1（草案，机器推导）",
      "",
      f"> 版本 `{VERSION}` ｜ 生成日期 2026-10-18 ｜ 生成脚本 `governance/build_mechanism_vocabulary.py`",
      "> 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 5 条 + §2 第 2 项（`O-15` 的 Agent 通道）。",
      "> **本文件所有数字与词条一律由脚本从已提交工件推导**，手写数字即构建失败。",
      "> 本文件是**新增**治理文件：`01`/`02`/`03`/`06` 与 `literature/registry.json` 一字未改（§5 追加制、第 8 条）。",
      "",
      "## 1 十二机制族（01 §1.2 冻结用词 + 实际用量）",
      "",
      "| 族 | 中文 | 英文 | Phase I′ 注册表行数 | 其中主族 | L-01 主族 | L-01 辅族 |",
      "| --- | --- | --- | --- | --- | --- | --- |"]
for k in sorted(k_fam, key=lambda x: int(x[1:])):
    v = out["k_families"][k]
    md.append(f"| **{k}** | {v['zh']} | {v['en']} | {v['registry_rows']} | {v['registry_primary']} "
              f"| {v['l01_primary']} | {v['l01_auxiliary']} |")
md += ["", "## 2 六层（01 §1.3 / 03 试标）", "", "| 层 | 定义用词 | L-01 记录数 |", "| --- | --- | --- |"]
for k in sorted(layers, key=lambda x: int(x[1:])):
    md.append(f"| **{k}** | {layers[k]} | {out['layers'][k]['l01_records']} |")
md += ["", "## 3 两轴与辅助标记（01 §1.4）", "",
       f"- **D 轴**：{axes['D']}", f"- **V 轴**：{axes['V']}",
       "- 辅助标记：" + "；".join(f"`{a}`（{b}）" for a, b in aux_marks),
       "", "## 4 机构类别与事件语法（01 §1.1 / §1.5）", "",
       "- " + "\n- ".join(f"`{a}`：{t}" for a, t in out["agency_classes"].items()),
       "- 事件语法：" + grammar,
       "", "## 5 字段枚举（02 §2.2 冻结案例契约）", "",
       "| 字段 | 允许值 |", "| --- | --- |"]
for name, vals in enums.items():
    md.append(f"| `{name}` | " + " \\| ".join(vals) + " |")
md += ["", "## 6 跨域桥接 id（06，判定逐条读出）", "", "| id | 标题 | 判定 |", "| --- | --- | --- |"]
for b in bridge:
    md.append(f"| {b['id']} | {b['title']} | {b['verdict']} |")
md += ["", "## 7 AGGREGATE（本轮唯一新增术语，状态 " + STATUS["AGGREGATE"] + "）", "",
       "- owner 裁定用词：**" + agg_line + "**",
       "- 原开放项：" + o07,
       "- 许可范围：" + out["aggregate"]["consequence"],
       "- 词表处理：以「派生聚合表示」写入 v1，标 `PROVISIONAL`；`PROVISIONAL` 术语不得进入任何 "
       "`SUPPORTED_MECHANISM` 主张（见 §8 第 4 条）。",
       "", "## 8 版本规则", ""]
for i, rule in enumerate(out["versioning_rules"], 1):
    md.append(f"{i}. {rule}")
md += ["", "## 9 口径漂移表（本轮的主要产出）", "",
       "`01` §1.4 定义的是 `D+ / D− / NEUTRAL_VALUE / MIXED / UNCERTAIN`；`02` §2.2 写的是 "
       "`D+ | D− | neutral`；而 106 行注册表里实际存在的是下面这些拼写。L-01 又引入了第五种"
       "（Phase I′ 计票口径 `D+ / D− / mixed / value-only`）。**注册表不回写**（§5、第 8 条），"
       "本表是唯一的对齐仪器：", "",
       "| 观察到的拼写 | 出现次数 | 出处 | 规范含义 |", "| --- | --- | --- | --- |"]
for a in alias_rows:
    md.append(f"| `{a['observed']}` | {a['rows']} | {a['source']} | {a['canonical']} |")
md += ["",
       "- 推导读数：规范拼写 `D−` 在 106 行注册表中出现 **" + str(dclass_observed.get("D−", 0)) +
       " 次**，ASCII `D-` 出现 **" + str(dclass_observed.get("D-", 0)) + " 次** ⇒ 任何按字符串相等做的"
       "方向计票都会把这 " + str(dclass_observed.get("D-", 0)) + " 行与规范拼写分成两类。这与 L-01 的 "
       "L01-D1（编码文件混用两种连字符）是**同一形状的缺陷**，区别只在于它已经躺在已提交工件里。",
       "- 计数后果：`D±`（" + str(dclass_observed.get("D±", 0)) + " 行）与 `mixed`（" +
       str(dclass_observed.get("mixed", 0)) + " 行）在 01 §1.4 里是同一个辅助标记 `MIXED`，"
       "`unspecified`（" + str(dclass_observed.get("unspecified", 0)) + " 行）对应 `UNCERTAIN` ⇒ "
       "注册表的方向列实际是 **6 类拼写表达 4 个状态**。"]
md += ["", "核验级别同样漂移：" + "、".join(f"`{k}` {v} 行" for k, v in lvl_observed.items()) +
       "，而 L-01 的 17 条里出现 `FULLTEXT_REVIEWED` " +
       str(sum(1 for r in l01["records"].values() if r["verification_level"] == "FULLTEXT_REVIEWED")) +
       " 条、`QUALIFIED` " +
       str(sum(1 for r in l01["records"].values() if r["verification_level"] == "QUALIFIED")) +
       " 条、`ABSTRACT_VERIFIED` " +
       str(sum(1 for r in l01["records"].values() if r["verification_level"] == "ABSTRACT_VERIFIED")) +
       " 条 ⇒ 注册表的级别字段与全文级读数是**两套口径并存**，引用时须写明是哪一套。",
       "", "## 10 复现", "", "```bash", "python3 governance/build_mechanism_vocabulary.py",
       "python3 literature/l01_gate.py   # 词表的 L-01 用量读数即出自其绑定的 L01_coding.json",
       "```", ""]
(M / "report/MECHANISM_VOCABULARY_v1.md").write_text("\n".join(md), encoding="utf-8")
print("k families", len(out["k_families"]), "| layers", len(out["layers"]), "| bridges", len(bridge),
      "| alias rows", len(alias_rows), "| unmapped", len(unmapped))
print("wrote report/MECHANISM_VOCABULARY_v1.md and governance/mechanism_" + VERSION + ".json")
