"""Utilities for Destrée/Salles/Zingano 2014 B1 consolidation.

Targets: edited volume *What is Up to Us? Studies on Agency and Responsibility
in Ancient Philosophy* (Academia Verlag, Sankt Augustin, 2014), 20 chapters by
~22 contributors. Thematic spine: τὸ ἐφ' ἡμῖν / what is up to us, from
Democritus / Plato through Aristotle, the Stoics, Epicurus, Cicero, Plotinus,
Porphyry, Middle Platonism, Augustine, Proclus, Simplicius, ending on
M. Frede's late synthesis.

Same shape as amand_b9_utils / dihle_b2_utils / etc.
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


DESTREE_BIBTEX_KEY = "destree-salles-zingano-2014-what-is-up-to-us"
DESTREE_PUB_ID = "pub_destree_salles_zingano_2014_what_is_up_to_us"


def destree_metadata(
    *,
    chapter: str,
    pages: str,
    author: str,
    md_line_range: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Metadata for nodes derived from the Destrée 2014 edited volume.

    Page-anchors and author-anchors every node, per academic-integrity policy.
    """
    md: dict[str, Any] = {
        "destree2014_chapter": chapter,
        "destree2014_pages": pages,
        "destree2014_author": author,
        "source_quality": "edited_volume_chapter_summary",
        "bibtex_key": DESTREE_BIBTEX_KEY,
        "publication": DESTREE_PUB_ID,
        "claimed_by": "scholar_destr_e_p_salles_zingano_eds",
    }
    if md_line_range:
        md["destree2014_md_line_range"] = md_line_range
    if extra:
        md.update(extra)
    return md
