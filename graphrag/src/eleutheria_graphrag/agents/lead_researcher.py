"""Lead-researcher pipeline (``agent_mode="lead"``).

An orchestrator that DECOMPOSES the question into 2-5 research facets,
DELEGATES each facet to a bounded retrieval sub-agent (a ``NativeAgentLoop``
over a restricted tool registry, on the utility-tier model), collects the
DISTILLED DOSSIERS they return (typed :class:`ResearchDossier`, never prose),
MERGES them into one bounded evidence set + ControversyMap, and then WRITES THE
ANSWER ITSELF through the existing synthesis (dialectical when Scholar-RAG is
on, the legacy grounded render otherwise) — followed by the unchanged
verification tail (``_verify_for_publication`` / ``_stream_publication_tail``).

What this buys: the synthesis prompt derives from the dossiers alone (capped by
``ELEUTHERIA_LEAD_CONTEXT_TOKENS``), not from the raw tool chatter of one long
ReAct run, so the lead never reads a ~400k-token context.

Selection: ``ELEUTHERIA_AGENT_MODE=lead`` or a per-request ``pipeline=lead``.

Layout of this module::

    planner   plan_facets / plan_facets_heuristic     (deterministic first)
    sub-agent run_facet_subagent / run_subagents      (parallel, isolated)
    merge     merge_dossiers / apply_merge_to_state   (dedupe, provenance, cap)
    lead      run_lead / stream_lead                  (synthesis + shared tail)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from eleutheria_graphrag.agents.controversy_map import attach_frames
from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.graph_nodes import _trace_stage, truncate_text
from eleutheria_graphrag.agents.plan_research import (
    extract_named_entities,
    plan_research,
)
from eleutheria_graphrag.agents.prompts import delimit_retrieved_text
from eleutheria_graphrag.agents.state import (
    AnswerShape,
    ContextPack,
    ControversyFrame,
    ControversyMap,
    Evidence,
    EvidenceBundle,
    EvidenceLayer,
    EvidenceSource,
    RAGState,
    ResearchFacet,
    ResearchPlan,
    RetrievalBudget,
    ScholarlyAnswer,
    scholar_rag_enabled,
)
from eleutheria_graphrag.agents.tools import ToolRegistry
from eleutheria_graphrag.models.dossier import (
    DossierNode,
    DossierPassage,
    DossierTension,
    DossierUsage,
    LeadFacet,
    ResearchDossier,
    bound_text,
    dossier_max_nodes,
    dossier_max_passages,
    dossier_statement_chars,
    empty_dossier,
)
from eleutheria_graphrag.services.json_extractor import (
    JSONExtractionError,
    extract_json_object,
)
from eleutheria_graphrag.services.llm_service import UTILITY_TIER
from eleutheria_graphrag.services.token_budget import estimate_tokens

logger = logging.getLogger(__name__)

PIPELINE_NAME = "lead"

#: The tool surface a sub-agent sees. ``find_debates`` and
#: ``build_controversy_frame`` are deterministic-only on the react path (the
#: pipeline drives them); a sub-agent may call them directly because its
#: distilled frames are exactly what the lead's map is built from.
SUBAGENT_TOOLS: tuple[str, ...] = (
    "search_passages",
    "read_passages",
    "read_work_section",
    "search_nodes",
    "get_node_detail",
    "get_neighbors",
    "find_debates",
    "build_controversy_frame",
    "explore_subgraph",
)


# ── env knobs ────────────────────────────────────────────────────────────────


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw:
        try:
            return max(minimum, min(maximum, int(raw)))
        except ValueError:
            return default
    return default


def _env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw:
        try:
            return max(minimum, min(maximum, float(raw)))
        except ValueError:
            return default
    return default


def lead_context_tokens() -> int:
    """Cap on the merged dossier context handed to the lead's synthesis."""
    return _env_int(
        "ELEUTHERIA_LEAD_CONTEXT_TOKENS", 60_000, minimum=8192, maximum=2_000_000
    )


def lead_max_facets() -> int:
    return _env_int("ELEUTHERIA_LEAD_MAX_FACETS", 5, minimum=2, maximum=8)


def subagent_tool_budget() -> int:
    return _env_int("ELEUTHERIA_SUBAGENT_TOOL_BUDGET", 12, minimum=1, maximum=200)


def subagent_wall_clock_s() -> float:
    return _env_float(
        "ELEUTHERIA_SUBAGENT_WALL_CLOCK_S", 120.0, minimum=5.0, maximum=3600.0
    )


def resolve_subagent_model(override: str | None = None) -> str | None:
    """The sub-agent model: request override, then env, else ``None``.

    ``None`` means "the provider's utility-tier (light) model" — the loop passes
    no override and lets the tier pick it.
    """
    value = (override or os.getenv("ELEUTHERIA_SUBAGENT_MODEL") or "").strip()
    return value or None


# ══════════════════════════════════════════════════════════════════════════════
# 1. Planner — deterministic first, one short LLM refinement only when < 2
# ══════════════════════════════════════════════════════════════════════════════

_TRADITIONS: dict[str, str] = {
    "stoic": "Stoic",
    "stoics": "Stoic",
    "epicurean": "Epicurean",
    "epicureans": "Epicurean",
    "platonic": "Platonic",
    "platonist": "Platonist",
    "platonists": "Platonist",
    "neoplatonic": "Neoplatonic",
    "neoplatonist": "Neoplatonist",
    "peripatetic": "Peripatetic",
    "peripatetics": "Peripatetic",
    "aristotelian": "Aristotelian",
    "academic": "Academic",
    "sceptic": "Sceptic",
    "sceptics": "Sceptic",
    "skeptic": "Sceptic",
    "skeptics": "Sceptic",
    "christian": "Christian",
    "christians": "Christian",
    "gnostic": "Gnostic",
    "gnostics": "Gnostic",
    "valentinian": "Valentinian",
    "jewish": "Jewish",
    "rabbinic": "Rabbinic",
    "pauline": "Pauline",
    "augustinian": "Augustinian",
    "pelagian": "Pelagian",
    "manichaean": "Manichaean",
    "manichean": "Manichaean",
    "patristic": "Patristic",
    "hellenistic": "Hellenistic",
}

_PERIOD_TERMS: dict[str, str] = {
    "hellenistic": "Hellenistic",
    "imperial": "Imperial",
    "late antique": "Late Antique",
    "late antiquity": "Late Antique",
    "classical": "Classical",
    "patristic": "Patristic",
    "medieval": "Medieval",
    "modern": "Modern",
    "contemporary": "Contemporary",
}

# Verbs that mark a clause as asking for a named person's assessment.
_ASSESS_RE = re.compile(
    r"\b(assess|assesses|argue|argues|read|reads|interpret|interprets|hold|holds|"
    r"maintain|maintains|claim|claims|evaluate|evaluates|treat|treats|see|sees|"
    r"understand|understands|reconstruct|reconstructs|explain|explains|"
    r"disagree|agree|compare|compares|characterise|characterize|judge|judges|"
    r"think|thinks|view|views|weigh|weighs)\b",
    re.IGNORECASE,
)

# Clause boundaries: ", and how …", "; …", "? …", " and to what extent …".
_CLAUSE_SPLIT_RE = re.compile(
    r"(?:[,;]\s*|\s+)(?:and|but|while|whereas)\s+(?=(?:how|what|why|whether|"
    r"does|do|did|is|are|was|were|to what extent|in what sense|which|where)\b)"
    r"|[;?]\s+",
    re.IGNORECASE,
)

_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿͰ-Ͽἀ-῿']+")
_ROMAN_RE = re.compile(
    r"^(?=[IVXLC])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
)
_PAREN_RE = re.compile(r"\(([^()]{2,80})\)")
_LOCUS_RE = re.compile(
    r"\b[A-Z][a-zA-Z]+(?:\s+[A-Za-z]+){0,3}\s+(?:[IVXLC]+|\d+)(?:[.,:]\s?\d+[a-z]?)*\b"
)

