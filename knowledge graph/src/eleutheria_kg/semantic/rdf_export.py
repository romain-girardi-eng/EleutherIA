"""Build an rdflib graph from EleutherIA JSONL artifacts and serialize it.

Reads ``data/kg/nodes.jsonl`` and ``data/kg/edges.jsonl`` (the canonical
snapshot of the live KG) and produces W3C-standard RDF in three
serializations: Turtle, JSON-LD, and N-Quads. Each node is typed with both
the kg-namespaced class and the standard-vocabulary classes declared in
:mod:`eleutheria_kg.semantic.vocab`. The ontology header and a VoID/DCAT
dataset description (CC BY 4.0, Zenodo DOI) are emitted into the same
graph so the output is self-contained. Edge provenance (auto_generated,
wave, confidence, source_model from the JSONB metadata, plus the edge
weight) is preserved via standard RDF reification — see
:func:`_emit_edge_provenance` for the rationale.

This module is *read-only* over the canonical KG — it never writes back to
Postgres.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, OWL, RDF, RDFS, VOID

from eleutheria_kg.semantic.vocab import (
    CLEAN_INVERSE_PAIRS,
    EDGE_TYPE_TO_PROPERTY,
    KG,
    KG_RESOURCE,
    NAMESPACE_BINDINGS,
    NODE_TYPE_TO_CLASSES,
    SYMMETRIC_EDGES,
    _camel_case,
    _pascal_case,
    edge_property,
    mint_node_iri,
    node_classes,
    wikidata_iri,
)

logger = logging.getLogger(__name__)

# Dataset-level description constants (VoID + DCAT).
DATASET_IRI: URIRef = URIRef("https://free-will.app/kg/dataset")
CC_BY_4_IRI: URIRef = URIRef("https://creativecommons.org/licenses/by/4.0/")
ZENODO_DOI: str = "10.5281/zenodo.17379489"


# ---------- ontology header --------------------------------------------------


def _emit_ontology(g: Graph) -> None:
    """Emit class and property declarations into ``g``.

    The header captures the same information that ``node_types.json`` and
    ``edge_types.json`` carry, expressed in OWL2-RL:

    - one ``owl:Class`` per node type, with ``rdfs:subClassOf`` links to
      external vocabularies (CIDOC-CRM, FOAF, etc.)
    - one ``owl:ObjectProperty`` per edge type, with ``rdfs:subPropertyOf``
      links to standard vocab properties
    - ``owl:inverseOf`` for the clean inverse pairs
    - ``owl:SymmetricProperty`` for symmetric relations
    """
    ontology_iri = URIRef(f"{KG}EleutherIA")
    g.add((ontology_iri, RDF.type, OWL.Ontology))
    g.add((ontology_iri, RDFS.label, Literal("EleutherIA Ontology", lang="en")))
    g.add(
        (
            ontology_iri,
            DCTERMS.description,
            Literal(
                "Ontology for the EleutherIA knowledge graph: ancient "
                "philosophical debates on free will, fate, and moral "
                "responsibility (6th c. BCE – 6th c. CE) plus their modern "
                "reception.",
                lang="en",
            ),
        )
    )

    for node_type, classes in NODE_TYPE_TO_CLASSES.items():
        kg_class = URIRef(f"{KG}{_pascal_case(node_type)}")
        g.add((kg_class, RDF.type, OWL.Class))
        g.add((kg_class, RDFS.label, Literal(node_type, lang="en")))
        g.add((kg_class, RDFS.isDefinedBy, ontology_iri))
        for super_class in classes:
            g.add((kg_class, RDFS.subClassOf, super_class))

    for relation, std_prop in EDGE_TYPE_TO_PROPERTY.items():
        kg_prop = URIRef(f"{KG}{_camel_case(relation)}")
        g.add((kg_prop, RDF.type, OWL.ObjectProperty))
        g.add((kg_prop, RDFS.subPropertyOf, std_prop))
        g.add((kg_prop, RDFS.isDefinedBy, ontology_iri))

    for a, b in CLEAN_INVERSE_PAIRS:
        prop_a = URIRef(f"{KG}{_camel_case(a)}")
        prop_b = URIRef(f"{KG}{_camel_case(b)}")
        g.add((prop_a, OWL.inverseOf, prop_b))

    for symmetric in SYMMETRIC_EDGES:
        prop = URIRef(f"{KG}{_camel_case(symmetric)}")
        g.add((prop, RDF.type, OWL.SymmetricProperty))


def _emit_dataset_description(g: Graph) -> None:
    """Emit a VoID + DCAT dataset description with license and DOI.

    Makes the export self-describing for aggregators (FAIR F/R): the
    dataset node carries the CC BY 4.0 license, the Zenodo DOI as a
    resolvable IRI, and VoID partition hints.
    """
    g.add((DATASET_IRI, RDF.type, VOID.Dataset))
    g.add((DATASET_IRI, RDF.type, DCAT.Dataset))
    g.add(
        (
            DATASET_IRI,
            DCTERMS.title,
            Literal("EleutherIA Knowledge Graph", lang="en"),
        )
    )
    g.add(
        (
            DATASET_IRI,
            DCTERMS.description,
            Literal(
                "FAIR knowledge graph of ancient philosophical debates on "
                "free will, fate, and moral responsibility (6th c. BCE – "
                "6th c. CE) and their modern scholarly reception.",
                lang="en",
            ),
        )
    )
    g.add((DATASET_IRI, DCTERMS.license, CC_BY_4_IRI))
    g.add((DATASET_IRI, DCTERMS.identifier, Literal(f"doi:{ZENODO_DOI}")))
    g.add((DATASET_IRI, RDFS.seeAlso, URIRef(f"https://doi.org/{ZENODO_DOI}")))
    g.add((DATASET_IRI, DCAT.landingPage, URIRef("https://free-will.app")))
    g.add((DATASET_IRI, VOID.uriSpace, Literal(str(KG_RESOURCE))))
    g.add((DATASET_IRI, VOID.vocabulary, URIRef(str(KG))))


# ---------- node emission ----------------------------------------------------


def _normalize_mapping(value: Any) -> dict[str, Any]:
    """Return a JSON-object mapping from API/JSONL metadata variants.

    The live REST export currently serializes JSONB metadata as strings for
    some snapshots. RDF/SHACL must be resilient to both forms because these
    artifacts are the publication gate, not an optional visualization cache.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _emit_json_literal(g: Graph, iri: URIRef, prop: URIRef, value: Any) -> None:
    if value in (None, "", [], {}):
        return
    g.add(
        (
            iri,
            prop,
            Literal(json.dumps(value, ensure_ascii=False, sort_keys=True)),
        )
    )


