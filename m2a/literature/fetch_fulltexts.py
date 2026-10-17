"""Fetch the open-access full texts found by oa_sweep.py (stored OUTSIDE the repository).

Third-party full texts are read locally and never committed: E:\\workshop\\_m2a_ft. Each record gets a
.txt and the manifest records which URL worked, how many characters were extracted, and any failure.
Only after review_fulltexts.py inspects the text may a record be listed as FULLTEXT_REVIEWED.

Usage: python fetch_fulltexts.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.request

import pypdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = pathlib.Path(r"E:\workshop\_m2a_ft")
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36")}


def fetch(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def pmc_xml_url(*urls):
    for u in urls:
        if not u:
            continue
        m = re.search(r"PMC(\d+)", u, re.I)
        if m:
            return f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{m.group(1)}/fullTextXML"
    return None


def to_text(blob: bytes) -> str:
    if blob[:4] == b"%PDF":
        tmp = OUT / "_tmp.pdf"
        tmp.write_bytes(blob)
        reader = pypdf.PdfReader(str(tmp))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    txt = blob.decode("utf-8", errors="replace")
    if "<" in txt[:2000]:
        txt = re.sub(r"<script.*?</script>", " ", txt, flags=re.S | re.I)
        txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"[ \t]+", " ", txt)


def main() -> int:
    idx = json.load(open("oa_index.json", encoding="utf-8"))["records"]
    manifest = {"schema": "m2a.phase1prime.fulltext_manifest.v1", "records": {}}
    for rid, v in idx.items():
        if not v.get("is_oa"):
            continue
        txt_path = OUT / f"{rid}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 2000:
            manifest["records"][rid] = {"status": "cached", "chars": txt_path.stat().st_size,
                                        "source": "cached"}
            print(f"{rid:8s} cached {txt_path.stat().st_size}")
            continue
        cands = []
        x = pmc_xml_url(v.get("landing_url"), v.get("pdf_url"), *(v.get("all_urls") or []))
        if x:
            cands.append(x)
        for u in [v.get("pdf_url"), *(v.get("all_urls") or []), v.get("landing_url")]:
            if u and u not in cands:
                cands.append(u)
        ok = False
        for url in cands:
            try:
                blob = fetch(url)
                text = to_text(blob)
            except Exception as e:  # noqa: BLE001
                print(f"{rid:8s} try failed: {str(e)[:60]}")
                continue
            if len(text) < 2000:
                print(f"{rid:8s} too short from {url[:50]} ({len(text)})")
                continue
            txt_path.write_text(text, encoding="utf-8")
            manifest["records"][rid] = {"status": "fetched", "chars": len(text), "source": url}
            print(f"{rid:8s} OK {len(text)} chars <- {url[:70]}")
            ok = True
            break
        if not ok:
            manifest["records"][rid] = {"status": "failed", "tried": cands}
            print(f"{rid:8s} FAILED all {len(cands)} candidate URLs")
        time.sleep(0.8)
    json.dump(manifest, open("fulltext_manifest.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    done = sum(1 for r in manifest["records"].values() if r["status"] in ("fetched", "cached"))
    print(f"\nfetched/cached: {done} of {sum(1 for v in idx.values() if v.get('is_oa'))} OA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
