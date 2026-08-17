"""Bootstrap a rebuilt Supabase/PostgreSQL database from the KG snapshot.

This script is intentionally idempotent. It can:
- apply the canonical schema and Supabase RPC compatibility SQL;
- import recovered KG nodes/edges from data/kg/*.jsonl;
- derive ancient_works, passages, and passage_citations from passage nodes.

Use --replace-data only when rebuilding a fresh/restored project and you want the
current KG/text slice to replace existing KG-derived rows.

Security posture:
- run from a trusted local shell/CI job only;
- prefer a direct or session-pooler maintenance DSN;
- never commit SUPABASE_DATABASE_URL or use the service-role API key here;
- runtime backends should use DATABASE_URL with pgbouncer and least privilege.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_FILES = (
    REPO_ROOT / "database" / "schema" / "schema.sql",
    REPO_ROOT / "database" / "schema" / "work_tree_indices.sql",
    REPO_ROOT / "database" / "schema" / "supabase_public_api.sql",
    REPO_ROOT / "database" / "schema" / "supabase_functions.sql",
    REPO_ROOT / "database" / "migrations" / "20260514_01_supabase_rebuild_support.sql",
)

UUID_NAMESPACE = uuid.UUID("d46efc36-9f19-45fb-9b8d-8a4d3e4d2728")
VALID_LANGUAGES = {"grc", "lat", "eng", "hbo", "ara"}
LANGUAGE_ALIASES = {
    "el": "grc",
    "en": "eng",
    "english": "eng",
    "greek": "grc",
    "gr": "grc",
    "he": "hbo",
    "hebrew": "hbo",
    "la": "lat",
    "latin": "lat",
}
PASSAGE_TYPES = {"passage", "quote"}
PASSAGE_TO_NODE_RELATIONS = {
    "discusses",
    "evidences",
    "exemplifies",
    "grounds",
    "source_for",
}
NODE_TO_PASSAGE_RELATIONS = {
    "discussed_in",
    "evidenced_by",
    "grounded_in",
    "source",
    "source_text",
    "supported_by",
}


@dataclass(frozen=True)
class SnapshotData:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@dataclass(frozen=True)
class ImportPayload:
    kg_nodes: list[tuple[Any, ...]]
    kg_edges: list[tuple[Any, ...]]
    ancient_works: list[tuple[Any, ...]]
    passages: list[tuple[Any, ...]]
    passage_citations: list[tuple[Any, ...]]


@dataclass(frozen=True)
class ImportTables:
    """Qualified table names used by the snapshot importer.

    Keeping the target names injectable lets the staged deploy reuse this
    loader without duplicating its transformation or insert logic.
    """

    kg_nodes: str = "free_will.kg_nodes"
    kg_edges: str = "free_will.kg_edges"
    ancient_works: str = "free_will.ancient_works"
    passages: str = "free_will.passages"
    passage_citations: str = "free_will.passage_citations"
    passage_relationships: str = "free_will.passage_relationships"

    def __post_init__(self) -> None:
        for value in self.__dict__.values():
            if not re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", value
            ):
                raise ValueError(f"unsafe qualified table name: {value!r}")

    @classmethod
    def with_suffix(cls, schema: str, suffix: str) -> ImportTables:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise ValueError(f"unsafe schema name: {schema!r}")
        if not re.fullmatch(r"__[A-Za-z0-9_]+", suffix):
            raise ValueError(f"unsafe table suffix: {suffix!r}")

        def table(name: str) -> str:
            return f"{schema}.{name}{suffix}"

        return cls(
            kg_nodes=table("kg_nodes"),
            kg_edges=table("kg_edges"),
            ancient_works=table("ancient_works"),
            passages=table("passages"),
            passage_citations=table("passage_citations"),
            passage_relationships=table("passage_relationships"),
        )


def load_snapshot(snapshot_dir: Path) -> SnapshotData:
    nodes_path = snapshot_dir / "nodes.jsonl"
    edges_path = snapshot_dir / "edges.jsonl"
    if not nodes_path.exists() or not edges_path.exists():
        raise FileNotFoundError(
            f"KG snapshot missing: expected {nodes_path} and {edges_path}"
        )
    return SnapshotData(
        nodes=list(_read_jsonl(nodes_path)),
        edges=list(_read_jsonl(edges_path)),
    )


def build_import_payload(snapshot: SnapshotData) -> ImportPayload:
    node_lookup = {
        str(row.get("id") or row.get("node_id")): row
        for row in snapshot.nodes
        if row.get("id") or row.get("node_id")
    }
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in snapshot.edges:
        source = str(edge.get("source") or edge.get("source_id") or "")
        target = str(edge.get("target") or edge.get("target_id") or "")
        if source and target:
            outgoing[source].append(edge)
            incoming[target].append(edge)

    kg_nodes = [_kg_node_record(row) for row in snapshot.nodes]
    kg_nodes = [row for row in kg_nodes if row[0]]

    node_ids = {row[0] for row in kg_nodes}
    kg_edges = [
        _kg_edge_record(edge)
        for edge in snapshot.edges
        if str(edge.get("source") or edge.get("source_id") or "") in node_ids
        and str(edge.get("target") or edge.get("target_id") or "") in node_ids
    ]

    passage_sources = _collect_passage_sources(node_lookup, outgoing)
    base_language_counts = Counter(source["base_key"] for source in passage_sources)

    work_map: dict[tuple[str, str], dict[str, Any]] = {}
    passage_rows: list[tuple[Any, ...]] = []
    sequence_by_work: Counter[uuid.UUID] = Counter()
    passage_id_by_node: dict[str, uuid.UUID] = {}

    for source in passage_sources:
        canonical_id = _canonical_work_id(
            source["base_key"],
            source["language"],
            base_language_counts[source["base_key"]],
        )
        work_id = deterministic_uuid("work", canonical_id)
        work_key = (canonical_id, source["language"])
        if work_key not in work_map:
            work_map[work_key] = {
                "work_id": work_id,
                "kg_work_id": source["kg_work_id"],
                "canonical_id": canonical_id,
                "title": source["work_title"],
                "author": source["author"],
                "language": source["language"],
                "period": source["period"],
                "school": source["school"],
                "metadata": source["work_metadata"],
            }

        sequence = source["sequence_number"]
        if sequence is None:
            sequence_by_work[work_id] += 1
            sequence = sequence_by_work[work_id]
        else:
            sequence_by_work[work_id] = max(sequence_by_work[work_id], sequence)

        passage_id = source["passage_id"]
        passage_id_by_node[source["node_id"]] = passage_id
        passage_rows.append(
            (
                passage_id,
                work_id,
                source["canonical_ref"],
                source["cts_urn"],
                source["book"],
                source["chapter"],
                source["section"],
                max(0, int(sequence)),
                source["text_content"],
                source["char_length"],
                source["word_count"],
                json_dumps(source["citation_hierarchy"]),
            )
        )

    citations = _derive_citations(
        node_lookup=node_lookup,
        edges=snapshot.edges,
        passage_id_by_node=passage_id_by_node,
    )

    return ImportPayload(
        kg_nodes=kg_nodes,
        kg_edges=kg_edges,
        ancient_works=[
            (
                row["work_id"],
                row["kg_work_id"],
                row["canonical_id"],
                row["title"],
                row["author"],
                row["language"],
                row["period"],
                row["school"],
                json_dumps(row["metadata"]),
            )
            for row in sorted(work_map.values(), key=lambda item: item["canonical_id"])
        ],
        passages=sorted(
            passage_rows, key=lambda row: (str(row[1]), row[7], str(row[0]))
        ),
        passage_citations=sorted(
            citations, key=lambda row: (str(row[0]), row[1], row[2])
        ),
    )


async def apply_schema(conn: asyncpg.Connection) -> None:
    for path in DEFAULT_SCHEMA_FILES:
        sql = path.read_text(encoding="utf-8")
        print(f"Applying {path.relative_to(REPO_ROOT)}")
        await conn.execute(sql)


async def import_payload(
    conn: asyncpg.Connection,
    payload: ImportPayload,
    *,
    replace_data: bool,
    batch_size: int,
    tables: ImportTables | None = None,
) -> None:
    target = tables or ImportTables()
    if replace_data:
        print("Replacing KG-derived data")
        await conn.execute(
            f"""
            TRUNCATE
                {target.passage_citations},
                {target.passage_relationships},
                {target.passages},
                {target.ancient_works},
                {target.kg_edges},
                {target.kg_nodes}
            RESTART IDENTITY CASCADE
            """
        )

    await _executemany_batched(
        conn,
        f"""
        INSERT INTO {target.kg_nodes} (
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
        payload.kg_nodes,
        batch_size,
        "kg_nodes",
    )

    await _executemany_batched(
        conn,
        f"""
        INSERT INTO {target.kg_edges} (
            source_id, target_id, relation, weight, metadata
        )
        SELECT $1::varchar, $2::varchar, $3::varchar, $4::double precision, $5::jsonb
        WHERE NOT EXISTS (
            SELECT 1
            FROM {target.kg_edges} e
            WHERE e.source_id = $1::varchar
              AND e.target_id = $2::varchar
              AND e.relation = $3::varchar
              AND e.metadata = $5::jsonb
        )
        """,
        payload.kg_edges,
        batch_size,
        "kg_edges",
    )

    await _executemany_batched(
        conn,
        f"""
        INSERT INTO {target.ancient_works} (
            work_id,
            kg_work_id,
            canonical_id,
            title,
            author,
            language,
            period,
            school,
            source,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'kg_snapshot', $9::jsonb)
        ON CONFLICT (work_id) DO UPDATE SET
            kg_work_id = EXCLUDED.kg_work_id,
            canonical_id = EXCLUDED.canonical_id,
            title = EXCLUDED.title,
            author = EXCLUDED.author,
            language = EXCLUDED.language,
            period = EXCLUDED.period,
            school = EXCLUDED.school,
            source = EXCLUDED.source,
            metadata = EXCLUDED.metadata,
            updated_at = now()
        """,
        payload.ancient_works,
        batch_size,
        "ancient_works",
    )

    await _executemany_batched(
        conn,
        f"""
        INSERT INTO {target.passages} (
            passage_id,
            work_id,
            canonical_ref,
            cts_urn,
            book,
            chapter,
            section,
            sequence_number,
            text_content,
            char_length,
            word_count,
            citation_hierarchy
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
        ON CONFLICT (passage_id) DO UPDATE SET
            work_id = EXCLUDED.work_id,
            canonical_ref = EXCLUDED.canonical_ref,
            cts_urn = EXCLUDED.cts_urn,
            book = EXCLUDED.book,
            chapter = EXCLUDED.chapter,
            section = EXCLUDED.section,
            sequence_number = EXCLUDED.sequence_number,
            text_content = EXCLUDED.text_content,
            char_length = EXCLUDED.char_length,
            word_count = EXCLUDED.word_count,
            citation_hierarchy = EXCLUDED.citation_hierarchy
        """,
        payload.passages,
        batch_size,
        "passages",
    )

    await _executemany_batched(
        conn,
        f"""
        INSERT INTO {target.passage_citations} (
            passage_id, kg_node_id, citation_type, confidence, notes
        )
        SELECT $1, $2, $3, $4, $5
        WHERE NOT EXISTS (
            SELECT 1
            FROM {target.passage_citations} pc
            WHERE pc.passage_id = $1
              AND pc.kg_node_id = $2
              AND COALESCE(pc.citation_type, '') = COALESCE($3, '')
        )
        """,
        payload.passage_citations,
        batch_size,
        "passage_citations",
    )

    await conn.execute(
        f"""
        UPDATE {target.ancient_works} aw
        SET
            total_divisions = stats.total_passages,
            total_words = stats.total_words,
            total_chars = stats.total_chars,
            updated_at = now()
        FROM (
            SELECT
                work_id,
                COUNT(*)::INTEGER AS total_passages,
                COALESCE(SUM(word_count), 0)::INTEGER AS total_words,
                COALESCE(SUM(char_length), 0)::INTEGER AS total_chars
            FROM {target.passages}
            GROUP BY work_id
        ) stats
        WHERE stats.work_id = aw.work_id
        """
    )
    await conn.execute(f"ANALYZE {target.kg_nodes}")
    await conn.execute(f"ANALYZE {target.kg_edges}")
    await conn.execute(f"ANALYZE {target.ancient_works}")
    await conn.execute(f"ANALYZE {target.passages}")
    await conn.execute(f"ANALYZE {target.passage_citations}")


