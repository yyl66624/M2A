# Phase XXVII 预注册：校准后的 C 策略能否取得决策优势（OBD）

> 日期：2026-10-23 ｜ 触发：Phase XXVI 的 `CONTEXT_MODEL_UNINFORMATIVE`（模型有排序信号但 log-loss 差于基础率）
> 轮次身份：真实随机化日志上的离线政策评估；同一 OBD 文件；不取新数据、不干预线上系统。
> 问题：把同一个 base model 做 **Platt / binned isotonic 校准**后，C 的决策优势是否可测。

## 0 数据身份与切分

同一 OBD zip：`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256
`e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78`；成员 `random/all/all.csv`。

| 段 | 行范围 | 用途 |
| --- | --- | --- |
| fit | 1–200 000 | 训练 base model（与 XXVI 同规格） |
| calibration | 200 001–300 000 | 拟合 Platt / isotonic（不参与 base model 训练） |
| test | 最后 30% | 评估；不参与任何拟合 |

## 1 模型与校准（先于读数冻结）

- Base model：160 维（80 个 `user-item_affinity_*` + 80 维 item one-hot），L2 logistic，LR 0.1，L2 1e-4，batch 1024，5 epoch，种子 `20261024`；80 个 affinity 用 fit 段均值/标准差标准化。
- **Platt**：在 calibration 段的 base logit 上拟合 `p = σ(a·z + b)`，Newton 50 步，Hessian 加 1e-6 ridge。
- **Binned isotonic**：calibration logit 按等频分 100 箱，箱内标签均值做 PAVA；测试 logit 用箱边界映射到对应块的均值。
- 概率裁剪到 `[1e-6, 1−1e-6]`。
- C 策略：`skip` 当且仅当校准后的预测 CTR 低于测试段校准预测的中位数；其余 `take`（按日志动作展示）。
- S 策略：沿用 `position % 3 == 0` 跳过，只读位置，不表征 item 价值。

## 2 估计量

- `Δ_S = mean(click | S take)`；`Δ_iso = mean(click | C_iso take)`；`Δ_platt` 同理；skip 奖励 0。
- 主对比：`Contrast_iso = Δ_iso − Δ_S`；次对比：`Contrast_platt = Δ_platt − Δ_S`（探索性）。
- 不确定性：1000 个用户哈希桶 × 2000 次 bootstrap，2.5%/97.5%。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_iso > 0` 且 95% CI 不含 0 | CI |
| C2 | 校准时模型在测试段有信息：isotonic log-loss < 基础率 log-loss，且 AUC > 0.5 | 严格不等式 |
| C3 | `Contrast_iso > 0` 且 95% CI 不含 0 | CI |
| C4 | 数据契约：哈希匹配、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

`Contrast_platt` 只作次读数，不参与出口；不得用它替代 C3。

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4 | `CALIBRATED_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，C3 不过 | `CALIBRATED_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过 | `CALIBRATION_FAILED` | `NOT_IDENTIFIED` |
| 4 | C4 不过 | `DATA_IDENTITY_MISMATCH` | `NULL` |

## 5 解释与边界

- 出口 1：校准后的 C 在真实日志上取得高于 S-only 的决策价值；XXV/XXVI 的“未测得”被更强的校准推翻。
- 出口 2：即使校准，C 的决策优势仍不可测；这是比 XXVI 更强的阴性结果（模型已过校准门）。
- 出口 3：校准仍不够；不得写成 C 无效。
- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。

## 6 停止规则

哈希/字段不符 ⇒ 停；运行 > 30 分钟或内存 > 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换数据、不改判据、不做事后换模型。

## 7 复现

```bash
python3 experiments/p27_gate.py --pre
python3 experiments/run_phase27.py --check
python3 experiments/run_phase27.py
python3 experiments/p27_gate.py
```
