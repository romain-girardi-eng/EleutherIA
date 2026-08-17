# Carte des sources du data paper EleutherIA

**Date de la carte :** 2026-08-17  
**Auteur du papier et du jeu de données :** Romain Girardi, seul auteur  
**Objet :** rendre chaque affirmation factuelle et chaque chiffre du brouillon `docs/paper/eleutheria_data_paper_draft.md` vérifiables dans le dépôt.

## 1. Règles de traçabilité retenues

- Les statistiques courantes viennent de `data/stats.md` et de sa source structurée `data/stats.json`, générées le 17 août 2026.
- Un décompte de lignes JSONL signifie ici un décompte d’objets JSON valides, un objet par ligne. Il est reproductible par lecture des fichiers, sans modifier le dépôt.
- Les rapports `*_plan.md` prouvent une méthode, un dry-run ou un état bloqué ; ils ne sont pas présentés comme une application lorsque leur propre statut dit « non appliqué ».
- Les rapports `*_applied.md` prouvent les écritures effectivement consignées par la vague correspondante.
- Une constatation d’audit n’est pas assimilée à une erreur confirmée. Les faux positifs et les décisions de maintien font partie de la preuve.
- Les nombres calculés par addition de décomptes présents dans plusieurs fichiers sont marqués « dérivé ». Les opérandes restent indiqués.

## 2. Deux divergences qu’il ne faut pas masquer

### 2.1 Total du corpus d’audit

La formulation de mission mentionne 5 425 constatations. Les quatre fichiers JSONL nommément désignés contiennent actuellement :

| Fichier | Objets JSON |
|---|---:|
| `data/audit/2026-08-16_deep_audit_structural.jsonl` | 41 |
| `data/audit/2026-08-16_deep_audit_linguistic.jsonl` | 1 589 |
| `data/audit/2026-08-16_deep_audit_bibliographic.jsonl` | 3 683 |
| `data/audit/2026-08-16_deep_audit_semantic.jsonl` | 108 |
| **Somme dérivée** | **5 421** |

Le papier emploie donc **5 421**, seul total reproductible à partir du corpus indiqué. Il précise explicitement « not 5,425 » afin de ne pas inventer les quatre enregistrements absents.

### 2.2 Nombre d’œuvres

`data/stats.md` et `data/stats.json` comptent **249 nœuds KG de type `work`** et **190 œuvres avec texte**. `CLAUDE.md` documente séparément un **catalogue de 254 œuvres**. Le papier conserve les trois mesures et explique qu’elles ne décrivent pas la même chose. Il n’attribue pas 254 à `data/stats.md`.

## 3. Registre exhaustif des chiffres du papier

