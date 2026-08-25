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
import time
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
from backend.services.trace_writer import TraceWriter
from backend.services.usage_limits import enforce_user_usage_limits

logger = logging.getLogger(__name__)

router = APIRouter(tags=["opencode"])


# ---------- Constants ----------

ALLOWED_AGENTS = frozenset({"scholar-orchestrator", "concept-mapper", "source-finder"})
ALLOWED_MODES = frozenset({"fast", "deep"})
HEARTBEAT_INTERVAL_SECONDS = 15.0
# Session → agent cache TTL matches the SSE token TTL (10 min). Sessions
# typically outlive this on the upstream side, but the cache only needs to
# be valid for the prompt-submission window of an active interactive chat.
SESSION_AGENT_TTL_SECONDS = 600


# ---------- Session → agent cache ----------
#
# `submit_prompt` needs to know which agent the session was created with so
# it can forward the correct `agent` field in the upstream payload. We cache
# the mapping in-process at session creation. Entries expire after
# `SESSION_AGENT_TTL_SECONDS` and are explicitly evicted on abort.
#
# `(agent, expires_at_epoch_seconds)`
_session_agent_cache: dict[str, tuple[str, float]] = {}


def _cache_session_agent(session_id: str, agent: str) -> None:
    _session_agent_cache[session_id] = (
        agent,
        time.monotonic() + SESSION_AGENT_TTL_SECONDS,
    )


def _lookup_session_agent(session_id: str) -> str | None:
    entry = _session_agent_cache.get(session_id)
    if entry is None:
        return None
    agent, expires_at = entry
    if time.monotonic() >= expires_at:
        _session_agent_cache.pop(session_id, None)
        return None
    return agent


def _evict_session_agent(session_id: str) -> None:
    _session_agent_cache.pop(session_id, None)


def _reset_session_agent_cache() -> None:
    """Test helper — clear the cache between cases."""
    _session_agent_cache.clear()


# ---------- Session → TraceWriter map ----------
#
# Populated by ``submit_prompt`` once the query is known. The SSE pump reads
# the writer here and dispatches events into it as they stream by. Lifetime
# matches the session JWT (10 min) so abandoned writers cannot leak.

_trace_writers: dict[str, TraceWriter] = {}


def _register_trace_writer(session_id: str, writer: TraceWriter) -> None:
    _trace_writers[session_id] = writer


def _pop_trace_writer(session_id: str) -> TraceWriter | None:
    return _trace_writers.pop(session_id, None)


def _peek_trace_writer(session_id: str) -> TraceWriter | None:
    return _trace_writers.get(session_id)


def _reset_trace_writers() -> None:
    """Test helper."""
    _trace_writers.clear()


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
    _cache_session_agent(session_id, body.agent)
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
    """Queue a prompt against an existing opencode session (async / fire-and-forget).

    Upstream opencode (since 2026-05-15) requires the payload shape
    ``{"parts": [{"type":"text","text":"..."}], "agent": "<agent_slug>"}``.
    The agent slug is recovered from the session→agent cache populated at
    ``create_session`` time so the client does not have to re-send it.
    """
    user = await get_current_user(request, db)
    if body.mode is not None and body.mode not in ALLOWED_MODES:
        raise HTTPException(status_code=400, detail=f"unknown mode: {body.mode}")
    await enforce_user_usage_limits(
        db, user["user_id"], mode=body.mode or "fast"
    )
    settings = _ensure_configured()

    agent = _lookup_session_agent(session_id)
    if agent is None:
        # The cache TTL expired or the api process restarted between the
        # session-create call and the first prompt. 410 (Gone) tells the
        # client to recreate the session — a 401/404 would be misleading.
        raise HTTPException(
            status_code=410,
            detail="session_agent_unknown_recreate_session",
        )

    upstream_payload: dict[str, Any] = {
        "agent": agent,
        "parts": [{"type": "text", "text": body.prompt}],
    }
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
        logger.warning(
            "opencode prompt upstream %s for %s: %s",
            upstream.status_code,
            session_id,
            upstream.text[:200],
        )
        raise HTTPException(
            status_code=502,
            detail=f"opencode_upstream_status_{upstream.status_code}",
        )

    # Persist an initial trace row so partial-view audit calls can already
    # see the query/user/started_at. The SSE pump enriches it as events arrive.
    try:
        writer = TraceWriter(
            db=db,
            trace_id=session_id,
            query=body.prompt,
            user_id=user.get("user_id"),
            mode=body.mode or "fast",
            metadata={"agent": agent},
        )
        await writer.record_agent_invocation(
            agent_id=agent, parent_agent_id=None, subagent_index=0
        )
        await writer.start()
        _register_trace_writer(session_id, writer)
    except Exception:
        logger.exception("trace_writer init failed for session %s", session_id)

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
    _evict_session_agent(session_id)
    writer = _pop_trace_writer(session_id)
    if writer is not None:
        try:
            await writer.finalize(final_answer="", citations=[], success=False)
        except Exception:
            logger.exception("trace_writer abort-finalize failed for %s", session_id)
    return AbortResponse(aborted=True)


