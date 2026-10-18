"""Rebuild m2a/governance/OBLIGATION_REGISTRY.md from the committed artifacts.

Two mechanisms, deliberately independent:

* **derivation** — every `P<n>-O<m>` mention is collected with `path:line`, and each mention is
  classified by the wording of the *sentence* it sits in. Line-level matching is wrong: the
  cumulative documents pack "X is closed. Y is still open" into one table row, so the first
  clause's verdict leaks onto the second label.
* **pin** — `EXPECT` records the disposition asserted for this round, with the sentence that
  justifies it. The build aborts if derivation and pin disagree, if a cited sentence stops
  matching, or if a label appears anywhere in the artifacts without a disposition.

So the registry cannot drift silently: a future round that closes or reopens something must
change the cited sentence *and* the pin, and a brand-new open item fails the build until it has
a recorded disposition.
"""
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent
SELF = "OBLIGATION_REGISTRY.md"

# --- wording classes -----------------------------------------------------------
CLOSE = re.compile(r"(?<![未非])(?:已)?关闭|已完成|落实|已交付|答复|已在 Phase|升格为定理|统一为定理")
ADOPT = re.compile(r"执行|覆盖|教训|模板条款|已按|采纳|写入纪律|落地为")
HAND = re.compile(r"→|->|前身|后继|收窄为|仍在册")
BLOCK = re.compile(r"未授权|未做|未启动|仍需|仍开放|尚开放|模型类决策|待框架|待决定|待 owner|留给 owner"
                   r"|需新一轮|需新预注册|先重定义|须换|需要第|才能升为|未关闭|未通过|未回答")
SENT = re.compile(r"[。；;！!？?]")

# (status, wording class, citation `path:line`, successor label or None)
# SUCCEEDED = handed to a successor label (which is itself CLOSED) instead of being closed in place.
EXPECT = {
    "P5-O1": ("CLOSED", "close", "experiments/PHASE5_RESULTS.md:130", None),
    "P5-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md:265", None),
    "P5-O3": ("OPEN", "block", "experiments/PHASE5_RESULTS.md:132", None),
    "P6-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md:310", None),
    "P6-O2": ("CLOSED", "adopt", "experiments/PHASE7_PREREGISTRATION.md:4", None),
    "P6-O3": ("CLOSED", "adopt", "experiments/PHASE7_PREREGISTRATION.md:51", None),
    "P7-O1": ("CLOSED", "close", "experiments/PHASE9_RESULTS.md:1", None),
    "P7-O2": ("CLOSED", "close", "experiments/PHASE9_RESULTS.md:1", None),
    "P7-O3": ("CLOSED", "adopt", "experiments/PHASE8_PREREGISTRATION.md:5", None),
    "P8-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md:515", None),
    "P8-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md:515", None),
    "P8-O3": ("CLOSED", "close", "M2A_PROGRAM_PLAN.md:118", None),
    "P9-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md:552", None),
    "P9-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md:552", None),
    "P9-O3": ("CLOSED", "close", "M2A_FINAL_REPORT.md:578", None),
    "P10-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md:590", None),
    "P10-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md:590", None),
    "P10-O3": ("CLOSED", "close", "M2A_FINAL_REPORT.md:584", None),
    "P11-O1": ("OPEN", "block", "M2A_FINAL_REPORT.md:832", None),
    # Phase XIII deliberately failed E2/E4 (the 0.2% tolerance was not derived in advance), so
    # these two were handed on, not closed in place; the successors closed in XIV and XV.
    "P11-O2": ("SUCCEEDED", "hand", "M2A_FINAL_REPORT.md:671", "P13-O1"),
    "P11-O3": ("CLOSED", "close", "experiments/PHASE13_RESULTS.md:28", None),
    "P12-O1": ("SUCCEEDED", "hand", "experiments/PHASE15_RESULTS.md:33", "P13-O2"),
    "P12-O2": ("CLOSED", "close", "experiments/PHASE13_RESULTS.md:10", None),
    "P12-O3": ("OPEN", "block", "M2A_FINAL_REPORT.md:832", None),
    "P13-O1": ("CLOSED", "close", "experiments/PHASE14_RESULTS.md:41", None),
    "P13-O2": ("CLOSED", "close", "M2A_FINAL_REPORT.md:715", None),
    "P14-O1": ("CLOSED", "close", "experiments/PHASE18_RESULTS.md:19", None),
    "P15-O1": ("OPEN", "block", "M2A_FINAL_REPORT.md:832", None),
    "P16-O1": ("CLOSED", "adopt", "M2A_FINAL_REPORT.md:783", None),
    "P17-O1": ("CLOSED", "close", "experiments/PHASE18_PREREGISTRATION.md:1", None),
    "P19-O1": ("CLOSED", "close", "experiments/PHASE20_RESULTS.md:64", None),
    "P20-O1": ("CLOSED", "close", "experiments/PHASE21_RESULTS.md:61", None),
    "P21-O1": ("CLOSED", "close", "experiments/PHASE22_RESULTS.md:64", None),
    "P22-O1": ("CLOSED", "close", "M2A_FINAL_REPORT.md:922", None),
}
CLASS = {"close": CLOSE, "adopt": ADOPT, "hand": HAND, "block": BLOCK}

