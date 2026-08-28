"""Streaming-route reliability regressions (incident audit fixes 8, 9, 10b).

- Fix 8: ``TraceWriter.finalize`` was only reachable inside the ``try``, so a
  client disconnect (``asyncio.CancelledError`` / ``GeneratorExit`` —
  BaseException) skipped all four call sites and left NULL ``completed_at`` /
  ``final_answer_text``.
- Fix 9: the answer-cache gate was length-only, so a degraded structural answer
  was cached and replayed to every future asker.
- Fix 10b: the reasoning path hardcoded empty traversed edges.
"""

from __future__ import annotations

from typing import Any

import pytest

from eleutheria_graphrag.agents.publication_gate import POLICY, is_publishable
from eleutheria_graphrag.api.routes import (
    _synthesis_is_cacheable,
    _traversed_edges,
)


class TestAnswerCacheGate:
    """Fix 9 — never cache an answer the synthesis model did not actually write."""

    @staticmethod
    def _verified_metadata() -> dict[str, Any]:
        return {
            "scholar_synthesis": {"status": "ok", "degraded": False},
            "content_gate": {"status": "passed", "passed": True},
            "citation_verifier_v2": {
                "status": "passed",
                "total": 2,
                "sampled": 2,
                "audited_citations": 2,
                "total_citations": 2,
                "verified": 2,
                "weak": 0,
                "rejected": 0,
                "missing": 0,
                "parse_errors": 0,
                "aborted": False,
            },
        }

    def test_ok_synthesis_is_cacheable(self):
        assert _synthesis_is_cacheable(self._verified_metadata())

    def test_degraded_flag_blocks_caching(self):
        assert not _synthesis_is_cacheable(
            {"scholar_synthesis": {"status": "ok", "degraded": True}}
        )

    def test_deterministic_map_hedge_is_not_cacheable(self):
        """The structural fallback emitted when the synthesis model was down."""
        assert not _synthesis_is_cacheable(
            {
                "scholar_synthesis": {
                    "status": "deterministic_map",
                    "degraded": True,
                    "reason": "empty",
                }
            }
        )

    def test_degraded_status_is_not_cacheable(self):
        assert not _synthesis_is_cacheable(
            {"scholar_synthesis": {"status": "degraded", "degraded": True}}
        )

    def test_failed_status_is_not_cacheable(self):
        assert not _synthesis_is_cacheable(
            {"scholar_synthesis": {"status": "failed", "reason": "empty"}}
        )

    def test_legacy_or_unaudited_path_is_not_cacheable(self):
        assert not _synthesis_is_cacheable({})
        assert not _synthesis_is_cacheable({"scholar_synthesis": None})

    def test_partial_verdict_is_not_cacheable(self):
        """A withheld sentence (one WEAK verdict) is published, but the holed
        prose is recomputed for the next asker, never replayed."""
        metadata = self._verified_metadata()
        metadata["citation_verifier_v2"].update(
            {
                "status": "failed",
                "verified": 1,
                "weak": 1,
                "verified_citations": ["c0"],
                "failed_citations": [
                    {
                        "citation_id": "c1",
                        "status": "WEAK",
                        "claim": "claim",
                        "reasoning": "reasoning",
                        "parse_error": False,
                    }
                ],
            }
        )
        assert is_publishable(metadata)
        assert not _synthesis_is_cacheable(metadata)
        metadata["publication_gate"] = {
            "policy": POLICY,
            "applied": True,
            "publishable": True,
            "status": "partial",
            "reasons": [],
            "warnings": [],
        }
        assert not _synthesis_is_cacheable(metadata)

    def test_one_rejected_citation_blocks_caching(self):
        metadata = self._verified_metadata()
        metadata["citation_verifier_v2"].update(
            {"status": "failed", "verified": 1, "rejected": 1}
        )
        assert not _synthesis_is_cacheable(metadata)


class _FakeGraphRAG:
    def __init__(self, nodes: dict[str, Any], edges: dict[str, list[dict[str, Any]]]):
        self.node_lookup = nodes
        self.outgoing_edges = edges


