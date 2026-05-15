"""Utilities for Amand B7 consolidation (Gregory of Nyssa + Chrysostom + Pseudo-Chrysostom + Nemesius)."""
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


AMAND_BIBTEX_KEY = "amand-1945-fatalisme-et-liberte-dans-l-antiquite-grecque"


def amand_metadata(
    *,
    page_range: str,
    md_line_range: str,
    chapter: str,
    amand_chapter_actual: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    md: dict[str, Any] = {
        "amand_location": {
            "page_range": page_range,
            "md_line_range": md_line_range,
            "chapter": chapter,
        },
        "amand_chapter_actual": amand_chapter_actual,
        "source_quality": "paraphrase_from_md_ocr_95pc",
        "contains_greek_to_verify": True,
        "amand_cited_edition_unverified": True,
        "bibtex_key": AMAND_BIBTEX_KEY,
        "claimed_by": "scholar_amand_de_mendieta_e",
        "publication": "pub_amand_1945_fatalisme",
    }
    if extra:
        md.update(extra)
    return md
