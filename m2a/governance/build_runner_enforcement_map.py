"""Derive, from the runner sources, whether each committed artifact's gate was actually enforced.

Why this is the sibling of the gate-coverage map (§42). That map answers "does any judgment read this
instrument". The claim it rests on is the pipeline rule "the runner refuses when the gate is red" -
and until now that claim was carried by the runners' own docstrings ("gate first, then ..."), i.e. by
prose. X-67 is exactly the failure shape this misses: a disposition written down somewhere is not a
check that runs. So here every writer of a committed JSON artifact is classified by its syntax:

  * `gate_executed`  - a subprocess call whose arguments name a `*_gate.py`;
  * `refusal_enforced` - an `if` guard on the gate's return code (directly on `<proc>.returncode`, or
    on the value returned by a helper that runs the gate and returns it - Phase XIV's `run_gate()`)
    whose body STOPS: `return <nonzero>`, `sys.exit`, `raise SystemExit`, or any `raise`;
  * `write_after_guard` - every artifact write occurs after that guard, so a red gate cannot leave a
    results file behind.

Verdicts: `enforced` (all three), `gate_ran_but_rc_unchecked`, `rc_checked_but_refusal_does_not_stop`,
`writes_before_the_guard`, `no_gate_at_all`. The last one is legitimate for reanalysis/post-hoc writers,
which compute on already-committed readings and hold zero-test status (R6) - but legitimacy has to be
REGISTERED: an unregistered `no_gate_at_all` aborts the build, because the whole point is that a round
that quietly stops gating its own results cannot slip in silently.

Reads are not writes. `json.load(open("phase8_results.json"))` names an artifact but does not touch
it; the writer test requires `json.dump` / `write_text` / `open(..., "w")`. Getting this wrong the
first time made four runners look like they were rewriting earlier rounds' committed artifacts.

No experiment is run, no artifact is modified, no verdict of any round is rewritten.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent
# "committed artifact" = a JSON that already exists under experiments/ or literature/. Naming the
# suffixes instead (_results/_reanalysis/_coding) would have silently dropped p5_v1_posthoc.json and
# r7_closure_report.json, both versioned readings written by scripts that run no gate.
ARTIFACT_NAMES = {q.name for d in ("experiments", "literature") for q in (M / d).glob("*.json")}
ARTIFACT = re.compile("|".join(re.escape(n) for n in sorted(ARTIFACT_NAMES)))
assert ARTIFACT_NAMES, "no committed JSON artifacts found - population would match everything"

# writers that legitimately run no gate (reanalysis / post-hoc: input is already-committed readings,
# output holds zero-test status). name -> reason. Unregistered instances abort the build.
KNOWN_NO_GATE = {
    "p5_v1_posthoc.py":
        "事后重分析：读已提交的 `phase5_results.json`，写的是自己的 `p5_v1_posthoc.json`（零检验地位，R6），"
        "不属于任何一轮的门控时序（X-32 一族）。",
    "p6_reanalyze.py":
        "Phase VI 的 reanalysis：在已提交读数上重算，另写 `phase6_reanalysis.json`，原轮判定与门控记录"
        "一字不动（R6）。",
    "r7_closure_report.py":
        "R7 闭合报告：只在已提交工件（Phase VIII/XII/XIII 的 results）上做逐字比对，把比对结果写进"
        " `r7_closure_report.json`；它是报告不是某一轮的读数，故无门控时序。",
    "run_L01_reanalysis.py":
        "L-01 主张层重判读：输入是已提交的 `L01_coding.json`，输出 `L01_reanalysis.json` 标注 "
        "`ZERO_TEST_REANALYSIS`；该轮的门控由 `run_L01.py` 在编码时执行过（`l01_gate.py`），重判读不得"
        "重跑门控（R6）。",
}


def src_of(path):
    return path.read_text(encoding="utf-8")


def gate_calls(tree, src):
    """(lineno, target var or None, gate file) for every subprocess call that names a *_gate.py."""
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Call,)):
            continue
        fn = n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
        if fn not in ("run", "Popen", "call", "check_output", "check_call"):
            continue
        seg = ast.get_source_segment(src, n) or ""
        g = re.findall(r"([A-Za-z0-9_]+_gate\.py)", seg)
        if g:
            out.append((n.lineno, g[0]))
    return out


def assigned_from(tree, name):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            out.append(n)
    return out


def stoppers(body):
    """Does this guarded body terminate the program (or the caller) on the refused path?
    Only the guard's OWN statements count, recursing into if/try blocks: a `return` living inside a
    nested `def` belongs to that function, not to the refusal, and counting it would invent a guard
    that stops nothing (`ast.walk` over the body would have done exactly that)."""
    for stmt in body:
        if isinstance(stmt, ast.Call) and getattr(stmt.func, "attr", "") == "exit":
            return True
        if isinstance(stmt, ast.Raise):
            return True
        if isinstance(stmt, ast.Return) and stmt.value is not None \
                and not (isinstance(stmt.value, ast.Constant) and stmt.value.value == 0):
            return True
        if isinstance(stmt, (ast.If, ast.Try)):
            kids = list(stmt.body) + (list(stmt.finalbody) if isinstance(stmt, ast.Try) else [])
            if isinstance(stmt, ast.If):
                kids += list(stmt.orelse)
            else:
                for h in stmt.handlers:
                    kids += list(h.body)
            if stoppers(kids):
                return True
    return False


def rc_guards(tree, src, call_lines, gate_helpers):
    """(lineno, gate file, stops: bool) for every `if` whose test consults a gate return code."""
    guards = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        test = ast.get_source_segment(src, n.test) or ""
        hit_call = any(isinstance(c, ast.Attribute) and c.attr == "returncode" for c in ast.walk(n.test))
        # a gate helper may take arguments (`if gate("--pre") != 0`); requiring empty parentheses made
        # run_L03 read as "ran the gate but never checked the code" when it checks both calls.
        hit_helper = bool(re.search(r"\b(" + "|".join(gate_helpers) + r")\s*\(", test)) if gate_helpers else False
        var = None
        for c in ast.walk(n.test):
            if isinstance(c, ast.Name):
                var = c.id
                break
        hit_var = var is not None and any(
            a.lineno <= n.lineno
            and re.search(r"\b" + var + r"\s*=\s*(subprocess\.|(" +
                          "|".join(gate_helpers) + r")\s*\()" if gate_helpers else r"\b" + var + r"\s*=\s*subprocess\.",
                          ast.get_source_segment(src, a) or "")
            for a in assigned_from(tree, var))
        if hit_call or hit_helper or hit_var:
            guards.append({"line": n.lineno, "test": test.strip()[:70], "stops": stoppers(n.body)})
    return guards


def module_attr_source(base, module, attr):
    """Source of `attr = ...` in an imported module. A runner may write `C.OUT.write_text(...)` where the
    path lives in the imported module; name-only resolution dropped that whole runner from the population."""
    p = base / (module + ".py")
    if not p.exists():
        return ""
    msrc = p.read_text(encoding="utf-8")
    for n in ast.walk(ast.parse(msrc)):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
                and n.targets[0].id == attr:
            return ast.get_source_segment(msrc, n.value) or ""
    return ""


def artifact_writes(tree, src, base):
    """(lineno, artifact) for calls that WRITE a committed artifact (reads are excluded).
    The name is often not in the call itself - `dst = LIT / "L01_reanalysis.json"` then
    `dst.write_text(...)` - so a callee name is resolved to its last assignment above the call.
    Without that resolution two of the four reanalysis writers looked like they wrote nothing.
    A path can also live in an imported module (`C.OUT.write_text`), so module constants are resolved
    from that module's AST; without it the runner disappeared from the table with no trace."""
    assigns = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            assigns[n.targets[0].id] = (n.lineno, ast.get_source_segment(src, n.value) or "")
    aliases = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                aliases[a.asname or a.name] = a.name
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
        seg = ast.get_source_segment(src, n) or ""
        owner = None
        if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
            owner = n.func.value.id
        elif fn == "open" and n.args and isinstance(n.args[0], ast.Name):
            owner = n.args[0].id
        if owner and owner in assigns and assigns[owner][0] <= n.lineno:
            seg = seg + " " + assigns[owner][1]
        elif isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Attribute) \
                and isinstance(n.func.value.value, ast.Name):
            mod, attr = n.func.value.value.id, n.func.value.attr
            if mod in aliases:
                seg = seg + " " + module_attr_source(base, aliases[mod], attr)
        art = ARTIFACT.findall(seg)
        if not art:
            continue
        if fn in ("dump", "dumps", "write_text", "write_bytes"):
            out.append((n.lineno, art[0]))
        elif fn == "open" and re.search(r"""['"]w""", seg):
            out.append((n.lineno, art[0]))
    return sorted(set(out))


