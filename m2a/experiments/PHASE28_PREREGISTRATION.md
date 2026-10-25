# Phase XXVIII 预注册：梯度提升 C 策略（OBD）

> 日期：2026-10-23 ｜ 触发：Phase XXVII 的 `CALIBRATION_FAILED`（isotonic 差基础率 2.86e-5）
> 轮次身份：真实随机化日志上的离线政策评估；同一 OBD 文件；不取新数据、不干预线上系统。
> 问题：把模型类换成**梯度提升决策 stump**，再做 isotonic 校准，C 的决策优势是否可测。
> 实现边界：本轮是 **numpy 实现的 depth-1 梯度提升**（stump boosting），不是 XGBoost/LightGBM 的完整 GBDT；
> 不新增第三方依赖。

## 0 数据身份与切分

同一 OBD zip：`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256
`e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78`；成员 `random/all/all.csv`。

| 段 | 行范围 | 用途 |
| --- | --- | --- |
| fit | 1–200 000 | 训练 GBDT 与分箱边界 |
| calibration | 200 001–300 000 | 拟合 isotonic 校准 |
| test | 最后 30% | 评估；不参与任何拟合 |

## 1 特征与模型（先于读数冻结）

- 80 个 `user-item_affinity_*`：用 fit 段的 16 个等频分位点分箱（`np.searchsorted`），得到 0–15 的箱号。
- 80 维 item one-hot（fit 段出现的 item）。
- 共 160 个二值/有序特征。
- **GBDT**：depth-1 stump，100 轮；每轮从 fit 段无放回抽 50 000 行；学习率 0.1；L2 1.0；
  初始分数 `logit(mean(y_fit))`；每轮用牛顿叶值 `−G/(H+λ)`，取增益最大的单特征单阈值；种子 `20261025`。
- **校准**：在 calibration 段的 GBDT 分数上做 100 箱等频 isotonic（PAVA）；测试映射到块的均值；概率裁剪到 `[1e-6, 1−1e-6]`。
- C 策略：`skip` 当且仅当校准后的预测 CTR 低于测试段中位数；其余 `take`（按日志动作展示）。
- S 策略：`position % 3 == 0` 跳过，只读位置，不表征 item 价值。

## 2 估计量

- `Δ_S = mean(click | S take)`；`Δ_G = mean(click | C take)`；`Contrast_G = Δ_G − Δ_S`；skip 奖励 0。
- 不确定性：1000 个用户哈希桶 × 2000 次 bootstrap，2.5%/97.5%。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_G > 0` 且 95% CI 不含 0 | CI |
| C2 | 校准后的 GBDT 在测试段有信息：log-loss < 基础率 log-loss，且 AUC > 0.5 | 严格不等式 |
| C3 | `Contrast_G > 0` 且 95% CI 不含 0 | CI |
| C4 | 数据契约：哈希匹配、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4 | `GBDT_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，C3 不过 | `GBDT_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过 | `GBDT_CALIBRATION_FAILED` | `NOT_IDENTIFIED` |
| 4 | C4 不过 | `DATA_IDENTITY_MISMATCH` | `NULL` |

## 5 解释与边界

- 出口 1：梯度提升 + 校准让 C 取得高于 S-only 的决策价值；XXV–XXVII 的“未测得”被更强模型推翻。
- 出口 2：即使换到非线性模型类并校准，C 的决策优势仍不可测；这是当前证据基上最强的阴性结果。
- 出口 3：模型/校准仍未过门；不得写成 C 无效。
- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统；不是完整 GBDT 实现。

## 6 停止规则

哈希/字段不符 ⇒ 停；运行 > 30 分钟或内存 > 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换数据、不改判据、不做事后调参。

## 7 复现

```bash
python3 experiments/p28_gate.py --pre
python3 experiments/run_phase28.py --check
python3 experiments/run_phase28.py
python3 experiments/p28_gate.py
```
