"""Soundness checks for the semantic vocabulary against the ontology.

Regression tests for two classes of bugs:

1. ``CLEAN_INVERSE_PAIRS`` once contained both ``(supports, supported_by)``
   and ``(argues_for, supported_by)`` — the closure then fabricated
   ``argues_for`` edges from every ``supports`` edge. Pairs must be unique
   per member and grounded in ``ontology/edge_types.json``.
2. ``EDGE_TYPE_TO_PROPERTY`` carried direction-inverted or type-invalid
   standard-vocabulary mappings (``wrote`` ⊑ dcterms:creator,
   ``influences`` ⊑ crm:P15_was_influenced_by, ``defines`` ⊑
   skos:definition, prov:wasUsedBy / prov:wasInformedBy on entity-ranged
   relations).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib.namespace import DCTERMS, FOAF, PROV, SKOS  # noqa: E402

from eleutheria_kg.semantic.vocab import (  # noqa: E402
    CITO,
    CLEAN_INVERSE_PAIRS,
    CRM,
    EDGE_TYPE_TO_PROPERTY,
    standard_super_property,
)

ONTOLOGY_EDGE_TYPES = (
    Path(__file__).resolve().parents[2] / "ontology" / "edge_types.json"
)


def _edge_types() -> dict[str, dict]:
    with ONTOLOGY_EDGE_TYPES.open(encoding="utf-8") as fh:
        return json.load(fh)["edge_types"]


def test_no_relation_appears_in_two_inverse_pairs() -> None:
    """A relation in two owl:inverseOf pairs lets the closure fabricate
    edges of the second pair's partner from the first pair's edges."""
    members = Counter()
    for a, b in CLEAN_INVERSE_PAIRS:
        members[a] += 1
        members[b] += 1
    duplicated = {rel: n for rel, n in members.items() if n > 1}
    assert duplicated == {}, f"relations in multiple inverse pairs: {duplicated}"


def test_no_duplicate_pairs_regardless_of_order() -> None:
    normalized = [frozenset(pair) for pair in CLEAN_INVERSE_PAIRS]
    dupes = [pair for pair, n in Counter(normalized).items() if n > 1]
    assert dupes == [], f"duplicated inverse pairs: {dupes}"


def test_every_inverse_pair_matches_edge_types_json() -> None:
    """Each pair (a, b) must be declared in the ontology: either
    edge_types[a].inverse == b or edge_types[b].inverse == a."""
    edge_types = _edge_types()
    for a, b in CLEAN_INVERSE_PAIRS:
        declared_ab = edge_types.get(a, {}).get("inverse") == b
        declared_ba = edge_types.get(b, {}).get("inverse") == a
        assert declared_ab or declared_ba, (
            f"pair ({a}, {b}) has no inverse declaration in edge_types.json"
        )


def test_argues_for_supports_collision_removed() -> None:
    """The fabricating pair (argues_for, supported_by) must stay out while
    the semantically canonical (supports, supported_by) stays in."""
    assert ("supports", "supported_by") in CLEAN_INVERSE_PAIRS
    assert ("argues_for", "supported_by") not in CLEAN_INVERSE_PAIRS
    members = {rel for pair in CLEAN_INVERSE_PAIRS for rel in pair}
    assert "argues_for" not in members


def test_wrote_maps_to_foaf_made_not_dcterms_creator() -> None:
    """dcterms:creator points work -> agent; ``wrote`` points agent -> work,
    so it must subsume under foaf:made (agent -> made thing)."""
    assert standard_super_property("wrote") == FOAF.made
    assert standard_super_property("authored_by") == DCTERMS.creator


def test_active_influence_relations_map_to_crm_p15i() -> None:
    """crm:P15_was_influenced_by points influenced -> influencer; the
    active-voice relations need the declared CIDOC inverse P15i."""
    assert standard_super_property("influences") == CRM.P15i_influenced
    assert standard_super_property("influenced") == CRM.P15i_influenced
    assert standard_super_property("influenced_by") == CRM.P15_was_influenced_by


def test_defines_not_mapped_to_skos_definition() -> None:
    """skos:definition is a literal-valued annotation property — it cannot
    subsume an object property between KG nodes."""
    assert standard_super_property("defines") is None
    assert SKOS.definition not in EDGE_TYPE_TO_PROPERTY.values()


def test_no_prov_activity_ranged_mappings_on_entity_relations() -> None:
    """prov:wasUsedBy (range Activity) and prov:wasInformedBy (domain and
    range Activity) entail our entity-typed nodes are Activities."""
    assert PROV.wasUsedBy not in EDGE_TYPE_TO_PROPERTY.values()
    assert PROV.wasInformedBy not in EDGE_TYPE_TO_PROPERTY.values()
    assert standard_super_property("source_for") is None
    assert standard_super_property("source_for_reconstruction") is None
    assert standard_super_property("interprets") is None
    assert standard_super_property("reconstructs") is None


def test_discusses_maps_to_cito_discusses() -> None:
    assert standard_super_property("discusses") == CITO.discusses


def test_all_mapped_relations_exist_in_ontology() -> None:
    """Every relation with a standard-vocab mapping must be grounded in
    edge_types.json — either as an edge type or as a declared inverse
    (e.g. ``founded_by`` exists only as the inverse of ``founded``)."""
    edge_types = _edge_types()
    known = set(edge_types) | {spec.get("inverse") for spec in edge_types.values()}
    unknown = [rel for rel in EDGE_TYPE_TO_PROPERTY if rel not in known]
    assert unknown == [], f"mapped relations missing from ontology: {unknown}"
