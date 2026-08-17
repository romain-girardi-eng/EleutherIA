# Plan de normalisation des arêtes inverses — 17 août 2026

## Statut

Plan et outillage prêts, **non appliqués au graphe canonique**. Les seuls fichiers
de données modifiés pendant la vérification se trouvent dans
`/tmp/eleutheria-inverse-normalization.3Fe4Ku/`.

- `data/kg/edges.jsonl` reste à 53 643 lignes, SHA-256
  `de9fe38cb85d272492b0230c7ed2787288b859d4017b8169e8705743c7d8b1b3`.
- La sauvegarde de la copie sandbox a exactement le même SHA-256.
- `data/kg/nodes.jsonl` reste à 19 796 lignes, SHA-256
  `f5a565d90ebd668bb3601d462527b3967e76b1c70f4808868d118b7055564888`.
- Aucune écriture n’a été faite dans `data/kg/` ni dans `data/corpus/`.

Décision mise en œuvre par le plan : une seule direction est assertée dans le
JSONL ; la direction inverse est une vue dérivée au chargement ou à l’inférence.

## Étape 0 — preuve de code avant le plan de données

### Chargement et index centraux

| Consommateur | Preuve `fichier:ligne` | Sens observé avant correction | Conclusion / protection |
|---|---|---|---|
| Snapshot KG | `knowledge graph/src/eleutheria_kg/services/snapshot.py:73`, `:91`, `:96` | Le chargeur normalisait uniquement les arêtes assertées. | Sensible. `materialize_inverse_edges` (`:134`) construit maintenant une vue inverse dédupliquée en une seule étape, sans réécrire le JSONL. |
| Chargement DB du backend | `backend/dependencies.py:119-156` | Le `SELECT` ramenait seulement `source_id -> target_id`. | Sensible. Les résultats DB passent par `materialize_inverse_edges` à `:156`. |
| Chargement GraphRAG | `graphrag/src/eleutheria_graphrag/services/graphrag_service.py:242-276`, `:401-441` | Deux index séparés `outgoing_edges` et `incoming_edges`; les consommateurs exacts restaient dépendants de la relation assertée. | Sensible. `_normalize_kg_data` retourne la vue inverse à `:441`, y compris quand GraphRAG est instancié directement sur la DB. |
| Chargement MCP | `mcp_server/deps.py:21-53`, `:93-129` | Index source et cible séparés, DB brute. | Sensible. La vue inverse est dérivée à `:129` avant la construction des index. |

La vue dérivée conserve d’abord toutes les arêtes assertées, n’ajoute pas une
triple déjà présente, marque chaque ajout `derived=true`,
`inference_rule=inverse`, et conserve `derived_from_edge_id` ou
`derived_from_triple`. Une seule application de la déclaration est faite : les
déclarations historiques qui se chevauchent (`has_section -> part_of` puis
`part_of -> contains`) ne sont pas transformées en fermeture d’équivalence
involontaire.

### Services KG, CTE SQL et endpoints

