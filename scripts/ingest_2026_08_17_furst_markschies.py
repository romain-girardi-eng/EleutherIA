#!/usr/bin/env python3
"""Gate and optionally apply the 2026-08-17 Fürst/Markschies PDF delta.

Idempotent merge of scripts/data_2026_08_17_furst_markschies.json into
data/kg/{nodes,edges}.jsonl:
- node ids already present are skipped;
- edge (source, relation, target) triples already present are skipped;
- all edge endpoints must resolve against existing plus delta nodes;
- the novel subset must pass check_ingestion_rules.py --new-only with
  BLOCK 0 before anything is written;
- invariants are asserted before save and backups use suffix
  .bak-furst-markschies.

Usage: python3 scripts/ingest_2026_08_17_furst_markschies.py [--apply]
Default is dry-run.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_furst_markschies.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
BAK_SUFFIX = ".bak-furst-markschies"
INGEST_SCRIPT = "scripts/ingest_2026_08_17_furst_markschies.py"
DIALECTICAL_RELATIONS = {"opposes", "agrees_with", "critiques"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def triple(edge: dict) -> tuple[str, str, str]:
    return (
        edge["source"],
        edge.get("relation") or edge.get("type"),
        edge["target"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="append the gated novel subset; otherwise perform a dry-run",
    )
    return parser.parse_args()


def assert_delta_invariants(delta: dict) -> None:
    assert set(delta) == {"nodes", "edges"}, "delta must contain nodes and edges only"
    assert isinstance(delta["nodes"], list) and isinstance(delta["edges"], list)

    node_ids = [node["id"] for node in delta["nodes"]]
    assert len(node_ids) == len(set(node_ids)), "duplicate node id within delta"
    for node in delta["nodes"]:
        assert node["id"] == node["node_id"], f"id/node_id mismatch: {node['id']}"
        metadata = node.get("metadata")
        assert isinstance(metadata, dict), f"metadata must be an object: {node['id']}"
        provenance = metadata.get("provenance")
        assert isinstance(provenance, dict), f"missing provenance: {node['id']}"
        assert provenance.get("source"), f"missing provenance source: {node['id']}"
        assert provenance.get("ingested_at"), f"missing ingested_at: {node['id']}"
        assert provenance.get("ingest_script") == INGEST_SCRIPT

        if node["type"] == "argument":
            assert node["id"].startswith("scholarly_argument_")
            assert metadata.get("scholar_id"), f"missing scholar_id: {node['id']}"
            assert metadata.get("scholarly_work_id"), (
                f"missing scholarly_work_id: {node['id']}"
            )
            assert metadata.get("page_range"), f"missing page_range: {node['id']}"
            source_file = metadata.get("source_file")
            assert source_file and source_file.endswith(".pdf"), (
                f"source_file must be a .pdf path: {node['id']}"
            )
            assert provenance["source"] == source_file, (
                f"source_file/provenance mismatch: {node['id']}"
            )

    edge_ids = [edge["edge_id"] for edge in delta["edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge id within delta"
    triples = [triple(edge) for edge in delta["edges"]]
    assert len(triples) == len(set(triples)), "duplicate edge triple within delta"
    for edge in delta["edges"]:
        assert edge["source"] == edge["source_id"]
        assert edge["target"] == edge["target_id"]
        assert edge["source"] != edge["target"]
        if edge["relation"] in DIALECTICAL_RELATIONS:
            attestation = edge.get("metadata", {}).get("attested_by", "")
            assert attestation and re.search(
                r"\b(?:p{1,2}\.|pages?)\s*\d", attestation
            ), f"dialectical edge lacks paged attestation: {edge['edge_id']}"

    delta_triples = set(triples)
    for node in delta["nodes"]:
        if node["type"] != "argument":
            continue
        node_id = node["id"]
        metadata = node["metadata"]
        assert (node_id, "created_by", metadata["scholar_id"]) in delta_triples
        assert (node_id, "advanced_in", metadata["scholarly_work_id"]) in delta_triples


def main() -> int:
    args = parse_args()

    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert_delta_invariants(delta)

    nodes = read_jsonl(NODES)
    edges = read_jsonl(EDGES)
    existing_ids = {node["id"] for node in nodes}
    existing_triples = {triple(edge) for edge in edges}
    existing_edge_ids = {edge.get("edge_id") for edge in edges if edge.get("edge_id")}

    new_nodes = [node for node in delta["nodes"] if node["id"] not in existing_ids]
    skipped_nodes = len(delta["nodes"]) - len(new_nodes)
    all_ids = existing_ids | {node["id"] for node in delta["nodes"]}

    new_edges: list[dict] = []
    skipped_edges = 0
    unresolved: list[tuple[str, str, str]] = []
    edge_id_collisions: list[str] = []
    seen_triples = set(existing_triples)
    for edge in delta["edges"]:
        edge_triple = triple(edge)
        if edge_triple in seen_triples:
            skipped_edges += 1
            continue
        if edge["source"] not in all_ids or edge["target"] not in all_ids:
            unresolved.append(edge_triple)
            continue
        if edge["edge_id"] in existing_edge_ids:
            edge_id_collisions.append(edge["edge_id"])
            continue
        new_edges.append(edge)
        seen_triples.add(edge_triple)

    print(f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges")
    print(
        f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges "
        f"(skipped existing: {skipped_nodes} nodes, {skipped_edges} edges)"
    )
    if unresolved:
        print(
            f"FATAL: {len(unresolved)} edges with unresolvable endpoints: "
            f"{unresolved[:5]}"
        )
        return 1
    if edge_id_collisions:
        print(
            f"FATAL: {len(edge_id_collisions)} novel edges reuse existing edge ids: "
            f"{edge_id_collisions[:5]}"
        )
        return 1

    subset_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            suffix="-furst-markschies.json",
            encoding="utf-8",
            delete=False,
        ) as handle:
            json.dump(
                {"nodes": new_nodes, "edges": new_edges},
                handle,
                ensure_ascii=False,
            )
            subset_path = Path(handle.name)
        gate = subprocess.run(
            [sys.executable, str(GATE), "--new-only", str(subset_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if subset_path is not None:
            subset_path.unlink(missing_ok=True)

    gate_output = gate.stdout.strip()
    print(gate_output.splitlines()[-1] if gate_output else gate.stderr[-200:])
    if gate.returncode != 0:
        print("FATAL: ingestion gate failed on the novel subset - nothing written")
        return 1

    merged_nodes = nodes + new_nodes
    merged_ids = {node["id"] for node in merged_nodes}
    assert len(merged_ids) == len(merged_nodes), "duplicate node id after merge"
    assert all(
        edge["source"] == edge["source_id"]
        and edge["target"] == edge["target_id"]
        for edge in new_edges
    )
    assert all(
        edge["source"] in merged_ids and edge["target"] in merged_ids
        for edge in new_edges
    )

    if not args.apply:
        print("dry-run: nothing written (use --apply)")
        return 0

    shutil.copy2(NODES, str(NODES) + BAK_SUFFIX)
    shutil.copy2(EDGES, str(EDGES) + BAK_SUFFIX)
    with NODES.open("a", encoding="utf-8") as handle:
        for node in new_nodes:
            handle.write(json.dumps(node, ensure_ascii=False) + "\n")
    with EDGES.open("a", encoding="utf-8") as handle:
        for edge in new_edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
    print(f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
