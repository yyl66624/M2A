"""Validator for the gate-instrument coverage map: instrument checks only (R2), no scientific criterion.

The map (`build_coverage_map.py` -> `gate_coverage_map_v1.json` +
`report/GATE_COVERAGE_MAP_v1.md`) is a set of CLAIMS about other people's source files: "this gate
imports this instrument and never calls it", "this name is reached only by a check that compares a
value with itself". Those claims were derived by one AST-walking program, so the risk is not that
they are wrong in an interesting way - it is that a bug in that one program becomes a published
inventory. Same rule as O-17: an instrument may not be the only thing standing behind its own output.

So every check below re-derives the claim by a DIFFERENT route - `tokenize` and line text, not the
builder's `ast.walk` - and additionally proves the fail-closed logic actually closes.

  C1/C2  the committed JSON and Markdown are reproduced byte-for-byte by the generator
  C3     a second run is idempotent (no hidden state, no timestamps)
  C4     the artifact's registered reasons equal the generator's KNOWN table (no drift)
  C5     every gap has a reason and every reason is still a live gap (both directions)
  C6     never_reached, tokenized: the imported bare name is never called outside import lines
  C7     never_reached, text closure: no function the gate does call contains the name in its body
  C8     only_self_comparison, textual: the name's call sites sit inside `X == Y` checks whose two
         sides were assigned from identical right-hand sides
  C9     the map agrees with the blindnesses the injection suite registered before its run
  C10    population: the gate files on disk equal the rows, and the check() census equals 169
  C11    the Markdown's numbers and tables equal the JSON (nothing hand-typed in the report)
  C12    the retracted false positive stays retracted
  C13    negative control: the fail-closed paths fire when they are supposed to (R2's "the gate can
         fail" requirement - a pin that cannot fail is decoration)
  C14    capability control on a synthetic gate: each of the three verdict classes CAN be produced,
         so the real map's `detail_only = 0` is a measurement and not a disabled detector
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import re
import subprocess
import sys
import tokenize

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
GEN = GOV / "build_coverage_map.py"
MAP = GOV / "gate_coverage_map_v1.json"
MD = M / "report/GATE_COVERAGE_MAP_v1.md"
SUITE = GOV / "gate_discrimination_gate.py"

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bare_name_lines(path, needle):
    """Lines where `needle` occurs as a NAME token not preceded by `.` - i.e. used as a bare
    identifier (a call or reference), not as `module.needle`. Comments and string literals cannot
    produce NAME tokens, so prose mentions in a detail f-string do not count."""
    lines, src = [], path.read_text(encoding="utf-8")
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    for i, t in enumerate(toks):
        if t.type == tokenize.NAME and t.string == needle:
            prev = toks[i - 1] if i else None
            if prev and prev.type == tokenize.OP and prev.string == ".":
                continue
            lines.append(t.start[0])
    return lines


def import_line_numbers(path):
    out = set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^\s*(from|import)\s", line):
            out.add(n)
    return out


def module_level_defs(path):
    """{name: body text} by line ranges - deliberately textual, so it does not reuse the builder's AST."""
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [(n, m.group(1)) for n, line in enumerate(lines, 1)
              if (m := re.match(r"^def ([A-Za-z_]\w*)\(", line))]
    out = {}
    for i, (n, fname) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else len(lines)
        out[fname] = "\n".join(lines[n - 1:end])
    return out


def called_identifiers(text):
    """Every `name(` in this source, including `mod.name(` - deliberately unfiltered."""
    return set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", text))


def text_reachable(gate_path, all_blocks):
    """Over-approximate call closure from a gate's own source, by text: every identifier used as a
    callee is treated as calling the same-named module-level def in EVERY local module. That reaches
    strictly more than the builder's import-resolved AST closure (where `rho_smooth` resolves to one
    specific module), so a pair that this control still cannot reach is airtight - the claim does not
    depend on the builder having resolved the imports the same way it claims to."""
    by_name = {}
    for stem, blocks in all_blocks.items():
        for fn in blocks:
            by_name.setdefault(fn, set()).add(stem)
    src = gate_path.read_text(encoding="utf-8")
    lines = src.splitlines()
    seeds = set()
    for t in tokenize.generate_tokens(io.StringIO(src).readline):
        if t.type != tokenize.NAME or t.string not in by_name:
            continue
        if re.match(r"^\s*(from|import)\s", lines[t.start[0] - 1]):
            continue
        if re.match(r"\s*\(", lines[t.start[0] - 1][t.start[1]:]):
            for stem in by_name[t.string]:
                seeds.add((stem, t.string))
    out, q = set(), list(seeds)
    while q:
        pair = q.pop()
        if pair in out:
            continue
        out.add(pair)
        for callee in called_identifiers(all_blocks[pair[0]][pair[1]]):
            for stem in by_name.get(callee, ()):
                if (stem, callee) not in out:
                    q.append((stem, callee))
    return out


