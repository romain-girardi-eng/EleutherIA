"""Auto-generate the SHACL shape files from ontology + audit constants.

The shapes are split into two severities:

- ``shapes/invariants/`` — true data invariants. Severity ``sh:Violation``.
  Currently: edge source/target type constraints (domain/range) drawn from
  ``edge_types.json``. A violation here is a data bug.
- ``shapes/quality/`` — quality goals that surface a triage backlog but
  do not block conformance. Severity ``sh:Warning``. Currently:
  ``NeedsEvidence`` (claim-bearing nodes lacking anchors), ``IdPrefix``
  (id prefix conventions), ``Period``/``School`` (controlled scheme
  whitelists), and ``DescriptionHygiene`` (no markdown in non-passage
  descriptions).

Idempotent: re-running overwrites the .ttl files in place. The output is
not intended to be hand-edited — diff this script if shapes need to evolve.

Sources of truth:
- ``knowledge graph/ontology/node_types.json`` — node types
- ``knowledge graph/ontology/edge_types.json`` — edge types and
  source/target type constraints
- ``knowledge graph/ontology/period_scheme.json`` — period values
- ``knowledge graph/ontology/school_scheme.json`` — school values
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[5]
ONTOLOGY_DIR = ROOT / "knowledge graph" / "ontology"
SHAPES_DIR = Path(__file__).parent
INVARIANTS_DIR = SHAPES_DIR / "invariants"
QUALITY_DIR = SHAPES_DIR / "quality"

# Audit constants that are not controlled vocabularies remain local so this
# generator does not import the asyncpg-dependent audit module.
CLAIM_TYPES: Final[frozenset[str]] = frozenset(
    {
        "argument",
        "argument_framework",
        "concept",
        "conceptual_evolution",
        "controversy",
        "debate",
        "group",
        "quote",
        "school",
        "synthesis",
    }
)

EVIDENCE_RELATIONS: Final[frozenset[str]] = frozenset(
    {"evidenced_by", "grounded_in", "source_for"}
)


def _load_scheme_values(name: str) -> frozenset[str]:
    payload = json.loads(
        (ONTOLOGY_DIR / f"{name}_scheme.json").read_text(encoding="utf-8")
    )
    if payload.get("scheme", {}).get("id") != name:
        raise ValueError(f"invalid {name} controlled-vocabulary scheme")
    values = [concept.get("prefLabel") for concept in payload.get("concepts", [])]
    if not values or not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"{name} scheme has an invalid prefLabel")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} scheme has duplicate prefLabels")
    return frozenset(values)


CANONICAL_PERIODS: Final[frozenset[str]] = _load_scheme_values("period")
CANONICAL_SCHOOLS: Final[frozenset[str]] = _load_scheme_values("school")

PASSAGE_ROLES: Final[tuple[str, ...]] = ("original", "translation", "paraphrase")

# Edge statuses that no longer denote a live, assertable relation. Shapes
# for these would validate Domain/Range on properties that new data should
# never use (deprecated) or that only exist as the auto-generated inverse
# of another relation (reserved/reserved_inverse) — skip them entirely.
INACTIVE_EDGE_STATUSES: Final[frozenset[str]] = frozenset(
    {"deprecated", "reserved", "reserved_inverse"}
)

# Suspicious node-id prefixes whose first segment must match the node type.
PREFIX_TO_TYPE_PREFIX: Final[dict[str, str]] = {
    "argument": "argument",
    "concept": "concept",
    "controversy": "controversy",
    "debate": "debate",
    "event": "event",
    "group": "group",
    "person": "person",
    "publication": "publication",
    "quote": "quote",
    "school": "school",
    "synthesis": "synthesis",
    "term": "term",
    "textual_variant": "textual_variant",
    "work": "work",
}

# Legitimate project-specific ID prefixes that must NEVER be flagged as
# "ID prefix violations" by the id_prefix SHACL shape. These coexist with
# the canonical type prefixes above; the swap-detection logic in
# ``_node_prefix_shape`` only fires when an ID starts with a *foreign
# canonical* prefix, so the prefixes listed here pass through naturally.
# Documenting them here makes the convention explicit:
# - ``sc<N>(bis)?_*``        : passage IDs anchored to a Sources Chrétiennes volume
# - ``scholarly_argument_*`` : argument nodes from the modern-scholarship layer
# - ``scholar_position_*``   : scholarly_position nodes
# - ``scholarly_work_*``     : modern scholarly publications
# - ``scholar_*``            : modern scholars (persons in the secondary layer)
# - ``pub_*``                : legacy publication-shell IDs
# - ``council_*``            : ecumenical/local councils (events)
# - ``collection_*``         : doxographic/source collections
# - ``source_collection_*``  : critical-edition source collections
# - ``argument_framework_*`` : meta-argument frameworks
# - ``conceptual_evolution_*``: concept-evolution nodes
# - ``position_*`` / ``scholar_position_*``: positions in debates
ALLOWED_PROJECT_PREFIXES: Final[frozenset[str]] = frozenset(
    {
        "sc",
        "scholar",
        "scholarly_argument",
        "scholar_position",
        "scholarly_work",
        "pub",
        "council",
        "collection",
        "source_collection",
        "argument_framework",
        "conceptual_evolution",
        "position",
        "passage",
    }
)

HEADER = """\
# AUTO-GENERATED by knowledge graph/src/eleutheria_kg/semantic/shapes/generate_shapes.py
# Do not edit by hand — re-run the generator instead.

