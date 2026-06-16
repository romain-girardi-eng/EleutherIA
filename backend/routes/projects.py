"""
Research project routes — per-user workspaces with document upload.

All endpoints require authentication. Every query is ownership-scoped
(user_id = current_user); 404 is returned rather than 403 when a row
exists but belongs to another user to avoid leaking existence.

File bytes are stored as Postgres BYTEA in project_document_blobs,
separated from the metadata table so list queries never load blob payloads.
Text extraction runs in a FastAPI BackgroundTasks job after the upload
returns 201.
"""

from __future__ import annotations

import io
import logging
import uuid
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.dependencies import get_db
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB
_ALLOWED_CONTENT_TYPES = frozenset({"application/pdf", "text/plain"})


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str | None
    status: str
    created_at: str
    updated_at: str
    document_count: int


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    content_type: str | None
    size_bytes: int | None
    page_count: int | None
    status: str
    created_at: str


class ProjectDetailResponse(BaseModel):
    project_id: str
    name: str
    description: str | None
    status: str
    created_at: str
    updated_at: str
    documents: list[DocumentSummary]


class DocumentFullResponse(BaseModel):
    document_id: str
    project_id: str
    filename: str
    content_type: str | None
    size_bytes: int | None
    page_count: int | None
    status: str
    extracted_text: str | None
    page_texts: list[dict[str, Any]] | None
    created_at: str


class UploadDocumentResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str | None
    size_bytes: int | None
    page_count: int | None
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fmt_ts(ts: Any) -> str:
    """Format a datetime-like value from asyncpg as an ISO-8601 string."""
    if ts is None:
        return ""
    return str(ts.isoformat()) if hasattr(ts, "isoformat") else str(ts)


def _project_row_to_response(
    row: dict[str, Any], document_count: int
) -> ProjectResponse:
    return ProjectResponse(
        project_id=str(row["project_id"]),
        name=row["name"],
        description=row.get("description"),
        status=row["status"],
        created_at=_fmt_ts(row["created_at"]),
        updated_at=_fmt_ts(row["updated_at"]),
        document_count=document_count,
    )


def _doc_summary(row: dict[str, Any]) -> DocumentSummary:
    return DocumentSummary(
        document_id=str(row["document_id"]),
        filename=row["filename"],
        content_type=row.get("content_type"),
        size_bytes=row.get("size_bytes"),
        page_count=row.get("page_count"),
        status=row["status"],
        created_at=_fmt_ts(row["created_at"]),
    )