def analyze(path):
    src, tree = src_of(path), ast.parse(path.read_text(encoding="utf-8"))
    calls = gate_calls(tree, src)
    # helpers of the shape `def run_gate(): ... return r.returncode` shift the guard one level up
    helpers = []
    for f in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        body = ast.get_source_segment(src, f) or ""
        if re.search(r"_gate\.py", body) and re.search(r"return\s+\w+\.returncode", body):
            helpers.append(f.name)
    guards = rc_guards(tree, src, [c[0] for c in calls], helpers)
    writes = artifact_writes(tree, src, path.parent)
    written = sorted({w for _, w in writes})
    enforced = any(g["stops"] for g in guards)
    if not calls:
        verdict = "no_gate_at_all"
    elif not guards:
        verdict = "gate_ran_but_rc_unchecked"
    elif not enforced:
        verdict = "rc_checked_but_refusal_does_not_stop"
    # a write is licensed by any stopping guard that precedes it; a full-gate run after the write is a
    # verification step, not the licence (run_L03 writes at line 52 between its pre-gate and full-gate).
    elif any(not any(g["stops"] and g["line"] < line for g in guards) for line, _ in writes):
        verdict = "writes_before_the_guard"
    else:
        verdict = "enforced"
    return {"runner": path.relative_to(M).as_posix(), "file": path.name,
            "gate_calls": [{"line": l, "gate": g} for l, g in calls],
            "gate_helpers": sorted(helpers),
            "rc_guards": guards, "artifact_writes": [{"line": l, "artifact": a} for l, a in writes],
            "artifacts_written": written,
            "writes_read_too": sorted({a for a in ARTIFACT.findall(src)} - set(written)),
            "verdict": verdict}


