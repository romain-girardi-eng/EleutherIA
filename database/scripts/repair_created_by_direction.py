#!/usr/bin/env python3
"""Repair live KG edges where `created_by` is used in the `creates` direction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CREATOR_TYPES = {"person", "group"}
CREATED_TYPES = {"argument", "argument_framework", "concept", "publication", "work"}


def _normalise_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _load_node_types(path: Path) -> dict[str, str]:
    node_types: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            node = json.loads(raw)
            node_id = node.get("id") or node.get("node_id")
            node_type = node.get("type")
            if node_id and node_type:
                node_types[str(node_id)] = str(node_type)
    return node_types


def _edge_endpoint(edge: dict[str, Any], short: str, legacy: str) -> str:
    return str(edge.get(short) or edge.get(legacy) or "")


def repair_edges(edges_path: Path, node_types: dict[str, str]) -> tuple[list[str], int]:
    repaired: list[str] = []
    lines: list[str] = []
    with edges_path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            edge = json.loads(raw)
            if edge.get("relation") == "created_by":
                source = _edge_endpoint(edge, "source", "source_id")
                target = _edge_endpoint(edge, "target", "target_id")
                source_type = node_types.get(source)
                target_type = node_types.get(target)
                if source_type in CREATOR_TYPES and target_type in CREATED_TYPES:
                    edge["relation"] = "creates"
                    metadata = _normalise_mapping(edge.get("metadata"))
                    metadata.setdefault("repair", "created_by_to_creates_direction")
                    metadata.setdefault(
                        "repair_reason",
                        "source node is a creator and target node is the created entity",
                    )
                    edge["metadata"] = json.dumps(metadata, ensure_ascii=False)
                    repaired.append(str(edge.get("edge_id") or f"{source}->{target}"))
            lines.append(json.dumps(edge, ensure_ascii=False, sort_keys=True) + "\n")
    return lines, len(repaired)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", default="data/kg/nodes.jsonl")
    parser.add_argument("--edges", default="data/kg/edges.jsonl")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    edges_path = ROOT / args.edges
    lines, repaired_count = repair_edges(edges_path, _load_node_types(ROOT / args.nodes))
    print(f"created_by -> creates repairs: {repaired_count}")
    if args.apply and repaired_count:
        edges_path.write_text("".join(lines), encoding="utf-8")
        print(f"wrote {edges_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
