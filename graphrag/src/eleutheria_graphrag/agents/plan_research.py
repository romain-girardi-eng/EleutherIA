"""Question -> scholarly-answer-shape planner (Scholar-RAG M2, ARCHITECTURE §1).

Replaces the keyword facet picker (``_default_research_facets``) on the
Scholar-RAG path. One cheap Fireworks ``kimi-k2p6`` JSON-mode call classifies the
question into ONE primary + optional secondary :class:`AnswerShape` and emits a
typed :class:`ResearchPlan` — a *retrieval program* (a small DAG of
:class:`GraphPattern`), not a fixed list of section titles.

The classifier is given the **inventory header** (counts of debate nodes + the
``opposes`` edge-list shape) so it knows the graph HAS a disagreement layer to
target. Default-when-ambiguous is ``survey_of_debates`` — the failing trigger
lands there (it currently mis-routes to Definition/Textual-Basis/Counterpoint,
failure-map F6).

``factual_lookup`` short-circuits: a single ``get_node_detail``, no synthesis
loop.

The planner is **gated by ELEUTHERIA_SCHOLAR_RAG at the call site**; this module
is import-safe and inert until a consumer invokes ``plan_research``. It carries a
deterministic heuristic so it works (and is tested) without an LLM, and degrades
to that heuristic when the LLM call fails — never raising into the pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from eleutheria_graphrag.agents.state import (
    AnswerShape,
    GraphPattern,
    ResearchPlan,
)

logger = logging.getLogger(__name__)

# ── Heuristic intent cues per shape (ARCHITECTURE §1 trigger column) ─────────
# Ordered by specificity: the FIRST matching shape wins, so the more specific
# intents (factual lookup, named locus, "did A know B") are checked before the
# broad survey/doxography defaults.

_FACTUAL_CUES: tuple[str, ...] = (
    "when did",
    "what year",
    "what date",
    "where was",
    "where did",
    "who was the teacher of",
    "what is the death date",
    "birth date of",
    "death date of",
)

# A named primary locus, e.g. "Cic. Fat. 41", "De Fato 12", "Republic 617e".
_LOCUS_RE = re.compile(
    r"\b(?:[A-Z][a-z]+\.?\s+)?[A-Z][a-z]+\.?\s+\d+[a-z]?(?:[.,–-]\d+)?\b"
)
_EXEGESIS_CUES: tuple[str, ...] = (
    "what does",
    "passage",
    "this text",
    "the line",
    "interpret",
    "exegesis",
    "translate",
    "construe",
)

_TRANSMISSION_CUES: tuple[str, ...] = (
    "did .* know",
    "source of",
    "influenced by",
    "transmission",
    "how .* reached",
    "borrow",
    "derive .* from",
    "where did .* get",
)

_GENEALOGY_CUES: tuple[str, ...] = (
    "origin",
    "emergence",
    "emerge",
    "history of",
    "who invented",
    "invention of",
    "first to",
    "development of",
    "genealogy",
    "rise of",
)

_COMPARISON_CUES: tuple[str, ...] = (
    " vs ",
    " versus ",
    "compare",
    "comparison",
    "differ from",
    "agree with",
    "disagree with",
    "did .* agree",
)

_DOXOGRAPHY_CUES: tuple[str, ...] = (
    "what did the stoics",
    "what did the epicureans",
    "what did the .* hold",
    "doctrine of the",
    "the .* view of",
    "stoic doctrine",
    "school .* held",
)

_SURVEY_CUES: tuple[str, ...] = (
    "open debate",
    "open debates",
    "controvers",
    "contested",
    "live debate",
    "current scholarship",
    "what's contested",
    "what is contested",
    "state of the question",
    "scholarly disagreement",
)


def _matches(question: str, cues: tuple[str, ...]) -> bool:
    low = question.lower()
    for cue in cues:
        if " .* " in cue or ".*" in cue:
            if re.search(cue, low):
                return True
        elif cue in low:
            return True
    return False


def classify_shape_heuristic(question: str) -> AnswerShape:
    """Deterministic shape classifier (no LLM).

    Ordered most-specific-first; defaults to ``survey_of_debates`` so the failing
    trigger ("big open debates about free will in antiquity") routes correctly.
    """
    if _matches(question, _FACTUAL_CUES):
        return AnswerShape.FACTUAL_LOOKUP
    if _matches(question, _SURVEY_CUES):
        return AnswerShape.SURVEY_OF_DEBATES
    if _matches(question, _COMPARISON_CUES):
        return AnswerShape.POSITION_COMPARISON
    if _matches(question, _TRANSMISSION_CUES):
        return AnswerShape.TRANSMISSION_TRACE
    if _matches(question, _GENEALOGY_CUES):
        return AnswerShape.CONCEPT_GENEALOGY
    if _matches(question, _DOXOGRAPHY_CUES):
        return AnswerShape.DOXOGRAPHICAL_SYNTHESIS
    # A named locus with an exegetical verb => primary-text exegesis.
    if _LOCUS_RE.search(question) and _matches(question, _EXEGESIS_CUES):
        return AnswerShape.PRIMARY_TEXT_EXEGESIS
    return AnswerShape.SURVEY_OF_DEBATES


# ── Per-shape graph-pattern skeletons (the DAG entry patterns, §1 table) ─────


def _patterns_for_shape(shape: AnswerShape, question: str) -> list[GraphPattern]:
    """The graph-entry pattern(s) for a shape (ARCHITECTURE §1 table)."""
    q = question.strip()
    if shape == AnswerShape.SURVEY_OF_DEBATES:
        return [
            GraphPattern(
                intent="locate the live fault lines on the topic",
                entry="debate",
                seed_query=q,
                edge_program=["participates_in", "opposes", "critiques"],
                depth=2,
            ),
            GraphPattern(
                intent="ground each surfaced position in primary text",
                entry="position",
                seed_query=q,
                edge_program=["evidenced_by", "cites_primary_source"],
                depth=1,
            ),
        ]
    if shape == AnswerShape.CONCEPT_GENEALOGY:
        return [
            GraphPattern(
                intent="trace the concept's chain + the dating dispute",
                entry="concept",
                seed_query=q,
                edge_program=["precedes", "influenced_by", "participates_in"],
                depth=3,
            ),
        ]
    if shape == AnswerShape.TRANSMISSION_TRACE:
        return [
            GraphPattern(
                intent="follow the source-stemma + the dispute over it",
                entry="person",
                seed_query=q,
                edge_program=[
                    "participates_in",
                    "cites_primary_source",
                    "opposes",
                ],
                depth=3,
            ),
        ]
    if shape == AnswerShape.POSITION_COMPARISON:
        return [
            GraphPattern(
                intent="anchor the two positions and the edge between them",
                entry="position",
                seed_query=q,
                edge_program=["opposes", "contrasts_with", "agrees_with"],
                depth=1,
            ),
        ]
    if shape == AnswerShape.PRIMARY_TEXT_EXEGESIS:
        return [
            GraphPattern(
                intent="pull the passage + its _en pair + interpretation history",
                entry="passage",
                seed_query=q,
                edge_program=["discusses", "interprets", "critiques"],
                depth=2,
            ),
        ]
    if shape == AnswerShape.DOXOGRAPHICAL_SYNTHESIS:
        return [
            GraphPattern(
                intent="cluster the school's doctrine + ancient counter-positions",
                entry="school",
                seed_query=q,
                edge_program=["member_of", "critiques"],
                depth=2,
            ),
        ]
    # factual_lookup: a single node detail, no traversal program.
    return [
        GraphPattern(
            intent="single-node factual lookup",
            entry="person",
            seed_query=q,
            edge_program=[],
            depth=0,
            want_bilingual=False,
        )
    ]


def _skeleton_for_shape(shape: AnswerShape) -> list[str]:
    """ADAPTIVE answer-skeleton HINTS (the synthesiser may override these)."""
    return {
        AnswerShape.SURVEY_OF_DEBATES: [
            "one movement per fault line",
            "name two sides + the edge for each",
            "close with what remains genuinely open",
        ],
        AnswerShape.CONCEPT_GENEALOGY: [
            "chronological",
            "foreground the dating dispute",
        ],
        AnswerShape.TRANSMISSION_TRACE: [
            "source-stemma",
            "the scholarly dispute over the source",
        ],
        AnswerShape.POSITION_COMPARISON: ["symmetric point-by-point"],
        AnswerShape.PRIMARY_TEXT_EXEGESIS: [
            "quote-first",
            "philological",
            "interpretation history",
        ],
        AnswerShape.DOXOGRAPHICAL_SYNTHESIS: [
            "doctrine + ancient counter-positions",
        ],
        AnswerShape.FACTUAL_LOOKUP: ["two-sentence answer, no synthesis loop"],
    }.get(shape, [])


def _budget_tier_for_shape(shape: AnswerShape) -> str:
    if shape == AnswerShape.FACTUAL_LOOKUP:
        return "quick"
    if shape in {AnswerShape.SURVEY_OF_DEBATES, AnswerShape.TRANSMISSION_TRACE}:
        return "deep"
    return "standard"


def plan_from_shape(
    question: str,
    primary: AnswerShape,
    secondary: AnswerShape | None = None,
    rationale: str = "",
) -> ResearchPlan:
    """Assemble a ResearchPlan from a chosen primary (+ optional secondary) shape."""
    patterns = _patterns_for_shape(primary, question)
    if secondary is not None and secondary != primary:
        patterns = patterns + _patterns_for_shape(secondary, question)
    return ResearchPlan(
        primary_shape=primary,
        secondary_shape=secondary,
        patterns=patterns,
        answer_skeleton=_skeleton_for_shape(primary),
        budget_tier=_budget_tier_for_shape(primary),
        rationale=rationale or "heuristic shape classification",
    )


# ── Inventory header (so the classifier knows the graph HAS a debate layer) ──


class GraphInventory(BaseModel):
    """Counts the classifier is shown so it can target the disagreement layer."""

    debate_node_count: int = 0
    opposes_edge_count: int = 0
    critiques_edge_count: int = 0
    position_node_count: int = 0


def build_inventory_header(inventory: GraphInventory) -> str:
    """Render the inventory header for the planner prompt (ARCHITECTURE §1)."""
    return (
        "GRAPH INVENTORY (the graph has a relational disagreement layer): "
        f"{inventory.debate_node_count} debate/controversy nodes; "
        f"{inventory.opposes_edge_count} `opposes` edges; "
        f"{inventory.critiques_edge_count} `critiques` edges; "
        f"{inventory.position_node_count} scholarly-position nodes. "
        "A question about open debates, controversies, origins, or comparisons "
        "should target this layer, not entity descriptions."
    )


# ── LLM planner (cheap Fireworks kimi-k2p6 JSON-mode call) ───────────────────

PLAN_RESEARCH_SYSTEM = (
    "You are a retrieval planner for a vectorless graph-RAG over a knowledge "
    "graph of ancient-philosophy scholarship. Classify the question into ONE "
    "primary answer shape (and an optional secondary). Shapes: "
    "survey_of_debates, concept_genealogy, transmission_trace, "
    "position_comparison, primary_text_exegesis, doxographical_synthesis, "
    "factual_lookup. When ambiguous, prefer survey_of_debates. Emit STRICT JSON "
    'with keys: {"primary_shape": <shape>, "secondary_shape": <shape|null>, '
    '"rationale": <one sentence>}. No prose outside the JSON.'
)

PLAN_RESEARCH_TEMPLATE = "{inventory}\n\nQUESTION: {question}\n\nReturn the JSON only."


class _PlanLLMResult(BaseModel):
    primary_shape: AnswerShape = AnswerShape.SURVEY_OF_DEBATES
    secondary_shape: AnswerShape | None = None
    rationale: str = Field(default="")


def _coerce_shape(value: Any) -> AnswerShape | None:
    if value is None:
        return None
    try:
        return AnswerShape(str(value).strip().lower())
    except ValueError:
        return None


def _parse_plan_json(raw: str) -> _PlanLLMResult:
    """Tolerant JSON parse: strip code fences, find the first object."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    payload = json.loads(match.group(0) if match else text)
    primary = _coerce_shape(payload.get("primary_shape"))
    secondary = _coerce_shape(payload.get("secondary_shape"))
    return _PlanLLMResult(
        primary_shape=primary or AnswerShape.SURVEY_OF_DEBATES,
        secondary_shape=secondary,
        rationale=str(payload.get("rationale", "") or ""),
    )


