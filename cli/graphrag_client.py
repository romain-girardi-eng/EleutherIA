"""Headless client for the SAME authenticated SSE endpoint used by the website.

Only publication verdicts are output. Draft/trace events are never retained.
This module does not need the GraphRAG server package or an LLM provider key.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

SESSION_PATH = Path.home() / ".config" / "eleutheria" / "session.json"
_PRIVATE = {
    "debug_trace",
    "raw_excerpt",
    "raw_output",
    "raw_response",
    "answer_excerpt",
    "raw_answer",
    "draft_answer",
    "provisionalAnswer",
    "provisional_answer",
    "thinking",
    "thinking_process",
    "synthesis_reasoning",
    "reasoning_excerpt",
    "full_prompt",
    "__answer_provenance__",
    "research_graph",
}


def default_api_url() -> str:
    """Explicit environment wins; otherwise reuse the API selected at login."""
    if os.getenv("ELEUTHERIA_API_URL"):
        return os.environ["ELEUTHERIA_API_URL"]
    try:
        saved = json.loads(SESSION_PATH.read_text()).get("api_root")
        if isinstance(saved, str) and saved.startswith(("https://", "http://")):
            return saved.removesuffix("/api")
    except (OSError, ValueError, AttributeError):
        pass
    return "http://localhost:8000"


def api_root(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base.startswith(("https://", "http://")):
        raise ValueError("API URL must start with https:// or http://")
    return base if base.endswith("/api") else base + "/api"


def auth_headers(base_url: str, token_file: Path | None = None) -> dict[str, str]:
    """Never take bearer tokens on argv or forward a saved session to another API."""
    token = os.getenv("ELEUTHERIA_API_TOKEN", "").strip()
    file_name = token_file or os.getenv("ELEUTHERIA_TOKEN_FILE")
    if file_name:
        token = Path(file_name).read_text().strip()
    elif not token and SESSION_PATH.exists():
        session = json.loads(SESSION_PATH.read_text())
        if session.get("api_root") == api_root(base_url):
            token = str(session.get("access_token") or "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic private artifact/session write, including when replacing a file."""
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False, encoding="utf-8"
        ) as handle:
            name = handle.name
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def _public(value: Any, diagnostic: bool = False) -> Any:
    if isinstance(value, list):
        return [_public(item, diagnostic) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in _PRIVATE or (
                diagnostic
                and key in {"claim", "sentence", "clause", "reasoning", "text"}
            ):
                continue
            if key == "claim_ledger" and isinstance(item, list):
                item = [
                    claim
                    for claim in item
                    if isinstance(claim, dict)
                    and claim.get("status") not in {"insufficient", "unverified"}
                ]
            result[key] = _public(
                item, diagnostic or key in {"citation_verifier_v2", "text_verification"}
            )
        return result
    return value


def sse_events(lines: Iterable[str]) -> Iterator[dict[str, Any]]:
    """Decode split/CRLF/multiline SSE data; ignore comments and event/id fields."""
    data: list[str] = []
    for line in lines:
        line = line.rstrip("\r\n")
        if line == "":
            if data:
                value = json.loads("\n".join(data))
                if not isinstance(value, dict):
                    raise ValueError("SSE data must be an object")
                yield value
                data.clear()
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))
    if data:
        value = json.loads("\n".join(data))
        if not isinstance(value, dict):
            raise ValueError("SSE data must be an object")
        yield value


def _verdict(data: dict[str, Any]) -> dict[str, Any] | None:
    gate = data.get("publication_gate")
    gate = dict(gate) if isinstance(gate, dict) else {}
    withheld = data.get("withheld") is True or gate.get("publishable") is False
    answer = data.get("answer") if isinstance(data.get("answer"), str) else ""
    if not withheld and (data.get("withheld") is not False or not answer.strip()):
        return None
    if withheld:
        gate.update(publishable=False, status="blocked")
    elif not gate:
        gate = {
            "publishable": True,
            "status": data.get("status", "passed"),
            "reasons": data.get("reasons", []),
        }
    citations = data.get("citations") if isinstance(data.get("citations"), list) else []
    return {
        "answer": "" if withheld else answer,
        "passage_citations": [] if withheld else citations,
        "citations": {
            "ancient_sources": [
                c.get("label", "")
                for c in citations
                if isinstance(c, dict) and c.get("layer") != "secondary"
            ],
            "modern_scholarship": [
                c.get("label", "")
                for c in citations
                if isinstance(c, dict) and c.get("layer") == "secondary"
            ],
        },
        "claim_ledger": [] if withheld else data.get("claim_ledger", []),
        "metadata": {
            "publication_gate": gate,
            "quality_badge": data.get("quality_badge"),
        },
    }


