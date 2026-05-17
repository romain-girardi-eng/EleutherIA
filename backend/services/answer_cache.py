"""AnswerCache — replay-cache for /api/graphrag/query/stream answers.

A persistent (normalized_question, model, retrieval_mode) -> final answer
cache, stored in ``free_will.answer_cache``. Looked up by the SSE endpoint
BEFORE running the agent pipeline; a hit lets us replay the cached
``complete`` payload immediately and skip the ~$0.45 / 7-minute synthesis.

Invalidation is twofold:

* **TTL** — entries older than ``ttl_days`` (default 14) are treated as
  stale and ignored.
* **KG version** — a row written when ``free_will.kg_version.version`` was
  ``N`` is invalidated as soon as that counter advances past ``N``. The
  counter is a manual lever for now (no auto-bump on KG mutations).

Hits bump ``hit_count`` and ``last_hit_at`` so we can rank popular queries
and pre-warm the cache for them.

Threading: the service holds no state — every public method does its work
through the shared :class:`DatabaseService` connection pool. Safe to share
across coroutines.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")
_KEY_SEP = "\x1f"  # ASCII unit-separator — never appears in user text


class AnswerCache:
    """Persistent answer cache for the GraphRAG SSE endpoint."""

    def __init__(self, db: DatabaseService) -> None:
        self._db = db

    # ---------- key derivation ----------

    @staticmethod
    def normalize_question(q: str) -> str:
        """Canonicalise a question for cache-key derivation.

        * NFC unicode normalisation (preserves polytonic Greek + Latin
          diacritics — important: ``ἐλευθερία`` and a decomposed form must
          collide).
        * Lowercase via :py:meth:`str.casefold` so Greek capitals collide
          with their lowercase forms.
        * Strip outer whitespace + collapse internal whitespace runs to a
          single space.
        """
        if not isinstance(q, str):
            raise TypeError("question must be a string")
        normalised = unicodedata.normalize("NFC", q)
        normalised = normalised.casefold()
        normalised = _WHITESPACE_RE.sub(" ", normalised).strip()
        return normalised

    @staticmethod
    def cache_key(question: str, model: str, retrieval_mode: str) -> str:
        """Stable sha256 hex digest over the normalised triple."""
        parts = (
            AnswerCache.normalize_question(question)
            + _KEY_SEP
            + model
            + _KEY_SEP
            + retrieval_mode
        )
        return hashlib.sha256(parts.encode("utf-8")).hexdigest()

    # ---------- queries ----------

    async def _current_kg_version(self) -> int:
        """Fetch the global KG version, or 0 if the table isn't there yet."""
        try:
            value = await self._db.fetchval(
                "SELECT version FROM free_will.kg_version WHERE id = 1"
            )
        except Exception:  # noqa: BLE001
            logger.debug("answer_cache: kg_version lookup failed", exc_info=True)
            return 0
        return int(value) if value is not None else 0

    async def lookup(
        self,
        *,
        question: str,
        model: str,
        retrieval_mode: str,
        ttl_days: int = 14,
    ) -> dict[str, Any] | None:
        """Look up a fresh cache entry; return its replay payload or ``None``.

        Returned dict shape::

            {
                "cache_key": str,
                "answer": str,
                "citations": list,
                "passage_citations": list,
                "sources": list,
                "reasoning_path": dict,
                "total_tokens": int,
                "total_cost_usd": float,
                "trace_id": str | None,
                "created_at": datetime,
                "hit_count": int,
            }
        """
        if not self._db.is_connected():
            return None

        key = self.cache_key(question, model, retrieval_mode)
        current_version = await self._current_kg_version()

        try:
            row = await self._db.fetchrow(
                """
                SELECT
                    cache_key,
                    answer,
                    citations_json,
                    passage_citations_json,
                    sources_json,
                    reasoning_path_json,
                    total_tokens,
                    total_cost_usd,
                    trace_id,
                    kg_version_at_creation,
                    hit_count,
                    created_at
                FROM free_will.answer_cache
                WHERE cache_key = $1
                  AND created_at > now() - ($2::int * INTERVAL '1 day')
                  AND kg_version_at_creation >= $3::bigint
                """,
                key,
                int(ttl_days),
                current_version,
            )
        except Exception:  # noqa: BLE001
            logger.exception("answer_cache: lookup query failed for key=%s", key[:12])
            return None

        if row is None:
            return None

        await self.record_hit(key)

        return {
            "cache_key": row["cache_key"],
            "answer": row["answer"],
            "citations": _coerce_json(row["citations_json"], default=[]),
            "passage_citations": _coerce_json(
                row["passage_citations_json"], default=[]
            ),
            "sources": _coerce_json(row["sources_json"], default=[]),
            "reasoning_path": _coerce_json(row["reasoning_path_json"], default={}),
            "total_tokens": int(row["total_tokens"] or 0),
            "total_cost_usd": float(row["total_cost_usd"] or 0),
            "trace_id": str(row["trace_id"]) if row["trace_id"] is not None else None,
            "created_at": _coerce_dt(row["created_at"]),
            "hit_count": int(row["hit_count"] or 0),
        }

    async def record_hit(self, cache_key: str) -> None:
        """Bump hit_count and update last_hit_at — best effort."""
        if not self._db.is_connected():
            return
        try:
            await self._db.execute(
                """
                UPDATE free_will.answer_cache
                   SET hit_count = hit_count + 1,
                       last_hit_at = now()
                 WHERE cache_key = $1
                """,
                cache_key,
            )
        except Exception:  # noqa: BLE001
            logger.exception("answer_cache: record_hit failed for %s", cache_key[:12])

    async def store(
        self,
        *,
        question: str,
        model: str,
        retrieval_mode: str,
        answer: str,
        citations: list[Any],
        passage_citations: list[Any],
        sources: list[Any],
        reasoning_path: dict[str, Any],
        total_tokens: int,
        total_cost_usd: float,
        trace_id: str | None,
    ) -> None:
        """Upsert a fresh cache entry.

        On conflict the row is fully overwritten, ``hit_count`` is reset to
        0, and ``created_at`` jumps to ``now()`` — re-rendering counts as a
        fresh entry so TTL restarts from the most recent synthesis.
        """
        if not self._db.is_connected():
            return

        key = self.cache_key(question, model, retrieval_mode)
        normalized = self.normalize_question(question)
        version = await self._current_kg_version()
        trace_uuid: UUID | None = None
        if trace_id:
            try:
                trace_uuid = UUID(trace_id)
            except (TypeError, ValueError) as _exc:
                del _exc
                trace_uuid = None

        try:
            await self._db.execute(
                """
                INSERT INTO free_will.answer_cache (
                    cache_key,
                    normalized_question,
                    raw_question,
                    model,
                    retrieval_mode,
                    answer,
                    citations_json,
                    passage_citations_json,
                    sources_json,
                    reasoning_path_json,
                    total_tokens,
                    total_cost_usd,
                    trace_id,
                    kg_version_at_creation,
                    hit_count,
                    last_hit_at,
                    created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb,
                    $11, $12, $13, $14,
                    0, NULL, now()
                )
                ON CONFLICT (cache_key) DO UPDATE SET
                    normalized_question = EXCLUDED.normalized_question,
                    raw_question = EXCLUDED.raw_question,
                    model = EXCLUDED.model,
                    retrieval_mode = EXCLUDED.retrieval_mode,
                    answer = EXCLUDED.answer,
                    citations_json = EXCLUDED.citations_json,
                    passage_citations_json = EXCLUDED.passage_citations_json,
                    sources_json = EXCLUDED.sources_json,
                    reasoning_path_json = EXCLUDED.reasoning_path_json,
                    total_tokens = EXCLUDED.total_tokens,
                    total_cost_usd = EXCLUDED.total_cost_usd,
                    trace_id = EXCLUDED.trace_id,
                    kg_version_at_creation = EXCLUDED.kg_version_at_creation,
                    hit_count = 0,
                    last_hit_at = NULL,
                    created_at = now()
                """,
                key,
                normalized,
                question,
                model,
                retrieval_mode,
                answer,
                json.dumps(citations, default=str),
                json.dumps(passage_citations, default=str),
                json.dumps(sources, default=str),
                json.dumps(reasoning_path, default=str),
                int(total_tokens),
                float(total_cost_usd),
                trace_uuid,
                int(version),
            )
        except Exception:  # noqa: BLE001
            logger.exception("answer_cache: store failed for key=%s", key[:12])


def _coerce_json(value: Any, *, default: Any) -> Any:
    """asyncpg may return JSONB as a string or as a parsed object."""
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError) as _exc:
            del _exc
            return default
    return value


def _coerce_dt(value: Any) -> datetime:
    """Normalise to a UTC-aware datetime for ISO serialisation."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    return datetime.now(UTC)
