"""Regression tests for same-thesis witness de-duplication (H-02)."""

from __future__ import annotations

from eleutheria_graphrag.agents.thesis_equivalence import (
    LOOSE_SAME_THESIS_EDGE_IDS,
    component_index,
    effective_relation,
    same_thesis_components,
)


def test_audit_confirmed_loose_links_are_runtime_related_to() -> None:
    for edge_id in LOOSE_SAME_THESIS_EDGE_IDS:
        edge = {"edge_id": edge_id, "relation": "same_thesis_as"}
        assert effective_relation(edge) == "related_to"
        assert same_thesis_components([edge]) == []


def test_component_chooses_richest_formulation_once() -> None:
    nodes = {
        "thin": {
            "id": "thin",
            "type": "argument",
            "description": "Short restatement.",
            "metadata": {"citation_verdict": "verified"},
        },
        "rich": {
            "id": "rich",
            "type": "argument",
            "description": "A long, atomically stated and source-grounded formulation. "
            * 4,
            "metadata": {
                "citation_verdict": "verified",
                "citation_verified": True,
                "verified_reference": "Author 2020, pp. 10-12",
                "page_range": "pp. 10-12",
            },
        },
    }
    edges = [
        {
            "edge_id": "same-1",
            "source": "thin",
            "target": "rich",
            "relation": "same_thesis_as",
        }
    ]
    representative_for, members_for = component_index(nodes, edges)
    assert representative_for == {"thin": "rich", "rich": "rich"}
    assert members_for == {"rich": frozenset({"thin", "rich"})}

