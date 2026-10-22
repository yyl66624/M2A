# 节 ↔ 页面 分数对账 v1（由工件推导）

> 推导器 `governance/build_section_page_reconciliation.py`，校验器
> `governance/section_page_reconciliation_gate.py`。承接关系取自 §46 的同步表；页面正文读自
> `feishu_wiki_fetches/<node_token>.txt`（抓取在收尾审计之外进行，审计本身不联网）。
> 判据只有一个硬的：页面上某仪器的 `n/n` 在**整个仓库**里既没有被严格印过、也没有被宽松读到过，
> 而且没有订正登记 ⇒ 抄错或凭空。严格口径是名字后三个字符内；宽松口径是同一行内最近的前置名字，
> 只用来**支持**页面的说法，不用来制造说法（口径不对称只会让判据更弱，不会凭空判红）。
> 派生工件自身不在出处扫描里：给自己背书会让一次漂移永久变成「仓库里印过」（R8）。
> 分数被后续轮次追上（页面写 7/7 而该套件今天印 8/8）记为 `page_superseded`，是事实陈年而非缺陷；
> 页面少点名若干仪器记为 `compressed`，是摘要取舍。

| 列 | 数 |
| --- | --- |
| 对账的页面 | 25 |
| 覆盖的步骤节 | 29（同步表登记 29） |
| **页面上的分数在仓库里查无出处** | 0 |
| 页面点名的仪器被本仓库有意排除在测量之外（披露，不判红） | 1 页 / 1 个值 |
| 仅由宽松口径支持的页面分数 | 0 |
| 只由登记处转写支持的分数（洗白通道，逐条列出） | 1 |
| 已登记的订正（页面上引用为错误的数字） | 1（生效 1） |
| 订正已登记但尚未生效（页面缺该数字或缺订正标记） | 0 |
| 页面分数已被后来的节追上 | 1 |
| 页面压缩（节里有、页里没有） | 2 |
| 完全一致 | 21 |
| 无抓取可比 | 0 |
| 草稿 ↔ 页面不一致（草稿的说法页面上没有） | 0 |
| 页面在发布之后又追加了内容（草稿是子集） | 2 |
| 仓库里被印过的仪器 | 24 台 |
| 页面点名 / 节点名 | 13 台 / 13 台 |
| 页面分数条数 / 节分数条数 | 16 / 15 |
| 只在页面出现（节里没点名） | l01_gate.py, suite_score_registry_gate.py |
| 只在节里出现（页面压缩掉） | frozen_input_map_gate.py, p24_gate.py |

## 逐页

| 节 | 页面（截断） | 判定 | 页面分数条数 | 仅宽松支持 | 订正 | 页面没写 | 被追上 | 草稿↔页 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 31 | M2A Phase I′｜闸门③补做一致性检 | aligned | 0 | - | - | - | - | not_a_governance_page |
| 32 | M2A 文献轮 L-01｜14 条全文编码， | aligned | 1 | - | l01_gate.py 6/6→7/7 | - | - | page_grew_after_publication |
| 33 | M2A 治理｜机制词表 v1 草案：由工件推 | aligned | 0 | - | - | - | - | aligned |
| 34,37 | M2A 治理｜五值标签口径表 v1→v2：M | aligned | 1 | - | - | - | - | aligned |
| 35,36 | M2A 治理｜台账三命名空间与 L-01 主 | page_superseded | 1 | - | - | - | obligation_registry_gate.py 7/7 | aligned |
| 38 | M2A 治理｜AO 预检落地为仪器，查出一条 | aligned | 1 | - | - | - | - | aligned |
| 39,40,41 | M2A 治理｜门控判别力审计：25 台的判别 | aligned | 1 | - | - | - | - | aligned |
| 42 | M2A 治理｜门控仪器覆盖表 v1：用语法导 | aligned | 1 | - | - | - | - | aligned |
| 43 | M2A 治理｜runner 侧门控强制表 v | aligned | 1 | - | - | - | - | aligned |
| 44 | M2A 治理｜门控分数三方对账 v1：文档引 | aligned | 2 | - | - | - | - | aligned |
| 45 | M2A 治理｜未测量仪器的治理层检查 v1： | aligned | 3 | - | - | - | - | aligned |
| 46 | M2A 治理｜wiki 同步表 v1：让「每 | aligned | 1 | - | - | - | - | aligned |
| 47 | M2A 治理｜节↔页分数对账 v1：页面说的 | aligned | 2 | - | - | - | - | aligned |
| 48 | M2A 治理｜套件分数引用对账 v1：仓库自 | self_referential_claim | 1 | - | - | - | - | page_grew_after_publication |
| 49 | M2A 治理｜判定标签↔工件对账 v1：散文 | aligned | 0 | - | - | - | - | aligned |
| 50 | M2A 治理｜判据数值↔轮次记录对账 v1： | aligned | 0 | - | - | - | - | aligned |
| 51 | M2A 文献轮 L-02｜把「族 + 符号」 | aligned | 0 | - | - | - | - | aligned |
| 52 | M2A 治理｜义务台账的命名空间由标签形状推 | aligned | 0 | - | - | - | - | aligned |
| 53 | M2A 治理｜判定锚点加宽之后，门控里不能装 | aligned | 0 | - | - | - | - | aligned |
| 54 | M2A 治理｜冻结输入登记表 v1：谁已经记 | aligned | 0 | - | - | - | - | aligned |
| 55 | M2A 治理｜一条硬伤档只能在误判别的形状时 | aligned | 0 | - | - | - | - | aligned |
| 56 | M2A 治理｜冻结的「看得见」不是一个开关， | aligned | 0 | - | - | - | - | aligned |
| 57 | M2A 治理｜校验器进人口不是往清单里加一行 | compressed | 0 | - | - | frozen_input_map_gate.py | - | aligned |
| 58 | M2A 文献轮 L-03｜R13-N15 全 | aligned | 0 | - | - | - | - | aligned |
| 59 | M2A Phase XXIV｜L2 权重衰减 | compressed | 0 | - | - | p24_gate.py | - | aligned |