| Consommateur | Preuve `fichier:ligne` | Verdict directionnel |
|---|---|---|
| Graphe NetworkX de voisinage | `knowledge graph/src/eleutheria_kg/services/analytics.py:129-156`, `:419-470` | Bidirectionnel : `nx.Graph`, puis `graph.neighbors`. Aucun voisin topologique perdu. |
| PageRank / eigenvector | `knowledge graph/src/eleutheria_kg/services/analytics.py:158-189`, `:371-379` | **Orienté** : `nx.DiGraph` suit uniquement source → cible. Protégé par la vue inverse au chargement. |
| Communautés sémantiques | `knowledge graph/src/eleutheria_kg/services/analytics.py:328-340` | Bidirectionnel explicite : chaque arête est indexée aux deux extrémités. |
| CTE récursif Postgres | `knowledge graph/src/eleutheria_kg/services/db_traversal.py:45-71` | **Bidirectionnel prouvé** : branche `e.source_id = khop.node_id`, puis `UNION ALL` avec `e.target_id = khop.node_id` (`:54-61`). |
| Retour du CTE | `knowledge graph/src/eleutheria_kg/services/db_traversal.py:101-145` | La topologie est sûre ; la relation/direction restait brute. `derive_inverses=True` ajoute la vue pour les appels sémantiques (`:143-144`). |
| Endpoint `/nodes/{id}/neighbors` | `knowledge graph/src/eleutheria_kg/api/routes.py:112-166`, `:169-208` | Le groupement distingue relation sortante et entrante, donc sensible. Le fallback DB demande désormais `derive_inverses=True` à `:141-143`. |
| Endpoint `/edges` | `knowledge graph/src/eleutheria_kg/api/routes.py:212-232` | Filtres exacts `relation`, `source`, `target`, donc orienté. Il lit la vue chargée. |
| Chemin le plus court | `knowledge graph/src/eleutheria_kg/services/analytics.py:396-417` | Non orienté (`_build_graph`). |
| Cytoscape / Cosmograph | `backend/routes/kg_extras.py:196-249` | Rend source et cible telles que chargées ; sensible pour l’affichage, protégé par la vue. |
| Matrice d’influence | `backend/routes/kg_extras.py:345-370` | Filtre la relation mais inscrit les deux extrémités dans la matrice ; la vue garantit les noms inverses. |
| Débats, chaînes, relations frontend | `backend/routes/graphrag_extras.py:400-486` | Comptage des deux extrémités pour les débats ; chaînes orientées et listes incoming/outgoing pour les autres. La vue chargée protège ces deux derniers cas. |
| Client doctoral | `frontend/src/services/doctoralApi.ts:122-160`, `:220-226` | Ne lit pas le JSONL ; il aplatit les groupes `outgoing` et `incoming` de l’API. La correction est donc côté backend. |

### Accès SQL directs qui ne passent pas par les chargeurs

Deux accès étaient réellement vulnérables au choix canonique `wrote` :

- l’auteur d’un ouvrage dans `backend/routes/passages.py:121-138` interrogeait
  seulement `work -[authored_by]-> person`. La requête unit maintenant ce cas
  historique avec `person -[wrote]-> work` (`:131-136`) ;
- le tagueur de sujets dans `backend/services/topic_tagger.py:149-171` fait la
  même union `authored_by UNION wrote` (`:161-169`).

L’accès aux traductions de
`database/src/eleutheria_database/api/works.py:164-182` est orienté et filtre
`translation_of`, mais cette relation est précisément le membre canonique de sa
paire : il ne se dégrade pas après normalisation. Le fichier de migration
historique `backend/alembic/versions/002_add_materialized_views.py:124-199`
contient des vues orientées, mais n’est pas un chemin de lecture runtime et ses
relations historiques (`influenced`, `taught`, etc.) ne correspondent pas aux
paires supprimées ici.

### GraphRAG et outils KG

