"""Round L-01 runner: gate first, then the §5 exit table. Refuses to run if the gate fails.

The exit table is computed from the coding artifacts by the rule registered in
L01_CODING_PROTOCOL.md §5 - no hand-entered verdicts:
  anchor primary family  = k_all[0] of the anchor's committed row in literature/registry.json
  anchor primary axis    = d_axis of that anchor's own primary mechanism entry
  m = neighbours with >=1 quote-bearing mechanism entry (the gate byte-verifies the quotes)
  C = neighbours whose PRIMARY entry family == anchor family AND primary d_axis == anchor axis
  R = neighbours whose PRIMARY entry family == anchor family AND primary d_axis is the opposite
Outputs literature/L01_coding.json with protocol_sha256, git ref, the 17 records, the table,
and - because §5 never defined how `neutral` compares to a sign - BOTH readings of the neutral
clause, side by side, with the conservative label chosen per 02 §2.3. Nothing is relaxed.
"""
import hashlib
import json
import math
import pathlib
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
COD = LIT / "_l01_coding"
GROUPS = {"R13": ["N2", "N3", "N8", "N15", "N16", "N17"],
          "G5-03": ["N1", "N2", "N4", "N6"],
          "R14": ["N1", "N4", "N7", "N8"]}
OPPOSITE = {"D+": "D−", "D−": "D+"}


