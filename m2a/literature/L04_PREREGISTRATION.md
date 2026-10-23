# Round L-04 预注册：I1 证据链的论文级审计（零检验重分析）

> 日期：2026-10-23 ｜ 父轮：`literature/L02_PREREGISTRATION.md`、`literature/ROUND_L02_RESULTS.md`
> 触发：`nature-reviewer` 审稿人 2 的 R2-M1（I1 证据链 blocking）与审稿人 3 的 R3-M3
> 轮次身份：**零检验重分析**（同一批已提交编码，不重跑、不取新全文、不改 `L01_coding.json`，R6）。它只能否证/收窄 I1，不能确证。
> 单编码者披露：本轮由同一编码者完成，**没有第二编码者**；可靠性上限写进出口与报告。

## 1 被审计的主张

I1：**省略（omission）作为一等机制 = S 层（选择性不响应）⊕ C 层（反事实可及性表征）**，且 C 层是“省略”区别于普通不响应的必要条件。

审稿人 2 的反对：I1 的证据写作“21 条全文 + E2（构造性）+ L3”，但 21 是全文审查人口，不是 I1 专用分母；E2 的 S_only 零是构造性的；主张层重数显示 `Δ=3`。因此 I1 至多是假说。

## 2 分母与数据

- 可审计分母：`literature/L01_coding.json` 的 **17 条已提交编码行**（14 `FULLTEXT_REVIEWED` + 2 `QUALIFIED` + 1 `ABSTRACT_VERIFIED`）。每条行有 `layers`、`mechanism[].k`、`mechanism[].claim`、`mechanism[].quote`。
- **不**把 `fulltext_review.json` 的 21 条全文审查记录当作 I1 分母：那 21 条是关键词审查人口，其中多数与省略/可及性无关（本轮会把这一点作为读数打印）。
- **不**读取任何新全文、不重新取词、不改引文；证据只能是 `L01_coding.json` 里已提交的 `mechanism[].quote` 或 `claim`。

## 3 编码规则（先于工件冻结）

对每条行给一个且只一个码：

| 码 | 定义 | 判定要件 |
| --- | --- | --- |
| `S_ONLY` | 只给出“选择性不响应/弃权/停止”的证据，**没有**给出被跳过选项的反事实可及性/表征 | 至少一条 `claim` 或 `quote` 明确描述不响应/弃权；同一条行内没有任何表征/可及性主张 |
| `C_ONLY` | 只给出“表征/预测/可及性”的证据，**没有**给出选择性不响应 | 至少一条描述表征/预测/可及性；同一条行内没有不响应/弃权主张 |
| `S_PLUS_C` | 同一行内同时给出 S 与 C 的证据 | 同时满足上面两条 |
| `NEITHER` | 与省略/可及性无关（例如只谈门控、学习率、时间间隔、注意） | 既无 S 也无 C |
| `UNDECIDABLE` | 已提交引文不足以判定 | 引文缺失、过短或只给题录 |

**判定只依据已提交的 `claim`/`quote` 文本**，不依据 `registry.json` 的标注（R6）。每条码必须附一句 `rationale` 和一个 `evidence_k`（该行 `mechanism` 里的 k）；`evidence_k` 必须真实存在，否则是仪器缺陷。

## 4 读数与出口（按序取第一个可触发项）

- `N` = 17（分母）；`n_S` / `n_C` / `n_SC` / `n_N` / `n_U` = 各码行数；`n_I1 = n_S + n_C + n_SC`（与 I1 相关的行数）。
- `n_21` = `fulltext_review.json` 的记录数（作为“21 不是 I1 分母”的披露量，单独打印，不进入分母）。

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | `n_SC ≥ 1` 且 `n_S = n_C = 0` | `I1_CONJUNCTION_OBSERVED` | `SUPPORTED` |
| 2 | `n_SC ≥ 1` 且（`n_S ≥ 1` 或 `n_C ≥ 1`） | `I1_LAYERS_SEPARABLE` | `INDETERMINATE` |
| 3 | `n_SC = 0` 且 `n_I1 ≥ 3` | `I1_CONJUNCTION_NOT_OBSERVED` | `REFUTED` |
| 4 | `n_I1 < 3` 或 `n_U > 0` | `I1_EVIDENCE_INSUFFICIENT` | `NOT_IDENTIFIED` |
| 5 | 任何码缺失/越界/`evidence_k` 不存在 | `I1_AUDIT_INVALID` | `NULL` |

出口 2 的含义是：I1 的两层在**不同论文**里都能看到，但同一条行内同时看到两层的只有一部分；因此 I1 是“有部分论文级支持的假说”，不是已建立的一等机制。出口 3 才会把 I1 直接判负。

## 5 边界

- 只审计 17 条已提交编码行；`fulltext_review.json` 的 21 条只作为“分母不是 21”的披露。
- 单编码者；没有第二编码者，故 `n_*` 是**一个编码者的一次读数**，不是一致性统计。
- 不新增实验；R2 要求的“非构造性 S-only 臂”不在本轮，另立设计并标 `NEEDS_OWNER_APPROVAL`。
- 不改 `L01_coding.json`、`L02_reanalysis.json`、任何轮次判定或台账状态。

## 6 复现

```bash
python3 literature/l04_i1_gate.py        # 只验仪器，离线
python3 literature/l04_i1_audit.py --check
python3 literature/l04_i1_audit.py        # 两路绑定本预注册，不过则 rc=4 不写盘
```
