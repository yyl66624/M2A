# M2A 机制词表 v1（草案，机器推导）

> 版本 `v1.0-draft` ｜ 生成日期 2026-10-18 ｜ 生成脚本 `governance/build_mechanism_vocabulary.py`
> 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 5 条 + §2 第 2 项（`O-15` 的 Agent 通道）。
> **本文件所有数字与词条一律由脚本从已提交工件推导**，手写数字即构建失败。
> 本文件是**新增**治理文件：`01`/`02`/`03`/`06` 与 `literature/registry.json` 一字未改（§5 追加制、第 8 条）。

## 1 十二机制族（01 §1.2 冻结用词 + 实际用量）

| 族 | 中文 | 英文 | Phase I′ 注册表行数 | 其中主族 | L-01 主族 | L-01 辅族 |
| --- | --- | --- | --- | --- | --- | --- |
| **K1** | 触发 | threshold/trigger | 31 | 1 | 1 | 3 |
| **K2** | 抑制/门控 | inhibition/gate | 29 | 6 | 6 | 4 |
| **K3** | 竞争 | competition | 9 | 0 | 0 | 1 |
| **K4** | 协同 | synergy/conjunction | 11 | 6 | 0 | 2 |
| **K5** | 延迟/记忆 | delay/memory | 14 | 0 | 8 | 4 |
| **K6** | 反馈 | feedback | 21 | 0 | 0 | 4 |
| **K7** | 切换/滞回 | switching/hysteresis | 17 | 0 | 0 | 1 |
| **K8** | 级联 | cascade | 14 | 0 | 0 | 2 |
| **K9** | 省略/弃权 | omission/abstention | 15 | 0 | 1 | 0 |
| **K10** | 角色重排 | role reassignment | 9 | 6 | 0 | 3 |
| **K11** | 资源约束 | resource constraint | 28 | 0 | 1 | 1 |
| **K12** | 选择/适应 | selection/adaptation | 9 | 0 | 0 | 0 |

## 2 六层（01 §1.3 / 03 试标）

| 层 | 定义用词 | L-01 记录数 |
| --- | --- | --- |
| **L0** | 形式/数学 | 3 |
| **L1** | 物理/化学 | 5 |
| **L2** | 句法/结构 | 5 |
| **L3** | 语义/事件/生理机制 | 13 |
| **L4** | 语用/话语/决策 | 6 |
| **L5** | 叙事/脚本 | 2 |
| **L6** | 社会/制度/演化 | 1 |

## 3 两轴与辅助标记（01 §1.4）

- **D 轴**：D+ 该条件下 motion→action 更可能发生/更强；D− 更不可能/更弱。
- **V 轴**：B+ 该条件提高 motion/action 对行动者的价值；B− 降低价值。
- 辅助标记：`NEUTRAL_VALUE`（D 有效而 V 中性）；`MIXED`（同机制在不同子条件分裂）；`UNCERTAIN`（证据不足判定）

## 4 机构类别与事件语法（01 §1.1 / §1.5）

- `AGENTIC`：motion 来源于内部模型/意图/策略（人或人工行动者的大多数行动）。
- `RESPONSIVE`：motion 是对外部刺激/信号的响应（反射、信号转导、触发词激活）。
- `MIXED`：两者交织（习惯、制度行为、RLHF 后的语言模型行为）。
- 事件语法：[MOTION SOURCE] --> [MECHANISM/GATE] --> [ACTION/INACTION] --> [OUTCOME] --> [FEEDBACK]

## 5 字段枚举（02 §2.2 冻结案例契约）

| 字段 | 允许值 |
| --- | --- |
| `verification_level` | IDENTITY_VERIFIED \| ABSTRACT_VERIFIED \| FULLTEXT_REVIEWED \| CLAIM_INDEPENDENTLY_CHECKED |
| `evidence_type` | formal_theorem \| causal_intervention \| observational \| simulation \| interpretive \| analogy |
| `provenance` | PAPER_CLAIM \| M2A_HYPOTHESIS \| SUPPORTED_MECHANISM \| MATHEMATICAL_ANALOGY \| REFUTED_CLAIM |
| `d_axis` | D+ \| D− \| neutral, v_axis: B+ \| B− \| neutral |
| `agency_class` | AGENTIC \| RESPONSIVE \| MIXED |

## 6 跨域桥接 id（06，判定逐条读出）

