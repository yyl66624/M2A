"""Suite: do the repo's gates actually refuse a wrong mechanism, or only certify themselves?

Motivation. AO §4-P6 shipped as a check that could not fail: mutating `silence()` into the reading
the protocol forbids still passed, because the two definitions coincide on every normalised measure.
That is the X-29 / R7 family (report the smallest difference an instrument can distinguish), in a new
form - not a loose tolerance but a criterion with no falsifying input.

So this suite mutates each mechanism under its own gate and requires the gate to refuse. Everything
runs on a throwaway copy in a temp directory; the repository is never modified, and no experiment is
run (this inspects instruments, per R2).

Two outcomes are recorded per target, deliberately separate:
  * refused        - the gate exited non-zero (good);
  * which check fired - because a *cross-path* check (G3-type) cannot see corruption that sits
    upstream of both paths: mutating `reading` moves both paths together only when they share the
    helper. In the first run, Phase XIX's G3 stayed silent and the refusal came from G4, the
    degenerate-case check. A gate whose only numeric check is a cross-path agreement is therefore
    not self-sufficient, which is R8's no-self-certification rule read the other way round.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

M = pathlib.Path(__file__).resolve().parent.parent
EXP = M / "experiments"

# (gate, module, anchor to find, replacement, what the mutation does)
TARGETS = [
    ("p19_gate.py", "p19_timesym.py", "",
     '\n_o = recurrence\ndef recurrence(n, c=1.0):\n    r = dict(_o(n, c))'
     '\n    r["M3"] = r["M3"] + 1e-8\n    return r\n',
     "shift M3's recurrence by 1e-8"),
    ("p20_gate.py", "p20_filter.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8"),
    ("p21_gate.py", "p21_integral.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8"),
    ("p22_gate.py", "p22_powerlaw.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8"),
    ("ao_preflight_gate.py", "ao_opp.py",
     '    return mu.get(NONE, 0.0)',
     '    return 1.0 - sum(v for k, v in mu.items() if k != NONE)',
     "replace the event definition of Z with the forbidden complement reading"),
]


def run_one(tmp, gate, module, find, replace):
    src = pathlib.Path(tmp) / module
    text = src.read_text(encoding="utf-8")
    if find:
        if text.count(find) != 1:
            return None, ["anchor found " + str(text.count(find)) + " times in " + module
                          + ", expected exactly 1"]
        src.write_text(text.replace(find, replace, 1), encoding="utf-8")
    else:
        src.write_text(text + replace, encoding="utf-8")
    r = subprocess.run([sys.executable, str(pathlib.Path(tmp) / gate)], cwd=tmp,
                       capture_output=True, text=True, timeout=900)
    return r.returncode, re.findall(r"^FAIL\s+(\S+)", r.stdout, re.M)


def main() -> int:
    checks = ok = 0

    def report(name, passed, detail=""):
        nonlocal checks, ok
        checks += 1
        ok += int(passed)
        print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))

    for gate, module, find, replace, what in TARGETS:
        tmp = tempfile.mkdtemp(prefix="gate_audit_")
        try:
            work = pathlib.Path(tmp) / "experiments"
            shutil.copytree(EXP, work)
            rc, fails = run_one(str(work), gate, module, find, replace)
            if rc is None:
                report("MUT_" + gate.split("_")[0], False, "; ".join(fails))
                continue
            report("MUT_" + gate.split("_")[0] + "_refused", rc != 0,
                   f"{what}: exit {rc}, checks that fired: "
                   + (", ".join(fails) if fails else "(none - gate passed a wrong mechanism!)"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"{ok}/{checks} checks passed")
    return 0 if ok == checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
