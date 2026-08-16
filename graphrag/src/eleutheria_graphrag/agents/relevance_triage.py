"""LLM relevance triage — semantic priority for the prompt fitter (optional stage).

WHY THIS EXISTS. The synthesis prompt fitter
(:mod:`eleutheria_graphrag.agents.prompt_budget` +
:func:`eleutheria_graphrag.agents.controversy_map.fit_controversy_frames_layer`)
decides WHAT survives into the prompt with structural and lexical rules only:
round-robin across frames, then question-term overlap inside an excerpt window.
That is fair but semantically blind — a real run surfaced 4,389 position claims,
and which 200 of them the fitter kept was decided by frame order, not by whether
the claim answers the question.

This module adds an OPTIONAL stage between map assembly and prompt fitting: a
fast utility model reads each candidate item (id + a short snippet) and returns a
0-10 pertinence score. The fitter then sheds the LOWEST-scoring items first
within each shed step, instead of the last ones in round-robin order.

HARD RULES.

* **The triage model only ever scores.** Its output is parsed into
  ``{item_id: float}`` and nothing else; not one character of model text can
  reach the synthesis prompt. Academic integrity is therefore unaffected: the
  stage can only reorder evidence the retrieval layer already produced.
* **It can never fail a query.** Timeout, transport error, malformed JSON, a
  provider outage — every failure path returns whatever scores did arrive (or
  none at all), and the fitter falls back to the existing lexical ordering.
* **Off by default.** ``ELEUTHERIA_RELEVANCE_TRIAGE`` gates the whole stage.

The fitter never mutates the :class:`~eleutheria_graphrag.agents.state.ControversyMap`:
scores travel as a side dict keyed by the namespaced ids built here
(:func:`position_key`, :func:`passage_key`, :func:`exegesis_key`).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from eleutheria_graphrag.services.json_extractor import extract_json
from eleutheria_graphrag.services.llm_service import (
    UTILITY_TIER,
    gemini_proxy_enabled,
    resolve_gemini_light_model,
)

logger = logging.getLogger(__name__)

__all__ = [
    "MAX_SCORE",
    "NEUTRAL_SCORE",
    "TriageItem",
    "TriageResult",
    "exegesis_key",
    "parse_triage_scores",
    "passage_key",
    "position_key",
    "prioritize",
    "relevance_triage_enabled",
    "score_relevance",
    "snippet",
    "triage_model",
]


#: Score range the model is asked for.
MAX_SCORE = 10.0

#: Priority given to an item the triage never scored (budget cap, failed batch).
#: Mid-scale, so an unscored item outranks what the model judged irrelevant and
#: yields to what it judged pertinent — never a silent demotion of everything
#: the triage could not reach.
NEUTRAL_SCORE = 5.0

#: Items per request. Measured on the production proxy: a 120-item batch is a
#: ~3-4 s flash call, and fewer batches keeps the stage clear of the provider's
#: sliding-window rate limiter. A malformed response costs only its own slice.
BATCH_SIZE = 120

#: Batches in flight at once.
MAX_PARALLEL = 4

#: Ceiling on how many items are sent at all. Beyond it the tail keeps the
#: existing lexical ordering (it is the tail the fitter sheds first anyway).
MAX_ITEMS = 720

#: Whole-stage wall-clock budget. On expiry the pending batches are cancelled
#: and whatever already returned is used.
BUDGET_SECONDS = 20.0

#: Snippet length per item. Enough to judge pertinence, short enough that 60
#: items fit comfortably in one utility-tier call.
SNIPPET_CHARS = 300

_TRIAGE_SYSTEM = (
    "You rank research material by relevance. You output ONLY JSON scores — "
    "never prose, never a summary, never any text drawn from the items. You do "
    "not judge truth, quality or scholarship: only how directly each item bears "
    "on the question asked."
)

_TRIAGE_TEMPLATE = """\
QUESTION: {question}

Score how directly each item below bears on that question, from 0 (irrelevant) \
to 10 (central evidence for answering it).

Return ONLY this JSON object, one entry per item id, no other text:
{{"scores": [{{"id": "<item id>", "score": <0-10>}}]}}