_STOP: frozenset[str] = frozenset(
    {
        "how",
        "what",
        "why",
        "does",
        "do",
        "did",
        "is",
        "are",
        "the",
        "and",
        "for",
        "against",
        "between",
        "with",
        "in",
        "of",
        "to",
        "on",
        "a",
        "an",
        "his",
        "her",
        "their",
        "its",
        "this",
        "that",
        "these",
        "those",
        "whether",
        "which",
        "who",
        "whom",
    }
)


def _clauses(question: str) -> list[str]:
    """Split a compound question into its sub-questions (clause order kept)."""
    text = " ".join((question or "").split())
    parts = [p.strip(" ,;?") for p in _CLAUSE_SPLIT_RE.split(text)]
    parts = [p for p in parts if len(p) >= 12]
    return parts or ([text] if text else [])


def _capitalised_names(text: str) -> list[str]:
    """Capitalised tokens that read as names (no stopwords, numerals, traditions)."""
    names: list[str] = []
    seen: set[str] = set()
    tokens = _WORD_RE.findall(text)
    for idx, token in enumerate(tokens):
        if not token[0].isupper() or len(token) < 3:
            continue
        low = re.sub(r"['’]s$", "", token.lower())
        if low in _STOP or _ROMAN_RE.match(token) or low in _TRADITIONS:
            continue
        # A sentence-initial interrogative is not a name; a run-internal
        # capitalised word following a lowercase word usually is.
        if idx == 0 and low in {"how", "what", "why", "does", "do", "did"}:
            continue
        if low not in seen:
            seen.add(low)
            names.append(token)
    return names


def _base_name(token: str, candidates: list[str]) -> str | None:
    """``Origenian`` -> ``Origen`` when the base form is also named."""
    low = token.lower()
    for suffix in ("ian", "ean", "ic", "ist", "ine"):
        if low.endswith(suffix):
            stem = low[: -len(suffix)]
            for cand in candidates:
                if cand.lower() == stem or cand.lower().startswith(stem):
                    return cand
    return None


def _is_work(entity: str) -> bool:
    """A named entity that reads as a work title / locus (``De Principiis III``)."""
    first = entity.split()[0].lower() if entity.split() else ""
    if first in {"de", "contra", "ad", "adversus", "peri", "in", "quaestiones"}:
        return True
    return any(_ROMAN_RE.match(tok) or tok.isdigit() for tok in entity.split()[1:])


def _traditions_in(text: str) -> list[str]:
    low = text.lower()
    found: list[str] = []
    for key, label in _TRADITIONS.items():
        if re.search(rf"\b{re.escape(key)}\b", low) and label not in found:
            found.append(label)
    return found


def _periods_in(text: str) -> list[str]:
    low = text.lower()
    return [
        label
        for key, label in _PERIOD_TERMS.items()
        if re.search(rf"\b{re.escape(key)}\b", low)
    ]


def _keywords(text: str, *, exclude: set[str]) -> list[str]:
    """Content words worth seeding a search with (hyphenated terms kept)."""
    out: list[str] = []
    for match in re.finditer(r"[A-Za-zÀ-ÖØ-öø-ÿͰ-Ͽἀ-῿'-]{4,}", text):
        word = match.group(0).strip("'-")
        low = word.lower()
        if low in _STOP or low in exclude or low in _TRADITIONS:
            continue
        if low in {
            "argue",
            "argues",
            "assess",
            "against",
            "between",
            "continuity",
            "conceptions",
            "conception",
            "self",
            "does",
        }:
            continue
        if low not in {o.lower() for o in out}:
            out.append(word)
    return out[:8]


def _topic_after(text: str, term: str, *, words: int = 3) -> str:
    """The short noun phrase following ``term`` (``Stoic determinism``)."""
    match = re.search(
        rf"\b{re.escape(term)}\b\s+((?:[\w'-]+\s*){{1,{words}}})", text, re.I
    )
    if not match:
        return ""
    phrase = match.group(1).split()
    kept: list[str] = []
    for word in phrase:
        if word.lower() in _STOP or word.lower() in {"and", "or"}:
            break
        kept.append(word.strip(",.;:"))
    return " ".join(kept)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:40] or "facet"


def _clause_core(clause: str) -> str:
    """Strip the interrogative head (``how do Bobzien and Frede``)."""
    core = re.sub(
        r"^(?:and\s+)?(?:how|what|why|whether|to what extent|in what sense)\s+"
        r"(?:does|did|do|is|are|was|were)?\s*",
        "",
        clause.strip(),
        flags=re.IGNORECASE,
    )
    return core.strip(" ?.,;")


@dataclass
class _ClauseAnalysis:
    text: str
    names: list[str]
    works: list[str]
    traditions: list[str]
    periods: list[str]
    parentheticals: list[str]
    scholar_pair: list[str]


def _analyse_clause(clause: str, all_names: list[str]) -> _ClauseAnalysis:
    entities = extract_named_entities(clause)
    works = [e for e in entities if _is_work(e)]
    locus = [m.group(0) for m in _LOCUS_RE.finditer(clause)]
    for loc in locus:
        if loc not in works and not any(loc in w or w in loc for w in works):
            works.append(loc)
    # Multi-word entities first ("Alexander of Aphrodisias"), then any
    # capitalised token they do not already cover, adjectives mapped back to
    # their base name ("Origenian" -> "Origen").
    names: list[str] = [
        e for e in entities if e not in works and e.lower() not in _TRADITIONS
    ]
    for token in _capitalised_names(clause):
        if any(token in w for w in works) or any(token in n for n in names):
            continue
        base = _base_name(token, all_names)
        candidate = base or token
        if candidate not in names and not any(candidate in n for n in names):
            names.append(candidate)
    parentheticals = [p.strip() for p in _PAREN_RE.findall(clause)]

    # "how do Bobzien and Frede assess …" — a coordinated pair of persons plus
    # an assessment verb: one facet per assessor.
    scholar_pair: list[str] = []
    pair = re.search(
        r"\b([A-Z][a-zA-Z'-]+)(?:,\s*([A-Z][a-zA-Z'-]+))?\s+and\s+([A-Z][a-zA-Z'-]+)\b",
        clause,
    )
    if pair and _ASSESS_RE.search(clause):
        members = [m for m in pair.groups() if m]
        if all(
            m.lower() not in _TRADITIONS
            and m.lower() not in _STOP
            and not _ROMAN_RE.match(m)
            and not any(m in w for w in works)
            for m in members
        ):
            scholar_pair = members
    return _ClauseAnalysis(
        text=clause,
        names=names,
        works=works,
        traditions=_traditions_in(clause),
        periods=_periods_in(clause),
        parentheticals=parentheticals,
        scholar_pair=scholar_pair,
    )


