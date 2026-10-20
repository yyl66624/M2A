# Round L-02 结果｜主张层一致性判据 + `neutral` 零值口径 + 竞争理论全文编码

> 日期：2026-10-20 ｜ 判据登记：`literature/L02_PREREGISTRATION.md`（SHA-256 `c143a08b5740…`，**先于任何读数提交**，
> 提交 `f4fbbfd`）｜仪器：`literature/l02_gate.py`（16/16 checks passed，只验仪器；规则清单钉在门控的 `RULES` 常量上，条数与打印判定互锁）｜运行器：`literature/l02_reanalysis.py`
> （门控不过即拒跑；写盘前对磁盘字节与 `git show HEAD:` 对象两路绑定）
> 本轮身份：Q1/Q2 是**零检验地位的重判读**（同一批 L-01 读数，不重跑、不改原工件、不改原判定，R6）；
> Q3 是本轮唯一的新取回与编码。本轮不新增真实数据统计、不跑仿真、不做跨系统实施。

## 0 运行前更正登记（A1–A5 先于任何读数提交；A6–A11 在工件第一次写盘之后、读数写入本记录之前或同时发现，每一条都注明它能不能改变读数（见各行第四列），不是判据松动）

| 编号 | 原声明 | 错在哪 | 改成什么 | 为什么这不算事后调整 |
| --- | --- | --- | --- | --- |
| `L02-A1` | 用 `C_surface − C_claim` 作主读数 | 两个量不是同一个估计量：`C_surface` 是 L-01 `exit_table` 里逐字取用的 `C_signed`，`C_claim` 在**全部** 14 行上数，相减会把「主张层新看见的支持」当成负数抵扣（X-83 同一个坑） | 主读数改为 `Δ` = # { s ∈ `S` : ρ(s) ∉ {SUPPORTS, EXTENDS} }，`S` 取 L-01 自己标的 `same-family-same-axis` 行集；`C_claim` 降为披露量，单独打印且**不进** `Δ` | 干跑阶段暴露，读数未落盘；改后判据更严（只数「计入而不支持」），不改任何容差数值 |
| `L02-A2` | 整轮停线按 L-01 的比例（10/14）折算到本轮分母 | 换口径等于换判据：L-01 的 10 是**绝对**下限，不是比例 | 停线保持绝对数 10，并在 §2.3 写明「本轮分母是 17 条重判读行，10 不随分母移动」 | 提交前改定；绝对数比折算值（12）更松还是更严与结果无关，因为它不参与 Q1/Q2 的触发 |
| `L02-A3` | 字段契约按 `L01_coding.json` 的键名逐字检查 | L-01 的工件用的是 `sid`/`title`，协议 `02` §2.2 写的是 `case_id`/`reference`；逐字检查会把 17 行全判成缺字段，把一次真实的命名分歧伪装成编码缺陷 | 显式声明别名 `case_id→sid`、`reference→title`，并把「哪两个协议名是靠别名满足的」打印出来 | 别名是我方文档之间的事，与任何读数无关；不声明就会造出 17 条假缺陷 |
| `L02-A4` | 「门控按字节复核」未声明行尾口径 | 挂载把 `local_cache` 通道的一份全文存成 CRLF（`_m2a_ft/R14.txt` 有 138 个 `\r\n`），而 L-01 的清单按 LF 记 `sha256`/`chars`、引文下标也按 LF 计数：按原始字节复核时 R14 的哈希与长度都对不上，第 2 条引文的下标偏 26 | 声明复核基准＝解码后把 `\r\n`/`\r` 折成 `\n` 的文本；在该基准上 `sha256` 前缀、`chars`、每条引文的 `quote_offset` 与 `quote_sha16` 必须**全部逐字命中**，且取消「引文在别处也能找到」的降级通道 | 这条只把「按字节」写成可复现的口径，判据方向不变；折行尾的行如实打印（`line-endings folded ['R14']`），不改写 `_m2a_ft` 里任何文件 |
| `L02-A5` | 字段契约要求 12 个字段全部非空 | 已冻结的 L-01 工件里 12 行把 `contradiction_ref` 记为 `null`（语义是「本案不引用任何矛盾」），而 `02` §2.2 从未声明该字段可否为空；按「必须非空」检查就是 12 条红，按「看不见就当没有」检查就是把真实分歧洗白 | 契约改为「12 个键必须全部在场 ＋ 其中 11 个必须非空」，并把 12 条 `null` 行**逐行列名打印**；该分歧登记为对上游工件的开放项（负面日志 `X-98`），不给绿勾 | R6 禁止回写 `L01_coding.json`；把不可回写的既有事实写成「登记的缺口」而不是「通过」或「12 条新缺陷」，是唯一不撒谎的实现 |
| `L02-A6` | 写盘前对磁盘字节与 `git show HEAD:` 做两路绑定，并把 `prereg_binding` 记进产物 | 绑定算在序列化**之后**：`blob` 先冻结、再往 `doc` 里塞 `prereg_binding`、最后写的是旧 blob——第一次落盘的 `L02_reanalysis.json` 里根本没有那个字段（读回来是 `None`），等于产物在声称一次它体内没有的绑定 | 把两路哈希算在序列化之前，`prereg_binding.two_channel_match` 由实算值得出；`--check` 模式同时打印 binding 是 match 还是 MISMATCH | 这条只让产物真正携带它声称的绑定，不增加也不减少任何读数；重跑后 17 个键逐字节相同，唯一新增就是 `prereg_binding`；第一次落盘字节的 SHA-256 前缀是 `3da87493dbdbef0b`（把两行代码还原回去即可复现那批字节），最终工件的 SHA-256 记在 §3 |
| `L02-A7` | §3 Q2 注册口径：只有零值支撑的机制主张记 `NEUTRAL_UNDECIDABLE` 并**从 `C_claim` 中排除** | 实现里漏了排除：`neutral_only` 只用来数 `Z`，`SUPPORTS/EXTENDS` 分支照样把该行加入 `C_claim`，于是注册的口径在本语料上不改变任何数（`C_claim = 8`）；同时 `NEUTRAL_UNDECIDABLE` 这个标签在工件里无处落地 | 加入 `and not neutral` 的谓词，并新增 `neutral_undecidable_rows` / `rules_disagree_rows` 两个具名字段；`C_claim` 由 8 变 7，`Δ/X/U/Z` 与两条出口一字未动 | 这条是把我注册的判据**实现出来**，不是改判据：改动方向是把主张收紧（少计一行），且把代价如实打印（门控 `G12` 用第二条通路复算，指出 R14-N8 既是 L-01 计入的 `S` 行、又被主张层排除）|
| `L02-A8` | §3 Q3 第 1 档的标签格写的是「按 ρ 实际读数的方向给 `SUPPORTS` / `REFUTES` / `MIXED`」 | 那一格用了 ρ 的词表，而 R17 要求标签取五值；照字面实现会产出一个五值之外的标签，`MIXED` 也没有定义「几条反证加几条不可判」算不算混合 | 映射写死并打印输入：只有 ρ 取向的行参与投票（§2.1 明确 `UNDECIDABLE` 与 `UNRELATED` 不带方向），全为 `REFUTES` ⇒ `CONTRADICTED`，全为支持/扩展 ⇒ `SUPPORTED`，两边都有 ⇒ `INDETERMINATE`，没有一行取向 ⇒ `NOT_IDENTIFIED`；工件同时记 `directional_votes` 与 `label_derivation` | 这是在把注册的说法翻译成 R17 的词表，不是换判据：投票集合与实读数一致（3 条反证、0 条支持），本档的出口与标签在任何一次实现版本下都是 `COMPETING_CODED`；`MIXED` 这个词从未产出过读数 |
| `L02-A9` | 全文走 `local_cache` 时沿用清单里钉住的哈希即可，不必再取网络 | 工件的 `obtain_attempts` 被第二次运行覆盖成只剩 abs 页一条：正文「是怎么进来的」（哪个 URL、什么状态码、多少字节）从工件里消失了，`local_cache` 成了一句没有出处的自述 | 取回正文时把入库凭证写进同目录侧车 `L02_C-04.acquire.json`（仓库外），`local_cache` 运行必须从侧车读出取得记录；侧车缺失时重新取一次，只有**哈希相同**才接受缓存并补写侧车，不同则如实记 `DIVERGED` | 该修正在 Q3 第一次写盘之后、读数写进本记录之前发现：重取后正文 SHA-256 与钉住的相同（`RESTORED_BY_REFETCH`），两次运行的出口、条目数、偏移一字未变；顺带得到一条仪器事实——同一 URL 的 HTML 在两次抓取之间从 329 790 字节变成 331 545 字节，而抽取正文的哈希不变，说明剥离只看标记不看页面装饰 |
| `L02-A10` | §3 Q3 的出口表写了三档：编码成功 / 身份通过但抽取不足 / 取回失败 | 表**不完备**：「取回成功但题名与登记的不是同一篇」没有归属。L-01 的 `L01-A3` 恰好真踩过这个状态（选择器先挑中了 Rocchi 那篇同名不同文的论文）；把它折叠进「取回失败」会让一次选错看起来像一次诚实的 NULL | 新注册第 4 档 `COMPETING_IDENTITY_MISMATCH`（NULL，并把两个题名都打印出来），门控 `G13` 用探针确认四档都可达且状态空间里没有未登记的出口 | 登记在 Q3 读数之后，但该分支从未被触发（实读 overlap = 1.0），因此不可能改变本轮任何结论；新增一档只会多接住一种状态，不会把已经落进低档的读数抬上来（与 §45 同向） |
| `L02-A11` | 门控 12 条规则覆盖绑定、冻结输入、词表、字段契约、引文定位、阈值可推导、出口可触发、写盘拒绝 | Q3 的仪器（`l02_coding.py`）在门控里没有对应的可推翻检查——它说的话（身份、地板、下标、标签）此前只有它自己的一面之词 | 加 `G13`（离线探针：身份判别能分开 L-01 选错的那篇、状态空间只落已登记出口、标签只取五值）与 `G14`（把工件对回它引用的文件：逐条下标命中、引文唯一、`quote_sha16` 重算、正文哈希与`chars` 相同、取得记录钉的是同一批字节、出口由第二条通路复算），并把 `G8` 的普查人群扩到本轮新增的那一行 | 读数之后加检查只能**多找问题**，不可能把已红洗成绿（§45 的论证），且新检查全部要求工件与外部文件相符，不允许工件自证 |

