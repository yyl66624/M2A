"""M2A Phase I' discovery via OpenAlex, filtered to real articles with abstracts.

Why not Crossref alone: the first expansion pass returned book chapters, peer-review records
("Review for ..."), decision letters and supporting-information components (DOIs ending .s001) for
exactly the three families that need strengthening. Those cannot carry mechanism annotations. OpenAlex
allows filtering to type:article with an abstract, sorting by citation count, and returning the abstract
itself, which is what a K/L/D-B annotation needs.

Raw hits are UNVERIFIED and non-citable; verification is a separate Crossref step.

Usage: python discovery_openalex.py -> expansion_openalex.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
API = "https://api.openalex.org/works"
UA = {"User-Agent": "M2A-PhaseIprime-discovery/1.0 (mailto:none)"}
SEL = ("id,doi,title,publication_year,primary_location,cited_by_count,type,"
       "abstract_inverted_index,authorships")

QUERIES = {
    "K4": {
        "multisensory": "multisensory integration optimal combination cues",
        "coincidence": "coincidence detection AND logic molecular circuit",
        "joint_action": "joint action synergy interpersonal coordination",
        "quorum": "quorum sensing collective decision threshold bacteria",
    },
    "K10": {
        "task_set": "task set reconfiguration cognitive control switching",
        "team_role": "team role adaptation reassignment performance",
        "alternation": "argument structure alternation verb diathesis",
        "reprogramming": "cell fate reprogramming transcription factor identity",
    },
    "K9": {
        "ion_selectivity": "ion channel selectivity filter molecular mechanism",
        "enzyme_specificity": "enzyme substrate specificity active site selectivity",
        "molecular_recognition": "molecular recognition selective binding discrimination",
    },
}


def abstract_text(inv) -> str:
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))[:700]


def search(text: str, per_page: int = 6) -> list:
    params = {
        "search": text,
        "filter": "type:article,has_abstract:true",
        "sort": "cited_by_count:desc",
        "per-page": str(per_page),
        "select": SEL,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["results"]


def main() -> int:
    out = {"schema": "m2a.phase1prime.openalex.v1",
           "note": "raw OpenAlex hits, UNVERIFIED and not citable", "families": {}}
    for fam, qs in QUERIES.items():
        out["families"][fam] = {}
        print(f"\n######## {fam}")
        for name, text in qs.items():
            try:
                items = search(text)
            except Exception as e:  # noqa: BLE001
                out["families"][fam][name] = {"query": text, "error": str(e)}
                print(f"== {name} -> FAILED {e}")
                continue
            hits = []
            for it in items:
                doi = (it.get("doi") or "").replace("https://doi.org/", "")
                venue = ((it.get("primary_location") or {}).get("source") or {}).get("display_name")
                au = it.get("authorships") or []
                hits.append({
                    "doi": doi,
                    "title": it.get("title"),
                    "year": it.get("publication_year"),
                    "venue": venue,
                    "first_author": (au[0]["author"]["display_name"] if au else None),
                    "cited_by": it.get("cited_by_count"),
                    "abstract": abstract_text(it.get("abstract_inverted_index")),
                })
            out["families"][fam][name] = {"query": text, "hits": hits}
            print(f"== {name}: {text}")
            for h in hits:
                print(f"   {h['year']} | {h['first_author']} | {str(h['title'])[:70]} | "
                      f"{str(h['venue'])[:24]} | c={h['cited_by']} | {h['doi']}")
            time.sleep(0.6)
    with open("expansion_openalex.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwrote expansion_openalex.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
