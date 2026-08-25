"""Single fail-closed publication verdict for GraphRAG answers.

The citation auditor, the streaming boundary, and both answer caches must make
the same decision.  Keeping that decision here prevents a rejected draft from
being withheld by one path but replayed by another.

This module deliberately distinguishes *internal draft* from *publishable
answer*.  Callers may keep an internal draft for diagnostics, but a blocked
draft is stripped before it crosses the public ``GraphRAGService``/SSE boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from eleutheria_graphrag.agents.state import (
    ClaimStatus,
    ScholarlyAnswer,
)


@dataclass(frozen=True, slots=True)
class PublicationDecision:
    """Deterministic answer-publication decision."""

    publishable: bool
    reasons: tuple[str, ...]

    @property
    def status(self) -> str:
        return "passed" if self.publishable else "blocked"

    def as_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "publishable": self.publishable,
            "reasons": list(self.reasons),
            "policy": "content_and_full_citation_audit_v1",
        }


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except TypeError, ValueError:
        return default


def evaluate_publication(
    metadata: Mapping[str, Any] | None,
) -> PublicationDecision:
    """Evaluate the final content gate and the *full* citation audit.

    Fail-closed invariants:

    * the post-revision content gate ran and passed (or was explicitly marked
      not applicable for the legacy non-dialectical renderer);
    * the citation verifier completed successfully;
    * every emitted citation was audited;
    * every audited citation was ``VERIFIED``;
    * no ``WEAK``, ``REJECTED``, ``MISSING`` or parser-error verdict survives;
    * an aggregate ``aborted`` report always blocks publication.
    """

    data = _mapping(metadata)
    reasons: list[str] = []

    synthesis = _mapping(data.get("scholar_synthesis"))
    if synthesis and (
        synthesis.get("degraded") or str(synthesis.get("status") or "") != "ok"
    ):
        reasons.append("scholar_synthesis_not_authoritative")

    content = _mapping(data.get("content_gate"))
    content_status = str(content.get("status") or "")
    if content_status not in {"passed", "not_applicable"}:
        reasons.append("content_gate_not_passed")

    audit = _mapping(data.get("citation_verifier_v2"))
    audit_status = str(audit.get("status") or "")
    if audit_status != "passed":
        reasons.append("citation_audit_not_passed")

    total_citations = _integer(audit.get("total_citations"), -1)
    audited = _integer(
        audit.get("audited_citations", audit.get("sampled", audit.get("total"))),
        -1,
    )
    report_total = _integer(audit.get("total"), -1)
    verified = _integer(audit.get("verified"), 0)
    weak = _integer(audit.get("weak"), 0)
    rejected = _integer(audit.get("rejected"), 0)
    missing = _integer(audit.get("missing"), 0)
    parse_errors = _integer(audit.get("parse_errors"), 0)

    if total_citations <= 0:
        reasons.append("no_auditable_citations")
    elif audited != total_citations or report_total != total_citations:
        reasons.append("citation_audit_partial")

    if weak:
        reasons.append("weak_citations_present")
    if rejected:
        reasons.append("rejected_citations_present")
    if missing:
        reasons.append("missing_citations_present")
    if parse_errors:
        reasons.append("citation_audit_parse_errors")
    if bool(audit.get("aborted")):
        reasons.append("citation_audit_aborted")
    if total_citations > 0 and verified != total_citations:
        reasons.append("not_all_citations_verified")

    # Stable, de-duplicated order makes metadata and tests reproducible.
    unique_reasons = tuple(dict.fromkeys(reasons))
    return PublicationDecision(not unique_reasons, unique_reasons)


def annotate_publication_decision(
    answer: ScholarlyAnswer,
    *,
    withhold_prose: bool,
) -> ScholarlyAnswer:
    """Attach the shared verdict and optionally strip an unsafe draft.

    Even when the internal prose is retained for a local diagnostic caller, all
    citations are marked unverified and supported claims are downgraded.  At a
    public boundary ``withhold_prose=True`` additionally removes prose,
    citations, and the claim ledger so the rejected draft cannot be mistaken for
    an answer.
    """

    decision = evaluate_publication(answer.metadata)
    metadata = {
        **answer.metadata,
        "publication_gate": decision.as_metadata(),
    }
    if decision.publishable:
        return answer.model_copy(update={"metadata": metadata})

    reason = ", ".join(decision.reasons) or "publication gate blocked"
    unverified_citations = [
        citation.model_copy(
            update={
                "verified": False,
                "verification_note": citation.verification_note
                or f"[WITHHELD] {reason}",
            }
        )
        for citation in answer.citations
    ]
    downgraded_ledger = [
        item.model_copy(update={"status": ClaimStatus.INSUFFICIENT})
        if item.status is ClaimStatus.SUPPORTED
        else item
        for item in answer.claim_ledger
    ]
    updates: dict[str, Any] = {
        "metadata": metadata,
        "citations": unverified_citations,
        "claim_ledger": downgraded_ledger,
        "quality_badge": "Blocked",
        "insufficient_evidence": True,
    }
    if withhold_prose:
        updates.update(
            {
                "answer": "",
                "citations": [],
                "claim_ledger": [],
                "passages_used": 0,
            }
        )
    return answer.model_copy(update=updates)


def withhold_mapping_if_needed(result: Mapping[str, Any]) -> dict[str, Any]:
    """Public-boundary equivalent for ``GraphRAGService.query_dict`` results."""

    output = dict(result)
    metadata = _mapping(output.get("metadata"))
    decision = evaluate_publication(metadata)
    output["metadata"] = {
        **metadata,
        "publication_gate": decision.as_metadata(),
    }
    if decision.publishable:
        return output
    output.update(
        {
            "answer": "",
            "citations": [],
            "claim_ledger": [],
            "passages_used": 0,
            "polished_markdown": "",
            "insufficient_evidence": True,
        }
    )
    return output


__all__ = [
    "PublicationDecision",
    "annotate_publication_decision",
    "evaluate_publication",
    "withhold_mapping_if_needed",
]
