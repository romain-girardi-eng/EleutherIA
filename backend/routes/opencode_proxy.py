"""opencode proxy routes.

The browser frontend talks to opencode through these routes so the
`OPENCODE_SERVER_PASSWORD` HTTP Basic credential never transits client-side.

Four endpoints:

| Verb  | Path                                          | Auth              | Purpose                                   |
|-------|-----------------------------------------------|-------------------|-------------------------------------------|
| POST  | /api/opencode/session                         | JWT (Bearer)      | Create a session, return SSE token       |
| POST  | /api/opencode/session/{id}/prompt             | JWT (Bearer)      | Queue a prompt on an existing session    |
| GET   | /api/opencode/event                           | Session JWT (qs)  | Long-poll SSE proxy, filters by session  |
| POST  | /api/opencode/session/{id}/abort              | JWT (Bearer)      | Abort a running session                  |

`GET /api/opencode/event` cannot rely on `Authorization` headers because
browser SSE polyfills built on top of `fetch` cannot append them through
`EventSource`, and our hook uses a streaming `fetch` to keep things uniform.
Instead the session-create response includes an `sse_token` (10-minute JWT
bound to the user + session_id pair) that the client passes as `?token=...`.

The upstream opencode SSE channel is GLOBAL — events for every active
session land on the same stream. This proxy filters by
`properties.sessionID` and forwards a 15-second heartbeat so the
Cloudflare tunnel does not idle-close the connection.

Reference: docs/plans/2026-05-14-opencode-event-protocol.md
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime
from typing import Annotated, Any

import httpx
import jwt
from eleutheria_database.services.db import DatabaseService
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.dependencies import get_db
from backend.integrations.opencode import (
    OpencodeSettings,
    basic_auth,
    get_opencode_settings,
    make_session_token,
    verify_session_token,
)
from backend.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["opencode"])


# ---------- Constants ----------

ALLOWED_AGENTS = frozenset({"scholar-orchestrator", "concept-mapper", "source-finder"})
ALLOWED_MODES = frozenset({"fast", "deep"})
HEARTBEAT_INTERVAL_SECONDS = 15.0


# ---------- Request / response models ----------


class CreateSessionRequest(BaseModel):
    agent: str = Field(..., description="opencode agent slug")
    title: str | None = Field(None, max_length=200)


class CreateSessionResponse(BaseModel):
    session_id: str
    agent: str
    sse_token: str


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    mode: str | None = Field(None, description="fast | deep")


class PromptResponse(BaseModel):
    trace_id: str
    started_at: str


class AbortResponse(BaseModel):
    aborted: bool


# ---------- HTTP client factory ----------


def _build_client(settings: OpencodeSettings) -> httpx.AsyncClient:
    """Construct an httpx client preconfigured for the upstream opencode."""
    return httpx.AsyncClient(
        base_url=settings.opencode_base_url,
        auth=basic_auth(),
        timeout=httpx.Timeout(settings.opencode_proxy_timeout, connect=10.0),
    )


# Test seam — overridden in unit tests so they don't open real sockets.
_client_factory = _build_client


def set_client_factory(factory: Any) -> None:
    """Replace the upstream client factory (test seam)."""
    global _client_factory
    _client_factory = factory


def reset_client_factory() -> None:
    """Restore the production client factory."""
    global _client_factory
    _client_factory = _build_client


# ---------- Helpers ----------


def _ensure_configured() -> OpencodeSettings:
    settings = get_opencode_settings()
    if not settings.opencode_server_password:
        raise HTTPException(
            status_code=503,
            detail="opencode proxy is not configured (OPENCODE_SERVER_PASSWORD missing)",
        )
    return settings


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


# ---------- Routes ----------


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(
    body: CreateSessionRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> CreateSessionResponse:
    """Create an opencode session and mint a short-lived SSE token."""
    user = await get_current_user(request, db)
    if body.agent not in ALLOWED_AGENTS:
        raise HTTPException(status_code=400, detail=f"unknown agent: {body.agent}")
    settings = _ensure_configured()

    payload: dict[str, Any] = {"agent": body.agent}
    if body.title:
        payload["title"] = body.title

    async with _client_factory(settings) as client:
        try:
            upstream = await client.post("/session", json=payload)
        except httpx.HTTPError as exc:
            logger.exception("opencode session create failed")
            raise HTTPException(status_code=502, detail="opencode_unreachable") from exc

    if upstream.status_code >= 400:
        logger.warning(
            "opencode session create returned %s: %s",
            upstream.status_code,
            upstream.text[:200],
        )
        raise HTTPException(
            status_code=502,
            detail=f"opencode_upstream_status_{upstream.status_code}",
        )

    body_json = upstream.json()
    session_id = (
        body_json.get("session_id") or body_json.get("sessionID") or body_json.get("id")
    )
    if not session_id:
        raise HTTPException(status_code=502, detail="opencode returned no session id")

    sse_token = make_session_token(user_id=user["user_id"], session_id=session_id)
    return CreateSessionResponse(
        session_id=session_id, agent=body.agent, sse_token=sse_token
    )


@router.post("/session/{session_id}/prompt", response_model=PromptResponse)
async def submit_prompt(
    session_id: str,
    body: PromptRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> PromptResponse:
    """Queue a prompt against an existing opencode session (async / fire-and-forget)."""
    await get_current_user(request, db)
    if body.mode is not None and body.mode not in ALLOWED_MODES:
        raise HTTPException(status_code=400, detail=f"unknown mode: {body.mode}")
    settings = _ensure_configured()

    upstream_payload: dict[str, Any] = {"prompt": body.prompt}
    if body.mode:
        upstream_payload["mode"] = body.mode

    async with _client_factory(settings) as client:
        try:
            upstream = await client.post(
                f"/session/{session_id}/prompt_async",
                json=upstream_payload,
            )
        except httpx.HTTPError as exc:
            logger.exception("opencode prompt failed for %s", session_id)
            raise HTTPException(status_code=502, detail="opencode_unreachable") from exc

    if upstream.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"opencode_upstream_status_{upstream.status_code}",
        )

    return PromptResponse(trace_id=session_id, started_at=_now_iso())


@router.post("/session/{session_id}/abort", response_model=AbortResponse)
async def abort_session(
    session_id: str,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
) -> AbortResponse:
    """Abort an in-flight opencode session."""
    await get_current_user(request, db)
    settings = _ensure_configured()

    async with _client_factory(settings) as client:
        try:
            upstream = await client.post(f"/session/{session_id}/abort")
        except httpx.HTTPError as exc:
            logger.exception("opencode abort failed for %s", session_id)
            raise HTTPException(status_code=502, detail="opencode_unreachable") from exc

    # opencode returns 200 on abort; treat 404 (session already gone) as success.
    if upstream.status_code >= 400 and upstream.status_code != 404:
        raise HTTPException(
            status_code=502,
            detail=f"opencode_upstream_status_{upstream.status_code}",
        )
    return AbortResponse(aborted=True)


# ---------- SSE proxy ----------


def _session_id_of(envelope: dict[str, Any]) -> str | None:
    props = envelope.get("properties")
    if not isinstance(props, dict):
        return None
    sid = props.get("sessionID") or props.get("sessionId") or props.get("session_id")
    return sid if isinstance(sid, str) else None


async def _proxy_event_stream(
    session_id: str,
    last_event_id: str | None,
    settings: OpencodeSettings,
) -> Any:
    """Async generator yielding filtered SSE bytes from upstream opencode.

    Runs a single consumer task that reads lines from the upstream stream and
    pushes them onto a queue. The outer loop reads from the queue with a
    timeout so we can emit a `: heartbeat` comment whenever the upstream is
    idle for more than `HEARTBEAT_INTERVAL_SECONDS`. This keeps the
    Cloudflare tunnel alive between long-running opencode tool calls.
    """
    headers: dict[str, str] = {"Accept": "text/event-stream"}
    if last_event_id:
        headers["Last-Event-ID"] = last_event_id

    client = _client_factory(settings)
    try:
        async with client:
            try:
                async with client.stream(
                    "GET",
                    "/event",
                    headers=headers,
                    timeout=httpx.Timeout(None, connect=10.0, read=None, write=10.0),
                ) as upstream:
                    if upstream.status_code >= 400:
                        msg = {
                            "type": "error",
                            "properties": {
                                "message": f"upstream_status_{upstream.status_code}",
                            },
                        }
                        yield f"data: {json.dumps(msg)}\n\n".encode()
                        return

                    yield b": connected\n\n"

                    queue: asyncio.Queue[str | None] = asyncio.Queue()

                    async def pump() -> None:
                        try:
                            async for raw_line in upstream.aiter_lines():
                                await queue.put(raw_line or "")
                        finally:
                            await queue.put(None)

                    pump_task = asyncio.create_task(pump())
                    event_buffer: list[str] = []
                    current_id: str | None = None
                    try:
                        while True:
                            try:
                                line = await asyncio.wait_for(
                                    queue.get(), timeout=HEARTBEAT_INTERVAL_SECONDS
                                )
                            except TimeoutError:
                                yield b": heartbeat\n\n"
                                continue
                            if line is None:
                                # Upstream closed.
                                break
                            if line == "":
                                if event_buffer:
                                    event_text = "\n".join(event_buffer)
                                    data_lines = [
                                        ln[5:].lstrip()
                                        for ln in event_buffer
                                        if ln.startswith("data:")
                                    ]
                                    data_blob = "".join(data_lines).strip()
                                    emit = True
                                    if data_blob:
                                        try:
                                            parsed = json.loads(data_blob)
                                        except json.JSONDecodeError:
                                            parsed = None
                                        if isinstance(parsed, dict):
                                            envelope_sid = _session_id_of(parsed)
                                            evt_type = parsed.get("type", "")
                                            # Server-level events (heartbeat /
                                            # connected / disconnected) carry no
                                            # sessionID — forward them so the
                                            # client knows the stream is alive.
                                            if envelope_sid is None:
                                                emit = evt_type.startswith("server.")
                                            else:
                                                emit = envelope_sid == session_id
                                    if emit:
                                        payload = event_text + "\n\n"
                                        if current_id:
                                            payload = f"id: {current_id}\n" + payload
                                        yield payload.encode()
                                event_buffer = []
                                current_id = None
                                continue
                            if line.startswith("id:"):
                                current_id = line[3:].strip()
                            event_buffer.append(line)
                    finally:
                        pump_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError, Exception):
                            await pump_task
            except httpx.HTTPError as exc:
                logger.warning("opencode SSE upstream error: %s", exc)
                err = {"type": "error", "properties": {"message": "upstream_error"}}
                yield f"data: {json.dumps(err)}\n\n".encode()
    except asyncio.CancelledError:
        logger.info("opencode SSE proxy cancelled (client disconnect)")
        raise


@router.get("/event")
async def event_stream(
    request: Request,
    session_id: Annotated[str, Query(..., min_length=1)],
    token: Annotated[str, Query(..., min_length=1)],
) -> StreamingResponse:
    """Proxy opencode's global SSE stream filtered to one session_id.

    Auth is via a short-lived JWT in the `token` query parameter — see
    `make_session_token` in `backend.integrations.opencode`. The token is
    issued by `POST /api/opencode/session` and expires in 10 minutes.
    """
    try:
        verify_session_token(token, expected_session_id=session_id)
    except (jwt.PyJWTError, ValueError) as exc:
        logger.debug("opencode SSE token rejected: %s", exc)
        raise HTTPException(status_code=401, detail="invalid_session_token") from None

    settings = _ensure_configured()
    last_event_id = request.headers.get("Last-Event-ID")

    return StreamingResponse(
        _proxy_event_stream(session_id, last_event_id, settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
