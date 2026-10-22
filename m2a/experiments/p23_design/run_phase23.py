"""Run Phase XXIII (AO measurement) when the owner approves it.

Formal mode refuses unless --approved-by-owner is passed; before that it only offers --smoke, which
validates the sampling pipeline and never writes a result artifact. The gate must pass first.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import statistics
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import ao_opp as ao
import p23_mechanisms as P

REPO = HERE.parents[2]
PREREG = HERE / "PHASE23_PREREGISTRATION.md"
PREREG_REL = "m2a/experiments/p23_design/PHASE23_PREREGISTRATION.md"
CODE_RELS = [PREREG_REL, "m2a/experiments/p23_design/p23_mechanisms.py",
             "m2a/experiments/p23_design/p23_gate.py",
             "m2a/experiments/p23_design/run_phase23.py"]
OUT_JSON = HERE / "phase23_results.json"
OUT_MD = HERE / "PHASE23_RESULTS.md"
T975_9 = 2.2621571627409915


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)


def git_raw(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True)


def bind():
    disk = sha(PREREG.read_bytes())
    g = git_raw("show", "HEAD:" + PREREG_REL)
    if g.returncode != 0:
        print("REFUSING: prereg is not committed at HEAD", file=sys.stderr)
        return None
    if disk != sha(g.stdout):
        print("REFUSING: prereg bytes differ from HEAD", file=sys.stderr)
        return None
    dirty = git("status", "--porcelain", "--", *CODE_RELS).stdout.strip()
    if dirty:
        print("REFUSING: code files are not clean:\n" + dirty, file=sys.stderr)
        return None
    return {"prereg_sha256": disk, "git_sha256": sha(g.stdout),
            "commit": git("rev-parse", "HEAD").stdout.strip()}


def gate_ok():
    p = subprocess.run([sys.executable, str(HERE / "p23_gate.py")], cwd=HERE,
                       capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print("REFUSING TO RUN: gate failed", file=sys.stderr)
        return False
    return True


def collect(n, seeds):
    out = {}
    for name in P.MULTI + P.SINGLE:
        model = ao.MULTI[name] if name in ao.MULTI else ao.ONE_CATEGORY[name]
        mu = model.mu(P.THETA_STAR)
        vals = [P.sample_gap(mu, n, s) for s in seeds]
        out[name] = {"exact_mu": mu, "samples": vals}
    return out


def summarize(collected, seeds):
    rows = {}
    for name, rec in collected.items():
        gs = [v[0] for v in rec["samples"]]
        old = [v[3] for v in rec["samples"]]
        mean = float(statistics.fmean(gs))
        sd = float(statistics.stdev(gs)) if len(gs) > 1 else 0.0
        se = sd / math.sqrt(len(gs))
        ci = [mean - T975_9 * se, mean + T975_9 * se] if se > 0 else [mean, mean]
        rows[name] = {"n": len(gs), "seeds": list(seeds), "mean": mean, "sd": sd, "se": se,
                      "ci95": ci, "old_mean": float(statistics.fmean(old)),
                      "values": [float(x) for x in gs]}
    return rows


def main() -> int:
    argv = sys.argv[1:]
    smoke = None
    if "--smoke" in argv:
        smoke = int(argv[argv.index("--smoke") + 1])
    if not gate_ok():
        return 1
    if smoke is not None:
        cols = collect(smoke, P.SEEDS[:2])
        rows = summarize(cols, P.SEEDS[:2])
        for name, r in rows.items():
            exact = P.exact_gap(ao.MULTI[name] if name in ao.MULTI else ao.ONE_CATEGORY[name],
                                P.THETA_STAR)[0]
            print("SMOKE %-14s exact %.6f mean %.6f n=%d (pipeline only; not a reading)"
                  % (name, exact, r["mean"], smoke))
        return 0
    if "--approved-by-owner" not in argv:
        print("REFUSING: the AO protocol requires explicit owner approval for the formal run")
        return 1
    binding = bind()
    if binding is None:
        return 1
    t0 = time.time()
    seeds = P.SEEDS
    cols = collect(P.N_SAMPLES, seeds)
    rows = summarize(cols, seeds)

    exact, tols = {}, {}
    for name in P.MULTI:
        exact[name] = P.exact_gap(ao.MULTI[name], P.THETA_STAR)[0]
        tols[name] = P.grid_tol(ao.MULTI[name], P.THETA_STAR)[0]
    single = {n: P.exact_gap(ao.ONE_CATEGORY[n], P.THETA_STAR)[0] for n in P.SINGLE}

    exact_ok = all(exact[n] > 3 * tols[n] for n in P.MULTI) \
        and all(abs(v) <= P.MEASURE_TOL for v in single.values())
    c3 = {}
    for name in P.MULTI:
        r = rows[name]
        c3[name] = {"tol": tols[name], "abs_err": abs(r["mean"] - exact[name]),
                    "ci_low": r["ci95"][0], "ok": (r["ci95"][0] > 0
                                                   and abs(r["mean"] - exact[name]) <= tols[name])}
    single_ok = all(abs(rows[n]["mean"]) <= P.MEASURE_TOL for n in P.SINGLE)
    resolution_ok = all(c3[n]["ok"] for n in P.MULTI) and single_ok
    old_separates = any(abs(rows[n]["old_mean"]) > tols[n] for n in P.MULTI)

    metrics = {"exact_ok": exact_ok, "resolution_ok": resolution_ok,
               "old_separates": old_separates,
               "clean": exact_ok and resolution_ok and not old_separates}
    exit_label = P.classify(metrics)
    label = {"AO-COLLAPSES": "CONTRADICTED", "SAMPLING-UNDERPOWERED": "INDETERMINATE",
             "OLD-COMPLEMENT-ALSO-SEPARATES": "NULL", "AO-SEPARATES": "SUPPORTED",
             "O-NONE": "NOT_IDENTIFIED"}[exit_label]

    payload = {"schema": "m2a.phase23.results.v1", "round": "Phase XXIII / P23-AO",
               "prereg_sha256": binding["prereg_sha256"],
               "prereg_binding": {"disk_sha256": binding["prereg_sha256"],
                                  "git_sha256": binding["git_sha256"],
                                  "git_ref": "HEAD:" + PREREG_REL, "commit": binding["commit"]},
               "commit": binding["commit"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "theta_star": P.THETA_STAR, "n_samples": P.N_SAMPLES, "seeds": list(seeds),
               "rows": rows, "exact": {"multi": exact, "single": single, "grid_tol": tols},
               "checks": {"C1_C2_exact_and_grid": exact_ok, "C3_sampling": resolution_ok,
                          "C4_old_complement": not old_separates, "c3": c3},
               "metrics": metrics, "exit": exit_label, "label_r17": label,
               "elapsed_sec": time.time() - t0}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lines = ["# Phase XXIII 结果：AO 测度把发放与静默分开", "",
             "> 预注册 `PHASE23_PREREGISTRATION.md`（sha256 `%s`）｜commit `%s`｜gate 15/15"
             % (binding["prereg_sha256"], binding["commit"]), "",
             "| 模型 | 精确 G | 网格容差 | 采样均值 | 95% CI |", "| --- | --- | --- | --- | --- |"]
    for n in P.MULTI + P.SINGLE:
        r = rows[n]
        lines.append("| `%s` | %s | %s | %s | [%s, %s] |"
                     % (n, ("%.6f" % exact[n]) if n in exact else ("%.3e" % single[n]),
                        ("%.3e" % tols[n]) if n in tols else "—",
                        "%.6f" % r["mean"], "%.6f" % r["ci95"][0], "%.6f" % r["ci95"][1]))
    lines += ["", "## 判据", "",
              "- C1/C2 精确分离与网格稳定：**%s**；C3 采样恢复：**%s**；C4 旧补集退化：**%s**。"
              % ("过" if exact_ok else "不过", "过" if resolution_ok else "不过",
                 "过" if not old_separates else "不过"), "",
              "## 出口", "",
              "**`%s`** ⇒ R17 五值标签 **`%s`**。" % (exit_label, label), "",
              "## 边界", "",
              "只覆盖四个固定模型、θ*=0.1、G 的定义与这组种子；不声明真实主体或其它层级系统；"
              "全为 `SIMULATION_RESULT`。", "",
              "## 复现", "", "```bash", "cd m2a/experiments/p23_design",
              "python3 p23_gate.py          # 15/15",
              "python3 run_phase23.py --approved-by-owner", "```", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("exit %s | label %s | elapsed %.1fs" % (exit_label, label, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