@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix kg:    <https://free-will.app/ontology/> .
@prefix res:   <https://free-will.app/kg/> .
"""


def _camel_case(snake: str) -> str:
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _pascal_case(snake: str) -> str:
    return "".join(p.title() for p in snake.split("_"))


def _load_ontology() -> tuple[dict, dict]:
    nodes = json.loads((ONTOLOGY_DIR / "node_types.json").read_text())["node_types"]
    edges = json.loads((ONTOLOGY_DIR / "edge_types.json").read_text())["edge_types"]
    return nodes, edges


def _class_iri(node_type: str) -> str:
    return f"kg:{_pascal_case(node_type)}"


def _property_iri(relation: str) -> str:
    return f"kg:{_camel_case(relation)}"


def _types_to_class_list(types: list[str]) -> list[str]:
    return [_class_iri(t) for t in types if t != "*"]


def _emit_or_class(class_iris: list[str]) -> str:
    """SHACL ``sh:or`` (list of ``sh:class`` constraints) for type union."""
    if len(class_iris) == 1:
        return f"sh:class {class_iris[0]}"
    parts = [f"[ sh:class {c} ]" for c in class_iris]
    return "sh:or ( " + " ".join(parts) + " )"


def _ttl_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# ---------- invariants/edges.ttl --------------------------------------------


def _edge_shape(relation: str, definition: dict) -> str:
    # Dead relations (deprecated / reserved / reserved_inverse) should not
    # get Domain/Range shapes: they validate properties no new edge is
    # expected to use, so a "violation" here is noise, not a data bug.
    if definition.get("status") in INACTIVE_EDGE_STATUSES:
        return ""

    source_types = definition.get("source_types", []) or []
    target_types = definition.get("target_types", []) or []
    prop = _property_iri(relation)
    camel = _camel_case(relation)

    # "*" wildcard: no class constraint. Skip emitting the shape entirely —
    # nothing to enforce on either side.
    if "*" in source_types and "*" in target_types:
        return ""

    msg = _ttl_string(
        f"Edge `{relation}` violates source/target type constraints from edge_types.json"
    )

    blocks: list[str] = []

    if "*" not in target_types and target_types:
        tgt_classes = _types_to_class_list(target_types)
        target_constraint = _emit_or_class(tgt_classes)
        # Property shape gets a named IRI so violations resolve to it
        # instead of an opaque blank node.
        blocks.append(
            f"""kg:Shape_{camel}_Range a sh:NodeShape ;
    sh:targetSubjectsOf {prop} ;
    sh:property kg:Shape_{camel}_RangeProp .