LABEL = re.compile(r"P\d{1,2}-O\d")
BOUNDARY = re.compile(r"[，,。；;！!？?]")
ARROW = re.compile(r"→|->")
JOIN = re.compile(r"[\s`/／与和及\-—–()（）*·]*")
# The negative/null log records the defect *as known at that round*, and its rows are ordered by
# incident number, not by when a disposition was reached; letting it decide status would rank a
# Phase VI incident above a Phase XVIII closure. It still counts as a mention and as evidence.
STATUS_SKIP = {"governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md"}


def attaches(sent, key, pat, window=60):
    """True if `pat` matches within `window` chars of an occurrence of `key`, and the wording is
    syntactically linked to *that* label rather than to a neighbour.

    Rules, with the reason each exists:
    * labels joined by nothing but `、`-free glue (space, backticks, `/`, 与/和/及, dashes, brackets)
      share a verdict — "`P8-O1` 与 `P8-O2` 关闭" closes both, and "`P6-O1/O2/O3` … 全部关闭" too;
      but `、` is an enumeration of items that each carry their own verdict, so it does not glue;
    * a *preceding* verdict must not be separated from the label by a clause boundary — that is how
      "`P13-O1` 关闭，`P11-O2` 的退化分支变成…" would otherwise leak P13-O1's verdict onto P11-O2;
    * a *following* verdict may have free text in between ("`P11-O1`/`P12-O3` 测度口径（须先重定义判据，
      属模型类决策）"), as long as no un-glued label intervenes.
    """
    kpos = [(m.start(), m.end()) for m in re.finditer(re.escape(key), sent)]
    others = sorted((m.start(), m.end()) for m in LABEL.finditer(sent) if m.group(0) != key)
    for w in pat.finditer(sent):
        for i, k_end in kpos:
            lo, hi = min(i, w.start()), max(i, w.start())
            if hi - lo > window:
                continue
            inside = [span for span in others if lo < span[0] < hi]
            if w.start() < i:
                if BOUNDARY.search(sent[lo:hi]) or ARROW.search(sent[w.end():i]):
                    continue  # the verdict belongs to the arrow's source, not its target
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


def order(path, ln):
    """Sort key: phase rounds by round number, cumulative documents last, then path, then line."""
    m = re.search(r"PHASE(\d{1,3})", path)
    return (int(m.group(1)) if m else 999, path, ln)


def sentences(text_lines):
    for ln, line in enumerate(text_lines, 1):
        for sent in SENT.split(line):
            if sent.strip():
                yield ln, sent.strip()


def collect():
    labels = {}
    for f in sorted(list(M.rglob("*.md")) + list(M.rglob("*.json"))):
        if f.name == SELF:
            continue  # the registry must never cite itself
        rel = str(f.relative_to(M))
        for ln, sent in sentences(f.read_text(encoding="utf-8", errors="replace").splitlines()):
            for a, b in re.findall(r"\bP(\d{1,2})-O(\d)\b", sent):
                labels.setdefault("P" + a + "-O" + b, []).append((rel, ln, sent, order(rel, ln)))
    return labels


def successor(sent, key):
    """The label this sentence hands `key` over to, or None. Directional on purpose: in
    "`P14-O1` 仍开放（→ P17-O1）" the hand-over belongs to P14-O1, and must not make P17-O1 look
    like it was itself handed on."""
    for i in (m.start() for m in re.finditer(re.escape(key), sent)):
        labs = sorted((m.start(), m.end(), m.group(0)) for m in LABEL.finditer(sent)
                      if m.group(0) != key)
        for a in re.finditer(r"→|->", sent):
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


