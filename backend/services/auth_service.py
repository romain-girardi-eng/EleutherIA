"""
Authentication service — JWT tokens, password hashing, rate limiting.
"""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

# JWT config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "168"))  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting (in-memory sliding window)
_rate_windows: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any], expires_hours: int | None = None) -> str:
    """Create a signed JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours or JWT_EXPIRATION_HOURS)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


async def authenticate_user(
    db: DatabaseService, username: str, password: str
) -> dict[str, Any] | None:
    """
    Validate credentials and return user dict, or None.

    Also handles account locking after repeated failures.
    """
    user = await db.fetchrow(
        """
        SELECT user_id, username, email, hashed_password, role,
               is_active, failed_login_attempts, locked_until
        FROM free_will.users
        WHERE username = $1
        """,
        username,
    )

    if not user:
        return None

    # Check account lock
    if user.get("locked_until"):
        locked = user["locked_until"]
        if isinstance(locked, datetime) and locked > datetime.now(timezone.utc):
            logger.warning(f"Account locked: {username}")
            return None

    # Check active
    if not user.get("is_active", True):
        return None

    # Verify password
    if not verify_password(password, user["hashed_password"]):
        # Increment failed attempts
        attempts = (user.get("failed_login_attempts") or 0) + 1
        lock_until = None
        if attempts >= 5:
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.execute(
            """
            UPDATE free_will.users
            SET failed_login_attempts = $1, locked_until = $2
            WHERE user_id = $3
            """,
            attempts, lock_until, user["user_id"],
        )
        return None

    # Success — reset failed attempts and update last login
    await db.execute(
        """
        UPDATE free_will.users
        SET failed_login_attempts = 0, locked_until = NULL,
            last_login_at = now()
        WHERE user_id = $1
        """,
        user["user_id"],
    )

    return {
        "user_id": str(user["user_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
    }


def check_rate_limit(key: str) -> dict[str, Any]:
    """
    Check sliding-window rate limit for a key (user or IP).

    Returns dict with limit, remaining, reset info.
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_windows[key] = [ts for ts in _rate_windows[key] if ts > window_start]

    remaining = max(0, RATE_LIMIT_MAX - len(_rate_windows[key]))
    reset = int(window_start + RATE_LIMIT_WINDOW - now)

    return {
        "limit": RATE_LIMIT_MAX,
        "remaining": remaining,
        "reset": reset,
        "window": RATE_LIMIT_WINDOW,
    }


def record_request(key: str) -> None:
    """Record a request for rate limiting."""
    _rate_windows[key].append(time.time())