def plan_facets_heuristic(
    question: str,
    *,
    tool_budget: int | None = None,
    wall_clock_s: float | None = None,
    max_facets: int | None = None,
) -> list[LeadFacet]:
    """Decompose ``question`` into research facets without an LLM.

    One primary facet per clause (its named author + work + locus), one
    tradition/background facet per school named as a foil (``against Stoic
    determinism``), and one scholar facet per assessor in a coordinated pair
    (``how do Bobzien and Frede assess …``). Ordered primary -> background ->
    scholars, capped at ``max_facets`` (primary and scholar facets survive
    first).
    """
    budget = tool_budget or subagent_tool_budget()
    clock = wall_clock_s or subagent_wall_clock_s()
    cap = max_facets or lead_max_facets()
    clauses = _clauses(question)
    all_names = _capitalised_names(question)
    analyses = [_analyse_clause(c, all_names) for c in clauses]

    primary: list[LeadFacet] = []
    scholars: list[LeadFacet] = []
    background: list[LeadFacet] = []
    seen_titles: set[str] = set()
    global_kw_exclude = {n.lower() for n in all_names}

    for analysis in analyses:
        core = _clause_core(analysis.text)
        keywords = _keywords(analysis.text, exclude=global_kw_exclude)
        if analysis.scholar_pair:
            topic = _clause_core(
                re.sub(
                    r"^.*?\b(?:assess|argue|read|interpret|hold|maintain|claim|"
                    r"evaluate|treat|see|understand|reconstruct|explain|compare|"
                    r"judge|think|view|weigh)\w*\s+",
                    "",
                    analysis.text,
                    flags=re.IGNORECASE,
                )
            )
            for name in analysis.scholar_pair:
                title = f"{name} on {truncate_text(topic, 60)}"
                if title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())
                scholars.append(
                    LeadFacet(
                        facet_id="",
                        title=title,
                        question=(
                            f"What does {name} argue about {topic}, and on what "
                            "textual and scholarly basis? Locate the publication, "
                            "the pages, and the primary passages at stake."
                        ),
                        kind="scholar",
                        target_entities=[name],
                        target_scholars=[name],
                        tradition_hints=analysis.traditions,
                        period_hints=analysis.periods,
                        keywords=keywords,
                        tool_budget=budget,
                        wall_clock_s=clock,
                        priority=1,
                    )
                )
            continue

        # A plain clause: the primary facet (author/work/locus).
        head = analysis.names[0] if analysis.names else ""
        work = analysis.works[0] if analysis.works else ""
        if head and work:
            title = f"{head} in {work}"
        elif head and core.lower().startswith(head.lower()):
            title = truncate_text(core, 70)
        elif head:
            title = f"{head}: {truncate_text(core, 50)}"
        else:
            title = truncate_text(core, 70)
        if title.lower() not in seen_titles:
            seen_titles.add(title.lower())
            primary.append(
                LeadFacet(
                    facet_id="",
                    title=title,
                    question=analysis.text.rstrip("?") + "?",
                    kind="primary",
                    target_entities=analysis.names,
                    target_works=analysis.works,
                    tradition_hints=analysis.traditions,
                    period_hints=analysis.periods,
                    keywords=keywords + analysis.parentheticals,
                    tool_budget=budget,
                    wall_clock_s=clock,
                    priority=1,
                )
            )

        # Background facets: each school named as a FOIL in this clause — a
        # clause whose only subject is the school ("What did the Stoics think
        # about fate?") is already the primary facet.
        if not (analysis.names or analysis.works):
            continue
        for tradition in analysis.traditions:
            if any(tradition.lower() in f.title.lower() for f in background):
                continue
            topic = _topic_after(analysis.text, tradition) or (
                keywords[0] if keywords else truncate_text(core, 40)
            )
            focus = ", ".join(analysis.parentheticals[:2])
            title = f"{tradition} background: {topic}"
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())
            background.append(
                LeadFacet(
                    facet_id="",
                    title=title,
                    question=(
                        f"What is the {tradition} conception of {topic}"
                        + (f" ({focus})" if focus else "")
                        + "? Gather the primary passages, the technical terms "
                        "and the ancient counter-positions."
                    ),
                    kind="tradition",
                    target_entities=[tradition],
                    tradition_hints=[tradition],
                    period_hints=analysis.periods,
                    keywords=[topic, *analysis.parentheticals, *keywords[:4]],
                    tool_budget=budget,
                    wall_clock_s=clock,
                    priority=2,
                )
            )

    facets = primary + background + scholars
    if len(facets) > cap:
        # Keep every primary + scholar facet first; background fills the rest.
        keep = primary + scholars
        room = max(0, cap - len(keep))
        facets = primary + background[:room] + scholars
        facets = facets[:cap]
    for idx, facet in enumerate(facets, start=1):
        facet.facet_id = f"f{idx}_{_slug(facet.title)}"
    return facets


# ── LLM refinement (only when the heuristic yields < 2 facets) ──────────────

PLAN_FACETS_SYSTEM = (
    "You decompose a research question about ancient philosophy and its modern "
    "scholarship into 2 to 5 independent retrieval facets for parallel "
    "sub-agents working over a knowledge graph and a corpus of primary texts. "
    "Each facet is ONE sub-question with its target authors/works/scholars. "
    "Emit STRICT JSON only: "
    '{"facets": [{"title": str, "question": str, "target_entities": [str], '
    '"target_works": [str], "target_scholars": [str], "tradition_hints": [str], '
    '"period_hints": [str]}]}. No prose outside the JSON.'
)

PLAN_FACETS_TEMPLATE = (
    "QUESTION: {question}\n\nHEURISTIC FACETS SO FAR (may be empty or too few):\n"
    "{facets}\n\nReturn the JSON only."
)


class _FacetDraft(BaseModel):
    title: str = ""
    question: str
    target_entities: list[str] = Field(default_factory=list)
    target_works: list[str] = Field(default_factory=list)
    target_scholars: list[str] = Field(default_factory=list)
    tradition_hints: list[str] = Field(default_factory=list)
    period_hints: list[str] = Field(default_factory=list)


class _FacetPlanResult(BaseModel):
    facets: list[_FacetDraft] = Field(default_factory=list)


async def _refine_facets_with_llm(
    question: str,
    heuristic: list[LeadFacet],
    llm: Any,
    *,
    budget: int,
    clock: float,
    cap: int,
) -> list[LeadFacet]:
    prompt = PLAN_FACETS_TEMPLATE.format(
        question=question,
        facets="\n".join(f"- {f.title}: {f.question}" for f in heuristic) or "(none)",
    )
    raw = await llm.generate(
        prompt,
        system_prompt=PLAN_FACETS_SYSTEM,
        temperature=0.0,
        max_tokens=1200,
        tier=UTILITY_TIER,
        cache_key="lead-facet-planner",
        cache_prefix="lead_facets_v1",
    )
    payload = extract_json_object(raw)
    if "items" in payload and "facets" not in payload:
        payload = {"facets": payload["items"]}
    result = _FacetPlanResult.model_validate(payload)
    facets: list[LeadFacet] = []
    for idx, draft in enumerate(result.facets[:cap], start=1):
        q = draft.question.strip()
        if len(q) < 8:
            continue
        title = draft.title.strip() or truncate_text(q, 60)
        facets.append(
            LeadFacet(
                facet_id=f"f{idx}_{_slug(title)}",
                title=title,
                question=q,
                kind="refined",
                target_entities=[e for e in draft.target_entities if e][:8],
                target_works=[w for w in draft.target_works if w][:8],
                target_scholars=[s for s in draft.target_scholars if s][:8],
                tradition_hints=[t for t in draft.tradition_hints if t][:6],
                period_hints=[p for p in draft.period_hints if p][:6],
                keywords=_keywords(q, exclude=set()),
                tool_budget=budget,
                wall_clock_s=clock,
            )
        )
    return facets


def _default_second_facet(question: str, *, budget: int, clock: float) -> LeadFacet:
    """The always-available companion facet: the modern scholarly assessment."""
    return LeadFacet(
        facet_id="f2_scholarly_assessment",
        title="Modern scholarly assessment",
        question=(
            "How has modern scholarship assessed the following, and where do the "
            f"scholars disagree? {question}"
        ),
        kind="background",
        keywords=_keywords(question, exclude=set()),
        tool_budget=budget,
        wall_clock_s=clock,
        priority=2,
    )


