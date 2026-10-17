"""M2A Phase I' discovery via Europe PMC (relevance-ranked, abstracts included).

OpenAlex with a citation sort returned mega-cited general papers; Crossref alone returned book chapters
and supporting-information fragments. The three weak families live mostly in the life sciences
(costimulation AND logic, multisensory conjunction, task-set reconfiguration, ion-channel selectivity,
enzyme specificity), where Europe PMC's relevance ranking plus abstract text is the right instrument.

Raw hits are UNVERIFIED and non-citable; verification is a separate Crossref step.

Usage: python discovery_epmc.py -> expansion_epmc.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
UA = {"User-Agent": "M2A-PhaseIprime-discovery/1.0 (mailto:none)"}

QUERIES = {
    "K4": {
        "costimulation": 'TITLE_ABS:"costimulation" AND TITLE_ABS:"T cell" AND '
                         '(TITLE_ABS:"synergy" OR TITLE_ABS:"cooperat")',
        "multisensory": 'TITLE_ABS:"multisensory integration" AND TITLE_ABS:"optimal"',
        "coincidence": 'TITLE_ABS:"coincidence detection" AND TITLE_ABS:"neuron"',
    },
    "K10": {
        "task_switching": 'TITLE_ABS:"task switching" AND TITLE_ABS:"reconfiguration"',
        "cell_fate": 'TITLE_ABS:"cell fate" AND TITLE_ABS:"reprogramming" AND '
                     'TITLE_ABS:"transcription factor"',
    },
    "K9": {
        "selectivity_filter": 'TITLE_ABS:"selectivity filter" AND TITLE_ABS:"potassium channel"',
        "enzyme_specificity": 'TITLE_ABS:"substrate specificity" AND TITLE_ABS:"enzyme" AND '
                              'TITLE_ABS:"mechanism"',
    },
}


def search(query: str, page_size: int = 8) -> list:
    params = {"query": query, "format": "json", "resultType": "core",
              "pageSize": str(page_size), "sort": "CITED desc"}
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["resultList"]["result"]


def main() -> int:
    out = {"schema": "m2a.phase1prime.epmc.v1",
           "note": "raw Europe PMC hits, UNVERIFIED and not citable", "families": {}}
    for fam, qs in QUERIES.items():
        out["families"][fam] = {}
        print(f"\n######## {fam}")
        for name, q in qs.items():
            try:
                items = search(q)
            except Exception as e:  # noqa: BLE001
                out["families"][fam][name] = {"query": q, "error": str(e)}
                print(f"== {name} -> FAILED {e}")
                continue
            hits = []
            for it in items:
                hits.append({
                    "doi": it.get("doi"),
                    "pmid": it.get("pmid"),
                    "title": it.get("title"),
                    "year": it.get("pubYear"),
                    "venue": it.get("journalTitle"),
                    "first_author": it.get("authorString", "").split(",")[0] or None,
                    "cited_by": it.get("citedByCount"),
                    "abstract": (it.get("abstractText") or "")[:500],
                })
            out["families"][fam][name] = {"query": q, "hits": hits}
            print(f"== {name}")
            for h in hits:
                print(f"   {h['year']} | {h['first_author']} | {str(h['title'])[:70]} | "
                      f"{str(h['venue'])[:26]} | c={h['cited_by']} | {h['doi']}")
            time.sleep(0.6)
    with open("expansion_epmc.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwrote expansion_epmc.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
