"""Coverage gap tests for the semantic layer.

Fills the uncovered branches in :mod:`eleutheria_kg.semantic.inference`,
:mod:`eleutheria_kg.semantic.proof`, :mod:`eleutheria_kg.semantic.validator`,
:mod:`eleutheria_kg.semantic.vocab`, and the shapes loader. Each test is a
focused, behavior-oriented assertion rather than a line-coverage trick.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, Literal, URIRef  # noqa: E402
from rdflib.namespace import OWL  # noqa: E402

from eleutheria_kg.semantic import build_graph  # noqa: E402
from eleutheria_kg.semantic.inference import (  # noqa: E402
    declared_inverse,
    declared_inverse_in_graph,
    inverse_neighbors,
    is_transitive_property,
    materialize_full_owl_rl,
    materialize_inverses_and_transitivity,
    transitive_closure,
)
from eleutheria_kg.semantic.proof import (  # noqa: E402
    DerivationRecord,
    build_proof_chain,
    serialize_proof_chain,
)
from eleutheria_kg.semantic.shapes import (  # noqa: E402
    load_invariant_shapes,
    load_quality_shapes,
    load_shapes,
)
from eleutheria_kg.semantic.validator import (  # noqa: E402
    ValidationReport,
    Violation,
    validate_kg,
    validate_kg_invariants,
)
from eleutheria_kg.semantic.vocab import (  # noqa: E402
    KG,
    _camel_case,
    edge_property,
    is_symmetric,
    mint_node_iri,
    standard_super_property,
    wikidata_iri,
)

WROTE: Final[URIRef] = URIRef(f"{KG}{_camel_case('wrote')}")
AUTHORED_BY: Final[URIRef] = URIRef(f"{KG}{_camel_case('authored_by')}")
PART_OF: Final[URIRef] = URIRef(f"{KG}{_camel_case('part_of')}")
PARALLEL_TO: Final[URIRef] = URIRef(f"{KG}{_camel_case('parallel_to')}")
RELATED_TO: Final[URIRef] = URIRef(f"{KG}{_camel_case('related_to')}")
INFLUENCES: Final[URIRef] = URIRef(f"{KG}{_camel_case('influences')}")


# --- vocab.py edge cases ----------------------------------------------------


def test_standard_super_property_known_and_unknown() -> None:
    """vocab.standard_super_property (line 211)."""
    assert standard_super_property("wrote") is not None
    # An edge with no clean standard equivalent returns None.
    assert standard_super_property("not_a_real_relation") is None


def test_is_symmetric_known_and_unknown() -> None:
    """vocab.is_symmetric (line 216)."""
    assert is_symmetric("parallel_to") is True
    assert is_symmetric("related_to") is True
    assert is_symmetric("wrote") is False


def test_wikidata_iri_minting() -> None:
    iri = wikidata_iri("Q183144")
    assert str(iri).endswith("Q183144")
    assert str(iri).startswith("http://www.wikidata.org/entity/")


# --- inference.py edge cases ------------------------------------------------


def test_materialize_inverses_both_directions() -> None:
    """Triggers lines 85-86 (reverse direction prop_b -> prop_a)."""
    g = Graph()
    a = mint_node_iri("work_a")
    b = mint_node_iri("person_b")
    # Seed with the inverse direction (authored_by), then expect ``wrote``
    # to be materialized from it.
    g.add((a, AUTHORED_BY, b))
    materialize_inverses_and_transitivity(g)
    assert (b, WROTE, a) in g


def test_materialize_symmetric_adds_reverse_triple() -> None:
    """Covers lines 95-97 (symmetric materialization branch)."""
    g = Graph()
    a = mint_node_iri("concept_a")
    b = mint_node_iri("concept_b")
    g.add((a, PARALLEL_TO, b))
    materialize_inverses_and_transitivity(g)
    assert (b, PARALLEL_TO, a) in g


def test_transitive_closure_skips_self_loop() -> None:
    """Covers line 122 — the ``c == a`` (self-loop) skip path."""
    g = Graph()
    a = mint_node_iri("node_loop_a")
    b = mint_node_iri("node_loop_b")
    # a -> b, b -> a forms a 2-cycle. Transitive composition would add a->a;
    # the cycle-skip branch must prevent that.
    g.add((a, PART_OF, b))
    g.add((b, PART_OF, a))
    materialize_inverses_and_transitivity(g)
    # Self-loop must not be added.
    assert (a, PART_OF, a) not in g


def test_materialize_full_owl_rl_runs_end_to_end() -> None:
    """Covers lines 166-169 (full owlrl deductive closure)."""
    pytest.importorskip("owlrl")
    g = Graph()
    person = mint_node_iri("person_x")
    work = mint_node_iri("work_x")
    g.add((person, WROTE, work))
    g.add((WROTE, OWL.inverseOf, AUTHORED_BY))
    before = len(g)
    materialize_full_owl_rl(g)
    # The full closure adds *many* triples (axiomatic, schema, inferred).
    assert len(g) > before


def test_is_transitive_property_branches() -> None:
    """Covers line 221."""
    assert is_transitive_property(PART_OF) is True
    assert is_transitive_property(WROTE) is False


def test_declared_inverse_unknown_returns_none() -> None:
    """Covers line 234 (no inverse declared)."""
    assert declared_inverse(URIRef(f"{KG}notARealProperty")) is None


def test_declared_inverse_in_graph_both_directions() -> None:
    """Covers lines 239-245."""
    g = Graph()
    g.add((WROTE, OWL.inverseOf, AUTHORED_BY))
    # Forward direction: query for inverse of `wrote` yields `authored_by`.
    assert declared_inverse_in_graph(g, WROTE) == AUTHORED_BY
    # Backward direction: query for inverse of `authored_by` yields `wrote`
    # (only the reverse triple direction matches the second branch).
    assert declared_inverse_in_graph(g, AUTHORED_BY) == WROTE
    # Unknown property: returns None (exhausts both loops).
    assert declared_inverse_in_graph(g, INFLUENCES) is None


# --- proof.py edge cases ----------------------------------------------------


def test_serialize_proof_chain_round_trip() -> None:
    """Covers serialize_proof_chain (and line 56 _triple_to_strings)."""
    g = Graph()
    plato = mint_node_iri("person_plato_p")
    republic = mint_node_iri("work_republic_p")
    g.add((plato, WROTE, republic))

    chain = build_proof_chain(g, (republic, AUTHORED_BY, plato))
    assert len(chain) == 1
    serialized = serialize_proof_chain(chain)
    assert serialized == [
        {
            "rule": "inverseOf",
            "premises": [[str(plato), str(WROTE), str(republic)]],
            "conclusion": [str(republic), str(AUTHORED_BY), str(plato)],
            "confidence": 1.0,
        }
    ]


def test_serialize_proof_chain_empty() -> None:
    assert serialize_proof_chain([]) == []


def test_try_inverse_returns_none_when_no_inverse_declared() -> None:
    """Covers proof.py line 87 (inv is None branch)."""
    g = Graph()
    a = mint_node_iri("node_no_inv_a")
    b = mint_node_iri("node_no_inv_b")
    g.add((a, INFLUENCES, b))
    # `influences` does not have a clean inverse pair, so the inverseOf
    # path returns None and the chain is empty.
    chain = build_proof_chain(g, (b, INFLUENCES, a))
    assert chain == []


def test_try_symmetric_finds_reverse_premise() -> None:
    """Covers proof.py lines 107-115 (symmetric proof step)."""
    g = Graph()
    a = mint_node_iri("concept_sym_a")
    b = mint_node_iri("concept_sym_b")
    g.add((a, PARALLEL_TO, b))
    # Claim the reverse direction. Symmetric step should derive it.
    chain = build_proof_chain(g, (b, PARALLEL_TO, a))
    assert len(chain) == 1
    assert chain[0].rule == "symmetric"
    assert chain[0].premises == [(a, PARALLEL_TO, b)]


def test_try_symmetric_returns_none_for_non_symmetric_property() -> None:
    """Covers proof.py line 107 (non-symmetric branch)."""
    g = Graph()
    a = mint_node_iri("person_sym_n_a")
    b = mint_node_iri("work_sym_n_b")
    # `wrote` is not symmetric. Without the inverse asserted, no proof.
    chain = build_proof_chain(g, (b, WROTE, a))
    assert chain == []


def test_try_transitivity_self_claim_returns_none() -> None:
    """Covers proof.py line 130 (s == o early-return)."""
    g = Graph()
    a = mint_node_iri("node_self_a")
    g.add((a, PART_OF, mint_node_iri("node_b")))
    # Claim a -> a; transitivity must refuse.
    chain = build_proof_chain(g, (a, PART_OF, a))
    assert chain == []


def test_try_transitivity_non_transitive_property() -> None:
    """Covers proof.py line 128 (property not transitive)."""
    g = Graph()
    a = mint_node_iri("person_t_a")
    b = mint_node_iri("work_t_b")
    g.add((a, WROTE, b))
    # `wrote` is not transitive — even though a path exists, transitivity
    # is not invoked.
    chain = build_proof_chain(g, (a, WROTE, mint_node_iri("nope")))
    assert chain == []


def test_try_transitivity_with_one_hop_returns_none() -> None:
    """Covers proof.py lines 156-157 (single-edge chain rejected)."""
    g = Graph()
    a = mint_node_iri("passage_one_a")
    b = mint_node_iri("work_one_b")
    g.add((a, PART_OF, b))
    # Direct assertion: build_proof_chain returns [] early (line 178), not
    # the transitivity rejection. To hit the transitivity-only path, we
    # call _try_transitivity directly.
    from eleutheria_kg.semantic.proof import _try_transitivity

    assert _try_transitivity(g, (a, PART_OF, b)) is None


def test_build_proof_chain_no_path_returns_empty() -> None:
    """Covers proof.py line 202 (fall-through empty return)."""
    g = Graph()
    a = mint_node_iri("passage_unreachable_a")
    b = mint_node_iri("work_unreachable_b")
    # Nothing connecting a and b; transitive property; no proof.
    chain = build_proof_chain(g, (a, PART_OF, b))
    assert chain == []


def test_derivation_record_defaults() -> None:
    """Covers DerivationRecord dataclass instantiation."""
    rec = DerivationRecord(node_id="x")
    assert rec.node_id == "x"
    assert rec.label == ""
    assert rec.node_type == ""
    assert rec.derivation == []
    assert rec.proof_chain == []


def test_inverse_neighbors_no_match_returns_empty_set() -> None:
    g = Graph()
    a = mint_node_iri("person_in_a")
    b = mint_node_iri("work_in_b")
    g.add((a, WROTE, b))
    # No one wrote `a` — so inverse_neighbors via WROTE for `a` is empty.
    assert inverse_neighbors(g, a, WROTE) == set()


# --- validator.py edge cases ------------------------------------------------


def _write_jsonl(tmp_path: Path, nodes: list[dict], edges: list[dict]) -> tuple[Path, Path]:
    nodes_path = tmp_path / "nodes.jsonl"
    edges_path = tmp_path / "edges.jsonl"
    nodes_path.write_text("\n".join(json.dumps(n) for n in nodes), encoding="utf-8")
    edges_path.write_text("\n".join(json.dumps(e) for e in edges), encoding="utf-8")
    return nodes_path, edges_path


def test_validation_report_counters_and_markdown(tmp_path: Path) -> None:
    """Exercise by_severity, by_constraint, by_shape, format_markdown_report
    (lines 48, 51, 56, 59-85)."""
    nodes = [
        {
            "id": "argument_unanchored_md_test",
            "label": "Floating",
            "type": "argument",
            "period": "Hellenistic",
            "description": "Plain prose.",
            "metadata": {},
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, [])
    g = build_graph(nodes_path, edges_path)
    quality = load_quality_shapes()
    report = validate_kg(g, quality)

    # Counters work and return Counters with expected keys.
    sev = report.by_severity()
    assert sev["warning"] >= 1
    constraints = report.by_constraint()
    assert sum(constraints.values()) == report.violation_count
    shapes = report.by_shape()
    assert sum(shapes.values()) == report.violation_count

    md = report.format_markdown_report(max_examples=3)
    assert "# SHACL Validation Report" in md
    assert "Conforms:" in md
    assert "By severity" in md
    assert "By shape" in md
    assert "By constraint component" in md
    assert "Examples" in md
    # max_examples=3 caps the example list.
    example_lines = [ln for ln in md.splitlines() if ln.startswith("- `https://")]
    assert len(example_lines) <= 3 * 2  # generous bound; markdown also lists shapes


def test_validation_report_markdown_empty_report() -> None:
    """format_markdown_report with no violations still renders."""
    report = ValidationReport(conforms=True, violation_count=0, violations=[])
    md = report.format_markdown_report()
    assert "Conforms: True" in md
    assert "Violation count: 0" in md


def test_validate_kg_invariants_clean_graph(tmp_path: Path) -> None:
    """Covers validator.py lines 170-172 (validate_kg_invariants wrapper)."""
    nodes = [
        {
            "id": "person_marcus_aurelius_test",
            "label": "Marcus Aurelius",
            "type": "person",
            "period": "Roman Imperial",
            "description": "Stoic emperor.",
            "metadata": {},
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, [])
    g = build_graph(nodes_path, edges_path)
    report = validate_kg_invariants(g)
    assert isinstance(report, ValidationReport)
    assert report.conforms is True
    assert report.violation_count == 0


def test_validate_kg_invariants_catches_domain_violation(
    tmp_path: Path,
) -> None:
    """Wrong source type for `wrote` triggers an invariant violation."""
    nodes = [
        # A concept node used as the source of `wrote` — should fail.
        {
            "id": "concept_bad_writer",
            "label": "Concept that wrote",
            "type": "concept",
            "period": "Hellenistic",
            "description": "Bad source type for wrote.",
            "metadata": {},
        },
        {
            "id": "work_target_test",
            "label": "Target work",
            "type": "work",
            "period": "Hellenistic",
            "description": "Target.",
            "metadata": {},
        },
    ]
    edges = [
        {
            "source": "concept_bad_writer",
            "target": "work_target_test",
            "relation": "wrote",
        }
    ]
    nodes_path, edges_path = _write_jsonl(tmp_path, nodes, edges)
    g = build_graph(nodes_path, edges_path)
    report = validate_kg_invariants(g)
    assert report.conforms is False
    assert report.violation_count >= 1
    severities = report.by_severity()
    assert severities["violation"] >= 1


# --- shapes/__init__.py edge cases ------------------------------------------


def test_load_invariant_shapes_returns_graph_with_edge_shapes() -> None:
    g = load_invariant_shapes()
    assert isinstance(g, Graph)
    # Smoke check: the wrote shape exists.
    wrote_range = URIRef("https://free-will.app/ontology/Shape_wrote_Range")
    sh_namespace = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    assert (wrote_range, rdflib.RDF.type, sh_namespace.NodeShape) in g


def test_load_quality_shapes_returns_graph_with_id_prefix_shapes() -> None:
    g = load_quality_shapes()
    assert isinstance(g, Graph)
    person_prefix = URIRef(
        "https://free-will.app/ontology/Shape_Person_IdPrefix"
    )
    sh_namespace = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    assert (person_prefix, rdflib.RDF.type, sh_namespace.NodeShape) in g


def test_load_shapes_with_explicit_directory_uses_legacy_path(
    tmp_path: Path,
) -> None:
    """load_shapes(shapes_dir=...) reads recursively from that directory."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "x.ttl").write_text(
        "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
        "@prefix kg: <https://free-will.app/ontology/> .\n"
        "kg:Shape_X a sh:NodeShape .\n",
        encoding="utf-8",
    )
    g = load_shapes(shapes_dir=tmp_path)
    assert len(g) >= 1


