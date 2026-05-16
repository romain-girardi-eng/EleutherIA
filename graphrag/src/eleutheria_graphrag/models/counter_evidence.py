"""
Counter-Evidence models — adversarial findings against a synthesized draft.

These are the contract between the CounterEvidenceHunter sub-agent and the
GraphRAGService two-pass synthesizer loop.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TestimonyType = Literal[
    "contradiction",
    "qualification",
    "alternative",
    "scholar_critique",
    "period_shift",
    "doxographical_alternative",
    "consensus_dispute",
]
TestimonyForce = Literal["strong", "moderate", "weak"]


class ClaimUnit(BaseModel):
    """A single atomic claim extracted from a synthesized draft."""

    model_config = ConfigDict(from_attributes=True)

    claim_id: str = Field(..., description="Stable identifier (e.g. 'c1', 'c2')")
    claim_text: str = Field(..., description="The verbatim claim sentence")
    # Optional anchors the hunter may use to start its search.
    seed_node_ids: list[str] = Field(
        default_factory=list,
        description="KG node ids the claim already cites — used as search anchors",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Salient terms (concepts, persons, schools) for opposition search",
    )


class OpposingTestimony(BaseModel):
    """One piece of evidence that contradicts / qualifies / opposes a claim."""

    model_config = ConfigDict(from_attributes=True)

    type: TestimonyType = Field(
        ...,
        description=(
            "contradiction = source denies the claim; "
            "qualification = adds a limit the synthesizer missed; "
            "alternative = rival school / scholar position"
        ),
    )
    source: str = Field(..., description="Author + work + locus, or scholar name")
    source_node_id: str | None = Field(
        None, description="KG node id the testimony comes from (if any)"
    )
    passage_id: str | None = Field(
        None, description="Passage id the testimony comes from (if any)"
    )
    excerpt: str = Field(
        "",
        description="Verbatim short excerpt from the tool response — never invented",
    )
    force: TestimonyForce = Field(
        ...,
        description="Honest assessment of opposition strength",
    )
    brief_reasoning: str = Field(
        "",
        description="One sentence explaining how this opposes the claim",
    )

    # ------------------------------------------------------------------
    # v2 dimension-specific fields (optional, populated per testimony_type)
    # ------------------------------------------------------------------

    # scholar_critique
    scholar: str | None = Field(
        None,
        description="KG node id for the scholar (person) issuing the critique",
    )
    scholarly_work: str | None = Field(
        None,
        description="Label / citation of the scholarly publication",
    )
    stance: str | None = Field(
        None,
        description="engages_with stance: critiques | opposes | qualifies | agrees",
    )
    summary: str | None = Field(
        None,
        description="Short paraphrase of the scholar's critique",
    )
    page_ref: str | None = Field(
        None,
        description="Page or locus reference inside the scholarly work",
    )

    # period_shift
    from_period: str | None = Field(
        None, description="Originating period of the ancient claim"
    )
    to_period: str | None = Field(
        None, description="Period in which the later reaction emerges"
    )
    school: str | None = Field(None, description="KG node id for the reacting school")
    response_summary: str | None = Field(
        None, description="Summary of how the later period reacted"
    )
    evidence_passage_ids: list[str] = Field(
        default_factory=list,
        description="Passage ids that anchor the period-shift response",
    )

    # doxographical_alternative
    fragment: str | None = Field(
        None,
        description="Fragment locus (e.g. 'SVF II.974', 'DK 22 B1')",
    )
    alternative_interpretation: str | None = Field(
        None,
        description="Rival scholarly reconstruction of the fragment",
    )
    scholarly_source: str | None = Field(
        None,
        description="Modern scholar / publication advancing the alternative",
    )

    # consensus_dispute
    topic_slug: str | None = Field(
        None,
        description="Slug of the row in scholarly_consensus_topics",
    )
    methodological_warning: str | None = Field(
        None,
        description="One-line warning describing the unresolved dispute",
    )
    positions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Rival scholarly positions (label + proponents + summary)",
    )


class ClaimFinding(BaseModel):
    """All opposing testimonia found for a single claim."""

    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    claim_text: str
    opposing_testimonia: list[OpposingTestimony] = Field(default_factory=list)

    @property
    def has_strong_opposition(self) -> bool:
        return any(t.force == "strong" for t in self.opposing_testimonia)


class SynthesizedDraft(BaseModel):
    """The synthesizer's v1 output, fed into the hunter."""

    model_config = ConfigDict(from_attributes=True)

    answer: str = Field(..., description="The full v1 draft answer")
    claims: list[ClaimUnit] = Field(
        default_factory=list,
        description="Atomic claims extracted from the draft",
    )


class CounterEvidenceReport(BaseModel):
    """Aggregate output of one hunt across all claims."""

    model_config = ConfigDict(from_attributes=True)

    per_claim_findings: list[ClaimFinding] = Field(default_factory=list)
    aggregate_summary: str = Field(
        "",
        description="2-3 sentence summary of where the draft is most one-sided",
    )

    @property
    def total_testimonia(self) -> int:
        return sum(len(f.opposing_testimonia) for f in self.per_claim_findings)

    def strong_findings(self) -> list[ClaimFinding]:
        return [f for f in self.per_claim_findings if f.has_strong_opposition]
