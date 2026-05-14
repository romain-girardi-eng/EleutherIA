"""opencode upstream integration.

Configuration + a small token helper used by `backend.routes.opencode_proxy`
to drive the opencode runtime exposed at `OPENCODE_BASE_URL`.

The browser never sees `OPENCODE_SERVER_PASSWORD` — the backend injects
HTTP Basic credentials when forwarding session / prompt / SSE / abort
requests. Server-Sent Event streams cannot easily set an `Authorization`
header from a browser `fetch`, so the proxy issues short-lived JWTs scoped
to a specific (user, session) pair that are passed as `?token=...` on the
`GET /api/opencode/event` endpoint.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpencodeSettings(BaseSettings):
    """Settings governing the upstream opencode connection.

    All fields are read from the process environment so the backend can be
    booted with neither code change nor compose override. When the proxy
    routes are imported but `OPENCODE_SERVER_PASSWORD` is unset, requests
    fail with a 503 rather than crash at import time.
    """

    opencode_base_url: str = "http://localhost:4096"
    opencode_username: str = "opencode"
    opencode_server_password: str | None = None
    opencode_proxy_timeout: float = 1800.0
    opencode_session_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_opencode_settings() -> OpencodeSettings:
    """Return the cached opencode settings singleton."""
    return OpencodeSettings()


def reset_opencode_settings_cache() -> None:
    """Drop the cached settings — used by tests that mutate the env."""
    get_opencode_settings.cache_clear()


def _session_secret() -> str:
    """Return the symmetric key used to sign session-scoped SSE tokens.

    Prefers `OPENCODE_SESSION_SECRET`, falls back to `JWT_SECRET_KEY` so a
    single secret can be configured for both auth tokens and SSE tokens.
    """
    settings = get_opencode_settings()
    if settings.opencode_session_secret:
        return settings.opencode_session_secret
    return os.getenv("JWT_SECRET_KEY", "change-me-in-production")


def make_session_token(user_id: str, session_id: str, ttl: int = 600) -> str:
    """Mint a JWT that authorises SSE access to a specific opencode session.

    The token is only valid for `ttl` seconds (default 10 minutes) and is
    bound to a single `session_id` — replay against another session is
    rejected by `verify_session_token`.
    """
    payload: dict[str, Any] = {
        "sub": user_id,
        "session_id": session_id,
        "exp": int(time.time()) + ttl,
        "iat": int(time.time()),
        "scope": "opencode_sse",
    }
    return jwt.encode(payload, _session_secret(), algorithm="HS256")


def verify_session_token(token: str, expected_session_id: str) -> dict[str, Any]:
    """Validate an SSE token and return its payload.

    Raises:
        jwt.PyJWTError: signature / expiry failures.
        ValueError: token is for a different session.
    """
    payload = jwt.decode(token, _session_secret(), algorithms=["HS256"])
    if payload.get("session_id") != expected_session_id:
        raise ValueError("session_id_mismatch")
    if payload.get("scope") != "opencode_sse":
        raise ValueError("invalid_scope")
    return payload


def basic_auth() -> tuple[str, str]:
    """Return the HTTP Basic credentials for the upstream opencode server.

    Raises RuntimeError when `OPENCODE_SERVER_PASSWORD` is unset.
    """
    settings = get_opencode_settings()
    if not settings.opencode_server_password:
        raise RuntimeError(
            "OPENCODE_SERVER_PASSWORD is not configured — opencode proxy disabled"
        )
    return (settings.opencode_username, settings.opencode_server_password)
