#!/usr/bin/env python3
"""
Deterministically repair reviewed KG quality issues in the live PostgreSQL graph.

This script intentionally avoids speculative content generation. It only applies:
- reviewed relation normalization
- reviewed duplicate-person merges
- metadata-only person description backfills
- deterministic `authored_by` / `part_of` backfills from existing KG metadata
- reviewed period normalization / override fixes

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/fix_kg_quality.py
    uv run --directory database python database/scripts/fix_kg_quality.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
REPAIR_TAG = "kg_quality_repair_2026_03_06"
AUTO_CREATED_PERSON_DESCRIPTION = "Author of ancient texts (auto-created by SC import)"

RELATION_NORMALIZATION = {
    "participated_in": "participates_in",
    "relates_to": "related_to",
}

PERIOD_NORMALIZATION = {
    "Late Republic": "Roman Republican",
}

# Reviewed against the live graph on 2026-03-06.
REVIEWED_PERSON_MERGES = {
    "person_irenaeus_lyon_d202": "person_irenaeus_d202",
    "person_tatian_2c_ce": "person_tatian",
    "person_lucretius_d55bce": "person_lucretius_99_55bce_k1l2m3n4",
    "origenes": "person_origen_alexandria_185_254ce_s9t0u1v2",
    "person_methodius_olympus_c250_c311": "person_methodius_olympus_d311",
    "person_pelagius_british_monk_4ba38f92": "person_pelagius_d420",
}

# Reviewed from the duplicate Lucretius metadata already present in the graph.
REVIEWED_PERIOD_OVERRIDES = {
    "person_lucretius_99_55bce_k1l2m3n4": "Roman Republican",
}

GENERIC_AUTHOR_KEYS = {
    "anonymous",
    "anonyme",
    "unknown",
}

PERSON_DESCRIPTION_FIELDS = [
    ("note", "Note"),
    ("roles", "Roles"),
    ("school", "School"),
    ("location", "Location"),
    ("floruit", "Floruit"),
    ("birth_year", "Birth year"),
    ("birth_date", "Birth date"),
    ("death_year", "Death year"),
    ("death_date", "Death date"),
]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def parse_json_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return copy.deepcopy(parsed) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def parse_json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
    return []


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def unique_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        key = normalize_text(cleaned)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered


def merge_metadata(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(primary)
    for key, value in secondary.items():
        if key not in merged or merged[key] in (None, "", [], {}):
            merged[key] = copy.deepcopy(value)
    return merged


def format_metadata_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def build_person_description(metadata: dict[str, Any]) -> str | None:
    parts: list[str] = []
    for key, label in PERSON_DESCRIPTION_FIELDS:
        value = metadata.get(key)
        if value in (None, "", [], {}):
            continue
        parts.append(f"{label}: {format_metadata_value(value)}")
    return "; ".join(parts) if parts else None


def expanded_person_aliases(label: str, alternative_names: list[str]) -> list[str]:
    aliases: list[str] = [label]
    if label:
        stripped = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip()
        if stripped and stripped != label:
            aliases.append(stripped)
        for part in re.findall(r"\((.*?)\)", label):
            if part.strip():
                aliases.append(part.strip())
    aliases.extend(alternative_names)
    return unique_preserve(aliases)


def normalize_author_key(value: str | None) -> str:
    return normalize_text(value)


def quote_author_candidate(label: str) -> str | None:
    if ":" in label:
        lead = label.split(":", 1)[0].strip()
        if "via" in lead.lower():
            return None
        return lead or None
    match = re.match(r"^(.+?)\s+on\s+", label)
    if match:
        lead = match.group(1).strip()
        if "via" in lead.lower():
            return None
        return lead or None
    return None


@dataclass
class Record:
    original: dict[str, Any] | None
    current: dict[str, Any]
    deleted: bool = False
    is_new: bool = False


class WorkingGraph:
    def __init__(
        self,
        *,
        nodes: dict[str, Record],
        edges: dict[str, Record],
        citations: dict[str, Record],
        passage_to_work_id: dict[str, str],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.citations = citations
        self.passage_to_work_id = passage_to_work_id
        self._new_edge_counter = 0
        self.rebuild_edge_indexes()
        self.rebuild_citation_indexes()

    def rebuild_edge_indexes(self) -> None:
        self.edge_ids_by_triple: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        self.targets_by_source_relation: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.sources_by_target_relation: dict[tuple[str, str], list[str]] = defaultdict(list)
        for edge_id, record in self.edges.items():
            if record.deleted:
                continue
            edge = record.current
            triple = (edge["source_id"], edge["target_id"], edge["relation"])
            self.edge_ids_by_triple[triple].append(edge_id)
            self.targets_by_source_relation[(edge["source_id"], edge["relation"])].append(
                edge["target_id"]
            )
            self.sources_by_target_relation[(edge["target_id"], edge["relation"])].append(
                edge["source_id"]
            )

    def rebuild_citation_indexes(self) -> None:
        self.citation_ids_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
        for citation_id, record in self.citations.items():
            if record.deleted:
                continue
            citation = record.current
            pair = (citation["passage_id"], citation["kg_node_id"])
            self.citation_ids_by_pair[pair].append(citation_id)

    def node_exists(self, node_id: str) -> bool:
        record = self.nodes.get(node_id)
        return bool(record) and not record.deleted

    def edge_exists(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        *,
        exclude_edge_id: str | None = None,
    ) -> bool:
        edge_ids = self.edge_ids_by_triple.get((source_id, target_id, relation), [])
        return any(edge_id != exclude_edge_id for edge_id in edge_ids)

    def unique_targets(self, source_id: str, relation: str) -> list[str]:
        values = self.targets_by_source_relation.get((source_id, relation), [])
        return sorted(set(values))

    def unique_sources(self, target_id: str, relation: str) -> list[str]:
        values = self.sources_by_target_relation.get((target_id, relation), [])
        return sorted(set(values))

    def update_node(self, node_id: str, **changes: Any) -> bool:
        record = self.nodes[node_id]
        changed = False
        for key, value in changes.items():
            if record.current.get(key) != value:
                record.current[key] = value
                changed = True
        return changed

    def add_edge(self, source_id: str, target_id: str, relation: str, reason: str) -> bool:
        if self.edge_exists(source_id, target_id, relation):
            return False
        edge_id = f"__new_edge_{self._new_edge_counter}"
        self._new_edge_counter += 1
        self.edges[edge_id] = Record(
            original=None,
            current={
                "edge_id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation": relation,
                "metadata": {
                    "repair_source": REPAIR_TAG,
                    "repair_reason": reason,
                },
            },
            is_new=True,
        )
        self.rebuild_edge_indexes()
        return True

    def update_edge(self, edge_id: str, *, source_id: str, target_id: str, relation: str) -> None:
        edge = self.edges[edge_id].current
        edge["source_id"] = source_id
        edge["target_id"] = target_id
        edge["relation"] = relation

    def delete_edge(self, edge_id: str) -> None:
        self.edges[edge_id].deleted = True

    def delete_node(self, node_id: str) -> None:
        self.nodes[node_id].deleted = True

    def update_citation_node(self, citation_id: str, kg_node_id: str) -> None:
        self.citations[citation_id].current["kg_node_id"] = kg_node_id

    def delete_citation(self, citation_id: str) -> None:
        self.citations[citation_id].deleted = True


async def fetch_graph() -> WorkingGraph:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        await conn.execute(f"SET search_path = {SCHEMA}, public;")
        node_rows = await conn.fetch(
            """
            SELECT node_id, label, type, period, description, alternative_names, metadata
            FROM kg_nodes
            ORDER BY node_id
            """
        )
        edge_rows = await conn.fetch(
            """
            SELECT edge_id::text AS edge_id, source_id, target_id, relation, metadata
            FROM kg_edges
            ORDER BY edge_id
            """
        )
        citation_rows = await conn.fetch(
            """
            SELECT citation_id::text AS citation_id, passage_id::text AS passage_id,
                   kg_node_id, citation_type, confidence, notes
            FROM passage_citations
            ORDER BY citation_id
            """
        )
        passage_rows = await conn.fetch(
            """
            SELECT passage_id::text AS passage_id, work_id::text AS work_id
            FROM passages
            """
        )
    finally:
        await conn.close()

    nodes = {
        row["node_id"]: Record(
            original={
                "node_id": row["node_id"],
                "label": row["label"],
                "type": row["type"],
                "period": row["period"],
                "description": row["description"],
                "alternative_names": parse_json_list(row["alternative_names"]),
                "metadata": parse_json_dict(row["metadata"]),
            },
            current={
                "node_id": row["node_id"],
                "label": row["label"],
                "type": row["type"],
                "period": row["period"],
                "description": row["description"],
                "alternative_names": parse_json_list(row["alternative_names"]),
                "metadata": parse_json_dict(row["metadata"]),
            },
        )
        for row in node_rows
    }
    edges = {
        row["edge_id"]: Record(
            original={
                "edge_id": row["edge_id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "relation": row["relation"],
                "metadata": parse_json_dict(row["metadata"]),
            },
            current={
                "edge_id": row["edge_id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "relation": row["relation"],
                "metadata": parse_json_dict(row["metadata"]),
            },
        )
        for row in edge_rows
    }
    citations = {
        row["citation_id"]: Record(
            original={
                "citation_id": row["citation_id"],
                "passage_id": row["passage_id"],
                "kg_node_id": row["kg_node_id"],
                "citation_type": row["citation_type"],
                "confidence": row["confidence"],
                "notes": row["notes"],
            },
            current={
                "citation_id": row["citation_id"],
                "passage_id": row["passage_id"],
                "kg_node_id": row["kg_node_id"],
                "citation_type": row["citation_type"],
                "confidence": row["confidence"],
                "notes": row["notes"],
            },
        )
        for row in citation_rows
    }
    passage_to_work_id = {row["passage_id"]: row["work_id"] for row in passage_rows}

    return WorkingGraph(
        nodes=nodes,
        edges=edges,
        citations=citations,
        passage_to_work_id=passage_to_work_id,
    )


def apply_relation_normalization(graph: WorkingGraph, summary: dict[str, Any]) -> None:
    for edge_id, record in list(graph.edges.items()):
        if record.deleted:
            continue
        old_relation = record.current["relation"]
        new_relation = RELATION_NORMALIZATION.get(old_relation)
        if not new_relation:
            continue
        edge = record.current
        if graph.edge_exists(edge["source_id"], edge["target_id"], new_relation, exclude_edge_id=edge_id):
            graph.delete_edge(edge_id)
            summary["relation_duplicates_removed"] += 1
            continue
        graph.update_edge(
            edge_id,
            source_id=edge["source_id"],
            target_id=edge["target_id"],
            relation=new_relation,
        )
        summary["relation_updates"][f"{old_relation}->{new_relation}"] += 1
    graph.rebuild_edge_indexes()


def merge_person_nodes(graph: WorkingGraph, summary: dict[str, Any]) -> None:
    for source_id, target_id in REVIEWED_PERSON_MERGES.items():
        if not graph.node_exists(source_id) or not graph.node_exists(target_id):
            continue
        source = graph.nodes[source_id].current
        target = graph.nodes[target_id].current
        if source["type"] != "person" or target["type"] != "person":
            continue

        merged_alternative_names = unique_preserve(
            target["alternative_names"]
            + [target["label"], source["label"]]
            + source["alternative_names"]
        )
        merged_alternative_names = [name for name in merged_alternative_names if name != target["label"]]
        merged_metadata = merge_metadata(target["metadata"], source["metadata"])
        merged_description = target["description"] or source["description"]
        merged_period = target["period"]
        if merged_period in PERIOD_NORMALIZATION:
            merged_period = PERIOD_NORMALIZATION[merged_period]
        if not merged_period and source["period"]:
            merged_period = PERIOD_NORMALIZATION.get(source["period"], source["period"])

        if graph.update_node(
            target_id,
            alternative_names=merged_alternative_names,
            metadata=merged_metadata,
            description=merged_description,
            period=merged_period,
        ):
            summary["node_updates"]["merged_person_fields"] += 1

        for edge_id, record in list(graph.edges.items()):
            if record.deleted:
                continue
            edge = record.current
            if edge["source_id"] != source_id and edge["target_id"] != source_id:
                continue
            new_source = target_id if edge["source_id"] == source_id else edge["source_id"]
            new_target = target_id if edge["target_id"] == source_id else edge["target_id"]
            if new_source == new_target:
                graph.delete_edge(edge_id)
                summary["merge_edges_dropped_self_loop"] += 1
                continue
            if graph.edge_exists(
                new_source,
                new_target,
                edge["relation"],
                exclude_edge_id=edge_id,
            ):
                graph.delete_edge(edge_id)
                summary["merge_edges_dropped_duplicate"] += 1
                continue
            graph.update_edge(
                edge_id,
                source_id=new_source,
                target_id=new_target,
                relation=edge["relation"],
            )
            summary["merge_edges_rewired"] += 1
        graph.rebuild_edge_indexes()

        for citation_id, record in list(graph.citations.items()):
            if record.deleted or record.current["kg_node_id"] != source_id:
                continue
            pair = (record.current["passage_id"], target_id)
            existing_ids = graph.citation_ids_by_pair.get(pair, [])
            if any(other_id != citation_id for other_id in existing_ids):
                graph.delete_citation(citation_id)
                summary["merge_citations_dropped_duplicate"] += 1
            else:
                graph.update_citation_node(citation_id, target_id)
                summary["merge_citations_rewired"] += 1
        graph.rebuild_citation_indexes()

        graph.delete_node(source_id)
        summary["person_merges_applied"] += 1
        summary["person_nodes_deleted"] += 1


def normalize_periods(graph: WorkingGraph, summary: dict[str, Any]) -> None:
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        period = record.current["period"]
        normalized = PERIOD_NORMALIZATION.get(period)
        if normalized and graph.update_node(node_id, period=normalized):
            summary["node_updates"]["period_normalized"] += 1

    for node_id, new_period in REVIEWED_PERIOD_OVERRIDES.items():
        if graph.node_exists(node_id) and graph.update_node(node_id, period=new_period):
            summary["node_updates"]["period_override"] += 1


def backfill_person_descriptions(graph: WorkingGraph, summary: dict[str, Any]) -> None:
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        node = record.current
        if node["type"] != "person":
            continue
        if (node["description"] or "").strip():
            continue
        description = build_person_description(node["metadata"])
        if description and graph.update_node(node_id, description=description):
            summary["node_updates"]["person_description_backfilled"] += 1


def build_person_alias_index(graph: WorkingGraph) -> dict[str, set[str]]:
    alias_index: dict[str, set[str]] = defaultdict(set)
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        node = record.current
        if node["type"] != "person":
            continue
        for alias in expanded_person_aliases(node["label"], node["alternative_names"]):
            key = normalize_author_key(alias)
            if key:
                alias_index[key].add(node_id)
    return alias_index


def unique_person_match(
    value: str | None,
    alias_index: dict[str, set[str]],
) -> str | None:
    key = normalize_author_key(value)
    if not key or key in GENERIC_AUTHOR_KEYS:
        return None
    matches = sorted(alias_index.get(key, set()))
    if len(matches) == 1:
        return matches[0]
    return None


def backfill_work_and_publication_authors(
    graph: WorkingGraph,
    alias_index: dict[str, set[str]],
    summary: dict[str, Any],
) -> None:
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        node = record.current
        if node["type"] not in {"work", "publication"}:
            continue
        if graph.unique_targets(node_id, "authored_by"):
            continue
        author_name = str(node["metadata"].get("author") or "").strip()
        person_id = unique_person_match(author_name, alias_index)
        if not person_id:
            continue
        if graph.add_edge(
            node_id,
            person_id,
            "authored_by",
            f"backfilled_from_{node['type']}_metadata_author",
        ):
            summary["edge_inserts"]["authored_by"] += 1


def backfill_quote_authors(
    graph: WorkingGraph,
    alias_index: dict[str, set[str]],
    summary: dict[str, Any],
) -> None:
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        node = record.current
        if node["type"] != "quote":
            continue
        if graph.unique_targets(node_id, "authored_by"):
            continue
        candidate = quote_author_candidate(node["label"])
        person_id = unique_person_match(candidate, alias_index)
        if not person_id:
            continue
        if graph.add_edge(
            node_id,
            person_id,
            "authored_by",
            "backfilled_from_quote_label",
        ):
            summary["edge_inserts"]["authored_by"] += 1


def work_id_to_kg_work_nodes(graph: WorkingGraph) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    for node_id, record in graph.nodes.items():
        if record.deleted:
            continue
        node = record.current
        if node["type"] != "work":
            continue
        work_id = str(node["metadata"].get("work_id") or "").strip()
        if work_id:
            mapping[work_id].add(node_id)
    return mapping


def backfill_passage_part_of(graph: WorkingGraph, summary: dict[str, Any]) -> None:
    work_mapping = work_id_to_kg_work_nodes(graph)

    changed = True
    while changed:
        changed = False
        for node_id, record in graph.nodes.items():
            if record.deleted:
                continue
            node = record.current
            if node["type"] != "passage":
                continue
            if graph.unique_targets(node_id, "part_of"):
                continue

            candidates: set[str] = set()
            metadata = node["metadata"]

            work_node_id = str(metadata.get("work_node_id") or "").strip()
            if work_node_id and graph.node_exists(work_node_id):
                target_node = graph.nodes[work_node_id].current
                if target_node["type"] == "work":
                    candidates.add(work_node_id)

            for original_id in graph.unique_targets(node_id, "translation_of"):
                candidates.update(graph.unique_targets(original_id, "part_of"))

            original_node_id = str(metadata.get("original_node_id") or "").strip()
            if original_node_id:
                candidates.update(graph.unique_targets(original_node_id, "part_of"))

            passage_id = str(metadata.get("db_passage_id") or metadata.get("passage_id") or "").strip()
            if passage_id:
                work_id = graph.passage_to_work_id.get(passage_id)
                if work_id:
                    candidates.update(work_mapping.get(work_id, set()))

            candidates = {candidate for candidate in candidates if graph.node_exists(candidate)}
            if len(candidates) != 1:
                continue

            if graph.add_edge(
                node_id,
                next(iter(candidates)),
                "part_of",
                "backfilled_from_passage_metadata",
            ):
                summary["edge_inserts"]["part_of"] += 1
                changed = True


def backfill_passage_authors(
    graph: WorkingGraph,
    alias_index: dict[str, set[str]],
    summary: dict[str, Any],
) -> None:
    changed = True
    while changed:
        changed = False
        for node_id, record in graph.nodes.items():
            if record.deleted:
                continue
            node = record.current
            if node["type"] != "passage":
                continue
            if graph.unique_targets(node_id, "authored_by"):
                continue

            candidates: set[str] = set()

            for original_id in graph.unique_targets(node_id, "translation_of"):
                candidates.update(graph.unique_targets(original_id, "authored_by"))

            for work_id in graph.unique_targets(node_id, "part_of"):
                candidates.update(graph.unique_targets(work_id, "authored_by"))

            author_name = str(node["metadata"].get("author") or "").strip()
            person_id = unique_person_match(author_name, alias_index)
            if person_id:
                candidates.add(person_id)

            candidates = {candidate for candidate in candidates if graph.node_exists(candidate)}
            if len(candidates) != 1:
                continue

            if graph.add_edge(
                node_id,
                next(iter(candidates)),
                "authored_by",
                "backfilled_from_passage_metadata_or_structure",
            ):
                summary["edge_inserts"]["authored_by"] += 1
                changed = True


def plan_repairs(graph: WorkingGraph) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "relation_updates": Counter(),
        "relation_duplicates_removed": 0,
        "person_merges_applied": 0,
        "person_nodes_deleted": 0,
        "merge_edges_rewired": 0,
        "merge_edges_dropped_duplicate": 0,
        "merge_edges_dropped_self_loop": 0,
        "merge_citations_rewired": 0,
        "merge_citations_dropped_duplicate": 0,
        "node_updates": Counter(),
        "edge_inserts": Counter(),
    }

    apply_relation_normalization(graph, summary)
    merge_person_nodes(graph, summary)
    normalize_periods(graph, summary)
    backfill_person_descriptions(graph, summary)

    alias_index = build_person_alias_index(graph)
    backfill_work_and_publication_authors(graph, alias_index, summary)
    backfill_quote_authors(graph, alias_index, summary)
    backfill_passage_part_of(graph, summary)
    backfill_passage_authors(graph, alias_index, summary)

    summary["final_counts"] = {
        "nodes_deleted": sum(1 for record in graph.nodes.values() if record.deleted and not record.is_new),
        "edges_inserted": sum(1 for record in graph.edges.values() if record.is_new and not record.deleted),
        "edges_updated": sum(
            1
            for record in graph.edges.values()
            if (
                record.original is not None
                and not record.deleted
                and (
                    record.original["source_id"] != record.current["source_id"]
                    or record.original["target_id"] != record.current["target_id"]
                    or record.original["relation"] != record.current["relation"]
                )
            )
        ),
        "edges_deleted": sum(
            1 for record in graph.edges.values() if record.original is not None and record.deleted
        ),
        "citations_updated": sum(
            1
            for record in graph.citations.values()
            if (
                record.original is not None
                and not record.deleted
                and record.original["kg_node_id"] != record.current["kg_node_id"]
            )
        ),
        "citations_deleted": sum(
            1 for record in graph.citations.values() if record.original is not None and record.deleted
        ),
        "nodes_updated": sum(
            1
            for record in graph.nodes.values()
            if (
                record.original is not None
                and not record.deleted
                and (
                    record.original["period"] != record.current["period"]
                    or record.original["description"] != record.current["description"]
                    or record.original["alternative_names"] != record.current["alternative_names"]
                    or record.original["metadata"] != record.current["metadata"]
                )
            )
        ),
    }
    return summary


async def apply_repairs(graph: WorkingGraph) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        async with conn.transaction():
            await conn.execute(f"SET search_path = {SCHEMA}, public;")

            for edge_id, record in graph.edges.items():
                if record.original is None or record.deleted:
                    continue
                changed = (
                    record.original["source_id"] != record.current["source_id"]
                    or record.original["target_id"] != record.current["target_id"]
                    or record.original["relation"] != record.current["relation"]
                )
                if not changed:
                    continue
                await conn.execute(
                    """
                    UPDATE kg_edges
                    SET source_id = $2, target_id = $3, relation = $4
                    WHERE edge_id = $1::uuid
                    """,
                    edge_id,
                    record.current["source_id"],
                    record.current["target_id"],
                    record.current["relation"],
                )

            for edge_id, record in graph.edges.items():
                if record.original is None or not record.deleted:
                    continue
                await conn.execute("DELETE FROM kg_edges WHERE edge_id = $1::uuid", edge_id)

            for _edge_id, record in graph.edges.items():
                if record.original is not None or record.deleted:
                    continue
                await conn.execute(
                    """
                    INSERT INTO kg_edges (source_id, target_id, relation, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                    """,
                    record.current["source_id"],
                    record.current["target_id"],
                    record.current["relation"],
                    json_dumps(record.current["metadata"]),
                )

            for citation_id, record in graph.citations.items():
                if record.original is None or record.deleted:
                    continue
                if record.original["kg_node_id"] == record.current["kg_node_id"]:
                    continue
                await conn.execute(
                    """
                    UPDATE passage_citations
                    SET kg_node_id = $2
                    WHERE citation_id = $1::uuid
                    """,
                    citation_id,
                    record.current["kg_node_id"],
                )

            for citation_id, record in graph.citations.items():
                if record.original is None or not record.deleted:
                    continue
                await conn.execute(
                    "DELETE FROM passage_citations WHERE citation_id = $1::uuid",
                    citation_id,
                )

            for node_id, record in graph.nodes.items():
                if record.original is None or record.deleted:
                    continue
                changed = (
                    record.original["period"] != record.current["period"]
                    or record.original["description"] != record.current["description"]
                    or record.original["alternative_names"] != record.current["alternative_names"]
                    or record.original["metadata"] != record.current["metadata"]
                )
                if not changed:
                    continue
                await conn.execute(
                    """
                    UPDATE kg_nodes
                    SET period = $2,
                        description = $3,
                        alternative_names = $4::jsonb,
                        metadata = $5::jsonb,
                        updated_at = NOW()
                    WHERE node_id = $1
                    """,
                    node_id,
                    record.current["period"],
                    record.current["description"],
                    json_dumps(record.current["alternative_names"]),
                    json_dumps(record.current["metadata"]),
                )

            for node_id, record in graph.nodes.items():
                if record.original is None or not record.deleted:
                    continue
                await conn.execute("DELETE FROM kg_nodes WHERE node_id = $1", node_id)
    finally:
        await conn.close()


def serialize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(summary)
    output["relation_updates"] = dict(output["relation_updates"])
    output["node_updates"] = dict(output["node_updates"])
    output["edge_inserts"] = dict(output["edge_inserts"])
    return output


def print_summary(summary: dict[str, Any], *, confirmed: bool) -> None:
    payload = serialize_summary(summary)
    mode = "APPLIED" if confirmed else "DRY RUN"
    print(f"[{mode}] KG repair summary")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Repair reviewed KG quality issues")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually write the planned repairs to the database.",
    )
    parser.add_argument(
        "--report-json",
        help="Optional path for the repair summary JSON.",
    )
    args = parser.parse_args()

    graph = await fetch_graph()
    summary = plan_repairs(graph)
    print_summary(summary, confirmed=args.confirm)

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json_dumps(serialize_summary(summary)) + "\n",
            encoding="utf-8",
        )

    if not args.confirm:
        return

    await apply_repairs(graph)


if __name__ == "__main__":
    asyncio.run(main())
