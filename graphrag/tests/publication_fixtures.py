"""Explicit publishable-result fixtures for GraphRAG service-boundary tests."""

from __future__ import annotations

from typing import Any


def verified_result(answer: str, *, citation_count: int = 1) -> dict[str, Any]:
    """Return a minimal result that truthfully satisfies the publication gate."""

    citations = [
        {
            "id": f"fixture-citation-{index}",
            "ref": str(index + 1),
            "type": "node",
            "label": f"Fixture citation {index + 1}",
            "verified": True,
        }
        for index in range(citation_count)
    ]
    return {
        "answer": answer,
        "question": "fixture question",
        "citations": citations,
        "claim_ledger": [],
        "metadata": {
            "scholar_synthesis": {"status": "ok", "degraded": False},
            "content_gate": {"status": "passed", "passed": True},
            "citation_verifier_v2": {
                "status": "passed",
                "total": citation_count,
                "sampled": citation_count,
                "audited_citations": citation_count,
                "total_citations": citation_count,
                "verified": citation_count,
                "weak": 0,
                "rejected": 0,
                "missing": 0,
                "parse_errors": 0,
                "aborted": False,
            },
        },
    }


__all__ = ["verified_result"]
