# 五值识别状态标签 × 既有台账/报告 口径表 v2

> 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 7 条与 §2 第 3 项。生成器：
> `governance/build_status_label_table.py`（机器可读版 `governance/status_label_table_v2.json`）。
> **本表是翻译层，不是改写层**：`experiments/phase*.json`、各 `PHASE*_RESULTS.md`、
> 412 行账本与 PNAS 冻结包一字未动（R6、第 8 条）。引用旧轮的五值标签时，按本表取
> `label` 列，并同时给出 `raw` 列的原文，以免翻译被当成原始判定。

## 1 为什么要翻译层

第 7 条要求每轮区分 `SUPPORTED / CONTRADICTED / NULL / INDETERMINATE / NOT_IDENTIFIED`，
但工件本身是在四套更早的标签体系下写成的：臂级判定（`SUPPORTED/REFUTED/NOT_EXPLAINED/QUALIFIED`）、关闭计数（`3/4 closed`）、出口名（`E3 TEST-UNSATISFIABLE`）、格级状态
（`NOT_RESOLVABLE`、`PARTIALLY_IDENTIFIED`）。**五值标签不是不存在，而是散落在四套拼写里**——
把它们统一起来只能靠本表，不能靠回写。

## 2 逐行映射（每个带判定的字段一行）