| Chiffre ou valeur | Emplacement/affirmation dans le papier | Source exacte | Trace dans la source |
|---|---|---|---|
| DOI `10.5281/zenodo.17379489` | Abstract, repository location, data accessibility, référence Girardi | `README.md` | badge DOI, section Citation et lien Zenodo |
| CC BY 4.0 | Abstract, overview, dataset description, data accessibility | `README.md` | badge et section License |
| `v5.2.0` | Overview, nom de la version auditée/réparée | message local du tag explicitement autorisé par la mission | « EleutherIA v5.2.0 — audited and repaired knowledge graph » |
| 17 août 2026 | date de l’instantané | `data/stats.md`; `data/stats.json` | `generated_at: 2026-08-17T08:44:31Z` |
| 19 994 nœuds | Abstract, overview | `data/stats.md`; `data/stats.json` | `kg.nodes: 19994` |
| 49 391 arêtes assertées | Abstract, overview | `data/stats.md`; `data/stats.json` | `kg.edges: 49391`; l’adjectif « assertées » est justifié par le modèle d’inverses dérivés |
| 21 103 passages | Abstract, overview | `data/stats.md`; `data/stats.json` | `corpus.passages: 21103` |
| 19 917 citations passage→KG | Abstract, overview | `data/stats.md`; `data/stats.json` | `corpus.passage_citations: 19917` |
| 254 œuvres cataloguées | Overview, limitations | `CLAUDE.md` | « Ancient Greek/Latin texts corpus (254 works…) » et table `ancient_works` |
| 249 nœuds `work` | Overview, limitations | `data/stats.json` | `kg.works: 249` et `node_type_counts.work: 249` |
| 190 œuvres avec texte | Overview, limitations | `data/stats.json` | `corpus.works_with_text: 190` |
| VIe s. av. n. è.–VIe s. de n. è. | Abstract et contexte | `README.md`; `CLAUDE.md` | bornes Presocratics/6th c. BCE et Boethius/Late Fathers/6th c. CE |
| 198 imports bibliographiques non lus | Construction et limitations | `data/audit/2026-08-17_origenality_import_plan.md`; `data/kg/nodes.jsonl` | « Publications nouvelles proposées : 198 » ; 198 nœuds actuels avec `citation_verdict=bibliographic_import` |
| 24 types de nœuds | Construction | `knowledge graph/ontology/node_types.json`; `data/stats.json` | 24 clés dans `node_types`; `ontology.node_types_defined: 24` |
| 16 types de nœuds employés | Construction | `data/stats.md`; `data/stats.json` | `node_types_in_use: 16` |
| 77 types d’arêtes | Construction | `knowledge graph/ontology/edge_types.json`; `data/stats.json` | 77 clés dans `edge_types`; `ontology.edge_types_defined: 77` |
| 54 relations employées | Construction | `data/stats.md`; `data/stats.json` | `edge_relations_in_use: 54` |
| 77 définitions avec inverse déclaré | Construction | `knowledge graph/ontology/edge_types.json` | chaque entrée de `edge_types` possède une valeur `inverse` non vide |
| version 1.0.0 des deux schémas | Construction | `knowledge graph/ontology/period_scheme.json`; `school_scheme.json` | `scheme.version: 1.0.0` dans les deux fichiers |
| émission des schémas le 17 août 2026 | Construction | mêmes fichiers | `scheme.issued: 2026-08-17` |
| 15 périodes | Construction | `period_scheme.json`; `data/audit/2026-08-17_vocab_freeze_plan.md` | 15 concepts/valeurs distinctes |
| 18 écoles/traditions | Construction | `school_scheme.json`; `2026-08-17_vocab_freeze_plan.md` | 18 concepts après nettoyage |
| 33 concepts contrôlés | Construction | `2026-08-17_vocab_freeze_plan.md` | sortie RDF : `controlled concepts=33`; somme 15+18 |
| R1–R18, R3b inclus, R6 absent | Construction | `docs/development/ingestion-rules.md`; `scripts/check_ingestion_rules.py` | table des règles et sections de contrôle du script |
| 41 résultats structurels | QA, tableau 1 | `2026-08-16_deep_audit_structural.jsonl` | 41 objets |
| 1 589 résultats linguistiques | QA, tableau 1 | `2026-08-16_deep_audit_linguistic.jsonl` | 1 589 objets |
| 3 683 résultats bibliographiques | QA, tableau 1 | `2026-08-16_deep_audit_bibliographic.jsonl` | 3 683 objets |
| 108 résultats sémantiques | QA, tableau 1 | `2026-08-16_deep_audit_semantic.jsonl` | 108 objets |
| total 5 421 | QA, tableau 1 | quatre fichiers précédents | somme dérivée 41+1 589+3 683+108 |
| 82 candidats Méthode bloqués; zéro description réécrite | QA, exemple du blocage sur source | `data/audit/2026-08-17_methodius_reingest_plan.md` | sorties `blocked=82`, `changed descriptions=0`, `rewritten=0` |
| 14 arêtes `opposes` | QA dialectique | `docs/development/ingestion-rules.md`; `scripts/check_ingestion_rules.py` | population complète indiquée par R16 |
| 13 arêtes `agrees_with` | QA dialectique | mêmes sources | population complète indiquée par R16 |
| 14,3 % | taux clair avant réparation pour `opposes` | mêmes sources | texte de R16 |
| 23,1 % | taux clair avant réparation pour `agrees_with` | mêmes sources | texte de R16 |
| pp. 78–81 | contre-exemple Salles | `data/audit/2026-08-17_dialectical_repairs_plan.md`; `scripts/check_ingestion_rules.py` | relecture imprimée indiquant que Salles s’oppose à la thèse enregistrée |
| graine 20260817 | échantillonnage stratifié | `data/audit/2026-08-17_stratified_verification.md`; `.jsonl` | `sample_seed: 20260817` |
| 160 passages | taille totale de l’échantillon | mêmes sources | 160 objets, 40 par strate |
| 40 par strate | plan de sondage | mêmes sources | rapport et rangs unitaires |
| environ 14 900 éligibles | limites de l’échantillon | `2026-08-17_stratified_verification.md` | « 160 passages sur ~14 900 éligibles » |
| SC : 15/25/0/0; IC [0,0 %; 8,8 %]; CER 0,0 % | tableau 2 | `2026-08-17_stratified_verification.md` | ligne SC-series OCR |
| TLG : 5/15/20/0; IC [35,2 %; 64,8 %]; CER 1,1 % | tableau 2 | même rapport | ligne TLG E realignments |
| Perseus/web : 0/9/12/19; IC [18,1 %; 45,4 %]; CER 1,8 % | tableau 2 | même rapport | ligne Perseus/web |
| First1KGreek : 0/3/37/0; IC [80,1 %; 97,4 %]; CER 21,0 % | tableau 2 | même rapport | ligne First1KGreek |
| SC 40/40 même source | interprétation du tableau 2 | même rapport et 40 enregistrements SC du JSONL | `authority_same_as_ingest_source: true` |
| 17 réingestions *Magna Moralia* | interprétation TLG | même rapport | sous-population indiquée dans la lecture critique |
| 23 nœuds Plotin | interprétation TLG | même rapport | sous-population indiquée |
| 20 sur 23 classés substantiels | interprétation TLG | même rapport | 20 verdicts mécaniques Plotin |
| CER médian Plotin 1,1 % | interprétation TLG | même rapport | lecture critique de la sous-population |
| 19 autorités indisponibles | interprétation Perseus/web | même rapport et JSONL | 19 `SOURCE_UNAVAILABLE` |
| borne supérieure 8,8 % avec zéro observation | limites | même rapport | section « Limites honnêtes » |
| 16–17 août 2026 | dates du cycle d’audit/réparation | noms et champs date des fichiers d’audit | audit profond le 16, plans/rapports le 17 |
| 2026 comme publication Zenodo citée | description du dataset et référence | `README.md` | entrée BibTeX `girardi2026eleutheria` |

