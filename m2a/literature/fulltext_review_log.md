# M2A Phase I′ 全文审查日志（Gate ②）

> 日期：2026-10-17 ｜ **21 条**达 FULLTEXT_REVIEWED（其中 3 条为 QUALIFIED）
> 获取：`oa_sweep.py`（Unpaywall，55 条带 DOI 中 24 条 OA）→ `fetch_fulltexts.py` / `retry_fulltexts.py` / `fetch_acl.py`
> 抽取：`review_fulltexts.py`（家族词表计数 + 最佳段落）｜ 身份核对：`check_text_identity.py` + 人工抽查开头
> 第三方全文存放于**仓库外** `E:\workshop\_m2a_ft`；本文件只做短句引用与自述转写。

---

## 1 方法（与 Phase I 的差别）

Phase I 全部止于 IDENTITY_VERIFIED（部分摘要级）。本轮对可开放获取的 21 条做到：

1. **取全文**：PMC → Europe PMC `fullTextXML`；出版方 PDF → pypdf；ACL Anthology → 直接 PDF；
2. **核身份**：抽取文本的开头必须与记录题名/作者一致（`check_text_identity.py` 的自动判定 +
   对 5 条 `SUSPECT` 的人工复核，均为同一篇）；
3. **核机制**：按该条标注的 K 族词表计数，并抽出**最佳段落**，判断论文是否真的承载该机制主张。

**关键区分（本轮新发现，须写入标注规则）**：K 族标注是**映射层**，不是论文自己的用词。
例如 `R02`（AMR）不以 "cascade" 描述其图结构，`G8-04`（ACE）以 "event/mention" 而非 "trigger" 表述。
⇒ 把"论文没出现这个词"当作"机制不成立"是错的；正确的核对是**看内容是否支持映射**。

---

## 2 逐条判定

| 记录 | 字符 | 家族 | 全文中的证据（短引/转写） | 判定 |
| --- | --- | --- | --- | --- |
| **R01** FrameNet | 19,557 | K1,K11 | 全文 `frame/evoke` 70 次；框架由动词唤起、词汇资源约束框架选择 | ✅ FULLTEXT |
| **R02** AMR | 28,872 | K8 | 单根有向图、谓词—论元结构（`graph/argument` 15 次）；"级联"是映射而非原词 | ✅ FULLTEXT |
| **R05** Seifert 2012 | 330,482 | K6,K11 | "measurement-based feedback processes and the relation between dissipation and irreversibility" | ✅ FULLTEXT |
| **R06** England 2013 | 22,423 | K1,K11 | `entropy/threshold` 16 次；自复制需要耗散条件 | ⚠ QUALIFIED：K11 强，K1 的"触发"是映射 |
| **R09** 共抑制综述 | 111,677 | K2,K4 | "IgSF co-inhibitory receptors use several mechanisms to inhibit T cell function" | ✅ FULLTEXT |
| **R13** Zimmerman 2025 | 200,960 | K5,K6 | "associate a stimulus (flavor) with a delayed reinforcement signal (postingestive feedback)" | ✅ FULLTEXT（机制逐字命中） |
| **R14** Burke 2026 | 136,487 | K5,K6 | "removal of up to 19 out of 20 cue–reward experiences has zero impact… if total conditioning time is maintained" | ✅ FULLTEXT（**间隔而非重复次数**，与本项目 K5 标注一致） |
| **R15** Gallistel & Shahan 2024 | 45,027 | K5,K12 | 用**前瞻/回溯互信息**度量反应—强化关联（式 [1][2]） | ✅ FULLTEXT |
| **R17** CFIR 实施科学 | 57,563 | K1,K2,K11,K12 | 干预/实施成本条目明确；触发/门控为解释性映射 | ⚠ QUALIFIED：K11 强，其余映射 |
| **R20** CBF 安全控制 | 137,404 | K2,K11 | "handle safety constraints with time and input constraints under disturbances" | ✅ FULLTEXT |
| **R24** CBF 构造技术 | 273,734 | K2,K7 | 安全集/约束构造；切换为控制律层面 | ✅ FULLTEXT |
| **G6-07** 实施成本 | 84,792 | K2,K11 | 成本/机会成本定义明确 | ✅ FULLTEXT |
| **G8-01** PropBank | 103,245 | K1,K10 | 角色识别/分类表（Role identification/classification） | ✅ FULLTEXT |
| **G8-03** UD v1 | 35,756 | K11 | 多语言树库资源约束；"资源不足以自动迁移" | ⚠ QUALIFIED：K11 为资源义 |
| **G8-04** ACE | 22,587 | K1 | `event/mention` 48 次；事件提及与触发结构 | ✅ FULLTEXT |
| **G8-05** GO 资源 | 35,821 | K11,K12 | 资源"essential but not sufficient" | ✅ FULLTEXT |
| **G8-08** 叙事事件链 | 35,098 | K1,K5,K8 | 事件间**时序关系**与 TimeBank 标注 | ✅ FULLTEXT（K5） |
| **X-K4-01** Kubin 1994 | 17,938 | K1,K4 | "IL-12 … has a strong **synergistic effect** with the B7/CD28 interaction" | ✅ FULLTEXT（逐字） |
| **X-K4-02** Ahonen 2004 | 57,310 | K1,K4 | "TLR/CD40 Triggering Elicits Long-Term, Antigen-specific CD8+ T Cell Immunity" | ✅ FULLTEXT |
| **X-K4-05** Cárcamo-Oyarce 2015 | 50,347 | K1,K3,K7 | "bacteria trigger the QS response only when their cell density has reached a certain threshold" | ✅ FULLTEXT |
| **X-K4-07** Bender 2006 | 80,505 | K4,K6 | "a single, postsynaptic NMDAR-based **coincidence detector** or multiple coincidence detector pathways" | ✅ FULLTEXT |