| id | 标题 | 判定 |
| --- | --- | --- |
| B-01 | 触发阈值（K1）：漂移扩散 × 证据累积 × 事件触发词 | ANALOGY-ONLY（偏强） |
| B-02 | 双稳态/滞回（K7）：信号转导 × 卵母细胞 × 社会制度 | ANALOGY-ONLY |
| B-03 | 反馈驱动学习（K6）：RL × 多巴胺 RPE × RLHF × 偏好学习 | VALID-BRIDGE（有条件） |
| B-04 | 抑制门（K2）：T 细胞检查点 × 基底节 no-go × 控制屏障函数 × LLM 拒绝方向 | ANALOGY-ONLY（四实例各自 VALID，桥为类比） |
| B-05 | 扩散级联（K8）：复杂传染 × 弱连接 × 叙事事件链 | VALID-BRIDGE（局部） |
| B-06 | 资源约束（K11）：信息容量 × 耗散功 × 适应负荷 × 满意度化 × 部分可观测 | VALID-BRIDGE（弱统一） |
| B-07 | 延迟与记忆（K5）：时间尺度不变性 × 延迟反馈绑定 × POMDP 信念 × 脚本 | ANALOGY-ONLY |
| B-08 | 省略/弃权（K9）：满意化 × 意向—行为缺口 × 道德风险 × 法律不作为 | VALID-BRIDGE（概念层） |

## 7 AGGREGATE（本轮唯一新增术语，状态 PROVISIONAL）

- owner 裁定用词：**AGGREGATE 暂定为派生聚合表示**
- 原开放项：**O-07｜AGGREGATE 行动的本体地位**：Schelling（G1-04）证明宏观结构可无个体意图
- 许可范围：AGGREGATE may be used as a term of art for macro-patterns that no individual intends; it does NOT license attributing agency, an action, or a value to the aggregate. Any bridge that needs the aggregate to ACT must first clear a round of its own.
- 词表处理：以「派生聚合表示」写入 v1，标 `PROVISIONAL`；`PROVISIONAL` 术语不得进入任何 `SUPPORTED_MECHANISM` 主张（见 §8 第 4 条）。

## 8 版本规则

1. term ids are permanent: K5 stays K5 forever; a retired family is marked DEPRECATED in a new version file, never deleted or renumbered
2. adding/renaming a K family or an L layer requires a new version file (v1.n) plus a hash binding; edits to a frozen 0x file are not the mechanism
3. every emitted count must be re-derivable by this script; a hand-typed number in the generated document is a build failure
4. PROVISIONAL terms (currently only AGGREGATE) may not appear in a SUPPORTED_MECHANISM claim until a round promotes them

## 9 口径漂移表（本轮的主要产出）

`01` §1.4 定义的是 `D+ / D− / NEUTRAL_VALUE / MIXED / UNCERTAIN`；`02` §2.2 写的是 `D+ | D− | neutral`；而 106 行注册表里实际存在的是下面这些拼写。L-01 又引入了第五种（Phase I′ 计票口径 `D+ / D− / mixed / value-only`）。**注册表不回写**（§5、第 8 条），本表是唯一的对齐仪器：

| 观察到的拼写 | 出现次数 | 出处 | 规范含义 |
| --- | --- | --- | --- |
| `D+` | 45 | registry.json (106 rows) | D+ (01 §1.4) |
| `unspecified` | 14 | registry.json (106 rows) | UNCERTAIN (01 §1.4 辅助标记) — no direction claim made |
| `value-only` | 13 | registry.json (106 rows) | NEUTRAL_VALUE (01 §1.4) — 'D 有效而 V 中性' |
| `mixed` | 13 | registry.json (106 rows) | MIXED (01 §1.4 辅助标记) |
| `D-` | 12 | registry.json (106 rows) | D− (01 §1.4) — ASCII hyphen, 12 rows |
| `D±` | 9 | registry.json (106 rows) | MIXED (01 §1.4 辅助标记) — invented in the registry |
| `D−` | 7 | L01_coding.json (17 records) | D− (01 §1.4) |
| `neutral` | 0 | L01_coding.json (17 records) | NEUTRAL_VALUE (02 §2.2 writes the same state as d_axis: neutral) |

- 推导读数：规范拼写 `D−` 在 106 行注册表中出现 **0 次**，ASCII `D-` 出现 **12 次** ⇒ 任何按字符串相等做的方向计票都会把这 12 行与规范拼写分成两类。这与 L-01 的 L01-D1（编码文件混用两种连字符）是**同一形状的缺陷**，区别只在于它已经躺在已提交工件里。
- 计数后果：`D±`（9 行）与 `mixed`（13 行）在 01 §1.4 里是同一个辅助标记 `MIXED`，`unspecified`（14 行）对应 `UNCERTAIN` ⇒ 注册表的方向列实际是 **6 类拼写表达 4 个状态**。

核验级别同样漂移：`IDENTITY_VERIFIED` 104 行、`ABSTRACT_VERIFIED` 2 行，而 L-01 的 17 条里出现 `FULLTEXT_REVIEWED` 14 条、`QUALIFIED` 2 条、`ABSTRACT_VERIFIED` 1 条 ⇒ 注册表的级别字段与全文级读数是**两套口径并存**，引用时须写明是哪一套。

## 10 复现

```bash
python3 governance/build_mechanism_vocabulary.py
python3 literature/l01_gate.py   # 词表的 L-01 用量读数即出自其绑定的 L01_coding.json
```