`L02-A1`…`A7` 都在本轮读数写进 §1–§3 之前提交；出口判定（`Δ`、`X`、`U`、`Z`）在 A6/A7 前后逐字相同，唯一移动的数是被 A7 实现出来的披露量 `C_claim` 8→7。第一次落盘字节的 SHA-256 前缀是`3da87493dbdbef0b`，其内容除 `prereg_binding` 缺失外与最终工件逐键相同。

## 1 一句话结论

`Δ` 合计 `3`（逐锚点 `G5-03` 2、`R13` 0、`R14` 1），G5-03 与 R14 两个锚点各自至少有一行「L-01 计入而主张层不支持」
⇒ Q1 走第 1 档；`Z` = 2 ⇒ Q2 走 `Z ≥ 1` 一侧；Q3 读数 `COMPETING_CODED` 第 1 档。

## 2 五值标签（R17，逐条对回 `L02_reanalysis.json`）

| 问 | 出口 | 本轮标签 | 依据打印行 |
| --- | --- | --- | --- |
| Q1 主张层一致性 | `CLAIM_LAYER_INFLATION` | **CONTRADICTED** | `l02_reanalysis.py` 打印行 `exit_q1` |
| Q2 `neutral` 零值口径 | `NEUTRAL_ZERO_IS_NOT_A_BOUNDARY` | **CONTRADICTED** | 打印行 `exit_q2` |
| Q3 竞争理论 | `COMPETING_CODED` | **CONTRADICTED** | `l02_coding.py` 打印行（见 §5） |

