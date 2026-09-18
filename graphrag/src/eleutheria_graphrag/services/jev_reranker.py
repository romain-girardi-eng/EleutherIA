"""Jev (TypeSafe AI) passage pruner and reranker through Vercel AI Gateway.

Jev is a System One model: it reads a state and answers typed questions in
parallel, with calibrated probabilities, and never generates text. Here it
answers one boolean per candidate passage ("this candidate directly bears on
the research question") and the answers order the candidates.

HARD RULES: the model only reorders evidence that retrieval already produced.
It never writes, translates or paraphrases Greek or Latin, and a failure of
any kind (missing key, timeout, HTTP error, malformed answer) returns the
input order unchanged so the pipeline degrades to its lexical ranking.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.state import Evidence

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "typesafe-ai/jev"
DEFAULT_BASE_URL = "https://ai-gateway.vercel.sh/v4/ai"
API_KEY_ENV = "AI_GATEWAY_API_KEY"
MODEL_ENV = "ELEUTHERIA_JEV_MODEL"
# One grouped request per chunk keeps the state under Jev's context limit
# (64k tokens for state plus questions; Greek tokenizes at ~1.4 tokens per
# character) while a 150-candidate pool still costs four parallel calls.
DEFAULT_CHUNK_SIZE = 40
DEFAULT_TEXT_CHARS = 600
DEFAULT_TIMEOUT_S = 1.5
DEFAULT_CONCURRENCY = 4

_QUESTION = (
    "`candidates[{i}]` directly bears on `research_question`: it contains the "
    "text, testimony or doctrine the question asks about (not merely the same "
    "author or a related theme)."
)


class JevRerankerService:
    """Score candidate passages against a question with Jev, grouped per chunk.

    ``prune_rows`` works on the plain dict rows that ``HybridSearchService``
    returns (the seed stage); ``rerank`` keeps the ``RerankerService``
    contract on ``Evidence`` objects so the two rerankers are interchangeable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        text_chars: int = DEFAULT_TEXT_CHARS,
        concurrency: int = DEFAULT_CONCURRENCY,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv(API_KEY_ENV) or ""
        self.model = model or os.getenv(MODEL_ENV) or DEFAULT_MODEL
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.chunk_size = max(1, chunk_size)
        self.text_chars = max(50, text_chars)
        self.concurrency = max(1, concurrency)
        self._client = client
        self.last_report: dict[str, Any] = {}

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "ai-model-id": self.model,
            "ai-evaluation-model-specification-version": "4",
            "ai-gateway-auth-method": "api-key",
            "ai-gateway-protocol-version": "0.0.1",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout_s)
        return self._client

    async def _evaluate_chunk(
        self, question: str, chunk: list[dict[str, Any]], offset: int
    ) -> tuple[list[float], dict[str, Any]]:
        """One grouped Jev call: returns probabilities aligned with ``chunk``."""
        candidates = [
            {
                "author": row.get("author"),
                "work": row.get("title") or row.get("work_title"),
                "reference": row.get("canonical_ref"),
                "language": row.get("language"),
                "text": (row.get("text_content") or "")[: self.text_chars],
            }
            for row in chunk
        ]
        questions = {
            f"c{offset + i}": {"type": "boolean", "instructions": _QUESTION.format(i=i)}
            for i in range(len(chunk))
        }
        body = {
            "state": {"research_question": question, "candidates": candidates},
            "questions": questions,
        }
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/evaluation-model", headers=self._headers(), json=body
        )
        response.raise_for_status()
        payload = response.json()
        answers = payload["answers"]
        probs = [
            float(answers[f"c{offset + i}"]["probability"]) for i in range(len(chunk))
        ]
        return probs, payload.get("providerMetadata") or {}

    async def score_rows(
        self, question: str, rows: list[dict[str, Any]]
    ) -> list[float] | None:
        """Probability per row that it bears on ``question``; ``None`` on failure."""
        if not rows:
            return []
        if not self.configured:
            self.last_report = {"applied": False, "reason": "no_api_key"}
            return None
        chunks = [
            rows[i : i + self.chunk_size] for i in range(0, len(rows), self.chunk_size)
        ]
        semaphore = asyncio.Semaphore(self.concurrency)
        started = time.perf_counter()

        async def run(
            index: int, chunk: list[dict[str, Any]]
        ) -> tuple[list[float], dict[str, Any]]:
            async with semaphore:
                return await self._evaluate_chunk(
                    question, chunk, index * self.chunk_size
                )

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*(run(i, c) for i, c in enumerate(chunks))),
                timeout=self.timeout_s,
            )
        except (TimeoutError, httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            self.last_report = {
                "applied": False,
                "reason": type(exc).__name__,
                "ms": int((time.perf_counter() - started) * 1000),
            }
            logger.warning("Jev scoring failed (%s); keeping input order", exc)
            return None
        probs: list[float] = []
        for chunk_probs, _ in results:
            probs.extend(chunk_probs)
        routing = (results[0][1].get("gateway") or {}).get("routing") or {}
        self.last_report = {
            "applied": True,
            "model": routing.get("canonicalSlug") or self.model,
            "scored": len(probs),
            "calls": len(chunks),
            "ms": int((time.perf_counter() - started) * 1000),
        }
        return probs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def prune_rows(
        self, question: str, rows: list[dict[str, Any]], keep: int
    ) -> list[dict[str, Any]]:
        """Return the ``keep`` rows most likely to bear on ``question``.

        Rows come back with ``jev_probability`` set. On any failure the first
        ``keep`` rows are returned in their input (lexical) order.
        """
        probs = await self.score_rows(question, rows)
        if probs is None:
            return rows[:keep]
        order = sorted(range(len(rows)), key=lambda i: (-probs[i], i))
        pruned: list[dict[str, Any]] = []
        for i in order[:keep]:
            row = dict(rows[i])
            row["jev_probability"] = probs[i]
            pruned.append(row)
        return pruned

    async def rerank(
        self,
        query: str,
        evidence: list[Evidence],
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[Evidence]:
        """``RerankerService``-compatible scorer over ``Evidence`` items.

        Writes the Jev probability into ``ev.score`` and orders by it; keeps
        the input order on failure. ``score_threshold`` drops items below it
        only when given; ``top_k`` caps the result.
        """
        if not evidence:
            return []
        rows = [
            {
                "author": ev.author,
                "title": ev.work_title,
                "canonical_ref": ev.canonical_ref,
                "language": ev.language,
                "text_content": ev.text_content or ev.description or ev.label,
            }
            for ev in evidence
        ]
        probs = await self.score_rows(query, rows)
        limit = len(evidence) if top_k is None else top_k
        if probs is None:
            return evidence[:limit]
        for ev, p in zip(evidence, probs, strict=True):
            ev.score = p
        ranked = sorted(evidence, key=lambda ev: -ev.score)
        if score_threshold is not None:
            ranked = [ev for ev in ranked if ev.score >= score_threshold]
        return ranked[:limit]
