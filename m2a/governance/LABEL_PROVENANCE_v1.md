# 判定标签↔工件对账 v1（LABEL_PROVENANCE_v1）

问题：散文写下的判定标签，能不能被它所说那一轮的工件推翻？（GOVERNANCE_ARTIFACT，不跑实验、不改任何轮次判定）

翻译权威：`governance/build_status_label_table.py` 的注册映射（源码 SHA-256 `d55da336c9c665e2`，登记 25 个词）；本表不重新定义任何翻译。
生成本表的推导器源码 SHA-256：`5491e5f7967d0c22`；工件文件 46 份，注册轮次数 22，标签词表 39 个，语料文档 51 份，产出主张行 637 行（文档 46 份）。

| 判定 | 条数 |
|---|---|
| `anchor_phantom` | 0 |
| `label_unregistered` | 0 |
| `label_wrong_for_anchor` | 0 |
| `stale_in_register` | 0 |
| `paired_correction` | 0 |
| `five_label_only_in_translation` | 31 |
| `not_a_round_verdict` | 0 |
| `attested_in_other_round` | 0 |
| `anchor_without_recorded_label` | 8 |
| `label_mention_without_predication` | 106 |
| `cross_round_refutation` | 0 |
| `paired_correction` | 0 |
| `label_without_anchor` | 409 |
| `matches_artifact` | 83 |
| **硬伤合计** | **0** |

硬伤逐条（只列本层判据认定的，不解释成对旧轮的重判）：


口径不对称（写死，供复核）：配对只在**轮次**层，不在臂层；一轮同时记录 E1/E2 时本表接受其一。本表的两个输出不参与语料（工件不给自己背书）。