async def plan_facets(
    question: str,
    llm: Any | None = None,
    *,
    tool_budget: int | None = None,
    wall_clock_s: float | None = None,
    max_facets: int | None = None,
) -> tuple[list[LeadFacet], str]:
    """Facets for ``question``; returns ``(facets, planner)``.

    ``planner`` is ``"heuristic"`` (no LLM call), ``"llm"`` (the one refinement
    call, taken only when the heuristic produced fewer than two facets) or
    ``"heuristic+default"`` (refinement unavailable/failed: a scholarly-
    assessment companion facet makes the pair). Never raises.
    """
    budget = tool_budget or subagent_tool_budget()
    clock = wall_clock_s or subagent_wall_clock_s()
    cap = max_facets or lead_max_facets()
    facets = plan_facets_heuristic(
        question, tool_budget=budget, wall_clock_s=clock, max_facets=cap
    )
    if len(facets) >= 2:
        return facets, "heuristic"
    if llm is not None:
        try:
            refined = await _refine_facets_with_llm(
                question, facets, llm, budget=budget, clock=clock, cap=cap
            )
            if len(refined) >= 2:
                return refined, "llm"
        except (JSONExtractionError, ValidationError, ValueError, KeyError) as exc:
            logger.debug("facet refinement returned no usable plan (%s)", exc)
        except Exception as exc:  # noqa: BLE001 — never fail the query on planning
            logger.warning("facet refinement call errored (%s)", exc)
    if not facets:
        facets = [
            LeadFacet(
                facet_id="f1_question",
                title=truncate_text(question, 60),
                question=question,
                kind="primary",
                target_entities=extract_named_entities(question),
                keywords=_keywords(question, exclude=set()),
                tool_budget=budget,
                wall_clock_s=clock,
            )
        ]
    facets.append(_default_second_facet(question, budget=budget, clock=clock))
    for idx, facet in enumerate(facets, start=1):
        facet.facet_id = f"f{idx}_{_slug(facet.title)}"
    return facets, "heuristic+default"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Sub-agents — bounded ReAct loops that return distilled dossiers
# ══════════════════════════════════════════════════════════════════════════════


class _FrameCapture:
    """Proxy over ``build_controversy_frame`` that records every frame built.

    The EvidenceCollector ignores this tool's results; the lead needs the typed
    :class:`ControversyFrame` objects themselves (``attach_frames`` input).
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.frames: list[ControversyFrame] = []

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def description(self) -> str:
        return self._inner.description

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return self._inner.parameters_schema

    async def execute(self, args: dict[str, Any]) -> BaseModel:
        result = await self._inner.execute(args)
        frame = getattr(result, "frame", None)
        if isinstance(frame, ControversyFrame) and (frame.positions or frame.links):
            self.frames.append(frame)
        return result


def build_subagent_registry(
    tools: Any,
) -> tuple[ToolRegistry, _FrameCapture | None]:
    """Restrict a full registry to :data:`SUBAGENT_TOOLS` (frame tool wrapped)."""
    registry = ToolRegistry()
    capture: _FrameCapture | None = None
    for name in SUBAGENT_TOOLS:
        tool = tools.get(name) if hasattr(tools, "get") else None
        if tool is None:
            continue
        if name == "build_controversy_frame":
            capture = _FrameCapture(tool)
            registry.register(capture)
        else:
            registry.register(tool)
    return registry, capture


def subagent_tool_schemas(registry: ToolRegistry) -> list[dict[str, Any]]:
    """Function schemas for EVERY registered sub-agent tool.

    Unlike :func:`build_tool_function_schemas`, the deterministic-only tools
    are exposed: on this path there is no pipeline-driven frame assembly to
    duplicate — the sub-agent's frames ARE the map.
    """
    from eleutheria_graphrag.agents.tool_schemas import _normalize_schema

    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": _normalize_schema(tool.parameters_schema),
            },
        }
        for tool in registry._tools.values()  # noqa: SLF001 — no iterator exposed
    ]


SUBAGENT_SYSTEM_PROMPT = """\
You are a retrieval sub-agent for a scholarly graph-RAG over ancient philosophy \
and its modern scholarship. A lead researcher delegated ONE facet of a larger \
question to you. Your job is to GATHER evidence for that facet only, using the \
tools, within a small tool budget:

- Start from the named authors, works, loci and scholars in the facet.
- Prefer read_passages / search_passages for primary texts (you need the text \
itself, with its translation), get_node_detail / search_nodes for concepts, \
persons, arguments and scholarly positions, get_neighbors / explore_subgraph for \
the debate structure, find_debates + build_controversy_frame for a fault line.
- Do NOT write an essay. When your budget is spent or the facet is covered, \
reply with a terse inventory: what you found, by id, and what is still missing.
Facet targets: entities={entities}; works={works}; scholars={scholars}; \
traditions={traditions}; periods={periods}; keywords={keywords}.
"""

DISTILL_SYSTEM = (
    "You are the same retrieval sub-agent, now handing your findings to the lead "
    "researcher as a STRUCTURED DOSSIER. Select from the inventory ONLY (ids must "
    "come from it; never invent ids or text). Emit STRICT JSON: "
    '{"passages": [{"passage_id": str, "why_relevant": str}], '
    '"nodes": [{"node_id": str}], '
    '"tensions": [{"statement": str, "between": [str]}], '
    '"candidate_citations": [str], "open_questions": [str]}. '
    "why_relevant / statements are one sentence each. No prose outside the JSON."
)

DISTILL_TEMPLATE = """\
FACET: {question}

INVENTORY (what your tools returned; ids are authoritative):
{inventory}

YOUR CLOSING NOTE (from the retrieval loop):
{note}

Return the dossier JSON only."""


class _DistillPayload(BaseModel):
    passages: list[dict[str, Any]] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    tensions: list[dict[str, Any]] = Field(default_factory=list)
    candidate_citations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


def _facet_system_prompt(facet: LeadFacet) -> str:
    return SUBAGENT_SYSTEM_PROMPT.format(
        entities=", ".join(facet.target_entities) or "-",
        works=", ".join(facet.target_works) or "-",
        scholars=", ".join(facet.target_scholars) or "-",
        traditions=", ".join(facet.tradition_hints) or "-",
        periods=", ".join(facet.period_hints) or "-",
        keywords=", ".join(facet.keywords) or "-",
    )


def inventory_from_evidence(
    *,
    bundles: list[EvidenceBundle],
    primary: list[Evidence],
    secondary: list[Evidence],
) -> tuple[dict[str, DossierPassage], dict[str, DossierNode]]:
    """Typed, bounded inventory of what a loop's EvidenceCollector gathered."""
    passages: dict[str, DossierPassage] = {}
    for bundle in bundles:
        pid = bundle.original_passage_id
        if not pid or pid in passages:
            continue
        passages[pid] = DossierPassage(
            passage_id=pid,
            work=bundle.work_title or "",
            author=bundle.author or "",
            ref=bundle.canonical_ref or "",
            language=bundle.language or "",
            original_text=bundle.original_text,
            translation=bundle.translation_text or "",
            work_id=bundle.work_id or "",
        )
    nodes: dict[str, DossierNode] = {}
    for ev in [*primary, *secondary]:
        if ev.type == "passage":
            pid = ev.passage_id or ev.id
            if pid and pid not in passages:
                # A flagged (non-citable) passage: keep the notice, no text.
                passages[pid] = DossierPassage(
                    passage_id=pid,
                    work=ev.work_title or "",
                    author=ev.author or "",
                    ref=ev.canonical_ref or "",
                    evidence_tier=ev.evidence_tier,
                    evidence_notice=ev.evidence_notice,
                )
            continue
        if ev.id and ev.id not in nodes:
            nodes[ev.id] = DossierNode(
                node_id=ev.id,
                type=ev.type,
                label=ev.label,
                statement=ev.description,
                period=ev.period or "",
                school=ev.school or "",
                evidence_tier=ev.evidence_tier,
                evidence_notice=ev.evidence_notice,
            )
    return passages, nodes


def _inventory_lines(
    passages: dict[str, DossierPassage], nodes: dict[str, DossierNode]
) -> str:
    lines: list[str] = []
    for p in passages.values():
        head = " ".join(part for part in (p.author, p.work, p.ref) if part)
        snippet = truncate_text(p.translation or p.original_text, 160)
        lines.append(f"passage {p.passage_id} — {head}: {snippet}")
    for n in nodes.values():
        lines.append(
            f"node {n.node_id} [{n.type}] {n.label}: {truncate_text(n.statement, 120)}"
        )
    return "\n".join(lines) or "(nothing retrieved)"


