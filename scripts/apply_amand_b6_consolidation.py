"""Apply Amand B6 consolidation (Eusebius + Basil + Gregory of Nazianzus).

Idempotent orchestrator:
- Updates 3 existing nodes (description / metadata enrichments)
- Inserts 39 new nodes (1 person + 5 works + 11 syntheses + 15 arguments + 7 concepts)
- Inserts ~75 edges (evidenced_by, cites_primary_source, transmits_to,
  influenced_by, cites, authored_by, contains, addresses, claimed_by)

Skips operations whose target already exists with matching state.

Usage:
    cd [local-path]
    python3 scripts/apply_amand_b6_consolidation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from this script's directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from amand_b6_data import UPDATES
from amand_b6_edges import NEW_EDGES
from amand_b6_inserts import NEW_INSERTS
from amand_b6_utils import (
    EDGES_PATH,
    NODES_PATH,
    dump_jsonl,
    dump_metadata,
    edge_exists,
    index_by_id,
    load_jsonl,
    merge_metadata,
    parse_metadata,
)


def apply_updates(nodes_by_id, updates):
    applied = 0
    skipped_missing = 0
    for u in updates:
        nid = u["id"]
        node = nodes_by_id.get(nid)
        if node is None:
            print(f"  [SKIP-MISSING] {nid}")
            skipped_missing += 1
            continue
        # Description
        if "description" in u and u["description"] and node.get("description") != u["description"]:
            node["description"] = u["description"]
        if "description_en" in u and u["description_en"] and node.get("description_en") != u["description_en"]:
            node["description_en"] = u["description_en"]
        # Metadata merge
        if "metadata_updates" in u:
            existing = parse_metadata(node)
            merged = merge_metadata(existing, u["metadata_updates"])
            node["metadata"] = dump_metadata(merged)
        applied += 1
        print(f"  [UPDATED] {nid}")
    return applied, skipped_missing


def apply_inserts(nodes_by_id, inserts):
    applied = 0
    skipped_dup = 0
    for n in inserts:
        nid = n["id"]
        if nid in nodes_by_id:
            print(f"  [SKIP-DUP] {nid}")
            skipped_dup += 1
            continue
        nodes_by_id[nid] = n
        applied += 1
        print(f"  [INSERTED] {nid}")
    return applied, skipped_dup


def apply_edges(edges, new_edges):
    applied = 0
    skipped_dup = 0
    skipped_missing = 0
    # Need fast existence check for nodes
    node_ids_set = {n["id"] for n in nodes_by_id_global.values()}
    for e in new_edges:
        src = e["source"]
        tgt = e["target"]
        rel = e["relation"]
        if src not in node_ids_set:
            print(f"  [SKIP-NO-SRC] {src} -- {rel} --> {tgt}")
            skipped_missing += 1
            continue
        if tgt not in node_ids_set:
            print(f"  [SKIP-NO-TGT] {src} -- {rel} --> {tgt}")
            skipped_missing += 1
            continue
        if edge_exists(edges, src, tgt, rel):
            print(f"  [SKIP-DUP-EDGE] {src} -- {rel} --> {tgt}")
            skipped_dup += 1
            continue
        edges.append(e)
        applied += 1
        print(f"  [EDGE+] {src} -- {rel} --> {tgt}")
    return applied, skipped_dup, skipped_missing


nodes_by_id_global: dict = {}


def main() -> int:
    print(f"Loading {NODES_PATH} and {EDGES_PATH}...")
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"  {len(nodes):,} nodes, {len(edges):,} edges loaded")

    global nodes_by_id_global
    nodes_by_id_global = index_by_id(nodes)

    print("\n=== B6 UPDATES (3 expected) ===")
    upd_applied, upd_skipped = apply_updates(nodes_by_id_global, UPDATES)
    print(f"  -> {upd_applied} applied, {upd_skipped} skipped (missing)")

    print(f"\n=== B6 INSERTS (nodes, {len(NEW_INSERTS)} candidates) ===")
    ins_applied, ins_skipped = apply_inserts(nodes_by_id_global, NEW_INSERTS)
    print(f"  -> {ins_applied} applied, {ins_skipped} skipped (duplicates)")

    print(f"\n=== B6 EDGES ({len(NEW_EDGES)} candidates) ===")
    edge_applied, edge_skipped_dup, edge_skipped_missing = apply_edges(edges, NEW_EDGES)
    print(f"  -> {edge_applied} applied, {edge_skipped_dup} dup-skipped, {edge_skipped_missing} missing-skipped")

    # Recreate nodes list preserving insertion order: existing nodes (in original
    # order, with updates merged in-place) followed by new nodes (in NEW_INSERTS order).
    existing_ids = {n["id"] for n in nodes}
    new_node_ids = [n["id"] for n in NEW_INSERTS if n["id"] not in existing_ids]
    final_nodes = nodes + [nodes_by_id_global[nid] for nid in new_node_ids]

    print(f"\nFinal: {len(final_nodes):,} nodes, {len(edges):,} edges")

    dump_jsonl(NODES_PATH, final_nodes)
    dump_jsonl(EDGES_PATH, edges)
    print(f"Wrote {NODES_PATH} and {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
