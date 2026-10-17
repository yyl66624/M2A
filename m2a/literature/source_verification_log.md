# M2A 来源核验日志（Source Verification Log）

> 版本：Phase I v1.0 ｜ 日期：2026-10-17 ｜ 覆盖：注册表全部 87 条
>
> 本日志记录每条文献的核验通道、裁定结果与书目元数据争议。核验级别与治理规则依据
> 《M2A_CROSS_DISCIPLINARY_FRAMEWORK_v0_2.md》§6。原则：不臆造、不补全、争议留痕、
> 消极/矛盾结果与积极结果同等登记。

## 1. 核验方法

**双通道规程**（每批次执行）：
1. **通道 A — 交叉确认**：web 检索，要求目标文献的题录（作者、题名、期刊/会议、年份、卷期、页码）
   在 ≥2 个相互独立的来源中一致。优先来源类型：出版方页面（出版社/期刊/ACL Anthology）、
   权威参考文献表（含 DOI 的引用列表）、图书馆藏记录（LCCN/ISBN）、JSTOR/PubMed 记录。
2. **通道 B — 定位符解析**：对带 DOI/arXiv/ISBN 的条目执行 DOI 解析或权威页面核对
   （curl 解析 doi.org；打开 ACL Anthology、arXiv、SEP 等条目页）。

**裁定规则**：两通道一致 → IDENTITY_VERIFIED；不一致 → 按来源权威级（出版方 > 图书馆藏 > 权威
参考文献表 > 一般引用页）裁定，并将争议记入本日志第 4 节；无法裁定 → 降级为"待核验"，不进注册表。

**放弃/降级记录**：Wald (1949)、Waddington (1957)、Redgrave (1999) 三条候选在通道 A 多轮
查询中未获双源一致题录，按规程移出候选池（记为 DROPPED-CANDIDATE），不以记忆补录。

## 2. 批次执行记录

| 批次 | 集群 | 条目数 | 结果 |
|---|---|---|---|
| S0 | 种子 R01–R24 | 24 | 全部 IDENTITY_VERIFIED；R13、R23 达 ABSTRACT_VERIFIED |
| S1 | G1 数学/形式 | 7 | 全部 IDENTITY_VERIFIED（Imbens & Rubin 走 LCCN 通道） |
| S2 | G2 物理/化学 | 8 | 全部 IDENTITY_VERIFIED |
| S3 | G3 生物 | 7 | 全部 IDENTITY_VERIFIED |
| S4 | G4 神经/行为 | 7 | 全部 IDENTITY_VERIFIED |
| S5 | G5 AI/工程 | 10 | 全部 IDENTITY_VERIFIED；Arditi 适用面争议转矛盾记录 |
| S6 | G6 社会/经济 | 8 | 全部 IDENTITY_VERIFIED |
| S7 | G7 人文/法律/哲学 | 8 | 全部 IDENTITY_VERIFIED；Anscombe 首版出版社更正 |
| S8 | G8 NLP/知识工程 | 8 | 全部 IDENTITY_VERIFIED；Chambers 2017 未获双源确认，改用 Chambers & Jurafsky 2008 |

累计检索轮次 ≥30（web_search 分组批次），满足 deep-research 规程 ≥10 步检索的最低要求。

## 3. 通道 B 执行摘要

- DOI 解析执行于全部带 DOI 条目（R01, R03–R10, R11, R12, R14–R17, R18, R20–R22,
  G1-01, G1-04, G1-06, G8-01, G8-02, G8-05, G8-06, G8-07 等），均返回与注册表一致之题录。
- ACL Anthology 条目页核对：R01, R02, G8-03 (L16-1262), G8-04 (L04-1011), G8-08 (P08-1090)。
- arXiv 记录核对：G5-01 (2203.02155), G5-02 (2210.03629), G5-03 (2406.11717),
  G5-04 (2209.13085), G5-05 (1606.06565), G5-07 (1803.10122), G5-08 (2108.06266), G5-09 (1706.03741)。
