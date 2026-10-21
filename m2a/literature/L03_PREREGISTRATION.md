# Round L-03 预注册（先注册，后取文本与编码）

> 日期：2026-10-21 ｜ 依据：`governance/OWNER_DECISION_2026-10-18.md` 第 4 条（文献研究：全文机制编码、
> 独立核验、竞争理论比较）与 `literature/ROUND_L01_DISPOSITIONS.md` 的 `L01-O5`（`R13-N15` 全文仍不可得）。
> 授权边界：新建本文件与 `literature/L03_*`、追加 `ROUND_L01_DISPOSITIONS.md` 的处置行、追加负面日志；
> **不**改 `literature/L01_coding.json`、`literature/ROUND_L01_RESULTS.md`、`registry.json`、`synthesis_v2.json`、
> `expansion_registry.*`、`07_CONTRADICTIONS_AND_COUNTEREVIDENCE.md` 的既有行，**不**跑新实验、**不**做跨系统实施、
> **不**改任何既有预注册哈希（R6 与各轮判定各自保持）。

## 0 轮次身份

| 项 | 值 |
| --- | --- |
| 轮次名 | Round L-03（文献轮，非仿真轮） |
| 上游工件 | `literature/L01_coding.json` 的 `R13-N15` 记录（摘要级，`ABSTRACT_VERIFIED`）、`literature/L01_fulltexts.json` 的 `R13-N15` 条目（预览页 5 374 字节）、`literature/L01_CODING_PROTOCOL.md`（字段契约与引文要件）、`literature/L02_PREREGISTRATION.md` §2.3（全文长度地板 21 224） |
| 编码字段契约 | 逐字沿用 L-01 §2 的字段集与三条增补（引文可定位、`PAPER_TERM`/`MAPPING` 二分、级别封顶） |
| 随机性 | 本轮无随机数、无种子池（检索、抽取与编码均为确定性读取）⇒ R4「不相交种子」条款不适用，登记为 N/A |
| 产物 | `literature/L03_coding.json`、`literature/l03_coding.py`、`literature/l03_gate.py`、`literature/run_L03.py`、`literature/ROUND_L03_RESULTS.md`；正文文本在仓库外 `_m2a_ft/L03_R13-N15.txt`，取得记录在同目录侧车 `L03_R13-N15.acquire.json` |
| 零检验地位 | Q1 是新数据（此前只有 5 374 字节的预览页，没有正文）⇒ 可确证「全文级编码与摘要级编码一致」这一件，不确证锚点主张本身，也不把预印本升为同行评议证据 |

## 1 本轮问的唯一问题（Q1）

`R13-N15`（Senapati B., Treiber C. D., Waddell S., "Visceral signaling of post-ingestive malaise directs
memory updating in Drosophila", bioRxiv 2025.10.21.683769, posted 2025-10-22）的**全文**能否取回，若取回，
全文级编码与 L-01 的摘要级编码（K5 主族、K7/K10 辅族，`d_axis` 依次为 D−/D−/D+）是否一致？

本轮不重判 L-01 的任何读数，不把摘要级记录升级或改写；新记录写在 `L03_coding.json`，以**追加**方式与
`R13-N15` 的旧记录并列。`L01-O5` 的关闭只表示「全文已取回并按注册判据编码」这一件事，不表示旧记录的级别
被改写（R6：旧记录与旧轮判定各自保持）。

## 2 取文本的通道（按序，先写死；每条记录状态码与字节）

只接受能给出**正文**的开放通道；预览页、摘要页、题录 API、补充材料清单都不算全文。按下列顺序尝试，
第一个成功取得正文的通道即停止；后续通道不再尝试，避免把「多通道取回」变成事后择优。

| 序 | 通道 | 入口 | 接受条件 |
| --- | --- | --- | --- |
| C1 | Europe PMC 免费全文 HTML | `https://europepmc.org/article/PPR/PPR1106376` 的 `#fulltextcontent` 容器 | 页面含正文各节、参考文献与 DOI；抽取后经 §3.1 归一化 |
| C2 | Europe PMC OA PDF | `https://europepmc.org/api/fulltextRepo?pprId=PPR1106376&type=FILE&fileName=EMS210035-pdf.pdf&mimeType=application/pdf&version=1` | PDF 可下载且 `pdftotext` 抽取 ≥ 地板；仅在 C1 失败时尝试 |
| C3 | bioRxiv 官方 JATS XML | `https://www.biorxiv.org/content/early/2025/10/22/2025.10.21.683769.source.xml` | XML 正文可解析；仅在 C1、C2 都失败时尝试 |
| C4 | bioRxiv 官方 PDF | `https://www.biorxiv.org/content/10.1101/2025.10.21.683769v1.full.pdf` 与早期路径 `.../content/biorxiv/early/2025/10/22/2025.10.21.683769.full.pdf` | PDF 可下载且抽取 ≥ 地板；仅在 C1–C3 都失败时尝试 |
| C5 | 已发表版本的开放全文 | 由 Crossref/OpenAlex 解析到的期刊 DOI；仅接受 Europe PMC/PMC OA 或出版商明确 OA 的正文 | 仅在 C1–C4 都失败时尝试；预印本 DOI 本身不算已发表版本 |