async def distill_dossier(
    llm: Any,
    facet: LeadFacet,
    *,
    passages: dict[str, DossierPassage],
    nodes: dict[str, DossierNode],
    note: str,
    model: str | None,
) -> tuple[_DistillPayload | None, str]:
    """One structured-JSON call; ``(payload, error)`` — never raises."""
    prompt = DISTILL_TEMPLATE.format(
        question=facet.question,
        inventory=delimit_retrieved_text(
            _inventory_lines(passages, nodes), data_id="subagent:inventory"
        ),
        note=delimit_retrieved_text(
            truncate_text(note or "(none)", 3000), data_id="subagent:note"
        ),
    )
    try:
        raw = await llm.generate(
            prompt,
            system_prompt=DISTILL_SYSTEM,
            temperature=0.0,
            max_tokens=2000,
            model_override=model,
            tier=UTILITY_TIER,
        )
        payload = extract_json_object(raw)
        return _DistillPayload.model_validate(payload), ""
    except (JSONExtractionError, ValidationError, ValueError, KeyError) as exc:
        return None, f"distillation unparseable: {type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001 — a failed distillation costs annotations only
        return None, f"distillation failed: {type(exc).__name__}: {exc}"[:300]


def assemble_dossier(
    facet: LeadFacet,
    *,
    passages: dict[str, DossierPassage],
    nodes: dict[str, DossierNode],
    frames: list[ControversyFrame],
    payload: _DistillPayload | None,
    usage: DossierUsage,
    errors: list[str],
    status: str = "ok",
) -> ResearchDossier:
    """Hydrate the sub-agent's selection from the inventory (ids must exist).

    The model's picks lead (with their ``why_relevant`` notes); whatever it left
    out is appended after them up to the dossier caps, so a thin selection never
    silently discards retrieved evidence. Unknown ids are dropped and counted.
    """
    chosen_passages: list[DossierPassage] = []
    chosen_nodes: list[DossierNode] = []
    unknown = 0
    limit = dossier_statement_chars()
    if payload is not None:
        for item in payload.passages:
            pid = str(item.get("passage_id") or "")
            src = passages.get(pid)
            if src is None:
                unknown += 1
                continue
            if any(p.passage_id == pid for p in chosen_passages):
                continue
            chosen_passages.append(
                src.model_copy(
                    update={
                        "why_relevant": bound_text(
                            str(item.get("why_relevant") or ""), limit
                        )
                    }
                )
            )
        for item in payload.nodes:
            nid = str(item.get("node_id") or "")
            src = nodes.get(nid)
            if src is None:
                unknown += 1
                continue
            if any(n.node_id == nid for n in chosen_nodes):
                continue
            chosen_nodes.append(src)
    seen_p = {p.passage_id for p in chosen_passages}
    for pid, src in passages.items():
        if len(chosen_passages) >= dossier_max_passages():
            break
        if pid not in seen_p:
            chosen_passages.append(src)
    seen_n = {n.node_id for n in chosen_nodes}
    for nid, src in nodes.items():
        if len(chosen_nodes) >= dossier_max_nodes():
            break
        if nid not in seen_n:
            chosen_nodes.append(src)

    tensions: list[DossierTension] = []
    if payload is not None:
        known = set(passages) | set(nodes)
        for item in payload.tensions[:12]:
            statement = str(item.get("statement") or "").strip()
            if not statement:
                continue
            between = [str(i) for i in (item.get("between") or []) if str(i) in known]
            tensions.append(DossierTension(statement=statement, between=between))
    if unknown:
        errors = [*errors, f"distillation named {unknown} unknown id(s); dropped"]

    if not (chosen_passages or chosen_nodes or frames) and status == "ok":
        status = "empty"
    return ResearchDossier(
        facet=facet,
        status=status,
        passages=chosen_passages,
        nodes=chosen_nodes,
        frames=frames,
        tensions=tensions,
        candidate_citations=payload.candidate_citations if payload else [],
        open_questions=payload.open_questions if payload else [],
        retrieval_errors=errors,
        usage=usage,
    )


async def run_facet_subagent(
    deps: Deps,
    facet: LeadFacet,
    tools: Any,
    *,
    model: str | None = None,
    parent_state: RAGState | None = None,
) -> ResearchDossier:
    """Run one bounded retrieval loop for ``facet`` and distil its dossier.

    Reuses :class:`~eleutheria_graphrag.agents.react_loop.NativeAgentLoop` with
    the restricted registry, the facet's tool budget and a wall-clock budget
    (``asyncio.wait_for``); on timeout the evidence gathered so far is still
    distilled. Raises only on programming errors — callers isolate anyway.
    """
    from eleutheria_graphrag.agents.react_loop import NativeAgentLoop
    from eleutheria_graphrag.agents.sse_emitter import NullEmitter

    started = time.monotonic()
    state = RAGState(
        question=facet.question,
        selected_model=(parent_state.selected_model if parent_state else "auto"),
        retrieval_mode=(parent_state.retrieval_mode if parent_state else "auto"),
    )
    if parent_state is not None:
        state.complexity = parent_state.complexity
        state.query_type = parent_state.query_type
    state.metadata["lead_facet"] = facet.facet_id

    registry, capture = build_subagent_registry(tools)
    loop = NativeAgentLoop(
        deps,
        state,
        registry,
        NullEmitter(),
        # "" (not None) = no explicit override: the utility tier picks the
        # provider's light model. An explicit model leads the rung list.
        model_override=model or "",
        tier=UTILITY_TIER,
        system_prompt=_facet_system_prompt(facet),
        max_tool_calls=facet.tool_budget,
        tool_schemas=subagent_tool_schemas(registry),
    )
    timed_out = False
    errors: list[str] = []
    try:
        await asyncio.wait_for(loop.run(), timeout=facet.wall_clock_s)
    except TimeoutError:
        timed_out = True
        errors.append(
            f"sub-agent wall-clock budget of {facet.wall_clock_s:.0f}s reached"
        )
    for err in state.metadata.get("retrieval_errors") or []:
        errors.append(str(err)[:300])

    passages, nodes = inventory_from_evidence(
        bundles=list(loop.evidence.evidence_bundles),
        primary=list(loop.evidence.primary_evidence),
        secondary=list(loop.evidence.secondary_evidence),
    )
    frames = list(capture.frames) if capture is not None else []
    payload: _DistillPayload | None = None
    if passages or nodes:
        payload, distill_error = await distill_dossier(
            deps.llm,
            facet,
            passages=passages,
            nodes=nodes,
            note=loop.final_answer or "",
            model=model,
        )
        if distill_error:
            errors.append(distill_error)
    usage = DossierUsage(
        tool_calls=loop.calls_made,
        llm_turns=getattr(loop, "llm_turns", 0),
        duration_ms=int((time.monotonic() - started) * 1000),
        timed_out=timed_out,
        budget_exhausted=loop.calls_made >= facet.tool_budget,
        model=model or "utility-tier",
    )
    return assemble_dossier(
        facet,
        passages=passages,
        nodes=nodes,
        frames=frames,
        payload=payload,
        usage=usage,
        errors=errors,
        status="timeout" if timed_out else "ok",
    )


async def _isolated_facet(
    deps: Deps,
    facet: LeadFacet,
    tools: Any,
    *,
    model: str | None,
    parent_state: RAGState | None,
) -> ResearchDossier:
    """Per-facet exception isolation: a crash yields an empty dossier."""
    try:
        return await run_facet_subagent(
            deps, facet, tools, model=model, parent_state=parent_state
        )
    except Exception as exc:  # noqa: BLE001 — one facet must never abort the query
        logger.warning("sub-agent for facet %s failed", facet.facet_id, exc_info=True)
        return empty_dossier(
            facet, status="error", error=f"{type(exc).__name__}: {exc}"[:300]
        )


