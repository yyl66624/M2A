"""Runner for Round L-03: pre-gate, build, write, full-gate, print the one reading the report may quote.

The pre-gate is a write barrier: if it fails, no artifact is created. The artifact is written only when the
preregistration's disk bytes and git object agree. The full gate then re-derives every field; a failure leaves
the artifact on disk for the zero-test reanalysis path but exits non-zero.

Run from anywhere: `python3 literature/run_L03.py`.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

LIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(LIT))
import l03_coding as C  # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def gate(mode: str) -> int:
    p = subprocess.run([sys.executable, str(LIT / "l03_gate.py"), mode], cwd=str(C.REPO))
    return p.returncode


def main() -> int:
    if gate("--pre") != 0:
        print("L03 REFUSED: pre-gate failed; no artifact written")
        return 2
    text = C.TEXT.read_text(encoding="utf-8")
    acq = json.loads(C.ACQ.read_text(encoding="utf-8"))
    art = C.build(text, acq, C.PREREG.read_bytes(), C.git_show(C.PREREG_REL))
    if not art["prereg_binding"]["match"]:
        print("L03 REFUSED: prereg disk bytes and git object disagree; no artifact written")
        return 3
    if C.OUT.exists():
        old = json.loads(C.OUT.read_text(encoding="utf-8"))
        old.pop("written_at", None)
        if old == art:
            print("L03 artifact already present and equal to the rebuild; nothing written")
        else:
            print("L03 REFUSED: an artifact with different content exists; refusing to overwrite it")
            return 4
    else:
        art["written_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        C.OUT.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("L03 wrote %s (%d bytes, sha256 %s)"
              % (C.OUT.name, C.OUT.stat().st_size, sha(C.OUT.read_bytes())[:16]))
    if gate("--full") != 0:
        print("L03 FULL GATE FAILED: artifact left on disk for the reanalysis path; no reading may be quoted")
        return 5
    cnt = art["counts"]
    print("L03 reading: exit %s | core c=%d r=%d u=%d f=%d | fulltext %d chars >= %d | quotes %d | "
          "additional %d | label %s"
          % (art["exit_q1"], cnt["confirmed"], cnt["revised"], cnt["unsupported"], cnt["refuted"],
             cnt["fulltext_chars"], cnt["floor"], cnt["quotes_total"], cnt["additional"],
             art["exit_q1_label_r17"]))
    print("L03 obligations: L01-O5 %s | L03-O1 %s"
          % (art["l01_o5"]["status"], art["l03_o1"]["status"]))
    print("L03 artifact sha256: %s" % sha(C.OUT.read_bytes()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
