# Round L-03 结果｜`R13-N15` 全文取回与全文级编码（`L01-O5` 关闭；K7 记为 REVISED）

> 日期：2026-10-21 ｜ 判据登记：`literature/L03_PREREGISTRATION.md`（SHA-256 `29bb39fbef77…`，**先于任何正文读数提交**，提交 `77c4bb1`）｜门控 `l03_gate.py` **20/20**（full；pre 13/13，只验仪器；退出档与计数互锁）｜运行器：`literature/run_L03.py`（pre 门控不过即拒跑；写盘前对磁盘字节与 `git show HEAD:` 对象两路绑定）｜编码器：`literature/l03_coding.py`
> 本轮身份：Q1 是**新数据**（此前只有 5 374 字节的预览页，没有正文）⇒ 可以确证「全文级编码与摘要级编码是否一致」这一件；不确证论文的机制主张本身，也不把预印本升为同行评议证据。L-01 的旧记录与旧轮判定一字未改（R6）。

## 0 运行前更正登记（先于编码读数）

| 编号 | 原声明 | 错在哪 | 改成什么 | 为什么这不算事后调整 |
| --- | --- | --- | --- | --- |
| `L03-A1` | 预注册 §2 要求逐条记录通道状态码与字节 | 侧车第一次写入时 `attempts` 字段是 `null`，只有一句自然语言说明；C1 的命令行 429 与浏览器 200 两条读数没有落到机器可读字段 | 编码前把五条通道读数补进侧车（C1 命令行 429；C2 403；C3 浏览器 `ERR_FAILED (-2)`；C4 429；C1 浏览器 200，`#fulltextcontent`，117 489 字节 / 116 345 字符）；正文的 `chars`、`bytes`、`text_sha256` 一字未动 | 补记发生在任何编码读数之前；判据、容差、出口表与正文哈希均未改变；补的是「仪器读数存在哪里」，不是读数本身 |

## 1 一句话结论

`R13-N15` 的全文已从 Europe PMC 的 C1 浏览器通路取回（归一化后 116 342 字符，身份三项全过），按预注册 §3.4 编码三条核心机制：K5、K10 为 `CONFIRMED`，K7 为 `REVISED`（全文把「离散相位反转、不是渐降」改成 120 min 内快速下降、6 h 转为相对回避，并把 24 h 选择归因于对 CS− 的 safety memory）。因此 Q1 走第 2 档 `FULLTEXT_REVISES`，五值标签 **INDETERMINATE**；`L01-O5` 按 §5.2 关闭为「全文已取回并按注册判据编码」，差异另立 `L03-O1`，L-01 记录不回写。

## 2 五值标签（R17，逐条对回 `L03_coding.json`）

| 问 | 出口 | 本轮标签 | 依据打印行 |
| --- | --- | --- | --- |
| Q1 全文与摘要级编码是否一致 | `FULLTEXT_REVISES` | **INDETERMINATE** | `run_L03.py` 的 `L03 reading:` 打印行 |

## 3 读数（只取打印行）

pre 门控：

```
13/13 checks passed
```

full 门控：

```
20/20 checks passed
```

运行器：

```
L03 reading: exit FULLTEXT_REVISES | core c=2 r=1 u=0 f=0 | fulltext 116342 chars >= 21224 | quotes 6 | additional 2 | label INDETERMINATE
L03 obligations: L01-O5 CLOSED | L03-O1 OPEN
L03 artifact sha256: a75684f50888176ab8e98419cdfefa08862517608c348437247edc8d50e46ea0
```

- 工件 `literature/L03_coding.json`，22 169 字节，SHA-256 前缀 `a75684f50888176a`。
- 正文文本在仓库外 `_m2a_ft/L03_R13-N15.txt`：116 342 字符 / 116 893 字节，SHA-256 `8be1559ff9d4c7c03a6c9969a448a4d8cb3bc22c973f74aef3b766371355514b`；取得侧车 `_m2a_ft/L03_R13-N15.acquire.json`。第三方正文不入库。
- 预注册绑定：磁盘 `29bb39fbef77…` = `git show HEAD:m2a/literature/L03_PREREGISTRATION.md` `29bb39fbef77…`，`prereg_binding.match = true`。

## 4 三条核心条目与两条附加条目

每条引文在归一化正文中出现且仅出现一次；下标与 `quote_sha16` 由门控 `G6` 逐字节复核。

| k | 类别 | role | d_axis | 关系 | 引文（截断显示） | 下标 | 字符 | `quote_sha16` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `K5` | CORE | primary | `D−` | **CONFIRMED** | 「This SA memory timeline is consistent with flies forming a sugar reward memory…」 | 11057 | 146 | `caee848107de2d05` |
| `K7` | CORE | auxiliary | `D−` | **REVISED** | 「In contrast, SA trained flies initially showed strong approach…」 | 10828 | 228 | `be3f6c91f5ddc84e` |
| `K10` | CORE | auxiliary | `D+` | **CONFIRMED** | 「The DPM blocking experiments therefore demonstrate that 15-30 min after training…」 | 16410 | 207 | `544e3506eeb0b54e` |
| `K5` | ADDITIONAL | additional | `D−` | CONFIRMED | 「Our work here suggests that DPM neuron released 5-HT can extend…」 | 43666 | 202 | `4dcf507022d6d2c1` |
| `K10` | ADDITIONAL | additional | `D+` | CONFIRMED | 「Development of 24 h CS- approach required excitatory 5-HT7 receptors…」 | 52819 | 159 | `59cb05b742de308e` |

