"""End-to-end tests for the SHACL shape generator.

These exercise ``generate_shapes.py`` against the real ontology files, verify
the emitted Turtle parses and contains the expected named shape IRIs, and
check both the invariants/quality split and the helper functions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDF  # noqa: E402

from eleutheria_kg.semantic.shapes import generate_shapes as gs  # noqa: E402

SH: Final[rdflib.Namespace] = rdflib.Namespace("http://www.w3.org/ns/shacl#")
KG: Final[rdflib.Namespace] = rdflib.Namespace("https://free-will.app/ontology/")


# --- low-level helpers ------------------------------------------------------


def test_ttl_string_escapes_backslash_and_quote() -> None:
    assert gs._ttl_string("hello") == '"hello"'
    assert gs._ttl_string('with "quote"') == '"with \\"quote\\""'
    assert gs._ttl_string("back\\slash") == '"back\\\\slash"'


def test_class_and_property_iri_use_pascal_camel() -> None:
    assert gs._class_iri("argument_framework") == "kg:ArgumentFramework"
    assert gs._property_iri("created_by") == "kg:createdBy"
    assert gs._class_iri("person") == "kg:Person"


def test_types_to_class_list_drops_wildcard() -> None:
    assert gs._types_to_class_list(["person", "*", "work"]) == [
        "kg:Person",
        "kg:Work",
    ]
    assert gs._types_to_class_list(["*"]) == []


def test_emit_or_class_single_vs_multiple() -> None:
    assert gs._emit_or_class(["kg:Person"]) == "sh:class kg:Person"
    multi = gs._emit_or_class(["kg:Person", "kg:Work"])
    assert multi.startswith("sh:or (")
    assert "[ sh:class kg:Person ]" in multi
    assert "[ sh:class kg:Work ]" in multi


# --- per-section generators -------------------------------------------------


def test_edge_shape_wildcard_both_sides_returns_empty() -> None:
    # ``related_to`` is the only relation with ``*`` on both sides.
    definition = {"source_types": ["*"], "target_types": ["*"]}
    assert gs._edge_shape("related_to", definition) == ""


def test_edge_shape_emits_both_domain_and_range_blocks() -> None:
    definition = {
        "source_types": ["person"],
        "target_types": ["work"],
    }
    shape = gs._edge_shape("wrote", definition)
    assert "kg:Shape_wrote_RangeProp" in shape
    assert "kg:Shape_wrote_Domain" in shape
    assert "sh:class kg:Work" in shape
    assert "sh:class kg:Person" in shape
    assert "sh:severity sh:Violation" in shape


def test_edge_shape_skips_domain_when_only_target_constrained() -> None:
    definition = {"source_types": ["*"], "target_types": ["person"]}
    shape = gs._edge_shape("rel", definition)
    assert "Shape_rel_RangeProp" in shape
    assert "Shape_rel_Domain" not in shape


def test_node_prefix_shape_unknown_type_returns_empty() -> None:
    assert gs._node_prefix_shape("not_a_real_type") == ""


def test_node_prefix_shape_emits_sparql_constraint() -> None:
    shape = gs._node_prefix_shape("person")
    assert "kg:Shape_Person_IdPrefix" in shape
    assert "sh:Warning" in shape
    assert "person_" in shape


# --- whole-file generators --------------------------------------------------


@pytest.fixture(scope="module")
def ontology() -> tuple[dict, dict]:
    nodes, edges = gs._load_ontology()
    return nodes, edges


def test_load_ontology_returns_dicts(ontology: tuple[dict, dict]) -> None:
    nodes, edges = ontology
    assert "person" in nodes
    assert "wrote" in edges
    assert "creates" in edges
    assert "created_by" in edges
    # Sanity check the fix: created_by source must include argument.
    assert "argument" in edges["created_by"]["source_types"]
    # The inverse `creates` must point the other way.
    assert "person" in edges["creates"]["source_types"]
    assert "work" in edges["creates"]["target_types"]


def test_generate_edges_ttl_parses_and_contains_expected_shapes(
    ontology: tuple[dict, dict],
) -> None:
    _, edges = ontology
    ttl = gs.generate_edges_ttl(edges)

    g = Graph()
    g.parse(data=ttl, format="turtle")

    # Each named-shape IRI we mint must show up as a NodeShape.
    wrote_range = URIRef("https://free-will.app/ontology/Shape_wrote_Range")
    wrote_domain = URIRef("https://free-will.app/ontology/Shape_wrote_Domain")
    assert (wrote_range, RDF.type, SH.NodeShape) in g
    assert (wrote_domain, RDF.type, SH.NodeShape) in g

    # Severity must be Violation (this is an invariant).
    severities = set(g.objects(wrote_domain, SH.severity))
    assert SH.Violation in severities


def test_generate_id_prefix_ttl_parses_and_uses_warning(
    ontology: tuple[dict, dict],
) -> None:
    nodes, _ = ontology
    ttl = gs.generate_id_prefix_ttl(nodes)

    g = Graph()
    g.parse(data=ttl, format="turtle")

    person_shape = URIRef("https://free-will.app/ontology/Shape_Person_IdPrefix")
    assert (person_shape, RDF.type, SH.NodeShape) in g
    severities = set(g.objects(person_shape, SH.severity))
    assert SH.Warning in severities


def test_generate_claims_ttl_parses_and_emits_evidence_shapes() -> None:
    ttl = gs.generate_claims_ttl()
    g = Graph()
    g.parse(data=ttl, format="turtle")

    expected = {
        URIRef(f"https://free-will.app/ontology/Shape_{name}_NeedsEvidence")
        for name in (
            "Argument",
            "ArgumentFramework",
            "Concept",
            "ConceptualEvolution",
            "Controversy",
            "Debate",
            "Group",
            "Quote",
            "School",
            "Synthesis",
        )
    }
    actual = {s for s, _, _ in g.triples((None, RDF.type, SH.NodeShape))}
    assert expected <= actual

    # All claim shapes are Warning severity post-split.
    for shape in expected:
        severities = set(g.objects(shape, SH.severity))
        assert SH.Warning in severities, f"{shape} should be Warning"


def test_generate_formatting_ttl_contains_period_and_hygiene(
    ontology: tuple[dict, dict],
) -> None:
    nodes, _ = ontology
    ttl = gs.generate_formatting_ttl(nodes)
    g = Graph()
    g.parse(data=ttl, format="turtle")

    person_period = URIRef("https://free-will.app/ontology/Shape_Person_Period")
    person_desc = URIRef(
        "https://free-will.app/ontology/Shape_Person_DescriptionHygiene"
    )
    assert (person_period, RDF.type, SH.NodeShape) in g
    assert (person_desc, RDF.type, SH.NodeShape) in g

    # Passage is intentionally excluded.
    passage_period = URIRef("https://free-will.app/ontology/Shape_Passage_Period")
    assert (passage_period, RDF.type, SH.NodeShape) not in g

    passage_school = URIRef("https://free-will.app/ontology/Shape_Passage_School")
    assert (passage_school, RDF.type, SH.NodeShape) in g
    first_temple = rdflib.Literal("First Temple / Pre-exilic Judaism")
    assert first_temple in set(g.objects(None, RDF.first))


def test_generate_philology_ttl_parses_and_contains_expected_shapes() -> None:
    ttl = gs.generate_philology_ttl()
    g = Graph()
    g.parse(data=ttl, format="turtle")

    expected = {
        URIRef("https://free-will.app/ontology/Shape_Passage_PassageRole"),
        URIRef("https://free-will.app/ontology/Shape_TextualVariant_RequiredFields"),
        URIRef("https://free-will.app/ontology/Shape_ArgumentReconstruction_Fidelity"),
        URIRef("https://free-will.app/ontology/Shape_Publication_BibtexMinimum"),
    }
    actual = {s for s, _, _ in g.triples((None, RDF.type, SH.NodeShape))}
    assert expected <= actual
    assert SH.Warning in set(g.objects(None, SH.severity))


# --- end-to-end main() ------------------------------------------------------


def test_main_writes_invariants_and_quality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the generator end-to-end pointing at the real ontology and check
    the four .ttl files appear under invariants/ and quality/."""
    invariants_dir = tmp_path / "invariants"
    quality_dir = tmp_path / "quality"
    shapes_dir = tmp_path

    monkeypatch.setattr(gs, "INVARIANTS_DIR", invariants_dir)
    monkeypatch.setattr(gs, "QUALITY_DIR", quality_dir)
    monkeypatch.setattr(gs, "SHAPES_DIR", shapes_dir)

    rc = gs.main()
    assert rc == 0
    assert (invariants_dir / "edges.ttl").is_file()
    assert (quality_dir / "id_prefix.ttl").is_file()
    assert (quality_dir / "claims.ttl").is_file()
    assert (quality_dir / "formatting.ttl").is_file()
    assert (quality_dir / "philology.ttl").is_file()

    # The output should be parseable Turtle and contain at least one shape.
    edges_g = Graph()
    edges_g.parse(invariants_dir / "edges.ttl", format="turtle")
    shape_count = len(list(edges_g.subjects(RDF.type, SH.NodeShape)))
    assert shape_count > 50, f"expected >50 edge shapes, got {shape_count}"


