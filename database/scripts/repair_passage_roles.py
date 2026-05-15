#!/usr/bin/env python3
"""Backfill passage_role and source_passage_id in data/kg/nodes.jsonl."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


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


def _translation_sources(edges_path: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    with edges_path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            edge = json.loads(raw)
            if edge.get("relation") != "translation_of":
                continue
            source = str(edge.get("source") or edge.get("source_id") or "")
            target = str(edge.get("target") or edge.get("target_id") or "")
            if source and target:
                sources[source] = target
    return sources


def repair_nodes(nodes_path: Path, translation_sources: dict[str, str]) -> tuple[str, int]:
    repaired = 0
    lines: list[str] = []
    with nodes_path.open(encoding="utf-8") as fh:
        for raw in fh:
            if not raw.strip():
                continue
            node = json.loads(raw)
            node_id = str(node.get("id") or node.get("node_id") or "")
            if node.get("type") == "passage":
                metadata = _normalise_mapping(node.get("metadata"))
                if metadata.get("passage_role") not in {
                    "original",
                    "translation",
                    "paraphrase",
                }:
                    metadata["passage_role"] = (
                        "translation" if node_id in translation_sources else "original"
                    )
                    repaired += 1
                if (
                    metadata.get("passage_role") == "translation"
                    and not metadata.get("source_passage_id")
                    and node_id in translation_sources
                ):
                    metadata["source_passage_id"] = translation_sources[node_id]
                    repaired += 1
                node["metadata"] = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
            lines.append(json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n")
    return "".join(lines), repaired


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", default="data/kg/nodes.jsonl")
    parser.add_argument("--edges", default="data/kg/edges.jsonl")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nodes_path = ROOT / args.nodes
    content, repaired = repair_nodes(nodes_path, _translation_sources(ROOT / args.edges))
    print(f"passage role/source repairs: {repaired}")
    if args.apply and repaired:
        nodes_path.write_text(content, encoding="utf-8")
        print(f"wrote {nodes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
