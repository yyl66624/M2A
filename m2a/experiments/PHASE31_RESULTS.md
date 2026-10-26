# Phase XXXI 结果：rank-based 固定 20% 弃权（零训练、零重校准）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE31_PREREGISTRATION.md`（sha256 `98f74c683074064c…`）
> 门控 `experiments/p31_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase31_results.json`
> 源：Phase XXVIII 的 100 stumps（`ab318006…`）+ Phase XXIX 的 Platt（`6eebc2ce…`）；零训练、零重校准。

## 0 运行打印行

```
wrote phase31_results.json | exit RANK20_C_NOT_BETTER (INDETERMINATE) | S 0.003402 C 0.003853 contrast 0.000452 | auc 0.5842 ll 0.02369/0.02379 | take 0.8000 skip 82459
```

## 1 一句话结论

**六轮里第一次非退化检验**：按校准概率排序、种子随机序打破并列，跳过底部 20%（`k=82 459`，take `0.8000`）。
C2 全过（`c_skip_n=k`、take 率 0.80、log-loss `0.023687 < 0.023792`、AUC `0.5842`）。
C 的 `Δ_C=0.003853` 高于 S 的 `Δ_S=0.003402`，但 `Contrast=0.000452`，95% CI `[-0.000362, 0.000596]` **含 0**。
出口 **`RANK20_C_NOT_BETTER` / `INDETERMINATE`**：**模型、校准、弃权集三者都非退化，C 的决策优势仍未测得。**

## 2 读数

| 项 | 值 |
| --- | --- |
| 测试行 | 412 299 |
| 弃权 / take | 82 459 / 329 840（take `0.8000`） |
| S-only | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003698]` |
| C-only | n=329 840，clicks=1271，`Δ_C=0.003853`，CI `[0.001932, 0.004148]` |
| Contrast | `0.000452`，CI `[-0.000362, 0.000596]` |
| AUC / log-loss / 基础率 | `0.5842` / `0.023687` / `0.023792` |

判据：C1 过；**C2 过**；**C3 不过**（CI 含 0）；C4 过。

## 3 解释

- 这是 XXVI–XXXI 六轮里唯一一次：C2（校准 + 非退化弃权集）全过，而 C3 仍不过。
  因此它不能被解释为“模型太弱”“校准太差”或“阈值退化”——**在这个系统、这个点击奖励、这个 20% 弃权率上，
  C 的决策优势没有达到可测水平**。
- 点估计 `+0.045` 个百分点，CI 跨 0；不能说“C 无用”，也不能说“C 更好”。
- XXV 的 S-only 非零省略效应仍然成立；本轮不改变它。I1 的窄表述（C 对 deliberative omission 必要）仍是假说，
  本轮的 C 策略是“按预测 CTR 弃权”，不是“基于被跳过项价值选择省略”。
- 继续加模型/校准/阈值不会改变这个读数；要改变结论，需要**换奖励（非点击）或换带状态转移的真实日志**，
  或做线上/人类被试实验（需单独授权）。

## 4 边界

- 推荐系统、点击奖励、离线评估；不声称生物主体；不干预线上系统。
- 零训练、零重校准；只改弃权规则为 rank-based 20%。
- 单次 test 切分；bootstrap 1000 桶 × 2000 次、种子 20261028。
- 不把“未测得”写成“C 无效”。

## 5 复现

```bash
python3 experiments/p31_gate.py --pre   # 8/8
python3 experiments/run_phase31.py --check
python3 experiments/run_phase31.py
python3 experiments/p31_gate.py         # 12/12
```