def test_main_removes_legacy_flat_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If older ``core.ttl``/``claims.ttl``/``formatting.ttl`` files sit at
    the shapes root, main() must remove them so the loader doesn't pick up
    a stale union."""
    shapes_dir = tmp_path
    invariants_dir = shapes_dir / "invariants"
    quality_dir = shapes_dir / "quality"

    legacy_files = [
        shapes_dir / "core.ttl",
        shapes_dir / "claims.ttl",
        shapes_dir / "formatting.ttl",
    ]
    for f in legacy_files:
        f.write_text("# stale", encoding="utf-8")
    for f in legacy_files:
        assert f.exists()

    monkeypatch.setattr(gs, "INVARIANTS_DIR", invariants_dir)
    monkeypatch.setattr(gs, "QUALITY_DIR", quality_dir)
    monkeypatch.setattr(gs, "SHAPES_DIR", shapes_dir)

    rc = gs.main()
    assert rc == 0
    for f in legacy_files:
        assert not f.exists(), f"{f} should have been removed"


def test_constants_are_frozenset() -> None:
    # Lightweight regression: these are imported in many places; if someone
    # accidentally swaps to a plain set the audit-script invariant breaks.
    assert isinstance(gs.CLAIM_TYPES, frozenset)
    assert isinstance(gs.EVIDENCE_RELATIONS, frozenset)
    assert isinstance(gs.CANONICAL_PERIODS, frozenset)
    assert "argument" in gs.CLAIM_TYPES
    assert "evidenced_by" in gs.EVIDENCE_RELATIONS
    assert "Hellenistic" in gs.CANONICAL_PERIODS


def test_invariants_shapes_align_with_ontology(
    ontology: tuple[dict, dict],
) -> None:
    """For every edge type with non-wildcard source or target types, the
    generated edges.ttl should have at least one named shape mentioning it."""
    _, edges = ontology
    ttl = gs.generate_edges_ttl(edges)

    for relation, defn in edges.items():
        src = defn.get("source_types", []) or []
        tgt = defn.get("target_types", []) or []
        # Wildcard both sides: shape is intentionally omitted.
        if "*" in src and "*" in tgt:
            continue
        # Inactive edge types (deprecated/reserved/reserved_inverse) are
        # intentionally omitted so shapes never validate dead relations.
        if defn.get("status") in gs.INACTIVE_EDGE_STATUSES:
            continue
        from eleutheria_kg.semantic.vocab import _camel_case

        camel = _camel_case(relation)
        assert f"kg:Shape_{camel}_Range" in ttl or f"kg:Shape_{camel}_Domain" in ttl, (
            f"missing shape for {relation}"
        )


def test_write_helper_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c"
    target = nested / "shape.ttl"
    out = gs._write(target, "# hi\n")
    assert out == target
    assert target.is_file()
    assert target.read_text() == "# hi\n"


def test_generate_edges_ttl_round_trips_via_disk(
    tmp_path: Path, ontology: tuple[dict, dict]
) -> None:
    """Belt-and-braces: write the TTL, reload it, count shapes is stable."""
    _, edges = ontology
    ttl1 = gs.generate_edges_ttl(edges)
    p = tmp_path / "edges.ttl"
    p.write_text(ttl1, encoding="utf-8")
    g = Graph()
    g.parse(p, format="turtle")
    count1 = len(list(g.subjects(RDF.type, SH.NodeShape)))

    # Re-generating must be byte-identical (idempotent).
    ttl2 = gs.generate_edges_ttl(edges)
    assert ttl1 == ttl2
    assert count1 > 0


def test_ontology_data_files_exist_at_expected_paths() -> None:
    """The generator points at ``ONTOLOGY_DIR``; that path must resolve."""
    assert gs.ONTOLOGY_DIR.is_dir()
    assert (gs.ONTOLOGY_DIR / "node_types.json").is_file()
    assert (gs.ONTOLOGY_DIR / "edge_types.json").is_file()
    # And the JSON parses.
    json.loads((gs.ONTOLOGY_DIR / "node_types.json").read_text())
    json.loads((gs.ONTOLOGY_DIR / "edge_types.json").read_text())
