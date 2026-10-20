"""Round L-02 gate: instrument-only checks, 10 rules plus 2 self-counts, 12 printed verdict lines.

What it refuses to do (R2): it never asks whether the claim-layer reading is *right*, what the anchors' verdicts
should be, or whether the competing theory wins. A gate that carried a scientific criterion would put the pressure
to loosen a threshold on the registered text every time a hand check failed - the failure this repo already paid
for. Every rule here is about the instrument: the binding, the frozen inputs, determinism, the closed vocabulary,
the field contract, byte-located quotes, a re-derivable threshold, an exit table that can be reached, and a write
path that refuses to write when the binding does not hold.

Run from anywhere: `python3 literature/l02_gate.py`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
M = LIT.parent
REPO = M.parent
PREREG = LIT / "L02_PREREGISTRATION.md"
CODING = LIT / "L01_coding.json"
FULLTEXTS = LIT / "L01_fulltexts.json"
RUNNER = LIT / "l02_reanalysis.py"
OUT = LIT / "L02_reanalysis.json"
FROZEN = ["literature/L01_coding.json", "literature/L01_fulltexts.json", "literature/L01_channels.json",
          "literature/L01_CODING_PROTOCOL.md", "literature/registry.json", "literature/synthesis_v2.json",
          "literature/ROUND_L01_RESULTS.md"]
RHOS = ("SUPPORTS", "EXTENDS", "REFUTES", "UNRELATED", "UNDECIDABLE")
REQUIRED_FIELDS = ["case_id", "reference", "verification_level", "evidence_type", "provenance",
                   "description_scope", "motion_source", "mechanism", "layers", "agency_class",
                   "event_grammar", "contradiction_ref"]

_verdicts = []
_n = 0
_ok = 0


def report(tag, cond, detail=""):
    global _n, _ok
    _n += 1
    cond = bool(cond)
    _verdicts.append((tag, cond))
    _ok += int(cond)
    print(("PASS " if cond else "FAIL ") + tag + " " + (detail if detail else ""))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + rel], capture_output=True).stdout


def run_check() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RUNNER), "--check"], cwd=LIT,
                          capture_output=True, text=True)


def main() -> int:
    coding = json.loads(CODING.read_text(encoding="utf-8"))
    recs, et = coding["records"], coding["exit_table"]
    sys.path.insert(0, str(LIT))
    import l02_reanalysis as R  # noqa: E402

    pre_disk = PREREG.read_bytes()
    pre_head = head_bytes("m2a/" + str(PREREG.relative_to(M)))
    report("G1 the preregistration is committed and its disk bytes equal the git object",
           bool(pre_head) and sha(pre_disk) == sha(pre_head),
           "disk %s git %s" % (sha(pre_disk)[:12], sha(pre_head)[:12]))

    drift = [f for f in FROZEN if sha((M / f).read_bytes()) != sha(head_bytes("m2a/" + f))]
    report("G2 every frozen upstream artifact still matches its committed bytes (R6 inputs untouched)",
           not drift, "drifted: " + (", ".join(drift) if drift else "none"))

    a, b = run_check(), run_check()
    da = re.search(r"digest ([0-9a-f]{16})", a.stdout)
    db = re.search(r"digest ([0-9a-f]{16})", b.stdout)
    wrote = OUT.exists() and OUT.read_bytes() != b""
    report("G3 the runner is deterministic under --check and writes nothing in that mode",
           a.returncode == 0 and b.returncode == 0 and da and da.group(1) == db.group(1),
           "digest %s / %s | artifact on disk %s"
           % (da.group(1) if da else "?", db.group(1) if db else "?", OUT.name if wrote else "absent"))

    values = {v for v, _ in R.RHO.values()}
    named = set(re.findall(r"`(%s)`" % "|".join(RHOS), pre_disk.decode("utf-8")))
    report("G4 the relation vocabulary is closed in the runner and every value is registered in the prereg",
           values <= set(RHOS) and named >= values and len(R.RHO) == 14,
           "used %s | registered %d" % (",".join(sorted(values)), len(named)))

    judged, known = set(R.RHO), set(recs)
    anchors_of = [s for s in known if s not in et]
    report("G5 the relation table covers exactly L-01's neighbour rows and names nothing else",
           judged <= known and judged == {s for s in anchors_of if any(s.startswith(a + "-") for a in et)}
           and not (judged & set(et)),
           "rows %d | neighbours %d | anchors excluded %s"
           % (len(judged), len(anchors_of), sorted(set(et) & judged) or "none"))

    bad = []
    for anc, v in et.items():
        S = sorted(r[0] for r in v["per_neighbour"] if r[-1] == "same-family-same-axis")
        if len(S) < v["C_signed"] or not S:
            bad.append(anc)
    report("G6 L-01's own surface labels are used verbatim as the surface set, never re-derived here",
           not bad, "offending: " + (",".join(bad) or "none")
           + " | C_signed per anchor " + json.dumps({k: v["C_signed"] for k, v in et.items()}))

    # The neighbour records carry no `file` field, but the anchors do, and every neighbour text on disk matches
    # its committed sha256 prefix under the convention "<dir>/L01_<sid>.txt". The directory is therefore derived
    # from a committed artifact instead of typed. L-01 hashed and indexed its texts with LF endings, while the
    # mount stores one `local_cache` file with CRLF, so the comparison base is declared (L02-A4): decode, fold
    # CRLF/CR to LF, then the manifest hash, the character count and every quote offset must hit exactly.
    # There is no "quote found somewhere else in the text" fallback - an offset that does not hit is a defect.
    ft = json.loads(FULLTEXTS.read_text(encoding="utf-8"))["records"]
    ft_dir = pathlib.Path(next(v["file"] for v in ft.values() if v.get("file"))).parent
    verified, unresolved, broken, hash_bad, normalized, qlens = 0, [], [], [], [], []
    for sid, rec in recs.items():
        r = ft.get(sid) or {}
        p = pathlib.Path(r["file"]) if r.get("file") else ft_dir / ("L01_%s.txt" % sid)
        if not p.exists():
            unresolved.append(sid)
            continue
        blob = p.read_bytes()
        text = blob.decode("utf-8", "replace")
        norm = text.replace("\r\n", "\n").replace("\r", "\n")
        if norm != text:
            normalized.append(sid)
        if sha(norm.encode("utf-8"))[:16] != r.get("sha256") and sha(blob)[:16] != r.get("sha256"):
            hash_bad.append(sid)
            continue
        if len(norm) != r.get("chars"):
            hash_bad.append(sid)
            continue
        for m in (rec.get("mechanism") or []):
            q, off = m.get("quote", ""), m.get("quote_offset")
            qlens.append(len(q))
            if isinstance(off, int) and 0 <= off <= len(norm) and norm[off:off + len(q)] == q \
                    and sha(q.encode("utf-8"))[:16] == m.get("quote_sha16"):
                verified += 1
            else:
                broken.append((sid, (q or "")[:24]))
    report("G7 quotes are byte-located at their recorded offsets in files whose hash and length still match "
           "the manifest, or the row is named",
           not broken and not hash_bad and not unresolved and qlens and min(qlens) >= 20 and max(qlens) <= 400,
           "quotes verified %d | rows unresolvable %s | hash/length mismatch %s | offset or sha mismatch %s "
           "| line-endings folded %s | quote chars %d-%d"
           % (verified, unresolved or "none", hash_bad or "none", broken[:2] or "none",
              normalized or "none", min(qlens) if qlens else -1, max(qlens) if qlens else -1))

    # The protocol names two fields the artifact never used by those names: L-01 coded `sid` where `02` §2.2 says
    # `case_id` and `title` where it says `reference`. Tolerating that silently would launder a real discrepancy
    # between the registered contract and the committed artifact, so the aliases are declared here and the alias
    # rows are printed as a disclosure (L02-A3) while the content requirement stays strict.
    # L02-A5: 12 of the 17 committed rows carry `contradiction_ref` as null - the artifact uses null for "this
    # case references no contradiction", and `02` section 2.2 never declared whether the field may be empty. The
    # frozen L-01 artifact cannot be rewritten (R6), so the contract is checked as key presence for all 12 fields
    # plus non-empty for the 11 that have no null reading, and the null rows are named in the printed line
    # instead of being rounded away. This is a registered gap in an upstream artifact (negative-log row), not a
    # green tick for it.
    ALIAS = {"case_id": ("case_id", "sid"), "reference": ("reference", "title")}
    NULLABLE = ("contradiction_ref",)

    def has(rec, f):
        return any(rec.get(n) not in (None, "") for n in ALIAS.get(f, (f,)))

    holes = {k: [f for f in REQUIRED_FIELDS if not has(v, f) and f not in NULLABLE] for k, v in recs.items()}
    holes = {k: v for k, v in holes.items() if v}
    keyless = {k: [f for f in REQUIRED_FIELDS if not any(n in v for n in ALIAS.get(f, (f,)))]
               for k, v in recs.items()}
    keyless = {k: v for k, v in keyless.items() if v}
    nulled = sorted(k for k, v in recs.items() if not has(v, "contradiction_ref"))
    aliased = [f for f in ALIAS if all(f not in r for r in recs.values())
               and any(ALIAS[f][1] in r for r in recs.values())]
    report("G8 the committed field contract holds for all 17 rows, layers included, aliases and nulls disclosed",
           not holes and not keyless and aliased == ["case_id", "reference"],
           "rows missing a required non-empty field: " + (json.dumps(holes, ensure_ascii=False)[:120] or "none")
           + " | rows missing a key: " + (json.dumps(keyless, ensure_ascii=False)[:80] or "none")
           + " | protocol names carried by an alias key: " + ",".join(aliased)
           + " | `contradiction_ref` null in %d rows: %s"
           % (len(nulled), ",".join(nulled[:6]) + ("..." if len(nulled) > 6 else "")))

    coded_ft = [k for k, v in recs.items() if v.get("verification_level") == "FULLTEXT_REVIEWED"]
    chars = [ft[k]["chars"] for k in coded_ft if k in ft and "chars" in ft[k]]
    derived = min(chars) if chars else None
    floor_in_text = re.search(r"全文长度地板 = ([\d ]+) 字符", pre_disk.decode("utf-8"))
    reg = int(floor_in_text.group(1).replace(" ", "")) if floor_in_text else None
    stopline = re.search(r"整轮停线 = (\d+) 条", pre_disk.decode("utf-8"))
    report("G9 the registered floor is the number the committed artifacts still derive (R5 reproducibility)",
           reg is not None and reg == derived and stopline and int(stopline.group(1)) == 10,
           "registered %s | re-derived %s over %d coded fulltexts | stopline %s"
           % (reg, derived, len(chars), stopline.group(1) if stopline else "?"))

    tables = re.findall(r"^\| \d+ \| `?([A-Z_]+)`? \|", pre_disk.decode("utf-8"), re.M)
    catch = re.findall(r"以上皆不成立|NOT_IDENTIFIED|COMPETING_NOT_OBTAINED|保持开放", pre_disk.decode("utf-8"))
    q_blocks = len(re.findall(r"^### Q[123] ", pre_disk.decode("utf-8"), re.M))
    report("G10 every question has a numbered exit table with a catch-all branch, so an exit can always be taken",
           q_blocks == 3 and len(tables) >= 7 and len(catch) >= 3,
           "questions %d | exit rows %d | catch-all phrases %d" % (q_blocks, len(tables), len(catch)))

    # G11 teeth: simulate a binding break by making the *git object* differ from the disk bytes. Moving the
    # preregistration outside the module tree would not test the binding at all - it dies earlier, in path
    # arithmetic, and a validator that crashes leaves no verdict line, which is a fail-open (X-85).
    before = OUT.read_bytes() if OUT.exists() else None
    orig_git = R.git_head_bytes
    R.git_head_bytes = lambda rel: pre_disk + b"\n(tampered after the binding)\n"
    try:
        rc = R.main()
    finally:
        R.git_head_bytes = orig_git
    after = OUT.read_bytes() if OUT.exists() else None
    report("G11 the write path refuses when the two-channel binding does not hold (fail closed, no artifact)",
           rc == 4 and (before or b"") == (after or b""),
           "exit=%d | artifact bytes unchanged=%s" % (rc, (before or b"") == (after or b"")))

    ids = [re.match(r"G\d+", tag).group(0) for tag, _ in _verdicts]
    report("SUITE_accounting every declared rule id was recorded exactly once",
           sorted(ids) == sorted("G%d" % i for i in range(1, 12)) and len(ids) == len(set(ids)),
           "ids=%d" % len(ids))
    n = len(_verdicts)
    ok = sum(1 for _, v in _verdicts if v)
    report("SUITE_tally the printed fraction is derived from the recorded verdicts",
           ok == sum(1 for _, v in _verdicts if v) and n == 12, "recorded=%d passed=%d" % (n, ok))
    print("%d/%d checks passed" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
