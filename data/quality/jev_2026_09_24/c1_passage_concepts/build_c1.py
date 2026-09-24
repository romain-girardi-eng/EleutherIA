"""C1 build: every original Greek/Latin passage (same selection logic as
~/Projects/Veille/2026-09-17-jev-gold/eleutheria-full/build_full.py) against
ALL concept nodes in data/kg/nodes.jsonl (type == 'concept', ~212), not only
the 62 concepts that had existing discusses/evidenced_by edges on 2026-09-17.

Writes candidates.jsonl (one row per passage, with existing concept edges in
both directions) and concepts.json (all concept nodes, gloss + label)."""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/romaingirardi/Projects/EleutherIA/data")
OUT = Path(__file__).parent
MAX_CHARS = 4000
MIN_CHARS = 80


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def meta_of(n):
    m = n.get("metadata") or {}
    if isinstance(m, str):
        try:
            m = json.loads(m)
        except Exception:
            m = {}
    return m


def strip_md(s: str) -> str:
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[*_#>]", "", s)
    return s


corpus = {p["passage_id"]: p for p in load_jsonl(ROOT / "corpus/passages.jsonl")}
nodes = {}
for n in load_jsonl(ROOT / "kg/nodes.jsonl"):
    nodes[n.get("node_id") or n.get("id")] = n

# existing discusses / evidenced_by edges between passage and concept nodes,
# both edge directions, using both source/target and source_id/target_id.
existing = defaultdict(set)
for e in load_jsonl(ROOT / "kg/edges.jsonl"):
    s = e.get("source") or e.get("source_id")
    t = e.get("target") or e.get("target_id")
    r = e.get("relation")
    ns, nt = nodes.get(s), nodes.get(t)
    if not ns or not nt:
        continue
    if r == "discusses" and ns.get("type") == "passage" and nt.get("type") == "concept":
        existing[s].add(t)
    elif r == "evidenced_by" and nt.get("type") == "passage" and ns.get("type") == "concept":
        existing[t].add(s)

# ALL concept nodes (not just the 62 with existing edges)
def gloss(n):
    d = strip_md((n.get("description") or "").strip())
    d = re.split(r"(?<=[.!?])\s", d)[0] if d else ""
    d = re.sub(r"\s+", " ", d)[:240]
    return d


concepts = {}
for nid, n in nodes.items():
    if n.get("type") != "concept":
        continue
    concepts[nid] = {"label": n.get("label"), "gloss": gloss(n)}
with open(OUT / "concepts.json", "w", encoding="utf-8") as f:
    json.dump(concepts, f, ensure_ascii=False, indent=1)
print("concepts:", len(concepts), "(with existing edges to >=1 passage:", sum(1 for c in concepts if any(c in v for v in existing.values())), ")")

rows = []
skipped = 0
for nid, n in nodes.items():
    if n.get("type") != "passage":
        continue
    m = meta_of(n)
    if m.get("language") not in ("grc", "lat"):
        continue
    pid = m.get("db_passage_id") or m.get("passage_id")
    p = corpus.get(pid)
    if not p:
        skipped += 1
        continue
    t = (p.get("text_content") or "").strip()
    if len(t) < MIN_CHARS:
        skipped += 1
        continue
    rows.append({
        "id": nid, "lang": m.get("language"), "author": m.get("author"), "work": m.get("work_title"),
        "ref": m.get("canonical_ref"), "text": t[:MAX_CHARS], "truncated": len(t) > MAX_CHARS,
        "existing": sorted(existing.get(nid, ())),
    })
print("passages:", len(rows), "skipped:", skipped, "truncated:", sum(r["truncated"] for r in rows))
with open(OUT / "candidates.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
