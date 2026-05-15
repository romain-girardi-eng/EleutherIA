"""
Community KG contribution endpoints — Feature 8 backbone.

Lifecycle:

    upload  ──>  processing  ──>  ready  ──>  approved  ──>  merged
                                       └──>   rejected
                                       └──>   failed

A researcher uploads a scholarly PDF via ``POST /api/contributions/upload``.
The PDF is stored in Supabase Storage (or local FS in dev) and a Temporal
workflow extracts free-will-relevant atoms (nodes, edges, passage citations).
Each atom lands in ``kg_contribution_proposals`` with ``status='pending'``.

Romain (admin) reviews proposals through ``GET /{id}`` and accepts/rejects
each one. ``POST /{id}/apply`` then merges every ``accepted`` proposal into
the live KG inside a single transaction — all-or-nothing — and bumps
``kg_contributions.status`` to ``merged``. The kg_version trigger installed
by migration 08 will fire on the INSERTs, invalidating the answer cache.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from eleutheria_database.services.db import DatabaseService
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from pydantic import BaseModel, Field

from backend.dependencies import get_db
from backend.routes.auth import get_current_user
from backend.services.contribution_storage import (
    ContributionStorage,
    get_contribution_storage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contributions", tags=["contributions"])


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_PDF_BYTES = 25 * 1024 * 1024  # 25 MB
_DEFAULT_LIST_STATUSES: tuple[str, ...] = (
    "processing",
    "ready",
    "approved",
    "merged",
)
_ALL_STATUSES: frozenset[str] = frozenset(
    {
        "uploaded",
        "processing",
        "ready",
        "approved",
        "rejected",
        "merged",
        "failed",
    }
)
_TEMPORAL_TASK_QUEUE_ENV = "TEMPORAL_TASK_QUEUE"
_PROCESS_WORKFLOW_TYPE = "ProcessContributionWorkflow"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ContributionUploadResponse(BaseModel):
    contribution_id: str
    status: str
    pdf_signed_url: str
    estimated_processing_seconds: int


class ContributionListItem(BaseModel):
    contribution_id: str
    title: str | None
    authors: list[str]
    publication_year: int | None
    doi: str | None
    status: str
    relevance_score: float | None
    free_will_concepts: list[str]
    proposal_count: int
    submitted_at: datetime
    submitter_user_id: str | None


class ContributionListResponse(BaseModel):
    items: list[ContributionListItem]
    next_cursor: str | None = None


class ProposalSummary(BaseModel):
    proposal_id: str
    kind: str
    confidence: float
    payload: dict[str, Any]
    target_kg_id: str | None
    evidence: dict[str, Any]
    status: str
    reviewer_notes: str | None


class ContributionDetail(ContributionListItem):
    pdf_signed_url: str
    relevance_summary: str | None
    pdf_metadata: dict[str, Any]
    proposals: list[ProposalSummary]
    reviewer_notes: str | None
    reviewer_user_id: str | None
    reviewed_at: datetime | None


class ReviewerNotesBody(BaseModel):
    reviewer_notes: str | None = Field(default=None, max_length=4000)


class ApplyResponse(BaseModel):
    contribution_id: str
    merged_proposals: int
    kg_version_after: int


# ---------------------------------------------------------------------------
# Dependencies / helpers
# ---------------------------------------------------------------------------


def get_storage() -> ContributionStorage:
    return get_contribution_storage()


async def _require_admin(
    request: Request,
    db: DatabaseService,
) -> dict[str, Any]:
    """Resolve the JWT-bound user and 403 unless their role is ``admin``."""
    user = await get_current_user(request, db)
    if (user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def _maybe_json(value: Any) -> Any:
    """asyncpg returns jsonb as decoded objects most of the time but falls back
    to raw strings in edge cases — handle both."""
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value:
        try:
            return json.loads(value)
        except json.JSONDecodeError, ValueError:
            return None
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    decoded = _maybe_json(value)
    return decoded if isinstance(decoded, dict) else {}


def _split_authors(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [piece.strip() for piece in raw.split(",") if piece.strip()]


def _encode_cursor(submitted_at: datetime, contribution_id: str) -> str:
    payload = f"{submitted_at.isoformat()}|{contribution_id}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        iso_part, id_part = decoded.split("|", 1)
        return datetime.fromisoformat(iso_part), id_part
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


def _list_item_from_row(row: dict[str, Any]) -> ContributionListItem:
    submitter = row.get("submitter_user_id")
    relevance = row.get("relevance_score")
    return ContributionListItem(
        contribution_id=str(row["contribution_id"]),
        title=row.get("title"),
        authors=list(row.get("authors") or []),
        publication_year=row.get("publication_year"),
        doi=row.get("doi"),
        status=row["status"],
        relevance_score=float(relevance) if relevance is not None else None,
        free_will_concepts=list(row.get("free_will_concepts") or []),
        proposal_count=int(row.get("proposal_count") or 0),
        submitted_at=row["submitted_at"],
        submitter_user_id=str(submitter) if submitter else None,
    )


def _proposal_summary(row: dict[str, Any]) -> ProposalSummary:
    return ProposalSummary(
        proposal_id=str(row["proposal_id"]),
        kind=row["kind"],
        confidence=float(row.get("confidence") or 0.0),
        payload=_as_dict(row.get("payload")),
        target_kg_id=row.get("target_kg_id"),
        evidence=_as_dict(row.get("evidence")),
        status=row["status"],
        reviewer_notes=row.get("reviewer_notes"),
    )


async def _enqueue_processing(contribution_id: str) -> None:
    """Best-effort dispatch of the extraction workflow.

    The workflow itself is owned by another agent; we simply hand the
    contribution id to Temporal. If Temporal isn't reachable we log and
    return — the contribution row sits at ``status='uploaded'`` and an
    out-of-band CLI runner can pick it up.
    """
    try:
        from backend.services.temporal import get_temporal_client

        client = await get_temporal_client()
        import os

        task_queue = os.getenv(_TEMPORAL_TASK_QUEUE_ENV, "eleutheria-ingestion")
        workflow_id = f"contribution-{contribution_id}"
        await client.start_workflow(
            _PROCESS_WORKFLOW_TYPE,
            contribution_id,
            id=workflow_id,
            task_queue=task_queue,
        )
        logger.info("Dispatched %s for %s", _PROCESS_WORKFLOW_TYPE, contribution_id)
    except Exception:
        logger.warning(
            "Temporal dispatch failed for contribution %s — fallback runner will pick it up",
            contribution_id,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Routes — upload
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=ContributionUploadResponse, status_code=201)
async def upload_contribution(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    storage: Annotated[ContributionStorage, Depends(get_storage)],
    pdf: Annotated[UploadFile, File(...)],
    title: Annotated[str | None, Form()] = None,
    authors: Annotated[str | None, Form()] = None,
    doi: Annotated[str | None, Form()] = None,
    publication_year: Annotated[int | None, Form()] = None,
) -> ContributionUploadResponse:
    """Upload a scholarly PDF and queue it for extraction."""
    user = await get_current_user(request, db)

    # ----- Validation ---------------------------------------------------
    content_type = (pdf.content_type or "").lower()
    if content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail=f"PDF required (got content-type '{pdf.content_type}')",
        )

    content = await pdf.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=422, detail="Empty PDF")
    if size > _MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(f"PDF too large ({size} bytes); max {_MAX_PDF_BYTES} bytes"),
        )

    filename = pdf.filename or "contribution.pdf"
    author_list = _split_authors(authors)

    # ----- Insert row ---------------------------------------------------
    submitter_uuid = uuid.UUID(user["user_id"])
    inserted = await db.fetchrow(
        """
        INSERT INTO free_will.kg_contributions (
            submitter_user_id, pdf_url, pdf_filename, pdf_size_bytes,
            title, authors, doi, publication_year, status
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'uploaded')
        RETURNING contribution_id, status
        """,
        submitter_uuid,
        "",  # pdf_url is filled after we know the storage path
        filename,
        size,
        title,
        author_list,
        doi,
        publication_year,
    )
    if not inserted:
        raise HTTPException(status_code=500, detail="Failed to insert contribution row")

    contribution_id = str(inserted["contribution_id"])

    # ----- Upload blob --------------------------------------------------
    try:
        storage_path = await storage.put_pdf(
            contribution_id=contribution_id,
            filename=filename,
            content=content,
            content_type=content_type,
        )
    except Exception as exc:
        # Best-effort rollback so we don't leave a row pointing at nothing.
        await db.execute(
            "DELETE FROM free_will.kg_contributions WHERE contribution_id = $1",
            uuid.UUID(contribution_id),
        )
        logger.exception("Failed to upload PDF blob for %s", contribution_id)
        raise HTTPException(
            status_code=502, detail="PDF storage upload failed"
        ) from exc

    await db.execute(
        """
        UPDATE free_will.kg_contributions
        SET pdf_url = $1
        WHERE contribution_id = $2
        """,
        storage_path,
        uuid.UUID(contribution_id),
    )

    signed_url = await storage.get_signed_url(storage_path)

    # ----- Dispatch workflow (non-blocking on failure) -----------------
    await _enqueue_processing(contribution_id)

    return ContributionUploadResponse(
        contribution_id=contribution_id,
        status=inserted["status"],
        pdf_signed_url=signed_url,
        estimated_processing_seconds=180,
    )


# ---------------------------------------------------------------------------
# Routes — list & detail (public)
# ---------------------------------------------------------------------------


@router.get("", response_model=ContributionListResponse)
async def list_contributions(
    db: Annotated[DatabaseService, Depends(get_db)],
    status: Annotated[
        str | None,
        Query(
            description=(
                "Comma-separated statuses to include. Defaults to processing,"
                "ready,approved,merged."
            )
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> ContributionListResponse:
    """Paginated list of contributions (newest first)."""
    if status:
        requested = [s.strip() for s in status.split(",") if s.strip()]
        if any(s not in _ALL_STATUSES for s in requested):
            raise HTTPException(status_code=400, detail="Unknown status filter")
        statuses = requested
    else:
        statuses = list(_DEFAULT_LIST_STATUSES)

    params: list[Any] = [statuses]
    conditions = ["c.status = ANY($1::text[])"]

    if cursor:
        cursor_dt, cursor_id = _decode_cursor(cursor)
        params.append(cursor_dt)
        params.append(uuid.UUID(cursor_id))
        conditions.append(
            f"(c.submitted_at, c.contribution_id) < (${len(params) - 1}, ${len(params)})"
        )

    params.append(limit + 1)
    sql = f"""
        SELECT
            c.contribution_id,
            c.title,
            c.authors,
            c.publication_year,
            c.doi,
            c.status,
            c.relevance_score,
            c.free_will_concepts,
            c.submitted_at,
            c.submitter_user_id,
            (
                SELECT count(*)::int
                FROM free_will.kg_contribution_proposals p
                WHERE p.contribution_id = c.contribution_id
                  AND p.status IN ('pending', 'accepted')
            ) AS proposal_count
        FROM free_will.kg_contributions c
        WHERE {" AND ".join(conditions)}
        ORDER BY c.submitted_at DESC, c.contribution_id DESC
        LIMIT ${len(params)}
    """

    rows = await db.fetch(sql, *params)
    has_more = len(rows) > limit
    visible = rows[:limit]

    items = [_list_item_from_row(row) for row in visible]
    next_cursor: str | None = None
    if has_more and visible:
        last = visible[-1]
        next_cursor = _encode_cursor(last["submitted_at"], str(last["contribution_id"]))

    return ContributionListResponse(items=items, next_cursor=next_cursor)


@router.get("/{contribution_id}", response_model=ContributionDetail)
async def get_contribution(
    contribution_id: str,
    db: Annotated[DatabaseService, Depends(get_db)],
    storage: Annotated[ContributionStorage, Depends(get_storage)],
) -> ContributionDetail:
    """Full contribution with every proposal."""
    try:
        contribution_uuid = uuid.UUID(contribution_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid contribution_id") from None

    row = await db.fetchrow(
        """
        SELECT
            c.contribution_id, c.submitter_user_id, c.submitted_at,
            c.pdf_url, c.pdf_filename, c.title, c.authors, c.doi,
            c.publication_year, c.pdf_metadata, c.relevance_score,
            c.relevance_summary, c.free_will_concepts, c.status,
            c.reviewer_notes, c.reviewer_user_id, c.reviewed_at,
            (
                SELECT count(*)::int
                FROM free_will.kg_contribution_proposals p
                WHERE p.contribution_id = c.contribution_id
                  AND p.status IN ('pending', 'accepted')
            ) AS proposal_count
        FROM free_will.kg_contributions c
        WHERE c.contribution_id = $1
        """,
        contribution_uuid,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Contribution not found")

    proposal_rows = await db.fetch(
        """
        SELECT proposal_id, kind, confidence, payload, target_kg_id,
               evidence, status, reviewer_notes
        FROM free_will.kg_contribution_proposals
        WHERE contribution_id = $1
        ORDER BY created_at ASC, proposal_id ASC
        """,
        contribution_uuid,
    )
    proposals = [_proposal_summary(p) for p in proposal_rows]

    signed_url = ""
    if row.get("pdf_url"):
        try:
            signed_url = await storage.get_signed_url(row["pdf_url"])
        except Exception:
            logger.exception(
                "Failed to sign PDF url for contribution %s", contribution_id
            )

    base = _list_item_from_row(row)
    reviewer_id = row.get("reviewer_user_id")
    return ContributionDetail(
        **base.model_dump(),
        pdf_signed_url=signed_url,
        relevance_summary=row.get("relevance_summary"),
        pdf_metadata=_as_dict(row.get("pdf_metadata")),
        proposals=proposals,
        reviewer_notes=row.get("reviewer_notes"),
        reviewer_user_id=str(reviewer_id) if reviewer_id else None,
        reviewed_at=row.get("reviewed_at"),
    )


# ---------------------------------------------------------------------------
# Routes — review (admin)
# ---------------------------------------------------------------------------


async def _set_proposal_status(
    *,
    db: DatabaseService,
    contribution_id: str,
    proposal_id: str,
    new_status: Literal["accepted", "rejected"],
    reviewer_notes: str | None,
) -> ProposalSummary:
    try:
        contribution_uuid = uuid.UUID(contribution_id)
        proposal_uuid = uuid.UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid id") from None

    updated = await db.fetchrow(
        """
        UPDATE free_will.kg_contribution_proposals
        SET status = $3,
            reviewer_notes = COALESCE($4, reviewer_notes)
        WHERE proposal_id = $1 AND contribution_id = $2
        RETURNING proposal_id, kind, confidence, payload, target_kg_id,
                  evidence, status, reviewer_notes
        """,
        proposal_uuid,
        contribution_uuid,
        new_status,
        reviewer_notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return _proposal_summary(updated)


@router.post(
    "/{contribution_id}/proposals/{proposal_id}/accept",
    response_model=ProposalSummary,
)
async def accept_proposal(
    contribution_id: str,
    proposal_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    body: ReviewerNotesBody | None = None,
) -> ProposalSummary:
    """Mark a single proposal as ``accepted``. Admin only."""
    await _require_admin(request, db)
    notes = body.reviewer_notes if body else None
    return await _set_proposal_status(
        db=db,
        contribution_id=contribution_id,
        proposal_id=proposal_id,
        new_status="accepted",
        reviewer_notes=notes,
    )


@router.post(
    "/{contribution_id}/proposals/{proposal_id}/reject",
    response_model=ProposalSummary,
)
async def reject_proposal(
    contribution_id: str,
    proposal_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    body: ReviewerNotesBody | None = None,
) -> ProposalSummary:
    """Mark a single proposal as ``rejected``. Admin only."""
    await _require_admin(request, db)
    notes = body.reviewer_notes if body else None
    return await _set_proposal_status(
        db=db,
        contribution_id=contribution_id,
        proposal_id=proposal_id,
        new_status="rejected",
        reviewer_notes=notes,
    )


# ---------------------------------------------------------------------------
# Routes — merge / reject whole contribution (admin)
# ---------------------------------------------------------------------------


def _node_payload_to_columns(payload: dict[str, Any]) -> dict[str, Any]:
    """Coerce a proposal payload into the kg_nodes column shape."""
    columns: dict[str, Any] = {
        "node_id": payload.get("node_id") or payload.get("id"),
        "label": payload.get("label"),
        "type": payload.get("type"),
        "description": payload.get("description"),
        "period": payload.get("period"),
        "alternative_names": payload.get("alternative_names"),
        "metadata": payload.get("metadata") or {},
    }
    if not columns["label"]:
        raise HTTPException(status_code=400, detail="node proposal missing 'label'")
    if not columns["type"]:
        raise HTTPException(status_code=400, detail="node proposal missing 'type'")
    return columns


def _edge_payload_to_columns(payload: dict[str, Any]) -> dict[str, Any]:
    source_id = payload.get("source_id") or payload.get("source")
    target_id = payload.get("target_id") or payload.get("target")
    relation = payload.get("relation")
    if not (source_id and target_id and relation):
        raise HTTPException(
            status_code=400,
            detail="edge proposal needs source_id/target_id/relation",
        )
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation": relation,
        "weight": payload.get("weight", 1.0),
        "metadata": payload.get("metadata") or {},
    }


def _passage_citation_to_columns(payload: dict[str, Any]) -> dict[str, Any]:
    passage_id = payload.get("passage_id")
    kg_node_id = payload.get("kg_node_id")
    if not (passage_id and kg_node_id):
        raise HTTPException(
            status_code=400,
            detail="passage_citation proposal needs passage_id and kg_node_id",
        )
    return {
        "passage_id": passage_id,
        "kg_node_id": kg_node_id,
        "citation_type": payload.get("citation_type"),
        "confidence": payload.get("confidence"),
        "notes": payload.get("notes"),
    }


async def _apply_node(conn: Any, payload: dict[str, Any]) -> str:
    cols = _node_payload_to_columns(payload)
    metadata_json = json.dumps(cols["metadata"])
    alt_json = (
        json.dumps(cols["alternative_names"])
        if cols["alternative_names"] is not None
        else None
    )
    if cols["node_id"]:
        row = await conn.fetchrow(
            """
            INSERT INTO free_will.kg_nodes
                (node_id, label, type, description, period,
                 alternative_names, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
            ON CONFLICT (node_id) DO UPDATE
                SET label = EXCLUDED.label,
                    type = EXCLUDED.type,
                    description = EXCLUDED.description,
                    period = EXCLUDED.period,
                    alternative_names = EXCLUDED.alternative_names,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
            RETURNING node_id
            """,
            cols["node_id"],
            cols["label"],
            cols["type"],
            cols["description"],
            cols["period"],
            alt_json,
            metadata_json,
        )
    else:
        node_id = f"contrib_{uuid.uuid4().hex[:12]}"
        row = await conn.fetchrow(
            """
            INSERT INTO free_will.kg_nodes
                (node_id, label, type, description, period,
                 alternative_names, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
            RETURNING node_id
            """,
            node_id,
            cols["label"],
            cols["type"],
            cols["description"],
            cols["period"],
            alt_json,
            metadata_json,
        )
    return str(row["node_id"])


async def _apply_edge(conn: Any, payload: dict[str, Any]) -> str:
    cols = _edge_payload_to_columns(payload)
    metadata_json = json.dumps(cols["metadata"])
    row = await conn.fetchrow(
        """
        INSERT INTO free_will.kg_edges
            (source_id, target_id, relation, weight, metadata)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        RETURNING edge_id
        """,
        cols["source_id"],
        cols["target_id"],
        cols["relation"],
        cols["weight"],
        metadata_json,
    )
    return str(row["edge_id"])


async def _apply_passage_citation(conn: Any, payload: dict[str, Any]) -> str:
    cols = _passage_citation_to_columns(payload)
    passage_uuid = uuid.UUID(str(cols["passage_id"]))
    row = await conn.fetchrow(
        """
        INSERT INTO free_will.passage_citations
            (passage_id, kg_node_id, citation_type, confidence, notes)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING citation_id
        """,
        passage_uuid,
        cols["kg_node_id"],
        cols["citation_type"],
        cols["confidence"],
        cols["notes"],
    )
    return str(row["citation_id"])


async def _apply_scholar_ref(conn: Any, payload: dict[str, Any]) -> str:
    """A scholar_ref proposal carries a `node` + optional `edge` already
    structured by the extraction pipeline."""
    node_payload = payload.get("node") or payload
    node_id = await _apply_node(conn, node_payload)
    edge_payload = payload.get("edge")
    if edge_payload:
        if not edge_payload.get("source_id") and not edge_payload.get("source"):
            edge_payload["source_id"] = node_id
        await _apply_edge(conn, edge_payload)
    return node_id


async def _apply_concept_attestation(conn: Any, payload: dict[str, Any]) -> str:
    """A concept_attestation = node + edge linking the concept to evidence."""
    return await _apply_scholar_ref(conn, payload)


_APPLIERS = {
    "node": _apply_node,
    "edge": _apply_edge,
    "passage_citation": _apply_passage_citation,
    "scholar_ref": _apply_scholar_ref,
    "concept_attestation": _apply_concept_attestation,
}


@router.post("/{contribution_id}/apply", response_model=ApplyResponse)
async def apply_contribution(
    contribution_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    body: ReviewerNotesBody | None = None,
) -> ApplyResponse:
    """Merge every ``accepted`` proposal into the live KG. All-or-nothing."""
    user = await _require_admin(request, db)
    notes = body.reviewer_notes if body else None

    try:
        contribution_uuid = uuid.UUID(contribution_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid contribution_id") from None

    accepted = await db.fetch(
        """
        SELECT proposal_id, kind, payload
        FROM free_will.kg_contribution_proposals
        WHERE contribution_id = $1 AND status = 'accepted'
        ORDER BY created_at ASC, proposal_id ASC
        """,
        contribution_uuid,
    )
    if not accepted:
        raise HTTPException(status_code=400, detail="No accepted proposals to apply")

    merged_count = 0
    kg_version_after = 0
    try:
        async with db.connection() as conn, conn.transaction():
            for proposal in accepted:
                kind = proposal["kind"]
                applier = _APPLIERS.get(kind)
                if applier is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown proposal kind: {kind}",
                    )
                payload = _as_dict(proposal.get("payload"))
                await applier(conn, payload)
                await conn.execute(
                    """
                    UPDATE free_will.kg_contribution_proposals
                    SET status = 'applied', applied_at = now()
                    WHERE proposal_id = $1
                    """,
                    proposal["proposal_id"],
                )
                merged_count += 1

            await conn.execute(
                """
                UPDATE free_will.kg_contributions
                SET status = 'merged',
                    merged_at = now(),
                    reviewer_user_id = $2,
                    reviewer_notes = COALESCE($3, reviewer_notes),
                    reviewed_at = now()
                WHERE contribution_id = $1
                """,
                contribution_uuid,
                uuid.UUID(user["user_id"]),
                notes,
            )

            version_row = await conn.fetchrow(
                "SELECT version FROM free_will.kg_version WHERE id = 1"
            )
            kg_version_after = int((version_row or {}).get("version") or 0)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Apply failed for contribution %s", contribution_id)
        raise HTTPException(
            status_code=500,
            detail=f"Apply failed and was rolled back: {exc}",
        ) from exc

    return ApplyResponse(
        contribution_id=contribution_id,
        merged_proposals=merged_count,
        kg_version_after=kg_version_after,
    )


@router.post("/{contribution_id}/reject", response_model=ContributionListItem)
async def reject_contribution(
    contribution_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    body: ReviewerNotesBody | None = None,
) -> ContributionListItem:
    """Reject the whole contribution. Admin only."""
    user = await _require_admin(request, db)
    notes = body.reviewer_notes if body else None

    try:
        contribution_uuid = uuid.UUID(contribution_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid contribution_id") from None

    row = await db.fetchrow(
        """
        UPDATE free_will.kg_contributions
        SET status = 'rejected',
            reviewer_user_id = $2,
            reviewer_notes = COALESCE($3, reviewer_notes),
            reviewed_at = now()
        WHERE contribution_id = $1
        RETURNING
            contribution_id, title, authors, publication_year, doi,
            status, relevance_score, free_will_concepts, submitted_at,
            submitter_user_id,
            (
                SELECT count(*)::int
                FROM free_will.kg_contribution_proposals p
                WHERE p.contribution_id = $1
                  AND p.status IN ('pending', 'accepted')
            ) AS proposal_count
        """,
        contribution_uuid,
        uuid.UUID(user["user_id"]),
        notes,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Contribution not found")
    # Reviewer fields silenced from datetime.utc — not used here but keep
    # consistent with downstream callers.
    _ = datetime.now(UTC)
    return _list_item_from_row(row)


__all__ = ["router"]