def start_subagents(
    deps: Deps,
    facets: list[LeadFacet],
    tools: Any,
    *,
    model: str | None,
    parent_state: RAGState | None,
) -> dict[asyncio.Task[ResearchDossier], LeadFacet]:
    """Launch every facet concurrently; returns ``{task: facet}``."""
    return {
        asyncio.create_task(
            _isolated_facet(deps, facet, tools, model=model, parent_state=parent_state),
            name=f"subagent:{facet.facet_id}",
        ): facet
        for facet in facets
    }


async def run_subagents(
    deps: Deps,
    facets: list[LeadFacet],
    tools: Any,
    *,
    model: str | None = None,
    parent_state: RAGState | None = None,
) -> list[ResearchDossier]:
    """All facets in parallel (``asyncio.gather``), results in facet order."""
    tasks = start_subagents(deps, facets, tools, model=model, parent_state=parent_state)
    results = await asyncio.gather(*tasks)
    return list(results)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Merge — dedupe, provenance, deterministic token cap
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class LeadMerge:
    """The lead's bounded evidence set, assembled from the dossiers only."""

    evidence_bundles: list[EvidenceBundle] = field(default_factory=list)
    primary_evidence: list[Evidence] = field(default_factory=list)
    secondary_evidence: list[Evidence] = field(default_factory=list)
    frames: list[ControversyFrame] = field(default_factory=list)
    controversy_map: ControversyMap | None = None
    passage_provenance: dict[str, list[str]] = field(default_factory=dict)
    node_provenance: dict[str, list[str]] = field(default_factory=dict)
    frame_provenance: dict[str, list[str]] = field(default_factory=dict)
    tensions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    candidate_citations: list[str] = field(default_factory=list)
    context_tokens: int = 0
    context_cap: int = 0
    dropped: dict[str, int] = field(default_factory=dict)
    admitted: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "merged_passages": len(self.evidence_bundles),
            "merged_nodes": len(self.primary_evidence) + len(self.secondary_evidence),
            "frames": len(self.frames),
            "context_tokens_in": self.context_tokens,
            "context_cap": self.context_cap,
            "dropped": dict(self.dropped),
            "multi_facet_passages": sum(
                1 for v in self.passage_provenance.values() if len(v) >= 2
            ),
        }


@dataclass
class _Candidate:
    kind: str  # passage | frame | node
    key: str
    facets: list[str]
    facet_index: int
    order: int
    tokens: int
    item: Any

    def priority(self) -> tuple[int, int, int, int]:
        kind_rank = {"passage": 0, "frame": 1, "node": 2}[self.kind]
        # ≥2 facets first (more facets before fewer), then facet order, then
        # kind (passages before frames before nodes), then in-facet order.
        return (-min(len(self.facets), 9), self.facet_index, kind_rank, self.order)


def _passage_tokens(p: DossierPassage) -> int:
    return estimate_tokens(p.original_text, p.translation, p.why_relevant) + 8


def _node_tokens(n: DossierNode) -> int:
    return estimate_tokens(n.label, n.statement) + 6


def _frame_tokens(f: ControversyFrame) -> int:
    return estimate_tokens(f.model_dump_json())


def _bundle_from_passage(p: DossierPassage) -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id=f"b_{uuid.uuid4().hex[:8]}",
        work_id=p.work_id or "",
        work_title=p.work or "",
        author=p.author or None,
        canonical_ref=p.ref or None,
        original_passage_id=p.passage_id,
        original_text=p.original_text,
        translation_text=p.translation or None,
        language=p.language or None,
        token_estimate=RetrievalBudget.estimate_tokens(
            "\n".join(part for part in (p.original_text, p.translation) if part)
        ),
        evidence_role="primary_support",
        source=EvidenceSource.PASSAGE_CITATION,
        metadata={"why_relevant": p.why_relevant} if p.why_relevant else {},
    )


def _flagged_passage_evidence(p: DossierPassage) -> Evidence:
    return Evidence(
        id=p.passage_id,
        label="flagged passage",
        type="passage",
        source=EvidenceSource.PASSAGE_CITATION,
        passage_id=p.passage_id,
        canonical_ref=p.ref or None,
        author=p.author or None,
        work_title=p.work or None,
        evidence_tier=p.evidence_tier,
        evidence_notice=p.evidence_notice,
    )


def _node_evidence(n: DossierNode) -> Evidence:
    return Evidence(
        id=n.node_id,
        label=n.label,
        type=n.type,
        layer=EvidenceLayer.PRIMARY,
        source=EvidenceSource.SEMANTIC_SEARCH,
        description=n.statement,
        period=n.period or None,
        school=n.school or None,
        evidence_tier=n.evidence_tier,
        evidence_notice=n.evidence_notice,
    )


def merge_dossiers(
    question: str,
    dossiers: list[ResearchDossier],
    *,
    context_tokens: int | None = None,
    shape: AnswerShape = AnswerShape.SURVEY_OF_DEBATES,
) -> LeadMerge:
    """Dedupe passages / nodes / frames by id across dossiers, keep provenance,
    and admit them under ``context_tokens`` with a deterministic priority:
    items found by ≥2 facets first, then facet order (passages before frames
    before nodes within a facet, in the order the sub-agent listed them).
    """
    cap = context_tokens or lead_context_tokens()
    merge = LeadMerge(context_cap=cap)
    candidates: dict[tuple[str, str], _Candidate] = {}

    for facet_index, dossier in enumerate(dossiers):
        fid = dossier.facet.facet_id
        for order, passage in enumerate(dossier.passages):
            key = ("passage", passage.passage_id)
            cand = candidates.get(key)
            if cand is None:
                candidates[key] = _Candidate(
                    "passage",
                    passage.passage_id,
                    [fid],
                    facet_index,
                    order,
                    _passage_tokens(passage),
                    passage,
                )
            else:
                if fid not in cand.facets:
                    cand.facets.append(fid)
                # Prefer the copy that carries text / a note.
                if len(passage.original_text) > len(cand.item.original_text) or (
                    passage.why_relevant and not cand.item.why_relevant
                ):
                    cand.item = passage
                    cand.tokens = _passage_tokens(passage)
        for order, frame in enumerate(dossier.frames):
            key = ("frame", frame.frame_id)
            cand = candidates.get(key)
            if cand is None:
                candidates[key] = _Candidate(
                    "frame",
                    frame.frame_id,
                    [fid],
                    facet_index,
                    order,
                    _frame_tokens(frame),
                    frame,
                )
            elif fid not in cand.facets:
                cand.facets.append(fid)
        for order, node in enumerate(dossier.nodes):
            key = ("node", node.node_id)
            cand = candidates.get(key)
            if cand is None:
                candidates[key] = _Candidate(
                    "node",
                    node.node_id,
                    [fid],
                    facet_index,
                    order,
                    _node_tokens(node),
                    node,
                )
            elif fid not in cand.facets:
                cand.facets.append(fid)
        merge.tensions.extend(
            f"[{fid}] {t.statement}" for t in dossier.tensions if t.statement
        )
        merge.open_questions.extend(f"[{fid}] {q}" for q in dossier.open_questions)
        merge.candidate_citations.extend(dossier.candidate_citations)

    used = 0
    for cand in sorted(candidates.values(), key=_Candidate.priority):
        if used + cand.tokens > cap:
            merge.dropped[cand.kind] = merge.dropped.get(cand.kind, 0) + 1
            continue
        used += cand.tokens
        merge.admitted[cand.kind] = merge.admitted.get(cand.kind, 0) + 1
        if cand.kind == "passage":
            passage: DossierPassage = cand.item
            merge.passage_provenance[passage.passage_id] = list(cand.facets)
            if passage.evidence_tier != "citable" or not passage.original_text:
                merge.secondary_evidence.append(_flagged_passage_evidence(passage))
            else:
                merge.evidence_bundles.append(_bundle_from_passage(passage))
        elif cand.kind == "frame":
            merge.frames.append(cand.item)
            merge.frame_provenance[cand.key] = list(cand.facets)
        else:
            node: DossierNode = cand.item
            merge.node_provenance[node.node_id] = list(cand.facets)
            target = (
                merge.primary_evidence
                if node.evidence_tier == "citable"
                else merge.secondary_evidence
            )
            target.append(_node_evidence(node))
    merge.context_tokens = used

    if merge.frames:
        cmap = ControversyMap(question_frame=question, shape=shape)
        merge.controversy_map = attach_frames(cmap, merge.frames)
    return merge