K7 还带一条支撑引文（门控同样按字节复核）：下标 57549，163 字符，`quote_sha16` `8af6a8b6e2a47df5`，原文为「24 h after training behavior appears to be solely directed by a safety memory for the non-food paired odor – no CS+ approach or avoidance was evident at this time.」

### 4.1 K7 的差异（`L03-O1` 的来源）

- L-01 的 K7 claim：行为是「离散的相位反转开关，不是渐降」，且「只有过巩固窗后」才把 CS+ 的反应切换成回避，属于双稳态、时间门控的反转。
- 全文读数：CS+ 的接近在训练后 **120 min 内快速下降**，6 h 转为回避（CS+ vs CS− 选择）；但 CS+ vs 新异气味在 2 h 已无偏好；24 h 的行为被明确写成由对 CS− 的 safety memory 单独驱动，并写明「no CS+ approach or avoidance was evident at this time」。
- 保留：接近→相对回避的方向、巩固窗依赖、以及「延迟的 post-ingestive 信号改写先前气味记忆」这一机制族。
- 差异：时间形态（快速下降 vs 离散相位反转）与 avoidance 的作用域（相对 CS− 的选择 vs CS+ 的绝对回避记忆）。按预注册 §3.4，这属于 `REVISED`，不是 `REFUTED`——论文的摘要句本身仍写「switches to avoidance」，全文没有一句明确主张「接近不会转向回避」；它明确的是「24 h 的 CS+ 绝对回避不可见」。因此不把 K7 记成反证。

## 5 `L01-O5` 的关闭与 `L03-O1` 的开放（只追加，不回写）

- **`L01-O5` 已关闭**（按 L-03 §5.2，出口 2 属于出口 1–4）：`R13-N15` 全文已按 L-03 预注册取回并编码；关闭的只是「全文已取回并按注册判据编码」这一件事。L-01 的 `ABSTRACT_VERIFIED` 级别、三条摘要级 claim 与 `ROUND_L01_RESULTS.md` 的判定一字未改。
- **`L03-O1` 仍开放**：K7 的全文级编码与 L-01 的摘要级 claim 在时间形态与 avoidance 的作用域上不同。差异已写进 `L03_coding.json` 的 `differences` 与本文件 §4.1；把它写回 L-01 或重下 L-01 的判定不在本轮权限内（R6），需要 owner 决定是否以一次新轮次重判 K7。
- `L01-O1` 仍开放（owner 权限表禁止改 `registry.json`）；`L02-O1`、`L02-O2` 仍开放（L-02 的零检验地位与表征层定义缺口，本轮未处理）。

## 6 不对称性与看不见什么

- 本轮的「一致 / 不一致」只到**同一预印本内部**的摘要级与全文级编码；它不证明论文的机制主张为真，也不把预印本升为同行评议证据。
- 看不见：补充材料（Supplementary Figures）只按正文引用计数，不另行编码；图注中的定量读数不进入机制条目；作者未写进正文的意图不推断。
- 检索词表只用于定位候选段落；`CONFIRMED` / `REVISED` 由人读段落并逐字引用判定。`UNSUPPORTED` 本轮未触发，但这不表示全篇没有遗漏——它只表示按 §3.5 的固定词表未见支持段落。
- 同一篇论文只有一份正文，不存在第二个独立语料复核编码本身；编码的独立性由门控的字节复核（引文唯一、下标、哈希）承担，不由第二篇论文承担。
- C1 的命令行通路被 Cloudflare 以 429 拒绝，正文来自同一 URL 的浏览器 DOM；两条读数都已写进侧车。这不等于「浏览器渲染一定等于 PDF 排版」——公式、图注与版式不在本轮编码范围内。

## 7 复现

```bash
python3 literature/l03_gate.py --pre     # 13/13，只验仪器；不过则拒跑
python3 literature/run_L03.py            # 先 pre，再两路绑定，写盘后 full 20/20
python3 literature/l03_gate.py --full    # 20/20；不需要网络，正文在仓库外缓存
```

## 8 开放项登记（2026-10-21，只追加）

- **`L03-O1`** 仍开放：K7 的全文级编码与 L-01 摘要级 claim 的差异（时间形态、avoidance 的作用域）需要 owner 决定是否以新轮次重判；本轮只登记差异，不回写 L-01（R6）。
- **`L01-O1`** 仍开放：把 R13 的注册层标注升为全文级要改 `registry.json`，owner 权限表禁止。
- **`L02-O1`**、**`L02-O2`** 仍开放：L-02 的同批读数只有否证地位；表征层定义侧未编码。
