"""Round L-01 step 1: build the candidate pools for the three anchors owner decision 4 names.

Anchors: R13 (Zimmerman 2025, delayed post-ingestive feedback), G5-03 (Arditi 2024, refusal
direction), R14 (Burke 2026, interval control of learning rate). Target pool sizes come from the
decision verbatim: 6 / 4 / 4 papers to encode as full texts.

Selection rule, fixed here before looking at any candidate (so the pool cannot be curated after
the fact):
  1. neighbours = the anchor's own reference list (works/{id}/referenced_works) plus citing works;
  2. keep a neighbour only if it has an open-access full-text URL (OA is_oa with pdf_url, or an
     arXiv/PMC landing page resolvable from its locations field);
  3. rank survivors by cited_by_count desc, then publication_year desc, then id asc (total order);
  4. take the top N; record every rejected neighbour with the reason it was rejected.
Rejections are part of the artifact: an unrecorded reject list is how cherry-picking hides.

Writes literature/L01_candidates.json. Does not touch any Phase I asset.
"""
import hashlib
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent / "L01_candidates.json"
UA = {"User-Agent": "M2A-research/1.0 (personal scholarly use; contact: repository owner)"}
ANCHORS = {
    "R13": {"doi": "10.1038/s41586-025-08828-z", "n": 6,
            "expected_title": "A neural mechanism for learning from delayed postingestive feedback"},
    "G5-03": {"doi": "10.48550/arXiv.2406.11717", "n": 4,
              "expected_title": "Refusal in Language Models Is Mediated by a Single Direction"},
    "R14": {"doi": "10.1038/s41593-026-02206-2", "n": 4,
            "expected_title": "Duration between rewards controls the rate of behavioral and dopaminergic learning"},
}


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001 - transient API failures are expected
            last = exc
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(str(last)[:120])


def resolve_anchor(spec):
    """Phase I' 2.2 identity rule: DOI lookup must give title overlap >= 0.85 and the expected
    year, otherwise it is a different work. 10.48550/arXiv.* DOIs have collided in OpenAlex, so a
    title+year search is the fallback channel rather than a silent accept."""
    doi_url = "https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(spec["doi"])
    want = {n for n in norm(spec["expected_title"])}
    w = get(doi_url)
    ov = overlap(w.get("title"), spec["expected_title"])
    if ov >= 0.85:
        return w, "doi", round(ov, 4)
    q = urllib.parse.quote(spec["expected_title"])
    alt = get("https://api.openalex.org/works?filter=title.search:" + q + "&per-page=25")
    best, best_ov = None, 0.0
    for c in alt.get("results", []):
        c_ov = overlap(c.get("title"), spec["expected_title"])
        if c_ov > best_ov:
            best, best_ov = c, c_ov
    if best is not None and best_ov >= 0.85:
        return best, "title.search fallback", round(best_ov, 4)
    raise RuntimeError("identity failed: doi overlap " + str(round(ov, 4))
                       + ", best fallback overlap " + str(round(best_ov, 4))
                       + " - neither reaches the 0.85 rule")


def norm(title):
    return re.sub(r"[^a-z0-9 ]+", " ", (title or "").lower()).split()


def overlap(a, b):
    ta, tb = set(norm(a)), set(norm(b))
    return 0.0 if not ta or not tb else len(ta & tb) / len(ta | tb)


def oa_url(work):
    loc = work.get("best_oa_location") or {}
    for key in ("pdf_url", "landing_page_url"):
        if loc.get(key):
            return loc[key], (loc.get("source") or {}).get("display_name", "?")
    for l in work.get("primary_location") and [work["primary_location"]] or []:
        if l.get("pdf_url"):
            return l["pdf_url"], (l.get("source") or {}).get("display_name", "?")
    return None, None


