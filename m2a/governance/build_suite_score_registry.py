"""Reconcile every suite score quoted in prose against the line that suite prints when it is run.

Why this layer. §47 proved a published page can be refuted by the repository. The documents inside the
repository are also full of suite scores - `x_gate.py n/n` appears in the final report, the negative log,
the obligation ledger and the derived summaries - and until now nothing checked them against the suites
themselves: G8 interlocks the ledger against the report (prose against prose), and §44 compares *round
result documents* against live runs for the 25 round gates. Neither covers the governance suites, and a
prose-vs-prose interlock goes quiet exactly when both documents are stale together (disclosed in X-83).
This table asks the single question that has an authority: **the suite's own printed line**.

Criteria, frozen before the first run (this file is the register for them):

  Population A (authority): every suite the closing audit collects - the `*gate*.py` namespaces - plus any
    `*gate*.py`-looking name quoted in prose that exists in the repo but is not in that glob (it gets run
    too). Each entry's live value is `n/n checks passed` from its own stdout, with the suite's source
    SHA-256 pinned so a changed suite is visible without running it.
  Population B (claims): every (suite, n/n) pair read out of the prose documents, using §47's strict tier:
    file name, then the self-equal fraction within three characters on the same line, digit-boundaried. The
    corpus is four kinds: `append_only` (M2A_FINAL_REPORT.md, the negative log), `regenerated`
    (governance/OBLIGATION_REGISTRY.md - the only kind with no history excuse), `derived_summary`
    (`report/*.md` plus the regenerated governance tables) and `run_record` (`experiments/*.md`,
    `literature/*.md`). Only the two files this step writes are excluded (§47's SELF_OUT lesson: a derived
    artifact must not attest its own numbers).

  Two amendments to population B, both written before any reading of this step was published, neither touching
  E1-E7 - they change *which documents are claims*, not *what a contradiction is*:
    A1 the register first said `report/*.md` for the run records, but the round records are
      `experiments/*RESULTS*.md` and `literature/*RESULTS*.md`: ten documents that really quote the gate of
      their own round sat outside the corpus. Q10 is the rule that caught it - it asks of every file in the
      repository that carries an adjacent name+fraction pair whether the corpus covers it. X-86.
    A3 WITHDRAWN the same round it shipped (registered as X-94): Q10 named a carrier this layer had
     never looked at: another governance layer ships a derived JSON table that quotes suite scores, and the
     corpus rule only read `*_v<n>.md`. A derived table may be REFUTED without being allowed to ATTEST, so
     the fix is to widen the claim population to `*_v<n>.json` as well, not to add it to the exclusion set.
  A2 the regenerated governance tables (`SECTION_PAGE_RECONCILIATION_v1.md`, `WIKI_SYNC_MAP_v1.md`) are
      claims of kind `derived_summary`. A derived document must not *support* a number (§47), but a number
      it prints is still refutable, and its ERRATA rows are exactly the "quoted as an error" shape E5 exists
      to allow. What stays excluded is only this step's own output pair, so the table cannot quote itself.

  Verdicts, in this precedence, first match wins:
    E1 `live_unavailable`   - a suite in population A does not print `n/n` today (or crashes). HARD.
    E2 `phantom_suite`      - prose names a `*gate*.py`-shaped instrument that does not exist in the repo.
                              HARD (X-80: file names are part of the contract; X-81/X-82: a register that
                              points at a non-existent object must fail loudly).
    E3 `stale_in_register`  - a regenerated document (`OBLIGATION_REGISTRY.md`) quotes a value != live.
                              HARD: a regenerated file has no excuse for carrying an old number.
    E4 `impossible_growth`  - an append-only document quotes a value **larger** than live. Suite rule counts
                              only grow in this repo, so a bigger number cannot be history: HARD.
    E5 `paired_correction`  - value != live, but the same physical line also states the live value for that
                              suite. Legal: the row presents the number as a corrected error (X-83's own
                              shape, and §47's "quoted as an error" discipline).
    E6 `possible_history`   - value < live in an append-only document. Legal but disclosed: this table cannot
                              tell "the value at the time" from "an old value cited as if it were today's".
                              That limit is the reason §47's ERRATA register exists and stays human.
    E7 `matches_live`       - value == live.

  Exit order (registered, first decisive exit taken): E1 or E2 or E3 or E4 present => the step's job is to
  fix the register or append a correction, never to widen a rule; otherwise the table is green and its only
  output is the disclosure counts (`possible_history`, `paired_correction`, `self_reference`).

  Stop rule, written before seeing any data: if a HARD verdict cannot be resolved by an appended correction
  (append-only documents) or a regenerated register, it is registered as a finding (X-##) and reported -
  the criteria are not relaxed and no document is rewritten.

Self-reference, disclosed instead of hidden: this step's own validator is in population A's namespace and is
**excluded** from being run by this deriver (a suite may not be its own instrument, R8). Prose that quotes it
is classified `self_reference` and counted; the authoritative reading of its fraction stays the closing audit.
  E8 `unmeasured_by_registration` - a suite deliberately kept OUT of population A because running it would
      re-derive a layer that reads this table (X-94's cycle). Disclosed, never hard, and the reason is stored
      in `UNMEASURED` so an exclusion can be audited instead of being a silent absence.

Cost, declared: running population A is the expensive part (the discrimination suite alone is ~5 minutes), so
this deriver is meant to be run once per step, outside the closing audit's own collection. The validator
checks byte reproducibility against a pinned run and re-runs only what changed.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

M = pathlib.Path(__file__).resolve().parent.parent      # m2a/
GOV = M / "governance"
JSON_OUT = GOV / "suite_score_registry_v1.json"
MD_OUT = GOV / "SUITE_SCORE_REGISTRY_v1.md"
LEDGER = GOV / "OBLIGATION_REGISTRY.md"
LOG = GOV / "NEGATIVE_AND_NULL_EVIDENCE_LOG.md"
REPORT = M / "M2A_FINAL_REPORT.md"
RUNS_DIR = M / "report"
RECORD_DIRS = (M / "experiments", M / "literature")
GOV_TABLE = re.compile(r"_v\d+\.md$")

SELF_OUT = {JSON_OUT.name, MD_OUT.name}
# A validator that re-runs this layer's generator must stay out of population A: running it here would
# re-derive the layer that reads the table this generator is writing (X-94's cycle, one level up).
# Its own reading stays authoritative in the closing audit; quotes of it are disclosed, never judged.
UNMEASURED = {"label_provenance_gate.py":
              "re-runs governance/build_label_provenance.py, which reads this layer's table (X-94)",
              "value_provenance_gate.py":
              "re-runs governance/build_value_provenance.py and pins this layer's own exclusion list, so "
              "measuring it here would put the closing audit in an order-dependent loop (X-95, same shape "
              "as X-94); its printed line stays authoritative in the audit itself",
              "frozen_input_map_gate.py":
              "re-runs governance/build_frozen_input_map.py, the last deriver, which reads this layer's own "
              "JSON; measuring it here would require this table to be final before the map it writes and the "
              "map to be final before this table (X-94's cycle, registered as X-117); its printed line stays "
              "authoritative in the closing audit"}
# A3 withdrew the JSON widening the same round it was added: another layer's derived JSON re-emits the
# very prose lines this layer extracts, so scanning it re-reads this layer's own rows (transcription
# laundering, X-85(g)) and made the two layers mutually dependent - the closing audit could then never
# be green whichever order it ran in. It is named here with its reason instead of being silently skipped.
LAYER_TRANSCRIPTIONS = {"LABEL_PROVENANCE_v1.md":
                        "the table governance/build_label_provenance.py writes, whose rows are copied "
                        "out of this layer's own claims (X-94)",
                        "label_provenance_v1.json":
                        "transcription of this layer's own claim lines by governance/"
                        "build_label_provenance.py; a claim source may not be a copy of the claims",
                        "VALUE_PROVENANCE_v1.md":
                        "the table governance/build_value_provenance.py writes; its rows quote prose "
                        "lines verbatim, so scanning it re-reads this layer's claims through a copy "
                        "that can be truncated mid-fraction (X-85(g), X-95)",
                        "value_provenance_v1.json":
                        "same table in machine form; a claim source may not be a copy of the claims"}
SELF_SUITE = "suite_score_registry_gate.py"
GLOB_SUITES = sorted(M.glob("experiments/*gate*.py")) + sorted(M.glob("literature/*gate*.py")) \
    + sorted(M.glob("governance/*gate*.py"))
CLAIM_DOC_KIND = {"regenerated": {LEDGER.name},
                  "append_only": {REPORT.name, LOG.name}}
QUOTED = re.compile(r"([A-Za-z0-9_]*gate[A-Za-z0-9_]*\.py)[^\n]{0,3}?(?<!\d)(\d+)/(\d+)(?![-\d])")
TAIL = re.compile(r"^(\d+)/(\d+) checks passed", re.M)


def norm(text: str) -> str:
    text = re.sub(r"<[^>]{1,60}>", "", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(a, b)
    text = text.replace("`", "")
    text = re.sub(r"\*\*?", "", text)
    return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines())


def run_suite(path: pathlib.Path):
    r = subprocess.run([sys.executable, str(path)], cwd=M, capture_output=True, text=True, timeout=1200)
    m = TAIL.search(r.stdout.strip())
    if not m or int(m.group(1)) != int(m.group(2)) or r.returncode != 0:
        return None, (r.stdout.strip().splitlines() or [""])[-1][:60]
    return (int(m.group(1)), int(m.group(2))), ""


def live_table():
    """Population A: the suites the audit collects, plus any quoted name outside that glob."""
    paths = {p.name: p for p in GLOB_SUITES if p.name != SELF_SUITE and p.name not in UNMEASURED}
    for q in quoted_names():
        name = q[2]
        if name not in paths and name != SELF_SUITE and name not in UNMEASURED:
            found = list(M.rglob(name))
            if found:
                paths[name] = found[0]
    out = {}
    for name, p in sorted(paths.items()):
        val, why = run_suite(p)
        out[name] = {"file": str(p.relative_to(M)), "live": list(val) if val else None,
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "why": why}
    return out


def corpus():
    """Population B: one definition, read by the deriver and by its validator (Q5/Q10/Q14/Q15 share it)."""
    docs = [(REPORT, "append_only"), (LOG, "append_only"), (LEDGER, "regenerated")]
    tables = [p for p in sorted(GOV.glob("*.md")) if GOV_TABLE.search(p.name)
              and p.name not in SELF_OUT and p.name not in LAYER_TRANSCRIPTIONS]
    docs += [(p, "derived_summary") for p in sorted(RUNS_DIR.glob("*.md")) + tables]
    docs += [(p, "run_record") for d in RECORD_DIRS for p in sorted(d.glob("*.md"))]
    return [(p, kind) for p, kind in docs if p.exists() and p.name not in SELF_OUT]


def quoted_names():
    """Every instrument-shaped name prose attaches a fraction to, with its document kind."""
    pairs = []
    for doc, kind in corpus():
        for line_no, line in enumerate(norm(doc.read_text(encoding="utf-8", errors="replace")).splitlines(), 1):
            for f, a, b in QUOTED.findall(line):
                if int(a) == int(b):
                    pairs.append((doc.name, kind, f, a + "/" + b, line_no, line))
    return pairs


def classify(pairs, live):
    rows = {}
    for doc, kind, name, val, line_no, line in pairs:
        key = (doc, name, val)
        entry = rows.setdefault(key, {"document": doc, "doc_kind": kind, "instrument": name,
                                     "quoted": val, "line": line_no, "live": None, "verdict": "",
                                     "context": line[max(0, line.find(name) - 40):line.find(name) + 60]})
        if name == SELF_SUITE:                 # before the phantom branch: this validator is deliberately
            entry["verdict"] = "self_reference"  # outside population A, so absence must not read as invention
            continue
        if name in UNMEASURED:            # registered exclusion, disclosed rather than judged
            entry["verdict"] = "unmeasured_by_registration"
            continue
        info = live.get(name)
        if info is None:
            entry["verdict"] = "phantom_suite"
            continue
        entry["live"] = "/".join(str(x) for x in info["live"]) if info["live"] else None
        if entry["live"] is None:
            entry["verdict"] = "live_unavailable"
            continue
        q, l = int(val.split("/")[0]), info["live"][0]
        if q == l:
            entry["verdict"] = "matches_live"
        elif "%d/%d" % (l, l) in line:
            entry["verdict"] = "paired_correction"
        elif kind == "regenerated":
            entry["verdict"] = "stale_in_register"
        elif q > l:
            entry["verdict"] = "impossible_growth"
        elif q < l:
            entry["verdict"] = "possible_history"
        else:
            entry["verdict"] = "unexplained_gap"
    return sorted(rows.values(), key=lambda r: (r["document"], r["instrument"], r["quoted"]))


def main() -> int:
    if not (REPORT.exists() and LOG.exists() and LEDGER.exists()):
        print("prose documents missing", file=sys.stderr)
        return 2
    pairs = quoted_names()
    live = live_table()
    rows = classify(pairs, live)
    for name, info in sorted(live.items()):
        if info["live"] is None:
            rows.append({"document": "-", "doc_kind": "population", "instrument": name,
                         "quoted": "-", "line": 0, "live": None, "verdict": "live_unavailable",
                         "context": info["why"]})
    hard_verdicts = ("phantom_suite", "live_unavailable", "stale_in_register", "impossible_growth",
                     "unexplained_gap")
    hard = [r for r in rows if r["verdict"] in hard_verdicts]
    dist = {}
    for r in rows:
        dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
    c = {"suites_run": len(live), "suites_live_green": sum(1 for v in live.values() if v["live"]),
         "corpus_documents": len(corpus()), "claim_documents": len({r["document"] for r in rows}),
         "quotes_found": len(pairs), "quote_rows": len(rows),
         "hard_findings": len(hard),
         "self_reference_quotes": dist.get("self_reference", 0),
         **{"verdict_" + k: v for k, v in sorted(dist.items())}}
    data = {"schema": "m2a.suite_score_registry.v1", "counts": c,
            "generator": {"file": str(pathlib.Path(__file__).resolve().relative_to(M)),
                          "sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},
            "live": live, "verdict_distribution": dist,
            "hard_findings": hard, "rows": rows}
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")

    lines = ["# 套件分数引用对账 v1（由实跑推导）", "",
             "> 推导器 `governance/build_suite_score_registry.py`（会实跑人口内每台套件，故本步设计成每轮跑一次，",
             "> 不进收尾审计的收集）；校验器 `governance/suite_score_registry_gate.py`。",
             "> 权威读数只有一个：**那台套件自己打印的 `n/n checks passed`**。散文里的引用与它逐条对账。",
             "> 判据在本文件运行之前冻结（见推导器 docstring 的 E1–E7 与出口顺序）。",
             "> 本步自己写出的两个文件不参与引用扫描（派生工件不给自己背书，R8）；本步的校验器不被本推导器运行",
             "> （仪器不得自证），凡对它的引用一律记为 `self_reference` 并如实披露。",
             "",
             "| 列 | 数 |", "| --- | --- |",
             "| 实跑的套件 | %d（今天为绿 %d） |" % (c["suites_run"], c["suites_live_green"]),
             "| 语料内文档 / 其中真的产出主张行的 | %d / %d |" % (c["corpus_documents"], c["claim_documents"]),
             "| 引用条数 / 去重后的判定行 | %d / %d |" % (c["quotes_found"], c["quote_rows"]),
             "| **硬伤（凭空仪器 / 实跑不绿 / 再生文档陈旧 / 不可能的增长）** | %d |" % c["hard_findings"],
             "| 引用与实跑一致 | %d |" % dist.get("matches_live", 0),
             "| 同一行同时给出实跑值（把错误当错误引用） | %d |" % dist.get("paired_correction", 0),
             "| 可能为历史值（小于实跑，仅披露不判红） | %d |" % dist.get("possible_history", 0),
             "| 对本步校验器自身的引用（不可自证） | %d |" % dist.get("self_reference", 0),
             "| 对已登记不测量仪器的引用（%s） | %d |" % ("；".join(sorted(UNMEASURED)),
                                                    dist.get("unmeasured_by_registration", 0)),
             "",
             "## 逐条引用", "",
             "| 文档 | 口径 | 仪器 | 引用 | 实跑 | 判定 | 行 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append("| `%s` | %s | `%s` | %s | %s | %s | %d |" % (
            r["document"][:34], r["doc_kind"], r["instrument"], r["quoted"], r["live"] or "-",
            r["verdict"], r["line"]))
    lines += ["", "## 人口与指纹", "",
              "> 生成本表的推导器源码 SHA-256：`%s`（`%s`）；语料文档 %d 份。语料缩小而不登记，Q18 会红。" % (
                  data["generator"]["sha256"][:16], data["generator"]["file"], c["corpus_documents"]), ""] + ["| 套件 | 路径 | 实跑 | 源码 sha256（前 12） |", "| --- | --- | --- | --- |"]
    for name, info in live.items():
        lines.append("| `%s` | `%s` | %s | `%s` |" % (
            name, info["file"], "/".join(str(x) for x in info["live"]) if info["live"] else "不绿",
            info["sha256"][:12]))
    lines += ["", "**看不见什么**：判定只看 `n/n` 这一种形状；不比句子、不比判据数值、不比容差。",
              "`possible_history` 是有意不判红的一档——一个小于今日值的数字既可能是当时成立的历史读数，也可能是",
              "被当作今日值引用的陈年值，机械规则分不开这两种；因此它逐条列出，并由 §47 的 ERRATA 与人工复核承担。",
              "再生文档没有这档豁免：`OBLIGATION_REGISTRY.md` 每次由工件重导，带旧号就是硬伤。", ""]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote %s | suites %d green %d quotes %d rows %d hard %d dist %s" % (
        JSON_OUT.name, c["suites_run"], c["suites_live_green"], c["quotes_found"], c["quote_rows"],
        c["hard_findings"], json.dumps(dist, sort_keys=True)))
    return 0 if not hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
