"""Round L-01 step 3: independent verification (second channel) + the registered competing theory.

Two things this closes:
  * decision 4 asks for 独立核验, i.e. each record confirmed through a channel other than the one
    that selected it. Selection ran on OpenAlex, so the check here is Crossref DOI lookup for
    records that have a DOI, and PMID/Crossref-container lookup otherwise, with the same identity
    rule as Phase I' 2.2 (title token overlap >= 0.85 and year match). A record that fails the
    second channel is reported as UNVERIFIED_SECOND_CHANNEL, not quietly dropped.
  * the repo already registers Wollschlager et al. 2025 ("concept cones") as the criticism of the
    single-direction refusal claim (07_CONTRADICTIONS, G5-03 annotation). A citation-rank pool does
    not guarantee the rival account is present, so it is fetched explicitly and labelled
    "competing-theory channel (amendment L01-A1)" rather than mixed into the ranked pool.

Writes literature/L01_verification.json.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

LIT = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "M2A-research/1.0 (personal scholarly use; contact: repository owner)"}
THRESH = 0.85


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def norm(t):
    return set(re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).split())


def overlap(a, b):
    ta, tb = norm(a), norm(b)
    return 0.0 if not ta or not tb else len(ta & tb) / len(ta | tb)


def crossref(doi):
    return get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]


def pmid_lookup(pmid):
    d = get_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="
                 + str(pmid))
    r = d.get("result", {}).get(str(pmid), {})
    return {"title": r.get("title"), "year": (r.get("pubdate") or "")[:4]}


def verify(records):
    out = {}
    for sid, r in records.items():
        if r.get("channel") == "FAILED":
            continue
        doi = (r.get("doi") or "").replace("https://doi.org/", "")
        row = {"title": r.get("title"), "year": r.get("year"), "first_channel": "openalex"}
        try:
            if doi:
                m = crossref(doi)
                t2 = (m.get("title") or [""])[0]
                y2 = ((m.get("published", {}) or {}).get("date-parts", [[None]])[0][0])
                row.update({"second_channel": "crossref", "doi": doi, "second_title": t2[:120],
                            "overlap": round(overlap(r.get("title"), t2), 4), "second_year": y2})
                row["verdict"] = ("VERIFIED_TWO_CHANNEL" if row["overlap"] >= THRESH
                                  and str(y2) == str(r.get("year"))[:4]
                                  else "SECOND_CHANNEL_MISMATCH")
            elif r.get("pmid"):
                m = pmid_lookup(r["pmid"])
                row.update({"second_channel": "pubmed", "second_title": (m["title"] or "")[:120],
                            "overlap": round(overlap(r.get("title"), m["title"]), 4),
                            "second_year": m["year"]})
                row["verdict"] = ("VERIFIED_TWO_CHANNEL" if row["overlap"] >= THRESH
                                  and str(m["year"])[:4] == str(r.get("year"))[:4]
                                  else "SECOND_CHANNEL_MISMATCH")
            else:
                row.update({"second_channel": None, "overlap": None,
                            "verdict": "UNVERIFIED_SECOND_CHANNEL(no doi, no pmid)"})
        except Exception as exc:  # noqa: BLE001 - a dead channel is a finding, not a crash
            row.update({"second_channel": "crossref/pubmed", "verdict": "SECOND_CHANNEL_ERROR",
                        "error": type(exc).__name__ + ": " + str(exc)[:90]})
        out[sid] = row
        time.sleep(0.3)
        print(sid, "|", row["verdict"], "| overlap", row.get("overlap"))
    return out


def anchors_via_pmid_or_crossref(cand):
    """The three anchors carry DOIs in the registry; verify them through Crossref directly."""
    doi_map = {"R13": "10.1038/s41586-025-08828-z", "R14": "10.1038/s41593-026-02206-2",
               "G5-03": "10.48550/arXiv.2406.11717"}
    rows = {}
    for k, doi in doi_map.items():
        want = cand["anchors"][k]["identity"]["resolved_title"]
        try:
            m = crossref(doi)
            t2 = (m.get("title") or [""])[0]
            y2 = ((m.get("published", {}) or {}).get("date-parts", [[None]])[0][0])
            rows[k] = {"title": want, "second_channel": "crossref", "doi": doi,
                       "second_title": t2[:140], "overlap": round(overlap(want, t2), 4),
                       "second_year": y2,
                       "verdict": "VERIFIED_TWO_CHANNEL" if overlap(want, t2) >= THRESH else
                                  "SECOND_CHANNEL_MISMATCH"}
        except Exception as exc:  # noqa: BLE001
            rows[k] = {"title": want, "second_channel": "crossref", "doi": doi,
                       "verdict": "SECOND_CHANNEL_ERROR",
                       "error": type(exc).__name__ + ": " + str(exc)[:90]}
        print("anchor", k, rows[k]["verdict"], rows[k].get("overlap"))
        time.sleep(0.3)
    return rows


def competing_theory():
    """Fetch the registered criticism of the single-direction claim through OpenAlex + OA url."""
    q = urllib.parse.quote("Concept Cones: Mechanistic Interpretability in Multiple "
                           "Representations through Geometrical Reasoning")
    try:
        d = get_json("https://api.openalex.org/works?filter=title.search:" + q + "&per-page=5")
    except Exception as exc:  # noqa: BLE001
        return {"found": False, "error": type(exc).__name__ + ": " + str(exc)[:90]}
    best = None
    for w in d.get("results", []):
        if overlap(w.get("title"), "Concept Cones Mechanistic Interpretability Multiple "
                                   "Representations Geometrical Reasoning") >= THRESH:
            best = w
            break
    if best is None:
        return {"found": False, "tried": [w.get("title") for w in d.get("results", [])][:5]}
    loc = best.get("best_oa_location") or {}
    return {"found": True, "title": best.get("title"), "year": best.get("publication_year"),
            "doi": best.get("doi"), "openalex": best["id"], "cited_by": best.get("cited_by_count"),
            "oa_url": loc.get("pdf_url") or loc.get("landing_page_url"),
            "relation": "registered criticism of G5-03 single-direction claim "
                        "(07_CONTRADICTIONS_AND_COUNTEREVIDENCE / G5-03 annotation)"}


def main():
    ft = json.loads((LIT / "L01_fulltexts.json").read_text(encoding="utf-8"))
    cand = json.loads((LIT / "L01_candidates.json").read_text(encoding="utf-8"))
    neigh = {}
    for blob in cand["anchors"].values():
        for c in (blob.get("ranked_pool") or blob["selected"]):
            neigh[c["id"]] = c
    recs = {}
    for sid, v in ft["records"].items():
        if v.get("channel") == "FAILED" or v["role"] == "anchor":
            continue
        src = neigh.get(v.get("openalex_id") or "", {})
        recs[sid] = dict(v)
        if not recs[sid].get("doi"):
            recs[sid]["doi"] = (src.get("doi") or "").replace("https://doi.org/", "") or None
        recs[sid]["pmid"] = src.get("pmid")
    verified = verify(recs)
    verified.update(anchors_via_pmid_or_crossref(cand))
    ct = competing_theory()
    out = {"schema": "m2a.roundL01.verification.v1",
           "identity_rule": "title token overlap >= " + str(THRESH) + " and year match "
                            "(Phase I' 2.2), checked through a channel other than the one that "
                            "selected the record",
           "records": verified,
           "competing_theory_channel_L01_A1": ct,
           "counts": {"total": len(verified),
                      "two_channel": sum(1 for v in verified.values()
                                         if v["verdict"] == "VERIFIED_TWO_CHANNEL"),
                      "mismatch": sum(1 for v in verified.values()
                                      if v["verdict"] in ("SECOND_CHANNEL_MISMATCH",
                                                          "SECOND_CHANNEL_ERROR")),
                      "no_second_channel": sum(1 for v in verified.values()
                                               if str(v["verdict"]).startswith("UNVERIFIED"))}}
    (LIT / "L01_verification.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    print("counts", out["counts"], "| competing theory found:", ct.get("found"))
    print(json.dumps(ct, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
