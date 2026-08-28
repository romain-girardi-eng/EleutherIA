"""Typed research dossiers for the lead-researcher pipeline.

A :class:`LeadFacet` is one sub-question the lead delegates to a retrieval
sub-agent; a :class:`ResearchDossier` is what the sub-agent hands back — a
distilled, bounded inventory of what it found (passages, nodes, controversy
frames, tensions, candidate citations, open questions), never prose. The lead
writes the answer from merged dossiers only, so every text field here carries
a hard character bound: the dossier IS the synthesis context.

Bounds are applied at construction (validators), so a dossier that round-trips
through JSON is bounded on both sides.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field, field_validator

from eleutheria_graphrag.agents.state import ControversyFrame
from eleutheria_graphrag.services.token_budget import estimate_tokens

# ── bounds (env-tunable, clamped) ────────────────────────────────────────────


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw:
        try:
            return max(minimum, min(maximum, int(raw)))
        except ValueError:
            return default
    return default


def dossier_passage_chars() -> int:
    """Per-passage bound on ``original_text`` / ``translation`` (chars)."""
    return _env_int(
        "ELEUTHERIA_DOSSIER_PASSAGE_CHARS", 2400, minimum=200, maximum=20_000
    )


def dossier_statement_chars() -> int:
    """Bound on a node statement / a why-relevant note / a tension (chars)."""
    return _env_int("ELEUTHERIA_DOSSIER_STATEMENT_CHARS", 600, minimum=80, maximum=4000)


def dossier_max_passages() -> int:
    """Maximum passages one dossier may carry."""
    return _env_int("ELEUTHERIA_DOSSIER_MAX_PASSAGES", 14, minimum=1, maximum=100)


def dossier_max_nodes() -> int:
    """Maximum KG nodes one dossier may carry."""
    return _env_int("ELEUTHERIA_DOSSIER_MAX_NODES", 24, minimum=1, maximum=200)


def bound_text(text: str | None, limit: int) -> str:
    """Cut ``text`` to ``limit`` chars on a word boundary, marking the cut."""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    if space > limit // 2:
        cut = cut[:space]
    return cut.rstrip() + " […]"


# ── facet ────────────────────────────────────────────────────────────────────


class LeadFacet(BaseModel):
    """One sub-question the lead delegates to a retrieval sub-agent."""

    facet_id: str
    title: str = ""
    question: str
    kind: str = "primary"  # primary | scholar | tradition | background | refined
    target_entities: list[str] = Field(default_factory=list)
    target_works: list[str] = Field(default_factory=list)
    target_scholars: list[str] = Field(default_factory=list)
    tradition_hints: list[str] = Field(default_factory=list)
    period_hints: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tool_budget: int = Field(12, ge=1, le=200)
    wall_clock_s: float = Field(120.0, gt=0)
    priority: int = Field(1, ge=1, le=5)


# ── dossier items ────────────────────────────────────────────────────────────


class DossierPassage(BaseModel):
    """A primary passage the sub-agent read, with bounded text."""

    passage_id: str
    work: str = ""
    author: str = ""
    ref: str = ""
    language: str = ""
    original_text: str = ""
    translation: str = ""
    why_relevant: str = ""
    evidence_tier: str = "citable"
    evidence_notice: str = ""
    work_id: str = ""

    @field_validator("original_text", "translation", mode="before")
    @classmethod
    def _bound_passage_text(cls, value: Any) -> str:
        return bound_text(str(value) if value else "", dossier_passage_chars())

    @field_validator("why_relevant", "evidence_notice", mode="before")
    @classmethod
    def _bound_note(cls, value: Any) -> str:
        return bound_text(str(value) if value else "", dossier_statement_chars())


class DossierNode(BaseModel):
    """A knowledge-graph node the sub-agent surfaced, with a bounded statement."""

    node_id: str
    type: str = ""
    label: str = ""
    statement: str = ""
    period: str = ""
    school: str = ""
    evidence_tier: str = "citable"
    evidence_notice: str = ""

    @field_validator("statement", "evidence_notice", mode="before")
    @classmethod
    def _bound_statement(cls, value: Any) -> str:
        return bound_text(str(value) if value else "", dossier_statement_chars())


class DossierTension(BaseModel):
    """A contradiction or tension the sub-agent noticed between items."""

    statement: str
    between: list[str] = Field(default_factory=list)  # passage / node ids

    @field_validator("statement", mode="before")
    @classmethod
    def _bound(cls, value: Any) -> str:
        return bound_text(str(value) if value else "", dossier_statement_chars())


class DossierUsage(BaseModel):
    """What the sub-agent spent."""

    tool_calls: int = 0
    llm_turns: int = 0
    duration_ms: int = 0
    timed_out: bool = False
    budget_exhausted: bool = False
    model: str = ""


class ResearchDossier(BaseModel):
    """What a retrieval sub-agent returns for one facet — never prose."""

    facet: LeadFacet
    status: str = "ok"  # ok | empty | error | timeout
    passages: list[DossierPassage] = Field(default_factory=list)
    nodes: list[DossierNode] = Field(default_factory=list)
    frames: list[ControversyFrame] = Field(default_factory=list)
    tensions: list[DossierTension] = Field(default_factory=list)
    candidate_citations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    retrieval_errors: list[str] = Field(default_factory=list)
    usage: DossierUsage = Field(default_factory=DossierUsage)

    @field_validator("passages")
    @classmethod
    def _cap_passages(cls, value: list[DossierPassage]) -> list[DossierPassage]:
        return value[: dossier_max_passages()]

    @field_validator("nodes")
    @classmethod
    def _cap_nodes(cls, value: list[DossierNode]) -> list[DossierNode]:
        return value[: dossier_max_nodes()]

    @field_validator("open_questions", "candidate_citations", mode="before")
    @classmethod
    def _bound_strings(cls, value: Any) -> list[str]:
        if not value:
            return []
        limit = dossier_statement_chars()
        return [bound_text(str(item), limit) for item in list(value)[:20] if item]

    @field_validator("retrieval_errors", mode="before")
    @classmethod
    def _bound_errors(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [str(item)[:300] for item in list(value)[:20] if item]

    # -- accounting ----------------------------------------------------------

    def token_estimate(self) -> int:
        """Rough token cost of this dossier as synthesis context."""
        total = 0
        for passage in self.passages:
            total += estimate_tokens(
                passage.original_text, passage.translation, passage.why_relevant
            )
        for node in self.nodes:
            total += estimate_tokens(node.label, node.statement)
        for frame in self.frames:
            total += estimate_tokens(frame.model_dump_json())
        for tension in self.tensions:
            total += estimate_tokens(tension.statement)
        total += estimate_tokens(*self.open_questions, *self.candidate_citations)
        return total

    def is_empty(self) -> bool:
        return not (self.passages or self.nodes or self.frames)

    def summary(self) -> dict[str, Any]:
        """Compact, wire-safe description for metadata / SSE frames."""
        return {
            "facet_id": self.facet.facet_id,
            "status": self.status,
            "passages": len(self.passages),
            "nodes": len(self.nodes),
            "frames": len(self.frames),
            "tensions": len(self.tensions),
            "open_questions": len(self.open_questions),
            "tokens": self.token_estimate(),
            "tool_calls": self.usage.tool_calls,
            "duration_ms": self.usage.duration_ms,
            "errors": len(self.retrieval_errors),
        }


def empty_dossier(facet: LeadFacet, *, status: str, error: str = "") -> ResearchDossier:
    """A dossier for a facet whose sub-agent failed or found nothing."""
    return ResearchDossier(
        facet=facet,
        status=status,
        retrieval_errors=[error] if error else [],
    )