def test_load_from_missing_directory_returns_empty_graph(
    tmp_path: Path,
) -> None:
    """Covers shapes/__init__.py line 31 (directory does not exist)."""
    g = load_invariant_shapes(shapes_dir=tmp_path / "missing")
    assert len(g) == 0
    assert isinstance(g, Graph)


def test_load_shapes_default_loads_both_invariants_and_quality() -> None:
    g = load_shapes()
    inv = load_invariant_shapes()
    qual = load_quality_shapes()
    # The union should be a superset of each part.
    assert len(g) >= len(inv)
    assert len(g) >= len(qual)


# --- Violation dataclass ----------------------------------------------------


def test_violation_dataclass_is_frozen() -> None:
    v = Violation(
        focus_node="x",
        source_shape="y",
        severity="violation",
        message="msg",
        source_constraint_component="c",
        result_path="p",
        value="v",
    )
    with pytest.raises(Exception):
        v.focus_node = "z"  # type: ignore[misc]


# --- edge property helpers --------------------------------------------------


def test_edge_property_is_kg_namespaced() -> None:
    p = edge_property("wrote")
    assert str(p) == "https://free-will.app/ontology/wrote"


def test_transitive_closure_respects_typed_only_uriref() -> None:
    """If a triple target is a Literal (not URIRef), it's ignored."""
    g = Graph()
    a = mint_node_iri("node_lit_a")
    g.add((a, PART_OF, Literal("not an iri")))
    # Should not crash, should return empty set.
    assert transitive_closure(g, a, PART_OF) == set()