def _emit_node(g: Graph, node: dict[str, Any]) -> None:
    node_id = node.get("id")
    node_type = node.get("type")
    if not node_id or not node_type:
        logger.warning("skipping node with missing id/type: %r", node)
        return

    iri = mint_node_iri(node_id)
    for cls in node_classes(node_type):
        g.add((iri, RDF.type, cls))

    if label := node.get("label"):
        g.add((iri, RDFS.label, Literal(label)))
    if desc := node.get("description"):
        g.add((iri, DCTERMS.description, Literal(desc)))
    if period := node.get("period"):
        g.add((iri, KG.period, Literal(period)))

    metadata = _normalize_mapping(node.get("metadata"))

    # Surface `metadata.needs_evidence` as the dedicated kg:needsEvidence
    # property so SHACL quality shapes can exempt nodes flagged as
    # intentionally unanchored. Audit batches use this flag to acknowledge
    # nodes that *could* be evidenced but currently are not.
    if metadata.get("needs_evidence") is True:
        g.add((iri, KG.needsEvidence, Literal(True)))

    # Person-specific fields.
    if node_type == "person":
        if qid := metadata.get("wikidata_qid"):
            g.add((iri, OWL.sameAs, wikidata_iri(qid)))
        for src_key, prop in (
            ("birth", KG.birthDate),
            ("death", KG.deathDate),
            ("floruit", KG.floruit),
        ):
            if value := node.get(src_key):
                g.add((iri, prop, Literal(value)))

    # Work and passage: emit CTS URN if present, both as a literal
    # identifier and as a resolvable Perseus stable-citation IRI.
    if node_type in {"work", "passage", "quote", "text_fragment"}:
        cts = metadata.get("cts_urn") or node.get("cts_urn")
        if cts:
            g.add((iri, DCTERMS.identifier, Literal(cts)))
            g.add((iri, KG.ctsURN, Literal(cts)))
            g.add((iri, RDFS.seeAlso, _cts_resolver_iri(str(cts))))

    # Passage role/provenance: distinguishes original critical text from
    # translation/paraphrase, which is essential for strict linguistic queries.
    if node_type == "passage":
        role = metadata.get("passage_role")
        if role:
            g.add((iri, KG.passageRole, Literal(str(role))))
        if source_passage_id := metadata.get("source_passage_id"):
            g.add((iri, KG.sourcePassageId, Literal(str(source_passage_id))))

    # Concept and term: emit greek/latin terms when present.
    if node_type in {"concept", "term"}:
        if grc := metadata.get("greek_term"):
            g.add((iri, KG.greekTerm, Literal(grc, lang="grc")))
        if lat := metadata.get("latin_term"):
            g.add((iri, KG.latinTerm, Literal(lat, lang="lat")))

    # Edition and uncertainty metadata are nested structured records. Keep a
    # JSON literal in RDF so downstream SPARQL can filter for presence while
    # preserving the editorial object for clients that parse it.
    editions = metadata.get("editions") or metadata.get("edition")
    _emit_json_literal(g, iri, KG.editionMetadata, editions)
    _emit_json_literal(g, iri, KG.dateUncertainty, metadata.get("date_uncertainty"))

    if node_type == "publication":
        for key in ("doi", "DOI"):
            if doi := metadata.get(key):
                g.add((iri, KG.doi, Literal(str(doi))))
                g.add((iri, RDFS.seeAlso, _doi_iri(str(doi))))
                break
        if isbn := metadata.get("isbn") or metadata.get("ISBN"):
            g.add((iri, KG.isbn, Literal(str(isbn))))
        if bibtex_key := metadata.get("bibtex_key") or metadata.get("zotero_key"):
            g.add((iri, KG.bibtexKey, Literal(str(bibtex_key))))

    if node_type == "textual_variant":
        for key, prop in (
            ("lemma", KG.lemma),
            ("lection_principale", KG.lectionPrincipale),
            ("source_critique", KG.sourceCritique),
        ):
            if value := metadata.get(key):
                g.add((iri, prop, Literal(str(value))))
        _emit_json_literal(
            g, iri, KG.lectionsAlternatives, metadata.get("lections_alternatives")
        )

    if node_type == "argument_reconstruction":
        if fidelity := metadata.get("fidelity_score"):
            g.add((iri, KG.fidelityScore, Literal(fidelity)))
        if note := metadata.get("reconstruction_note"):
            g.add((iri, KG.reconstructionNote, Literal(str(note))))


