"""Semantic layer for EleutherIA — RDF/OWL/SHACL reasoning sidecar.

Read-only derived layer over the canonical Postgres KG. Builds an rdflib
graph from data/kg/nodes.jsonl + edges.jsonl, exports W3C-standard
serializations (Turtle, JSON-LD, N-Quads), and provides SHACL validation
plus OWL-RL forward-chaining inference.
"""

from eleutheria_kg.semantic.inference import (
    INFERRED_GRAPH_ID,
    inverse_neighbors,
    materialize_full_owl_rl,
    materialize_inferred_graph,
    materialize_into_dataset,
    materialize_inverses_and_transitivity,
    transitive_closure,
)
from eleutheria_kg.semantic.proof import (
    InferenceStep,
    build_proof_chain,
    confidences_from_reified,
    serialize_proof_chain,
)
from eleutheria_kg.semantic.rdf_export import build_graph, export_graph
from eleutheria_kg.semantic.validator import (
    ValidationReport,
    Violation,
    validate_kg,
    validate_kg_invariants,
)
from eleutheria_kg.semantic.vocab import (
    KG,
    KG_RESOURCE,
    edge_property,
    mint_node_iri,
    node_classes,
)

__all__ = [
    "INFERRED_GRAPH_ID",
    "KG",
    "KG_RESOURCE",
    "InferenceStep",
    "ValidationReport",
    "Violation",
    "build_graph",
    "build_proof_chain",
    "confidences_from_reified",
    "edge_property",
    "export_graph",
    "inverse_neighbors",
    "materialize_full_owl_rl",
    "materialize_inferred_graph",
    "materialize_into_dataset",
    "materialize_inverses_and_transitivity",
    "mint_node_iri",
    "node_classes",
    "serialize_proof_chain",
    "transitive_closure",
    "validate_kg",
    "validate_kg_invariants",
]
