# M2A 义务台账（由各轮已提交工件推导，每条带出处）

> 生成：`python3 m2a/governance/build_obligation_registry.py`。本文件由脚本产出，勿手改。
> **为什么不是整行匹配**：累计文档会把「X 已关闭；Y 仍开放」写进同一行（同一个表格单元），按整行判定会把前一句的结论漏给后一个标签——本脚本先切句，再按邻近与连接词判定措辞归属。
> **负面日志不参与判定**：`governance/NEGATIVE_AND_NULL_EVIDENCE_LOG.md` 记的是当时已知的缺陷，行序按事件号而非处置时间，若让它参与排序，一条 Phase VI 的事故会压过 Phase XVIII 的关闭。该文件仍计入提及与证据，只是不决定状态。
> **双机制**：状态先由句子措辞推导（CLOSED / SUCCEEDED / OPEN），再与脚本内固定断言 `EXPECT` 逐条比对；不一致、断言句找不到或匹配多处、转手指向未关闭的后继、或出现无处置的新标签 ⇒ 构建失败并打印原因。台账因此不能悄悄漂移。
> **出处是内容锚定而非写死行号**：断言记的是「文件 + 该句的特征片段」，行号在构建时解析。本仓库文档只追加不删改，中途插入一段就会让所有后续行号失效——这个失效模式在本脚本第一次改完正文后真实出现过。
> **命名空间由标签形状推导（当前 5 个命名空间、5 份承载工件）**：`P<n>-O<m>`（实验轮）、`L0n-O<m>`（每一轮文献各一份，承载工件就是那一轮自己的记录）、`O-<nn>`（08 开放问题清单）。`L01-O*` 与 `O-*` 此前不在扫描范围内，一条开放项可以从台账上消失而构建毫无察觉（`ROUND_L01_RESULTS.md` §9.6 登记，与 X-67 同源）；命名空间若改用列举而非形状，下一轮仍然不在名单上（X-106 同族）。每个命名空间的措辞类别不同（文献侧写「待裁定 / 建议 / 需指定」而非「关闭 / 落实」），且**状态只由其承载判定措辞的那份工件决定**：`L0n-O<m>` 只看``ROUND_L0n_RESULTS.md``，`O-<nn>` 只看 `08_OPEN_QUESTIONS.md`（owner 2026-10-18 明示「状态字保持原样」）；其他文件的提及计入证据与漂移检测，但不得翻转状态。
> **提及句数**按「提到该标签的句子数」计，同一句里重复出现只算一句（X-67 行内两次写到 `P16-O1`，此处计 1）；它衡量的是**散布度**不是出现次数，因此与旧版按出现次数计的读数会有±1 的差，状态列不受影响。
> 证据为相对 `m2a/` 的 `路径:行号`，回指原文；本文件自身不参与扫描（否则会用自己当证据）。

