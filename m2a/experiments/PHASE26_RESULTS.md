# Phase XXVI 结果：上下文模型能否让 C 取得决策优势（OBD）

> 日期：2026-10-23 ｜ 预注册 `experiments/PHASE26_PREREGISTRATION.md`（sha256 `77359cee5625371b…`）
> 门控 `experiments/p26_gate.py` **12/12 checks passed** ｜ 结果 `experiments/phase26_results.json`
> 数据：ZOZO OBD `random/all/all.csv`（同一 SHA-256 `e8ec1819…`），仓库外；不干预线上系统。

## 0 运行打印行

```
wrote phase26_results.json | exit CONTEXT_MODEL_UNINFORMATIVE (NOT_IDENTIFIED) | S 0.003402 C 0.003751 contrast 0.000350 | auc 0.5410
```

## 1 一句话结论

160 维上下文 logistic 模型（80 个 user-item affinity + 80 个 item one-hot，200k 训练样本）在测试段有**排序信号**
（AUC `0.5410`），但 **log-loss `0.02807` 比基础率 `0.02379` 更差** ⇒ C2 不过。
C 策略的 `Δ_C = 0.003751`，`Contrast = 0.000350`，95% CI `[-0.001255, 0.000563]`。
出口 **`CONTEXT_MODEL_UNINFORMATIVE` / `NOT_IDENTIFIED`**：**本轮没有检验到 C 的决策优势**，
也没有推翻 Phase XXV 的“未测得”。

## 2 读数

| 项 | 值 |
| --- | --- |
| 测试行 | 412 299 |
| 测试点击率 | 0.003590 |
| S-only take | n=274 856，clicks=935，`Δ_S=0.003402`，CI `[0.002294, 0.003697]` |
| C-only take | n=207 918，clicks=780，`Δ_C=0.003751`，CI `[0.001038, 0.003829]` |
| Contrast | `0.000350`，CI `[-0.001255, 0.000563]` |
| 模型 AUC | 0.5410 |
| 模型 log-loss vs 基础率 | 0.02807 vs 0.02379（更差） |
| 阈值 | 测试预测中位数 `0.011258` |

判据：**C1 过**（Δ_C 的 CI 不含 0）；**C2 不过**（log-loss 未优于基础率）；**C3 不过**（Contrast CI 含 0）；**C4 过**。

## 3 解释

- 模型有弱排序信号（AUC > 0.5），但概率校准差于基础率；按预注册的 C2，它不能被用于检验 C 的决策优势。
- 因此本轮的正确读法是 **NOT_IDENTIFIED**，不是“C 不更好”。XXV 的 `C_NOT_BETTER` 仍然是那个系统、那个 item-CTR 阈值下的结论。
- 点估计上，Contrast 从 XXV 的 `0.001361` 降到 `0.000350`；没有证据表明上下文模型改善了 C 的决策价值。
- 若要用更强的模型类（校准、提升树、嵌入）重做，需要新的预注册；本轮不做事后换模型。

## 4 边界

- 推荐系统的一次展示机会，不是生物主体；点击奖励；离线评估；无线上干预。
- 训练只用前 200 000 行；测试是后 30%；单次切分；bootstrap 按 1000 用户桶、2000 次、固定种子 20261024。
- 不把“模型未识别”写成“C 无效”。

## 5 复现

```bash
python3 experiments/p26_gate.py --pre   # 8/8
python3 experiments/run_phase26.py --check
python3 experiments/run_phase26.py
python3 experiments/p26_gate.py         # 12/12
```
