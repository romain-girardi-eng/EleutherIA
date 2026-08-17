"""R16 gate/runtime relation parity and historical debt accounting (C-04)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from eleutheria_graphrag.agents.dialectical_relations import (
    RENDERED_FAULT_LINE_RELATIONS,
)


def _checker():
    path = Path(__file__).parents[3] / "scripts" / "check_ingestion_rules.py"
    spec = importlib.util.spec_from_file_location("check_ingestion_rules_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _edge(relation: str, *, attested: bool = False) -> dict:
    metadata = {"attested_by": "Source 2020, p. 12"} if attested else {}
    return {
        "edge_id": f"edge-{relation}",
        "source": "a",
        "source_id": "a",
        "target": "b",
        "target_id": "b",
        "relation": relation,
        "metadata": metadata,
    }


def test_r16_covers_exactly_every_rendered_fault_line_relation() -> None:
    checker = _checker()
    assert checker.DIALECTICAL_RELATIONS == RENDERED_FAULT_LINE_RELATIONS

    edges = [_edge(relation) for relation in RENDERED_FAULT_LINE_RELATIONS]
    checker.check([], edges, [], edges)
    r16 = [item for item in checker.violations if item[0] == "R16_dialectic_unattested"]
    assert {item[2] for item in r16} == {edge["edge_id"] for edge in edges}
    assert all(item[1] == checker.BLOCK for item in r16)


def test_r16_accepts_attested_new_fault_lines() -> None:
    checker = _checker()
    edges = [
        _edge(relation, attested=True)
        for relation in RENDERED_FAULT_LINE_RELATIONS
    ]
    checker.check([], edges, [], edges)
    assert not [
        item for item in checker.violations if item[0] == "R16_dialectic_unattested"
    ]


def test_r16_counts_existing_unattested_debt_by_relation() -> None:
    checker = _checker()
    edges = [_edge("supports"), _edge("supports"), _edge("responds_to")]
    checker.check([], edges, None, None)
    assert checker.r16_debt_by_relation == {"supports": 2, "responds_to": 1}
    r16 = [item for item in checker.violations if item[0] == "R16_dialectic_unattested"]
    assert all(item[1] == checker.WARN for item in r16)