async def _own_project(
    project_id: uuid.UUID,
    user_id: str,
    db: DatabaseService,
) -> dict[str, Any]:
    """Fetch a project row and 404 if missing or not owned by user_id."""
    row = await db.fetchrow(
        """
        SELECT project_id, user_id, name, description, status,
               created_at, updated_at
        FROM free_will.research_projects
        WHERE project_id = $1
        """,
        project_id,
    )
    if not row or str(row["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return dict(row)


async def _own_document(
    document_id: uuid.UUID,
    user_id: str,
    db: DatabaseService,
) -> dict[str, Any]:
    """Fetch a document row and 404 if missing or not owned by user_id."""
    row = await db.fetchrow(
        """
        SELECT document_id, project_id, user_id, filename, content_type,
               size_bytes, page_count, extracted_text, page_texts, status,
               metadata, created_at
        FROM free_will.project_documents
        WHERE document_id = $1
        """,
        document_id,
    )
    if not row or str(row["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(row)


# ---------------------------------------------------------------------------
# Background text extraction
# ---------------------------------------------------------------------------


async def _extract_and_update(
    document_id: uuid.UUID,
    db: DatabaseService,
) -> None:
    """Read blob, extract text via pypdf (or utf-8 for plain text), update row."""
    try:
        blob_row = await db.fetchrow(
            "SELECT bytes FROM free_will.project_document_blobs WHERE document_id = $1",
            document_id,
        )
        if not blob_row:
            logger.error("Blob not found for document %s", document_id)
            await db.execute(
                "UPDATE free_will.project_documents SET status = 'failed'"
                " WHERE document_id = $1",
                document_id,
            )
            return

        meta_row = await db.fetchrow(
            "SELECT content_type FROM free_will.project_documents WHERE document_id = $1",
            document_id,
        )
        content_type = (meta_row or {}).get("content_type") or ""

        raw: bytes = bytes(blob_row["bytes"])
        extracted_text: str
        page_texts: list[dict[str, Any]]
        page_count: int

        if content_type == "application/pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            pages: list[dict[str, Any]] = []
            full_parts: list[str] = []
            for idx, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    logger.exception(
                        "pypdf failed on page %d of document %s", idx, document_id
                    )
                    text = ""
                pages.append({"page": idx, "text": text})
                full_parts.append(text)
            page_texts = pages
            extracted_text = "\n".join(full_parts)
            page_count = len(reader.pages)
        else:
            # text/plain — treat as single page
            text = raw.decode("utf-8", errors="replace")
            page_texts = [{"page": 1, "text": text}]
            extracted_text = text
            page_count = 1

        import json

        await db.execute(
            """
            UPDATE free_will.project_documents
            SET extracted_text = $2,
                page_texts     = $3::jsonb,
                page_count     = $4,
                status         = 'ready'
            WHERE document_id = $1
            """,
            document_id,
            extracted_text,
            json.dumps(page_texts),
            page_count,
        )
        logger.info(
            "Extraction complete for document %s (%d pages)", document_id, page_count
        )

    except Exception:
        logger.exception("Extraction failed for document %s", document_id)
        try:
            await db.execute(
                "UPDATE free_will.project_documents SET status = 'failed'"
                " WHERE document_id = $1",
                document_id,
            )
        except Exception:
            logger.exception(
                "Could not update status to failed for document %s", document_id
            )


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    body: CreateProjectRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> ProjectResponse:
    """Create a new research project."""
    user = await get_current_user(request, db)
    user_uuid = uuid.UUID(user["user_id"])

    row = await db.fetchrow(
        """
        INSERT INTO free_will.research_projects (user_id, name, description)
        VALUES ($1, $2, $3)
        RETURNING project_id, user_id, name, description, status,
                  created_at, updated_at
        """,
        user_uuid,
        body.name,
        body.description,
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create project")
    return _project_row_to_response(dict(row), 0)


@router.get("", response_model=dict[str, list[ProjectResponse]])
async def list_projects(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, list[ProjectResponse]]:
    """List all projects for the authenticated user."""
    user = await get_current_user(request, db)
    user_uuid = uuid.UUID(user["user_id"])

    rows = await db.fetch(
        """
        SELECT p.project_id, p.user_id, p.name, p.description, p.status,
               p.created_at, p.updated_at,
               COUNT(d.document_id)::int AS document_count
        FROM free_will.research_projects p
        LEFT JOIN free_will.project_documents d
               ON d.project_id = p.project_id
        WHERE p.user_id = $1
        GROUP BY p.project_id
        ORDER BY p.created_at DESC
        """,
        user_uuid,
    )
    projects = [
        _project_row_to_response(dict(r), int(r["document_count"] or 0)) for r in rows
    ]
    return {"projects": projects}


@router.get("/documents/{document_id}", response_model=DocumentFullResponse)
async def get_document(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> DocumentFullResponse:
    """Get full document metadata including extracted text."""
    user = await get_current_user(request, db)
    row = await _own_document(document_id, user["user_id"], db)

    raw_pages = row.get("page_texts")
    page_texts_out: list[dict[str, Any]] | None = None
    if raw_pages is not None:
        if isinstance(raw_pages, list):
            page_texts_out = raw_pages
        elif isinstance(raw_pages, str):
            import json

            try:
                page_texts_out = json.loads(raw_pages)
            except json.JSONDecodeError, ValueError:
                page_texts_out = None

    return DocumentFullResponse(
        document_id=str(row["document_id"]),
        project_id=str(row["project_id"]),
        filename=row["filename"],
        content_type=row.get("content_type"),
        size_bytes=row.get("size_bytes"),
        page_count=row.get("page_count"),
        status=row["status"],
        extracted_text=row.get("extracted_text"),
        page_texts=page_texts_out,
        created_at=_fmt_ts(row["created_at"]),
    )


@router.get("/documents/{document_id}/file")
async def download_document(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> Response:
    """Stream raw document bytes with Content-Disposition: inline."""
    user = await get_current_user(request, db)
    meta = await _own_document(document_id, user["user_id"], db)

    blob_row = await db.fetchrow(
        "SELECT bytes FROM free_will.project_document_blobs WHERE document_id = $1",
        document_id,
    )
    if not blob_row:
        raise HTTPException(status_code=404, detail="Document file not found")

    raw: bytes = bytes(blob_row["bytes"])
    media_type = meta.get("content_type") or "application/pdf"
    filename = meta["filename"]

    return StreamingResponse(
        io.BytesIO(raw),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(raw)),
        },
    )


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> None:
    """Delete a document and its blob (cascade)."""
    user = await get_current_user(request, db)
    await _own_document(document_id, user["user_id"], db)

    await db.execute(
        "DELETE FROM free_will.project_documents WHERE document_id = $1",
        document_id,
    )


# ---------------------------------------------------------------------------
# Per-project document sub-routes
# IMPORTANT: these must be registered AFTER /documents/{document_id} routes
# so the static prefix "documents" is matched before /{project_id}.
# ---------------------------------------------------------------------------


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> ProjectDetailResponse:
    """Get project details with document list (no bytes, no extracted text)."""
    user = await get_current_user(request, db)
    proj = await _own_project(project_id, user["user_id"], db)

    doc_rows = await db.fetch(
        """
        SELECT document_id, filename, content_type, size_bytes,
               page_count, status, created_at
        FROM free_will.project_documents
        WHERE project_id = $1
        ORDER BY created_at DESC
        """,
        project_id,
    )
    return ProjectDetailResponse(
        project_id=str(proj["project_id"]),
        name=proj["name"],
        description=proj.get("description"),
        status=proj["status"],
        created_at=_fmt_ts(proj["created_at"]),
        updated_at=_fmt_ts(proj["updated_at"]),
        documents=[_doc_summary(dict(r)) for r in doc_rows],
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> ProjectResponse:
    """Update project name, description, and/or status."""
    user = await get_current_user(request, db)
    await _own_project(project_id, user["user_id"], db)

    row = await db.fetchrow(
        """
        UPDATE free_will.research_projects
        SET name        = COALESCE($2, name),
            description = COALESCE($3, description),
            status      = COALESCE($4, status),
            updated_at  = now()
        WHERE project_id = $1
        RETURNING project_id, user_id, name, description, status,
                  created_at, updated_at
        """,
        project_id,
        body.name,
        body.description,
        body.status,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    count_row = await db.fetchrow(
        "SELECT COUNT(*)::int AS n FROM free_will.project_documents WHERE project_id = $1",
        project_id,
    )
    doc_count = int((count_row or {}).get("n") or 0)
    return _project_row_to_response(dict(row), doc_count)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> None:
    """Delete a project and all its documents + blobs (cascade)."""
    user = await get_current_user(request, db)
    await _own_project(project_id, user["user_id"], db)

    await db.execute(
        "DELETE FROM free_will.research_projects WHERE project_id = $1",
        project_id,
    )


@router.post(
    "/{project_id}/documents", status_code=201, response_model=UploadDocumentResponse
)
async def upload_document(
    project_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[DatabaseService, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
) -> UploadDocumentResponse:
    """Upload a PDF or plain-text document to a project."""
    user = await get_current_user(request, db)
    user_uuid = uuid.UUID(user["user_id"])
    await _own_project(project_id, user["user_id"], db)

    # Validate content-type
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Only PDF and plain-text files accepted (got '{file.content_type}')",
        )

    content = await file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=422, detail="Empty file")
    if size > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size} bytes); max {_MAX_FILE_BYTES} bytes",
        )

    filename = file.filename or "document"

    # Insert document metadata + blob in a single transaction
    doc_row = await db.fetchrow(
        """
        INSERT INTO free_will.project_documents
            (project_id, user_id, filename, content_type, size_bytes, status)
        VALUES ($1, $2, $3, $4, $5, 'processing')
        RETURNING document_id, filename, content_type, size_bytes,
                  page_count, status, created_at
        """,
        project_id,
        user_uuid,
        filename,
        content_type or None,
        size,
    )
    if not doc_row:
        raise HTTPException(status_code=500, detail="Failed to insert document row")

    document_id = doc_row["document_id"]

    try:
        await db.execute(
            """
            INSERT INTO free_will.project_document_blobs (document_id, bytes)
            VALUES ($1, $2)
            """,
            document_id,
            content,
        )
    except Exception:
        # Best-effort rollback: remove orphaned document row
        await db.execute(
            "DELETE FROM free_will.project_documents WHERE document_id = $1",
            document_id,
        )
        logger.exception("Failed to insert blob for document %s", document_id)
        raise HTTPException(
            status_code=500, detail="Failed to store document bytes"
        ) from None

    # Queue extraction as background task (returns 201 immediately)
    background_tasks.add_task(_extract_and_update, document_id, db)

    return UploadDocumentResponse(
        document_id=str(document_id),
        filename=str(doc_row["filename"]),
        content_type=doc_row.get("content_type"),
        size_bytes=doc_row.get("size_bytes"),
        page_count=doc_row.get("page_count"),
        status=str(doc_row["status"]),
        created_at=_fmt_ts(doc_row["created_at"]),
    )


@router.get("/{project_id}/documents", response_model=dict[str, list[DocumentSummary]])
async def list_project_documents(
    project_id: uuid.UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, list[DocumentSummary]]:
    """List documents for a project (no bytes, no extracted text)."""
    user = await get_current_user(request, db)
    await _own_project(project_id, user["user_id"], db)

    rows = await db.fetch(
        """
        SELECT document_id, filename, content_type, size_bytes,
               page_count, status, created_at
        FROM free_will.project_documents
        WHERE project_id = $1
        ORDER BY created_at DESC
        """,
        project_id,
    )
    return {"documents": [_doc_summary(dict(r)) for r in rows]}


__all__ = ["router"]
