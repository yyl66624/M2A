"""Three extra Europe PMC queries to reach six verified sources per weak family."""
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "M2A-PhaseIprime/1.0 (mailto:none)"}

Q = {
    "K4_extra": 'TITLE_ABS:"coincidence detector" AND TITLE_ABS:"cortex"',
    "K10_extra": 'TITLE_ABS:"team" AND TITLE_ABS:"role" AND TITLE_ABS:"adaptation"',
    "K9_extra": 'TITLE_ABS:"substrate specificity" AND TITLE_ABS:"active site"',
}

for name, q in Q.items():
    params = {"query": q, "format": "json", "resultType": "core",
              "pageSize": "8", "sort": "CITED desc"}
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode(params))
    try:
        res = json.load(urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=60))["resultList"]["result"]
        print(f"== {name}")
        for r in res:
            print(f"   {r.get('pubYear')} | {(r.get('authorString') or '').split(',')[0]} | "
                  f"{str(r.get('title'))[:70]} | c={r.get('citedByCount')} | {r.get('doi')}")
    except Exception as e:  # noqa: BLE001
        print(name, "FAILED", e)