## 3 Q1/Q2 读数（只取打印行）

运行器 `--check` 干跑打印：

```
check-only digest 15ef980b319482bb | rows judged 14 | totals {"C_surface": 5, "S_rows": 6, "delta": 3, "C_claim": 7, "X": 1, "U": 0, "Z": 2} | per-anchor delta {"G5-03": 2, "R13": 0, "R14": 1} | binding match
```

正式写盘打印：

```
wrote L02_reanalysis.json | exit_q1 CLAIM_LAYER_INFLATION (CONTRADICTED) | exit_q2 NEUTRAL_ZERO_IS_NOT_A_BOUNDARY (CONTRADICTED) | totals {"C_surface": 5, "S_rows": 6, "delta": 3, "C_claim": 7, "X": 1, "U": 0, "Z": 2} | per-anchor delta {"G5-03": 2, "R13": 0, "R14": 1}
```

- 最终工件 `literature/L02_reanalysis.json` 的 SHA-256 前缀 `15ef980b319482bb`；第一次落盘字节的 SHA-256 前缀是 `3da87493dbdbef0b`，两者逐键相同，唯一差别就是 `L02-A6` 补进正文的 `prereg_binding`。
- `C_claim` = 7。关掉 `L02-A7` 的排除则是 8：14 行里 ρ 读作 SUPPORTS/EXTENDS 的共 8 行，其中 1 行是「只有零值支撑」，被排除后主张层少计 1 行（另一行 `R14-N4` 的 ρ 是 UNRELATED，本来就不进 `C_claim`）。被排除而 ρ 又读作支持的行是 `R14-N8`（锚点 R14），它同时落在 L-01 自己计入的 `S` 里，所以两条注册口径在这一行方向相反——该事实按行名进入工件（`rules_disagree_rows`），不折算成任何一个数字。
- 出口判定在 `A6`/`A7` 前后一字未动：`Δ` = 3、`X` = 1、`U` = 0、`Z` = 2。
- `C_surface` = L-01 `exit_table` 里逐字取用的 `C_signed` 之和；`S_rows` = L-01 自己标注 `same-family-same-axis`
  的行数；两者在 R14 上不等（`C_signed = 1` 而 `|S| = 2`），这正是 `L02-A1` 记下的分歧，**不得**相减。
