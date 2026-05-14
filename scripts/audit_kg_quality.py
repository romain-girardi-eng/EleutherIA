#!/usr/bin/env python3
"""
Audit live KG quality from PostgreSQL and write Markdown + JSON reports.

Usage:
  set -a; source .env; set +a
  uv run --directory database python scripts/audit_kg_quality.py
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[1]

CLAIM_TYPES = {
    "argument",
    "argument_framework",
    "concept",
    "conceptual_evolution",
    "controversy",
    "debate",
    "group",
    "quote",
    "school",
    "synthesis",
}

EVIDENCE_RELATIONS = {"evidenced_by", "grounded_in", "source_for"}

CANONICAL_PERIODS = {
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Republican",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
    "Second Temple Judaism",
    "Rabbinic",
    "Medieval",
    "Early Modern",
    "Modern",
    "Contemporary",
    "Cross-period",
}

POST_ANTIQUE_PERIODS = {"Medieval", "Early Modern", "Modern", "Contemporary"}

CLAIM_PATTERN = re.compile(
    r"\b("
    r"argues?|claims?|maintains?|shows?|demonstrates?|proves?|"
    r"rejects?|supports?|critiques?|develops?|established|"
    r"foundational|central|perennial"
    r")\b",
    re.IGNORECASE,
)

SUSPICIOUS_PREFIXES = {
    "argument",
    "concept",
    "controversy",
    "debate",
    "event",
    "group",
    "person",
    "publication",
    "quote",
    "school",
    "source",
    "synthesis",
    "term",
    "work",
}

NEAR_DUP_TYPES = {
    "argument",
    "concept",
    "controversy",
    "debate",
    "group",
    "school",
    "synthesis",
}

NEAR_DUP_STOPWORDS = {
    "and",
    "argument",
    "debate",
    "doctrine",
    "for",
    "model",
    "of",
    "on",
    "the",
    "theory",
    "view",
    "vs",
}


@dataclass(slots=True)
class Dataset:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    citation_counts: Counter[str]
    node_ontology: dict[str, Any]
    edge_ontology: dict[str, Any]


def load_ontology() -> tuple[dict[str, Any], dict[str, Any]]:
    node_ontology = json.loads(
        (ROOT / "knowledge graph/ontology/node_types.json").read_text()
    )["node_types"]
    edge_ontology = json.loads(
        (ROOT / "knowledge graph/ontology/edge_types.json").read_text()
    )["edge_types"]
    return node_ontology, edge_ontology


def normalize_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


async def fetch_dataset() -> Dataset:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    node_ontology, edge_ontology = load_ontology()

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        await conn.execute("SET search_path = free_will, public;")
        nodes = [
            dict(row)
            for row in await conn.fetch(
                """
                SELECT node_id, label, type, period, description, metadata
                FROM kg_nodes
                ORDER BY node_id
                """
            )
        ]
        edges = [
            dict(row)
            for row in await conn.fetch(
                """
                SELECT source_id, target_id, relation
                FROM kg_edges
                ORDER BY source_id, target_id, relation
                """
            )
        ]
        citation_counts = Counter(
            {
                row["kg_node_id"]: row["c"]
                for row in await conn.fetch(
                    """
                    SELECT kg_node_id, COUNT(*) AS c
                    FROM passage_citations
                    GROUP BY kg_node_id
                    """
                )
            }
        )
    finally:
        await conn.close()

    for node in nodes:
        node["metadata"] = normalize_metadata(node.get("metadata"))

    return Dataset(
        nodes=nodes,
        edges=edges,
        citation_counts=citation_counts,
        node_ontology=node_ontology,
        edge_ontology=edge_ontology,
    )


def percent(part: int, whole: int) -> str:
    if whole == 0:
        return "0.0%"
    return f"{(part / whole) * 100:.1f}%"


def short_snippet(text: str | None, limit: int = 180) -> str:
    if not text:
        return ""
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def label_norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def token_signature(text: str) -> set[str]:
    tokens = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {t for t in tokens.split() if t and t not in NEAR_DUP_STOPWORDS}


def first_segment(type_name: str) -> str:
    return type_name.split("_", 1)[0]


def example_rows(items: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    return items[:limit]


def analyze(dataset: Dataset) -> dict[str, Any]:
    nodes = dataset.nodes
    edges = dataset.edges
    node_by_id = {node["node_id"]: node for node in nodes}

    relation_counts = Counter(edge["relation"] for edge in edges)
    type_counts = Counter(node["type"] for node in nodes)
    period_counts = Counter(node["period"] or "<NULL>" for node in nodes)

    duplicate_edge_groups = [
        {
            "source_id": source_id,
            "target_id": target_id,
            "relation": relation,
            "count": count,
        }
        for (source_id, target_id, relation), count in Counter(
            (edge["source_id"], edge["target_id"], edge["relation"]) for edge in edges
        ).items()
        if count > 1
    ]

    orphan_edges = [
        edge
        for edge in edges
        if edge["source_id"] not in node_by_id or edge["target_id"] not in node_by_id
    ]
    self_loops = [edge for edge in edges if edge["source_id"] == edge["target_id"]]

    edge_lookup_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outgoing_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edge_lookup_by_node[edge["source_id"]].append(edge)
        edge_lookup_by_node[edge["target_id"]].append(edge)
        outgoing_by_node[edge["source_id"]].append(edge)
        incoming_by_node[edge["target_id"]].append(edge)

    isolated_nodes = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
        }
        for node in nodes
        if node["node_id"] not in edge_lookup_by_node
    ]

    weak_nodes = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
            "degree": len(edge_lookup_by_node[node["node_id"]]),
        }
        for node in nodes
        if 1 <= len(edge_lookup_by_node[node["node_id"]]) <= 2
    ]
    weak_nodes.sort(key=lambda item: (item["degree"], item["type"], item["label"]))

    orphan_citation_ids = sorted(
        node_id for node_id in dataset.citation_counts if node_id not in node_by_id
    )

    unknown_node_types = [
        {"type": node_type, "count": count}
        for node_type, count in type_counts.items()
        if node_type not in dataset.node_ontology
    ]
    unknown_relations = [
        {"relation": relation, "count": count}
        for relation, count in relation_counts.items()
        if relation not in dataset.edge_ontology
    ]
    unknown_relations.sort(key=lambda item: (-item["count"], item["relation"]))

    invalid_relation_pairs = Counter()
    invalid_relation_examples: dict[tuple[str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for edge in edges:
        relation_def = dataset.edge_ontology.get(edge["relation"])
        if not relation_def:
            continue
        source_type = node_by_id[edge["source_id"]]["type"]
        target_type = node_by_id[edge["target_id"]]["type"]
        source_ok = (
            "*" in relation_def["source_types"]
            or source_type in relation_def["source_types"]
        )
        target_ok = (
            "*" in relation_def["target_types"]
            or target_type in relation_def["target_types"]
        )
        if source_ok and target_ok:
            continue
        key = (edge["relation"], source_type, target_type)
        invalid_relation_pairs[key] += 1
        if len(invalid_relation_examples[key]) < 5:
            invalid_relation_examples[key].append(
                {
                    "source_id": edge["source_id"],
                    "source_label": node_by_id[edge["source_id"]]["label"],
                    "target_id": edge["target_id"],
                    "target_label": node_by_id[edge["target_id"]]["label"],
                }
            )

    invalid_relation_rows = [
        {
            "relation": relation,
            "source_type": source_type,
            "target_type": target_type,
            "count": count,
            "examples": invalid_relation_examples[(relation, source_type, target_type)],
        }
        for (
            relation,
            source_type,
            target_type,
        ), count in invalid_relation_pairs.most_common()
    ]

    invalid_period_nodes = defaultdict(list)
    for node in nodes:
        period = node["period"]
        if period and period not in CANONICAL_PERIODS:
            invalid_period_nodes[period].append(
                {
                    "node_id": node["node_id"],
                    "label": node["label"],
                    "type": node["type"],
                }
            )
    invalid_period_rows = [
        {
            "period": period,
            "count": len(items),
            "examples": example_rows(items, 10),
        }
        for period, items in sorted(
            invalid_period_nodes.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]

    null_period_nodes = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
        }
        for node in nodes
        if node["period"] is None
    ]

    nodes_without_description = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
        }
        for node in nodes
        if not (node.get("description") or "").strip()
    ]

    empty_metadata_nodes = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
            "description_snippet": short_snippet(node.get("description")),
        }
        for node in nodes
        if not node.get("metadata")
    ]

    exact_duplicate_label_groups = []
    duplicate_label_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        duplicate_label_map[(node["type"], label_norm(node["label"]))].append(node)
    for (node_type, _), group in duplicate_label_map.items():
        if len(group) < 2:
            continue
        exact_duplicate_label_groups.append(
            {
                "type": node_type,
                "label": group[0]["label"],
                "count": len(group),
                "ids": [item["node_id"] for item in group],
            }
        )
    exact_duplicate_label_groups.sort(
        key=lambda item: (-item["count"], item["type"], item["label"])
    )

    suspicious_prefix_mismatches = []
    for node in nodes:
        prefix = node["node_id"].split("_", 1)[0]
        type_prefix = first_segment(node["type"])
        if prefix in SUSPICIOUS_PREFIXES and prefix != type_prefix:
            suspicious_prefix_mismatches.append(
                {
                    "node_id": node["node_id"],
                    "label": node["label"],
                    "type": node["type"],
                    "prefix": prefix,
                }
            )
    suspicious_prefix_mismatches.sort(
        key=lambda item: (item["type"], item["prefix"], item["label"])
    )

    likely_near_duplicates = []
    non_passage_nodes = [node for node in nodes if node["type"] in NEAR_DUP_TYPES]
    for idx, left in enumerate(non_passage_nodes):
        left_norm = label_norm(left["label"])
        left_tokens = token_signature(left["label"])
        for right in non_passage_nodes[idx + 1 :]:
            if left["type"] != right["type"]:
                continue
            right_norm = label_norm(right["label"])
            if left_norm == right_norm:
                continue
            right_tokens = token_signature(right["label"])
            union = len(left_tokens | right_tokens) or 1
            overlap = len(left_tokens & right_tokens) / union
            similarity = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
            if overlap >= 0.8 and similarity >= 0.8:
                likely_near_duplicates.append(
                    {
                        "type": left["type"],
                        "label_a": left["label"],
                        "id_a": left["node_id"],
                        "label_b": right["label"],
                        "id_b": right["node_id"],
                        "token_overlap": round(overlap, 3),
                        "label_similarity": round(similarity, 3),
                    }
                )
    likely_near_duplicates.sort(
        key=lambda item: (
            -item["token_overlap"],
            -item["label_similarity"],
            item["type"],
            item["label_a"],
        )
    )

    non_passage_nodes = [node for node in nodes if node["type"] != "passage"]

    def description_flag_items(predicate: Any) -> list[dict[str, Any]]:
        return [
            {
                "node_id": node["node_id"],
                "label": node["label"],
                "type": node["type"],
                "period": node["period"],
                "description_snippet": short_snippet(node.get("description")),
            }
            for node in non_passage_nodes
            if predicate(node.get("description") or "")
        ]

    descriptions_with_markdown = description_flag_items(
        lambda text: (
            "**" in text
            or "__" in text
            or "[" in text
            or "]" in text
            or re.search(r"\n\s*[-*]", text) is not None
        )
    )
    descriptions_with_bold = description_flag_items(lambda text: "**" in text)
    descriptions_with_lists = description_flag_items(
        lambda text: re.search(r"\n\s*[-*]", text) is not None
    )
    descriptions_with_newlines = description_flag_items(lambda text: "\n" in text)

    passage_nodes = [node for node in nodes if node["type"] == "passage"]
    metadata_style_passage_labels = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "period": node["period"],
        }
        for node in passage_nodes
        if any(token in node["label"] for token in ("chap.:", "par.:", "verset.:"))
    ]
    underscore_passage_labels = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "period": node["period"],
        }
        for node in passage_nodes
        if "_" in node["label"]
    ]

    passage_translation_nodes = [
        node for node in passage_nodes if node["node_id"].endswith("_en")
    ]
    translation_integrity = {
        "translation_nodes": len(passage_translation_nodes),
        "translation_nodes_missing_translation_of": sum(
            1
            for node in passage_translation_nodes
            if not any(
                edge["relation"] == "translation_of"
                for edge in outgoing_by_node[node["node_id"]]
            )
        ),
        "source_nodes_with_translation_of": sum(
            1
            for node in passage_nodes
            if not node["node_id"].endswith("_en")
            and any(
                edge["relation"] == "translation_of"
                for edge in outgoing_by_node[node["node_id"]]
            )
        ),
    }

    def missing_outgoing(node_type: str, relation: str) -> list[dict[str, Any]]:
        return [
            {
                "node_id": node["node_id"],
                "label": node["label"],
                "type": node["type"],
                "period": node["period"],
            }
            for node in nodes
            if node["type"] == node_type
            and not any(
                edge["relation"] == relation
                for edge in outgoing_by_node[node["node_id"]]
            )
        ]

    work_missing_authored_by = missing_outgoing("work", "authored_by")
    publication_missing_authored_by = missing_outgoing("publication", "authored_by")
    quote_missing_authored_by = missing_outgoing("quote", "authored_by")
    passage_missing_authored_by = missing_outgoing("passage", "authored_by")
    passage_missing_part_of = missing_outgoing("passage", "part_of")

    evidence_touch = {
        node["node_id"]: {"passage_edge": 0, "evidence_relation": 0} for node in nodes
    }
    for edge in edges:
        if edge["relation"] in EVIDENCE_RELATIONS:
            evidence_touch[edge["source_id"]]["evidence_relation"] += 1
            evidence_touch[edge["target_id"]]["evidence_relation"] += 1
        if node_by_id[edge["source_id"]]["type"] == "passage":
            evidence_touch[edge["target_id"]]["passage_edge"] += 1
        if node_by_id[edge["target_id"]]["type"] == "passage":
            evidence_touch[edge["source_id"]]["passage_edge"] += 1

    claim_nodes = [node for node in nodes if node["type"] in CLAIM_TYPES]
    claim_nodes_without_anchor = []
    assertive_claim_candidates = []
    for node in claim_nodes:
        node_id = node["node_id"]
        no_anchor = (
            dataset.citation_counts.get(node_id, 0) == 0
            and evidence_touch[node_id]["evidence_relation"] == 0
            and evidence_touch[node_id]["passage_edge"] == 0
        )
        if not no_anchor:
            continue
        row = {
            "node_id": node_id,
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
            "description_snippet": short_snippet(node.get("description")),
            "empty_metadata": not bool(node.get("metadata")),
        }
        claim_nodes_without_anchor.append(row)
        if CLAIM_PATTERN.search(node.get("description") or ""):
            assertive_claim_candidates.append(row)

    claim_nodes_without_anchor.sort(
        key=lambda item: (item["type"], item["period"] or "", item["label"])
    )
    assertive_claim_candidates.sort(
        key=lambda item: (item["type"], item["period"] or "", item["label"])
    )

    post_antique_nodes = [
        {
            "node_id": node["node_id"],
            "label": node["label"],
            "type": node["type"],
            "period": node["period"],
        }
        for node in nodes
        if node["period"] in POST_ANTIQUE_PERIODS
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "passage_citations": sum(dataset.citation_counts.values()),
            "claim_nodes": len(claim_nodes),
            "node_types": type_counts,
            "edge_relations": relation_counts,
            "periods": period_counts,
        },
        "clean_checks": {
            "orphan_edges": len(orphan_edges),
            "orphan_passage_citations": len(orphan_citation_ids),
            "isolated_nodes": len(isolated_nodes),
            "duplicate_edge_groups": len(duplicate_edge_groups),
            "self_loops": len(self_loops),
        },
        "ontology_drift": {
            "unknown_node_types": unknown_node_types,
            "unknown_relations": unknown_relations,
            "invalid_relation_pairs": invalid_relation_rows,
            "invalid_periods": invalid_period_rows,
        },
        "completeness": {
            "nodes_without_description": {
                "count": len(nodes_without_description),
                "examples": nodes_without_description,
            },
            "empty_metadata": {
                "count": len(empty_metadata_nodes),
                "by_type": Counter(item["type"] for item in empty_metadata_nodes),
                "examples": example_rows(empty_metadata_nodes, 20),
            },
            "null_periods": {
                "count": len(null_period_nodes),
                "by_type": Counter(item["type"] for item in null_period_nodes),
                "examples": example_rows(null_period_nodes, 20),
            },
            "weak_nodes": {
                "count": len(weak_nodes),
                "by_type": Counter(item["type"] for item in weak_nodes),
                "examples": example_rows(weak_nodes, 40),
            },
            "exact_duplicate_labels": exact_duplicate_label_groups,
            "likely_near_duplicates": likely_near_duplicates,
            "authorship_and_structure": {
                "work_missing_authored_by": {
                    "count": len(work_missing_authored_by),
                    "examples": example_rows(work_missing_authored_by, 20),
                },
                "publication_missing_authored_by": {
                    "count": len(publication_missing_authored_by),
                    "examples": example_rows(publication_missing_authored_by, 20),
                },
                "quote_missing_authored_by": {
                    "count": len(quote_missing_authored_by),
                    "examples": example_rows(quote_missing_authored_by, 20),
                },
                "passage_missing_authored_by": {
                    "count": len(passage_missing_authored_by),
                    "source_nodes": sum(
                        1
                        for item in passage_missing_authored_by
                        if not item["node_id"].endswith("_en")
                    ),
                    "translation_nodes": sum(
                        1
                        for item in passage_missing_authored_by
                        if item["node_id"].endswith("_en")
                    ),
                    "examples": example_rows(passage_missing_authored_by, 20),
                },
                "passage_missing_part_of": {
                    "count": len(passage_missing_part_of),
                    "source_nodes": sum(
                        1
                        for item in passage_missing_part_of
                        if not item["node_id"].endswith("_en")
                    ),
                    "translation_nodes": sum(
                        1
                        for item in passage_missing_part_of
                        if item["node_id"].endswith("_en")
                    ),
                    "examples": example_rows(passage_missing_part_of, 20),
                },
                "translation_integrity": translation_integrity,
            },
        },
        "formatting": {
            "descriptions_with_markdown": {
                "count": len(descriptions_with_markdown),
                "by_type": Counter(item["type"] for item in descriptions_with_markdown),
                "examples": example_rows(descriptions_with_markdown, 20),
            },
            "descriptions_with_bold": {
                "count": len(descriptions_with_bold),
                "by_type": Counter(item["type"] for item in descriptions_with_bold),
                "examples": example_rows(descriptions_with_bold, 20),
            },
            "descriptions_with_lists": {
                "count": len(descriptions_with_lists),
                "by_type": Counter(item["type"] for item in descriptions_with_lists),
                "examples": example_rows(descriptions_with_lists, 20),
            },
            "descriptions_with_newlines": {
                "count": len(descriptions_with_newlines),
                "by_type": Counter(item["type"] for item in descriptions_with_newlines),
                "examples": example_rows(descriptions_with_newlines, 20),
            },
            "metadata_style_passage_labels": {
                "count": len(metadata_style_passage_labels),
                "examples": example_rows(metadata_style_passage_labels, 20),
            },
            "underscore_passage_labels": {
                "count": len(underscore_passage_labels),
                "examples": example_rows(underscore_passage_labels, 20),
            },
            "suspicious_id_prefix_mismatches": {
                "count": len(suspicious_prefix_mismatches),
                "examples": suspicious_prefix_mismatches,
            },
        },
        "provenance": {
            "claim_nodes_without_evidence_anchor": {
                "count": len(claim_nodes_without_anchor),
                "by_type": Counter(item["type"] for item in claim_nodes_without_anchor),
                "by_period": Counter(
                    item["period"] or "<NULL>" for item in claim_nodes_without_anchor
                ),
                "examples": example_rows(claim_nodes_without_anchor, 40),
            },
            "assertive_claim_candidates_without_evidence": {
                "count": len(assertive_claim_candidates),
                "by_type": Counter(item["type"] for item in assertive_claim_candidates),
                "by_period": Counter(
                    item["period"] or "<NULL>" for item in assertive_claim_candidates
                ),
                "empty_metadata_count": sum(
                    1 for item in assertive_claim_candidates if item["empty_metadata"]
                ),
                "examples": example_rows(assertive_claim_candidates, 40),
            },
        },
        "scope_drift": {
            "post_antique_nodes": {
                "count": len(post_antique_nodes),
                "by_period": Counter(item["period"] for item in post_antique_nodes),
                "examples": example_rows(post_antique_nodes, 30),
            }
        },
    }


def counter_lines(counter: Counter[str], limit: int = 8) -> list[str]:
    lines = []
    for key, count in counter.most_common(limit):
        lines.append(f"- `{key}`: {count}")
    return lines


def row_lines(
    items: list[dict[str, Any]], fields: list[str], limit: int = 10
) -> list[str]:
    lines = []
    for item in items[:limit]:
        parts = []
        for field in fields:
            value = item.get(field)
            if value in (None, ""):
                continue
            parts.append(f"{field}={value}")
        lines.append(f"- {', '.join(parts)}")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    clean = report["clean_checks"]
    ontology = report["ontology_drift"]
    completeness = report["completeness"]
    formatting = report["formatting"]
    provenance = report["provenance"]
    scope_drift = report["scope_drift"]

    claim_total = counts["claim_nodes"]
    no_anchor_count = provenance["claim_nodes_without_evidence_anchor"]["count"]
    assertive_count = provenance["assertive_claim_candidates_without_evidence"]["count"]
    empty_meta_count = completeness["empty_metadata"]["count"]

    lines = [
        "# KG Quality Audit",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Snapshot",
        "",
        "- Audited live PostgreSQL KG, not a checked-in export.",
        f"- Nodes: {counts['nodes']}",
        f"- Edges: {counts['edges']}",
        f"- Passage citations: {counts['passage_citations']}",
        f"- Claim-bearing nodes audited for provenance risk: {claim_total}",
        "",
        "## What Is Already Clean",
        "",
        f"- Orphan edges: {clean['orphan_edges']}",
        f"- Orphan passage citations: {clean['orphan_passage_citations']}",
        f"- Isolated / no-edge nodes: {clean['isolated_nodes']}",
        f"- Duplicate edge triples: {clean['duplicate_edge_groups']}",
        f"- Self-loops: {clean['self_loops']}",
        "",
        "## Priority Fixes",
        "",
        (
            f"1. Provenance gaps: {no_anchor_count}/{claim_total} "
            f"({percent(no_anchor_count, claim_total)}) claim-bearing nodes have no passage citation, "
            "no evidence relation, and no direct passage edge."
        ),
        (
            f"2. Unsupported-claim candidates: {assertive_count}/{claim_total} "
            f"({percent(assertive_count, claim_total)}) claim-bearing nodes still use assertive language "
            "despite lacking any evidence anchor."
        ),
        (
            f"3. Ontology drift: {len(ontology['unknown_relations'])} live relations are missing from the ontology, "
            f"and {sum(row['count'] for row in ontology['invalid_relation_pairs'])} edges violate the current "
            "relation type constraints."
        ),
        (
            f"4. Thin node records: {empty_meta_count} nodes have empty metadata and "
            f"{completeness['nodes_without_description']['count']} nodes have no description at all."
        ),
        (
            f"5. Incomplete authorship / structure: "
            f"{completeness['authorship_and_structure']['work_missing_authored_by']['count']} work nodes, "
            f"{completeness['authorship_and_structure']['publication_missing_authored_by']['count']} publication nodes, "
            f"{completeness['authorship_and_structure']['quote_missing_authored_by']['count']} quote nodes, and "
            f"{completeness['authorship_and_structure']['passage_missing_authored_by']['count']} passage nodes "
            "lack `authored_by`."
        ),
        (
            f"6. Formatting drift: {formatting['descriptions_with_markdown']['count']} non-passage node descriptions "
            f"contain markdown or list markup, and {formatting['metadata_style_passage_labels']['count']} passage labels "
            "still expose importer-style `chap.: / par.: / verset.:` strings."
        ),
        "",
        "## Provenance / Hallucination Risk",
        "",
        "- Heuristic used here:",
        "  A node is flagged when it is a claim-bearing type and has zero passage citations, zero `evidenced_by` / `source_for` / `grounded_in` relations, and zero direct graph edges to passage nodes.",
        "- Higher-risk subset:",
        "  Same rule as above, plus assertive wording in the description (`argues`, `shows`, `foundational`, `central`, etc.).",
        "",
        f"- Claim nodes without any evidence anchor: {no_anchor_count}",
        *counter_lines(provenance["claim_nodes_without_evidence_anchor"]["by_type"]),
        "",
        f"- Assertive claim candidates without evidence: {assertive_count}",
        *counter_lines(
            provenance["assertive_claim_candidates_without_evidence"]["by_type"]
        ),
        "",
        "- Representative assertive examples:",
        *row_lines(
            provenance["assertive_claim_candidates_without_evidence"]["examples"],
            ["type", "period", "label", "node_id"],
            12,
        ),
        "",
        "## Ontology Drift",
        "",
        "- Live relations missing from `knowledge graph/ontology/edge_types.json`:",
    ]

    if ontology["unknown_relations"]:
        for item in ontology["unknown_relations"]:
            lines.append(f"- `{item['relation']}`: {item['count']}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "- Invalid relation/type combinations:",
        ]
    )
    if ontology["invalid_relation_pairs"]:
        for item in ontology["invalid_relation_pairs"][:5]:
            lines.append(
                f"- `{item['relation']}` from `{item['source_type']}` -> `{item['target_type']}`: {item['count']}"
            )
    else:
        lines.append("- None")

    if ontology["invalid_periods"]:
        lines.extend(["", "- Invalid period labels:"])
        for item in ontology["invalid_periods"]:
            lines.append(f"- `{item['period']}`: {item['count']}")

    lines.extend(
        [
            "",
            "## Thin / Incomplete Nodes",
            "",
            f"- Nodes with empty metadata: {empty_meta_count}",
            *counter_lines(completeness["empty_metadata"]["by_type"]),
            "",
            f"- Nodes without description: {completeness['nodes_without_description']['count']}",
            *row_lines(
                completeness["nodes_without_description"]["examples"],
                ["type", "period", "label", "node_id"],
                12,
            ),
            "",
            f"- Nodes with null period: {completeness['null_periods']['count']}",
            *counter_lines(completeness["null_periods"]["by_type"]),
            "",
            f"- Weakly connected nodes (degree 1-2): {completeness['weak_nodes']['count']}",
            *counter_lines(completeness["weak_nodes"]["by_type"]),
            "",
            "## Authorship / Structure Gaps",
            "",
            (
                f"- Work nodes missing `authored_by`: "
                f"{completeness['authorship_and_structure']['work_missing_authored_by']['count']}/"
                f"{counts['node_types']['work']} "
                f"({percent(completeness['authorship_and_structure']['work_missing_authored_by']['count'], counts['node_types']['work'])})"
            ),
            (
                f"- Publication nodes missing `authored_by`: "
                f"{completeness['authorship_and_structure']['publication_missing_authored_by']['count']}/"
                f"{counts['node_types']['publication']} "
                f"({percent(completeness['authorship_and_structure']['publication_missing_authored_by']['count'], counts['node_types']['publication'])})"
            ),
            (
                f"- Quote nodes missing `authored_by`: "
                f"{completeness['authorship_and_structure']['quote_missing_authored_by']['count']}/"
                f"{counts['node_types']['quote']} "
                f"({percent(completeness['authorship_and_structure']['quote_missing_authored_by']['count'], counts['node_types']['quote'])})"
            ),
            (
                f"- Passage nodes missing `authored_by`: "
                f"{completeness['authorship_and_structure']['passage_missing_authored_by']['count']}/"
                f"{counts['node_types']['passage']} "
                f"({percent(completeness['authorship_and_structure']['passage_missing_authored_by']['count'], counts['node_types']['passage'])})"
            ),
            (
                f"- Passage nodes missing `part_of`: "
                f"{completeness['authorship_and_structure']['passage_missing_part_of']['count']}/"
                f"{counts['node_types']['passage']} "
                f"({percent(completeness['authorship_and_structure']['passage_missing_part_of']['count'], counts['node_types']['passage'])})"
            ),
            (
                f"- Translation integrity: "
                f"{completeness['authorship_and_structure']['translation_integrity']['translation_nodes']} English passage nodes, "
                f"{completeness['authorship_and_structure']['translation_integrity']['translation_nodes_missing_translation_of']} missing `translation_of`, "
                f"{completeness['authorship_and_structure']['translation_integrity']['source_nodes_with_translation_of']} source nodes incorrectly using `translation_of`."
            ),
            "",
            "- Representative missing authorship examples:",
            *row_lines(
                completeness["authorship_and_structure"][
                    "publication_missing_authored_by"
                ]["examples"],
                ["label", "node_id"],
                10,
            ),
            "",
            "## Formatting / Title Issues",
            "",
            (
                f"- Non-passage descriptions with markdown or list formatting: "
                f"{formatting['descriptions_with_markdown']['count']}"
            ),
            *counter_lines(formatting["descriptions_with_markdown"]["by_type"]),
            "",
            (
                f"- Non-passage descriptions with raw newlines: "
                f"{formatting['descriptions_with_newlines']['count']}"
            ),
            *counter_lines(formatting["descriptions_with_newlines"]["by_type"]),
            "",
            (
                f"- Passage labels with raw importer-style `chap.: / par.: / verset.:`: "
                f"{formatting['metadata_style_passage_labels']['count']}"
            ),
            (
                f"- Passage labels still containing underscores in the display title: "
                f"{formatting['underscore_passage_labels']['count']}"
            ),
            (
                f"- Suspicious ID/type prefix mismatches (e.g. `concept_*` typed as `synthesis`): "
                f"{formatting['suspicious_id_prefix_mismatches']['count']}"
            ),
            "",
            "- Representative suspicious ID/type mismatches:",
            *row_lines(
                formatting["suspicious_id_prefix_mismatches"]["examples"],
                ["type", "prefix", "label", "node_id"],
                10,
            ),
            "",
            "## Duplication",
            "",
            f"- Exact duplicate label groups: {len(completeness['exact_duplicate_labels'])}",
            *[
                f"- `{item['type']}` / `{item['label']}`: {item['count']} nodes"
                for item in completeness["exact_duplicate_labels"][:10]
            ],
            "",
            f"- Likely near-duplicate groups: {len(completeness['likely_near_duplicates'])}",
            *[
                f"- `{item['type']}`: `{item['label_a']}` vs `{item['label_b']}`"
                for item in completeness["likely_near_duplicates"][:10]
            ],
            "",
            "## Scope Drift Question",
            "",
            (
                f"- Nodes outside the ancient timeline (`Medieval`, `Early Modern`, `Modern`, `Contemporary`): "
                f"{scope_drift['post_antique_nodes']['count']}/"
                f"{counts['nodes']} "
                f"({percent(scope_drift['post_antique_nodes']['count'], counts['nodes'])})"
            ),
            *counter_lines(scope_drift["post_antique_nodes"]["by_period"]),
            "",
            "## Suggested Fix Order",
            "",
            "1. Keep the ontology and live relation inventory aligned, including `translation_of`, canonical semantic/debate relation names, and the live `passage -> debate` use of `contributes_to`.",
            "2. Repair the remaining provenance gaps on claim-bearing nodes, starting with the assertive claims that still lack evidence anchors.",
            "3. Fill remaining missing descriptions and empty metadata records, using only source-backed or metadata-backed content.",
            "4. Add the remaining missing `authored_by` links where a unique author can be proven from existing metadata, labels, or inherited work structure.",
            "5. Normalize the remaining raw importer-style passage labels and markdown-heavy node descriptions.",
            "6. Review the remaining duplicate candidates and scope-drift nodes that still require editorial judgment.",
            "",
            "## Artifacts",
            "",
            "- Full machine-readable details are in the sibling JSON report.",
        ]
    )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "docs" / "reports",
        help="Directory to write the Markdown and JSON reports into.",
    )
    parser.add_argument(
        "--basename",
        default=f"{datetime.now().date().isoformat()}-kg-quality-audit",
        help="Output file basename without extension.",
    )
    parser.add_argument(
        "--shacl",
        action="store_true",
        help=(
            "Also run the SHACL validation gate over the JSONL artifacts in "
            "data/kg/ and append a summary section to the Markdown report."
        ),
    )
    parser.add_argument(
        "--shacl-nodes",
        type=Path,
        default=ROOT / "data" / "kg" / "nodes.jsonl",
        help="Path to nodes.jsonl for SHACL validation.",
    )
    parser.add_argument(
        "--shacl-edges",
        type=Path,
        default=ROOT / "data" / "kg" / "edges.jsonl",
        help="Path to edges.jsonl for SHACL validation.",
    )
    return parser.parse_args()


def run_shacl_audit(nodes_path: Path, edges_path: Path) -> dict[str, Any]:
    """Build the RDF graph and run SHACL validation; return a summary dict."""
    from eleutheria_kg.semantic import build_graph
    from eleutheria_kg.semantic.shapes import load_shapes
    from eleutheria_kg.semantic.validator import validate_kg

    graph = build_graph(nodes_path, edges_path)
    shapes = load_shapes()
    report = validate_kg(graph, shapes)

    buckets = {"claims": 0, "formatting": 0, "core": 0, "other": 0}
    for v in report.violations:
        shape = v.source_shape or ""
        if "NeedsEvidence" in shape:
            buckets["claims"] += 1
        elif "DescriptionHygiene" in shape or "Period" in shape:
            buckets["formatting"] += 1
        elif "IdPrefix" in shape or "_Range" in shape or "_Domain" in shape:
            buckets["core"] += 1
        else:
            buckets["other"] += 1

    return {
        "conforms": report.conforms,
        "violation_count": report.violation_count,
        "duration_seconds": report.duration_seconds,
        "by_severity": dict(report.by_severity()),
        "by_bucket": buckets,
        "by_shape": dict(report.by_shape().most_common(20)),
    }


def render_shacl_section(summary: dict[str, Any]) -> str:
    lines = [
        "",
        "## SHACL Validation (Phase B Quality Gate)",
        "",
        f"- Conforms: {summary['conforms']}",
        f"- Total violations: {summary['violation_count']}",
        f"- Validation duration: {summary['duration_seconds']:.2f}s",
        "",
        "### By severity",
        "",
    ]
    for severity, count in sorted(
        summary["by_severity"].items(), key=lambda kv: (-kv[1], kv[0])
    ):
        lines.append(f"- `{severity}`: {count}")

    lines.extend(["", "### By shape bucket", ""])
    for bucket, count in summary["by_bucket"].items():
        lines.append(f"- `{bucket}.ttl`: {count}")

    lines.extend(["", "### Top shapes", ""])
    for shape, count in sorted(
        summary["by_shape"].items(), key=lambda kv: (-kv[1], kv[0])
    )[:15]:
        short = shape.rsplit("/", 1)[-1] if shape else "<bnode>"
        lines.append(f"- `{short}`: {count}")
    return "\n".join(lines) + "\n"


async def async_main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = await fetch_dataset()
    report = analyze(dataset)

    markdown_path = args.output_dir / f"{args.basename}.md"
    json_path = args.output_dir / f"{args.basename}.json"

    markdown_body = render_markdown(report)

    if args.shacl:
        shacl_summary = run_shacl_audit(args.shacl_nodes, args.shacl_edges)
        report["shacl"] = shacl_summary
        markdown_body += render_shacl_section(shacl_summary)

    markdown_path.write_text(markdown_body)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    print(f"Wrote {markdown_path}")
    print(f"Wrote {json_path}")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
