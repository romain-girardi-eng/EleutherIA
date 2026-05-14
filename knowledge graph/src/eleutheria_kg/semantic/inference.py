"""OWL-RL forward-chaining inference over the EleutherIA RDF graph.

This module materializes a small, deliberately restricted subset of OWL2-RL
semantics on top of the rdflib graph built by :mod:`rdf_export`:

* ``owl:inverseOf`` — for every ``s p o`` where ``owl:inverseOf(p, q)`` is
  declared in the ontology header, the triple ``o q s`` is added.
* ``owl:TransitiveProperty`` — for the transitive properties used in the
  EleutherIA ontology (``kg:partOf``, ``kg:contains``, ``kg:belongsToCorpus``,
  ``kg:hasSection``, ``kg:hasChapter``), the full transitive closure is
  materialized.
* ``owl:SymmetricProperty`` — declared symmetric properties get the
  reciprocal triple.

Why not full OWL2-RL via :mod:`owlrl`?  On the production KG (~158k
triples), full ``DeductiveClosure(OWLRL_Semantics)`` materialization is
multi-minute and produces tens of millions of extra triples we don't
need. The restricted closure here finishes in single-digit seconds and
gives us the only inferences the retrieval layer relies on (inverse +
ancestor chains).

The full OWL2-RL pass is still available via
:func:`materialize_full_owl_rl` for offline / validation use.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from rdflib import Graph, URIRef
from rdflib.namespace import OWL

from eleutheria_kg.semantic.vocab import (
    CLEAN_INVERSE_PAIRS,
    KG,
    SYMMETRIC_EDGES,
    _camel_case,
)

logger = logging.getLogger(__name__)


# Properties whose semantics are transitive in the EleutherIA ontology.
# Limiting transitive materialization to this set keeps the closure tight
# and avoids exploding on dense predicates (e.g. ``influences``).
_TRANSITIVE_PROPERTIES: tuple[URIRef, ...] = (
    URIRef(f"{KG}{_camel_case('part_of')}"),
    URIRef(f"{KG}{_camel_case('contains')}"),
    URIRef(f"{KG}{_camel_case('belongs_to_corpus')}"),
    URIRef(f"{KG}{_camel_case('has_section')}"),
    URIRef(f"{KG}{_camel_case('has_chapter')}"),
)


def _inverse_pairs_as_iris() -> list[tuple[URIRef, URIRef]]:
    """Return the clean inverse pairs as ``(prop_a, prop_b)`` IRI tuples."""
    return [
        (URIRef(f"{KG}{_camel_case(a)}"), URIRef(f"{KG}{_camel_case(b)}"))
        for a, b in CLEAN_INVERSE_PAIRS
    ]


def _symmetric_properties_as_iris() -> list[URIRef]:
    return [URIRef(f"{KG}{_camel_case(rel)}") for rel in SYMMETRIC_EDGES]


def _materialize_inverses(graph: Graph) -> int:
    """Add ``o q s`` for every ``s p o`` with a declared inverse ``q``.

    Returns the number of triples added.
    """
    added = 0
    for prop_a, prop_b in _inverse_pairs_as_iris():
        # Forward: prop_a -> prop_b
        for s, _, o in graph.triples((None, prop_a, None)):
            if (o, prop_b, s) not in graph:
                graph.add((o, prop_b, s))
                added += 1
        # Reverse: prop_b -> prop_a (since the pairs in CLEAN_INVERSE_PAIRS
        # are sometimes asymmetrically declared, we materialize both
        # directions and dedupe).
        for s, _, o in graph.triples((None, prop_b, None)):
            if (o, prop_a, s) not in graph:
                graph.add((o, prop_a, s))
                added += 1
    return added


def _materialize_symmetric(graph: Graph) -> int:
    """Add ``o p s`` for every ``s p o`` where ``p`` is symmetric."""
    added = 0
    for prop in _symmetric_properties_as_iris():
        for s, _, o in graph.triples((None, prop, None)):
            if (o, prop, s) not in graph:
                graph.add((o, prop, s))
                added += 1
    return added


def _materialize_transitive(graph: Graph, prop: URIRef) -> int:
    """Materialize the transitive closure of ``prop`` on ``graph``.

    Iterative fixed-point — each pass adds ``a prop c`` for every
    ``a prop b prop c`` not already present. Terminates when no new
    triple is added. Cycle-safe because :meth:`Graph.add` deduplicates.
    """
    added_total = 0
    while True:
        new_edges: list[tuple[URIRef, URIRef]] = []
        # Build an in-memory successor map for this property to avoid
        # quadratic graph.triples() calls per pass.
        successors: dict[URIRef, set[URIRef]] = defaultdict(set)
        for s, _, o in graph.triples((None, prop, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                successors[s].add(o)

        for a, bs in successors.items():
            for b in bs:
                for c in successors.get(b, ()):
                    if c == a:
                        continue  # skip self-loops from cycles
                    if c not in successors[a]:
                        new_edges.append((a, c))

        if not new_edges:
            break
        for a, c in new_edges:
            if (a, prop, c) not in graph:
                graph.add((a, prop, c))
                added_total += 1
    return added_total


def materialize_inverses_and_transitivity(graph: Graph) -> Graph:
    """Materialize inverse, symmetric and transitive triples in place.

    The graph is mutated and also returned so the call site can chain.
    Safe to call multiple times — the operation is idempotent.
    """
    initial = len(graph)
    inv = _materialize_inverses(graph)
    sym = _materialize_symmetric(graph)
    trans = 0
    for prop in _TRANSITIVE_PROPERTIES:
        trans += _materialize_transitive(graph, prop)
    logger.info(
        "restricted OWL-RL closure: +%d triples (inverse=%d, symmetric=%d, "
        "transitive=%d), from %d to %d",
        inv + sym + trans,
        inv,
        sym,
        trans,
        initial,
        len(graph),
    )
    return graph


def materialize_full_owl_rl(graph: Graph) -> Graph:
    """Run the full :mod:`owlrl` OWL2-RL deductive closure.

    Slow on the production KG (multi-minute); reserved for offline use
    such as full ontology validation. The graph is mutated in place.
    """
    from owlrl import (  # type: ignore[import-untyped]  # owlrl ships no py.typed marker
        DeductiveClosure,
        OWLRL_Semantics,
    )

    DeductiveClosure(OWLRL_Semantics).expand(graph)
    return graph


def transitive_closure(
    graph: Graph,
    start: URIRef,
    property_iri: URIRef,
    *,
    max_depth: int | None = None,
) -> set[URIRef]:
    """Return all ``start``-reachable nodes via repeated ``property_iri``.

    Pure: does not mutate ``graph``. Cycle-safe: a visited set prevents
    infinite recursion. ``max_depth`` (None = unbounded) caps the BFS.
    """
    visited: set[URIRef] = set()
    frontier: list[tuple[URIRef, int]] = [(start, 0)]
    while frontier:
        node, depth = frontier.pop()
        if max_depth is not None and depth >= max_depth:
            continue
        for _, _, obj in graph.triples((node, property_iri, None)):
            if not isinstance(obj, URIRef) or obj in visited:
                continue
            visited.add(obj)
            frontier.append((obj, depth + 1))
    return visited


def inverse_neighbors(graph: Graph, node: URIRef, property_iri: URIRef) -> set[URIRef]:
    """Return subjects ``s`` such that ``s property_iri node``.

    Useful when the inverse property isn't materialized yet — gives the
    same result as querying the materialized inverse, without paying the
    materialization cost.
    """
    return {
        s
        for s, _, _ in graph.triples((None, property_iri, node))
        if isinstance(s, URIRef)
    }


# Re-export for callers that need to know which properties get the
# transitive treatment (e.g. the ReAct tool's validation).
TRANSITIVE_PROPERTIES: tuple[URIRef, ...] = _TRANSITIVE_PROPERTIES


def is_transitive_property(property_iri: URIRef) -> bool:
    """True if ``property_iri`` is treated as transitive by this module."""
    return property_iri in _TRANSITIVE_PROPERTIES


def declared_inverse(property_iri: URIRef) -> URIRef | None:
    """Return the declared inverse of ``property_iri`` if any, else None.

    Honors both directions of :data:`CLEAN_INVERSE_PAIRS`.
    """
    for a, b in _inverse_pairs_as_iris():
        if property_iri == a:
            return b
        if property_iri == b:
            return a
    return None


def declared_inverse_in_graph(graph: Graph, property_iri: URIRef) -> URIRef | None:
    """Return the inverse asserted in ``graph`` via ``owl:inverseOf``."""
    for _, _, inv in graph.triples((property_iri, OWL.inverseOf, None)):
        if isinstance(inv, URIRef):
            return inv
    for inv, _, _ in graph.triples((None, OWL.inverseOf, property_iri)):
        if isinstance(inv, URIRef):
            return inv
    return None