| 标签 | 状态 | 提及句数 | 判定出处（构建时解析） | 该句的措辞类别 | 承接标签 |
| --- | --- | --- | --- | --- | --- |
| P5-O1 | **CLOSED** | 2 | `experiments/PHASE5_RESULTS.md:130` | 关闭类措辞 | — |
| P5-O2 | **CLOSED** | 11 | `M2A_FINAL_REPORT.md:265` | 关闭类措辞 | — |
| P5-O3 | **OPEN** | 3 | `experiments/PHASE5_RESULTS.md:132` | 开放类措辞 | — |
| P6-O1 | **CLOSED** | 13 | `M2A_FINAL_REPORT.md:310` | 关闭类措辞 | — |
| P6-O2 | **CLOSED** | 5 | `experiments/PHASE7_PREREGISTRATION.md:4` | 执行/沿用类措辞 | — |
| P6-O3 | **CLOSED** | 7 | `experiments/PHASE7_PREREGISTRATION.md:51` | 执行/沿用类措辞 | — |
| P7-O1 | **CLOSED** | 18 | `experiments/PHASE9_RESULTS.md:1` | 关闭类措辞 | — |
| P7-O2 | **CLOSED** | 14 | `experiments/PHASE9_RESULTS.md:1` | 关闭类措辞 | — |
| P7-O3 | **CLOSED** | 4 | `experiments/PHASE8_PREREGISTRATION.md:5` | 执行/沿用类措辞 | — |
| P8-O1 | **CLOSED** | 27 | `M2A_FINAL_REPORT.md:538` | 关闭类措辞 | — |
| P8-O2 | **CLOSED** | 15 | `M2A_FINAL_REPORT.md:538` | 关闭类措辞 | — |
| P8-O3 | **CLOSED** | 1 | `M2A_PROGRAM_PLAN.md:118` | 关闭类措辞 | — |
| P9-O1 | **CLOSED** | 15 | `M2A_FINAL_REPORT.md:575` | 关闭类措辞 | — |
| P9-O2 | **CLOSED** | 10 | `M2A_FINAL_REPORT.md:575` | 关闭类措辞 | — |
| P9-O3 | **CLOSED** | 6 | `M2A_FINAL_REPORT.md:601` | 关闭类措辞 | — |
| P10-O1 | **CLOSED** | 16 | `M2A_FINAL_REPORT.md:613` | 关闭类措辞 | — |
| P10-O2 | **CLOSED** | 9 | `M2A_FINAL_REPORT.md:613` | 关闭类措辞 | — |
| P10-O3 | **CLOSED** | 5 | `M2A_FINAL_REPORT.md:607` | 关闭类措辞 | — |
| P11-O1 | **CLOSED** | 32 | `experiments/PHASE23_RESULTS.md:34` | 关闭类措辞 | — |
| P11-O2 | **SUCCEEDED** | 16 | `M2A_FINAL_REPORT.md:694` | 转手类措辞 | P13-O1 |
| P11-O3 | **CLOSED** | 13 | `experiments/PHASE13_RESULTS.md:28` | 关闭类措辞 | — |
| P12-O1 | **SUCCEEDED** | 16 | `experiments/PHASE15_RESULTS.md:33` | 转手类措辞 | P13-O2 |
| P12-O2 | **CLOSED** | 11 | `experiments/PHASE13_RESULTS.md:10` | 关闭类措辞 | — |
| P12-O3 | **CLOSED** | 27 | `experiments/PHASE23_RESULTS.md:34` | 关闭类措辞 | — |
| P13-O1 | **CLOSED** | 24 | `experiments/PHASE14_RESULTS.md:23` | 关闭类措辞 | — |
| P13-O2 | **CLOSED** | 31 | `M2A_FINAL_REPORT.md:738` | 关闭类措辞 | — |
| P14-O1 | **CLOSED** | 47 | `experiments/PHASE18_RESULTS.md:19` | 关闭类措辞 | — |
| P15-O1 | **OPEN** | 10 | `M2A_FINAL_REPORT.md:855` | 开放类措辞 | — |
| P16-O1 | **CLOSED** | 11 | `M2A_FINAL_REPORT.md:806` | 执行/沿用类措辞 | — |
| P17-O1 | **CLOSED** | 10 | `experiments/PHASE18_PREREGISTRATION.md:1` | 关闭类措辞 | — |
| P19-O1 | **CLOSED** | 14 | `experiments/PHASE20_RESULTS.md:64` | 关闭类措辞 | — |
| P20-O1 | **CLOSED** | 16 | `experiments/PHASE21_RESULTS.md:61` | 关闭类措辞 | — |
| P21-O1 | **CLOSED** | 13 | `experiments/PHASE22_RESULTS.md:64` | 关闭类措辞 | — |
| P22-O1 | **CLOSED** | 10 | `M2A_FINAL_REPORT.md:945` | 关闭类措辞 | — |
| L01-O1 | **OPEN** | 11 | `literature/ROUND_L01_DISPOSITIONS.md:15` | 开放类措辞 | — |
| L01-O2 | **CLOSED** | 13 | `literature/ROUND_L01_DISPOSITIONS.md:9` | 关闭类措辞 | — |
| L01-O3 | **CLOSED** | 4 | `literature/ROUND_L01_DISPOSITIONS.md:11` | 关闭类措辞 | — |
| L01-O4 | **CLOSED** | 7 | `literature/ROUND_L01_DISPOSITIONS.md:13` | 关闭类措辞 | — |
| L01-O5 | **CLOSED** | 25 | `literature/ROUND_L01_DISPOSITIONS.md:17` | 关闭类措辞 | — |
| L02-O1 | **OPEN** | 5 | `literature/ROUND_L02_RESULTS.md:122` | 开放类措辞 | — |
| L02-O2 | **OPEN** | 5 | `literature/ROUND_L02_RESULTS.md:124` | 开放类措辞 | — |
| L03-O1 | **OPEN** | 12 | `literature/ROUND_L03_RESULTS.md:93` | 开放类措辞 | — |
| O-01 | **OPEN** | 7 | `08_OPEN_QUESTIONS.md:7` | 开放类措辞 | — |
| O-02 | **OPEN** | 1 | `08_OPEN_QUESTIONS.md:9` | 开放类措辞 | — |
| O-03 | **OPEN** | 20 | `08_OPEN_QUESTIONS.md:11` | 开放类措辞 | — |
| O-04 | **OPEN** | 1 | `08_OPEN_QUESTIONS.md:13` | 开放类措辞 | — |
| O-05 | **OPEN** | 1 | `08_OPEN_QUESTIONS.md:15` | 开放类措辞 | — |
| O-06 | **OPEN** | 9 | `08_OPEN_QUESTIONS.md:20` | 开放类措辞 | — |
| O-07 | **OPEN** | 11 | `08_OPEN_QUESTIONS.md:22` | 开放类措辞 | — |
| O-08 | **OPEN** | 1 | `08_OPEN_QUESTIONS.md:24` | 开放类措辞 | — |
| O-09 | **OPEN** | 2 | `08_OPEN_QUESTIONS.md:26` | 开放类措辞 | — |
| O-10 | **OPEN** | 1 | `08_OPEN_QUESTIONS.md:31` | 开放类措辞 | — |
| O-11 | **OPEN** | 2 | `08_OPEN_QUESTIONS.md:32` | 开放类措辞 | — |
| O-12 | **OPEN** | 5 | `08_OPEN_QUESTIONS.md:34` | 开放类措辞 | — |
| O-13 | **OPEN** | 3 | `08_OPEN_QUESTIONS.md:39` | 开放类措辞 | — |
| O-14 | **OPEN** | 8 | `08_OPEN_QUESTIONS.md:41` | 开放类措辞 | — |
| O-15 | **OPEN** | 16 | `08_OPEN_QUESTIONS.md:43` | 开放类措辞 | — |
| O-16 | **OPEN** | 7 | `08_OPEN_QUESTIONS.md:67` | 开放类措辞 | — |
| O-17 | **OPEN** | 13 | `08_OPEN_QUESTIONS.md:81` | 开放类措辞 | — |

