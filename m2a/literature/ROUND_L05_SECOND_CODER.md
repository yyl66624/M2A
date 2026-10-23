# Round L-05 结果：21 篇全文的 I1 双编码审计

> 日期：2026-10-23 ｜ 预注册 `literature/L05_PREREGISTRATION.md`（sha256 `5114653224211c3c618259bf5ea6a4fba39a1a3a70bb8ba53927e91065b3b157`）｜
> 门控 `literature/l05_gate.py` **12/12 checks passed** ｜ 工件 `literature/L05_SECOND_CODER.json`（sha256 `4590b35cd66fa0c6e9ac240dc5118e54122e74e8effd4752b93ffeb509f9a323`）｜
> 第二编码者文件 `scratch/l05_second.md`（仓库外，sha256 `0e25f82a92e127a2…`）。
> 轮次身份：双编码描述性审计；只读已取得的 21 篇全文；不取新数据、不改任何既有编码或判定。

## 0 运行打印行

```
wrote L05_SECOND_CODER.json | exit L05_DENOMINATOR_EMPTY (REFUTED) | agree 21/21 | raw 1.0 | kappa UNDEFINED
```

## 1 一句话结论

主编码者与独立上下文的第二编码者都对 **21 篇全文给出 `NEITHER`**（21/21 一致，Cohen's κ `UNDEFINED`，因为两侧边际方差为零）。
按预注册口径，出口 **`L05_DENOMINATOR_EMPTY` / `REFUTED`**：**这 21 篇不构成 I1 的证据基础**。
这不是“I1 被 21 篇支持”，而是“21 篇里没有一篇是行动省略/反事实可及性研究”。R2-M1 指出的分母混淆由此得到直接证据。

## 2 逐篇双编码

