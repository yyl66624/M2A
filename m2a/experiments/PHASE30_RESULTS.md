# Phase XXX 结果：固定弃权率 20%（零训练、零重校准）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE30_PREREGISTRATION.md`（sha256 `b8dec604054e1cdb…`）
> 门控 `experiments/p30_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase30_results.json`
> 源：Phase XXVIII 的 100 stumps（`ab318006…`）+ Phase XXIX 的 Platt（`6eebc2ce…`）；零训练、零重校准。

## 0 运行打印行

```
wrote phase30_results.json | exit FIXED20_CALIBRATION_FAILED (NOT_IDENTIFIED) | S 0.003402 C 0.003590 contrast 0.000188 | auc 0.5842 ll 0.02369/0.02379 | take 1.0000
```

## 1 一句话结论

按预注册的“20% 分位阈值 + `p < τ` 跳过”规则，**弃权集为空**：阈值 `τ = 0.002751` 正好落在校准概率的一个大原子上，
`p >= τ` 把整个原子都算作 take，`take_rate = 1.0000`、`c_skip_n = 0`。
C2 因此不过，出口 **`FIXED20_CALIBRATION_FAILED` / `NOT_IDENTIFIED`**。
这不是 C 的证据，而是**概率阈值无法在离散校准分数上实现固定弃权率**的规则实现问题。

## 2 读数

| 项 | 值 |
| --- | --- |
| 校准 | Phase XXIX Platt（`a=0.085568`，`b=-5.696330`） |
| log-loss / 基础率 | `0.023687` / `0.023792`（校准本身仍过） |
| AUC | `0.5842` |
| 20% 分位阈值 | `0.002751` |
| C skip / take | **0 / 412 299**（take_rate `1.0000`） |
| S-only | `Δ_S=0.003402`，CI `[0.002294, 0.003698]` |
| C-only | `Δ_C=0.003590`，CI `[0.001529, 0.003942]` |
| Contrast | `0.000188`，CI `[-0.000765, 0.000244]` |

判据：C1 过；**C2 不过**（`c_skip_n=0`，take_rate 越界）；C3 不过；C4 过。

## 3 解释

- 校准分数在 0.002751 处有**大原子**；分位阈值与 `p >= τ` 的组合把原子全部保留，弃权集为空。
- 这说明：**固定弃权率不能用“概率阈值”在离散分数上实现**；需要**按排名**选底部 20%（排序后用固定种子的随机序打破并列），
  而不是用 `p < quantile(p, 0.20)`。
- 正确的下一步是一个**新的预注册**（Phase XXXI）：rank-based 20%，并列用种子随机序打破；本轮不事后改规则。
- 本轮的 log-loss/AUC 与 XXIX 相同（校准没问题），因此它不是校准失败；出口名 `FIXED20_CALIBRATION_FAILED` 是预注册的
  “政策/契约未过”档，读作“固定 20% 规则未实现”，不是“C 不更好”。

## 4 边界

- 零训练、零重校准；只改弃权规则。
- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。
- 单次 test 切分；bootstrap 1000 桶 × 2000 次、种子 20261027。
- 不把“规则未实现”写成“C 无效”。

## 5 复现

```bash
python3 experiments/p30_gate.py --pre   # 8/8
python3 experiments/run_phase30.py --check
python3 experiments/run_phase30.py
python3 experiments/p30_gate.py         # 12/12
```