---

**计数**：CLOSED 34 / SUCCEEDED 2 / OPEN 23 / UNCLASSIFIED 0，共 59 条标签。命名空间分布：实验轮 `P<n>-O<m>` 34 条、文献轮 `L01-O<m>` 5 条、开放问题 `O-<nn>` 17 条。

## 仍开放（每条都必须带登记原因；缺原因即构建失败）

- **P5-O3**：三个以上独立系统的跨域复验——真实数据未授权；owner 2026-10-18 第 3 条裁定「继续停留在设计阶段」。
- **P15-O1**：`e₁` 只给单侧界。**已裁定**保留单侧界（owner 第 2、7 条），不得改目标函数制造双侧结论 ⇒ 本条作为「双侧估计」的诉求已放弃，但作为「双侧可识别」的证据缺口仍在册。**注意**：owner 第 2 条要求的 `PARTIALLY_IDENTIFIED` 状态字目前只写在治理文档与累计报告里，`experiments/PHASE15_RESULTS.md` 与 `phase15_results.json` 均为 0 次命中，口径表 v2 的扫描已证实（X-74 / `M2A_FINAL_REPORT.md` §37.5）⇒ 「按 `PARTIALLY_IDENTIFIED` 记录」这一半**尚未落在承载判定的工件里**；旧轮文档不回写（R6、第 8 条），补法是本条的下一轮在新结果 JSON 里直接带该字段。

- **L01-O1**：注册层 R13/R14 标注与全文读数的分歧：升为全文级须由一次带**新判据**的轮次决定，不在本轮权限内。`registry.json` 仍 0 条 FULLTEXT（第 8 条禁止回写）。

- **L02-O1**：本轮 Q1 / Q2 与 L-01 共用同一批读数，按 §6 只有否证地位、确证地位为零 ⇒ 要取得确证须换语料并把判据先于读数注册（`ROUND_L02_RESULTS.md` §8）。
- **L02-O2**：表征层定义侧未编码：锥的维度与 `RCO` 收敛条件落在被剥离的数学行上，本轮按预注册不予编码（`ROUND_L02_RESULTS.md` §5、§8）。

- **L03-O1**：K7 的全文级编码与 L-01 摘要级 claim 在时间形态（120 min 内快速下降 vs 离散相位反转）与 avoidance 的作用域（相对 CS− 的 safety memory vs CS+ 的绝对回避）上不同；差异只写入 `L03_coding.json` 与 `ROUND_L03_RESULTS.md`，不回写 L-01（R6）。

