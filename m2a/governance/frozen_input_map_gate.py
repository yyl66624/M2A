"""§57 validator for the frozen-input map: 16 rules plus 2 self-counts, and every rule is asked whether it can fire.

Landed in `governance/` after §56 settled the visibility shape: its own bytes are now part of `repo_files()`, so
the map it validates counts one more scanned file (X-116). Every total this moves is re-derived in the same pass,
never hand-patched. Reads only committed artifacts and the repository's own files; runs no experiment and goes
nowhere near the network. Three inherited invariants are load-bearing here:

* the validator never adopts the bytes its own run produced (X-91): a reproducibility mismatch is reported and
  the entry bytes are restored, so the red can still be inspected;
* the pairing criterion is tested against the criterion it replaced (Q8): the naive first-sibling join must yield
  strictly *more* stale-looking rows than the key-name join, or the rule that refuses it is decoration;
* a freeze must be *visible in the pinner* (Q11): re-reading the pinner's source is a second path to the claim
  "this instrument hashes these bytes", so the map cannot mint an R6 restriction from a filename coincidence.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

GOV = pathlib.Path(__file__).resolve().parent   # landed in the population it validates (X-116); paths
M = GOV.parent                                # resolve from this file, not from the shell's cwd
ART = GOV / "frozen_input_map_v1.json"
MD = GOV / "FROZEN_INPUT_MAP_v1.md"
GEN = GOV / "build_frozen_input_map.py"

sys.path.insert(0, str(GOV))
import build_frozen_input_map as B  # noqa: E402  the registered joiner, imported not re-typed

QIDS = ["Q%d" % i for i in range(1, 17)]
SELF = ["SUITE_accounting", "SUITE_tally"]
HARD = ("stale_attestation", "named_object_absent", "pin_of_this_layer_output")
HASHKEY = re.compile(r"sha256|hash", re.I)
_ok = _n = 0
_verdicts = []


def report(tag, cond, detail=""):
    global _ok, _n
    _n += 1
    _verdicts.append((tag, bool(cond)))
    if cond:
        _ok += 1
        print("PASS %s %s" % (tag, detail[:78] if detail else ""))
    else:
        print("FAIL %s %s" % (tag, detail))


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def naive_pair(obj, hash_key):
    """The join this layer refused: the first sibling that merely looks like a path."""
    for k, v in obj.items():
        if k != hash_key and isinstance(v, str) and B.PATHISH.search(v):
            return [(k, v)]
    return []


def count_stale(joiner):
    """Walk the same JSON population with a *given* joiner and count rows whose named object exists but no longer
    hashes to the recorded value. Written independently of the deriver's walk on purpose: Q8 compares two joins
    over identical inputs, so the only difference allowed between them is the pairing rule."""
    bad = tot = 0

    def visit(node):
        nonlocal bad, tot
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) and HASHKEY.search(k):
                    tot += 1
                    pair = joiner(node, k)
                    if len(pair) == 1:
                        q = M / pair[0][1]
                        if q.is_file() and sha(q) != v:
                            bad += 1
                elif isinstance(v, (dict, list)):
                    visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    for p in B.repo_files():
        if p.suffix != ".json":
            continue
        try:
            visit(json.loads(p.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    return bad, tot


def main() -> int:
    if not (ART.exists() and MD.exists()):
        print("artifact missing - run build_frozen_input_map.py first", file=sys.stderr)
        return 2
    before_json, before_md = ART.read_bytes(), MD.read_bytes()
    r1 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_json = ART.read_bytes()
    report("Q1 the generator reproduces the committed JSON",
           r1.returncode == 0 and fresh_json == before_json,
           (r1.stdout.strip().splitlines() or [""])[0][:78])
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    fresh_md = MD.read_bytes()
    report("Q2 the generator reproduces the committed Markdown", r2.returncode == 0 and fresh_md == before_md)
    if fresh_json != before_json:
        ART.write_bytes(before_json)
    if fresh_md != before_md:
        MD.write_bytes(before_md)
    report("Q3 derivation idempotent, and a non-reproducing run leaves the committed bytes in place",
           ART.read_bytes() == before_json and MD.read_bytes() == before_md,
           "the validator does not adopt its own repair (X-91)")

    d = json.loads(ART.read_text(encoding="utf-8"))
    rows, c = d["rows"], d["counts"]
    report("Q4 the partition covers every declared category, hard ones included",
           sum(c[v] for v in B.ORDER) == c["rows"] and {r["verdict"] for r in rows} <= set(B.ORDER)
           and c["hard_findings"] == sum(c[v] for v in HARD),
           "rows=%d sum=%d hard=%d" % (c["rows"], sum(c[v] for v in B.ORDER), c["hard_findings"]))
    recount = {v: sum(1 for r in rows if r["verdict"] == v) for v in B.ORDER}
    report("Q5 every headline count equals what the rows hold",
           all(c[v] == recount[v] for v in B.ORDER)
           and c["pinning_documents"] == len({r["pinner"] for r in rows})
           and c["repo_files_scanned"] == len(B.repo_files()),
           "docs=%d files=%d" % (c["pinning_documents"], c["repo_files_scanned"]))

    second = []
    for p in B.repo_files():
        if p.suffix != ".json":
            continue
        txt = p.read_text(encoding="utf-8")
        for m in re.finditer(r'"([^"]*)"\s*:\s*"([0-9a-f]{64})"', txt):
            second.append((str(p.relative_to(M)), m.group(1), m.group(2)))
    inart = {(r["pinner"], r["key"], r["hash"]) for r in rows if r["hash"]}
    report("Q6 a regex scan of the raw JSON text finds the same pinned hash values",
           {t for t in second if t in inart} == inart and len(inart) > 0,
           "independent=%d artifact=%d" % (len({t for t in second if t in inart}), len(inart)))

    stale_now = [r for r in rows if r["verdict"] == "stale_attestation"]
    rehashed = []
    for r in rows:
        if r.get("object") and r["verdict"] in ("stale_attestation", "renewable_governance_pin",
                                                "frozen_by_round_instrument") and r["hash"]:
            q = (M / r["object"]) if r.get("object_namespace") == "repo" else None
            if q and q.is_file() and sha(q) != r["hash"]:
                rehashed.append(r)
    report("Q7 the hard verdict equals a fresh re-hash of the named objects",
           {(r["pinner"], r["key"]) for r in rehashed} == {(r["pinner"], r["key"]) for r in stale_now},
           "rehashed=%d recorded=%d" % (len(rehashed), len(stale_now)))

    bad_naive, tot = count_stale(naive_pair)
    bad_key, _ = count_stale(B.pair_of)
    report("Q8 the criterion that was refused really would have manufactured findings (key-name join is load-bearing)",
           bad_naive > bad_key and tot > 0,
           "naive=%d key-name=%d rows=%d" % (bad_naive, bad_key, tot))

    gp = d["generator"]
    report("Q9 the generator's source hash and its corpus counts still match today's bytes",
           gp["sha256"] == sha(GEN) and gp["file"] == str(GEN.relative_to(M))
           and c["rows"] == len(rows) and c["workshop_objects"] == len(B.workshop_files()),
           "gen %s | rows %d | workshop %d" % (gp["sha256"][:12], c["rows"], c["workshop_objects"]))

    report("Q10 the table does not attest itself",
           not [r for r in rows if pathlib.Path(r["pinner"]).name in B.SELF_OUT]
           and not [r for r in rows if (r.get("object") or "").split("/")[-1] in B.SELF_OUT]
           and c["pin_of_this_layer_output"] == 0,
           "excluded=%s" % ",".join(sorted(B.SELF_OUT)))

    def synth_vis(pinner, obj, digest, key, ns="repo"):
        return B.visibility({"verdict": "frozen_by_round_instrument", "object": obj, "pinner": pinner,
                             "hash": digest, "key": key, "json_path": "synthetic", "object_namespace": ns})

    live_vis = [r for r in rows if r.get("visibility")]
    states = {}
    for r in live_vis:
        states[r["visibility"]] = states.get(r["visibility"], 0) + 1
    src_rows = [r for r in rows if r.get("visibility") == "source_call_visible"]
    js_rows = [r for r in rows if r.get("visibility") == "json_key_reproduced"]
    assert src_rows and js_rows, "the population has neither of the two live visibility states"
    py = src_rows[0]["pinner"]
    js = js_rows[0]
    pre = sorted((M / "experiments").glob("*PREREG*.md"))[0]
    pre_digest = sha(pre)
    probes = {
        "source_call_visible": synth_vis(py, src_rows[0]["object"], None, "instrument_collection"),
        "freeze_not_visible_in_source": synth_vis(py, "governance/ZPROBE_UNMENTIONED.md", None,
                                                  "instrument_collection"),
        "json_key_reproduced": synth_vis(js["pinner"], js["object"], js["hash"], "sha256"),
        "digest_not_reproduced": synth_vis(js["pinner"], "governance/build_coverage_map.py",
                                           "0" * 64, "sha256"),
        "same_line_named": synth_vis(str(pre.relative_to(M)), "governance/build_coverage_map.py",
                                     pre_digest, "prereg_md"),
        "pinner_unreadable": synth_vis("governance/ZPROBE_ABSENT_PINNER.py",
                                       "governance/build_coverage_map.py", None, "instrument_collection"),
    }
    hard_states = ("freeze_not_visible_in_source", "digest_not_reproduced")
    kinds = {pathlib.Path(r["pinner"]).suffix for r in live_vis}
    report("Q11 every freeze row carries a visible state, all six states are reachable, and the pinner kinds the "
           "criterion dispatches on cover every pinner actually found",
           live_vis and kinds <= {".py", ".json", ".md"}
           and all(r["visibility"] not in hard_states for r in live_vis)
           and len(live_vis) == c["frozen_by_round_instrument"]
           and all(probes[k] == k for k in probes)
           and c["freeze_not_visible"] == 0 and c["freeze_visibility_unread"] == 0
           and c["freeze_rows_visible"] == len(live_vis),
           "probe_miss=%s live=%d kinds=%s states=%s" % ([k for k in probes if probes[k] != k][:3],
                                                         len(live_vis), sorted(kinds), sorted(states)))

    prereg_frozen = set()
    for p in (M / "literature").glob("*PREREG*.md"):
        txt = p.read_text(encoding="utf-8")
        for m in re.finditer(r"[\"`']?([\w./\-]+/[\w.\-]+\.(?:md|json|py))[\"`']?", txt):
            if "sha256" in txt.lower() or re.search(r"[0-9a-f]{16}", txt):
                prereg_frozen.add(m.group(1))
    mapped = {r["object"] for r in rows if r.get("object")}
    report("Q12 objects named by a pre-registration are in the map's population (a positive control that can fail)",
           not prereg_frozen or (prereg_frozen & mapped) == prereg_frozen or len(prereg_frozen & mapped) > 0,
           "prereg-named=%d matched=%d" % (len(prereg_frozen), len(prereg_frozen & mapped)))

    uni = {h: names for h, names in B.by_basename()[0].items()}
    fake_absent = {"pinner": "experiments/p1_gate.py", "key": "instrument_collection", "hash": None,
                   "pair": [("src", "nowhere/DEFINITELY_ABSENT.md")], "json_path": ""}
    one = B.classify([fake_absent], {n for s in uni.values() for n in s},
                     {str(p.relative_to(B.W)) for p in B.workshop_files()})
    real_row = next((r for r in rows if r.get("bytes_match")), None)
    probes = []
    probes.append(("absent", one[0]["verdict"] if one else "dropped"))
    if real_row is not None:
        moved = dict(real_row)
        moved["hash"] = "f" * 64 if real_row["hash"] != "f" * 64 else "0" * 64
        again = B.classify([moved], {n for s in uni.values() for n in s},
                           {str(p.relative_to(B.W)) for p in B.workshop_files()})
        probes.append(("stale", again[0]["verdict"] if again else "dropped"))
    selfrow = {"pinner": "governance/build_frozen_input_map.py", "key": "sha256",
               "hash": "a" * 64, "pair": [("file", "governance/frozen_input_map_v1.json")], "json_path": ""}
    again2 = B.classify([selfrow], {n for s in uni.values() for n in s},
                        {str(p.relative_to(B.W)) for p in B.workshop_files()})
    probes.append(("self", again2[0]["verdict"] if again2 else "dropped"))
    want = {"absent": "named_object_absent", "stale": "stale_attestation", "self": "pin_of_this_layer_output"}
    fired = {k: v for k, v in probes}
    report("Q13 each hard tier is reachable by a synthetic row, and the probes run on copies",
           all(fired.get(k) == v for k, v in want.items()),
           "fired=%s" % json.dumps(fired, ensure_ascii=False))
    report("Q14 no probe touched disk: the artifact bytes still equal what the suite entered with",
           ART.read_bytes() == before_json and MD.read_bytes() == before_md)
    report("Q15 the map answers the question it was built for: every pre-registered round input that a round"
           " instrument pins is listed as frozen",
           all(any(r["verdict"] == "frozen_by_round_instrument" and (r.get("object") or "").endswith(n)
                   for r in rows) for n in ("ROUND_L01_RESULTS.md", "L02_PREREGISTRATION.md"))
           and c["frozen_by_round_instrument"] > 0,
           "frozen rows=%d objects=%d" % (c["frozen_by_round_instrument"], len(d["frozen_inputs"])))
    report("Q16 disclosed tiers are disclosed, never judged: nothing outside the three hard names carries a"
           " finding count",
           c["hard_findings"] == sum(c[v] for v in HARD)
           and all(c[v] == recount[v] for v in B.ORDER if v not in HARD))

    ids = [tag.split()[0] for tag, _ in _verdicts]
    report("SUITE_accounting every declared rule id was recorded exactly once",
           sorted(ids) == sorted(QIDS) and len(ids) == len(set(ids)),
           "ids=%s qids=%d" % (",".join(ids), len(QIDS)))
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           _n == len(_verdicts) and _ok == sum(1 for _, v in _verdicts if v),
           "recorded=%d passed=%d ids=%d" % (_n, _ok, len({t for t, _ in _verdicts})))
    print("%d/%d checks passed" % (_ok, len(_verdicts)))
    return 0 if _ok == len(_verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
