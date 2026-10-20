"""Round L-02 Q1+Q2: re-judge L-01's committed coding under the claim-layer criterion.

Zero-test status only (L02_PREREGISTRATION §0): no re-fetch, no re-coding, no edit of any L-01 artifact. The
relation table below is a reading of quotes that are *already committed* in `L01_coding.json`; every entry names
the quote it stands on, and the run aborts if that text is not a byte-exact prefix of a committed quote, so the
judgement is auditable and cannot invent evidence.

`--check` computes and prints digests without writing anything (that is what the gate runs).
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
PREREG = LIT / "L02_PREREGISTRATION.md"
CODING = LIT / "L01_coding.json"
OUT = LIT / "L02_reanalysis.json"

RHO = {
    "G5-03-N1": ("UNRELATED", "finetuning can produce models behaving in a misaligned way"),
    "G5-03-N2": ("UNRELATED", "we can bypass safety mechanisms reliably by changing the context"),
    "G5-03-N4": ("UNRELATED", "The system prefers abstention over confident but unfounded"),
    "G5-03-N6": ("REFUTES", "Contrary to prior assumptions that refusal mechanisms are linear"),
    "R13-N2": ("SUPPORTS", "learned avoidance of the novel flavors despite the delayed mala"),
    "R13-N3": ("UNRELATED", "rather than waiting for an imbalance to occur, the brain predicts"),
    "R13-N8": ("SUPPORTS", "mice tend to associate novel, but not familiar, flavors with delayed"),
    "R13-N15": ("SUPPORTS", "overcomes the credit assignment problem of delayed post-ingestive"),
    "R13-N16": ("EXTENDS", "Co-administration of the GIPR agonist"),
    "R13-N17": ("SUPPORTS", "amygdalar activity heightens when novel foods are paired with"),
    "R14-N1": ("EXTENDS", "Conditioned responding was attenuated for the cue-reward contingency"),
    "R14-N4": ("UNRELATED", "common analysis strategies can reduce the detection of effects"),
    "R14-N7": ("SUPPORTS", "The learning rate\u2014operationally defined as the reciprocal"),
    "R14-N8": ("SUPPORTS", "mesolimbic dopamine ramps are only observed when the inter-trial"),
}
LEVEL_VETO = {"ABSTRACT_VERIFIED", "IDENTITY_VERIFIED"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_head_bytes(rel: str) -> bytes:
    return subprocess.run(["git", "-C", str(M.parent), "show", "HEAD:" + rel],
                          capture_output=True).stdout


def basis_ok(recs: dict) -> list:
    bad = []
    for sid, (_rho, basis) in RHO.items():
        quotes = [m.get("quote", "") for m in (recs[sid].get("mechanism") or [])] if sid in recs else []
        if not any(q.startswith(basis) or basis in q for q in quotes):
            bad.append((sid, basis[:40]))
    return bad


def neutral_only(rec) -> bool:
    ms = rec.get("mechanism") or []
    return bool(ms) and all((m.get("d_axis") == "neutral") for m in ms)


def build() -> dict:
    raw = CODING.read_bytes()
    coding = json.loads(raw.decode("utf-8"))
    recs, et = coding["records"], coding["exit_table"]
    bad = basis_ok(recs)
    if bad:
        print("BASIS NOT BYTE-VERIFIABLE:", bad, file=sys.stderr)
        raise SystemExit(3)
    missing = [s for s in RHO if s not in recs]
    if missing:
        print("RELATION TABLE NAMES UNKNOWN ROWS:", missing, file=sys.stderr)
        raise SystemExit(3)
    # the anchor key can itself contain a dash (G5-03), so grouping matches the registered exit-table keys
    # instead of splitting on the first one.
    anchors = sorted(k for k in et if any(s.startswith(k + "-") for s in RHO))
    orphan = [s for s in RHO if sum(1 for a in anchors if s.startswith(a + "-")) != 1]
    if orphan:
        print("RELATION TABLE ROWS WITHOUT EXACTLY ONE ANCHOR:", orphan, file=sys.stderr)
        raise SystemExit(3)
    per, tot = {}, {"C_surface": 0, "S_rows": 0, "delta": 0, "C_claim": 0, "X": 0, "U": 0, "Z": 0}
    for a in anchors:
        rows = sorted(s for s in RHO if s.startswith(a + "-"))
        # L-01's own surface set is read from its printed per-neighbour relation labels, not re-derived here
        S_rows = sorted(r[0] for r in et[a]["per_neighbour"] if r[-1] == "same-family-same-axis")
        c_claim, x, u, z, sup, neu = 0, 0, 0, 0, [], []
        for s in rows:
            rho = RHO[s][0]
            neutral = neutral_only(recs[s])
            if neutral:
                z += 1
                neu.append(s)
            # prereg §3 Q2: a claim carried only by d_axis=neutral entries is NEUTRAL_UNDECIDABLE and is *not*
            # added to C_claim. Without the exclusion the Z reading would change nothing on this corpus.
            if rho in ("SUPPORTS", "EXTENDS") and not neutral:
                c_claim += 1
                sup.append(s)
            elif rho == "REFUTES":
                x += 1
            elif rho == "UNDECIDABLE":
                u += 1
        inflated = [s for s in S_rows if RHO[s][0] not in ("SUPPORTS", "EXTENDS")]
        # The two registered rules are different estimators and can disagree on one row: Delta asks only about rho,
        # Q2 asks whether the row is claim-eligible. A neutral-only row read as SUPPORTS is counted by neither
        # inflation nor claim, so the disagreement is named instead of being resolved by whichever is convenient.
        both = [s for s in neu if RHO[s][0] in ("SUPPORTS", "EXTENDS")]
        surface = et[a]["C_signed"]
        per[a] = {"m_registered": et[a]["m"], "C_surface": surface, "S_rows": S_rows,
                  "delta": len(inflated), "inflated_rows": inflated,
                  "C_claim_all": c_claim, "claim_supporting_rows": sup,
                  "neutral_undecidable_rows": neu, "rules_disagree_rows": both,
                  "X": x, "U": u, "Z": z,
                  "rows": {s: {"rho": RHO[s][0], "basis": RHO[s][1],
                               "verification_level": recs[s]["verification_level"],
                               "neutral_only": neutral_only(recs[s])} for s in rows}}
        tot["C_surface"] += surface
        tot["S_rows"] += len(S_rows)
        tot["delta"] += len(inflated)
        tot["C_claim"] += c_claim
        tot["X"] += x
        tot["U"] += u
        tot["Z"] += z
    infl = [a for a in anchors if per[a]["delta"] >= 1]
    additive = [a for a in anchors if per[a]["delta"] == 0 and per[a]["X"] >= 1]
    equiv = [a for a in anchors if per[a]["delta"] == 0 and per[a]["X"] == 0 and per[a]["U"] == 0]
    if infl:
        q1, q1_label = "CLAIM_LAYER_INFLATION", "CONTRADICTED"
    elif additive:
        q1, q1_label = "CLAIM_LAYER_ADDITIVE", "NULL"
    elif len(equiv) == len(anchors) and tot["U"] == 0:
        q1, q1_label = "CLAIM_LAYER_EQUIVALENT", "NULL"
    else:
        q1, q1_label = "NOT_IDENTIFIED", "NOT_IDENTIFIED"
    q2 = "NEUTRAL_ZERO_IS_NOT_A_BOUNDARY" if tot["Z"] >= 1 else "NEUTRAL_ZERO_UNEXERCISED"
    q2_label = "CONTRADICTED" if tot["Z"] >= 1 else "NULL"
    return {
        "schema": "m2a.roundL02.reanalysis.v1",
        "question": "does a claim-layer relation field change the consistency counts that family+sign produced",
        "preregistration": str(PREREG.relative_to(M)),
        "prereg_sha256": sha(PREREG.read_bytes()),
        "coding_sha256": sha(raw),
        "status": "ZERO_TEST_REANALYSIS",
        "readings_reused": "no re-fetch, no re-coding, no edit of any L-01 artifact (R6)",
        "relation_vocabulary": ["SUPPORTS", "EXTENDS", "REFUTES", "UNRELATED", "UNDECIDABLE"],
        "derived_thresholds": {
            "neutral_rule": "a row whose mechanism entries are ALL d_axis=neutral is NEUTRAL_UNDECIDABLE "
                            "and excluded from C_claim (prereg §3 Q2, mechanical on the committed field)",
            "stopline_absolute": 10,
            "rows_judged": len(RHO),
        },
        "totals": tot,
        "per_anchor": per,
        "exit_q1": q1, "exit_q1_label_r17": q1_label,
        "exit_q2": q2, "exit_q2_label_r17": q2_label,
        "asymmetry": "delta counts only rows L-01 itself put in S and which the claim layer does not support, "
                     "so a row it never counted cannot cancel an inflated one; C_claim_all is disclosed "
                     "separately and never enters any exit",
        "rows_not_judged": sorted(s for s in recs if s not in RHO),
    }


def main() -> int:
    check_only = "--check" in sys.argv
    doc = build()
    # The binding has to be inside the serialized bytes: computing it after the blob was frozen wrote an artifact
    # that asserted a two-channel match it did not contain (L02-A6).
    disk = sha(PREREG.read_bytes())
    head = sha(git_head_bytes("m2a/literature/L02_PREREGISTRATION.md"))
    doc["prereg_binding"] = {"disk": disk, "git_head": head, "two_channel_match": disk == head}
    blob = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if check_only:
        print("check-only digest", hashlib.sha256(blob).hexdigest()[:16],
              "| rows judged", doc["derived_thresholds"]["rows_judged"],
              "| totals", json.dumps(doc["totals"], ensure_ascii=False),
              "| per-anchor delta", json.dumps({k: v["delta"] for k, v in doc["per_anchor"].items()}),
              "| binding", "match" if disk == head else "MISMATCH")
        return 0
    if disk != head:
        print("PREREG NOT COMMITTED: disk %s git %s" % (disk[:12], head[:12]), file=sys.stderr)
        return 4
    OUT.write_bytes(blob)
    print("wrote L02_reanalysis.json | exit_q1 %s (%s) | exit_q2 %s (%s) | totals %s | per-anchor delta %s"
          % (doc["exit_q1"], doc["exit_q1_label_r17"], doc["exit_q2"], doc["exit_q2_label_r17"],
             json.dumps(doc["totals"], ensure_ascii=False),
             json.dumps({k: v["delta"] for k, v in doc["per_anchor"].items()})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