## 4. Traçabilité des affirmations non numériques par section

### 4.1 Overview et contexte

| Affirmation | Fichier(s) probant(s) |
|---|---|
| dépôt GitHub, site, DOI, licence, périmètre historique | `README.md` |
| structure primaire/secondaire et fonction de la réception moderne | `CLAUDE.md`; `docs/academic/METHODOLOGY.md` |
| intérêt du graphe pour relier témoins, arguments, concepts et interprétations | `README.md`; `docs/architecture/OVERVIEW.md`; `docs/reference/API.md` |
| implémentation FAIR : DOI, API, CTS, RDF/JSON-LD, licence | `docs/academic/METHODOLOGY.md`; `docs/architecture/semantic-layer.md`; `README.md` |
| titres et années Bobzien, Dihle, Frede, Fürst | `data/kg/nodes.jsonl`; `data/kg/publications.bib` |

### 4.2 Construction

| Affirmation | Fichier(s) probant(s) |
|---|---|
| politique « éditions critiques seulement » et séries prioritaires | `docs/ACADEMIC_INTEGRITY.md` |
| présence et usage des fonds TLG E et Sources Chrétiennes | `CLAUDE.md`; `data/audit/2026-08-17_linguistic_repairs_plan.md`; `2026-08-17_mm_reingest_plan.md` |
| Perseus/Scaife et First1KGreek comme témoins numériques identifiés | `docs/operations/corpus-integrity.md`; `data/audit/2026-08-17_stratified_verification.md`; verdicts sous `data/audit/primary_fetch/` |
| contrat SHA-256 NFC, provenance d’édition et détection de dérive | `docs/operations/corpus-integrity.md` |
| archive OCR moderne non redistribuée; manifeste et empreintes | `data/scholarly_sources/README.md` |
| import Origenality : verdict, rang « unread », droits et provenance des résumés, absence de thèse fabriquée | `data/audit/2026-08-17_origenality_import_plan.md`; `scripts/ingest_2026_08_17_origenality_import.py`; nœuds importés dans `data/kg/nodes.jsonl` |
| types, relations, catégories et inverses | `knowledge graph/ontology/node_types.json`; `edge_types.json` |
| vocabulaires contrôlés et notes de portée | `period_scheme.json`; `school_scheme.json`; `data/audit/2026-08-17_vocab_freeze_plan.md` |
| RDF, mappings externes, sérialisations, SHACL à deux niveaux, OWL-RL et chaînes de preuve | `docs/architecture/semantic-layer.md`; code sous `knowledge graph/src/eleutheria_kg/semantic/` |
| formats JSONL et rôle du miroir | `CLAUDE.md`; fichiers `data/kg/*.jsonl`, `data/corpus/*.jsonl` |
| API œuvres/passages/KG/GraphRAG | `docs/reference/API.md` |
| style `canonical_ref` et rôle du CTS URN | `docs/reference/CITATION_STYLE.md`; `docs/academic/METHODOLOGY.md` |
| règles R1–R18 motivées par incidents | `docs/development/ingestion-rules.md`; `scripts/check_ingestion_rules.py` |

