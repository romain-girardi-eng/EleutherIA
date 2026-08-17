"""IRI namespaces and vocabulary mappings for the EleutherIA RDF export.

Two namespaces are minted:
- ``KG`` (https://free-will.app/ontology/) — the EleutherIA ontology classes
  and properties (e.g., ``kg:Argument``, ``kg:authoredBy``).
- ``KG_RESOURCE`` (https://free-will.app/kg/) — the resource namespace for
  individual nodes, derived directly from the canonical ``node_id``.

Each EleutherIA node type carries a mapping to one or more standard
vocabulary classes (CIDOC-CRM, FOAF, SKOS, Dublin Core, BIBO, PROV-O).
Each edge type carries a mapping to a standard property when one exists;
otherwise the kg-namespaced property stands on its own.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from rdflib import Namespace, URIRef
from rdflib.namespace import (
    DCAT,
    DCTERMS,
    FOAF,
    OWL,
    PROV,
    RDF,
    RDFS,
    SKOS,
    VOID,
    XSD,
    DefinedNamespaceMeta,
)

# Project-owned namespaces.
KG: Final[Namespace] = Namespace("https://free-will.app/ontology/")
KG_RESOURCE: Final[Namespace] = Namespace("https://free-will.app/kg/")
KG_VOCAB: Final[Namespace] = Namespace("https://free-will.app/vocabulary/")

# External vocabularies not preloaded by rdflib.
CRM: Final[Namespace] = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
BIBO: Final[Namespace] = Namespace("http://purl.org/ontology/bibo/")
CITO: Final[Namespace] = Namespace("http://purl.org/spar/cito/")
WD: Final[Namespace] = Namespace("http://www.wikidata.org/entity/")
DCMITYPE: Final[Namespace] = Namespace("http://purl.org/dc/dcmitype/")

NAMESPACE_BINDINGS: Final[dict[str, Namespace | DefinedNamespaceMeta]] = {
    "kg": KG,
    "res": KG_RESOURCE,
    "vocab": KG_VOCAB,
    "crm": CRM,
    "foaf": FOAF,
    "skos": SKOS,
    "dcterms": DCTERMS,
    "dcmitype": DCMITYPE,
    "bibo": BIBO,
    "cito": CITO,
    "prov": PROV,
    "void": VOID,
    "dcat": DCAT,
    "owl": OWL,
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
    "wd": WD,
}


# Versioned controlled vocabularies.  The JSON scheme files are the sole
# sources of truth shared by ingestion, SHACL generation, and RDF export.
ONTOLOGY_DIR: Final[Path] = Path(__file__).resolve().parents[3] / "ontology"


def _load_controlled_scheme(name: str) -> dict[str, Any]:
    path = ONTOLOGY_DIR / f"{name}_scheme.json"
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    scheme = payload.get("scheme")
    concepts = payload.get("concepts")
    if not isinstance(scheme, dict) or scheme.get("id") != name:
        raise ValueError(f"{path}: expected scheme.id={name!r}")
    if not isinstance(concepts, list) or not concepts:
        raise ValueError(f"{path}: concepts must be a non-empty list")
    labels = [concept.get("prefLabel") for concept in concepts]
    ids = [concept.get("id") for concept in concepts]
    if not all(isinstance(value, str) and value for value in [*labels, *ids]):
        raise ValueError(f"{path}: concept ids and labels must be non-empty strings")
    if len(labels) != len(set(labels)) or len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate concept id or prefLabel")
    return payload


PERIOD_SCHEME: Final[dict[str, Any]] = _load_controlled_scheme("period")
SCHOOL_SCHEME: Final[dict[str, Any]] = _load_controlled_scheme("school")
CONTROLLED_SCHEMES: Final[dict[str, dict[str, Any]]] = {
    "period": PERIOD_SCHEME,
    "school": SCHOOL_SCHEME,
}
PERIOD_VALUES: Final[frozenset[str]] = frozenset(
    concept["prefLabel"] for concept in PERIOD_SCHEME["concepts"]
)
SCHOOL_VALUES: Final[frozenset[str]] = frozenset(
    concept["prefLabel"] for concept in SCHOOL_SCHEME["concepts"]
)


def controlled_scheme_iri(field: str) -> URIRef:
    """Return the stable SKOS ConceptScheme IRI for ``period`` or ``school``."""
    payload = CONTROLLED_SCHEMES[field]
    return URIRef(payload["scheme"]["uri"])


def controlled_concept_iri(field: str, concept_id: str) -> URIRef:
    """Return the stable SKOS concept IRI for a scheme-local concept id."""
    return URIRef(f"{controlled_scheme_iri(field)}/{concept_id}")


def controlled_concept_for_label(field: str, label: str) -> URIRef | None:
    """Resolve a retained prefLabel to its SKOS IRI, or return ``None``."""
    for concept in CONTROLLED_SCHEMES[field]["concepts"]:
        if concept["prefLabel"] == label:
            return controlled_concept_iri(field, concept["id"])
    return None


# Maps each EleutherIA node type to standard vocabulary classes.
# The kg-namespaced class is always emitted in addition to these.
NODE_TYPE_TO_CLASSES: Final[dict[str, tuple[URIRef, ...]]] = {
    "person": (CRM.E21_Person, FOAF.Person),
    "concept": (SKOS.Concept, CRM.E55_Type),
    "argument": (PROV.Entity,),
    "work": (CRM.E73_Information_Object, DCTERMS.BibliographicResource),
    "school": (CRM.E74_Group, FOAF.Group),
    "passage": (CRM.E33_Linguistic_Object,),
    "debate": (PROV.Entity,),
    "position": (PROV.Entity,),
    "event": (CRM.E5_Event,),
    "institution": (CRM.E74_Group, FOAF.Organization),
    "text_fragment": (CRM.E33_Linguistic_Object,),
    "modern_interpretation": (PROV.Entity,),
    "term": (SKOS.Concept,),
    "source_collection": (DCMITYPE.Collection,),
    "doctrine": (PROV.Entity,),
    "publication": (DCTERMS.BibliographicResource, BIBO.Document),
    "quote": (CRM.E33_Linguistic_Object,),
    "synthesis": (PROV.Entity,),
    "controversy": (PROV.Entity,),
    "conceptual_evolution": (PROV.Entity,),
    "group": (FOAF.Group, CRM.E74_Group),
    "argument_framework": (PROV.Entity,),
    "textual_variant": (CRM.E33_Linguistic_Object, PROV.Entity),
    "argument_reconstruction": (PROV.Entity,),
}


# Subset of edge types with a clean standard equivalent. The kg-namespaced
# property is always emitted; if a mapping exists here, an additional
# ``rdfs:subPropertyOf`` triple is emitted in the ontology header.
EDGE_TYPE_TO_PROPERTY: Final[dict[str, URIRef]] = {
    # ``wrote`` points agent -> work: foaf:made has exactly that direction.
    # dcterms:creator points work -> agent, so it maps ``authored_by`` only.
    "wrote": FOAF.made,
    "authored_by": DCTERMS.creator,
    "part_of": DCTERMS.isPartOf,
    "contains": DCTERMS.hasPart,
    "has_section": DCTERMS.hasPart,
    "has_chapter": DCTERMS.hasPart,
    "belongs_to_corpus": DCTERMS.isPartOf,
    "cites": CITO.cites,
    "cited_by": CITO.isCitedBy,
    "translation_of": CITO.isTranslationOf,
    "has_translation": CITO.hasTranslation,
    # crm:P15_was_influenced_by points influenced -> influencer, so only
    # ``influenced_by`` subsumes under it; the active-voice relations map to
    # the declared CIDOC inverse crm:P15i_influenced (influencer -> influenced).
    "influences": CRM.P15i_influenced,
    "influenced": CRM.P15i_influenced,
    "influenced_by": CRM.P15_was_influenced_by,
    "member_of": CRM.P107i_is_current_or_former_member_of,
    "has_member": CRM.P107_has_current_or_former_member,
    "belongs_to_school": CRM.P107i_is_current_or_former_member_of,
    "founded": CRM.P94_has_created,
    "founded_by": CRM.P94i_was_created_by,
    "evidenced_by": PROV.wasDerivedFrom,
    # ``source_for`` / ``source_for_reconstruction`` previously mapped to
    # prov:wasUsedBy, whose range is prov:Activity — our targets are
    # entities (arguments, works), so the kg properties stand on their own.
    # ``discusses`` maps to cito:discusses (deliberately unconstrained
    # domain/range in CiTO). ``interprets`` / ``reconstructs`` previously
    # mapped to prov:wasInformedBy (Activity -> Activity only) — removed.
    # ``defines`` previously mapped to skos:definition, which is a literal-
    # valued annotation property, not an object property — removed.
    "discusses": CITO.discusses,
    "variant_of": DCTERMS.isVersionOf,
    "has_variant": DCTERMS.hasVersion,
    "reconstructed_from": PROV.wasDerivedFrom,
}


# Unambiguous owl:inverseOf pairs that survive the ontology audit.
# Only pairs where both directions point at each other cleanly are listed;
# three-way inverse declarations in edge_types.json are intentionally
# excluded to avoid generating contradictory OWL axioms. In particular,
# ``argues_for`` also declares ``supported_by`` as its inverse in
# edge_types.json, but pairing it here alongside (supports, supported_by)
# made the closure fabricate ``argues_for`` edges from ``supports`` edges;
# each relation must therefore appear in at most one pair.
CLEAN_INVERSE_PAIRS: Final[tuple[tuple[str, str], ...]] = (
    ("wrote", "authored_by"),
    ("part_of", "contains"),
    ("cites", "cited_by"),
    ("translation_of", "has_translation"),
    ("teaches", "taught_by"),
    ("preserves", "preserved_in"),
    ("evidenced_by", "source_for"),
    ("interprets", "interpreted_by"),
    ("supports", "supported_by"),
    ("critiques", "critiqued_by"),
    ("argues_against", "opposed_by"),
    ("refutes", "refuted_by"),
    ("responds_to", "has_response"),
    ("discusses", "discussed_in"),
    ("employs", "employed_by"),
    ("presupposes", "presupposed_by"),
    ("grounded_in", "grounds"),
    ("holds_position", "held_by"),
    ("endorses", "endorsed_by"),
    ("rejects", "rejected_by"),
    ("extends", "extended_by"),
    ("participates_in", "has_participant"),
    ("contributes_to", "contributed_to_by"),
    ("represents", "represented_by"),
    ("exemplifies", "exemplified_by"),
    ("specializes_in", "specialist"),
    ("precedes", "follows"),
    ("variant_of", "has_variant"),
    ("reconstructs", "reconstructed_by"),
    ("reconstructed_from", "source_for_reconstruction"),
)


# Edges whose semantics are symmetric (source ↔ target equivalent).
SYMMETRIC_EDGES: Final[frozenset[str]] = frozenset(
    {"related_to", "contrasts_with", "parallel_to", "contemporary_of"}
)


def _camel_case(snake: str) -> str:
    """Convert ``snake_case`` to ``camelCase`` for OWL property names."""
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _pascal_case(snake: str) -> str:
    """Convert ``snake_case`` to ``PascalCase`` for OWL class names."""
    return "".join(p.title() for p in snake.split("_"))


def mint_node_iri(node_id: str) -> URIRef:
    """Mint a dereferenceable IRI for a KG node.

    Node IDs are opaque slugs (e.g., ``argument_agent_causation_alex``); the
    minted IRI is ``https://free-will.app/kg/<node_id>``. URL-safe by
    construction since node_id values are ASCII slugs.
    """
    return URIRef(f"{KG_RESOURCE}{node_id}")


def node_classes(node_type: str) -> tuple[URIRef, ...]:
    """Return the RDFS classes a node of the given type should be typed as.

    Always includes the kg-namespaced class; appends standard-vocabulary
    classes from :data:`NODE_TYPE_TO_CLASSES` when present. Unknown types
    fall back to the kg class only.
    """
    kg_class = URIRef(f"{KG}{_pascal_case(node_type)}")
    extras = NODE_TYPE_TO_CLASSES.get(node_type, ())
    return (kg_class, *extras)


def edge_property(relation: str) -> URIRef:
    """Return the kg-namespaced property IRI for an edge relation.

    The mapping to a standard vocabulary (if any) is materialized as an
    ``rdfs:subPropertyOf`` triple in the ontology header rather than by
    substituting the property here, so the export stays self-contained.
    """
    return URIRef(f"{KG}{_camel_case(relation)}")


def standard_super_property(relation: str) -> URIRef | None:
    """Return the standard property to declare as ``rdfs:subPropertyOf``.

    Returns ``None`` if the relation has no clean standard equivalent.
    """
    return EDGE_TYPE_TO_PROPERTY.get(relation)


def is_symmetric(relation: str) -> bool:
    """True if the relation is its own inverse (e.g., ``parallel_to``)."""
    return relation in SYMMETRIC_EDGES


def wikidata_iri(qid: str) -> URIRef:
    """Mint a Wikidata entity IRI from a QID like ``Q183144``."""
    return URIRef(f"{WD}{qid}")