| 工件 | 字段 | 原始读数 | 五值标签 | 层 | 依据 |
| --- | --- | --- | --- | --- | --- |
| `experiments/phase10_results.json` | `exit` | `E1 CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase10_results.json` | `exit_reason` | `X1-X5 all pass` | **SUPPORTED** | artifact-field | this field carries no status of its own; the label is read from `verdict` of the same file (via `SUPPORTED`). Marked `derived`, so the per-claim tally counts the row the label came from, not this one twice |
| `experiments/phase10_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase11_results.json` | `exit` | `E1 CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase11_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase12_results.json` | `exit` | `E1 CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase12_results.json` | `exit_reason` | `XC1-XC4 and XC6 pass; XC5 recorded as a finding` | **SUPPORTED** | artifact-field | this field carries no status of its own; the label is read from `verdict` of the same file (via `SUPPORTED`). Marked `derived`, so the per-claim tally counts the row the label came from, not this one twice |
| `experiments/phase12_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase13_results.json` | `exits[taken_first_exit]` | `E1 CONVENTION RECONCILED` | **SUPPORTED** | artifact-field | Phase XIII E1: the convention conflict was resolved by derivation |
| `experiments/phase13_results.json` | `exit` | `E1 CONVENTION RECONCILED / E3 K4 CONFIRMED` | **SUPPORTED** | artifact-field | Phase XIII E1: the convention conflict was resolved by derivation |
| `experiments/phase13_results.json` | `verdict` | `2/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase14_results.json` | `exits[taken_first_exit]` | `E1 RATE-LAW EXACT` | **SUPPORTED** | artifact-field | Phase XIV E1 RATE-LAW-EXACT: the law held at the registered tolerance |
| `experiments/phase14_results.json` | `exit` | `E1 RATE-LAW EXACT` | **SUPPORTED** | artifact-field | Phase XIV E1 RATE-LAW-EXACT: the law held at the registered tolerance |
| `experiments/phase14_results.json` | `verdict` | `4/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase15_results.json` | `exits[taken_first_exit]` | `E1 GAP-IS-NOISE` | **SUPPORTED** | artifact-field | Phase XV E1: the joint-fit gap is explained by measurement noise |
| `experiments/phase15_results.json` | `verdict` | `4/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase16_results.json` | `exits[taken_first_exit]` | `E2 K-DEPENDENT-RESIDUAL` | **CONTRADICTED** | artifact-field | Phase XVI E2: cross-k readings are incompatible |
| `experiments/phase16_results.json` | `exit` | `E2 K-DEPENDENT-RESIDUAL` | **CONTRADICTED** | artifact-field | Phase XVI E2: cross-k readings are incompatible |
| `experiments/phase16_results.json` | `verdict` | `3/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase17_results.json` | `exits[taken_first_exit]` | `E2 TRUNCATION-NOT-THE-CULPRIT` | **INDETERMINATE** | artifact-field | Phase XVII E2: one hypothesis excluded, the law still undecided |
| `experiments/phase17_results.json` | `exit` | `E2 TRUNCATION-NOT-THE-CULPRIT` | **INDETERMINATE** | artifact-field | Phase XVII E2: one hypothesis excluded, the law still undecided |
| `experiments/phase17_results.json` | `verdict` | `3/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase18_results.json` | `exits[taken_first_exit]` | `E1 LAW-K-INVARIANT-UNDER-3LAYER` | **SUPPORTED** | artifact-field | Phase XVIII E1: three displacement knobs, cross-k 0/42 over-tolerance |
| `experiments/phase18_results.json` | `exit` | `E1 LAW-K-INVARIANT-UNDER-3LAYER` | **SUPPORTED** | artifact-field | Phase XVIII E1: three displacement knobs, cross-k 0/42 over-tolerance |
| `experiments/phase18_results.json` | `verdict` | `4/4 closed` | **COUNT_NOT_STATUS** | artifact-field | a closure COUNT, not a status; the round's own label is the `exit`/`verdict` row of this same file, so giving this row a label too would count one claim twice |
| `experiments/phase19_results.json` | `exits[taken_first_exit]` | `E3 TEST-UNSATISFIABLE` | **CONTRADICTED** | artifact-field | Phase XIX E3: the registered necessary condition cannot be met |
| `experiments/phase19_results.json` | `exit` | `E3 TEST-UNSATISFIABLE` | **CONTRADICTED** | artifact-field | Phase XIX E3: the registered necessary condition cannot be met |
| `experiments/phase19_results.json` | `verdict` | `E3 TEST-UNSATISFIABLE` | **CONTRADICTED** | artifact-field | Phase XIX E3: the registered necessary condition cannot be met |
| `experiments/phase20_results.json` | `exits[taken_first_exit]` | `E1 FILTER-USABLE` | **SUPPORTED** | artifact-field | Phase XX-XXII E1: the B-07 filter is satisfiable and separates |
| `experiments/phase20_results.json` | `exit` | `E1 FILTER-USABLE` | **SUPPORTED** | artifact-field | Phase XX-XXII E1: the B-07 filter is satisfiable and separates |
| `experiments/phase21_results.json` | `exits[taken_first_exit]` | `E1 UNIQUE-AND-SEPARABLE` | **SUPPORTED** | artifact-field | Phase XXI E1 UNIQUE-AND-SEPARABLE |
| `experiments/phase21_results.json` | `exit` | `E1 UNIQUE-AND-SEPARABLE` | **SUPPORTED** | artifact-field | Phase XXI E1 UNIQUE-AND-SEPARABLE |
| `experiments/phase22_results.json` | `exits[taken_first_exit]` | `E1 FAMILY-MAP-AS-PREDICTED` | **SUPPORTED** | artifact-field | Phase XXII E1 FAMILY-MAP-AS-PREDICTED: coverage matched the prior |
| `experiments/phase22_results.json` | `exit` | `E1 FAMILY-MAP-AS-PREDICTED` | **SUPPORTED** | artifact-field | Phase XXII E1 FAMILY-MAP-AS-PREDICTED: coverage matched the prior |
| `experiments/phase23_results.json` | `exit` | `AO-SEPARATES` | **SUPPORTED** | artifact-field | Phase XXIII E1: the AO measure separates issuance from silence |
| `experiments/phase23_results.json` | `label_r17` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase24_results.json` | `exit` | `REGULARIZATION-DOES-NOT-REPAIR` | **SUPPORTED** | artifact-field | Phase XXIV E1: L2 weight decay did not repair the old-law deviation |
| `experiments/phase24_results.json` | `label_r17` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase25_results.json` | `exit` | `S_ONLY_NONZERO_C_NOT_BETTER` | **INDETERMINATE** | artifact-field | Phase XXV E2: S-only effect nonzero, C advantage not detected |
| `experiments/phase25_results.json` | `label_r17` | `INDETERMINATE` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase26_results.json` | `exit` | `CONTEXT_MODEL_UNINFORMATIVE` | **NOT_IDENTIFIED** | artifact-field | Phase XXVI: context model miscalibrated; C advantage not tested |
| `experiments/phase26_results.json` | `label_r17` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase27_results.json` | `exit` | `CALIBRATION_FAILED` | **NOT_IDENTIFIED** | artifact-field | Phase XXVII: calibration did not beat the base rate; C advantage not tested |
| `experiments/phase27_results.json` | `label_r17` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase28_results.json` | `exit` | `GBDT_CALIBRATION_FAILED` | **NOT_IDENTIFIED** | artifact-field | Phase XXVIII: GBDT isotonic calibration degenerated to take-all |
| `experiments/phase28_results.json` | `label_r17` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase29_results.json` | `exit` | `PLATT_GBDT_CALIBRATION_FAILED` | **NOT_IDENTIFIED** | artifact-field | Phase XXIX: Platt fixed log-loss but the median threshold still took all rows |
| `experiments/phase29_results.json` | `label_r17` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase2_results.json` | `verdicts[E1]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase2_results.json` | `verdicts[E1b]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase2_results.json` | `verdicts[E2]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase30_results.json` | `exit` | `FIXED20_CALIBRATION_FAILED` | **NOT_IDENTIFIED** | artifact-field | Phase XXX: the 20% probability threshold fell on a large atom; no abstention set |
| `experiments/phase30_results.json` | `label_r17` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase31_results.json` | `exit` | `RANK20_C_NOT_BETTER` | **INDETERMINATE** | artifact-field | Phase XXXI: rank-based 20% policy passed C2 but the contrast CI included zero |
| `experiments/phase31_results.json` | `label_r17` | `INDETERMINATE` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/phase3_results.json` | `verdicts[L1]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase3_results.json` | `verdicts[L2]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase3_results.json` | `verdicts[L3]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase4_results.json` | `verdicts[L1]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase4_results.json` | `verdicts[L2]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase4_results.json` | `verdicts[L3]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase5_results.json` | `verdicts[V1]` | `NOT_EXPLAINED` | **INDETERMINATE** | artifact-field | Phase V/5c arm verdict: residual not attributable |
| `experiments/phase5_results.json` | `verdicts[V2]` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase5_results.json` | `verdicts[V3]` | `REFUTED` | **CONTRADICTED** | artifact-field | arm verdict used verbatim from Phase V/VI |
| `experiments/phase5b_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase5c_results.json` | `outcome` | `J_NOT_DECISIVE` | **INDETERMINATE** | artifact-field | Phase V-c outcome J_NOT_DECISIVE |
| `experiments/phase5c_results.json` | `verdict` | `NOT_EXPLAINED` | **INDETERMINATE** | artifact-field | Phase V/5c arm verdict: residual not attributable |
| `experiments/phase5c_results.json` | `v1_verdict_unchanged` | `J_NOT_DECISIVE (registered in Phase V; P5c-F4)` | **INDETERMINATE** | artifact-field | Phase V-c outcome J_NOT_DECISIVE |
| `experiments/phase5d_results.json` | `outcome` | `CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase6_results.json` | `outcome` | `O-REFUTED` | **CONTRADICTED** | artifact-field | Phase VI outcome string for the same judgement |
| `experiments/phase6_results.json` | `verdict` | `REFUTED` | **CONTRADICTED** | artifact-field | arm verdict used verbatim from Phase V/VI |
| `experiments/phase7_results.json` | `exit` | `E1 CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase7_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase7_results.json` | `phase6_verdict_unchanged` | `S2 REFUTED / S3 numeric-vs-analytic agreement stands (both u` | **CONTRADICTED** | artifact-field | arm verdict used verbatim from Phase V/VI |
| `experiments/phase8_results.json` | `exit` | `E2 EXPONENT-NOT-MINUS-TWO` | **CONTRADICTED** | artifact-field | Phase VIII E2: the exponent claim was falsified |
| `experiments/phase8_results.json` | `verdict` | `QUALIFIED` | **CONTRADICTED** | artifact-field | Phase VIII verdict: claim holds only after being narrowed |
| `experiments/phase8_results.json` | `phase6_verdict_unchanged` | `S2 stays REFUTED (P8-F4); this round only explains its readi` | **CONTRADICTED** | artifact-field | arm verdict used verbatim from Phase V/VI |
| `experiments/phase9_results.json` | `exit` | `E1 CONFIRMED` | **SUPPORTED** | artifact-field | exit-name synonym used from Phase VII on |
| `experiments/phase9_results.json` | `verdict` | `SUPPORTED` | **SUPPORTED** | artifact-field | 02/05-era arm verdict: the registered criterion was met |
| `experiments/phase22_reanalysis.json` | `verdict_on_P22_O1` | `CLOSED by derivation on committed readings, zero-test status` | **ZERO_TEST_REANALYSIS** | artifact-field | the file is a zero-test re-analysis; its fields quote another artifact's label (a runner label, an incomplete exit table), so no rule-7 status may be attached - a re-analysis may not carry a verdict (R6) |
| `experiments/phase6_reanalysis.json` | `P6_A8_outcome_table_incomplete[runner_label]` | `O-REFUTED` | **CONTRADICTED** | artifact-field | Phase VI outcome string for the same judgement |
| `experiments/phase6_reanalysis.json` | `P6_A8_outcome_table_incomplete[correct_label]` | `O-NONE (three registered exits all inapplicable)` | **ZERO_TEST_REANALYSIS** | artifact-field | the file is a zero-test re-analysis; its fields quote another artifact's label (a runner label, an incomplete exit table), so no rule-7 status may be attached - a re-analysis may not carry a verdict (R6) |
| `experiments/phase6_reanalysis.json` | `P6_A8_outcome_table_incomplete[reason]` | `S2 的不符发生在幂指数与近似单调性上，不构成 O-REFUTED 所要求的符号/单调性矛盾` | **CONTRADICTED** | artifact-field | Phase VI outcome string for the same judgement |
| `literature/L01_coding.json` | `exit_table[R13]` | `{'anchor_primary_family_from_registry': 'K5', 'anchor_primar` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `literature/L01_coding.json` | `exit_table[G5-03]` | `{'anchor_primary_family_from_registry': 'K2', 'anchor_primar` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `literature/L01_coding.json` | `exit_table[R14]` | `{'anchor_primary_family_from_registry': 'K5', 'anchor_primar` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `literature/L01_coding.json` | `round_label` | `INDETERMINATE` | **INDETERMINATE** | artifact-field | already canonical - this artifact field literally carries a rule-7 label |
| `literature/L01_coding.json` | `exit_table[R13]` | `label_reported=INDETERMINATE` | **INDETERMINATE** | artifact-field | Round L-01 emits the five labels natively (rule 7 written after the decision, this round was the first to obey it) |
| `literature/L01_coding.json` | `exit_table[G5-03]` | `label_reported=INDETERMINATE` | **INDETERMINATE** | artifact-field | Round L-01 emits the five labels natively (rule 7 written after the decision, this round was the first to obey it) |
| `literature/L01_coding.json` | `exit_table[R14]` | `label_reported=INDETERMINATE` | **INDETERMINATE** | artifact-field | Round L-01 emits the five labels natively (rule 7 written after the decision, this round was the first to obey it) |
| `experiments/PHASE10_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE10_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE11_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE12_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE12_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE13_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE14_RESULTS.md` | `prose` | `NOT_RESOLVABLE` | **NOT_IDENTIFIED** | document-only | cell-level state: tolerance exceeds the signal, no reading |
| `experiments/PHASE18_RESULTS.md` | `prose` | `NOT_RESOLVABLE` | **NOT_IDENTIFIED** | document-only | cell-level state: tolerance exceeds the signal, no reading |
| `experiments/PHASE23_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE24_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE25_RESULTS.md` | `prose` | `INDETERMINATE` | **INDETERMINATE** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE26_RESULTS.md` | `prose` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE27_RESULTS.md` | `prose` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE28_RESULTS.md` | `prose` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE29_RESULTS.md` | `prose` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE2_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE30_RESULTS.md` | `prose` | `NOT_IDENTIFIED` | **NOT_IDENTIFIED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE31_RESULTS.md` | `prose` | `INDETERMINATE` | **INDETERMINATE** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `experiments/PHASE3_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE4_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE5B_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE5B_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE5_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `experiments/PHASE5_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE6_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE8_RESULTS.md` | `prose` | `REFUTED` | **CONTRADICTED** | document-only | arm verdict used verbatim from Phase V/VI |
| `experiments/PHASE9_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `literature/ROUND_L01_RESULTS.md` | `prose` | `SUPPORTED` | **SUPPORTED** | document-only | 02/05-era arm verdict: the registered criterion was met |
| `literature/ROUND_L01_RESULTS.md` | `prose` | `CONTRADICTED` | **CONTRADICTED** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `literature/ROUND_L01_RESULTS.md` | `prose` | `NULL` | **NULL** | document-only | already canonical - this artifact field literally carries a rule-7 label |
| `literature/ROUND_L01_RESULTS.md` | `prose` | `INDETERMINATE` | **INDETERMINATE** | document-only | already canonical - this artifact field literally carries a rule-7 label |

