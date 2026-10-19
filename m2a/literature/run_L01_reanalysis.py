"""Round L-01 reanalysis (L01-O2 / L01-D3): re-judge consistency under a claim-level relation.

ZERO TEST STATUS. Not a new round, not a confirmation. Everything is recomputed from the readings
already committed in `L01_coding.json`: no re-coding, no fetching, no modification of
`L01_coding.json`, and the round verdict cannot change (R6). The criterion below is stated after
the round ran, hence `registered_before_run: false`.

Why. L01-D3 is a registered defect of the §5 consistency criterion: `C` compared only
「族 + 符号」, so a neighbour that agrees on family and sign while *denying the anchor's actual
claim* still counted as corroboration. G5-03-N6 is exactly that case - K2/D− primary (agreeing
with the anchor), but its claim is that refusal is nonlinear and multidimensional, i.e. that no
single refusal direction exists.

New relation, stated before computing (four-valued, as L01-O2 asks), from committed fields only:

    反证  if contradiction_ref is not null
    支持  elif same_family and same_sign
    扩展  elif same_family                       (= same family, opposite/absent sign)
    无关  else

Registered §5 quantities are reproduced as C = #支持, R_sign = #扩展 (the registered R is defined
by family + opposite `d_axis` + that family listed as primary, which is what 扩展 selects here).
Two variants then feed the **unchanged, ordered** exit table of `L01_CODING_PROTOCOL.md` §5:

    A: R' = #扩展 + #反证    claim-level counter-evidence joins the refutation count
    B: R' = #扩展            claim-level counter-evidence only leaves C (lower bound on harm)

Exit order (verbatim from §5): 1 CONTRADICTED if R' ≥ 2; 2 SUPPORTED if m ≥ 3 and C ≥ ⌈2m/3⌉;
3 NULL if m ≥ 3 and C = 0; 4 INDETERMINATE if 1 ≤ C < ⌈2m/3⌉; 5 NOT_IDENTIFIED if m ≤ 2.
Thresholds and `m` are the committed ones - the reanalysis does not touch them.

Limitation printed into the artifact: `contradiction_ref` is the only machine-readable claim-level
signal in the schema, so #反证 is a **lower bound**; a contradiction never registered in
`07_CONTRADICTIONS_AND_COUNTEREVIDENCE.md` stays counted as 支持. This is why the reanalysis can
show how a label would move but cannot upgrade or overturn anything.
"""
import hashlib
import json
import math
import pathlib

LIT = pathlib.Path(__file__).resolve().parent
SRC = LIT / "L01_coding.json"
RELATIONS = ("支持", "扩展", "反证", "无关", "符号不可判")


def axis_class(rec_axis, anchor_axis):
    """The §5 sign comparison, reconstructed the way the exit table evidently computed it: by
    comparing `d_axis` strings. Kept separate from the record's own `anchor_concordance.same_sign`,
    which turns out to encode something else (see the divergence field)."""
    if rec_axis == anchor_axis:
        return "same"
    if "neutral" in (rec_axis, anchor_axis):
        return "unclassifiable"
    return "opposite"


def relation(rec, anchor_axis):
    """The new claim-level relation (L01-O2), stated before computing. `primary_against_anchor`
    means the neighbour lists the anchor's own family as primary, which is what §5 required of both
    C and R."""
    conc = rec.get("anchor_concordance") or {}
    prim = [m for m in rec["mechanism"] if m.get("role") == "primary"]
    axes = [m.get("d_axis") for m in prim]
    cls = [axis_class(a, anchor_axis) for a in axes]
    fam = bool(conc.get("same_family"))
    if not fam:
        return "无关", cls, fam
    if "same" in cls:
        return ("反证" if rec.get("contradiction_ref") else "支持"), cls, fam
    if "unclassifiable" in cls:
        return ("反证" if rec.get("contradiction_ref") else "符号不可判"), cls, fam
    return "扩展", cls, fam