def _cts_resolver_iri(cts_urn: str) -> URIRef:
    """Resolvable HTTP IRI for a CTS URN (Perseus stable citation URI).

    Some snapshot URNs carry editorially convenient but URI-unsafe
    characters (e.g. spaces in Patrologia Latina column refs); they are
    percent-encoded so the resulting IRI always serializes cleanly.
    """
    return URIRef(
        "https://data.perseus.org/citations/" + quote(cts_urn, safe=":/.,;@()_-")
    )


def _doi_iri(doi: str) -> URIRef:
    """Resolvable https://doi.org/ IRI from a raw DOI string.

    Accepts bare DOIs (``10.x/...``), ``doi:``-prefixed values, and
    already-resolvable ``http(s)://doi.org/`` / ``dx.doi.org`` forms.
    """
    value = doi.strip()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :]
            break
    return URIRef("https://doi.org/" + quote(value, safe="/:.,;@()_-"))


# ---------- edge emission ----------------------------------------------------


# JSONB metadata keys that carry edge provenance worth preserving in RDF.
_EDGE_PROVENANCE_KEYS: tuple[tuple[str, URIRef], ...] = (
    ("auto_generated", KG.autoGenerated),
    ("wave", KG.wave),
    ("confidence", KG.confidence),
    ("source_model", KG.sourceModel),
)


