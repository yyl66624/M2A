# Phase XXVII 结果：校准后的 C 策略能否取得决策优势（OBD）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE27_PREREGISTRATION.md`（sha256 `8a603a2deb185cd4…`）
> 门控 `experiments/p27_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase27_results.json`
> 数据：ZOZO OBD `random/all/all.csv`（同一 SHA-256 `e8ec1819…`），仓库外；不干预线上系统。

## 0 运行打印行

```
wrote phase27_results.json | exit CALIBRATION_FAILED (NOT_IDENTIFIED) | S 0.003402 iso 0.003832 platt 0.003751 | iso contrast 0.000430 | auc 0.5472 ll 0.02382/0.02379
```

## 1 一句话结论

同一 160 维 base model 加 **binned isotonic** 校准后，log-loss 从 XXVI 的 `0.02807` 拉回 `0.02382`，
但仍**略差于基础率** `0.02379`（差 `2.86e-5`）⇒ C2 不过；AUC `0.5472`。
isotonic 的 `Contrast = 0.000430`，95% CI `[-0.000309, 0.000640]`；Platt 的 `Contrast = 0.000350`，
CI `[-0.001255, 0.000563]`。出口 **`CALIBRATION_FAILED` / `NOT_IDENTIFIED`**：
**校准几乎追平基础率，但仍未过预注册的校准门；C 的决策优势仍不可测。**

## 2 读数

| 项 | 值 |
| --- | --- |
| 测试行 | 412 299 |
| base model | 160 维，fit 200k，5 epoch，种子 20261024 |
| calibration | 100k 行；isotonic 100 箱；Platt `a=0.7567`、`b=-2.3624` |
| S-only | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003697]` |
| Isotonic C | n=314 231，clicks=1204，`Δ_iso=0.003832`，CI `[0.001984, 0.004040]` |
| Platt C | n=207 918，clicks=780，`Δ_platt=0.003751` |
| Contrast_iso | `0.000430`，CI `[-0.000309, 0.000640]` |
| Contrast_platt | `0.000350`，CI `[-0.001255, 0.000563]` |
| AUC / log-loss / 基础率 | `0.5472` / `0.023820` / `0.023792` |

判据：**C1 过**；**C2 不过**（log-loss 未严格优于基础率）；**C3 不过**（CI 含 0）；**C4 过**。

## 3 解释

- 校准把 XXVI 的 miscalibration 基本修好（`0.02807 → 0.02382`），但**没有跨过基础率**；按预注册的严格不等式，C2 仍失败。
- 即使把 isotonic 的 take 率提高到 76%（314 231/412 299），C 的点估计只比 S-only 高 `0.00043`，CI 含 0。
- 正确读法：**本轮没有检验到 C 的决策优势**，也没有把 XXV 的“未测得”改写成“C 不更好”。XXVII 比 XXVI 更强的地方是：校准已接近基础率，仍没有信号。
- 若再换模型类（梯度提升等），需要新的预注册；本轮不做事后换模型。

## 4 边界

- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。
- fit / calibration / test 三段互不重叠；单次切分；bootstrap 1000 桶 × 2000 次、固定种子 20261024。
- 不把“校准门失败”写成“C 无效”。

## 5 复现

```bash
python3 experiments/p27_gate.py --pre   # 8/8
python3 experiments/run_phase27.py --check
python3 experiments/run_phase27.py
python3 experiments/p27_gate.py         # 12/12
```
