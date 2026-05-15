"""TopicTagger — derive ``free_will.query_traces.topic_tags`` from a trace.

The community gallery filter chips (``/recherches``) match on
``topic_tags @> ARRAY[?]`` for both ``period`` and ``philosopher``
parameters. This module computes those tags automatically at the end of
every :class:`TraceWriter.finalize` call (best-effort hook) and is also
run by ``database/scripts/backfill_topic_tags.py`` over existing rows.

Three independent sources are unioned, deduped and sorted:

1. **Citations join** — ``final_answer_citations[].id`` is matched against
   ``passages.passage_id``; the join climbs to ``ancient_works`` (for the
   ``period`` and ``kg_work_id``) and to ``kg_edges`` (for the work's
   ``authored_by`` person). The dominant period across cited passages
   becomes the single ``period:*`` tag.
2. **Regex over the final answer** — ``person_<id>`` / ``school_<id>``
   node ids are routinely embedded by the proof-chain rendering, so we
   pick them up cheaply with a single ``\\b<prefix>[a-z0-9_]+\\b`` scan.
3. **Metadata seed lists** — ``metadata.touched_node_ids`` and
   ``metadata.seed_nodes`` if present.

No LLM calls. Pure SQL, parameterised, asyncpg. Cheap enough to run on
every finalize.

Tag format::

    period:<period>            # e.g. ``period:imperial``
    school:<school_node_id>    # e.g. ``school:school_stoics``
    person:<person_node_id>    # e.g. ``person:person_justin_martyr_2c_ce``

The output is capped at 25 tags, sorted alphabetically. The ``period:*``
tag is always exactly one (or omitted if no period information is
recoverable).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any
from uuid import UUID

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Period normalisation
# ---------------------------------------------------------------------------

# Canonical slugs that the frontend chip values are expected to match
# (see CANONICAL_PERIODS in knowledge graph semantic shapes).
_PERIOD_TO_SLUG: dict[str, str] = {
    # canonical KG period → slug
    "presocratic": "presocratic",
    "classical greek": "classical",
    "classical": "classical",
    "hellenistic": "hellenistic",
    "roman republican": "imperial",  # Roman republican texts roll up to imperial chip
    "roman imperial": "imperial",
    "imperial": "imperial",
    "patristic": "late_antiquity",
    "late antiquity": "late_antiquity",
    "late antique": "late_antiquity",
    "second temple judaism": "late_antiquity",
    "rabbinic": "late_antiquity",
    "medieval": "medieval",
    "early modern": "early_modern",
    "modern": "modern",
    "contemporary": "modern",
}

_ALLOWED_PERIOD_SLUGS: frozenset[str] = frozenset(
    {
        "presocratic",
        "classical",
        "hellenistic",
        "imperial",
        "late_antiquity",
        "medieval",
        "early_modern",
        "modern",
    }
)

_NODE_ID_RE: re.Pattern[str] = re.compile(r"\b((?:person|school)_[a-z0-9_]+)\b")
_TAG_RE: re.Pattern[str] = re.compile(r"^(period|school|person):[a-z][a-z0-9_]*$")

_MAX_TAGS: int = 25


def _normalize_period(raw: str | None) -> str | None:
    """Map a free-form KG period value to a canonical slug, or ``None``."""
    if not raw:
        return None
    key = raw.strip().lower()
    return _PERIOD_TO_SLUG.get(key)


def _is_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------------------
# TopicTagger
# ---------------------------------------------------------------------------


class TopicTagger:
    """Compute (and optionally persist) topic tags for a query trace."""

    def __init__(self, db: DatabaseService) -> None:
        self._db = db

    async def tag_trace(self, trace_id: str) -> list[str]:
        """Compute and return the tag list for ``trace_id`` (does not write)."""
        if not self._db.is_connected():
            return []

        row = await self._db.fetchrow(
            """
            SELECT
                final_answer_citations,
                final_answer_text,
                metadata
            FROM free_will.query_traces
            WHERE trace_id = $1::uuid
            """,
            trace_id,
        )
        if row is None:
            return []

        citations = _as_list_of_dicts(row.get("final_answer_citations"))
        answer_text = row.get("final_answer_text") or ""
        metadata = _as_dict(row.get("metadata"))

        persons: set[str] = set()
        schools: set[str] = set()
        period_counter: Counter[str] = Counter()

        # 1. Citation-driven derivation: join passages → works → kg_edges.
        passage_ids = [c.get("id") for c in citations if c.get("id")]
        passage_uuids = [pid for pid in passage_ids if pid and _is_uuid(str(pid))]
        if passage_uuids:
            cite_rows = await self._db.fetch(
                """
                SELECT
                    w.period AS period,
                    w.kg_work_id AS kg_work_id,
                    auth_edge.target_id AS person_id
                FROM passages p
                JOIN ancient_works w ON p.work_id = w.work_id
                LEFT JOIN kg_edges auth_edge
                       ON auth_edge.source_id = w.kg_work_id
                      AND auth_edge.relation = 'authored_by'
                WHERE p.passage_id = ANY($1::uuid[])
                """,
                passage_uuids,
            )
            for cite_row in cite_rows:
                period_slug = _normalize_period(cite_row.get("period"))
                if period_slug is not None:
                    period_counter[period_slug] += 1
                person_id = cite_row.get("person_id")
                if isinstance(person_id, str) and person_id.startswith("person_"):
                    persons.add(person_id)

        # 2. Regex over the rendered final answer.
        for match in _NODE_ID_RE.finditer(answer_text or ""):
            node_id = match.group(1)
            if node_id.startswith("person_"):
                persons.add(node_id)
            elif node_id.startswith("school_"):
                schools.add(node_id)

        # 3. Metadata seed / touched lists.
        for key in ("touched_node_ids", "seed_nodes"):
            for node_id in _iter_strings(metadata.get(key)):
                if node_id.startswith("person_"):
                    persons.add(node_id)
                elif node_id.startswith("school_"):
                    schools.add(node_id)

        # Assemble tags.
        tags: list[str] = []
        if period_counter:
            dominant_period, _ = period_counter.most_common(1)[0]
            if dominant_period in _ALLOWED_PERIOD_SLUGS:
                tags.append(f"period:{dominant_period}")

        tags.extend(f"person:{pid}" for pid in persons)
        tags.extend(f"school:{sid}" for sid in schools)

        # Keep only well-formed tags, dedupe and sort.
        validated = sorted({tag for tag in tags if _TAG_RE.match(tag)})
        return validated[:_MAX_TAGS]

    async def tag_and_persist(self, trace_id: str) -> list[str]:
        """Compute, write to ``free_will.query_traces.topic_tags``, return tags."""
        tags = await self.tag_trace(trace_id)
        if not self._db.is_connected():
            return tags
        try:
            await self._db.execute(
                """
                UPDATE free_will.query_traces
                SET topic_tags = $2::text[]
                WHERE trace_id = $1::uuid
                """,
                trace_id,
                tags,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "TopicTagger: failed to persist topic_tags for %s", trace_id
            )
        return tags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        import json

        try:
            decoded = json.loads(value)
        except TypeError, ValueError:
            return []
        value = decoded
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        import json

        try:
            decoded = json.loads(value)
        except TypeError, ValueError:
            return {}
        value = decoded
    return value if isinstance(value, dict) else {}


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []
