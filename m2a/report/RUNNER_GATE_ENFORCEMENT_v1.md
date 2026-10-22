# _runner 侧门控强制表 v1（由 `governance/build_runner_enforcement_map.py` 从 runner 源码推导）

> 依据：§42 的覆盖表把结论建立在「runner 会在门控不过时拒绝执行」这条规则上，而这条规则此前**只由 runner 自己的 docstring 承载**（文字）。本表把它变成语法事实。生成物：本文件与 `governance/runner_enforcement_map_v1.json`。不跑实验、不改工件、不改任何轮次判定。

## 1 三个判定

* **执行了门控**：存在一条 subprocess 调用，其参数点名某个 `*_gate.py`；
* **拒绝真的会停**：针对返回码的 `if` 守卫，其体内有 `return <非零>` / `sys.exit` / `raise`——注意守卫可以隔一层（Phase XIV 的 `run_gate()` 自己返回 rc，真正的拒绝在调用处）；
* **写盘在守卫之后**：所有工件写入的行号都晚于守卫，于是门控红了也不会留下 results 文件。

人口：**31 个工件写入者**，写 **31 个**已提交 JSON。判定：**enforced 27**、其它 0、登记在册的无门控 4。

## 2 逐行结果

| runner | 门控 | 守卫 | 写入 | 判定 |
| --- | --- | --- | --- | --- |
| `experiments/p5_v1_posthoc.py` | — | — | p5_v1_posthoc.json@68 | `no_gate_at_all` |
| `experiments/p6_reanalyze.py` | — | — | phase6_reanalysis.json@34 | `no_gate_at_all` |
| `experiments/r7_closure_report.py` | — | — | r7_closure_report.json@87 | `no_gate_at_all` |
| `experiments/run_phase10.py` | p10_gate.py@85 | 87（停） | phase10_results.json@142 | `enforced` |
| `experiments/run_phase11.py` | p11_gate.py@170 | 172（停） | phase11_results.json@200 | `enforced` |
| `experiments/run_phase12.py` | p12_gate.py@31 | 33（停） | phase12_results.json@124 | `enforced` |
| `experiments/run_phase13.py` | p13_gate.py@148 | 150（停） | phase13_results.json@185 | `enforced` |
| `experiments/run_phase14.py` | p14_gate.py@29 | 31（不停！）；39（停） | phase14_results.json@131 | `enforced` |
| `experiments/run_phase15.py` | p15_gate.py@30 | 32（不停！）；39（停） | phase15_results.json@122 | `enforced` |
| `experiments/run_phase16.py` | p16_gate.py@30 | 32（不停！）；39（停） | phase16_results.json@132 | `enforced` |
| `experiments/run_phase17.py` | p17_gate.py@28 | 30（不停！）；37（停） | phase17_results.json@139 | `enforced` |
| `experiments/run_phase18.py` | p18_gate.py@27 | 29（不停！）；36（停） | phase18_results.json@137 | `enforced` |
| `experiments/run_phase19.py` | p19_gate.py@22 | 24（停） | phase19_results.json@91 | `enforced` |
| `experiments/run_phase2.py` | phase2_gate.py@134 | 137（停） | phase2_results.json@147 | `enforced` |
| `experiments/run_phase20.py` | p20_gate.py@17 | 19（停） | phase20_results.json@76 | `enforced` |
| `experiments/run_phase21.py` | p21_gate.py@21 | 23（停） | phase21_results.json@81 | `enforced` |
| `experiments/run_phase22.py` | p22_gate.py@21 | 23（停） | phase22_results.json@76 | `enforced` |
| `experiments/run_phase24.py` | p24_gate.py@69 | 50（停）；72（不停！） | phase24_results.json@162 | `enforced` |
| `experiments/run_phase3.py` | p3_gate.py@116 | 118（停） | phase3_results.json@127 | `enforced` |
| `experiments/run_phase4.py` | p4_gate.py@101 | 103（停） | phase4_results.json@112 | `enforced` |
| `experiments/run_phase5.py` | p5_gate.py@190 | 192（停） | phase5_results.json@207 | `enforced` |
| `experiments/run_phase5b.py` | p5b_gate.py@28 | 30（停） | phase5b_results.json@85 | `enforced` |
| `experiments/run_phase5c.py` | p5c_gate.py@20 | 22（停） | phase5c_results.json@81 | `enforced` |
| `experiments/run_phase5d.py` | p5d_gate.py@21 | 23（停） | phase5d_results.json@65 | `enforced` |
| `experiments/run_phase6.py` | p6_gate.py@93 | 95（停） | phase6_results.json@126 | `enforced` |
| `experiments/run_phase7.py` | p7_gate.py@26 | 28（停） | phase7_results.json@107 | `enforced` |
| `experiments/run_phase8.py` | p8_gate.py@22 | 24（停） | phase8_results.json@80 | `enforced` |
| `experiments/run_phase9.py` | p9_gate.py@205 | 207（停） | phase9_results.json@231 | `enforced` |
| `literature/run_L01.py` | l01_gate.py@40 | 43（停） | L01_coding.json@178 | `enforced` |
| `literature/run_L01_reanalysis.py` | — | — | L01_reanalysis.json@200 | `no_gate_at_all` |
| `literature/run_L03.py` | l03_gate.py@28 | 33（停）；55（停） | L03_coding.json@52 | `enforced` |

## 3 登记在册的无门控写入者（每条都必须写明为什么合法）

- `p5_v1_posthoc.py`：事后重分析：读已提交的 `phase5_results.json`，写的是自己的 `p5_v1_posthoc.json`（零检验地位，R6），不属于任何一轮的门控时序（X-32 一族）。
- `p6_reanalyze.py`：Phase VI 的 reanalysis：在已提交读数上重算，另写 `phase6_reanalysis.json`，原轮判定与门控记录一字不动（R6）。
- `r7_closure_report.py`：R7 闭合报告：只在已提交工件（Phase VIII/XII/XIII 的 results）上做逐字比对，把比对结果写进 `r7_closure_report.json`；它是报告不是某一轮的读数，故无门控时序。
- `run_L01_reanalysis.py`：L-01 主张层重判读：输入是已提交的 `L01_coding.json`，输出 `L01_reanalysis.json` 标注 `ZERO_TEST_REANALYSIS`；该轮的门控由 `run_L01.py` 在编码时执行过（`l01_gate.py`），重判读不得重跑门控（R6）。

## 4 本表看不见的东西

1. **守卫只保证「本轮不写」，不保证「本轮的门控真的测了判据」**——那是 §42 覆盖表负责的层面。两张表合起来才说完整：门控被跑（本表）且门控里确有读数量具（覆盖表）。
2. **行号顺序是保守近似**：写盘在函数 `main()` 的更深处时，行号晚于守卫并不能证明运行时一定在守卫之后（异常路径、循环内的提前返回）。因此「写盘在守卫之后」只用作**筛查漏报**的线索，不作为独立结论；结论只看前两条。
3. **治理套件的构建脚本不在人口内**（`governance/build_*.py`）：它们写的是治理工件而非某轮的读数。

---

## 复现

```bash
python3 governance/build_runner_enforcement_map.py
python3 governance/runner_gate_map_gate.py
```
