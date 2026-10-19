"""Validator for the runner-side gate-enforcement map: instrument checks only (R2).

The map (`build_runner_enforcement_map.py`) turns "the runner refuses when the gate is red" from a
docstring into a syntactic fact. Everything it says is produced by one AST program, so this suite
re-derives each claim by text/line scanning (a different route), proves the detector can produce
EVERY verdict - including the four bad ones, which the live population does not contain - and proves
the fail-closed registration actually bites.

  T1/T2/T3  the committed JSON and Markdown are reproduced byte-for-byte; a second run is identical
  T4        population recomputed by text (writer = dump/write_text/open-w naming a committed JSON)
  T5        reads are not writes: `json.load(open("x_results.json"))` must not count (the false
            positive this deriver produced first, which made four runners look like they were
            rewriting earlier rounds' frozen artifacts)
  T6        every `enforced` row re-checked by line text: a gate subprocess call AND a stop line
            (return / raise / sys.exit) under an if that consults the return code or run_gate()
  T7        every registered no-gate reason names an artifact its file really writes
  T8        all four bad verdicts fire on synthetic runners (a verdict nobody can produce is decoration)
  T9        the registration check bites in both directions
  T10       Markdown equals the JSON (numbers and per-row table)
  T11       every round runner on disk is in the population and is enforced - the headline claim
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
GEN = GOV / "build_runner_enforcement_map.py"
MAP = GOV / "runner_enforcement_map_v1.json"
MD = M / "report/RUNNER_GATE_ENFORCEMENT_v1.md"

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def load_gen():
    spec = importlib.util.spec_from_file_location("enf_gen", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def text_verdict(path):
    """Independent, line-based reading of the same question: is the gate run, and does a red gate
    stop the program before anything is written?"""
    lines = path.read_text(encoding="utf-8").splitlines()
    run_lines = [i for i, l in enumerate(lines)
                 if "subprocess." in l and re.search(r"_gate\.py", l)]
    stop_at = None
    for i, l in enumerate(lines):
        if not re.match(r"^\s*if .*returncode", l) and not re.match(r"^\s*if .*\brun_gate\(\)", l) \
                and not re.match(r"^\s*if .*\b(code|rc|out|res)\b.*!= *0", l):
            continue
        for j in range(i + 1, min(i + 8, len(lines))):
            if re.match(r"^\s*(return\s+(?!0\b)\S|raise\b|sys\.exit)", lines[j]):
                stop_at = i
                break
        if stop_at is not None:
            break
    write_lines = [i for i, l in enumerate(lines)
                   if re.search(r"(json\.dump|write_text|write_bytes)\(", l)
                   and re.search(r"_results\.json|_reanalysis\.json|_coding\.json|_posthoc\.json"
                                 r"|closure_report\.json", l)]
    return run_lines, stop_at, write_lines


def synthetic(gen, body, artifact="x_results.json"):
    """Run the deriver's `analyze` on a hand-written runner inside a throwaway tree."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        (tmp / "experiments").mkdir()
        (tmp / "literature").mkdir()
        f = tmp / "experiments" / "run_x.py"
        f.write_text(body, encoding="utf-8")
        saved = (gen.M, gen.ARTIFACT_NAMES, gen.ARTIFACT, gen.KNOWN_NO_GATE)
        try:
            gen.M = tmp
            gen.ARTIFACT_NAMES = {artifact}
            gen.ARTIFACT = __import__("re").compile(__import__("re").escape(artifact))
            gen.KNOWN_NO_GATE = {}
            return gen.analyze(f)
        finally:
            gen.M, gen.ARTIFACT_NAMES, gen.ARTIFACT, gen.KNOWN_NO_GATE = saved


HEADER = "import json, subprocess, sys\n\n\ndef main():\n"
SHAPES = {
    "enforced": HEADER + "    g = subprocess.run([sys.executable, 'x_gate.py'])\n"
                "    if g.returncode != 0:\n        return 1\n"
                "    json.dump({}, open('x_results.json', 'w'))\n    return 0\n",
    "gate_ran_but_rc_unchecked": HEADER + "    subprocess.run([sys.executable, 'x_gate.py'])\n"
                "    json.dump({}, open('x_results.json', 'w'))\n    return 0\n",
    "rc_checked_but_refusal_does_not_stop": HEADER + "    g = subprocess.run([sys.executable, 'x_gate.py'])\n"
                "    if g.returncode != 0:\n        print('gate failed')\n"
                "    json.dump({}, open('x_results.json', 'w'))\n    return 0\n",
    "writes_before_the_guard": HEADER + "    json.dump({}, open('x_results.json', 'w'))\n"
                "    g = subprocess.run([sys.executable, 'x_gate.py'])\n"
                "    if g.returncode != 0:\n        return 1\n    return 0\n",
    "no_gate_at_all": HEADER + "    json.dump({}, open('x_results.json', 'w'))\n    return 0\n",
}