| Chemin | Preuve `fichier:ligne` | Verdict directionnel |
|---|---|---|
| Traversée pondérée | `graphrag/src/eleutheria_graphrag/services/weighted_traversal.py:128-217` | Développe explicitement les sortantes (`:180-195`) puis les entrantes (`:196-210`) : topologie bidirectionnelle. Les filtres de relation restent sensibles, donc vue requise. |
| Stratégie de retrieval 1-hop | `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py:332-417` | Parcourt les deux index et enregistre déjà les inverses OWL propres (`:388-415`). Sûr topologiquement ; la vue étend la couverture aux déclarations non présentes dans `CLEAN_INVERSE_PAIRS`. |
| Passages liés | `graphrag/src/eleutheria_graphrag/services/retrieval_strategy.py:622-638`, `services/snapshot_retrieval.py:128-162` | Deux sens explicites. |
| Résolution `part_of` / `authored_by` | `graphrag/src/eleutheria_graphrag/services/snapshot_retrieval.py:81-109`, `:286-297` | `_first_neighbor_id` suit seulement les sortantes et filtre une relation exacte : **sensible**, protégé par la vue. |
| Traductions snapshot | `graphrag/src/eleutheria_graphrag/services/snapshot_retrieval.py:216-244` | Cherche `translation_of` dans les deux index. |
| Boucle ReAct | `graphrag/src/eleutheria_graphrag/agents/react_loop.py:302-314`, `:755-841`, `:1410-1435` | `_neighbor_ids` est bidirectionnel ; le reste consomme les résultats des outils, sans lecture parallèle du JSONL. |
| `get_neighbors` | `graphrag/src/eleutheria_graphrag/agents/tools/get_neighbors.py:87-207`, `:217-254` | Filtres exacts relation + direction, donc **sensible**. Les index et le fallback CTE ont la vue inverse ; sans filtre, l’original et son inverse dérivé sont dédupliqués comme une connexion logique. |
| `explore_subgraph` PPR | `graphrag/src/eleutheria_graphrag/agents/tools/explore_subgraph.py:145-230` | Le PPR distribue le score uniquement sur l’adjacence sortante : **orienté** et protégé par la vue. |
| `explore_subgraph` distance | `graphrag/src/eleutheria_graphrag/agents/tools/explore_subgraph.py:232-255`, `:337-358` | BFS explicitement bidirectionnel. |
| `infer_transitive` | `graphrag/src/eleutheria_graphrag/agents/tools/infer_transitive.py:205-397` | Utilise relation sortante, inverse sortante, relation entrante et inverse entrante (`:261-377`) : bidirectionnel et conscient de l’ontologie. |
| `find_debates` | `graphrag/src/eleutheria_graphrag/agents/tools/find_debates.py:218-267` | Mélange les deux index, mais avec ensembles de relations exacts : vue nécessaire. |
| `build_controversy_frame` | `graphrag/src/eleutheria_graphrag/agents/tools/build_controversy_frame.py:313-387`, `:479-518`, `:564-585`, `:675-725` | La plupart des recherches consultent les deux sens ; quelques résolutions (`authored_by`, publication, ancrage) sont relation-sensibles. Vue nécessaire. |
| `read_passages` | `graphrag/src/eleutheria_graphrag/agents/tools/read_passages.py:195-219`, `:326-347` | Cherche auteurs et traductions avec relations/directions précises. Vue nécessaire. |
| `get_node_detail` | `graphrag/src/eleutheria_graphrag/agents/tools/get_node_detail.py:69-101` | Compte séparément les index entrants et sortants ; protégé par la vue. |
| Fallbacks du graphe agentique | `graphrag/src/eleutheria_graphrag/agents/graph_nodes.py:200-244`, `:2572-2598`, `:2797-2850`, `:2916-2992` | Le BFS et les traductions utilisent les deux sens ; la preuve RDF ciblée et certaines relations sont orientées. Vue nécessaire. |
| Sous-graphe de réponse | `graphrag/src/eleutheria_graphrag/agents/answer_subgraph.py:228-248`, `:413-425` | Joint uniquement les sortantes : **orienté**, protégé par la vue. |
| Arêtes du chemin de raisonnement | `graphrag/src/eleutheria_graphrag/api/routes.py:54-90`, `:740-760` | Parcourt seulement `outgoing_edges` : **orienté**, protégé par la vue. |
| Chasseur de contre-preuves | `graphrag/src/eleutheria_graphrag/services/counter_evidence_hunter.py:408-425`, `:467-483`, `:565-580` | Délègue à `explore_subgraph` et `get_neighbors`; pas de troisième lecteur d’arêtes. |
| Façade MCP | `mcp_server/tools/kg.py:51-120` | Délègue aux mêmes outils ; les index MCP sont corrigés avant appel. |

### Export RDF et inférence

- `knowledge graph/src/eleutheria_kg/semantic/vocab.py:201-246` déclare les
  paires OWL non ambiguës dans `CLEAN_INVERSE_PAIRS` et quatre propriétés
  symétriques.
- `knowledge graph/src/eleutheria_kg/semantic/rdf_export.py:62-113` émet les
  axiomes `owl:inverseOf` et `owl:SymmetricProperty`.
- `knowledge graph/src/eleutheria_kg/semantic/inference.py:105-124` matérialise
  les deux sens des paires propres ; `:127-139` matérialise les symétriques ;
  `:299-310` permet aussi une lecture inverse sans matérialisation.
- L’export des triples assertés était toutefois direct à
  `rdf_export.py:489-517` et les paires qui se chevauchent dans l’ontologie
  (`has_section/part_of`, `has_chapter/part_of`) sont volontairement exclues de
  `CLEAN_INVERSE_PAIRS`. Après normalisation, cette limitation aurait supprimé
  leur sens inverse dans l’export. Le correctif fait maintenant passer les
  arêtes exportées par `materialize_inverse_edges` à
  `rdf_export.py:504-516`, tout en conservant les axiomes OWL propres.

Conclusion de l’étape 0 : le CTE et la majorité des BFS ne perdent aucun voisin,
mais PageRank/PPR, les filtres relation-direction, des résolutions spécialisées,
le sous-graphe de réponse, deux requêtes SQL d’auteur et l’export RDF sont
direction-sensibles. La normalisation de données ne doit donc être appliquée
qu’avec la vue inverse de chargement et les unions SQL présentes dans ce plan.

