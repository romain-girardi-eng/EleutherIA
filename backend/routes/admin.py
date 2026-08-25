"""Authenticated administration of users, access requests, and LLM budgets."""

from __future__ import annotations

import json
import logging
import re
import secrets
import uuid
from decimal import Decimal
from typing import Annotated, Any, Literal

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.dependencies import get_db
from backend.routes.auth import get_current_user
from backend.services.auth_service import hash_password
from backend.services.email_service import send_account_approved_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminUserUpdate(BaseModel):
    role: Literal["admin", "researcher", "viewer"] | None = None
    is_active: bool | None = None
    monthly_token_limit: int | None = Field(None, ge=0)
    monthly_cost_limit_usd: Decimal | None = Field(None, ge=0)
    monthly_query_limit: int | None = Field(None, ge=0)
    allow_deep_mode: bool | None = None
    notes: str | None = Field(None, max_length=2000)


class ApproveAccountRequest(BaseModel):
    role: Literal["researcher", "viewer"] = "researcher"


class AdminFeedbackUpdate(BaseModel):
    status: Literal["new", "triaged", "in_progress", "resolved", "dismissed"]
    admin_notes: str | None = Field(None, max_length=4_000)


async def _require_admin(request: Request, db: DatabaseService) -> dict[str, Any]:
    user = await get_current_user(request, db)
    if str(user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _state(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "role",
        "is_active",
        "monthly_token_limit",
        "monthly_cost_limit_usd",
        "monthly_query_limit",
        "allow_deep_mode",
        "notes",
    )
    return {key: _jsonable(row.get(key)) for key in keys}


def _decode_latest_request(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, dict) else None
        except json.JSONDecodeError, TypeError:
            return None
    return None


@router.get("/users")
async def list_users(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    await _require_admin(request, db)
    rows = await db.fetch(
        """
        WITH usage AS (
            SELECT user_id,
                   count(*)::int AS lifetime_queries,
                   COALESCE(sum(total_tokens), 0)::bigint AS lifetime_tokens,
                   COALESCE(sum(total_cost_usd), 0)::double precision AS lifetime_cost_usd,
                   count(*) FILTER (WHERE started_at >= date_trunc('month', now()))::int AS month_queries,
                   COALESCE(sum(total_tokens) FILTER (WHERE started_at >= date_trunc('month', now())), 0)::bigint AS month_tokens,
                   COALESCE(sum(total_cost_usd) FILTER (WHERE started_at >= date_trunc('month', now())), 0)::double precision AS month_cost_usd,
                   max(started_at) AS last_query_at
            FROM free_will.query_traces
            GROUP BY user_id
        ), latest_request AS (
            SELECT DISTINCT ON (lower(email))
                   lower(email) AS email_key,
                   request_id, full_name, affiliation, requested_role,
                   research_focus, intended_use, locale,
                   privacy_notice_version, status, created_at
            FROM free_will.account_requests
            ORDER BY lower(email), created_at DESC
        )
        SELECT u.user_id, u.username, u.email, u.role, u.is_active,
               u.created_at, u.updated_at, u.last_login_at,
               u.failed_login_attempts, u.locked_until,
               p.monthly_token_limit,
               p.monthly_cost_limit_usd::double precision AS monthly_cost_limit_usd,
               p.monthly_query_limit, COALESCE(p.allow_deep_mode, true) AS allow_deep_mode,
               p.notes,
               COALESCE(s.lifetime_queries, 0) AS lifetime_queries,
               COALESCE(s.lifetime_tokens, 0) AS lifetime_tokens,
               COALESCE(s.lifetime_cost_usd, 0) AS lifetime_cost_usd,
               COALESCE(s.month_queries, 0) AS month_queries,
               COALESCE(s.month_tokens, 0) AS month_tokens,
               COALESCE(s.month_cost_usd, 0) AS month_cost_usd,
               s.last_query_at,
               CASE WHEN r.request_id IS NULL THEN NULL ELSE jsonb_build_object(
                   'request_id', r.request_id, 'full_name', r.full_name,
                   'affiliation', r.affiliation, 'requested_role', r.requested_role,
                   'research_focus', r.research_focus, 'intended_use', r.intended_use,
                   'locale', r.locale, 'privacy_notice_version', r.privacy_notice_version,
                   'status', r.status, 'created_at', r.created_at
               ) END AS latest_request
        FROM free_will.users u
        LEFT JOIN free_will.user_access_policies p ON p.user_id = u.user_id
        LEFT JOIN usage s ON s.user_id = u.user_id
        LEFT JOIN latest_request r ON r.email_key = lower(u.email)
        ORDER BY (u.role = 'admin') DESC, u.created_at, lower(u.email)
        """
    )
    for row in rows:
        row["latest_request"] = _decode_latest_request(row.get("latest_request"))
    totals = await db.fetchrow(
        """
        SELECT count(*)::int AS users,
               count(*) FILTER (WHERE is_active)::int AS active_users,
               count(*) FILTER (WHERE role = 'admin' AND is_active)::int AS active_admins
        FROM free_will.users
        """
    )
    usage = await db.fetchrow(
        """
        SELECT count(*)::int AS lifetime_queries,
               COALESCE(sum(total_tokens), 0)::bigint AS lifetime_tokens,
               COALESCE(sum(total_cost_usd), 0)::double precision AS lifetime_cost_usd,
               count(*) FILTER (WHERE started_at >= date_trunc('month', now()))::int AS month_queries,
               COALESCE(sum(total_tokens) FILTER (WHERE started_at >= date_trunc('month', now())), 0)::bigint AS month_tokens,
               COALESCE(sum(total_cost_usd) FILTER (WHERE started_at >= date_trunc('month', now())), 0)::double precision AS month_cost_usd,
               count(*) FILTER (WHERE user_id IS NULL)::int AS unassigned_queries,
               COALESCE(sum(total_cost_usd) FILTER (WHERE user_id IS NULL), 0)::double precision AS unassigned_cost_usd
        FROM free_will.query_traces
        """
    )
    return {"users": rows, "summary": {**(totals or {}), **(usage or {})}}


@router.get("/account-requests")
async def list_account_requests(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    await _require_admin(request, db)
    rows = await db.fetch(
        """
        SELECT request_id, full_name, email, affiliation, requested_role,
               research_focus, intended_use, locale, privacy_notice_version,
               status, reviewer_notification_status, reviewer_notified_at,
               approval_email_status, approval_email_sent_at,
               approved_user_id, reviewed_at, decision_notes, created_at
        FROM free_will.account_requests
        ORDER BY (status = 'pending') DESC, created_at DESC
        """
    )
    return {"requests": rows}


@router.get("/feedback")
async def list_feedback(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    await _require_admin(request, db)
    rows = await db.fetch(
        """
        SELECT f.id, f.trace_id, f.user_id, f.user_email, u.username,
               f.rating, f.comment, f.report_type, f.report_text,
               f.answer_excerpt, f.scope, f.severity, f.page_url, f.entity_id,
               f.contact_allowed, f.status, f.admin_notes, f.assigned_to,
               f.app_commit, f.model, f.created_at, f.updated_at, f.resolved_at
        FROM free_will.answer_feedback f
        LEFT JOIN free_will.users u ON u.user_id=f.user_id
        ORDER BY
          CASE f.status WHEN 'new' THEN 0 WHEN 'triaged' THEN 1
                        WHEN 'in_progress' THEN 2 ELSE 3 END,
          CASE f.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                          WHEN 'normal' THEN 2 ELSE 3 END,
          f.created_at DESC
        """
    )
    counts = await db.fetchrow(
        """
        SELECT count(*)::int AS total,
               count(*) FILTER (WHERE status='new')::int AS new,
               count(*) FILTER (WHERE status='in_progress')::int AS in_progress,
               count(*) FILTER (WHERE status='resolved')::int AS resolved
        FROM free_will.answer_feedback
        """
    )
    return {"feedback": rows, "summary": counts or {}}


@router.patch("/feedback/{feedback_id}")
async def update_feedback(
    feedback_id: uuid.UUID,
    body: AdminFeedbackUpdate,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    actor = await _require_admin(request, db)
    row = await db.fetchrow(
        """
        UPDATE free_will.answer_feedback
        SET status=$2, admin_notes=$3,
            assigned_to=CASE WHEN $2 IN ('triaged','in_progress') THEN $4 ELSE assigned_to END,
            resolved_at=CASE WHEN $2='resolved' THEN now() ELSE NULL END,
            updated_at=now()
        WHERE id=$1
        RETURNING id,status,admin_notes,assigned_to,resolved_at,updated_at
        """,
        feedback_id,
        body.status,
        body.admin_notes.strip() if body.admin_notes else None,
        uuid.UUID(str(actor["user_id"])),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return row


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: AdminUserUpdate,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    actor = await _require_admin(request, db)
    async with db.connection() as conn, conn.transaction():
        row = await conn.fetchrow(
            """
                SELECT u.user_id, u.role, u.is_active,
                       p.monthly_token_limit, p.monthly_cost_limit_usd,
                       p.monthly_query_limit, COALESCE(p.allow_deep_mode, true) AS allow_deep_mode,
                       p.notes
                FROM free_will.users u
                LEFT JOIN free_will.user_access_policies p ON p.user_id=u.user_id
                WHERE u.user_id=$1 FOR UPDATE OF u
                """,
            user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        before = dict(row)
        fields = body.model_fields_set
        next_role = body.role if "role" in fields else before["role"]
        next_active = body.is_active if "is_active" in fields else before["is_active"]
        if str(actor["user_id"]) == str(user_id) and (
            next_role != "admin" or not next_active
        ):
            raise HTTPException(
                status_code=409,
                detail="You cannot remove your own active admin access",
            )
        if (
            before["role"] == "admin"
            and before["is_active"]
            and (next_role != "admin" or not next_active)
        ):
            admins = await conn.fetchval(
                "SELECT count(*) FROM free_will.users WHERE role='admin' AND is_active"
            )
            if int(admins or 0) <= 1:
                raise HTTPException(
                    status_code=409, detail="At least one active admin is required"
                )

        await conn.execute(
            "UPDATE free_will.users SET role=$2, is_active=$3, updated_at=now() WHERE user_id=$1",
            user_id,
            next_role,
            next_active,
        )
        policy = {
            "monthly_token_limit": body.monthly_token_limit
            if "monthly_token_limit" in fields
            else before["monthly_token_limit"],
            "monthly_cost_limit_usd": body.monthly_cost_limit_usd
            if "monthly_cost_limit_usd" in fields
            else before["monthly_cost_limit_usd"],
            "monthly_query_limit": body.monthly_query_limit
            if "monthly_query_limit" in fields
            else before["monthly_query_limit"],
            "allow_deep_mode": body.allow_deep_mode
            if "allow_deep_mode" in fields
            else before["allow_deep_mode"],
            "notes": body.notes if "notes" in fields else before["notes"],
        }
        await conn.execute(
            """
                INSERT INTO free_will.user_access_policies (
                    user_id, monthly_token_limit, monthly_cost_limit_usd,
                    monthly_query_limit, allow_deep_mode, notes, updated_by
                ) VALUES ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (user_id) DO UPDATE SET
                    monthly_token_limit=EXCLUDED.monthly_token_limit,
                    monthly_cost_limit_usd=EXCLUDED.monthly_cost_limit_usd,
                    monthly_query_limit=EXCLUDED.monthly_query_limit,
                    allow_deep_mode=EXCLUDED.allow_deep_mode,
                    notes=EXCLUDED.notes, updated_by=EXCLUDED.updated_by,
                    updated_at=now()
                """,
            user_id,
            policy["monthly_token_limit"],
            policy["monthly_cost_limit_usd"],
            policy["monthly_query_limit"],
            policy["allow_deep_mode"],
            policy["notes"],
            uuid.UUID(str(actor["user_id"])),
        )
        after = {"role": next_role, "is_active": next_active, **policy}
        action = (
            "role_changed"
            if next_role != before["role"]
            else "activation_changed"
            if next_active != before["is_active"]
            else "limits_changed"
        )
        await conn.execute(
            """
                INSERT INTO free_will.user_admin_actions (
                    actor_user_id,target_user_id,action,before_state,after_state
                ) VALUES ($1,$2,$3,$4::jsonb,$5::jsonb)
                """,
            uuid.UUID(str(actor["user_id"])),
            user_id,
            action,
            json.dumps(_state(before)),
            json.dumps({key: _jsonable(value) for key, value in after.items()}),
        )
    return {"user_id": str(user_id), "updated": True}


def _username_seed(full_name: str, email: str) -> str:
    source = full_name.strip().lower().replace(" ", ".") or email.split("@", 1)[0]
    seed = re.sub(r"[^a-z0-9._-]+", "", source)[:42].strip("._-")
    return seed if len(seed) >= 3 else f"scholar-{secrets.token_hex(3)}"


@router.post("/account-requests/{request_id}/approve")
async def approve_account_request(
    request_id: str,
    body: ApproveAccountRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    actor = await _require_admin(request, db)
    async with db.connection() as conn, conn.transaction():
        account_request = await conn.fetchrow(
            "SELECT * FROM free_will.account_requests WHERE request_id=$1 FOR UPDATE",
            request_id,
        )
        if not account_request:
            raise HTTPException(status_code=404, detail="Account request not found")
        if account_request["status"] not in {"pending", "approved"}:
            raise HTTPException(status_code=409, detail="Request is not approvable")
        existing = await conn.fetchrow(
            "SELECT user_id FROM free_will.users WHERE lower(email)=lower($1)",
            account_request["email"],
        )
        if existing:
            user_id = existing["user_id"]
            await conn.execute(
                "UPDATE free_will.users SET role=$2,is_active=true,updated_at=now() WHERE user_id=$1",
                user_id,
                body.role,
            )
        else:
            seed = _username_seed(
                account_request["full_name"], account_request["email"]
            )
            username = seed
            suffix = 1
            while await conn.fetchval(
                "SELECT 1 FROM free_will.users WHERE username=$1", username
            ):
                suffix += 1
                username = f"{seed[:44]}-{suffix}"
            user_id = await conn.fetchval(
                """
                    INSERT INTO free_will.users (
                        username,email,hashed_password,role,is_active
                    ) VALUES ($1,$2,$3,$4,true) RETURNING user_id
                    """,
                username,
                account_request["email"],
                hash_password(secrets.token_urlsafe(32)),
                body.role,
            )
        await conn.execute(
            """
                UPDATE free_will.account_requests
                SET status='approved', approved_user_id=$2, reviewed_at=now(),
                    reviewed_by=$3, updated_at=now()
                WHERE request_id=$1
                """,
            request_id,
            user_id,
            uuid.UUID(str(actor["user_id"])),
        )
        await conn.execute(
            """
                INSERT INTO free_will.user_admin_actions (
                    actor_user_id,target_user_id,action,after_state
                ) VALUES ($1,$2,'account_approved',$3::jsonb)
                """,
            uuid.UUID(str(actor["user_id"])),
            user_id,
            json.dumps({"role": body.role, "request_id": request_id}),
        )

    delivered = await send_account_approved_notification(
        account_request["email"],
        account_request["full_name"],
        body.role,
        locale=account_request["locale"],
        transaction_id=request_id,
    )
    try:
        await db.execute(
            """
            UPDATE free_will.account_requests
            SET approval_email_status=$2::varchar,
                approval_email_sent_at=CASE
                    WHEN $2::varchar='sent' THEN now()
                    ELSE approval_email_sent_at
                END,
                updated_at=now()
            WHERE request_id=$1
            """,
            request_id,
            "sent" if delivered else "failed",
        )
    except Exception:
        # The account transaction has committed and the external notification
        # may already be delivered. Never report the approval itself as failed
        # merely because its delivery-status bookkeeping could not be updated.
        logger.exception("Could not persist approval email status for %s", request_id)
    return {
        "request_id": request_id,
        "user_id": str(user_id),
        "role": body.role,
        "email_delivered": delivered,
    }
