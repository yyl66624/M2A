"""Fetch the ACL Anthology full texts (freely available, no DOI required)."""
import pathlib
import re
import sys
import time
import urllib.request

import pypdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = pathlib.Path(r"E:\workshop\_m2a_ft")
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36")}

TARGETS = {
    "R01": "https://aclanthology.org/P98-1013.pdf",
    "R02": "https://aclanthology.org/W13-2322.pdf",
    "G8-03": "https://aclanthology.org/L16-1262.pdf",
    "G8-04": "https://aclanthology.org/L04-1011.pdf",
    "G8-08": "https://aclanthology.org/P08-1090.pdf",
}

for rid, url in TARGETS.items():
    p = OUT / f"{rid}.txt"
    if p.exists() and p.stat().st_size > 5000:
        print(f"{rid:7s} cached")
        continue
    try:
        blob = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        if blob[:4] != b"%PDF":
            print(f"{rid:7s} not a PDF ({len(blob)})")
            continue
        (OUT / "_acl.pdf").write_bytes(blob)
        text = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(OUT / "_acl.pdf")).pages)
        if len(text) < 5000:
            print(f"{rid:7s} short {len(text)}")
            continue
        p.write_text(text, encoding="utf-8")
        print(f"{rid:7s} OK {len(text)}")
    except Exception as e:  # noqa: BLE001
        print(f"{rid:7s} FAILED {str(e)[:60]}")
    time.sleep(0.6)
