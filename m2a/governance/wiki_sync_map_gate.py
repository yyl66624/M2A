"""Validate the wiki sync map: re-derive it, then check each verdict through a second path.

The map's job (see `build_wiki_sync_map.py`) is to make 「每一步写入飞书」 a fact the closing audit can
turn red. This suite therefore has to prove the rules that decide it can fire: S14 drives the decision
function through five drift shapes and then shows the live data produces none of them - an unpublished
section, a claim pointing at a page that is not in the ledger, a governance page no section claims, a
draft edited after publication, and a first batch that grew without registration.

Identifier spaces are kept apart on purpose: claims are page **titles** here, node tokens are only
compared against the ledger (mixing the two is the class of bug X-81 registered).

Checks touch instruments only (R2): no scientific criterion, no round verdict, no publishing.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

M = pathlib.Path(__file__).resolve().parent.parent
W = M.parent.parent
GOV = M / "governance"
GEN = GOV / "build_wiki_sync_map.py"
MAP = GOV / "wiki_sync_map_v1.json"
MD = GOV / "WIKI_SYNC_MAP_v1.md"
LEDGER = W / "feishu_wiki_nodes.json"
DRAFTS = W / "feishu_wiki_drafts"

results = []
tally = {"printed": 0, "printed_pass": 0}


def report(name, passed, detail=""):
    passed = bool(passed)
    results.append((name, passed))
    tally["printed"] += 1
    tally["printed_pass"] += int(passed)
    print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def verdicts(pop, claims, gov_titles, disk_sha, art_sha, first_batch_len, pin):
    """The whole decision surface of the map, as one pure function, so controls can drive it.

    `claims` maps section -> set of page titles that section points at.
    """
    unclaimed = [s for s in pop if s not in claims]
    stale = [s for s in claims if s not in pop]
    claimed = {t for ts in claims.values() for t in ts}
    return {"unclaimed": unclaimed,
            "stale_claims": stale,
            "orphan_pages": sorted(t for t in gov_titles if t not in claimed),
            "sha_drift": sorted(k for k in art_sha if disk_sha.get(k) != art_sha[k]),
            "first_batch_off_pin": first_batch_len - pin}


def main() -> int:
    if not (MAP.exists() and MD.exists()):
        print("artifact missing - run build_wiki_sync_map.py first", file=sys.stderr)
        return 2
    before_json, before_md = MAP.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_json, fresh_md = MAP.read_bytes(), MD.read_bytes()
    report("S1 generator reproduces the committed JSON",
           r1.returncode == 0 and fresh_json == before_json,
           (r1.stdout.strip().splitlines() or [""])[0][:78])
    report("S2 generator reproduces the committed Markdown", fresh_md == before_md)
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    # the generator writes in place, so a mismatch it just printed would otherwise be adopted as its own
    # repair: put the committed bytes back and require them still there at exit (X-91).
    if fresh_json != before_json:
        MAP.write_bytes(before_json)
    if fresh_md != before_md:
        MD.write_bytes(before_md)
    report("S3 derivation idempotent, and a non-reproducing run leaves the committed bytes in place",
           MAP.read_bytes() == before_json and MD.read_bytes() == before_md
           and fresh_json == before_json and r2.returncode == 0)

    d = json.loads(MAP.read_text(encoding="utf-8"))
    rep = (M / "M2A_FINAL_REPORT.md").read_text(encoding="utf-8")

    # S4: population by a different code path - split the file, then read each chunk's heading number
    chunks = [c.split(None, 1)[0] for c in re.split(r"\n#{2,3} ", "\n" + rep)]
    indep = sorted({int(c) for c in chunks if c.isdigit() and int(c) >= d["base_section"]})
    report("S4 section population re-derived by splitting equals the artifact's regex scan",
           indep == sorted(r["section"] for r in d["sections"]),
           "split %d vs artifact %d" % (len(indep), len(d["sections"])))

    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    pages = [p for p in led.get("pages", []) if p.get("node_token")]
    tokens = {p["node_token"] for p in pages}
    titles = {p["page"] for p in pages}

    claims = {}
    for cr in d["claims"]:
        if cr.get("title"):
            claims.setdefault(cr["section"], set()).add(cr["title"])
    pop = [r["section"] for r in d["sections"]]
    gov_titles = {p["title"] for p in d["pages"]}

    claimed_tokens = {cr["node_token"] for cr in d["claims"]} - {None}
    report("S5 every claimed page resolves to a node token that is in the ledger",
           not d["dangling_claims"] and claimed_tokens <= tokens,
           "dangling %d | claim tokens %d | ledger tokens %d"
           % (len(d["dangling_claims"]), len(claimed_tokens), len(tokens)))
    live = verdicts(pop, claims, gov_titles,
                    {p["draft"]: sha(DRAFTS / p["draft"]) for p in d["pages"]},
                    {p["draft"]: p["draft_sha256"] for p in d["pages"]},
                    len(d["first_batch_pages"]), d["first_batch_expected"])
    # the artifact's own headline count must equal what can be enumerated from its rows: on the first
    # build it said 15 claimed while only 14 were listable, because a claim at a first-batch page was
    # dropped from the per-page rows - a self-contradiction no single-path check would have seen.
    report("S6 no section unclaimed, no claim stale, and the claimed count equals the enumerable rows",
           not live["unclaimed"] and not live["stale_claims"] and not d["unclaimed_sections"]
           and not d["stale_claims"] and d["counts"]["sections_claimed"] == len(claims),
           "population %d claims %d count %s unclaimed %s"
           % (len(pop), len(claims), d["counts"]["sections_claimed"], live["unclaimed"]))
    report("S7 every governance page is claimed by >=1 section",
           not live["orphan_pages"] and not d["orphan_pages"] and gov_titles <= titles,
           "orphans %s | governance %d" % (live["orphan_pages"], len(gov_titles)))
    report("S8 first-batch pages match the pin and none of them is in the PAGES manifest",
           live["first_batch_off_pin"] == 0
           and len(d["first_batch_pages"]) == d["first_batch_expected"]
           and not (set(d["first_batch_pages"]) & gov_titles),
           "first_batch %d pin %d" % (len(d["first_batch_pages"]), d["first_batch_expected"]))

    report("S9 draft fingerprints on disk equal the artifact (a rewritten draft goes red)",
           not live["sha_drift"] and None not in
           [sha(DRAFTS / p["draft"]) for p in d["pages"]],
           "%d drafts | drift %s" % (len(d["pages"]), live["sha_drift"]))
    tdisk = {t["file"]: sha(W / t["file"]) for t in d["tools"]}
    tarc = {t["file"]: t["sha256"] for t in d["tools"]}
    report("S10 guard-tool fingerprints on disk equal the artifact",
           tdisk == tarc and None not in tdisk.values(),
           " ".join(sorted(k.split("/")[-1] for k, v in tdisk.items() if v != tarc[k])) or "all match")

    report("S11 ledger page count and parent node read independently equal the artifact",
           len(pages) == d["counts"]["ledger_pages_with_node"]
           and led["parent_node_token"] == d["wiki_parent_node_token"],
           "ledger %d vs artifact %d" % (len(pages), d["counts"]["ledger_pages_with_node"]))
    report("S12 every governance page recorded a successful read-back",
           all(p["markers_ok_recorded"] is True and (p["read_back_chars_recorded"] or 0) > 0
               for p in d["pages"]),
           "not ok: %s" % [p["title"][:20] for p in d["pages"] if not p["markers_ok_recorded"]])

    lg = {int(x) for x in re.findall(r"^\| X-(\d+) \|",
           (GOV / "NEGATIVE_AND_NULL_EVIDENCE_LOG.md").read_text(encoding="utf-8"), re.M)}
    cited = {x for r in d["sections"] for x in r["xids_named"]}
    report("S13 every X-id cited by an in-population section exists in the negative log",
           cited <= lg, "cited %d | missing %s" % (len(cited), sorted(cited - lg)[:6]))

    one_draft = sorted(live["sha_drift"] or [p["draft"] for p in d["pages"]])[0]
    # sentinels are computed, not hard-coded: the first draft used the literal 46 for "a section that
    # was published nowhere", and the moment §46 really existed that control became vacuous - it still
    # "passed" nothing, it just stopped firing. Same family as X-84's counts-vs-rows bug.
    ghost, missing = max(pop) + 2, max(pop) + 1
    assert ghost not in claims and missing not in claims
    ctrl = {
        "section published nowhere": verdicts(pop + [missing], claims, gov_titles, {}, {}, 12, 12)["unclaimed"],
        "claim kept for a section that no longer exists":
            verdicts(pop, {**claims, ghost: {sorted(gov_titles)[0]}}, gov_titles, {}, {}, 12, 12)["stale_claims"],
        "governance page no section claims":
            verdicts(pop, {k: v for k, v in claims.items() if k != pop[-1]}, gov_titles, {}, {}, 12, 12)["orphan_pages"],
        "draft edited after publication":
            verdicts(pop, claims, gov_titles, {one_draft: "0" * 64}, {one_draft: "f" * 64}, 12, 12)["sha_drift"],
        "first batch grew without registration":
            verdicts(pop, claims, gov_titles, {}, {}, 13, 12)["first_batch_off_pin"],
    }
    report("S14 the decision function fires on all five drift shapes and is silent on live data",
           not any([live["unclaimed"], live["stale_claims"], live["orphan_pages"], live["sha_drift"]])
           and live["first_batch_off_pin"] == 0
           and ctrl["section published nowhere"] == [missing]
           and ctrl["claim kept for a section that no longer exists"] == [ghost]
           and len(ctrl["governance page no section claims"]) == 1
           and ctrl["draft edited after publication"] == [one_draft]
           and ctrl["first batch grew without registration"] == 1,
           "live=%s | controls=%s" % ({k: v for k, v in live.items() if v},
                                      {k: bool(v) for k, v in ctrl.items()}))

    names = [n for n, _ in results]
    report("SUITE_accounting", len(names) == len(set(names)) and len(names) >= 14,
           "%d rules, all distinct" % len(names))
    report("SUITE_tally", tally["printed"] == len(results)
           and tally["printed_pass"] == sum(1 for _, p in results if p),
           "lines printed equal rules recorded")
    n_pass = sum(1 for _, p in results if p)
    print("%d/%d checks passed" % (n_pass, len(results)))
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
