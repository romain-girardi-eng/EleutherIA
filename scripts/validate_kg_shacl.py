#!/usr/bin/env python3
"""Validate the JSONL KG snapshot through the RDF/SHACL semantic layer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))

from eleutheria_kg.semantic import (  # noqa: E402
    build_graph,
    validate_kg,
    validate_kg_invariants,
)
from eleutheria_kg.semantic.shapes import load_quality_shapes  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate data/kg JSONL via RDF export and SHACL shapes."
    )
    parser.add_argument("--nodes", default="data/kg/nodes.jsonl")
    parser.add_argument("--edges", default="data/kg/edges.jsonl")
    parser.add_argument(
        "--invariant-report",
        default="kg-invariants-shacl.md",
        help="Markdown report for blocking invariant SHACL checks.",
    )
    parser.add_argument(
        "--quality-report",
        default="kg-quality-shacl.md",
        help="Markdown report for non-blocking scholarly quality checks.",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Only run blocking invariant shapes.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=100,
        help="Maximum examples to write in Markdown reports.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nodes_path = ROOT / args.nodes
    edges_path = ROOT / args.edges
    if not nodes_path.exists() or not edges_path.exists():
        raise SystemExit(f"Missing KG snapshot files: {nodes_path}, {edges_path}")

    graph = build_graph(nodes_path, edges_path)

    invariant_report = validate_kg_invariants(graph)
    invariant_markdown = invariant_report.format_markdown_report(
        max_examples=args.max_examples
    )
    (ROOT / args.invariant_report).write_text(invariant_markdown, encoding="utf-8")
    print(invariant_markdown)
    if not invariant_report.conforms:
        return 1

    if not args.skip_quality:
        quality_report = validate_kg(graph, load_quality_shapes())
        quality_markdown = quality_report.format_markdown_report(
            max_examples=args.max_examples
        )
        (ROOT / args.quality_report).write_text(quality_markdown, encoding="utf-8")
        print(quality_markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
