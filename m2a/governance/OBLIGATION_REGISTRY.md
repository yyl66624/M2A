# M2A 义务台账（由各轮已提交工件推导，每条带出处）

> 生成：`python3 m2a/governance/build_obligation_registry.py`。本文件由脚本产出，勿手改。
> **为什么不是整行匹配**：累计文档会把「X 已关闭；Y 仍开放」写进同一行（同一个表格单元），按整行判定会把前一句的结论漏给后一个标签——本脚本先切句，再按邻近与连接词判定措辞归属。
> **负面日志不参与判定**：`governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` 记的是当时已知的缺陷，行序按事件号而非处置时间，若让它参与排序，一条 Phase VI 的事故会压过 Phase XVIII 的关闭。该文件仍计入提及与证据，只是不决定状态。
> **双机制**：状态先由句子措辞推导（CLOSED / SUCCEEDED / OPEN），再与脚本内固定断言 `EXPECT` 逐条比对；不一致、断言句找不到或匹配多处、转手指向未关闭的后继、或出现无处置的新标签 ⇒ 构建失败并打印原因。台账因此不能悄悄漂移。
> **出处是内容锚定而非写死行号**：断言记的是「文件 + 该句的特征片段」，行号在构建时解析。本仓库文档只追加不删改，中途插入一段就会让所有后续行号失效——这个失效模式在本脚本第一次改完正文后真实出现过。
> 证据为相对 `m2a/` 的 `路径:行号`，回指原文；本文件自身不参与扫描（否则会用自己当证据）。

| 标签 | 状态 | 提及句数 | 判定出处（构建时解析） | 该句的措辞类别 | 承接标签 |
| --- | --- | --- | --- | --- | --- |
| P5-O1 | **CLOSED** | 2 | `experiments/PHASE5_RESULTS.md:130` | 关闭类措辞 | — |
| P5-O2 | **CLOSED** | 11 | `M2A_FINAL_REPORT.md:265` | 关闭类措辞 | — |
| P5-O3 | **OPEN** | 2 | `experiments/PHASE5_RESULTS.md:132` | 开放类措辞 | — |
| P6-O1 | **CLOSED** | 13 | `M2A_FINAL_REPORT.md:310` | 关闭类措辞 | — |
| P6-O2 | **CLOSED** | 5 | `experiments/PHASE7_PREREGISTRATION.md:4` | 执行/沿用类措辞 | — |
| P6-O3 | **CLOSED** | 7 | `experiments/PHASE7_PREREGISTRATION.md:51` | 执行/沿用类措辞 | — |
| P7-O1 | **CLOSED** | 18 | `experiments/PHASE9_RESULTS.md:1` | 关闭类措辞 | — |
| P7-O2 | **CLOSED** | 14 | `experiments/PHASE9_RESULTS.md:1` | 关闭类措辞 | — |
| P7-O3 | **CLOSED** | 4 | `experiments/PHASE8_PREREGISTRATION.md:5` | 执行/沿用类措辞 | — |
| P8-O1 | **CLOSED** | 27 | `M2A_FINAL_REPORT.md:531` | 关闭类措辞 | — |
| P8-O2 | **CLOSED** | 15 | `M2A_FINAL_REPORT.md:531` | 关闭类措辞 | — |
| P8-O3 | **CLOSED** | 1 | `M2A_PROGRAM_PLAN.md:118` | 关闭类措辞 | — |
| P9-O1 | **CLOSED** | 15 | `M2A_FINAL_REPORT.md:568` | 关闭类措辞 | — |
| P9-O2 | **CLOSED** | 10 | `M2A_FINAL_REPORT.md:568` | 关闭类措辞 | — |
| P9-O3 | **CLOSED** | 6 | `M2A_FINAL_REPORT.md:594` | 关闭类措辞 | — |
| P10-O1 | **CLOSED** | 15 | `M2A_FINAL_REPORT.md:606` | 关闭类措辞 | — |
| P10-O2 | **CLOSED** | 9 | `M2A_FINAL_REPORT.md:606` | 关闭类措辞 | — |
| P10-O3 | **CLOSED** | 5 | `M2A_FINAL_REPORT.md:600` | 关闭类措辞 | — |
| P11-O1 | **OPEN** | 19 | `M2A_FINAL_REPORT.md:848` | 开放类措辞 | — |
| P11-O2 | **SUCCEEDED** | 15 | `M2A_FINAL_REPORT.md:687` | 转手类措辞 | P13-O1 |
| P11-O3 | **CLOSED** | 13 | `experiments/PHASE13_RESULTS.md:28` | 关闭类措辞 | — |
| P12-O1 | **SUCCEEDED** | 15 | `experiments/PHASE15_RESULTS.md:33` | 转手类措辞 | P13-O2 |
| P12-O2 | **CLOSED** | 11 | `experiments/PHASE13_RESULTS.md:10` | 关闭类措辞 | — |
| P12-O3 | **OPEN** | 14 | `M2A_FINAL_REPORT.md:848` | 开放类措辞 | — |
| P13-O1 | **CLOSED** | 24 | `experiments/PHASE14_RESULTS.md:23` | 关闭类措辞 | — |
| P13-O2 | **CLOSED** | 31 | `M2A_FINAL_REPORT.md:731` | 关闭类措辞 | — |
| P14-O1 | **CLOSED** | 46 | `experiments/PHASE18_RESULTS.md:19` | 关闭类措辞 | — |
| P15-O1 | **OPEN** | 6 | `M2A_FINAL_REPORT.md:848` | 开放类措辞 | — |
| P16-O1 | **CLOSED** | 10 | `M2A_FINAL_REPORT.md:799` | 执行/沿用类措辞 | — |
| P17-O1 | **CLOSED** | 10 | `experiments/PHASE18_PREREGISTRATION.md:1` | 关闭类措辞 | — |
| P19-O1 | **CLOSED** | 14 | `experiments/PHASE20_RESULTS.md:64` | 关闭类措辞 | — |
| P20-O1 | **CLOSED** | 16 | `experiments/PHASE21_RESULTS.md:61` | 关闭类措辞 | — |
| P21-O1 | **CLOSED** | 13 | `experiments/PHASE22_RESULTS.md:64` | 关闭类措辞 | — |
| P22-O1 | **CLOSED** | 10 | `M2A_FINAL_REPORT.md:938` | 关闭类措辞 | — |