# ---------- SSE proxy ----------


def _session_id_of(envelope: dict[str, Any]) -> str | None:
    props = envelope.get("properties")
    if not isinstance(props, dict):
        return None
    sid = props.get("sessionID") or props.get("sessionId") or props.get("session_id")
    return sid if isinstance(sid, str) else None


def _synthesise_cost_events(
    session_id: str, event: dict[str, Any]
) -> list[dict[str, Any]]:
    """Derive synthetic SSE envelopes (``tokens_used`` rollups +
    ``cost_summary`` on completion) from the writer's running totals.

    Lets the frontend show a live "$0.034 · 12,348 tok" badge even when the
    upstream agent runtime (opencode) does not natively emit per-call
    ``tokens_used`` events — we synthesise them from whatever the writer
    has aggregated so far. Always returns a list (possibly empty).
    """
    writer = _peek_trace_writer(session_id)
    if writer is None:
        return []
    evt_type = event.get("type") or ""
    out: list[dict[str, Any]] = []
    try:
        totals = writer.get_running_totals()
    except Exception:
        return []

    if evt_type in {"subagent_complete", "tokens_used", "tool_result"} and (
        totals.get("total_tokens", 0) or totals.get("total_cost_usd", 0)
    ):
        out.append(
            {
                "type": "tokens_used_rollup",
                "total_tokens": totals.get("total_tokens", 0),
                "total_cost_usd": totals.get("total_cost_usd", 0.0),
            }
        )

    if evt_type == "final_answer":
        out.append(
            {
                "type": "cost_summary",
                "total_tokens": totals.get("total_tokens", 0),
                "total_cost_usd": totals.get("total_cost_usd", 0.0),
                "by_model": totals.get("by_model", {}),
                "by_agent": totals.get("by_agent", {}),
                "by_provider": totals.get("by_provider", {}),
            }
        )
    return out


