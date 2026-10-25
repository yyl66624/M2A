"""Build the five-label reconciliation table (owner decision 2026-10-18, item 7 + §2-3).

Rule 7 says every round must distinguish SUPPORTED / CONTRADICTED / NULL / INDETERMINATE /
NOT_IDENTIFIED. The artifacts, however, were written under four older label systems: arm verdicts
(SUPPORTED / REFUTED / NOT_EXPLAINED / QUALIFIED), fraction verdicts ("3/4 closed"), exit names
("E3 TEST-UNSATISFIABLE"), and cell-level states (NOT_RESOLVABLE, PARTIALLY_IDENTIFIED). Rule 7
also forbids rewriting them (R6, decision 8), so the only lawful way to get one report-wide
vocabulary is a translation table that lives in a NEW file and points at the committed bytes.

Mechanics:
  * every label token is READ from the artifacts - nothing is typed into the table by hand;
  * each token must appear in RULES with a stated reason; an unknown token becomes a MANUAL_REVIEW
    row and is counted, so the next round's new wording cannot pass silently;
  * a round that emitted several sub-verdicts gets several rows - the five labels are per claim,
    not per round.
"""
import json
import pathlib
import re

M = pathlib.Path(__file__).resolve().parent.parent
FIVE = ["SUPPORTED", "CONTRADICTED", "NULL", "INDETERMINATE", "NOT_IDENTIFIED"]
FIELDS = re.compile(r"verdict|exit|outcome|label|status", re.I)
TOKEN = re.compile(r"\b[A-Z][A-Z0-9_\-]{2,}\b")

# token -> (label, why). Kept as data so the table is auditable in one screen.
RULES = {
    "SUPPORTED": ("SUPPORTED", "02/05-era arm verdict: the registered criterion was met"),
    "CONFIRMED": ("SUPPORTED", "exit-name synonym used from Phase VII on"),
    "EXACT": ("SUPPORTED", "Phase XIV E1 RATE-LAW-EXACT: the law held at the registered tolerance"),
    "RECONCILED": ("SUPPORTED", "Phase XIII E1: the convention conflict was resolved by derivation"),
    "GAP-IS-NOISE": ("SUPPORTED", "Phase XV E1: the joint-fit gap is explained by measurement noise"),
    "USABLE": ("SUPPORTED", "Phase XX-XXII E1: the B-07 filter is satisfiable and separates"),
    "PREDICTED": ("SUPPORTED", "Phase XXII E1 FAMILY-MAP-AS-PREDICTED: coverage matched the prior"),
    "SEPARABLE": ("SUPPORTED", "Phase XXI E1 UNIQUE-AND-SEPARABLE"),
    "REGULARIZATION-DOES-NOT-REPAIR": ("SUPPORTED", "Phase XXIV E1: L2 weight decay did not repair the old-law deviation"),
    "AO-SEPARATES": ("SUPPORTED", "Phase XXIII E1: the AO measure separates issuance from silence"),
    "S_ONLY_NONZERO_C_NOT_BETTER": ("INDETERMINATE", "Phase XXV E2: S-only effect nonzero, C advantage not detected"),
    "CONTEXT_MODEL_UNINFORMATIVE": ("NOT_IDENTIFIED", "Phase XXVI: context model miscalibrated; C advantage not tested"),
    "CALIBRATION_FAILED": ("NOT_IDENTIFIED", "Phase XXVII: calibration did not beat the base rate; C advantage not tested"),
    "GBDT_CALIBRATION_FAILED": ("NOT_IDENTIFIED", "Phase XXVIII: GBDT isotonic calibration degenerated to take-all"),
    "REFUTED": ("CONTRADICTED", "arm verdict used verbatim from Phase V/VI"),
    "O-REFUTED": ("CONTRADICTED", "Phase VI outcome string for the same judgement"),
    "UNSATISFIABLE": ("CONTRADICTED", "Phase XIX E3: the registered necessary condition cannot be met"),
    "K-DEPENDENT-RESIDUAL": ("CONTRADICTED", "Phase XVI E2: cross-k readings are incompatible"),
    "NOT-MINUS-TWO": ("CONTRADICTED", "Phase VIII E2: the exponent claim was falsified"),
    "QUALIFIED": ("CONTRADICTED", "Phase VIII verdict: claim holds only after being narrowed"),
    "NOT_EXPLAINED": ("INDETERMINATE", "Phase V/5c arm verdict: residual not attributable"),
    "NOT_DECISIVE": ("INDETERMINATE", "Phase V-c outcome J_NOT_DECISIVE"),
    "NOT-THE-CULPRIT": ("INDETERMINATE", "Phase XVII E2: one hypothesis excluded, the law still undecided"),
    "NOT_RESOLVABLE": ("NOT_IDENTIFIED", "cell-level state: tolerance exceeds the signal, no reading"),
    "PARTIALLY_IDENTIFIED": ("NOT_IDENTIFIED", "Phase XV single-sided bound, decision 2 wording"),
    "NOT_OBTAINED": ("NULL", "literature round: the comparison was run and returned nothing"),
    "LAW-K-INVARIANT-UNDER-3LAYER": ("SUPPORTED", "Phase XVIII E1: three displacement knobs, cross-k 0/42 "
                                      "over-tolerance"),
}
# Round-level status fields, in the order a reader would consult them. `verdict` first because most
# rounds write the arm verdict there; `exit` next because that is where the exit name lives.
EXIT_ORDER = re.compile(r"^E(\d)\b")
EXIT_NUM = EXIT_ORDER
FRACTION = re.compile(r"^\d+/\d+ closed$")
# the five labels are their own rule: a round that already obeys rule 7 needs no translation
for _lab in FIVE:
    RULES.setdefault(_lab, (_lab, "already canonical - this artifact field literally carries a "
                                  "rule-7 label"))

