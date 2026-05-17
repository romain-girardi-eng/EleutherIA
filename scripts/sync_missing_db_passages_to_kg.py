#!/usr/bin/env python3
"""Sync DB-covered source passages that are missing from the checked-in KG.

This is intentionally narrower than a full KG bootstrap:

- reads the live ``free_will.ancient_works`` / ``passages`` corpus
- reads ``data/quality/ancient_source_backlog.json`` for source-gap targets
- appends missing work shells, passage nodes, ``part_of`` edges, and
  ``authored_by`` edges to ``data/kg/{nodes,edges}.jsonl``

Existing passage nodes are reused when their ``metadata.db_passage_id`` already
matches a DB passage. In that case the script only adds missing structural
edges. It does not delete or rewrite existing nodes/edges.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from database.scripts.philological_audit import _common


KG_ROOT = REPO_ROOT / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"
STATS_PATH = KG_ROOT / "stats.json"
BACKLOG_PATH = REPO_ROOT / "data" / "quality" / "ancient_source_backlog.json"

CREATED_BY = "sync_missing_db_passages_to_kg_2026_05_17"

AUTHOR_PERSON_IDS = {
    "Aristotle": "person_aristotle_384_322bce_c2d4f6a8",
    "Basil the Great": "person_basil_great_d379",
    "Calcidius": "person_calcidius_4c_ce",
    "Clement of Alexandria": "person_clement_alexandria",
    "Epicurus": "person_epicurus_341_270bce_j0k1l2m3",
    "Plato": "person_plato_428_348bce_a1b2c3d4",
    "Plutarch": "person_plutarch_45_120ce_b9c2a8f3",
    "Seneca": "person_seneca_4bce_65ce_a1b2c3d4",
    "Tertullian": "person_tertullian_d220",
}

PREFERRED_WORK_IDS_BY_LABEL = {
    "Aristotle, De Anima": "work_aristotle_de_anima",
    "Aristotle, Eudemian Ethics": "work_aristotle_eudemian_ethics",
    "Aristotle, Magna Moralia": "work_aristotle_magna_moralia",
    "Aristotle, Physics": "work_aristotle_physics",
    "Basil, Hexaemeron": "work_basil_hexaemeron",
    "Calcidius, In Timaeum": "work_calcidius_in_timaeum",
    "Clement of Alexandria, Protrepticus": "work_clement_protrepticus",
    "Epicurus, Letters and Fragments": "work_epicurus_letters_fragments",
    "Plato, Apology": "work_plato_apology",
    "Plutarch, De Communibus Notitiis adversus Stoicos": "work_plutarch_de_communibus_notitiis",
    "Plutarch, De Stoicorum Repugnantiis": "work_plutarch_stoic_repugnantiis",
    "Seneca, Epistulae Morales": "work_seneca_epistulae_morales",
    "Tertullian, Adversus Marcionem": "work_tertullian_adv_marcionem",
    "Tertullian, De Anima": "work_tertullian_de_anima",
}


@dataclass(frozen=True)
class Candidate:
    label: str
    priority: str
    db_work_id: str
    target_work_id: str
    passage_count: int
    kg_passage_count: int


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")


def parse_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def metadata_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source_id") or edge.get("source") or "")


def edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target_id") or edge.get("target") or "")


def slug(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ἠθικὰ εὐδήμεια", "eudemian_ethics")
    text = text.replace("ἀπολογία σωκράτους", "apology")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def suffix_for_passage(row: asyncpg.Record) -> str:
    parts = [
        str(row.get("canonical_ref") or ""),
        str(row.get("book") or ""),
        str(row.get("chapter") or ""),
        str(row.get("section") or ""),
    ]
    for part in parts:
        out = slug(part)
        if out:
            return out[:80]
    seq = row.get("sequence_number")
    if seq is not None:
        return f"seq_{seq}"
    return str(row["passage_id"]).replace("-", "")[:12]


def label_for_work(row: asyncpg.Record) -> str:
    author = str(row.get("author") or "").strip()
    title = str(row.get("title") or "").strip()
    if not author:
        return title
    if title.lower().startswith(author.lower()):
        return title
    return f"{author}, {title}"


def build_work_node(row: asyncpg.Record, target_work_id: str, now: str) -> dict[str, Any]:
    metadata = {
        "author": row.get("author"),
        "auto_generated": True,
        "canonical_id": row.get("canonical_id"),
        "created_by": CREATED_BY,
        "db_work_id": str(row["work_id"]),
        "kg_work_id_original": row.get("kg_work_id"),
        "language": row.get("language"),
        "source_table": "free_will.ancient_works",
        "title": row.get("title"),
    }
    if row.get("cts_urn"):
        metadata["cts_urn"] = row.get("cts_urn")
    return {
        "id": target_work_id,
        "node_id": target_work_id,
        "type": "work",
        "label": label_for_work(row),
        "description": (
            f"{label_for_work(row)}. Work shell created from the live corpus "
            "so DB passages can be represented in the KG at passage level."
        ),
        "alternative_names": "[]",
        "period": row.get("period"),
        "role": None,
        "school": row.get("school"),
        "metadata": metadata_json(metadata),
        "created_at": now,
        "updated_at": now,
    }


def build_passage_node(
    row: asyncpg.Record,
    work: asyncpg.Record,
    passage_node_id: str,
    now: str,
) -> dict[str, Any]:
    canonical_ref = str(row.get("canonical_ref") or "")
    label = f"{work['author']}, {work['title']}, {canonical_ref}".strip().strip(",")
    if len(label) > 220:
        label = label[:217] + "..."
    metadata = {
        "author": work.get("author"),
        "auto_generated": True,
        "canonical_ref": canonical_ref,
        "created_by": CREATED_BY,
        "db_passage_id": str(row["passage_id"]),
        "db_work_id": str(work["work_id"]),
        "language": work.get("language"),
        "passage_role": "original",
        "source_table": "free_will.passages",
        "work_canonical_id": work.get("canonical_id"),
        "work_title": work.get("title"),
    }
    for key in ("book", "chapter", "section", "sequence_number", "char_length", "word_count", "cts_urn"):
        value = row.get(key)
        if value is not None:
            metadata[key] = value
    if work.get("school"):
        metadata["school"] = work.get("school")
    return {
        "id": passage_node_id,
        "node_id": passage_node_id,
        "type": "passage",
        "label": label,
        "description": row.get("text_content") or "",
        "alternative_names": "[]",
        "period": work.get("period"),
        "role": None,
        "school": work.get("school"),
        "metadata": metadata_json(metadata),
        "created_at": now,
        "updated_at": now,
    }


def build_edge(source: str, target: str, relation: str, now: str, metadata: dict[str, Any]) -> dict[str, Any]:
    metadata = {"created_by": CREATED_BY, **metadata}
    return {
        "edge_id": str(uuid4()),
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "relation": relation,
        "weight": 1.0,
        "metadata": metadata_json(metadata),
        "created_at": now,
    }


def choose_target_work_id(entry: dict[str, Any], known_node_ids: set[str]) -> str | None:
    preferred = PREFERRED_WORK_IDS_BY_LABEL.get(str(entry.get("label") or ""))
    if preferred:
        return preferred
    work_node = entry.get("work_node_id")
    if isinstance(work_node, str) and work_node:
        return work_node
    if isinstance(work_node, list):
        for value in work_node:
            if isinstance(value, str) and value in known_node_ids:
                return value
    return None


def iter_db_work_ids(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def load_candidates(
    path: Path,
    known_node_ids: set[str],
    include_partial: bool,
    priorities: set[str],
    labels: set[str],
) -> list[Candidate]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[Candidate] = []
    for entry in data.get("entries", []):
        label = str(entry.get("label") or "")
        priority = str(entry.get("priority") or "")
        passage_count = int(entry.get("passage_count") or 0)
        kg_passage_count = int(entry.get("kg_passage_count") or 0)
        if labels and label not in labels:
            continue
        if priorities and priority not in priorities:
            continue
        if passage_count <= 0:
            continue
        if include_partial:
            if passage_count <= kg_passage_count:
                continue
        elif kg_passage_count != 0:
            continue
        target_work_id = choose_target_work_id(entry, known_node_ids)
        if not target_work_id:
            target_work_id = "work_" + slug(label)
        for db_work_id in iter_db_work_ids(entry.get("db_work_id")):
            out.append(
                Candidate(
                    label=label,
                    priority=priority,
                    db_work_id=db_work_id,
                    target_work_id=target_work_id,
                    passage_count=passage_count,
                    kg_passage_count=kg_passage_count,
                )
            )
    return out


async def fetch_work(conn: asyncpg.Connection, work_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT
            work_id::text,
            kg_work_id,
            canonical_id,
            title,
            author,
            language,
            period,
            school,
            cts_urn
        FROM free_will.ancient_works
        WHERE work_id = $1::uuid
        """,
        work_id,
    )


