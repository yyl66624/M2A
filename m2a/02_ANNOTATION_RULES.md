# 02 标注规则与案例记录契约（冻结）

## 2.1 标注决策规则

1. **描述相对性**：行动判定必须先写明"under which description"（G7-01 判据），
   无描述的行动标注无效。
2. **近因/远因分离**：机制标注仅限近因（mechanism 层）；功能/演化解释单独挂 K12 并注明
   Tinbergen 层级（G3-06），不得与近因混标。
3. **双轴分离**：D 轴与 V 轴独立判定；一条机制可同时 D+ 而 B−（例：奖励黑客 G5-04）。
4. **多族并标**：一个案例可挂多个 K 族，但须注明主族（第一个）与辅族。
5. **类比降级**：跨域结构相似但无共享因果机制者，主张类型只许 MATHEMATICAL_ANALOGY 或
   M2A_HYPOTHESIS，禁止升为 SUPPORTED_MECHANISM（章程 §0.2-2）。
6. **反证并挂**：存在公开反驳文献的机制（如 G5-03、G7-06），标注时须同时挂入
   07_CONTRADICTIONS 登记册编号。
7. **核验级别封顶**：标注不得超出文献的核验级别；IDENTITY_VERIFIED 条目只做机制
   结构性分析，不做定量主张。

## 2.2 YAML 案例记录契约（每条案例必填字段）

```yaml
case_id: M2A-G?-NN
reference: R##/G#-##
verification_level: IDENTITY_VERIFIED|ABSTRACT_VERIFIED|FULLTEXT_REVIEWED|CLAIM_INDEPENDENTLY_CHECKED
evidence_type: formal_theorem|causal_intervention|observational|simulation|interpretive|analogy
provenance: PAPER_CLAIM|M2A_HYPOTHESIS|SUPPORTED_MECHANISM|MATHEMATICAL_ANALOGY|REFUTED_CLAIM
description_scope: <本案例行动判定所依赖的描述>
motion_source: <L 层 + 物理载体>
mechanism: [{k: K#, role: primary|auxiliary, d_axis: D+|D−|neutral, v_axis: B+|B−|neutral}]
layers: [L#...]
agency_class: AGENTIC|RESPONSIVE|MIXED
event_grammar: "[MOTION]-->[GATE]-->[ACTION/INACTION]-->[OUTCOME]-->[FEEDBACK]"
contradiction_ref: <07-编号或 null>
```

## 2.3 冲突解决

标注分歧以"更保守的声称"为准（charter 0.2-1/-2/-3）；无法保守解决则挂 UNCERTAIN 并列入
08_OPEN_QUESTIONS.md。
