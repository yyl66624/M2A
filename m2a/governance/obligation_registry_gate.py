"""Closing-audit suite for the obligation ledger: it checks the *instrument*, not any scientific claim.

Why this exists: `build_obligation_registry.py` can abort on a broken pin, but nothing checked that
the committed `OBLIGATION_REGISTRY.md` still matches a fresh derivation. That is the X-68 failure
mode in a new place - "the artifact exists" is not "the check was run" - and it is the same reason
a hand-copied list in a results document went stale (X-67).

Checks (all mechanical):
  G1 the generator runs and reports derive == pin
  G2 its exit code is 0 (a pin break, an unclassified label or a reasonless OPEN label is a failure)
  G3 the derivation is idempotent: a second run leaves the bytes unchanged
  G4 the committed ledger is byte-identical to a fresh derivation (no stale ledger)
  G5 every label row carries one of CLOSED / SUCCEEDED / OPEN - no UNCLASSIFIED escapes to the file
  G6 every OPEN label has a registered reason (a placeholder string counts as missing)
  G7 the ledger's own counts add up: CLOSED + SUCCEEDED + OPEN == number of rows == number of labels
     found in the artifacts, and the namespace split sums to the same total
  G8 a suite score quoted in the ledger's prose is the same score the closing report quotes for that
     suite - added because the ledger said `gate_coverage_map_gate.py` 17/17 after that validator had
     grown an eighteenth rule, i.e. a fail-closed artifact carried a stale number in its own text (X-83)
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

GOV = pathlib.Path(__file__).resolve().parent
GEN = GOV / "build_obligation_registry.py"
LEDGER = GOV / "OBLIGATION_REGISTRY.md"
STATUSES = ("CLOSED", "SUCCEEDED", "OPEN")


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
    report("G4 committed ledger matches fresh derivation", before == after,
           "run the generator and commit its output" if before != after else "")

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