**统计**：21 条全文；**18 条 ✅**、**3 条 ⚠ QUALIFIED**；0 条被否证（没有一条论文与标注**内容**冲突，
冲突只出现在"术语 vs 映射"层面）。

---

## 3 未能取得全文的 OA 记录（给出理由，不静默跳过）

| 记录 | 情况 |
| --- | --- |
| `G8-07`（OBO Foundry, `10.1038/nbt1346`） | Unpaywall 标 green/PMC2814061，但 Europe PMC `fullTextXML` 返回 500，PMC 页面仅 167 字符 ⇒ **不可得** |
| `X-K4-03`（Fetsch 2011, `10.1038/nn.2983`） | PMC3398428 同上；机构库只给 3,172 字符的封面页 ⇒ **不可得** |
| `X-K9-05`（Knäuper 1996） | JBC 两个 PDF 端点均 403 ⇒ **不可得** |
| `X-K10-04`（Rico 2019） | 机构库连接超时（WinError 10060）⇒ **不可得** |
| `R18`（TREE 2019） | 出版方 PDF 403，Unpaywall 仅给着陆页 ⇒ **不可得** |
| `G8-06`（Wikidata, `10.1145/2629489`） | ACM 端点 403 ⇒ **不可得** |
| `R10`（PMC11598642） | Europe PMC XML 500、PMC PDF 123 字符 ⇒ **不可得** |

**精确账目**：Unpaywall 判定的 OA 记录共 **24** 条 → **17 条**读成全文、**7 条**不可得（上表）；
另有 **4 条** ACL Anthology 记录（`R02`/`G8-03`/`G8-04`/`G8-08`，无 DOI、不在 Unpaywall 扫描内）
经 `fetch_acl.py` 直接取得 ⇒ **17 + 4 = 21**。两组集合的差集已用脚本核对，
详见 `oa_index.json`、`fulltext_manifest.json` 与 `fulltext_review.json`。

---

## 4 全文审查**改变了什么**

| 变化 | 内容 |
| --- | --- |
| **证据级别** | `FULLTEXT_REVIEWED` 从 **0 → 21**（Phase I 的上限声明被打破，但仅对这 21 条） |
| **K5 的读法** | `R14` 全文给出的原句（去掉 19/20 次配对、只要总时间不变则无影响）**逐字支持**"间隔而非次数"——这比摘要级引用强得多 |
| **K4 的三形态** | `X-K4-01`（逐字 synergy）、`X-K4-02`（联合触发）、`X-K4-07`（coincidence detector）三条全文均可定位 ⇒ E1 的三个原型有全文级依据 |
| **标注规则需补一条** | 映射型标注（`R02`/`G8-04`/`R06` 的 K 族）必须在注册表中标明 **MAPPING**（相对 PAPER_TERM），否则下游会把"我们的词"误当成"论文的词" |

---

## 5 声明

- 本轮**未**把任何不可得全文的记录升级；它们保持原级别；
- `FULLTEXT_REVIEWED` 的含义是"**该条的机制主张已在全文文本中定位并核对**"，不等于
  `CLAIM_INDEPENDENTLY_CHECKED`（后者需要独立复现）；
- 抽取文本来自 PDF/XML 自动抽取，可能存在排版噪声；判定以**可定位的段落**为准，不以词频单独作结论。
