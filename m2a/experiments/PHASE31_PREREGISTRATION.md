# Phase XXXI 预注册：rank-based 固定弃权 20%（零训练、零重校准）

> 日期：2026-10-23 ｜ 触发：Phase XXX 的 `FIXED20_CALIBRATION_FAILED`（概率阈值落在离散分数的大原子上，弃权集为空）
> 轮次身份：**零训练、零重校准重分析**。模型/校准继续冻结在 Phase XXVIII/XXIX；只把弃权规则改为**按排名**。
> 不重新训练、不重拟合校准、不取新数据、不改前轮工件。

## 0 源工件与数据

| 项 | 值 |
| --- | --- |
| 数据 | 同一 OBD zip，`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256 `e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78` |
| 模型 | Phase XXVIII 的 100 stumps，`experiments/phase28_results.json`，SHA-256 `ab31800636fcc92f9a7c94b88090f3646e1a04be540838e924850e5b96f9d63d` |
| 校准 | Phase XXIX 的 Platt `a=0.08556797386692835`、`b=-5.696329563076636`，`experiments/phase29_results.json`，SHA-256 `6eebc2cec84b5169b2023422a326acace3c9e7867dbb8c2e6bd032473d5ba2a7` |
| 切分 | fit 1–200 000；calibration 200 001–300 000；test 最后 30%（与 XXVIII–XXX 相同） |

## 1 rank-based 弃权规则

- 用冻结的 GBDT + Platt 计算 test 段校准概率 `p`。
- `k = floor(0.20 × n_test)`；用**固定种子 `20261028`** 生成 `tie = permutation(n)`；
  按 `(p, tie)` 字典序升序排序（`np.lexsort((tie, p))`），**跳过排序后的前 `k` 行**，其余 `take`。
- 这保证弃权集恰为 `k` 行、take 恰为 `n−k` 行；并列由种子随机序打破，不再依赖概率阈值。
- 若 `k = 0` 或 `k = n`，C2 不过，出口 3。

## 2 估计量

- `Δ_S = mean(click | S take)`；`Δ_C = mean(click | C take)`；`Contrast = Δ_C − Δ_S`；skip 奖励 0。
- 不确定性：1000 个用户哈希桶 × 2000 次 bootstrap，2.5%/97.5%；bootstrap 种子 `20261028`。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_C > 0` 且 95% CI 不含 0 | CI |
| C2 | `c_skip_n = k` 且 `0.79 ≤ take_rate ≤ 0.81`；Platt log-loss < 基础率；AUC > 0.5 | 0.79–0.81 |
| C3 | `Contrast > 0` 且 95% CI 不含 0 | CI |
| C4 | 数据/模型契约：数据哈希、两个源工件哈希、stump 数 100、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4 | `RANK20_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，C3 不过 | `RANK20_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过 | `RANK20_CALIBRATION_FAILED` | `NOT_IDENTIFIED` |
| 4 | C4 不过 | `DATA_OR_MODEL_MISMATCH` | `NULL` |

## 5 解释与边界

- 出口 1：在真实的 20% 弃权集上，C 的决策价值高于 S-only；XXV–XXX 的“未测得”被这一规则推翻。
- 出口 2：模型、校准、弃权集三者都已固定且非退化，C 仍没有高于 S-only 的决策价值；这是当前证据基上最强的阴性结果。
- 出口 3：规则/校准/模型仍不过门；不得写成 C 无效。
- 不重新训练、不重拟合校准；推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。

## 6 停止规则

源哈希不符 ⇒ 停；运行 > 30 分钟或内存 > 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换 20%、不改判据、不做事后调参。

## 7 复现

```bash
python3 experiments/p31_gate.py --pre
python3 experiments/run_phase31.py --check
python3 experiments/run_phase31.py
python3 experiments/p31_gate.py
```