## Étape 1 — politique canonique

Ordre de décision :

1. une relation `active` ou `reserved` gagne sur `reserved_inverse`, qui gagne
   sur `deprecated` ;
2. à rang égal, si un seul membre déclare l’autre comme inverse, ce membre est
   primaire ;
3. si la déclaration est réciproque, le premier membre dans l’ordre de
   `edge_types.json` est primaire ;
4. pour une relation auto-inverse, le nom ne change pas et l’arête conservée a
   `source < target` lexicalement.

Cette politique est implémentée dans
`scripts/data_2026_08_17_inverse_normalization.py:89-192`.

| Relation | Inverse déclaré | Canonique | Motif |
|---|---|---|---|
| `argues_for` | `supported_by` | `argues_for` | membre déclarant seul l’inverse |
| `argues_against` | `opposed_by` | `argues_against` | membre déclarant seul l’inverse |
| `refutes` | `refuted_by` | `refutes` | membre déclarant seul l’inverse |
| `responds_to` | `has_response` | `responds_to` | membre déclarant seul l’inverse |
| `influences` | `influenced_by` | `influences` | ordre primaire de `edge_types.json` |
| `influenced` | `influenced_by` | `influenced_by` | membre non inverse/non déprécié |
| `taught_by` | `teaches` | `taught_by` | ordre primaire de `edge_types.json` |
| `student_of` | `teaches` | `student_of` | membre non inverse/non déprécié |
| `belongs_to_school` | `has_member` | `has_member` | membre non inverse/non déprécié |
| `has_member` | `member_of` | `member_of` | membre non inverse/non déprécié |
| `founded` | `founded_by` | `founded` | membre déclarant seul l’inverse |
| `wrote` | `authored_by` | `wrote` | ordre primaire de `edge_types.json` |
| `created_by` | `creates` | `created_by` | ordre primaire de `edge_types.json` |
| `developed_by` | `develops` | `developed_by` | membre déclarant seul l’inverse |
| `cites` | `cited_by` | `cites` | membre non inverse/non déprécié |
| `source_for` | `evidenced_by` | `source_for` | ordre primaire de `edge_types.json` |
| `attested_by` | `attests` | `attested_by` | ordre primaire de `edge_types.json` |
| `preserves` | `preserved_in` | `preserves` | ordre primaire de `edge_types.json` |
| `contains` | `part_of` | `contains` | ordre primaire de `edge_types.json` |
| `translation_of` | `has_translation` | `translation_of` | ordre primaire de `edge_types.json` |
| `has_section` | `part_of` | `has_section` | membre déclarant seul l’inverse |
| `has_chapter` | `part_of` | `has_chapter` | membre déclarant seul l’inverse |
| `belongs_to_corpus` | `contains` | `belongs_to_corpus` | membre déclarant seul l’inverse |
| `discusses` | `discussed_in` | `discusses` | ordre primaire de `edge_types.json` |
| `defines` | `defined_by` | `defines` | membre déclarant seul l’inverse |
| `related_to` | `related_to` | `related_to; source < target` | symétrique |
| `contrasts_with` | `contrasts_with` | `contrasts_with; source < target` | symétrique |
| `parallel_to` | `parallel_to` | `parallel_to; source < target` | symétrique |
| `same_thesis_as` | `same_thesis_as` | `same_thesis_as; source < target` | symétrique |
| `employs` | `employed_by` | `employs` | membre déclarant seul l’inverse |
| `presupposes` | `presupposed_by` | `presupposes` | membre déclarant seul l’inverse |
| `grounded_in` | `grounds` | `grounded_in` | membre déclarant seul l’inverse |
| `holds_position` | `held_by` | `holds_position` | membre déclarant seul l’inverse |
| `endorses` | `endorsed_by` | `endorses` | membre déclarant seul l’inverse |
| `rejects` | `rejected_by` | `rejects` | membre déclarant seul l’inverse |
| `supports` | `supported_by` | `supports` | membre déclarant seul l’inverse |
| `critiques` | `critiqued_by` | `critiques` | membre déclarant seul l’inverse |
| `extends` | `extended_by` | `extends` | membre déclarant seul l’inverse |
| `participates_in` | `has_participant` | `participates_in` | membre déclarant seul l’inverse |
| `contributes_to` | `contributed_to_by` | `contributes_to` | membre déclarant seul l’inverse |
| `interprets` | `interpreted_by` | `interprets` | membre non inverse/non déprécié |
| `represents` | `represented_by` | `represents` | membre déclarant seul l’inverse |
| `exemplifies` | `exemplified_by` | `exemplifies` | membre déclarant seul l’inverse |
| `specializes_in` | `specialist` | `specializes_in` | membre déclarant seul l’inverse |
| `contemporary_of` | `contemporary_of` | `contemporary_of; source < target` | symétrique |
| `precedes` | `follows` | `precedes` | ordre primaire de `edge_types.json` |
| `wrote_about` | `written_about_by` | `wrote_about` | membre déclarant seul l’inverse |
| `engages_with` | `engages_with` | `engages_with; source < target` | symétrique |
| `cites_primary_source` | `primary_source_cited_by` | `cites_primary_source` | membre déclarant seul l’inverse |
| `published` | `published_by` | `published` | membre déclarant seul l’inverse |
| `agrees_with` | `agreed_with_by` | `agrees_with` | membre déclarant seul l’inverse |
| `opposes` | `opposed_by` | `opposes` | membre déclarant seul l’inverse |
| `uses_methodology_of` | `methodology_used_by` | `uses_methodology_of` | membre déclarant seul l’inverse |
| `edited_by` | `edited` | `edited_by` | membre déclarant seul l’inverse |
| `variant_of` | `has_variant` | `variant_of` | ordre primaire de `edge_types.json` |
| `reconstructs` | `reconstructed_by` | `reconstructs` | ordre primaire de `edge_types.json` |
| `reconstructed_from` | `source_for_reconstruction` | `reconstructed_from` | ordre primaire de `edge_types.json` |
| `has_position` | `position_in_debate` | `has_position` | ordre primaire de `edge_types.json` |
| `advanced_in` | `advances` | `advanced_in` | membre déclarant seul l’inverse |

