"""Authenticated answer-feedback capture and admin JSONL export.

Feedback bodies are never written to application logs. PostgreSQL is the sole
durable sink; responses contain only the row that was just stored or the
caller's own current rating.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.dependencies import get_db
from backend.routes.auth import get_current_user
from backend.services.auth_service import normalize_email
from backend.services.rate_limit import SlidingWindowLimiter

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

COMMENT_MAX_LENGTH = 4_000
REPORT_MAX_LENGTH = 8_000
EXCERPT_MAX_LENGTH = 2_000
PROVENANCE_LABEL_MAX_LENGTH = 128

_feedback_limiter = SlidingWindowLimiter(
    max_requests=max(1, int(os.getenv("FEEDBACK_RATE_LIMIT_MAX", "12"))),
    window_seconds=max(
        1.0, float(os.getenv("FEEDBACK_RATE_LIMIT_WINDOW_SECONDS", "60"))
    ),
    max_keys=max(100, int(os.getenv("FEEDBACK_RATE_LIMIT_MAX_KEYS", "10000"))),
)


class ReportType(StrEnum):
    factual_error = "factual_error"
    wrong_citation = "wrong_citation"
    missing_source = "missing_source"
    ui_issue = "ui_issue"
    improvement = "improvement"
    other = "other"


class FeedbackBody(BaseModel):
    trace_id: uuid.UUID
    rating: int | None = Field(default=None, strict=True, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=COMMENT_MAX_LENGTH)
    app_commit: str | None = Field(
        default=None, max_length=PROVENANCE_LABEL_MAX_LENGTH
    )
    model: str | None = Field(default=None, max_length=PROVENANCE_LABEL_MAX_LENGTH)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("comment must not be blank")
        return cleaned

    @field_validator("app_commit", "model")
    @classmethod
    def normalize_provenance_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def require_content(self) -> FeedbackBody:
        if self.rating is None and self.comment is None:
            raise ValueError("rating or comment is required")
        return self


class ReportBody(BaseModel):
    trace_id: uuid.UUID
    report_type: ReportType
    report_text: str = Field(min_length=1, max_length=REPORT_MAX_LENGTH)
    answer_excerpt: str | None = Field(default=None, max_length=EXCERPT_MAX_LENGTH)
    app_commit: str | None = Field(
        default=None, max_length=PROVENANCE_LABEL_MAX_LENGTH
    )
    model: str | None = Field(default=None, max_length=PROVENANCE_LABEL_MAX_LENGTH)

    @field_validator("report_text")
    @classmethod
    def validate_report_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("report_text must not be blank")
        return cleaned

    @field_validator("answer_excerpt", "app_commit", "model")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class FeedbackRecord(BaseModel):
    id: uuid.UUID
    trace_id: uuid.UUID | None
    rating: int | None
    comment: str | None
    report_type: ReportType | None
    report_text: str | None
    answer_excerpt: str | None
    app_commit: str | None
    model: str | None
    created_at: datetime


class MineResponse(BaseModel):
    trace_id: uuid.UUID
    rating: int | None
    comment: str | None


def _rate_key(email: str, trace_id: uuid.UUID) -> str:
    return f"{normalize_email(email)}:{trace_id}"


def _admit_feedback(email: str, trace_id: uuid.UUID) -> None:
    key = _rate_key(email, trace_id)
    if not _feedback_limiter.admit(key):
        raise HTTPException(
            status_code=429,
            detail="Too many feedback submissions for this answer. Please retry later.",
            headers={"Retry-After": str(_feedback_limiter.retry_after(key))},
        )


def _record_from_row(row: dict[str, Any]) -> FeedbackRecord:
    return FeedbackRecord.model_validate(row)


@router.post("", response_model=FeedbackRecord)
async def submit_feedback(
    body: FeedbackBody,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> FeedbackRecord:
    """Store a rating/impression; rating-bearing rows are owner-upserted."""
    email = normalize_email(str(current_user["email"]))
    _admit_feedback(email, body.trace_id)

    if body.rating is not None:
        row = await db.fetchrow(
            """
            INSERT INTO free_will.answer_feedback (
                trace_id, user_email, rating, comment, app_commit, model
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (trace_id, user_email)
                WHERE rating IS NOT NULL AND report_type IS NULL
            DO UPDATE SET
                rating = EXCLUDED.rating,
                comment = COALESCE(EXCLUDED.comment, answer_feedback.comment),
                app_commit = COALESCE(EXCLUDED.app_commit, answer_feedback.app_commit),
                model = COALESCE(EXCLUDED.model, answer_feedback.model)
            RETURNING
                id, trace_id, rating, comment, report_type, report_text,
                answer_excerpt, app_commit, model, created_at
            """,
            body.trace_id,
            email,
            body.rating,
            body.comment,
            body.app_commit,
            body.model,
        )
    else:
        row = await db.fetchrow(
            """
            INSERT INTO free_will.answer_feedback (
                trace_id, user_email, comment, app_commit, model
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING
                id, trace_id, rating, comment, report_type, report_text,
                answer_excerpt, app_commit, model, created_at
            """,
            body.trace_id,
            email,
            body.comment,
            body.app_commit,
            body.model,
        )

    if row is None:
        raise HTTPException(status_code=500, detail="Feedback could not be stored")
    return _record_from_row(row)


@router.post("/report", response_model=FeedbackRecord)
async def submit_report(
    body: ReportBody,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> FeedbackRecord:
    """Append a typed error or improvement report."""
    email = normalize_email(str(current_user["email"]))
    _admit_feedback(email, body.trace_id)

    row = await db.fetchrow(
        """
        INSERT INTO free_will.answer_feedback (
            trace_id, user_email, report_type, report_text,
            answer_excerpt, app_commit, model
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING
            id, trace_id, rating, comment, report_type, report_text,
            answer_excerpt, app_commit, model, created_at
        """,
        body.trace_id,
        email,
        body.report_type.value,
        body.report_text,
        body.answer_excerpt,
        body.app_commit,
        body.model,
    )
    if row is None:
        raise HTTPException(status_code=500, detail="Report could not be stored")
    return _record_from_row(row)


@router.get("/mine", response_model=MineResponse)
async def get_my_feedback(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[DatabaseService, Depends(get_db)],
    trace_id: Annotated[uuid.UUID, Query()],
) -> MineResponse:
    """Return the caller's current rating and latest long-form impression."""
    email = normalize_email(str(current_user["email"]))
    rating_row = await db.fetchrow(
        """
        SELECT rating
        FROM free_will.answer_feedback
        WHERE trace_id = $1 AND user_email = $2
          AND rating IS NOT NULL AND report_type IS NULL
        ORDER BY created_at DESC
        LIMIT 1
        """,
        trace_id,
        email,
    )
    comment_row = await db.fetchrow(
        """
        SELECT comment
        FROM free_will.answer_feedback
        WHERE trace_id = $1 AND user_email = $2
          AND comment IS NOT NULL AND report_type IS NULL
        ORDER BY created_at DESC
        LIMIT 1
        """,
        trace_id,
        email,
    )
    return MineResponse(
        trace_id=trace_id,
        rating=int(rating_row["rating"]) if rating_row else None,
        comment=str(comment_row["comment"]) if comment_row else None,
    )


def _jsonl_rows(rows: list[dict[str, Any]]) -> Iterator[str]:
    for row in rows:
        payload = jsonable_encoder(dict(row))
        yield json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


@router.get("/export")
async def export_feedback(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[DatabaseService, Depends(get_db)],
) -> StreamingResponse:
    """Stream every feedback row as JSONL to an authenticated administrator."""
    if str(current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    rows = await db.fetch(
        """
        SELECT
            id, trace_id, user_email, rating, comment, report_type,
            report_text, answer_excerpt, app_commit, model, created_at
        FROM free_will.answer_feedback
        ORDER BY created_at ASC, id ASC
        """
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return StreamingResponse(
        _jsonl_rows(rows),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": (
                f'attachment; filename="eleutheria-answer-feedback-{stamp}.jsonl"'
            )
        },
    )
