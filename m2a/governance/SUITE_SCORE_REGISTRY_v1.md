# 套件分数引用对账 v1（由实跑推导）

> 推导器 `governance/build_suite_score_registry.py`（会实跑人口内每台套件，故本步设计成每轮跑一次，
> 不进收尾审计的收集）；校验器 `governance/suite_score_registry_gate.py`。
> 权威读数只有一个：**那台套件自己打印的 `n/n checks passed`**。散文里的引用与它逐条对账。
> 判据在本文件运行之前冻结（见推导器 docstring 的 E1–E7 与出口顺序）。
> 本步自己写出的两个文件不参与引用扫描（派生工件不给自己背书，R8）；本步的校验器不被本推导器运行
> （仪器不得自证），凡对它的引用一律记为 `self_reference` 并如实披露。

| 列 | 数 |
| --- | --- |
| 实跑的套件 | 36（今天为绿 36） |
| 语料内文档 / 其中真的产出主张行的 | 73 / 15 |
| 引用条数 / 去重后的判定行 | 87 / 75 |
| **硬伤（凭空仪器 / 实跑不绿 / 再生文档陈旧 / 不可能的增长）** | 0 |
| 引用与实跑一致 | 63 |
| 同一行同时给出实跑值（把错误当错误引用） | 4 |
| 可能为历史值（小于实跑，仅披露不判红） | 7 |
| 对本步校验器自身的引用（不可自证） | 1 |

## 逐条引用

