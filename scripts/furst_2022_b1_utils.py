"""Utilities for Fürst 2022 B1 consolidation.

Targets: Alfons Fürst, *Wege zur Freiheit. Menschliche Selbstbestimmung von
Homer bis Origenes* (Mohr Siebeck, Tübingen 2022 ; Tria Corda 15 ; ISBN
978-3-16-161656-3 ; DOI 10.1628/978-3-16-161657-0).

Source: German monograph extracted at
/Users/romaingirardi/Desktop/DOCTORAT/Doctorat SHAL/04_Littérature_secondaire/
05_Origene/Alfons Fürst - Wege zur Freiheit_ Menschliche Selbstbestimmung
von Homer bis Origenes-Mohr Siebeck (2022).md

Pattern shape mirrors `amand_b9_utils.py`.

Description policy:
- `description`     = French (primary, with strict diacritics)
- `description_en`  = English (secondary)
- `description_de`  = German (optional, only for verbatim Fürst phrasing)
- Confidence: 0.9 explicit textual claims with page; 0.8 paraphrased theses;
  0.7 inferred connections / cautious attribution.
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


FURST_BIBTEX_KEY = (
    "furst-2022-wege-zur-freiheit-menschliche-selbstbestimmung-von-homer-bis-origenes"
)


def furst_metadata(
    *,
    page_range: str,
    chapter: str,
    chapter_actual: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard metadata footprint for Fürst 2022 enrichments / inserts.

    Use `chapter` for the structural pointer (e.g. "Kap. V 1 Der zentrale
    Stellenwert der Freiheit") and `chapter_actual` for a longer description.
    """
    md: dict[str, Any] = {
        "furst_2022_location": {
            "page_range": page_range,
            "chapter": chapter,
        },
        "furst_2022_chapter_actual": chapter_actual,
        "source_quality": "paraphrase_from_md_extraction_native_pymupdf",
        "language_of_source": "de",
        "bibtex_key": FURST_BIBTEX_KEY,
        "claimed_by": "scholar_furst_alfons",
        "publication": "pub_furst_2022_wege_freiheit",
    }
    if extra:
        md.update(extra)
    return md
