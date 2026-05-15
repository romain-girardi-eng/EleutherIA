"""
Bibliography models — three-tier annotated bibliography output.

Contract between the BibliographyBuilder sub-agent and the GraphRAGService
deep-mode pipeline. Emitted after Synthesizer v2 and before Polishing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BibliographyTier = Literal[
    "primary_sources",
    "secondary_literature",
    "supplementary_reading",
]


class BibliographyEntry(BaseModel):
    """A single bibliography entry annotated for the draft."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(
        ...,
        description="KG node id this entry resolves to (work, scholar, scholarly_work)",
    )
    citation: str = Field(
        ...,
        description=(
            "Bibliographic citation built from node metadata "
            "(full_citation / bibliographic_ref / label + edition)"
        ),
    )
    relevance_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="0.0-1.0 — how load-bearing this source is for the draft",
    )
    in_answer_citations: list[str] = Field(
        default_factory=list,
        description="claim_ids from the input ledger that this source supports",
    )
    annotation: str = Field(
        "",
        description=(
            "One-to-two-sentence editorial gloss explaining why this source "
            "matters here. Never invents Greek/Latin text."
        ),
    )
    tier: BibliographyTier = Field(
        "secondary_literature",
        description="Which tier this entry belongs to",
    )


class AnnotatedBibliography(BaseModel):
    """Three-tier bibliography returned by the BibliographyBuilder."""

    model_config = ConfigDict(from_attributes=True)

    primary_sources: list[BibliographyEntry] = Field(default_factory=list)
    secondary_literature: list[BibliographyEntry] = Field(default_factory=list)
    supplementary_reading: list[BibliographyEntry] = Field(default_factory=list)

    @property
    def total_entries(self) -> int:
        return (
            len(self.primary_sources)
            + len(self.secondary_literature)
            + len(self.supplementary_reading)
        )

    def all_entries(self) -> list[BibliographyEntry]:
        return [
            *self.primary_sources,
            *self.secondary_literature,
            *self.supplementary_reading,
        ]


class ConsensusPosition(BaseModel):
    """One side of a scholarly debate on a topic."""

    model_config = ConfigDict(from_attributes=True)

    label: str = Field(..., description="Short tag, e.g. 'Bobzien — no'")
    scholars: list[str] = Field(
        default_factory=list,
        description="Scholar names holding this position",
    )
    citation: str = Field(
        "",
        description="Primary published citation supporting this position",
    )
    summary: str = Field(
        "",
        description="One-sentence statement of the position",
    )


class ConsensusTopic(BaseModel):
    """A scholarly consensus topic loaded from the consensus DB."""

    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    topic_slug: str
    question: str
    relevant_concepts: list[str] = Field(default_factory=list)
    relevant_persons: list[str] = Field(default_factory=list)
    relevant_period: str | None = None
    positions: list[ConsensusPosition] = Field(default_factory=list)
    consensus_status: Literal[
        "consensus", "contested", "recently_unsettled", "open"
    ] = "open"
    methodological_warning: str = ""
