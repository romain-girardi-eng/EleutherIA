"""Shared relation contract for fault lines rendered by Scholar-RAG."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

# Every relation that BuildControversyFrameTool may render as a scholarly fault
# line.  R16 imports this exact set, preventing gate/runtime drift.
RENDERED_FAULT_LINE_RELATIONS: frozenset[str] = frozenset(
    {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
    }
)

# Broader relations retained in the generic retrieval dossier.  Only the set
# above is narrated as a fault line by build_controversy_frame.
DIALECTICAL_CONTEXT_RELATIONS: frozenset[str] = RENDERED_FAULT_LINE_RELATIONS | {
    "participates_in",
    "contributes_to",
    "has_position",
    "advanced_in",
    "engages_with",
    "interprets",
}


def edge_metadata(edge: Mapping[str, Any]) -> dict[str, Any]:
    value = edge.get("metadata")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        # Parenthesized because ingestion/deploy gates import this file on Python 3.12.
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return dict(parsed) if isinstance(parsed, Mapping) else {}
    return {}


def edge_attestation(edge: Mapping[str, Any]) -> str | list[Any] | None:
    """Return a non-empty R16 attestation, otherwise ``None``."""

    value = edge_metadata(edge).get("attested_by")
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        cleaned = [item for item in value if str(item).strip()]
        return cleaned or None
    return None


def edge_is_attested(edge: Mapping[str, Any]) -> bool:
    return edge_attestation(edge) is not None
