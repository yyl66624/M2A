# Round L-04 结果：I1 的论文级审计（零检验重分析）

> 日期：2026-10-23 ｜ 预注册 `literature/L04_PREREGISTRATION.md`（sha256 `1234142f0c72dc6c520098b952b5aa4e21e5efd3f7f5116b7e859bb496f8fb2a`，先于工件提交）｜
> 门控 `literature/l04_i1_gate.py` **14/14 checks passed**（pre 模式 12/12）｜ 工件 `literature/L04_I1_AUDIT.json`
> （sha256 `6d5f904072b7ed4792048a9931425ad84e139ff05ea3d13b88915d5eca1da73f`）｜ 运行器 `literature/l04_i1_audit.py`。
> 轮次身份：零检验重分析；只读 17 条已提交 L-01 编码行；不取新全文、不改 `L01_coding.json`、不改任何轮次判定（R6）。

## 0 运行打印行

```
wrote L04_I1_AUDIT.json | exit I1_LAYERS_SEPARABLE (INDETERMINATE) | rows 17 | S 1 C 1 SC 3 neither 12 | binding match
```

## 1 一句话结论

17 条已提交编码行里只有 **5 条**与 I1 相关：**3 条同时给出 S 与 C**、**1 条 S-only**、**1 条 C-only**，其余 **12 条无关**。
出口 `I1_LAYERS_SEPARABLE`，五值标签 **`INDETERMINATE`**。读法：**S 层与 C 层可以在不同论文中分离**；
同一条行内同时给出两层的只有 3 条。I1 从“最强创新”降为**有部分论文级支持的假说**，不是已建立的一等机制。

`fulltext_review.json` 的 **21 条**是全文审查人口，**不是** I1 专用分母；I1 专用分母是 17 条编码行。这一点就是审稿人 2 的 R2-M1 所指的证据链缺口。

## 2 逐行编码

| 行 | 码 | 证据键 | 理由 |
| --- | --- | --- | --- |
| `G5-03-N1` | `NEITHER` | K1 | Trigger and cross-domain misalignment only; no omission or availability claim. |
| `G5-03-N2` | `NEITHER` | K2 | Intent-gated refusal, not selective non-response or a representation of skipped options. |
| `G5-03-N4` | `S_ONLY` | K9 | Reasoned abstention with a confidence threshold; no description of representing the skipped answer. |
| `G5-03-N6` | `NEITHER` | K2 | Refusal representation and multi-dimensional gate; neither omission nor availability of omitted options. |
| `G5-03` | `NEITHER` | K2 | A single necessary-and-sufficient refusal direction; not an omission claim. |
| `R13-N15` | `NEITHER` | K5 | Delayed reinforcement and phase-reversed switch; not omission or counterfactual availability. |
| `R13-N16` | `NEITHER` | K2 | GIPR suppression of inflammation-derived aversion is a gate, not omission. |
| `R13-N17` | `NEITHER` | K11 | Motivational intensity and effort; no selective non-response or availability representation. |
| `R13-N2` | `S_PLUS_C` | K2, K5 | Feeding is stopped by cell-type-specific gates (S) and novel flavours activate/reactivate amygdala representations (C). |
| `R13-N3` | `C_ONLY` | K5 | Predictive allostatic model (C); no selective non-response is described. |
| `R13-N8` | `S_PLUS_C` | K6, K5 | Restrictive eating/abstention is self-reinforcing (S) and the amygdala is experience-driven and represents food cues (C). |
| `R13` | `S_PLUS_C` | K2, K5 | Novelty gates the delayed signal (S) and malaise reactivates neural representations of novel flavours (C). |
| `R14-N1` | `NEITHER` | K2 | Dopamine contingency tracking; not an omission or availability claim. |
| `R14-N4` | `NEITHER` | K5 | Statistical analysis of within-trial signals; not omission. |
| `R14-N7` | `NEITHER` | K5 | Learning rate as a function of temporal separation; not omission. |
| `R14-N8` | `NEITHER` | K5 | Dopamine ramps and intertrial interval; not omission. |
| `R14` | `NEITHER` | K5 | Reward duration sets the learning rate; not omission or counterfactual availability. |

计数：`S_ONLY 1`、`C_ONLY 1`、`S_PLUS_C 3`、`NEITHER 12`、`UNDECIDABLE 0`、`I1_relevant 5`、分母 `17`。

## 3 出口与边界

- 出口 2：`I1_LAYERS_SEPARABLE` / `INDETERMINATE`。它表示两层各自有论文级实例，但同一行同时给出两层的只有 3 条，且另有 1 条 S-only 与 1 条 C-only 显示两层可分离。
- **单编码者**：本轮由同一编码者完成，没有第二编码者；`n_*` 是一次读数，不是一致性统计。
- **没有运行** R2 要求的“非构造性 S-only 臂”：那是新实验，须另行授权；本轮只做零检验重分析，只能否证/收窄 I1，不能确证。
- 不改变 `L01_coding.json`、`L02_reanalysis.json`、`synthesis_v2.json` 或任何台账状态。
- 21 条全文审查记录仍是 Phase I′ 的记录；本轮只说明它不是 I1 专用分母，不改写它。

## 4 对报告的影响

终报 §5 的 I1 段已追加同日修入：分母改为 17 条编码行，I1 降为“有部分论文级支持的假说”。
§63 的权威主张表仍以“定义 + 假说”表述 I1；本轮的读数不改变那句话，只是把它的证据边界写实。

## 5 复现

```bash
python3 literature/l04_i1_gate.py --pre   # 12/12
python3 literature/l04_i1_audit.py --check
python3 literature/l04_i1_audit.py        # 先跑 pre 门控，再两路绑定预注册；不过则 rc=4
python3 literature/l04_i1_gate.py         # 14/14
```
