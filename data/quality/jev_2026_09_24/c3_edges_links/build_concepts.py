"""Part B — build candidates for proposing missing node -> concept links.

For every argument, work, publication, person and synthesis node with a
description >= 60 chars, ask Jev booleans against ALL 212 concept nodes:
"This <type>, as described, explicitly deals with the concept: <label>. <gloss>"
Batched ~55 concepts per call (run_concepts.py does the batching+API calls;
this script only prepares the node list, the concept question bank, and the
existing-edge index for later comparison).

Outputs:
  concepts_B.json       -- {concept_id: {label, gloss}}
  candidates_B.jsonl     -- one row per node: id, type, name, description,
                            existing (sorted list of concept_ids already
                            linked to this node, any relation, either
                            direction)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("/Users/romaingirardi/Projects/EleutherIA/data")
OUT = Path(__file__).parent

CANDIDATE_TYPES = {"argument", "work", "publication", "person", "synthesis"}
MIN_DESC = 60
MAX_DESC = 3000


def load_jsonl(p: Path):
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def node_id(n: dict) -> str:
    return n.get("node_id") or n.get("id")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def gloss_of(n: dict) -> str:
    d = clean(n.get("description") or "")
    # first sentence, capped
    m = re.split(r"(?<=[.!?])\s", d, maxsplit=1)
    first = m[0] if m else d
    return first[:200]


def main() -> None:
    nodes = {}
    for n in load_jsonl(ROOT / "kg/nodes.jsonl"):
        nodes[node_id(n)] = n

    concepts = {
        nid: {"label": n.get("label"), "gloss": gloss_of(n)}
        for nid, n in nodes.items()
        if n.get("type") == "concept"
    }
    with open(OUT / "concepts_B.json", "w", encoding="utf-8") as f:
        json.dump(concepts, f, ensure_ascii=False, indent=1)
    print("concepts:", len(concepts))

    concept_ids = set(concepts)
    existing: dict[str, set[str]] = {}
    for e in load_jsonl(ROOT / "kg/edges.jsonl"):
        s = e.get("source") or e.get("source_id")
        t = e.get("target") or e.get("target_id")
        if t in concept_ids and s in nodes:
            existing.setdefault(s, set()).add(t)
        if s in concept_ids and t in nodes:
            existing.setdefault(t, set()).add(s)

    n_written = 0
    n_skipped = 0
    with open(OUT / "candidates_B.jsonl", "w", encoding="utf-8") as f:
        for nid, n in nodes.items():
            t = n.get("type")
            if t not in CANDIDATE_TYPES:
                continue
            desc = clean(n.get("description") or "")
            if len(desc) < MIN_DESC:
                n_skipped += 1
                continue
            row = {
                "id": nid,
                "type": t,
                "name": n.get("label") or nid,
                "description": desc[:MAX_DESC],
                "existing": sorted(existing.get(nid, ())),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"candidate nodes: {n_written}, skipped (desc<{MIN_DESC}): {n_skipped}")


if __name__ == "__main__":
    main()