## Étape 2 — plan de normalisation

Le plan est construit à
`scripts/data_2026_08_17_inverse_normalization.py:202-305`. Une paire n’est
retenue que si les deux triples inverses existent réellement. Les arêtes sans
jumeau matériel sont laissées strictement intactes.

### Comptes

| Relation conservée | Relation supprimée | Paires | Survivants recevant au moins un champ manquant |
|---|---|---:|---:|
| `created_by` | `creates` | 19 | 19 |
| `engages_with` | `engages_with` | 4 | 2 |
| `has_chapter` | `part_of` | 788 | 788 |
| `has_section` | `part_of` | 1 236 | 1 236 |
| `influences` | `influenced_by` | 3 | 2 |
| `source_for` | `evidenced_by` | 2 | 1 |
| `translation_of` | `has_translation` | 2 612 | 2 564 |
| `wrote` | `authored_by` | 28 | 3 |
| **Total** |  | **4 692** | **4 615** |

Effet prévu : **53 643 → 48 951 arêtes assertées**. Les 4 692 paires sont
disjointes : aucune arête ne participe à deux suppressions. Il n’existe aucune
triple dupliquée avant traitement.

### Fusion de métadonnées

La fusion est effectuée à
`scripts/apply_2026_08_17_inverse_normalization.py:51-130` :

- un champ absent ou vide sur le survivant est copié depuis le jumeau ;
- `attested_by`, `note`, `notes` et `provenance` sont unifiés sans doublon ;
- les dictionnaires sont fusionnés récursivement et les listes par union stable ;
- une valeur scalaire contradictoire ne remplace jamais la valeur canonique :
  la valeur du jumeau est archivée dans le stamp ;
- le stamp `inverse_normalization_2026_08_17` porte l’identifiant et la relation
  du jumeau supprimé, les clés fusionnées et les éventuels conflits.

Dans l’état actuel, 9 771 chemins de métadonnées seraient fusionnés et huit
conflits scalaires seraient archivés. Aucune paire concernée ne porte actuellement
`attested_by`, mais l’invariant porte sur tout le graphe : l’union contient 122
valeurs distinctes avant et 122 après.

### Dix exemples de fusion