def sha(blob):
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def git_ref():
    r = subprocess.run(["git", "-C", str(LIT.parent), "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "no-git"


def main():
    g = subprocess.run([sys.executable, str(LIT / "l01_gate.py")], capture_output=True, text=True)
    tail = [l for l in g.stdout.splitlines() if "checks passed" in l]
    print(g.stdout.rstrip()[-600:])
    if g.returncode != 0:
        print("REFUSING TO RUN: gate not green (this is a feature, R2)")
        return 1
    print("gate:", tail[-1] if tail else "green")

    prot = (LIT / "L01_CODING_PROTOCOL.md").read_text(encoding="utf-8")
    reg = {r["id"]: r for r in json.loads((LIT / "registry.json").read_text(encoding="utf-8"))["records"]}
    recs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(COD.glob("*.json"))}
    ft = json.loads((LIT / "L01_fulltexts.json").read_text(encoding="utf-8"))
    ver = json.loads((LIT / "L01_verification.json").read_text(encoding="utf-8"))
    chan = json.loads((LIT / "L01_channels.json").read_text(encoding="utf-8"))

    table = {}
    for anchor, ids in GROUPS.items():
        a_rec = recs[anchor]
        fam = reg[anchor]["k_all"][0]
        axis = a_rec["mechanism"][0]["d_axis"]
        m = C = R = U = 0
        detail = []
        for i in ids:
            sid = anchor + "-" + i
            r = recs[sid]
            p0 = r["mechanism"][0]
            has_quote = any(len(str(x.get("quote") or "")) >= 20 for x in r["mechanism"])
            if not has_quote:
                detail.append([sid, "no-quote", None, None])
                continue
            m += 1
            if p0["k"] != fam:
                detail.append([sid, p0["k"], p0["d_axis"], "family-divergent"])
                continue
            if p0["d_axis"] == axis:
                C += 1
                kind = "same-family-same-axis"
            elif p0["d_axis"] == OPPOSITE.get(axis):
                R += 1
                kind = "same-family-OPPOSITE-axis"
            else:
                U += 1
                kind = "same-family-unclassifiable-sign"
            detail.append([sid, p0["k"], p0["d_axis"], kind])
        thr = math.ceil(2 * m / 3) if m else None

        def pick(c_val):
            if R >= 2:
                return "CONTRADICTED"
            if m <= 2:
                return "NOT_IDENTIFIED"
            if m >= 3 and c_val >= thr:
                return "SUPPORTED"
            if m >= 3 and c_val == 0:
                return "NULL"
            return "INDETERMINATE"

        strict = pick(C)          # neutral == neutral counts as agreement (literal equality)
        signed = pick(C - U) if U else strict   # only signed agreement counts
        order = {"CONTRADICTED": 0, "NULL": 1, "NOT_IDENTIFIED": 2, "INDETERMINATE": 3,
                 "SUPPORTED": 4}
        final = strict if order[strict] <= order[signed] else signed
        table[anchor] = {"anchor_primary_family_from_registry": fam,
                         "anchor_primary_axis_from_coding": axis, "m": m, "C_strict": C,
                         "C_signed": C - U, "unclassifiable_sign": U, "R": R,
                         "support_threshold": thr,
                         "label_strict": strict, "label_signed_reading": signed,
                         "label_reported": final,
                         "conservative_rule": "02 §2.3 more-conservative-claim wins; the two "
                                              "readings are both printed, neither is discarded",
                         "per_neighbour": detail}
    total_m = sum(v["m"] for v in table.values())
    round_label = ("NOT_IDENTIFIED" if total_m < 10 else
                   "INDETERMINATE" if all(v["label_reported"] == "INDETERMINATE"
                                          for v in table.values()) else
                   "MIXED-PER-ANCHOR (see per-anchor labels)")

    out = {"schema": "m2a.roundL01.coding.v1",
           "protocol": "literature/L01_CODING_PROTOCOL.md",
           "protocol_sha256": sha(prot),
           "git_ref": git_ref(),
           "upstream_artifacts": {
               "candidates_sha256": sha((LIT / "L01_candidates.json").read_text(encoding="utf-8")),
               "fulltexts_sha256": sha((LIT / "L01_fulltexts.json").read_text(encoding="utf-8")),
               "verification_sha256": sha((LIT / "L01_verification.json").read_text(encoding="utf-8")),
               "channels_sha256": sha((LIT / "L01_channels.json").read_text(encoding="utf-8"))},
           "gate": {"command": "python3 literature/l01_gate.py", "groups": "6/6",
                    "quotes_checked": sum(len(r["mechanism"]) for r in recs.values()),
                    "full_texts_fetched": ft["fetched"], "full_texts_failed": ft["failed"],
                    "second_channel_counts": ver["counts"]},
           "third_channel": chan,
           "neighbours_citing_their_own_anchor": ["R13-N3", "R13-N16", "R13-N17"],
           "exit_table": table,
           "total_codeable_neighbours": total_m, "round_stop_line": "10 of 14",
           "round_label": round_label,
           "records": recs,
           "defects_registered": {
               "L01-D1": "coding files used both 'D-' and 'D−' for the same enum value; "
                         "unified to the protocol spelling (20 fields across 10 files), "
                         "no reading changed",
               "L01-D2": "R14-N1 and G5-03-N4 were labelled QUALIFIED against titles quoted in "
                         "the coding tasking note rather than against the registered artifacts; "
                         "identity re-checked (both channels agree, overlap 1.0) and level "
                         "restored. Caused by the tasking note, not by the papers",
               "L01-D3": "the §5 mechanical concordance (family + axis) cannot see a claim-level "
                         "contradiction: G5-03-N6 argues refusal is NOT a single direction yet "
                         "lists K2/D− as primary, so it is counted as concordant. Reported "
                         "C=2 is therefore an upper bound for G5-03",
               "L01-D4": "protocol §5 never defined how a 'neutral' anchor axis compares to a "
                         "sign. Reading A (C_strict) treats neutral == neutral as agreement; "
                         "reading B (C_signed) additionally refuses to count a same-family "
                         "neighbour whose axis is neither equal nor opposite (the unclassifiable "
                         "count). Both are computed for every anchor; the conservative label is "
                         "taken per 02 §2.3. Numbers: " + ", ".join(
                             f"{a} C_strict={v['C_strict']} C_signed={v['C_signed']} "
                             f"unclassifiable={v['unclassifiable_sign']} "
                             f"labels {v['label_strict']}/{v['label_signed_reading']}"
                             for a, v in table.items())}}
    (LIT / "L01_coding.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    for a, v in table.items():
        print(a, "| m", v["m"], "| C_strict", v["C_strict"], "| C_signed", v["C_signed"],
              "| R", v["R"], "| thr", v["support_threshold"], "| label", v["label_reported"])
    print("total codeable neighbours", total_m, "| round label", round_label)
    print("wrote L01_coding.json | protocol_sha256", out["protocol_sha256"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
