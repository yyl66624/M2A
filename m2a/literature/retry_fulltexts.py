"""Second pass for the open-access records whose first fetch failed.

Each entry lists explicit alternative routes (Europe PMC XML by PMC id, PMC PDF, publisher PDF, arXiv,
OpenAlex OA locations). Success or failure is written into fulltext_manifest.json; failures are what the
review log reports as unobtainable, with the routes tried.
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
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36")}

ALT = {
    "G8-07": ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2814061/fullTextXML"],
    "X-K4-01": ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2191554/fullTextXML"],
    "X-K4-03": ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3398428/fullTextXML"],
    "R10": ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11598642/fullTextXML"],
    "X-K9-05": ["https://www.jbc.org/article/S0021-9258(19)83072-7/pdf",
                "https://www.jbc.org/article/S0021-9258(20)X0000-0/pdf"],
    "R18": ["https://www.cell.com/trends/ecology-evolution/pdf/S0169-5347(19)30037-4.pdf"],
    "G8-06": ["https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1145/2629489%22&format=json"],
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def to_text(blob: bytes) -> str:
    if blob[:4] == b"%PDF":
        (OUT / "_tmp2.pdf").write_bytes(blob)
        reader = pypdf.PdfReader(str(OUT / "_tmp2.pdf"))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    txt = blob.decode("utf-8", errors="replace")
    if "<" in txt[:2000]:
        txt = re.sub(r"<script.*?</script>", " ", txt, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"[ \t]+", " ", txt)


def main() -> int:
    man = json.load(open("fulltext_manifest.json", encoding="utf-8"))
    for rid, urls in ALT.items():
        txt_path = OUT / f"{rid}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 5000:
            print(f"{rid:8s} already present")
            continue
        ok = False
        tried = []
        for url in urls:
            tried.append(url)
            try:
                text = to_text(fetch(url))
            except Exception as e:  # noqa: BLE001
                print(f"{rid:8s} fail {str(e)[:50]} <- {url[:60]}")
                continue
            if len(text) < 5000:
                print(f"{rid:8s} short {len(text)} <- {url[:60]}")
                continue
            txt_path.write_text(text, encoding="utf-8")
            man["records"][rid] = {"status": "fetched", "chars": len(text), "source": url}
            print(f"{rid:8s} OK {len(text)} <- {url[:60]}")
            ok = True
            break
        if not ok:
            man["records"][rid] = {"status": "failed", "tried": tried}
        time.sleep(0.7)
    json.dump(man, open("fulltext_manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    done = sum(1 for r in man["records"].values() if r["status"] in ("fetched", "cached"))
    print(f"\nfetched/cached now: {done}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