kg:Shape_{camel}_RangeProp a sh:PropertyShape ;
    sh:path {prop} ;
    {target_constraint} ;
    sh:severity sh:Violation ;
    sh:message {msg} ."""
        )

    if "*" not in source_types and source_types:
        src_classes = _types_to_class_list(source_types)
        source_constraint = _emit_or_class(src_classes)
        blocks.append(
            f"""kg:Shape_{camel}_Domain a sh:NodeShape ;
    sh:targetSubjectsOf {prop} ;
    {source_constraint} ;
    sh:severity sh:Violation ;
    sh:message {msg} ."""
        )

    return "\n\n".join(blocks)


def generate_edges_ttl(edges_ontology: dict) -> str:
    chunks: list[str] = [HEADER]
    chunks.append("# --- Edge type constraints (source/target class) ---\n")
    for relation, definition in sorted(edges_ontology.items()):
        shape = _edge_shape(relation, definition)
        if shape:
            chunks.append(shape)
            chunks.append("")
    return "\n".join(chunks)


# ---------- quality/id_prefix.ttl -------------------------------------------


def _node_prefix_shape(node_type: str) -> str:
    """Emit a SHACL warning for a node whose ID prefix swaps to another type.

    The shape mirrors the Python audit semantics (``audit_kg_quality.py``):
    only flag a node when its ID starts with *another* recognized
    canonical-type prefix. IDs that use an unknown or domain-specific
    prefix (``pub_``, ``scholar_``, ``council_``, ``sc123_``) are not
    flagged, since they are valid project conventions that do not
    conflict with any other type's namespace.
    """
    prefix = PREFIX_TO_TYPE_PREFIX.get(node_type)
    if not prefix:
        return ""
    # All other canonical type prefixes — used to detect *swaps*.
    other_prefixes = sorted(
        p for nt, p in PREFIX_TO_TYPE_PREFIX.items() if nt != node_type
    )
    if not other_prefixes:
        return ""
    # SPARQL ``||`` chain checking each foreign prefix.
    foreign_filters = " || ".join(
        f'STRSTARTS( ?localName, "{p}_" )' for p in other_prefixes
    )
    msg = _ttl_string(
        f"Node ID for type `{node_type}` uses a different canonical "
        f"type prefix (expected `{prefix}_` or a project convention)"
    )
    return f"""kg:Shape_{_pascal_case(node_type)}_IdPrefix a sh:NodeShape ;
    sh:targetClass {_class_iri(node_type)} ;
    sh:severity sh:Warning ;
    sh:sparql [
        sh:message {msg} ;
        sh:select \"\"\"
            PREFIX kg: <https://free-will.app/ontology/>
            PREFIX res: <https://free-will.app/kg/>
            SELECT $this WHERE {{
              $this a {_class_iri(node_type)} .
              BIND( STRAFTER(STR($this), STR(res:)) AS ?localName )
              FILTER ( STRSTARTS( STR($this), STR(res:) ) )
              FILTER ( ! STRSTARTS( ?localName, \"{prefix}_\" ) )
              FILTER ( {foreign_filters} )
            }}
        \"\"\" ;
    ] ."""


def generate_id_prefix_ttl(nodes_ontology: dict) -> str:
    chunks: list[str] = [HEADER]
    chunks.append("# --- Node ID prefix conventions (warning severity) ---\n")
    for node_type in sorted(nodes_ontology.keys()):
        shape = _node_prefix_shape(node_type)
        if shape:
            chunks.append(shape)
            chunks.append("")
    return "\n".join(chunks)


# ---------- quality/claims.ttl ----------------------------------------------


def generate_claims_ttl() -> str:
    chunks: list[str] = [HEADER]
    chunks.append("# --- Claim-bearing nodes should be anchored to evidence ---\n")

    evidence_props = " | ".join(_property_iri(r) for r in sorted(EVIDENCE_RELATIONS))

    for claim_type in sorted(CLAIM_TYPES):
        cls = _class_iri(claim_type)
        msg = _ttl_string(
            f"Claim-bearing `{claim_type}` node lacks any evidence anchor "
            f"({', '.join(sorted(EVIDENCE_RELATIONS))})"
        )
        # SHACL alternative property paths can express "at least one of
        # several edges", but pyshacl's minCount on a UNION path can be
        # finicky for our scale — SPARQL is the more reliable form here.
        chunks.append(
            f"""kg:Shape_{_pascal_case(claim_type)}_NeedsEvidence a sh:NodeShape ;
    sh:targetClass {cls} ;
    sh:severity sh:Warning ;
    sh:sparql [
        sh:message {msg} ;
        sh:select \"\"\"
            PREFIX kg: <https://free-will.app/ontology/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT $this WHERE {{
              $this a {cls} .
              FILTER NOT EXISTS {{ $this ( {evidence_props} ) ?anchor }}
              FILTER NOT EXISTS {{ ?anchor ( {evidence_props} ) $this }}
              FILTER NOT EXISTS {{ $this kg:needsEvidence true }}
              FILTER NOT EXISTS {{ $this kg:needsEvidence \\\"true\\\"^^xsd:boolean }}
            }}
        \"\"\" ;
    ] ."""
        )
        chunks.append("")

    return "\n".join(chunks)


# ---------- quality/formatting.ttl ------------------------------------------


def generate_formatting_ttl(nodes_ontology: dict) -> str:
    chunks: list[str] = [HEADER]

    period_options = " ".join(_ttl_string(p) for p in sorted(CANONICAL_PERIODS))
    chunks.append("# --- Periods restricted to canonical list (non-passage) ---\n")

    non_passage_types = [t for t in sorted(nodes_ontology.keys()) if t != "passage"]
    for node_type in non_passage_types:
        cls = _class_iri(node_type)
        pascal = _pascal_case(node_type)
        msg = _ttl_string(
            f"Node period for `{node_type}` must be one of the canonical periods"
        )
        # Named PropertyShape so sourceShape resolves to a named IRI.
        chunks.append(
            f"""kg:Shape_{pascal}_Period a sh:NodeShape ;
    sh:targetClass {cls} ;
    sh:property kg:Shape_{pascal}_PeriodProp .

kg:Shape_{pascal}_PeriodProp a sh:PropertyShape ;
    sh:path kg:period ;
    sh:in ( {period_options} ) ;
    sh:severity sh:Warning ;
    sh:message {msg} ."""
        )
        chunks.append("")

    school_options = " ".join(_ttl_string(s) for s in sorted(CANONICAL_SCHOOLS))
    chunks.append("# --- Schools restricted to school_scheme.json ---\n")
    for node_type in sorted(nodes_ontology.keys()):
        cls = _class_iri(node_type)
        pascal = _pascal_case(node_type)
        msg = _ttl_string(
            f"Node school for `{node_type}` must belong to school_scheme.json"
        )
        chunks.append(
            f"""kg:Shape_{pascal}_School a sh:NodeShape ;
    sh:targetClass {cls} ;
    sh:property kg:Shape_{pascal}_SchoolProp .

kg:Shape_{pascal}_SchoolProp a sh:PropertyShape ;
    sh:path kg:school ;
    sh:in ( {school_options} ) ;
    sh:severity sh:Warning ;
    sh:message {msg} ."""
        )
        chunks.append("")

    chunks.append("# --- Description hygiene: no markdown artefacts ---\n")
    # XSD-regex (used by SHACL sh:pattern) does not support negative
    # lookahead. We express "no markdown" as a disjunction of positive
    # patterns wrapped in sh:not, which is semantically equivalent and
    # actually evaluable by pyshacl.
    hygiene_patterns: list[tuple[str, str]] = [
        ("BoldStars", r"\\*\\*"),
        ("BoldUnderscore", r"__"),
        ("MarkdownLink", r"\\[[^\\]]+\\]\\([^)]+\\)"),
        ("ListBullet", r"(^|\\n)\\s*[-*]\\s"),
        ("HeadingHash", r"(^|\\n)\\s*#+\\s"),
    ]
    for node_type in non_passage_types:
        cls = _class_iri(node_type)
        pascal = _pascal_case(node_type)
        msg = _ttl_string(
            f"Description on `{node_type}` contains markdown formatting "
            "(bold, list bullets, headings, or [text](url))"
        )
        not_blocks: list[str] = []
        for _variant, pat in hygiene_patterns:
            not_blocks.append(f'        sh:not [ sh:pattern "{pat}" ; sh:flags "s" ] ;')
        not_joined = "\n".join(not_blocks)
        chunks.append(
            f"""kg:Shape_{pascal}_DescriptionHygiene a sh:NodeShape ;
    sh:targetClass {cls} ;
    sh:property kg:Shape_{pascal}_DescriptionHygieneProp .

kg:Shape_{pascal}_DescriptionHygieneProp a sh:PropertyShape ;
    sh:path dcterms:description ;
{not_joined}
        sh:severity sh:Warning ;
        sh:message {msg} ."""
        )
        chunks.append("")

    return "\n".join(chunks)


# ---------- quality/philology.ttl ------------------------------------------


def generate_philology_ttl() -> str:
    chunks: list[str] = [HEADER]
    chunks.append("# --- Philological publication metadata (warning severity) ---\n")

    role_options = " ".join(_ttl_string(role) for role in PASSAGE_ROLES)
    chunks.append(
        f"""kg:Shape_Passage_PassageRole a sh:NodeShape ;
    sh:targetClass kg:Passage ;
    sh:property kg:Shape_Passage_PassageRoleProp .

kg:Shape_Passage_PassageRoleProp a sh:PropertyShape ;
    sh:path kg:passageRole ;
    sh:minCount 1 ;
    sh:in ( {role_options} ) ;
    sh:severity sh:Warning ;
    sh:message "Passage nodes should declare metadata.passage_role as original, translation, or paraphrase" ."""
    )
    chunks.append("")

    chunks.append(
        """kg:Shape_TextualVariant_RequiredFields a sh:NodeShape ;
    sh:targetClass kg:TextualVariant ;
    sh:property kg:Shape_TextualVariant_LemmaProp ;
    sh:property kg:Shape_TextualVariant_PrincipalReadingProp ;
    sh:property kg:Shape_TextualVariant_AlternativesProp .

kg:Shape_TextualVariant_LemmaProp a sh:PropertyShape ;
    sh:path kg:lemma ;
    sh:minCount 1 ;
    sh:severity sh:Warning ;
    sh:message "Textual-variant nodes should carry metadata.lemma" .

kg:Shape_TextualVariant_PrincipalReadingProp a sh:PropertyShape ;
    sh:path kg:lectionPrincipale ;
    sh:minCount 1 ;
    sh:severity sh:Warning ;
    sh:message "Textual-variant nodes should carry metadata.lection_principale" .

kg:Shape_TextualVariant_AlternativesProp a sh:PropertyShape ;
    sh:path kg:lectionsAlternatives ;
    sh:minCount 1 ;
    sh:severity sh:Warning ;
    sh:message "Textual-variant nodes should carry metadata.lections_alternatives" ."""
    )
    chunks.append("")

    chunks.append(
        """kg:Shape_ArgumentReconstruction_Fidelity a sh:NodeShape ;
    sh:targetClass kg:ArgumentReconstruction ;
    sh:property kg:Shape_ArgumentReconstruction_FidelityProp .

kg:Shape_ArgumentReconstruction_FidelityProp a sh:PropertyShape ;
    sh:path kg:fidelityScore ;
    sh:minCount 1 ;
    sh:minInclusive 0 ;
    sh:maxInclusive 1 ;
    sh:severity sh:Warning ;
    sh:message "Argument-reconstruction nodes should carry metadata.fidelity_score in [0, 1]" ."""
    )
    chunks.append("")

    chunks.append(
        """kg:Shape_Publication_BibtexMinimum a sh:NodeShape ;
    sh:targetClass kg:Publication ;
    sh:property kg:Shape_Publication_BibtexKeyProp .

kg:Shape_Publication_BibtexKeyProp a sh:PropertyShape ;
    sh:path kg:bibtexKey ;
    sh:minCount 1 ;
    sh:severity sh:Warning ;
    sh:message "Publication nodes should carry metadata.bibtex_key or metadata.zotero_key for stable BibTeX export" ."""
    )
    chunks.append("")

    return "\n".join(chunks)


# ---------- entrypoint ------------------------------------------------------


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    nodes_ontology, edges_ontology = _load_ontology()
    INVARIANTS_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    # Invariants — must produce zero violations on the prod KG.
    written.append(
        _write(INVARIANTS_DIR / "edges.ttl", generate_edges_ttl(edges_ontology))
    )

    # Quality goals — drive the triage backlog. Severity Warning.
    written.append(
        _write(QUALITY_DIR / "id_prefix.ttl", generate_id_prefix_ttl(nodes_ontology))
    )
    written.append(_write(QUALITY_DIR / "claims.ttl", generate_claims_ttl()))
    written.append(
        _write(QUALITY_DIR / "formatting.ttl", generate_formatting_ttl(nodes_ontology))
    )
    written.append(_write(QUALITY_DIR / "philology.ttl", generate_philology_ttl()))

    # Remove the legacy flat-file shapes if they linger, so the loader
    # never picks up a stale union by accident.
    for legacy in (
        SHAPES_DIR / "core.ttl",
        SHAPES_DIR / "claims.ttl",
        SHAPES_DIR / "formatting.ttl",
    ):
        if legacy.exists():
            legacy.unlink()

    for p in written:
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
