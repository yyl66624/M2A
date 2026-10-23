# 门控仪器覆盖表 v1（由 `governance/build_coverage_map.py` 从门控源码推导）

> 依据：owner 2026-10-18 第 7 条的仪器侧要求 + 台账 `O-16`/`O-17`。生成物：本文件与
> `governance/gate_coverage_map_v1.json`。**本表不改写任何门控、不跑实验**，只读源码。

## 1 这台仪器与那台仪器的分工

判别力套件（`governance/gate_discrimination_gate.py`）用**注入**回答「多小的错这台门控看不见」；
本表用**语法**回答「哪个量根本没有进入任何判定」。两者不可互相替代：
本表能枚举没人想到去注入的缺口，注入能发现本表看不见的口径问题（见 §4）。

覆盖人口：31 份轮次门控（`experiments/*_gate.py` + `literature/*_gate.py`），
199 条 `check()`，84 个从本地机制模块导入的可调用量。

## 2 缺口清单（每条都必须带登记理由；新增而未登记者构建失败）

| 门控 | 量 | 类别 | 理由 |
| --- | --- | --- | --- |
| `experiments/p10_gate.py` | `p8_smooth.rho_smooth` | 导入了，但没有任何检查执行它 | 本表新查出：Phase X 的门控从 `p8_smooth` 导入 `rho_smooth` 却从未调用，它自己只用 `p10_exponent.rho`。两族读数本应对齐（Phase VIII 的平滑曲线 vs Phase X 的指数族），这一对齐从未在门控层做过。 |
| `experiments/p13_gate.py` | `p8_smooth.rho_exact` | 导入了，但没有任何检查执行它 | 本表新查出：Phase XIII 的门控导入 `rho_exact` 未调用，W5 只锚 `rho_smooth` ⇒ 精确仪器在该轮门控层无人核对；`rho_exact` 在 Phase VIII 那里也只是一条自我比较（见上）。 |
| `experiments/p13_gate.py` | `p8_smooth.rho_smooth` | 导入了，但没有任何检查执行它 | 本表新查出（同名遮蔽）：门控从 `p8_smooth` 导入 `rho_smooth`，而 W5 实际调用的是 `p12.rho_smooth`（第 59 行）⇒ 两个模块各有一个同名函数，被锚定的不是导入的那个；该轮对 Phase VIII 平滑曲线的门控层依赖是**空的**。文件里 `import p12_lattice as p12  # noqa: F401 (used via rho_smooth)` 这条注释还会把人引向相反结论。它也没有被 `p8_smooth` 内任何被调用的函数间接执行。 |
| `experiments/p5b_gate.py` | `p5_mechanisms.chain_polarity` | 导入了，但没有任何检查执行它 | 本表新查出：与 `gap_for` 同一行导入（`from p5_mechanisms import chain_polarity, gap_for, tnorm, channels, window_exists`），且没有任何被调用的同模块函数在内部调用它 ⇒ 串行极性以及它作用的整条链在该轮门控层无人执行；V-b 只重测了窗口与网格。 |
| `experiments/p5b_gate.py` | `p5_mechanisms.channels` | 导入了，但没有任何检查执行它 | 本表新查出：silent 侧输入构型（hard / one_weak / all_weak）从未被该门控构造，也没有被任何它调用的函数内部构造⇒「三档构型按注册生成」无仪器答案。注意它只被 `gap_for` 消费，而 `gap_for` 自己也没被执行。 |
| `experiments/p5b_gate.py` | `p5_mechanisms.gap_for` | 导入了，但没有任何检查执行它 | X-79 的实测例：门控 `from p5_mechanisms import gap_for` 却从未调用 ⇒ 该轮量具的输入（驱动差 Δ）在仪器层无人核对；注入 1e-4 全绿已证实其盲。 |
| `experiments/p5b_gate.py` | `p5_mechanisms.tnorm` | 导入了，但没有任何检查执行它 | 本表新查出：聚合算子在该轮门控层未被执行。这条**不是**「算子从未被测」——Phase IX 的门控有 `C8_tnorm_algebra` 盯它；这里的含义仅限「V-b 声称用到的那条链没有仪器」。 |
| `experiments/p5d_gate.py` | `p5d_confirm.readout_d` | 被执行，但只被「与自己比较」的检查执行 | 本表新查出（自我比较类）：`readout_d(0.8, 101, arm)` 只出现在 `G3_determinism`（`a == b`，同种子两次调用）⇒ 该确证轮的 MC 读数在门控层的唯一守护是「同种子给同一个数」，任何确定性实现错误都能通过（X-79 那一族的第三例）。 |
| `experiments/p8_gate.py` | `p8_smooth.rho_exact` | 被执行，但只被「与自己比较」的检查执行 | X-79 的第二例：唯一读取它的 J5 写的是 `rho_exact(0.6) == rho_exact(0.6)`（自我比较，无可证伪输入）；注入 1e-1（154.664→170.130）后 6 档全绿。 |
| `experiments/phase2_gate.py` | `m2a_mechanisms.e1_rates` | 被执行，但只被「与自己比较」的检查执行 | 本表新查出（自我比较类）：`e1_rates("and", 2000, seed=3)` 只出现在 `C1_determinism`（`r1 == r2`）⇒ Phase II 的机制生成器在门控层只被「同种子给同一个数」守护；C2/C3 盯的是闭式 `p_action`，不消费 `e1_rates`。这是全仓库最早的一条无可证伪输入检查。 |