- **O-01**：K4 协同族单薄：Phase I′ 补入 7 条后仍为 3/8，缺口已被改判为**结构性**而非检索性（`M2A_FINAL_REPORT.md` §2 第 3 条）⇒ 检索建议已执行，条目诉求（取得因果级协同证据）未达。
- **O-02**：K10 角色重排族单薄：由 2/8 升到 4/8，说明缺口**部分**是检索造成的，方向仍一半混合 ⇒ 未闭合。
- **O-03**：K9 在物理化学层零覆盖：工作假设「省略需表征系统」仍未获得无表征系统中的反例 ⇒ 开放。
- **O-04**：非英语学术传统未覆盖（现象学行动理论、日文行动论、中文知行哲学）：全库 106 条均为英文载体 ⇒ 开放。
- **O-05**：法学实证未覆盖：G7-07（Hart）仅为概念基线，合规行为研究缺位 ⇒ 开放。
- **O-06**：设计已交付（`report/O06_MOTION_SOURCE_DESIGN.md`：四格决策表 + D1–D4 观测量 + 判别力自检），但条目原意为「仅设计，不实施」，其**裁定**仍需真实数据或人体/动物实验，章程 §0.2.5 未授权 ⇒ 开放。
- **O-07**：AGGREGATE 的本体地位：owner 第 5 条把它暂定「派生聚合表示」并写入词表 v1 标 `PROVISIONAL`，`report/MECHANISM_VOCABULARY_v1.md` 明确「没有替 owner 决定本体问题」⇒ 措辞可用、推论受限，本体问题开放。
- **O-08**：习惯的行动地位已按「描述相对性」程序化处理，但批量标注所需更细的分描述判定流程未建 ⇒ 开放。
- **O-09**：双稳态数学分类：K7 内部至少含鞍结分岔/亚稳切换/振荡三类，当前 K 族粒度不足以区分，子标签未设 ⇒ 开放。
- **O-10**：结构化检索缺失：升级系统综述时才补 PRISMA-S 全项，本轮未做 ⇒ 开放。
- **O-11**：全文编码缺失：L-01 已对 3 锚点 + 14 邻域做全文编码（42 条逐字引文），仍低于条目建议的 20–30 条核心子集，且三簇全部判 `INDETERMINATE` ⇒ 「校准 K 族标注」的目标未达成，本条保持开放。
- **O-12**：量化合成未做：现有计票是**记录数**的方向性票，不是效应量；跨域合并被明确禁止（`literature/PRELIMINARY_CONCLUSIONS_V2.md` §3）⇒ 开放。
- **O-13**：核验级别升级路径：owner 第 4 条已**执行**建议的优先级子集（R13/G5-03/R14），但条目要求的「升级预算与全库优先级」未定，且 `registry.json` 仍 0 条 FULLTEXT ⇒ 开放。
- **O-14**：DROPPED-CANDIDATE 复池：owner 第 5 条把复核人指派给独立审查 Agent（三条候选 Wald 1949 / Waddington 1957 / Redgrave 1999 需双源题录），复池审查本身未做 ⇒ 开放，且不在本 Agent 的 §2 范围内。
- **O-15**：词表治理：v1 草案已交付（`report/MECHANISM_VOCABULARY_v1.md`，owner 第 5 条的 Agent 通道），但版本化治理流程与责任人决定未落地，`AGGREGATE` 仍为 `PROVISIONAL`，且推导器查出的方向列拼写漂移（X-70）只登记未清洗 ⇒ 开放。
- **O-16**：判别力审计推广（初为 15 台门控 / 19 个注入变异，`M2A_FINAL_REPORT.md` §40；§41 已推广到 25 台 / 33 个）暴露的两条仪器段要求（X-77）：闭式 `predicted` 被移 1e-4 后门控全绿且 `rel_diff` 无人读取；W2 的「一个计数」容差与 Y2 的网格半步 0.0050 使小于一个晶格步的机制错误原理上不可见。⇒ 两条要求**须先写入下一轮预注册的仪器段才可执行**，本轮不替下一轮定判据（owner 第 3 条未授权新一轮），故开放。
- **O-17**：同一次推广（§41、X-79）暴露的另两条：Phase VIII 的 `J5` 写的是 `rho_exact(0.6) == rho_exact(0.6)`，注入 1e-1 偏移使读数由 154.664 变到 170.130，门控 6 档仍全绿——该条不存在可证伪输入；Phase V-b 的门控 `import gap_for` 却从未调用它。⇒ 要求「每条数值检查写明可证伪输入、纯确定性自检不计入仪器条数、import 而未调用的机制函数要么补检查要么删导入」，**须先写入下一轮预注册的仪器段才可执行**，本轮不回写旧轮门控与其 n/n 记录（R6、第 8 条），故开放。本条要求的静态普查已交付：`governance/build_coverage_map.py`（覆盖表 v1，`gate_coverage_map_gate.py` 18/18）给出 26 台门控 / 81 个导入仪器 / 10 条缺口名单；名单是处置的前提，处置本身仍属下一轮，故本条不因交付而关闭。§45 追加：那 10 条名单已在治理层各配到至少一条带可推翻输入的检查（`unmeasured_instruments_gate.py` 25/25，`rho_exact` 由两台闭式夹逼、`gap_for` 由解析律 1 − sⁿ 约束），但这改变的只是「是否存在一台仪器」；本条要求的是**轮次判据层**写明可证伪输入并停止把纯确定性自检计入仪器条数，仍须由下一轮预注册承接 ⇒ 保持 OPEN。

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