| 文档 | 口径 | 仪器 | 引用 | 实跑 | 判定 | 行 |
| --- | --- | --- | --- | --- | --- | --- |
| `M2A_FINAL_REPORT.md` | append_only | `ao_preflight_gate.py` | 8/8 | 8/8 | matches_live | 1371 |
| `M2A_FINAL_REPORT.md` | append_only | `gate_coverage_map_gate.py` | 17/17 | 18/18 | paired_correction | 1721 |
| `M2A_FINAL_REPORT.md` | append_only | `gate_coverage_map_gate.py` | 18/18 | 18/18 | matches_live | 1614 |
| `M2A_FINAL_REPORT.md` | append_only | `gate_discrimination_gate.py` | 5/5 | 59/59 | possible_history | 1398 |
| `M2A_FINAL_REPORT.md` | append_only | `gate_discrimination_gate.py` | 59/59 | 59/59 | matches_live | 1789 |
| `M2A_FINAL_REPORT.md` | append_only | `obligation_registry_gate.py` | 8/8 | 8/8 | matches_live | 1730 |
| `M2A_FINAL_REPORT.md` | append_only | `p10_gate.py` | 6/6 | 6/6 | matches_live | 1663 |
| `M2A_FINAL_REPORT.md` | append_only | `result_score_map_gate.py` | 12/12 | 12/12 | matches_live | 1685 |
| `M2A_FINAL_REPORT.md` | append_only | `runner_enforcement_map_gate.py` | 14/14 | 14/14 | matches_live | 1645 |
| `M2A_FINAL_REPORT.md` | append_only | `section_page_reconciliation_gate.py` | 22/22 | 23/23 | possible_history | 1812 |
| `M2A_FINAL_REPORT.md` | append_only | `status_label_table_gate.py` | 6/6 | 6/6 | matches_live | 1341 |
| `M2A_FINAL_REPORT.md` | append_only | `unmeasured_instruments_gate.py` | 25/25 | 25/25 | matches_live | 1728 |
| `M2A_FINAL_REPORT.md` | append_only | `wiki_sync_map_gate.py` | 16/16 | 16/16 | matches_live | 1749 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `gate_coverage_map_gate.py` | 17/17 | 18/18 | paired_correction | 204 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `gate_coverage_map_gate.py` | 18/18 | 18/18 | matches_live | 201 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `gate_discrimination_gate.py` | 5/5 | 59/59 | possible_history | 197 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `gate_discrimination_gate.py` | 59/59 | 59/59 | matches_live | 206 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `obligation_registry_gate.py` | 7/7 | 8/8 | possible_history | 190 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `result_score_map_gate.py` | 12/12 | 12/12 | matches_live | 203 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `runner_enforcement_map_gate.py` | 14/14 | 14/14 | matches_live | 202 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `section_page_reconciliation_gate.py` | 22/22 | 23/23 | possible_history | 206 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `status_label_table_gate.py` | 6/6 | 6/6 | matches_live | 193 |
| `NEGATIVE_AND_NULL_EVIDENCE_LOG.md` | append_only | `wiki_sync_map_gate.py` | 16/16 | 16/16 | matches_live | 205 |
| `OBLIGATION_REGISTRY.md` | regenerated | `gate_coverage_map_gate.py` | 18/18 | 18/18 | matches_live | 104 |
| `OBLIGATION_REGISTRY.md` | regenerated | `unmeasured_instruments_gate.py` | 25/25 | 25/25 | matches_live | 104 |
| `PHASE10_RESULTS.md` | run_record | `p10_gate.py` | 6/6 | 6/6 | matches_live | 4 |
| `PHASE11_RESULTS.md` | run_record | `p11_gate.py` | 6/6 | 6/6 | matches_live | 4 |
| `PHASE12_RESULTS.md` | run_record | `p12_gate.py` | 4/4 | 4/4 | matches_live | 4 |
| `PHASE13_RESULTS.md` | run_record | `p13_gate.py` | 6/6 | 6/6 | matches_live | 4 |
| `PHASE14_RESULTS.md` | run_record | `p14_gate.py` | 7/7 | 7/7 | matches_live | 5 |
| `PHASE19_RESULTS.md` | run_record | `p19_gate.py` | 6/6 | 6/6 | matches_live | 10 |
| `PHASE20_RESULTS.md` | run_record | `p20_gate.py` | 7/7 | 7/7 | matches_live | 10 |
| `PHASE2_RESULTS.md` | run_record | `phase2_gate.py` | 7/7 | 7/7 | matches_live | 4 |
| `PHASE9_RESULTS.md` | run_record | `p9_gate.py` | 8/8 | 8/8 | matches_live | 4 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `l01_gate.py` | 7/7 | 7/7 | matches_live | 43 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p10_gate.py` | 6/6 | 6/6 | matches_live | 7 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p11_gate.py` | 6/6 | 6/6 | matches_live | 20 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p12_gate.py` | 4/4 | 4/4 | matches_live | 21 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p13_gate.py` | 6/6 | 6/6 | matches_live | 22 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p14_gate.py` | 7/7 | 7/7 | matches_live | 23 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p15_gate.py` | 7/7 | 7/7 | matches_live | 24 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p16_gate.py` | 7/7 | 7/7 | matches_live | 25 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p17_gate.py` | 7/7 | 7/7 | matches_live | 26 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p18_gate.py` | 7/7 | 7/7 | matches_live | 27 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p19_gate.py` | 6/6 | 6/6 | matches_live | 28 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p20_gate.py` | 7/7 | 7/7 | matches_live | 29 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p21_gate.py` | 8/8 | 8/8 | matches_live | 30 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p22_gate.py` | 7/7 | 7/7 | matches_live | 31 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p3_gate.py` | 7/7 | 7/7 | matches_live | 33 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p4_gate.py` | 5/5 | 5/5 | matches_live | 34 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p5_gate.py` | 8/8 | 8/8 | matches_live | 38 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p5b_gate.py` | 6/6 | 6/6 | matches_live | 35 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p5c_gate.py` | 7/7 | 7/7 | matches_live | 36 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p5d_gate.py` | 7/7 | 7/7 | matches_live | 37 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p6_gate.py` | 7/7 | 7/7 | matches_live | 39 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p7_gate.py` | 9/9 | 9/9 | matches_live | 40 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p8_gate.py` | 6/6 | 6/6 | matches_live | 41 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `p9_gate.py` | 8/8 | 8/8 | matches_live | 42 |
| `RESULT_SCORE_RECONCILIATION_v1.md` | derived_summary | `phase2_gate.py` | 7/7 | 7/7 | matches_live | 32 |
| `ROUND_L01_RESULTS.md` | run_record | `l01_gate.py` | 7/7 | 7/7 | matches_live | 6 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `ao_preflight_gate.py` | 8/8 | 8/8 | matches_live | 61 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `gate_coverage_map_gate.py` | 17/17 | 18/18 | paired_correction | 67 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `gate_coverage_map_gate.py` | 18/18 | 18/18 | matches_live | 63 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `gate_discrimination_gate.py` | 59/59 | 59/59 | matches_live | 62 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `l01_gate.py` | 6/6 | 7/7 | paired_correction | 40 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `obligation_registry_gate.py` | 7/7 | 8/8 | possible_history | 43 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `obligation_registry_gate.py` | 8/8 | 8/8 | matches_live | 68 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `p10_gate.py` | 6/6 | 6/6 | matches_live | 65 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `result_score_map_gate.py` | 12/12 | 12/12 | matches_live | 66 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `runner_enforcement_map_gate.py` | 14/14 | 14/14 | matches_live | 64 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `section_page_reconciliation_gate.py` | 22/22 | 23/23 | possible_history | 72 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `status_label_table_gate.py` | 6/6 | 6/6 | matches_live | 59 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `suite_score_registry_gate.py` | 20/20 | - | self_reference | 73 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `unmeasured_instruments_gate.py` | 25/25 | 25/25 | matches_live | 69 |
| `SECTION_PAGE_RECONCILIATION_v1.md` | derived_summary | `wiki_sync_map_gate.py` | 16/16 | 16/16 | matches_live | 70 |

## 人口与指纹

> 生成本表的推导器源码 SHA-256：`657c00885b8c89ce`（`governance/build_suite_score_registry.py`）；语料文档 73 份。语料缩小而不登记，Q18 会红。

