"""Run Phase XXIV: weight-decayed L3 learner vs the regularized visit-weighted operator.

Refuses to run unless:
  * the pre-registration at HEAD is byte-identical to the working tree;
  * the code files themselves are committed and clean;
  * p24_gate.py passes (instrument identity, resolution, seed disjointness, purity).

Writes phase24_results.json and PHASE24_RESULTS.md from the computed rows; no hand-typed readings.
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
REPO = HERE.parents[1]
PREREG_REL = "m2a/experiments/PHASE24_PREREGISTRATION.md"
PREREG = HERE / "PHASE24_PREREGISTRATION.md"
CODE_RELS = ["m2a/experiments/PHASE24_PREREGISTRATION.md", "m2a/experiments/p24_mechanisms.py",
             "m2a/experiments/p24_gate.py", "m2a/experiments/run_phase24.py"]
OUT_JSON = HERE / "phase24_results.json"
OUT_MD = HERE / "PHASE24_RESULTS.md"
T975_9 = 2.2621571627409915

sys.path.insert(0, str(HERE))
import p24_mechanisms as P


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def git_raw(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True)


def bind() -> dict | None:
    disk = sha256(PREREG.read_bytes())
    g = git_raw("show", "HEAD:" + PREREG_REL)
    if g.returncode != 0:
        print("REFUSING: prereg is not committed at HEAD\n" + g.stderr.decode("utf-8", "replace"),
              file=sys.stderr)
        return None
    gitsha = sha256(g.stdout)
    if disk != gitsha:
        print("REFUSING: prereg bytes differ from HEAD (%s vs %s)" % (disk[:12], gitsha[:12]),
              file=sys.stderr)
        return None
    dirty = git("status", "--porcelain", "--", *CODE_RELS).stdout.strip()
    if dirty:
        print("REFUSING: code files are not clean:\n" + dirty, file=sys.stderr)
        return None
    commit = git("rev-parse", "HEAD").stdout.strip()
    return {"prereg_sha256": disk, "disk_sha256": disk, "git_sha256": gitsha,
            "git_ref": "HEAD:" + PREREG_REL, "commit": commit}


def run_gate() -> bool:
    p = subprocess.run([sys.executable, str(HERE / "p24_gate.py")], cwd=HERE,
                       capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print("REFUSING TO RUN: gate failed", file=sys.stderr)
        print(p.stderr[-500:], file=sys.stderr)
        return False
    return True


def main() -> int:
    binding = bind()
    if binding is None:
        return 1
    if not run_gate():
        return 1

    t0 = time.time()
    rows = {}
    complete = True
    for q in P.QS:
        qrow = {}
        for lam in P.LAMBDAS:
            vals = [P.sensitivity_reg(q, P.STEPS, s, lam) for s in P.SEEDS]
            dp = P.dp_sensitivity_reg(q, lam)[0]
            mean = float(statistics.fmean(vals))
            sd = float(statistics.stdev(vals))
            qrow[str(lam)] = {
                "seeds": list(P.SEEDS), "values": [float(x) for x in vals],
                "mean": mean, "sd": sd, "se": sd / math.sqrt(len(vals)),
                "dp": float(dp), "c1_diff": abs(mean - dp),
                "c1_ok": abs(mean - dp) <= P.EPS_OP,
                "old_law": P.old_law(q), "old_dev": P.old_deviation(mean, q),
            }
            complete = complete and len(vals) == len(P.SEEDS) and all(math.isfinite(x) for x in vals)
        rows[str(q)] = qrow

    c1_ok = all(c["c1_ok"] for qrow in rows.values() for c in qrow.values())
    c2_cells = {}
    repair_found = False
    for q in P.QS:
        d0 = rows[str(q)]["0.0"]["old_dev"]
        for lam in P.LAMBDAS[1:]:
            d = rows[str(q)][str(lam)]["old_dev"]
            cell_repair = d < d0 - P.EPS_REPAIR
            c2_cells["q=%.1f,lam=%.1f" % (q, lam)] = {
                "old_dev_lambda0": d0, "old_dev": d, "delta": d - d0,
                "repair": cell_repair}
            repair_found = repair_found or cell_repair

    primary_q, primary_lam = 0.8, 0.1
    v0 = rows[str(primary_q)]["0.0"]["values"]
    v1 = rows[str(primary_q)][str(primary_lam)]["values"]
    paired = [a - b for a, b in zip(v0, v1)]
    mean_d = float(statistics.fmean(paired))
    sd_d = float(statistics.stdev(paired)) if len(paired) > 1 else 0.0
    se_d = sd_d / math.sqrt(len(paired))
    if se_d > 0:
        ci = [mean_d - T975_9 * se_d, mean_d + T975_9 * se_d]
    else:
        ci = [mean_d, mean_d]
    resolution_ok = bool(ci[0] > 0 and mean_d >= 4 * se_d)
    c3 = {"q": primary_q, "lambda": primary_lam, "per_seed_shift": paired,
          "mean_shift": mean_d, "sd_shift": sd_d, "se_shift": se_d, "t_0.975_9": T975_9,
          "ci95": ci, "four_se": 4 * se_d, "resolution_ok": resolution_ok}

    anchor_ok = all(rows[str(q)]["0.0"]["c1_ok"] for q in P.QS)
    metrics = {"anchor_ok": anchor_ok, "resolution_ok": resolution_ok,
               "operator_ok": c1_ok, "repair_found": repair_found,
               "clean": c1_ok and not repair_found and resolution_ok and complete}
    exit_label = P.classify(metrics)
    label = {"ANCHOR-BROKEN": "INSTRUMENT_BROKEN", "INDETERMINATE": "INDETERMINATE",
             "OPERATOR-MISMATCH": "REFUTED", "REGULARIZATION-REPAIRS": "REFUTED",
             "REGULARIZATION-DOES-NOT-REPAIR": "SUPPORTED",
             "O-NONE": "NOT_IDENTIFIED"}[exit_label]

    payload = {
        "schema": "m2a.phase24.results.v1",
        "round": "Phase XXIV / P24-L3REG",
        "prereg_sha256": binding["prereg_sha256"],
        "prereg_binding": {k: binding[k] for k in
                           ("disk_sha256", "git_sha256", "git_ref", "commit")},
        "commit": binding["commit"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "seeds": list(P.SEEDS), "lambdas": list(P.LAMBDAS), "qs": list(P.QS),
        "steps": P.STEPS, "gate_fraction": "15/15",
        "tol": {"eps_op": P.EPS_OP, "eps_repair": P.EPS_REPAIR},
        "rows": rows, "c2_cells": c2_cells, "c3": c3,
        "checks": {"C1_all_ok": c1_ok, "C2_no_repair": not repair_found,
                   "C3_resolution": resolution_ok,
                   "complete": complete, "anchor_ok": anchor_ok},
        "metrics": metrics, "exit": exit_label, "label_r17": label,
        "elapsed_sec": time.time() - t0,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def fmt(x):
        return "%.6f" % x

    lines = ["# Phase XXIV 结果：L2 权重衰减与 L3 中段偏差", "",
             "> 预注册 `PHASE24_PREREGISTRATION.md`（sha256 `%s`）｜commit `%s`｜gate **15/15**"
             % (binding["prereg_sha256"], binding["commit"]), "",
             "| q | λ | 采样均值 ± SD | 正则化 DP | C1 差 | 旧律 | 旧律偏差 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for q in P.QS:
        for lam in P.LAMBDAS:
            c = rows[str(q)][str(lam)]
            lines.append("| %.1f | %.1f | %s ± %s | %s | %s | %s | %s |"
                         % (q, lam, fmt(c["mean"]), fmt(c["sd"]), fmt(c["dp"]),
                            fmt(c["c1_diff"]), fmt(c["old_law"]), fmt(c["old_dev"])))
    lines += ["", "## 判据", "",
              "- **C1 算子忠实性**：全部 24 格 `|mean − DP| ≤ 0.008` ⇒ **%s**；最大差 **%s**。"
              % ("过" if c1_ok else "不过",
                 fmt(max(c["c1_diff"] for qrow in rows.values() for c in qrow.values()))),
              "- **C2 不修复**：每一格 `d(λ) ≥ d(0) − 0.008` ⇒ **%s**；%s。"
              % ("过" if not repair_found else "不过",
                 "没有一格把旧律偏差减小超过 0.008" if not repair_found
                 else "存在修复格：" + ", ".join(k for k, v in c2_cells.items() if v["repair"])),
              "- **C3 分辨率**：主格 q=0.8, λ=0.1 的配对位移 **%s**，SE **%s**，95%% CI **[%s, %s]**，"
              "4×SE **%s** ⇒ **%s**。"
              % (fmt(mean_d), fmt(se_d), fmt(ci[0]), fmt(ci[1]), fmt(4 * se_d),
                 "过" if resolution_ok else "不过"),
              "", "## 出口", "",
              "按预注册 §4 顺序取到：**`%s`** ⇒ R17 五值标签 **`%s`**。" % (exit_label, label), ""]
    if exit_label == "REGULARIZATION-DOES-NOT-REPAIR":
        lines += ["在 24 格中，正则化学习器与正则化访问加权算子一致（C1 过），旧律偏差没有任何一格被"
                  "正则化减小超过 0.008（C2 过），主格位移可分辨（C3 过）。**H1 被支持**："
                  "在这个学习器、这个算子和这组 λ/q 上，L2 权重衰减不修复旧律偏差；它按算子移动，"
                  "并把旧律偏差推大（例如 q=0.8, λ=0.1 的旧律偏差 %s vs λ=0 的 %s）。"
                  % (fmt(rows["0.8"]["0.1"]["old_dev"]), fmt(rows["0.8"]["0.0"]["old_dev"])), ""]
    elif exit_label == "REGULARIZATION-REPAIRS":
        lines += ["至少一格把旧律偏差减小超过 0.008 ⇒ **H1 被否证**：正则化确实修掉了一部分偏差；"
                  "修复格见 `c2_cells`。", ""]
    elif exit_label == "OPERATOR-MISMATCH":
        lines += ["至少一格采样均值与正则化 DP 差超过 0.008 ⇒ **正则化算子模型被否证**；"
                  "逐格差见上表。", ""]
    elif exit_label == "INDETERMINATE":
        lines += ["主格配对位移的 95% CI 含 0 ⇒ **本轮无法判定**；按预注册 §5 只能用种子池 4010–4019 "
                  "做一次确证，容差一字不动。", ""]
    elif exit_label == "ANCHOR-BROKEN":
        lines += ["λ=0 的已知答案没有复现 Phase V 算子 ⇒ **仪器损坏**，本轮不产出科学判定。", ""]
    else:
        lines += ["数据不完整或模式混合 ⇒ **不识别**；按预注册兜底档处理。", ""]
    lines += ["## 边界", "",
              "- 只针对这台表格 Q-learning、这个访问加权算子、λ∈{0, 0.1, 0.2, 0.4}、q∈{0.5…1.0}；"
              "不声明其它正则化（L1、dropout、early stopping）或其它估计器族。",
              "- 全为 `SIMULATION_RESULT`；Phase III/IV/V/V-d 的判定一字未改（R6）。",
              "- 旧律 `0.36(2q−1)` 只是描述基线；Phase V 的算子才是主对照。",
              "", "## 复现", "",
              "```bash",
              "cd m2a/experiments",
              "python3 p24_gate.py          # 15/15",
              "python3 run_phase24.py       # 先验预注册绑定，再跑 24 格 × 10 种子",
              "```", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("exit %s | label %s | C1 %s | C2 %s | C3 %s | elapsed %.1fs"
          % (exit_label, label, c1_ok, not repair_found, resolution_ok, time.time() - t0))
    print("wrote %s and %s" % (OUT_JSON.name, OUT_MD.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
