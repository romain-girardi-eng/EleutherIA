#!/usr/bin/env python3
"""Apply the 2026-08-17 reading-ingestion wave B delta to the KG.

The default mode is a read-only dry-run.  ``--apply`` performs an
idempotent merge only after the novel subset passes R1-R18 with BLOCK 0.
Existing node ids and edge triples are skipped; enrichment records can
promote exact existing publication shells under explicit preconditions.

Usage: python3 scripts/ingest_2026_08_17_reading_wave_b.py [--apply]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_reading_wave_b.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
G6_PROBE = ROOT / "graphrag/tests/g6/test_reachability_probe.py"
INGEST_SCRIPT = "scripts/ingest_2026_08_17_reading_wave_b.py"
BAK_SUFFIX = ".bak-reading-wave-b"
DIALECTICAL_RELATIONS = {
    "opposes",
    "critiques",
    "responds_to",
    "refutes",
    "contrasts_with",
    "agrees_with",
    "supports",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the gated novel subset; default is a dry-run",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def metadata(record: dict) -> dict:
    value = record.get("metadata") or {}
    return json.loads(value) if isinstance(value, str) else value


def set_metadata(record: dict, value: dict) -> None:
    record["metadata"] = (
        json.dumps(value, ensure_ascii=False)
        if isinstance(record.get("metadata"), str)
        else value
    )


def triple(edge: dict) -> tuple[str, str, str]:
    return (
        edge["source"],
        edge.get("relation") or edge.get("type"),
        edge["target"],
    )


def pinned_opposes_count() -> int:
    source = G6_PROBE.read_text(encoding="utf-8")
    match = re.search(r"assert len\(all_opposes\) == (\d+)", source)
    if not match:
        raise AssertionError(f"cannot locate G6 opposes pin in {G6_PROBE}")
    return int(match.group(1))


def assert_delta_invariants(delta: dict) -> None:
    assert set(delta) == {"nodes", "edges", "enrichments"}, (
        "delta must contain nodes, edges, and enrichments only"
    )
    assert all(isinstance(delta[key], list) for key in delta)

    node_ids = [node["id"] for node in delta["nodes"]]
    assert len(node_ids) == len(set(node_ids)), "duplicate node id within delta"
    for node in delta["nodes"]:
        assert node["id"] == node["node_id"], f"id/node_id mismatch: {node['id']}"
        md = metadata(node)
        provenance = md.get("provenance")
        assert isinstance(provenance, dict), f"missing provenance: {node['id']}"
        assert provenance.get("source"), f"missing provenance source: {node['id']}"
        assert provenance.get("ingested_at"), f"missing ingested_at: {node['id']}"
        assert provenance.get("ingest_script") == INGEST_SCRIPT, node["id"]

        if node["type"] == "publication":
            assert md.get("citation_verdict") == "read_and_extracted", node["id"]
            assert md.get("citation_verified") is True, node["id"]
            assert md.get("source_rank"), node["id"]
        if node["type"] == "argument":
            assert node["id"].startswith("scholarly_argument_")
            assert md.get("scholar_id"), f"missing scholar_id: {node['id']}"
            assert md.get("scholarly_work_id"), (
                f"missing scholarly_work_id: {node['id']}"
            )
            assert md.get("page_range"), f"missing page_range: {node['id']}"
            source_file = md.get("source_file")
            assert source_file and source_file.endswith(".pdf"), (
                f"source_file must be the read PDF: {node['id']}"
            )
            assert provenance["source"] == source_file, (
                f"source_file/provenance mismatch: {node['id']}"
            )

    edge_ids = [edge["edge_id"] for edge in delta["edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge id within delta"
    triples = [triple(edge) for edge in delta["edges"]]
    assert len(triples) == len(set(triples)), "duplicate edge triple within delta"
    for edge in delta["edges"]:
        assert edge["source"] == edge["source_id"], edge["edge_id"]
        assert edge["target"] == edge["target_id"], edge["edge_id"]
        assert edge["source"] != edge["target"], edge["edge_id"]
        attestation = metadata(edge).get("attested_by", "")
        assert attestation and re.search(r"\bpp?\.\s*\d", attestation), (
            f"edge lacks a page attestation: {edge['edge_id']}"
        )
        if edge["relation"] in DIALECTICAL_RELATIONS:
            assert attestation, (
                f"dialectical edge lacks attested_by: {edge['edge_id']}"
            )

    delta_triples = set(triples)
    for node in delta["nodes"]:
        if node["type"] != "argument":
            continue
        node_id = node["id"]
        md = metadata(node)
        assert (node_id, "created_by", md["scholar_id"]) in delta_triples
        assert (node_id, "advanced_in", md["scholarly_work_id"]) in delta_triples

    delta_ids = set(node_ids)
    enrichment_targets: set[str] = set()
    for enrichment in delta["enrichments"]:
        target_id = enrichment["target_id"]
        assert target_id not in delta_ids, (
            f"enrichment must target an existing node: {target_id}"
        )
        assert target_id not in enrichment_targets, (
            f"duplicate enrichment target: {target_id}"
        )
        enrichment_targets.add(target_id)
        assert isinstance(enrichment.get("preconditions"), dict)
        updates = enrichment.get("set_metadata")
        assert isinstance(updates, dict) and updates, target_id
        if "citation_verdict" in updates:
            assert updates["citation_verdict"] == "read_and_extracted"
            assert updates.get("source_rank"), target_id


def prepare_enrichments(
    nodes: list[dict], enrichments: list[dict]
) -> tuple[list[dict], int, int, list[str]]:
    prepared = copy.deepcopy(nodes)
    by_id = {node["id"]: node for node in prepared}
    enrichable = 0
    already_applied = 0
    failures: list[str] = []

    for enrichment in enrichments:
        target_id = enrichment["target_id"]
        target = by_id.get(target_id)
        if target is None:
            failures.append(f"missing enrichment target {target_id}")
            continue
        md = metadata(target)
        updates = enrichment["set_metadata"]
        if all(md.get(key) == value for key, value in updates.items()):
            already_applied += 1
            continue

        preconditions = enrichment["preconditions"]
        ok = True
        if "type" in preconditions and target.get("type") != preconditions["type"]:
            ok = False
        if "label" in preconditions and target.get("label") != preconditions["label"]:
            ok = False
        for key, value in preconditions.get("metadata", {}).items():
            if md.get(key) != value:
                ok = False
        if not ok:
            failures.append(f"failed enrichment preconditions for {target_id}")
            continue

        md.update(updates)
        set_metadata(target, md)
        enrichable += 1

    return prepared, enrichable, already_applied, failures


def write_jsonl_atomic(path: Path, rows: list[dict]) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            encoding="utf-8",
            delete=False,
        ) as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert_delta_invariants(delta)

    nodes = read_jsonl(NODES)
    edges = read_jsonl(EDGES)
    by_id = {node["id"]: node for node in nodes}
    existing_ids = set(by_id)
    existing_triples = {triple(edge) for edge in edges}
    existing_edge_ids = {
        edge.get("edge_id") for edge in edges if edge.get("edge_id")
    }

    conflicts: list[str] = []
    new_nodes: list[dict] = []
    skipped_nodes = 0
    for node in delta["nodes"]:
        existing = by_id.get(node["id"])
        if existing is None:
            new_nodes.append(node)
            continue
        if existing.get("type") != node.get("type") or existing.get("label") != node.get("label"):
            conflicts.append(f"node-id identity conflict: {node['id']}")
        else:
            skipped_nodes += 1

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

    prepared_nodes, enrichable, enriched_already, enrichment_failures = (
        prepare_enrichments(nodes, delta["enrichments"])
    )

    print(
        f"delta: {len(delta['nodes'])} nodes / {len(delta['edges'])} edges / "
        f"{len(delta['enrichments'])} enrichments"
    )
    print(
        f"novel: {len(new_nodes)} nodes / {len(new_edges)} edges "
        f"(skipped existing: {skipped_nodes} nodes, {skipped_edges} edges)"
    )
    print(
        f"enrichments: enrichable={enrichable}, already-applied={enriched_already}"
    )

    failures = [
        *conflicts,
        *enrichment_failures,
    ]
    if unresolved:
        failures.append(f"{len(unresolved)} unresolvable edges: {unresolved[:5]}")
    if edge_id_collisions:
        failures.append(
            f"{len(edge_id_collisions)} edge-id collisions: {edge_id_collisions[:5]}"
        )
    if failures:
        for failure in failures:
            print(f"FATAL: {failure}")
        print("nothing written")
        return 1

    current_opposes = sum(edge.get("relation") == "opposes" for edge in edges)
    novel_opposes = sum(edge["relation"] == "opposes" for edge in new_edges)
    post_apply_opposes = current_opposes + novel_opposes
    g6_pin: int | None = None
    if novel_opposes:
        g6_pin = pinned_opposes_count()
        print(
            f"opposes: current={current_opposes}, novel={novel_opposes}, "
            f"post-apply={post_apply_opposes}, g6-pin={g6_pin}"
        )
    else:
        print(
            f"opposes: current={current_opposes}, novel=0, "
            f"post-apply={post_apply_opposes}, g6-pin-check=not-required"
        )

    subset_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            suffix="-reading-wave-b.json",
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

    if gate.stdout.strip():
        print(gate.stdout.rstrip())
    if gate.stderr.strip():
        print(gate.stderr.rstrip(), file=sys.stderr)
    if gate.returncode != 0:
        print("FATAL: ingestion gate failed - nothing written")
        return 1

    merged_nodes = prepared_nodes + new_nodes
    merged_ids = {node["id"] for node in merged_nodes}
    assert len(merged_ids) == len(merged_nodes), "duplicate node id after merge"
    assert all(
        edge["source"] in merged_ids and edge["target"] in merged_ids
        for edge in new_edges
    )

    if not args.apply:
        print("dry-run: nothing written (use --apply)")
        return 0

    if novel_opposes and g6_pin != post_apply_opposes:
        print(
            f"FATAL: G6 opposes pin is {g6_pin}, but post-apply count is "
            f"{post_apply_opposes}; update the pin in the same commit before --apply"
        )
        print("nothing written")
        return 1

    shutil.copy2(NODES, str(NODES) + BAK_SUFFIX)
    shutil.copy2(EDGES, str(EDGES) + BAK_SUFFIX)
    write_jsonl_atomic(NODES, merged_nodes)
    with EDGES.open("a", encoding="utf-8") as handle:
        for edge in new_edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
    print(
        f"applied: +{len(new_nodes)} nodes, +{len(new_edges)} edges, "
        f"{enrichable} nodes enriched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