def split_top(text, sep=","):
    """Split on `sep` only at bracket depth 0 - `rho_exact(0.6), rho_exact(0.6)` has two parts,
    `f(a, b), g(a, b)` also has two. Needed because the self-comparison lines carry commas inside
    their call parentheses. Quotes are tracked too: an unbalanced bracket inside a string literal
    (`f("(")`) must not shift the depth."""
    parts, depth, quote, cur = [], 0, None, ""
    for ch in text:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "([{":
            depth += 1
            cur += ch
        elif ch in ")]}":
            depth -= 1
            cur += ch
        elif ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts]


def find_self_comparison_checks(gate_path, needle):
    """Text version of the builder's `is_self_comparison`: a `check("N", X == Y, ...)` line where X
    and Y carry the same right-hand side - either the same element count of one tuple line
    `X, Y = E, E` or two identical `X = E` / `Y = E` lines."""
    lines = gate_path.read_text(encoding="utf-8").splitlines()
    eq_checks = []
    for line in lines:
        m = re.match(r'^\s*check\(\s*"([^"]+)"\s*,\s*(\w+)\s*==\s*(\w+)\s*,', line)
        if m:
            eq_checks.append((m.group(1), m.group(2), m.group(3)))

    def rhs(var):
        best = None
        for line in lines:
            m = re.match(r"^\s*([\w, ]+?)\s*=\s*(?!=)(.+)$", line)
            if not m:
                continue
            left = [x.strip() for x in m.group(1).split(",")]
            parts = split_top(m.group(2))
            if var not in left:
                continue
            if len(left) == len(parts) and len(set(parts)) == 1:
                best = parts[left.index(var)]
            elif len(left) == 1 and len(parts) == 1:
                best = parts[0]
        return best
    matched = []
    for cname, x, y in eq_checks:
        rx, ry = rhs(x), rhs(y)
        if rx and rx == ry and needle in rx:
            matched.append(cname)
    return matched


