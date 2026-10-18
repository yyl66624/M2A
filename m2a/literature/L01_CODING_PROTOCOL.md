# Round L-01 机制编码协议（先注册，后编码）

> 日期：2026-10-18 ｜ 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 4 条（R13 六篇 / G5-03 四篇 /
> R14 四篇的**全文机制编码、独立核验、竞争理论比较**）与 §2 第 1 项（文献研究，产出只写新增文件）。
> 本文件是编码步骤的判据登记处：**写下本文件时，14 篇邻文献的全文已取回、身份已核验，但尚无任何一条
> 机制编码存在**。因此本轮的口径顺序是「取文本 → 注册判据 → 编码」，编码结果不得回写本文件的任何数字。
> 触碰禁令沿用第 8 条：`assets/`、412 条台账、既有 `PHASE*_PREREGISTRATION.md`、PNAS 冻结包一律不写。

## 1 身份与范围

| 项 | 值 |
| --- | --- |
| 轮次名 | Round L-01（文献轮，非仿真轮） |
| 上游工件 | `L01_candidates.json`（池与拒绝表）、`L01_fulltexts.json`（全文哈希/长度/关键词窗）、`L01_verification.json`（第二通道核验） |
| 编码对象 | 决策点名的 **14 篇邻文献**（R13 六篇、G5-03 四篇、R14 四篇）＋ 3 个锚点自身作为对照记录 |
| 全文位置 | `workshop/_m2a_ft/L01_<sid>.txt`（仓库外，第三方文本不入库；仓库内只存哈希与引文） |
| 随机性 | 本轮无随机数、无种子池（检索与编码均为确定性读取）；因此 R4「不相交种子」条款不适用，登记为 N/A |
| 产物 | `literature/L01_coding.json`（内嵌本文件 SHA-256）、`literature/check_l01_coding.py`、`literature/ROUND_L01_RESULTS.md` |

## 2 编码字段契约（逐字沿用冻结的 `02_ANNOTATION_RULES.md` §2.2）

每条记录必填：`case_id`、`reference`、`verification_level`、`evidence_type`、`provenance`、
`description_scope`（无描述的行动标注无效）、`motion_source`、`mechanism[]`（`k`/`role`/`d_axis`/`v_axis`）、
`layers[]`、`agency_class`、`event_grammar`、`contradiction_ref`。

词表取 `01_COMMON_DEFINITIONS.md` 第 18–21 行原样：
K1 触发｜K2 抑制/门控｜K3 竞争｜K4 协同｜K5 延迟/记忆｜K6 反馈｜K7 切换/滞回｜K8 级联｜
K9 省略/弃权｜K10 角色重排｜K11 资源约束｜K12 选择/适应；层取 L0–L6。
方向类标签取 Phase I′ 计票口径四值：`D+` / `D−` / `mixed` / `value-only`。

本轮另加三条（不修改 §2.2，只增补）：

1. **引文可定位要件**：每个 `mechanism` 条目必须带 `quote`（20–400 字符，逐字摘自全文文件）与
   `quote_offset`（该字符串在文件中的字符下标）。门控脚本按字节复核，对不上即判仪器缺陷。
2. **`PAPER_TERM` / `MAPPING` 二分**（`ANNOTATION_ADDENDUM.md` 增补 1）：每条编码标 `term_type`，
   `MAPPING` 须在 `mapping_note` 写出「论文用词 → 我们的映射」这一步。词频只用于定位段落，
   **不得**单独作为机制成立或不成立的证据。
3. **级别封顶**（§2.1-7 与增补 2）：`FULLTEXT_REVIEWED` 要求身份核对 + 可定位机制段落两项同时成立，
   缺任一项写 `ABSTRACT_VERIFIED` 或 `IDENTITY_VERIFIED`；与标注冲突的记 `QUALIFIED` 并写明冲突点，
   不得静默保留原标注。

## 3 竞争理论比较（决策第 4 条第三项）