| # | Survivant | Jumeau supprimé | Champs récupérés |
|---:|---|---|---|
| 1 | `175bc8d7-1da6-4630-8f88-8920e7ae76f0` `argument_anselms_necessity_of_the_past_f7947dab -[created_by]-> person_anselm_of_canterbury_4e07b080` | `be01b742-ae6f-4b6a-8ad4-da21f0a32778` (`creates`) | `repair`, `repair_reason` |
| 2 | `dad2c7e9-9611-4246-9805-da83d4e1bab3` `person_bobzien_susanne_contemporary -[engages_with]-> scholar_sharples_robert` | `b6c8c933-81ad-4ffc-af34-115cb7929b4c` (`engages_with`) | `description`, `source_track` |
| 3 | `14b5d5e3-227f-4ec2-aa33-703e97a61126` `sc10bis_ignatius_ad_ephesios -[has_chapter]-> sc10bis_ignatius_ad_ephesios_chap1` | `e289b2c4-001d-44f7-a3cc-6d9e8a24bbe1` (`part_of`) | `auto_generated` |
| 4 | `687544a2-211f-47df-a60f-5efc354a3eb4` `sc464_pamphilus_apologia_pro_origene -[has_section]-> sc464_pamphilus_apologia_pro_origene_par1` | `6cf71193-4d0d-42bc-8437-e881c16bf059` (`part_of`) | `auto_generated` |
| 5 | `fd2cdba4-eacf-4ccc-812f-8b0f99d52b4d` `person_justin_martyr_2c_ce -[influences]-> person_irenaeus_d202` | `d456226f-e7de-4937-b3d3-f30d6cee212b` (`influenced_by`) | `confidence` |
| 6 | `357c5020-5c7d-4fcf-9050-203ddf064081` `passage_clement_strom_1_17_83 -[source_for]-> argument_clement_alex_strom_1_83_5_praise_blame` | `1a366ef3-40a4-47b0-948a-c82123e7ee44` (`evidenced_by`) | `anchor_source`, `anchor_via`, `created_by` |
| 7 | `359b93ac-1ff1-4c51-8a6b-b344bf1a5e2f` `passage_alex_fat_10_en -[translation_of]-> passage_alex_fat_10` | `28b0c4f2-e8a2-4784-94f3-7f12cb94abda` (`has_translation`) | `created_by`, `inverse_of_relation`, `repair_scope` |
| 8 | `add7641c-fee4-48ee-933d-f8258f3c7029` `person_justin_martyr_2c_ce -[wrote]-> sc507_iustinus_apologia_i` | `d1acc86d-c50f-464e-835a-4e96085dcadf` (`authored_by`) | `repair_reason`, `repair_source` |
| 9 | `e0b2d3a2-4305-47e7-b2d6-55cd83cf0121` `argument_aquinass_intellectualism_f0058bf9 -[created_by]-> person_thomas_aquinas_61b633ce` | `3504de28-379b-4469-bfc6-30617e84293d` (`creates`) | `repair`, `repair_reason` |
| 10 | `1adccf2a-36af-4d9f-86f4-bd5b846d3e29` `argument_aquinass_natural_inclination_to_happiness_7a145771 -[created_by]-> person_thomas_aquinas_61b633ce` | `85929df5-117a-4c2e-8703-99a435f84ec9` (`creates`) | `repair`, `repair_reason` |

### Préconditions et invariants de l’applier

Les préconditions sont contrôlées avant la première mutation en mémoire à
`scripts/apply_2026_08_17_inverse_normalization.py:143-188` : les deux IDs
existent encore, chaque triple est identique au plan, les extrémités sont
miroirs, et l’ontologie déclare toujours l’une des relations comme inverse de
l’autre. Toute dérive annule le lot avant écriture.

Les invariants de `:194-243` imposent :

- zéro arête pendante ;
- zéro triple dupliquée ;
- `source == source_id` et `target == target_id` partout ;
- union exacte des valeurs `metadata.attested_by` avant/après ;
- zéro paire inverse matérielle résiduelle ;
- disparition de chaque ID condamné ;
- identité octet-structurelle de toute arête étrangère au lot.

`--write` est opt-in, crée `edges.jsonl.bak-inverse_norm`, refuse d’écraser une
sauvegarde existante et remplace atomiquement le JSONL. Le deuxième passage est
un no-op grâce à l’absence de paires et au stamp des survivants.

## Étape 3 — garde R17

