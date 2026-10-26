# Phase XXIX 预注册：用 Platt 校准 Phase XXVIII 的 GBDT（零训练重分析）

> 日期：2026-10-23 ｜ 触发：Phase XXVIII 的 `GBDT_CALIBRATION_FAILED`（isotonic 阈值退化到 0.001，C 全收）
> 轮次身份：**零训练重分析**。模型固定为 Phase XXVIII 已提交的 100 个 stump；只换校准器与阈值。
> 不重新训练、不取新数据、不改 Phase XXVIII 工件；本轮只能检验“校准器是否是退化原因”，不能改写 XXVIII 的读数。

## 0 数据身份与模型身份

| 项 | 值 |
| --- | --- |
| 数据 | 同一 OBD zip，`_m2a_data/open_bandit_dataset.zip`，412 931 917 字节，SHA-256 `e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78` |
| 模型 | Phase XXVIII 的 100 个 stump，来自 `experiments/phase28_results.json`（SHA-256 `ab31800636fcc92f9a7c94b88090f3646e1a04be540838e924850e5b96f9d63d`） |
| 切分 | 同 XXVII/XXVIII：fit 1–200 000；calibration 200 001–300 000；test 最后 30% |
| 特征 | 80 个 affinity 的 16 分位箱 + 80 个 item one-hot；由同一 fit 段重建（确定性） |

**零训练声明**：本轮不调用 `gbdt_fit`；stump 的 feature/threshold/leaf 全部从 Phase XXVIII 工件读取。
若工件的 SHA-256、stump 数（应为 100）或 schema 不符，立即停，写 `MODEL_SOURCE_MISMATCH`。

## 1 校准与策略

- 用 Phase XXVIII 的 stump 计算 calibration 段与 test 段的 GBDT 分数。
- **Platt**：在 calibration 分数上拟合 `p = σ(a·z + b)`，Newton 50 步，Hessian 加 1e-6 ridge。
- 不做 isotonic；不调箱数；不换阈值规则。
- C 策略：`skip` 当且仅当 Platt 概率低于 test 段 Platt 概率的中位数；其余 `take`（按日志动作展示）。
- S 策略：`position % 3 == 0` 跳过。

## 2 估计量

- `Δ_S = mean(click | S take)`；`Δ_P = mean(click | C take)`；`Contrast_P = Δ_P − Δ_S`；skip 奖励 0。
- 不确定性：1000 个用户哈希桶 × 2000 次 bootstrap，2.5%/97.5%。

## 3 判据

| 判据 | 内容 | 容差 |
| --- | --- | --- |
| C1 | `Δ_P > 0` 且 95% CI 不含 0 | CI |
| C2 | Platt 校准后的 GBDT 在 test 有信息：log-loss < 基础率，且 AUC > 0.5 | 严格不等式 |
| C3 | `Contrast_P > 0` 且 95% CI 不含 0 | CI |
| C4 | 数据与模型契约：数据哈希匹配、Phase28 工件哈希匹配、stump 数 100、`click ∈ {0,1}`、`position ≥ 1`、timestamp 违规 ≤ 0.1% | 0.001 |

另外必须披露：C take 数必须严格小于 test 行数（否则仍是全收退化；若全收，C2 视为不过，出口 3）。

## 4 出口

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | C2 与 C3 与 C4，且 C take < test rows | `PLATT_GBDT_C_BETTER` | `SUPPORTED` |
| 2 | C2 与 C4，C3 不过 | `PLATT_GBDT_C_NOT_BETTER` | `INDETERMINATE` |
| 3 | C2 不过，或 C 仍全收 | `PLATT_GBDT_CALIBRATION_FAILED` | `NOT_IDENTIFIED` |
| 4 | 数据/模型契约不过 | `DATA_OR_MODEL_MISMATCH` | `NULL` |

## 5 解释与边界

- 出口 1：Platt 修好了 XXVIII 的校准退化，并让 C 取得高于 S-only 的决策价值。
- 出口 2：Platt 修好了信息门，但 C 的决策优势仍不可测；这是当前 GBDT 类上更强的阴性结果。
- 出口 3：Platt 仍不过门或仍全收；不能据此说 C 无效。
- 本轮不重新训练模型，不对 XXVIII 的判定做任何改写；交叉验证只发生在同一 test 段的政策值上。
- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。

## 6 停止规则

数据/模型哈希不符 ⇒ 停；运行 > 30 分钟或内存 > 4 GB ⇒ 停并写 `NOT_IDENTIFIED`；不换校准器、不改判据、不做事后调参。

## 7 复现

```bash
python3 experiments/p29_gate.py --pre
python3 experiments/run_phase29.py --check
python3 experiments/run_phase29.py
python3 experiments/p29_gate.py
```