- 图书馆藏通道：R19 (ISBN 9780262039246), R22 (DOI 10.2307/j.ctt7s7wm + ISBN),
  G1-02 (LCCN 2014-020988), G6-04 (ISBN 9780521405997), G6-08 (ISBN 9780674707580),
  G7-05 (ISBN 9780262232227), G7-08 (ISBN 0521273021)。
- SEP 全文读取：R23（按 ABSTRACT_VERIFIED 保守标注，防止越级声称）。

## 4. 书目元数据争议登记册（裁定记录）

| # | 涉及条目 | 争议内容 | 裁定 | 依据 |
|---|---|---|---|---|
| V-01 | R08 | online 2025 vs 纸本 2026 双日期 | 引用作 2025/2026，以卷期页为准 | 出版方页面显示 online 2025、卷期 4(3):236–249 属 2026 年卷 |
| V-02 | R13 | 摘要级 vs 全文级核验 | ABSTRACT_VERIFIED | nature.com 条目页受访问限制，仅摘要可核 |
| V-03 | R14 | Publisher Correction 存在 | 主引文保留，勘误 DOI 并列登记 | 出版方勘误页 DOI 10.1038/s41593-026-02425-7（2026-08-03） |
| V-04 | G5-03 (Arditi) | 结论普遍性：13 个模型均为 RLHF/DPO 对齐的开源聊天模型；后续批评（Wollschläger et al. 2025, arXiv 2502.17420 "concept cones"；2026 年后续 arXiv 2602.02132） | 机制标注保留 K2 但转矛盾记录 07-号 | 批评文题录经通道 A 确认 |
| V-05 | G6-01 | 一处来源页码作 363–391 | 采用 263–291 | Econometric Society 卷 47(2) 记录 263–291；JSTOR 1914185 |
| V-06 | G7-01 | Anscombe《Intention》首版出版社 | 首版 Basil Blackwell (Oxford)；Harvard UP 为 2000 重印 | 图书馆藏与版权页记录 |
| V-07 | G6-07 | Damschroder 2009 双 PMID | 采用 PMID 19664226；19123945 并存登记 | PubMed 记录；Implement. Sci. 4:50, DOI 10.1186/1748-5908-4-50 |
| V-08 | G5-04 | Skalse 2022 页码各源不一（9460–9471 等） | 注册表不列页码，以 arXiv 为准 | 引用源间不一致，按不臆造原则省略 |
| V-09 | G7-06 | Libet 1985 BBS 文 vs Libet et al. 1983 Brain 106:623–642 伴生实验文 | 两文分列，避免张冠李戴 | BBS 8(4):529–566, DOI 10.1017/S0140525X00044903 |
| V-10 | G3-03 vs R10 | 两篇同名 "CD28 costimulation: from mechanism to therapy"（Immunity 2016 / Nat. Rev. Immunol. 2024） | 各归各条，题名重名登记 | 作者、期刊、年份均不同，属不同文献 |
| V-11 | G5-07 | World Models arXiv 版 vs NeurIPS 2018 会议版（题名不同） | 两版并列登记 | arXiv:1803.10122；NeurIPS 版 pp. 2455–2467 |
| V-12 | G8-04 | ACE 论文页码 837–840 仅见于部分引用源 | 注册表不列页码，以 ACL Anthology L04-1011 为准 | Anthology 条目页未列页码 |
| V-13 | G8 | Chambers (2017) TACL 条目未获双源一致 | 弃用，改用 Chambers & Jurafsky (2008) ACL-08: HLT, pp. 789–797 (P08-1090) | 通道 A 0 结果 + 备选获双源确认 |

## 5. 未决与 Phase II 移交事项

1. R13 全文级核验：移交 Phase II（需机构访问权限或作者存档版）。
2. Arditi 单方向结论的跨模型复现：移交 Phase II 机制验证候选。
3. R14 Publisher Correction 对定量结论的影响程度：Phase II 需对照勘误正文核定。
4. DROPPED-CANDIDATE（Wald 1949 / Waddington 1957 / Redgrave 1999）若后续获得双源题录，可重新入池。
5. 全部 87 条中无一条达到 FULLTEXT_REVIEWED / CLAIM_INDEPENDENTLY_CHECKED；
   Phase I 报告须如实声明此上限（详见报告 §1 与 §7）。
