"""
Methodology + Polishing models — final-pass review of a verified draft.

Contract between the MethodologyAgent / PolishingAgent sub-agents and the
GraphRAGService deep-mode pipeline. Methodology emits structured flags
(JSON); polishing emits rewritten Markdown.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FlagType = Literal[
    "anachronism",
    "source_criticism",
    "scholarly_consensus",
    "period_appropriateness",
]

FlagSeverity = Literal["blocker", "major", "minor"]


class MethodologyFlag(BaseModel):
    """A single methodological issue flagged on a verified draft."""

    model_config = ConfigDict(from_attributes=True)

    type: FlagType = Field(
        ...,
        description=(
            "anachronism = modern term/concept projected onto an ancient "
            "author without caveat; source_criticism = direct attestation "
            "vs testimonium vs doxography conflated; scholarly_consensus = "
            "draft sides with one scholar in a live debate without naming "
            "the opposing view; period_appropriateness = doctrine assigned "
            "to the wrong school/period"
        ),
    )
    claim_id_or_excerpt: str = Field(
        ...,
        description="Claim id from the ledger, or a short verbatim quote",
    )
    issue: str = Field(
        ..., description="One sentence stating what is methodologically wrong"
    )
    scholarly_basis: str = Field(
        "",
        description=(
            "One or two sentences naming the scholars involved and the "
            "disagreement, when applicable"
        ),
    )
    suggested_revision: str = Field(
        ..., description="One sentence rewriting the claim correctly"
    )
    severity: FlagSeverity = Field(
        ...,
        description=(
            "blocker = re-synthesize; major = forward inline to polishing; "
            "minor = forward inline to polishing"
        ),
    )


class MethodologyReport(BaseModel):
    """Aggregate output of one methodology pass."""

    model_config = ConfigDict(from_attributes=True)

    methodology_flags: list[MethodologyFlag] = Field(default_factory=list)
    approved_for_polishing: bool = Field(
        True,
        description="False whenever any flag has severity=blocker.",
    )

    @property
    def blockers(self) -> list[MethodologyFlag]:
        return [f for f in self.methodology_flags if f.severity == "blocker"]

    @property
    def non_blockers(self) -> list[MethodologyFlag]:
        return [f for f in self.methodology_flags if f.severity != "blocker"]


class PolishingResult(BaseModel):
    """Polished Markdown plus accounting of what was changed."""

    model_config = ConfigDict(from_attributes=True)

    markdown: str = Field(..., description="The polished Markdown draft")
    sections_modified: int = Field(
        0, description="Count of sections the polisher restructured or added"
    )
    unresolved_flags_carried: int = Field(
        0,
        description="Methodology flags forwarded inline as [ED: …] markers",
    )
