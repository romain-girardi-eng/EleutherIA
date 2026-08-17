#!/usr/bin/env python3
"""Gate and optionally apply the 2026-08-17 historiographical fault-line edges.

The delta is deliberately edges-only.  Default execution is a dry-run: it
checks endpoints, duplicate triples in both directions, same-scholar wiring,
R16 attestations, the ingestion gate, and the post-apply ``opposes`` count,
without writing to ``data/kg`` or ``data/corpus``.

The future apply is intentionally coupled to the G6 churn pin: ``--apply``
refuses to append the edges unless ``graphrag/tests/g6/test_reachability_probe.py``
already pins the exact post-apply ``opposes`` count.

Usage:
    python3 scripts/ingest_2026_08_17_faultlines_wiring.py
    python3 scripts/ingest_2026_08_17_faultlines_wiring.py --apply
"""

from __future__ import annotations

import argparse
import collections
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
DELTA = ROOT / "scripts/data_2026_08_17_faultlines_wiring.json"
GATE = ROOT / "scripts/check_ingestion_rules.py"
G6_PROBE = ROOT / "graphrag/tests/g6/test_reachability_probe.py"
BAK_SUFFIX = ".bak-faultlines_wiring"

ALLOWED_RELATIONS = {
    "opposes",
    "agrees_with",
    "critiques",
    "responds_to",
    "extends",
}
PAGE_RE = re.compile(r"\b(?:p{1,2}\.)\s*(?:\d+|[ivxlcdm]+)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="append the gated edges (default: dry-run, nothing written)",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def triple(edge: dict) -> tuple[str, str, str]:
    return (
        edge["source"],
        edge.get("relation") or edge.get("type"),
        edge["target"],
    )


def metadata(obj: dict) -> dict:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def assert_delta_invariants(delta: dict) -> None:
    assert set(delta) == {"nodes", "edges"}, "delta must contain nodes and edges"
    assert delta["nodes"] == [], "fault-line delta must remain edges-only"
    assert isinstance(delta["edges"], list) and delta["edges"], "empty edge delta"

    edge_ids = [edge["edge_id"] for edge in delta["edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate edge id within delta"
    triples = [triple(edge) for edge in delta["edges"]]
    assert len(triples) == len(set(triples)), "duplicate edge triple within delta"
    triple_set = set(triples)

    for edge in delta["edges"]:
        edge_triple = triple(edge)
        reverse = (edge_triple[2], edge_triple[1], edge_triple[0])
        assert reverse not in triple_set, f"bidirectional duplicate in delta: {edge_triple}"
        assert edge["relation"] in ALLOWED_RELATIONS, edge["relation"]
        assert edge["source"] == edge["source_id"]
        assert edge["target"] == edge["target_id"]
        assert edge["source"] != edge["target"]
        md = metadata(edge)
        attestation = md.get("attested_by")
        proposition = md.get("proposition")
        assert isinstance(attestation, str) and attestation.strip(), (
            f"missing metadata.attested_by: {edge['edge_id']}"
        )
        assert PAGE_RE.search(attestation), (
            f"attestation has no page: {edge['edge_id']}: {attestation}"
        )
        assert isinstance(proposition, str) and proposition.strip(), (
            f"missing metadata.proposition: {edge['edge_id']}"
        )


def author_map(nodes: list[dict], edges: list[dict]) -> dict[str, str]:
    authors: dict[str, str] = {}
    for node in nodes:
        node_id = node["id"]
        md = metadata(node)
        author = md.get("scholar_id") or md.get("author_id")
        if isinstance(author, str) and author:
            authors[node_id] = author
        elif node.get("type") == "person":
            authors[node_id] = node_id
    for edge in edges:
        if edge.get("relation") == "created_by" and edge.get("target"):
            authors.setdefault(edge["source"], edge["target"])
    return authors


def pinned_opposes_count() -> int:
    source = G6_PROBE.read_text(encoding="utf-8")
    match = re.search(r"assert len\(all_opposes\) == (\d+)", source)
    if not match:
        raise AssertionError(f"cannot locate G6 opposes pin in {G6_PROBE}")
    return int(match.group(1))


def main() -> int:
    args = parse_args()
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert_delta_invariants(delta)

    nodes = read_jsonl(NODES)
    edges = read_jsonl(EDGES)
    node_ids = {node["id"] for node in nodes}
    existing_triples = {triple(edge) for edge in edges}
    existing_edge_ids = {
        edge.get("edge_id") for edge in edges if edge.get("edge_id")
    }
    authors = author_map(nodes, edges)

    new_edges: list[dict] = []
    skipped_existing = 0
    unresolved: list[tuple[str, str, str]] = []
    reverse_duplicates: list[tuple[str, str, str]] = []
    edge_id_collisions: list[str] = []
    same_scholar: list[tuple[str, str, str]] = []
    seen_triples = set(existing_triples)

    for edge in delta["edges"]:
        edge_triple = triple(edge)
        if edge_triple in seen_triples:
            skipped_existing += 1
            continue
        reverse = (edge["target"], edge["relation"], edge["source"])
        if reverse in seen_triples:
            reverse_duplicates.append(edge_triple)
            continue
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            unresolved.append(edge_triple)
            continue
        if edge["edge_id"] in existing_edge_ids:
            edge_id_collisions.append(edge["edge_id"])
            continue

        source_author = authors.get(edge["source"])
        target_author = authors.get(edge["target"])
        documented_retraction = (
            edge["relation"] == "responds_to"
            and metadata(edge).get("documented_self_retraction") is True
        )
        if source_author and source_author == target_author and not documented_retraction:
            same_scholar.append(edge_triple)
            continue

        new_edges.append(edge)
        seen_triples.add(edge_triple)

    print(f"delta: 0 nodes / {len(delta['edges'])} edges")
    print(
        f"novel: 0 nodes / {len(new_edges)} edges "
        f"(skipped existing: {skipped_existing} edges)"
    )
    relation_counts = collections.Counter(edge["relation"] for edge in new_edges)
    print(
        "relations: "
        + ", ".join(
            f"{relation}={relation_counts.get(relation, 0)}"
            for relation in sorted(ALLOWED_RELATIONS)
        )
    )

    failures = [
        ("unresolvable endpoints", unresolved),
        ("reverse-direction duplicates", reverse_duplicates),
        ("edge-id collisions", edge_id_collisions),
        ("same-scholar edges without documented retraction", same_scholar),
    ]
    for label, rows in failures:
        if rows:
            print(f"FATAL: {len(rows)} {label}: {rows[:5]}")
    if any(rows for _, rows in failures):
        print("nothing written")
        return 1

    current_opposes = sum(edge.get("relation") == "opposes" for edge in edges)
    novel_opposes = sum(edge["relation"] == "opposes" for edge in new_edges)
    post_apply_opposes = current_opposes + novel_opposes
    g6_pin = pinned_opposes_count()
    print(
        f"opposes: current={current_opposes}, novel={novel_opposes}, "
        f"post-apply={post_apply_opposes}, g6-pin={g6_pin}"
    )

    subset_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            suffix="-faultlines-wiring.json",
            encoding="utf-8",
            delete=False,
        ) as handle:
            json.dump({"nodes": [], "edges": new_edges}, handle, ensure_ascii=False)
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

    if not args.apply:
        print(
            f"dry-run: nothing written; future apply must update G6 opposes pin "
            f"from {g6_pin} to {post_apply_opposes} in the same commit"
        )
        return 0

    if g6_pin != post_apply_opposes:
        print(
            f"FATAL: G6 opposes pin is {g6_pin}, but post-apply count is "
            f"{post_apply_opposes}; update the pin in the same commit before --apply"
        )
        print("nothing written")
        return 1

    shutil.copy2(EDGES, str(EDGES) + BAK_SUFFIX)
    with EDGES.open("a", encoding="utf-8") as handle:
        for edge in new_edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")
    print(f"applied: +0 nodes, +{len(new_edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
