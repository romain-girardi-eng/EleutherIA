#!/usr/bin/env python3
"""Gate and optionally apply the golden-corridor edges-only delta.

The operation is idempotent by ``(source, relation, target)``.  The default is
a read-only dry-run.  ``--apply`` is the only mode that writes, and it writes
only ``data/kg/edges.jsonl`` after the novel subset passes
``check_ingestion_rules.py --new-only`` with no BLOCK.

Usage:
    python3 scripts/ingest_2026_08_17_corridor_wiring.py
    python3 scripts/ingest_2026_08_17_corridor_wiring.py --dry-run
    python3 scripts/ingest_2026_08_17_corridor_wiring.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "data/kg/nodes.jsonl"
EDGES = ROOT / "data/kg/edges.jsonl"
DELTA = ROOT / "scripts/data_2026_08_17_corridor_wiring.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
BACKUP = EDGES.with_name(f"{EDGES.name}.bak-corridor_wiring")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def triple(edge: dict) -> tuple[str, str, str]:
    return edge["source"], edge["relation"], edge["target"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="append the gated novel edges (default is dry-run)",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="validate only; this is already the default",
    )
    return parser.parse_args()


def assert_delta_invariants(delta: dict, node_ids: set[str]) -> None:
    assert set(delta) == {"nodes", "edges"}, (
        "delta must contain exactly nodes and edges"
    )
    assert delta["nodes"] == [], "corridor delta must remain edges-only"
    assert isinstance(delta["edges"], list), "edges must be a list"

    edge_ids: list[str] = []
    triples: list[tuple[str, str, str]] = []
    for edge in delta["edges"]:
        required = {
            "edge_id",
            "source",
            "source_id",
            "relation",
            "target",
            "target_id",
            "metadata",
        }
        missing = required - set(edge)
        assert not missing, f"{edge.get('edge_id', '<unknown>')}: missing {missing}"
        assert edge["source"] == edge["source_id"], (
            f"{edge['edge_id']}: source/source_id mismatch"
        )
        assert edge["target"] == edge["target_id"], (
            f"{edge['edge_id']}: target/target_id mismatch"
        )
        assert edge["source"] != edge["target"], (
            f"{edge['edge_id']}: self-edge forbidden"
        )
        assert edge["source"] in node_ids, (
            f"{edge['edge_id']}: unresolved source {edge['source']}"
        )
        assert edge["target"] in node_ids, (
            f"{edge['edge_id']}: unresolved target {edge['target']}"
        )
        attestation = edge["metadata"].get("attested_by")
        assert isinstance(attestation, (str, list)) and attestation, (
            f"{edge['edge_id']}: metadata.attested_by is required"
        )
        edge_ids.append(edge["edge_id"])
        triples.append(triple(edge))

    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge_id in delta"
    assert len(triples) == len(set(triples)), "duplicate edge triple in delta"


def novel_edges(delta_edges: list[dict], existing_edges: list[dict]) -> list[dict]:
    existing_ids = {edge["edge_id"]: triple(edge) for edge in existing_edges}
    existing_triples = {triple(edge) for edge in existing_edges}
    novel: list[dict] = []

    for edge in delta_edges:
        edge_triple = triple(edge)
        prior = existing_ids.get(edge["edge_id"])
        if prior is not None:
            if prior != edge_triple:
                raise AssertionError(
                    f"edge_id collision: {edge['edge_id']} maps to {prior}, "
                    f"delta proposes {edge_triple}"
                )
            continue
        if edge_triple in existing_triples:
            continue
        novel.append(edge)
    return novel


def run_gate(edges: list[dict]) -> None:
    payload = {"nodes": [], "edges": edges}
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        subset_path = Path(handle.name)

    try:
        result = subprocess.run(
            [sys.executable, str(GATE), "--new-only", str(subset_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        subset_path.unlink(missing_ok=True)

    print("--- check_ingestion_rules.py --new-only (novel subset) ---")
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode:
        raise RuntimeError(f"ingestion gate failed with exit {result.returncode}")


def write_edges_atomically(existing: list[dict], novel: list[dict]) -> None:
    shutil.copy2(EDGES, BACKUP)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{EDGES.name}.", suffix=".tmp", dir=EDGES.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for edge in [*existing, *novel]:
                handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, EDGES)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def main() -> int:
    args = parse_args()
    node_ids = {node["id"] for node in read_jsonl(NODES)}
    existing_edges = read_jsonl(EDGES)
    delta = json.loads(DELTA.read_text(encoding="utf-8"))

    assert_delta_invariants(delta, node_ids)
    novel = novel_edges(delta["edges"], existing_edges)
    run_gate(novel)

    print("--- corridor wiring summary ---")
    print(f"mode: {'apply' if args.apply else 'dry-run'}")
    print(f"delta edges: {len(delta['edges'])}")
    print(f"novel edges: {len(novel)}")
    print(f"already present: {len(delta['edges']) - len(novel)}")
    print("unresolved endpoints: 0")

    if not args.apply:
        print("dry-run: nothing written")
        return 0

    write_edges_atomically(existing_edges, novel)
    post_edges = read_jsonl(EDGES)
    post_triples = {triple(edge) for edge in post_edges}
    assert all(triple(edge) in post_triples for edge in novel)
    print(f"applied: {len(novel)} edges")
    print(f"backup: {BACKUP.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
