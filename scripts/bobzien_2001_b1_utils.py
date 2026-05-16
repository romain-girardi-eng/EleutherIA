"""Utilities for Bobzien 2001 B1 consolidation (Determinism and Freedom in Stoic Philosophy).

Targets: chapter-by-chapter enrichment of the EleutherIA KG with the central
scholarly theses of Susanne Bobzien's 2001 monograph (Oxford: Clarendon Press;
copyright 1998 / paperback 2001). Same shape as the amand_b9_* batch.

Bobzien 2001 is THE gold-standard modern reconstruction of Stoic determinism
and compatibilism. Many KG nodes already exist (scholar = person_bobzien_susanne_
contemporary, publication = scholarly_work_bobzien_2001_determinism_and_freedom_
in_stoic_philoso). This batch updates them and grafts the 8-chapter
architecture onto them.
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


# Canonical identifiers for Bobzien 2001 batch B1
BOBZIEN_2001_BIBTEX_KEY = "bobzien-2001-determinism-and-freedom-in-stoic-philosophy"
BOBZIEN_PUBLICATION_ID = "scholarly_work_bobzien_2001_determinism_and_freedom_in_stoic_philoso"
BOBZIEN_PERSON_ID = "person_bobzien_susanne_contemporary"


def bobzien_metadata(
    *,
    page_range: str,
    chapter: str,
    bobzien_chapter_actual: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard metadata stamp for every node in batch B1.

    `chapter` = canonical chapter label (e.g. 'Ch. 1 Determinism and Fate').
    `bobzien_chapter_actual` = freeform descriptive scope of the node.
    """
    md: dict[str, Any] = {
        "bobzien_2001_location": {
            "page_range": page_range,
            "chapter": chapter,
        },
        "bobzien_2001_chapter_actual": bobzien_chapter_actual,
        "source_quality": "scholarly_thesis_verified_from_md",
        "bibtex_key": BOBZIEN_2001_BIBTEX_KEY,
        "claimed_by": BOBZIEN_PERSON_ID,
        "publication": BOBZIEN_PUBLICATION_ID,
    }
    if extra:
        md.update(extra)
    return md
