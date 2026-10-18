"""Round L-01 step 2: fetch the full texts chosen by discover_L01.py and build evidence digests.

Channels, in priority order (PDF extraction is unavailable in this environment - pypdf and friends
are not installed - so a PDF-only source is recorded as unavailable with its HTTP-level reason
rather than silently skipped, exactly as Phase I' did for its 7 closed-access records):
  local cache  ->  arXiv /html  ->  Europe PMC fullTextXML  ->  publisher HTML  ->  fail

Full texts are stored OUTSIDE the repository (workshop/_m2a_ft), following the Phase I' rule that
third-party text is read locally and never committed. Each record keeps: channel used, url, chars,
sha256, and a mechanically derived keyword-window digest - the digest is what the annotation is
written from, so a reviewer can check the coding against the same passage.

Writes literature/L01_fulltexts.json.
"""
import hashlib
import html as htmllib
import json
import pathlib
import re
import urllib.request

LIT = pathlib.Path(__file__).resolve().parent
FT = LIT.parent.parent.parent / "_m2a_ft"          # workshop/_m2a_ft
CAND = json.loads((LIT / "L01_candidates.json").read_text(encoding="utf-8"))
UA = {"User-Agent": "M2A-research/1.0 (personal scholarly use; contact: repository owner)"}

# arXiv ids for the anchors themselves, used when no local cache file exists
ANCHOR_ARXIV = {"G5-03": "2406.11717", "R14": None, "R13": None}

KEYS = {
    "R13": ["delay", "post-ingestive", "postingestive", "habenula", "CGRP", "nausea", "allostasis",
            "taste avoidance", "interval", "eligibility", "interocept", "sucrose", "visceral"],
    "G5-03": ["refusal", "single direction", "ablat", "steering", "probe", "concept cone",
              "emergent misalignment", "fine-tun", "jailbreak", "sparse autoencoder", "direction",
              "generaliz"],
    "R14": ["inter-trial interval", "ITI", "duration between rewards", "learning rate", "dopamin",
            "scaling", "time scale", "eligibility", "policy", "Rescorla", "exponential", "trace"],
}
MIN_CHARS = 4000
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
ENT = re.compile(r"<[^>]+>")


def fetch(url, limit=6_000_000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        blob = r.read(limit)
    low = url.lower()
    if blob[:5] == b"%PDF-" or low.endswith(".pdf"):
        return None, "pdf-only: no text extractor in this environment (pypdf not installed)"
    txt = blob.decode("utf-8", errors="replace")
    if "<html" not in txt.lower() and "{" in txt[:40]:
        return None, "not an HTML/text payload"
    clean = strip(txt)
    if len(clean) < MIN_CHARS:
        return None, "empty payload after stripping (" + str(len(clean)) + " chars < " \
               + str(MIN_CHARS) + "); usually a cookie wall, redirect stub or abstract-only page"
    return clean, "ok"


def strip(raw):
    raw = TAG.sub(" ", raw)
    raw = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>", "\n", raw, flags=re.I)
    txt = htmllib.unescape(ENT.sub(" ", raw))
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


def digest(text, keys, width=340, max_hits=8):
    low = text.lower()
    out, taken = [], set()
    for kw in keys:
        for m in list(re.finditer(re.escape(kw.lower()), low))[:2]:
            lo = max(0, m.start() - 120)
            hi = min(len(text), m.start() + width)
            band = lo // 200
            if band in taken:
                continue
            taken.add(band)
            out.append({"keyword": kw, "window": re.sub(r"\s+", " ", text[lo:hi]).strip()})
            if len(out) >= max_hits:
                return out
    return out


def try_channels(c, anchor):
    url = c["oa_url"] or ""
    tried = []
    # 1. arXiv html
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", url, re.I)
    if m:
        u = "https://arxiv.org/html/" + m.group(1)
        tried.append(u)
        txt, st = fetch_safe(u)
        if st == "ok":
            return txt, "arxiv_html", u
    # 2. Europe PMC fullTextXML by DOI
    doi = (c.get("doi") or "").replace("https://doi.org/", "")
    if doi:
        u = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22"
             + urllib.parse.quote(doi) + "%22&format=json&resultType=core")
        tried.append(u)
        meta, st = fetch_raw_json(u)
        if st == "ok" and meta.get("resultList", {}).get("result"):
            r0 = meta["resultList"]["result"][0]
            if r0.get("pmcid"):
                u2 = ("https://www.ebi.ac.uk/europepmc/webservices/rest/" + r0["pmcid"]
                      + "/fullTextXML")
                tried.append(u2)
                txt, st2 = fetch_safe(u2)
                if st2 == "ok":
                    return txt, "europepmc_fullTextXML", u2
    # 3. the OA url itself (publisher HTML / landing page)
    if url:
        tried.append(url)
        txt, st = fetch_safe(url)
        if st == "ok":
            return txt, "oa_url_direct", url
        tried_note = st
    else:
        tried_note = "no url"
    return None, "failed", tried_note


