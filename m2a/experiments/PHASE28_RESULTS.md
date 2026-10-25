# Phase XXVIII 结果：梯度提升 C 策略（OBD）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE28_PREREGISTRATION.md`（sha256 `a4f894be71a031ac…`）
> 门控 `experiments/p28_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase28_results.json`
> 数据：ZOZO OBD `random/all/all.csv`（同一 SHA-256 `e8ec1819…`），仓库外；不干预线上系统。
> 实现：numpy depth-1 梯度提升（100 stumps、16 箱、50k 子采样、L2=1.0）；不是 XGBoost/LightGBM。

## 0 运行打印行

```
wrote phase28_results.json | exit GBDT_CALIBRATION_FAILED (NOT_IDENTIFIED) | S 0.003402 C 0.003590 contrast 0.000188 | auc 0.5864 ll 0.02416/0.02379 | stumps 100
```

## 1 一句话结论

GBDT 的**排序信号更强**（AUC `0.5864`，高于线性模型的 `0.5472`），但 isotonic 校准后的 log-loss
`0.024156` 仍差于基础率 `0.023792` ⇒ C2 不过。更关键的是：校准后的中位阈值落在 `0.001`，
**C 策略 take 了全部 412 299 行**（没有弃权），`Contrast = 0.000188`，CI `[-0.000765, 0.000244]`。
出口 **`GBDT_CALIBRATION_FAILED` / `NOT_IDENTIFIED`**：本轮**没有检验到 C 的决策优势**，
而且 C 策略已经退化为“全收”，不是一次有效的弃权检验。

## 2 读数

| 项 | 值 |
| --- | --- |
| 测试行 | 412 299 |
| GBDT | 100/100 stumps；16 箱；50k 子采样；lr 0.1；L2 1.0；种子 20261025 |
| AUC | `0.5864` |
| isotonic log-loss vs 基础率 | `0.024156` vs `0.023792`（更差） |
| 校准阈值 | `0.001`（中位数）；C take = 412 299（**全收**） |
| S-only | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003698]` |
| C-only | n=412 299，clicks=1480，`Δ_C=0.003590`，CI `[0.001529, 0.003942]` |
| Contrast | `0.000188`，CI `[-0.000765, 0.000244]` |

判据：C1 过；**C2 不过**；**C3 不过**；C4 过。出口 `GBDT_CALIBRATION_FAILED`。

## 3 解释

- GBDT 比线性模型有更强的**排序**能力（AUC 0.586 vs 0.547），但这没有转化为可用的概率或决策价值。
- isotonic 校准在 100 箱上把大部分测试分数压到 0.001，导致中位阈值以下没有样本；C 策略变成全收，
  `Δ_C` 就是总体点击率。**这不是“C 不更好”的证据**，而是校准/阈值退化的证据。
- 若继续，正确做法是**新预注册**一个 Platt 校准的 GBDT（或减少 isotonic 箱数/加平滑），而不是在本轮改判据。
- 本轮不据此更新 XXV 的“C 未测得”；XXV 的结论仍限于 item-CTR 阈值。

## 4 边界

- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统；不是完整 GBDT。
- fit 200k / calibration 100k / test 最后 30%；bootstrap 1000 桶 × 2000 次、种子 20261025。
- 不把“校准退化”写成“C 无效”。

## 5 复现

```bash
python3 experiments/p28_gate.py --pre   # 8/8
python3 experiments/run_phase28.py --check
python3 experiments/run_phase28.py
python3 experiments/p28_gate.py         # 12/12
```
