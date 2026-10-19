"""Rebuild m2a/governance/OBLIGATION_REGISTRY.md from the committed artifacts.

Two mechanisms, deliberately independent:

* **derivation** — every `P<n>-O<m>` mention is collected and classified by the wording of the
  *sentence* it sits in. Line-level matching is wrong: the cumulative documents pack "X is closed.
  Y is still open" into one table row, so the first clause's verdict leaks onto the second label.
* **pin** — `EXPECT` records the disposition asserted for this round, anchored to the *text* of the
  sentence that justifies it (a distinctive snippet plus the file). The line number is resolved at
  build time, so inserting a paragraph in the middle of an append-only report cannot rot the
  citations — that failure mode appeared the first time this file was edited after the pins were
  written as fixed line numbers.

The build aborts if derivation and pin disagree, if a pinned sentence can no longer be found (or
matches twice), if a hand-over points at a successor that is not itself closed, or if a label
appears anywhere in the artifacts with no disposition.
"""
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent
SELF = "OBLIGATION_REGISTRY.md"

# --- wording classes -----------------------------------------------------------
CLOSE = re.compile(r"(?<![未非])(?:已)?关闭|已完成|落实|已交付|答复|已在 Phase|升格为定理|统一为定理")
ADOPT = re.compile(r"执行|覆盖|教训|模板条款|已按|采纳|写入纪律|落地为")
HAND = re.compile(r"→|->|前身|后继|承接")
BLOCK = re.compile(r"未授权|未做|未启动|仍需|仍开放|尚开放|模型类决策|待框架|待决定|待 owner|留给 owner"
                   r"|需新一轮|需新预注册|先重定义|须换|需要第|才能升为|未关闭|未通过|未回答")
SENT = re.compile(r"[。；;！!？?]")

# (status, wording class, file, snippet identifying the sentence, successor label or None)
# SUCCEEDED = handed to a successor label (itself closed) rather than closed in place.
EXPECT = {
    "P5-O1": ("CLOSED", "close", "experiments/PHASE5_RESULTS.md", "V3-C4 的重测", None),
    "P5-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "至此关闭", None),
    "P5-O3": ("OPEN", "block", "experiments/PHASE5_RESULTS.md", "三个以上**独立系统**的跨域复验", None),
    "P6-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "计数系统的平滑门槛", None),
    "P6-O2": ("CLOSED", "adopt", "experiments/PHASE7_PREREGISTRATION.md", "混合聚合的第三结构", None),
    "P6-O3": ("CLOSED", "adopt", "experiments/PHASE7_PREREGISTRATION.md", "指出的漏洞", None),
    "P7-O1": ("CLOSED", "close", "experiments/PHASE9_RESULTS.md", "门槛律对级内聚合", None),
    "P7-O2": ("CLOSED", "close", "experiments/PHASE9_RESULTS.md", "不改变常数", None),
    "P7-O3": ("CLOSED", "adopt", "experiments/PHASE8_PREREGISTRATION.md", "修正后的四档形式", None),
    "P8-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P8-O1 与 P8-O2 关闭", None),
    "P8-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P8-O1 与 P8-O2 关闭", None),
    "P8-O3": ("CLOSED", "close", "M2A_PROGRAM_PLAN.md", "P8-O3 落实", None),
    "P9-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P9-O1 与 P9-O2 关闭", None),
    "P9-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P9-O1 与 P9-O2 关闭", None),
    "P9-O3": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "统一为定理", None),
    "P10-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P10-O1 与 P10-O2 关闭", None),
    "P10-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "P10-O1 与 P10-O2 关闭", None),
    "P10-O3": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "已落实为规则", None),
    "P11-O1": ("OPEN", "block", "M2A_FINAL_REPORT.md", "测度口径（须先重定义判据", None),
    # Phase XIII failed E2/E4 on purpose (a tolerance not derived in advance), so these two were
    # handed to P13-O1 / P13-O2 rather than closed; the successors closed in XIV and XV.
    "P11-O2": ("SUCCEEDED", "hand", "M2A_FINAL_REPORT.md", "（→ P13-O1）、P12-O1", "P13-O1"),
    "P11-O3": ("CLOSED", "close", "experiments/PHASE13_RESULTS.md", "E3 关闭", None),
    "P12-O1": ("SUCCEEDED", "hand", "experiments/PHASE15_RESULTS.md", "P13-O2 前身", "P13-O2"),
    "P12-O2": ("CLOSED", "close", "experiments/PHASE13_RESULTS.md", "E1 关闭", None),
    "P12-O3": ("OPEN", "block", "M2A_FINAL_REPORT.md", "测度口径（须先重定义判据", None),
    "P13-O1": ("CLOSED", "close", "experiments/PHASE14_RESULTS.md", "这关闭了什么", None),
    "P13-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "多少信息", None),
    "P14-O1": ("CLOSED", "close", "experiments/PHASE18_RESULTS.md", "注册的关闭条件正是 E1", None),
    "P15-O1": ("OPEN", "block", "M2A_FINAL_REPORT.md", "要双侧估计须换目标函数或换数据族", None),
    "P16-O1": ("CLOSED", "adopt", "M2A_FINAL_REPORT.md", "落地为一次两层同时加密的复验", None),
    "P17-O1": ("CLOSED", "close", "experiments/PHASE18_PREREGISTRATION.md", "重判跨", None),
    "P19-O1": ("CLOSED", "close", "experiments/PHASE20_RESULTS.md", "重述后的检验可分且可满足", None),
    "P20-O1": ("CLOSED", "close", "experiments/PHASE21_RESULTS.md", "扩族后检验仍可分且唯一性可判", None),
    "P21-O1": ("CLOSED", "close", "experiments/PHASE22_RESULTS.md", "逐族报告三列并判定", None),
    "P22-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md", "已以推导关闭", None),
    # --- literature round L-01: all five are preconditions for round L-02, none disposed here
    # (ROUND_L01_RESULTS.md §9 is the status-bearing artifact for this namespace)
    "L01-O1": ("OPEN", "block", "literature/ROUND_L01_RESULTS.md", "分歧登记为开放项", None),
    "L01-O2": ("OPEN", "block", "literature/ROUND_L01_RESULTS.md", "族 + 符号 + 主张层关系", None),
    "L01-O3": ("OPEN", "block", "literature/ROUND_L01_RESULTS.md", "轴的零值处理", None),
    "L01-O4": ("OPEN", "block", "literature/ROUND_L01_RESULTS.md", "竞争理论全文编码须另开一轮", None),
    "L01-O5": ("OPEN", "block", "literature/ROUND_L01_RESULTS.md", "全文仍不可得", None),
    # --- core open-questions list (08): the status words there are kept as written; owner
    # 2026-10-18 froze them (`O-01…O-15` 的状态字保持原样), so nothing here is closed in place
    "O-01": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "K4 协同族单薄", None),
    "O-02": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "K10 角色重排族单薄", None),
    "O-03": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "K9 在物理化学层零覆盖", None),
    "O-04": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "非英语学术传统未覆盖", None),
    "O-05": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "仅为概念基线", None),
    "O-06": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "填充规则待裁定", None),
    "O-07": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "待框架 v0.3 裁定", None),
    "O-08": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "需要更细的分描述判定流程", None),
    "O-09": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "粒度不足以区分", None),
    "O-10": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "结构化检索缺失", None),
    "O-11": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "全文编码缺失", None),
    "O-12": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "量化合成未做", None),
    "O-13": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "需明确升级预算", None),
    "O-14": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "需指定复核人", None),
    "O-15": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "需决定治理责任人", None),
    "O-16": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "判据引用的闭式在门控层没有实现级对照", None),
    "O-17": ("OPEN", "block", "08_OPEN_QUESTIONS.md", "每条数值检查都必须有可证伪输入", None),
}
CLASS = {"close": CLOSE, "adopt": ADOPT, "hand": HAND, "block": BLOCK}