补充规则：

1. 若 C1 在浏览器通道可读、但命令行直连被 Cloudflare 以 429/403 拒绝，取得记录必须同时写下**两条读数**
   （命令行状态码与浏览器成功读数），不得只写成功的一条；这正是「仪器的位置是读数条件」。
2. 同一通道只尝试一次；失败后不得用不同 User-Agent、代理、镜像或缓存反复重试。重试属于下一轮，须先注册。
3. 取回的正文只能来自一个通道；不得把多个通道的文本拼接成一份「更完整」的正文。
4. 正文文本与侧车都放在仓库外；仓库内只存哈希、长度、引文与偏移。第三方全文不入库。

### 2.1 正文抽取与归一化（先写死）

C1 的抽取对象是 `#fulltextcontent` 容器的可见文本。归一化只做四件事，顺序固定：

1. 把 CRLF/CR 统一成 LF；
2. 去掉每行行尾空白；
3. 把三个及以上连续换行压成两个；
4. 去掉首尾空白。

不替换 Unicode 引号、不改写连字符、不做词形还原、不删除参考文献。归一化后的文本写入
`_m2a_ft/L03_R13-N15.txt`，其 SHA-256 与字符数写入侧车与 `L03_coding.json`。C2/C4 的 PDF 若被使用，
用 `pdftotext -layout` 抽取后走同一归一化。

## 3 判据与容差（冻结于任何正文读数之前）

### 3.1 身份判据

取回文本必须同时满足：

- 归一化文本包含 DOI `10.1101/2025.10.21.683769`（逐字）；
- 题名规范化（小写、压缩空白、去掉首尾标点）后与 L-01 记录的题名**完全相等**；
- 作者姓氏 `Senapati`、`Treiber`、`Waddell` 三者都在文本中出现。

任一不满足 ⇒ `IDENTITY_MISMATCH`，不编码。

### 3.2 全文长度地板

沿用 `L02_PREREGISTRATION.md` §2.3 由 L-01 已提交工件推导的数：**21 224 字符**（L-01 的 14 条
`FULLTEXT_REVIEWED` 全文最小长度）。该数在本轮任何取回动作之前已存在于已提交工件中，不由本篇的实际长度
决定。低于此值 ⇒ `BELOW_FLOOR`，不得进入全文级编码。

### 3.3 引文要件

每条机制条目必须带：

- `quote`：20–400 字符，逐字摘自归一化文本；
- `quote_offset`：该字符串在归一化文本中的字符下标；
- `quote_sha16`：该引文 UTF-8 字节的 SHA-256 前 16 位十六进制。

门控按字节复核：引文必须在文本中、必须唯一、必须在给定下标处、长度必须在 20–400。任何一条对不上即判
**仪器缺陷**（不是证据不足），本轮结果不得写盘。

### 3.4 核心比较集与关系标签

核心比较集固定为 L-01 记录的三条：K5（primary，D−）、K7（auxiliary，D−）、K10（auxiliary，D+）。
对每条核心条目，在全文里找一段支持同一机制主张的段落，并按下列**唯一**规则给关系：

- `CONFIRMED`：全文段落支持同一机制族与同一方向（同号；若 L-01 记 `mixed`，全文段落必须同样呈现双向结构）；
- `REVISED`：全文段落支持该机制族，但方向、主/辅角色或作用域与 L-01 记录不同（逐条写出差异）；
- `UNSUPPORTED`：按 §3.5 的检索规则找不到支持段落。此档是「全文未见」，不是「全文反驳」；
- `REFUTED`：全文有段落**明确主张** L-01 的方向命题不成立。只有明确的反向主张才算，沉默、省略、
  或只换术语不算。

可以额外编码核心集之外的机制条目（如 K2/K6/K8），但必须单列为 `ADDITIONAL`，不进入核心集的
`c/r/u/f` 计数，也不改变出口。

### 3.5 「找不到」的检索规则（先写死，避免以搜索能力冒充文本事实）

对每条核心条目，用来定位支持段落的检索词固定为该条 L-01 `claim` 中的机制词与下列词表的交集：

- K5：`credit assignment`、`delayed`、`post-ingestive`、`consolidation`、`update`；
- K7：`switch`、`switches`、`reversal`、`avoidance`、`approach`、`consolidation`；
- K10：`serotonin`、`serotonergic`、`dopaminergic`、`safety`、`suppress`、`invert`。

检索不区分大小写，只用于定位候选段落；最终是否 `CONFIRMED` 仍由人读该段落并逐字引用来判定。
若候选段落为空，记 `UNSUPPORTED` 并打印检索词；不得扩大词表、不得改用摘要、不得把预览页当正文。

### 3.6 主读数

