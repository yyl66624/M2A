"""Phase XXVIII: a numpy depth-1 gradient-boosted model as the C policy on the OBD log.

80 affinity features are binned into 16 quantiles; 80 item one-hots are added. The model is 100
stumps, each fit on a 50k subsample with Newton leaves and L2=1.0, then isotonic-calibrated on
rows 200,001-300,000. The test is the last 30%. No third-party ML dependency; no online action.

Run from anywhere: `python3 experiments/run_phase28.py [--check]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time
import zipfile

import numpy as np

import run_phase26 as P26
import run_phase27 as P27

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
PREREG = EXP / "PHASE28_PREREGISTRATION.md"
OUT = EXP / "phase28_results.json"
DATA_FILE = "open_bandit_dataset.zip"  # outside the repository, under WORK/_m2a_data/
FIT = 200000
CAL = 100000
BINS = 16
ROUNDS = 100
SUBSAMPLE = 50000
LR = 0.1
L2 = 1.0
SEED = 20261025
ISO_BINS = 100
BOOT = 2000
BUCKETS = 1000
TS_TOL = 0.001
EXITS = ("GBDT_C_BETTER", "GBDT_C_NOT_BETTER", "GBDT_CALIBRATION_FAILED",
         "DATA_IDENTITY_MISMATCH")


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


def collect(total: int):
    fit_A, fit_item, fit_y = [], [], []
    cal_A, cal_item, cal_y = [], [], []
    te_A, te_item, te_y, te_pos, te_user = [], [], [], [], []
    train_n = int(total * 0.70)
    seen = 0
    z = zipfile.ZipFile(P26.ZIP)
    for p in P26.rows_of(z):
        seen += 1
        a = np.asarray(p[10:90], dtype=np.float32)
        if seen <= FIT:
            fit_A.append(a); fit_item.append(p[2]); fit_y.append(int(p[4]))
        elif seen <= FIT + CAL:
            cal_A.append(a); cal_item.append(p[2]); cal_y.append(int(p[4]))
        elif seen > train_n:
            te_A.append(a); te_item.append(p[2]); te_y.append(int(p[4]))
            te_pos.append(int(p[3])); te_user.append(p[6])
    return (np.vstack(fit_A), fit_item, np.asarray(fit_y, dtype=np.float64),
            np.vstack(cal_A), cal_item, np.asarray(cal_y, dtype=np.float64),
            np.vstack(te_A), te_item, np.asarray(te_y, dtype=np.int8),
            np.asarray(te_pos, dtype=np.int32), te_user)


def make_bins(A_fit):
    q = np.linspace(0, 1, BINS + 1)[1:-1]
    return np.quantile(A_fit, q, axis=0)  # (BINS-1, 80)


def to_matrix(A, items, edges, item_index):
    n = A.shape[0]
    X = np.zeros((n, 80 + 80), dtype=np.int8)
    for j in range(80):
        X[:, j] = np.searchsorted(edges[:, j], A[:, j], side="right")
    for i, it in enumerate(items):
        k = item_index.get(it)
        if k is not None:
            X[i, 80 + k] = 1
    return X


def gbdt_fit(X, y, seed):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    p0 = float(y.mean())
    score = np.full(n, np.log(p0 / (1 - p0)), dtype=np.float64)
    stumps = []
    for _ in range(ROUNDS):
        idx = rng.choice(n, SUBSAMPLE, replace=False)
        p = sigmoid(score[idx])
        g = p - y[idx]
        h = p * (1 - p)
        Gt = float(g.sum()); Ht = float(h.sum())
        base = Gt * Gt / (Ht + L2)
        best = None
        for j in range(80):
            b = X[idx, j]
            G = np.bincount(b, weights=g, minlength=BINS)
            H = np.bincount(b, weights=h, minlength=BINS)
            Gc = np.cumsum(G)[:-1]; Hc = np.cumsum(H)[:-1]
            gain = Gc * Gc / (Hc + L2) + (Gt - Gc) ** 2 / (Ht - Hc + L2) - base
            t = int(np.argmax(gain))
            if gain[t] > 0 and (best is None or gain[t] > best[0]):
                left = -Gc[t] / (Hc[t] + L2)
                right = -(Gt - Gc[t]) / (Ht - Hc[t] + L2)
                best = (float(gain[t]), j, t, left, right, False)
        for j in range(80, 160):
            b = X[idx, j] == 1
            G1 = float(g[b].sum()); H1 = float(h[b].sum())
            G0 = Gt - G1; H0 = Ht - H1
            gain = G1 * G1 / (H1 + L2) + G0 * G0 / (H0 + L2) - base
            if gain > 0 and (best is None or gain > best[0]):
                best = (float(gain), j, 0, -G1 / (H1 + L2), -G0 / (H0 + L2), True)
        if best is None:
            continue
        _, j, t, left, right, binary = best
        if binary:
            mask = X[:, j] == 1
        else:
            mask = X[:, j] <= t
        score += LR * np.where(mask, left, right)
        stumps.append({"j": j, "t": t, "left": float(left), "right": float(right),
                       "binary": bool(binary)})
    return stumps


def apply_stumps(X, stumps):
    s = np.zeros(X.shape[0], dtype=np.float64)
    for st in stumps:
        if st["binary"]:
            mask = X[:, st["j"]] == 1
        else:
            mask = X[:, st["j"]] <= st["t"]
        s += np.where(mask, st["left"], st["right"])
    return s


def build() -> dict:
    t0 = time.time()
    zb = P26.ZIP.read_bytes() if P26.ZIP.exists() else b""
    hash_ok = bool(zb) and sha(zb) == P26.ZIP_SHA and len(zb) == P26.ZIP_BYTES
    binding = bind()
    if not hash_ok:
        return {"schema": "m2a.phase28.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
                "prereg_binding": binding, "dataset": {"hash_ok": False},
                "exit": "DATA_IDENTITY_MISMATCH", "label_r17": "NULL"}
    scan = P26.scan(0)
    A_fit, fit_item, y_fit, A_cal, cal_item, y_cal, A_te, te_item, y_te, pos, users = collect(scan["total_rows"])
    item_index = {}
    for it in fit_item:
        if it not in item_index and len(item_index) < 80:
            item_index[it] = len(item_index)
    edges = make_bins(A_fit)
    X_fit = to_matrix(A_fit, fit_item, edges, item_index)
    X_cal = to_matrix(A_cal, cal_item, edges, item_index)
    X_te = to_matrix(A_te, te_item, edges, item_index)
    del A_fit, A_cal, A_te
    stumps = gbdt_fit(X_fit, y_fit, SEED)
    cal_score = apply_stumps(X_cal, stumps)
    iso_edges, iso_blocks = P27.fit_isotonic(cal_score, y_cal)
    te_score = apply_stumps(X_te, stumps)
    p_iso = np.clip(P27.apply_iso(te_score, iso_edges, iso_blocks), 1e-6, 1 - 1e-6)
    p0 = float(y_te.mean())
    base_ll = -(p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)) if 0 < p0 < 1 else 0.0
    iso_ll = float(-np.mean(y_te * np.log(p_iso) + (1 - y_te) * np.log(1 - p_iso)))
    auc = P27.auc_rank(p_iso, y_te)
    s_take = (pos % 3 != 0)
    thr = float(np.median(p_iso))
    c_take = p_iso >= thr
    def rate(mask):
        n = int(mask.sum()); c = int(y_te[mask].sum())
        return n, c, (c / n if n else 0.0)
    s_n, s_c, s_r = rate(s_take)
    c_n, c_c, c_r = rate(c_take)
    buck = np.array([int(hashlib.sha1(u.encode("utf-8")).hexdigest(), 16) % BUCKETS for u in users],
                    dtype=np.int32)
    rng = np.random.default_rng(SEED)
    arr = np.zeros((BUCKETS, 4), dtype=float)
    for b in range(BUCKETS):
        mb = buck == b
        ms, mc = mb & s_take, mb & c_take
        arr[b] = [int(ms.sum()), int(y_te[ms].sum()), int(mc.sum()), int(y_te[mc].sum())]
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
        "contrast": c_r - s_r,
        "delta_s_ci95": [float(np.nanpercentile(sr, q[0])), float(np.nanpercentile(sr, q[1]))],
        "delta_c_ci95": [float(np.nanpercentile(cr, q[0])), float(np.nanpercentile(cr, q[1]))],
        "contrast_ci95": [float(np.nanpercentile(diff, q[0])), float(np.nanpercentile(diff, q[1]))],
        "threshold": thr, "auc": auc, "log_loss": iso_ll, "base_log_loss": base_ll,
    }
    c4 = bool(scan["click_violations"] == 0 and scan["position_violations"] == 0
              and scan["timestamp_violations"] <= TS_TOL * max(1, scan["total_rows"]))
    c2 = bool(iso_ll < base_ll and auc > 0.5)
    c3 = bool(ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0)
    if not c4:
        exit_code, label = "DATA_IDENTITY_MISMATCH", "NULL"
    elif not c2:
        exit_code, label = "GBDT_CALIBRATION_FAILED", "NOT_IDENTIFIED"
    elif c3:
        exit_code, label = "GBDT_C_BETTER", "SUPPORTED"
    else:
        exit_code, label = "GBDT_C_NOT_BETTER", "INDETERMINATE"
    return {
        "schema": "m2a.phase28.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "prereg_binding": binding,
        "dataset": {"file": str(P26.ZIP), "member": P26.MEMBER, "sha256": P26.ZIP_SHA,
                    "bytes": P26.ZIP_BYTES, "hash_ok": True,
                    "fit": "rows 1-200000", "calibration": "rows 200001-300000", "test": "last 30%"},
        "model": {"kind": "numpy depth-1 gradient boosting", "features": 160, "bins": BINS,
                  "rounds": ROUNDS, "stumps_used": len(stumps), "subsample": SUBSAMPLE,
                  "lr": LR, "l2": L2, "seed": SEED, "iso_bins": ISO_BINS,
                  "stumps": stumps},
        "scan": scan, "estimates": ev,
        "criteria": {"C1_delta_c": ev["delta_c"] > 0 and ev["delta_c_ci95"][0] > 0,
                     "C2_calibration": c2, "C3_contrast": c3, "C4_contract": c4},
        "bootstrap": {"buckets": BUCKETS, "resamples": BOOT, "seed": SEED},
        "exit": exit_code, "label_r17": label, "elapsed_sec": time.time() - t0,
        "no_online_intervention": True,
    }


def exit_of(scan_d: dict, ev: dict, hash_ok: bool) -> tuple[str, str]:
    c4 = bool(hash_ok and scan_d["click_violations"] == 0 and scan_d["position_violations"] == 0
              and scan_d["timestamp_violations"] <= TS_TOL * max(1, scan_d["total_rows"]))
    c2 = bool(ev["log_loss"] < ev["base_log_loss"] and ev["auc"] > 0.5)
    c3 = bool(ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0)
    if not c4:
        return "DATA_IDENTITY_MISMATCH", "NULL"
    if not c2:
        return "GBDT_CALIBRATION_FAILED", "NOT_IDENTIFIED"
    if c3:
        return "GBDT_C_BETTER", "SUPPORTED"
    return "GBDT_C_NOT_BETTER", "INDETERMINATE"


def main() -> int:
    pre = subprocess.run([sys.executable, str(EXP / "p28_gate.py"), "--pre"], capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | S %s C %s contrast %s | auc %s ll %s/%s"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc.get("estimates", {}).get("delta_s"), doc.get("estimates", {}).get("delta_c"),
                 doc.get("estimates", {}).get("contrast"), doc.get("estimates", {}).get("auc"),
                 doc.get("estimates", {}).get("log_loss"), doc.get("estimates", {}).get("base_log_loss")))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    ev = doc.get("estimates", {})
    print("wrote %s | exit %s (%s) | S %.6f C %.6f contrast %.6f | auc %.4f ll %.5f/%.5f | stumps %d"
          % (OUT.name, doc["exit"], doc["label_r17"], ev.get("delta_s", 0), ev.get("delta_c", 0),
             ev.get("contrast", 0), ev.get("auc", 0), ev.get("log_loss", 0),
             ev.get("base_log_loss", 0), doc["model"]["stumps_used"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