async def plan_research(
    question: str,
    llm: Any | None = None,
    *,
    inventory: GraphInventory | None = None,
    model_override: str | None = None,
) -> ResearchPlan:
    """Classify ``question`` into a typed ResearchPlan (Scholar-RAG M2).

    With ``llm`` provided, one cheap JSON-mode call picks the shape; on any
    failure (or with ``llm=None``), the deterministic heuristic is used. The
    typed pattern DAG is always assembled locally from the chosen shape, so the
    LLM only ever decides the *shape*, never the (auditable) ``edge_program``.
    """
    if llm is None:
        shape = classify_shape_heuristic(question)
        return plan_from_shape(question, shape, rationale="heuristic (no llm)")

    header = build_inventory_header(inventory or GraphInventory())
    prompt = PLAN_RESEARCH_TEMPLATE.format(inventory=header, question=question)
    try:
        raw = await llm.generate(
            prompt,
            system_prompt=PLAN_RESEARCH_SYSTEM,
            temperature=0.0,
            max_tokens=1500,
            cache_key="scholar-rag-planner",
            cache_prefix="scholar_rag_plan_v1",
            model_override=model_override,
        )
        result = _parse_plan_json(raw)
        return plan_from_shape(
            question,
            result.primary_shape,
            result.secondary_shape,
            rationale=result.rationale or "llm shape classification",
        )
    except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
        logger.debug("plan_research LLM path failed (%s); using heuristic", exc)
    except Exception as exc:  # pragma: no cover - defensive, never raise upstream
        logger.warning("plan_research LLM call errored (%s); using heuristic", exc)
    shape = classify_shape_heuristic(question)
    return plan_from_shape(question, shape, rationale="heuristic fallback")
