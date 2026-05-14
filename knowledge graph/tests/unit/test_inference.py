"""Tests for the restricted OWL-RL inference layer."""

from __future__ import annotations

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, URIRef  # noqa: E402

from eleutheria_kg.semantic.inference import (  # noqa: E402
    inverse_neighbors,
    materialize_inverses_and_transitivity,
    transitive_closure,
)
from eleutheria_kg.semantic.proof import build_proof_chain  # noqa: E402
from eleutheria_kg.semantic.vocab import KG, _camel_case, mint_node_iri  # noqa: E402

WROTE = URIRef(f"{KG}{_camel_case('wrote')}")
AUTHORED_BY = URIRef(f"{KG}{_camel_case('authored_by')}")
PART_OF = URIRef(f"{KG}{_camel_case('part_of')}")
CONTAINS = URIRef(f"{KG}{_camel_case('contains')}")


def _seed_inverse_graph() -> Graph:
    """3 persons → 3 works via ``wrote``, no inverse asserted."""
    g = Graph()
    plato = mint_node_iri("person_plato")
    aristotle = mint_node_iri("person_aristotle")
    cicero = mint_node_iri("person_cicero")
    republic = mint_node_iri("work_republic")
    metaphysics = mint_node_iri("work_metaphysics")
    de_fato = mint_node_iri("work_de_fato")
    g.add((plato, WROTE, republic))
    g.add((aristotle, WROTE, metaphysics))
    g.add((cicero, WROTE, de_fato))
    return g


def _seed_part_of_chain() -> Graph:
    """passage_p1 part_of chapter_c1 part_of book_b1 part_of work_w1."""
    g = Graph()
    p1 = mint_node_iri("passage_p1")
    c1 = mint_node_iri("chapter_c1")
    b1 = mint_node_iri("book_b1")
    w1 = mint_node_iri("work_w1")
    g.add((p1, PART_OF, c1))
    g.add((c1, PART_OF, b1))
    g.add((b1, PART_OF, w1))
    return g


def test_materialize_inverses_adds_authored_by() -> None:
    g = _seed_inverse_graph()
    before = len(g)
    materialize_inverses_and_transitivity(g)

    plato = mint_node_iri("person_plato")
    republic = mint_node_iri("work_republic")
    assert (republic, AUTHORED_BY, plato) in g

    # All three inverse triples should be present.
    inverses = list(g.triples((None, AUTHORED_BY, None)))
    assert len(inverses) == 3
    assert len(g) > before


def test_materialize_is_idempotent() -> None:
    g = _seed_inverse_graph()
    materialize_inverses_and_transitivity(g)
    first = len(g)
    materialize_inverses_and_transitivity(g)
    second = len(g)
    assert first == second


def test_transitive_closure_part_of_chain() -> None:
    g = _seed_part_of_chain()
    p1 = mint_node_iri("passage_p1")
    w1 = mint_node_iri("work_w1")
    b1 = mint_node_iri("book_b1")
    c1 = mint_node_iri("chapter_c1")

    ancestors = transitive_closure(g, p1, PART_OF)
    assert {c1, b1, w1} == ancestors

    # After materialization, the direct triples exist on the graph too.
    materialize_inverses_and_transitivity(g)
    assert (p1, PART_OF, w1) in g
    assert (p1, PART_OF, b1) in g


def test_transitive_closure_on_cycle_terminates() -> None:
    g = Graph()
    a = mint_node_iri("node_a")
    b = mint_node_iri("node_b")
    c = mint_node_iri("node_c")
    g.add((a, PART_OF, b))
    g.add((b, PART_OF, c))
    g.add((c, PART_OF, a))  # cycle

    reachable = transitive_closure(g, a, PART_OF)
    # All three nodes are reachable; the start itself is not included
    # unless it appears as a successor (it does, via the cycle).
    assert b in reachable
    assert c in reachable
    assert a in reachable  # because c -> a closes the cycle


def test_transitive_closure_respects_max_depth() -> None:
    g = _seed_part_of_chain()
    p1 = mint_node_iri("passage_p1")
    c1 = mint_node_iri("chapter_c1")
    b1 = mint_node_iri("book_b1")
    w1 = mint_node_iri("work_w1")

    one_hop = transitive_closure(g, p1, PART_OF, max_depth=1)
    assert one_hop == {c1}

    two_hop = transitive_closure(g, p1, PART_OF, max_depth=2)
    assert two_hop == {c1, b1}

    three_hop = transitive_closure(g, p1, PART_OF, max_depth=3)
    assert three_hop == {c1, b1, w1}


def test_inverse_neighbors() -> None:
    g = _seed_inverse_graph()
    plato = mint_node_iri("person_plato")
    republic = mint_node_iri("work_republic")
    # Without materialization, inverse_neighbors finds Plato via ``wrote``.
    neighbors = inverse_neighbors(g, republic, WROTE)
    assert neighbors == {plato}


def test_build_proof_chain_directly_asserted() -> None:
    g = _seed_inverse_graph()
    plato = mint_node_iri("person_plato")
    republic = mint_node_iri("work_republic")
    # The triple is asserted directly — proof chain must be empty.
    chain = build_proof_chain(g, (plato, WROTE, republic))
    assert chain == []


def test_build_proof_chain_inverse() -> None:
    g = _seed_inverse_graph()
    plato = mint_node_iri("person_plato")
    republic = mint_node_iri("work_republic")
    # The inverse triple is *not* asserted, but is derivable via owl:inverseOf.
    chain = build_proof_chain(g, (republic, AUTHORED_BY, plato))
    assert len(chain) == 1
    assert chain[0].rule == "inverseOf"
    assert chain[0].premises == [(plato, WROTE, republic)]
    assert chain[0].conclusion == (republic, AUTHORED_BY, plato)


def test_build_proof_chain_transitivity() -> None:
    g = _seed_part_of_chain()
    p1 = mint_node_iri("passage_p1")
    c1 = mint_node_iri("chapter_c1")
    b1 = mint_node_iri("book_b1")
    w1 = mint_node_iri("work_w1")

    chain = build_proof_chain(g, (p1, PART_OF, w1))
    assert len(chain) == 1
    step = chain[0]
    assert step.rule == "transitivity"
    assert step.conclusion == (p1, PART_OF, w1)
    assert step.premises == [
        (p1, PART_OF, c1),
        (c1, PART_OF, b1),
        (b1, PART_OF, w1),
    ]


def test_materialize_contains_after_inverse_then_transitive() -> None:
    """Inverse of part_of is contains; both should close transitively."""
    g = _seed_part_of_chain()
    materialize_inverses_and_transitivity(g)

    p1 = mint_node_iri("passage_p1")
    w1 = mint_node_iri("work_w1")
    # Inverse direction: w1 contains p1 (via materialized inverse +
    # transitive closure on contains).
    assert (w1, CONTAINS, p1) in g