# --- namespaces ---------------------------------------------------------------
# Three label namespaces live in the artifacts. Until 2026-10-19 only one of them was in scope
# here, so `L01-O*` and `O-01…O-15` could be absent from the ledger without the build noticing —
# registered as ROUND_L01_RESULTS.md §9.6, same root cause as X-67.
# Each namespace gets (a) its own wording classes, because the literature side writes dispositions
# as 「待裁定 / 建议 / 需指定」rather than 「关闭 / 落实」, and (b) its own status-bearing artifact,
# because X-67/X-71 established that a disposition must live in the artifact that carries the
# judgement. For these two namespaces that artifact is the open-questions list and the round's own
# results document, not the cumulative report.
def ns_of(key):
    return "P" if key.startswith("P") else ("L01" if key.startswith("L01") else "O")


NAMESPACES = {
    "P": re.compile(r"P\d{1,2}-O\d"),
    "L01": re.compile(r"L01-O\d"),
    "O": re.compile(r"O-\d{2}"),
}
CLOSE_LIT = re.compile(r"已关闭|已裁定|已完成|已落实|已入册|已升级")
ADOPT_LIT = re.compile(r"已执行|已采纳|已覆盖|写入纪律")
BLOCK_LIT = re.compile(r"未|无|不|须|需|待|建议|缺口|空白|单薄|缺失|不足以|仅为|零覆盖|仍|不可比"
                       r"|保持原样|需指定|待裁定")