## 3 处置计数与两层缺口

计数按**逐条主张**：`derived` 行（标签从同文件另一字段读来）只作出处指向，不重复计数。
工件行共 121 行，其中派生行 2 行。

| 处置 | 主张计数 | 其中：工件字段 | 其中：仅文档措辞 |
| --- | --- | --- | --- |
| SUPPORTED | 51 | 39 | 12 |
| CONTRADICTED | 22 | 14 | 8 |
| NULL | 1 | 0 | 1 |
| INDETERMINATE | 20 | 17 | 3 |
| NOT_IDENTIFIED | 17 | 10 | 7 |
| MANUAL_REVIEW | 0 | 0 | 0 |
| ZERO_TEST_REANALYSIS | 2 | 2 | 0 |
| COUNT_NOT_STATUS | 6 | 6 | 0 |

**读法**：`工件字段` 列说明该标签是否真的写在结果 JSON 的判定字段里；`仅文档措辞` 列说明它
是否只存在于结果文档的行文。**两者不成对就是缺口**，因为第 7 条要求的是每轮的判定标签，
而审计规则要求「报告里引用的每个标签都要能逐个对回结果 JSON」——只写在文档里的标签对不回任何字段。

推导出的缺口（121 行中，工件字段 90 行、文档措辞 31 行）：

