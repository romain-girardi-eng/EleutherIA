"""
Authentication service — JWT tokens, password hashing, rate limiting.
"""

import logging
import os
import secrets
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

# Password hashing — use bcrypt directly (passlib has compatibility issues with bcrypt >= 4.1)
import bcrypt as _bcrypt
import jwt
from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

# JWT config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "168"))  # 7 days

# Rate limiting (in-memory sliding window)
_rate_windows: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_hours: int | None = None) -> str:
    """Create a signed JWT token."""
    expire = datetime.now(UTC) + timedelta(hours=expires_hours or JWT_EXPIRATION_HOURS)
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
        if isinstance(locked, datetime) and locked > datetime.now(UTC):
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
            lock_until = datetime.now(UTC) + timedelta(minutes=15)
        await db.execute(
            """
            UPDATE free_will.users
            SET failed_login_attempts = $1, locked_until = $2
            WHERE user_id = $3
            """,
            attempts,
            lock_until,
            user["user_id"],
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


def check_rate_limit(
    key: str,
    *,
    limit: int = RATE_LIMIT_MAX,
    window: int = RATE_LIMIT_WINDOW,
) -> dict[str, Any]:
    """
    Check sliding-window rate limit for a key (user or IP).

    Returns dict with limit, remaining, reset info.
    """
    now = time.time()
    window_start = now - window

    # Clean old entries
    _rate_windows[key] = [ts for ts in _rate_windows[key] if ts > window_start]

    remaining = max(0, limit - len(_rate_windows[key]))
    reset = (
        max(0, int(_rate_windows[key][0] + window - now))
        if _rate_windows[key]
        else 0
    )

    return {
        "limit": limit,
        "remaining": remaining,
        "reset": reset,
        "window": window,
    }


def record_request(key: str) -> None:
    """Record a request for rate limiting."""
    _rate_windows[key].append(time.time())


# ---------------------------------------------------------------------------
# Email one-time-code (OTP) login
# ---------------------------------------------------------------------------

# Legacy bootstrap allowlist. Runtime access is authoritative in
# ``free_will.users``: an active row may sign in, and deactivation takes effect
# on every authenticated request without an API restart.
_DEFAULT_AUTHORIZED = "romain-girardi@hotmail.fr"

LOGIN_CODE_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))
LOGIN_CODE_LENGTH = 6
LOGIN_CODE_MAX_ATTEMPTS = 5
LOGIN_CODE_RESEND_COOLDOWN_SECONDS = int(os.getenv("LOGIN_CODE_RESEND_COOLDOWN", "60"))


def normalize_email(email: str) -> str:
    """Canonical form used for every comparison and lookup."""
    return (email or "").strip().lower()


def authorized_emails() -> set[str]:
    """The current allowlist, read from AUTHORIZED_EMAILS at call time."""
    raw = os.getenv("AUTHORIZED_EMAILS", _DEFAULT_AUTHORIZED)
    return {normalize_email(part) for part in raw.split(",") if part.strip()}


def is_email_authorized(email: str) -> bool:
    """True if ``email`` is on the allowlist."""
    return normalize_email(email) in authorized_emails()


def generate_login_code() -> str:
    """A cryptographically-random numeric code, left-padded to fixed length."""
    upper = 10**LOGIN_CODE_LENGTH
    return str(secrets.randbelow(upper)).zfill(LOGIN_CODE_LENGTH)


async def get_active_user_by_email(
    db: DatabaseService, email: str
) -> dict[str, Any] | None:
    """Return the active user row for ``email`` (case-insensitive), or None."""
    user = await db.fetchrow(
        """
        SELECT user_id, username, email, role, is_active
        FROM free_will.users
        WHERE lower(email) = $1 AND is_active = TRUE
        """,
        normalize_email(email),
    )
    return dict(user) if user else None


async def issue_login_code(db: DatabaseService, email: str) -> str | None:
    """Create and store a fresh login code for ``email``; return the plaintext.

    Returns None when a code was issued within the resend cooldown (caller
    should stay silent about it). Old codes for the email are invalidated so
    only the newest is ever valid.
    """
    normalized = normalize_email(email)

    recent = await db.fetchrow(
        """
        SELECT created_at FROM free_will.login_codes
        WHERE lower(email) = $1 AND consumed_at IS NULL
        ORDER BY created_at DESC LIMIT 1
        """,
        normalized,
    )
    if recent and recent.get("created_at"):
        age = (datetime.now(UTC) - recent["created_at"]).total_seconds()
        if age < LOGIN_CODE_RESEND_COOLDOWN_SECONDS:
            return None

    # Opportunistic prune + invalidate any outstanding codes for this email.
    await db.execute(
        """
        DELETE FROM free_will.login_codes
        WHERE lower(email) = $1 OR expires_at < now()
        """,
        normalized,
    )

    code = generate_login_code()
    expires_at = datetime.now(UTC) + timedelta(minutes=LOGIN_CODE_TTL_MINUTES)
    await db.execute(
        """
        INSERT INTO free_will.login_codes (email, code_hash, expires_at)
        VALUES ($1, $2, $3)
        """,
        normalized,
        hash_password(code),
        expires_at,
    )
    return code


async def verify_login_code(
    db: DatabaseService, email: str, code: str
) -> dict[str, Any] | None:
    """Validate ``code`` for ``email`` and return the active user row, or None.

    Fails closed: wrong/expired/consumed codes and over-limit attempts all
    return None. A correct code is consumed (single-use) on success.
    """
    normalized = normalize_email(email)
    row = await db.fetchrow(
        """
        SELECT code_id, code_hash, attempts, expires_at
        FROM free_will.login_codes
        WHERE lower(email) = $1 AND consumed_at IS NULL
        ORDER BY created_at DESC LIMIT 1
        """,
        normalized,
    )
    if not row:
        return None

    expires_at = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return None
    if (row.get("attempts") or 0) >= LOGIN_CODE_MAX_ATTEMPTS:
        return None

    if not verify_password(code or "", row["code_hash"]):
        await db.execute(
            "UPDATE free_will.login_codes SET attempts = attempts + 1 WHERE code_id = $1",
            row["code_id"],
        )
        return None

    await db.execute(
        "UPDATE free_will.login_codes SET consumed_at = now() WHERE code_id = $1",
        row["code_id"],
    )
    user = await get_active_user_by_email(db, normalized)
    if user is None:
        return None

    # A consumed code is a successful login: record it on the user row so
    # ``last_login_at`` reflects the passwordless path too, not only the
    # legacy password path in ``authenticate_user``.
    await db.execute(
        """
        UPDATE free_will.users
        SET failed_login_attempts = 0, locked_until = NULL,
            last_login_at = now()
        WHERE user_id = $1
        """,
        user["user_id"],
    )
    return user