def apply_merge_to_state(
    state: RAGState,
    merge: LeadMerge,
    *,
    facets: list[LeadFacet],
    dossiers: list[ResearchDossier],
    plan: ResearchPlan | None,
    planner: str,
    subagent_model: str | None,
) -> None:
    """Populate ``state`` from the merge — the lead's whole retrieval result.

    The legacy context pack is bounded through ``state.retrieval_budget`` (its
    window is the lead cap) and the dialectical map is the dossier frames only,
    so whichever synthesis runs, its input derives from the dossiers.
    """
    state.evidence_bundles = list(merge.evidence_bundles)
    state.primary_evidence = list(merge.primary_evidence)
    state.secondary_evidence = list(merge.secondary_evidence)
    state.seed_node_ids = [ev.id for ev in merge.primary_evidence]
    state.context_node_ids = []
    state.passages_used = len(merge.evidence_bundles)
    state.context_pack = ContextPack()
    state.accumulated_context = ""
    state.sub_queries = [f.question for f in facets]
    state.retrieval_budget = RetrievalBudget(model_window=max(8192, merge.context_cap))
    if plan is not None:
        state.research_plan = plan

    notebook = state.research_notebook
    notebook.question_frame = state.question
    notebook.facets = [
        ResearchFacet(
            facet_id=f.facet_id,
            title=f.title,
            question=f.question,
            keywords=list(f.keywords),
            priority=f.priority,
        )
        for f in facets
    ]
    notebook.competing_hypotheses.extend(merge.tensions[:20])
    notebook.open_questions.extend(merge.open_questions[:20])
    for dossier in dossiers:
        if dossier.status in {"error", "timeout", "empty"}:
            notebook.uncertainties.append(
                f"[{dossier.facet.facet_id}] sub-agent {dossier.status}"
                + (
                    f": {dossier.retrieval_errors[0]}"
                    if dossier.retrieval_errors
                    else ""
                )
            )

    cmap = merge.controversy_map
    if cmap is not None and cmap.frames and scholar_rag_enabled():
        state.controversy_map = cmap
        state.metadata["controversy_map"] = {
            "status": "ok",
            "shape": cmap.shape.value,
            "frames": len(cmap.frames),
            "coverage_gaps": len(cmap.coverage_gaps),
            "provenance_passages": len(cmap.provenance),
            "source": "subagent_dossiers",
        }
    else:
        state.controversy_map = None
        state.metadata["controversy_map"] = {
            "status": "degraded" if scholar_rag_enabled() else "skipped",
            "reason": (
                "no controversy frames in the dossiers"
                if scholar_rag_enabled()
                else "scholar-rag off"
            ),
            "frames": len(merge.frames),
        }

    state.metadata["pipeline"] = PIPELINE_NAME
    state.metadata["lead"] = {
        "planner": planner,
        "facets": [
            {
                "facet_id": f.facet_id,
                "title": f.title,
                "question": f.question,
                "kind": f.kind,
                "target_entities": f.target_entities,
                "target_works": f.target_works,
                "target_scholars": f.target_scholars,
                "tradition_hints": f.tradition_hints,
                "period_hints": f.period_hints,
                "tool_budget": f.tool_budget,
                "wall_clock_s": f.wall_clock_s,
            }
            for f in facets
        ],
        "dossier_sizes": {d.facet.facet_id: d.summary() for d in dossiers},
        "subagent_ms": {d.facet.facet_id: d.usage.duration_ms for d in dossiers},
        "subagent_model": subagent_model or "utility-tier",
        "retrieval_errors": {
            d.facet.facet_id: list(d.retrieval_errors)
            for d in dossiers
            if d.retrieval_errors
        },
        "passage_provenance": dict(merge.passage_provenance),
        **merge.summary(),
    }
    _trace_stage(
        state,
        "lead_merge",
        {"mode": "lead", **merge.summary(), "facets": len(facets)},
    )


# ══════════════════════════════════════════════════════════════════════════════
# 4. The lead — orchestration, synthesis, shared verification tail
# ══════════════════════════════════════════════════════════════════════════════


def _stage_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _record_stage(state: RAGState, stage: str, ms: int, **payload: Any) -> None:
    metrics = state.metadata.setdefault("stage_metrics", [])
    if isinstance(metrics, list):
        metrics.append({"stage": stage, "duration_ms": ms, **payload})
    _trace_stage(state, f"lead_{stage}", {"mode": "lead", "duration_ms": ms, **payload})


async def _plan_stage(
    agent: Any, state: RAGState
) -> tuple[list[LeadFacet], ResearchPlan, str]:
    """Shape (heuristic, no LLM) + facets (LLM only when the heuristic is thin)."""
    plan = await plan_research(state.question, None)
    facets, planner = await plan_facets(state.question, agent.deps.llm)
    state.research_plan = plan
    return facets, plan, planner


async def _retrieve_and_merge(
    agent: Any,
    state: RAGState,
    facets: list[LeadFacet],
    plan: ResearchPlan,
    planner: str,
    *,
    subagent_model: str | None,
) -> tuple[list[ResearchDossier], LeadMerge]:
    from eleutheria_graphrag.agents.tools import build_tool_registry

    tools = build_tool_registry(agent.deps)
    model = resolve_subagent_model(subagent_model)
    started = time.perf_counter()
    dossiers = await run_subagents(
        agent.deps, facets, tools, model=model, parent_state=state
    )
    _record_stage(
        state,
        "subagents",
        _stage_ms(started),
        facets=len(facets),
        failed=sum(1 for d in dossiers if d.status == "error"),
    )
    started = time.perf_counter()
    merge = merge_dossiers(state.question, dossiers, shape=plan.primary_shape)
    apply_merge_to_state(
        state,
        merge,
        facets=facets,
        dossiers=dossiers,
        plan=plan,
        planner=planner,
        subagent_model=model,
    )
    _record_stage(state, "merge", _stage_ms(started), **merge.summary())
    return dossiers, merge


async def run_lead(
    agent: Any, state: RAGState, *, subagent_model: str | None = None
) -> ScholarlyAnswer:
    """The non-streaming lead pipeline.

    classify -> plan facets -> parallel sub-agents -> merge dossiers ->
    claim ledger -> synthesis (dialectical / legacy render) -> ProgrammaticVerify
    -> the SAME verification tail as the other pipelines
    (``ScholarlyAgent._verify_for_publication``, drained).
    """
    from pydantic_graph import End, GraphRunContext

    from eleutheria_graphrag.agents import scholarly_agent as sa

    ctx = GraphRunContext(state=state, deps=agent.deps)
    await sa.ClassifyQueryType().run(ctx)

    started = time.perf_counter()
    facets, plan, planner = await _plan_stage(agent, state)
    _record_stage(
        state, "plan", _stage_ms(started), facets=len(facets), planner=planner
    )

    await _retrieve_and_merge(
        agent, state, facets, plan, planner, subagent_model=subagent_model
    )

    started = time.perf_counter()
    ctx = GraphRunContext(state=state, deps=agent.deps)
    await sa.DraftClaimLedger().run(ctx)
    prose: str | None = None
    if agent._scholar_render_active(state):
        prose = await agent._synthesize_dialectical(state)
    if prose is None:
        ctx = GraphRunContext(state=state, deps=agent.deps)
        await sa.RenderGroundedAnswer().run(ctx)
    _record_stage(
        state,
        "synthesis",
        _stage_ms(started),
        render_mode=state.metadata.get("render_answer_mode"),
    )

    state.metadata["scholar_diagnostics"] = sa._build_scholar_diagnostics(state)
    ctx = GraphRunContext(state=state, deps=agent.deps)
    result = await sa.ProgrammaticVerify().run(ctx)
    answer = result.data if isinstance(result, End) else sa._make_answer(state)
    answer.metadata["pipeline"] = PIPELINE_NAME

    # The ONE verification tail, drained exactly as the FSM facade drains it.
    holder: dict[str, Any] = {}
    async for _frame in agent._verify_for_publication(
        answer, state, journal=sa.ResearchJournal(), result_into=holder
    ):
        pass
    return holder["answer"]


