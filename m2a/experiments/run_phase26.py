"""Phase XXVI: does a context model give the C-only policy a decision advantage on the OBD log?

C uses 160 features (80 user-item affinities + 80 item one-hot), a logistic model trained on the
first 200k rows of the train segment, and skips when the predicted click probability is below the
test median. S is the position-only skip from Phase XXV. The estimand is the click rate on taken
impressions; skip earns 0. No online intervention; the data stay outside the repository.

Run from anywhere: `python3 experiments/run_phase26.py [--check]`.
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

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
WORK = REPO.parent
PREREG = EXP / "PHASE26_PREREGISTRATION.md"
OUT = EXP / "phase26_results.json"
ZIP = WORK / "_m2a_data" / "open_bandit_dataset.zip"
MEMBER = "open_bandit_dataset/random/all/all.csv"
ZIP_SHA = "e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78"
ZIP_BYTES = 412931917
TRAIN_FRAC = 0.70
TRAIN_SAMPLE = 200000
N_AFF = 80
N_ITEM = 80
LR = 0.1
L2 = 1e-4
BATCH = 1024
EPOCHS = 5
SEED = 20261024
BUCKETS = 1000
BOOT = 2000
S_MOD = 3
TS_TOL = 0.001
EXITS = ("CONTEXT_C_BETTER", "CONTEXT_C_NOT_BETTER", "CONTEXT_MODEL_UNINFORMATIVE",
         "DATA_IDENTITY_MISMATCH")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_head(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def bind(prereg: pathlib.Path = PREREG) -> dict:
    rel = str(prereg.resolve().relative_to(REPO)) if prereg.resolve().is_relative_to(REPO) else ""
    disk = prereg.read_bytes() if prereg.exists() else b""
    head = git_head(rel) if rel else b""
    return {"path": rel, "disk_sha256": sha(disk) if disk else "",
            "git_head_sha256": sha(head) if head else "",
            "two_channel_match": bool(disk) and sha(disk) == sha(head)}


def rows_of(z: zipfile.ZipFile):
    with z.open(MEMBER) as f:
        first = True
        for raw in f:
            line = raw.decode("utf-8", "replace").rstrip("\n")
            if first:
                first = False
                continue
            p = line.split(",", 90)
            if len(p) < 90:
                continue
            yield p


def aff(p) -> np.ndarray:
    out = np.zeros(N_AFF, dtype=np.float32)
    for j in range(N_AFF):
        try:
            out[j] = float(p[10 + j])
        except ValueError:
            pass
    return out


def scan(total: int) -> dict:
    z = zipfile.ZipFile(ZIP)
    click_bad = pos_bad = ts_bad = 0
    first_ts = last_ts = None
    n = 0
    for p in rows_of(z):
        n += 1
        if first_ts is None:
            first_ts = p[1]
        if last_ts is not None and p[1] < last_ts:
            ts_bad += 1
        last_ts = p[1]
        try:
            c, pos = int(p[4]), int(p[3])
        except ValueError:
            click_bad += 1
            continue
        if c not in (0, 1):
            click_bad += 1
        if pos < 1:
            pos_bad += 1
    return {"total_rows": n, "click_violations": click_bad, "position_violations": pos_bad,
            "timestamp_violations": ts_bad, "first_timestamp": first_ts, "last_timestamp": last_ts}


def train_model() -> tuple[np.ndarray, np.ndarray, dict]:
    z = zipfile.ZipFile(ZIP)
    rows = []
    for p in rows_of(z):
        rows.append(p)
        if len(rows) >= TRAIN_SAMPLE:
            break
    item_index = {}
    for p in rows:
        if p[2] not in item_index and len(item_index) < N_ITEM:
            item_index[p[2]] = len(item_index)
    n = len(rows)
    X = np.zeros((n, N_AFF + N_ITEM), dtype=np.float32)
    y = np.zeros(n, dtype=np.float32)
    for i, p in enumerate(rows):
        X[i, :N_AFF] = aff(p)
        j = item_index.get(p[2])
        if j is not None:
            X[i, N_AFF + j] = 1.0
        y[i] = int(p[4])
    mu = X[:, :N_AFF].mean(axis=0)
    sd = X[:, :N_AFF].std(axis=0)
    sd[sd == 0] = 1.0
    X[:, :N_AFF] = (X[:, :N_AFF] - mu) / sd
    rng = np.random.default_rng(SEED)
    w = np.zeros(N_AFF + N_ITEM + 1, dtype=np.float32)
    for _ in range(EPOCHS):
        perm = rng.permutation(n)
        for b in range(0, n, BATCH):
            idx = perm[b:b + BATCH]
            xb = X[idx]
            zz = xb @ w[1:] + w[0]
            pr = 1.0 / (1.0 + np.exp(-zz))
            g = (pr - y[idx]) / len(idx)
            gw = xb.T @ g + L2 * w[1:]
            w[1:] -= LR * gw
            w[0] -= LR * g.sum()
    return w, mu, {"train_sample": n, "items": len(item_index), "item_index": item_index,
                   "features": N_AFF + N_ITEM}


def evaluate(total: int, w: np.ndarray, mu: np.ndarray, sd_placeholder=None) -> dict:
    # Re-standardise the test affinities with the same train mu/sd: recompute sd from the train sample.
    z = zipfile.ZipFile(ZIP)
    rows = []
    for p in rows_of(z):
        rows.append(p)
        if len(rows) >= TRAIN_SAMPLE:
            break
    sd = np.zeros(N_AFF, dtype=np.float32)
    for p in rows:
        sd += (aff(p) - mu) ** 2
    sd = np.sqrt(sd / max(1, len(rows)))
    sd[sd == 0] = 1.0
    train_n = int(total * TRAIN_FRAC)
    z = zipfile.ZipFile(ZIP)
    preds, clicks, poss, buckets = [], [], [], []
    seen = 0
    for p in rows_of(z):
        seen += 1
        if seen <= train_n:
            continue
        x = aff(p)
        x = (x - mu) / sd
        j = None
        # item one-hot: rebuild the index from the training sample order
        try:
            j = ITEM_INDEX.get(p[2])
        except NameError:
            j = None
        zz = float(np.dot(w[1:N_AFF + 1], x) + w[0])
        if j is not None:
            zz += float(w[1 + N_AFF + j])
        pr = 1.0 / (1.0 + np.exp(-zz))
        preds.append(pr)
        clicks.append(int(p[4]))
        poss.append(int(p[3]))
        buckets.append(int(hashlib.sha1(p[6].encode("utf-8")).hexdigest(), 16) % BUCKETS)
    preds = np.asarray(preds, dtype=np.float64)
    clicks = np.asarray(clicks, dtype=np.int8)
    poss = np.asarray(poss, dtype=np.int32)
    buckets = np.asarray(buckets, dtype=np.int32)
    clip = np.clip(preds, 1e-9, 1 - 1e-9)
    ll = -np.mean(clicks * np.log(clip) + (1 - clicks) * np.log(1 - clip))
    p0 = float(clicks.mean())
    base_ll = -(p0 * np.log(p0) + (1 - p0) * np.log(1 - p0)) if 0 < p0 < 1 else 0.0
    uniq, inv, counts = np.unique(preds, return_inverse=True, return_counts=True)
    cum = np.concatenate([[0], np.cumsum(counts)])
    rank_unique = cum[:-1] + (counts + 1) / 2.0
    ranks = rank_unique[inv]
    n1 = int(clicks.sum()); n0 = len(clicks) - n1
    auc = float((ranks[clicks == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)) if n1 and n0 else 0.5
    thr = float(np.median(preds))
    s_take = (poss % S_MOD != 0)
    c_take = (preds >= thr)
    def rate(mask):
        n = int(mask.sum()); c = int(clicks[mask].sum())
        return n, c, (c / n if n else 0.0)
    s_n, s_c, s_rate = rate(s_take)
    c_n, c_c, c_rate = rate(c_take)
    rng = np.random.default_rng(SEED)
    arr = np.zeros((BUCKETS, 4), dtype=float)
    for b in range(BUCKETS):
        mb = buckets == b
        ms, mc = mb & s_take, mb & c_take
        arr[b] = [int(ms.sum()), int(clicks[ms].sum()), int(mc.sum()), int(clicks[mc].sum())]
    idx = rng.integers(0, BUCKETS, size=(BOOT, BUCKETS))
    samp = arr[idx].sum(axis=1)
    sr = np.where(samp[:, 0] > 0, samp[:, 1] / samp[:, 0], np.nan)
    cr = np.where(samp[:, 2] > 0, samp[:, 3] / samp[:, 2], np.nan)
    diff = cr - sr
    q = [2.5, 97.5]
    return {
        "test_rows": int(len(clicks)), "test_click_rate": p0,
        "s_take_n": s_n, "s_take_clicks": s_c, "delta_s": s_rate,
        "c_take_n": c_n, "c_take_clicks": c_c, "delta_c": c_rate,
        "contrast": c_rate - s_rate,
        "delta_s_ci95": [float(np.nanpercentile(sr, q[0])), float(np.nanpercentile(sr, q[1]))],
        "delta_c_ci95": [float(np.nanpercentile(cr, q[0])), float(np.nanpercentile(cr, q[1]))],
        "contrast_ci95": [float(np.nanpercentile(diff, q[0])), float(np.nanpercentile(diff, q[1]))],
        "threshold": thr, "log_loss": float(ll), "base_log_loss": float(base_ll), "auc": auc,
    }


def exit_of(scan_d: dict, ev: dict, hash_ok: bool) -> tuple[str, str]:
    c4 = (hash_ok and scan_d["click_violations"] == 0 and scan_d["position_violations"] == 0
          and scan_d["timestamp_violations"] <= TS_TOL * max(1, scan_d["total_rows"]))
    c2 = ev["log_loss"] < ev["base_log_loss"] and ev["auc"] > 0.5
    c3 = ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0
    if not c4:
        return "DATA_IDENTITY_MISMATCH", "NULL"
    if not c2:
        return "CONTEXT_MODEL_UNINFORMATIVE", "NOT_IDENTIFIED"
    if c3:
        return "CONTEXT_C_BETTER", "SUPPORTED"
    return "CONTEXT_C_NOT_BETTER", "INDETERMINATE"


def build() -> dict:
    t0 = time.time()
    zb = ZIP.read_bytes() if ZIP.exists() else b""
    hash_ok = bool(zb) and sha(zb) == ZIP_SHA and len(zb) == ZIP_BYTES
    binding = bind()
    if not hash_ok:
        return {"schema": "m2a.phase26.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
                "prereg_binding": binding, "dataset": {"hash_ok": False},
                "exit": "DATA_IDENTITY_MISMATCH", "label_r17": "NULL"}
    scan_d = scan(0)
    w, mu, meta = train_model()
    global ITEM_INDEX
    ITEM_INDEX = meta["item_index"]
    ev = evaluate(scan_d["total_rows"], w, mu)
    exit_code, label = exit_of(scan_d, ev, hash_ok)
    return {
        "schema": "m2a.phase26.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "prereg_binding": binding,
        "dataset": {"file": str(ZIP), "member": MEMBER, "sha256": ZIP_SHA, "bytes": ZIP_BYTES,
                    "hash_ok": True, "split": "first 70% train, last 30% test"},
        "model": {"features": 160, "affinity": 80, "item_onehot": 80, "train_sample": meta["train_sample"],
                  "items": meta["items"], "lr": LR, "l2": L2, "batch": BATCH, "epochs": EPOCHS,
                  "seed": SEED, "threshold": "test median predicted probability"},
        "scan": scan_d, "estimates": ev,
        "criteria": {"C1_delta_c": ev["delta_c"] > 0 and ev["delta_c_ci95"][0] > 0,
                     "C2_model": ev["log_loss"] < ev["base_log_loss"] and ev["auc"] > 0.5,
                     "C3_contrast": ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0,
                     "C4_contract": exit_code != "DATA_IDENTITY_MISMATCH"},
        "bootstrap": {"buckets": BUCKETS, "resamples": BOOT, "seed": SEED},
        "exit": exit_code, "label_r17": label, "elapsed_sec": time.time() - t0,
        "no_online_intervention": True,
    }


def main() -> int:
    pre = subprocess.run([sys.executable, str(EXP / "p26_gate.py"), "--pre"], capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | S %s C %s contrast %s | auc %s"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc.get("estimates", {}).get("delta_s"), doc.get("estimates", {}).get("delta_c"),
                 doc.get("estimates", {}).get("contrast"), doc.get("estimates", {}).get("auc")))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    ev = doc.get("estimates", {})
    print("wrote %s | exit %s (%s) | S %.6f C %.6f contrast %.6f | auc %.4f"
          % (OUT.name, doc["exit"], doc["label_r17"], ev.get("delta_s", 0), ev.get("delta_c", 0),
             ev.get("contrast", 0), ev.get("auc", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