def derive(key, hits):
    """Sentence-level, nearest-label disposition.

    `attaches` decides whether a verdict wording belongs to this label rather than a neighbour;
    see its docstring. Hand-over sentences are read directionally by `successor`, and count as a
    positive only when the named successor is itself closed somewhere in the artifacts.
    """
    pos, neg = [], []
    for h in hits:
        if h[0] in STATUS_SKIP:
            continue
        s = h[2]
        if CLOSE.search(s) and attaches(s, key, CLOSE):
            pos.append((h, "close"))
        elif ADOPT.search(s) and attaches(s, key, ADOPT):
            pos.append((h, "adopt"))
        else:
            succ = successor(s, key)
            if succ and EXPECT.get(succ, ("?",))[0] in ("CLOSED", "SUCCEEDED"):
                pos.append((h, "hand", succ))
        if BLOCK.search(s) and attaches(s, key, BLOCK):
            neg.append(h)
    pos.sort(key=lambda ca: ca[0][3])
    neg.sort(key=lambda h: h[3])
    if pos and (not neg or pos[-1][0][3] >= neg[-1][3]):
        winner = pos[-1]
        if len(winner) == 3:
            return "SUCCEEDED", winner[0]
        return "CLOSED", winner[0]
    if neg:
        return "OPEN", neg[-1]
    return "UNCLASSIFIED", sorted(hits, key=lambda h: h[3])[-1]


def cited_sentence(cite, key):
    """Return the sentence at `path:line` that mentions `key`, or None."""
    rel, ln = cite.rsplit(":", 1)
    path = M / rel
    if not path.is_file():
        return None, "file missing"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = int(ln) - 1
    if idx < 0 or idx >= len(lines):
        return None, "past EOF"
    for sent in SENT.split(lines[idx]):
        if key in sent:
            return sent, None
    return None, "line " + cite + " has no sentence mentioning " + key


def verify_pins():
    errors = []
    for key, spec in sorted(EXPECT.items()):
        status, cls, cite, succ = spec
        sent, bad = cited_sentence(cite, key)
        if bad:
            errors.append(key + ": " + bad + " (" + cite + ")")
            continue
        if cls == "hand":
            got = successor(sent, key)
            if got != succ:
                errors.append(key + ": cited sentence " + cite + " hands over to " + str(got)
                              + ", pin says " + str(succ))
        elif not attaches(sent, key, CLASS[cls]):
            errors.append(key + ": cited sentence " + cite + " has " + cls
                          + " wording, but not attached to this label (another label intervenes)")
        if status == "SUCCEEDED":
            if succ not in sent:
                errors.append(key + ": successor " + str(succ) + " not named in " + cite)
            if EXPECT.get(succ, ("?",))[0] not in ("CLOSED", "SUCCEEDED"):
                errors.append(key + ": successor " + str(succ) + " is not itself closed")
    return errors


