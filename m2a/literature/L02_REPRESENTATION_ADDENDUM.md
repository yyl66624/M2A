# L-02 表征层编码附加件（落实 `L02-O2`）

> 日期：2026-10-23 ｜ 父轮：`literature/L02_PREREGISTRATION.md`（SHA-256 `c143a08b5740…`，先于 L-02 任何读数提交）
> 与 `literature/ROUND_L02_RESULTS.md` §8 的 `L02-O2`
> 本附加件**不修改**父轮任何判据、读数、判定或工件（R6）；它是 `L02-O2` 的独立承载工件。
> 本轮不跑仿真、不取新的真实数据、不启动任何实验；只对一份已取得的公开全文做规则先行的**描述性编码**。

## 0 披露：正文取得先于本附加件

`ROUND_L02_RESULTS.md` §5 记录：L-02 Q3 的正文来自 arXiv 的 LaTeXML HTML，行内数学在标签剥离时被吞掉，
因此锥的维度、`RCO` 的收敛条件这类内容**没有被编码**（`L02-O2`）。

本附加件改用同一篇论文的 PDF 版（`https://arxiv.org/pdf/2502.17420v2`）。
该 PDF 在**本附加件写定之前**已取得并人工读过。因此本件**不是**一次盲法预注册：

- 冻结的是**编码与引用规则**（编哪些项、什么算 `STATED`、什么算 `NOT_STATED`、引文与缺失如何复核），
  不是「我会看到什么」；
- 本轮读数只有**描述地位**：源文某处说了什么，可被任何持有同一 SHA-256 正文的人逐字复核；
- 本轮**没有确证地位**——它不能确认任何跨域主张，也不能把 L-02 的 `CONTRADICTED` 抬成 `SUPPORTED`；
  与 L-02 §6 对 Q1/Q2 的裁定同构。

## 1 被检验的合取主张

**H-R**：`L02-O2` 点名的表征层内容——锥的维度、`RCO` 的收敛条件——**连同**该层其余四项定义性内容，
都可以从源文的明述文本中逐字恢复。

六条合取项 `R-1…R-6`，登记如下。每条要么 `STATED`（存在一段 20–400 字符、在规范化正文中**出现且仅出现一次**
的逐字引文），要么 `NOT_STATED`（在 §3 登记的区间内，登记的关键词**零命中**；且唯一候选短语的出现次数被记录）。
不允许第三种状态：`UNLOCATABLE` 属于仪器缺陷，会把整轮降级为 `REPRESENTATION_PARTIAL`，不会静默变成 `NOT_STATED`。

| 项 | 内容 | 判据 | 结论由什么决定 |
| --- | --- | --- | --- |
| `R-1` | 锥的定义：正交基 `B` 张成 `N` 维多面体锥 `R_N = {Σλ_i b_i \| λ_i ≥ 0}\{0}`，且锥内所有方向满足拒绝性质（定理 4.1）；同一锥内的方向被称作 **concept cone** | 引文一遍命中 | 正文 |
| `R-2` | 观察到的锥维度：所有被测模型可达「最多五维」，且在四维处饱和 | 引文一遍命中（两条） | 正文 |
| `R-3` | `RCO` 的构造：Gram–Schmidt 把基投影回锥 | 引文一遍命中 | 正文 |
| `R-4` | RepInd 定义 6.1：在逐层余弦相似度意义上，消融一个方向不改变另一个方向的表达 | 引文一遍命中 | 正文 |
| `R-5` | `RCO` 的**收敛条件**：`while not converged` 是否有可复核的数值判据（容差、最大迭代、相对变化、停止规则） | 区间内零命中 ⇒ `NOT_STATED`；任一命中 ⇒ `STATED` | 正文 |
| `R-6` | 「正交不蕴含独立」：网络后层中消融仍会间接降低另一方向，正交性本身不保证独立 | 引文一遍命中 | 正文 |

`R-5` 是本轮唯一允许落 `NOT_STATED` 的项，因为它的判据是**缺失**；其余五项若 `NOT_STATED`，那是引文没找对，
属于仪器缺陷（`REPRESENTATION_PARTIAL`），不是源文缺失。

## 2 正文身份与提取口径

| 项 | 值 |
| --- | --- |
| 文件 | `_m2a_ft/L02_C-04_v2.pdf`（仓库外，不提交第三方全文） |
| 字节数 | `3261118` |
| SHA-256 | `998a608e506b286ddb047996add9eb86aeca51afa36f3eba125089607249d534` |
| 论文 | *The Geometry of Refusal in Large Language Models: Concept Cones and Representational Independence*（Wollschläger et al.），arXiv `2502.17420v2` |
| 提取器 | `pdftotext -raw`，poppler `22.02.0` |
| 规范化 | 折 `\r\n`/`\r` → `\n`；行尾连字符换行 `-\n` 接词时去掉连字符；所有空白折叠为单个空格；首尾去空白 |
| 引文坐标 | 一律记在**规范化正文**上的字符下标；`quote_sha16` = 引文 UTF-8 字节 SHA-256 的前 16 位十六进制 |

