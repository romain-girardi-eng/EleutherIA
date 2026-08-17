"""Runtime consumption of ``same_thesis_as`` equivalence components.

The canonical JSONL remains untouched here.  Two audit-confirmed over-broad
links are downgraded at the runtime boundary to ``related_to``; every other
``same_thesis_as`` edge participates in witness de-duplication.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from eleutheria_graphrag.agents.citability import CitabilityTier, evidence_policy

SAME_THESIS_RELATION = "same_thesis_as"
RELATED_RELATION = "related_to"

# Re-verified against the four node formulations during the 2026-08-17 cold
# audit repair: cylinder/internal-cause responsibility is not identical to the
# co-fated-events thesis; general datability is not identical to Epictetus-first.
LOOSE_SAME_THESIS_EDGE_IDS: frozenset[str] = frozenset(
    {
        "semmerge-same_thesis_as-argument_bobzien_2001_b1_cylinder_compatibilism_reconstruction-scholarly_argument_bobzien_chrysippus_compatibilism_fate__1",
        "semmerge-same_thesis_as-argument_frede_2011_notion_is_technical_and_datable-scholarly_argument_frede_origin_of_free_will_0",
    }
)


def effective_relation(edge: Mapping[str, Any]) -> str:
    relation = str(edge.get("relation") or "")
    if relation == SAME_THESIS_RELATION and str(edge.get("edge_id") or "") in (
        LOOSE_SAME_THESIS_EDGE_IDS
    ):
        return RELATED_RELATION
    return relation


def _metadata(node: Mapping[str, Any]) -> dict[str, Any]:
    value = node.get("metadata")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except TypeError, ValueError:
            return {}
        return dict(parsed) if isinstance(parsed, Mapping) else {}
    return {}


def formulation_richness(node_id: str, node: Mapping[str, Any]) -> tuple[int, ...]:
    """Deterministic ranking for the representative formulation of a component."""

    decision = evidence_policy(node)
    tier = {
        CitabilityTier.CITABLE: 2,
        CitabilityTier.DISCOVERABLE_ONLY: 1,
        CitabilityTier.BLOCKED: 0,
    }[decision.tier]
    metadata = _metadata(node)
    page_grounded = int(
        any(
            metadata.get(key)
            for key in ("page_grounding", "page_range", "pages", "page")
        )
    )
    verified = int(
        bool(metadata.get("citation_verified"))
        or str(metadata.get("citation_verdict") or "") in {"verified", "corrected"}
    )
    referenced = int(
        any(
            metadata.get(key)
            for key in ("verified_reference", "scholarly_work_id", "publication_id")
        )
    )
    formulation = " ".join(
        str(value or "")
        for value in (
            metadata.get("stance"),
            metadata.get("claim"),
            metadata.get("conclusion"),
            node.get("description"),
        )
    ).strip()
    # Prefer substantive, grounded formulations; node id is a stable tie-break.
    return (
        tier,
        page_grounded,
        verified,
        referenced,
        min(len(formulation), 20_000),
        -len(node_id),
    )


def same_thesis_components(
    edges: Iterable[Mapping[str, Any]],
) -> list[frozenset[str]]:
    """Connected components of effective ``same_thesis_as`` edges."""

    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for edge in edges:
        if effective_relation(edge) != SAME_THESIS_RELATION:
            continue
        source = str(edge.get("source") or edge.get("source_id") or "")
        target = str(edge.get("target") or edge.get("target_id") or "")
        if source and target and source != target:
            union(source, target)

    grouped: dict[str, set[str]] = {}
    for node_id in parent:
        grouped.setdefault(find(node_id), set()).add(node_id)
    return [frozenset(group) for group in grouped.values() if len(group) > 1]


def component_index(
    node_lookup: Mapping[str, Mapping[str, Any]],
    edges: Iterable[Mapping[str, Any]],
    *,
    eligible: Iterable[str] | None = None,
) -> tuple[dict[str, str], dict[str, frozenset[str]]]:
    """Return ``member -> representative`` and ``representative -> component``.

    ``eligible`` constrains which component members may be rendered as the
    representative (for example, argument/position nodes rather than concepts),
    while the formulation count still covers the whole equivalence component.
    """

    eligible_ids = set(eligible) if eligible is not None else None
    representative_for: dict[str, str] = {}
    members_for: dict[str, frozenset[str]] = {}
    for component in same_thesis_components(edges):
        candidates = [
            node_id
            for node_id in component
            if node_id in node_lookup
            and (eligible_ids is None or node_id in eligible_ids)
            and evidence_policy(node_lookup[node_id]).tier is not CitabilityTier.BLOCKED
        ]
        if not candidates:
            continue
        representative = max(
            candidates,
            key=lambda node_id: (
                formulation_richness(node_id, node_lookup[node_id]),
                node_id,
            ),
        )
        members_for[representative] = component
        for node_id in component:
            representative_for[node_id] = representative
    return representative_for, members_for