def _kg_node_record(row: dict[str, Any]) -> tuple[Any, ...]:
    metadata = normalize_mapping(row.get("metadata"))
    node_id = str(row.get("id") or row.get("node_id") or "")
    alt_names = row.get("alternative_names")
    return (
        node_id,
        row.get("label") or node_id,
        str(row.get("type") or "unknown").lower(),
        row.get("description"),
        row.get("period") or metadata.get("period"),
        json_dumps(alt_names if alt_names is not None else []),
        json_dumps(metadata),
    )


def _kg_edge_record(row: dict[str, Any]) -> tuple[Any, ...]:
    metadata = normalize_mapping(row.get("metadata"))
    weight = coerce_float(row.get("weight", metadata.get("weight", 1.0)), default=1.0)
    return (
        str(row.get("source") or row.get("source_id") or ""),
        str(row.get("target") or row.get("target_id") or ""),
        str(row.get("relation") or row.get("edge_type") or "related_to"),
        weight,
        json_dumps(metadata),
    )


def _collect_passage_sources(
    node_lookup: dict[str, dict[str, Any]],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for node_id, node in node_lookup.items():
        if str(node.get("type") or "").lower() not in PASSAGE_TYPES:
            continue
        text_content = str(node.get("description") or "").strip()
        if not text_content:
            continue

        metadata = normalize_mapping(node.get("metadata"))
        language = normalize_language(metadata.get("language") or node.get("language"))
        work_node = _linked_work_node(node_id, node_lookup, outgoing)
        author_node = _linked_author_node(node_id, node_lookup, outgoing)

        work_title = (
            metadata.get("work_title")
            or metadata.get("source_work")
            or (work_node or {}).get("label")
            or _title_from_label(str(node.get("label") or node_id))
            or "Recovered KG Snapshot"
        )
        author = (
            metadata.get("author")
            or (author_node or {}).get("label")
            or normalize_author_from_title(work_title)
            or "Unknown"
        )
        base_key = slugify(
            metadata.get("work_canonical_id")
            or metadata.get("work_id")
            or (work_node or {}).get("id")
            or f"{author}_{work_title}"
        )
        canonical_ref = str(
            metadata.get("canonical_ref")
            or metadata.get("section")
            or str(node.get("label") or node_id)
        )
        book, chapter, section = citation_parts(canonical_ref, metadata)
        sequence_number = coerce_int(
            metadata.get("sequence_number")
            or metadata.get("sequence")
            or metadata.get("order")
        )
        if sequence_number is None:
            sequence_number = sequence_from_ref(canonical_ref)

        passage_id = uuid_from_metadata(
            metadata.get("db_passage_id") or metadata.get("passage_id"),
            fallback_key=f"passage:{node_id}",
        )
        sources.append(
            {
                "node_id": node_id,
                "passage_id": passage_id,
                "base_key": base_key or slugify(f"{author}_{work_title}"),
                "kg_work_id": (work_node or {}).get("id"),
                "work_title": str(work_title),
                "author": str(author),
                "language": language,
                "period": node.get("period") or metadata.get("period"),
                "school": node.get("school") or metadata.get("school"),
                "work_metadata": {
                    "source": "kg_snapshot",
                    "work_canonical_id": metadata.get("work_canonical_id"),
                    "source_work": metadata.get("source_work"),
                    "edition": metadata.get("edition"),
                },
                "canonical_ref": str(canonical_ref),
                "cts_urn": metadata.get("cts_urn"),
                "book": book,
                "chapter": chapter,
                "section": section,
                "sequence_number": sequence_number,
                "text_content": text_content,
                "char_length": coerce_int(metadata.get("char_length"))
                or len(text_content),
                "word_count": coerce_int(metadata.get("word_count"))
                or len(text_content.split()),
                "citation_hierarchy": {
                    "book": book,
                    "chapter": chapter,
                    "section": section,
                    "kg_node_id": node_id,
                    "snapshot_metadata": metadata,
                },
            }
        )
    return sources


def _derive_citations(
    *,
    node_lookup: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    passage_id_by_node: dict[str, uuid.UUID],
) -> list[tuple[Any, ...]]:
    seen: set[tuple[uuid.UUID, str, str]] = set()
    records: list[tuple[Any, ...]] = []

    def add(
        passage_node_id: str,
        kg_node_id: str,
        citation_type: str,
        confidence: float,
        note: str,
    ) -> None:
        passage_id = passage_id_by_node.get(passage_node_id)
        if not passage_id or kg_node_id not in node_lookup:
            return
        key = (passage_id, kg_node_id, citation_type)
        if key in seen:
            return
        seen.add(key)
        records.append(
            (
                passage_id,
                kg_node_id,
                citation_type,
                clamp_confidence(confidence),
                note,
            )
        )

    for passage_node_id in passage_id_by_node:
        add(
            passage_node_id,
            passage_node_id,
            "snapshot_passage_node",
            1.0,
            "Recovered from KG snapshot passage node",
        )

    for edge in edges:
        source = str(edge.get("source") or edge.get("source_id") or "")
        target = str(edge.get("target") or edge.get("target_id") or "")
        relation = str(edge.get("relation") or edge.get("edge_type") or "")
        metadata = normalize_mapping(edge.get("metadata"))
        confidence = coerce_float(
            metadata.get(
                "confidence", edge.get("weight", metadata.get("weight", 0.75))
            ),
            default=0.75,
        )

        source_is_passage = source in passage_id_by_node
        target_is_passage = target in passage_id_by_node
        if (
            target_is_passage
            and not source_is_passage
            and relation in NODE_TO_PASSAGE_RELATIONS
        ):
            add(target, source, relation, confidence, "Derived from KG edge")
        elif (
            source_is_passage
            and not target_is_passage
            and relation in PASSAGE_TO_NODE_RELATIONS
        ):
            add(source, target, relation, confidence, "Derived from KG edge")

    return records


def _linked_work_node(
    node_id: str,
    node_lookup: dict[str, dict[str, Any]],
    outgoing: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    for edge in outgoing.get(node_id, []):
        if edge.get("relation") == "part_of":
            target = str(edge.get("target") or edge.get("target_id") or "")
            node = node_lookup.get(target)
            if str((node or {}).get("type") or "").lower() == "work":
                return node
    return None


def _linked_author_node(
    node_id: str,
    node_lookup: dict[str, dict[str, Any]],
    outgoing: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    for edge in outgoing.get(node_id, []):
        if edge.get("relation") == "authored_by":
            target = str(edge.get("target") or edge.get("target_id") or "")
            node = node_lookup.get(target)
            if str((node or {}).get("type") or "").lower() == "person":
                return node
    return None


async def _executemany_batched(
    conn: asyncpg.Connection,
    sql: str,
    records: list[tuple[Any, ...]],
    batch_size: int,
    label: str,
) -> None:
    if not records:
        print(f"{label}: 0 rows")
        return
    for offset in range(0, len(records), batch_size):
        batch = records[offset : offset + batch_size]
        await conn.executemany(sql, batch)
    print(f"{label}: {len(records)} rows")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
            if isinstance(row, dict):
                rows.append(row)
    return rows


def normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def json_dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def normalize_language(value: Any) -> str:
    raw = str(value or "eng").strip().lower()
    normalized = LANGUAGE_ALIASES.get(raw, raw)
    return normalized if normalized in VALID_LANGUAGES else "eng"


def deterministic_uuid(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(UUID_NAMESPACE, f"{kind}:{key}")


def uuid_from_metadata(value: Any, *, fallback_key: str) -> uuid.UUID:
    if value:
        try:
            return uuid.UUID(str(value))
        except ValueError:
            pass
    return deterministic_uuid("snapshot", fallback_key)


def slugify(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_") or "snapshot"


def _canonical_work_id(
    base_key: str, language: str, language_variant_count: int
) -> str:
    base = slugify(base_key)
    if language_variant_count > 1:
        return f"{base}_{language}"
    return base


def _title_from_label(label: str) -> str | None:
    parts = [part.strip() for part in label.split(",") if part.strip()]
    if len(parts) >= 2:
        return parts[-2] if parts[-1].isdigit() else parts[-1]
    return label or None


def normalize_author_from_title(title: str) -> str | None:
    if "," not in title:
        return None
    first = title.split(",", 1)[0].strip()
    return first if first else None


def citation_parts(
    canonical_ref: str,
    metadata: dict[str, Any],
) -> tuple[str | None, str | None, str | None]:
    book = _string_or_none(metadata.get("book"))
    chapter = _string_or_none(metadata.get("chapter"))
    section = _string_or_none(metadata.get("section"))
    if book or chapter or section:
        return book, chapter, section

    numbers = re.findall(r"\d+[a-zA-Z]?", canonical_ref or "")
    if len(numbers) >= 3:
        return numbers[0], numbers[1], numbers[2]
    if len(numbers) == 2:
        return numbers[0], None, numbers[1]
    if len(numbers) == 1:
        return None, None, numbers[0]
    return None, None, None


def sequence_from_ref(canonical_ref: str) -> int | None:
    numbers = re.findall(r"\d+", canonical_ref or "")
    if not numbers:
        return None
    value = 0
    for number in numbers[:4]:
        value = value * 10000 + int(number)
    return value


def coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def coerce_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply Supabase schema and import the recovered KG snapshot."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help=(
            "PostgreSQL maintenance DSN. Defaults to SUPABASE_DATABASE_URL or "
            "DATABASE_URL. Prefer SUPABASE_DATABASE_URL so runtime and bootstrap "
            "credentials stay separate."
        ),
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path(
            os.getenv("ELEUTHERIA_KG_SNAPSHOT_DIR", REPO_ROOT / "data" / "kg")
        ),
        help="Directory containing nodes.jsonl and edges.jsonl.",
    )
    parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Do not apply schema/RPC SQL files.",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Do not import snapshot data.",
    )
    parser.add_argument(
        "--replace-data",
        action="store_true",
        help="TRUNCATE KG-derived tables before importing.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows per executemany batch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build payload and print counts without connecting to PostgreSQL.",
    )
    return parser.parse_args(argv)


async def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.database_url:
        _warn_if_pooler_transaction_url(args.database_url)
    snapshot = load_snapshot(args.snapshot_dir)
    payload = build_import_payload(snapshot)

    print("Recovered snapshot payload")
    print(f"  kg_nodes: {len(payload.kg_nodes)}")
    print(f"  kg_edges: {len(payload.kg_edges)}")
    print(f"  ancient_works: {len(payload.ancient_works)}")
    print(f"  passages: {len(payload.passages)}")
    print(f"  passage_citations: {len(payload.passage_citations)}")

    if args.dry_run:
        return 0
    if not args.database_url:
        raise SystemExit(
            "Missing --database-url, SUPABASE_DATABASE_URL, or DATABASE_URL"
        )

    conn = await asyncpg.connect(
        dsn=args.database_url,
        statement_cache_size=0,
        timeout=30,
        command_timeout=300,
    )
    try:
        if not args.skip_schema:
            await apply_schema(conn)
        if not args.skip_import:
            await import_payload(
                conn,
                payload,
                replace_data=args.replace_data,
                batch_size=max(1, args.batch_size),
            )
        stats = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM free_will.kg_nodes) AS kg_nodes,
                (SELECT COUNT(*) FROM free_will.kg_edges) AS kg_edges,
                (SELECT COUNT(*) FROM free_will.ancient_works) AS ancient_works,
                (SELECT COUNT(*) FROM free_will.passages) AS passages,
                (SELECT COUNT(*) FROM free_will.passage_citations) AS passage_citations
            """
        )
        print("Database counts")
        for key, value in dict(stats).items():
            print(f"  {key}: {value}")
    finally:
        await conn.close()
    return 0


def _warn_if_pooler_transaction_url(database_url: str) -> None:
    lower = database_url.lower()
    if ".pooler.supabase.com:6543" in lower:
        print(
            "Warning: transaction-pooler DSN detected. Supabase recommends direct "
            "or session-pooler connections for migrations/imports; transaction "
            "pooling is best kept for runtime/serverless traffic.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
