"""
Pydantic models for the adversarial Citation Verifier (v2).

These models are deliberately separate from the existing
:class:`eleutheria_graphrag.agents.state.Citation` flow — the v2 verifier is
a *post-synthesis audit* with its own four-way status, not a pre-filter on
evidence. See ``services/citation_verifier_v2.py``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class CitationStatus(StrEnum):
    """Four-way verdict for a (claim, passage_id) pair."""

    VERIFIED = "VERIFIED"
    WEAK = "WEAK"
    REJECTED = "REJECTED"
    MISSING = "MISSING"


class DraftClaim(BaseModel):
    """One claim/citation pair extracted from the synthesizer's draft.

    A claim may have multiple citations; each becomes its own :class:`DraftClaim`
    instance during normalization so the verifier can audit them independently.
    """

    claim: str = Field(
        ..., description="The assertion the citation is supposed to support."
    )
    citation_id: str = Field(
        ..., description="passage_id (preferred) or KG node_id being cited."
    )
    citation_kind: str = Field(
        "passage", description="'passage' or 'node' — drives which MCP tool is used."
    )
    section_id: str | None = Field(
        None, description="Optional section/heading of the draft for traceability."
    )


class SynthesizedDraft(BaseModel):
    """Wrapper around a synthesizer output we want to audit.

    The verifier consumes this and produces a :class:`VerificationReport`.
    """

    question: str = ""
    answer_text: str = ""
    claims: list[DraftClaim] = Field(default_factory=list)


class CitationCheck(BaseModel):
    """Verdict for a single (claim, citation) pair."""

    citation_id: str
    status: CitationStatus
    reasoning: str = Field(
        "",
        description=(
            "One-sentence justification. For REJECTED/WEAK MUST contain a verbatim "
            "quote from the passage."
        ),
    )
    claim: str = ""
    passage_excerpt: str = Field(
        "",
        description=(
            "Verbatim excerpt of the passage as fetched fresh — never the "
            "synthesizer's paraphrase."
        ),
    )
    suggested_action: str | None = Field(
        None,
        description="Optional remediation: 'remove citation', 'hedge claim', etc.",
    )
    parse_error: bool = Field(
        False,
        description=(
            "True when this WEAK verdict is a verifier failure (LLM call failed "
            "or returned unparseable output), NOT a real adversarial judgment. "
            "Lets benchmarks/downstream distinguish 'unjudged' from 'judged weak'."
        ),
    )

    @property
    def is_passing(self) -> bool:
        """Whether the citation passed the audit (VERIFIED only)."""
        return self.status is CitationStatus.VERIFIED


class VerificationReport(BaseModel):
    """Aggregate report for all checks against one :class:`SynthesizedDraft`.

    ``flagged_for_rewrite`` lists citation_ids the orchestrator should drop,
    hedge, or replace. ``aborted`` is True when rejection rate exceeded the
    fatal threshold (default 0.50) and the draft should be discarded.
    """

    checks: list[CitationCheck] = Field(default_factory=list)
    total: int = 0
    verified: int = 0
    weak: int = 0
    rejected: int = 0
    missing: int = 0
    rejection_rate: float = Field(0.0, ge=0.0, le=1.0)
    flagged_for_rewrite: list[str] = Field(default_factory=list)
    warning: str | None = None
    aborted: bool = False

    @classmethod
    def from_checks(
        cls,
        checks: list[CitationCheck],
        *,
        warn_threshold: float = 0.20,
        abort_threshold: float = 0.50,
    ) -> VerificationReport:
        """Aggregate a list of per-citation checks into a report.

        ``warn_threshold`` and ``abort_threshold`` are computed against
        ``(REJECTED + MISSING) / total`` — both are "the citation does not
        support the claim" from the user's perspective.
        """
        total = len(checks)
        verified = sum(1 for c in checks if c.status is CitationStatus.VERIFIED)
        weak = sum(1 for c in checks if c.status is CitationStatus.WEAK)
        rejected = sum(1 for c in checks if c.status is CitationStatus.REJECTED)
        missing = sum(1 for c in checks if c.status is CitationStatus.MISSING)

        fail_count = rejected + missing
        rate = (fail_count / total) if total else 0.0

        # Flag anything that isn't a clean VERIFIED — orchestrator decides
        # remediation per-status.
        flagged = [
            c.citation_id for c in checks if c.status is not CitationStatus.VERIFIED
        ]

        warning: str | None = None
        aborted = False
        if total and rate >= abort_threshold:
            warning = (
                f"Citation rejection rate {rate:.0%} exceeds abort threshold "
                f"{abort_threshold:.0%}: draft is fundamentally unsupported."
            )
            aborted = True
        elif total and rate >= warn_threshold:
            warning = (
                f"Citation rejection rate {rate:.0%} exceeds warning threshold "
                f"{warn_threshold:.0%}: draft flagged for review."
            )

        return cls(
            checks=checks,
            total=total,
            verified=verified,
            weak=weak,
            rejected=rejected,
            missing=missing,
            rejection_rate=rate,
            flagged_for_rewrite=flagged,
            warning=warning,
            aborted=aborted,
        )
