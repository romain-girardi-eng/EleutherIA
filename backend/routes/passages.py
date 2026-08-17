"""Single-passage detail endpoint for the doctoral UI.

``GET /api/passages/{passage_id}`` accepts either a passages.passage_id UUID
or — preferred — a KG node_id (``passage_aristotle_eth_nic_3_1_1110a4``).
It returns the original text, the AI/published English translation (if
available), edition + translator provenance, attestation type, and any
fragment-collection references, all in a single round-trip.

The translation is sourced from the companion ``{node_id}_en`` KG node
created by :mod:`database/scripts/create_passage_translations.py` — see
the two-node architecture documented there.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, cast

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.dependencies import get_db
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["passages"])


def _is_uuid_shape(value: str) -> bool:
    return len(value) == 36 and value.count("-") == 4


async def _fetch_kg_node(db: DatabaseService, node_id: str) -> dict[str, Any] | None:
    row = await db.fetchrow(
        """
        SELECT node_id, label, type, description, period, metadata
        FROM free_will.kg_nodes
        WHERE node_id = $1
        """,
        node_id,
    )
    return cast(dict[str, Any] | None, row)


async def _fetch_passage_row(
    db: DatabaseService, passage_id: str
) -> dict[str, Any] | None:
    """Try to resolve the passage row.

    Order of attempts:
    1. metadata.db_passage_id stored on the KG node (most authoritative)
    2. passage_id treated as a UUID directly
    3. passage_citations.kg_node_id → passages.passage_id (fallback)
    """
    # Direct UUID hit
    if _is_uuid_shape(passage_id):
        row = await db.fetchrow(
            """
            SELECT p.*, w.title AS work_title, w.author, w.language,
                   w.canonical_id AS work_canonical_id, w.kg_work_id
            FROM free_will.passages p
            JOIN free_will.ancient_works w ON p.work_id = w.work_id
            WHERE p.passage_id = $1::uuid
            """,
            passage_id,
        )
        if row:
            return cast(dict[str, Any], row)

    # Fallback: KG node carries the actual passages.passage_id in metadata.
    node = await _fetch_kg_node(db, passage_id)
    if node is not None:
        meta_raw: Any = node.get("metadata") or {}
        if isinstance(meta_raw, str):
            try:
                meta_raw = json.loads(meta_raw)
            except Exception:  # noqa: BLE001
                meta_raw = {}
        db_pid = meta_raw.get("db_passage_id") if isinstance(meta_raw, dict) else None
        if db_pid and _is_uuid_shape(str(db_pid)):
            row = await db.fetchrow(
                """
                SELECT p.*, w.title AS work_title, w.author, w.language,
                       w.canonical_id AS work_canonical_id, w.kg_work_id
                FROM free_will.passages p
                JOIN free_will.ancient_works w ON p.work_id = w.work_id
                WHERE p.passage_id = $1::uuid
                """,
                str(db_pid),
            )
            if row:
                return cast(dict[str, Any], row)

    # Last resort: passage_citations bridge.
    bridge = await db.fetchrow(
        """
        SELECT p.*, w.title AS work_title, w.author, w.language,
               w.canonical_id AS work_canonical_id, w.kg_work_id
        FROM free_will.passage_citations pc
        JOIN free_will.passages p ON pc.passage_id = p.passage_id
        JOIN free_will.ancient_works w ON p.work_id = w.work_id
        WHERE pc.kg_node_id = $1
        LIMIT 1
        """,
        passage_id,
    )
    return cast(dict[str, Any] | None, bridge)


async def _fetch_english_translation(
    db: DatabaseService, node_id: str
) -> dict[str, Any] | None:
    """Look up the companion ``{node_id}_en`` KG node, if it exists."""
    if not node_id.startswith("passage_"):
        return None
    return await _fetch_kg_node(db, f"{node_id}_en")


async def _fetch_author_for_work(
    db: DatabaseService, kg_work_id: str | None
) -> dict[str, Any] | None:
    if not kg_work_id:
        return None
    row = await db.fetchrow(
        """
        SELECT n.node_id, n.label
        FROM free_will.kg_edges e
        JOIN free_will.kg_nodes n ON e.target_id = n.node_id
        WHERE e.source_id = $1 AND e.relation = 'authored_by' AND n.type = 'person'
        UNION
        SELECT n.node_id, n.label
        FROM free_will.kg_edges e
        JOIN free_will.kg_nodes n ON e.source_id = n.node_id
        WHERE e.target_id = $1 AND e.relation = 'wrote' AND n.type = 'person'
        LIMIT 1
        """,
        kg_work_id,
    )
    return cast(dict[str, Any] | None, row)


def _extract_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            if isinstance(decoded, dict):
                return cast(dict[str, Any], decoded)
        except Exception:  # noqa: BLE001
            pass
    return {}


@router.get("/{passage_id}")
async def get_passage(
    passage_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Return one passage in the rich UI-friendly shape.

    Accepts a passages.passage_id UUID or a ``passage_*`` KG node_id.
    """
    await get_current_user(request, db)

    row = await _fetch_passage_row(db, passage_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Passage not found")

    kg_node_id = passage_id if not _is_uuid_shape(passage_id) else None
    if kg_node_id is None:
        # Try to find a KG passage node that points to this DB passage.
        bridge = await db.fetchrow(
            """
            SELECT kg_node_id FROM free_will.passage_citations
            WHERE passage_id = $1 LIMIT 1
            """,
            row["passage_id"],
        )
        if bridge:
            kg_node_id = bridge["kg_node_id"]

    english_node = (
        await _fetch_english_translation(db, kg_node_id) if kg_node_id else None
    )
    english_meta = (
        _extract_metadata(english_node.get("metadata")) if english_node else {}
    )
    english_text = english_node.get("description") if english_node else None
    translator = english_meta.get("translator") or english_meta.get("source_model")
    translation_source = (
        "published"
        if english_meta.get("source") in {"published", "scholarly"}
        else "machine"
        if english_node
        else None
    )

    author_node = await _fetch_author_for_work(db, row.get("kg_work_id"))

    metadata = _extract_metadata(row.get("metadata") if hasattr(row, "get") else None)
    pass_meta = _extract_metadata(row.get("citation_hierarchy"))
    # Edition info lives either on the KG node or as a column on ancient_works.
    edition_metadata = {
        "edition": metadata.get("edition") or english_meta.get("edition"),
        "publisher": metadata.get("publisher"),
        "section": row.get("canonical_ref"),
    }

    attestation_type = (
        metadata.get("attestation_type")
        or english_meta.get("attestation_type")
        or "direct"
    )
    fragment_collections = metadata.get("fragment_collections") or []

    return {
        "passage_id": str(row["passage_id"]),
        "node_id": kg_node_id,
        "work_id": str(row["work_id"]) if row.get("work_id") else None,
        "work_canonical_id": row.get("work_canonical_id"),
        "work_label": row.get("work_title"),
        "author": (
            {"node_id": author_node["node_id"], "label": author_node["label"]}
            if author_node
            else {"node_id": None, "label": row.get("author")}
        ),
        "cts_urn": row.get("cts_urn"),
        "label": row.get("canonical_ref"),
        "text_content_original": row.get("text_content"),
        "text_content_english": english_text,
        "translation_metadata": {
            "translator": translator,
            "source": translation_source,
        },
        "edition_metadata": edition_metadata,
        "language": row.get("language") or "grc",
        "lemmas": (row.get("morphology") or {})
        if isinstance(row.get("morphology"), dict)
        else [],
        "metadata": {**metadata, **pass_meta} if metadata or pass_meta else {},
        "attestation_type": attestation_type,
        "fragment_collections": fragment_collections,
        "sequence_number": row.get("sequence_number"),
    }