def exit_label(m, c, r):
    """The registered §5 exit table, applied in its registered order."""
    if r >= 2:
        return "CONTRADICTED"
    if m >= 3 and c >= math.ceil(2 * m / 3):
        return "SUPPORTED"
    if m >= 3 and c == 0:
        return "NULL"
    if 1 <= c < math.ceil(2 * m / 3):
        return "INDETERMINATE"
    return "NOT_IDENTIFIED"


# how conservative each label is about the anchor's claim: a label that asserts less is safer, and
# `INDETERMINATE` asserts nothing, so it wins a tie exactly as 02 §2.3 already ruled for the round
CONSERVATISM = {"SUPPORTED": 0, "NULL": 1, "CONTRADICTED": 2, "NOT_IDENTIFIED": 3,
                "INDETERMINATE": 4}


def conservative(a, b):
    return a if CONSERVATISM[a] >= CONSERVATISM[b] else b


def primary(rec):
    return [[m["k"], m.get("d_axis")] for m in rec["mechanism"] if m.get("role") == "primary"]


def main():
    src = json.loads(SRC.read_text(encoding="utf-8"))
    recs = src["records"]
    out = {
        "schema": "m2a.roundL01.reanalysis.v1",
        "source_artifact": "literature/L01_coding.json",
        "source_protocol": src["protocol"],
        "protocol_sha256_recorded_by_round": src["protocol_sha256"],
        "source_records_sha256": hashlib.sha256(
            json.dumps(recs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16],
        "registered_before_run": False,
        "status": "ZERO_TEST_REANALYSIS",
        "defect_addressed": "L01-D3 (round verdict INDETERMINATE, 14/14 codeable, unchanged here)",
        "criterion": "relation = 反证 if contradiction_ref else 支持 if same_family and same_sign "
                     "else 扩展 if same_family else 无关; A: R'=#扩展+#反证, B: R'=#扩展; C'=#支持; "
                     "the registered ordered exit table of §5 is applied unchanged to (m, C', R')",
        "limitation": "contradiction_ref is the schema's only machine-readable claim-level signal, so "
                      "#反证 is a lower bound: an unregistered contradiction is still counted as 支持. "
                      "Variant B is the conservative bound on how much the defect moved C; variant A "
                      "is what admitting claim-level refutation into R would imply.",
        "round_label_committed": src["round_label"],
        "round_label_after": src["round_label"],
        "verdict_changed": False,
        "anchors": {},
    }

    for anchor, committed in src["exit_table"].items():
        anchor_axis = committed["anchor_primary_axis_from_coding"]
        pool = sorted((r for sid, r in recs.items()
                       if sid != anchor and sid.startswith(anchor + "-")), key=lambda x: x["sid"])
        rows, cnt = [], {k: 0 for k in RELATIONS}
        mech_c = mech_r = mech_u = 0
        divergent = []
        for r in pool:
            rel, cls, fam = relation(r, anchor_axis)
            cnt[rel] += 1
            conc = r.get("anchor_concordance") or {}
            if fam and "same" in cls:
                mech_c += 1
            elif fam and "opposite" in cls:
                mech_r += 1
            elif fam and "unclassifiable" in cls:
                mech_u += 1
            sgn_field = conc.get("same_sign")
            axis_same = "same" in cls
            if sgn_field is not None and bool(sgn_field) != axis_same:
                divergent.append({"sid": r["sid"], "record_same_sign": sgn_field,
                                  "axis_comparison": cls, "contradiction_ref":
                                  r.get("contradiction_ref")})
            rows.append({"sid": r["sid"], "primary": primary(r), "axis_vs_anchor": cls,
                         "relation": rel, "same_family": fam,
                         "record_same_sign": sgn_field,
                         "contradiction_ref": r.get("contradiction_ref"),
                         "counted_in_C_by_registered_rule": fam and axis_same})
        m = committed["m"]
        lab_a = exit_label(m, cnt["支持"], cnt["扩展"] + cnt["反证"])
        lab_b = exit_label(m, cnt["支持"], cnt["扩展"])
        out["anchors"][anchor] = {
            "anchor_axis_from_coding": anchor_axis,
            "m": m, "support_threshold": committed["support_threshold"],
            "committed": {"C_strict": committed["C_strict"], "C_signed": committed["C_signed"],
                          "R": committed["R"], "unclassifiable_sign":
                          committed["unclassifiable_sign"],
                          "label_reported": committed["label_reported"]},
            "mechanical_reproduction_of_registered_counts": {
                "C": [committed["C_strict"], mech_c], "C_reproduced": committed["C_strict"] == mech_c,
                "R": [committed["R"], mech_r], "R_reproduced": committed["R"] == mech_r,
                "unclassifiable": [committed["unclassifiable_sign"], mech_u],
                "unclassifiable_reproduced": committed["unclassifiable_sign"] == mech_u},
            "reanalysed": {"支持": cnt["支持"], "扩展": cnt["扩展"], "反证": cnt["反证"],
                           "符号不可判": cnt["符号不可判"], "无关": cnt["无关"],
                           "C_dropped_by_claim_level": mech_c - cnt["支持"]},
            "concordance_field_diverges_from_axis_comparison": divergent,
            "variant_A": {"R_prime": cnt["扩展"] + cnt["反证"], "label": lab_a},
            "variant_B": {"R_prime": cnt["扩展"], "label": lab_b},
            "conservative_label": conservative(lab_a, lab_b),
            "label_moves_vs_committed": (lab_a != committed["label_reported"]
                                         or lab_b != committed["label_reported"]),
            "per_neighbour": rows,
        }

    repro = [(a, v["mechanical_reproduction_of_registered_counts"])
             for a, v in out["anchors"].items()]
    out["all_registered_counts_reproduced"] = all(
        v["C_reproduced"] and v["R_reproduced"] and v["unclassifiable_reproduced"]
        for _, v in repro)
    out["concordance_field_divergences"] = {
        a: v["concordance_field_diverges_from_axis_comparison"]
        for a, v in out["anchors"].items()
        if v["concordance_field_diverges_from_axis_comparison"]}
    movers = sorted(k for k, v in out["anchors"].items() if v["label_moves_vs_committed"])
    out["anchors_whose_label_moves"] = movers
    out["reading"] = ("counts move and at least one label would move under variant A, but the "
                      "round's own conservative rule keeps every label; the committed verdict "
                      "INDETERMINATE stands (R6, zero test status)" if movers else
                      "counts move; no label moves under either variant")
    dst = LIT / "L01_reanalysis.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    for a, v in repro:
        print("reproduction", a, v)
    print("all registered counts reproduced:", out["all_registered_counts_reproduced"])
    for anchor, v in out["anchors"].items():
        print(anchor, "| committed C/R =", v["committed"]["C_strict"], "/", v["committed"]["R"],
              "-> C' =", v["reanalysed"]["支持"], "| 反证 =", v["reanalysed"]["反证"],
              "| 扩展 =", v["reanalysed"]["扩展"], "| A:", v["variant_A"]["label"],
              "B:", v["variant_B"]["label"], "| committed:", v["committed"]["label_reported"],
              "|| MOVES" if v["label_moves_vs_committed"] else "|| same")
        for r in v["per_neighbour"]:
            if r["relation"] in ("反证", "支持", "符号不可判"):
                print("     ", r["sid"], r["relation"], "axis", r["axis_vs_anchor"],
                      "record_same_sign", r["record_same_sign"], "contra",
                      r["contradiction_ref"], "| §5 put it in C:",
                      r["counted_in_C_by_registered_rule"])
    print("wrote", dst.name, "| label moves:", movers, "|", out["reading"])


if __name__ == "__main__":
    main()
