"""
Authentication routes — passwordless email one-time-code (OTP) login,
current user, rate limit status, semativerse permissions.

Flow: POST /request-code {email} → a 6-digit code is emailed ONLY to an
authorized, active user (the response is identical either way, so the
endpoint never reveals whether an address is registered). POST /verify-code
{email, code} → exchanges a valid code for a JWT.
"""

import logging
import os
import uuid
from typing import Annotated, Any, Literal

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from backend.dependencies import get_db
from backend.services.auth_service import (
    JWT_EXPIRATION_HOURS,
    LOGIN_CODE_TTL_MINUTES,
    check_rate_limit,
    create_access_token,
    decode_token,
    get_active_user_by_email,
    issue_login_code,
    record_request,
    verify_login_code,
)
from backend.services.email_service import (
    send_account_request_notification,
    send_login_code,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

# Uniform response for /request-code — never leaks whether the email exists.
_REQUEST_CODE_MESSAGE = (
    "Si cet e-mail est autorisé, un code de connexion vient d'être envoyé."
)
_ACCOUNT_REQUEST_RATE_LIMIT = int(os.getenv("ACCOUNT_REQUEST_RATE_LIMIT", "5"))
_ACCOUNT_REQUEST_RATE_WINDOW = int(
    os.getenv("ACCOUNT_REQUEST_RATE_WINDOW", "3600")
)
_ACCOUNT_REQUEST_PRIVACY_VERSION = "2026-08-24"


# ---------- Models ----------


class RequestCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)


class AccountRequestRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[^\r\n]+$",
    )
    email: EmailStr
    affiliation: str | None = Field(None, max_length=160)
    role: Literal[
        "doctoral_researcher",
        "researcher",
        "student",
        "teacher",
        "independent_scholar",
        "other",
    ]
    research_focus: str = Field(..., min_length=20, max_length=800)
    intended_use: list[
        Literal[
            "research",
            "teaching",
            "writing",
            "data_exploration",
            "other",
        ]
    ] = Field(..., min_length=1, max_length=5)
    privacy_acknowledged: bool
    privacy_notice_version: Literal["2026-08-24"]
    locale: str = Field("en", min_length=2, max_length=12, pattern=r"^[a-zA-Z-]+$")
    # Deliberately hidden from people; populated only by unsophisticated bots.
    website: str = Field("", max_length=200)


class SemativerseCheckRequest(BaseModel):
    action: str = "view"


# ---------- Helpers ----------


async def get_current_user(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Extract and validate JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth[7:]
    try:
        payload = decode_token(token)
    except Exception:
        logger.debug("Token decode failed", exc_info=True)
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        ) from None

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.fetchrow(
        """
        SELECT user_id, username, email, role, is_active
        FROM free_will.users WHERE user_id = $1
        """,
        __import__("uuid").UUID(user_id),
    )
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Ensure user_id is a string for consistent downstream usage
    result = dict(user)
    result["user_id"] = str(result["user_id"])
    return result


# ---------- Routes ----------


