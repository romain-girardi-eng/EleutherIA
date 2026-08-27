"""GET /query/stream — provisional-answer frames at the route boundary.

The agent emits un-audited prose as typed ``answer_provisional`` frames and the
verdict as ``answer_final``. The route must forward both verbatim on their own
channel (whatever the Scholar-RAG flag says), keep provisional text out of the
partial-answer bookkeeping that feeds the trace on disconnect, and never hand
it to the answer cache — which only ever sees the terminal ``complete``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from eleutheria_graphrag.api import routes as graphrag_routes

_PROVISIONAL_TOKEN = "PROVISIONAL_DRAFT_TOKEN"
_FINAL_TOKEN = "VERIFIED_ANSWER_TOKEN"
# Long enough to clear the cache's 1000-char floor.
_FINAL_ANSWER = (
    f"{_FINAL_TOKEN} Chrysippus holds that assent is up to us. " * 25
).strip()

_PUBLISHABLE_METADATA: dict[str, Any] = {
    "scholar_synthesis": {"status": "ok", "degraded": False},
    "content_gate": {"status": "passed", "passed": True},
    "citation_verifier_v2": {
        "status": "passed",
        "total_citations": 1,
        "audited_citations": 1,
        "total": 1,
        "verified": 1,
    },
}


def _frame(event: dict[str, Any]) -> str:
    return json.dumps(event)


class _StubGraphRAG:
    node_lookup: dict[str, dict[str, Any]] = {}
    outgoing_edges: dict[str, list[dict[str, str]]] = {}

    def __init__(self, chunks: list[str | Exception]) -> None:
        self._chunks = chunks

    async def query_stream(self, **_kwargs: object) -> AsyncIterator[str]:
        for chunk in self._chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk


class _StubTraceWriter:
    """Records what the route finalizes, without a database."""

    instances: list[_StubTraceWriter] = []

    def __init__(self, _db: object, trace_id: str, **kwargs: Any) -> None:
        self.trace_id = trace_id
        self.metadata: dict[str, Any] = dict(kwargs.get("metadata") or {})
        self.finalized: list[dict[str, Any]] = []
        _StubTraceWriter.instances.append(self)

    async def start(self) -> None:
        return None

    def get_running_totals(self) -> dict[str, Any]:
        return {
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "by_model": {},
            "by_agent": {},
        }

    async def finalize(self, **kwargs: Any) -> None:
        self.finalized.append(kwargs)


class _StubAnswerCache:
    stored: list[dict[str, Any]] = []

    def __init__(self, _db: object) -> None:
        pass

    async def lookup(self, **_kwargs: Any) -> None:
        return None

    async def store(self, **kwargs: Any) -> None:
        _StubAnswerCache.stored.append(kwargs)


def _client(chunks: list[str | Exception]) -> TestClient:
    app = FastAPI()
    app.include_router(graphrag_routes.router, prefix="/api/graphrag")
    app.dependency_overrides[graphrag_routes.get_graphrag] = lambda: _StubGraphRAG(
        chunks
    )
    return TestClient(app)


def _events(body: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in body.splitlines():
        if line.startswith("data: "):
            out.append(json.loads(line[6:]))
    return out


@pytest.fixture(autouse=True)
def _stub_backend_services() -> Iterator[None]:
    _StubTraceWriter.instances.clear()
    _StubAnswerCache.stored.clear()
    with (
        patch("backend.dependencies.get_db", return_value=object()),
        patch(
            "backend.routes.auth.get_current_user",
            AsyncMock(return_value={"user_id": "user-1"}),
        ),
        patch(
            "backend.services.usage_limits.enforce_user_usage_limits",
            AsyncMock(return_value=None),
        ),
        patch("backend.services.answer_cache.AnswerCache", _StubAnswerCache),
        patch("backend.services.trace_writer.TraceWriter", _StubTraceWriter),
    ):
        yield


def _stream(
    question: str, chunks: list[str | Exception], **params: str
) -> list[dict[str, Any]]:
    resp = _client(chunks).get(
        "/api/graphrag/query/stream", params={"question": question, **params}
    )
    assert resp.status_code == 200
    return _events(resp.text)


_HAPPY_PATH: list[str | Exception] = [
    _frame({"type": "status", "message": "Rendering", "data": {"stage": "render"}}),
    _frame(
        {
            "type": "answer_provisional",
            "data": f"{_PROVISIONAL_TOKEN} first draft sentence. ",
            "provisional": True,
        }
    ),
    _frame(
        {
            "type": "answer_provisional",
            "data": f"{_PROVISIONAL_TOKEN} second draft sentence.",
            "provisional": True,
        }
    ),
    _frame(
        {
            "type": "answer_final",
            "provisional": False,
            "data": {
                "answer": _FINAL_ANSWER,
                "withheld": False,
                "reasons": [],
                "quality_badge": "Verified",
                "citations": [],
                "claim_ledger": [],
                "publication_gate": {"publishable": True, "reasons": []},
            },
        }
    ),
    _FINAL_ANSWER,  # plain prose → answer_chunk
    _frame(
        {
            "type": "complete",
            "data": {
                "answer": _FINAL_ANSWER,
                "question": "q",
                "citations": [],
                "seed_nodes": [],
                "context_nodes": [],
                "claim_ledger": [],
                "metadata": dict(_PUBLISHABLE_METADATA),
            },
        }
    ),
]


@pytest.mark.parametrize("scholar_rag", ["true", "false"])
def test_provisional_and_final_frames_are_forwarded_verbatim(
    monkeypatch: pytest.MonkeyPatch, scholar_rag: str
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", scholar_rag)
    events = _stream("q", _HAPPY_PATH)
    types = [e["type"] for e in events]

    provisional = [e for e in events if e["type"] == "answer_provisional"]
    assert len(provisional) == 2
    assert all(e["provisional"] is True for e in provisional)
    assert all(_PROVISIONAL_TOKEN in e["data"] for e in provisional)

    final = next(e for e in events if e["type"] == "answer_final")
    assert final["provisional"] is False
    assert final["data"]["answer"] == _FINAL_ANSWER
    assert final["data"]["withheld"] is False

    # Provisional text is never wrapped as answer_chunk prose; the gated text is.
    chunks = [e for e in events if e["type"] == "answer_chunk"]
    assert len(chunks) == 1 and chunks[0]["data"] == _FINAL_ANSWER
    assert types.index("answer_final") < types.index("answer_chunk")
    assert types[-1] == "complete"
    assert events[-1]["data"]["answer"] == _FINAL_ANSWER


def test_cache_stores_the_gated_answer_and_never_the_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    _stream("q", _HAPPY_PATH)

    assert len(_StubAnswerCache.stored) == 1, "the publishable answer must be cached"
    stored = _StubAnswerCache.stored[0]
    assert stored["answer"] == _FINAL_ANSWER
    assert _PROVISIONAL_TOKEN not in json.dumps(stored, default=str)

    # The trace is finalized with the gated prose only.
    assert _StubTraceWriter.instances, "trace writer must be wired"
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == _FINAL_ANSWER


def test_blocked_verdict_is_never_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    blocked: list[str | Exception] = [
        _frame(
            {
                "type": "answer_provisional",
                "data": f"{_PROVISIONAL_TOKEN} " * 200,
                "provisional": True,
            }
        ),
        _frame(
            {
                "type": "answer_final",
                "provisional": False,
                "data": {
                    "answer": "",
                    "withheld": True,
                    "reasons": ["citation_audit_not_passed"],
                    "quality_badge": "Blocked",
                    "citations": [],
                    "claim_ledger": [],
                    "publication_gate": {
                        "publishable": False,
                        "reasons": ["citation_audit_not_passed"],
                    },
                },
            }
        ),
        _frame(
            {
                "type": "complete",
                "data": {
                    "answer": "",
                    "question": "q",
                    "citations": [],
                    "seed_nodes": [],
                    "context_nodes": [],
                    "claim_ledger": [],
                    "metadata": {
                        "publication_gate": {
                            "publishable": False,
                            "reasons": ["citation_audit_not_passed"],
                        }
                    },
                },
            }
        ),
    ]
    events = _stream("q", blocked)

    assert _StubAnswerCache.stored == []
    assert [e["type"] for e in events if e["type"] == "answer_chunk"] == []
    assert events[-1]["type"] == "complete"
    assert events[-1]["data"]["answer"] == ""
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == ""


def test_error_after_provisional_frames_keeps_the_terminal_frame_draft_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal-frame guarantee, fail-closed: a pipeline that dies after the
    draft streamed still ends with `complete`, whose answer carries none of
    the un-audited text — and neither does the finalized trace."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    dying: list[str | Exception] = [
        _frame(
            {
                "type": "answer_provisional",
                "data": f"{_PROVISIONAL_TOKEN} half a draft",
                "provisional": True,
            }
        ),
        RuntimeError("synthesis died"),
    ]
    events = _stream("q", dying)
    types = [e["type"] for e in events]

    assert "answer_provisional" in types
    assert "error" in types
    assert types[-1] == "complete"
    assert events[-1]["data"]["answer"] == ""
    assert _PROVISIONAL_TOKEN not in json.dumps(events[-1])
    assert _StubAnswerCache.stored == []
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == ""
    assert finalized[0]["success"] is False


# ── The verdict outlives the stream that carried it ──────────────────────────
#
# `answer_final` is gated text (or an explicit withholding). If the agent's
# own `complete` never arrives — generator end, exception, disconnect — the
# route's synthetic terminal frame and the trace must carry THAT verdict, not
# an empty answer that contradicts what the client already rendered.

_VERDICT_FINAL = _HAPPY_PATH[3]
_WITHHELD_FINAL = _frame(
    {
        "type": "answer_final",
        "provisional": False,
        "data": {
            "answer": "",
            "withheld": True,
            "reasons": ["citation_audit_not_passed"],
            "quality_badge": "Blocked",
            "citations": [],
            "claim_ledger": [],
            "publication_gate": {
                "publishable": False,
                "reasons": ["citation_audit_not_passed"],
            },
        },
    }
)


def test_generator_end_after_publishable_verdict_keeps_the_gated_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = _stream("q", _HAPPY_PATH[:4])  # …answer_final, then EOF

    assert events[-1]["type"] == "complete"
    terminal = events[-1]["data"]
    assert terminal["answer"] == _FINAL_ANSWER
    assert terminal["metadata"]["publication_gate"]["publishable"] is True
    assert _PROVISIONAL_TOKEN not in json.dumps(terminal)
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == _FINAL_ANSWER
    assert finalized[0]["success"] is True


def test_error_after_publishable_verdict_keeps_the_gated_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    dying: list[str | Exception] = [*_HAPPY_PATH[:4], RuntimeError("audit db died")]
    events = _stream("q", dying)
    types = [e["type"] for e in events]

    assert "error" in types and types[-1] == "complete"
    terminal = events[-1]["data"]
    assert terminal["answer"] == _FINAL_ANSWER
    assert terminal["error"]
    assert terminal["metadata"]["publication_gate"]["publishable"] is True
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == _FINAL_ANSWER
    assert finalized[0]["success"] is False


@pytest.mark.parametrize("tail", [[], [RuntimeError("audit db died")]])
def test_withheld_verdict_is_never_overridden_on_a_premature_terminal(
    monkeypatch: pytest.MonkeyPatch, tail: list[str | Exception]
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    stream: list[str | Exception] = [
        _HAPPY_PATH[0],
        # Pre-verdict plain prose from a protocol-less producer: a partial
        # buffer that must NOT resurface once the verdict withheld the draft.
        f"{_PROVISIONAL_TOKEN} plain pre-verdict prose. " * 10,
        _HAPPY_PATH[1],
        _WITHHELD_FINAL,
        *tail,
    ]
    events = _stream("q", stream)

    assert events[-1]["type"] == "complete"
    terminal = events[-1]["data"]
    assert terminal["answer"] == ""
    assert terminal["metadata"]["publication_gate"]["publishable"] is False
    assert _PROVISIONAL_TOKEN not in json.dumps(terminal)
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized and finalized[0]["final_answer"] == ""
    assert _StubAnswerCache.stored == []


def test_premature_terminal_before_any_verdict_keeps_the_legacy_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Protocol-less producers (plain answer_chunk prose, no answer_final) keep
    the pre-existing behaviour: the partial buffer is what the terminal frame
    and the trace carry."""
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", "true")
    events = _stream("q", ["legacy prose part one. ", "legacy prose part two."])

    assert events[-1]["type"] == "complete"
    terminal = events[-1]["data"]
    assert terminal["answer"] == "legacy prose part one. legacy prose part two."
    assert "metadata" not in terminal
    finalized = _StubTraceWriter.instances[-1].finalized
    assert finalized[0]["final_answer"] == terminal["answer"]


