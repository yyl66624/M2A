"""Suite: do the repo's gates refuse a wrong mechanism, or only certify themselves?

Motivation. AO §4-P6 shipped as a check that could not fail: mutating `silence()` into the reading
the protocol forbids still passed, because the two definitions coincide on every normalised measure.
That is the X-29 / R7 family (report the smallest difference an instrument can distinguish), in a new
form - not a loose tolerance but a criterion with no falsifying input.

So this suite mutates each mechanism under its own gate and requires the gate to refuse. Everything
runs on a throwaway copy in a temp directory; the repository is never modified, and no experiment is
run (this inspects instruments, per R2).

Three outcomes are recorded per target, deliberately separate:
  * refused        - the gate exited non-zero AND printed at least one FAIL line;
  * blind          - the gate stayed green on a mutation that demonstrably changed a reading;
  * crashed        - non-zero exit with no FAIL line, i.e. the mutation broke the program rather than
    being caught by a criterion. The first pass of this suite counted a crash as a refusal; that is a
    hole in the audit instrument itself, closed here (a refusal must name the check that refused).

Two controls run before a target's verdict is trusted:
  * the mutated module must still import (syntax/NameError guard, the R1.1 class);
  * the mutation must change a probe reading (R8: an accepted mutation that does nothing is not
    evidence about the gate - it is evidence about the probe).

Expectations are set from the registered tolerance BEFORE the run, not from the observed result: a
target predicted `blind` is one whose registered tolerance is coarser than the injected error, and a
predicted-blind target that refuses is reported as a failed prediction.

What each refusal is attributed to matters as much as the refusal, but only so much can be said
mechanically: the fired check NAMES are printed, and each refusal is tagged by whether the names
claim a referent outside the module (a committed artifact, a hand-written multiset, a closed form) or
only claim consistency. That tag is a name heuristic - see `classify` - because code-path sharing is
not derivable from a check's name, and the X-76 case is precisely a two-path check that stayed silent
with both paths downstream of the mutated helper. The rule this suite can and does enforce is the
weaker one: a gate must refuse at least one instrument-side mutation, and every refusal must name a
check rather than a crash.

Which SIDE of a round a mutation lands on decides what a blind verdict means, and the two must not be
conflated (R2):
  * instrument-side - the mutation corrupts the measuring device (grid, root finder, tail index,
    aggregator, measurand definition). A gate that stays green here is not an instrument, it is a
    certificate: the rule below requires every gate to refuse at least one instrument-side mutation.
  * claim-side - the mutation changes the quantity the round was built to test (the analytic beta*
    law of Phase XI). The gate must NOT refuse it: refusing it would mean the instrument re-tests the
    science, which is what R2 forbids. Its guard is elsewhere - the reading is frozen in a committed
    results JSON whose bytes are hash-bound, so a changed claim shows up as a broken binding, not as a
    gate failure. Such targets are registered as expect="blind" and a refusal is reported as a
    prediction failure worth reading.
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
TIMEOUT = 2400

# The injected mechanism error. 1e-4 relative is ~1e5 times every registered anchor tolerance
# (1e-9 rel, 1e-15, exact equality) and still far below the smallest EFFECT any round measures
# (1.25e-3 at J=800), so a refusal says "the gate tracks the committed reading", not
# "the gate tracks a grossly broken program".
REL = 1e-4


def wrap(fn: str) -> str:
    """Code appended to a module to redefine `fn` with a relative shift of every finite numeric
    return. Sentinels survive untouched: None and non-scalars pass through (TypeError), +-inf stays
    inf - so the mutation is a wrong reading, not a wrong program."""
    return ("\n_o = " + fn + "\ndef " + fn + "(*a, **k):\n"
            "    v = _o(*a, **k)\n    try:\n"
            "        import math as _mm\n"
            "        return v * (1.0 + " + repr(REL) + ") if _mm.isfinite(v) else v\n"
            "    except TypeError:\n        return v\n")


ANCHOR_WORDS = ("anchor", "committed", "reproduces", "hand", "unchanged", "identical", "vs_")
# (gate, module, anchor-text ["" = append], replacement, what the mutation does,
#  probe expression evaluated in the module namespace, expect, side)
TARGETS = [
    # ---- first pass (report 39 / X-76), kept byte-identical
    ("p19_gate.py", "p19_timesym.py", "",
     '\n_o = recurrence\ndef recurrence(n, c=1.0):\n    r = dict(_o(n, c))'
     '\n    r["M3"] = r["M3"] + 1e-8\n    return r\n',
     "shift M3's recurrence by 1e-8", 'recurrence(6)["M3"]', "refused", "instrument"),
    ("p20_gate.py", "p20_filter.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8", 'reading("M3", 7, 1.3, True)', "refused", "instrument"),
    ("p21_gate.py", "p21_integral.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8", 'reading("M5", 9, 0.7, True)', "refused", "instrument"),
    ("p22_gate.py", "p22_powerlaw.py", "",
     "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
     "shift the closed-form reading by 1e-8", 'reading(CLASSES[0], 9, 1.0, True)', "refused", "instrument"),
    ("ao_preflight_gate.py", "ao_opp.py",
     '    return mu.get(NONE, 0.0)',
     '    return 1.0 - sum(v for k, v in mu.items() if k != NONE)',
     "replace the event definition of Z with the forbidden complement reading",
     'silence({"a1": 0.5, "a2": 0.2, NONE: 0.3})', "refused", "instrument"),

    # ---- generalisation: the module-backed gates of Phases IX-XVIII, one reading shift each
    ("p9_gate.py", "p9_aggregation.py", "", wrap("agg_value"),
     "shift every t-norm aggregation by 1e-4",
     'agg_value("lukasiewicz", [0.3, 1.0])', "refused", "instrument"),
    ("p10_gate.py", "p10_exponent.py", "", wrap("root_R"),
     "shift the onset root of the cubic by 1e-4",
     "root_R(0.85, 3.7, 61.0)", "refused", "instrument"),
    ("p11_gate.py", "p11_softband.py", "", wrap("L_tau"),
     "shift every reachable band level by 1e-4",
     'L_tau("lukasiewicz", 2, 0.3)', "refused", "instrument"),
    ("p11_gate.py", "p11_softband.py", "", wrap("predicted"),
     "shift the analytic beta* law by 1e-4",
     'predicted("logistic", 2, 0.5)', "blind", "claim"),
    ("p12_gate.py", "p12_lattice.py", "", wrap("rho_smooth"),
     "shift the smoothed lattice reading R^2 by 1e-4",
     "rho_smooth(1.137, 0.75)", "refused", "instrument"),
    ("p13_gate.py", "p13_closeout.py", "", wrap("q_cont"),
     "shift the continuous Poisson quantile by 1e-4",
     "q_cont(3.0)", "blind", "instrument"),   # W2's registered tolerance is ONE COUNT; 1e-4 x ~5.7
                                              # counts is ~6e-4 counts, so the check cannot see it.
    ("p14_gate.py", "p14_ratelaw.py", "", wrap("level"),
     "shift the band level lo(J) by 1e-4", "level(40)", "refused", "instrument"),
    ("p15_gate.py", "p13_closeout.py", "", wrap("rms_error"),
     "shift the fit objective by 1e-4",
     'rms_error(0.53, 12.0, [0.5, 0.6, 0.7], {"0.5": 1.0, "0.6": 1.1, "0.7": 1.2})',
     "refused", "instrument"),
    ("p16_gate.py", "p14_ratelaw.py", "", wrap("level"),
     "shift the band level lo(J) by 1e-4", "level(40)", "refused", "instrument"),
    ("p17_gate.py", "p17_twolayer.py", "", wrap("level"),
     "shift the band level lo(J) by 1e-4", "level(40)", "refused", "instrument"),
    ("p18_gate.py", "p18_stagger.py", "", wrap("level"),
     "shift the band level lo(J) by 1e-4", "level(40)", "refused", "instrument"),

    # ---- structural mutations: the defect classes this repo actually hit (off-by-one lattice index,
    #      k-dependency exponent mis-carried), not a magnitude error
    ("p13_gate.py", "p13_closeout.py", "    return int(idx) if bool(sf[idx] <= alpha) else -1",
     "    return int(idx) + 1 if bool(sf[idx] <= alpha) else -1",
     "lattice off-by-one in the minimal tail index m_ge", "m_ge(3.0)", "refused", "instrument"),
    ("p14_gate.py", "p14_ratelaw.py", "dtype=float) * f ** (k - 1)",
     "dtype=float) * f ** k",
     "mis-carry the k-dependency exponent in the silent-side weight",
     'beta_star("logistic", 3, level(40), N_COARSE)', "refused", "instrument"),
    ("p16_gate.py", "p14_ratelaw.py", "dtype=float) * f ** (k - 1)",
     "dtype=float) * f ** k",
     "mis-carry the k-dependency exponent in the silent-side weight",
     'beta_star("logistic", 3, level(40), N_COARSE)', "refused", "instrument"),
]


def probe_value(workdir, module, expr):
    src = ("import " + module[:-3] + " as m\n"
           "print(repr(eval(" + repr(expr) + ", m.__dict__)))\n")
    try:
        r = subprocess.run([sys.executable, "-c", src], cwd=workdir,
                           capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    out = r.stdout.strip().splitlines()
    return out[-1] if r.returncode == 0 and out else "ERROR:" + r.stderr.strip()[-120:]


def apply_mutation(work, module, find, replace):
    src = work / module
    text = src.read_text(encoding="utf-8")
    if find:
        n = text.count(find)
        if n != 1:
            return "anchor found " + str(n) + " times in " + module + ", expected exactly 1"
        src.write_text(text.replace(find, replace, 1), encoding="utf-8")
    else:
        src.write_text(text + replace, encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", "import " + module[:-3]], cwd=str(work),
                       capture_output=True, text=True, timeout=TIMEOUT)
    return None if r.returncode == 0 else "mutated module does not import: " + r.stderr.strip()[-160:]


def run_gate(work, gate):
    r = subprocess.run([sys.executable, str(work / gate)], cwd=str(work),
                       capture_output=True, text=True, timeout=TIMEOUT)
    return r.returncode, re.findall(r"^FAIL\s+(\S+)", r.stdout, re.M), r.stderr.strip()[-160:]


def classify(fails):
    """A LEXICAL heuristic over check names, not a derivation: it asks whether the refusing check's
    name says it compares against a record (committed artifact, hand value, closed form). Which code
    paths a check actually shares with the mutated function is not derivable from a name, so this
    column must be read as "the check claims an independent referent", never as "the check is
    independent". The X-76 case (a two-path check that stayed silent because both paths sat
    downstream of the mutated helper) is exactly what this heuristic cannot see."""
    if not fails:
        return "none"
    hit = [f for f in fails if any(w in f.lower() for w in ANCHOR_WORDS)]
    if len(hit) == len(fails):
        return "names-say-record"
    if not hit:
        return "names-say-no-record"
    return "mixed"


def main() -> int:
    checks = ok = 0
    per_gate = {}

    def report(name, passed, detail=""):
        nonlocal checks, ok
        checks += 1
        ok += int(passed)
        print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))

    for gate, module, find, replace, what, probe, expect, side in TARGETS:
        stem = gate.split("_")[0] + "/" + ("inline" if find else module.split("_")[-1][:-3])
        tmp = tempfile.mkdtemp(prefix="gate_audit_")
        try:
            work = pathlib.Path(tmp) / "experiments"
            shutil.copytree(EXP, work)
            err = apply_mutation(work, module, find, replace)
            if err:
                report("MUT_" + stem, False, err)
                continue
            clean, mut = probe_value(str(EXP), module, probe), probe_value(str(work), module, probe)
            if mut.startswith(("ERROR", "TIMEOUT")):
                report("MUT_" + stem, False, "probe failed on mutated module: " + mut)
                continue
            if clean == mut:
                report("MUT_" + stem, False,
                       "mutation is a NO-OP on the probe (" + probe + " = " + clean
                       + " both ways): nothing was injected, so the gate's answer is void")
                continue
            rc, fails, errtxt = run_gate(work, gate)
            verdict = ("refused" if (rc != 0 and fails)
                       else "crashed" if rc != 0 else "blind")
            per_gate.setdefault(gate, []).append((what, verdict, side))
            good = (verdict == expect)
            report("MUT_" + stem + "_is_" + expect, good,
                   what[:58] + " [" + side + "]: probe " + clean + " -> " + mut + "; " + verdict
                   + (" (exit " + str(rc) + ", stderr " + errtxt + ")" if verdict == "crashed" else "")
                   + "; checks that fired: " + (", ".join(fails) + " [" + classify(fails) + "]"
                                               if fails else "none"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # every gate under audit must refuse at least one INSTRUMENT-side mutation. Claim-side mutations
    # are excluded from this rule by R2 - a gate that refuses them is testing the science, and the
    # guard for a changed claim is the committed reading's hash binding, not a gate.
    print("")
    for gate in sorted({t[0] for t in TARGETS}):
        got = per_gate.get(gate, [])
        instr = [w for w, v, s in got if s == "instrument"]
        refused = [w for w, v, s in got if v == "refused"]
        blind_instr = [w for w, v, s in got if v == "blind" and s == "instrument"]
        refused_claim = [w for w, v, s in got if v == "refused" and s == "claim"]
        report("GATE_" + gate.split("_")[0] + "_refuses_an_instrument_mutation",
               any(w in refused for w in instr),
               f"{len(got)} mutations injected ({len(instr)} instrument-side); refused "
               + str(len(refused)) + (", blind on instrument-side: " + "; ".join(blind_instr)
                                      if blind_instr else ", no instrument-side blindness")
               + (", refuses a CLAIM-side mutation (R2 candidate): " + "; ".join(refused_claim)
                  if refused_claim else ""))

    print(f"\n{ok}/{checks} checks passed")
    return 0 if ok == checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