ITEMS:
{items}
"""

_TRIAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "number"},
                },
                "required": ["id", "score"],
            },
        }
    },
    "required": ["scores"],
}


# ── item identity ────────────────────────────────────────────────────────────
#
# Namespaced so a position and a passage can never collide in the side dict, and
# so a passage scored as contested evidence is distinct from the same text
# pooled as standalone exegesis (they are shed by different steps).


def position_key(position_id: str) -> str:
    return f"pos:{position_id}"


def passage_key(passage_id: str) -> str:
    return f"psg:{passage_id}"


def exegesis_key(passage_id: str) -> str:
    return f"exe:{passage_id}"


@dataclass(frozen=True)
class TriageItem:
    """One scoreable unit: its side-dict key and the snippet the model reads."""

    key: str
    snippet: str


@dataclass
class TriageResult:
    """Scores plus the observability the INFO line reports."""

    scores: dict[str, float] = field(default_factory=dict)
    model: str = ""
    batches: int = 0
    failures: int = 0
    elapsed: float = 0.0
    items_submitted: int = 0

    def log_line(self) -> str:
        return (
            f"relevance triage: scored {len(self.scores)} items in "
            f"{self.elapsed:.1f}s via {self.model or 'utility tier'} "
            f"({self.batches} batches, {self.failures} failures)"
        )


# ── configuration ────────────────────────────────────────────────────────────


def relevance_triage_enabled() -> bool:
    """Whether the triage stage runs. ``ELEUTHERIA_RELEVANCE_TRIAGE``, default off."""
    return (os.getenv("ELEUTHERIA_RELEVANCE_TRIAGE") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def triage_model() -> str:
    """The triage ``model_override``, or "" for "let the utility tier decide".

    ``ELEUTHERIA_TRIAGE_MODEL`` pins it. Otherwise the Gemini light model is used
    when the Gemini proxy is configured (a fast, subscription-billed flash model
    is exactly the right shape for this), and an empty string otherwise — the
    call then goes through the normal provider loop at
    :data:`~eleutheria_graphrag.services.llm_service.UTILITY_TIER`.
    """
    pinned = (os.getenv("ELEUTHERIA_TRIAGE_MODEL") or "").strip()
    if pinned:
        return pinned
    if gemini_proxy_enabled():
        return resolve_gemini_light_model()
    return ""


def _env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw:
        try:
            return max(minimum, min(maximum, float(raw)))
        except ValueError:
            pass
    return default


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw:
        try:
            return max(minimum, min(maximum, int(raw)))
        except ValueError:
            pass
    return default


def triage_budget_seconds() -> float:
    """Whole-stage wall-clock budget; ``ELEUTHERIA_TRIAGE_TIMEOUT`` overrides."""
    return _env_float(
        "ELEUTHERIA_TRIAGE_TIMEOUT", BUDGET_SECONDS, minimum=0.1, maximum=120.0
    )


def triage_max_items() -> int:
    """Item ceiling; ``ELEUTHERIA_TRIAGE_MAX_ITEMS`` overrides."""
    return _env_int(
        "ELEUTHERIA_TRIAGE_MAX_ITEMS", MAX_ITEMS, minimum=BATCH_SIZE, maximum=6000
    )


# ── parsing (defensive: the proxy may or may not honour json_schema) ──────────


def _coerce_score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        score = float(value)
    elif isinstance(value, str):
        try:
            score = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if score != score:  # NaN
        return None
    return max(0.0, min(MAX_SCORE, score))


def _score_entries(payload: Any) -> list[Any]:
    """The list of ``{id, score}`` entries inside whatever the model returned.

    Accepts the requested ``{"scores": [...]}`` object, a bare array (some
    providers ignore the wrapper), or any single-key object whose value is an
    array — the shapes a degraded ``json_object`` response actually takes.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("scores", "items", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for value in payload.values():
            if isinstance(value, list):
                return value
    return []


def parse_triage_scores(raw: str, id_map: Mapping[str, str]) -> dict[str, float]:
    """Parse one batch response into ``{item_key: score}``.

    ``id_map`` maps the per-batch id the model was shown to the side-dict key.
    Everything unrecognised is DROPPED rather than guessed: an unknown id, a
    missing/NaN/non-numeric score, a bare string entry. A partially valid
    response therefore yields its valid part, and a fully malformed one yields
    ``{}`` — both are fine, because an unscored item simply keeps the lexical
    ordering.
    """
    if not raw or not raw.strip():
        return {}
    try:
        payload = extract_json(raw)
    except Exception:  # noqa: BLE001 — JSONExtractionError and friends
        return {}

    out: dict[str, float] = {}
    for entry in _score_entries(payload):
        if not isinstance(entry, dict):
            continue
        raw_id = entry.get("id", entry.get("item_id", entry.get("index")))
        if raw_id is None:
            continue
        key = id_map.get(str(raw_id).strip())
        if key is None:
            continue
        score = _coerce_score(entry.get("score", entry.get("relevance")))
        if score is None:
            continue
        out[key] = score
    return out


# ── scoring ──────────────────────────────────────────────────────────────────


def snippet(text: str) -> str:
    """One-line, length-capped snippet (the model only needs the gist)."""
    flat = " ".join((text or "").split())
    if len(flat) <= SNIPPET_CHARS:
        return flat
    return flat[:SNIPPET_CHARS].rstrip() + "…"


def _batches(items: Sequence[TriageItem]) -> list[list[TriageItem]]:
    return [
        list(items[start : start + BATCH_SIZE])
        for start in range(0, len(items), BATCH_SIZE)
    ]


async def _score_batch(
    question: str,
    batch: Sequence[TriageItem],
    llm: Any,
    *,
    model: str,
    timeout: float,
) -> dict[str, float]:
    """Score one batch. Returns ``{}`` on ANY failure (never raises)."""
    # Per-batch ids are the batch-local index: short (cheap tokens), and a model
    # that garbles a long KG id cannot silently mis-attribute a score.
    id_map = {str(idx): item.key for idx, item in enumerate(batch)}
    lines = "\n".join(
        f"[{idx}] {item.snippet}" for idx, item in enumerate(batch) if item.snippet
    )
    if not lines:
        return {}
    prompt = _TRIAGE_TEMPLATE.format(question=question, items=lines)
    raw = await llm.generate(
        prompt,
        system_prompt=_TRIAGE_SYSTEM,
        temperature=0.0,
        max_tokens=4096,
        model_override=model or None,
        response_json_schema=_TRIAGE_SCHEMA,
        request_timeout=timeout,
        tier=UTILITY_TIER,
    )
    scores = parse_triage_scores(raw or "", id_map)
    if not scores:
        # Silent-empty batches are the one failure mode that is invisible
        # without the raw payload — name it so tuning is evidence-based.
        head = (raw or "").strip().replace("\n", " ")[:200]
        logger.warning(
            "relevance triage batch yielded no scores (raw head: %r)", head or "<empty>"
        )
    return scores


async def score_relevance(
    question: str,
    items: Sequence[TriageItem],
    llm: Any,
    *,
    model: str | None = None,
) -> TriageResult:
    """Score ``items`` for pertinence to ``question``. NEVER raises.

    Batches of :data:`BATCH_SIZE`, at most :data:`MAX_PARALLEL` in flight, the
    whole stage under :func:`triage_budget_seconds`. Batches that fail or do not
    return in time contribute nothing and are counted as failures; their items
    keep the fitter's existing lexical ordering.
    """
    started = time.monotonic()
    resolved_model = triage_model() if model is None else model
    submitted = list(items)[: triage_max_items()]
    result = TriageResult(model=resolved_model, items_submitted=len(submitted))
    if not submitted:
        return result

    batches = _batches(submitted)
    result.batches = len(batches)
    budget = triage_budget_seconds()
    semaphore = asyncio.Semaphore(MAX_PARALLEL)

    async def _run(batch: list[TriageItem]) -> dict[str, float]:
        async with semaphore:
            try:
                return await _score_batch(
                    question, batch, llm, model=resolved_model, timeout=budget
                )
            except Exception as exc:  # noqa: BLE001 — triage must never fail a query
                logger.warning("relevance triage batch failed (%s)", exc)
                return {}

    tasks = [asyncio.create_task(_run(batch)) for batch in batches]
    try:
        done = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True), timeout=budget
        )
    except TimeoutError:
        # Our own budget only. An outer CancelledError (client disconnect, query
        # cancelled) is deliberately NOT caught: it must keep propagating.
        logger.warning(
            "relevance triage exceeded its %.1fs budget; using partial scores", budget
        )
        done = []
        for task in tasks:
            if task.done() and not task.cancelled():
                exc = task.exception()
                done.append({} if exc is not None else task.result())
            else:
                task.cancel()
                done.append({})

    for outcome in done:
        if isinstance(outcome, dict) and outcome:
            result.scores.update(outcome)
        else:
            result.failures += 1

    result.elapsed = time.monotonic() - started
    logger.info(result.log_line())
    return result


# ── consumption helper (shared by every shed step in the fitter) ──────────────


def prioritize[T](
    items: Sequence[T],
    key_of: Callable[[T], str],
    relevance: Mapping[str, float] | None,
) -> list[T]:
    """Order ``items`` by triage score, lexical/structural order as tiebreak.

    With no scores (triage off, or every batch failed) the sequence is returned
    UNCHANGED — the existing ordering is the fallback, exactly as before. With
    scores, items sort by descending score and, at equal score, by their original
    position: the fitter's round-robin fairness survives inside a score band, and
    the lowest-scoring items land at the end where the shed steps cut.
    """
    ordered = list(items)
    if not relevance:
        return ordered
    scores = relevance
    return [
        item
        for _idx, item in sorted(
            enumerate(ordered),
            key=lambda pair: (-scores.get(key_of(pair[1]), NEUTRAL_SCORE), pair[0]),
        )
    ]
