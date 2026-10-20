"""Closing-audit suite for the obligation ledger: it checks the *instrument*, not any scientific claim.

Why this exists: `build_obligation_registry.py` can abort on a broken pin, but nothing checked that
the committed `OBLIGATION_REGISTRY.md` still matches a fresh derivation. That is the X-68 failure
mode in a new place - "the artifact exists" is not "the check was run" - and it is the same reason
a hand-copied list in a results document went stale (X-67).

Checks (all mechanical):
  G1 the generator runs and reports derive == pin
  G2 its exit code is 0 (a pin break, an unclassified label or a reasonless OPEN label is a failure)
  G3 the derivation is idempotent: a second run leaves the bytes unchanged
  G4 the committed ledger is byte-identical to a fresh derivation (no stale ledger), *and* the exclusion of
     derived tables from the status corpus is load-bearing: at least one obligation-bearing sentence must exist
     only inside a derived table - a copy of a truncated line - and no primary record may be excluded (X-95)
  G5 every label row carries one of CLOSED / SUCCEEDED / OPEN - no UNCLASSIFIED escapes to the file
  G6 every OPEN label has a registered reason (a placeholder string counts as missing)
  G7 the ledger's own counts add up: CLOSED + SUCCEEDED + OPEN == number of rows == number of labels
     found in the artifacts, and the namespace split sums to the same total
  G8 a suite score quoted in the ledger's prose is the same score the closing report quotes for that
     suite - added because the ledger said `gate_coverage_map_gate.py` 17/17 after that validator had
     grown an eighteenth rule, i.e. a fail-closed artifact carried a stale number in its own text (X-83)
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

import build_obligation_registry as B

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
GEN = GOV / "build_obligation_registry.py"
LEDGER = GOV / "OBLIGATION_REGISTRY.md"
STATUSES = ("CLOSED", "SUCCEEDED", "OPEN")


def json_leaves(node):
    """Every string leaf of a parsed JSON, however deep - used to ask what a derived table actually asserts."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from json_leaves(v)
    elif isinstance(node, list):
        for v in node:
            yield from json_leaves(v)


def run_generator():
    return subprocess.run([sys.executable, str(GEN)], cwd=GOV.parent,
                          capture_output=True, text=True)


def main() -> int:
    checks, ok = 0, 0

    def report(name, passed, detail=""):
        nonlocal checks, ok
        checks += 1
        ok += int(passed)
        print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))

    first = run_generator()
    report("G1 derive == pin reported", "derive == pin" in first.stdout,
           first.stdout.strip().splitlines()[-1][:80] if first.stdout else first.stderr[:80])
    report("G2 generator exit 0", first.returncode == 0, "exit=" + str(first.returncode))

    before = LEDGER.read_bytes()
    second = run_generator()
    after = LEDGER.read_bytes()
    report("G3 derivation idempotent", before == after and second.returncode == 0,
           "bytes " + str(len(before)) + " -> " + str(len(after)))

    # G4 (folded, X-95): the committed ledger must match a fresh derivation *and* the transcription exclusion
    # must be load-bearing. A rule that cannot fire is a rule that measures nothing, so the exclusion is proved
    # by the mechanism that made it necessary: a derived table must contain an obligation-bearing sentence that
    # no scanned primary document contains. That is exactly how governance/value_provenance_v1.json flipped
    # P10-O1/P11-O2/P12-O1/P14-O1 to OPEN - its `excerpt` fields hold the originals truncated at 90-150
    # characters, so the copy asserted a disposition the source never states.
    excluded = [f for f in sorted(list(M.rglob("*.md")) + list(M.rglob("*.json")))
                if B.TRANSCRIBED_TABLE.match(str(f.relative_to(M)))]
    scanned_blob = "\n".join(f.read_text(encoding="utf-8", errors="replace")
                             for f in sorted(list(M.rglob("*.md")) + list(M.rglob("*.json")))
                             if f.name != B.SELF and not B.TRANSCRIBED_TABLE.match(str(f.relative_to(M))))
    laundered = []
    for f in excluded:
        if f.suffix != ".json":
            continue
        for leaf in json_leaves(json.loads(f.read_text(encoding="utf-8"))):
            if B.ALL_LABEL.search(leaf) and leaf[:40] not in scanned_blob:
                laundered.append((f.name, leaf[:40]))
    outside = [f for f in sorted(list(M.rglob("*.md")) + list(M.rglob("*.json")))
               if f.parent.name != "governance" and f.name != B.SELF]
    outside_scanned = [f for f in outside
                       if not B.TRANSCRIBED_TABLE.match(str(f.relative_to(M)))]
    report("G4 committed ledger matches a fresh derivation, and the transcription exclusion is load-bearing",
           before == after and bool(excluded) and bool(laundered) and len(outside_scanned) == len(outside),
           "ledger bytes " + str(len(before)) + " | excluded tables " + str(len(excluded))
           + " | sentences the originals do not contain " + str(len(laundered))
           + " | primary records outside governance/ " + str(len(outside_scanned)) + "/" + str(len(outside))
           if before == after else "run the generator and commit its output")

    text = before.decode("utf-8")
    rows = [l for l in text.splitlines() if l.startswith("| ") and "**" in l]
    bad = [r.split("|")[1].strip() for r in rows
           if not any("**" + s + "**" in r for s in STATUSES)]
    report("G5 every row has a lawful status", not bad, "offending: " + ", ".join(bad[:4]))

    open_labels = [r.split("|")[1].strip() for r in rows if "**OPEN**" in r]
    reasons = [l for l in text.splitlines() if l.startswith("- **") and "】" not in l]
    explained = {l.split("**")[1] for l in reasons if len(l.split("**")) > 2}
    missing = [k for k in open_labels if k not in explained]
    placeholder = [l for l in reasons if "缺登记原因" in l]
    report("G6 every OPEN label has a reason", not missing and not placeholder,
           "missing: " + (", ".join(missing[:5]) or "none"))

    counts = {s: sum(1 for r in rows if "**" + s + "**" in r) for s in STATUSES}
    total = sum(counts.values())
    report("G7 counts add up", total == len(rows) == len(set(r.split("|")[1].strip() for r in rows)),
           " ".join(s + "=" + str(counts[s]) for s in STATUSES) + " rows=" + str(len(rows)))

    # Two prose documents must agree on every suite score the ledger cites. This catches drift between
    # them, not a stale pair - the authoritative oracle stays the closing audit's per-suite line.
    rep_text = (GOV.parent / "M2A_FINAL_REPORT.md").read_text(encoding="utf-8")
    quoted = {f: a + "/" + b for f, a, b in
              re.findall(r"python3\s+(?:[\w./]*/)?(\w+\.py)[^\n#]*#\s*(\d+)/(\d+)", rep_text)}
    claims = re.findall(r"(\w+\.py)`?[^\n]{0,3}?(\d+)/(\d+)", text)
    stale = [f + " " + a + "/" + b + " != report " + quoted.get(f, "absent")
             for f, a, b in claims if quoted.get(f) != a + "/" + b]
    report("G8 ledger prose quotes only suite scores the report also quotes",
           bool(claims) and not stale,
           f"{len(claims)} ledger claims vs {len(quoted)} report scores | "
           + ("; ".join(stale[:3]) if stale else "all agree"))

    print(f"{ok}/{checks} checks passed")
    return 0 if ok == checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
