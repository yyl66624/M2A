"""Derive, from the gate sources themselves, which mechanism functions each round's gate measures.

Motivation. The discrimination audit (§39-§41, `governance/gate_discrimination_gate.py`) finds a
gate's blindness by injection - slow, and limited to what someone thinks to inject. Two of the
blindnesses it found were structural and could have been read off the source: `p5b_gate` imports
`gap_for` and never calls it, and `p8_gate` reaches `rho_exact` only through
`rho_exact(0.6) == rho_exact(0.6)`. Statements about the AST should be DERIVED and PINNED, and doing
that also enumerates the instances nobody has injected yet.

Population: every `experiments/*_gate.py` and `literature/*_gate.py` - the round instruments. The
governance suites (`*_gate.py` under `governance/`) are excluded on purpose: they are audits of
artifacts, not instruments of a round, and they call `report()` rather than `check()`.

All of this is syntactic; no experiment is run and no artifact is modified:
  * an imported local name is REACHED by a check if it appears as a callee in that check's condition,
    or in a condition name's assigned value (followed transitively, bounded depth);
  * a check is a SELF-COMPARISON if its condition is `a == b` where a and b were assigned from
    structurally identical expressions (`a = f(...)` / `b = f(...)`, or `a1, a2 = f(...), f(...)`) -
    such a check cannot be falsified by any mechanism error, the extreme form of R8;
  * a name is DETAIL-ONLY if it is reached only through a check's detail argument: its value is
    printed for the reader but no pass/fail depends on it (X-67's "written down is not checked").

Three verdicts per gate: `never_reached`, `only_self_comparison`, `detail_only`. The first two are
gaps and every instance must carry a registered reason in `KNOWN` - a new one aborts the build,
because the whole point is that the inventory cannot grow silently (same rule as the obligation
ledger's EXPECT pins and the label table's RULES). The third is reported, not gated.

One class this map cannot see, stated so it is not mistaken for completeness: a name that IS reached
by a real condition, but by a check whose registered tolerance is coarser than the error (Phase XIII's
W2 = one count; Phase V-d's known-answer = +-0.005 absolute). Detecting that requires injection, which
is why this map and the discrimination suite are two instruments, not one.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

M = pathlib.Path(__file__).resolve().parent.parent
GATES = sorted((M / "experiments").glob("*_gate.py")) + sorted((M / "literature").glob("*_gate.py"))
LOCAL_MODULES = {p.stem for p in list((M / "experiments").glob("*.py"))
                 + list((M / "literature").glob("*.py")) + list((M / "governance").glob("*.py"))}
NON_INSTRUMENT = re.compile(r"^(annotations|np|json|sys|pathlib|re|shutil|subprocess|tempfile|math|"
                            r"collections|itertools|os|time|random|functools|hashlib|statistics)$")

# registered gap instances (name -> reason). New findings must be added here with a reason; the
# build refuses to proceed on an unregistered one.
KNOWN = {
    ("p5b_gate.py", "gap_for"):
        "X-79 的实测例：门控 `from p5_mechanisms import gap_for` 却从未调用 ⇒ 该轮量具的输入（驱动差 Δ）"
        "在仪器层无人核对；注入 1e-4 全绿已证实其盲。",
    ("p8_gate.py", "rho_exact"):
        "X-79 的第二例：唯一读取它的 J5 写的是 `rho_exact(0.6) == rho_exact(0.6)`（自我比较，无可证伪输入）；"
        "注入 1e-1（154.664→170.130）后 6 档全绿。",
    ("p10_gate.py", "rho_smooth"):
        "本表新查出：Phase X 的门控从 `p8_smooth` 导入 `rho_smooth` 却从未调用，它自己只用 `p10_exponent.rho`。"
        "两族读数本应对齐（Phase VIII 的平滑曲线 vs Phase X 的指数族），这一对齐从未在门控层做过。",
    ("p13_gate.py", "rho_exact"):
        "本表新查出：Phase XIII 的门控导入 `rho_exact` 未调用，W5 只锚 `rho_smooth` ⇒ 精确仪器在该轮门控层"
        "无人核对；`rho_exact` 在 Phase VIII 那里也只是一条自我比较（见上）。",
    ("p13_gate.py", "rho_smooth"):
        "本表新查出（同名遮蔽）：门控从 `p8_smooth` 导入 `rho_smooth`，而 W5 实际调用的是 `p12.rho_smooth`（第 59 行）"
        "⇒ 两个模块各有一个同名函数，被锚定的不是导入的那个；该轮对 Phase VIII 平滑曲线的门控层依赖是**空的**。"
        "文件里 `import p12_lattice as p12  # noqa: F401 (used via rho_smooth)` 这条注释还会把人引向相反结论。"
        "它也没有被 `p8_smooth` 内任何被调用的函数间接执行。",
    ("p5b_gate.py", "chain_polarity"):
        "本表新查出：与 `gap_for` 同一行导入（`from p5_mechanisms import chain_polarity, gap_for, tnorm, channels, "
        "window_exists`），且没有任何被调用的同模块函数在内部调用它 ⇒ 串行极性以及它作用的整条链在该轮门控层无人执行；"
        "V-b 只重测了窗口与网格。",
    ("p5b_gate.py", "channels"):
        "本表新查出：silent 侧输入构型（hard / one_weak / all_weak）从未被该门控构造，也没有被任何它调用的函数内部构造"
        "⇒「三档构型按注册生成」无仪器答案。注意它只被 `gap_for` 消费，而 `gap_for` 自己也没被执行。",
    ("p5b_gate.py", "tnorm"):
        "本表新查出：聚合算子在该轮门控层未被执行。这条**不是**「算子从未被测」——Phase IX 的门控有 `C8_tnorm_algebra` "
        "盯它；这里的含义仅限「V-b 声称用到的那条链没有仪器」。",
    ("p5d_gate.py", "readout_d"):
        "本表新查出（自我比较类）：`readout_d(0.8, 101, arm)` 只出现在 `G3_determinism`（`a == b`，同种子两次调用）"
        "⇒ 该确证轮的 MC 读数在门控层的唯一守护是「同种子给同一个数」，任何确定性实现错误都能通过（X-79 那一族的第三例）。",
    ("phase2_gate.py", "e1_rates"):
        "本表新查出（自我比较类）：`e1_rates(\"and\", 2000, seed=3)` 只出现在 `C1_determinism`（`r1 == r2`）"
        "⇒ Phase II 的机制生成器在门控层只被「同种子给同一个数」守护；C2/C3 盯的是闭式 `p_action`，不消费 `e1_rates`。"
        "这是全仓库最早的一条无可证伪输入检查。",
}

# Gap claims the map itself produced and then retracted. Kept in the artifact because a corrected
# false positive is a finding about the instrument: an early version of this map reported
# `p6_gate.py :: s3_window_exists` as dead, but the gate reaches it indirectly (the gate calls
# `s3_critical_beta`, whose body calls `s3_window_exists`). Name-level reachability is not execution
# reachability - the same distinction X-78 made about mutation paths.
CORRECTED = [{
    "claim": "p6_gate.py :: s3_window_exists imported but never called",
    "status": "retracted",
    "why": "门控调用 `s3_critical_beta`，其函数体内部调用 `s3_window_exists` ⇒ 该函数被执行，只是不按名字出现。"
           "推导器随后加入调用图闭包，此项自动消失。闭包后来又发现一个更隐蔽的同族风险（`p12_lattice` 自己"
           "`from p8_smooth import rho_exact` 却不调用），因此闭包已改为**跨模块**执行。",
}]


def module_functions(mod_stem):
    return set(module_info(mod_stem).get("defs", ()))


_INFO = {}


def locate(mod_stem):
    for cand in (M / "experiments" / (mod_stem + ".py"), M / "literature" / (mod_stem + ".py"),
                 M / "governance" / (mod_stem + ".py")):
        if cand.exists():
            return cand
    return None


def module_info(mod_stem):
    """{defs, calls, from_imports, aliases} for a local module. `calls[f]` is the set of
    `(owning module, function)` pairs that f's body invokes - ACROSS module boundaries, because
    `from p8_smooth import rho_exact` inside p12_lattice means a p12 call can execute a p8 reading.
    The first version closed only within one module (that fix is what retracted the
    `s3_window_exists` false positive); a cross-module check is what makes `never_reached` mean
    "nothing anywhere that this gate runs touches it", not "no same-module chain touches it"."""
    if mod_stem in _INFO:
        return _INFO[mod_stem]
    path, info = locate(mod_stem), {"defs": set(), "calls": {}, "from_imports": {}, "aliases": {}}
    if path is not None:
        tree, from_imports, aliases, _ = collect(path)
        defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        calls = {}
        for n in tree.body:
            if not isinstance(n, ast.FunctionDef):
                continue
            found = set()
            for x in ast.walk(n):
                if isinstance(x, ast.Name) and not isinstance(x.ctx, ast.Store):
                    if x.id in defs:
                        found.add((mod_stem, x.id))
                    elif x.id in from_imports:
                        found.add((from_imports[x.id], x.id))
                elif isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) \
                        and x.value.id in aliases:
                    found.add((aliases[x.value.id], x.attr))
            calls[n.name] = found
        info = {"defs": defs, "calls": calls, "from_imports": from_imports, "aliases": aliases}
    _INFO[mod_stem] = info
    return info


def close_cross(seeds, limit=20000):
    """Transitive inter-procedural closure from `(module, function)` entry points."""
    out, frontier, n = set(), [s for s in seeds if s], 0
    while frontier and n < limit:
        mod, fn = frontier.pop()
        if (mod, fn) in out:
            continue
        out.add((mod, fn))
        n += 1
        for callee in module_info(mod).get("calls", {}).get(fn, ()):
            if callee not in out:
                frontier.append(callee)
    return out


def collect(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    from_imports, aliases = {}, {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module in LOCAL_MODULES:
            for a in n.names:
                from_imports[a.asname or a.name] = n.module
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name in LOCAL_MODULES:
                    aliases[a.asname or a.name] = a.name
    assigns = []                       # (lineno, name, value node) - positional on purpose:
    for n in ast.walk(tree):           # gates reuse names (`worst` is assigned by several checks),
        if isinstance(n, ast.Assign):  # so a name->value dict would attribute a check to the wrong line
            for t in n.targets:
                if isinstance(t, ast.Name):
                    assigns.append((n.lineno, t.id, n.value))
                elif isinstance(t, (ast.Tuple, ast.List)):
                    if isinstance(n.value, ast.Tuple) and len(t.elts) == len(n.value.elts):
                        for e, v in zip(t.elts, n.value.elts):
                            if isinstance(e, ast.Name):
                                assigns.append((n.lineno, e.id, v))
                    else:
                        for e in t.elts:
                            if isinstance(e, ast.Name):
                                assigns.append((n.lineno, e.id, n.value))
                # containers built by mutation (`e = []` then `e.append(f(...))`) - the real callees
                # live in the mutator call, so record it as a later binding of the same name
                elif isinstance(t, (ast.Subscript, ast.Attribute)):
                    base = t.value
                    while isinstance(base, (ast.Subscript, ast.Attribute)):
                        base = base.value
                    if isinstance(base, ast.Name):
                        assigns.append((n.lineno, base.id, n.value))
        elif isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) \
                and isinstance(n.value.func, ast.Attribute) \
                and n.value.func.attr in ("append", "extend", "update", "insert", "add") \
                and isinstance(n.value.func.value, ast.Name):
            assigns.append((n.lineno, n.value.func.value.id, n.value))
    return tree, from_imports, aliases, assigns


def resolve(assigns, name, before_line):
    best = None
    for ln, nm, node in assigns:
        if nm == name and ln <= before_line and (best is None or ln >= best[0]):
            best = (ln, node)
    return best


def names_in(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def attr_pairs(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            out.add((n.value.id, n.attr))
    return out


def closure(roots, line, assigns, limit=8):
    """Names and `alias.member` pairs reachable from these expressions, following assignments
    positionally (a name resolves to the last assignment at or before the line that uses it)."""
    seen, pairs, frontier, depth = set(), set(), [(n, line) for n in roots], limit
    while frontier and depth:
        depth -= 1
        nxt = []
        for node, ln in frontier:
            pairs |= attr_pairs(node)
            new = names_in(node) - seen
            seen |= new
            for nm in new:
                got = resolve(assigns, nm, ln)
                if got:
                    nxt.append((got[1], got[0]))
        frontier = nxt
    return seen, pairs


def is_self_comparison(cond, assigns, line):
    if not (isinstance(cond, ast.Compare) and len(cond.ops) == 1 and isinstance(cond.ops[0], ast.Eq)
            and isinstance(cond.left, ast.Name) and len(cond.comparators) == 1
            and isinstance(cond.comparators[0], ast.Name)):
        return False
    a, b = resolve(assigns, cond.left.id, line), resolve(assigns, cond.comparators[0].id, line)
    return a is not None and b is not None and ast.dump(a[1]) == ast.dump(b[1])


def analyze(path):
    tree, from_imports, aliases, assigns = collect(path)
    # only CALLABLES can be "measured"; imported constants/tables are data, reported separately
    instrument, data = {}, {}
    for k, mod in from_imports.items():
        if NON_INSTRUMENT.match(k):
            continue
        (instrument if k in module_functions(mod) else data)[k] = mod
    # pairs, not names: `rho_smooth` exists in both p8_smooth and p12_lattice, and Phase XIII's gate
    # imports one while calling the other. Identity of an instrument is (module, function).
    instrument_pairs = {(mod, k) for k, mod in instrument.items()}
    read_any = names_in(tree)
    alias_mods = {k: v for k, v in aliases.items() if not NON_INSTRUMENT.match(k)}
    checks = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check"):
            continue
        if len(n.args) < 2:
            continue
        cname = n.args[0].value if isinstance(n.args[0], ast.Constant) else "<dynamic>"
        line = n.lineno
        cond_names, cond_pairs = closure([n.args[1]], line, assigns)
        det_names, det_pairs = closure(list(n.args[2:]), line, assigns)
        cond_mod_fns = {f"{alias_mods[b]}.{a}" for b, a in cond_pairs if b in alias_mods
                        and a in module_functions(alias_mods[b])}
        checks.append({
            "check": cname,
            "line": line,
            "self_comparison": is_self_comparison(n.args[1], assigns, line),
            "cond_functions": sorted(cond_names & set(instrument)),
            "cond_module_functions": sorted(cond_mod_fns),
            "detail_only_functions": sorted((det_names & set(instrument)) - cond_names),
        })
    called, judged_nonself = set(), set()
    for c in checks:
        nonself = not c["self_comparison"]
        for name in c["cond_functions"]:
            seed = (instrument[name], name)
            called.add(seed)
            if nonself:
                judged_nonself.add(seed)
        for spec in c["cond_module_functions"]:
            seed = tuple(spec.split("."))
            called.add(seed)
            if nonself:
                judged_nonself.add(seed)
        for name in c["detail_only_functions"]:
            c.setdefault("_detail_seeds", []).append((instrument[name], name))
    detail_seeds = {(m, n) for c in checks for (m, n) in c.get("_detail_seeds", [])}
    closure_all = close_cross(called)
    closure_nonself = close_cross(judged_nonself)
    self_only, detail_only = set(), set()
    for pair in instrument_pairs:
        if pair in closure_all:
            if pair not in closure_nonself:
                self_only.add(pair)
        elif pair in detail_seeds:
            detail_only.add(pair)
    never = sorted(instrument_pairs - closure_all - detail_seeds)

    def names(pairs):
        return sorted(n for _, n in pairs)
    return {"gate": path.relative_to(M).as_posix(), "file": path.name,
            "imported_instruments": names(instrument_pairs), "alias_modules": sorted(alias_mods),
            "imported_data": sorted(data),
            "imported_data_never_read": sorted(k for k in data if k not in read_any),
            "checks": [c["check"] for c in checks],
            "self_comparison_checks": [c["check"] for c in checks if c["self_comparison"]],
            "never_reached": names(never),
            "never_reached_pairs": sorted(never),
            "only_self_comparison": names(self_only),
            "only_self_comparison_pairs": sorted(self_only),
            "detail_only": names(detail_only)}


# blindnesses the INJECTION suite registered before running (expect="blind_all" in
# governance/gate_discrimination_gate.py) and the reason each is or is not a syntactic gap. The
# cross-check in `main` requires every one of them to be accounted for: either the map predicts it,
# or it belongs to a class this map declared blind to. A new blind_all with no line here fails the
# build - that is the point: the two instruments must stay in agreement or say why they diverge.
INJECTION_BLINDNESSES = {
    ("p5b_gate.py", "gap_for"): "predicted - imported and never reached",
    ("p8_gate.py", "rho_exact"): "predicted - reached only by a self-comparison",
    ("p13_gate.py", "q_cont"):
        "NOT a syntactic gap: W2 does call q_cont, its registered tolerance is one count, so the "
        "blindness is class 1 of this map (real condition, coarser tolerance) - only injection sees it",
}


def gap_pairs(rows):
    return {(pathlib.Path(r["gate"]).name, n)
            for r in rows for n in (r["never_reached"] + r["only_self_comparison"])}


def registration_errors(gaps):
    """Gap instances with no KNOWN reason, and KNOWN reasons that no longer correspond to a gap.
    Both directions: the inventory must not grow silently and must not rot into stale claims."""
    pairs = {(pathlib.Path(g["gate"]).name, g["name"]) for cat in gaps.values() for g in cat}
    return (sorted(pairs - set(KNOWN)), sorted(set(KNOWN) - pairs))


def injection_disagreements(predicted):
    """Blindnesses the injection suite registered that this map's structure does not account for.
    A `predicted` entry must appear in the gaps; a `NOT a syntactic gap` entry must not."""
    return {k: v for k, v in INJECTION_BLINDNESSES.items()
            if (k in predicted) != v.startswith("predicted")}


def main():
    rows = [analyze(p) for p in GATES]
    gaps = {"never_reached": [{"gate": r["gate"], "module": m, "name": n}
                              for r in rows for m, n in r["never_reached_pairs"]],
            "only_self_comparison": [{"gate": r["gate"], "module": m, "name": n}
                                     for r in rows for m, n in r["only_self_comparison_pairs"]]}
    missing, stale = registration_errors(gaps)
    if missing or stale:
        print("registration failed - unregistered gap instances:", missing,
              "| stale KNOWN entries:", stale,
              "(add a reason to KNOWN; do not delete the finding)", file=sys.stderr)
        raise SystemExit(4)
    predicted = gap_pairs(rows)
    unagreed = injection_disagreements(predicted)
    if unagreed:
        print("cross-check failed: the map disagrees with a blindness the injection suite measured "
              "before this build (see INJECTION_BLINDNESSES):", unagreed, file=sys.stderr)
        raise SystemExit(4)
    counts = {"gates": len(rows), "checks": sum(len(r["checks"]) for r in rows),
              "imported_instruments": sum(len(r["imported_instruments"]) for r in rows),
              "never_reached": len(gaps["never_reached"]),
              "only_self_comparison": len(gaps["only_self_comparison"]),
              "detail_only": sum(len(r["detail_only"]) for r in rows),
              "imported_data_never_read": sum(len(r["imported_data_never_read"]) for r in rows),
              "self_comparison_checks": sum(len(r["self_comparison_checks"]) for r in rows)}
    (M / "governance/gate_coverage_map_v1.json").write_text(json.dumps(
        {"schema": "m2a.gate-coverage-map.v1",
         "derived_from": "AST of every experiments/*_gate.py and literature/*_gate.py",
         "counts": counts, "rows": rows, "gaps": gaps,
         "known_reasons": {f"{k[0]}::{k[1]}": v for k, v in KNOWN.items()},
         "corrected_false_positives": CORRECTED,
         "gates_with_no_check_sites": [r["gate"] for r in rows if not r["checks"]],
         "injection_blindnesses": {f"{k[0]}::{k[1]}": v for k, v in INJECTION_BLINDNESSES.items()},
         "blind_class_this_map_cannot_see": "a name reached by a real condition whose registered "
                                            "tolerance is coarser than the error (p13 W2 = one count, "
                                            "p5d G4 = +-0.005 absolute) - only injection can show that"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("gates", counts["gates"], "| checks", counts["checks"],
          "| imported instruments", counts["imported_instruments"],
          "| never_reached", counts["never_reached"],
          "| only_self_comparison", counts["only_self_comparison"],
          "| detail_only", counts["detail_only"],
          "| self-comparison checks", counts["self_comparison_checks"])
    write_md(rows, gaps, counts)
    for cat in ("never_reached", "only_self_comparison"):
        for g in gaps[cat]:
            print("  ", cat, g["gate"], g["name"])


def write_md(rows, gaps, counts):
    cls_cn = {"never_reached": "导入了，但没有任何检查执行它",
              "only_self_comparison": "被执行，但只被「与自己比较」的检查执行"}
    md = ["# 门控仪器覆盖表 v1（由 `governance/build_coverage_map.py` 从门控源码推导）", "",
          "> 依据：owner 2026-10-18 第 7 条的仪器侧要求 + 台账 `O-16`/`O-17`。生成物：本文件与",
          "> `governance/gate_coverage_map_v1.json`。**本表不改写任何门控、不跑实验**，只读源码。",
          "",
          "## 1 这台仪器与那台仪器的分工",
          "",
          "判别力套件（`governance/gate_discrimination_gate.py`）用**注入**回答「多小的错这台门控看不见」；",
          "本表用**语法**回答「哪个量根本没有进入任何判定」。两者不可互相替代：",
          "本表能枚举没人想到去注入的缺口，注入能发现本表看不见的口径问题（见 §4）。",
          "",
          f"覆盖人口：{counts['gates']} 份轮次门控（`experiments/*_gate.py` + `literature/*_gate.py`），",
          f"{counts['checks']} 条 `check()`，{counts['imported_instruments']} 个从本地机制模块导入的可调用量。",
          "",
          "## 2 缺口清单（每条都必须带登记理由；新增而未登记者构建失败）",
          "",
          "| 门控 | 量 | 类别 | 理由 |",
          "| --- | --- | --- | --- |"]
    for cat, items in gaps.items():
        for g in items:
            fname = pathlib.Path(g["gate"]).name
            md.append("| `" + g["gate"] + "` | `" + g["module"] + "." + g["name"] + "` | "
                      + cls_cn[cat] + " | " + KNOWN[(fname, g["name"])] + " |")
    self_rows = [r for r in rows if r["self_comparison_checks"]]
    md += ["", f"**合计**：`never_reached` {counts['never_reached']} 条、"
                f"`only_self_comparison` {counts['only_self_comparison']} 条、"
                f"`detail_only` {counts['detail_only']} 条。", "",
           "## 3 自我比较型检查的普查（这些检查本身没有错，错在被当作仪器）", "",
           f"共 {counts['self_comparison_checks']} 条 `check()` 的条件形如 `a == b`，且 a 与 b 由**结构相同的表达式**赋值而来。",
           "它们能抓 NaN、崩溃与非确定性，抓不了任何数值错误 ⇒ 按 O-17 的要求，**不计入仪器条数**。", "",
           "| 门控 | 该类检查 |", "| --- | --- |"]
    for r in self_rows:
        md.append("| `" + r["gate"] + "` | " + "、".join("`" + c + "`" for c in r["self_comparison_checks"]) + " |")
    data_rows = [r for r in rows if r["imported_data_never_read"]]
    zero_check = [r["gate"] for r in rows if not r["checks"]]
    md += ["", "## 4 本表看不见的三类东西（写明，免得被当成完整清单）", "",
           "1. **被执行、但被一条容差太粗的检查判定**：Phase XIII 的 W2 容差是「一个计数」，Phase V-d 的 G4 是 "
           "±0.005 绝对。这些名字在表里显示为「已覆盖」，注入实验却证明它们对 1e-4 级的机制错误全盲。",
           "2. **治理套件不在人口内**：`governance/*_gate.py` 用 `report()` 而非 `check()`，它们是工件审计，"
           "不是某一轮的仪器。",
           f"3. **不用 `check()` 的轮次门控**：{'、'.join('`' + z + '`' for z in zero_check) or '无'} "
           f"贡献 0 条 `check()`（{zero_check and '它用自带的手段审计工件' or ''}），本表对任何不使用 "
           "`check()` 的门控**沉默**——「表里没写」不等于「已覆盖」。", "",
           "与注入套件的三条已登记失明（`expect=\"blind_all\"`）的对账：", "",
           "| 目标 | 本表的立场 |", "| --- | --- |"]
    for k, v in INJECTION_BLINDNESSES.items():
        md.append("| `" + k[0] + " :: " + k[1] + "` | " + v + " |")
    md += ["", "两条本表也预测到、一条属于上面第 1 类。**这条对账是构建时硬校验**：新增的 `blind_all` "
           "若既不被本表预测、也不登记在本表的盲区类里，构建直接失败。", "",
           "## 5 本表自己撤回的一条假阳性（保留在此，因为它说明推导器的边界）", ""]
    for c in CORRECTED:
        md.append("- 曾报 **" + c["claim"] + "**；已撤回。" + c["why"])
    md += ["", "## 6 导入但从未读取的数据/常量（提示性，不计为缺口）", ""]
    for r in data_rows:
        md.append("- `" + r["gate"] + "`：" + "、".join("`" + d + "`" for d in r["imported_data_never_read"]))
    md += ["", "---", "", "## 复现", "", "```bash",
           "python3 governance/build_coverage_map.py",
           "python3 governance/gate_coverage_map_gate.py",
           "python3 governance/gate_discrimination_gate.py   # 注入侧的互补仪器", "```", ""]
    (M / "report/GATE_COVERAGE_MAP_v1.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote report/GATE_COVERAGE_MAP_v1.md")
    for r in rows:
        if r["self_comparison_checks"] or r["detail_only"]:
            print("  note", r["file"], "self-comparison", r["self_comparison_checks"],
                  "detail-only", r["detail_only"])
        if r["imported_data_never_read"]:
            print("  data", r["file"], "imported but never read", r["imported_data_never_read"])


if __name__ == "__main__":
    main()