def main() -> int:
    if not MAP.exists() or not MD.exists():
        print("artifact missing - run build_runner_enforcement_map.py first", file=sys.stderr)
        return 2
    before_json, before_md = MAP.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("T1 generator reproduces the committed JSON",
           r1.returncode == 0 and MAP.read_bytes() == before_json,
           (r1.stdout.strip().splitlines() or [""])[1][:60] if r1.stdout.strip() else "")
    report("T2 generator reproduces the committed Markdown", MD.read_bytes() == before_md)
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("T3 derivation idempotent", MAP.read_bytes() == before_json and MD.read_bytes() == before_md
           and r2.returncode == 0)

    d = json.loads(MAP.read_text(encoding="utf-8"))
    gen = load_gen()

    by_text = {}
    for p in sorted((M / "experiments").glob("*.py")) + sorted((M / "literature").glob("*.py")):
        runs, stop, writes = text_verdict(p)
        if writes:
            by_text[p.name] = (bool(runs), stop is not None)
    by_name = {pathlib.Path(r["runner"]).name: r for r in d["rows"]}
    mismatched = []
    for name, (ran, stopped) in by_text.items():
        row = by_name.get(name)
        if row is None:
            continue
        ast_ran = bool(row["gate_calls"])
        ast_stops = any(g["stops"] for g in row["rc_guards"])
        if (ran, stopped) != (ast_ran, ast_stops):
            mismatched.append(f"{name}: text {(ran, stopped)} vs ast {(ast_ran, ast_stops)}")
    report("T4 text re-derivation agrees with the AST population",
           not mismatched, "; ".join(mismatched) or f"{len(by_text)} writers re-checked")
    report("T4b every writer found by text is in the map",
           {n for n in by_text} <= set(by_name),
           f"text {len(by_text)} vs map {len(by_name)} | map-only (text cannot see the target, it is "
           "held in a variable): " + str(sorted(set(by_name) - set(by_text))))

    read_only = HEADER.replace("json, subprocess, sys", "json, sys") \
        + "    data = json.load(open('x_results.json'))\n    return data and 0\n"
    r5 = synthetic(gen, read_only)
    report("T5 a read of an artifact is not counted as a write",
           r5["artifact_writes"] == [] and r5["verdict"] == "no_gate_at_all",
           str(r5["artifact_writes"]))

    bad = []
    n_enf = sum(1 for r in d["rows"] if r["verdict"] == "enforced")
    for r in d["rows"]:
        if r["verdict"] != "enforced":
            continue
        runs, stop, _ = text_verdict(M / r["runner"])
        if not runs or stop is None:
            bad.append(r["runner"] + " text says runs=" + str(bool(runs)) + " stop=" + str(stop))
    report("T6 every enforced row also stops by line text", not bad,
           "; ".join(bad) or str(n_enf) + " rows re-checked")

    wrong = []
    for k, reason in d["known_no_gate"].items():
        row = next((r for r in d["rows"] if r["file"] == k), None)
        if row is None or not any(a in reason for a in row["artifacts_written"]):
            wrong.append(k)
    report("T7 each no-gate reason names an artifact the file really writes", not wrong,
           "reasons without a referent: " + (", ".join(wrong) or "none"))

    fired = {k: synthetic(gen, v)["verdict"] for k, v in SHAPES.items()}
    report("T8 all five verdicts are producible (four of them only by construction)",
           all(fired[k] == k for k in SHAPES), str(fired))

    extra = d["rows"] + [{"file": "run_new.py", "verdict": "no_gate_at_all",
                          "artifacts_written": ["new_results.json"]}]
    unreg, stale_new, _ = gen.registration_errors(extra)
    flipped = [dict(r, verdict="enforced") if r["file"] == "p6_reanalyze.py" else r
               for r in d["rows"]]
    unreg2, stale, _ = gen.registration_errors(flipped)
    report("T9 registration bites both ways (unregistered writer, pin that no longer applies)",
           unreg == ["run_new.py"] and stale_new == []
           and unreg2 == [] and stale == ["p6_reanalyze.py"],
           f"unregistered={unreg} | stale={stale}")

    md = MD.read_text(encoding="utf-8")
    tbl = re.findall(r"^\| `(experiments/\S+|literature/\S+)` \| (.+) \| (.+) \| (.+) \| `(\w+)` \|$",
                     md, re.M)
    report("T10 Markdown equals the JSON (table rows, verdicts, headline numbers)",
           {t[0] for t in tbl} == {r["runner"] for r in d["rows"]}
           and {t[4] for t in tbl} == {r["verdict"] for r in d["rows"]}
           and f"判定：**enforced {d['counts']['enforced']}**" in md
           and f"**{d['counts']['writers']} 个工件写入者**，写 **{d['counts']['artifacts']} 个**" in md,
           f"md rows {len(tbl)} vs json {len(d['rows'])}")

    phase_runners = sorted(p.name for p in (M / "experiments").glob("run_phase*.py"))
    missing = [n for n in phase_runners if n not in by_name]
    not_enforced = [r["runner"] for r in d["rows"]
                    if r["file"].startswith("run_phase") and r["verdict"] != "enforced"]
    report("T11 every round runner is in the population and enforced",
           not missing and not not_enforced,
           f"{len(phase_runners)} runners | missing={missing} not_enforced={not_enforced}")

    rule_names = [n for n, _ in results]
    report("SUITE_accounting", len(rule_names) == len(set(rule_names)) and len(rule_names) >= 11,
           f"{len(rule_names)} rules, all distinct")
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    n_pass = sum(1 for _, p in results if p)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
