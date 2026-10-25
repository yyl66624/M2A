"""Phase XXVII: Platt and binned-isotonic calibration of the Phase XXVI base model on the OBD log.

Fit slice: first 200k rows. Calibration slice: rows 200,001-300,000. Test: last 30%. The primary
C policy uses the isotonic-calibrated probability and skips below the test median; Platt is the
secondary. No online intervention; the data stay outside the repository.

Run from anywhere: `python3 experiments/run_phase27.py [--check]`.
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

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
PREREG = EXP / "PHASE27_PREREGISTRATION.md"
OUT = EXP / "phase27_results.json"
FIT = 200000
CAL = 100000
BINS = 100
BOOT = 2000
BUCKETS = 1000
SEED = 20261024
TS_TOL = 0.001
EXITS = ("CALIBRATED_C_BETTER", "CALIBRATED_C_NOT_BETTER", "CALIBRATION_FAILED",
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


def base_std(mu):
    z = zipfile.ZipFile(P26.ZIP)
    n = 0
    s = np.zeros(80, dtype=np.float64)
    for p in P26.rows_of(z):
        a = P26.aff(p).astype(np.float64)
        s += (a - mu) ** 2
        n += 1
        if n >= FIT:
            break
    sd = np.sqrt(s / max(1, n))
    sd[sd == 0] = 1.0
    return sd


def logits(rows, w, mu, sd, item_index):
    out = np.empty(len(rows), dtype=np.float64)
    for i, p in enumerate(rows):
        x = (P26.aff(p).astype(np.float64) - mu) / sd
        z = float(w[0] + np.dot(w[1:81], x))
        j = item_index.get(p[2])
        if j is not None:
            z += float(w[1 + 80 + j])
        out[i] = z
    return out


def pava(y, wt):
    blocks = []
    for i in range(len(y)):
        blocks.append([float(y[i]), float(wt[i]), i, i])
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            b1 = blocks.pop(); b0 = blocks.pop()
            m = (b0[0] * b0[1] + b1[0] * b1[1]) / (b0[1] + b1[1])
            blocks.append([m, b0[1] + b1[1], b0[2], b1[3]])
    return blocks


def fit_platt(z, y):
    a, b = 1.0, 0.0
    for _ in range(50):
        p = sigmoid(a * z + b)
        wt = p * (1 - p)
        g0 = float(((p - y) * z).sum()); g1 = float((p - y).sum())
        h00 = float((wt * z * z).sum()) + 1e-6
        h01 = float((wt * z).sum())
        h11 = float(wt.sum()) + 1e-6
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        a -= (h11 * g0 - h01 * g1) / det
        b -= (h00 * g1 - h01 * g0) / det
    return a, b


def fit_isotonic(z, y):
    order = np.argsort(z)
    zs, ys = z[order], y[order]
    chunks = np.array_split(np.arange(len(zs)), BINS)
    means, weights, edges = [], [], []
    for ch in chunks:
        if len(ch) == 0:
            continue
        means.append(float(ys[ch].mean())); weights.append(float(len(ch))); edges.append(float(zs[ch].max()))
    blocks = pava(means, weights)
    # map each bin to its block mean
    bin_block = [0] * len(means)
    pos = 0
    for m, wt, s, e in blocks:
        for b in range(s, e + 1):
            bin_block[b] = m
        pos = e
    return np.asarray(edges, dtype=np.float64), np.asarray(bin_block, dtype=np.float64)


def apply_iso(z, edges, bin_block):
    idx = np.searchsorted(edges, z, side="left")
    idx = np.clip(idx, 0, len(bin_block) - 1)
    return bin_block[idx]


def auc_rank(p, y):
    uniq, inv, counts = np.unique(p, return_inverse=True, return_counts=True)
    cum = np.concatenate([[0], np.cumsum(counts)])
    ranks = (cum[:-1] + (counts + 1) / 2.0)[inv]
    n1 = int(y.sum()); n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)) if n1 and n0 else 0.5


def exit_of(scan_d: dict, ev: dict, hash_ok: bool) -> tuple[str, str]:
    c4 = (hash_ok and scan_d["click_violations"] == 0 and scan_d["position_violations"] == 0
          and scan_d["timestamp_violations"] <= TS_TOL * max(1, scan_d["total_rows"]))
    c2 = ev["log_loss"] < ev["base_log_loss"] and ev["auc"] > 0.5
    c3 = ev["contrast_iso"] > 0 and ev["contrast_iso_ci95"][0] > 0
    if not c4:
        return "DATA_IDENTITY_MISMATCH", "NULL"
    if not c2:
        return "CALIBRATION_FAILED", "NOT_IDENTIFIED"
    if c3:
        return "CALIBRATED_C_BETTER", "SUPPORTED"
    return "CALIBRATED_C_NOT_BETTER", "INDETERMINATE"


def build() -> dict:
    t0 = time.time()
    zb = P26.ZIP.read_bytes() if P26.ZIP.exists() else b""
    hash_ok = bool(zb) and sha(zb) == P26.ZIP_SHA and len(zb) == P26.ZIP_BYTES
    binding = bind()
    if not hash_ok:
        return {"schema": "m2a.phase27.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
                "prereg_binding": binding, "dataset": {"hash_ok": False},
                "exit": "DATA_IDENTITY_MISMATCH", "label_r17": "NULL"}
    scan = P26.scan(0)
    w, mu, meta = P26.train_model()
    sd = base_std(mu)
    item_index = meta["item_index"]
    # calibration slice
    z = zipfile.ZipFile(P26.ZIP)
    cal_rows = []
    seen = 0
    for p in P26.rows_of(z):
        seen += 1
        if seen <= FIT:
            continue
        cal_rows.append(p)
        if len(cal_rows) >= CAL:
            break
    cz = logits(cal_rows, w, mu, sd, item_index)
    cy = np.array([int(p[4]) for p in cal_rows], dtype=np.float64)
    a, b = fit_platt(cz, cy)
    edges, bin_block = fit_isotonic(cz, cy)
    # test slice: one pass, logits on the fly
    train_n = int(scan["total_rows"] * 0.70)
    z = zipfile.ZipFile(P26.ZIP)
    seen = 0
    tz, ty, pos, buck = [], [], [], []
    for p in P26.rows_of(z):
        seen += 1
        if seen <= train_n:
            continue
        x = (P26.aff(p).astype(np.float64) - mu) / sd
        zz = float(w[0] + np.dot(w[1:81], x))
        j = item_index.get(p[2])
        if j is not None:
            zz += float(w[1 + 80 + j])
        tz.append(zz); ty.append(int(p[4])); pos.append(int(p[3]))
        buck.append(int(hashlib.sha1(p[6].encode("utf-8")).hexdigest(), 16) % BUCKETS)
    tz = np.asarray(tz, dtype=np.float64)
    ty = np.asarray(ty, dtype=np.int8)
    pos = np.asarray(pos, dtype=np.int32)
    buck = np.asarray(buck, dtype=np.int32)
    p_platt = np.clip(sigmoid(a * tz + b), 1e-6, 1 - 1e-6)
    p_iso = np.clip(apply_iso(tz, edges, bin_block), 1e-6, 1 - 1e-6)
    p0 = float(ty.mean())
    base_ll = -(p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)) if 0 < p0 < 1 else 0.0
    iso_ll = float(-np.mean(ty * np.log(p_iso) + (1 - ty) * np.log(1 - p_iso)))
    auc = auc_rank(p_iso, ty)
    s_take = (pos % 3 != 0)
    thr_iso = float(np.median(p_iso)); thr_platt = float(np.median(p_platt))
    iso_take = p_iso >= thr_iso
    platt_take = p_platt >= thr_platt
    def rate(mask):
        n = int(mask.sum()); c = int(ty[mask].sum())
        return n, c, (c / n if n else 0.0)
    s_n, s_c, s_r = rate(s_take)
    i_n, i_c, i_r = rate(iso_take)
    pl_n, pl_c, pl_r = rate(platt_take)
    rng = np.random.default_rng(SEED)
    arr = np.zeros((BUCKETS, 6), dtype=float)
    for bkt in range(BUCKETS):
        mb = buck == bkt
        ms, mi, mp = mb & s_take, mb & iso_take, mb & platt_take
        arr[bkt] = [int(ms.sum()), int(ty[ms].sum()), int(mi.sum()), int(ty[mi].sum()),
                    int(mp.sum()), int(ty[mp].sum())]
    idx = rng.integers(0, BUCKETS, size=(BOOT, BUCKETS))
    sm = arr[idx].sum(axis=1)
    sr = np.where(sm[:, 0] > 0, sm[:, 1] / sm[:, 0], np.nan)
    ir = np.where(sm[:, 2] > 0, sm[:, 3] / sm[:, 2], np.nan)
    pr = np.where(sm[:, 4] > 0, sm[:, 5] / sm[:, 4], np.nan)
    d_iso, d_platt = ir - sr, pr - sr
    q = [2.5, 97.5]
    ev = {
        "test_rows": int(len(ty)), "test_click_rate": p0,
        "s_take_n": s_n, "s_take_clicks": s_c, "delta_s": s_r,
        "iso_take_n": i_n, "iso_take_clicks": i_c, "delta_iso": i_r,
        "platt_take_n": pl_n, "platt_take_clicks": pl_c, "delta_platt": pl_r,
        "contrast_iso": i_r - s_r, "contrast_platt": pl_r - s_r,
        "contrast_iso_ci95": [float(np.nanpercentile(d_iso, q[0])), float(np.nanpercentile(d_iso, q[1]))],
        "contrast_platt_ci95": [float(np.nanpercentile(d_platt, q[0])), float(np.nanpercentile(d_platt, q[1]))],
        "delta_iso_ci95": [float(np.nanpercentile(ir, q[0])), float(np.nanpercentile(ir, q[1]))],
        "delta_s_ci95": [float(np.nanpercentile(sr, q[0])), float(np.nanpercentile(sr, q[1]))],
        "auc": auc, "log_loss": iso_ll, "base_log_loss": base_ll,
        "threshold_iso": thr_iso, "threshold_platt": thr_platt,
    }
    exit_code, label = exit_of(scan, ev, True)
    return {
        "schema": "m2a.phase27.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "prereg_binding": binding,
        "dataset": {"file": str(P26.ZIP), "member": P26.MEMBER, "sha256": P26.ZIP_SHA,
                    "bytes": P26.ZIP_BYTES, "hash_ok": True,
                    "fit": "rows 1-200000", "calibration": "rows 200001-300000", "test": "last 30%"},
        "model": {"features": 160, "fit": FIT, "calibration": CAL, "bins": BINS,
                  "platt": {"a": a, "b": b}, "seed": SEED},
        "scan": scan, "estimates": ev,
        "criteria": {"C1_delta_iso": ev["delta_iso"] > 0 and ev["delta_iso_ci95"][0] > 0,
                     "C2_calibration": c2, "C3_contrast_iso": c3, "C4_contract": c4},
        "bootstrap": {"buckets": BUCKETS, "resamples": BOOT, "seed": SEED},
        "exit": exit_code, "label_r17": label, "elapsed_sec": time.time() - t0,
        "no_online_intervention": True,
    }


def main() -> int:
    pre = subprocess.run([sys.executable, str(EXP / "p27_gate.py"), "--pre"], capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | S %s iso %s platt %s | iso contrast %s | auc %s ll %s/%s"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc.get("estimates", {}).get("delta_s"), doc.get("estimates", {}).get("delta_iso"),
                 doc.get("estimates", {}).get("delta_platt"),
                 doc.get("estimates", {}).get("contrast_iso"), doc.get("estimates", {}).get("auc"),
                 doc.get("estimates", {}).get("log_loss"), doc.get("estimates", {}).get("base_log_loss")))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    ev = doc.get("estimates", {})
    print("wrote %s | exit %s (%s) | S %.6f iso %.6f platt %.6f | iso contrast %.6f | auc %.4f ll %.5f/%.5f"
          % (OUT.name, doc["exit"], doc["label_r17"], ev.get("delta_s", 0), ev.get("delta_iso", 0),
             ev.get("delta_platt", 0), ev.get("contrast_iso", 0), ev.get("auc", 0),
             ev.get("log_loss", 0), ev.get("base_log_loss", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