PDF 的 SHA-256 是身份；规范化正文的 SHA-256 是工件的读数（由提取器与规范化规则共同决定，重跑必须逐字节相同）。
`-raw` 而不是 `-layout` 的理由：`-layout` 保留双栏并排，一句话会被另一栏的行打断，引文无法跨行命中；
`-raw` 按内容流顺序输出，先左栏后右栏。代价是上标/下标被拉平（`Rd`、`PN i=1`），因此引文是
**「pdftotext 22.02.0 的线性化文本」逐字**，不是排版的逐字形复刻；这一限制写进工件，不当作源文的措辞。

## 3 `R-5` 的缺失检验（先登记区间与关键词）

两个区间（都取自规范化正文，端点均须恰好命中一次）：

| 区间 | 起点（含） | 终点（不含） |
| --- | --- | --- |
| `A2_BODY` | `Algorithm 2 Refusal Cone Optimization (RCO)` | `1: function SAMPLE(B)` |
| `A2_PROSE` | `In Algorithm 2, we describe the procedure` | `Can we find refusal concept cones?` |

关键词（大小写不敏感、词边界匹配，两个区间分别统计）：
`tol`、`tolerance`、`threshold`、`patience`、`max_iter`、`max iter`、`max-iter`、`epsilon`、
`convergence criterion`、`stopping criterion`、`relative change`、`gradient norm`。

另记唯一候选短语 `while not converged do` 的全文出现次数（预期 2：算法 1 与算法 2 各一次）与区间 `A2_BODY` 内次数（预期 1），
以便「没有判据」不被误读成「没有循环」。`A2_PROSE` 覆盖论文对算法 2 的散文解释；若数值判据只写在解释里，
同样算 `STATED`。两个区间之外（例如附录的伪代码复本）**不**参与判定——这是本轮声明的可主张范围，不是全域。

## 4 出口表（先于工件登记）

| 档 | 条件 | 出口 | 五值标签 |
| --- | --- | --- | --- |
| 1 | 六项全部落定（五条引文一遍命中；`R-5` 的区间与零命中可复核） | `REPRESENTATION_CODED` | 六项全 `STATED` ⇒ `SUPPORTED`；否则 `REFUTED` |
| 2 | 任一项引文不唯一/找不到，或区间端点不唯一，或词表外状态 | `REPRESENTATION_PARTIAL` | `NOT_IDENTIFIED` |
| 3 | PDF 存在但 SHA-256 不符 | `REPRESENTATION_SOURCE_MISMATCH` | `NULL` |
| 4 | PDF 不存在 | `REPRESENTATION_SOURCE_MISSING` | `NULL` |

标签推导只由合取项决定：`H-R` 只要有一条合取项 `NOT_STATED` 就整体被否证（`REFUTED`）；
本轮预期 `refuting_items = ["R-5"]` 是**读数**，不是预写结论——若区间内出现任一关键词，`R-5` 落 `STATED`，
标签随之为 `SUPPORTED`。两种结果都按出口表取，不做事后改档。

`REPRESENTATION_CODED / REFUTED` 的正确读法是：**编码完成了**，而被编码的合取主张被源文否证
（`RCO` 没有可复核的收敛判据）。它关闭的是 `L02-O2` 的**编码义务**，不是「源文有缺陷」这一价值判断；
`L02-O2` 关闭后，`L02-O1`（确证地位）**保持 OPEN**。

## 5 反例与自我否证

本轮**主动寻找能推翻自己结论的反例**，不靠「搜索没发现」冒充证明：

1. **判据写在别处**：若收敛判据只出现在正文对算法 2 的解释段（`A2_PROSE`）而不是伪代码里，`R-5` 必须落 `STATED`。
   该区间是为此设的；两个区间都零命中才允许 `NOT_STATED`。
2. **循环即判据**：若 `while not converged` 被某个数值条件填充（如误差 < 1e-6），关键词表能抓住
   `epsilon`/`threshold`/`tol` 一类写法，且 `\d(e-|\.\d)` 形式的数值判据由 `R-5` 的复核脚本逐字符扫描。
3. **我自己的编码错**：若任一引文在正文中出现两次，或偏移对不上，则本轮不是「源文缺失」，而是仪器坏了 ⇒ 出口 2。
4. **另一版本**：v1/v3 可能有不同措辞。本轮只对 `v2` 的 SHA-256 负责；不得把结论外推到其他版本。

## 6 复现

```bash
python3 literature/l02_representation_gate.py     # 只验仪器，离线；打印 n/n checks passed
python3 literature/l02_representation_coding.py --check
python3 literature/l02_representation_coding.py   # 先两路绑定本附加件，不过则 rc=4 不写盘
```

正文在仓库外；仓库内只提交哈希、长度、引文与偏移。