CLOSE_L01 = re.compile(r"已关闭|已完成|已裁定|已落实")
ADOPT_L01 = re.compile(r"已执行|已交付|已覆盖")
BLOCK_L01 = re.compile(r"需|须|不|先注册|待修|另开|仍|开放项")
CLASS_NS = {
    "P": {"close": CLOSE, "adopt": ADOPT, "hand": HAND, "block": BLOCK},
    "L01": {"close": CLOSE_L01, "adopt": ADOPT_L01, "hand": HAND, "block": BLOCK_L01},
    "O": {"close": CLOSE_LIT, "adopt": ADOPT_LIT, "hand": HAND, "block": BLOCK_LIT},
}
# None = every document may decide status (the experiment namespace, unchanged). A path = only that
# document decides, everything else counts as a mention and as evidence but cannot flip a status.
STATUS_FILE = {"P": None, "L01": "literature/ROUND_L01_RESULTS.md", "O": "08_OPEN_QUESTIONS.md"}

LABEL = NAMESPACES["P"]
BOUNDARY = re.compile(r"[，,。；;！!？?]")
ARROW = re.compile(r"→|->")
JOIN = re.compile(r"[\s`/／与和及\-—–()（）*·]*")
# The negative/null log records the defect *as known at that round*, and its rows are ordered by
# incident number rather than by when a disposition was reached; letting it decide status would
# rank a Phase VI incident above a Phase XVIII closure. It still counts as a mention and evidence.
STATUS_SKIP = {"governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md"}


def label_sort(s):
    """Namespace first, then round/number. The experiment namespace keeps exactly its previous
    order; the two literature namespaces follow it. The key this replaced matched only `P<digits>`
    and raised on anything else, which is how an escaping namespace also became a crash."""
    n = ns_of(s)
    if n == "P":
        m = re.match(r"P(\d+)-O(\d)", s)
        return (0, int(m.group(1)), int(m.group(2)))
    if n == "L01":
        return (1, 0, int(s.split("-O")[1]))
    return (2, 0, int(s.split("-")[1]))


def order(path, ln):
    """Sort key: phase rounds by round number, cumulative documents last, then path, then line."""
    m = re.search(r"PHASE(\d{1,3})", path)
    return (int(m.group(1)) if m else 999, path, ln)


def attaches(sent, key, pat, window=None):
    """True if `pat` matches within `window` chars of an occurrence of `key` and is syntactically
    linked to *that* label rather than to a neighbour.

    * labels joined by nothing but glue (space, backticks, `/`, 与/和/及, dashes, brackets) share a
      verdict — "`P8-O1` 与 `P8-O2` 关闭" closes both; `、` is an enumeration of items that each
      carry their own verdict, so it does not glue;
    * a *preceding* verdict must not be separated from the label by a clause boundary, and must not
      point at the label with an arrow — that is how "`P13-O1` 关闭，`P11-O2` …" and
      "`P14-O1` 仍开放（→ `P17-O1`）" would otherwise leak a verdict onto the wrong label;
    * a *following* verdict may have free text in between, as long as no un-glued label intervenes
      ("`P11-O1`/`P12-O3` 测度口径（须先重定义判据，属模型类决策）").
    * only labels of the *same namespace* count as neighbours: `O-14` sitting between `P15-O1` and a
      verdict must not break the gluing test for an experiment label.
    """
    if window is None:
        window = WIN[ns_of(key)]
    kpos = [(m.start(), m.end()) for m in re.finditer(re.escape(key), sent)]
    pat_ns = NAMESPACES[ns_of(key)]
    others = sorted((m.start(), m.end()) for m in pat_ns.finditer(sent) if m.group(0) != key)
    for w in pat.finditer(sent):
        for i, k_end in kpos:
            lo, hi = min(i, w.start()), max(i, w.start())
            if hi - lo > window:
                continue
            inside = [span for span in others if lo < span[0] < hi]
            if w.start() < i:
                if BOUNDARY.search(sent[lo:hi]) or ARROW.search(sent[w.end():i]):
                    continue
                prev, glued = i, True
                for s, e in reversed(inside):
                    if not JOIN.fullmatch(sent[e:prev]):
                        glued = False
                        break
                    prev = s
                if glued:
                    return True
            else:
                prev, glued = k_end, True
                for s, e in inside:
                    if not JOIN.fullmatch(sent[prev:s]):
                        glued = False
                        break
                    prev = e
                if glued:
                    return True
    return False


def successor(sent, key):
    """The label this sentence hands `key` over to, or None. Directional on purpose: in
    "`P14-O1` 仍开放（→ `P17-O1`）" the hand-over belongs to P14-O1 and must not make P17-O1 look
    like it was itself handed on."""
    pat_ns = NAMESPACES[ns_of(key)]
    for i in (m.start() for m in re.finditer(re.escape(key), sent)):
        labs = sorted((m.start(), m.end(), m.group(0)) for m in pat_ns.finditer(sent)
                      if m.group(0) != key)
        for a in ARROW.finditer(sent):
            if a.start() <= i or any(i < l[0] < a.start() for l in labs):
                continue
            if not JOIN.fullmatch(sent[i + len(key):a.start()]):
                continue
            nxt = [l for l in labs if l[0] > a.end()]
            if nxt and nxt[0][0] - a.end() <= 6:
                return nxt[0][2]
        for m in re.finditer(r"前身|后继|承接", sent):
            mid = [l for l in labs if i < l[0] < m.start()]
            if len(mid) == 1:
                return mid[0][2]
    return None


