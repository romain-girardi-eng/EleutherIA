"""Tests for the RDF export pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from eleutheria_kg.semantic import build_graph, export_graph  # noqa: E402
from eleutheria_kg.semantic.vocab import (  # noqa: E402
    KG,
    KG_RESOURCE,
    edge_property,
    mint_node_iri,
    node_classes,
)


SAMPLE_NODES = [
    {
        "id": "person_chrysippus_280bce_t9u0v1w2",
        "label": "Chrysippus of Soli",
        "type": "person",
        "description": "Third head of the Stoic school.",
        "period": "Hellenistic",
        "metadata": {"wikidata_qid": "Q188311"},
        "birth": "c. 279 BCE",
        "death": "c. 206 BCE",
    },
    {
        "id": "work_chrysippus_on_fate",
        "label": "On Fate (lost)",
        "type": "work",
        "description": "Lost treatise on fate; reconstructed from SVF.",
        "period": "Hellenistic",
        "metadata": {"cts_urn": "urn:cts:greekLit:tlg0331.tlg002"},
    },
    {
        "id": "concept_synkatathesis",
        "label": "Synkatathesis",
        "type": "concept",
        "description": "Assent.",
        "period": "Hellenistic",
        "metadata": {"greek_term": "συγκατάθεσις", "latin_term": "adsensio"},
    },
]

SAMPLE_EDGES = [
    {
        "source": "person_chrysippus_280bce_t9u0v1w2",
        "target": "work_chrysippus_on_fate",
        "relation": "wrote",
        "weight": 1.0,
        "metadata": {"edge_type": "authorship"},
    },
    {
        "source": "work_chrysippus_on_fate",
        "target": "concept_synkatathesis",
        "relation": "discusses",
        "weight": 0.9,
        "metadata": {"edge_type": "semantic"},
    },
]


@pytest.fixture
def jsonl_snapshot(tmp_path: Path) -> tuple[Path, Path]:
    nodes_path = tmp_path / "nodes.jsonl"
    edges_path = tmp_path / "edges.jsonl"
    nodes_path.write_text(
        "\n".join(json.dumps(n) for n in SAMPLE_NODES), encoding="utf-8"
    )
    edges_path.write_text(
        "\n".join(json.dumps(e) for e in SAMPLE_EDGES), encoding="utf-8"
    )
    return nodes_path, edges_path


def test_build_graph_emits_typed_nodes(jsonl_snapshot: tuple[Path, Path]) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    chrysippus = mint_node_iri("person_chrysippus_280bce_t9u0v1w2")
    types = {str(t) for t in g.objects(chrysippus, rdflib.RDF.type)}

    assert str(KG.Person) in types
    assert "http://www.cidoc-crm.org/cidoc-crm/E21_Person" in types
    assert "http://xmlns.com/foaf/0.1/Person" in types


def test_build_graph_emits_wikidata_sameas(jsonl_snapshot: tuple[Path, Path]) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    chrysippus = mint_node_iri("person_chrysippus_280bce_t9u0v1w2")
    same_as = list(g.objects(chrysippus, rdflib.OWL.sameAs))
    assert any("Q188311" in str(s) for s in same_as), f"got {same_as}"


def test_build_graph_emits_edge_with_kg_property(
    jsonl_snapshot: tuple[Path, Path],
) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    src = mint_node_iri("person_chrysippus_280bce_t9u0v1w2")
    tgt = mint_node_iri("work_chrysippus_on_fate")
    prop = edge_property("wrote")
    assert (src, prop, tgt) in g
    assert str(prop) == f"{KG}wrote"


def test_ontology_header_declares_subproperty(
    jsonl_snapshot: tuple[Path, Path],
) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    wrote = edge_property("wrote")
    supers = {str(o) for o in g.objects(wrote, rdflib.RDFS.subPropertyOf)}
    assert "http://purl.org/dc/terms/creator" in supers


def test_ontology_header_declares_inverse(
    jsonl_snapshot: tuple[Path, Path],
) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    wrote = edge_property("wrote")
    authored_by = edge_property("authored_by")
    assert (wrote, rdflib.OWL.inverseOf, authored_by) in g


def test_concept_carries_greek_and_latin_terms(
    jsonl_snapshot: tuple[Path, Path],
) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)

    concept = mint_node_iri("concept_synkatathesis")
    greek_terms = list(g.objects(concept, KG.greekTerm))
    latin_terms = list(g.objects(concept, KG.latinTerm))
    assert any("συγκατάθεσις" in str(t) for t in greek_terms)
    assert any("adsensio" in str(t) for t in latin_terms)


def test_round_trip_through_turtle_preserves_count(
    jsonl_snapshot: tuple[Path, Path], tmp_path: Path
) -> None:
    nodes_path, edges_path = jsonl_snapshot
    g = build_graph(nodes_path, edges_path)
    original_count = len(g)

    paths = export_graph(g, tmp_path / "sample", formats=("turtle",))
    reloaded = rdflib.Graph()
    reloaded.parse(str(paths["turtle"]), format="turtle")
    assert len(reloaded) == original_count


def test_mint_node_iri_is_dereferenceable_form() -> None:
    iri = mint_node_iri("person_zeno")
    assert str(iri) == f"{KG_RESOURCE}person_zeno"
    assert str(iri).startswith("https://free-will.app/kg/")


def test_node_classes_unknown_type_falls_back_to_kg_only() -> None:
    classes = node_classes("nonexistent_type")
    assert len(classes) == 1
    assert str(classes[0]) == f"{KG}NonexistentType"
