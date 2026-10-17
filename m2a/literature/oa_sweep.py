"""M2A Phase I' gate 2: find open-access copies for every DOI-bearing record.

Phase I has ZERO full-text reviews. This sweep asks Unpaywall, per record, whether an OA copy exists
and where, and writes oa_index.json. It changes no verification level: fetching and reading is a
separate step (fetch_fulltexts.py), and only after actually inspecting the text may a record be listed
as FULLTEXT_REVIEWED in the review log.

Usage: python oa_sweep.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "M2A-PhaseIprime-oa/1.0 (mailto:none)"}


def unpaywall(doi: str) -> dict:
    url = (f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}"
           f"?email=m2a@example.org")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())


def main() -> int:
    reg = json.load(open("registry.json", encoding="utf-8"))["records"]
    out = {"schema": "m2a.phase1prime.oa_index.v1", "records": {}}
    n_doi = n_oa = 0
    for rec in reg:
        doi = rec.get("doi")
        if not doi:
            continue
        n_doi += 1
        try:
            d = unpaywall(doi)
            best = d.get("best_oa_location") or {}
            entry = {
                "id": rec["id"], "doi": doi, "is_oa": bool(d.get("is_oa")),
                "oa_status": d.get("oa_status"),
                "pdf_url": best.get("url_for_pdf"),
                "landing_url": best.get("url"),
                "host": best.get("host_type"),
                "all_urls": [loc.get("url_for_pdf") or loc.get("url")
                             for loc in (d.get("oa_locations") or [])][:4],
            }
            if entry["is_oa"]:
                n_oa += 1
        except Exception as e:  # noqa: BLE001
            entry = {"id": rec["id"], "doi": doi, "error": str(e)}
        out["records"][rec["id"]] = entry
        print(f"{rec['id']:7s} {doi:34s} OA={entry.get('is_oa')} "
              f"{entry.get('oa_status')} {entry.get('pdf_url') or entry.get('landing_url') or ''}")
        time.sleep(0.4)
    out["counts"] = {"with_doi": n_doi, "oa": n_oa}
    json.dump(out, open("oa_index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nwith DOI {n_doi}, open access {n_oa}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
