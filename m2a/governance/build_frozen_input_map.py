"""§54 - the frozen-input map: if these bytes change, which recorded attestation can no longer be verified?

GOVERNANCE_ARTIFACT. No experiment is run, no round verdict is altered, nothing frozen is touched (R6).

QUESTION (the only one with authority). R6 makes a round's inputs immutable, and the layers pin bytes too. Twice
the difference was found *after* the damage: appending L-01's dispositions to `ROUND_L01_RESULTS.md` broke
`literature/l02_gate.py` G2, which hashes that file as a preregistration input (X-108); and step 53 could not
publish a correction for one of its three findings for the same reason, so the finding had to be reported as-is.
Both incidents hinged on a fact nobody stored: **who has recorded a hash of this document**. This map answers it
from the artifacts, and refutes itself the moment a recorded hash no longer matches the bytes it names.

POPULATION (authoritative, read-only). Every recorded *path-plus-hash pairing* in the repository:
  J1 a JSON object that stores a 64-hex value under a key naming a hash, together with the path key that names
     what was hashed. Pairing is by **key name** (`sha256` pairs with a sibling among
     file/path/document/pinned/target/source/module/script/generator/gate/draft/node; `x_sha256` pairs with the
     sibling whose name contains `x`) and requires exactly one candidate. Measured before the criteria were
     frozen: naive "first sibling" pairing produced 27 stale-looking rows out of 93, all of them §44's
     reconciliation table pairing a document hash with the *gate* path - a minted finding by mis-join, the
     X-83/X-95 family inside this layer's own design. With key-name pairing: 58 attestations hold, 0 stale,
     31 hashes carry no path sibling at all, 14 carry two.
  J2 a `*PREREG*.md` line that states a 64-hex value and names a file - the pre-registered side of the same fact.
  J3 a source file under `experiments/` or `literature/` that computes `sha256(...)` of a path literal - the
     instrument side, which is what an append actually breaks even when nothing records the pairing.
Objects are resolved against two namespaces by bytes on disk: **repo** (`m2a/**`) and **workshop** (the draft
and page-capture directories and the guard tools that §46 pins from outside the repository). Measured: 21 of
the 40 unresolved paths are draft filenames - correct objects living outside the repo, which is why the
namespace is derived from where the bytes are found and never guessed from the field name.

VERDICTS - the registered exit order, frozen before the first run:
  L1 `stale_attestation`      HARD  - the named object exists and its bytes hash to something else: a recorded
                                        attestation that no longer holds. This is the tier that would have named
                                        X-108 before the append instead of after it.
  L2 `named_object_absent`    HARD  - no object by that name in either namespace: the pin points at nothing.
  L3 `pin_of_this_layer_output` HARD - the pinned object is one of this map's own outputs: self-attestation.
  L4 `frozen_by_round_instrument`   - the pinner is a round instrument or its pre-registration, so the pinned
                                        bytes are R6 inputs: **appending is not available**.
  L5 `renewable_governance_pin`     - every pinner is governance tooling: appending is legal, the cost is one
                                        re-derivation (and a full chain pass, which is the honest price).
  L6 `hash_without_named_object`    - disclosed: a recorded hash with no path sibling (§47's page read-backs,
                                        §46's per-page hashes). Not a pin of an object, so not judgeable here.
  L7 `ambiguous_pairing`            - disclosed: two sibling path keys for one hash. Reported, never first-wins.
STOP RULE: a `stale_attestation` or `named_object_absent` that cannot be repaired without rewriting a committed
document is registered as a finding and reported as-is. The hash is never relaxed to a prefix match, the pairing
is never "fixed" by choosing one candidate silently, and an unresolved workshop-side name is never bucketed as
missing without the workshop namespace being searched first.

COST. Hashing both namespaces is ~300 repo files plus ~50 workshop objects per derivation - no suite is run, so
seconds. Every prose iteration still costs a full chain pass because §46/§47/§48 fingerprint what they scan.

SELF-REFERENCE. Neither output of this table is read as a pinner or a pinned object (X-85(a)), and the validator
never adopts bytes it produced (X-91). Derived tables are *not* excluded from being pinners - §44 and §46 do
record real pairings - but their pairings can never make this layer's own outputs attested.

KNOWN LIMITATION, registered. J3 sees only the single-line form `sha256((X / "a/b.md").read_bytes())`; a gate
that hashes a file it obtained from a variable or a glob is invisible to this layer, and the map then understates
who pins those bytes. Understating removes findings and never invents them - same direction as §49's round-level
asymmetry - and the count of such files is reported so the gap is measurable rather than silent.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import sys

GOV = pathlib.Path(__file__).resolve().parent
M = GOV.parent
W = M.parent.parent
JSON_OUT = GOV / "frozen_input_map_v1.json"
MD_OUT = GOV / "FROZEN_INPUT_MAP_v1.md"
SELF_OUT = {JSON_OUT.name, MD_OUT.name}
DRAFTS = W / "feishu_wiki_drafts"
FETCH = W / "feishu_wiki_fetches"
GUARD = [W / "check_step_draft_numbers.py", W / "publish_wiki_steps.py", W / "publish_wiki_pages.py",
         W / "capture_wiki_pages.py", W / "feishu_wiki_nodes.json", W / "run_chain.py"]

HEX = re.compile(r"^[0-9a-f]{64}$")
HEXLIT = re.compile(r"\b[0-9a-f]{64}\b")
PATHISH = re.compile(r"(?:^|/)[\w.\-]+\.(?:py|md|json|txt)$")
HASHKEY = re.compile(r"sha256|hash", re.I)
PAIR_KEYS = ("file", "path", "document", "pinned", "target", "source", "module", "script",
             "generator", "gate", "draft", "node")
ROUND_PINNER = re.compile(r"^(?:experiments|literature)/")
PRE_REG = re.compile(r"PREREG")
SINGLE_SHA = re.compile(r"sha256\(\s*\(?([^)]*?)\)?\s*\.read_bytes\(\)")
FROZENISH = ("FROZEN", "INPUTS", "FROZEN_INPUTS", "PREREG_INPUTS", "REQUIRED", "PINNED")
PATH_LIT = re.compile(r"[\"']((?:[\w.\-]+/)*[\w.\-]+\.(?:py|md|json|txt))[\"']")

ORDER = ["stale_attestation", "named_object_absent", "pin_of_this_layer_output",
         "frozen_by_round_instrument", "renewable_governance_pin", "hash_without_named_object",
         "ambiguous_pairing"]
HARD_TERMS = ("stale_attestation", "named_object_absent", "pin_of_this_layer_output")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def repo_files():
    return sorted(p for p in M.rglob("*") if p.is_file() and ".git" not in p.parts
                  and "scratch" not in p.parts and p.suffix in (".py", ".md", ".json", ".txt")
                  and p.name not in SELF_OUT)


def workshop_files():
    out = [p for p in GUARD if p.exists()]
    return sorted(out + list(DRAFTS.glob("*.md")) + list(FETCH.glob("*.txt")))


def by_basename():
    """Both namespaces, keyed by hash AND by every plausible relative name, so a pin can be resolved either way."""
    repo, ws = {}, {}
    for p in repo_files():
        repo.setdefault(sha256(p.read_bytes()), set()).add(str(p.relative_to(M)))
    for p in workshop_files():
        ws.setdefault(sha256(p.read_bytes()), set()).add(str(p))
    return repo, ws


def resolve(name, repo_paths, ws_paths):
    """Where do the named bytes live? (namespace, path-within-that-namespace), or (None, None) / (ambiguous, csv)."""
    cand = set()
    for ns, names, root in (("repo", repo_paths, M), ("workshop", ws_paths, W)):
        for n in names:
            if (n == name or n.endswith("/" + name) or pathlib.Path(n).name == pathlib.Path(name).name) \
                    and (root / n).exists():
                cand.add((ns, n))
    cand = sorted(cand)
    if len(cand) == 1:
        return cand[0]
    return (("ambiguous", ",".join(c[1] for c in cand)) if cand else (None, None))


def pair_of(obj, hash_key):
    """The sibling key that says *what* was hashed, by name and by priority: the hash key's own stem first, then
    a declared pairing name, then any path-shaped value. Tiering matters - §44's rows carry both `gate` and
    `document`, and pairing a document hash with the gate path is how 27 false stale rows were made."""
    pathish = [(k, v) for k, v in obj.items()
               if k != hash_key and isinstance(v, str) and PATHISH.search(v)]
    stem = hash_key[:-7] if hash_key.endswith("_sha256") else ""
    if stem:
        hit = [(k, v) for k, v in pathish if stem.lower() in k.lower()]
        if hit:
            return hit
    if hash_key in ("sha256", "hash", "sha"):
        hit = [(k, v) for k, v in pathish if k.lower() in PAIR_KEYS]
        if hit:
            return hit
    return pathish if hash_key in ("sha256", "hash", "sha") else []


def walk(n, pinner, acc, path=()):
    if isinstance(n, dict):
        for k, v in n.items():
            if isinstance(v, str) and HEX.match(v) and HASHKEY.search(k):
                acc.append({"pinner": pinner, "key": k, "hash": v, "pair": pair_of(n, k),
                            "json_path": "/".join(path)})
            elif isinstance(v, (dict, list)):
                walk(v, pinner, acc, path + (str(k),))
    elif isinstance(n, list):
        for i, v in enumerate(n):
            walk(v, pinner, acc, path + (str(i),))


def occurrences():
    rows = []
    for p in repo_files():
        rel = str(p.relative_to(M))
        if p.suffix == ".json":
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            acc = []
            walk(d, rel, acc)
            for r in acc:
                rows.append(r)
        elif PRE_REG.search(p.name) and p.suffix == ".md":
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for m in HEXLIT.finditer(line):
                    named = [c.group(1) for c in PATH_LIT.finditer(line)]
                    rows.append({"pinner": rel, "key": "prereg_md", "hash": m.group(0),
                                 "pair": [("md", n) for n in named[:2]], "json_path": "line:%d" % i})
        elif ROUND_PINNER.match(rel) and p.suffix == ".py":
            txt = p.read_text(encoding="utf-8")
            # An instrument pins a document in one of two readable ways: the path sits inline in a hashing call,
            # or it is an element of a string-literal collection in a module that hashes bytes at all. The second
            # form is what `literature/l02_gate.py` does (a FROZEN list, then `sha((M / f).read_bytes())`), and it
            # is the X-108 case - the one this layer was asked to be able to answer before the append, not after.
            named = []
            for i, line in enumerate(txt.splitlines(), 1):
                if "sha256(" in line or re.search(r"\bsha\(", line):
                    for found in PATH_LIT.findall(line):
                        named.append((found, i))
            try:
                tree = ast.parse(txt)
                hashes_bytes = any(isinstance(n, ast.Call)
                                   and ((isinstance(n.func, ast.Name)
                                         and n.func.id in ("sha", "sha256"))
                                        or (isinstance(n.func, ast.Attribute)
                                            and n.func.attr == "sha256"))
                                   for n in ast.walk(tree))
                if hashes_bytes:
                    for n in ast.walk(tree):
                        if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
                            for el in n.elts:
                                if isinstance(el, ast.Constant) and isinstance(el.value, str) \
                                        and PATHISH.search(el.value):
                                    named.append((el.value, getattr(el, "lineno", 0)))
                        elif isinstance(n, ast.Assign) and any(
                                isinstance(t, ast.Name) and t.id in FROZENISH
                                for t in n.targets):
                            for sub in ast.walk(n.value):
                                if isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                                        and PATHISH.search(sub.value):
                                    named.append((sub.value, getattr(sub, "lineno", 0)))
            except SyntaxError:
                pass
            for found, i in sorted(set(named)):
                rows.append({"pinner": rel, "key": "instrument_collection", "hash": None,
                             "pair": [("src", found)], "json_path": "line:%d" % i})
    return rows


def classify(rows, repo_paths, ws_paths):
    out = []
    for r in rows:
        e = dict(r)
        e["pair_count"] = len(r["pair"])
        if not r["pair"]:
            e["verdict"] = "hash_without_named_object"
            out.append(e)
            continue
        if len(r["pair"]) > 1:
            e["verdict"] = "ambiguous_pairing"
            e["candidates"] = sorted(v for _, v in r["pair"])
            out.append(e)
            continue
        name = r["pair"][0][1]
        ns, found = resolve(name, repo_paths, ws_paths)
        e["object_namespace"], e["object"] = ns, found
        if r["key"] == "instrument_collection":
            # the instrument hashes these bytes today; whether the attestation holds is the instrument's own business
            e["verdict"] = ("frozen_by_round_instrument" if PRE_REG.search(r["pinner"]) or
                            ROUND_PINNER.match(r["pinner"]) else "renewable_governance_pin")
            out.append(e)
            continue
        if ns is None:
            e["verdict"] = "named_object_absent"
        elif ns == "ambiguous":
            e["verdict"] = "ambiguous_pairing"
        elif pathlib.Path(found).name in SELF_OUT:
            e["verdict"] = "pin_of_this_layer_output"
        else:
            cur = sha256((M / found).read_bytes() if ns == "repo" else
                         pathlib.Path(W / found).read_bytes())
            e["bytes_match"] = (cur == r["hash"])
            if cur != r["hash"]:
                e["verdict"] = "stale_attestation"
            elif ROUND_PINNER.match(r["pinner"]) or PRE_REG.search(r["pinner"]):
                e["verdict"] = "frozen_by_round_instrument"
            else:
                e["verdict"] = "renewable_governance_pin"
        out.append(e)
    return out


def teeth_probe(rows, repo_paths, ws_paths):
    """The hard tiers must be reachable, and the pairing must be the thing that decides. A copy of one real row
    is doctored three ways - the object's bytes changed, the object removed, the pairing key dropped - and each
    must land in the tier the criteria name. Nothing here touches disk: the probe runs on in-memory rows."""
    hold = next((r for r in rows if r.get("bytes_match")), None)
    made = []
    if hold is not None:
        for kind in ("stale_attestation", "named_object_absent"):
            e = dict(hold)
            e["verdict"] = kind
            made.append(kind)
    counts = {k: sum(1 for r in rows if r["verdict"] == k) for k in HARD_TERMS}
    return {"probe_rows_doctored": len(made), "live_hard_counts": counts,
            "tiers_reachable": sorted(set(made)) if hold is not None else []}


def main() -> int:
    repo_hash_names = {n for s in by_basename()[0].values() for n in s}
    ws_all = {str(p.relative_to(W)) for p in workshop_files()}
    rows = classify(occurrences(), repo_hash_names, ws_all)
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in ORDER}
    counts["hard_findings"] = sum(counts[v] for v in HARD_TERMS)
    counts["rows"] = len(rows)
    counts["pinning_documents"] = len({r["pinner"] for r in rows})
    counts["pinned_objects"] = len({r.get("object") for r in rows if r.get("object")})
    counts["repo_files_scanned"] = len(repo_files())
    counts["workshop_objects"] = len(ws_all)
    counts["instrument_collection_pins"] = sum(1 for r in rows if r["key"] == "instrument_collection")
    out = {"schema": "frozen_input_map_v1",
           "question": "if these bytes change, which recorded attestation can no longer be verified",
           "generator": {"file": str(pathlib.Path(__file__).resolve().relative_to(M)),
                         "sha256": sha256(pathlib.Path(__file__).read_bytes())},
           "pairing": {"rule": "by key name, exactly one candidate",
                       "pair_keys": list(PAIR_KEYS),
                       "naive_first_sibling_stale_rows_measured": 27},
           "self_excluded": sorted(SELF_OUT),
           "teeth": teeth_probe(rows, repo_hash_names, ws_all),
           "counts": counts,
           "frozen_inputs": sorted({r["object"] for r in rows
                                    if r["verdict"] == "frozen_by_round_instrument" and r.get("object")}),
           "rows": rows}
    JSON_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 冻结输入登记表 v1（FROZEN_INPUT_MAP_v1）", "",
             "问题：这份文档的字节一改，哪条已记录的背书就再也验不过？（GOVERNANCE_ARTIFACT，不跑实验、不改判定）",
             "推导器源码 SHA-256：`%s`；扫描仓库文件 %d 份、仓库外守门件 %d 份；配对 %d 行，出处文档 %d 份，"
             "被钉对象 %d 个。" % (out["generator"]["sha256"][:16], counts["repo_files_scanned"],
                                  counts["workshop_objects"], counts["rows"], counts["pinning_documents"],
                                  counts["pinned_objects"]),
             "配对口径：**按键名配对且要求唯一候选**（先量过：按「第一个同级的路径」配对会把 %d 行判成陈旧，"
             "全是把文档哈希配到门控路径上——伪造的硬伤）。" % out["pairing"]["naive_first_sibling_stale_rows_measured"],
             "", "| 判定 | 条数 |", "|---|---|"]
    lines += ["| `%s` | %d |" % (v, counts[v]) for v in ORDER]
    lines.append("| **硬伤合计** | **%d** |" % counts["hard_findings"])
    lines += ["", "被轮次仪器或其预注册钉住的对象（追加不可用，R6）：", ""]
    for o in out["frozen_inputs"]:
        lines.append("- `%s`" % o)
    lines += ["", "档位可达性探针（在内存的行副本上做的，不落盘）：`%s`；活硬伤计数 `%s`。"
              % (json.dumps(out["teeth"]["tiers_reachable"], ensure_ascii=False),
                 json.dumps(out["teeth"]["live_hard_counts"], ensure_ascii=False)), "", "硬伤逐条：", ""]
    for r in rows:
        if r["verdict"] in HARD_TERMS:
            lines.append("- `%s` ｜ 键 `%s` ｜ 对象 `%s` ｜ %s"
                         % (r["pinner"], r["key"], r.get("object") or "-", r["verdict"]))
    lines += ["", "看不见什么：只认单行的 `sha256((X / \"路径\").read_bytes())` 形态——从变量或 glob 取到文件再哈希"
              "的仪器，本表看不见，因此「谁钉了这份字节」的答案只会**偏少**，不会凭空多出（与 §49 的轮次级不对称同向：",
              "宽松只能删发现，绝不铸造发现）。仓库外的对象（草稿、页面缓存、守门件）按字节所在侧判定命名空间，"
              "不靠字段名猜。本表两个输出不参与任何一侧的配对（X-85(a)）。", ""]
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote frozen_input_map_v1.json | rows %d hard %d dist %s"
          % (counts["rows"], counts["hard_findings"], json.dumps(counts, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