### 4.3 Assurance qualité

| Affirmation | Fichier(s) probant(s) |
|---|---|
| portée des quatre dimensions | contenu et champs des quatre `2026-08-16_deep_audit_*.jsonl` |
| un finding n’est pas nécessairement une erreur | classes `uncited_claim_false_positive`, `false_positive_attested`, verdicts des plans dialectique/linguistique/sémantique |
| réparations datées, dry-run, préconditions, invariants, estampilles, sauvegardes et rapports | `CLAUDE.md`; ensemble des `2026-08-17_*_plan.md` et `*_applied.md` |
| absence d’écriture lorsque la source manque | `2026-08-17_methodius_reingest_plan.md`; `2026-08-17_translations_plan.md`; champs `needs_*` des nœuds |
| politique anti-fabrication | `docs/ACADEMIC_INTEGRITY.md`; `docs/development/ingestion-rules.md`; `CLAUDE.md` |
| gate grec : corpus, allowlist ou TLG E avec provenance | `scripts/check_greek_gate.py` |
| vérificateur déterministe à la réponse, raisons et suppression par défaut | `graphrag/src/eleutheria_graphrag/agents/text_verifier.py` |
| mesure puis réparation de la couche dialectique | `docs/development/ingestion-rules.md`; `2026-08-17_dialectical_repairs_plan.md`; `2026-08-17_dialectical_repairs_applied.md` |
| obligation `attested_by` après incident | `scripts/check_ingestion_rules.py`, règle R16 |
| conception, résultats et limites du sondage stratifié | `2026-08-17_stratified_verification.md`; 160 lignes du `.jsonl` associé |

### 4.4 Description du dataset

| Affirmation | Fichier(s) probant(s) |
|---|---|
| liste des objets JSONL | fichiers sous `data/kg/` et `data/corpus/`; `CLAUDE.md` |
| ontologie et schémas JSON | `knowledge graph/ontology/` |
| shapes Turtle | `knowledge graph/src/eleutheria_kg/semantic/shapes/` |
| bibliographie BibTeX | `data/kg/publications.bib`; `data/kg/publications_bibtex_report.json` |
| sérialisations RDF reproductibles | `docs/architecture/semantic-layer.md`; `semantic/rdf_export.py` |
| valeurs actuelles de `citation_verdict` | `data/kg/nodes.jsonl`: `verified`, `corrected`, `false_positive_attested`, `bibliographic_import` |
| sens de `bibliographic_import` | `2026-08-17_origenality_import_plan.md` et chaîne `source_rank` des nœuds importés |
| dette visible par champs `needs_*` | `data/kg/nodes.jsonl`; `docs/development/ingestion-rules.md`; plans de réingestion/traduction |

