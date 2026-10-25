"""Phase XXV: the non-constructive S-only arm on a real randomized recommender log.

S-only policy: skip every third impression by position, with no representation of the item's
value. C-only policy: skip items whose training click rate is below the item median. The
estimand is the click rate on taken impressions; a skipped impression earns 0. The data are the
ZOZO Open Bandit Dataset's uniform-policy log, outside the repository; only identity, counts and
estimates are committed.

Run from anywhere: `python3 experiments/run_phase25.py [--check]`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
import subprocess
import sys
import time
import zipfile

import numpy as np

EXP = pathlib.Path(__file__).resolve().parent
M = EXP.parent
REPO = M.parent
WORK = REPO.parent
PREREG = EXP / "PHASE25_PREREGISTRATION.md"
OUT = EXP / "phase25_results.json"
ZIP = WORK / "_m2a_data" / "open_bandit_dataset.zip"
MEMBER = "open_bandit_dataset/random/all/all.csv"
ZIP_SHA = "e8ec18196582a5937381a1776382ca940689b90a18d2dcd1fb635be6df614d78"
ZIP_BYTES = 412931917
TRAIN_FRAC = 0.70
MIN_ITEM_SHOWS = 100
BUCKETS = 1000
BOOT = 2000
SEED = 20261023
S_MOD = 3
C2_TOL = 0.01
TS_TOL = 0.001
EXITS = ("S_ONLY_NONZERO_AND_C_BETTER", "S_ONLY_NONZERO_C_NOT_BETTER",
         "S_ONLY_ZERO_OR_NEGLIGIBLE", "DATA_IDENTITY_MISMATCH")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_head(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def bind(prereg: pathlib.Path = PREREG) -> dict:
    rel = str(prereg.resolve().relative_to(REPO)) if prereg.resolve().is_relative_to(REPO) else ""
    disk = prereg.read_bytes() if prereg.exists() else b""
    head = git_head(rel)
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
            p = line.split(",", 8)
            if len(p) < 7:
                continue
            yield p


def scan() -> dict:
    z = zipfile.ZipFile(ZIP)
    total = 0
    click_bad = pos_bad = ts_bad = 0
    first_ts = last_ts = None
    props = set()
    with z.open(MEMBER) as f:
        first = True
        for raw in f:
            line = raw.decode("utf-8", "replace").rstrip("\n")
            if first:
                first = False
                continue
            p = line.split(",", 8)
            if len(p) < 7:
                continue
            total += 1
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
            if len(props) < 20:
                props.add(p[5])
    return {"total_rows": total, "click_violations": click_bad, "position_violations": pos_bad,
            "timestamp_violations": ts_bad, "first_timestamp": first_ts, "last_timestamp": last_ts,
            "propensity_values_sample": sorted(props)}


def evaluate(total: int) -> dict:
    train_n = int(total * TRAIN_FRAC)
    z = zipfile.ZipFile(ZIP)
    item_n, item_clicks = {}, {}
    s_take_n = s_take_c = 0
    c_take_n = c_take_c = 0
    s_skip_n = s_skip_c = 0
    s_take_label_n = s_take_label_c = 0
    buckets = {i: [0, 0, 0, 0] for i in range(BUCKETS)}  # S take n, S take c, C take n, C take c
    train_rows = 0
    for p in rows_of(z):
        try:
            item, pos, click, user = p[2], int(p[3]), int(p[4]), p[6]
        except ValueError:
            continue
        if train_rows < train_n:
            item_n[item] = item_n.get(item, 0) + 1
            item_clicks[item] = item_clicks.get(item, 0) + click
            train_rows += 1
    ctr = {k: item_clicks[k] / n for k, n in item_n.items() if n >= MIN_ITEM_SHOWS}
    threshold = statistics.median(ctr.values()) if ctr else 0.0
    z = zipfile.ZipFile(ZIP)
    seen = 0
    for p in rows_of(z):
        try:
            item, pos, click, user = p[2], int(p[3]), int(p[4]), p[6]
        except ValueError:
            continue
        if seen < train_n:
            seen += 1
            continue
        b = int(hashlib.sha1(user.encode("utf-8")).hexdigest(), 16) % BUCKETS
        s_skip = (pos % S_MOD == 0)
        c_val = ctr.get(item)
        c_skip = (c_val is None) or (c_val < threshold)
        if s_skip:
            s_skip_n += 1
            s_skip_c += click
        else:
            s_take_n += 1
            s_take_c += click
            buckets[b][0] += 1
            buckets[b][1] += click
        if not c_skip:
            c_take_n += 1
            c_take_c += click
            buckets[b][2] += 1
            buckets[b][3] += click
    rng = np.random.default_rng(SEED)
    arr = np.array([buckets[i] for i in range(BUCKETS)], dtype=float)
    idx = rng.integers(0, BUCKETS, size=(BOOT, BUCKETS))
    samp = arr[idx].sum(axis=1)
    s_rate = np.where(samp[:, 0] > 0, samp[:, 1] / samp[:, 0], np.nan)
    c_rate = np.where(samp[:, 2] > 0, samp[:, 3] / samp[:, 2], np.nan)
    diff = c_rate - s_rate
    q = [2.5, 97.5]
    return {
        "train_rows": train_n, "test_rows": total - train_n,
        "items_seen_train": len(item_n), "items_in_ctr": len(ctr), "ctr_threshold": threshold,
        "s_take_n": s_take_n, "s_take_clicks": s_take_c, "s_skip_n": s_skip_n, "s_skip_clicks": s_skip_c,
        "c_take_n": c_take_n, "c_take_clicks": c_take_c,
        "delta_s": s_take_c / s_take_n if s_take_n else 0.0,
        "delta_c": c_take_c / c_take_n if c_take_n else 0.0,
        "contrast": (c_take_c / c_take_n if c_take_n else 0.0) - (s_take_c / s_take_n if s_take_n else 0.0),
        "delta_s_ci95": [float(np.nanpercentile(s_rate, q[0])), float(np.nanpercentile(s_rate, q[1]))],
        "delta_c_ci95": [float(np.nanpercentile(c_rate, q[0])), float(np.nanpercentile(c_rate, q[1]))],
        "contrast_ci95": [float(np.nanpercentile(diff, q[0])), float(np.nanpercentile(diff, q[1]))],
        "s_skip_label_click_rate": s_skip_c / s_skip_n if s_skip_n else 0.0,
        "s_take_label_click_rate": s_take_c / s_take_n if s_take_n else 0.0,
    }


def exit_of(scan_d: dict, ev: dict, hash_ok: bool) -> tuple[str, str]:
    c4 = (hash_ok
          and scan_d["click_violations"] == 0 and scan_d["position_violations"] == 0
          and scan_d["timestamp_violations"] <= TS_TOL * max(1, scan_d["total_rows"]))
    c1 = ev["delta_s"] > 0 and ev["delta_s_ci95"][0] > 0
    c2 = abs(ev["s_skip_label_click_rate"] - ev["s_take_label_click_rate"]) <= C2_TOL
    c3 = ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0
    if not c4:
        return "DATA_IDENTITY_MISMATCH", "NULL"
    if c1 and c3:
        return "S_ONLY_NONZERO_AND_C_BETTER", "SUPPORTED"
    if c1:
        return "S_ONLY_NONZERO_C_NOT_BETTER", "INDETERMINATE"
    return "S_ONLY_ZERO_OR_NEGLIGIBLE", "REFUTED"


def build() -> dict:
    t0 = time.time()
    zip_bytes = ZIP.read_bytes() if ZIP.exists() else b""
    hash_ok = bool(zip_bytes) and sha(zip_bytes) == ZIP_SHA and len(zip_bytes) == ZIP_BYTES
    binding = bind()
    if not hash_ok:
        return {"schema": "m2a.phase25.v1", "preregistration": str(PREREG.relative_to(M)),
                "prereg_sha256": sha(PREREG.read_bytes()) if PREREG.exists() else "",
                "prereg_binding": binding,
                "dataset": {"sha256": sha(zip_bytes) if zip_bytes else "", "bytes": len(zip_bytes),
                            "expected_sha256": ZIP_SHA, "expected_bytes": ZIP_BYTES, "hash_ok": False},
                "exit": "DATA_IDENTITY_MISMATCH", "label_r17": "NULL", "elapsed_sec": time.time() - t0}
    scan_d = scan()
    ev = evaluate(scan_d["total_rows"])
    exit_code, label = exit_of(scan_d, ev, hash_ok)
    return {
        "schema": "m2a.phase25.v1",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "prereg_binding": binding,
        "dataset": {"file": str(ZIP), "member": MEMBER, "sha256": ZIP_SHA, "bytes": ZIP_BYTES,
                    "hash_ok": True, "source": "https://research.zozo.com/data_release/open_bandit_dataset.zip",
                    "split": "first 70% rows train, last 30% test (row order)"},
        "policies": {"s_only": "skip iff position % 3 == 0; no item-value representation",
                     "c_only": "skip iff item training CTR < median of item CTRs (>=100 shows); else take",
                     "skip_reward": 0.0, "take_reward": "logged click"},
        "scan": scan_d, "estimates": ev,
        "criteria": {"C1_delta_s": ev["delta_s"] > 0 and ev["delta_s_ci95"][0] > 0,
                     "C2_independence": abs(ev["s_skip_label_click_rate"] - ev["s_take_label_click_rate"]) <= C2_TOL,
                     "C3_contrast": ev["contrast"] > 0 and ev["contrast_ci95"][0] > 0,
                     "C4_contract": exit_code != "DATA_IDENTITY_MISMATCH"},
        "bootstrap": {"buckets": BUCKETS, "resamples": BOOT, "seed": SEED},
        "exit": exit_code, "label_r17": label,
        "elapsed_sec": time.time() - t0,
        "no_online_intervention": True,
    }


def main() -> int:
    pre = subprocess.run([sys.executable, str(EXP / "p25_gate.py"), "--pre"],
                         capture_output=True, text=True)
    if pre.returncode != 0:
        print("pre-gate refused execution (rc=%d)" % pre.returncode)
        return 4
    doc = build()
    if not doc["prereg_binding"]["two_channel_match"]:
        print("binding MISMATCH - refusing to write")
        return 4
    payload = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        print("check-only digest %s | exit %s (%s) | S %s C %s contrast %s"
              % (sha(payload.encode())[:16], doc["exit"], doc["label_r17"],
                 doc.get("estimates", {}).get("delta_s"), doc.get("estimates", {}).get("delta_c"),
                 doc.get("estimates", {}).get("contrast")))
        return 0
    OUT.write_text(payload, encoding="utf-8")
    ev = doc.get("estimates", {})
    print("wrote %s | exit %s (%s) | S %.6f C %.6f contrast %.6f | rows %s"
          % (OUT.name, doc["exit"], doc["label_r17"], ev.get("delta_s", 0), ev.get("delta_c", 0),
             ev.get("contrast", 0), doc.get("scan", {}).get("total_rows")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