**合计**：`never_reached` 7 条、`only_self_comparison` 3 条、`detail_only` 3 条。

## 3 自我比较型检查的普查（这些检查本身没有错，错在被当作仪器）

共 18 条 `check()` 的条件形如 `a == b`，且 a 与 b 由**结构相同的表达式**赋值而来。
它们能抓 NaN、崩溃与非确定性，抓不了任何数值错误 ⇒ 按 O-17 的要求，**不计入仪器条数**。

| 门控 | 该类检查 |
| --- | --- |
| `experiments/p10_gate.py` | `K6_determinism` |
| `experiments/p11_gate.py` | `Y5_determinism`、`Y6_random_control_reproducible` |
| `experiments/p12_gate.py` | `Z4_determinism` |
| `experiments/p13_gate.py` | `W6_determinism` |
| `experiments/p14_gate.py` | `G7_determinism` |
| `experiments/p16_gate.py` | `G7_determinism` |
| `experiments/p17_gate.py` | `G7_determinism` |
| `experiments/p18_gate.py` | `G7_determinism` |
| `experiments/p19_gate.py` | `G2_determinism` |
| `experiments/p3_gate.py` | `C7_determinism` |
| `experiments/p5b_gate.py` | `G6_determinism` |
| `experiments/p5d_gate.py` | `G3_determinism` |
| `experiments/p6_gate.py` | `K7_determinism` |
| `experiments/p7_gate.py` | `H6_determinism` |
| `experiments/p8_gate.py` | `J5_exact_instrument_determinism` |
| `experiments/p9_gate.py` | `G7_determinism` |
| `experiments/phase2_gate.py` | `C1_determinism` |

## 4 本表看不见的三类东西（写明，免得被当成完整清单）

1. **被执行、但被一条容差太粗的检查判定**：Phase XIII 的 W2 容差是「一个计数」，Phase V-d 的 G4 是 ±0.005 绝对。这些名字在表里显示为「已覆盖」，注入实验却证明它们对 1e-4 级的机制错误全盲。
2. **治理套件不在人口内**：`governance/*_gate.py` 用 `report()` 而非 `check()`，它们是工件审计，不是某一轮的仪器。
3. **不用 `check()` 的轮次门控**：`literature/l01_gate.py`、`literature/l02_gate.py`、`literature/l02_representation_gate.py`、`literature/l03_gate.py` 贡献 0 条 `check()`（它用自带的手段审计工件），本表对任何不使用 `check()` 的门控**沉默**——「表里没写」不等于「已覆盖」。

与注入套件的三条已登记失明（`expect="blind_all"`）的对账：

| 目标 | 本表的立场 |
| --- | --- |
| `p5b_gate.py :: gap_for` | predicted - imported and never reached |
| `p8_gate.py :: rho_exact` | predicted - reached only by a self-comparison |
| `p13_gate.py :: q_cont` | NOT a syntactic gap: W2 does call q_cont, its registered tolerance is one count, so the blindness is class 1 of this map (real condition, coarser tolerance) - only injection sees it |

两条本表也预测到、一条属于上面第 1 类。**这条对账是构建时硬校验**：新增的 `blind_all` 若既不被本表预测、也不登记在本表的盲区类里，构建直接失败。

## 5 本表自己撤回的一条假阳性（保留在此，因为它说明推导器的边界）

- 曾报 **p6_gate.py :: s3_window_exists imported but never called**；已撤回。门控调用 `s3_critical_beta`，其函数体内部调用 `s3_window_exists` ⇒ 该函数被执行，只是不按名字出现。推导器随后加入调用图闭包，此项自动消失。闭包后来又发现一个更隐蔽的同族风险（`p12_lattice` 自己`from p8_smooth import rho_exact` 却不调用），因此闭包已改为**跨模块**执行。

## 6 导入但从未读取的数据/常量（提示性，不计为缺口）

- `experiments/p5_gate.py`：`ARMS`、`DP_SPEC`、`QS`
- `experiments/p5b_gate.py`：`DTHETA_FACTOR`
- `experiments/p6_gate.py`：`DTHETA_FACTOR`、`Z95`

---

## 复现

```bash
python3 governance/build_coverage_map.py
python3 governance/gate_coverage_map_gate.py
python3 governance/gate_discrimination_gate.py   # 注入侧的互补仪器
```