def _emit_edge_provenance(
    g: Graph,
    src: URIRef,
    prop: URIRef,
    tgt: URIRef,
    edge: dict[str, Any],
) -> None:
    """Reify edge provenance via standard RDF reification (export-only).

    RDF reification (``rdf:Statement`` + ``rdf:subject/predicate/object``)
    was chosen over the PROV qualified-relation form because the source
    JSONB carries flat editorial bookkeeping (``auto_generated``, ``wave``,
    ``confidence``, ``source_model``), not activity/agent structure, and
    reification round-trips losslessly through all three serializations.
    A statement node is emitted when at least one provenance key OR a
    numeric top-level ``weight`` is present (the weight used to be silently
    dropped for edges carrying no other provenance), keyed on the stable
    ``edge_id`` when available.
    """
    metadata = _normalize_mapping(edge.get("metadata"))
    fields = [
        (prov_prop, metadata[key])
        for key, prov_prop in _EDGE_PROVENANCE_KEYS
        if metadata.get(key) not in (None, "", [], {})
    ]
    weight = edge.get("weight")
    has_weight = isinstance(weight, int | float) and not isinstance(weight, bool)
    if not fields and not has_weight:
        return

    edge_id = edge.get("edge_id")
    statement: URIRef | BNode = (
        URIRef(f"{KG_RESOURCE}statement/{edge_id}") if edge_id else BNode()
    )

    g.add((statement, RDF.type, RDF.Statement))
    g.add((statement, RDF.subject, src))
    g.add((statement, RDF.predicate, prop))
    g.add((statement, RDF.object, tgt))

    for prov_prop, value in fields:
        if prov_prop in (KG.confidence,):
            try:
                g.add((statement, prov_prop, Literal(float(value))))
            except (TypeError, ValueError):
                g.add((statement, prov_prop, Literal(str(value))))
        elif isinstance(value, bool):
            g.add((statement, prov_prop, Literal(value)))
        else:
            g.add((statement, prov_prop, Literal(str(value))))

    # The retrieval weight lives at the top level of the edge record;
    # emitted independently of the JSONB provenance fields.
    if has_weight:
        g.add((statement, KG.weight, Literal(float(weight))))


def _emit_edge(g: Graph, edge: dict[str, Any]) -> None:
    source_id = edge.get("source")
    target_id = edge.get("target")
    relation = edge.get("relation")
    if not source_id or not target_id or not relation:
        logger.warning("skipping malformed edge: %r", edge)
        return

    src = mint_node_iri(source_id)
    tgt = mint_node_iri(target_id)
    prop = edge_property(relation)
    g.add((src, prop, tgt))
    _emit_edge_provenance(g, src, prop, tgt, edge)


# ---------- public API -------------------------------------------------------


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("invalid JSON at %s:%d", path, line_no)


def build_graph(nodes_path: Path, edges_path: Path) -> Graph:
    """Read JSONL artifacts and produce an rdflib graph with ontology header."""
    g = Graph()
    for prefix, ns in NAMESPACE_BINDINGS.items():
        g.bind(prefix, ns, override=True)

    _emit_ontology(g)
    _emit_dataset_description(g)

    node_count = 0
    for node in _iter_jsonl(nodes_path):
        _emit_node(g, node)
        node_count += 1

    edge_count = 0
    for edge in _iter_jsonl(edges_path):
        _emit_edge(g, edge)
        edge_count += 1

    logger.info(
        "built rdflib graph: %d nodes, %d edges, %d triples",
        node_count,
        edge_count,
        len(g),
    )
    return g


_FORMAT_TO_EXTENSION: dict[str, tuple[str, str]] = {
    "turtle": ("ttl", "turtle"),
    "ttl": ("ttl", "turtle"),
    "jsonld": ("jsonld", "json-ld"),
    "json-ld": ("jsonld", "json-ld"),
    "ntriples": ("nt", "nt"),
    "nt": ("nt", "nt"),
}


def export_graph(
    g: Graph,
    output_base: str | Path,
    formats: tuple[str, ...] = ("turtle", "jsonld", "ntriples"),
) -> dict[str, Path]:
    """Serialize ``g`` to one or more files sharing the same basename.

    Returns a mapping of format name to the output path.
    """
    base = Path(output_base)
    written: dict[str, Path] = {}

    for fmt in formats:
        ext, serializer = _FORMAT_TO_EXTENSION[fmt]
        target = base.with_suffix(f".{ext}")
        target.parent.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(target), format=serializer)
        written[fmt] = target
        logger.info("wrote %s (%s)", target, serializer)

    return written