def synthetic_firing(gen):
    """Capability control: a hand-built gate that MUST produce one instance of each verdict class.
    The real map reports `detail_only = 0`, and "zero" is only a finding if the detector can count -
    same rule X-77 established for injections (a mutation that changes nothing proves nothing)."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "experiments").mkdir()
        (tmp / "literature").mkdir()
        (tmp / "experiments" / "mech.py").write_text(
            "def f(x):\n    return x\n\n\ndef g(x):\n    return x\n\n\ndef h(x):\n    return x\n\n\n"
            "def q(x):\n    return x\n", encoding="utf-8")
        (tmp / "experiments" / "synth_gate.py").write_text(
            "from mech import f, g, h, q\n\n\ndef check(name, ok, detail=\"\"):\n"
            "    print(name, ok, detail)\n\n\na = f(1)\nb = f(1)\ncheck(\"S1_determinism\", a == b, \"x\")\n"
            "check(\"S2_real\", g(1) == 1, f\"h = {h(2)}\")\n", encoding="utf-8")
        saved = (gen.M, gen.LOCAL_MODULES, gen.GATES, dict(gen._INFO))
        try:
            gen.M = tmp
            gen.LOCAL_MODULES = {p.stem for p in (tmp / "experiments").glob("*.py")}
            gen.GATES = sorted((tmp / "experiments").glob("*_gate.py"))
            gen._INFO.clear()
            row = gen.analyze(tmp / "experiments" / "synth_gate.py")
        finally:
            gen.M, gen.LOCAL_MODULES, gen.GATES = saved[0], saved[1], saved[2]
            gen._INFO.clear()
            gen._INFO.update(saved[3])
    return (row["never_reached"], row["only_self_comparison"], row["detail_only"])


def main() -> int:
    if not MAP.exists() or not MD.exists():
        print("artifact missing - run build_coverage_map.py first", file=sys.stderr)
        return 2
    before_json, before_md = MAP.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("C1 generator reproduces the committed JSON",
           r1.returncode == 0 and MAP.read_bytes() == before_json,
           (r1.stdout.strip().splitlines() or [""])[0][:70])
    report("C2 generator reproduces the committed Markdown", MD.read_bytes() == before_md)
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("C3 derivation idempotent (second run, byte-identical)",
           MAP.read_bytes() == before_json and MD.read_bytes() == before_md and r2.returncode == 0)

    d = json.loads(MAP.read_text(encoding="utf-8"))
    gen = load_module(GEN, "covmap_gen")
    gap_pairs = {(pathlib.Path(g["gate"]).name, g["name"])
                 for cat in d["gaps"].values() for g in cat}
    reasons = set(d["known_reasons"])
    report("C4 artifact reasons equal the generator KNOWN table",
           reasons == {f"{k[0]}::{k[1]}" for k in gen.KNOWN}
           and all(v == gen.KNOWN[tuple(k.split("::"))] for k, v in d["known_reasons"].items()),
           f"{len(reasons)} entries")
    missing = sorted(p for p in gap_pairs if f"{p[0]}::{p[1]}" not in reasons)
    stale = sorted(r for r in reasons
                   if tuple(r.split("::")) not in gap_pairs)
    report("C5 gaps registered, registrations still live", not missing and not stale,
           "unregistered=" + str(missing) + " stale=" + str(stale))

    bad6 = []
    for g in d["gaps"]["never_reached"]:
        p = M / g["gate"]
        try:
            used = [ln for ln in bare_name_lines(p, g["name"])
                    if ln not in import_line_numbers(p)]
        except (tokenize.TokenError, IndentationError) as e:
            bad6.append(g["gate"] + " tokenize error " + str(e))
            continue
        if used:
            bad6.append(f"{g['gate']}::{g['name']} called on line {used}")
    report("C6 never_reached survives a tokenize control (bare name only on import lines)",
           not bad6, "; ".join(bad6) or f"{len(d['gaps']['never_reached'])} entries re-checked")

    bad7 = []
    all_blocks = {p.stem: module_level_defs(p) for p in sorted((M / "experiments").glob("*.py"))
                  + sorted((M / "literature").glob("*.py")) if module_level_defs(p)}
    for g in d["gaps"]["never_reached"]:
        gate = M / g["gate"]
        reach = text_reachable(gate, all_blocks)
        if (g["module"], g["name"]) in reach:
            bad7.append(f"{g['gate']}::{g['name']} reachable from {(g['module'],)} by text closure")
    report("C7 never_reached survives an over-approximate text closure (no body anywhere calls it)",
           not bad7, "; ".join(bad7) or "control reaches strictly more than the AST closure does")

    bad8 = []
    for g in d["gaps"]["only_self_comparison"]:
        gate = M / g["gate"]
        matched = find_self_comparison_checks(gate, g["name"])
        if not matched:
            bad8.append(f"{g['gate']}::{g['name']} not inside any `X == Y` check with identical RHS")
    report("C8 self-comparison claims reproduce from line text", not bad8,
           "; ".join(bad8) or "each claim has an `X == Y` check with identical right-hand sides")

    suite = load_module(SUITE, "covmap_suite")
    blind = {(t["gate"], t["fn"]) for t in suite.TARGETS
             if t.get("expect") == "blind_all" and t.get("fn")}
    registered = {tuple(k.split("::")) for k in d["injection_blindnesses"]}
    predicted = gen.gap_pairs(d["rows"])
    unagreed = gen.injection_disagreements(predicted)
    report("C9 injection-registered blindnesses are all accounted for",
           blind == registered and not unagreed,
           "suite blind_all=" + str(len(blind)) + " map registered=" + str(len(registered))
           + " unagreed=" + str(sorted(unagreed)))

    disk = sorted((M / "experiments").glob("*_gate.py")) + sorted((M / "literature").glob("*_gate.py"))
    report("C10 population: every gate on disk is in the map",
           {p.relative_to(M).as_posix() for p in disk} == {r["gate"] for r in d["rows"]},
           f"{len(disk)} files")
    census = 0
    for p in disk:
        toks = list(tokenize.generate_tokens(io.StringIO(p.read_text(encoding="utf-8")).readline))
        for i, t in enumerate(toks):
            if t.type != tokenize.NAME or t.string != "check":
                continue
            prev = toks[i - 1] if i else None
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            if nxt and nxt.type == tokenize.OP and nxt.string == "(" \
                    and not (prev and prev.type == tokenize.NAME and prev.string == "def"):
                census += 1
    report("C10b check() census re-counted by tokenize", census == d["counts"]["checks"],
           f"tokenize {census} vs map {d['counts']['checks']}")

    md = MD.read_text(encoding="utf-8")

    def section(markdown, start, end):
        i = markdown.index(start)
        return markdown[i:markdown.index(end, i)]

    md_gaps = {(f, m + "." + n) for f, m, n in re.findall(
        r"^\| `(experiments/\S+|literature/\S+)` \| `(\w+)\.(\w+)` \|",
        section(md, "## 2 ", "## 3 "), re.M)}
    json_gaps = {(g["gate"], g["module"] + "." + g["name"])
                 for cat in d["gaps"].values() for g in cat}
    census = {}
    for gate, cell in re.findall(r"^\| `(experiments/\S+|literature/\S+)` \| (.+) \|$",
                                 section(md, "## 3 ", "## 4 "), re.M):
        census[gate] = re.findall(r"`([^`]+)`", cell)
    json_self = {r["gate"]: r["self_comparison_checks"] for r in d["rows"] if r["self_comparison_checks"]}
    numbers_ok = (f"覆盖人口：{d['counts']['gates']} 份" in md
                  and f"{d['counts']['checks']} 条 `check()`，{d['counts']['imported_instruments']} 个" in md
                  and f"`never_reached` {d['counts']['never_reached']} 条、"
                      f"`only_self_comparison` {d['counts']['only_self_comparison']} 条、"
                      f"`detail_only` {d['counts']['detail_only']} 条" in md
                  and f"共 {d['counts']['self_comparison_checks']} 条" in md)
    report("C11 Markdown equals the JSON (gap table, census, headline numbers)",
           md_gaps == json_gaps and census == json_self and numbers_ok,
           f"gap rows md {len(md_gaps)} vs json {len(json_gaps)}; census gates md {len(census)} vs "
           f"json {len(json_self)}; headline numbers {'match' if numbers_ok else 'MISMATCH'}")
    report("C11b bare-name gap pairs in the Markdown equal the JSON name lists",
           {(f, n.split(".")[-1]) for f, n in md_gaps}
           == {(g["gate"], g["name"]) for cat in d["gaps"].values() for g in cat})
    retracted = {("p6_gate.py", "s3_window_exists")}
    report("C12 retracted false positive stays retracted",
           d["corrected_false_positives"] and not (retracted & gap_pairs)
           and "s3_window_exists" in md,
           f"{len(d['corrected_false_positives'])} correction(s) on file")

    # C13 negative controls - the pins must actually reject. A check list that can only ever print
    # PASS is the failure mode X-78/X-79 turned into a rule, so prove each gate bites.
    key = ("p5b_gate.py", "gap_for")
    keep = gen.KNOWN[key]
    try:
        del gen.KNOWN[key]
        miss, stale2 = gen.registration_errors({"never_reached": [{"gate": "experiments/p5b_gate.py",
                                                                   "name": "gap_for"}],
                                                "only_self_comparison": []})
        bites = (key in [tuple(x) for x in miss])
    finally:
        gen.KNOWN[key] = keep
    fake = gen.injection_disagreements(predicted - {key})
    new_key = ("p9_gate.py", "agg_value")
    gen.INJECTION_BLINDNESSES[new_key] = "predicted - would have to be a real gap"
    try:
        dropped_new = gen.injection_disagreements(predicted)
    finally:
        del gen.INJECTION_BLINDNESSES[new_key]
    report("C13 fail-closed paths bite (unregistered gap, withdrawn prediction, new blind spot)",
           bites and bool(fake) and bool(dropped_new)
           and not gen.injection_disagreements(predicted),
           f"missing-pin detected={bites}, withdrawn-prediction={sorted(fake)}, "
           f"unpredicted-blind-spot={sorted(dropped_new)}")

    fire = synthetic_firing(gen)
    report("C14 every verdict class can fire (synthetic gate: 1 dead import, 1 self-comparison, "
           "1 detail-only)", fire == (["q"], ["f"], ["h"]), "detector produced " + str(fire))

    # a gate that never runs cannot be trusted: the suite must have exercised both branches
    rule_names = [n for n, _ in results]
    report("SUITE_accounting", len(rule_names) == len(set(rule_names)) and len(rule_names) >= 14,
           f"{len(rule_names)} rules, all distinct")
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    # the headline fraction is derived AFTER the last report(): the first version summed before
    # appending SUITE_accounting and printed "15/16" over sixteen PASS lines (X-78b's family).
    n_pass = sum(1 for _, p in results if p)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
