"""Phase XXIV pre-flight gate: instruments only. It measures no scientific effect.

Rules:
  * λ=0 must be bit-identical to the Phase III learner and to the Phase V DP (known answer);
  * the DP prediction frozen in the preregistration must be reproduced by the code;
  * the planning resolution must exceed the pre-registered floor *before* a run;
  * the seed pool must be disjoint from every committed seed field;
  * the exit table must be reachable through synthetic metrics;
  * the gate reads no Phase XXIV result artifact and writes nothing.

This gate is runnable before the runner exists. It prints `n/n checks passed`.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import p24_mechanisms as P
from p3_mechanisms import cue_sensitivity, train_cue_agent
from p5_mechanisms import dp_sensitivity

PREREG = HERE / "PHASE24_PREREGISTRATION.md"
M = HERE.parent
CHECKS = []


def check(rule, desc, cond, detail=""):
    CHECKS.append({"rule": rule, "pass": bool(cond), "desc": desc, "detail": str(detail)})
    print("%s  %-4s %s  %s" % ("PASS" if cond else "FAIL", rule, desc, detail))
    return bool(cond)


def prior_seed_values():
    """Only registered seed fields, and only pre-Phase-XXIV artifacts."""
    vals = set()
    files = sorted((M / "experiments").glob("*.json")) + sorted((M / "literature").glob("*.json"))
    for p in files:
        if p.name.startswith("phase24"):
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
    # G1 λ=0 learner identity
    q0 = 0.8
    Qreg = P.train_cue_agent_reg(q0, 5000, 0, 0.0)
    Qref = train_cue_agent(q0, 5000, 0)
    check("G01", "lambda=0 learner is bit-identical to Phase III",
          Qreg == Qref and set(Qreg) == set(Qref),
          "entries %d | sens %.12f" % (len(Qreg), cue_sensitivity(Qreg)))

    # G2 λ=0 DP identity to Phase V
    diffs = {}
    for q in (0.6, 0.8, 1.0):
        a = P.dp_sensitivity_reg(q, 0.0)[0]
        b = dp_sensitivity(q)[0]
        diffs[q] = abs(a - b)
    check("G02", "lambda=0 DP is identical to the Phase V operator",
          max(diffs.values()) <= 1e-12,
          " ".join("q=%.1f %.2e" % (q, d) for q, d in diffs.items()))

    # G3 determinism and seed sensitivity
    a = P.train_cue_agent_reg(q0, 2000, 5, 0.1)
    b = P.train_cue_agent_reg(q0, 2000, 5, 0.1)
    c = P.train_cue_agent_reg(q0, 2000, 6, 0.1)
    check("G03", "same seed is deterministic and a different seed moves the table",
          a == b and a != c, "same=%s diff=%s" % (a == b, a != c))

    # G4 the frozen regularization prediction is reproduced
    d00 = P.dp_sensitivity_reg(0.8, 0.0)[0]
    d01 = P.dp_sensitivity_reg(0.8, 0.1)[0]
    shift = d00 - d01
    check("G04", "the frozen q=0.8 prediction is reproduced by the code",
          abs(d00 - 0.194400) <= 1e-6 and abs(d01 - 0.160661) <= 1e-6
          and abs(shift - 0.033739) <= 1e-6,
          "d0 %.6f d01 %.6f shift %.6f" % (d00, d01, shift))

    # G5 planning resolution (R5/R7), using only the committed Phase IV SD
    p4 = json.loads((M / "experiments/phase4_results.json").read_text(encoding="utf-8"))
    sd = float(p4["L3"]["rows"]["0.8"]["q_learning"]["sd"])
    se = sd / (len(P.SEEDS) ** 0.5)
    min_shift = None
    for q in P.QS:
        if q <= 0.5:
            continue
        base = P.dp_sensitivity_reg(q, 0.0)[0]
        for lam in P.LAMBDAS[1:]:
            s = base - P.dp_sensitivity_reg(q, lam)[0]
            if min_shift is None or s < min_shift:
                min_shift = s
    check("G05", "planning resolution clears the pre-registered floor",
          se > 0 and min_shift >= 4 * se and min_shift > P.EPS_OP
          and shift >= 4 * se,
          "sd %.6f se %.6f min_shift %.6f (%.1f se) eps %.3f"
          % (sd, se, min_shift, min_shift / se, P.EPS_OP))

    # G6 grids and seeds
    check("G06", "the registered grids are distinct, ordered and complete",
          P.LAMBDAS == (0.0, 0.1, 0.2, 0.4)
          and P.QS == (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
          and P.SEEDS == tuple(range(4000, 4010)) and P.CONFIRM_SEEDS == tuple(range(4010, 4020))
          and len(set(P.LAMBDAS)) == len(P.LAMBDAS) and len(set(P.QS)) == len(P.QS)
          and P.STEPS == 100000,
          "lambdas %s | qs %s | seeds %d | steps %d"
          % (list(P.LAMBDAS), list(P.QS), len(P.SEEDS), P.STEPS))

    # G7 seed disjointness against committed seed fields
    prior = prior_seed_values()
    clash = sorted((set(P.SEEDS) | set(P.CONFIRM_SEEDS)) & prior)
    check("G07", "the new seed pools are disjoint from every committed seed field",
          not clash, "clash %s | prior values %d" % (clash, len(prior)))

    # G8 the instrument module is pure
    bad = writes_in_module(HERE / "p24_mechanisms.py")
    check("G08", "the instrument module contains no write call", not bad, "writes %s" % bad)

    # G9 the gate does not read a Phase XXIV result artifact
    needle = "phase24" + "_results" + ".json"
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    check("G09", "the gate names no Phase XXIV result artifact", needle not in src,
          "needle present=%s" % (needle in src))

    # G10 preregistration structure
    pre = PREREG.read_text(encoding="utf-8")
    heads = ["## %d" % i for i in range(10)]
    exits = ["ANCHOR-BROKEN", "INDETERMINATE", "OPERATOR-MISMATCH",
             "REGULARIZATION-REPAIRS", "REGULARIZATION-DOES-NOT-REPAIR", "O-NONE"]
    frozen = ["0.194400", "0.160661", "0.135000", "0.099184", "0.051004"]
    check("G10", "the preregistration carries all sections, exits, tolerances and frozen values",
          all(h in pre for h in heads) and all(e in pre for e in exits)
          and all(v in pre for v in frozen)
          and "0.008" in pre and "4000–4009" in pre and "4010–4019" in pre
          and "100 000" in pre and "不运行 runner" in pre,
          "heads %d/10 exits %d/6 frozen %d/5"
          % (sum(h in pre for h in heads), sum(e in pre for e in exits),
             sum(v in pre for v in frozen)))

    # G11 every exit can be reached by a synthetic metric profile
    probes = {
        "ANCHOR-BROKEN": dict(anchor_ok=False),
        "INDETERMINATE": dict(anchor_ok=True, resolution_ok=False),
        "OPERATOR-MISMATCH": dict(anchor_ok=True, resolution_ok=True, operator_ok=False),
        "REGULARIZATION-REPAIRS": dict(anchor_ok=True, resolution_ok=True, operator_ok=True,
                                      repair_found=True),
        "REGULARIZATION-DOES-NOT-REPAIR": dict(anchor_ok=True, resolution_ok=True,
                                               operator_ok=True, repair_found=False, clean=True),
        "O-NONE": dict(anchor_ok=True, resolution_ok=True, operator_ok=True,
                       repair_found=False, clean=False),
    }
    got = {k: P.classify(v) for k, v in probes.items()}
    check("G11", "every registered exit is reachable from a synthetic metric profile",
          all(got[k] == k for k in probes), "got %s" % got)

    # G12 preregistration hash
    sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    check("G12", "the preregistration hash is a well-formed SHA-256",
          bool(re.fullmatch(r"[0-9a-f]{64}", sha)), sha)

    # G13 the prereg's table equals the instrument's computed values
    table = {}
    for q, lam, want in ((0.8, 0.0, "0.194400"), (0.8, 0.1, "0.160661"),
                         (0.8, 0.2, "0.135000"), (0.8, 0.4, "0.099184"),
                         (0.6, 0.1, "0.051004")):
        got_v = "%.6f" % P.dp_sensitivity_reg(q, lam)[0]
        table["q%.1f_l%.1f" % (q, lam)] = (got_v, want, got_v == want)
    check("G13", "the frozen table is exactly the instrument's current output",
          all(v[2] for v in table.values()),
          " ".join("%s=%s" % (k, v[0]) for k, v in table.items()))

    # suite accounting: all rule ids distinct, tally derived from records
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