### 4.5 Réutilisation et limites

| Affirmation | Fichier(s) probant(s) |
|---|---|
| réutilisation GraphRAG et QA sourcée | `README.md`; `docs/architecture/OVERVIEW.md`; `docs/reference/API.md` |
| instrument de *status quaestionis* via relations dialectiques attestées | `2026-08-17_dialectical_repairs_plan.md`; R16 dans `ingestion-rules.md` |
| transfert de la méthode incident→règle | introduction et tableau de `docs/development/ingestion-rules.md` |
| asymétrie de couverture | `data/stats.json`; distinction avec `CLAUDE.md` pour les 254 cataloguées |
| couche bibliographique non lue | `2026-08-17_origenality_import_plan.md`; nœuds importés |
| éléments bloqués sur source | `2026-08-17_methodius_reingest_plan.md` et autres plans marqués non appliqués |
| limites fidélité/correction, variance d’édition et désalignement d’empans | `2026-08-17_stratified_verification.md` |

## 5. Références savantes vérifiées contre les publications du KG

| Citation du papier | Nœud KG / entrée BibTeX | Éléments vérifiés |
|---|---|---|
| Bobzien 1998, *Determinism and Freedom in Stoic Philosophy* | `scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso`; entrée `publication-1998-determinism-and-freedom-in-stoic-philosophy` | Susanne Bobzien, 1998, Clarendon Press/OUP |
| Dihle 1982, *The Theory of Will in Classical Antiquity* | `pub_dihle_1982_theory_of_will`; entrée `dihle-1982-theory-of-will-classical-antiquity` | Albrecht Dihle, Sather 48, University of California Press, 1982 |
| Frede 2011, *A Free Will: Origins of the Notion in Ancient Thought* | `pub_frede_2011_free_will`; entrée `frede-2011-free-will-origins-notion-ancient-thought` | Michael Frede; A. A. Long éd.; Sather 68; University of California Press; 2011 |
| Fürst 2022, *Wege zur Freiheit: Menschliche Selbstbestimmung von Homer bis Origenes* | `pub_furst_2022_wege_freiheit`; entrée `furst-2022-wege-zur-freiheit-menschliche-selbstbestimmung-von-homer-bis-origenes` | Alfons Fürst; Mohr Siebeck; 2022; DOI et ISBN |
| Girardi 2026, EleutherIA | entrée BibTeX de `README.md` | auteur unique Romain Girardi, titre, année, Zenodo, DOI |
| Salles 2005, *The Stoics on Determinism and Compatibilism* | `scholarly_work_salles_2005_the_stoics_on_determinism_and_compatibil` | Ricardo Salles; Ashgate; 2005; pages probantes 78–81 dans le plan dialectique |

Les références FAIR, CTS, SKOS et SHACL sont des références normatives externes ; elles soutiennent l’explication des standards, pas un chiffre propre à EleutherIA.

## 6. Plans et rapports du 17 août effectivement examinés

Cette table empêche qu’une vague soit citée globalement sans respecter son statut.

