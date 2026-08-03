"""Utilities for Alexander De Fato deep-anchor batch B1.

Goal : take 12+ scholar arguments / syntheses / publications that currently
reference Alexander of Aphrodisias *De Fato* only at WORK level and bind them
to the specific chapter-level passage nodes (`passage_alex_fat_<n>`) that the
scholar is actually engaging with.

The 78 existing passage nodes cover all 39 chapters of the De Fato (Greek +
English variants). No new passage shells are needed here. The bulk of the
batch lives in `alexander_de_fato_deep_b1_edges.NEW_EDGES`.

Same shape as `frede_2011_b1_utils` / `amand_b9_utils`.
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


# ----------------------------------------------------------------------------
# Shared identifiers
# ----------------------------------------------------------------------------
ALEX_DE_FATO_WORK_ID = "work_de_fato_alexander_c200ce_o6p7q8r9"

# Greek-text passage IDs for the 39 chapters of De Fato.
# (The `_en` English-translation passages exist but cite-edges target the
# Greek originals; the English shells are linked to their Greek counterparts
# elsewhere in the KG via `translates` / `part_of`.)
ALEX_PASSAGE = {n: f"passage_alex_fat_{n}" for n in range(1, 40)}


def passage(chapter: int) -> str:
    """Return the canonical passage node ID for De Fato chapter ``chapter``."""
    if chapter not in ALEX_PASSAGE:
        raise ValueError(f"Alexander De Fato has no chapter {chapter}")
    return ALEX_PASSAGE[chapter]


# Bruns CAG Suppl. II.2 pages corresponding (approximately) to each chapter
# of De Fato. Used as the canonical citation key in scholarly literature.
# Source : Sharples 1983 Table of Concordance, p. 4.
BRUNS_PAGES = {
    1: "164.3-165.13",
    2: "165.14-166.16",
    3: "166.17-167.13",
    4: "167.14-168.23",
    5: "168.24-170.8",
    6: "170.9-171.16",
    7: "171.17-172.16",
    8: "172.17-173.23",
    9: "173.24-175.4",
    10: "175.5-176.23",
    11: "176.24-178.7",
    12: "178.8-180.4",
    13: "180.5-182.19",
    14: "182.20-184.20",
    15: "184.21-186.31",
    16: "186.32-188.10",
    17: "188.11-189.7",
    18: "189.8-191.30",
    19: "191.31-192.27",
    20: "192.28-194.10",
    21: "194.11-195.18",
    22: "195.19-196.23",
    23: "196.24-198.7",
    24: "198.8-199.21",
    25: "199.22-201.16",
    26: "201.17-203.5",
    27: "203.6-204.18",
    28: "204.19-205.32",
    29: "205.33-207.20",
    30: "207.21-209.11",
    31: "209.12-210.7",
    32: "210.8-211.18",
    33: "211.19-213.4",
    34: "213.5-214.27",
    35: "214.28-216.7",
    36: "216.8-217.18",
    37: "217.19-218.31",
    38: "218.32-220.3",
    39: "220.4-221.7",
}


# ----------------------------------------------------------------------------
# Edge-builder helper
# ----------------------------------------------------------------------------
def cite_edge(
    source: str,
    chapter: int,
    *,
    relation: str = "cites_primary_source",
    confidence: float = 0.9,
    scholar: str | None = None,
    publication: str | None = None,
    original_citation: str | None = None,
    note: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single passage-level scholar→Alexander-De-Fato edge.

    `relation` is `cites_primary_source` by default; for synthesis-type
    sources the orchestrator will down-grade to `part_of`/`discusses` since
    synthesis nodes are not valid as `cites_primary_source` source-types per
    the ontology.
    """
    target = passage(chapter)
    md: dict[str, Any] = {
        "alex_de_fato_chapter": chapter,
        "alex_de_fato_bruns_pages": BRUNS_PAGES[chapter],
    }
    if scholar:
        md["scholar"] = scholar
    if publication:
        md["publication"] = publication
    if original_citation:
        md["original_citation"] = original_citation
    if note:
        md["note"] = note
    if extra:
        md.update(extra)
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
        "metadata": md,
    }