| 套件 | 路径 | 实跑 | 源码 sha256（前 12） |
| --- | --- | --- | --- |
| `ao_preflight_gate.py` | `experiments/ao_preflight_gate.py` | 8/8 | `f7cb76ca7e80` |
| `check_phase1prime_gate3.py` | `literature/check_phase1prime_gate3.py` | 21/21 | `20df8e00df4e` |
| `gate_coverage_map_gate.py` | `governance/gate_coverage_map_gate.py` | 18/18 | `e4e265a0a875` |
| `gate_discrimination_gate.py` | `governance/gate_discrimination_gate.py` | 59/59 | `b487c70a7338` |
| `l01_gate.py` | `literature/l01_gate.py` | 7/7 | `4fcbc82ef9a2` |
| `obligation_registry_gate.py` | `governance/obligation_registry_gate.py` | 8/8 | `8cf107bb7410` |
| `p10_gate.py` | `experiments/p10_gate.py` | 6/6 | `433f2913cc7a` |
| `p11_gate.py` | `experiments/p11_gate.py` | 6/6 | `ec5ca1ca28be` |
| `p12_gate.py` | `experiments/p12_gate.py` | 4/4 | `5a1fd094d95c` |
| `p13_gate.py` | `experiments/p13_gate.py` | 6/6 | `3ffad7486680` |
| `p14_gate.py` | `experiments/p14_gate.py` | 7/7 | `c0bafd7c751b` |
| `p15_gate.py` | `experiments/p15_gate.py` | 7/7 | `610b5e4ed1ac` |
| `p16_gate.py` | `experiments/p16_gate.py` | 7/7 | `2e1b72ca26db` |
| `p17_gate.py` | `experiments/p17_gate.py` | 7/7 | `686ea937fdc2` |
| `p18_gate.py` | `experiments/p18_gate.py` | 7/7 | `fd3a54dbd6c5` |
| `p19_gate.py` | `experiments/p19_gate.py` | 6/6 | `dcdb4e56cd65` |
| `p20_gate.py` | `experiments/p20_gate.py` | 7/7 | `def465f2d5bf` |
| `p21_gate.py` | `experiments/p21_gate.py` | 8/8 | `ea8ec46bb2e1` |
| `p22_gate.py` | `experiments/p22_gate.py` | 7/7 | `7ccef873b7ea` |
| `p3_gate.py` | `experiments/p3_gate.py` | 7/7 | `0dea02e14745` |
| `p4_gate.py` | `experiments/p4_gate.py` | 5/5 | `a37dd2e0a5b0` |
| `p5_gate.py` | `experiments/p5_gate.py` | 8/8 | `83cfc522d3a6` |
| `p5b_gate.py` | `experiments/p5b_gate.py` | 6/6 | `2ad486b3a5e2` |
| `p5c_gate.py` | `experiments/p5c_gate.py` | 7/7 | `006b0d90456c` |
| `p5d_gate.py` | `experiments/p5d_gate.py` | 7/7 | `5c0b3ed7015b` |
| `p6_gate.py` | `experiments/p6_gate.py` | 7/7 | `7b6eb4ec5b44` |
| `p7_gate.py` | `experiments/p7_gate.py` | 9/9 | `433e9f78a5bb` |
| `p8_gate.py` | `experiments/p8_gate.py` | 6/6 | `f8d9a9f53c2d` |
| `p9_gate.py` | `experiments/p9_gate.py` | 8/8 | `55c0bbc4ef25` |
| `phase2_gate.py` | `experiments/phase2_gate.py` | 7/7 | `57554ebdbfd4` |
| `result_score_map_gate.py` | `governance/result_score_map_gate.py` | 12/12 | `03f55a6f59b4` |
| `runner_enforcement_map_gate.py` | `governance/runner_enforcement_map_gate.py` | 14/14 | `ea45cda8f072` |
| `section_page_reconciliation_gate.py` | `governance/section_page_reconciliation_gate.py` | 23/23 | `10404b959e57` |
| `status_label_table_gate.py` | `governance/status_label_table_gate.py` | 6/6 | `e5c82a140086` |
| `unmeasured_instruments_gate.py` | `governance/unmeasured_instruments_gate.py` | 25/25 | `e12431e55f5d` |
| `wiki_sync_map_gate.py` | `governance/wiki_sync_map_gate.py` | 16/16 | `96c4a531c913` |

**看不见什么**：判定只看 `n/n` 这一种形状；不比句子、不比判据数值、不比容差。
`possible_history` 是有意不判红的一档——一个小于今日值的数字既可能是当时成立的历史读数，也可能是
被当作今日值引用的陈年值，机械规则分不开这两种；因此它逐条列出，并由 §47 的 ERRATA 与人工复核承担。
再生文档没有这档豁免：`OBLIGATION_REGISTRY.md` 每次由工件重导，带旧号就是硬伤。
