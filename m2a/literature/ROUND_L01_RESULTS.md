# Round L-01 结果｜R13 / G5-03 / R14 全文机制编码 + 独立核验 + 竞争理论比较

> 日期：2026-10-18 ｜ 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 4 条与 §2 第 1 项
> 判据登记：`literature/L01_CODING_PROTOCOL.md`（SHA-256 `7e590b1d643dcba7…`，**先于编码落盘**）
> 产物：`L01_candidates.json` → `L01_fulltexts.json` → `L01_verification.json` → `L01_channels.json`
> → `L01_coding.json`；仪器：`l01_gate.py`（7/7）｜运行器：`run_L01.py`（门控不过即拒跑）
> 本轮不重跑任何实验、不改写任何历史判定（R6）、不触碰 `assets/`、412 行账本与既有预注册（第 8 条）。

## 1 一句话结论

**14 篇全文全部可编码，但没有一个锚点达到注册阈值** ⇒ 三簇判定均为 `INDETERMINATE`；
同时本轮暴露五处仪器/协议缺陷（其中三处是我自己的），并把 C-04 的「降权」裁定**加强**而非放松。

## 2 五值标签表（R17，逐条对回 `L01_coding.json`）

| 锚点 | m（可编码邻文献） | C 严格 / C 带符号 | R | 支持阈值 ⌈2m/3⌉ | 本轮标签 | 依据出口 |
| --- | --- | --- | --- | --- | --- | --- |
| R13（延迟摄入后反馈，K5） | 6 | 2 / 2 | 1 | 4 | **INDETERMINATE** | §5 出口 4（`1 ≤ C < ⌈2m/3⌉`） |
| G5-03（拒绝单方向，K2） | 4 | 2 / 2 | 0 | 3 | **INDETERMINATE** | §5 出口 4；`C` 是**上界**（见 §6 L01-D3） |
| R14（奖励间隔控学习率，K5） | 4 | 2 / 1 | 0 | 3 | **INDETERMINATE** | §5 出口 4；两种中性口径读法同标签 |
| **整轮** | 14 / 14 | — | — | 停线 10 | **INDETERMINATE** | 停线未触发（14 ≥ 10），故不扩池、不换锚点 |

没有一簇触发 `CONTRADICTED`（R 最大为 1），也没有一簇触发 `SUPPORTED`。
`NULL` 亦不成立：三簇各有 ≥1 篇同号同族命中，故只能落在 `INDETERMINATE`。

## 3 编码层读数（17 条，全部带逐字引文 + 字符下标）

| sid | 主族 | d_class | term_type | 级别 | 相对锚点 |
| --- | --- | --- | --- | --- | --- |
| R13（锚，缓存全文=bioRxiv/PMC 作者稿） | K5 | D− | PAPER_TERM | QUALIFIED | 与注册表 `value-only` 冲突（§5） |
| R13-N2 迷走/恶心通路 | K2（辅 K5/K8） | D− | MIXED | FULLTEXT_REVIEWED | 族不同、K5 辅条目同号 |
| R13-N3 内感受能量异稳模型 | K5（辅 K6/K11） | mixed | MIXED | FULLTEXT_REVIEWED | **同族反号**（预期启动行动，非压制）＝唯一 R |
| R13-N8 食物恐惧→食物自由 | K5（辅 K2/K6） | D− | MIXED | FULLTEXT_REVIEWED | 同族同号（引用锚点） |
| R13-N15 果蝇内脏信号→记忆更新 | K5（辅 K7/K10） | mixed | PAPER_TERM | **ABSTRACT_VERIFIED** | 端点仅返回 bioRxiv 预览页（5 370 字符），非全文 |
| R13-N16 GIP 受体激动→炎症性厌食 | K2（辅 K4/K5） | D+ | MIXED | FULLTEXT_REVIEWED | 族不同、K5 辅条目反号（引用锚点） |
| R13-N17 肠—心与奖赏加工 | K11（辅 K1/K5） | mixed | MIXED | FULLTEXT_REVIEWED | 族不同、K5 辅条目同号（引用锚点） |
| G5-03（锚） | K2 | D− | MAPPING | FULLTEXT_REVIEWED | — |
| G5-03-N1 窄任务微调→广义失准 | K1（辅 K8） | D+ | MIXED | FULLTEXT_REVIEWED | 族不同；正文赞同并沿用单方向结果 |
| G5-03-N2 自我伤害类越狱 | K2（辅 K1） | mixed | MIXED | FULLTEXT_REVIEWED | 同族同号（行为层，不测方向） |
| G5-03-N4 AVA 政策 RAG 现场研究 | K9（辅 K1） | D− | PAPER_TERM | FULLTEXT_REVIEWED | 族不同；弃权被**工程化到系统层**，无内部方向 |
| G5-03-N6 拒绝的非线性视角 | K2（辅 K4） | D− | MAPPING | FULLTEXT_REVIEWED | **主张层反证**（拒绝非单方向）⇒ `contradiction_ref = C-04` |
| R14（锚，缓存全文=preprint v2 题名不同） | K5（辅 K6） | value-only | PAPER_TERM | QUALIFIED | 直接支持「间隔而非次数」 |
| R14-N1 中纹状体多巴胺与线索—奖赏或然性 | K2（辅 K5） | D− | MIXED | FULLTEXT_REVIEWED | 不测间隔主张（间隔与奖赏率被固定） |
| R14-N4 光纤维度试验级统计框架 | K5 | value-only | MAPPING | FULLTEXT_REVIEWED | 方法学仪器，既不支也不反 |
| R14-N7 重新概念化的联想学习 | K5（辅 K2/K10） | mixed | MIXED | FULLTEXT_REVIEWED | 同族反号：以信息量/C-T 而非 ITI  govern，并否认 eligibility trace |
| R14-N8 边缘多巴胺斜坡反映环境时间尺度 | K5（辅 K2/K10） | value-only | MIXED | FULLTEXT_REVIEWED | 同族同号，但**与锚点同实验室** ⇒ 非独立 |

