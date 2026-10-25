# Phase XXV 结果：真实随机化推荐日志上的非构造性 S-only 臂

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE25_PREREGISTRATION.md`（sha256 `847ded6a0f1d1a59…`，先于读数提交）
> 门控 `experiments/p25_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase25_results.json`
> 数据：ZOZO Open Bandit Dataset，`random/all/all.csv`，仓库外，SHA-256 `e8ec18196582a593…`（412 931 917 字节）
> 轮次身份：**真实系统、真实随机化日志的离线政策评估**；不干预线上系统；不是生物主体。

## 0 运行打印行

```
wrote phase25_results.json | exit S_ONLY_NONZERO_C_NOT_BETTER (INDETERMINATE) | S 0.003402 C 0.004763 contrast 0.001361 | rows 1374327
```

## 1 一句话结论

在真实推荐系统的均匀随机日志上，一个**不表征被跳过项价值**的 S-only 跳过策略（`position % 3 == 0`）
仍有非零省略效应：`Δ_S = 0.003402`，95% CI `[0.002294, 0.003698]`。
C-only 策略的点击率更高（`Δ_C = 0.004763`），但两者之差 `Contrast = 0.001361` 的 95% CI
`[-0.001359, 0.002160]` 含 0 ⇒ **C 的决策优势在本系统上未测得**。
出口 **`S_ONLY_NONZERO_C_NOT_BETTER`**，五值 **`INDETERMINATE`**。

## 2 读数

| 项 | 值 |
| --- | --- |
| 总行数 | 1 374 327（2019-11-24 至 2019-11-30，`timestamp` 非降违规 0） |
| 训练 / 测试 | 962 028 / 412 299（按行序前 70% / 后 30%） |
| 物品数 | 80；训练中 ≥100 次展示并进入 CTR 的 80 |
| propensity | 采样值恒为 `0.0125`（均匀随机策略） |
| S-only take | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003698]` |
| C-only take | n=207 217，clicks=987，`Δ_C=0.004763`，CI `[0.001988, 0.005394]` |
| Contrast | `0.001361`，CI `[-0.001359, 0.002160]` |
| C2 独立性 | skip 标注点击率 `0.003965`，take 标注 `0.003402`，差 `0.000563 ≤ 0.01` |
| C4 契约 | click/position 违规 0，哈希匹配 |

判据：**C1 过**（Δ_S 的 CI 不含 0）；**C2 过**；**C3 不过**（Contrast 的 CI 含 0）；**C4 过**。

## 3 解释

- **C 不是任何省略效应的必要条件**：S-only 策略只读位置，不读 item 价值，仍然放弃了可测的点击。
  这与解析反例 `report/I1_S_ONLY_COUNTEREXAMPLE.md` 同向，并把“E2 的 S_only 零是构造性的”从数学陈述推进到真实系统读数。
- **C 的决策优势未建立**：在这个系统、这个阈值和这个点击奖励上，C-only 的点估计更高，但差值 CI 含 0。
  因此不能声称“C 提高决策质量”；只能说“本系统未测得”。
- **不能反推 C 不必要于 deliberative omission**：本实验的 S-only 策略不是“基于被跳过项价值选择省略”，
  所以它不检验窄表述；窄表述仍是假说。

## 4 边界

- 推荐系统的一次展示机会，不是生物主体的行动选择；结论不外推到大脑、社会或语言模型。
- 离线政策评估：take 的奖励是日志点击；skip 的奖励定义为 0；不干预线上系统，不处理用户被跳过后的替代行为。
- 均匀随机策略的日志；其它 logging policy、其它奖励、其它阈值不外推。
- 单次切分（前 70% / 后 30%）；bootstrap 按 1000 个用户哈希桶、2000 次重采样、固定种子 20261023。

## 5 复现

```bash
python3 experiments/p25_gate.py --pre   # 8/8
python3 experiments/run_phase25.py --check
python3 experiments/run_phase25.py      # 先门控，再绑定预注册；不过则 rc=4
python3 experiments/p25_gate.py         # 12/12
```
