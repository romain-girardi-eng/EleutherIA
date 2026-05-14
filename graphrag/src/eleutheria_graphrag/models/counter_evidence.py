"""
Counter-Evidence models — adversarial findings against a synthesized draft.

These are the contract between the CounterEvidenceHunter sub-agent and the
GraphRAGService two-pass synthesizer loop.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TestimonyType = Literal["contradiction", "qualification", "alternative"]
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