class TestTraversedEdges:
    """Fix 10b — the reasoning path must report the traversal that happened."""

    @staticmethod
    def _graph() -> _FakeGraphRAG:
        return _FakeGraphRAG(
            nodes={
                "a": {"id": "a", "label": "Chrysippus"},
                "b": {"id": "b", "label": "Fate"},
                "c": {"id": "c", "label": "Assent"},
                "outside": {"id": "outside", "label": "Not retrieved"},
            },
            edges={
                "a": [
                    {"target": "b", "relation": "discusses"},
                    {"target": "outside", "relation": "discusses"},
                ],
                "b": [{"target": "c", "relation": "related_to"}],
            },
        )

    def test_reports_edges_between_retrieved_nodes(self):
        edges = _traversed_edges(self._graph(), ["a"], ["b", "c"])
        pairs = {(e["source"], e["target"], e["relation"]) for e in edges}
        assert pairs == {("a", "b", "discusses"), ("b", "c", "related_to")}

    def test_excludes_edges_leaving_the_retrieved_subgraph(self):
        edges = _traversed_edges(self._graph(), ["a"], ["b", "c"])
        assert all(e["target"] != "outside" for e in edges)

    def test_empty_when_nothing_was_retrieved(self):
        assert _traversed_edges(self._graph(), [], []) == []

    def test_description_falls_back_to_the_target_label(self):
        edges = _traversed_edges(self._graph(), ["a"], ["b"])
        assert edges[0]["description"] == "Fate"

    def test_shape_matches_the_frontend_contract(self):
        for edge in _traversed_edges(self._graph(), ["a"], ["b", "c"]):
            assert set(edge) == {"source", "target", "relation", "description"}


class _RecordingWriter:
    """Minimal TraceWriter stand-in."""

    def __init__(self) -> None:
        self.finalize_calls: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}

    async def finalize(
        self, *, final_answer: str, citations: list, success: bool = True
    ) -> None:
        self.finalize_calls.append(
            {
                "final_answer": final_answer,
                "citations": citations,
                "success": success,
            }
        )


class TestFinalizeOnce:
    """Fix 8 — the finalize-once + BaseException-safe compensation contract.

    Exercised against a faithful reproduction of the route's local helper and
    ``finally`` block (the route generator itself needs the full FastAPI +
    GraphRAG stack to drive).
    """

    @staticmethod
    def _make_stream(writer: _RecordingWriter, chunks: list[str]):
        import asyncio
        import contextlib

        state = {"finalized": False, "complete_sent": False}
        parts: list[str] = []

        async def _finalize_once(
            *, final_answer: str, citations: list, success: bool = True
        ) -> None:
            if state["finalized"] or writer is None:
                return
            state["finalized"] = True
            await writer.finalize(
                final_answer=final_answer, citations=citations, success=success
            )

        async def generate():
            try:
                for chunk in chunks:
                    parts.append(chunk)
                    yield chunk
                state["complete_sent"] = True
                await _finalize_once(final_answer="".join(parts), citations=[])
            finally:
                if not state["finalized"] and writer is not None:
                    task = asyncio.ensure_future(
                        _finalize_once(
                            final_answer="".join(parts),
                            citations=[],
                            success=state["complete_sent"],
                        )
                    )
                    with contextlib.suppress(BaseException):
                        await asyncio.shield(task)

        return generate, state

    @pytest.mark.asyncio
    async def test_finalizes_once_on_the_happy_path(self):
        writer = _RecordingWriter()
        generate, _ = self._make_stream(writer, ["alpha", "beta"])
        async for _ in generate():
            pass
        assert len(writer.finalize_calls) == 1
        assert writer.finalize_calls[0]["final_answer"] == "alphabeta"
        assert writer.finalize_calls[0]["success"] is True

    @pytest.mark.asyncio
    async def test_finalizes_with_the_partial_answer_when_the_client_disconnects(self):
        """THE regression: an aclose() mid-stream used to skip finalize entirely."""
        writer = _RecordingWriter()
        generate, _ = self._make_stream(writer, ["alpha", "beta", "gamma"])
        agen = generate()
        assert await anext(agen) == "alpha"
        assert await anext(agen) == "beta"
        await agen.aclose()  # client disconnected

        assert len(writer.finalize_calls) == 1, "finalize must run on disconnect"
        assert writer.finalize_calls[0]["final_answer"] == "alphabeta"
        assert writer.finalize_calls[0]["success"] is False

    @pytest.mark.asyncio
    async def test_never_finalizes_twice(self):
        writer = _RecordingWriter()
        generate, _ = self._make_stream(writer, ["alpha"])
        agen = generate()
        async for _ in agen:
            pass
        await agen.aclose()
        assert len(writer.finalize_calls) == 1
