"""Apply Frede 2011 B1 consolidation.

Idempotent orchestrator for the Frede 2011 batch B1 :
- Updates existing nodes (metadata enrichments only — no description rewriting)
  for Aristotle, Chrysippus, Zeno, Musonius, Epictetus, Alexander, Carneades,
  Plotinus, Origen, Augustine, Alcinous, Porphyry, Justin Martyr, Tatian,
  Cicero, Clement, key concepts (prohairesis, hekousion, eph' hemin, voluntas,
  synkatathesis), key works (Discourses, EN, De fato Alex, Enn VI.8, De princ,
  Philocalia, De lib. ar., De fato Cic), and modern scholars (Dihle, Bobzien,
  Sorabji, Kahn, Broadie, Kenny, Long, Sedley).
- Inserts new nodes : 1 scholar (Michael Frede), 1 publication (pub_frede_
  2011_free_will), 2 concepts (general schema, inner-life), 11 syntheses,
  14 scholarly arguments.
- Inserts edges : authorship of publication / syntheses / arguments,
  publication's discusses + cites_primary_source coverage of ancient persons /
  works / concepts, polemical critiques (esp. against Dihle), influence
  chains and precedes-chronology, argument-to-argument relations.

Skips operations whose target already exists with matching state, or whose
source/target node is missing in the KG.

Usage:
    cd [local-path]
    .venv/bin/python3 scripts/apply_frede_2011_b1_consolidation.py

NOTE: This script writes to data/kg/{nodes,edges}.jsonl. Parent agent
running the parallel-dispatch wave will apply this script (and the four
others) sequentially.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frede_2011_b1_data import UPDATES
from frede_2011_b1_edges import NEW_EDGES
from frede_2011_b1_inserts import (
    NEW_ARGUMENTS,
    NEW_CONCEPTS,
    NEW_PERSONS,
    NEW_PUBLICATIONS,
    NEW_SYNTHESES,
    NEW_WORKS,
)
from frede_2011_b1_utils import (
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


NEW_INSERTS = (
    NEW_PERSONS
    + NEW_PUBLICATIONS
    + NEW_WORKS
    + NEW_CONCEPTS
    + NEW_SYNTHESES
    + NEW_ARGUMENTS
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
        if "description" in u and u["description"] and node.get("description") != u["description"]:
            node["description"] = u["description"]
        if "description_en" in u and u["description_en"] and node.get("description_en") != u["description_en"]:
            node["description_en"] = u["description_en"]
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


def apply_edges(edges, new_edges, node_ids_set):
    applied = 0
    skipped_dup = 0
    skipped_missing = 0
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


def main() -> int:
    print(f"Loading {NODES_PATH} and {EDGES_PATH}...")
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    print(f"  {len(nodes):,} nodes, {len(edges):,} edges loaded")

    nodes_by_id = index_by_id(nodes)

    print(f"\n=== FREDE 2011 B1 UPDATES ({len(UPDATES)} candidates) ===")
    upd_applied, upd_skipped = apply_updates(nodes_by_id, UPDATES)
    print(f"  -> {upd_applied} applied, {upd_skipped} skipped (missing)")

    print(f"\n=== FREDE 2011 B1 INSERTS ({len(NEW_INSERTS)} candidates) ===")
    print(
        f"  Breakdown : {len(NEW_PERSONS)} persons + {len(NEW_PUBLICATIONS)} publications + "
        f"{len(NEW_WORKS)} works + {len(NEW_CONCEPTS)} concepts + "
        f"{len(NEW_SYNTHESES)} syntheses + {len(NEW_ARGUMENTS)} arguments"
    )
    ins_applied, ins_skipped = apply_inserts(nodes_by_id, NEW_INSERTS)
    print(f"  -> {ins_applied} applied, {ins_skipped} skipped (duplicates)")

    node_ids_set = set(nodes_by_id.keys())
    print(f"\n=== FREDE 2011 B1 EDGES ({len(NEW_EDGES)} candidates) ===")
    edge_applied, edge_skipped_dup, edge_skipped_missing = apply_edges(
        edges, NEW_EDGES, node_ids_set
    )
    print(
        f"  -> {edge_applied} applied, {edge_skipped_dup} dup-skipped, "
        f"{edge_skipped_missing} missing-skipped"
    )

    existing_ids = {n["id"] for n in nodes}
    new_node_ids = [n["id"] for n in NEW_INSERTS if n["id"] not in existing_ids]
    final_nodes = nodes + [nodes_by_id[nid] for nid in new_node_ids]

    print(f"\nFinal: {len(final_nodes):,} nodes, {len(edges):,} edges")

    dump_jsonl(NODES_PATH, final_nodes)
    dump_jsonl(EDGES_PATH, edges)
    print(f"Wrote {NODES_PATH} and {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
