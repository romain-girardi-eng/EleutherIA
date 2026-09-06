"""AnswerCache — replay-cache for /api/graphrag/query/stream answers.

A persistent (normalized_question, model, retrieval_mode, mode) -> final
answer cache, stored in ``free_will.answer_cache``. ``mode`` ('fast' |
'deep') segments the key: deep (counter-evidence) and fast answers must
never share a cache slot. Looked up by the SSE endpoint
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

Rollback hazard — ``__answer_provenance__`` piggyback: :meth:`AnswerCache.store`
packs the answer provenance (metadata + claim_ledger) into
``reasoning_path_json`` under the reserved ``__answer_provenance__`` key
(no schema migration), and :meth:`AnswerCache.lookup` strips it back out.
Old code (pre-piggyback) returns ``reasoning_path_json`` verbatim, so on a
code rollback any row written by the new code replays a ``reasoning_path``
that still contains the raw ``__answer_provenance__`` blob — leaking
verification metadata into the reasoning-path UI. Safe rollback procedure:
clear the cache (``TRUNCATE free_will.answer_cache`` or bump
``free_will.kg_version``) when reverting to a build that predates the
marker.

Threading: the service holds no state — every public method does its work
through the shared :class:`DatabaseService` connection pool. Safe to share
across coroutines.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from eleutheria_database.services.db import DatabaseService
from eleutheria_graphrag.public_payload import public_payload

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")
_KEY_SEP = "\x1f"  # ASCII unit-separator — never appears in user text

# Cache schema version — folded into every cache key. This is the MANUAL
# OVERRIDE lever: bump it to force-invalidate every stored row at once (e.g.
# when the SHAPE/CONTENT of a stored payload changes in a way unrelated to the
# synthesis prompt). v2 (GOAL-8): rows written before citation resolution
# persisted RAW node ids (b_…, scholarly_argument_…, concept_…) as citation
# labels; bumping made every such row MISS, a code-only non-destructive purge.
#
# F5: this constant is now only the MANUAL base segment. The EFFECTIVE version
# folded into the cache key is :func:`_effective_cache_version`, which mixes
# this base with a hash of the live scholar-RAG synthesis prompt + an optional
# build SHA — so ANY prompt/logic change AUTO-invalidates the cache without a
# hand-bump (the bug that masked GOAL-7 fixes with stale pre-fix answers).
# v5 also rejects unregistered inline citations and excludes verifier prose.
_CACHE_SCHEMA_VERSION = "v5"

# Optional build/git SHA: when set (e.g. by the deploy pipeline) it is folded
# into the cache version so a code rollout that changes scholar-RAG LOGIC —
# even without touching the prompt text — also auto-invalidates the cache.
_BUILD_SHA_ENV = "ELEUTHERIA_BUILD_SHA"


def _synthesis_prompt_fingerprint() -> str:
    """Short hash of the live dialectical-synthesis prompt text (F5).

    Imports the scholar-RAG synthesis SYSTEM + TEMPLATE constants and hashes
    them so any edit to the prompt auto-invalidates every cached answer. The
    import is best-effort: ``answer_cache`` is also usable standalone (CLI,
    tests) where graphrag may be absent — then we degrade to a static marker
    so the cache key stays stable rather than crashing. Backend → graphrag is
    the allowed dependency direction, so this never creates a cycle.
    """
    try:
        from eleutheria_graphrag.agents.dialectical_synthesis import (
            DIALECTICAL_SYNTHESIS_SYSTEM,
            DIALECTICAL_SYNTHESIS_TEMPLATE,
        )
    except Exception:  # noqa: BLE001 - graphrag optional; never crash key derivation
        return "noprompt"
    blob = f"{DIALECTICAL_SYNTHESIS_SYSTEM}\x1f{DIALECTICAL_SYNTHESIS_TEMPLATE}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _effective_cache_version() -> str:
    """The version segment actually folded into the cache key (F5).

    ``{manual_base}.{prompt_fingerprint}[.{build_sha}]`` — derived, not
    hand-bumped, so any change to the synthesis prompt (or, when set, the build
    SHA) makes every prior row MISS automatically. The manual
    :data:`_CACHE_SCHEMA_VERSION` base is preserved as an explicit override.

    Computed once and memoised: the prompt text is import-time-constant and the
    env SHA is fixed for the process lifetime, so recomputing per key is waste.
    """
    cached = getattr(_effective_cache_version, "_value", None)
    if cached is not None:
        return cached  # type: ignore[no-any-return]
    parts = [_CACHE_SCHEMA_VERSION, _synthesis_prompt_fingerprint()]
    build_sha = (os.environ.get(_BUILD_SHA_ENV) or "").strip()
    if build_sha:
        parts.append(build_sha[:12])
    value = ".".join(parts)
    _effective_cache_version._value = value  # type: ignore[attr-defined]
    return value


# Reserved key inside ``reasoning_path_json`` used to piggyback the answer
# provenance (metadata + claim_ledger) without a schema migration. Stripped
# back out on lookup so the replayed ``reasoning_path`` keeps its shape.
_PROVENANCE_KEY = "__answer_provenance__"


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
    def cache_key(
        question: str, model: str, retrieval_mode: str, mode: str = "fast"
    ) -> str:
        """Stable sha256 hex digest over the normalised key tuple.

        ``mode`` ('fast' | 'deep') is part of the key: deep answers carry
        counter-evidence ledger items that fast answers must never replay,
        and a deep request must never silently reuse a fast answer (mirrors
        ``ResponseCache._key`` in graphrag_service). Rows written before the
        ``mode`` segment existed simply miss — no migration needed.

        A trailing version segment lets us invalidate every stored row at once
        (GOAL-8: purge rows that persisted leaked raw-id citation labels) — no
        ``TRUNCATE`` required. F5: that segment is now DERIVED by
        :func:`_effective_cache_version` (manual base + a hash of the live
        synthesis prompt + optional build SHA), so any prompt/logic change
        auto-invalidates the cache; the manual base stays an override lever.
        """
        parts = (
            AnswerCache.normalize_question(question)
            + _KEY_SEP
            + model
            + _KEY_SEP
            + retrieval_mode
            + _KEY_SEP
            + (mode or "fast")
            + _KEY_SEP
            + _effective_cache_version()
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
        mode: str = "fast",
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
                "metadata": dict,        # answer provenance (may be empty)
                "claim_ledger": list,    # typed claims (may be empty)
                "total_tokens": int,
                "total_cost_usd": float,
                "trace_id": str | None,
                "created_at": datetime,
                "hit_count": int,
            }
        """
        if not self._db.is_connected():
            return None

        key = self.cache_key(question, model, retrieval_mode, mode)
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

        reasoning_path = _coerce_json(row["reasoning_path_json"], default={})
        provenance: dict[str, Any] = {}
        if isinstance(reasoning_path, dict):
            raw_provenance = reasoning_path.pop(_PROVENANCE_KEY, None)
            if isinstance(raw_provenance, dict):
                provenance = raw_provenance

        return {
            "cache_key": row["cache_key"],
            "answer": row["answer"],
            "citations": _coerce_json(row["citations_json"], default=[]),
            "passage_citations": _coerce_json(
                row["passage_citations_json"], default=[]
            ),
            "sources": _coerce_json(row["sources_json"], default=[]),
            "reasoning_path": public_payload(reasoning_path),
            "metadata": public_payload(provenance.get("metadata") or {}),
            "claim_ledger": public_payload(
                {"claim_ledger": provenance.get("claim_ledger") or []}
            )["claim_ledger"],
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
        mode: str = "fast",
        answer: str,
        citations: list[Any],
        passage_citations: list[Any],
        sources: list[Any],
        reasoning_path: dict[str, Any],
        total_tokens: int,
        total_cost_usd: float,
        trace_id: str | None,
        metadata: dict[str, Any] | None = None,
        claim_ledger: list[Any] | None = None,
    ) -> None:
        """Upsert a fresh cache entry.

        On conflict the row is fully overwritten, ``hit_count`` is reset to
        0, and ``created_at`` jumps to ``now()`` — re-rendering counts as a
        fresh entry so TTL restarts from the most recent synthesis.

        ``metadata`` and ``claim_ledger`` carry the answer provenance
        (text_verification, grounding, citation_verifier_v2, research-graph
        keys, typed claims). They are packed into ``reasoning_path_json``
        under :data:`_PROVENANCE_KEY` — no schema change — and unpacked by
        :meth:`lookup` so cache replays keep the full verification contract.
        """
        if not self._db.is_connected():
            return

        if metadata or claim_ledger:
            reasoning_path = {
                **reasoning_path,
                _PROVENANCE_KEY: {
                    "metadata": metadata or {},
                    "claim_ledger": claim_ledger or [],
                },
            }

        reasoning_path = public_payload(reasoning_path)
        key = self.cache_key(question, model, retrieval_mode, mode)
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
