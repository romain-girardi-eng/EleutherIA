#!/usr/bin/env python3
"""Generate the scholarly backlog for evidence, editions, variants, and dates."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


THEMES: dict[str, tuple[str, ...]] = {
    "augustine_grace_will": ("augustine", "grace", "pelagian", "will"),
    "stoic_fate_assent": ("stoic", "chrysippus", "fate", "assent", "synkatath"),
    "aristotle_voluntary_akrasia": (
        "aristotle",
        "voluntary",
        "prohairesis",
        "akrasia",
    ),
    "epicurean_swerve": ("epicurus", "epicurean", "swerve", "clinamen"),
    "academic_antifatalism": ("carneades", "academic", "anti-fatal", "fato"),
    "late_antique_providence": ("boethius", "proclus", "providence", "origen"),
}


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


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                rows.append(json.loads(raw))
    return rows


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def _edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source") or edge.get("source_id") or "")


def _edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target") or edge.get("target_id") or "")


def _has_complete_edition(metadata: dict[str, Any]) -> bool:
    editions = metadata.get("editions") or metadata.get("edition")
    if isinstance(editions, dict):
        editions = [editions]
    if not isinstance(editions, list) or not editions:
        return False
    for edition in editions:
        if not isinstance(edition, dict):
            continue
        has_editor = bool(edition.get("editor") or edition.get("editors"))
        has_year = bool(edition.get("year") or edition.get("date"))
        has_series = bool(
            edition.get("series") or edition.get("publisher") or edition.get("isbn")
        )
        if has_editor and has_year and has_series:
            return True
    return False


def _has_publication_minimum(node: dict[str, Any], metadata: dict[str, Any]) -> bool:
    has_title = bool(node.get("label") or metadata.get("title"))
    has_year = bool(metadata.get("year") or metadata.get("date"))
    has_author = bool(
        metadata.get("author")
        or metadata.get("authors")
        or metadata.get("editor")
        or metadata.get("editors")
    )
    return has_title and has_year and has_author


def _theme_for(node: dict[str, Any], metadata: dict[str, Any]) -> str:
    haystack = " ".join(
        str(part)
        for part in (
            _node_id(node),
            node.get("label"),
            node.get("description"),
            metadata.get("school"),
            metadata.get("author"),
            metadata.get("keywords"),
        )
        if part
    ).lower()
    for theme, tokens in THEMES.items():
        if any(token in haystack for token in tokens):
            return theme
    return "unclassified"


def build_backlog(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_by_argument: set[str] = {
        _edge_source(edge)
        for edge in edges
        if edge.get("relation") == "evidenced_by" and _edge_source(edge)
    }

    by_type = Counter(str(node.get("type")) for node in nodes)
    missing_evidence: dict[str, list[str]] = defaultdict(list)
    missing_editions: list[str] = []
    publication_gaps: list[str] = []
    passage_role_gaps: list[str] = []
    translation_source_gaps: list[str] = []
    date_uncertainty_gaps: list[str] = []

    for node in nodes:
        node_id = _node_id(node)
        node_type = str(node.get("type") or "")
        metadata = _normalise_mapping(node.get("metadata"))

        if node_type == "argument":
            needs_evidence = metadata.get("needs_evidence") is True
            if needs_evidence or node_id not in evidence_by_argument:
                missing_evidence[_theme_for(node, metadata)].append(node_id)

        if node_type == "work" and not _has_complete_edition(metadata):
            missing_editions.append(node_id)

        if node_type == "publication" and not _has_publication_minimum(node, metadata):
            publication_gaps.append(node_id)

        if node_type == "passage":
            role = metadata.get("passage_role")
            if role not in {"original", "translation", "paraphrase"}:
                passage_role_gaps.append(node_id)
            if role == "translation" and not metadata.get("source_passage_id"):
                translation_source_gaps.append(node_id)

        if node_type in {"person", "work"} and not metadata.get("date_uncertainty"):
            date_uncertainty_gaps.append(node_id)

    return {
        "counts_by_type": dict(by_type),
        "missing_evidence_by_theme": dict(sorted(missing_evidence.items())),
        "missing_edition_metadata": missing_editions,
        "publication_bibtex_gaps": publication_gaps,
        "passage_role_gaps": passage_role_gaps,
        "translation_source_gaps": translation_source_gaps,
        "date_uncertainty_gaps": date_uncertainty_gaps,
    }


def _write_markdown(backlog: dict[str, Any], path: Path) -> None:
    lines = [
        "# Scholarly Backlog",
        "",
        "## Corpus Counts",
        "",
    ]
    for node_type, count in sorted(backlog["counts_by_type"].items()):
        lines.append(f"- `{node_type}`: {count}")

    lines.extend(["", "## Evidence Anchoring", ""])
    for theme, ids in backlog["missing_evidence_by_theme"].items():
        lines.append(f"- `{theme}`: {len(ids)}")

    sections = [
        ("Edition Metadata", "missing_edition_metadata"),
        ("Publication BibTeX Metadata", "publication_bibtex_gaps"),
        ("Passage Role", "passage_role_gaps"),
        ("Translation Source Links", "translation_source_gaps"),
        ("Date Uncertainty", "date_uncertainty_gaps"),
    ]
    for title, key in sections:
        values = backlog[key]
        lines.extend(["", f"## {title}", "", f"Total: {len(values)}", ""])
        for value in values[:100]:
            lines.append(f"- `{value}`")
        if len(values) > 100:
            lines.append(f"- ... {len(values) - 100} more")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", default="data/kg/nodes.jsonl")
    parser.add_argument("--edges", default="data/kg/edges.jsonl")
    parser.add_argument("--output-json", default="data/quality/scholarly_backlog.json")
    parser.add_argument("--output-md", default="data/quality/scholarly_backlog.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backlog = build_backlog(_iter_jsonl(ROOT / args.nodes), _iter_jsonl(ROOT / args.edges))
    output_json = ROOT / args.output_json
    output_md = ROOT / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(backlog, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    _write_markdown(backlog, output_md)
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