- G5-03 组的竞争理论为 `07_CONTRADICTIONS_AND_COUNTEREVIDENCE.md` 已登记的 V-04 式批评
  （Wollschlager et al. 2025 "Concept Cones"），走**独立通道**取回，标注
  `competing_theory_channel_L01_A1`，**不并入引用排名池**（避免用同一条排名既选证据又选反证）。
- 取回失败时如实记 `NOT_OBTAINED`，该比较项按 R17 打 `NULL` 标签，不得以「池中没有」代替「未比较」。

## 4 独立核验的口径（本轮固定，不看结果再改）

`L01_verification.json` 已给出严格口径读数 **14/17 `VERIFIED_TWO_CHANNEL`**。三条例外逐条定名处理，
不做任何全表放宽：

| 记录 | 严格口径 | 本轮登记 |
| --- | --- | --- |
| `R14-N4`、`R14-N8` | `SECOND_CHANNEL_MISMATCH`（标题 overlap 1.0，年份 OpenAlex 2024 vs Crossref 2025） | 保持 MISMATCH 标签，另记诊断字段 `year_channel_note`：两通道取的是**不同日期字段**（venue 首发 vs 版本刊发）。身份结论以 overlap 为准，年份不进本轮判据 |
| `G5-03` 锚点 | `SECOND_CHANNEL_ERROR`（`10.48550/arXiv.*` DOI 在 Crossref 返回 404） | 走**第三通道** arXiv API（`export.arxiv.org/api/query`）复核，结果记 `third_channel` 字段；Crossref 读数原样保留 |

**登记为订正 L01-A2**：本条只改「例外如何登记」，不改 overlap/年份读数本身，也不改 14/17 这个数字。

## 5 出口表（每锚点独立判定，按序取第一个可触发项）

记 `m` = 该锚点下**可编码**（含 ≥1 条带引文 mechanism 条目）的邻文献数，
`C` = 其中主族命中该锚点主 K 族且 `d_axis` 同号的篇数，`R` = 与锚点主族同族但 `d_axis` 反号且自身把该族列为 primary 的篇数。

| 顺序 | 出口 | 条件 | 标签（R17 五值） |
| --- | --- | --- | --- |
| 1 | `CONTRADICTED` | `R ≥ 2` | 锚点的机制主张在全文级被邻文献反向证据推翻 |
| 2 | `SUPPORTED` | `m ≥ 3` 且 `C ≥ ⌈2m/3⌉` | 全文级支持（只支持「机制在该簇内可编码」，不支持跨域迁移） |
| 3 | `NULL` | `m ≥ 3` 且 `C = 0` | 零结果：可编码但无一命中 |
| 4 | `INDETERMINATE` | `1 ≤ C < ⌈2m/3⌉` 或 `m = 3` 以下的非零情形 | 未决定性 |
| 5 | `NOT_IDENTIFIED` | `m ≤ 2` | 部分识别：全文不足，锚点结论停留在摘要级 |

**整轮停线**：若 14 篇中可编码总数 `< 10`，本轮整体记 `NOT_IDENTIFIED`，
**不得**扩池、**不得**换锚点、**不得**降低引文字数要件来凑数。此后只登记，不再补跑。

## 6 本轮不做什么

1. 不新增任何真实数据统计分析、不跑新实验、不做跨系统复验实施（第 1/3 条）；
2. 不改 `literature/registry.json`、`SYNTHESIS_V2.md`、`expansion_registry.*` 等既有产出（§5 追加制）；
3. 不把编码结果升为 `SUPPORTED_MECHANISM` 之外的跨域主张；类比一律 `MATHEMATICAL_ANALOGY` /
   `M2A_HYPOTHESIS`（§2.1-5）；
4. 编码完成后本文件一字不改；发现缺陷只登记 `L01-A<n>` 或负面日志（R6）。

## 7 本文件 SHA-256

（落盘后由 `check_l01_coding.py` 读取并写入 `L01_coding.json` 的 `protocol_sha256` 字段；
双口径校验：磁盘字节与 `git show HEAD:literature/L01_CODING_PROTOCOL.md` 对象，见 R-workshop 行尾规则。）