ALL_LABEL = re.compile(r"\b(?:P\d{1,2}-O\d|L01-O\d|O-\d{2})\b")
ITEM_START = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")
WIN = {"P": 60, "L01": 160, "O": 160}


def units(rel, lines):
    """Yield (line, unit) - the sentence-like windows a disposition is read from.

    Outside a status file: one unit per sentence per line. That is the experiment-round behaviour
    and it is deliberately unchanged.

    Inside a status file: one unit per bullet / numbered item, with its continuation lines joined.
    `08_OPEN_QUESTIONS.md` and `ROUND_L01_RESULTS.md` §9 hold exactly one obligation per item and
    break a long item across lines, so a line-local window would cut the label off from the wording
    that disposes of it (that is what made `L01-O2` and `L01-O5` unclassifiable on first run)."""
    if rel not in STATUS_FILE.values():
        for ln, line in enumerate(lines, 1):
            for sent in SENT.split(line):
                s = sent.strip()
                if s:
                    yield ln, s
        return
    cur, start = [], 0
    for ln, line in enumerate(lines, 1):
        if ITEM_START.match(line):
            if cur:
                yield start, re.sub(r"\s+", " ", " ".join(cur)).strip()
            cur, start = [line], ln
        elif line.strip() and cur and not line.startswith("#"):
            cur.append(line)
        else:
            if cur:
                yield start, re.sub(r"\s+", " ", " ".join(cur)).strip()
                cur, start = [], 0
            # headings and running prose keep the per-line windows used elsewhere, so a label that
            # appears *only* in prose is still collected - and then fails as having no disposition
            for sent in SENT.split(line):
                s = sent.strip()
                if s:
                    yield ln, s
    if cur:
        yield start, re.sub(r"\s+", " ", " ".join(cur)).strip()


def collect():
    labels = {}
    for f in sorted(list(M.rglob("*.md")) + list(M.rglob("*.json"))):
        if f.name == SELF:
            continue  # the registry must never cite itself
        rel = str(f.relative_to(M))
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        for ln, sent in units(rel, lines):
            for key in set(m.group(0) for m in ALL_LABEL.finditer(sent)):
                labels.setdefault(key, []).append((rel, ln, sent, order(rel, ln)))
    return labels


def derive(key, hits):
    n = ns_of(key)
    cls, sf = CLASS_NS[n], STATUS_FILE[n]
    pos, neg = [], []
    for h in hits:
        # a status-bearing namespace reads its disposition from one artifact; every other mention
        # is evidence and is counted, but may not flip the status
        if h[0] in STATUS_SKIP or (sf is not None and h[0] != sf):
            continue
        s = h[2]
        if cls["close"].search(s) and attaches(s, key, cls["close"]):
            pos.append((h, "close"))
        elif cls["adopt"].search(s) and attaches(s, key, cls["adopt"]):
            pos.append((h, "adopt"))
        else:
            succ = successor(s, key)
            if succ and EXPECT.get(succ, ("?",))[0] in ("CLOSED", "SUCCEEDED"):
                pos.append((h, "hand"))
        if cls["block"].search(s) and attaches(s, key, cls["block"]):
            neg.append(h)
    pos.sort(key=lambda ca: ca[0][3])
    neg.sort(key=lambda h: h[3])
    if pos and (not neg or pos[-1][0][3] >= neg[-1][3]):
        return ("SUCCEEDED" if pos[-1][1] == "hand" else "CLOSED"), pos[-1][0]
    if neg:
        return "OPEN", neg[-1]
    return "UNCLASSIFIED", sorted(hits, key=lambda h: h[3])[-1]


def resolve(key, rel, snippet):
    """Find the one sentence in `rel` that mentions both `key` and `snippet`."""
    path = M / rel
    if not path.is_file():
        return None, "file missing: " + rel
    found = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for ln, sent in units(rel, lines):
        if key in sent and snippet in sent:
            found.append((ln, sent))
    if not found:
        return None, "no sentence in " + rel + " mentions both " + key + " and " + repr(snippet)
    if len(found) > 1:
        return None, ("snippet " + repr(snippet) + " for " + key + " matches " + rel + " at lines "
                      + str([f[0] for f in found]) + ", expected exactly one")
    return found[0], None


