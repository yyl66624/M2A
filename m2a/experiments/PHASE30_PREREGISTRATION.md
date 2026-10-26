# Phase XXX 预注册：固定弃权率 20% 的 C 策略（零训练、零重校准）

> 日期：2026-10-23 ｜ 触发：Phase XXIX 的 `PLATT_GBDT_CALIBRATION_FAILED`（Platt 校准过，但中位阈值仍全收）
> 轮次身份：**零训练、零重校准重分析**。模型固定为 Phase XXVIII 的 100 stumps，校准固定为 Phase XXIX 的 Platt 参数；
> 只改弃权规则为**固定 20%**。不重新训练、不重拟合校准、不取新数据、不改前轮工件。

## 0 源工件与数据

| 项 | 值 |
| --- | --- |
| 数据 | 同一 OBD zip，`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256 `e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78` |
| 模型 | Phase XXVIII 的 100 stumps，`experiments/phase28_results.json`，SHA-256 `ab31800636fcc92f9a7c94b88090f3646e1a04be540838e924850e5b96f9d63d` |
| 校准 | Phase XXIX 的 Platt `a=0.08556797386692835`、`b=-5.696329563076636`，`experiments/phase29_results.json`，SHA-256 `6eebc2cec84b5169b2023422a326acace3c9e7867dbb8c2e6bd032473d5ba2a7` |
| 切分 | fit 1–200 000；calibration 200 001–300 000；test 最后 30%（与 XXVIII/XXIX 相同） |

**零训练/零重校准声明**：不调用 `gbdt_fit`、不调用 `fit_platt`；stump 与 Platt 参数全部从上述两个工件读取。
源工件 SHA-256 或 schema 不符 ⇒ 立刻停，写 `DATA_OR_MODEL_MISMATCH`。

## 1 弃权规则

- 用冻结的 GBDT + Platt 计算 test 段校准概率 `p`。
- **固定弃权率 20%**：阈值 `τ = quantile(p, 0.20)`；`skip` 当 `p < τ`，其余 `take`（按日志动作展示）。
- 若阈值处有并列，`take` 数可能略高于 80%；必须记录实际 take 率，且只接受 `0.75 ≤ take_rate ≤ 0.85`。
- 如果弃权集为空或 take 率越界，C2 不过，出口 3。

## 2 估计量

- `Δ_S = mean(click | S take)`；`Δ_C = mean(click | C take)`；`Contrast = Δ_C − Δ_S`；skip 奖励 0。
- 不确定性：1000 个用户哈希桶 × 2000 次 bootstrap，2.5%/97.5%。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_C > 0` 且 95% CI 不含 0 | CI |
| C2 | 弃权集非空；`0.75 ≤ take_rate ≤ 0.85`；Platt 的 log-loss < 基础率；AUC > 0.5 | 0.75–0.85；严格不等式 |
| C3 | `Contrast > 0` 且 95% CI 不含 0 | CI |
| C4 | 数据/模型契约：数据哈希、两个源工件哈希、stump 数 100、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4 | `FIXED20_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，C3 不过 | `FIXED20_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过 | `FIXED20_CALIBRATION_FAILED` | `NOT_IDENTIFIED` |
| 4 | C4 不过 | `DATA_OR_MODEL_MISMATCH` | `NULL` |

## 5 解释与边界

- 出口 1：在固定 20% 弃权的 C 策略上，决策价值高于 S-only；XXV–XXIX 的“未测得”被这一规则推翻。
- 出口 2：即使 C 有真实的 20% 弃权集，仍没有高于 S-only 的决策价值；这是当前证据基上最强的阴性结果（模型、校准、阈值三者都已固定且非退化）。
- 出口 3：弃权集/校准/模型仍不过门；不得写成 C 无效。
- 不重新训练、不重拟合校准；推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。

## 6 停止规则

源哈希不符 ⇒ 停；运行 > 30 分钟或内存 > 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换 20%、不改判据、不做事后调参。

## 7 复现

```bash
python3 experiments/p30_gate.py --pre
python3 experiments/run_phase30.py --check
python3 experiments/run_phase30.py
python3 experiments/p30_gate.py
```
