"""Apply merged fragment mappings to the local KG snapshot JSONL.

Reads:
  - data/doxographical_audit/fragment_mappings_merged.jsonl
  - data/kg/nodes.jsonl (will be backed up to nodes.jsonl.bak before write)
  - data/kg/edges.jsonl (backup similarly)

Writes:
  - Updated data/kg/nodes.jsonl with metadata.fragment_collections etc. merged
  - Updated data/kg/edges.jsonl with new attested_by edges where applicable

This lets us materialise mappings even when the live Supabase pooler is
unreachable. Re-applying to the DB later is handled by
``doxographical_mapper.py`` (idempotent via jsonb_set).
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger("apply_mappings_to_snapshot")

ROOT = Path(__file__).resolve().parents[2]
MAPPINGS = ROOT / "data" / "doxographical_audit" / "fragment_mappings_merged.jsonl"
NODES = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES = ROOT / "data" / "kg" / "edges.jsonl"


PHILO_NODE_REMAP: dict[str, str] = {
    # Stale IDs in earlier Kimi rows → canonical IDs in snapshot
    "person_zeno_of_citium": "person_zeno_citium_334_262bce",
    "person_cleanthes": "person_cleanthes_assos_330_230bce",
    "person_posidonius_135_51bce_e5f6g7h8": "person_posidonius_apameia_135_51bce",
    "person_epicurus_341_270bce_a1b2c3d4": "person_epicurus_341_270bce_j0k1l2m3",
    "person_heraclitus": "person_heraclitus_fl500bce_a1b2c3d4",
    "person_parmenides": "person_parmenides_of_elea_44a65114",
    "person_democritus": "person_democritus_460_370bce_g7h8i9j0",
    "person_leucippus": "person_leucippus_and_democritus_8a42be84",
}


def load_mappings(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            r = json.loads(line)
            pn = r.get("philosopher_node_id")
            if pn in PHILO_NODE_REMAP:
                r["philosopher_node_id"] = PHILO_NODE_REMAP[pn]
            out[r["passage_id"]] = r
    return out


def merge_metadata(
    existing: dict[str, Any] | None, mapping: dict[str, Any]
) -> dict[str, Any]:
    md = dict(existing or {})
    md["attestation_type"] = mapping.get("attestation_type", md.get("attestation_type"))
    if mapping.get("primary_attestation"):
        md["primary_attestation"] = mapping["primary_attestation"]
    if mapping.get("fragment_collections"):
        md["fragment_collections"] = mapping["fragment_collections"]
    md["extant_in_original"] = mapping.get(
        "extant_in_original", md.get("extant_in_original", False)
    )
    md["extant_in_translation_only"] = mapping.get(
        "extant_in_translation_only", md.get("extant_in_translation_only", False)
    )
    md["doxographical_confidence"] = mapping.get(
        "confidence", md.get("doxographical_confidence", "medium")
    )
    if mapping.get("note"):
        md["doxographical_note"] = mapping["note"]
    md["doxographical_source"] = mapping.get("doxographical_source", "merged")
    if mapping.get("fragmented_philosopher"):
        md["fragmented_philosopher"] = mapping["fragmented_philosopher"]
    if mapping.get("philosopher_node_id"):
        md["fragmented_philosopher_node_id"] = mapping["philosopher_node_id"]
    if mapping.get("needs_review"):
        md["needs_review"] = True
    if mapping.get("doxographical_contributing_sources"):
        md["doxographical_contributing_sources"] = mapping[
            "doxographical_contributing_sources"
        ]
    return md


def apply_to_nodes(
    nodes_path: Path, mappings: dict[str, dict[str, Any]], *, dry_run: bool
) -> dict[str, int]:
    stats = {"nodes_scanned": 0, "nodes_updated": 0, "mappings_unused": 0}
    matched_ids: set[str] = set()
    if dry_run:
        with nodes_path.open() as fh:
            for line in fh:
                n = json.loads(line)
                stats["nodes_scanned"] += 1
                if n.get("node_id") in mappings:
                    matched_ids.add(n["node_id"])
                    stats["nodes_updated"] += 1
    else:
        backup = nodes_path.with_suffix(".jsonl.bak")
        shutil.copy(nodes_path, backup)
        logger.info("Backed up %s → %s", nodes_path, backup)
        tmp = nodes_path.with_suffix(".jsonl.tmp")
        with nodes_path.open() as src, tmp.open("w") as dst:
            for line in src:
                n = json.loads(line)
                stats["nodes_scanned"] += 1
                pid = n.get("node_id")
                if pid in mappings:
                    n["metadata"] = merge_metadata(n.get("metadata"), mappings[pid])
                    matched_ids.add(pid)
                    stats["nodes_updated"] += 1
                dst.write(json.dumps(n, ensure_ascii=False) + "\n")
        tmp.replace(nodes_path)
    stats["mappings_unused"] = len(set(mappings) - matched_ids)
    return stats


def edge_signature(e: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(e.get("source_id") or e.get("source", "")),
        str(e.get("target_id") or e.get("target", "")),
        str(e.get("relation", "")),
    )


def apply_attested_by_edges(
    edges_path: Path, mappings: dict[str, dict[str, Any]], *, dry_run: bool
) -> dict[str, int]:
    """Add attested_by edges from fragment-passage → fragmented-philosopher node.

    The semantics: when Cicero De Fato 42 transmits a Chrysippus fragment, we
    add ``passage_cic_fat_42 --attested_by--> person_chrysippus``. This makes
    the doxographical attribution traversable in the graph.
    """
    stats = {
        "edges_proposed": 0,
        "edges_added": 0,
        "edges_skipped_no_philosopher": 0,
        "edges_existing": 0,
    }
    new_edges: list[dict[str, Any]] = []
    for pid, m in mappings.items():
        philo_node = m.get("philosopher_node_id")
        if not philo_node:
            stats["edges_skipped_no_philosopher"] += 1
            continue
        stats["edges_proposed"] += 1
        new_edges.append(
            {
                "source_id": pid,
                "target_id": philo_node,
                "source": pid,
                "target": philo_node,
                "relation": "attested_by",
                "weight": 1.0,
                "metadata": {
                    "doxographical": True,
                    "confidence": m.get("confidence", "medium"),
                    "fragment_collections": m.get("fragment_collections", []),
                    "fragmented_philosopher": m.get("fragmented_philosopher"),
                    "source": m.get("doxographical_source", "merged"),
                },
            }
        )

    existing_sigs: set[tuple[str, str, str]] = set()
    with edges_path.open() as fh:
        for line in fh:
            try:
                e = json.loads(line)
                existing_sigs.add(edge_signature(e))
            except json.JSONDecodeError:
                continue

    to_add = [e for e in new_edges if edge_signature(e) not in existing_sigs]
    stats["edges_existing"] = stats["edges_proposed"] - len(to_add)

    if dry_run:
        stats["edges_added"] = len(to_add)
        return stats

    if to_add:
        backup = edges_path.with_suffix(".jsonl.bak")
        if not backup.exists():
            shutil.copy(edges_path, backup)
        with edges_path.open("a", encoding="utf-8") as fh:
            for e in to_add:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    stats["edges_added"] = len(to_add)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mappings", type=Path, default=MAPPINGS)
    parser.add_argument("--nodes", type=Path, default=NODES)
    parser.add_argument("--edges", type=Path, default=EDGES)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-edges", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    mappings = load_mappings(args.mappings)
    logger.info("Loaded %d merged mappings", len(mappings))

    node_stats = apply_to_nodes(args.nodes, mappings, dry_run=args.dry_run)
    edge_stats = (
        {"edges_proposed": 0, "edges_added": 0}
        if args.skip_edges
        else apply_attested_by_edges(args.edges, mappings, dry_run=args.dry_run)
    )
    print(
        json.dumps(
            {"nodes": node_stats, "edges": edge_stats, "dry_run": args.dry_run},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