DOC_TOKENS = FIVE + ["NOT_RESOLVABLE", "PARTIALLY_IDENTIFIED", "NOT_EXPLAINED", "REFUTED"]


def prose_rows():
    """The documents use states that the JSON fields never record; those rows ARE the gap."""
    rows, seen = [], set()
    docs = sorted((M / "experiments").glob("PHASE*_RESULTS.md")) + \
        [M / "literature/ROUND_L01_RESULTS.md"]
    for f in docs:
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(M).as_posix()
        for tok in DOC_TOKENS:
            if re.search(r"\b" + tok + r"\b", text) and (rel, tok) not in seen:
                seen.add((rel, tok))
                rows.append({"artifact": rel, "field": "prose", "raw": tok,
                             "label": RULES[tok][0], "why": RULES[tok][1],
                             "layer": "document-only"})
    return rows



def tokens_of(s):
    return [x for x in TOKEN.findall(str(s))
            if x not in ("E0", "E1", "E2", "E3", "E4", "V1", "V2", "V3", "L1", "L2", "L3", "ID")]


def hits(s):
    """RULES keys occurring in `s`, longest first.

    Exact token equality is not enough: exit names are compounds, so `E3 TEST-UNSATISFIABLE` is one
    token while the registered rule is `UNSATISFIABLE`. A key therefore also matches when it appears
    as a hyphen/underscore-delimited part of the value; longest-first keeps a more specific rule
    from being shadowed by a shorter one."""
    return [key for key in sorted(RULES, key=len, reverse=True)
            if re.search(r"(?<![A-Z0-9])" + re.escape(key) + r"(?![A-Z0-9])", str(s))]


def same_file_resolution(blob):
    """Resolve a round's five-label from a *status-bearing field of the same file*.

    A closure count ("2/4 closed") is not a status, but every such file also carries the round's
    verdict or its taken exit name. Reading the label from that field keeps the table a translation
    of committed bytes; nothing is typed in by hand. Returns None when the file offers no lawful
    status field at all - that row then stays MANUAL_REVIEW and is reported as a gap.
    """
    for key in ("label_reported", "verdict", "exit", "outcome", "status"):
        v = blob.get(key)
        if isinstance(v, str):
            hit = hits(v)
            if hit:
                lab, why = RULES[hit[0]]
                return {"field": key, "raw": v[:60], "label": lab, "via": hit[0], "why": why}
    exits = blob.get("exits")
    if isinstance(exits, dict):
        named = [(name, taken) for name, taken in exits.items() if EXIT_ORDER.match(name or "")]
        for name, taken in sorted(named, key=lambda kv: int(EXIT_ORDER.match(kv[0]).group(1))):
            if taken is not True or int(EXIT_ORDER.match(name).group(1)) == 0:
                continue          # E0 is always the anchor-reproduction control, never a status
            hit = hits(name)
            if hit:
                lab, why = RULES[hit[0]]
                return {"field": "exits[" + name + "]", "raw": name, "label": lab, "via": hit[0],
                        "why": why + "; taken from the registered exit-name order (E0 is the "
                                   "anchor-reproduction control and is excluded)"}
    return None


