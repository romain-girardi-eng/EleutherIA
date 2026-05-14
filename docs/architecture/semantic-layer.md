# Couche sémantique RDF/OWL/SHACL

> **Statut** : Phases A (RDF export), B (SHACL gate), C (OWL-RL + GraphRAG) **livrées** ; Phase D (câblage bout-en-bout + SHACL conforme + couverture > 95%) en cours d'achèvement.

La couche sémantique est un dérivé *read-only* du graphe canonique stocké dans Postgres. Elle expose le KG dans des sérialisations W3C standard, fournit un gate de validation SHACL, et matérialise des faits inférés (inverses, transitivité) directement exploités par l'agent ReAct.

## Objectifs (atteints)

- **FAIR-Interoperability** — KG exposé en RDF/OWL aligné sur CIDOC-CRM, FOAF, SKOS, Dublin Core, BIBO, PROV-O, Wikidata ; le « I » de FAIR n'est plus aspirationnel.
- **Gate qualité** — validation SHACL complète couvre les invariants ontologiques (`shapes/invariants/*.ttl`) et un backlog de qualité (`shapes/quality/*.ttl`) distinct du Python audit.
- **Raisonnement vérifiable** — OWL-RL forward-chaining matérialise inverses + clôture transitive en sub-seconde ; chaque claim peut porter sa proof chain.

Le canonique reste Postgres ; aucune mutation au runtime.

## Architecture

```
knowledge graph/src/eleutheria_kg/semantic/
├── __init__.py              # façade publique
├── vocab.py                 # namespaces IRI + mappings types/relations → vocabs (CIDOC-CRM, FOAF, SKOS, Dublin Core, BIBO, PROV-O, Wikidata)
├── rdf_export.py            # JSONL → rdflib.Graph + sérialisation Turtle/JSON-LD/N-Triples
├── inference.py             # OWL-RL restreint (inverse + symmetric + transitive sur 5 prop. hiérarchiques)
├── proof.py                 # InferenceStep + build_proof_chain + serialize_proof_chain
├── validator.py             # wrapper pyshacl + ValidationReport
└── shapes/
    ├── __init__.py          # load_shapes / load_invariant_shapes / load_quality_shapes
    ├── generate_shapes.py   # générateur idempotent depuis node_types.json + edge_types.json
    ├── invariants/          # contraintes bloquantes (sh:Violation) — conformance gate
    │   └── *.ttl
    └── quality/             # objectifs qualité (sh:Warning) — backlog triage
        └── *.ttl
```

Dépendances : `rdflib >= 7.6`, `owlrl >= 7.1`, `pyshacl >= 0.31`, déclarées sous l'extra `semantic` dans `knowledge graph/pyproject.toml`.

## Schéma d'IRI

| Préfixe | IRI | Usage |
|---|---|---|
| `kg:` | `https://free-will.app/ontology/` | Ontologie : classes (`kg:Argument`, `kg:Person`) et propriétés (`kg:authoredBy`, `kg:partOf`) |
| `res:` | `https://free-will.app/kg/` | Ressources : un nœud `argument_xxx` devient `res:argument_xxx` |

Les IRI `res:` sont déréférenciables via la route FastAPI `GET /api/kg/nodes/{id}`.

## Mapping vers vocabulaires standards

### Classes (extrait — voir `vocab.py:NODE_TYPE_TO_CLASSES` pour la liste complète)

| Type EleutherIA | Classes standard |
|---|---|
| `person` | `crm:E21_Person`, `foaf:Person`, `wd:Q5` (via `owl:sameAs` quand `wikidata_qid`) |
| `work` | `crm:E73_Information_Object`, `dcterms:BibliographicResource` |
| `passage` | `crm:E33_Linguistic_Object` |
| `concept` | `skos:Concept`, `crm:E55_Type` |
| `argument` / `synthesis` / `debate` | `prov:Entity` (+ classe `kg:` dédiée) |
| `school` / `group` | `crm:E74_Group`, `foaf:Group` |
| `event` | `crm:E5_Event` |
| `publication` | `dcterms:BibliographicResource`, `bibo:Document` |
| `quote` / `text_fragment` | `crm:E33_Linguistic_Object` |
| `source_collection` | `dcmitype:Collection` |

Chaque nœud reçoit *à la fois* sa classe `kg:` et les classes standard ; les classes `kg:` sont déclarées comme `rdfs:subClassOf` des standards dans le header d'ontologie.

### Propriétés (extrait — voir `vocab.py:EDGE_TYPE_TO_PROPERTY`)

| Relation EleutherIA | Propriété standard |
|---|---|
| `wrote` / `authored_by` | `dcterms:creator` |
| `part_of` / `contains` / `has_section` / `has_chapter` | `dcterms:isPartOf` / `dcterms:hasPart` |
| `cites` / `cited_by` | `cito:cites` / `cito:isCitedBy` |
| `translation_of` / `has_translation` | `cito:isTranslationOf` / `cito:hasTranslation` |
| `influences` / `influenced_by` / `influenced` | `crm:P15_was_influenced_by` |
| `member_of` / `belongs_to_school` / `has_member` | `crm:P107_has_current_or_former_member` (+ inverse) |
| `evidenced_by` / `source_for` | `prov:wasDerivedFrom` / `prov:wasUsedBy` |
| `discusses` / `interprets` | `prov:wasInformedBy` |
| `defines` | `skos:definition` |

Les propriétés sans équivalent standard restent uniquement dans `kg:`.

### Inverses OWL