| Fichier | Statut déclaré / apport au papier |
|---|---|
| `2026-08-17_dialectical_repairs_plan.md` | plan détaillé, preuves imprimées, dry-run, faux positifs, R16 |
| `2026-08-17_dialectical_repairs_applied.md` | application consignée de la vague dialectique |
| `2026-08-17_factual_corrections_applied.md` | corrections chronologiques, auteurs et parentages |
| `2026-08-17_furst_markschies_plan.md` | plan d’ingestion secondaire, vérifications et exclusions; non appliqué dans le rapport |
| `2026-08-17_gibbons_reingest_plan.md` | plan d’ingestion secondaire avec provenance/pages; non appliqué |
| `2026-08-17_ingestion_debt_applied.md` | dette R1–R15 traitée et états de passages requalifiés |
| `2026-08-17_inverse_normalization_plan.md` | politique de direction canonique, fusion de métadonnées, R17, sandbox idempotente |
| `2026-08-17_linguistic_repairs_plan.md` | plan philologique, TLG E, erreurs de langue/URN, garde-fous |
| `2026-08-17_linguistic_repairs_applied.md` | application consignée des réparations linguistiques |
| `2026-08-17_methodius_reingest_plan.md` | plan bloqué par absence de TLG 2959; aucune réécriture textuelle |
| `2026-08-17_mm_reingest_plan.md` | réingestion *Magna Moralia* préparée et testée en sandbox |
| `2026-08-17_origen_lit_plan.md` | sélection de littérature sur Origène; non-application explicitée |
| `2026-08-17_origenality_import_plan.md` | politique fédérée, marquage non lu, droits/provenance, déduplication |
| `2026-08-17_plotinus_remap_plan.md` | remappage de 709 références préparé; texte inchangé; sandbox idempotente |
| `2026-08-17_semantic_merges_plan.md` | arbitrage des doublons/thèses, préconditions et dry-run |
| `2026-08-17_semantic_merges_applied.md` | application consignée des fusions sémantiques |
| `2026-08-17_translations_plan.md` | vrais jumeaux de traduction et dix cas bloqués; texte source préservé |
| `2026-08-17_vocab_freeze_plan.md` | schémas v1.0.0, SKOS/SHACL, R18, application sandbox seulement |
| `2026-08-17_work_conflation_applied.md` | séparation consignée de onze conteneurs d’œuvres conflés |

## 7. Traçabilité du plan de figures

### Figure 1 — couches et provenance

Sources : `README.md`, `CLAUDE.md`, `docs/academic/METHODOLOGY.md`, `docs/architecture/semantic-layer.md`, `docs/operations/corpus-integrity.md`, `docs/reference/API.md`.

### Tableau 1 — audit par dimension

Sources et nombres : les quatre JSONL du 16 août listés en section 2.1. La légende doit dire « constatations » et non « erreurs ».

### Figure 2 — cycle de réparation

Sources : règles de `CLAUDE.md`, tous les plans/applied du 17 août, `docs/development/ingestion-rules.md`, `scripts/check_ingestion_rules.py`.

### Tableau 2 — vérification stratifiée

Source narrative : `data/audit/2026-08-17_stratified_verification.md`.  
Source unitaire : `data/audit/2026-08-17_stratified_verification.jsonl`.  
Les quatre lignes et les IC doivent être recopiés sans interprétation automatique en taux d’erreur réel.

### Figure 3 — trajectoire d’instantanés

| Instantané | Nœuds | Arêtes | Nœuds work | Passages corpus | Citations |
|---|---:|---:|---:|---:|---:|
| v5.1.0, snapshot 2026-06-05 | 20 060 | 56 737 | 241 | 17 823 | 19 751 |
| snapshot généré 2026-08-17 | 19 994 | 49 391 | 249 | 21 103 | 19 917 |

Sources : `docs/releases/v5.1.0.md` pour la première ligne; `data/stats.md` et `data/stats.json` pour la seconde. Les plans/applied de normalisation d’inverses, fusions sémantiques et conflation d’œuvres expliquent pourquoi une baisse d’arêtes peut être un effet de curation et non une perte accidentelle.

## 8. Contrôle final attendu avant soumission

1. Régénérer `data/stats.md`/`.json` et reporter toute évolution dans le papier et cette carte.
2. Recompter les quatre JSONL d’audit; ne changer 5 421 que si les fichiers changent.
3. Vérifier que la version Zenodo citée correspond bien au snapshot décrit, le DOI actuel étant un DOI concept.
4. Confirmer les placeholders Acknowledgements, Funding et Competing interests.
5. Choisir avec la revue entre condensation en Data Paper et reclassement en Discussion Paper; ne pas supprimer les limites statistiques pour gagner des mots.