def fetch_safe(u):
    try:
        return fetch(u)
    except Exception as exc:  # noqa: BLE001 - HTTP 403/404/500 are the finding, not a crash
        return None, type(exc).__name__ + ": " + str(exc)[:80]


def fetch_raw_json(u):
    try:
        req = urllib.request.Request(u, headers=UA)
        return json.loads(urllib.request.urlopen(req, timeout=30).read()), "ok"
    except Exception as exc:  # noqa: BLE001
        return None, type(exc).__name__ + ": " + str(exc)[:80]


import urllib.parse  # noqa: E402  (used inside try_channels; kept late to minimize the diff)

def main():
    FT.mkdir(parents=True, exist_ok=True)
    recs = {}
    for anchor, blob in CAND["anchors"].items():
        keys = KEYS[anchor]
        local = FT / (anchor + ".txt")
        if not local.is_file():
            aid = ANCHOR_ARXIV.get(anchor)
            cand = [{"title": blob["identity"]["resolved_title"], "year": blob["identity"]["year"],
                     "cited_by": blob["identity"]["cited_by_count"], "doi": None,
                     "oa_url": ("https://arxiv.org/abs/" + aid) if aid else None}]
            txt, chan, note = try_channels(cand[0], anchor)
            if txt is None:
                recs[anchor] = {"role": "anchor", "channel": "FAILED", "reason": note,
                                "title": blob["identity"]["resolved_title"]}
                print(anchor, "anchor FAILED", str(note)[:70])
            else:
                path = FT / ("L01_" + anchor + ".txt")
                path.write_text(txt, encoding="utf-8")
                recs[anchor] = {"role": "anchor", "channel": chan, "url": note, "chars": len(txt),
                                "sha256": hashlib.sha256(txt.encode()).hexdigest()[:16],
                                "title": blob["identity"]["resolved_title"],
                                "digest": digest(txt, keys)}
                print(anchor, "anchor via", chan, "chars", len(txt))
        if local.is_file():
            txt = local.read_text(encoding="utf-8", errors="replace")
            recs[anchor] = {"role": "anchor", "channel": "local_cache", "file": str(local),
                            "chars": len(txt), "sha256": hashlib.sha256(txt.encode()).hexdigest()[:16],
                            "title": blob["identity"]["resolved_title"],
                            "digest": digest(txt, keys)[:8]}
            print(anchor, "anchor from local cache, chars", len(txt))
        pool = blob.get("ranked_pool") or blob["selected"]
        target = blob["identity"].get("n", len(blob["selected"]))
        got, i, ptr, skipped = 0, 0, 0, []
        while got < len(blob["selected"]) and ptr < len(pool):
            c = pool[ptr]
            ptr += 1
            i += 1
            sid = anchor + "-N" + str(i)
            txt, chan, note = try_channels(c, anchor)
            if txt is None:
                skipped.append({"rank": ptr, "title": c["title"], "year": c["year"],
                                "reason": note})
                recs[sid] = {"role": "neighbour", "channel": "FAILED", "reason": note,
                             "title": c["title"], "year": c["year"], "oa_url": c["oa_url"]}
                print(sid, "FAILED", str(note)[:70], "- substituting next ranked candidate")
                continue
            got += 1
            path = FT / ("L01_" + sid + ".txt")
            path.write_text(txt, encoding="utf-8")
            low = txt.lower()
            abst = ""
            m = re.search(r"abstract", low)
            if m:
                abst = re.sub(r"\s+", " ", txt[m.start():m.start() + 900])
            recs[sid] = {"role": "neighbour", "channel": chan, "url": note, "chars": len(txt),
                        "sha256": hashlib.sha256(txt.encode()).hexdigest()[:16],
                        "title": c["title"], "year": c["year"], "cited_by": c["cited_by"],
                        "doi": c.get("doi"), "abstract_head": abst[:600],
                        "digest": digest(txt, keys)}
            print(sid, chan, "chars", len(txt), "| windows", len(recs[sid]["digest"]))
        recs[anchor]["substitutions_skipped"] = skipped
        recs[anchor]["full_texts_read"] = got + (1 if recs.get(anchor, {}).get("channel") != "FAILED" else 0)
    out = {"schema": "m2a.roundL01.fulltexts.v2", "records": recs,
           "fetched": sum(1 for v in recs.values() if v["channel"] != "FAILED"),
           "failed": sum(1 for v in recs.values() if v["channel"] == "FAILED"),
           "note": "full texts live outside the repository; only hashes, lengths and keyword "
                   "windows are committed so a coding claim can be traced to the same passage"}
    (LIT / "L01_fulltexts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print("wrote L01_fulltexts.json | fetched", out["fetched"], "failed", out["failed"])


if __name__ == "__main__":
    main()