**独立性登记（仪器只报告，不剔除）**：`l01_gate.py` G6 检出 3 篇邻文献正文含锚点题名/DOI
（R13-N3、R13-N16、R13-N17），R13-N8 亦引用锚点；R14-N8 与 R14 作者重叠。
⇒ R13 的 `C = 2` 中至多 1 篇可算独立命中；本轮阈值按注册口径计，不做事后剔除，但**下一轮的比较须带此限定**。

## 4 独立核验（第 4 条「独立核验」项）

| 通道 | 读数 | 说明 |
| --- | --- | --- |
| 第一通道（选择用） | OpenAlex | 池 R13 28 / G5-03 32 / R14 27，逐条拒绝原因已入库（12 / 0 / 12 条），R13、R14 各有 **48 条参考文献未查**（API 负载上限，已登记不静默丢弃） |
| 第二通道 | Crossref / PubMed | **严格口径 14/17 `VERIFIED_TWO_CHANNEL`**；3 条例外逐条定名：`R14-N4`、`R14-N8` 标题 overlap 1.0 而年份 2024 vs 2025（两通道取的是**不同日期字段**），`G5-03` 锚点 `10.48550/arXiv.*` 在 Crossref 404 |
| 第三通道（订正 L01-A2） | arXiv API | `G5-03` 锚点 **`VERIFIED_THIRD_CHANNEL`**：题名 overlap 1.0、2024、第一作者 Andy Arditi、`arxiv.org/abs/2406.11717v3` |
| 全文绑定 | 42 条引文逐字复核 | 每条 `text[off:off+len(quote)] == quote` 且 `sha256(quote)[:16]` 相符，**0 例改写、0 例偏移漂移**；17 份全文 sha256 与 `L01_fulltexts.json` 逐一相符 |

年份口径**未放宽**：14/17 这个读数原样保留，两条 2024/2025 差异只补诊断字段，不改标签。

## 5 编码层与注册层的分歧（不回写，R6）

`registry.json` 现行 R13 行：`d_class = value-only`、级别 `ABSTRACT_VERIFIED`、B+「价值学习」。
全文读数是**行动方向主张**（一次配对即学会拒食被配对风味，且按 `01` §1.4 定义该线索价值下降）
⇒ 本轮编码为 `D− / B−` 并把该锚点标 `QUALIFIED`。**注册表一字未改**（§6 追加制、第 8 条），
分歧登记为开放项 **L01-O1**：是否把 R13 的注册层标注升为全文级，须由一次带新判据的轮次决定，
而不是由本轮的编码文件决定。

## 6 缺陷与订正登记

