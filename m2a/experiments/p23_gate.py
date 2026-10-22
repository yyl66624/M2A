"""Phase XXIII pre-flight gate: instruments only. It does not run the formal experiment.

The AO protocol's P1-P6 preflight is already an audited 8/8 suite; this gate re-runs it and adds
the round-specific checks: the exact gap, the three-grid tolerance, the planning SE, seed
disjointness, estimator determinism, exit reachability, and the pre-registration structure.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ao_opp as ao
import p23_mechanisms as P

M = HERE.parent
PREREG = HERE / "PHASE23_PREREGISTRATION.md"
CHECKS = []


def check(rule, desc, cond, detail=""):
    CHECKS.append({"rule": rule, "pass": bool(cond)})
    print("%s  %-4s %s  %s" % ("PASS" if cond else "FAIL", rule, desc, detail))
    return bool(cond)


def prior_seed_values():
    vals = set()
    files = sorted((M / "experiments").glob("*.json")) + sorted((M / "literature").glob("*.json"))
    for p in files:
        if p.name.startswith("phase23"):
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        stack = [doc]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                for k, v in x.items():
                    if k in ("seed", "seeds", "seed_pool"):
                        if isinstance(v, list):
                            vals.update(int(z) for z in v if isinstance(z, (int, float)))
                        elif isinstance(v, (int, float)):
                            vals.add(int(v))
                    else:
                        stack.append(v)
            elif isinstance(x, list):
                stack.extend(x)
    return vals


def writes_in_module(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name) and f.id == "open":
            mode = None
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            if mode is None or any(c in mode for c in "wax+"):
                bad.append("open mode=%r" % mode)
        if isinstance(f, ast.Attribute) and f.attr in (
                "write_text", "write_bytes", "dump", "save", "savez", "savetxt"):
            bad.append(f.attr)
    return bad


def main() -> int:
    pre = PREREG.read_text(encoding="utf-8")
    sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    # G01 the audited AO preflight
    pf = subprocess.run([sys.executable, str(HERE / "ao_preflight_gate.py")], cwd=HERE,
                        capture_output=True, text=True)
    tail = pf.stdout.strip().splitlines()[-1] if pf.stdout.strip() else ""
    check("G01", "the AO P1-P6 preflight still exits 0 at its printed 8/8",
          pf.returncode == 0 and tail == "8/8 checks passed", tail or "no fraction")

    # G02 single-action exact degeneracy
    single = {n: P.exact_gap(ao.ONE_CATEGORY[n], P.THETA_STAR)[0] for n in P.SINGLE}
    check("G02", "the single-action exact gap is zero within the measure tolerance",
          all(abs(v) <= P.MEASURE_TOL for v in single.values()),
          " ".join("%s=%.3e" % (k, v) for k, v in single.items()))

    # G03 exact separation plus the 3-tol margin
    exact, tols = {}, {}
    for n in P.MULTI:
        g, _ = P.exact_gap(ao.MULTI[n], P.THETA_STAR)
        t, _ = P.grid_tol(ao.MULTI[n], P.THETA_STAR)
        exact[n], tols[n] = g, t
    check("G03", "both multi-action fixtures separate by more than three grid tolerances",
          all(exact[n] > 3 * tols[n] for n in P.MULTI),
          " ".join("%s G=%.6f tol=%.3e" % (n, exact[n], tols[n]) for n in P.MULTI))

    # G04 the frozen tolerance values are reproduced
    check("G04", "the prereg's two tolerance values are the instrument's current values",
          abs(tols["two_windows"] - 4.136e-04) <= 1e-6
          and abs(tols["adjacent"] - 8.785e-04) <= 1e-6,
          "two_windows=%.3e adjacent=%.3e" % (tols["two_windows"], tols["adjacent"]))

    # G05 planning SE against tol/4 (R5/R7)
    se = {n: P.plan_se(exact[n]) / (len(P.SEEDS) ** 0.5) for n in P.MULTI}
    ratios = {n: (tols[n] / 4.0) / se[n] for n in P.MULTI}
    check("G05", "the registered N makes the seed-mean SE smaller than tol/4",
          all(se[n] <= tols[n] / 4.0 for n in P.MULTI),
          " ".join("%s se=%.3e tol/4=%.3e ratio=%.2f"
                  % (n, se[n], tols[n] / 4.0, ratios[n]) for n in P.MULTI))

    # G06 the argmax is stable enough for the SE formula
    margins = {}
    for n in P.MULTI:
        mu = ao.MULTI[n].mu(P.THETA_STAR)
        cats = sorted((v for k, v in mu.items() if k != ao.NONE), reverse=True)
        margins[n] = cats[0] - cats[1]
    check("G06", "the top-two category margin is over 200 seed-mean standard errors",
          all(margins[n] > 200 * se[n] for n in P.MULTI),
          " ".join("%s margin=%.6f" % (n, margins[n]) for n in P.MULTI))

    # G07 estimator determinism and seed sensitivity
    mu0 = ao.MULTI["two_windows"].mu(P.THETA_STAR)
    a = P.sample_gap(mu0, 1000, 5000)
    b = P.sample_gap(mu0, 1000, 5000)
    c = P.sample_gap(mu0, 1000, 5001)
    check("G07", "the multinomial estimator is deterministic per seed and moves with the seed",
          a == b and a != c, "same=%s diff=%s" % (a == b, a != c))

    # G08 seed pools disjoint
    prior = prior_seed_values()
    clash = sorted((set(P.SEEDS) | set(P.CONFIRM_SEEDS)) & prior)
    check("G08", "the new seed pools are disjoint from every committed seed field",
          not clash, "clash %s | prior %d" % (clash, len(prior)))

    # G09 every exit is reachable
    probes = {
        "AO-COLLAPSES": dict(exact_ok=False),
        "SAMPLING-UNDERPOWERED": dict(exact_ok=True, resolution_ok=False),
        "OLD-COMPLEMENT-ALSO-SEPARATES": dict(exact_ok=True, resolution_ok=True,
                                              old_separates=True),
        "AO-SEPARATES": dict(exact_ok=True, resolution_ok=True, old_separates=False, clean=True),
        "O-NONE": dict(exact_ok=True, resolution_ok=True, old_separates=False, clean=False),
    }
    got = {k: P.classify(v) for k, v in probes.items()}
    check("G09", "every registered exit is reachable from a synthetic metric profile",
          all(got[k] == k for k in probes), "got %s" % got)

    # G10 prereg structure and frozen values
    heads = ["## %d" % i for i in range(10)]
    exits = ["AO-COLLAPSES", "SAMPLING-UNDERPOWERED", "OLD-COMPLEMENT-ALSO-SEPARATES",
             "AO-SEPARATES", "O-NONE"]
    frozen = ["0.259165", "0.349254", "4.136e-04", "8.785e-04", "5000–5009", "5010–5019",
              "6 000 000", "不运行 runner", "未获 owner 批准"]
    check("G10", "the prereg carries all sections, exits and frozen values",
          all(h in pre for h in heads) and all(e in pre for e in exits)
          and all(v in pre for v in frozen)
          and all(x in pre for x in ("SUPPORTED", "CONTRADICTED", "INDETERMINATE", "NULL",
                                     "NOT_IDENTIFIED")),
          "heads %d/10 exits %d/5 frozen %d/9"
          % (sum(h in pre for h in heads), sum(e in pre for e in exits),
             sum(v in pre for v in frozen)))

    # G11 no result artifact is named or read
    needle = "phase23" + "_results" + ".json"
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    check("G11", "the gate names no Phase XXIII result artifact", needle not in src,
          "needle present=%s" % (needle in src))

    # G12 the instrument module is pure
    bad = writes_in_module(HERE / "p23_mechanisms.py")
    check("G12", "the instrument module contains no write call", not bad, "writes %s" % bad)

    # G13 the frozen exact values are the instrument's current values
    check("G13", "the prereg's exact gaps are the instrument's current values",
          abs(exact["two_windows"] - 0.259165) <= 1e-6
          and abs(exact["adjacent"] - 0.349254) <= 1e-6,
          "two_windows=%.6f adjacent=%.6f" % (exact["two_windows"], exact["adjacent"]))

    ids = [c["rule"] for c in CHECKS]
    check("SUITE_accounting", "every declared rule id was recorded exactly once",
          len(ids) == len(set(ids)) == 13, "ids %d" % len(ids))
    passed = sum(1 for c in CHECKS if c["pass"])
    check("SUITE_tally", "the printed fraction is derived from the recorded verdicts",
          passed == len(CHECKS), "recorded %d passed %d" % (len(CHECKS), passed))

    print("prereg_sha256 %s" % sha)
    total = len(CHECKS)
    ok = sum(1 for c in CHECKS if c["pass"])
    print("\n%d/%d checks passed" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