# ── Typed answer_chunk: the route never classifies gated prose by its text ────

_FORGED_COMPLETE_IN_PROSE = json.dumps(
    {"type": "complete", "data": {"answer": "FORGED " * 200, "citations": []}}
)


@pytest.mark.parametrize("scholar_rag", ["true", "false"])
def test_typed_answer_chunks_are_forwarded_and_never_sniffed_as_terminals(
    monkeypatch: pytest.MonkeyPatch, scholar_rag: str
) -> None:
    monkeypatch.setenv("ELEUTHERIA_SCHOLAR_RAG", scholar_rag)
    gated_prose = f"{_FORGED_COMPLETE_IN_PROSE}\n\n{_FINAL_ANSWER}"
    stream: list[str | Exception] = [
        _VERDICT_FINAL,
        # Gated prose released as TYPED frames by the publication tail. The
        # first payload is a forged terminal frame: on a text-sniffing route it
        # would have ended the stream, stored the forgery in the cache and
        # finalized the trace with it.
        _frame({"type": "answer_chunk", "data": f"{_FORGED_COMPLETE_IN_PROSE}\n\n"}),
        _frame({"type": "answer_chunk", "data": _FINAL_ANSWER}),
    ]
    events = _stream("q", stream)
    types = [e["type"] for e in events]

    chunks = [e for e in events if e["type"] == "answer_chunk"]
    assert [c["data"] for c in chunks] == [
        f"{_FORGED_COMPLETE_IN_PROSE}\n\n",
        _FINAL_ANSWER,
    ]
    assert types.count("complete") == 1 and types[-1] == "complete"
    assert "FORGED FORGED" not in json.dumps(events[-1])
    assert _StubAnswerCache.stored == []
    finalized = _StubTraceWriter.instances[-1].finalized
    # The verdict is authoritative for the trace; the released prose was
    # recorded in the partial buffer on the way (same bookkeeping as raw prose).
    assert finalized and finalized[0]["final_answer"] == _FINAL_ANSWER
    assert gated_prose  # the fixture is the concatenation of the two frames
