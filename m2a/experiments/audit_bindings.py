"""Closing audit (M2A_FINAL_REPORT 15.1 / 15.2): run every gate suite and re-derive the pre-registration
hash bindings from the artifacts themselves, so no hand-transcribed value can serve as a reference.

Run from anywhere: `python3 m2a/experiments/audit_bindings.py`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

EXP = pathlib.Path(__file__).resolve().parent
ROOT = EXP.parent.parent


def suites():
    return sorted(p.name for p in EXP.glob("*gate*.py"))


def bindings():
    out = []
    for jf in sorted(EXP.glob("phase*_results.json")):
        recorded = json.loads(jf.read_text(encoding="utf-8")).get("prereg_sha256")
        if recorded is None:
            continue
        pname = jf.name.replace("_results.json", "").upper() + "_PREREGISTRATION.md"
        pf = EXP / pname
        disk = hashlib.sha256(pf.read_bytes()).hexdigest()
        blob = subprocess.run(["git", "show", f"HEAD:{EXP.relative_to(ROOT)}/{pname}"], cwd=ROOT,
                              capture_output=True).stdout
        git_h = hashlib.sha256(blob).hexdigest()
        out.append((pname, recorded, disk, git_h, disk == recorded == git_h))
    return out


def main() -> int:
    names = suites()
    green, checks = 0, 0
    print(f"gate suites: {len(names)}")
    for s in names:
        r = subprocess.run([sys.executable, s], cwd=EXP, capture_output=True, text=True)
        summary = [l for l in r.stdout.splitlines() if "checks passed" in l]
        if not summary:
            print(f"FAIL  {s}  (no summary line)")
            continue
        a, b = summary[-1].split()[0].split("/")
        ok = r.returncode == 0 and int(a) == int(b)
        green += int(ok)
        checks += int(b)
        print(f"{'PASS' if ok else 'FAIL'}  {s:26s} {a}/{b}")

    print("\npre-registration hash bindings (recorded / disk / git object):")
    rows = bindings()
    for pname, recorded, disk, git_h, ok in rows:
        print(f"{'MATCH' if ok else 'MISMATCH'}  {pname:34s} {recorded[:12]} / {disk[:12]} / {git_h[:12]}")

    print(f"\nSUMMARY  suites {green}/{len(names)} green, checks {checks}, bindings "
          f"{sum(r[-1] for r in rows)}/{len(rows)}")
    return 0 if green == len(names) and all(r[-1] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
