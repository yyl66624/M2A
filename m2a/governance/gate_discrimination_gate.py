"""Suite: do the repo's gates refuse a wrong mechanism, or only certify themselves?

Motivation. AO §4-P6 shipped as a check that could not fail: mutating `silence()` into the reading
the protocol forbids still passed, because the two definitions coincide on every normalised measure.
That is the X-29 / R7 family (report the smallest difference an instrument can distinguish), in a new
form - not a loose tolerance but a criterion with no falsifying input.

So this suite mutates each mechanism under its own gate and requires the gate to refuse. Everything
runs on a throwaway copy in a temp directory; the repository is never modified, and no experiment is
run (this inspects instruments, per R2).

Outcomes per target, kept deliberately separate:
  * refused        - the gate exited non-zero AND printed at least one FAIL line;
  * blind          - the gate stayed green on a mutation that demonstrably changed a reading;
  * crashed        - non-zero exit with no FAIL line, i.e. the mutation broke the program rather than
    being caught by a criterion. The first pass counted a crash as a refusal; that is a hole in this
    audit's own instrument, closed here (a refusal must name the check that refused).

Two controls run before a verdict is trusted:
  * the mutated module must still import (the R1.1 class);
  * the mutation must change a probe reading. An accepted mutation that does nothing is not evidence
    about the gate - it is evidence about the probe (R8 applied to this suite itself).

SCALE LADDER. A binary refused/blind verdict is not the honest statement, because a gate's registered
tolerance sets what it can see at all: Phase V-d's tolerance is Monte-Carlo sized, so a 1e-4 relative
error in its readout is BELOW its resolution, not beneath its notice. So every wrap-based target is
injected at 1e-9, 1e-6, 1e-4 in ascending order and the suite reports the SMALLEST refused scale - the
gate's discrimination floor, exactly the R7 quantity, measured on the instrument rather than asserted.
A scale whose probe does not move is skipped with disclosure: that is float resolution, not gate
resolution. `blind_all` (no scale refused) is rejected unless it was registered BEFORE the run as
`expect="blind_all"` with a reason - a predicted blindness is a measurement of the gate's floor, an
unpredicted one is a hole in the gate.

Which SIDE of a round a mutation lands on decides what a blind verdict means, and the two must not be
conflated (R2):
  * instrument-side - the mutation corrupts the measuring device (grid, root finder, tail index,
    aggregator, CDF, measurand definition). A gate that stays green at every scale here is not an
    instrument, it is a certificate.
  * claim-side - the mutation changes the quantity the round was built to test (an analytic beta*
    law). The gate need not refuse it, and if it does refuse, that is usually a degenerate-identity
    check (k=1 reduces to a committed law), which is an instrument check, not the gate testing the
    science. Claim-side targets are therefore reported but never gated; their registered guard is the
    committed reading's hash binding.

The fired check NAMES are printed, and each refusal is tagged by whether the names claim a referent
outside the module. That tag is a name heuristic - see `classify` - because code-path sharing is not
derivable from a check's name, and the X-76 case is precisely a two-path check that stayed silent with
both paths downstream of the mutated helper.
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
LADDER = (1e-9, 1e-6, 1e-4)
# the wide ladder is for rounds whose registered tolerances are coarse (a known-answer check at
# 5e-3 absolute, a hand-set 0.05 on beta): their floor is not below 1e-4 by construction, so the
# ladder has to reach 1e-1 before "blind" can mean anything.
LADDER_WIDE = (1e-9, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1)

ANCHOR_WORDS = ("anchor", "committed", "reproduces", "hand", "unchanged", "identical", "vs_")


def wrap(fn: str, rel: float) -> str:
    """Code appended to a module to redefine `fn` with a relative shift of every finite numeric
    return - scalars AND arrays, because the same mechanism function is called with a theta grid in
    most instruments. The first version of this helper caught only `TypeError` from `math.isfinite`,
    which silently left every array-valued call unshifted and made Phase IV's CDF look unmeasured;
    numpy handles both, and non-numeric returns still pass through untouched (None, dicts, strings).
    +-inf stays inf, so the mutation is a wrong reading, not a wrong program."""
    return ("\n_o = " + fn + "\ndef " + fn + "(*a, **k):\n"
            "    import numpy as _np\n    v = _o(*a, **k)\n    try:\n"
            "        return v * (1.0 + " + repr(rel) + ") if bool(_np.all(_np.isfinite(v))) else v\n"
            "    except (TypeError, ValueError):\n        return v\n")


def legacy(gate, module, find, replace, what, probe):
    """The five §39 first-pass targets, snippet kept byte-identical, single scale."""
    return dict(gate=gate, module=module, find=find, replace=replace, what=what, probe=probe,
                side="instrument", expect="refused", fn=None, scales=None)


# ------------------------------------------------------------------ the target list
TARGETS = [
    legacy("p19_gate.py", "p19_timesym.py", "",
           '\n_o = recurrence\ndef recurrence(n, c=1.0):\n    r = dict(_o(n, c))'
           '\n    r["M3"] = r["M3"] + 1e-8\n    return r\n',
           "shift M3's recurrence by 1e-8 (abs)", 'recurrence(6)["M3"]'),
    legacy("p20_gate.py", "p20_filter.py", "",
           "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
           "shift the closed-form reading by 1e-8 (abs)", 'reading("M3", 7, 1.3, True)'),
    legacy("p21_gate.py", "p21_integral.py", "",
           "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
           "shift the closed-form reading by 1e-8 (abs)", 'reading("M5", 9, 0.7, True)'),
    legacy("p22_gate.py", "p22_powerlaw.py", "",
           "\n_o = reading\ndef reading(*a, **k):\n    return _o(*a, **k) + 1e-8\n",
           "shift the closed-form reading by 1e-8 (abs)", 'reading(CLASSES[0], 9, 1.0, True)'),
    legacy("ao_preflight_gate.py", "ao_opp.py",
           '    return mu.get(NONE, 0.0)',
           '    return 1.0 - sum(v for k, v in mu.items() if k != NONE)',
           "replace Z with the forbidden complement definition",
           'silence({"a1": 0.5, "a2": 0.2, NONE: 0.3})'),
]


def add(gate, module, fn, what, probe, side="instrument", expect="floor", scales=LADDER):
    TARGETS.append(dict(gate=gate, module=module, find="", replace=None, what=what, probe=probe,
                        side=side, expect=expect, fn=fn, scales=scales))


def add_inline(gate, module, find, replace, what, probe, side="instrument", expect="refused"):
    TARGETS.append(dict(gate=gate, module=module, find=find, replace=replace, what=what, probe=probe,
                        side=side, expect=expect, fn=None, scales=None))


# ---- Phase II-VIII: the oldest rounds, read through `from X import f`, which still binds the
#      redefined name (module execution finishes before the import statement returns)
add("phase2_gate.py", "m2a_mechanisms.py", "p_action",
    "shift the binary choice rule", 'p_action("and", 0.8, 0.8)')
add("p3_gate.py", "p3_mechanisms.py", "p_and",
    "shift the AND-gate probability", "p_and(0.8, 0.8, 6.0, 0.5)")
add("p4_gate.py", "p4_mechanisms.py", "cdf",
    "shift every channel CDF", 'cdf(0.5, "logistic")', scales=LADDER_WIDE)
add("p4_gate.py", "p4_mechanisms.py", "quantile",
    "shift every channel quantile", 'quantile(0.95, "logistic")', scales=LADDER_WIDE)
add("p5_gate.py", "p5_mechanisms.py", "tnorm",
    "shift every t-norm chain value", 'tnorm("godel", [0.5, 0.6])')
add("p5b_gate.py", "p5_mechanisms.py", "gap_for",
    "shift the chain gap that sets the drive window", 'gap_for("godel", 3, "all_weak", 0.7)',
    expect="blind_all")   # the gate imports gap_for and never calls it: nothing measures the gap
add("p5c_gate.py", "p5c_arms.py", "dp_c",
    "shift the deterministic-programming readout", 'dp_c(0.4, "sarsa_c")')
add("p5d_gate.py", "p5d_confirm.py", "dp_d",
    "shift the out-of-sample DP readout", "dp_d(0.4)", scales=LADDER_WIDE)
add("p6_gate.py", "p6_systems.py", "poisson_sf",
    "shift the Poisson survival function", "poisson_sf(5, 3.0)")
add("p7_gate.py", "p4_mechanisms.py", "cdf",
    "shift the CDF the S4 silent side integrates over", 'cdf(0.5, "probit")', scales=LADDER_WIDE)
# J5 is the only check that reads rho_exact, and it reads it as `a1 == a2` on the same call twice:
# a self-comparison, so no value of the mechanism - not even a 10% error - can falsify it.
add("p8_gate.py", "p8_smooth.py", "rho_exact",
    "shift the exact-curve rho (its only check is a determinism self-comparison)",
    "rho_exact(0.75)", scales=LADDER_WIDE, expect="blind_all")
add("p8_gate.py", "p8_smooth.py", "rho_smooth",
    "shift the smoothed threshold curve", "rho_smooth(0.75)")
add("p7_gate.py", "p7_systems.py", "predicted_beta",
    "shift the analytic beta* law of Phase VII", 'predicted_beta("logistic", 2, 0.5)',
    side="claim", expect="report")

# ---- Phases IX-XVIII: one reading shift per module-backed gate
add("p9_gate.py", "p9_aggregation.py", "agg_value",
    "shift every t-norm aggregation", 'agg_value("lukasiewicz", [0.3, 1.0])')
add("p10_gate.py", "p10_exponent.py", "root_R",
    "shift the onset root of the cubic", "root_R(0.85, 3.7, 61.0)")
add("p11_gate.py", "p11_softband.py", "L_tau",
    "shift every reachable band level", 'L_tau("lukasiewicz", 2, 0.3)')
add("p11_gate.py", "p11_softband.py", "predicted",
    "shift the analytic beta* law of Phase XI", 'predicted("logistic", 2, 0.5)',
    side="claim", expect="report")
add("p12_gate.py", "p12_lattice.py", "rho_smooth",
    "shift the smoothed lattice reading R^2", "rho_smooth(1.137, 0.75)")
add("p13_gate.py", "p13_closeout.py", "q_cont",
    "shift the continuous Poisson quantile", "q_cont(3.0)",
    expect="blind_all")   # W2's registered tolerance is ONE COUNT; even 1e-4 x 5.67 = 6e-4 counts
add("p14_gate.py", "p14_ratelaw.py", "level",
    "shift the band level lo(J)", "level(40)")
add("p15_gate.py", "p13_closeout.py", "rms_error",
    "shift the fit objective",
    'rms_error(0.53, 12.0, [0.5, 0.6, 0.7], {"0.5": 1.0, "0.6": 1.1, "0.7": 1.2})',
    scales=(1e-4,))   # runtime: this gate takes ~51 s per run
add("p16_gate.py", "p14_ratelaw.py", "level",
    "shift the band level lo(J)", "level(40)")
add("p17_gate.py", "p17_twolayer.py", "level",
    "shift the band level lo(J)", "level(40)", scales=(1e-4,))   # ~30 s per run
add("p18_gate.py", "p18_stagger.py", "level",
    "shift the band level lo(J)", "level(40)", scales=(1e-4,))   # ~152 s per run

# ---- structural mutations: the defect classes this repo actually hit, not a magnitude error
add_inline("p13_gate.py", "p13_closeout.py",
           "    return int(idx) if bool(sf[idx] <= alpha) else -1",
           "    return int(idx) + 1 if bool(sf[idx] <= alpha) else -1",
           "lattice off-by-one in the minimal tail index m_ge", "m_ge(3.0)")
add_inline("p5b_gate.py", "p5b_instrument.py",
           "    n = int(math.ceil(span / dtheta)) + 1",
           "    n = int(math.ceil(span / dtheta))",
           "grid node count off by one (endpoint-inclusive +1 dropped)", "grid_spec(0.0625)[1]")
add_inline("p14_gate.py", "p14_ratelaw.py", "dtype=float) * f ** (k - 1)",
           "dtype=float) * f ** k",
           "mis-carry the k-dependency exponent in the silent-side weight",
           'beta_star("logistic", 3, level(40), N_COARSE)')
add_inline("p16_gate.py", "p14_ratelaw.py", "dtype=float) * f ** (k - 1)",
           "dtype=float) * f ** k",
           "mis-carry the k-dependency exponent in the silent-side weight",
           'beta_star("logistic", 3, level(40), N_COARSE)')


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
    return r.returncode, re.findall(r"^FAIL\s+(\S+)", r.stdout, re.M), r.stderr.strip()[-140:]


def classify(fails):
    """A LEXICAL heuristic over check names, not a derivation: it asks whether the refusing check
    claims a referent outside the mutated module. Code-path sharing is not derivable from a name, so
    read this as "the check claims an independent referent", never as "the check is independent"."""
    if not fails:
        return "none"
    hit = [f for f in fails if any(w in f.lower() for w in ANCHOR_WORDS)]
    if len(hit) == len(fails):
        return "names-say-record"
    if not hit:
        return "names-say-no-record"
    return "mixed"


def run_target(t, scale):
    """Inject at `scale` (None = the target's own literal snippet) and return a verdict dict."""
    tmp = tempfile.mkdtemp(prefix="gate_audit_")
    try:
        work = pathlib.Path(tmp) / "experiments"
        shutil.copytree(EXP, work)
        replace = wrap(t["fn"], scale) if scale is not None else t["replace"]
        err = apply_mutation(work, t["module"], t["find"], replace)
        if err:
            return {"status": "broken", "detail": err}
        clean = probe_value(str(EXP), t["module"], t["probe"])
        mut = probe_value(str(work), t["module"], t["probe"])
        if mut.startswith(("ERROR", "TIMEOUT")):
            return {"status": "broken", "detail": "probe failed on mutated module: " + mut}
        if clean == mut:
            return {"status": "no-op", "detail": "probe " + t["probe"] + " = " + clean}
        rc, fails, errtxt = run_gate(work, t["gate"])
        verdict = ("refused" if (rc != 0 and fails)
                   else "crashed" if rc != 0 else "blind")
        return {"status": verdict, "scale": scale, "clean": clean, "mut": mut,
                "fails": fails, "detail": errtxt if verdict == "crashed" else ""}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    results = []
    per_gate = {}

    def report(name, passed, detail=""):
        """The tally is DERIVED from the recorded verdicts, not accumulated in a counter: an
        accumulated counter can be clobbered by any local variable of the same name (one was, in the
        gate-level rule, and it printed 56 PASS lines under a `2/58` total)."""
        results.append((name, bool(passed)))
        print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))

    for t in TARGETS:
        stem = t["gate"].split("_")[0] + "/" + (t["module"].split("_")[-1][:-3] if t["fn"] else "inline")
        if t["scales"] is None:
            runs = [run_target(t, None)]
        else:
            runs = []
            for scale in t["scales"]:
                r = run_target(t, scale)
                if r["status"] == "no-op":
                    r["note"] = "scale " + repr(scale) + " below float resolution for this probe: skipped"
                runs.append(r)
                if r["status"] == "refused" or r["status"] == "broken":
                    break
        refused = [r for r in runs if r["status"] == "refused"]
        broken = [r for r in runs if r["status"] == "broken"]
        floor = refused[0]["scale"] if refused and refused[0].get("scale") is not None else None
        verdict = ("broken" if broken and not refused
                   else ("refused" if refused and t["scales"] is None
                         else "floor@" + str(floor) if refused else "blind_all"))
        per_gate.setdefault(t["gate"], []).append((t["side"], verdict, t["what"], t["expect"]))
        skipped = [r["note"] for r in runs if "note" in r]

        if t["expect"] == "report":
            report("MUT_" + stem + "_reported", True,
                   t["what"] + " [" + t["side"] + "]: " + verdict + " - claim side, never gated here; "
                   + ("its guard is the committed reading's hash binding"
                      if verdict == "blind_all" else "refused by a degenerate-identity check"))
            continue
        if t["expect"] == "floor":
            good, why = (verdict.startswith("floor@"), "expected to refuse at some ladder scale")
        else:
            good, why = (verdict == t["expect"], "expected " + t["expect"])
        if broken:
            good, why = False, broken[0]["detail"]
        report("MUT_" + stem + "_" + t["expect"], good,
               t["what"] + " [" + t["side"] + "]: " + verdict
               + ("" if refused else "; " + why)
               + "; probe " + (refused[0]["clean"] + " -> " + refused[0]["mut"] if refused
                               else (runs[-1].get("clean", "?") + " -> " + runs[-1].get("mut", "?")))
               + "; scales run " + str(len(runs))
               + ("; " + "; ".join(skipped) if skipped else "")
               + "; checks that fired: " + (", ".join(refused[0]["fails"])
                                            + " [" + classify(refused[0]["fails"]) + "]"
                                            if refused else "none"))

    print("")
    for gate in sorted({t["gate"] for t in TARGETS}):
        got = per_gate.get(gate, [])
        instr = [(v, w, e) for s, v, w, e in got if s == "instrument"]
        refused = [v for v, _, _ in instr if v.startswith("floor@") or v == "refused"]
        blind = [(w, e) for v, w, e in instr if v not in ("refused",) and not v.startswith("floor@")]
        registered = [w for w, e in blind if e == "blind_all"]
        unexpected = [w for w, e in blind if e != "blind_all"]
        # a gate is an instrument if it refuses something it can see, or if its inability to see
        # anything was predicted, registered and explained BEFORE the run (expect="blind_all").
        gate_ok = bool(refused) or (bool(instr) and bool(registered) and not unexpected)
        report("GATE_" + gate.split("_")[0] + "_refuses_or_registers_instrument_blindness", gate_ok,
               f"{len(got)} mutations injected ({len(instr)} instrument-side); "
               + ("floor(s) " + ", ".join(refused) if refused
                  else "registered blind at every injected scale: " + "; ".join(registered))
               + ("" if not unexpected else "; UNEXPECTED blindness: " + "; ".join(unexpected)))

    n_gates = len({t["gate"] for t in TARGETS})
    report("SUITE_accounting", len(results) == len(TARGETS) + n_gates,
           f"{len(results)} verdicts recorded, {len(TARGETS) + n_gates} expected "
           f"({len(TARGETS)} targets + {n_gates} gate rules)")

    # the distribution is printed by the suite so that any report quoting it quotes a derived line
    # rather than a hand-typed count (the X-74 class of defect).
    dist = {}
    for rows in per_gate.values():
        for _, v, _, _ in rows:
            dist[v] = dist.get(v, 0) + 1
    print("\nverdict distribution: " + ", ".join(f"{k}={v}" for k, v in sorted(dist.items()))
          + f" over {sum(dist.values())} targets")

    checks, ok = len(results), sum(1 for _, p in results if p)
    print(f"\n{ok}/{checks} checks passed")
    return 0 if ok == checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
