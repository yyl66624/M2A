# Phase XXIX 结果：Platt 校准 Phase XXVIII 的 GBDT（零训练重分析）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE29_PREREGISTRATION.md`（sha256 `5a3dc9b1293a531b…`）
> 门控 `experiments/p29_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase29_results.json`
> 模型：Phase XXVIII 的 100 个 stump（`phase28_results.json` SHA-256 `ab31800636fcc92f…`）；**不重新训练**。
> 数据：同一 OBD zip；不干预线上系统。

## 0 运行打印行

```
wrote phase29_results.json | exit PLATT_GBDT_CALIBRATION_FAILED (NOT_IDENTIFIED) | S 0.003402 C 0.003590 contrast 0.000188 | auc 0.5842 ll 0.02369/0.02379 | take 412299/412299
```

## 1 一句话结论

Platt 校准把 log-loss 修到 **`0.023687` < 基础率 `0.023792`**（校准部分通过），AUC `0.5842`；
但 Platt 的斜率只有 `0.0856`，概率被压缩，**中位阈值 `0.002751` 以下没有样本**，C 策略仍 take 全部
412 299 行。按预注册的 C2（要求 C take < test rows），出口 **`PLATT_GBDT_CALIBRATION_FAILED` / `NOT_IDENTIFIED`**：
**校准问题修好了，弃权阈值仍然是退化的**。

## 2 读数

| 项 | 值 |
| --- | --- |
| 模型 | Phase XXVIII 的 100 stumps（零训练） |
| Platt | `a=0.085568`，`b=-5.696330` |
| log-loss vs 基础率 | `0.023687` vs `0.023792`（**更好**） |
| AUC | `0.5842` |
| 阈值 | `0.002751`；C take = 412 299 / 412 299（**全收**） |
| S-only | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003698]` |
| C-only | n=412 299，clicks=1480，`Δ_C=0.003590`，CI `[0.001529, 0.003942]` |
| Contrast | `0.000188`，CI `[-0.000765, 0.000244]` |

判据：C1 过；**C2 不过**（仅因 `C take = test rows`，全收条件）；C3 不过；C4 过。

## 3 解释

- **校准器确实是 XXVIII 退化的部分原因**：换成 Platt 后 log-loss 低于基础率，AUC 保持 0.584。
- **但阈值仍然退化**：Platt 斜率 0.086 把概率压到 0.0027–0.004 的窄带，中位数以下没有样本，C 还是全收。
  所以“全收”不是 isotonic 独有，而是**中位阈值 + 窄概率带**的共同结果。
- 正确的下一步不是再换校准器，而是**改弃权规则**：例如固定弃权率（bottom 10%/20%）或绝对阈值；
  这需要新的预注册，本轮不事后改判据。
- 本轮不把“全收”写成“C 不更好”；它只说明在这个阈值规则下没有形成弃权决策。

## 4 边界

- 零训练重分析：模型固定为 Phase XXVIII 的 stump；只换校准器与阈值规则。
- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。
- 单次 test 切分；bootstrap 1000 桶 × 2000 次、种子 20261026。

## 5 复现

```bash
python3 experiments/p29_gate.py --pre   # 8/8
python3 experiments/run_phase29.py --check
python3 experiments/run_phase29.py
python3 experiments/p29_gate.py         # 12/12
```
