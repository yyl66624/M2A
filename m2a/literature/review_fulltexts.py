"""Inspect the fetched full texts against their annotations.

For each record with a text file, count family-specific vocabulary matches and extract the sentence with
the strongest match, so the reviewer can check whether the paper actually carries the mechanism claim
rather than trusting the abstract. Writes fulltext_review.json; the human-readable verdicts go into
fulltext_review_log.md (written by hand from these snippets).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FT = pathlib.Path(r"E:\workshop\_m2a_ft")

VOCAB = {
    "K1": ["trigger", "threshold", "evoke", "elicits", "activate"],
    "K2": ["inhibit", "gate", "suppress", "block", "checkpoint"],
    "K3": ["compet", "conflict", "rival"],
    "K4": ["synerg", "conjunction", "coincide", "combination", "integrat"],
    "K5": ["delay", "memory", "trace", "interval", "temporal"],
    "K6": ["feedback", "prediction error", "reinforc", "learning"],
    "K7": ["bistab", "hysteresis", "switch", "transition"],
    "K8": ["cascade", "spread", "diffusion", "propagat", "contagion"],
    "K9": ["omit", "omission", "abstain", "skip", "withhold", "non-response", "selectivity"],
    "K10": ["role", "reassign", "reconfigur", "task switch", "identity"],
    "K11": ["capacity", "resource", "constraint", "cost", "budget"],
    "K12": ["select", "adapt", "evolution", "fitness"],
}


def sentences(text: str):
    return re.split(r"(?<=[.!?])\s+", text)


def main() -> int:
    reg = {r["id"]: r for r in json.load(open("registry.json", encoding="utf-8"))["records"]}
    out = {"schema": "m2a.phase1prime.fulltext_review.v1", "records": {}}
    for rid, rec in reg.items():
        p = FT / f"{rid}.txt"
        if not p.exists() or p.stat().st_size < 5000:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        fams = rec.get("k_all") or []
        counts = {}
        best = ("", None, 0)
        for fam in fams:
            terms = VOCAB.get(fam, [])
            c = sum(low.count(t) for t in terms)
            counts[fam] = c
            for s in sentences(text):
                sl = s.lower()
                score = sum(sl.count(t) for t in terms)
                if score > best[2]:
                    best = (s.strip()[:300], fam, score)
        out["records"][rid] = {
            "chars": len(text), "families": fams, "counts": counts,
            "best_family": best[1], "best_score": best[2], "snippet": best[0],
        }
        print(f"{rid:8s} {len(text):7d} chars | " +
              " ".join(f"{k}:{v}" for k, v in counts.items()) + f" | best {best[1]}={best[2]}")
    json.dump(out, open("fulltext_review.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nreviewed {len(out['records'])} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