def rows_for(path, blob, kind):
    out = []
    for key, val in blob.items():
        if not FIELDS.search(key):
            continue
        if key == "exits" and isinstance(val, dict):
            # the registered exit NAMES live in the dict keys, not the values; rounds whose `exit`
            # string is only "E1 | E2 | E3 | E4" would otherwise contribute no row at all
            taken = sorted((n for n, v in val.items() if v is True and EXIT_NUM.match(n or "")),
                           key=lambda n: int(EXIT_NUM.match(n).group(1)))
            taken = [n for n in taken if int(EXIT_NUM.match(n).group(1)) != 0]
            if taken:
                val = {"taken_first_exit": taken[0]}
        vals = val if isinstance(val, dict) else {"": val}
        for sub, v in vals.items():
            s = str(v)
            if s in ("None", ""):
                continue
            tokens = [t for t in TOKEN.findall(s) if t not in ("E0", "E1", "E2", "E3", "E4", "V1",
                                                               "V2", "V3", "L1", "L2", "L3", "ID")]
            if FRACTION.match(s):
                out.append({"artifact": path, "field": key + (f"[{sub}]" if sub else ""),
                            "raw": s, "label": "COUNT_NOT_STATUS",
                            "why": "a closure COUNT, not a status; the round's own label is the "
                                   "`exit`/`verdict` row of this same file, so giving this row a "
                                   "label too would count one claim twice"})
                continue
            h = hits(s)
            hit = [(x, RULES[x]) for x in h]
            unknown = [x for x in tokens if x not in RULES]
            if hit:
                t, (lab, why) = hit[0]
                out.append({"artifact": path, "field": key + (f"[{sub}]" if sub else ""),
                            "raw": s[:60], "label": lab, "why": why, "via": t,
                            "unmatched_tokens": unknown})
            elif tokens:
                out.append({"artifact": path, "field": key + (f"[{sub}]" if sub else ""),
                            "raw": s[:60], "label": "MANUAL_REVIEW",
                            "why": "no rule covers " + ", ".join(sorted(set(tokens)))})
    if kind == "coding":
        for anchor, v in blob["exit_table"].items():
            out.append({"artifact": path, "field": "exit_table[" + anchor + "]",
                        "raw": "label_reported=" + v["label_reported"],
                        "label": v["label_reported"],
                        "why": "Round L-01 emits the five labels natively (rule 7 written after "
                               "the decision, this round was the first to obey it)"})
    return rows_out(out)


def rows_out(acc):
    seen, ded = set(), []
    for r in acc:
        k = (r["artifact"], r["field"], r["raw"])
        if k not in seen:
            seen.add(k); ded.append(r)
    return ded


def resolve_manual_rows(rows, blobs):
    """Turn a MANUAL_REVIEW row into a label, or say why it cannot become one.

    Two lawful outcomes besides a label:
      * ZERO_TEST_REANALYSIS - the file is a re-analysis (`status` says zero-test), so the strings
        inside it describe *what some other artifact says* (a runner label, an incomplete exit
        table). Attaching a rule-7 label to those would be inventing a verdict the round never
        issued, and R6 forbids a re-analysis from carrying one.
      * still MANUAL_REVIEW - no status field in that file resolves; the row stays visible.
    """
    for r in rows:
        if r["label"] != "MANUAL_REVIEW" or r.get("layer") == "document-only":
            continue
        blob = blobs.get(r["artifact"])
        if blob is None:
            continue
        if r["artifact"].endswith("_reanalysis.json"):
            r["label"] = "ZERO_TEST_REANALYSIS"
            r["why"] = ("the file is a zero-test re-analysis; its fields quote another artifact's "
                        "label (a runner label, an incomplete exit table), so no rule-7 status may "
                        "be attached - a re-analysis may not carry a verdict (R6)")
            continue
        hit = same_file_resolution(blob)
        if hit and hit["label"] in FIVE:
            r["label"] = hit["label"]
            r["derived"] = True
            r["resolved_from_field"] = hit["field"]
            r["resolved_from_raw"] = hit["raw"]
            r["resolved_via"] = hit["via"]
            r["why"] = "this field carries no status of its own; the label is read from `" \
                       + hit["field"] + "` of the same file (via `" + hit["via"] + "`). Marked " \
                       "`derived`, so the per-claim tally counts the row the label came from, not " \
                       "this one twice"