- `X`（ρ = REFUTES）与 `U`（ρ = UNDECIDABLE）逐锚点出处：`X` = 1：`G5-03-N6`（锚点 G5-03）引文「Contrary to prior assumptions …」 ｜ `U` = 0：无该行。
- `Z`（mechanism 条目全为 `d_axis = neutral` 的行）逐行出处：`R14-N4`（ρ=UNRELATED，1 条 mechanism 的 `d_axis` 全为 `neutral`，级别 FULLTEXT_REVIEWED，锚点 R14）；`R14-N8`（ρ=SUPPORTS，3 条 mechanism 的 `d_axis` 全为 `neutral`，级别 FULLTEXT_REVIEWED，锚点 R14）。

## 4 与 L-01 开放项的关系（只追加，不回写）

- `L01-D3`（`C` 是上界还是点值）：`Δ ≥ 1` 说明「族+符号」这一计入规则里确实存在主张层不支持的行，
  因此 L-01 的 `C_signed` 作为**支持计数**被否证过一次；这不改动 L-01 任何一簇的 `INDETERMINATE`（R6）。
- `L01-O2`：本轮 `U` = `0`。本轮把 ρ 注册成了字段并跑完它的读法，所以 `L01-O2` 要求的**前置**（先注册新字段，再谈改判据）已完成。该义务保持 **OPEN**：把 L-01 三簇的判定换成主张层口径重下不在本轮权限内（R6：旧判定各自保持），关闭它需要 owner 决定是否把 ρ 写进 `02_ANNOTATION_RULES.md` 的判据文本。
- C-04（竞争理论）：只以 Q3 的新行**追加**，旧行不回写；Q3 的读数不足以最终裁定锚点。

## 5 Q3 竞争理论全文编码

身份：abs 页题名与 `L01_channels.json` 登记的 C-04 题名 token overlap = `1.0`（首作者 Tom Wollschläger，arXiv 2502.17420v2）。
正文通道 `local_cache`，取得记录 `RESTORED_BY_REFETCH`（侧车在仓库外 `_m2a_ft/L02_C-04.acquire.json`）；抽取正文 71382 字符 ≥ 注册地板 21224 ⇒ 级别 `FULLTEXT_REVIEWED`。

编码 4 条机制条目，每条的引文在抽取正文中**出现且仅出现一次**，下标与哈希可字节复核：

