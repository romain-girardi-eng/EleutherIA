"""Merge 5 duplicate node-sets introduced/uncovered by the 5-scholars B1 batches.

Each merge: pick canonical, union metadata (canonical wins on conflict), keep
longest description, repoint every edge to canonical, drop resulting self-loops
and exact duplicates, remove non-canonical nodes.

Merge sets (chosen by edge count + label correctness + content richness):

 1. Frede 2011 publication →  pub_frede_2011_free_will (deg=68, desc 4752 chars)
    merge in:
      - scholarly_work_frede_2011_a_free_will_origins_of_the_notion_in_anc (deg=1)
      - scholarly_work_frede_2011_free_will (deg=1)
      - work_frede_free_will_2011 (deg=12, desc 2867 chars — preserve description)

 2. Dihle 1982 publication →  pub_dihle_1982_theory_of_will (deg=17, desc 3436 chars)
    merge in:
      - pub_dihle_1982_theory_will (deg=13, desc 2414 chars — preserve description)
      - scholarly_work_dihle_1982_the_theory_of_will_in_classical_antiquit (deg=1)
      - scholarly_work_dihle_1982_theory_will (deg=0)

 3. Albrecht Dihle (person) →  scholar_albrecht_dihle (deg=36, pre-existing)
    merge in:  scholar_dihle_albrecht (deg=30, NEW from B1)

 4. Michael Frede (person) →  scholar_frede_michael (correctly labeled, rich desc)
    merge in:  person_frede_michael_1940_2007 (deg=40, MISLABELED "Dorothea Frede"
                but ID indicates Michael 1940-2007; all 40 edges verified
                semantically refer to Michael)

 5. Ricardo Salles (person) →  person_salles_ricardo_contemporary (deg=15, pre-existing)
    merge in:  scholar_salles_ricardo (deg=7, NEW from B1)

Idempotent: re-running detects already-merged state (non-canonical IDs missing)
and exits cleanly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"


MERGES: list[dict[str, Any]] = [
    {
        "name": "Frede 2011 publication",
        "canonical": "pub_frede_2011_free_will",
        "merge_in": [
            "scholarly_work_frede_2011_a_free_will_origins_of_the_notion_in_anc",
            "scholarly_work_frede_2011_free_will",
            "work_frede_free_will_2011",
        ],
    },
    {
        "name": "Dihle 1982 publication",
        "canonical": "pub_dihle_1982_theory_of_will",
        "merge_in": [
            "pub_dihle_1982_theory_will",
            "scholarly_work_dihle_1982_the_theory_of_will_in_classical_antiquit",
            "scholarly_work_dihle_1982_theory_will",
        ],
    },
    {
        "name": "Albrecht Dihle (person)",
        "canonical": "scholar_albrecht_dihle",
        "merge_in": ["scholar_dihle_albrecht"],
    },
    {
        "name": "Michael Frede (person)",
        "canonical": "scholar_frede_michael",
        "merge_in": ["person_frede_michael_1940_2007"],
    },
    {
        "name": "Ricardo Salles (person)",
        "canonical": "person_salles_ricardo_contemporary",
        "merge_in": ["scholar_salles_ricardo"],
    },
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def parse_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def merge_metadata(canon_md: dict[str, Any], in_md: dict[str, Any]) -> dict[str, Any]:
    """Canonical wins on conflict; non-empty merge_in fills empties; lists are unioned."""
    out = dict(canon_md)
    for k, v in in_md.items():
        if k not in out or out[k] in (None, "", [], {}):
            out[k] = v
        elif isinstance(out[k], list) and isinstance(v, list):
            # Union preserving order, dedupe by str repr
            seen = set()
            unioned = []
            for item in list(out[k]) + list(v):
                key = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if key not in seen:
                    seen.add(key)
                    unioned.append(item)
            out[k] = unioned
        # else: canonical wins
    return out


def merge_descriptions(canon: dict[str, Any], in_node: dict[str, Any]) -> None:
    """Longer description wins; the other is preserved as `description_alt_<n>`."""
    for field in ("description", "description_en", "description_de"):
        canon_v = canon.get(field) or ""
        in_v = in_node.get(field) or ""
        if not in_v:
            continue
        if not canon_v:
            canon[field] = in_v
        elif len(in_v) > len(canon_v):
            # in_node has longer — swap and preserve canon as alt
            canon[field] = in_v
            md = parse_metadata(canon)
            md.setdefault(f"{field}_alt_pre_merge", canon_v)
            canon["metadata"] = md
        elif in_v != canon_v:
            md = parse_metadata(canon)
            alt_key = f"{field}_from_{in_node['id']}"
            md.setdefault(alt_key, in_v)
            canon["metadata"] = md


def merge_one(canon: dict[str, Any], in_node: dict[str, Any]) -> None:
    """In-place merge of in_node into canon. Metadata/desc, confidence, period."""
    canon_md = parse_metadata(canon)
    in_md = parse_metadata(in_node)
    merged_md = merge_metadata(canon_md, in_md)
    # Note merger lineage
    history = list(merged_md.get("merged_from", []))
    if in_node["id"] not in history:
        history.append(in_node["id"])
    merged_md["merged_from"] = history
    canon["metadata"] = merged_md

    merge_descriptions(canon, in_node)

    canon["confidence"] = max(canon.get("confidence", 0.0) or 0.0, in_node.get("confidence", 0.0) or 0.0)

    # Preserve `period` if canonical lacks one
    if not canon.get("period") and in_node.get("period"):
        canon["period"] = in_node["period"]

    # Preserve `needs_evidence` only if BOTH have it set
    if in_node.get("needs_evidence") and not canon.get("needs_evidence"):
        # canonical is presumed evidenced — don't reintroduce flag
        pass

    # Re-serialize metadata as string (matches existing KG convention)
    canon["metadata"] = json.dumps(canon["metadata"], ensure_ascii=False)


def edge_key(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e["source"], e["target"], e["relation"])


def parse_edge_metadata(e: dict[str, Any]) -> dict[str, Any]:
    md = e.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    if isinstance(md, str):
        try:
            parsed = json.loads(md)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def main() -> int:
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    by_id = {n["id"]: n for n in nodes}
    print(f"Loaded {len(nodes):,} nodes, {len(edges):,} edges")

    # Build remap table: merge_in_id -> canonical_id
    remap: dict[str, str] = {}
    merge_count_nodes = 0
    skipped_sets = 0

    for ms in MERGES:
        canon_id = ms["canonical"]
        canon = by_id.get(canon_id)
        if canon is None:
            print(f"\n[!] SKIP set '{ms['name']}': canonical {canon_id} not found")
            skipped_sets += 1
            continue
        print(f"\n=== {ms['name']} → {canon_id} ===")
        for mid in ms["merge_in"]:
            if mid not in by_id:
                print(f"  [skip-missing] {mid}")
                continue
            if mid == canon_id:
                continue
            in_node = by_id[mid]
            merge_one(canon, in_node)
            remap[mid] = canon_id
            merge_count_nodes += 1
            print(f"  [merged]  {mid}  →  {canon_id}")

    print(f"\nMerged {merge_count_nodes} nodes into {len(MERGES) - skipped_sets} canonicals")

    # Repoint edges
    repointed = 0
    self_loop = 0
    new_edges: list[dict[str, Any]] = []
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        new_src = remap.get(src, src)
        new_tgt = remap.get(tgt, tgt)
        if new_src != src or new_tgt != tgt:
            repointed += 1
            e = dict(e)
            e["source"] = new_src
            e["target"] = new_tgt
            md = parse_edge_metadata(e)
            md["remapped_from"] = {k: v for k, v in [("source", src), ("target", tgt)] if (k=="source" and src!=new_src) or (k=="target" and tgt!=new_tgt)}
            e["metadata"] = md
        if new_src == new_tgt:
            self_loop += 1
            continue
        k = edge_key(e)
        if k in seen:
            # Keep edge with higher confidence; preserve metadata union
            prev = seen[k]
            keep = e if (e.get("confidence", 0.0) or 0.0) >= (prev.get("confidence", 0.0) or 0.0) else prev
            other = prev if keep is e else e
            md = parse_edge_metadata(keep)
            other_md = parse_edge_metadata(other)
            for kk, vv in other_md.items():
                if kk not in md:
                    md[kk] = vv
            keep["metadata"] = md
            seen[k] = keep
        else:
            seen[k] = e

    new_edges = list(seen.values())
    dup_dropped = repointed - (len(edges) - len(new_edges) - self_loop) if False else (len(edges) - len(new_edges) - self_loop)
    print(f"\nEdge repoint:")
    print(f"  edges before:   {len(edges):,}")
    print(f"  repointed:      {repointed}")
    print(f"  self-loops dropped: {self_loop}")
    print(f"  exact dups dropped: {dup_dropped}")
    print(f"  edges after:    {len(new_edges):,}  (delta {len(new_edges) - len(edges):+d})")

    # Rebuild node list excluding merged-in IDs, preserving original order
    survivors = [n for n in nodes if n["id"] not in remap]
    print(f"\nNode list: {len(nodes):,} → {len(survivors):,} (dropped {len(nodes) - len(survivors)})")

    dump_jsonl(NODES_PATH, survivors)
    dump_jsonl(EDGES_PATH, new_edges)
    print(f"\nWrote {NODES_PATH} and {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
