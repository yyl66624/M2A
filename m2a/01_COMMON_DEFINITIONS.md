# 01 共同定义（Common Definitions，冻结）

> 依据框架 v0.2 §2–§3；Phase I 使用中的一切标注以本文件为准。

## 1.1 基础词汇

- **Motion（运动）**：系统中可观测的状态变化或其倾向，不含"意图""价值"预设。
  例：肌肉收缩、力施加、token 生成、信号分子浓度上升、投票行为。
- **Action（行动）**：在某一**描述**下归属于行动者、并进入评价/因果/规范网络的 motion。
  （Anscombe 判据，G7-01：行动是"under a description"的概念；不同描述下同一 motion 可为行动或不为行动。）
- **Agency class（机构类别）**：
  - AGENTIC：motion 来源于内部模型/意图/策略（人或人工行动者的大多数行动）。
  - RESPONSIVE：motion 是对外部刺激/信号的响应（反射、信号转导、触发词激活）。
  - MIXED：两者交织（习惯、制度行为、RLHF 后的语言模型行为）。

## 1.2 十二机制族（K1–K12）

K1 触发（threshold/trigger）｜K2 抑制/门控（inhibition/gate）｜K3 竞争（competition）｜
K4 协同（synergy/conjunction）｜K5 延迟/记忆（delay/memory）｜K6 反馈（feedback）｜
K7 切换/滞回（switching/hysteresis）｜K8 级联（cascade）｜K9 省略/弃权（omission/abstention）｜
K10 角色重排（role reassignment）｜K11 资源约束（resource constraint）｜K12 选择/适应（selection/adaptation）。

## 1.3 六层（L0–L6）

L0 形式/数学 ｜ L1 物理/化学 ｜ L2 句法/结构 ｜ L3 语义/事件/生理机制 ｜
L4 语用/话语/决策 ｜ L5 叙事/脚本 ｜ L6 社会/制度/演化。

## 1.4 四条件角色（D±/B±）

对候选机制在情景中的条件作用，沿两轴判定：

- **D 轴（行动效果）**：D+ 该条件下 motion→action 更可能发生/更强；D− 更不可能/更弱。
- **V 轴（价值效果）**：B+ 该条件提高 motion/action 对行动者的价值；B− 降低价值。

辅助标记：NEUTRAL_VALUE（D 有效而 V 中性）、MIXED（同机制在不同子条件分裂）、
UNCERTAIN（证据不足判定）。

## 1.5 事件语法模板

```
[MOTION SOURCE] --> [MECHANISM/GATE] --> [ACTION/INACTION] --> [OUTCOME] --> [FEEDBACK]
```

## 1.6 证据类型与主张类型

- 证据类型：formal_theorem ｜ causal_intervention ｜ observational ｜ simulation ｜ interpretive ｜ analogy。
- 主张类型（Provenance）：PAPER_CLAIM（文献自述）｜ M2A_HYPOTHESIS（本框架假设）｜
  SUPPORTED_MECHANISM（有跨源支持）｜ MATHEMATICAL_ANALOGY（仅形式类比，不得计为实证）｜
  REFUTED_CLAIM（已被反驳，登记留存）。