def main():
    errors = verify_pins()
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
    for key in sorted(labels, key=lambda s: (int(re.match(r"P(\d+)", s).group(1)),
                                             int(s.split("O")[1]))):
        status, cls, cite, succ = EXPECT[key]
        dv, ev = derive(key, labels[key])
        if dv != status:
            mismatches.append((key, status, dv, ev[0] + ":" + str(ev[1]),
                               re.sub(r"\s+", " ", ev[2])[:110]))
        rows.append((key, status, len(labels[key]), cite, cls, succ))

    names = {"close": "关闭类措辞", "adopt": "执行/沿用类措辞", "hand": "转手类措辞",
             "block": "开放类措辞"}
    out = ["# M2A 义务台账（由各轮已提交工件推导，每条带出处）", "",
           "> 生成：`python3 m2a/governance/build_obligation_registry.py`。本文件由脚本产出，勿手改。",
           "> **为什么不是整行匹配**：累计文档会把「X 已关闭。Y 仍开放」写进同一行（同一个表格单元），"
           "按整行判定会把前一句的结论漏给后一个标签——本脚本先切句再判定。",
           "> **负面日志不参与判定**：`governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` 记的是当时已知的缺陷，"
           "行序按事件号而非处置时间，若让它参与排序，一条 Phase VI 的事故会压过 Phase XVIII 的关闭。"
           "该文件仍计入提及与证据，只是不决定状态。",
           "> **双机制**：状态先由句子措辞推导（CLOSED / SUCCEEDED / OPEN），再与本轮固定断言 `EXPECT` 逐条比对；"
           "不一致、断言引用的句子不再成立、或出现无处置的新标签 ⇒ 构建失败并打印原因。"
           "台账因此不能悄悄漂移。",
           "> 证据为相对 `m2a/` 的 `路径:行号`，回指原文；本文件自身不参与扫描（否则会用自己当证据）。", "",
           "| 标签 | 状态 | 提及句数 | 判定出处 | 该句的措辞类别 | 承接标签 |",
           "| --- | --- | --- | --- | --- | --- |"]
    for key, status, n, cite, cls, succ in rows:
        out.append("| " + key + " | **" + status + "** | " + str(n) + " | `" + cite + "` | "
                   + names[cls] + " | " + (succ or "—") + " |")

    closed = [r[0] for r in rows if r[1] == "CLOSED"]
    succ = [r[0] for r in rows if r[1] == "SUCCEEDED"]
    openi = [r[0] for r in rows if r[1] == "OPEN"]
    out += ["", "---", "",
            "**计数**：CLOSED " + str(len(closed)) + " / SUCCEEDED " + str(len(succ)) + " / OPEN "
            + str(len(openi)) + " / UNCLASSIFIED 0，共 " + str(len(rows)) + " 条标签、"
            + str(sum(r[2] for r in rows)) + " 处句子级提及。", "",
            "## 仍开放（都需要本轮之外的授权或决定，脚本无权替 owner 关闭）", ""]
    reasons = {
        "P5-O3": "三个以上独立系统的跨域复验——真实数据未授权。",
        "P11-O1": "测度口径：静默事件与发放事件互为补集 ⇒ 双侧窗口塌缩，须先重定义判据，属模型类决策。",
        "P12-O3": "同上，发放事件一侧的测度口径，属模型类决策。",
        "P15-O1": "`e₁` 要双侧估计须换目标函数或换数据族——更细的网格无用。",
    }
    for key in openi:
        out.append("- **" + key + "**：" + reasons.get(key, "（缺登记原因，须补）"))
    out += ["", "## 转手关闭（不是在原标签上关闭，如实记为 SUCCEEDED）", "",
            "- **P11-O2**（上确界不可达的退化分支）：Phase XIII 的 E2 **判据失败未关闭**"
            "（0.2% 容差没有由级集离散化速率导出，X-38），改为 P13-O1 重注册，"
            "由 Phase XIV 以精确速率式关闭（`experiments/PHASE14_RESULTS.md:41`）。",
            "- **P12-O1**（全曲线加权联合拟合）：Phase XIII 的 E4 **未关闭**（D1 严格 `≤` 落在噪声以下，"
            "X-39），收窄为 P13-O2 的可辨识性设计，由 Phase XV 关闭；"
            "`experiments/PHASE15_RESULTS.md:33` 明确把 P12-O1 记为 P13-O2 的前身。",
            "- 两条的原始「未关闭」判定**均未回写**（R6）：Phase XIII 结果文档照原样保留。", "",
            "## 靠「执行/沿用」而非「已关闭」字样关闭的标签", "",
            "- **P6-O2**（混合聚合的第三结构）：`PHASE7_PREREGISTRATION.md:4` 声明执行，"
            "`PHASE7_RESULTS.md` §2 给出 `β*(k,m,s)` 组合律——`k=1` 退回 Phase V、`m=1` 退回 Phase VI S3，"
            "第三结构是被算出来的，不是类比。",
            "- **P6-O3**（出口表扩充）：`PHASE7_PREREGISTRATION.md:51` 建成四档出口表，"
            "`PHASE8_PREREGISTRATION.md:5` 起沿用该形式。",
            "- **P7-O3**（静默端必须取失效构型集合上的最大值）：写成模板条款后被 "
            "`PHASE8_PREREGISTRATION.md:5` 作为纪律沿用。",
            "- **P16-O1**（两层离散化联合加密后再比跨 `k`）：`M2A_FINAL_REPORT.md:783` 记其"
            "「落地为一次两层同时加密的复验」，该复验即 Phase XVII，出口 E2——"
            "**它没有关闭 `P14-O1`**（`PHASE17_RESULTS.md:6` 写明），而是把 `P14-O1` 的复活路径改写为 "
            "`P17-O1`（`PHASE17_RESULTS.md:49`），后者由 XVIII 关闭。"
            "本条的处置只写在 `M2A_FINAL_REPORT.md:783`，结果文档未复述，登记为 X-67。",
            "- **P17-O1**（第三条旋钮）：关闭条件在注册时写死于 `PHASE18_PREREGISTRATION.md:1` 与其 E1，"
            "XVIII 实得 E1（`PHASE18_RESULTS.md:1`，4/4）⇒ 按注册条件关闭；"
            "但 XVIII 的结果文档只复述了 `P14-O1`，未点名本条，同样登记为 X-67。", "",
            "## 与手抄清单的关系", "",
            "`PHASE18_RESULTS.md` §6 的手抄关闭清单只写到 Phase XVIII，此后各轮"
            "（P19-O1…P22-O1）不在其中，已过期；该节原文保留不改（R6），"
            "义务状态的权威列表以本台账为准。", ""]

    dest = M / "governance" / SELF
    dest.write_text("\n".join(out), encoding="utf-8")
    print("wrote", dest, "|", len(rows), "labels |", len(closed), "closed |", len(succ),
          "succeeded |", len(openi), "open")
    if mismatches:
        print("\n".join("DERIVE != PIN  " + k + " pinned=" + st + " derived=" + dv
                        + " last-sentence=" + ev + " | " + txt
                        for k, st, dv, ev, txt in mismatches), file=sys.stderr)
        raise SystemExit(3)
    print("derive == pin for all " + str(len(rows)) + " labels")


if __name__ == "__main__":
    main()