def registration_errors(rows):
    """Unregistered no-gate writers, and registrations that no longer describe a no-gate writer.
    A registration also has to name an artifact its file really writes - the reasons first claimed
    that `p5_v1_posthoc.py` wrote `phase5_results.json`, when it writes its own file."""
    ungated = [r for r in rows if r["verdict"] == "no_gate_at_all"]
    names = {r["file"] for r in rows}
    unregistered = sorted(r["file"] for r in ungated if r["file"] not in KNOWN_NO_GATE)
    stale = sorted(f for f in KNOWN_NO_GATE if f not in {r["file"] for r in ungated})
    wrong_target = []
    for r in rows:
        if r["file"] in KNOWN_NO_GATE and r["artifacts_written"] \
                and not any(a in KNOWN_NO_GATE[r["file"]] for a in r["artifacts_written"]):
            wrong_target.append(r["file"] + " writes " + str(r["artifacts_written"])
                                + " but the reason names none of them")
    return unregistered, stale, wrong_target


def main():
    files = sorted(set((M / "experiments").glob("run_*.py")) | set((M / "literature").glob("run_*.py"))
                   | {p for p in list((M / "experiments").glob("*.py")) + list((M / "literature").glob("*.py"))
                      if p.name in KNOWN_NO_GATE})
    analyzed = [analyze(p) for p in files]
    rows = [r for r in analyzed if r["artifacts_written"]]
    by_runner = {r["runner"]: r for r in analyzed}
    blind = sorted(r for r in by_runner
                   if not by_runner[r]["artifacts_written"]
                   and re.search(r"\.write_text\s*\(|\.write_bytes\s*\(|json\.dump\s*\(",
                                 (M / r).read_text(encoding="utf-8")))
    if blind:
        print("a runner writes but no artifact name could be resolved: " + str(blind),
              file=sys.stderr)
        raise SystemExit(4)
    unregistered, stale, wrong_target = registration_errors(rows)
    if unregistered or stale or wrong_target:
        print("registration failed - unregistered no-gate writers: " + str(unregistered)
              + " | registered but now gated: " + str(stale)
              + " | reasons naming an artifact the file does not write: " + str(wrong_target),
              file=sys.stderr)
        raise SystemExit(4)
    counts = {"writers": len(rows), "artifacts": len({a for r in rows for a in r["artifacts_written"]}),
              "enforced": sum(1 for r in rows if r["verdict"] == "enforced"),
              "ungated_round_runners": sum(1 for r in rows
                                           if r["verdict"] != "enforced"
                                           and r["verdict"] != "no_gate_at_all"),
              "no_gate_registered": len([r for r in rows if r["verdict"] == "no_gate_at_all"]),
              "guards_that_do_not_stop": sum(1 for r in rows for g in r["rc_guards"] if not g["stops"])}
    if not counts["enforced"]:
        print("nothing is enforced - the population or the detector is wrong", file=sys.stderr)
        raise SystemExit(4)
    (M / "governance/runner_enforcement_map_v1.json").write_text(json.dumps(
        {"schema": "m2a.runner-gate-map.v1",
         "derived_from": "AST of every experiments/run_*.py and literature/run_*.py that writes a "
                         "committed artifact, plus the registered reanalysis writers",
         "counts": counts, "rows": rows,
         "readers_not_writers": sorted(r["file"] for r in analyzed if not r["artifacts_written"]),
         "known_no_gate": KNOWN_NO_GATE},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("unregistered", unregistered, "| stale", stale, "| wrong-target", wrong_target)
    print("writers", counts["writers"], "| artifacts", counts["artifacts"],
          "| enforced", counts["enforced"], "| other verdicts", counts["ungated_round_runners"],
          "| registered no-gate", counts["no_gate_registered"],
          "| guards that do not stop", counts["guards_that_do_not_stop"])
    for r in rows:
        if r["verdict"] != "enforced":
            print("  ", r["verdict"], r["runner"], [g["line"] for g in r["rc_guards"]])
    write_md(rows, counts)


def write_md(rows, counts):
    md = ["# _runner 侧门控强制表 v1（由 `governance/build_runner_enforcement_map.py` 从 runner 源码推导）", "",
          "> 依据：§42 的覆盖表把结论建立在「runner 会在门控不过时拒绝执行」这条规则上，而这条规则此前**只由 "
          "runner 自己的 docstring 承载**（文字）。本表把它变成语法事实。生成物：本文件与 "
          "`governance/runner_enforcement_map_v1.json`。不跑实验、不改工件、不改任何轮次判定。", "",
          "## 1 三个判定", "",
          "* **执行了门控**：存在一条 subprocess 调用，其参数点名某个 `*_gate.py`；",
          "* **拒绝真的会停**：针对返回码的 `if` 守卫，其体内有 `return <非零>` / `sys.exit` / `raise`——"
          "注意守卫可以隔一层（Phase XIV 的 `run_gate()` 自己返回 rc，真正的拒绝在调用处）；",
          "* **写盘在守卫之后**：所有工件写入的行号都晚于守卫，于是门控红了也不会留下 results 文件。", "",
          f"人口：**{counts['writers']} 个工件写入者**，写 **{counts['artifacts']} 个**已提交 JSON。"
          f"判定：**enforced {counts['enforced']}**、其它 {counts['ungated_round_runners']}、"
          f"登记在册的无门控 {counts['no_gate_registered']}。", "",
          "## 2 逐行结果", "", "| runner | 门控 | 守卫 | 写入 | 判定 |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        g = "；".join(f"{x['gate']}@{x['line']}" for x in r["gate_calls"]) or "—"
        gd = "；".join(f"{x['line']}{'（停）' if x['stops'] else '（不停！）'}" for x in r["rc_guards"]) or "—"
        w = "、".join(f"{x['artifact']}@{x['line']}" for x in r["artifact_writes"][:2]) or "—"
        md.append("| `" + r["runner"] + "` | " + g + " | " + gd + " | " + w + " | `" + r["verdict"] + "` |")
    md += ["", "## 3 登记在册的无门控写入者（每条都必须写明为什么合法）", ""]
    for k, v in KNOWN_NO_GATE.items():
        md.append("- `" + k + "`：" + v)
    md += ["", "## 4 本表看不见的东西", "",
           "1. **守卫只保证「本轮不写」，不保证「本轮的门控真的测了判据」**——那是 §42 覆盖表负责的层面。"
           "两张表合起来才说完整：门控被跑（本表）且门控里确有读数量具（覆盖表）。",
           "2. **行号顺序是保守近似**：写盘在函数 `main()` 的更深处时，行号晚于守卫并不能证明运行时一定在守卫之后"
           "（异常路径、循环内的提前返回）。因此「写盘在守卫之后」只用作**筛查漏报**的线索，不作为独立结论；"
           "结论只看前两条。",
           "3. **治理套件的构建脚本不在人口内**（`governance/build_*.py`）：它们写的是治理工件而非某轮的读数。",
           "", "---", "", "## 复现", "", "```bash",
           "python3 governance/build_runner_enforcement_map.py",
           "python3 governance/runner_gate_map_gate.py", "```", ""]
    (M / "report/RUNNER_GATE_ENFORCEMENT_v1.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote report/RUNNER_GATE_ENFORCEMENT_v1.md")


if __name__ == "__main__":
    main()
