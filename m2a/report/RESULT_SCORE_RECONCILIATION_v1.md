# 门控分数三方对账 v1（文档引用 ↔ 仪器实跑 ↔ 静态站点数）

> 生成物：本文件与 `governance/result_score_reconciliation_v1.json`。不跑实验、不改任何轮次文档与判定；`live` 这一列就是**跑一次门控**。

## 1 三个数不是同一个东西

* **claim**：轮次文档开头那一行写的分数（`门控 \`p10_gate.py\` **6/6**`）；
* **live**：这台门控今天被跑到时打印的 `n/N checks passed`；
* **static**：§42 覆盖表按语法数出的 `check()` **站点数**（全库 169）。

两个数会分开，本库现有两例（都已登记，见 §3.1）：一条写在 `for` 里的 `check()` 只有一个站点、却打印多条判定（`p17_gate.py`：6 站点 / 7 判定）；不使用 `check()` 的自带仪器在静态普查里记 0（`l01_gate.py`：0 站点 / 7 判定）。这就是为什么 §42 那句「169 条 `check()`」必须被读作**站点数**而不是执行量。

人口：**25 份轮次文档**；判定：**aligned 23**、已登记的静态口径差 2、坏判定 0、无分数声明 0。执行侧共打印 **169** 条判定，本表人口内 25 台仪器静态共 **161** 个站点（§42 全库 26 台是 169 个——**两个总数相等不代表同一件事**，见 §1 末尾的抵消说明）。

## 2 逐轮对账

| 文档 | 仪器 | 文档引用 | 实跑 | 静态站点 | 判定 |
| --- | --- | --- | --- | --- | --- |
| `PHASE10_RESULTS.md` | `experiments/p10_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE11_RESULTS.md` | `experiments/p11_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE12_RESULTS.md` | `experiments/p12_gate.py` | 4/4 | 4/4 | 4 | `aligned` |
| `PHASE13_RESULTS.md` | `experiments/p13_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE14_RESULTS.md` | `experiments/p14_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE15_RESULTS.md` | `experiments/p15_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE16_RESULTS.md` | `experiments/p16_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE17_RESULTS.md` | `experiments/p17_gate.py` | 7/7 | 7/7 | 6 | `loop_nested` |
| `PHASE18_RESULTS.md` | `experiments/p18_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE19_RESULTS.md` | `experiments/p19_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE20_RESULTS.md` | `experiments/p20_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE21_RESULTS.md` | `experiments/p21_gate.py` | 8/8 | 8/8 | 8 | `aligned` |
| `PHASE22_RESULTS.md` | `experiments/p22_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE2_RESULTS.md` | `experiments/phase2_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE3_RESULTS.md` | `experiments/p3_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE4_RESULTS.md` | `experiments/p4_gate.py` | 5/5 | 5/5 | 5 | `aligned` |
| `PHASE5B_RESULTS.md` | `experiments/p5b_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE5C_RESULTS.md` | `experiments/p5c_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE5D_RESULTS.md` | `experiments/p5d_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE5_RESULTS.md` | `experiments/p5_gate.py` | 8/8 | 8/8 | 8 | `aligned` |
| `PHASE6_RESULTS.md` | `experiments/p6_gate.py` | 7/7 | 7/7 | 7 | `aligned` |
| `PHASE7_RESULTS.md` | `experiments/p7_gate.py` | 9/9 | 9/9 | 9 | `aligned` |
| `PHASE8_RESULTS.md` | `experiments/p8_gate.py` | 6/6 | 6/6 | 6 | `aligned` |
| `PHASE9_RESULTS.md` | `experiments/p9_gate.py` | 8/8 | 8/8 | 8 | `aligned` |
| `ROUND_L01_RESULTS.md` | `literature/l01_gate.py` | 7/7 | 7/7 | 0 | `other_harness` |

## 3 登记在册的例外

### 3.1 静态站点数与打印判定数不可比（每一条都必须写明类别与原因）

- `p17_gate.py`（类别 `loop_nested`）：G1 的锚定比较写在 `for` 里（两条口径各一次），静态 6 个站点、执行 7 条判定。§42 的 169 是**站点数**，门控打印的是**判定条数**：本表把两个数放在一起，免得「169」被当成执行量引用。
- `l01_gate.py`（类别 `other_harness`）：文献轮的 `l01_gate.py` 不使用 `check()`——它自带断言并打印 `7/7 checks passed`，所以 §42 的静态普查对它记 0。这是「两数不可比」，不是缺失：§42 的 §4 第三条已声明本库对不使用 `check()` 的门控**沉默**。

### 3.2 文档未声明分数

- 无。若某轮文档删掉了分数行而未登记，构建直接失败。

## 4 本表看不见的东西

1. **分数对得上不代表门控量了判据**——那是 §42 覆盖表的层面；本表只管三个数是否互相一致。
2. **`live` 是今天的读数**：文档写的是当时的读数。本轮全部一致，但这条检查的意义在于「amendment 之后忘了改文档」那一天会立刻红。
3. **只覆盖 `n/N checks passed` 这种打印格式**（与收尾审计同一契约，X-68）。

---

## 复现

```bash
python3 governance/build_result_score_reconciliation.py           # 跑到实跑一遍门控
python3 governance/build_result_score_reconciliation.py --offline  # 复用已记录分数
python3 governance/result_score_map_gate.py
```


### 1.1 两个总数相等，却是两条不同的抵消

文档人口内 25 台仪器的静态站点数之和是 **161**；§42 的 26 台（多出 `ao_preflight_gate.py` 的 8 条）是 **169**。而执行侧打印总数同样落到 **169**：161 + `l01_gate.py` 的 7（静态记 0）+ `p17_gate.py` 多出的 1（循环内站点）= 169。**只比总数会同时抹平这两处口径差**，所以本表逐台比对，不对总数。