`scripts/check_ingestion_rules.py:565-615` indexe les triples et tient compte à
la fois de `R.inverse` et des relations qui déclarent `R` comme inverse. Il
déduplique les signalements par paire d’arêtes.

- mode `--new-only` : **BLOCK** si une nouvelle arête matérialise l’inverse
  d’une arête existante ou d’une autre arête du lot ;
- mode graphe complet : **WARN** sur la dette résiduelle ;
- documentation : `docs/development/ingestion-rules.md:43`.

Vérification synthétique :

```text
ingestion-rules: delta of 0 nodes / 1 edges
  [BLOCK] R17_materialized_inverse_pair: 1
        r17-probe: person_alexander_aphrodisias_fl200ce_n5o6p7q8
        -[creates]-> argument_agent_causation_two_way_powers_alexander_q8r9s0t1
        materializes the inverse of 0a1ee026-9e3e-49da-aa4f-5e8521b3f436

BLOCK: 1   WARN: 0
exit: 1
```

Audit complet actuel : `R17_materialized_inverse_pair: 4692` au niveau WARN ;
le mode complet par défaut reste informatif et sort avec le code 0.

## Sortie dry-run

Commande :

```bash
.venv/bin/python scripts/apply_2026_08_17_inverse_normalization.py
```

Sortie :

```text
inverse normalization: edges 53643 -> 48951; pairs=4692
  created_by: 19
  engages_with: 4
  has_chapter: 788
  has_section: 1236
  influences: 3
  source_for: 2
  translation_of: 2612
  wrote: 28
metadata fields merged: 9771
metadata conflicts archived in stamp: 8
invariants: dangling=0; duplicate_triples=0; paired_ids=OK
invariant attested_by union: OK
residual materialized inverse pairs: 0
--dry-run (default): nothing written. Use --write to apply.
```

## Application et idempotence sur copie sandbox

Première exécution `--write` sur la copie :

```text
inverse normalization: edges 53643 -> 48951; pairs=4692
metadata fields merged: 9771
metadata conflicts archived in stamp: 8
invariants: dangling=0; duplicate_triples=0; paired_ids=OK
invariant attested_by union: OK
residual materialized inverse pairs: 0
backup: /tmp/eleutheria-inverse-normalization.3Fe4Ku/edges.jsonl.bak-inverse_norm
wrote: /tmp/eleutheria-inverse-normalization.3Fe4Ku/edges.jsonl
```

Deuxième exécution :

```text
inverse normalization: edges 48951 -> 48951; pairs=0
idempotence: no materialized inverse pair remains; nothing to do
--write: no file changed
```

Comptage physique : 48 951 lignes dans la copie normalisée, 53 643 dans sa
sauvegarde. La vue runtime issue de la copie contient 97 902 arêtes (48 951
assertées + 48 951 inverses dérivées), sans triple doublonnée.

## Tests GraphRAG g6 sur la copie normalisée

Commande demandée, avec la copie sélectionnée par l’environnement :

```bash
cd graphrag && \
ELEUTHERIA_KG_SNAPSHOT_DIR=/tmp/eleutheria-inverse-normalization.3Fe4Ku \
../.venv/bin/python -m pytest tests/g6/ -q
```

Résultat :

```text
collected 87 items
...............................................................................
........
87 passed in 121.94s (0:02:01)
```

Tests cassés : **aucun**.

Le graphe contient 18 arêtes `opposes` avant normalisation et 18 après. Aucune
des 18 n’a de jumeau `opposed_by` matériel : nombre de suppressions touchant
`opposes` = **0**. La nouvelle valeur du pin g6 reste donc **18** ; le test n’a
pas été modifié. La vue runtime expose aussi les inverses `opposed_by` dérivés,
mais `_opposes_edges` compte uniquement la relation `opposes` assertée.

Vérifications ciblées complémentaires :

```text
knowledge graph: snapshot + db_traversal + analytics       25 passed
knowledge graph: RDF export + inference + semantic coverage 69 passed, 1 warning
backend: passages + KG neighbors                            8 passed
backend: topic tagger                                       8 passed
GraphRAG: weighted traversal + service                     24 passed
GraphRAG: get_neighbors + explore_subgraph                 16 passed
MCP tools                                                  13 passed
ruff (fichiers modifiés)                                   OK
```

L’avertissement unique est une dépréciation rdflib
`Dataset.default_context`; il est antérieur et sans rapport avec cette
normalisation.
