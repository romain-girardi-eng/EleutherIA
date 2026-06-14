"""Proof-chain reconstruction for inferred RDF triples.

When the ReAct agent surfaces an inferred fact (e.g. "Republic V is
authored by Plato" derived from "Republic V part_of Republic" + "Republic
authored_by Plato"), the claim ledger should carry an explicit chain of
inference steps that makes the derivation auditable.

This module knows about the same restricted OWL-RL rules materialized in
:mod:`inference`: ``owl:inverseOf``, ``owl:TransitiveProperty``, and
``owl:SymmetricProperty``. Full OWL2-RL proof reconstruction is out of
scope.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from eleutheria_kg.semantic.inference import (
    TRANSITIVE_PROPERTIES,
    declared_inverse,
)
from eleutheria_kg.semantic.vocab import KG

# An RDF-ish triple of IRIs. Using URIRef everywhere keeps the chain
# round-trippable through serialization.
Triple = tuple[URIRef, URIRef, URIRef]


@dataclass
class InferenceStep:
    """One step in a proof chain.

    ``rule`` is one of:
      - ``"asserted"`` — the triple is in the canonical graph directly.
      - ``"inverseOf"`` — derived from a single asserted triple via an
        ``owl:inverseOf`` declaration.
      - ``"symmetric"`` — derived from a single asserted triple via an
        ``owl:SymmetricProperty`` declaration.
      - ``"transitivity"`` — derived from two premises (a chain of two
        triples with the same transitive property).
      - ``"subPropertyOf"`` — derived from a more specific property via
        ``rdfs:subPropertyOf`` (not yet implemented; reserved).
    """

    rule: str
    premises: list[Triple]
    conclusion: Triple
    confidence: float = 1.0


def _triple_to_strings(triple: Triple) -> list[str]:
    """Serialize a triple to a 3-list of IRI strings."""
    return [str(triple[0]), str(triple[1]), str(triple[2])]


def serialize_proof_chain(steps: list[InferenceStep]) -> list[dict]:
    """Convert proof steps to JSON-safe dicts.

    Output shape matches what the claim-ledger consumer expects:
    ``{rule, premises: [[s, p, o], ...], conclusion: [s, p, o], confidence}``.
    """
    return [
        {
            "rule": step.rule,
            "premises": [_triple_to_strings(p) for p in step.premises],
            "conclusion": _triple_to_strings(step.conclusion),
            "confidence": step.confidence,
        }
        for step in steps
    ]


def _triple_present_directly(graph: Graph, triple: Triple) -> bool:
    """True if ``triple`` is asserted in ``graph`` (not derived)."""
    return triple in graph


def _try_inverse(graph: Graph, claim: Triple) -> InferenceStep | None:
    """If ``claim = (s, p, o)`` and ``inverse(p) = q`` and ``(o, q, s)`` is
    asserted, return the inverseOf step. Else None."""
    s, p, o = claim
    inv = declared_inverse(p)
    if inv is None:
        return None
    premise: Triple = (o, inv, s)
    if premise in graph:
        return InferenceStep(
            rule="inverseOf",
            premises=[premise],
            conclusion=claim,
            confidence=1.0,
        )
    return None


def _try_symmetric(graph: Graph, claim: Triple) -> InferenceStep | None:
    """If ``p`` is symmetric and ``(o, p, s)`` is asserted, return the
    symmetric step."""
    from eleutheria_kg.semantic.inference import _symmetric_properties_as_iris

    s, p, o = claim
    if p not in _symmetric_properties_as_iris():
        return None
    premise: Triple = (o, p, s)
    if premise in graph:
        return InferenceStep(
            rule="symmetric",
            premises=[premise],
            conclusion=claim,
            confidence=1.0,
        )
    return None


def _try_transitivity(graph: Graph, claim: Triple) -> list[Triple] | None:
    """Return the asserted premise chain if ``claim`` is reachable by
    transitive composition of ``p``, else None.

    The returned list is in order: [(s, p, x1), (x1, p, x2), ..., (xn, p, o)].
    Only transitive properties (see :data:`TRANSITIVE_PROPERTIES`) are
    considered; the search is BFS over asserted edges.
    """
    s, p, o = claim
    if p not in TRANSITIVE_PROPERTIES:
        return None
    if s == o:
        return None

    # BFS over asserted edges of property p only.
    # parent[node] = (prev_node, premise_triple)
    parent: dict[URIRef, tuple[URIRef, Triple]] = {}
    queue: deque[URIRef] = deque([s])
    visited: set[URIRef] = {s}

    while queue:
        cur = queue.popleft()
        for _, _, nxt in graph.triples((cur, p, None)):
            if not isinstance(nxt, URIRef) or nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = (cur, (cur, p, nxt))
            if nxt == o:
                # Reconstruct premise chain
                chain: list[Triple] = []
                node = o
                while node in parent:
                    prev, premise = parent[node]
                    chain.append(premise)
                    node = prev
                chain.reverse()
                # Trivial single-edge chain means the triple is directly
                # asserted; we don't treat that as transitivity.
                if len(chain) <= 1:
                    return None
                return chain
            queue.append(nxt)

    return None


def _chain_confidence(
    premises: list[Triple],
    confidences: Mapping[Triple, float] | None,
) -> float:
    """Product of premise edge confidences (1.0 for unknown premises)."""
    confidence = 1.0
    if confidences:
        for premise in premises:
            confidence *= float(confidences.get(premise, 1.0))
    return confidence


def confidences_from_reified(graph: Graph) -> dict[Triple, float]:
    """Extract per-triple confidence from RDF reification statements.

    :mod:`eleutheria_kg.semantic.rdf_export` reifies edge provenance as
    ``rdf:Statement`` nodes carrying ``kg:confidence`` (curated value)
    and/or ``kg:weight`` (retrieval weight). This reads them back into a
    mapping suitable for the ``confidences`` argument of
    :func:`build_proof_chain`. ``kg:confidence`` wins over ``kg:weight``.
    """
    out: dict[Triple, float] = {}
    for statement in graph.subjects(RDF.type, RDF.Statement):
        s = graph.value(statement, RDF.subject)
        p = graph.value(statement, RDF.predicate)
        o = graph.value(statement, RDF.object)
        value = graph.value(statement, KG.confidence)
        if value is None:
            value = graph.value(statement, KG.weight)
        if (
            isinstance(s, URIRef)
            and isinstance(p, URIRef)
            and isinstance(o, URIRef)
            and isinstance(value, Literal)
        ):
            try:
                out[(s, p, o)] = float(value)
            except (TypeError, ValueError):  # fmt: skip
                continue
    return out


def build_proof_chain(
    graph: Graph,
    claim: Triple,
    *,
    confidences: Mapping[Triple, float] | None = None,
) -> list[InferenceStep]:
    """Reconstruct a proof chain for ``claim`` over ``graph``.

    ``graph`` MUST be the *asserted* graph. Passing a graph that already
    contains materialized inferences makes every derived claim look
    directly asserted (empty chain, implicit confidence 1.0) — use
    :func:`~eleutheria_kg.semantic.inference.materialize_inferred_graph`
    or :func:`~eleutheria_kg.semantic.inference.materialize_into_dataset`
    to keep inferences out of the asserted graph.

    ``confidences`` optionally maps asserted premise triples to edge
    confidence/weight values (see :func:`confidences_from_reified`); each
    step's confidence is the product of its premise confidences instead
    of a flat 1.0.

    Rule priority (cheapest first, most informative last):
      1. Directly asserted ⇒ empty list (no inference needed).
      2. inverseOf via a single asserted premise.
      3. symmetric via a single asserted premise.
      4. transitivity via a chain of asserted premises.

    Returns the list of inference steps from premises to conclusion.
    Returns an empty list when the triple is asserted directly (which
    is the desired contract per the project brief). Returns an empty
    list if no proof can be reconstructed within the supported rules.
    """
    if _triple_present_directly(graph, claim):
        return []

    steps: list[InferenceStep] = []

    inverse_step = _try_inverse(graph, claim)
    if inverse_step is not None:
        steps = [inverse_step]
    else:
        symmetric_step = _try_symmetric(graph, claim)
        if symmetric_step is not None:
            steps = [symmetric_step]
        else:
            chain = _try_transitivity(graph, claim)
            if chain is not None:
                # One InferenceStep that bundles the full premise chain.
                # The rule remains "transitivity" regardless of length.
                steps = [
                    InferenceStep(
                        rule="transitivity",
                        premises=chain,
                        conclusion=claim,
                    )
                ]

    for step in steps:
        step.confidence = _chain_confidence(step.premises, confidences)
    return steps


@dataclass
class DerivationRecord:
    """Compact representation of a derived fact + how it was obtained.

    Used by the ReAct tool to thread proof chains into the claim ledger.
    """

    node_id: str
    label: str = ""
    node_type: str = ""
    derivation: list[str] = field(default_factory=list)
    proof_chain: list[dict] = field(default_factory=list)