async def fetch_passages(conn: asyncpg.Connection, work_id: str) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT
            passage_id::text,
            canonical_ref,
            cts_urn,
            book,
            chapter,
            section,
            sequence_number,
            text_content,
            char_length,
            word_count
        FROM free_will.passages
        WHERE work_id = $1::uuid
        ORDER BY sequence_number NULLS LAST, canonical_ref NULLS LAST, passage_id
        """,
        work_id,
    )


def row_created_by(row: dict[str, Any]) -> str | None:
    return parse_metadata(row.get("metadata")).get("created_by")


def shape_node_for_db(node: dict[str, Any]) -> tuple[str, str, str, str | None, str | None, str, str]:
    metadata = parse_metadata(node.get("metadata"))
    alt_names = node.get("alternative_names") or []
    if isinstance(alt_names, str):
        try:
            alt_names = json.loads(alt_names)
        except json.JSONDecodeError:
            alt_names = []
    return (
        node_id(node),
        str(node.get("label") or node_id(node)),
        str(node.get("type") or "unknown"),
        node.get("description"),
        node.get("period"),
        json.dumps(alt_names, ensure_ascii=False),
        json.dumps(metadata, ensure_ascii=False),
    )


def shape_edge_for_db(edge: dict[str, Any]) -> tuple[str, str, str, float, str]:
    metadata = parse_metadata(edge.get("metadata"))
    try:
        weight = float(edge.get("weight") or edge.get("confidence") or 1.0)
    except (TypeError, ValueError):
        weight = 1.0
    return (
        edge_source(edge),
        edge_target(edge),
        str(edge.get("relation") or ""),
        weight,
        json.dumps(metadata, ensure_ascii=False),
    )


async def apply_created_rows_to_db(db_url: str, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
    selected_nodes = [n for n in nodes if row_created_by(n) == CREATED_BY]
    selected_edges = [e for e in edges if row_created_by(e) == CREATED_BY]
    counts = {
        "nodes_selected": len(selected_nodes),
        "edges_selected": len(selected_edges),
        "nodes_inserted_or_updated": 0,
        "edges_inserted": 0,
        "edges_skipped_existing": 0,
    }
    if not selected_nodes and not selected_edges:
        return counts

    conn = await asyncpg.connect(db_url, statement_cache_size=0)
    try:
        async with conn.transaction():
            for node in selected_nodes:
                await conn.execute(
                    """
                    INSERT INTO free_will.kg_nodes
                        (node_id, label, type, description, period, alternative_names, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
                    ON CONFLICT (node_id) DO UPDATE SET
                        label = EXCLUDED.label,
                        type = EXCLUDED.type,
                        description = COALESCE(EXCLUDED.description, free_will.kg_nodes.description),
                        period = COALESCE(EXCLUDED.period, free_will.kg_nodes.period),
                        alternative_names = EXCLUDED.alternative_names,
                        metadata = free_will.kg_nodes.metadata || EXCLUDED.metadata,
                        updated_at = now()
                    """,
                    *shape_node_for_db(node),
                )
                counts["nodes_inserted_or_updated"] += 1

            for edge in selected_edges:
                result = await conn.fetchval(
                    """
                    INSERT INTO free_will.kg_edges
                        (source_id, target_id, relation, weight, metadata)
                    SELECT $1::varchar, $2::varchar, $3::varchar, $4::double precision, $5::jsonb
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM free_will.kg_edges e
                        WHERE e.source_id = $1::varchar
                          AND e.target_id = $2::varchar
                          AND e.relation = $3::varchar
                    )
                    RETURNING 1
                    """,
                    *shape_edge_for_db(edge),
                )
                if result == 1:
                    counts["edges_inserted"] += 1
                else:
                    counts["edges_skipped_existing"] += 1
    finally:
        await conn.close()
    return counts


def rebuild_stats(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], now: str) -> dict[str, Any]:
    node_types = Counter(str(n.get("type") or "unknown") for n in nodes)
    edge_relations = Counter(str(e.get("relation") or "unknown") for e in edges)
    return {
        "generated_at": now.replace(" ", "T"),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": dict(sorted(node_types.items())),
        "edge_relations": dict(sorted(edge_relations.items())),
    }


async def run(args: argparse.Namespace) -> int:
    nodes = load_jsonl(args.nodes)
    edges = load_jsonl(args.edges)

    known_node_ids = {node_id(n) for n in nodes}
    existing_edges = {
        (edge_source(e), edge_target(e), str(e.get("relation") or ""))
        for e in edges
    }
    passage_part_of_targets: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.get("relation") == "part_of":
            passage_part_of_targets[edge_source(edge)].add(edge_target(edge))

    db_passage_to_node: dict[str, str] = {}
    canonical_to_node: dict[tuple[str, str], str] = {}
    for node in nodes:
        if node.get("type") != "passage":
            continue
        md = parse_metadata(node.get("metadata"))
        nid = node_id(node)
        db_passage_id = md.get("db_passage_id")
        if db_passage_id:
            db_passage_to_node[str(db_passage_id)] = nid
        work_canonical_id = md.get("work_canonical_id")
        canonical_ref = md.get("canonical_ref")
        if work_canonical_id and canonical_ref:
            canonical_to_node[(str(work_canonical_id), str(canonical_ref))] = nid

    priorities = set(args.priority or [])
    labels = set(args.label or [])
    candidates = load_candidates(
        args.backlog,
        known_node_ids,
        include_partial=args.include_partial,
        priorities=priorities,
        labels=labels,
    )
    if not candidates:
        print("No candidates selected.")
        return 0

    db_url = args.db_url or os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL") or _common.dsn()
    conn = await asyncpg.connect(db_url, statement_cache_size=0)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
    new_nodes: list[dict[str, Any]] = []
    new_edges: list[dict[str, Any]] = []
    added_by_label: Counter[str] = Counter()
    linked_existing_by_label: Counter[str] = Counter()
    skipped_existing_by_label: Counter[str] = Counter()
    created_work_nodes: set[str] = set()
    warnings: list[str] = []

    try:
        for candidate in candidates:
            work = await fetch_work(conn, candidate.db_work_id)
            if not work:
                warnings.append(f"missing DB work {candidate.db_work_id} for {candidate.label}")
                continue

            if candidate.target_work_id not in known_node_ids:
                work_node = build_work_node(work, candidate.target_work_id, now)
                new_nodes.append(work_node)
                nodes.append(work_node)
                known_node_ids.add(candidate.target_work_id)
                created_work_nodes.add(candidate.target_work_id)

            person_id = AUTHOR_PERSON_IDS.get(str(work["author"]))
            if person_id not in known_node_ids:
                person_id = None

            passages = await fetch_passages(conn, candidate.db_work_id)
            prefix = "passage_" + candidate.target_work_id.removeprefix("work_")
            seen_new_ids: set[str] = set()

            for passage in passages:
                passage_id = str(passage["passage_id"])
                existing_node_id = db_passage_to_node.get(passage_id)
                if not existing_node_id:
                    key = (str(work["canonical_id"]), str(passage.get("canonical_ref") or ""))
                    existing_node_id = canonical_to_node.get(key)

                if existing_node_id:
                    node_for_edges = existing_node_id
                    skipped_existing_by_label[candidate.label] += 1
                else:
                    suffix = suffix_for_passage(passage)
                    base_id = f"{prefix}_{suffix}"
                    node_for_edges = base_id
                    if node_for_edges in known_node_ids or node_for_edges in seen_new_ids:
                        seq = passage.get("sequence_number")
                        extra = f"s{seq}" if seq is not None else passage_id.replace("-", "")[:8]
                        node_for_edges = f"{base_id}_{extra}"
                    if node_for_edges in known_node_ids or node_for_edges in seen_new_ids:
                        node_for_edges = f"{base_id}_{passage_id.replace('-', '')[:12]}"

                    passage_node = build_passage_node(passage, work, node_for_edges, now)
                    new_nodes.append(passage_node)
                    nodes.append(passage_node)
                    known_node_ids.add(node_for_edges)
                    seen_new_ids.add(node_for_edges)
                    db_passage_to_node[passage_id] = node_for_edges
                    canonical_ref = passage.get("canonical_ref")
                    if canonical_ref:
                        canonical_to_node[(str(work["canonical_id"]), str(canonical_ref))] = node_for_edges
                    added_by_label[candidate.label] += 1

                part_of_key = (node_for_edges, candidate.target_work_id, "part_of")
                if part_of_key not in existing_edges:
                    new_edges.append(
                        build_edge(
                            node_for_edges,
                            candidate.target_work_id,
                            "part_of",
                            now,
                            {
                                "auto_generated": True,
                                "db_passage_id": passage_id,
                                "db_work_id": str(work["work_id"]),
                                "relation_source": "db_passage_reconciliation",
                            },
                        )
                    )
                    existing_edges.add(part_of_key)
                    passage_part_of_targets[node_for_edges].add(candidate.target_work_id)
                    if existing_node_id:
                        linked_existing_by_label[candidate.label] += 1

                if person_id:
                    authored_key = (node_for_edges, person_id, "authored_by")
                    if authored_key not in existing_edges:
                        new_edges.append(
                            build_edge(
                                node_for_edges,
                                person_id,
                                "authored_by",
                                now,
                                {
                                    "auto_generated": True,
                                    "db_passage_id": passage_id,
                                    "db_work_id": str(work["work_id"]),
                                    "propagated_from_work": True,
                                },
                            )
                        )
                        existing_edges.add(authored_key)
    finally:
        await conn.close()

    print("Selected candidates:", len(candidates))
    print("New work nodes:", len(created_work_nodes))
    print("New passage nodes:", sum(added_by_label.values()))
    print("Existing passage nodes linked:", sum(linked_existing_by_label.values()))
    print("New edges:", len(new_edges))
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    for label in sorted(set(added_by_label) | set(linked_existing_by_label) | set(skipped_existing_by_label)):
        print(
            f"  {label}: "
            f"new_passages={added_by_label[label]} "
            f"existing_seen={skipped_existing_by_label[label]} "
            f"new_links_for_existing={linked_existing_by_label[label]}"
        )

    if args.dry_run and not args.apply_db:
        print("DRY RUN - no files written. Re-run with --apply to append.")
        return 0

    all_edges = edges + new_edges
    if args.apply:
        append_jsonl(args.nodes, new_nodes)
        append_jsonl(args.edges, new_edges)
        if args.update_stats:
            stats = rebuild_stats(nodes, all_edges, now)
            args.stats.write_text(json.dumps(stats, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Wrote {len(new_nodes)} nodes to {args.nodes}")
        print(f"Wrote {len(new_edges)} edges to {args.edges}")
        if args.update_stats:
            print(f"Updated {args.stats}")

    if args.apply_db:
        db_counts = await apply_created_rows_to_db(db_url, nodes, all_edges)
        print("DB apply:")
        for key, value in db_counts.items():
            print(f"  {key}: {value}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", type=Path, default=BACKLOG_PATH)
    parser.add_argument("--nodes", type=Path, default=NODES_PATH)
    parser.add_argument("--edges", type=Path, default=EDGES_PATH)
    parser.add_argument("--stats", type=Path, default=STATS_PATH)
    parser.add_argument("--db-url", help="PostgreSQL DSN. Defaults to env, then repo audit DSN.")
    parser.add_argument(
        "--include-partial",
        action="store_true",
        help="Also reconcile backlog rows where DB passage count is greater than KG count. Default only rows with KG count 0.",
    )
    parser.add_argument(
        "--priority",
        action="append",
        choices=("P0", "P1", "P2", "P3"),
        help="Restrict to a priority. May be repeated.",
    )
    parser.add_argument(
        "--label",
        action="append",
        help="Restrict to an exact backlog label. May be repeated.",
    )
    parser.add_argument("--apply", action="store_true", help="Append changes to KG JSONL files.")
    parser.add_argument("--apply-db", action="store_true", help="Upsert rows created by this script into free_will.kg_nodes/kg_edges.")
    parser.add_argument(
        "--no-update-stats",
        dest="update_stats",
        action="store_false",
        help="Do not rewrite data/kg/stats.json.",
    )
    parser.set_defaults(update_stats=True)
    args = parser.parse_args()
    args.dry_run = not args.apply
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
