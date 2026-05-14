"""Unit tests for the SHACL validator over small synthetic graphs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
pytest.importorskip("pyshacl")

from eleutheria_kg.semantic import build_graph  # noqa: E402
from eleutheria_kg.semantic.shapes import load_shapes  # noqa: E402
from eleutheria_kg.semantic.validator import (  # noqa: E402
    ValidationReport,
    validate_kg,
)


def _write_jsonl(
    tmp_path: Path, nodes: list[dict], edges: list[dict]
) -> tuple[Path, Path]:
    nodes_path = tmp_path / "nodes.jsonl"
    edges_path = tmp_path / "edges.jsonl"
    nodes_path.write_text("\n".join(json.dumps(n) for n in nodes), encoding="utf-8")
    edges_path.write_text("\n".join(json.dumps(e) for e in edges), encoding="utf-8")
    return nodes_path, edges_path


@pytest.fixture(scope="module")
def shapes_graph() -> rdflib.Graph:
    return load_shapes()


def _violations_for_shape(report: ValidationReport, shape_suffix: str) -> list:
    return [
        v
        for v in report.violations
        if v.source_shape and v.source_shape.endswith(shape_suffix)
    ]


def test_unanchored_claim_node_triggers_violation(
    tmp_path: Path, shapes_graph: rdflib.Graph
) -> None:
    nodes = [
        {
            "id": "argument_unanchored_test",
            "label": "Floating argument",
            "type": "argument",
            "period": "Hellenistic",
            "description": "An argument with no evidence anchor.",
            "metadata": {},
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, [])
    g = build_graph(nodes_path, edges_path)
    report = validate_kg(g, shapes_graph)

    matching = _violations_for_shape(report, "Argument_NeedsEvidence")
    assert len(matching) == 1, f"expected 1 evidence violation, got {matching}"
    assert matching[0].focus_node == "https://free-will.app/kg/argument_unanchored_test"


def test_anchored_claim_node_passes_evidence_check(
    tmp_path: Path, shapes_graph: rdflib.Graph
) -> None:
    nodes = [
        {
            "id": "argument_anchored_test",
            "label": "Anchored argument",
            "type": "argument",
            "period": "Hellenistic",
            "description": "An anchored argument.",
            "metadata": {},
        },
        {
            "id": "passage_anchor_passage_test",
            "label": "Anchor passage",
            "type": "passage",
            "period": "Hellenistic",
            "metadata": {},
        },
    ]
    edges = [
        {
            "source": "argument_anchored_test",
            "target": "passage_anchor_passage_test",
            "relation": "evidenced_by",
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, edges)
    g = build_graph(nodes_path, edges_path)
    report = validate_kg(g, shapes_graph)

    matching = _violations_for_shape(report, "Argument_NeedsEvidence")
    assert matching == [], f"expected no evidence violations, got {matching}"


def test_invalid_period_triggers_formatting_warning(
    tmp_path: Path, shapes_graph: rdflib.Graph
) -> None:
    nodes = [
        {
            "id": "argument_invalid_period_test",
            "label": "Bad period argument",
            "type": "argument",
            "period": "Renaissance",  # not in CANONICAL_PERIODS
            "description": "Plain prose without markdown markers.",
            "metadata": {},
        },
        {
            "id": "passage_anchor_for_invalid_period_test",
            "label": "Anchor",
            "type": "passage",
            "period": "Hellenistic",
            "metadata": {},
        },
    ]
    edges = [
        {
            "source": "argument_invalid_period_test",
            "target": "passage_anchor_for_invalid_period_test",
            "relation": "evidenced_by",
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, edges)
    g = build_graph(nodes_path, edges_path)
    report = validate_kg(g, shapes_graph)

    matching = _violations_for_shape(report, "Argument_PeriodProp")
    assert len(matching) == 1, f"expected one period warning, got {matching}"
    assert matching[0].severity == "warning"


def test_prefix_mismatch_triggers_warning(
    tmp_path: Path, shapes_graph: rdflib.Graph
) -> None:
    nodes = [
        {
            # Person typed node whose id uses the argument_ prefix.
            "id": "argument_misnamed_person_test",
            "label": "Mis-prefixed person",
            "type": "person",
            "period": "Hellenistic",
            "description": "Plain prose without markdown markers.",
            "metadata": {},
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, [])
    g = build_graph(nodes_path, edges_path)
    report = validate_kg(g, shapes_graph)

    matching = _violations_for_shape(report, "Person_IdPrefix")
    assert len(matching) == 1, f"expected one prefix warning, got {matching}"
    assert matching[0].severity == "warning"


def test_clean_small_graph_conforms(tmp_path: Path, shapes_graph: rdflib.Graph) -> None:
    nodes = [
        {
            "id": "person_zeno_citium_test",
            "label": "Zeno of Citium",
            "type": "person",
            "period": "Hellenistic",
            "description": "Founder of Stoicism.",
            "metadata": {},
        },
        {
            "id": "work_zeno_republic_test",
            "label": "Republic (Zeno)",
            "type": "work",
            "period": "Hellenistic",
            "description": "Zeno of Citium's lost Republic.",
            "metadata": {},
        },
    ]
    edges = [
        {
            "source": "person_zeno_citium_test",
            "target": "work_zeno_republic_test",
            "relation": "wrote",
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, edges)
    g = build_graph(nodes_path, edges_path)
    report = validate_kg(g, shapes_graph)

    # Person and work have no claim-evidence constraint and the data is
    # consistent; we expect no violations at all.
    severe = [v for v in report.violations if v.severity == "violation"]
    warnings = [v for v in report.violations if v.severity == "warning"]
    assert severe == [], f"unexpected violations: {severe}"
    assert warnings == [], f"unexpected warnings: {warnings}"
    assert report.conforms is True