## 每条页面分数的仓库出处（`attest`）

| 仪器 | 页面上的分数 | 仓库里印过它的文件 | 节里最新引用它的节号 |
| --- | --- | --- | --- |
| `l01_gate.py` | 6/6/7/7 | `literature/ROUND_L01_RESULTS.md` | §- |
| `status_label_table_gate.py` | 6/6 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §37 |
| `obligation_registry_gate.py` | 7/7 | `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §45 |
| `ao_preflight_gate.py` | 8/8 | `M2A_FINAL_REPORT.md` | §38 |
| `gate_discrimination_gate.py` | 59/59 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §47 |
| `gate_coverage_map_gate.py` | 18/18 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §45 |
| `runner_enforcement_map_gate.py` | 14/14 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §43 |
| `p10_gate.py` | 6/6 | `M2A_FINAL_REPORT.md`, `experiments/PHASE10_RESULTS.md` | §44 |
| `result_score_map_gate.py` | 12/12 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §44 |
| `gate_coverage_map_gate.py` | 17/17/18/18 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §45 |
| `obligation_registry_gate.py` | 8/8 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §45 |
| `unmeasured_instruments_gate.py` | 25/25 | `M2A_FINAL_REPORT.md`, `governance/OBLIGATION_REGISTRY.md` | §45 |
| `wiki_sync_map_gate.py` | 16/16 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §46 |
| `gate_discrimination_gate.py` | 59/59 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §47 |
| `section_page_reconciliation_gate.py` | 22/22 | `M2A_FINAL_REPORT.md`, `governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | §47 |
| `suite_score_registry_gate.py` | 20/20 | -无- | §- |

**能看见与看不见**：只比 `n/n` 头条，且只有一条硬判据。它不比句子、判据数值、容差阶梯与
结论措辞；陈年分数与摘要压缩都如实列出而不判红（本项目规矩是历史陈述不回写，更正出现在新节）；
抓取不重新联网，其时刻证据是 `feishu_wiki_fetches/` 的文件指纹；抓取脚本本身不在同步表钉住的
工具之列（钉住的是数字复核器、发布器与台账），这是已知缺口。出处扫描**排除本工件自己写出的
两个文件**（`section_page_reconciliation_v1.json`、`SECTION_PAGE_RECONCILIATION_v1.md`）：
派生工件若给自己背书，一次漂移被记进工件后就永远“在仓库里印过”，判据从此打不响（R8）。
排除按**命名空间**而不是手写清单：`governance/` 下所有 `*_v<N>.json/.md` 与 `report/` 下的摘要
都算转写件不作出处；轮次读数（`*_RESULTS.md`、`phase*_results.json`、`L01_coding.json`）由 runner
写出，仍是合法出处。这样新增一台派生工件时不必再改排除表（§48 一进来就会被这张表洗白，正是这条
规则要挡的形状）。
它也不排除台账与负面日志那类转写件——转写错误若进了它们，仍会被当成出处，这是有意保留的宽松。
