"""Utilities for Cicero De Fato deep-anchoring batch B1.

Goal : 15+ scholar nodes currently cite work_de_fato_cicero_44bce_b9c4e5d2 at
WORK level only. Anchor each at PASSAGE level via `cites_primary_source`
(arguments / publications) or routed via authored arguments for syntheses
(ontology forbids synthesis -> passage cites_primary_source).

Same shape as amand_b9_utils / bobzien_2001_b1_utils.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def parse_metadata(node: dict[str, Any]) -> dict[str, Any]:
    md = node.get("metadata")
    if md is None or md == "":
        return {}
    if isinstance(md, dict):
        return md
    try:
        return json.loads(md)
    except (json.JSONDecodeError, TypeError):
        return {}


def dump_metadata(d: dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False)


def merge_metadata(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged.update(updates)
    return merged


def edge_exists(
    edges: list[dict[str, Any]],
    source: str,
    target: str,
    relation: str,
) -> bool:
    return any(
        e.get("source") == source
        and e.get("target") == target
        and e.get("relation") == relation
        for e in edges
    )


# Canonical Latin-text passage prefix (used by Bobzien cylinder edges in KG).
# The parallel `passage_cicero_fat_<n>` (curated English-summary + Latin) variant
# also exists for §1-48 and is acceptable; we prefer `passage_cic_fat_<n>` for
# consistency with existing scholar -> passage edges already in the KG.
PASSAGE_PREFIX = "passage_cic_fat_"

# Common edge metadata fields shared by all cite-edges in this batch.
WORK_ID = "work_de_fato_cicero_44bce_b9c4e5d2"
