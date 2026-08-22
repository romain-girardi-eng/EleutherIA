"""Central evidence-citability policy for scholarly retrieval.

The knowledge graph deliberately keeps records that are useful for discovery
but are not honest quotation evidence yet (unread bibliography, OCR debt,
apparatus, and editorial syntheses).  This module is the single decision point
that turns those markers into a stable three-tier contract consumed by search,
controversy-map assembly, prompt packing, and verification.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CitabilityTier(StrEnum):
    """Whether a node may be used as evidence in generated prose."""

    CITABLE = "citable"
    DISCOVERABLE_ONLY = "discoverable_only"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class CitabilityDecision:
    """A tier plus the exact honesty marker that caused it."""

    tier: CitabilityTier
    reason: str = ""
    marker: str = ""

    @property
    def citable(self) -> bool:
        return self.tier is CitabilityTier.CITABLE

    @property
    def discoverable(self) -> bool:
        return self.tier is not CitabilityTier.BLOCKED

    @property
    def prompt_notice(self) -> str:
        if self.tier is CitabilityTier.CITABLE:
            return ""
        if self.marker == "citation_verdict=bibliographic_import":
            return "UNREAD BIBLIOGRAPHY — discovery only; do not cite as read evidence"
        if self.tier is CitabilityTier.BLOCKED:
            return f"BLOCKED SOURCE — {self.reason}; do not use as evidence"
        return f"FLAGGED TEXT — {self.reason}; discovery only; do not quote"


_DEBT_MARKERS: tuple[tuple[str, str], ...] = (
    ("needs_reocr", "OCR must be redone"),
    ("needs_locus_mapping", "canonical locus mapping is unresolved"),
    ("needs_text_ingestion", "the source text has not been ingested"),
    ("needs_reference_remapping", "the reference must be remapped"),
    ("translation_blocked_ocr", "translation is blocked by defective OCR"),
)
_DISCOVERY_PASSAGE_ROLES = frozenset({"apparatus", "editorial_synthesis"})
_BLOCKED_VERDICTS = frozenset(
    {
        "blocked",
        "fabricated",
        "invalid",
        "rejected",
        "retracted",
    }
)


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        # Parenthesized because shared ingestion/deploy paths run on Python 3.12.
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return dict(parsed) if isinstance(parsed, Mapping) else {}
    return {}


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return value is True or (isinstance(value, int | float) and value == 1)


def honesty_markers(node_or_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return policy-relevant fields from either a node or a metadata mapping.

    The live JSONL mixes dict and stringified-dict metadata, and a few historic
    waves placed flags at top level.  Both shapes are normalised here so no
    consumer has to reproduce that defensive parsing.
    """

    source = dict(node_or_metadata or {})
    metadata = _mapping(source.get("metadata")) if "metadata" in source else source
    merged = dict(metadata)
    for key in (
        "citation_verdict",
        "citation_type",
        "bibliographic_import",
        "needs_reocr",
        "needs_locus_mapping",
        "needs_text_ingestion",
        "needs_reference_remapping",
        "translation_blocked_ocr",
        "passage_role",
        "integrity_status",
        "citation_blocked",
        "parity_status",
    ):
        if key in source:
            merged[key] = source[key]
    if "passage_role" not in merged and source.get("role"):
        merged["passage_role"] = source["role"]
    return merged


def evidence_policy(
    node_or_metadata: Mapping[str, Any] | None,
) -> CitabilityDecision:
    """Map honesty markers to ``citable | discoverable_only | blocked``.

    Precedence is fail-closed: an explicit integrity/citation block wins over a
    discovery-only marker.  ``false_positive_attested`` remains citable: in the
    current curation vocabulary it means the suspected mismatch was itself a
    false positive and the citation was verified against the source.
    """

    markers = honesty_markers(node_or_metadata)
    integrity = str(markers.get("integrity_status") or "").strip()
    if integrity:
        return CitabilityDecision(
            CitabilityTier.DISCOVERABLE_ONLY,
            reason=f"integrity_status={integrity}",
            marker="integrity_status",
        )
    if _truthy(markers.get("citation_blocked")):
        return CitabilityDecision(
            CitabilityTier.BLOCKED,
            reason="citation is explicitly blocked",
            marker="citation_blocked",
        )

    verdict = str(markers.get("citation_verdict") or "").strip().lower()
    if verdict in _BLOCKED_VERDICTS:
        return CitabilityDecision(
            CitabilityTier.BLOCKED,
            reason=f"citation_verdict={verdict}",
            marker=f"citation_verdict={verdict}",
        )

    citation_type = str(markers.get("citation_type") or "").strip().lower()
    parity_status = str(markers.get("parity_status") or "").strip().lower()
    if (
        citation_type == "related_passage_non_exact"
        or parity_status == "related_not_exact_twin"
    ):
        marker = (
            "citation_type=related_passage_non_exact"
            if citation_type == "related_passage_non_exact"
            else "parity_status=related_not_exact_twin"
        )
        return CitabilityDecision(
            CitabilityTier.DISCOVERABLE_ONLY,
            reason="linked corpus passage is related, not an exact textual twin",
            marker=marker,
        )
    if verdict == "bibliographic_import" or _truthy(
        markers.get("bibliographic_import")
    ):
        return CitabilityDecision(
            CitabilityTier.DISCOVERABLE_ONLY,
            reason="bibliographic record imported without a verified local reading",
            marker="citation_verdict=bibliographic_import",
        )

    for key, reason in _DEBT_MARKERS:
        if _truthy(markers.get(key)):
            return CitabilityDecision(
                CitabilityTier.DISCOVERABLE_ONLY,
                reason=reason,
                marker=key,
            )

    role = str(markers.get("passage_role") or "").strip().lower()
    if role in _DISCOVERY_PASSAGE_ROLES:
        return CitabilityDecision(
            CitabilityTier.DISCOVERABLE_ONLY,
            reason=f"passage_role={role} is editorial material, not primary evidence",
            marker=f"passage_role={role}",
        )
    return CitabilityDecision(CitabilityTier.CITABLE)


def stricter_decision(*decisions: CitabilityDecision) -> CitabilityDecision:
    """Return the strictest decision (blocked > discovery-only > citable)."""

    rank = {
        CitabilityTier.CITABLE: 0,
        CitabilityTier.DISCOVERABLE_ONLY: 1,
        CitabilityTier.BLOCKED: 2,
    }
    if not decisions:
        return CitabilityDecision(CitabilityTier.CITABLE)
    return max(decisions, key=lambda decision: rank[decision.tier])
