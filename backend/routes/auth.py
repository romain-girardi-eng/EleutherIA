"""
Authentication routes — login, current user, rate limit status, semativerse permissions.
"""

import logging
from typing import Annotated, Any

from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.dependencies import get_db
from backend.services.auth_service import (
    authenticate_user,
    check_rate_limit,
    create_access_token,
    decode_token,
    record_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# ---------- Models ----------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


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
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

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

@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> dict[str, Any]:
    """Authenticate user and return JWT token."""
    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    rl = check_rate_limit(f"login:{client_ip}")
    if rl["remaining"] <= 0:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    record_request(f"login:{client_ip}")

    user = await authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user["user_id"], "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 168 * 3600,  # 7 days in seconds
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
