"""M2A Phase I' discovery: fill the three weakest cells of the Phase I map.

Phase I's own gap list names them: K4 synergy (3/8 clusters), K10 role reassignment (2/8), and K9
omission with zero coverage in physics/chemistry (the source of the project's most novel working
hypothesis). This pass only decides WHAT IS WORTH VERIFYING: Crossref bibliographic hits are raw,
unverified and non-citable, exactly as in the ims-research protocol.

Usage: python discovery_expansion.py -> expansion_candidates.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = {"User-Agent": "M2A-PhaseIprime-discovery/1.0 (mailto:none)"}
SEL = "DOI,title,issued,container-title,author,type,is-referenced-by-count"

QUERIES = {
    "K4_synergy": {
        "multisensory_conjunction": "multisensory integration conjunction cues Bayesian optimal",
        "and_gate_circuit": "AND gate genetic circuit coincidence detector synthetic biology",
        "joint_action": "joint action coordination two-person motor synergy",
        "quorum_synergy": "quorum sensing synergy collective decision threshold",
    },
    "K10_role_reassignment": {
        "task_switching": "task switching cognitive control reconfiguration role",
        "team_roles": "role reassignment team adaptation organizational",
        "argument_alternation": "diathesis alternation argument structure verb role",
        "cell_fate": "cell fate reprogramming transcription factor role switch",
    },
    "K9_physics_chem": {
        "bandpass": "band-pass filter selective frequency response non-response",
        "ion_channel": "ion channel selectivity filter mechanism",
        "catalyst": "catalyst substrate specificity selectivity mechanism",
    },
}


def query(text: str, rows: int = 6) -> list:
    url = (f"https://api.crossref.org/works?rows={rows}&select={SEL}"
           f"&query.bibliographic={urllib.parse.quote(text)}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)["message"]["items"]


def main() -> int:
    out = {"schema": "m2a.phase1prime.discovery.v1",
           "note": "raw Crossref hits, UNVERIFIED and not citable",
           "families": {}}
    for fam, qs in QUERIES.items():
        out["families"][fam] = {}
        print(f"\n######## {fam}")
        for name, text in qs.items():
            try:
                items = query(text)
            except Exception as e:  # noqa: BLE001
                out["families"][fam][name] = {"query": text, "error": str(e)}
                print(f"== {name} -> FAILED {e}")
                continue
            hits = [{"doi": it.get("DOI"),
                     "title": (it.get("title") or [""])[0],
                     "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
                     "venue": (it.get("container-title") or [""])[0],
                     "first_author": ((it.get("author") or [{}])[0].get("family")),
                     "type": it.get("type"),
                     "cited_by": it.get("is-referenced-by-count")} for it in items]
            out["families"][fam][name] = {"query": text, "hits": hits}
            print(f"== {name}: {text}")
            for h in hits:
                print(f"   {h['year']} | {h['first_author']} | {h['title'][:74]} | "
                      f"{h['venue'][:26]} | c={h['cited_by']} | {h['doi']}")
            time.sleep(0.8)
    with open("expansion_candidates.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwrote expansion_candidates.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