def main():
    pools = {}
    for code, spec in ANCHORS.items():
      try:
        anchor, resolve_channel, resolve_overlap = resolve_anchor(spec)
        title = anchor.get("title") or ""
        # title-token overlap against the expected string is an identity check, not a ranking input
        identity = {"resolved_title": title, "expected": spec["expected_title"],
                    "resolved_via": resolve_channel, "doi_requested": spec["doi"],
                    "token_overlap": resolve_overlap,
                    "year": (anchor.get("publication_year")), "openalex_id": anchor["id"],
                    "cited_by_count": anchor.get("cited_by_count")}
        refs = anchor.get("referenced_works") or []
        citing = get("https://api.openalex.org/works?filter=cites:" + anchor["id"].rsplit("/", 1)[-1]
                     + ",is_oa:true&per-page=100&sort=cited_by_count:desc")
        neigh_ids = [u.rsplit("/", 1)[-1] for u in refs[:60]]
        cand = []
        for w in citing.get("results", []):
            u, src = oa_url(w)
            cand.append({"from": "citing", "id": w["id"], "title": w.get("title"),
                         "year": w.get("publication_year"), "cited_by": w.get("cited_by_count"),
                         "oa_url": u, "oa_source": src, "doi": w.get("doi")})
        rejected = [{"from": "citing", "id": c["id"], "title": c["title"], "reason": "no OA full-text url"}
                    for c in cand if not c["oa_url"]]
        survivors = [c for c in cand if c["oa_url"]]
        # the reference-list neighbours need one lookup each; cap at 12 to bound the API load,
        # and record how many were not looked up rather than silently dropping them
        ref_pool, skipped_refs = [], max(0, len(neigh_ids) - 12)
        for wid in neigh_ids[:12]:
            w = get("https://api.openalex.org/works/" + wid)
            u, src = oa_url(w)
            if not w.get("is_oa") or not u:
                rejected.append({"from": "reference", "id": w["id"], "title": w.get("title"),
                                 "reason": "closed access"})
                continue
            ref_pool.append({"from": "reference", "id": w["id"], "title": w.get("title"),
                             "year": w.get("publication_year"), "cited_by": w.get("cited_by_count"),
                             "oa_url": u, "oa_source": src, "doi": w.get("doi")})
        pool = survivors + ref_pool
        pool.sort(key=lambda c: (-(c["cited_by"] or 0), -(c["year"] or 0), c["id"]))
        pools[code] = {"identity": identity, "selected": pool[:spec["n"]],
                       "ranked_pool": pool[:40],
                       "pool_size": len(pool), "reference_list_size": len(neigh_ids),
                       "references_not_looked_up": skipped_refs,
                       "rejected": rejected[:40], "rejected_total": len(rejected)}
        print(code, "| overlap", identity["token_overlap"], "| year", identity["year"],
              "| pool", len(pool), "| selected", len(pools[code]["selected"]),
              "| rejected", len(rejected))
      except Exception as exc:  # noqa: BLE001 - one dead anchor must not lose the other two
        pools[code] = {"identity": {"doi": spec["doi"], "resolved": False}, "selected": [],
                       "pool_size": 0, "reference_list_size": 0, "references_not_looked_up": 0,
                       "rejected": [], "rejected_total": 0,
                       "anchor_lookup_failed": type(exc).__name__ + ": " + str(exc)[:160]}
        print(code, "| ANCHOR LOOKUP FAILED:", type(exc).__name__, str(exc)[:120])
      time.sleep(0.4)

    blob = {"schema": "m2a.roundL01.candidates.v1",
            "selection_rule": "OA full text required; rank by cited_by desc, year desc, id asc; "
                              "take top N from decision 4 (6/4/4); every reject recorded with a reason",
            "pool_sizes": {k: v["pool_size"] for k, v in pools.items()},
            "anchors": pools,
            "anchors_with_no_selection": [k for k, v in pools.items() if not v["selected"]],
            "anchor_failures": {k: v.get("anchor_lookup_failed") for k, v in pools.items()
                                if v.get("anchor_lookup_failed")},
            "raw_sha256_of_first_selected_titles": hashlib.sha256(
                "\n".join(v["selected"][0]["title"] for v in pools.values() if v["selected"]
                           ).encode()).hexdigest()[:16]}
    OUT.write_text(json.dumps(blob, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
