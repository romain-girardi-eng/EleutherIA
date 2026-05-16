"""Utilities for Frede 2011 batch B1 consolidation.

Frede, Michael. *A Free Will: Origins of the Notion in Ancient Thought*.
Edited by A. A. Long, with a foreword by David Sedley. Sather Classical
Lectures, vol. 68. Berkeley/Los Angeles/London: University of California
Press, 2011. ISBN 978-0-520-26848-7. xiv + 206 pp. (Posthumous; based on
the 1997-98 Sather Lectures delivered at Berkeley; Frede died 2007.)

Same shape as amand_b9_utils / dihle_*_utils — provides a frede_metadata()
factory that anchors every new node and synthesis to the publication
pub_frede_2011_free_will and to the bibtex key.
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


FREDE_BIBTEX_KEY = "frede-2011-free-will-origins-notion-ancient-thought"
FREDE_PUBLICATION_ID = "pub_frede_2011_free_will"
FREDE_SCHOLAR_ID = "scholar_frede_michael"


def frede_metadata(
    *,
    page_range: str,
    chapter: str,
    chapter_actual: str,
    md_line_range: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard metadata block for every Frede 2011 node and synthesis.

    `chapter` = canonical chapter label, e.g. "Ch. 5 Emergence of a Free Will".
    `chapter_actual` = free-form description of the precise sub-thesis.
    """
    md: dict[str, Any] = {
        "frede_2011_location": {
            "page_range": page_range,
            "chapter": chapter,
        },
        "frede_2011_chapter_actual": chapter_actual,
        "source_quality": "verified_against_md_extraction_native",
        "contains_greek_to_verify": True,
        "bibtex_key": FREDE_BIBTEX_KEY,
        "claimed_by": FREDE_SCHOLAR_ID,
        "publication": FREDE_PUBLICATION_ID,
    }
    if md_line_range:
        md["frede_2011_location"]["md_line_range"] = md_line_range
    if extra:
        md.update(extra)
    return md
