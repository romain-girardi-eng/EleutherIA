#!/usr/bin/env python3
"""Repair safe academic/source integrity issues in the KG.

This script intentionally limits itself to structural fixes where the evidence is
already present in the graph:

- merge stale ``passage_basil_hex_*`` Eusebius PE clones into the canonical
  ``passage_eusebius_praep_ev_book_*`` nodes;
- correct Origen bilingual source anchors that were misclassified as standalone
  translations;
- normalize known synthesis node identifiers where ``id`` and ``node_id``
  disagree;
- add missing ``has_translation`` inverse edges for existing
  ``translation_of`` edges.

It does not infer new scholarly evidence claims.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from database.scripts.bootstrap_supabase import json_dumps, normalize_mapping
from database.scripts.philological_audit import _common


KG_ROOT = REPO_ROOT / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"
STATS_PATH = KG_ROOT / "stats.json"

CREATED_BY = "repair_academic_kg_integrity_2026_05_17"
WORK_EUSEBIUS = "work_eusebius_praeparatio_evangelica"
WORK_BASIL = "work_basil_hexaemeron"
PERSON_EUSEBIUS = "person_eusebius_caesarea_d339"
PERSON_BASIL = "person_basil_great_d379"
CTS_EUSEBIUS_BASE = "urn:cts:greekLit:tlg2018.tlg001.1st1K-grc1"
EUSEBIUS_TEI_URL = (
    "https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/"
    "data/tlg2018/tlg001/tlg2018.tlg001.1st1K-grc1.xml"
)

ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
    13: "XIII",
    14: "XIV",
    15: "XV",
}

SYNTHESIS_RENAMES = {
    "concept_cic_fat_index": "synthesis_cic_fat_index",
    "concept_cic_fat_synthesis": "synthesis_cic_fat_in_nostra_potestate",
    "concept_ditte_hamartia_double_sin_plotinus": "synthesis_ditte_hamartia_double_sin_plotinus",
    "concept_epict_eph_hemin_synthesis": "synthesis_epict_eph_hemin_doctrine",
    "concept_epict_thematic_index": "synthesis_epict_thematic_index",
}


@dataclass
class RepairResult:
    node_updates: dict[str, dict[str, Any]] = field(default_factory=dict)
    removed_nodes: set[str] = field(default_factory=set)
    edge_updates: dict[int, dict[str, Any]] = field(default_factory=dict)
    appended_edges: list[dict[str, Any]] = field(default_factory=list)
    skipped_edge_indexes: set[int] = field(default_factory=set)
    counters: Counter[str] = field(default_factory=Counter)


def parse_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def metadata_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source") or edge.get("source_id") or "")


def edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target") or edge.get("target_id") or "")


def eusebius_book_id(book_num: int) -> str:
    return f"passage_eusebius_praep_ev_book_{book_num:02d}"


def basil_clone_id(book_num: int) -> str:
    return f"passage_basil_hex_{book_num}"


def is_eusebius_book(nid: str) -> bool:
    return nid.startswith("passage_eusebius_praep_ev_book_")


def load_jsonl_with_raw(path: Path) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            if raw.strip():
                rows.append((raw, json.loads(raw)))
    return rows


def write_nodes(
    path: Path,
    rows: list[tuple[str, dict[str, Any]]],
    result: RepairResult,
) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for raw, node in rows:
            nid = node_id(node)
            if nid in result.removed_nodes:
                continue
            updated = result.node_updates.get(nid)
            if updated is not None:
                fh.write(json.dumps(updated, ensure_ascii=False))
                fh.write("\n")
            else:
                fh.write(raw)
        for edge in []:
            # Keeps static analyzers from mistaking this writer for the edge writer.
            _ = edge
    tmp.replace(path)


def write_edges(
    path: Path,
    rows: list[tuple[str, dict[str, Any]]],
    result: RepairResult,
) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for idx, (raw, _edge) in enumerate(rows):
            if idx in result.skipped_edge_indexes:
                continue
            updated = result.edge_updates.get(idx)
            if updated is not None:
                fh.write(json.dumps(updated, ensure_ascii=False))
                fh.write("\n")
            else:
                fh.write(raw)
        for edge in result.appended_edges:
            fh.write(json.dumps(edge, ensure_ascii=False, separators=(",", ":")))
            fh.write("\n")
    tmp.replace(path)


def update_stats(nodes_path: Path, edges_path: Path, stats_path: Path) -> dict[str, Any]:
    node_types: Counter[str] = Counter()
    edge_relations: Counter[str] = Counter()
    total_nodes = 0
    total_edges = 0
    with nodes_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            node = json.loads(line)
            node_types[str(node.get("type") or "unknown")] += 1
            total_nodes += 1
    with edges_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            edge = json.loads(line)
            edge_relations[str(edge.get("relation") or "related_to")] += 1
            total_edges += 1
    stats = {
        "edge_relations": dict(sorted(edge_relations.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_types": dict(sorted(node_types.items())),
        "total_edges": total_edges,
        "total_nodes": total_nodes,
    }
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


def repair_origen_source_anchor(node: dict[str, Any], now: str) -> bool:
    md = parse_metadata(node.get("metadata"))
    if md.get("passage_role") != "translation":
        return False
    if not node_id(node).startswith("passage_origen_"):
        return False
    if not (node.get("description_grc") or node.get("description_la")):
        return False

    md["passage_role"] = "original"
    md["translation_note"] = (
        "Primary-source anchor with original Greek/Latin text fields and helper "
        "translations/summaries; not a standalone translation node."
    )
    if node.get("description_grc") and not md.get("language"):
        md["language"] = "grc"
    md["metadata_repaired_by"] = CREATED_BY
    md["metadata_repaired_at"] = now
    node["metadata"] = metadata_json(md)
    if "updated_at" in node:
        node["updated_at"] = now
    return True


def merge_eusebius_book_node(
    stub: dict[str, Any],
    clone: dict[str, Any],
    book_num: int,
    now: str,
) -> None:
    clone_md = parse_metadata(clone.get("metadata"))
    stub_md = parse_metadata(stub.get("metadata"))
    text = str(clone.get("description") or "")
    roman = ROMAN[book_num]

    md = {
        **stub_md,
        **clone_md,
        "attestation_type": "direct",
        "author": "Eusebius of Caesarea",
        "author_id": PERSON_EUSEBIUS,
        "book_number": book_num,
        "book_roman": roman,
        "canonical_ref": f"PE {book_num}",
        "cts_urn": f"{CTS_EUSEBIUS_BASE}:{book_num}",
        "edition": "Dindorf t. I-IV (Leipzig 1867), re-encoded TEI by Digital Divide Data / Univ. Leipzig",
        "language": "grc",
        "merged_from_node_id": basil_clone_id(book_num),
        "metadata_repaired_by": CREATED_BY,
        "metadata_repaired_at": now,
        "passage_role": "original",
        "repair_note": (
            "Merged stale passage_basil_hex_* clone into canonical Eusebius "
            "Praeparatio Evangelica book node."
        ),
        "school": "Patristic",
        "source_tei": "OpenGreekAndLatin/First1KGreek tlg2018.tlg001.1st1K-grc1.xml",
        "source_tei_url": EUSEBIUS_TEI_URL,
        "text_status": "book_level_monolithic",
        "work_canonical_id": "tlg2018.tlg001.1st1K-grc1",
        "work_title": "Praeparatio Evangelica",
    }
    md.pop("needs_text_ingestion", None)
    if text:
        md["char_length"] = len(text)
        md["word_count"] = len(text.split())
    if book_num == 6:
        md["legacy_monolithic"] = True
        md["superseded_by_sections"] = (
            "passage_eusebius_praep_ev_6_6_1 .. passage_eusebius_praep_ev_6_6_74"
        )

    stub["id"] = eusebius_book_id(book_num)
    stub["node_id"] = eusebius_book_id(book_num)
    stub["type"] = "passage"
    stub["label"] = f"Eusebius, Praeparatio Evangelica, book {roman}"
    stub["description"] = text
    stub["period"] = "Late Antiquity"
    stub["school"] = "Patristic"
    stub["role"] = None
    stub["metadata"] = metadata_json(md)
    stub["updated_at"] = now


def build_edge(source: str, target: str, relation: str, now: str, metadata: dict[str, Any]) -> dict[str, Any]:
    md = {"created_by": CREATED_BY, **metadata}
    return {
        "edge_id": str(uuid4()),
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "relation": relation,
        "weight": 1.0,
        "metadata": metadata_json(md),
        "created_at": now,
    }


def canonicalize_edge(
    edge: dict[str, Any],
    renames: dict[str, str],
    now: str,
) -> tuple[dict[str, Any], bool]:
    updated = dict(edge)
    changed = False
    endpoint_changed = False

    for field_name in ("source", "source_id", "target", "target_id"):
        value = updated.get(field_name)
        if isinstance(value, str) and value in renames:
            updated[field_name] = renames[value]
            changed = True
            endpoint_changed = True

    source = edge_source(updated)
    target = edge_target(updated)
    relation = str(updated.get("relation") or "")

    if relation == "authored_by" and is_eusebius_book(source) and target == PERSON_BASIL:
        target = PERSON_EUSEBIUS
        changed = True
        endpoint_changed = True
    if relation == "part_of" and is_eusebius_book(source) and target == WORK_BASIL:
        target = WORK_EUSEBIUS
        changed = True
        endpoint_changed = True

    source_mismatch = (
        updated.get("source") is not None
        and updated.get("source_id") is not None
        and updated.get("source") != updated.get("source_id")
    )
    target_mismatch = (
        updated.get("target") is not None
        and updated.get("target_id") is not None
        and updated.get("target") != updated.get("target_id")
    )

    if endpoint_changed or source_mismatch:
        updated["source"] = source
        updated["source_id"] = source
        changed = True
    if endpoint_changed or target_mismatch:
        updated["target"] = target
        updated["target_id"] = target
        changed = True

    if changed:
        md = parse_metadata(updated.get("metadata"))
        md.setdefault("repaired_by", CREATED_BY)
        md.setdefault("repaired_at", now)
        updated["metadata"] = metadata_json(md)
    return updated, changed


def compute_repairs(nodes_path: Path, edges_path: Path) -> tuple[
    list[tuple[str, dict[str, Any]]],
    list[tuple[str, dict[str, Any]]],
    RepairResult,
]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
    node_rows = load_jsonl_with_raw(nodes_path)
    edge_rows = load_jsonl_with_raw(edges_path)
    result = RepairResult()

    by_node_id = {node_id(node): node for _, node in node_rows}
    renames = dict(SYNTHESIS_RENAMES)

    for book_num in range(1, 16):
        old_id = basil_clone_id(book_num)
        new_id = eusebius_book_id(book_num)
        renames[old_id] = new_id
        clone = by_node_id.get(old_id)
        stub = by_node_id.get(new_id)
        if clone and stub:
            merge_eusebius_book_node(stub, clone, book_num, now)
            result.node_updates[new_id] = stub
            result.removed_nodes.add(old_id)
            result.counters["eusebius_books_merged"] += 1

    for _, node in node_rows:
        nid = node_id(node)
        if nid in result.removed_nodes or nid in result.node_updates:
            continue
        if nid in SYNTHESIS_RENAMES and node.get("id") == SYNTHESIS_RENAMES[nid]:
            node["node_id"] = SYNTHESIS_RENAMES[nid]
            md = parse_metadata(node.get("metadata"))
            md["renamed_from_node_id"] = nid
            md["metadata_repaired_by"] = CREATED_BY
            md["metadata_repaired_at"] = now
            node["metadata"] = metadata_json(md)
            if "updated_at" in node:
                node["updated_at"] = now
            result.node_updates[SYNTHESIS_RENAMES[nid]] = node
            result.counters["synthesis_node_ids_normalized"] += 1
        elif repair_origen_source_anchor(node, now):
            result.node_updates[nid] = node
            result.counters["origen_source_anchor_roles"] += 1

    eusebius_edge_seen: set[tuple[str, str, str]] = set()
    existing_has_translation: set[tuple[str, str]] = set()
    translation_edges: list[tuple[str, str]] = []

    for idx, (_raw, edge) in enumerate(edge_rows):
        updated, changed = canonicalize_edge(edge, renames, now)
        source = edge_source(updated)
        target = edge_target(updated)
        relation = str(updated.get("relation") or "")

        if relation == "has_translation":
            existing_has_translation.add((source, target))
        elif relation == "translation_of":
            translation_edges.append((source, target))

        if is_eusebius_book(source) and relation in {"part_of", "authored_by"}:
            triple = (source, relation, target)
            if triple in eusebius_edge_seen:
                result.skipped_edge_indexes.add(idx)
                result.counters["duplicate_eusebius_edges_removed"] += 1
                continue
            eusebius_edge_seen.add(triple)

        if changed:
            result.edge_updates[idx] = updated
            result.counters["edge_endpoints_normalized"] += 1

    final_existing = {
        (
            edge_source(result.edge_updates.get(idx, edge)),
            str(result.edge_updates.get(idx, edge).get("relation") or ""),
            edge_target(result.edge_updates.get(idx, edge)),
        )
        for idx, (_raw, edge) in enumerate(edge_rows)
        if idx not in result.skipped_edge_indexes
    }

    for book_num in range(1, 16):
        book_id = eusebius_book_id(book_num)
        for target, relation, md in (
            (WORK_EUSEBIUS, "part_of", {"auto_generated": True, "repair_scope": "eusebius_book_structure"}),
            (
                PERSON_EUSEBIUS,
                "authored_by",
                {"auto_generated": True, "propagated_from_work": True, "repair_scope": "eusebius_book_authorship"},
            ),
        ):
            triple = (book_id, relation, target)
            if triple not in final_existing:
                result.appended_edges.append(build_edge(book_id, target, relation, now, md))
                final_existing.add(triple)
                result.counters["eusebius_edges_inserted"] += 1

    for translation_node, source_node in translation_edges:
        if (source_node, translation_node) in existing_has_translation:
            continue
        result.appended_edges.append(
            build_edge(
                source_node,
                translation_node,
                "has_translation",
                now,
                {
                    "auto_generated": True,
                    "inverse_of_relation": "translation_of",
                    "repair_scope": "translation_inverse",
                },
            )
        )
        existing_has_translation.add((source_node, translation_node))
        result.counters["has_translation_edges_inserted"] += 1

    return node_rows, edge_rows, result


async def upsert_db_nodes(conn: asyncpg.Connection, nodes: list[dict[str, Any]]) -> int:
    count = 0
    for node in nodes:
        md = normalize_mapping(node.get("metadata"))
        alt = node.get("alternative_names")
        await conn.execute(
            """
            INSERT INTO free_will.kg_nodes (
                node_id, label, type, description, period, alternative_names, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
            ON CONFLICT (node_id) DO UPDATE SET
                label = EXCLUDED.label,
                type = EXCLUDED.type,
                description = EXCLUDED.description,
                period = EXCLUDED.period,
                alternative_names = EXCLUDED.alternative_names,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            """,
            node_id(node),
            node.get("label") or node_id(node),
            str(node.get("type") or "unknown").lower(),
            node.get("description"),
            node.get("period") or md.get("period"),
            json_dumps(alt if alt is not None else []),
            json_dumps(md),
        )
        count += 1
    return count


async def db_update_edge_id(conn: asyncpg.Connection, old_id: str, new_id: str) -> int:
    tag = {"repaired_by": CREATED_BY, "renamed_from": old_id}
    result = await conn.execute(
        """
        UPDATE free_will.kg_edges
        SET
            source_id = CASE WHEN source_id = $1::varchar THEN $2::varchar ELSE source_id END,
            target_id = CASE WHEN target_id = $1::varchar THEN $2::varchar ELSE target_id END,
            metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
        WHERE source_id = $1::varchar OR target_id = $1::varchar
        """,
        old_id,
        new_id,
        json.dumps(tag),
    )
    return int(result.split()[-1])


async def apply_db_repairs(
    conn: asyncpg.Connection,
    result: RepairResult,
    nodes_to_upsert: list[dict[str, Any]],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    changed_nodes = nodes_to_upsert or list(result.node_updates.values())

    async with conn.transaction():
        counts["db_nodes_upserted"] = await upsert_db_nodes(conn, changed_nodes)

        stale_node_ids = (
            set(result.removed_nodes)
            | set(SYNTHESIS_RENAMES)
            | {basil_clone_id(n) for n in range(1, 16)}
        )
        for old_id in sorted(stale_node_ids):
            new_id = SYNTHESIS_RENAMES.get(old_id)
            if old_id.startswith("passage_basil_hex_"):
                suffix = int(old_id.rsplit("_", 1)[-1])
                new_id = eusebius_book_id(suffix)
            if new_id:
                counts["db_edge_refs_renamed"] += await db_update_edge_id(conn, old_id, new_id)

        eusebius_books = [eusebius_book_id(n) for n in range(1, 16)]
        counts["db_eusebius_authorship_retargeted"] = int(
            (await conn.execute(
                """
                UPDATE free_will.kg_edges
                SET target_id = $2,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                WHERE relation = 'authored_by'
                  AND source_id = ANY($1::text[])
                  AND target_id = $4::varchar
                """,
                eusebius_books,
                PERSON_EUSEBIUS,
                json.dumps({"repaired_by": CREATED_BY, "repair_scope": "eusebius_authorship"}),
                PERSON_BASIL,
            )).split()[-1]
        )
        counts["db_eusebius_partof_retargeted"] = int(
            (await conn.execute(
                """
                UPDATE free_will.kg_edges
                SET target_id = $2,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                WHERE relation = 'part_of'
                  AND source_id = ANY($1::text[])
                  AND target_id = $4::varchar
                """,
                eusebius_books,
                WORK_EUSEBIUS,
                json.dumps({"repaired_by": CREATED_BY, "repair_scope": "eusebius_work"}),
                WORK_BASIL,
            )).split()[-1]
        )

        for book_id in eusebius_books:
            for target, relation, md in (
                (WORK_EUSEBIUS, "part_of", {"auto_generated": True, "repair_scope": "eusebius_book_structure"}),
                (
                    PERSON_EUSEBIUS,
                    "authored_by",
                    {"auto_generated": True, "propagated_from_work": True, "repair_scope": "eusebius_book_authorship"},
                ),
            ):
                await conn.execute(
                    """
                    INSERT INTO free_will.kg_edges (
                        edge_id, source_id, target_id, relation, weight, metadata
                    )
                    SELECT gen_random_uuid(), $1::varchar, $2::varchar, $3::varchar, 1.0, $4::jsonb
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM free_will.kg_edges
                        WHERE source_id = $1::varchar
                          AND target_id = $2::varchar
                          AND relation = $3::varchar
                    )
                    """,
                    book_id,
                    target,
                    relation,
                    json.dumps({"created_by": CREATED_BY, **md}),
                )

        counts["db_stub_citations_deleted"] = int(
            (await conn.execute(
                """
                DELETE FROM free_will.passage_citations pc
                USING free_will.passages p
                WHERE pc.passage_id = p.passage_id
                  AND pc.kg_node_id = ANY($1::text[])
                  AND p.text_content LIKE 'Stub pour la Préparation évangélique%'
                """,
                eusebius_books,
            )).split()[-1]
        )
        for book_num in range(1, 16):
            counts["db_basil_citations_retargeted"] += int(
                (await conn.execute(
                    """
                    UPDATE free_will.passage_citations
                    SET kg_node_id = $2
                    WHERE kg_node_id = $1
                    """,
                    basil_clone_id(book_num),
                    eusebius_book_id(book_num),
                )).split()[-1]
            )

        eusebius_work_id = await conn.fetchval(
            """
            SELECT work_id
            FROM free_will.ancient_works
            WHERE kg_work_id = $1
              AND author = 'Eusebius of Caesarea'
              AND title = 'Praeparatio Evangelica'
              AND language = 'grc'
            ORDER BY created_at NULLS LAST
            LIMIT 1
            """,
            WORK_EUSEBIUS,
        )
        if eusebius_work_id:
            for book_num in range(1, 16):
                counts["db_eusebius_passages_corrected"] += int(
                    (await conn.execute(
                        """
                        UPDATE free_will.passages p
                        SET work_id = $1,
                            canonical_ref = $2,
                            passage_role = 'original',
                            source_passage_id = NULL,
                            source_metadata = COALESCE(p.source_metadata, '{}'::jsonb) || $3::jsonb,
                            notes = COALESCE(p.notes || E'\n', '') || $4
                        FROM free_will.passage_citations pc
                        WHERE pc.passage_id = p.passage_id
                          AND pc.kg_node_id = $5
                        """,
                        eusebius_work_id,
                        f"PE {book_num}",
                        json.dumps({"repaired_by": CREATED_BY, "work_corrected_to": WORK_EUSEBIUS}),
                        f"{CREATED_BY}: corrected stale Basil/Hexaemeron clone to Eusebius Praeparatio Evangelica.",
                        eusebius_book_id(book_num),
                    )).split()[-1]
                )

        for book_num, roman in ROMAN.items():
            actual_passage_id = await conn.fetchval(
                """
                SELECT pc.passage_id
                FROM free_will.passage_citations pc
                JOIN free_will.passages p ON p.passage_id = pc.passage_id
                WHERE pc.kg_node_id = $1
                  AND p.text_content NOT LIKE 'Stub pour la Préparation évangélique%'
                ORDER BY p.created_at NULLS LAST, pc.passage_id
                LIMIT 1
                """,
                eusebius_book_id(book_num),
            )
            if actual_passage_id is None:
                continue
            counts["db_stub_derived_citations_moved"] += int(
                (await conn.execute(
                    """
                    UPDATE free_will.passage_citations pc
                    SET passage_id = $1
                    FROM free_will.passages p
                    WHERE pc.passage_id = p.passage_id
                      AND p.text_content LIKE 'Stub pour la Préparation évangélique%'
                      AND p.canonical_ref LIKE $2
                    """,
                    actual_passage_id,
                    f"%livre {roman}%",
                )).split()[-1]
            )

        counts["db_stub_passages_deleted"] = int(
            (await conn.execute(
                """
                DELETE FROM free_will.passages p
                WHERE p.text_content LIKE 'Stub pour la Préparation évangélique%'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM free_will.passage_citations pc
                      WHERE pc.passage_id = p.passage_id
                  )
                """,
            )).split()[-1]
        )
        counts["db_empty_legacy_works_deleted"] = int(
            (await conn.execute(
                """
                DELETE FROM free_will.ancient_works aw
                WHERE aw.kg_work_id = $1
                  AND aw.author <> 'Eusebius of Caesarea'
                  AND NOT EXISTS (
                      SELECT 1 FROM free_will.passages p WHERE p.work_id = aw.work_id
                  )
                """,
                WORK_EUSEBIUS,
            )).split()[-1]
        )

        counts["db_removed_stale_nodes"] = int(
            (await conn.execute(
                "DELETE FROM free_will.kg_nodes WHERE node_id = ANY($1::text[])",
                sorted(stale_node_ids),
            )).split()[-1]
        )

        counts["db_has_translation_inserted"] = int(
            (await conn.execute(
                """
                INSERT INTO free_will.kg_edges (
                    edge_id, source_id, target_id, relation, weight, metadata
                )
                SELECT
                    gen_random_uuid(),
                    te.target_id,
                    te.source_id,
                    'has_translation',
                    1.0,
                    $1::jsonb
                FROM free_will.kg_edges te
                WHERE te.relation = 'translation_of'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM free_will.kg_edges inv
                      WHERE inv.relation = 'has_translation'
                        AND inv.source_id = te.target_id
                        AND inv.target_id = te.source_id
                  )
                """,
                json.dumps(
                    {
                        "created_by": CREATED_BY,
                        "auto_generated": True,
                        "inverse_of_relation": "translation_of",
                        "repair_scope": "translation_inverse",
                    }
                ),
            )).split()[-1]
        )

        counts["db_translation_passage_roles_backfilled"] = int(
            (await conn.execute(
                """
                WITH translation_edges AS (
                    SELECT source_id AS translation_node_id, target_id AS source_node_id
                    FROM free_will.kg_edges
                    WHERE relation = 'translation_of'
                ),
                translation_passages AS (
                    SELECT te.translation_node_id, te.source_node_id, MIN(pc.passage_id::text)::uuid AS translation_passage_id
                    FROM translation_edges te
                    JOIN free_will.passage_citations pc ON pc.kg_node_id = te.translation_node_id
                    GROUP BY te.translation_node_id, te.source_node_id
                ),
                source_passages AS (
                    SELECT te.translation_node_id, MIN(pc.passage_id::text)::uuid AS source_passage_id
                    FROM translation_edges te
                    JOIN free_will.passage_citations pc ON pc.kg_node_id = te.source_node_id
                    GROUP BY te.translation_node_id
                )
                UPDATE free_will.passages p
                SET passage_role = 'translation',
                    source_passage_id = sp.source_passage_id,
                    source_metadata = COALESCE(p.source_metadata, '{}'::jsonb)
                        || jsonb_build_object(
                            'repaired_by', $1::text,
                            'kg_translation_node_id', tp.translation_node_id,
                            'kg_source_node_id', tp.source_node_id
                        )
                FROM translation_passages tp
                JOIN source_passages sp ON sp.translation_node_id = tp.translation_node_id
                WHERE p.passage_id = tp.translation_passage_id
                  AND sp.source_passage_id IS NOT NULL
                """,
                CREATED_BY,
            )).split()[-1]
        )

        counts["db_eusebius_edge_duplicates_removed"] = int(
            (await conn.execute(
                """
                WITH ranked AS (
                    SELECT
                        edge_id,
                        row_number() OVER (
                            PARTITION BY source_id, target_id, relation
                            ORDER BY created_at NULLS LAST, edge_id
                        ) AS rn
                    FROM free_will.kg_edges
                    WHERE relation IN ('part_of', 'authored_by')
                      AND source_id = ANY($1::text[])
                )
                DELETE FROM free_will.kg_edges e
                USING ranked r
                WHERE e.edge_id = r.edge_id
                  AND r.rn > 1
                """,
                eusebius_books,
            )).split()[-1]
        )

        await conn.execute(
            """
            UPDATE free_will.ancient_works aw
            SET total_divisions = stats.total_passages,
                total_words = stats.total_words,
                total_chars = stats.total_chars,
                updated_at = now()
            FROM (
                SELECT
                    work_id,
                    COUNT(*)::INTEGER AS total_passages,
                    COALESCE(SUM(word_count), 0)::INTEGER AS total_words,
                    COALESCE(SUM(char_length), 0)::INTEGER AS total_chars
                FROM free_will.passages
                GROUP BY work_id
            ) stats
            WHERE aw.work_id = stats.work_id
            """
        )

    return counts


def print_counts(title: str, counter: Counter[str] | dict[str, Any]) -> None:
    print(title)
    for key, value in sorted(counter.items()):
        print(f"  {key}: {value}")


def collect_db_nodes_to_upsert(nodes_path: Path, result: RepairResult) -> list[dict[str, Any]]:
    wanted = {eusebius_book_id(n) for n in range(1, 16)}
    wanted.update(SYNTHESIS_RENAMES.values())
    wanted.update(result.node_updates)

    out: dict[str, dict[str, Any]] = {}
    with nodes_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            node = json.loads(line)
            nid = node_id(node)
            md = parse_metadata(node.get("metadata"))
            if (
                nid in wanted
                or (
                    nid.startswith("passage_origen_")
                    and md.get("metadata_repaired_by") == CREATED_BY
                )
            ):
                out[nid] = node
    return list(out.values())


async def run(args: argparse.Namespace) -> int:
    node_rows, edge_rows, result = compute_repairs(args.nodes, args.edges)
    print_counts("Local planned repairs:", result.counters)
    print(f"  removed_nodes: {len(result.removed_nodes)}")
    print(f"  node_updates: {len(result.node_updates)}")
    print(f"  edge_updates: {len(result.edge_updates)}")
    print(f"  skipped_edges: {len(result.skipped_edge_indexes)}")
    print(f"  appended_edges: {len(result.appended_edges)}")

    if not args.apply and not args.apply_db:
        print("DRY RUN - no writes. Use --apply and/or --apply-db.")
        return 0

    if args.apply:
        write_nodes(args.nodes, node_rows, result)
        write_edges(args.edges, edge_rows, result)
        stats = update_stats(args.nodes, args.edges, args.stats)
        print(f"Wrote {args.nodes}")
        print(f"Wrote {args.edges}")
        print(f"Wrote {args.stats}")
        print_counts("Updated local stats:", {"total_nodes": stats["total_nodes"], "total_edges": stats["total_edges"]})

    if args.apply_db:
        db_url = args.db_url or os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL") or _common.dsn()
        nodes_to_upsert = collect_db_nodes_to_upsert(args.nodes, result)
        conn = await asyncpg.connect(db_url, statement_cache_size=0)
        try:
            counts = await apply_db_repairs(conn, result, nodes_to_upsert)
        finally:
            await conn.close()
        print_counts("DB repairs applied:", counts)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, default=NODES_PATH)
    parser.add_argument("--edges", type=Path, default=EDGES_PATH)
    parser.add_argument("--stats", type=Path, default=STATS_PATH)
    parser.add_argument("--db-url", help="PostgreSQL DSN. Defaults to env, then repo audit DSN.")
    parser.add_argument("--apply", action="store_true", help="Rewrite local KG files.")
    parser.add_argument("--apply-db", action="store_true", help="Patch live DB tables.")
    return parser.parse_args()


def main() -> int:
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