1. **只在文档里存在、工件字段里为 0 的标签**：`NULL`。典型是格级状态 `NOT_RESOLVABLE` 与部分识别标签 `PARTIALLY_IDENTIFIED`——它们各自写在 `PHASE*_RESULTS.md` 的正文与表格里，但**没有任何 `phase*_results.json` 字段承载它**，所以按字段扫描时 `NOT_IDENTIFIED` 一栏为 0。这与 X-67 是同一条治理规律：**处置与标签必须写在承载判定的工件里，写在累计文档里等于没写**。
2. **两个层级都为 0 的标签**：无。`NULL`（仪器正常、效应为零）在 24 个实验轮里从未被字面写出：实验侧的失败形态被归入`CONTRADICTED`（判据被否证）或格级 `NOT_RESOLVABLE`（不可判），而「零结果」这一档在预注册出口表里从未被单独命名。这不是漏改旧轮（R6 禁止），而是**下一轮的出口表必须显式含 `NULL` 一档**，否则第 7 条要求的五值区分在实验侧仍只有四值。
3. 文献轮 L-01 是**第一个原生使用五值标签**的轮次（`L01_coding.json` 的 `exit_table[*].label_reported`）。

`MANUAL_REVIEW` 共 0 行：无。这些行的共同点是「字段里装的是关闭计数或过程标签，不是状态」，其五值标签须由同一文件的出口行取得。

## 4 引用规则

1. 引用旧轮判定时**两个都要写**：`raw`（原文，不可变）与 `label`（本表翻译）；
2. 本表由脚本推导，出现未被 `RULES` 覆盖的新拼写即落为 `MANUAL_REVIEW` 行并计数——这是刻意的：**词表漂移必须可见，不得静默归类**（与 X-70 同一处置原则）；
3. 新一轮若引入新的状态字面，须先在本表加规则再加判据，顺序不可颠倒。

## 5 复现

```bash
python3 governance/build_status_label_table.py
python3 experiments/audit_bindings.py
```
