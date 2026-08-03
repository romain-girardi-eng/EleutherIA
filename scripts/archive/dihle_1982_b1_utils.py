"""Utilities for Dihle 1982 B1 consolidation.

Targets: Albrecht Dihle, *The Theory of Will in Classical Antiquity*,
Sather Classical Lectures 48, University of California Press 1982
(reprinted 2020). Six lectures arguing that the philosophical concept of
will is a Christian and especially Augustinian invention, alien to Greek
intellectualism.

Same shape as amand_b9_utils.
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


DIHLE_BIBTEX_KEY = "dihle-1982-theory-of-will-classical-antiquity"


def dihle_metadata(
    *,
    page_range: str,
    md_line_range: str,
    lecture: str,
    dihle_section: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md: dict[str, Any] = {
        "dihle_1982_location": {
            "page_range": page_range,
            "md_line_range": md_line_range,
            "lecture": lecture,
        },
        "dihle_1982_section": dihle_section,
        "source_quality": "paraphrase_from_md_2020_reprint",
        "contains_greek_to_verify": True,
        "bibtex_key": DIHLE_BIBTEX_KEY,
        "claimed_by": "scholar_albrecht_dihle",
        "publication": "pub_dihle_1982_theory_of_will",
    }
    if extra:
        md.update(extra)
    return md