`c` = `CONFIRMED` 的核心条目数，`r` = `REVISED`，`u` = `UNSUPPORTED`，`f` = `REFUTED`；
四者之和必须等于 3。另打印：全文长度、核心引文数、附加条目数、每条的检索词命中数。

## 4 出口表（按序取第一个可触发项；七档都可达，含「全都不满足」那一档）

| 序 | 出口 | 条件 | R17 标签 |
| --- | --- | --- | --- |
| 1 | `FULLTEXT_CONFIRMS` | 正文取回、身份通过、长度 ≥ 21 224、≥3 条核心条目各有合法引文，且 `c=3, r=0, u=0, f=0` | SUPPORTED（只支持「全文级编码与摘要级编码一致」，不支持锚点主张或跨域迁移） |
| 2 | `FULLTEXT_REVISES` | 正文取回并编码，`r ≥ 1` 且 `f = 0` | INDETERMINATE（摘要级编码不是全文级编码；写出逐条差异） |
| 3 | `FULLTEXT_PARTIAL` | 正文取回并编码，`u ≥ 1` 且 `r = 0, f = 0` | NOT_IDENTIFIED（对 `u` 条而言；`L01-O5` 的取回义务可关闭，但编码缺口另立 `L03-O1`） |
| 4 | `FULLTEXT_REFUTES` | 正文取回并编码，`f ≥ 1` | CONTRADICTED（只对 L-01 的对应机制条目，不对锚点） |
| 5 | `FULLTEXT_BELOW_FLOOR` | 身份通过但长度 < 21 224，或引文无法按字节定位 | NOT_IDENTIFIED（不得以短文本或摘要冒充全文；`L01-O5` 保持开放） |
| 6 | `FULLTEXT_IDENTITY_MISMATCH` | 取回文本的题名/作者/DOI 不符 | NOT_IDENTIFIED（不编码；`L01-O5` 保持开放） |
| 7 | `FULLTEXT_NOT_OBTAINED` | C1–C5 全部失败 | NULL（停机档；逐条列出通道、状态码与失败原因；`L01-O5` 保持开放） |

## 5 停机规则（写在看到读数之前）

1. 出口 5/6/7 一旦触发即停：不编码、不重试其他通道、不把预览页或摘要升级为全文；`L01-O5` 保持开放，
   本轮只登记失败通道与原因。
2. 出口 1–4 触发后，`L01-O5` 可按「全文已取回并按注册判据编码」关闭；旧记录 `L01_coding.json` 的级别与
   文本一字不改，新记录单列。若出口 2/3/4，另立 `L03-O1` 记录编码差异，不把差异写回 L-01。
3. 任何出口一旦按序触发即终止 Q1 的判定；看完读数再重排出口、补一档、换口径，一律禁止。
4. 发现实现缺陷：跑之前发现 ⇒ 登记 `L03-A<n>` 并改代码后重跑门控；跑之后发现 ⇒ 只做零检验地位的
   reanalysis，写入 `L03_reanalysis.json`，不改原工件、不改原判定。

## 6 不对称性与看不见什么

- 本轮的「确认」只到**同一预印本内部**的摘要级与全文级编码一致；它不证明论文的机制主张为真，也不把
  预印本升为同行评议证据。
- 看不见：论文的补充材料（Supplementary Figures）只按正文引用计数，不另行编码；图注中的定量读数不进入
  机制条目；作者未写进正文的意图不推断。
- 检索词表只用于定位，不能把「词没出现」当成「机制不存在」；`UNSUPPORTED` 的语义已在 §3.4 限定为
  「按固定检索规则未见支持段落」。
- 同一篇论文只有一份正文；不存在第二个独立语料来复核编码本身。编码的独立性由门控的字节复核与第二通路
  （引文哈希、下标、唯一性）承担，不由第二篇论文承担。

## 7 本轮不做什么

1. 不改 `L01_coding.json`、`ROUND_L01_RESULTS.md`、`registry.json`、`synthesis_v2.json`、`SYNTHESIS_V2.md`、
   `expansion_registry.*`、`07` 各条裁定；
2. 不新增真实数据统计、不跑仿真、不做跨系统实施；
3. 不把 `R13-N15` 的编码升为对锚点的最终裁定；只做机制层的文本核对；
4. 本文件落盘并提交后一字不改；缺陷只登记 `L03-A<n>` 或负面日志（R6）。

## 8 哈希绑定

本文件落盘后先提交；`L03_coding.json` 记录本文件的 SHA-256（`prereg_sha256`），并同时对**磁盘字节**与
**`git show HEAD:m2a/literature/L03_PREREGISTRATION.md` 对象**校验。取回的正文哈希只写入仓库外的侧车与
`L03_coding.json`，不把正文入库。产物写盘之前不得有任何编码读数；`l03_gate.py` 在编码前运行，失败即拒绝
写盘。

（本文件**不自载哈希**：把自身的 SHA-256 写进正文会让写完的那一行立刻改动被哈希的字节，绑定就成了假的。
权威做法是先提交本文件，再由产物记录哈希并由门控复核两条通路。）