| 编号 | 内容 | 处置 |
| --- | --- | --- |
| **L01-A1** | 竞争理论走独立通道，不并入引用排名池 | OpenAlex 检索返回 **0 命中**（首版判为 `NOT_OBTAINED`），改走 arXiv API 后取得：Wollschläger et al. 2025《The Geometry of Refusal in LLMs: Concept Cones and Representational Independence》，overlap 1.0，`2502.17420v2` ⇒ `OBTAINED_THIRD_CHANNEL` |
| **L01-A2** | 第二通道 404 的记录改走第三通道（见 §4） | 已执行，读数入库 `L01_channels.json` |
| **L01-A3** | 竞争理论选择器首版只按关键词 `concept cone` 命中，挑中的是**另一篇**同名不同题的论文（Rocchi/Fel/Franchi《A Geometric Unification of Concept Learning with Concept Cones》） | 在任何判定写下之前改为按 C-04 登记的**完整题名**匹配；首版工件保留在 `L01_channels.json.superseded_first_attempt` 供审计 |
| **L01-D1** | 编码文件混用 `D-`（ASCII）与 `D−`（协议用字），同一枚举两个拼写 | 统一为协议拼写（10 个文件、20 个字段），**未改任何读数**；门控 G5 现会拒绝拼写漂移 |
| **L01-D2** | R14-N1 与 G5-03-N4 被我给的**任务书题名**判成 QUALIFIED，而两份已登记工件的题名与之不同——错在我给的任务书，不在论文 | 对已注册工件重核身份（两通道一致、overlap 1.0）后恢复 `FULLTEXT_REVIEWED`，`identity_check`/`notes` 均写明来源；登负面日志 X-69 |
| **L01-D3** | §5 的一致性判据只看「族 + 符号」，看不到主张层反证：G5-03-N6 主张拒绝**不是**单方向，却因列 K2/D− 为 primary 而被计入 `C` | 不事后改判据。本轮把 G5-03 的 `C = 2` 明确写作**上界**，主张层读法（`C = 1`）同表并列；判据级修订留给 **L01-O2** |
| **L01-D5** | §2 要求逐字沿用 `02` §2.2 的字段集，其中含 `layers[]`；但我交给编码步骤的 schema **漏了该字段**，而门控的必填字段循环**也没查它** ⇒ 这个缺口原本会静默通过 | 恢复方式是确定性的而非补写主张：`layers` 取各记录 `motion_source` 里**已经写下的** L 记号集合，门控现对「不在载体描述里的层」直接判失败。§5 出口不读 `layers`，故判定不受影响；17 条层用量 L3 13 / L4 6 / L2 5 / L1 5 / L0 3 / L5 2 / L6 1 已入 `L01_coding.json.vocabulary_usage` |

## 7 竞争理论比较（第 4 条第三项）

- C-04 已登记：G5-03 的样本仅 13 个 RLHF/DPO 开源模型，Wollschläger 等以「概念锥 + 表征独立性」质疑单方向性。
- 本轮 4 篇邻文献中，**N6 与 C-04 同向**（拒绝为非线性/多维），N1 与锚点同向，N2 在行为层支持「门可被越狱」但不测方向，
  N4 把弃权做成系统层工程（既不支持也不反驳内部方向）。
- Wollschläger 原文**未进入引用排名池**，故本轮只取得其身份级读数（题名/年份/作者/编号），**未做全文编码**；
  ⇒ 登记 **L01-O4**：竞争理论全文编码须另开一轮（L-02），并预先规定「反证与正证同表计票」的口径。
- 对 C-04 裁定的影响：**维持降权（`PAPER_CLAIM + REFUTED_CLAIM(部分)`），并新增一条限定**——
  「单方向」主张在本轮 4 篇独立全文中没有获得可判支持。G5-03 的 ◐ 标记不变。

## 8 本轮不改变的东西

1. `registry.json`（106 条）、`synthesis_v2.json`、`SYNTHESIS_V2.md`、`expansion_registry.*` 一字未改；
2. Phase I′ 闸门①②③判定与 `PHASE1PRIME_STATUS.md` 读数不变（本轮产物另库登记）；
3. `07_CONTRADICTIONS` C-04 裁定、`06` 各 B 条判定级别不变；
4. 各实验轮判定与预注册哈希不变；新增套件接入收尾审计后须重新出具 `n/n`（见 `M2A_FINAL_REPORT.md` §15）。

## 9 下一轮（L-02）前置，按序

1. **L01-O1** 注册层 R13/R14 标注与全文读数的分歧处置（需新判据，不在本轮权限内）；
2. **L01-O2** 把一致性判据从「族 + 符号」改为「族 + 符号 + 主张层关系（支持/扩展/反证/无关）」，
   **先注册后跑**，并对本轮 17 条做零检验地位的重判读（不重跑、不改原工件，R6）；
3. **L01-O3** 在注册时决定 `neutral` 轴的零值处理（与纪律规则 R14 同形：零值既不表示无偏差，也不能当界）；
4. **L01-O4** Wollschläger 等《Concept Cones》全文编码 + 与 G5-03-N6 的正/反证同表计票；
5. **L01-O5** R13-N15 全文仍不可得（预览页 5 370 字符，403/无全文）⇒ 按 `ANNOTATION_ADDENDUM` 增补 3 保持原级别，
   不得以摘要冒充全文；
6. 台账口径缺口：`build_obligation_registry.py` 的标签式只覆盖 `P<n>-O<m>`，本轮 `L01-O*` 不在其推导范围内
   ⇒ 属可复现性缺陷，登记待修（与 X-67 同源：处置必须写在承载判定的工件里）。

## 10 复现

```bash
python3 literature/l01_gate.py     # 仪器：7/7 checks passed
python3 literature/run_L01.py      # 门控不过即拒跑；重写 L01_coding.json（内嵌协议哈希）
python3 experiments/audit_bindings.py   # 收尾审计：套件与预注册哈希双口径
```
全文文本在仓库外 `workshop/_m2a_ft/`（第三方文本不入库），仓库内只存哈希、长度与逐字引文下标。