async def _dispatch_to_trace_writer(session_id: str, event: dict[str, Any]) -> None:
    """Forward a single SSE envelope into the session's :class:`TraceWriter`.

    Maps the streaming event vocabulary onto the persistent trace shape:

    - ``agent_invocation`` → ``record_agent_invocation`` (root or sub-agent).
    - ``tool_call`` / ``tool_result`` → ``record_tool_call`` (paired via
      ``properties.id`` when present).
    - ``subagent_complete`` → ``record_subagent_complete``.
    - Report events (citation_verifier / counter_evidence_complete /
      methodology_approved / polishing_pass_complete) → ``set_report``.
    - ``final_answer`` → ``finalize`` and evict the writer.

    Unknown event types are ignored.
    """
    writer = _peek_trace_writer(session_id)
    if writer is None:
        return

    props = event.get("properties") or {}
    if not isinstance(props, dict):
        return
    evt_type = event.get("type") or ""

    try:
        if evt_type == "agent_invocation":
            await writer.record_agent_invocation(
                agent_id=str(props.get("agent_id") or props.get("agent") or "unknown"),
                parent_agent_id=props.get("parent_agent_id"),
                subagent_index=props.get("subagent_index"),
            )
        elif evt_type == "tool_call":
            await writer.record_tool_call(
                agent_id=str(props.get("agent") or "unknown"),
                tool=str(props.get("tool") or "unknown"),
                args=props.get("args") or {},
                result_summary="(pending result)",
            )
        elif evt_type == "tool_result":
            agent_id = str(props.get("agent") or "unknown")
            await writer.record_tool_call(
                agent_id=agent_id,
                tool=str(props.get("tool") or "unknown"),
                args={},
                result_summary=str(
                    props.get("result_summary") or props.get("summary") or ""
                ),
                duration_ms=props.get("duration_ms"),
            )
        elif evt_type == "subagent_complete":
            await writer.record_subagent_complete(
                agent_id=str(props.get("agent_id") or "unknown"),
                success=bool(props.get("success", True)),
                tokens_used=props.get("tokens_used"),
            )
        elif evt_type == "tokens_used":
            # Forward token-usage observations into the writer so totals get
            # persisted alongside the agent tree. Opencode emits one event per
            # underlying LLM call; the writer dedupes by (agent_id, model).
            try:
                from eleutheria_graphrag.services.llm_pricing import (
                    TokenUsage,
                    estimate_cost_usd,
                )

                provider = str(props.get("provider") or "unknown")
                prompt_tokens = int(props.get("prompt_tokens") or 0)
                completion_tokens = int(props.get("completion_tokens") or 0)
                total_tokens = int(
                    props.get("total_tokens") or (prompt_tokens + completion_tokens)
                )
                cost = props.get("estimated_cost_usd")
                cost_usd = (
                    float(cost)
                    if isinstance(cost, (int, float, str)) and str(cost).strip() != ""
                    else estimate_cost_usd(
                        provider=provider,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )
                )
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=str(props.get("model") or ""),
                    provider=provider,
                    estimated_cost_usd=cost_usd,
                    agent_id=str(props.get("agent_id") or "") or None,
                )
                await writer.record_token_usage(agent_id=usage.agent_id, usage=usage)
            except Exception:
                logger.exception("token usage dispatch failed for %s", session_id)
        elif evt_type == "citation_verified":
            # Aggregate the rolling verifier report.
            current = writer._reports.get("citation_verifier_report") or {
                "verifications": []
            }
            if isinstance(current, dict):
                verifs = current.setdefault("verifications", [])
                verifs.append(props)
                await writer.set_report("citation_verifier_report", current)
        elif evt_type == "counter_evidence_complete":
            await writer.set_report("counter_evidence_report", props)
        elif evt_type == "methodology_approved":
            await writer.set_report("methodology_report", {"approved": True, **props})
        elif evt_type == "methodology_flagged":
            current = writer._reports.get("methodology_report") or {"flags": []}
            if isinstance(current, dict):
                flags = current.setdefault("flags", [])
                flags.append(props)
                await writer.set_report("methodology_report", current)
        elif evt_type == "polishing_pass_complete":
            await writer.set_report("polishing_report", props)
        elif evt_type == "final_answer":
            await writer.finalize(
                final_answer=str(props.get("answer") or ""),
                citations=props.get("citations") or [],
                success=True,
            )
            _pop_trace_writer(session_id)
        elif evt_type == "error":
            await writer.finalize(
                final_answer="",
                citations=[],
                success=False,
            )
            _pop_trace_writer(session_id)
    except Exception:
        logger.exception("trace_writer dispatch failed for session %s", session_id)


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
                                            if emit and envelope_sid == session_id:
                                                await _dispatch_to_trace_writer(
                                                    session_id, parsed
                                                )
                                    if emit:
                                        payload = event_text + "\n\n"
                                        if current_id:
                                            payload = f"id: {current_id}\n" + payload
                                        yield payload.encode()

                                    # After each forwarded event, derive any
                                    # synthetic envelopes the client should
                                    # see (cost_summary on final_answer,
                                    # rolling tokens_used on subagent
                                    # completion). These piggyback on the
                                    # TraceWriter's running totals so the UI
                                    # gets a live cost figure even when the
                                    # upstream doesn't natively emit it.
                                    if emit and isinstance(parsed, dict):
                                        for extra in _synthesise_cost_events(
                                            session_id, parsed
                                        ):
                                            extra_payload = (
                                                f"data: {json.dumps(extra)}\n\n"
                                            )
                                            yield extra_payload.encode()
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