| k | role | d_axis | ρ | 引文（逐字，取自抽取正文） | 下标 | 字符 | `quote_sha16` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K2` | primary | `mixed` | **REFUTES** | 「We establish that refusal behaviors can be better understood via high-dimensio…」 | 35216 | 204 | `de8dd9bad8935f83` |
| `K3` | primary | `mixed` | **REFUTES** | 「Contrary to prior work, we uncover multiple independent directions and even mu…」 | 2465 | 129 | `28f2b77cae63ccdf` |
| `K4` | auxiliary | `mixed` | **REFUTES** | 「Additionally, we introduce representational independence and show that within …」 | 35421 | 187 | `59062884baf9b456` |
| `K10` | auxiliary | `value-only` | **UNDECIDABLE** | 「Moreover, we show that orthogonality alone does not imply independence under i…」 | 2595 | 199 | `12e2e706e7b6d34e` |

锚点侧的主张文本用的是论文自己转述的那句（ `Prior work suggests that a single refusal direction in t`…），它被记为 `target_characterization` 而**不是**机制条目：
那句话转述的是锚点的立场，不是本篇的主张，给它铸一个 ρ 就是让一行造出它声称登记的主张（X-85(g) 同族）。

读法：取向的 3 行全为 `REFUTES`（`directional_votes` = REFUTES,REFUTES,REFUTES），`UNDECIDABLE` 一行不参与投票——它攻击的是「由正交推独立」这一步推理，本身不断言拒绝方向的数量。按 `L02-A8` 的映射 ⇒ 本轮 Q3 标签 `CONTRADICTED`；
这与 G5-03 锚点行自己记录的引文（「this single direction is both necessary and sufficient」）构成正面冲突，
因此 C-04 的处置在本节**追加**如下限定，旧行不回写（R6）：

> 追加（L-02 Q3）：C-04 的一侧（Concept Cones）在全文层面主张拒绝由多维锥与多条机制独立方向介导，并对「正交⇒独立」的推断给出否证；据此 C-04 的**表征层**读法应记为「单一方向」不充分。该读数不足以最终裁定哪一侧正确——它是主张层关系，不是实验复验——因此 `07` 各条裁定一字未动，可主张范围照 §6 收窄。

Q3 打印行：

```
wrote L02_coding.json | exit_q3 COMPETING_CODED (CONTRADICTED) | overlap 1.0 | channel local_cache | chars 71382 | entries 4 | directional votes REFUTES,REFUTES,REFUTES | unlocatable none | target quote occurrences 1 | acquisition RESTORED_BY_REFETCH
```

看不见什么：本轮只核了**题名级**身份（abs 页），作者名单/单位靠登记处的转述；正文由 arXiv 的 LaTeXML HTML 抽取，行内数学被标记剥离吞掉（工件的 `extraction_note` 写明），因此所选引文一律落在不含数学的行上——这不是补救，是约束：任何跨公式的主张本轮不予编码。锥的维度定义、RCO 算法的收敛条件这类内容留在看不见之列。

## 6 不对称性与看不见什么

- `Δ` 只能把行从「计入」移到「不计入」，因此它**能**制造 `CLAIM_LAYER_INFLATION`，也能因 `U > 0` 自我否决；
  不存在「放宽到全绿」的通道，第 4 档 `NOT_IDENTIFIED` 就是出口。
- ρ 是「论文主张之间」的关系，不是「论文是对的」的判定；`EXTENDS` 不重复计为支持。
- 看不见：`registry.json` 的注册层标注（本轮权限外）、锚点主张的跨域迁移、任何需要新实验才能定的事；
  Q1/Q2 的确证地位为零（同批读数只能否证，不能确证）。
- §43 的「runner 先跑门控，门控红即拒跑」在本轮是**反方向**的：门控要在 `--check` 与篡改探针里调用运行器，运行器再回头调用门控就会成环。本轮的拒跑由运行器自己承担（绑定不过 ⇒ `rc=4` 且不写盘，`G11` 证明它），而 `l02_coding.py` 每次运行都要重取 abs 页做身份核验，正文才允许走本地缓存——身份不缓存，因为「这是不是登记的那篇」正是最容易被陈旧缓存掩盖的一步。
- 门控 `G7` 打印的 `line-endings folded` 只说明「哪份文本需要折行尾才能对上清单」，不说明该文本的内容是否
  与 L-01 判读时一致——那需要仓库外的原件，本轮不声称拥有。

## 7 复现

```bash
python3 literature/l02_gate.py            # 16/16，只验仪器；离线可跑（Q3 检查读工件与仓库外正文）
python3 literature/l02_reanalysis.py --check
python3 literature/l02_reanalysis.py      # 先两路绑定预注册哈希，不过则 rc=4 不写盘
python3 literature/l02_coding.py --extract  # 取回并落仓库外正文（有缓存且哈希对得上则不取正文）
python3 literature/l02_coding.py            # 同样先绑定预注册哈希
```
