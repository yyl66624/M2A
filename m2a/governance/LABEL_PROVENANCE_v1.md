# 判定标签↔工件对账 v1（LABEL_PROVENANCE_v1）

问题：散文写下的判定标签，能不能被它所说那一轮的工件推翻？（GOVERNANCE_ARTIFACT，不跑实验、不改任何轮次判定）

翻译权威：`governance/build_status_label_table.py` 的注册映射（源码 SHA-256 `7b9c18a5e5a64832`，登记 27 个词）；本表不重新定义任何翻译。
生成本表的推导器源码 SHA-256：`9f87c71d61da7e73`；工件文件 52 份，注册轮次数 24，标签词表 49 个，语料文档 61 份，产出主张行 805 行（文档 54 份）。

| 判定 | 条数 |
|---|---|
| `anchor_phantom` | 0 |
| `label_unregistered` | 0 |
| `label_wrong_for_anchor` | 1 |
| `stale_in_register` | 0 |
| `paired_correction` | 0 |
| `five_label_only_in_translation` | 1 |
| `not_a_round_verdict` | 0 |
| `attested_in_other_round` | 0 |
| `anchor_without_recorded_label` | 3 |
| `label_mention_without_predication` | 247 |
| `cross_round_refutation` | 0 |
| `paired_correction` | 0 |
| `label_without_anchor` | 494 |
| `matches_artifact` | 59 |
| **硬伤合计** | **1** |

硬伤逐条（只列本层判据认定的，不解释成对旧轮的重判）：

- `literature/ROUND_L01_RESULTS.md:75` label_wrong_for_anchor → 允许的五值 `CONTRADICTED,INDETERMINATE` ｜ 摘录：| **L01-A1** | 竞争理论走独立通道，不并入引用排名池 | OpenAlex 检索返回 **0 命中**（首版判为 `NOT_OBTAINED`），改走 arXiv A

口径不对称（写死，供复核）：配对只在**轮次**层，不在臂层；一轮同时记录 E1/E2 时本表接受其一。本表的两个输出不参与语料（工件不给自己背书）。

