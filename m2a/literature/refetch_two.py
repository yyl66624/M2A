"""Re-fetch R13 from Europe PMC (the DOIs landing page yields navigation chrome) and re-try R01."""
import pathlib
import re
import sys
import urllib.request

import pypdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = pathlib.Path(r"E:\workshop\_m2a_ft")
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120 Safari/537.36")}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()


def strip(blob):
    txt = blob.decode("utf-8", errors="replace")
    txt = re.sub(r"<script.*?</script>", " ", txt, flags=re.S | re.I)
    txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", txt))


# R13: known-good Europe PMC full text (PMC10592633)
try:
    text = strip(get("https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10592633/fullTextXML"))
    assert len(text) > 50000
    (OUT / "R13.txt").write_text(text, encoding="utf-8")
    print("R13 OK", len(text))
except Exception as e:  # noqa: BLE001
    print("R13 FAILED", e)

# R01: re-extract the ACL PDF without the shared temp-file race, keep the longer of the two
try:
    blob = get("https://aclanthology.org/P98-1013.pdf")
    (OUT / "_r01.pdf").write_bytes(blob)
    reader = pypdf.PdfReader(str(OUT / "_r01.pdf"))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    print("R01 pages", len(reader.pages), "chars", len(text))
    if len(text) > 5000:
        (OUT / "R01.txt").write_text(text, encoding="utf-8")
        print("R01 OK", len(text))
except Exception as e:  # noqa: BLE001
    print("R01 FAILED", e)