def _settle(
    verdict: dict[str, Any] | None, terminal: dict[str, Any] | None
) -> dict[str, Any]:
    result = {**(verdict or {}), **(terminal or {})}
    terminal_meta = (terminal or {}).get("metadata") or {}
    verdict_meta = (verdict or {}).get("metadata") or {}
    terminal_meta = terminal_meta if isinstance(terminal_meta, dict) else {}
    verdict_meta = verdict_meta if isinstance(verdict_meta, dict) else {}
    result["metadata"] = {
        **terminal_meta,
        **{k: v for k, v in verdict_meta.items() if v is not None},
    }
    if verdict:
        result["answer"] = verdict["answer"]
        for key in ("passage_citations", "claim_ledger"):
            if verdict.get(key) or not result.get(key):
                result[key] = verdict.get(key, [])
        if verdict.get("passage_citations"):
            result["citations"] = verdict["citations"]
    gates = [
        verdict_meta.get("publication_gate"),
        terminal_meta.get("publication_gate"),
    ]
    blocked = next(
        (g for g in gates if isinstance(g, dict) and g.get("publishable") is False),
        None,
    )
    gate = result["metadata"].get("publication_gate")
    if blocked is None and not (
        isinstance(gate, dict) and gate.get("publishable") is True
    ):
        blocked = {
            "publishable": False,
            "status": "blocked",
            "reasons": ["publication_report_missing"],
        }
    if blocked is not None:
        result.update(
            answer="",
            citations={"ancient_sources": [], "modern_scholarship": []},
            passage_citations=[],
            claim_ledger=[],
            success=False,
        )
        result["metadata"].update(publication_gate=blocked, quality_badge="Blocked")
    elif not isinstance(result.get("answer"), str) or not result["answer"].strip():
        return _settle(
            None,
            {
                "metadata": {
                    "publication_gate": {
                        "publishable": False,
                        "status": "blocked",
                        "reasons": ["no_published_answer"],
                    }
                }
            },
        )
    return _public(result)


def capture_query(
    question: str,
    *,
    base_url: str,
    model: str = "auto",
    mode: str = "fast",
    pipeline: str | None = None,
    timeout: float = 1200,
    fresh: bool = False,
    token_file: Path | None = None,
    on_status: Callable[[str], None] | None = None,
    client: Any = None,
) -> tuple[dict[str, Any], int]:
    """Return a gated payload and exit code (0 complete, 2 withheld/partial, 3 I/O, 4 auth)."""
    import httpx

    started = time.monotonic()
    verdict = terminal = None
    error = None
    status_code = None
    event_count = 0
    cancelled = False
    params = {"question": question, "model": model, "mode": mode}
    if fresh:
        params["force_refresh"] = "true"
    if pipeline:
        params["pipeline"] = pipeline
    owns_client = client is None
    if owns_client:
        client = httpx.Client()
    try:
        headers = auth_headers(base_url, token_file)
        with client.stream(
            "GET",
            api_root(base_url) + "/graphrag/query/stream",
            params=params,
            headers=headers,
            timeout=httpx.Timeout(timeout, connect=min(timeout, 15)),
        ) as response:
            status_code = response.status_code
            if status_code in (401, 403):
                error = "Authentication required. Run eleutheria login or set ELEUTHERIA_API_TOKEN."
            elif status_code != 200:
                error = f"API returned HTTP {status_code}."
            else:
                for event in sse_events(response.iter_lines()):
                    event_count += 1
                    kind = event.get("type")
                    data = event.get("data")
                    if kind == "answer_final" and isinstance(data, dict):
                        received = _verdict(data)
                        if received:
                            verdict = (
                                _settle(verdict, received) if verdict else received
                            )
                    elif kind == "complete" and isinstance(data, dict):
                        terminal = _public(data)
                    elif kind == "status" and on_status:
                        message = (
                            data.get("message")
                            if isinstance(data, dict)
                            else event.get("message")
                        )
                        if isinstance(message, str):
                            on_status(message)
                    elif kind == "error":
                        error = "The server reported a stream error."
                    # No draft prose, thought deltas or citation previews retained.
    except KeyboardInterrupt:
        cancelled = True
        error = "Cancelled by user."
    except (httpx.HTTPError, OSError, ValueError) as exc:
        error = f"Stream interrupted ({type(exc).__name__})."
    finally:
        if owns_client:
            client.close()
    result = _settle(verdict, terminal)
    result.setdefault("query", question)
    gate = result["metadata"]["publication_gate"]
    code = (
        130
        if cancelled
        else 4
        if status_code in (401, 403)
        else 3
        if error
        else 0
        if gate.get("publishable") and gate.get("status") != "partial"
        else 2
    )
    result["_cli"] = {
        "exit_code": code,
        "error": error,
        "http_status": status_code,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "received_verdict": verdict is not None,
        "received_complete": terminal is not None,
        "event_count": event_count,
        "api_root": api_root(base_url),
        "requested_model": model,
        "mode": mode,
    }
    return result, code