def check_pins():
    errors, resolved = [], {}
    for key, (status, cls, rel, snippet, succ) in sorted(EXPECT.items()):
        hit, bad = resolve(key, rel, snippet)
        if bad:
            errors.append(key + ": " + bad)
            continue
        ln, sent = hit
        if cls == "hand":
            got = successor(sent, key)
            if got != succ:
                errors.append(key + ": sentence " + rel + ":" + str(ln) + " hands over to "
                              + str(got) + ", pin says " + str(succ))
                continue
        elif not attaches(sent, key, CLASS_NS[ns_of(key)][cls]):
            errors.append(key + ": sentence " + rel + ":" + str(ln) + " has " + cls
                          + " wording but not attached to this label")
            continue
        if status == "SUCCEEDED" and EXPECT.get(succ, ("?",))[0] not in ("CLOSED", "SUCCEEDED"):
            errors.append(key + ": successor " + str(succ) + " is not itself closed")
            continue
        resolved[key] = (status, cls, rel + ":" + str(ln), succ)
    return errors, resolved


def main():
    errors, resolved = check_pins()
    if errors:
        print("\n".join("PIN BROKEN  " + e for e in errors), file=sys.stderr)
        raise SystemExit(2)
    labels = collect()
    unknown = sorted(set(labels) - set(EXPECT))
    untracked = sorted(set(EXPECT) - set(labels))
    if unknown or untracked:
        print("LABEL SET CHANGED\n  in artifacts, no disposition: " + (", ".join(unknown) or "none")
              + "\n  pinned, absent from artifacts: " + (", ".join(untracked) or "none"),
              file=sys.stderr)
        raise SystemExit(2)

    rows, mismatches = [], []
    for key in sorted(labels, key=label_sort):
        status, cls, cite, succ = resolved[key]
        dv, ev = derive(key, labels[key])
        if dv != status:
            mismatches.append((key, status, dv, ev[0] + ":" + str(ev[1]),
                               re.sub(r"\s+", " ", ev[2])[:110]))
        rows.append((key, status, len(labels[key]), cite, cls, succ))

    names = {"close": "关闭类措辞", "adopt": "执行/沿用类措辞", "hand": "转手类措辞",
             "block": "开放类措辞"}
    out = ["# M2A 义务台账（由各轮已提交工件推导，每条带出处）", "",
           "> 生成：`python3 m2a/governance/build_obligation_registry.py`。本文件由脚本产出，勿手改。",
           "> **为什么不是整行匹配**：累计文档会把「X 已关闭；Y 仍开放」写进同一行（同一个表格单元），"
           "按整行判定会把前一句的结论漏给后一个标签——本脚本先切句，再按邻近与连接词判定措辞归属。",
           "> **负面日志不参与判定**：`governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` 记的是当时已知的缺陷，"
           "行序按事件号而非处置时间，若让它参与排序，一条 Phase VI 的事故会压过 Phase XVIII 的关闭。"
           "该文件仍计入提及与证据，只是不决定状态。",
           "> **双机制**：状态先由句子措辞推导（CLOSED / SUCCEEDED / OPEN），再与脚本内固定断言 `EXPECT` 逐条比对；"
           "不一致、断言句找不到或匹配多处、转手指向未关闭的后继、或出现无处置的新标签 ⇒ 构建失败并打印原因。"
           "台账因此不能悄悄漂移。",
           "> **出处是内容锚定而非写死行号**：断言记的是「文件 + 该句的特征片段」，行号在构建时解析。"
           "本仓库文档只追加不删改，中途插入一段就会让所有后续行号失效——这个失效模式在本脚本第一次改完正文后真实出现过。",
           "> **三个命名空间、三套措辞、三份承载工件**：`P<n>-O<m>`（实验轮）、`L01-O<m>`（文献轮 L-01）、"
           "`O-<nn>`（08 开放问题清单）。后两个命名空间此前**不在扫描范围内**，一条开放项可以从台账上消失而构建"
           "毫无察觉（`ROUND_L01_RESULTS.md` §9.6 登记，与 X-67 同源）。每个命名空间的措辞类别不同（文献侧写"
           "「待裁定 / 建议 / 需指定」而非「关闭 / 落实」），且**状态只由其承载判定措辞的那份工件决定**："
           "`L01-O<m>` 只看 `literature/ROUND_L01_RESULTS.md`，`O-<nn>` 只看 `08_OPEN_QUESTIONS.md`"
           "（owner 2026-10-18 明示「状态字保持原样」）；其他文件的提及计入证据与漂移检测，但不得翻转状态。",
           "> **提及句数**按「提到该标签的句子数」计，同一句里重复出现只算一句（X-67 行内两次写到 "
           "`P16-O1`，此处计 1）；它衡量的是**散布度**不是出现次数，因此与旧版按出现次数计的读数会有"
           "±1 的差，状态列不受影响。",
           "> 证据为相对 `m2a/` 的 `路径:行号`，回指原文；本文件自身不参与扫描（否则会用自己当证据）。", "",
           "| 标签 | 状态 | 提及句数 | 判定出处（构建时解析） | 该句的措辞类别 | 承接标签 |",
           "| --- | --- | --- | --- | --- | --- |"]
    for key, status, n, cite, cls, succ in rows:
        out.append("| " + key + " | **" + status + "** | " + str(n) + " | `" + cite + "` | "
                   + names[cls] + " | " + (succ or "—") + " |")

    closed = [r[0] for r in rows if r[1] == "CLOSED"]
    succ_rows = [r[0] for r in rows if r[1] == "SUCCEEDED"]
    openi = [r[0] for r in rows if r[1] == "OPEN"]
    unk = [r[0] for r in rows if r[1] == "UNCLASSIFIED"]
    reasons = {
        "P5-O3": "三个以上独立系统的跨域复验——真实数据未授权；owner 2026-10-18 第 3 条裁定「继续停留在设计阶段」。",
        "P11-O1": "测度口径：静默事件与发放事件互为补集 ⇒ 双侧窗口塌缩。**已裁定**采用 Action Opportunity "
                  "统一分析单位（owner 第 1 条），协议设计稿见 `report/AO_MEASUREMENT_PROTOCOL_v1.md`；"
                  "但正式实验未被自动批准，判据也未写进预注册 ⇒ 本条仍开放。",
        "P12-O3": "发放事件一侧的测度口径，同上：协议 §2 给出 `I(o)` 候选形式，预注册与读数尚未做 ⇒ 仍开放。",
        "P15-O1": "`e₁` 只给单侧界。**已裁定**保留单侧界（owner 第 2、7 条），不得改目标函数制造双侧结论 ⇒ "
                  "本条作为「双侧估计」的诉求已放弃，但作为「双侧可识别」的证据缺口仍在册。"
                  "**注意**：owner 第 2 条要求的 `PARTIALLY_IDENTIFIED` 状态字目前只写在治理文档与累计报告里，"
                  "`experiments/PHASE15_RESULTS.md` 与 `phase15_results.json` 均为 0 次命中，"
                  "口径表 v2 的扫描已证实（X-74 / `M2A_FINAL_REPORT.md` §37.5）⇒ 「按 `PARTIALLY_IDENTIFIED` "
                  "记录」这一半**尚未落在承载判定的工件里**；旧轮文档不回写（R6、第 8 条），补法是本条的下一轮"
                  "在新结果 JSON 里直接带该字段。",
        # --- L-01：五条都是 L-02 的前置，本轮无权处置（owner 第 4 条只批到 14 篇编码 + 核验 + 竞争理论）
        "L01-O1": "注册层 R13/R14 标注与全文读数的分歧：升为全文级须由一次带**新判据**的轮次决定，"
                  "不在本轮权限内。`registry.json` 仍 0 条 FULLTEXT（第 8 条禁止回写）。",
        "L01-O2": "一致性判据只到「族 + 符号」，看不见主张层反证（L01-D3：G5-03-N6 主张拒绝**不是**单方向却计入 `C`）"
                  "⇒ 改为「族 + 符号 + 主张层关系」须**先注册后跑**，再对本轮 17 条做零检验地位重判读（不重跑、"
                  "不改原工件，R6）。",
        "L01-O3": "`neutral` 轴的零值处理与符号比较口径未在注册时定死（L01-D4）：两种读法并行计算后取更保守标签，"
                  "「保守序」本身成了未测分支 ⇒ 须与纪律规则 R14 同形地在注册时决定。",
        "L01-O4": "竞争理论《Concept Cones》已取得题录与 OA 地址（`L01_verification.json` 的 "
                  "`competing_theory_channel_L01_A1`），但**全文编码与正反证同表计票未做** ⇒ 须另开一轮并预先规定口径。",
        "L01-O5": "R13-N15 端点只返回 bioRxiv 预览页（5 370 字符，403/无全文）⇒ 按 `ANNOTATION_ADDENDUM` 增补 3 "
                  "保持 `ABSTRACT_VERIFIED`，不得以摘要冒充全文；不可得原因已记录，升级路径未定。",
        # --- 08 开放问题清单：owner 2026-10-18 明示「状态字保持原样」，故没有任何一条就地关闭
        "O-01": "K4 协同族单薄：Phase I′ 补入 7 条后仍为 3/8，缺口已被改判为**结构性**而非检索性"
                "（`M2A_FINAL_REPORT.md` §2 第 3 条）⇒ 检索建议已执行，条目诉求（取得因果级协同证据）未达。",
        "O-02": "K10 角色重排族单薄：由 2/8 升到 4/8，说明缺口**部分**是检索造成的，方向仍一半混合 ⇒ 未闭合。",
        "O-03": "K9 在物理化学层零覆盖：工作假设「省略需表征系统」仍未获得无表征系统中的反例 ⇒ 开放。",
        "O-04": "非英语学术传统未覆盖（现象学行动理论、日文行动论、中文知行哲学）：全库 106 条均为英文载体 ⇒ 开放。",
        "O-05": "法学实证未覆盖：G7-07（Hart）仅为概念基线，合规行为研究缺位 ⇒ 开放。",
        "O-06": "设计已交付（`report/O06_MOTION_SOURCE_DESIGN.md`：四格决策表 + D1–D4 观测量 + 判别力自检），"
                "但条目原意为「仅设计，不实施」，其**裁定**仍需真实数据或人体/动物实验，章程 §0.2.5 未授权 ⇒ 开放。",
        "O-07": "AGGREGATE 的本体地位：owner 第 5 条把它暂定「派生聚合表示」并写入词表 v1 标 `PROVISIONAL`，"
                "`report/MECHANISM_VOCABULARY_v1.md` 明确「没有替 owner 决定本体问题」⇒ 措辞可用、推论受限，本体问题开放。",
        "O-08": "习惯的行动地位已按「描述相对性」程序化处理，但批量标注所需更细的分描述判定流程未建 ⇒ 开放。",
        "O-09": "双稳态数学分类：K7 内部至少含鞍结分岔/亚稳切换/振荡三类，当前 K 族粒度不足以区分，子标签未设 ⇒ 开放。",
        "O-10": "结构化检索缺失：升级系统综述时才补 PRISMA-S 全项，本轮未做 ⇒ 开放。",
        "O-11": "全文编码缺失：L-01 已对 3 锚点 + 14 邻域做全文编码（42 条逐字引文），仍低于条目建议的 20–30 条核心子集，"
                "且三簇全部判 `INDETERMINATE` ⇒ 「校准 K 族标注」的目标未达成，本条保持开放。",
        "O-12": "量化合成未做：现有计票是**记录数**的方向性票，不是效应量；跨域合并被明确禁止"
                "（`literature/PRELIMINARY_CONCLUSIONS_V2.md` §3）⇒ 开放。",
        "O-13": "核验级别升级路径：owner 第 4 条已**执行**建议的优先级子集（R13/G5-03/R14），但条目要求的「升级预算与"
                "全库优先级」未定，且 `registry.json` 仍 0 条 FULLTEXT ⇒ 开放。",
        "O-14": "DROPPED-CANDIDATE 复池：owner 第 5 条把复核人指派给独立审查 Agent（三条候选 Wald 1949 / "
                "Waddington 1957 / Redgrave 1999 需双源题录），复池审查本身未做 ⇒ 开放，且不在本 Agent 的 §2 范围内。",
        "O-15": "词表治理：v1 草案已交付（`report/MECHANISM_VOCABULARY_v1.md`，owner 第 5 条的 Agent 通道），"
                "但版本化治理流程与责任人决定未落地，`AGGREGATE` 仍为 `PROVISIONAL`，且推导器查出的方向列拼写漂移"
                "（X-70）只登记未清洗 ⇒ 开放。",
        "O-16": "判别力审计推广（初为 15 台门控 / 19 个注入变异，`M2A_FINAL_REPORT.md` §40；§41 已推广到 25 台 / 33 个）"
                "暴露的两条仪器段要求（X-77）：闭式 `predicted` 被移 1e-4 后门控全绿且 `rel_diff` 无人读取；"
                "W2 的「一个计数」容差与 Y2 的网格半步 0.0050 使小于一个晶格步的机制错误原理上不可见。⇒ 两条要求"
                "**须先写入下一轮预注册的仪器段才可执行**，本轮不替下一轮定判据（owner 第 3 条未授权新一轮），故开放。",
        "O-17": "同一次推广（§41、X-79）暴露的另两条：Phase VIII 的 `J5` 写的是 `rho_exact(0.6) == rho_exact(0.6)`，"
                "注入 1e-1 偏移使读数由 154.664 变到 170.130，门控 6 档仍全绿——该条不存在可证伪输入；"
                "Phase V-b 的门控 `import gap_for` 却从未调用它。⇒ 要求「每条数值检查写明可证伪输入、"
                "纯确定性自检不计入仪器条数、import 而未调用的机制函数要么补检查要么删导入」，"
                "**须先写入下一轮预注册的仪器段才可执行**，本轮不回写旧轮门控与其 n/n 记录（R6、第 8 条），故开放。"
                "本条要求的静态普查已交付：`governance/build_coverage_map.py`（覆盖表 v1，`gate_coverage_map_gate.py` "
                "18/18）给出 26 台门控 / 81 个导入仪器 / 10 条缺口名单；名单是处置的前提，处置本身仍属下一轮，"
                "故本条不因交付而关闭。§45 追加：那 10 条名单已在治理层各配到至少一条带可推翻输入的检查"
                "（`unmeasured_instruments_gate.py` 25/25，`rho_exact` 由两台闭式夹逼、`gap_for` 由解析律 1 − sⁿ 约束），"
                "但这改变的只是「是否存在一台仪器」；本条要求的是**轮次判据层**写明可证伪输入并停止把纯确定性自检"
                "计入仪器条数，仍须由下一轮预注册承接 ⇒ 保持 OPEN。",
    }
    if unk:
        print("UNCLASSIFIED labels (no wording class attaches): " + ", ".join(unk), file=sys.stderr)
        raise SystemExit(4)
    no_reason = [k for k in openi if k not in reasons]
    if no_reason:
        print("OPEN label with no registered reason: " + ", ".join(sorted(no_reason)), file=sys.stderr)
        raise SystemExit(4)
    ns_count = {n: sum(1 for r in rows if ns_of(r[0]) == n) for n in ("P", "L01", "O")}
    out += ["", "---", "",
            "**计数**：CLOSED " + str(len(closed)) + " / SUCCEEDED " + str(len(succ_rows))
            + " / OPEN " + str(len(openi)) + " / UNCLASSIFIED " + str(len(unk))
            + "，共 " + str(len(rows)) + " 条标签。命名空间分布：实验轮 `P<n>-O<m>` "
            + str(ns_count["P"]) + " 条、文献轮 `L01-O<m>` " + str(ns_count["L01"])
            + " 条、开放问题 `O-<nn>` " + str(ns_count["O"]) + " 条。", "",
            "## 仍开放（每条都必须带登记原因；缺原因即构建失败）", ""]
    last = None
    for key in sorted(openi, key=label_sort):
        if last is not None and ns_of(last) != ns_of(key):
            out.append("")
        out.append("- **" + key + "**：" + reasons[key])
        last = key
    out += ["", "## 转手关闭（不是在原标签上关闭，如实记为 SUCCEEDED）", "",
            "- **P11-O2**（上确界不可达的退化分支）：Phase XIII 的 E2 **判据失败未关闭**"
            "（0.2% 容差没有由级集离散化速率导出，X-38），改为 P13-O1 重注册，"
            "由 Phase XIV 以精确速率式关闭（`experiments/PHASE14_RESULTS.md`）。",
            "- **P12-O1**（全曲线加权联合拟合）：Phase XIII 的 E4 **未关闭**（D1 严格 `≤` 落在噪声以下，"
            "X-39），收窄为 P13-O2 的可辨识性设计，由 Phase XV 关闭；"
            "`experiments/PHASE15_RESULTS.md` 明确把 P12-O1 记为 P13-O2 的前身。",
            "- 两条的原始「未关闭」判定**均未回写**（R6）：Phase XIII 结果文档照原样保留。", "",
            "## 靠「执行/沿用」而非「已关闭」字样关闭的标签", "",
            "- **P6-O2**（混合聚合的第三结构）：`PHASE7_PREREGISTRATION.md` 声明执行，"
            "`PHASE7_RESULTS.md` §2 给出 `β*(k,m,s)` 组合律——`k=1` 退回 Phase V、`m=1` 退回 Phase VI S3，"
            "第三结构是被算出来的，不是类比。",
            "- **P6-O3**（出口表扩充）：`PHASE7_PREREGISTRATION.md` 建成四档出口表，"
            "`PHASE8_PREREGISTRATION.md` 起沿用该形式。",
            "- **P7-O3**（静默端必须取失效构型集合上的最大值）：写成模板条款后被 "
            "`PHASE8_PREREGISTRATION.md` 作为纪律沿用。",
            "- **P16-O1**（两层离散化联合加密后再比跨 `k`）：`M2A_FINAL_REPORT.md` 记其「落地为一次两层"
            "同时加密的复验」，该复验即 Phase XVII，出口 E2——**它没有关闭 `P14-O1`**"
            "（`PHASE17_RESULTS.md` 写明），而是把 `P14-O1` 的复活路径改写为 `P17-O1`"
            "（`PHASE17_RESULTS.md` §表格），后者由 XVIII 关闭。本条的处置只写在累计报告里，"
            "结果文档未复述，登记为 X-67。",
            "- **P17-O1**（第三条旋钮）：关闭条件在注册时写死于 `PHASE18_PREREGISTRATION.md` 的标题与其 E1，"
            "XVIII 实得 E1（`PHASE18_RESULTS.md`，4/4）⇒ 按注册条件关闭；但 XVIII 的结果文档只复述了 "
            "`P14-O1`，未点名本条，同样登记为 X-67。", "",
            "## 与手抄清单的关系", "",
            "`PHASE18_RESULTS.md` §6 的手抄关闭清单只写到 Phase XVIII，此后各轮（P19-O1…P22-O1）不在其中，"
            "已过期；该节原文保留不改（R6），并已在该节追加指针。义务状态的权威列表是本台账。", ""]

    dest = M / "governance" / SELF
    dest.write_text("\n".join(out), encoding="utf-8")
    print("wrote", dest, "|", len(rows), "labels |", len(closed), "closed |", len(succ_rows),
          "succeeded |", len(openi), "open")
    if mismatches:
        print("\n".join("DERIVE != PIN  " + k + " pinned=" + st + " derived=" + dv
                        + " deciding-sentence=" + ev + " | " + txt
                        for k, st, dv, ev, txt in mismatches), file=sys.stderr)
        raise SystemExit(3)
    print("derive == pin for all " + str(len(rows)) + " labels")


if __name__ == "__main__":
    main()