---

**计数**：CLOSED 28 / SUCCEEDED 2 / OPEN 4 / UNCLASSIFIED 0，共 34 条标签。

## 仍开放（都需要本轮之外的授权或决定，脚本无权替 owner 关闭）

- **P5-O3**：三个以上独立系统的跨域复验——真实数据未授权。
- **P11-O1**：测度口径：静默事件与发放事件互为补集 ⇒ 双侧窗口塌缩，须先重定义判据，属模型类决策。
- **P12-O3**：同上，发放事件一侧的测度口径，属模型类决策。
- **P15-O1**：`e₁` 要双侧估计须换目标函数或换数据族——更细的网格无用。

## 转手关闭（不是在原标签上关闭，如实记为 SUCCEEDED）

- **P11-O2**（上确界不可达的退化分支）：Phase XIII 的 E2 **判据失败未关闭**（0.2% 容差没有由级集离散化速率导出，X-38），改为 P13-O1 重注册，由 Phase XIV 以精确速率式关闭（`experiments/PHASE14_RESULTS.md`）。
- **P12-O1**（全曲线加权联合拟合）：Phase XIII 的 E4 **未关闭**（D1 严格 `≤` 落在噪声以下，X-39），收窄为 P13-O2 的可辨识性设计，由 Phase XV 关闭；`experiments/PHASE15_RESULTS.md` 明确把 P12-O1 记为 P13-O2 的前身。
- 两条的原始「未关闭」判定**均未回写**（R6）：Phase XIII 结果文档照原样保留。

## 靠「执行/沿用」而非「已关闭」字样关闭的标签

- **P6-O2**（混合聚合的第三结构）：`PHASE7_PREREGISTRATION.md` 声明执行，`PHASE7_RESULTS.md` §2 给出 `β*(k,m,s)` 组合律——`k=1` 退回 Phase V、`m=1` 退回 Phase VI S3，第三结构是被算出来的，不是类比。
- **P6-O3**（出口表扩充）：`PHASE7_PREREGISTRATION.md` 建成四档出口表，`PHASE8_PREREGISTRATION.md` 起沿用该形式。
- **P7-O3**（静默端必须取失效构型集合上的最大值）：写成模板条款后被 `PHASE8_PREREGISTRATION.md` 作为纪律沿用。
- **P16-O1**（两层离散化联合加密后再比跨 `k`）：`M2A_FINAL_REPORT.md` 记其「落地为一次两层同时加密的复验」，该复验即 Phase XVII，出口 E2——**它没有关闭 `P14-O1`**（`PHASE17_RESULTS.md` 写明），而是把 `P14-O1` 的复活路径改写为 `P17-O1`（`PHASE17_RESULTS.md` §表格），后者由 XVIII 关闭。本条的处置只写在累计报告里，结果文档未复述，登记为 X-67。
- **P17-O1**（第三条旋钮）：关闭条件在注册时写死于 `PHASE18_PREREGISTRATION.md` 的标题与其 E1，XVIII 实得 E1（`PHASE18_RESULTS.md`，4/4）⇒ 按注册条件关闭；但 XVIII 的结果文档只复述了 `P14-O1`，未点名本条，同样登记为 X-67。

## 与手抄清单的关系

`PHASE18_RESULTS.md` §6 的手抄关闭清单只写到 Phase XVIII，此后各轮（P19-O1…P22-O1）不在其中，已过期；该节原文保留不改（R6），并已在该节追加指针。义务状态的权威列表是本台账。
