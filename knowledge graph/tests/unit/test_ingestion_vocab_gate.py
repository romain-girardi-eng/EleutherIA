"""Regression tests for R18's scheme-backed ingestion behavior."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts import check_ingestion_rules as rules  # noqa: E402


def _node(period: str, school: str) -> dict:
    return {
        "id": "concept_r18_fixture",
        "node_id": "concept_r18_fixture",
        "type": "concept",
        "label": "R18 fixture",
        "description": "Controlled-vocabulary fixture.",
        "period": period,
        "school": school,
        "metadata": {
            "provenance": {
                "source": "test fixture",
                "ingested_at": "2026-08-17",
                "ingest_script": "test_ingestion_vocab_gate.py",
            }
        },
    }


def _r18_violations() -> list[tuple[str, str, str, str]]:
    return [item for item in rules.violations if item[0] == "R18_controlled_vocabulary"]


def test_r18_blocks_off_scheme_values_in_new_only_mode() -> None:
    node = _node("Imperial", "Apologetic")
    rules.violations.clear()
    rules.check([node], [], [node], [])
    violations = _r18_violations()
    assert len(violations) == 2
    assert {item[1] for item in violations} == {rules.BLOCK}
    assert {item[2] for item in violations} == {
        "period='Imperial'",
        "school='Apologetic'",
    }


def test_r18_accepts_retained_values() -> None:
    node = _node("Roman Imperial", "Christian Apologetics")
    rules.violations.clear()
    rules.check([node], [], [node], [])
    assert _r18_violations() == []


def test_r18_whole_graph_reports_grouped_warnings() -> None:
    nodes = [_node("Imperial", "Apologetic"), _node("Imperial", "Apologetic")]
    nodes[1]["id"] = nodes[1]["node_id"] = "concept_r18_fixture_2"
    rules.violations.clear()
    rules.check(nodes, [], None, None)
    violations = _r18_violations()
    assert len(violations) == 2
    assert {item[1] for item in violations} == {rules.WARN}
    assert all("2 node(s)" in item[3] for item in violations)