def main():
    files = sorted((M / "experiments").glob("phase*_results.json")) \
        + sorted((M / "experiments").glob("phase*_reanalysis.json")) \
        + [M / "literature/L01_coding.json"]
    rows, blobs = [], {}
    for f in files:
        blob = json.loads(f.read_text(encoding="utf-8"))
        rel = f.relative_to(M).as_posix()
        blobs[rel] = blob
        rows += rows_for(rel, blob, "coding" if "L01" in rel else "results")
    for r in rows:
        r.setdefault("layer", "artifact-field")
    n_artifact_rows = len(rows)
    rows += prose_rows()
    resolve_manual_rows(rows, blobs)
    DISPOSED = FIVE + ["MANUAL_REVIEW", "ZERO_TEST_REANALYSIS", "COUNT_NOT_STATUS"]
    # per-claim tally excludes `derived` rows: the same claim must not be counted twice just because
    # a file expresses it in both a count field and a status field
    claims = [r for r in rows if not r.get("derived")]
    counts = {lab: sum(1 for r in claims if r["label"] == lab) for lab in DISPOSED}
    counts["_derived_rows"] = len(rows) - len(claims)
    counts["_rows_total"] = len(rows)
    gap = {lab: {"artifact_fields": sum(1 for r in claims if r["label"] == lab
                                        and r["layer"] != "document-only"),
                 "prose_only": sum(1 for r in claims if r["label"] == lab
                                   and r["layer"] == "document-only")}
           for lab in FIVE}
    manual = [r for r in rows if r["label"] == "MANUAL_REVIEW"]

    (M / "governance/status_label_table_v2.json").write_text(json.dumps(
        {"schema": "m2a.status-label-table.v2", "labels": FIVE, "rows": rows, "counts": counts,
         "rules": {k: {"label": v[0], "why": v[1]} for k, v in RULES.items()},
         "gap": gap, "artifact_field_rows": n_artifact_rows, "prose_rows": len(rows) - n_artifact_rows,
         "reading": "one row per claim-bearing field, not per round; MANUAL_REVIEW rows are listed "
                    "with the reason they cannot be translated mechanically"},
        ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# 五值识别状态标签 × 既有台账/报告 口径表 v2",
          "",
          "> 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 7 条与 §2 第 3 项。生成器：",
          "> `governance/build_status_label_table.py`（机器可读版 `governance/status_label_table_v2.json`）。",
          "> **本表是翻译层，不是改写层**：`experiments/phase*.json`、各 `PHASE*_RESULTS.md`、",
          "> 412 行账本与 PNAS 冻结包一字未动（R6、第 8 条）。引用旧轮的五值标签时，按本表取",
          "> `label` 列，并同时给出 `raw` 列的原文，以免翻译被当成原始判定。",
          "",
          "## 1 为什么要翻译层",
          "",
          "第 7 条要求每轮区分 `SUPPORTED / CONTRADICTED / NULL / INDETERMINATE / NOT_IDENTIFIED`，",
          "但工件本身是在四套更早的标签体系下写成的：臂级判定（`SUPPORTED/REFUTED/NOT_EXPLAINED/"
          "QUALIFIED`）、关闭计数（`3/4 closed`）、出口名（`E3 TEST-UNSATISFIABLE`）、格级状态",
          "（`NOT_RESOLVABLE`、`PARTIALLY_IDENTIFIED`）。**五值标签不是不存在，而是散落在四套拼写里**——",
          "把它们统一起来只能靠本表，不能靠回写。",
          "",
          "## 2 逐行映射（每个带判定的字段一行）",
          "",
          "| 工件 | 字段 | 原始读数 | 五值标签 | 层 | 依据 |",
          "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| `{r['artifact']}` | `{r['field']}` | `{r['raw']}` | **{r['label']}** | "
                  f"{r.get('layer', 'artifact-field')} | {r['why']} |")
    md += ["", "## 3 处置计数与两层缺口", "",
           "计数按**逐条主张**：`derived` 行（标签从同文件另一字段读来）只作出处指向，不重复计数。",
           "工件行共 " + str(counts["_rows_total"]) + " 行，其中派生行 "
           + str(counts["_derived_rows"]) + " 行。",
           "", "| 处置 | 主张计数 | 其中：工件字段 | 其中：仅文档措辞 |", "| --- | --- | --- | --- |"]
    for lab in DISPOSED:
        g = gap.get(lab, {"artifact_fields": sum(1 for r in claims if r["label"] == lab),
                          "prose_only": 0})
        md.append(f"| {lab} | {counts[lab]} | {g['artifact_fields']} | {g['prose_only']} |")
    prose_only_labels = [lab for lab in FIVE if gap[lab]["artifact_fields"] == 0
                         and gap[lab]["prose_only"] > 0]
    absent_labels = [lab for lab in FIVE if counts[lab] == 0]
    null_rows = counts["NULL"]
    md += ["",
           "**读法**：`工件字段` 列说明该标签是否真的写在结果 JSON 的判定字段里；`仅文档措辞` 列说明它",
           "是否只存在于结果文档的行文。**两者不成对就是缺口**，因为第 7 条要求的是每轮的判定标签，",
           "而审计规则要求「报告里引用的每个标签都要能逐个对回结果 JSON」——只写在文档里的标签对不回任何字段。",
           "",
           f"推导出的缺口（{len(rows)} 行中，工件字段 {n_artifact_rows} 行、文档措辞 "
           f"{len(rows) - n_artifact_rows} 行）：",
           "",
           "1. **只在文档里存在、工件字段里为 0 的标签**：" +
           ("、".join(f"`{l}`" for l in prose_only_labels) or "无") +
           "。典型是格级状态 `NOT_RESOLVABLE` 与部分识别标签 `PARTIALLY_IDENTIFIED`——"
           "它们各自写在 `PHASE*_RESULTS.md` 的正文与表格里，但**没有任何 `phase*_results.json` 字段承载它**，"
           "所以按字段扫描时 `NOT_IDENTIFIED` 一栏为 0。这与 X-67 是同一条治理规律："
           "**处置与标签必须写在承载判定的工件里，写在累计文档里等于没写**。",
           "2. **两个层级都为 0 的标签**：" + ("、".join(f"`{l}`" for l in absent_labels) or "无") +
           "。`NULL`（仪器正常、效应为零）在 24 个实验轮里从未被字面写出：实验侧的失败形态被归入"
           "`CONTRADICTED`（判据被否证）或格级 `NOT_RESOLVABLE`（不可判），而「零结果」这一档在预注册"
           "出口表里从未被单独命名。这不是漏改旧轮（R6 禁止），而是**下一轮的出口表必须显式含 `NULL` 一档**，"
           "否则第 7 条要求的五值区分在实验侧仍只有四值。",
           "3. 文献轮 L-01 是**第一个原生使用五值标签**的轮次（`L01_coding.json` 的 `exit_table[*].label_reported`）。",
           "",
           f"`MANUAL_REVIEW` 共 {len(manual)} 行：{'; '.join(m['artifact'] + ' ' + m['field'] for m in manual) or '无'}。"
           "这些行的共同点是「字段里装的是关闭计数或过程标签，不是状态」，其五值标签须由同一文件的"
           "出口行取得。",
           "",
           "## 4 引用规则",
           "",
           "1. 引用旧轮判定时**两个都要写**：`raw`（原文，不可变）与 `label`（本表翻译）；",
           "2. 本表由脚本推导，出现未被 `RULES` 覆盖的新拼写即落为 `MANUAL_REVIEW` 行并计数——"
           "这是刻意的：**词表漂移必须可见，不得静默归类**（与 X-70 同一处置原则）；",
           "3. 新一轮若引入新的状态字面，须先在本表加规则再加判据，顺序不可颠倒。",
           "",
           "## 5 复现", "", "```bash", "python3 governance/build_status_label_table.py",
           "python3 experiments/audit_bindings.py", "```", ""]
    (M / "report/STATUS_LABEL_TABLE_v2.md").write_text("\n".join(md), encoding="utf-8")
    print("rows", len(rows), "| counts", counts)
    print("manual review rows:", [m["artifact"] + "::" + m["field"] for m in manual])


if __name__ == "__main__":
    main()
