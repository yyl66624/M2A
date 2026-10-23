# L-02 表征层编码结果（`L02-O2`）

> 日期：2026-10-23 ｜ 规则登记：`literature/L02_REPRESENTATION_ADDENDUM.md`（SHA-256 `ec51c0b87cde…`，提交 `dab0bb5`，
> **先于本工件存在**）｜ 仪器：`literature/l02_representation_coding.py`（含 `--check`）｜ 门控：
> `literature/l02_representation_gate.py`（**16/16 checks passed**，full 模式；pre 模式 14/14）
> 本轮身份：**描述性编码**，无新实验、无新真实数据、无仿真；不修改 L-02 任何既有判据、读数或工件（R6）。

## 0 披露：正文取得先于附加件

本轮不是盲法预注册。PDF 在附加件写定之前已取得并人工读过（L-02 §8 的记录即为此事的起点），
附加件冻结的是**编码与引用规则**，不是「会看到什么」。因此下面的读数是「源文在此处说了什么」，
可被任何持有同一 SHA-256 正文的人逐字复核；它**没有确证地位**，也不能确认任何跨域主张。

## 1 一句话结论

六项定义性内容里五项 `STATED`、一项 `NOT_STATED`（`R-5`：`RCO` 的收敛条件）；合取主张 `H-R` 被否证
⇒ 出口 `REPRESENTATION_CODED`，五值标签 **REFUTED**。`L02-O2` 的**编码义务**由此落实：
表征层不再有「未编码」的定义项，缺的那一项是**源文没有给出**，不是本轮没有找到。

## 2 五值标签（R17）

| 问 | 出口 | 标签 | 依据打印行 |
| --- | --- | --- | --- |
| 表征层定义能否逐字恢复 | `REPRESENTATION_CODED` | **REFUTED** | `l02_representation_coding.py` 打印行，见 §3 |

正确读法：**编码完成了**，而编码所检验的合取主张被源文否证。它不是对论文质量的评价，也不改变
`ROUND_L02_RESULTS.md` 的任何判定；`L02-O1`（确证地位）**保持 OPEN**。

## 3 读数（只取打印行）

运行器正式写盘打印（`python3 literature/l02_representation_coding.py`）：

```
wrote L02_representation_coding.json | exit REPRESENTATION_CODED (REFUTED) | items 6 | stated 5 | not_stated ['R-5'] | text_sha256 83656c4e44864edd | binding match
```

工件 `literature/L02_representation_coding.json` 的 SHA-256 前缀 `c1d3f804fc701f0a`；
规范化正文 71 950 字符、SHA-256 前缀 `83656c4e44864edd`；PDF 3 261 118 字节、SHA-256
`998a608e506b286d…`（全文在仓库外 `_m2a_ft/L02_C-04_v2.pdf`，不提交）。

逐项读数（偏移与 `quote_sha16` 逐字对回工件；引文一律取自 `pdftotext -raw` 规范化文本）：

| 项 | 状态 | 引文（截断显示） | 偏移 | 字符 | `quote_sha16` |
| --- | --- | --- | --- | --- | --- |
| `R-1` | **STATED** | 「For this, we optimize an orthonormal basis … where all directions r ∈ RN satisfy the refusal properties (Theorem 4.1).」 | 20524 | 214 | `4413d5110eb3f85a` |
| `R-1` | **STATED** | 「Since all directions in the cone correspond to the same refusal concept, we also refer to this as a concept cone.」 | 20739 | 113 | `68f3985d547c727b` |
| `R-2` | **STATED** | 「we identify refusal–mediating cones with dimensions up to five across all tested models.」 | 23060 | 88 | `b3c6d244aa39fd0f` |
| `R-2` | **STATED** | 「Figure 19 reveals that ASR increases with cone dimensionality but plateaus at four dimensions.」 | 25526 | 94 | `8eb95f617c3e5635` |
| `R-3` | **STATED** | 「we project the basis back onto the cone using the Gram–Schmidt orthogonalization procedure」 | 22225 | 90 | `bcbb619a0f111986` |
| `R-4` | **STATED** | 「Definition 6.1. The directions λ, µ ∈ Rd are representationally independent … if:」 | 30613 | 178 | `cea56a7ea596f6c6` |
| `R-6` | **STATED** | 「This effect is reciprocal, suggesting that orthogonality alone does not guarantee independence throughout the network.」 | 29821 | 118 | `2df42cc6594d855d` |

`R-5` 的缺失检验（两个区间、12 个关键词、2 类数值写法，逐项零命中；唯一候选短语在 `A2_BODY` 内恰出现 1 次）：

| 区间 | 字符 | 块 SHA-256 前缀 | 12 词命中 | 数值命中 |
| --- | --- | --- | --- | --- |
| `A2_BODY` | 304 | `96e0f93dd8a7c0c2` | 0 | 0 |
| `A2_PROSE` | 925 | `6f2a99b212500e8c` | 0 | 0 |

`A2_BODY` 只覆盖 `Algorithm 2` 的伪代码；`A2_PROSE` 覆盖紧随其后的解释段。两个区间以外（附录复本等）
**不参与判定**，这是本轮声明的可主张范围。

## 4 与既有开放项的关系（只追加，不回写）

- **`L02-O2` 落实**：表征层的六项定义性内容逐项落定；缺的一项（`RCO` 的无判据收敛）是源文属性。
  台账由 `OPEN` 改为 `CLOSED`，理由是「已落实：表征层定义侧」，不是「已确认」。
- **`L02-O1` 保持 OPEN**：本轮没有换语料、没有新判据、没有确证地位；它要求的是一次带新判据的前瞻轮。
- **`L01-O1` / `L03-O1` 不动**：本轮不触碰注册层标注与 K7 的时间形态；两者各自等待新语料/新授权。
- 本轮不改变 `L02_coding.json` 的四条机制条目与 `CONTRADICTED` 判定；`R-4`/`R-6` 只是把 L-02 §5
  的 `UNDECIDABLE` 引文扩到定义层，没有给任何机制条目重铸 `ρ`。

## 5 不对称性与看不见什么

- 只对 **v2** 的 SHA-256 负责；v1/v3 的措辞可能不同，结论不外推。
- 引文是 `pdftotext 22.02.0` 线性化文本的逐字，不是排版逐字形：上标/下标被拉平（`Rd`、`PN i=1`）。
- `NOT_STATED` 是**关于两个声明区间的否定**，不是「论文没有收敛判据」的全域命题：附录、代码仓库、
  补充材料都不在本轮证据里。若判据写在那些地方，本轮不改口，但也不声称覆盖。
- 「最多五维 / 四维饱和」是论文在其被测模型上的报告，不是对任意模型的定律；本轮只编码「它这样写了」。
- 本轮不检验论文的实现是否真的收敛，也不复跑 `RCO`；`R-5` 的后果（无判据的停止规则可能使复现依赖
  运行预算）是一条**待检验的开放问题**，不是本轮的结论。

## 6 复现

```bash
python3 literature/l02_representation_gate.py --pre   # 12 rules + 2 self-counts, 14/14
python3 literature/l02_representation_coding.py --check
python3 literature/l02_representation_coding.py       # 先跑 pre 门控，再两路绑定附加件；不过则 rc=4
python3 literature/l02_representation_gate.py         # full: 14 rules + 2 self-counts, 16/16
```