async def stream_lead(
    agent: Any,
    question: str,
    *,
    max_iterations: int = 5,
    selected_model: str = "gemini-3.1-pro",
    retrieval_mode: str = "auto",
    hunt_counter_evidence: bool = False,
    subagent_model: str | None = None,
) -> AsyncIterator[str]:
    """The streaming lead pipeline (SSE frames as JSON strings).

    Frame order: status/stage_complete for ``classify``, ``plan``, one
    ``stage_complete`` per facet (``subagent:<facet_id>``) as each sub-agent
    finishes, ``subagents``, ``merge``, then the react protocol — provisional
    prose during ``synthesis``, ``scholar_diagnostics``, ``verify`` — and the
    shared publication tail (``verification_warning`` / ``answer_final`` /
    ``answer_chunk`` / ``complete``) via ``_stream_publication_tail``.
    """
    from pydantic_graph import End, GraphRunContext

    from eleutheria_graphrag.agents import scholarly_agent as sa
    from eleutheria_graphrag.agents.tools import build_tool_registry

    state = RAGState(
        question=question,
        max_iterations=max_iterations,
        selected_model=selected_model,
        retrieval_mode=retrieval_mode,
    )
    if hunt_counter_evidence:
        state.metadata["hunt_counter_evidence"] = True
    state.metadata["pipeline"] = PIPELINE_NAME
    journal = sa.ResearchJournal()

    def _status(message: str, **data: Any) -> str:
        return json.dumps({"type": "status", "message": message, "data": data})

    def _stage(stage: str, ms: int, **metadata: Any) -> str:
        return json.dumps(
            {
                "type": "stage_complete",
                "stage": stage,
                "duration_ms": ms,
                "metadata": metadata,
            }
        )

    # Phase 1: classify (deterministic / cheap).
    started = time.perf_counter()
    yield _status("Classifying query...", step=0)
    ctx = GraphRunContext(state=state, deps=agent.deps)
    await sa.ClassifyQueryType().run(ctx)
    yield _stage("classify", _stage_ms(started), complexity=state.complexity.value)

    # Phase 2: plan facets.
    started = time.perf_counter()
    yield _status("Planning research facets...", step=1, stage="plan")
    facets, plan, planner = await _plan_stage(agent, state)
    plan_ms = _stage_ms(started)
    _record_stage(state, "plan", plan_ms, facets=len(facets), planner=planner)
    yield _stage(
        "plan",
        plan_ms,
        planner=planner,
        facets=[{"facet_id": f.facet_id, "title": f.title} for f in facets],
    )

    # Phase 3: sub-agents in parallel, one frame per finished facet, with
    # heartbeats so the wire never goes silent while they run.
    tools = build_tool_registry(agent.deps)
    model = resolve_subagent_model(subagent_model)
    started = time.perf_counter()
    yield _status(
        f"Delegating {len(facets)} facets to sub-agents...",
        step=2,
        stage="subagents",
        facets=[f.facet_id for f in facets],
    )
    tasks = start_subagents(agent.deps, facets, tools, model=model, parent_state=state)
    by_facet: dict[str, ResearchDossier] = {}
    pending: set[asyncio.Task[ResearchDossier]] = set(tasks)
    while pending:
        done, pending = await asyncio.wait(
            pending, timeout=10.0, return_when=asyncio.FIRST_COMPLETED
        )
        if not done:
            yield _status(
                f"Sub-agents running ({len(by_facet)}/{len(facets)} done)...",
                step=2,
                stage="subagents",
                elapsed_s=round(time.perf_counter() - started, 1),
            )
            continue
        for task in done:
            facet = tasks[task]
            try:
                dossier = task.result()
            except Exception as exc:  # noqa: BLE001 — belt and braces
                dossier = empty_dossier(
                    facet, status="error", error=f"{type(exc).__name__}: {exc}"[:300]
                )
            by_facet[facet.facet_id] = dossier
            yield _stage(
                f"subagent:{facet.facet_id}",
                dossier.usage.duration_ms,
                title=facet.title,
                **dossier.summary(),
            )
    dossiers = [by_facet[f.facet_id] for f in facets]
    sub_ms = _stage_ms(started)
    failed = sum(1 for d in dossiers if d.status == "error")
    _record_stage(state, "subagents", sub_ms, facets=len(facets), failed=failed)
    yield _stage(
        "subagents",
        sub_ms,
        facets=len(facets),
        failed=failed,
        tool_calls=sum(d.usage.tool_calls for d in dossiers),
    )

    # Phase 4: merge into the bounded evidence set + map.
    started = time.perf_counter()
    yield _status("Merging dossiers...", step=3, stage="merge")
    merge = merge_dossiers(state.question, dossiers, shape=plan.primary_shape)
    apply_merge_to_state(
        state,
        merge,
        facets=facets,
        dossiers=dossiers,
        plan=plan,
        planner=planner,
        subagent_model=model,
    )
    merge_ms = _stage_ms(started)
    _record_stage(state, "merge", merge_ms, **merge.summary())
    yield _stage("merge", merge_ms, **merge.summary())

    # Phase 5: the lead writes — same seams as the react stream.
    started = time.perf_counter()
    yield _status("Synthesizing answer...", step=99)
    ctx = GraphRunContext(state=state, deps=agent.deps)
    async for hb in agent._await_with_heartbeat(
        sa.DraftClaimLedger().run(ctx),
        label="Drafting claim ledger",
        stage_id="draft_claim_ledger",
        max_wait=180.0,
    ):
        yield hb
    for frame in sa._serialise_notes(
        journal, sa.rejected_claim_notes(state), "claim_ledger"
    ):
        yield frame

    async for ev in agent._stream_render(state):
        if isinstance(ev, sa.RenderProse):
            if ev:
                yield sa._provisional_frame(str(ev))
            continue
        control = sa._render_control_frame(ev)
        if control is not None:
            yield control
    state.metadata["prose_provisional_until_verified"] = True
    synthesis_ms = _stage_ms(started)
    _record_stage(
        state,
        "synthesis",
        synthesis_ms,
        render_mode=state.metadata.get("render_answer_mode"),
    )
    yield _stage("synthesis", synthesis_ms)

    diagnostics = sa._build_scholar_diagnostics(state)
    state.metadata["scholar_diagnostics"] = diagnostics
    yield json.dumps({"type": "scholar_diagnostics", "data": diagnostics})

    started = time.perf_counter()
    verify_holder: dict[str, Any] = {}
    verify_error: Exception | None = None
    ctx = GraphRunContext(state=state, deps=agent.deps)
    try:
        async for hb in agent._await_with_heartbeat(
            sa.ProgrammaticVerify().run(ctx),
            label="Verifying citations",
            stage_id="verify",
            interval=8.0,
            max_wait=120.0,
            result_into=verify_holder,
        ):
            yield hb
    except Exception as exc:  # noqa: BLE001 — never strand the client
        verify_error = exc
        logger.warning("Citation verification stage failed", exc_info=True)
    result = verify_holder.get("value")
    yield json.dumps(
        {
            "type": "stage_complete",
            "stage": "verify",
            "duration_ms": _stage_ms(started),
            "failed": verify_error is not None,
        }
    )
    answer = result.data if isinstance(result, End) else sa._make_answer(state)
    answer.metadata["pipeline"] = PIPELINE_NAME

    async for ev in agent._stream_publication_tail(answer, state, journal=journal):
        yield ev