| 篇 | 主编码 | 第二编码 | 第二编码理由 |
| --- | --- | --- | --- |
| `R01` | `NEITHER` | `NEITHER` | FrameNet describes frame-semantic valence annotation of lexical items, and its only "representation" claim concerns frame-element valences rather than any agent's selective non-response or an unchosen option's availability. |
| `R02` | `NEITHER` | `NEITHER` | The AMR paper claims an abstract meaning representation that deliberately omits articles and other surface material, which is linguistic constituent omission, not action omission or counterfactual availability. |
| `R05` | `NEITHER` | `NEITHER` | This is a physics review of stochastic thermodynamics and fluctuation theorems, with no claim about a system selectively not responding or about representing an unchosen option. |
| `R06` | `NEITHER` | `NEITHER` | England's self-replication paper derives a thermodynamic bound on heat production during replication and makes no claim about action omission or counterfactual availability. |
| `R09` | `NEITHER` | `NEITHER` | This immunology review of T cell co-stimulation and co-inhibition treats "tolerance/anergy" as a molecular unresponsive state, not a selective withholding of response among available options, and its only "availability" hits concern tryptophan and data access. |
| `R13` | `NEITHER` | `NEITHER` | The paper concerns a neural mechanism for learning from delayed postingestive feedback in mice, and its "availability" mention is the reward-availability window of a port in the task, an excluded stimulus/port availability. |
| `R14` | `NEITHER` | `NEITHER` | All omission language in this dopamine/reward-timescale paper refers to trials where the reward outcome was omitted (reward omission), an explicitly excluded construct, and no skipped action option is claimed to be represented. |
| `R15` | `NEITHER` | `NEITHER` | This paper argues rats learn an instrumental action despite a 16-min reinforcement delay via information-theoretic contingency, mentioning alternative response distributions only as the authors' counterfactual analysis of reinforcement rate, not as a representation of a foregone option. |
| `R17` | `NEITHER` | `NEITHER` | The Behaviour Change Wheel paper characterizes behaviour via capability/opportunity/motivation and intervention functions, with no claim about selective non-response or a represented unchosen option (its "barriers" are generic behaviour-change barriers). |
| `R20` | `NEITHER` | `NEITHER` | This control-barrier-function review discusses constraint satisfaction and collision avoidance, where "omit"/"skip"/"refrain" are authorial shorthand and "avoidance" is physical obstacle avoidance, not selective non-response with counterfactual availability. |
| `R24` | `NEITHER` | `NEITHER` | This CBF reduced-order-model survey makes safety-control claims about constraint satisfaction, and its only related words are "alternative approaches" for controller design, unrelated to omission or unchosen-option representation. |
| `G6-07` | `NEITHER` | `NEITHER` | The Consolidated Framework for Implementation Research paper organizes implementation determinants and contains no claim about a system abstaining or about representing a skipped option. |
| `G8-01` | `NEITHER` | `NEITHER` | PropBank adds semantic role labels to Treebank syntax, and its "omitted"/"skip" hits are zeros dropped from result tables and a table entry, i.e. data-reporting artifacts. |
| `G8-03` | `NEITHER` | `NEITHER` | The Universal Dependencies v1 paper describes a cross-lingual annotation scheme and contains no omission, abstention, or counterfactual-availability claim. |
| `G8-04` | `NEITHER` | `NEITHER` | The ACE program paper describes entity/relation/event extraction tasks and evaluation, and its "Availability" hit is a table column about resource availability in the evaluation setup. |
| `G8-05` | `NEITHER` | `NEITHER` | The Gene Ontology paper describes a controlled vocabulary for molecular function and biological process annotation, with no claim bearing on action omission or an unchosen option's availability. |
| `G8-08` | `NEITHER` | `NEITHER` | This narrative event-chain paper learns stereotyped event sequences from corpora and evaluates narrative cloze, making no claim about a system selectively not responding or representing an unchosen option. |
| `X-K4-01` | `NEITHER` | `NEITHER` | An in vitro immunology paper on IL-12/B7-CD28 synergy, whose "unresponsive" mentions occur only in cited reference titles and involve global T cell unresponsiveness, not selective non-response among options. |
| `X-K4-02` | `NEITHER` | `NEITHER` | A study of combined TLR/CD40 triggering of CD8+ T cell expansion, containing no omission, abstention, or counterfactual-availability claim beyond site-navigation text. |
| `X-K4-05` | `NEITHER` | `NEITHER` | The quorum-sensing biofilm paper argues QS signals act as self-regulatory rather than neighbour-inducing cues, which is about signal design and stochastic escape, not a selective abstention whose skipped option would need representation. |
| `X-K4-07` | `NEITHER` | `NEITHER` | A slice-physiology study of two coincidence detectors for spike-timing-dependent plasticity, with no claim about response omission or the availability of a non-chosen option. |

## 3 解释

- 21 篇的主题是 FrameNet/AMR/PropBank/UD/叙事链、热力学/自复制、T 细胞/免疫、生物膜、控制屏障函数、实施科学等；它们的 omission/availability 命中分别是**语言成分省略、奖励省略、数据省略、刺激/数据可用性**，均被预注册规则排除。
- 主编码者与第二编码者独立同意 21/21；但 κ 在“全为同一类”时是 `UNDEFINED`，**不能当作 1.0 的可靠性**。这是一次**分母审计**，不是平衡编码任务的信度估计。
- I1 的证据仍以 **L-04 的 17 条编码行**为准（3 条 S+C、1 条 S-only、1 条 C-only、12 条无关）；L-05 只是证明“21 篇”不是那个分母。
- 一个构造效度观察：L-04 曾把 R13 读作 S+C（novelty gating + representation）；在本轮更严格的“行动省略”规则下 R13 是 `NEITHER`。差异来自规则边界（泛表征/非行动省略被排除），不是编码错误；这说明 I1 的构念边界本身需要固定。

## 4 边界

- 两位编码者都是本项目的 AI 上下文，不是两位人类独立编码者；本轮提高的是**规程在独立上下文中的可复现性**，不是人类一致性。
- 不改变 `L01_coding.json`、`L04_I1_AUDIT.json`、任何轮次判定或台账。
- 不新增实验；R2 要求的非构造性 S-only 臂仍未运行。

## 5 复现

```bash
python3 literature/l05_second_coder.py --check
python3 literature/l05_second_coder.py
python3 literature/l05_gate.py            # 12/12
```
