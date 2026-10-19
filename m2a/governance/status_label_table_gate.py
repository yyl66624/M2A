"""Suite for the five-label table: instrument checks only (R2), no scientific criterion.

Two failure modes this closes:

* the committed table going stale against its generator (X-68: "the artifact exists" is not
  "the check was run");
* the report quoting a number that the generated artifact does not contain. That is not hypothetical
  - M2A_FINAL_REPORT.md §34 hand-typed the v1 count row for `NULL` as "1 / 1 / 0" while
  `status_label_table_v1.json` says counts.NULL = 1 with artifact_fields = 0 and prose_only = 1, and
  it attributed that reading to a token (`NOT_OBTAINED`) that does not occur in `L01_coding.json` at
  all. The correction is recorded in §37 and in X-74; this suite is what stops the next one.

Checks:
  S1 the generator rewrites the committed v2 JSON byte-for-byte (derivation is reproducible)
  S2 the derivation is idempotent
  S3 MANUAL_REVIEW is reported, not silently absorbed: every remaining manual row is listed
  S4 the five labels are each counted from rows that carry them, and the dispositions partition
     the rows exactly (sum over dispositions == number of rows)
  S5 every count quoted in the report's v2 table equals the JSON
  S6 no RULES entry is asserted to exist in an artifact unless it actually occurs there
     (this is the `NOT_OBTAINED` class of error: a rule kept as if it were evidence)
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
GEN = GOV / "build_status_label_table.py"
TABLE = GOV / "status_label_table_v2.json"
REPORT = M / "M2A_FINAL_REPORT.md"
FIVE = ["SUPPORTED", "CONTRADICTED", "NULL", "INDETERMINATE", "NOT_IDENTIFIED"]


def main() -> int:
    checks = ok = 0

    def report(name, passed, detail=""):
        nonlocal checks, ok
        checks += 1
        ok += int(passed)
        print(("PASS  " if passed else "FAIL  ") + name + ("  " + detail if detail else ""))

    before = TABLE.read_bytes()
    r = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("S1 generator reproduces the committed table", r.returncode == 0 and
           TABLE.read_bytes() == before, (r.stdout.strip().splitlines() or [""])[-1][:70])
    r2 = subprocess.run([sys.executable, str(GEN)], cwd=M, capture_output=True, text=True)
    report("S2 derivation idempotent", TABLE.read_bytes() == before and r2.returncode == 0)

    d = json.loads(TABLE.read_text(encoding="utf-8"))
    manual = [x for x in d["rows"] if x["label"] == "MANUAL_REVIEW"]
    report("S3 MANUAL_REVIEW visible, never absorbed",
           len(manual) == d["counts"]["MANUAL_REVIEW"],
           "rows=" + str(len(manual)))

    labs = FIVE + ["MANUAL_REVIEW", "ZERO_TEST_REANALYSIS", "COUNT_NOT_STATUS"]
    per_claim = [x for x in d["rows"] if not x.get("derived")]
    s = sum(1 for x in per_claim if x["label"] in labs)
    report("S4 dispositions partition the claim rows", s == len(per_claim) and
           sum(d["counts"][l] for l in labs) == len(per_claim),
           "claims=" + str(len(per_claim)))

    text = REPORT.read_text(encoding="utf-8")
    # `#### 37.1` contains the substring "### 37", so the split has to be anchored at line start
    m_sec = re.search(r"^### 37 [^\n]*\n", text, re.M)
    sec = text[m_sec.end():] if m_sec else ""
    quoted = {}
    for lab in FIVE:
        m = re.search(r"^\| `" + lab + r"` \| (\d+) \| (\d+) \| (\d+) \|", sec, re.M)
        if m:
            quoted[lab] = [int(m.group(1)), int(m.group(2)), int(m.group(3))]
    mism = []
    for lab in FIVE:
        truth = [d["counts"][lab], d["gap"][lab]["artifact_fields"], d["gap"][lab]["prose_only"]]
        if quoted.get(lab) is not None and quoted[lab] != truth:
            mism.append(lab + " quoted " + str(quoted[lab]) + " != artifact " + str(truth))
    report("S5 report v2 table matches the JSON", not mism and len(quoted) == len(FIVE),
           "; ".join(mism) or ("checked " + str(len(quoted)) + " labels"))

    claims = " ".join(str(x.get("raw", "")) + " " + str(x.get("field", "")) + " "
                       + str(x.get("via", "")) + " " + str(x.get("resolved_via", ""))
                       for x in d["rows"])
    # a RULES token that never occurs in any scanned artifact is a rule without a referent. That is
    # only acceptable when the report says so out loud, so the guard is: absent => must be named in
    # the §37 correction section, otherwise FAIL. (NOT_OBTAINED is exactly this case: the table
    # shipped it as if it were an L-01 reading, and it is in no L-01 artifact.)
    absent = [tok for tok in d["rules"] if tok not in FIVE and tok not in claims]
    unregistered = [tok for tok in absent if tok not in sec]
    report("S6 a RULES token with no artifact referent is registered as such",
           not unregistered,
           "absent and unregistered: " + (", ".join(unregistered) or "none")
           + (" | registered absences: " + ", ".join(absent) if absent else ""))

    print(str(ok) + "/" + str(checks) + " checks passed")
    return 0 if ok == checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
