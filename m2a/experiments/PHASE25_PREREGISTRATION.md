# Phase XXV 预注册：真实系统上的非构造性 S-only 臂（Open Bandit Dataset）

> 日期：2026-10-23 ｜ 触发：审稿人 2 的 R2-M1（“非构造性 S-only 臂，使非零 Δ 成为可能”）
> 轮次身份：**真实系统、真实随机化日志的预注册政策评估**。数据是 ZOZO 的 Open Bandit Dataset（OBD），
> 不是合成模型；本机只做离线评估，不干预线上系统。
> 前置：`report/I1_S_ONLY_COUNTEREXAMPLE.md` 已给出解析反例；本轮检验同一命题在真实系统上的经验版本。

## 0 数据身份与边界

| 项 | 值 |
| --- | --- |
| 来源 | `https://research.zozo.com/data_release/open_bandit_dataset.zip`（ZOZO Research 公开数据） |
| 文件 | 仓库外 `_m2a_data/open_bandit_dataset.zip` |
| 字节 | 412 931 917 |
| SHA-256 | `e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78` |
| 使用成员 | `open_bandit_dataset/random/all/all.csv`（均匀随机策略；字段含 `timestamp,item_id,position,click,propensity_score,user_feature_0`） |
| 数据性质 | 真实 A/B 测试的随机化日志；动作由 logging policy 随机化，`propensity_score` 记录在行内 |
| 边界 | 这是**推荐系统**中的“跳过一次展示机会”，不是生物主体的行动省略；结论只覆盖这个系统与这个 operationalization |

**允许的主张**：在真实随机化日志中，一个不表征被跳过项价值的 S-only 跳过策略，仍有非零的省略效应（被放弃的点击）。
**不允许的主张**：任何关于真实大脑、人类社会或语言模型的机制结论；任何线上干预效果（本轮不干预线上系统）。

## 1 政策与估计量

- **S-only 策略**：`skip` 当且仅当 `position % 3 == 0`；其余 `take`（按日志动作展示）。跳过规则只读位置，不读 `item_id`、`click` 或任何价值估计 ⇒ **没有 C**。
- **C-only 策略**：在训练段估计每个 `item_id` 的点击率；`skip` 当且仅当该估计低于训练段（至少 100 次展示的）项目点击率中位数；其余 `take`。它**表征了被跳过项的价值**。
- 估计量（测试段）：
  - `Δ_S = mean(click | S take)`，因为 S 跳过时的奖励定义为 0。
  - `Δ_C = mean(click | C take)`。
  - `Contrast = Δ_C − Δ_S`。
- 切分：按文件行序前 70% 训练、后 30% 测试；运行器检查 `timestamp` 非降（若违反，仍按行序但打印违规数）。
- 不确定性：按 `user_feature_0` 的稳定哈希分 1000 个桶；对桶做 2000 次有放回 bootstrap，取 2.5%/97.5% 分位。

## 2 判据（先于读数冻结）

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_S > 0` 且 95% CI 不含 0 | 无（CI 判据） |
| C2 | S 的跳过规则与点击独立：`|click_rate(skip-labeled) − click_rate(take-labeled)| ≤ 0.01` | 0.01 |
| C3 | `Contrast > 0` 且 95% CI 不含 0（C 的决策质量更高） | 无（CI 判据） |
| C4 | 数据契约：哈希匹配、`click ∈ {0,1}`、`position ≥ 1`、`timestamp` 非降违规 ≤ 0.1% 行 | 0.001 |

## 3 出口（按序取第一个可触发项）

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C1 与 C3 与 C4 全过 | `S_ONLY_NONZERO_AND_C_BETTER` | `SUPPORTED` |
| 2 | C1 与 C4 过，但 C3 不过 | `S_ONLY_NONZERO_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C1 不过，C4 过 | `S_ONLY_ZERO_OR_NEGLIGIBLE` | `REFUTED` |
| 4 | 数据身份或契约不过 | `DATA_IDENTITY_MISMATCH` | `NULL` |

## 4 解释规则

- 出口 1 的含义：**真实系统里存在“没有 C 也有非零省略效应”的案例**；C 不是省略效应的必要条件；C 的作用是提高决策质量（Contrast > 0）。这与解析反例一致，并把 I1 的窄表述（C 对 deliberative omission 必要）留在假说层。
- 出口 2 的含义：省略效应非零，但 C 在这个系统里没有带来可测的决策优势；不能据此支持 C 的决策价值。
- 出口 3 的含义：在这个系统与这个政策下，S-only 的省略效应不可测；不得据此反推“C 必要”。

## 5 停止规则

- 数据哈希不符、成员缺失、字段缺失 ⇒ 立即停，写 `DATA_IDENTITY_MISMATCH`，不进入读数。
- 运行时间超过 30 分钟或内存超过 4 GB ⇒ 停，写 `NOT_IDENTIFIED`，不改变判据。
- 不重跑、不改判据、不换数据；任何实现缺陷登记为 amendment，零检验重分析另立。

## 6 复现

```bash
python3 experiments/p25_gate.py           # 只验仪器，离线
python3 experiments/run_phase25.py --check
python3 experiments/run_phase25.py        # 先门控，再绑定预注册；不过则 rc=4
```
