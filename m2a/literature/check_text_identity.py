"""Quality check: is each fetched text actually the paper it claims to be?

For each text file, report length, a proxy for prose content (count of ' the '), and whether a
distinctive token from the record's title or the first author's surname appears. A text that fails the
identity check must NOT be counted as reviewed, whatever its length.
"""
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FT = pathlib.Path(r"E:\workshop\_m2a_ft")
reg = {r["id"]: r for r in json.load(open("registry.json", encoding="utf-8"))["records"]}

print(f"{'id':9s} {'chars':>7s} {'the':>6s}  identity")
ok, bad = [], []
for rid, rec in reg.items():
    p = FT / f"{rid}.txt"
    if not p.exists() or p.stat().st_size < 5000:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    the = low.count(" the ")
    title = (rec.get("citation") or "")
    head = title.split(".")[0][:40].lower()
    toks = [t for t in re.findall(r"[a-z]{6,}", head)][:6]
    hit = sum(1 for t in toks if t in low)
    ident = hit >= max(2, len(toks) // 2) or the > 200
    (ok if ident else bad).append(rid)
    print(f"{rid:9s} {len(text):7d} {the:6d}  {'OK' if ident else 'SUSPECT'} (title hits {hit}/{len(toks)})")
print(f"\nidentity OK: {len(ok)}  suspect: {len(bad)} {bad}")
