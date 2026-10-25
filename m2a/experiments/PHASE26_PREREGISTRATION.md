# Phase XXVI 预注册：上下文模型能否让 C 取得决策优势（OBD）

> 日期：2026-10-23 ｜ 触发：Phase XXV 的 `S_ONLY_NONZERO_C_NOT_BETTER`（C 的决策优势未测得）
> 轮次身份：真实随机化日志上的**离线政策评估**；只读同一 OBD 文件，不取新数据、不干预线上系统。
> 问题：XXV 的 C 策略只用 item CTR 中位数；本轮用**上下文特征**训练奖励模型，检验 C 的决策优势是否是阈值太弱造成的。

## 0 数据身份

同一 OBD zip：`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256
`e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78`；成员 `random/all/all.csv`；
切分沿用 XXV：行序前 70% 训练、后 30% 测试。

## 1 特征与模型（先于读数冻结）

- 每条展示取 **160 维**：80 个 `user-item_affinity_*` 浮点 + 80 维 `item_id` one-hot（训练样本中出现的 item）。
- 80 个 affinity 用**训练样本**的均值/标准差标准化（sd=0 时置 1）；one-hot 不标准化。
- 模型：L2 正则 logistic 回归，SGD；学习率 0.1，L2 1e-4，batch 1024，5 个 epoch，种子 `20261024`。
- 训练样本：训练段的**前 200 000 行**（预先固定，不用全量，控制运行时间）。
- 测试段预测后，阈值取**预测 CTR 的中位数**；C 策略 `skip` 当且仅当预测值低于中位数，其余 `take`（按日志动作展示）。
- S 策略沿用 XXV：`skip` 当且仅当 `position % 3 == 0`，只读位置，不表征 item 价值。

## 2 估计量

- `Δ_S = mean(click | S take)`，skip 奖励 0。
- `Δ_C = mean(click | C take)`，skip 奖励 0。
- `Contrast = Δ_C − Δ_S`。
- 不确定性：按 `user_feature_0` 的稳定哈希分 1000 桶，2000 次 bootstrap，2.5%/97.5%。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_C > 0` 且 95% CI 不含 0 | CI 判据 |
| C2 | 模型在测试段有信息：log-loss < 基础率 log-loss，且 AUC > 0.5 | 严格不等式 |
| C3 | `Contrast > 0` 且 95% CI 不含 0 | CI 判据 |
| C4 | 数据契约：哈希匹配、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4 | `CONTEXT_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，但 C3 不过 | `CONTEXT_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过 | `CONTEXT_MODEL_UNINFORMATIVE` | `NOT_IDENTIFIED` |
| 4 | C4 不过 | `DATA_IDENTITY_MISMATCH` | `NULL` |

C1 只作披露：C 策略自身价值 > 0 是预期，不是“C 更好”的证据。

## 5 解释与边界

- 出口 1：上下文 C 策略在真实日志上取得高于 S-only 的决策价值；XXV 的“未测得”被更强的 C 推翻。
- 出口 2：即使有上下文模型，C 的决策优势仍不可测；XXV 的结论不是阈值太弱造成的（在这个模型类与这个系统上）。
- 出口 3：模型没有信息，不能判断 C；不得写成 C 无效。
- 不干预线上系统；不声称生物主体；不把点击奖励外推到其它价值。

## 6 停止规则

哈希/字段不符 ⇒ 停；运行超过 30 分钟或内存超过 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换数据、不改判据、不重跑。

## 7 复现

```bash
python3 experiments/p26_gate.py --pre
python3 experiments/run_phase26.py --check
python3 experiments/run_phase26.py
python3 experiments/p26_gate.py
```
