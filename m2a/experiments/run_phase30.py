"""Phase XXX: fixed 20% abstention on the frozen GBDT + Platt scores.

Zero-training, zero-refit: the 100 stumps come from Phase XXVIII and the Platt a,b from Phase XXIX.
The C policy skips the bottom 20% of the calibrated probabilities, so the take set is non-degenerate
by construction. No new data; no online intervention.

Run from anywhere: `python3 experiments/run_phase30.py [--check]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

import numpy as np

import run_phase26 as P26
import run_phase27 as P27
import run_phase28 as P28

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
PREREG = EXP / "PHASE30_PREREGISTRATION.md"
OUT = EXP / "phase30_results.json"
MODEL = EXP / "phase28_results.json"
CAL = EXP / "phase29_results.json"
DATA_FILE = "open_bandit_dataset.zip"  # outside the repository, under WORK/_m2a_data/
MODEL_SHA = "ab31800636fcc92f9a7c94b88090f3646e1a04be540838e924850e5b96f9d63d"
CAL_SHA = "6eebc2cec84b5169b2023422a326acace3c9e7867dbb8c2e6bd032473d5ba2a7"
ABSTAIN = 0.20
LOW, HIGH = 0.75, 0.85
BOOT = 2000
BUCKETS = 1000
SEED = 20261027
TS_TOL = 0.001
EXITS = ("FIXED20_C_BETTER", "FIXED20_C_NOT_BETTER", "FIXED20_CALIBRATION_FAILED",
         "DATA_OR_MODEL_MISMATCH")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def bind(prereg: pathlib.Path = PREREG) -> dict:
    rel = str(prereg.resolve().relative_to(REPO)) if prereg.resolve().is_relative_to(REPO) else ""
    disk = prereg.read_bytes() if prereg.exists() else b""
    head = P26.git_head(rel) if rel else b""
    return {"path": rel, "disk_sha256": sha(disk) if disk else "",
            "git_head_sha256": sha(head) if head else "",
            "two_channel_match": bool(disk) and sha(disk) == sha(head)}


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def build() -> dict:
    t0 = time.time()
    zb = P26.ZIP.read_bytes() if P26.ZIP.exists() else b""
    mb = MODEL.read_bytes() if MODEL.exists() else b""
    cb = CAL.read_bytes() if CAL.exists() else b""
    data_ok = bool(zb) and sha(zb) == P26.ZIP_SHA and len(zb) == P26.ZIP_BYTES
    model_ok = bool(mb) and sha(mb) == MODEL_SHA
    cal_ok = bool(cb) and sha(cb) == CAL_SHA
    binding = bind()
    if not (data_ok and model_ok and cal_ok):
        return {"schema": "m2a.phase30.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
                "prereg_binding": binding, "data_ok": data_ok, "model_ok": model_ok,
                "cal_ok": cal_ok, "exit": "DATA_OR_MODEL_MISMATCH", "label_r17": "NULL"}
    src = json.loads(mb)
    stumps = src["model"]["stumps"]
    cal = json.loads(cb)["calibration"]
    if len(stumps) != 100 or cal.get("kind") != "Platt":
        return {"schema": "m2a.phase30.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()), "prereg_binding": binding,
                "data_ok": True, "model_ok": False, "cal_ok": False,
                "exit": "DATA_OR_MODEL_MISMATCH", "label_r17": "NULL"}
    a, b = float(cal["a"]), float(cal["b"])
    scan = P26.scan(0)
    A_fit, fit_item, y_fit, A_cal, cal_item, y_cal, A_te, te_item, y_te, pos, users = P28.collect(scan["total_rows"])
    item_index = {}
    for it in fit_item:
        if it not in item_index and len(item_index) < 80:
            item_index[it] = len(item_index)
    edges = P28.make_bins(A_fit)
    X_te = P28.to_matrix(A_te, te_item, edges, item_index)
    score = P28.apply_stumps(X_te, stumps)
    p = np.clip(sigmoid(a * score + b), 1e-6, 1 - 1e-6)
    p0 = float(y_te.mean())
    base_ll = -(p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)) if 0 < p0 < 1 else 0.0
    ll = float(-np.mean(y_te * np.log(p) + (1 - y_te) * np.log(1 - p)))
    auc = P27.auc_rank(p, y_te)
    thr = float(np.quantile(p, ABSTAIN))
    c_take = p >= thr
    c_skip = ~c_take
    s_take = (pos % 3 != 0)
    def rate(mask):
        n = int(mask.sum()); c = int(y_te[mask].sum())
        return n, c, (c / n if n else 0.0)
    s_n, s_c, s_r = rate(s_take)
    c_n, c_c, c_r = rate(c_take)
    take_rate = c_n / len(y_te)
    buck = np.array([int(hashlib.sha1(u.encode("utf-8")).hexdigest(), 16) % BUCKETS for u in users],
                    dtype=np.int32)
    rng = np.random.default_rng(SEED)
    arr = np.zeros((BUCKETS, 4), dtype=float)
    for k in range(BUCKETS):
        mk = buck == k
        ms, mc = mk & s_take, mk & c_take
        arr[k] = [int(ms.sum()), int(y_te[ms].sum()), int(mc.sum()), int(y_te[mc].sum())]
    idx = rng.integers(0, BUCKETS, size=(BOOT, BUCKETS))
    sm = arr[idx].sum(axis=1)
    sr = np.where(sm[:, 0] > 0, sm[:, 1] / sm[:, 0], np.nan)
    cr = np.where(sm[:, 2] > 0, sm[:, 3] / sm[:, 2], np.nan)
    diff = cr - sr
    q = [2.5, 97.5]
    ev = {
        "test_rows": int(len(y_te)), "test_click_rate": p0,
        "s_take_n": s_n, "s_take_clicks": s_c, "delta_s": s_r,
        "c_take_n": c_n, "c_take_clicks": c_c, "delta_c": c_r,
        "c_skip_n": int(c_skip.sum()), "take_rate": take_rate,
        "contrast": c_r - s_r,
        "delta_s_ci95": [float(np.nanpercentile(sr, q[0])), float(np.nanpercentile(sr, q[1]))],
        "delta_c_ci95": [float(np.nanpercentile(cr, q[0])), float(np.nanpercentile(cr, q[1]))],
        "contrast_ci95": [float(np.nanpercentile(diff, q[0])), float(np.nanpercentile(diff, q[1]))],
        "threshold": thr, "auc": auc, "log_loss": ll, "base_log_loss": base_ll,
    }
    c4 = bool(scan["click_violations"] == 0 and scan["position_violations"] == 0
              and scan["timestamp_violations"] <= TS_TOL * max(1, scan["total_rows"]))
    c2 = bool(ev["c_skip_n"] > 0 and LOW <= take_rate <= HIGH
              and ll < base_ll and auc > 0.5)
    c3 = bool(ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0)
    if not c4:
        exit_code, label = "DATA_OR_MODEL_MISMATCH", "NULL"
    elif not c2:
        exit_code, label = "FIXED20_CALIBRATION_FAILED", "NOT_IDENTIFIED"
    elif c3:
        exit_code, label = "FIXED20_C_BETTER", "SUPPORTED"
    else:
        exit_code, label = "FIXED20_C_NOT_BETTER", "INDETERMINATE"
    return {
        "schema": "m2a.phase30.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "prereg_binding": binding,
        "dataset": {"file": str(P26.ZIP), "sha256": P26.ZIP_SHA, "bytes": P26.ZIP_BYTES,
                    "hash_ok": True},
        "sources": {"model": {"file": str(MODEL.relative_to(M)), "sha256": MODEL_SHA, "stumps": len(stumps)},
                    "calibration": {"file": str(CAL.relative_to(M)), "sha256": CAL_SHA,
                                    "kind": "Platt", "a": a, "b": b}},
        "policy": {"abstain_rate": ABSTAIN, "threshold": "20th percentile of calibrated p",
                   "take_rule": "p >= threshold", "zero_training": True, "zero_refit": True},
        "scan": scan, "estimates": ev,
        "criteria": {"C1_delta_c": ev["delta_c"] > 0 and ev["delta_c_ci95"][0] > 0,
                     "C2_policy": c2, "C3_contrast": c3, "C4_contract": c4},
        "bootstrap": {"buckets": BUCKETS, "resamples": BOOT, "seed": SEED},
        "exit": exit_code, "label_r17": label, "elapsed_sec": time.time() - t0,
        "no_online_intervention": True,
    }


def exit_of(scan_d: dict, ev: dict, contract_ok: bool) -> tuple[str, str]:
    c4 = bool(contract_ok and scan_d["click_violations"] == 0 and scan_d["position_violations"] == 0
              and scan_d["timestamp_violations"] <= TS_TOL * max(1, scan_d["total_rows"]))
    c2 = bool(ev["c_skip_n"] > 0 and LOW <= ev["take_rate"] <= HIGH
              and ev["log_loss"] < ev["base_log_loss"] and ev["auc"] > 0.5)
    c3 = bool(ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0)
    if not c4:
        return "DATA_OR_MODEL_MISMATCH", "NULL"
    if not c2:
        return "FIXED20_CALIBRATION_FAILED", "NOT_IDENTIFIED"
    if c3:
        return "FIXED20_C_BETTER", "SUPPORTED"
    return "FIXED20_C_NOT_BETTER", "INDETERMINATE"


def main() -> int:
    pre = subprocess.run([sys.executable, str(EXP / "p30_gate.py"), "--pre"], capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | S %s C %s contrast %s | auc %s ll %s/%s | take %.4f"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc.get("estimates", {}).get("delta_s"), doc.get("estimates", {}).get("delta_c"),
                 doc.get("estimates", {}).get("contrast"), doc.get("estimates", {}).get("auc"),
                 doc.get("estimates", {}).get("log_loss"), doc.get("estimates", {}).get("base_log_loss"),
                 doc.get("estimates", {}).get("take_rate", 0)))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    ev = doc.get("estimates", {})
    print("wrote %s | exit %s (%s) | S %.6f C %.6f contrast %.6f | auc %.4f ll %.5f/%.5f | take %.4f"
          % (OUT.name, doc["exit"], doc["label_r17"], ev.get("delta_s", 0), ev.get("delta_c", 0),
             ev.get("contrast", 0), ev.get("auc", 0), ev.get("log_loss", 0), ev.get("base_log_loss", 0),
             ev.get("take_rate", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