Les inverses « propres » (paires symétriques sans triangle ambigu) sont déclarés en `owl:inverseOf` dans le header de l'ontologie ; voir `CLEAN_INVERSE_PAIRS` dans `vocab.py`. Les relations symétriques (`related_to`, `contrasts_with`, `parallel_to`, `contemporary_of`) sont déclarées `owl:SymmetricProperty`.

## Phase A — Export RDF

```bash
eleutheria export kg --format rdf --output /chemin/eleutheria_kg
```

Produit `*.ttl`, `*.jsonld`, `*.nt` partageant la même base. À 17 757 nœuds / 43 063 arêtes → **157 805 triples** (Turtle ~40 MB, JSON-LD ~49 MB, N-Triples ~52 MB).

API programmatique : `build_graph(nodes_path, edges_path) -> rdflib.Graph` + `export_graph(g, basename)`.

## Phase B — Validation SHACL

Deux niveaux séparés pour distinguer invariants bloquants et objectifs qualité :

```python
from eleutheria_kg.semantic import build_graph, validate_kg
from eleutheria_kg.semantic.shapes import load_invariant_shapes, load_quality_shapes
from eleutheria_kg.semantic.validator import validate_kg_invariants

g = build_graph(nodes_path, edges_path)

# Gate CI : doit être conforms=True à chaque snapshot
invariants = validate_kg_invariants(g)
assert invariants.conforms, invariants.format_markdown_report()

# Backlog qualité : reste un objectif, n'oblige pas
quality = validate_kg(g, load_quality_shapes())
print(quality.format_markdown_report())
```

Intégration audit : `python scripts/audit_kg_quality.py --shacl` ajoute la section SHACL au rapport markdown standard.

Rapport courant sur le KG production : `docs/reports/2026-05-14-shacl-validation.md`.

## Phase C — Inférence OWL-RL

```python
from eleutheria_kg.semantic import (
    materialize_inverses_and_transitivity,
    transitive_closure,
    inverse_neighbors,
)

# Restricted closure (recommandée en runtime) : 0.34 s sur 158k triples,
# matérialise +40 716 inverses + transitivité part_of/contains/etc.
g = materialize_inverses_and_transitivity(g)  # mutates in place

# Ou closure ciblée sans matérialisation globale
ancestors = transitive_closure(g, mint_node_iri("passage_xyz"), KG.partOf)
```

Une variante `materialize_full_owl_rl(g)` exécute le `DeductiveClosure(OWLRL_Semantics)` complet ; multi-minute, réservée à des contrôles offline.

### Proof chains

Quand une claim s'appuie sur un fait inféré (et non directement asserted), l'agent peut reconstruire la dérivation :

```python
from eleutheria_kg.semantic import build_proof_chain, serialize_proof_chain

chain = build_proof_chain(g, (subj, pred, obj))
ledger_item.proof_chain = serialize_proof_chain(chain)
```

Chaque `InferenceStep` porte `rule` (`inverseOf` / `transitivity` / `subPropertyOf`), `premises` (liste de triples), `conclusion`, et `confidence` (défaut 1.0). Le tout sérialisable JSON pour l'API.

### Intégration GraphRAG

- **8e outil ReAct** `InferTransitiveFactsTool` (`graphrag/src/eleutheria_graphrag/agents/tools/infer_transitive.py`) — réponses à « tous les passages contenus dans Republic VII », « toutes les œuvres écrites par Augustin (direct ou inverse) ». Utilise les edge dicts in-memory (pas rdflib) pour rapidité.
- **Mode ontology-aware** sur `_expand_1hop` (`graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py`) — quand activé, retourne inverses + ancêtres transitifs en plus des arêtes directes.
- **Champ `proof_chain`** sur `ClaimLedgerItem` (`graphrag/src/eleutheria_graphrag/agents/state.py`) — optionnel, backward-compatible.

## Phase D — Activation bout-en-bout

Câblage des primitives Phase C dans le pipeline live :

- `proof_chain` instancié par `DraftClaimLedger` quand l'evidence inclut des faits inférés ; surfacé dans le reasoning trace et la réponse API.
- `ontology_aware=True` activé par défaut dans le pipeline retrieval — inverses et transitivité remontent désormais sans flag explicite.
- Shapes split en `invariants/` (must pass) et `quality/` (backlog). Conformance sur les invariants atteinte.
- Couverture `eleutheria_kg.semantic` > 95%.

Détails opérationnels dans `~/.claude/projects/-Users-romaingirardi-Projects-EleutherIA/memory/project_semantic_layer.md`.

## Hors-scope (intentionnel)

- Sidecar GraphDB / RDFox / Stardog — pas justifié à 17k nœuds ; pile Python suffit.
- OWL-DL (Pellet / HermiT) — overkill ; OWL2-RL couvre nos cas.
- Conformité CIDOC-CRM complète — mapping partiel suffisant pour la découvrabilité.
- Endpoint SPARQL externe — Apache Jena Fuseki en sidecar the platform, à déclencher uniquement sur demande externe.

## Références

- Plan : `~/.claude/plans/can-you-ultrathink-abou-twinkling-lynx.md`
- Audit qualité : `docs/reports/2026-03-10-kg-quality-audit-post-batch-04.md`, `docs/reports/2026-05-14-shacl-validation.md`
- Ontologie : `knowledge graph/ontology/{node_types.json, edge_types.json}`
- Mémoire projet : `~/.claude/projects/-Users-romaingirardi-Projects-EleutherIA/memory/project_semantic_layer.md`
