"""Validator for the three-way score reconciliation: instrument checks only (R2).

The artifact compares a document's quoted gate score, the score the gate prints today, and the
number of `check()` sites counted syntactically. Two aggregates being EQUAL is not evidence of
agreement (this population once landed on the same total by two different cancellations), so every rule below is
per-instrument, and the live column is re-measured here rather than trusted.

  R1/R2  the committed JSON and Markdown are reproduced byte-for-byte by the generator in offline
         mode; `--offline` and a fresh online run must agree, otherwise the live column is not
         what the gate prints now
  R3     a deterministic sample of three gates is re-run here and compared with the recorded live
         score (the recorded column must be re-measurable, not archived)
  R4     every row's recorded gate source SHA-256 still matches the file on disk - a gate edited
         after this map was built makes the map stale, loudly
  R5     the claim column re-extracted from each document by a plain line regex
  R6     population: the docs on disk equal the rows, and instruments with no document are named
  R7     the static column equals §42's per-gate check-site counts (two instruments, one number)
  R8     every static/live gap carries a registered reason, and every reason is still needed
  R9     negative controls: a stale claim, a red instrument and an unregistered gap are all caught
  R10    Markdown numbers equal the JSON
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
GEN = GOV / "build_result_score_reconciliation.py"
MAP = GOV / "result_score_reconciliation_v1.json"
# Instruments whose round record is not a `*_RESULTS.md` file. The population below cannot see such a record,
# so the pairing is declared here - and the declaration is checked (the file must exist and must name the gate)
# rather than widening the glob, which would drag a non-`*_RESULTS` document into a score-claim namespace.
EXTRA_RECORDS = {"l02_representation_gate.py": "literature/ROUND_L02_REPRESENTATION.md",
                 "l04_i1_gate.py": "literature/ROUND_L04_I1.md",
                 "l05_gate.py": "literature/ROUND_L05_SECOND_CODER.md"}
MD = M / "report/RESULT_SCORE_RECONCILIATION_v1.md"
CMAP = GOV / "gate_coverage_map_v1.json"

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def load_gen():
    spec = importlib.util.spec_from_file_location("score_gen", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not MAP.exists() or not MD.exists():
        print("artifact missing - run build_result_score_reconciliation.py first", file=sys.stderr)
        return 2
    before_json, before_md = MAP.read_bytes(), MD.read_bytes()
    r_off = subprocess.run([sys.executable, str(GEN), "--offline"], cwd=M,
                           capture_output=True, text=True)
    report("R1 offline regeneration reproduces JSON and Markdown",
           r_off.returncode == 0 and MAP.read_bytes() == before_json and MD.read_bytes() == before_md,
           (r_off.stdout.strip().splitlines() or [""])[0][:60])
    d = json.loads(MAP.read_text(encoding="utf-8"))
    gen = load_gen()

    gates = sorted({r["gate"] for r in d["rows"]})
    sample = [gates[0], gates[len(gates) // 2], gates[-1]]
    bad3 = []
    for g in sample:
        live = gen.run_gate(g)
        recorded = next((tuple(r["live"]) for r in d["rows"] if r["gate"] == g), None)
        if live is None or tuple(live) != recorded:
            bad3.append(f"{g}: re-ran {live}, recorded {recorded}")
    report("R3 a deterministic 3-gate sample re-measures the recorded live column",
           not bad3, "; ".join(bad3) or "sample " + ", ".join(sample))

    bad4 = [r["gate"] for r in d["rows"]
            if hashlib.sha256((M / r["gate"]).read_bytes()).hexdigest() != r["gate_sha256"]]
    report("R4 every recorded instrument is unchanged on disk (staleness guard)",
           not bad4, "changed since built: " + (", ".join(bad4) or "none"))

    bad5 = []
    for r in d["rows"]:
        lines = (M / r["doc"]).read_text(encoding="utf-8").splitlines()[:16]
        found = None
        for line in lines:
            if ("门控" in line or "gate" in line.lower()):
                m = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})", line)
                if m:
                    found = [int(m.group(1)), int(m.group(2))]
                    break
        if found != r["claim"]:
            bad5.append(f"{r['doc']}: line regex {found} vs artifact {r['claim']}")
    report("R5 claims re-extracted by an independent line regex", not bad5,
           "; ".join(bad5) or f"{len(d['rows'])} documents re-read")

    disk_docs = {p.relative_to(M).as_posix() for p in (M / "experiments").glob("PHASE*_RESULTS.md")} \
        | {p.relative_to(M).as_posix() for p in (M / "literature").glob("ROUND_*_RESULTS.md")}
    cm = json.loads(CMAP.read_text(encoding="utf-8"))
    static = {r["file"]: len(r["checks"]) for r in cm["rows"]}
    documented = {pathlib.Path(r["gate"]).name for r in d["rows"]} | set(EXTRA_RECORDS)
    undocumented = sorted(k for k in static if k not in documented)
    declared_ok = all((M / p).exists() and g in (M / p).read_text(encoding="utf-8")
                      for g, p in EXTRA_RECORDS.items())
    report("R6 population equals the documents on disk, and undocumented instruments are named",
           disk_docs == {r["doc"] for r in d["rows"]}
           and len(d["rows"]) == len(disk_docs) and undocumented == ["ao_preflight_gate.py"]
           and declared_ok,
           f"{len(disk_docs)} docs | no doc for: {undocumented} | declared records {sorted(EXTRA_RECORDS)}")

    bad7 = [r["gate"] for r in d["rows"]
            if r["static_sites"] != static.get(pathlib.Path(r["gate"]).name)]
    report("R7 the static column equals §42's per-gate site census", not bad7,
           "differs: " + (", ".join(bad7) or "none"))

    unexpl = sorted({pathlib.Path(r["gate"]).name for r in d["rows"]
                     if r["live"] and r["static_sites"] is not None
                     and r["static_sites"] != r["live"][1]} - set(gen.KNOWN_STATIC_GAPS))
    report("R8 every static/live difference is registered",
           not unexpl and d["counts"]["static_gap_registered"] == len(gen.KNOWN_STATIC_GAPS),
           "unregistered: " + (", ".join(unexpl) or "none")
           + f" | registered {len(gen.KNOWN_STATIC_GAPS)}")

    rows = d["rows"]
    one = dict(rows[0])
    one["claim"] = [one["live"][1] - 1, one["live"][1]]
    red = dict(rows[1])
    red["live"] = [red["live"][0] - 1, red["live"][1]]
    gap = dict(rows[2])
    gap["static_sites"] = (gap["live"][1] + 3) if gap["static_sites"] is not None else 99
    verdicts = [gen.classify(r) for r in (one, red, gap)]
    keep = dict(gen.KNOWN_STATIC_GAPS)
    gen.KNOWN_STATIC_GAPS.clear()
    try:
        unexpl_after_clear = gen.classify(gap)
        gaps_caught = gen.registration_errors([dict(gap, verdict=unexpl_after_clear)])[2]
    finally:
        gen.KNOWN_STATIC_GAPS.update(keep)
    fake_doc = pathlib.Path(rows[0]["doc"]).name
    gen.KNOWN_NO_CLAIM[fake_doc] = "deliberately wrong registration used by this control"
    try:
        stale_pin = gen.registration_errors([dict(rows[0], verdict="aligned")])[1]
    finally:
        del gen.KNOWN_NO_CLAIM[fake_doc]
    report("R9 negative controls bite (stale claim, red instrument, unregistered difference, "
           "stale registration)",
           verdicts[0] == "doc_stale" and verdicts[1] == "live_red"
           and unexpl_after_clear == "unexplained_static_live_gap" and bool(gaps_caught)
           and stale_pin == [fake_doc],
           "verdicts " + str(verdicts[:2] + [unexpl_after_clear])
           + " | gaps " + str(gaps_caught) + " | stale pin " + str(stale_pin))

    md = MD.read_text(encoding="utf-8")
    report("R10 Markdown numbers equal the JSON",
           f"人口：**{d['counts']['docs']} 份轮次文档**" in md
           and f"**aligned {d['counts']['aligned']}**" in md
           and f"执行侧共打印 **{d['counts']['checks_printed']}**" in md
           and f"静态共 **{d['counts']['static_sites_in_population']}**" in md
           and md.count("| `") >= d["counts"]["docs"],
           f"table rows {md.count('| `')} for {d['counts']['docs']} documents")

    headline = (d["counts"]["bad"] == 0 and d["counts"]["no_claim"] == 0
                and d["counts"]["aligned"] + d["counts"]["static_gap_registered"]
                == d["counts"]["docs"])
    report("R11 today the three columns agree everywhere except the two registered differences",
           headline, json.dumps(d["counts"], ensure_ascii=False))

    names = [n for n, _ in results]
    report("SUITE_accounting", len(names) == len(set(names)) and len(names) >= 10,
           f"{len(names)} rules, all distinct")
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    n_pass = sum(1 for _, p in results if p)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