@router.post("/request-code")
async def request_code(
    body: RequestCodeRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Email a one-time login code — but only to an authorized, active user.

    The response is identical whether or not the address is registered, so it
    can never be used to enumerate valid emails.
    """
    client_ip = request.client.host if request.client else "unknown"
    if check_rate_limit(f"request-code:{client_ip}")["remaining"] <= 0:
        raise HTTPException(
            status_code=429, detail="Trop de tentatives, réessayez plus tard."
        )
    record_request(f"request-code:{client_ip}")

    email = str(body.email)
    if await get_active_user_by_email(db, email):
        code = await issue_login_code(db, email)
        if code is not None:
            await send_login_code(email, code, LOGIN_CODE_TTL_MINUTES)

    return {"message": _REQUEST_CODE_MESSAGE}


@router.post("/request-account", status_code=202)
async def request_account(
    body: AccountRequestRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, str]:
    """Persist a consent-backed request and notify the human reviewer."""
    client_ip = request.client.host if request.client else "unknown"
    limit_key = f"account-request:{client_ip}"
    if check_rate_limit(
        limit_key,
        limit=_ACCOUNT_REQUEST_RATE_LIMIT,
        window=_ACCOUNT_REQUEST_RATE_WINDOW,
    )["remaining"] <= 0:
        raise HTTPException(
            status_code=429,
            detail="Too many account requests. Please try again later.",
        )
    record_request(limit_key)

    request_id = f"EAR-{uuid.uuid4().hex[:10].upper()}"

    # Honeypot submissions receive the same public response without creating
    # mail. This deters retrying bots without exposing the filter.
    if body.website.strip():
        return {
            "message": "Your account request has been received.",
            "request_id": request_id,
        }

    if not body.privacy_acknowledged:
        raise HTTPException(
            status_code=422,
            detail="The privacy information must be acknowledged.",
        )
    if body.privacy_notice_version != _ACCOUNT_REQUEST_PRIVACY_VERSION:
        raise HTTPException(status_code=422, detail="Privacy notice version mismatch.")

    request_info = body.model_dump(exclude={"website"})
    request_info["email"] = str(body.email).strip().lower()
    request_info["full_name"] = body.full_name.strip()
    request_info["affiliation"] = (
        body.affiliation.strip() if body.affiliation else None
    )
    request_info["research_focus"] = body.research_focus.strip()
    request_info["intended_use"] = list(dict.fromkeys(body.intended_use))

    await db.execute(
        """
        INSERT INTO free_will.account_requests (
            request_id, full_name, email, affiliation, requested_role,
            research_focus, intended_use, locale, privacy_acknowledged,
            privacy_notice_version
        ) VALUES ($1, $2, $3, $4, $5, $6, $7::text[], $8, $9, $10)
        """,
        request_id,
        request_info["full_name"],
        request_info["email"],
        request_info["affiliation"],
        request_info["role"],
        request_info["research_focus"],
        request_info["intended_use"],
        request_info["locale"],
        request_info["privacy_acknowledged"],
        request_info["privacy_notice_version"],
    )

    delivered = await send_account_request_notification(request_id, request_info)
    await db.execute(
        """
        UPDATE free_will.account_requests
        SET reviewer_notification_status = $2,
            reviewer_notified_at = CASE WHEN $2 = 'sent' THEN now() ELSE NULL END,
            updated_at = now()
        WHERE request_id = $1
        """,
        request_id,
        "sent" if delivered else "failed",
    )
    if not delivered:
        logger.error("Account request %s could not be delivered", request_id)
        raise HTTPException(
            status_code=503,
            detail="The request could not be delivered. Please try again later.",
        )

    return {
        "message": "Your account request has been received.",
        "request_id": request_id,
    }


@router.post("/verify-code")
async def verify_code(
    body: VerifyCodeRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Exchange a valid login code for a JWT."""
    client_ip = request.client.host if request.client else "unknown"
    if check_rate_limit(f"verify-code:{client_ip}")["remaining"] <= 0:
        raise HTTPException(
            status_code=429, detail="Trop de tentatives, réessayez plus tard."
        )
    record_request(f"verify-code:{client_ip}")

    email = str(body.email)
    user = None
    user = await verify_login_code(db, email, body.code)
    if not user:
        raise HTTPException(status_code=401, detail="Code invalide ou expiré.")

    token = create_access_token({"sub": str(user["user_id"]), "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
    }


@router.get("/me")
async def me(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Get current authenticated user info."""
    user = await get_current_user(request, db)
    return {
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
    }


@router.get("/rate-limit")
async def rate_limit_status(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Get current rate limit status for the authenticated user."""
    user = await get_current_user(request, db)
    client_ip = request.client.host if request.client else "unknown"

    return {
        "user": user["username"],
        "ip": client_ip,
        "rate_limit": check_rate_limit(f"api:{user['username']}"),
    }


@router.post("/semativerse/check")
async def semativerse_check(
    body: SemativerseCheckRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Check if user has permission for Semativerse features."""
    user = await get_current_user(request, db)
    # All authenticated users can access semativerse
    return {
        "allowed": True,
        "reason": "authenticated",
        "user": user["username"],
        "role": user["role"],
    }


@router.get("/semativerse/status")
async def semativerse_status() -> dict[str, Any]:
    """Get Semativerse feature status (public endpoint)."""
    return {
        "enabled": True,
        "requires_auth": True,
        "features": ["3d_visualization", "semantic_space", "embedding_journey"],
    }
