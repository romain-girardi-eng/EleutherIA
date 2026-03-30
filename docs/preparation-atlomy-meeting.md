# Preparation Meeting ATLOMY — Hebrew University of Jerusalem

**Interlocuteurs :** Dr. Orly Lewis (PI), équipe ATLOMY (ERC Starting Grant #852550)
**Leur projet :** Atlas anatomique 3D du monde gréco-romain (5e s. av. J.-C. → 2e s. ap. J.-C.)
**Overlap :** Même période, mêmes langues (grec/latin), même défi (structurer des textes anciens numériquement)

---

## 1. CORPUS & DONNEES TEXTUELLES

### Q: D'où viennent vos textes ?

**Sources primaires :**
- **Scaife/Perseus** via l'API CTS (`https://scaife-cts.perseus.org/api/cts`) — workflow automatisé :
  1. `GetValidReff` récupère tous les URN de sections à la profondeur configurée
  2. `GetPassage` par section récupère le TEI-XML
  3. Nettoyage TEI : suppression `<note>`, skip `<pb>/<lb>/<milestone>`, `<gap>` → `[...]`, suppression `<del>`
  4. Validation : ratio de caractères grecs (U+0370-03FF + U+1F00-1FFF) ou latins > 70% (seuil strict)
- **SBLGNT** pour le Nouveau Testament grec
- **Sources Chrétiennes** (pseudo-CTS URNs `urn:sc:{number}:{ref}`)
- Import TEI-XML brut stocké dans le champ `ancient_works.tei_xml` quand disponible

**Scripts :**
- `database/scripts/fetch_scaife_work.py` — fetcher générique, rate-limited (0.5s entre requêtes)
- `database/scripts/ingest_scaife_work.py` — ingestion batch (`execute_values`, page_size=100)

**Chiffres :** 487 oeuvres, 69 277 passages (schema migration note), 5 langues (`grc`, `lat`, `eng`, `hbo`, `ara`)

### Q: Comment traitez-vous les fragments ?

- Les fragments (Chrysippe via Stobée/Plutarque, SVF, etc.) sont typés `text_fragment` dans le KG, avec `source_work` et `svf_number` en propriétés
- Un noeud `source_collection` existe pour les SVF
- Les relations `preserves`/`preserved_in` lient fragment → oeuvre de transmission
- Les 50+ noeuds d'arguments sans ancrage textuel sont flaggés `needs_evidence=true` (Phase 0F)

### Q: Copyright et licences ?

- Textes Perseus/Scaife : domaine public ou CC
- Pas de textes TLG (payant, sous copyright)
- Éditions critiques modernes (Teubner, Budé, SC) : on stocke les références (éditeur, série, date) dans les métadonnées des noeuds `work`, pas le texte des éditions elles-mêmes
- Licence du projet : **CC BY 4.0**, DOI Zenodo `10.5281/zenodo.17379489`

### Q: Taux de couverture ?

- **Exhaustif** pour : Épictète (Entretiens, Manuel), Cicéron De Fato, Alexandre De Fato, Boèce Consolation V
- **Partiel** pour : Aristote (NE, Met, De Interp, De Gen et Corr, Physique), Platon (Rép., Lois, Timée, Phèdre, Phédon), Augustin, Origène
- **Critère de sélection** : pertinence pour le libre arbitre, le destin, la responsabilité morale ; priorisé en P0/P1/P2/P3

### Q: Grec polytone et lemmatisation ?

- **Stockage UTF-8** avec diacritiques polytones complets
- **Lemmatisation pré-calculée** via **OGA** (Open Greek and Latin Annotator) — pas de NLP runtime
- Tables dédiées :
  - `oga_tokens` : analyse morphologique mot par mot (`surface_form`, `lemma`, `pos`, `morphology JSONB`, `cts_urn`)
  - `oga_dependencies` : arbre syntaxique (Universal Dependencies : `nsubj`, `obj`, `amod`, etc.)
  - `passages.morphology` : cache JSONB passage-level (format `[{"l": "<lemma>"}]`) pour la recherche lemmatique
- Flag `ancient_works.has_morphology` indique les oeuvres traitées
- **Pas de CLTK, spaCy, ou Stanza** — tout est pré-calculé, importé comme données

---

## 2. KNOWLEDGE GRAPH & ONTOLOGIE

### Q: Comment avez-vous défini votre ontologie ?

**Approche hybride top-down / bottom-up :**
- Ontologie formelle dans `knowledge graph/ontology/` (JSON, version 3.0.0)
- **22 types de noeuds** : person, concept, argument, work, school, passage, debate, position, event, institution, text_fragment, modern_interpretation, term, source_collection, doctrine, publication, quote, synthesis, controversy, conceptual_evolution, group, argument_framework
- **56 types de relations** dans **12 catégories** : Argumentative (argues_for/against, refutes, responds_to, supports, critiques), Intellectual (influences, taught_by, student_of, extends), Affiliation (belongs_to_school, member_of, founded), Authorship (wrote, authored_by, created_by), Citation (cites, source_for, evidenced_by), Textual (preserves, preserved_in), Structural (contains, part_of, translation_of), Semantic (discusses, defines, related_to, contrasts_with, employs, presupposes), Doctrinal (holds_position, endorses, rejects), Debate (participates_in, contributes_to), Hermeneutic (interprets, represents, exemplifies), Temporal (contemporary_of, precedes, follows)

### Q: Qui valide les relations ?

- **Phase initiale** : import semi-automatique + validation manuelle
- **Audit automatisé** (`scripts/audit_kg_quality.py`) vérifie en continu :
  - Contraintes ontologiques (`source_types`/`target_types` par relation)
  - Noeuds orphelins/isolés, self-loops, doublons exacts
  - Near-duplicates (Jaccard tokens ≥ 0.8 ET SequenceMatcher ≥ 0.8)
  - Noeuds d'assertions sans preuve textuelle (regex sur langage assertif)
  - Drift ontologique (types inconnus, périodes invalides)
  - Artefacts de formatage (markdown, underscores, préfixes incohérents)
- **12 phases de correction manuelle** documentées (Phases 0-12), incluant :
  - 6 corrections de misattribution majeures (DL passages → Diogène Laërce, Pseudo-Plutarque, Porphyre, etc.)
  - Qualification systématique de 41 labels anachroniques ("compatibilisme" → "what modern scholars term...")
  - 229 noeuds nettoyés de ALL CAPS, 68 passages nettoyés d'artefacts HYPERLINK
  - 3 doublons fusionnés, 4 arêtes inversées corrigées

### Q: Confidence scores ?

- Table `passage_citations` : `confidence DOUBLE PRECISION CHECK 0.0-1.0`
- Valeurs attribuées selon la source :
  - Citation directe trouvée : **1.0**
  - Claim backed par KG : **0.7**
  - Résumé de métadonnées : **0.6**
  - Passage générique (fallback sans facettes) : **0.65**
  - Preuve insuffisante : **0.45**
  - Auto-linked (Phase 8) : recalibré à **0.5**
- Index partiel sur `confidence >= 0.7` pour les requêtes fréquentes
- Le pipeline GraphRAG trie par `confidence DESC` puis `sequence_number`

### Q: Interopérabilité FAIR ? RDF/OWL ?

**Ce qui existe :**
- **DOI Zenodo** : `10.5281/zenodo.17379489` (concept DOI, rolling archive)
- **CTS URNs** partout (standard Perseus/TLG/PHI)
- **CodeMeta 2.0** (`docs/codemeta.json`) — JSON-LD valide avec `@context: "https://doi.org/10.5063/schema/codemeta-2.0"`
- **CITATION.cff** (CFF 1.2.0)
- **ORCID** de l'auteur : `0000-0002-5310-5346`
- **CC BY 4.0**

**Ce qui n'existe pas encore :**
- Pas d'export RDF/OWL/Turtle natif du KG — le CLI a un stub `--format rdf` qui affiche "not yet implemented"
- L'ontologie est en JSON, pas en OWL/RDFS
- Pas de mapping CIDOC-CRM

**Réponse honnête :** L'ontologie JSON est conçue pour être convertible en OWL (types, contraintes source/target documentés). L'export RDF est sur la roadmap. Le CodeMeta est déjà du JSON-LD valide. La priorité actuelle est la complétude du corpus et la qualité des données.

---

## 3. IA & GRAPHRAG

### Q: Pourquoi Gemini 3 ?

- **Contexte 1M tokens** — permet d'envoyer le contexte COMPLET sans troncation (budget : 850k tokens disponibles après réserve de 15%)
- **Modèle principal** : `gemini-3.1-pro-preview` (30 req/min)
- **Fallback chain (mode normal)** : Gemini → Kimi (`kimi-latest`, 20 req/min) → OpenRouter (`google/gemini-3-flash-preview`, 60 req/min)
- **Fallback chain (thinking mode)** : Gemini → OpenRouter → Kimi (pour le raisonnement étendu)
- **Prompt caching Gemini** : SHA-256 cache key, TTL 15 min, seuil minimum 4096 tokens (pro) / 1024 (flash) — réduit les coûts sur les requêtes répétées
- **Embedding** : `models/gemini-embedding-001` (3072 dimensions, Matryoshka Representation Learning)

### Q: Comment empêchez-vous les hallucinations ?

**Politique zero-tolerance + contrôles techniques :**

1. **Pas de génération de texte ancien** — règle absolue dans les instructions système
2. **Pipeline grounded** — le LLM ne synthétise QUE à partir de passages réellement récupérés de la base
3. **Vérification programmatique** (noeud `ProgrammaticVerify` du FSM) — pas d'appel LLM, pure vérification :
   - Chaque citation dans la réponse est validée contre les `passage_citations` + `passages` réels
   - Construction du `ScholarlyAnswer` avec références vérifiées uniquement
4. **Claim Ledger** — chaque affirmation est décomposée en claims avec score de confiance (0.0-1.0), lié à des evidence bundles spécifiques
5. **Counter-evidence seeking** — noeud dédié (`SeekCounterEvidence`) qui cherche activement des preuves contradictoires
6. **Evidence sufficiency check** — heuristique multi-facteurs avant la synthèse : `0.12*bundles + 0.08*works + 0.1*counter + 0.08*facets`
7. **Audit continu** — 143 noeuds flaggés `needs_evidence`, 63 noeuds modernes flaggés comme potentiellement hors scope

### Q: Pipeline GraphRAG — architecture complète ?

**FSM pydantic-graph, 12 noeuds actifs :**

```
1.  ClassifyQueryType     → 5 types: specific_entity, global_abstract, multi_hop, comparative, temporal
                            Heuristique déterministe pour SPECIFIC_ENTITY (conf=0.75), sinon LLM (temp=0.0)

2.  ExpandQuery           → Expansion avec termes grecs/latins, philosophes, concepts, écoles
                            Skippé pour SPECIFIC_ENTITY/SIMPLE

3.  DiscoverCorpus        → Recherche large : noeuds KG + passages liés via Qdrant

4.  BuildResearchNotebook → Cadrage de la recherche (LLM)

5.  PlanReading           → Plan de lecture structuré (LLM)

6.  TreeNavigateWorks     → Navigation hiérarchique dans l'index arborescent des oeuvres
                            Par oeuvre : LLM ou heuristique de sélection de sections

7.  ExpandEvidenceBundles → Chargement des bundles de passages des sections sélectionnées

8.  SeekCounterEvidence   → Recherche active de contre-preuves (LLM)
                            Skippé pour SPECIFIC_ENTITY/SIMPLE

9.  EvidenceSufficiency   → Score heuristique multi-facteurs + validation LLM optionnelle

10. DraftClaimLedger      → 6-12 claims structurés, JSON schema enforced (temp=0.0)
                            Fast path si citation directe trouvée (conf=1.0)

11. RenderGroundedAnswer  → Synthèse scholarly (temp=0.2) + polish optionnel (temp=0.1)
                            + compression repair si nécessaire

12. ProgrammaticVerify    → Vérification pure (ZERO LLM) → ScholarlyAnswer final
```

**Nombre d'appels LLM :**
- Simple (SPECIFIC_ENTITY) : **1-2 appels** (DraftClaimLedger + RenderGroundedAnswer)
- Complexe (COMPARATIVE/TEMPORAL) : **jusqu'à 11 appels** (classification, expansion, cadrage, plan de lecture, navigation ×N, counter-evidence, sufficiency, claims, render, polish)

### Q: Quel modèle d'embedding ? Performance sur le grec ancien ?

- **Modèle** : `models/gemini-embedding-001` (Google)
- **Dimensions** : 3072 (configurable via `EMBEDDING_DIMENSIONS`)
- **Distance** : Cosine (Qdrant)
- **Matryoshka Representation Learning** — permet de tronquer les vecteurs à moindre dimension si besoin

**Collections Qdrant (6) :**

| Collection | Usage |
|---|---|
| `kg_nodes_dual` | Production, vecteur nommé "gemini" (prioritaire) |
| `kg_nodes_gemini` | Legacy, fallback |
| `ancient_free_will_vectors` | Historique, fallback filtré par `node_id` |
| `text_embeddings` | Embeddings de passages |
| `passages_contextual` | Passages ré-embeddés avec en-tête contextuel (auteur/oeuvre/période) — **prioritaire** |
| `kg_edges` | Embeddings d'arêtes |

**Performance grec ancien :** Le modèle Gemini est multilingue et gère le grec polytone. La collection `passages_contextual` améliore les résultats en ajoutant le contexte (auteur, oeuvre, période) avant le texte grec lors de l'embedding, ce qui désambiguïse les termes polysémiques.

### Q: Recherche hybride — comment ça marche ?

**3 modes fusionnés par Reciprocal Rank Fusion (RRF, k=60) :**

1. **Full-text** (PostgreSQL) : `to_tsvector('simple')` + `plainto_tsquery('simple')` + `ts_rank()` — config `'simple'` pour matching language-agnostic du grec/latin
2. **Lemmatique** : requête JSONB `passages.morphology @> '[{"l": "<lemma>"}]'` — cherche dans le cache morphologique pré-calculé
3. **Sémantique** : embedding Gemini de la requête → recherche Qdrant → scores normalisés

Formule RRF : `score(d) = Σ 1/(k + rank_i(d))` — les résultats présents dans plusieurs listes voient leur source concaténée (ex: "fulltext, lemmatic").

Flags activables : `enable_fulltext`, `enable_lemmatic`, `enable_semantic` sur `POST /search/hybrid`.

---

## 4. METHODOLOGIE & STANDARDS ACADEMIQUES

### Q: Comment un informaticien garantit la rigueur ?

1. **Vérification systématique contre les sources** — bibliothèque de PDFs, markdown, et extractions textuelles (~50 ouvrages majeurs : Bobzien 1998/2001, Dihle 1982, Frede 2011, Long & Sedley, etc.)
2. **Phases de review savant** (Phases 9-11) : fact-check noeud par noeud pour Origène, Justin Martyr, puis les 7 philosophes majeurs (Épictète, Chrysippe, Alexandre, Épicure, Augustin, Boèce, Cicéron)
   - Corrections concrètes : référence SC 290 fabriquée supprimée (Justin), affirmation "explicitly citing Carneades" supprimée (Origène), dates corrigées, labels anachroniques qualifiés
3. **Audit automatisé** continu (`scripts/audit_kg_quality.py`) — 6 dimensions d'analyse
4. **Affiliation** : Université Côte d'Azur (CEPAM) + Université de Genève
5. **Dataset publié** : Zenodo DOI `10.5281/zenodo.17379489`, CC BY 4.0, ORCID lié

### Q: Labels anachroniques — comment les signalez-vous ?

Phase 12 dédiée — **41 noeuds** où "compatibilisme/incompatibilisme" était présenté comme fait historique :
- Pattern systématique : "Stoic compatibilism" → "what modern scholars term Stoic compatibilism"
- "soft/hard determinism" qualifié comme terminologie moderne
- 8 priority claims hedgés : "First systematic" → "Often considered the first systematic"
- 1 superlatif adouci : "was the most important" → "is widely regarded as the most important"
- 1 assertion corrigée : "This proves that" → "This is taken to show that"

### Q: KG = interprétations ou faits ?

**Distinction explicite dans l'ontologie :**
- Type `modern_interpretation` dédié aux interprétations savantes (avec `interpreter`, `publication_year`)
- Type `publication` pour les travaux modernes (avec `key_claim`, `zotero_key`)
- Relation `interprets` / `interpreted_by` pour lier interprétation → source
- **Dual-layer structure** : couche primaire (sources anciennes) vs. couche secondaire (réception moderne : Bobzien, Frede, Kane, etc.)
- Confiance graduée : les auto-linked citations sont à 0.5, les citations vérifiées manuellement à 0.7-1.0

---

## 5. INFRASTRUCTURE TECHNIQUE

### Q: Architecture de déploiement ?

**3 modes :**

| Mode | Stack | Usage |
|---|---|---|
| **Local** | Docker Compose (PostgreSQL 16-alpine, Qdrant 1.13.3, FastAPI, Nginx) | Développement |
| **Production Docker** | Supabase (pgbouncer:6543, SSL) + Qdrant Cloud + Docker backend/frontend | Staging |
| **Production live** | **Cloudflare Workers** (Hono, TypeScript) + Supabase + Qdrant Cloud | `free-will.app` |

**Docker Compose :**
- 4 services core + 3 optionnels (pgAdmin 8, Prometheus 2.51, Grafana 10.4)
- Réseaux isolés : `internal` (bridge, pas d'accès externe), `frontend` (backend+frontend), `monitoring`
- Sécurité : `read_only: true`, `no-new-privileges`, tmpfs pour `/tmp`
- Limites mémoire : Postgres 1G, Qdrant 2G, Backend 1G/2CPU, Frontend 256M/1CPU

**Cloudflare Workers (production) :**
- Framework Hono, services TypeScript complets : GraphRAG agentic/hiérarchique/workflow, KG, cache, auth
- Agents : planning, reasoning (enhanced), refinement, verification, citation-mapper

### Q: CI/CD ?

**GitHub Actions** (`ci.yml`) sur push/PR vers `main` :
- `lint` : Ruff (linter + formatter) sur les 3 packages Python
- `typecheck` : mypy
- `test-database` / `test-kg` / `test-graphrag` : pytest séparés
- `test-frontend` : ESLint + Vitest + `npm run build`
- `docker` : build des images (après lint+typecheck)

**Publication** (`publish.yml`) : PyPI via trusted publishing (OIDC, pas de mot de passe)

### Q: Comment reproduire le setup ?

1. `git clone` + `cp .env.example .env` + ajouter clé(s) API
2. `docker compose -f deploy/docker-compose.yml up`
3. Dataset complet sur Zenodo (`10.5281/zenodo.17379489`)
4. **Manque** : les embeddings Qdrant ne sont pas dans le dataset Zenodo — il faut re-embed avec `scripts/reembed_kg_nodes.py` (nécessite une clé Gemini)

---

## 6. FRONTEND & VISUALISATION

### Q: Stack frontend ?

- **React 19.1** + **TypeScript 5.9** + **Vite 7.1**
- **Cosmograph** (visualisation de graphe 2D, GPU-accelerated)
- **Three.js / React Three Fiber** (espace sémantique 3D des embeddings)
- **D3.js 7** (timelines, charts)
- **Framer Motion 12** (animations)
- **Radix UI + Tailwind CSS** (composants UI)
- **i18next** : 5 langues (EN, FR, DE, IT, EL), détection par localStorage → navigator → htmlTag
- **Accessibilité** : axe-core intégré

### Q: Code splitting ?

6 chunks manuels dans Vite : `cosmograph-vendor`, `three-vendor`, `charts-vendor`, `animation-vendor`, `react-vendor`, `ui-vendor`

---

## 7. SYNERGIES POTENTIELLES AVEC ATLOMY

### Overlap textuel direct

| Texte | EleutherIA | ATLOMY |
|---|---|---|
| **Galien, De Placitis** (De Plac. Hipp. et Plat.) | 3 passages ingérés | Source anatomique centrale |
| **Aristote, De Anima** | KG nodes + passages | Physiologie de la perception |
| **Aristote, De Gen. et Corr.** | 69 passages (Scaife) | Théorie des éléments/corps |
| **Corpus hippocratique** | Références fragmentaires | Source fondamentale pour ATLOMY |
| **Galien** (autres traités) | Références dans le KG | Coeur du projet ATLOMY |

### Ponts thématiques

1. **Déterminisme physiologique chez Galien** — le rapport entre constitution corporelle et libre arbitre (De Plac. = pont direct)
2. **Âme et corps chez les Stoïciens** — pneuma, tonos, hegemonikon : concepts partagés entre anatomie et philosophie morale
3. **Aristote De Anima** — la perception, le désir, la prohairesis : de l'anatomie à l'éthique
4. **Alexandre d'Aphrodise** — commentateur d'Aristote sur le De Anima ET auteur du De Fato
5. **Lexique technique commun** — termes grecs partagés : ψυχή, πνεῦμα, ἡγεμονικόν, αἴσθησις, ὄρεξις

### Complémentarité technique

| ATLOMY | EleutherIA | Synergie possible |
|---|---|---|
| Atlas 3D anatomique | Knowledge graph philosophique | Visualisation intégrée : cliquer sur un organe → voir les débats philosophiques associés |
| Lexique anatomique structuré | Lemmatisation OGA + recherche hybride | Enrichissement croisé des lexiques |
| TEI-XML (probablement) | CTS URNs + PostgreSQL | Standards interopérables |
| Focus texte → image 3D | Focus texte → graphe de connaissances | Deux modalités de "lecture augmentée" |

### Proposition concrète

- **Échange de données** : si ATLOMY a un lexique structuré des termes anatomiques grecs, il pourrait enrichir les `term` nodes d'EleutherIA pour les concepts psycho-physiologiques
- **Galien De Placitis comme projet pilote** : ce texte est au croisement exact des deux projets (anatomie du cerveau ET libre arbitre)
- **Standard commun** : CTS URNs pour les références textuelles, possibilité de converger vers un export RDF/LOD commun

---

## 8. CHIFFRES CLES (aide-mémoire)

| Métrique | Valeur |
|---|---|
| Noeuds KG | 17 746 |
| Arêtes KG | 42 925 |
| Types de noeuds | 22 |
| Types de relations | 56 (12 catégories) |
| Oeuvres | 487 |
| Passages | 69 277 |
| Citations passage-KG | 13 293 |
| Langues sources | 5 (grc, lat, eng, hbo, ara) |
| Langues UI | 5 (EN, FR, DE, IT, EL) |
| Couverture temporelle | ~1 200 ans (6e s. av. J.-C. → 6e s. ap. J.-C.) |
| Tests | 77 (18 database + 31 KG + 28 GraphRAG) |
| Embedding dimensions | 3 072 (Gemini, cosine) |
| Contexte LLM max | 1M tokens (850k disponibles) |
| Budget passage bundles | 552 500 tokens (65% du budget) |
| Collections Qdrant | 6 |
| DOI | 10.5281/zenodo.17379489 |
| Licence | CC BY 4.0 |
| ORCID | 0000-0002-5310-5346 |
| Prod URL | https://free-will.app |

---

## 9. QUESTIONS A POSER A ATLOMY

1. Utilisez-vous des CTS URNs ou un autre système de référencement textuel ?
2. Votre lexique anatomique est-il exportable dans un format structuré (JSON, CSV, RDF) ?
3. Avez-vous envisagé de connecter les termes anatomiques aux débats philosophiques sur l'âme (De Anima, pneuma stoïcien) ?
4. Quel est votre stack technique ? (TEI-XML ? Base de données ? Moteur de recherche ?)
5. Le projet est-il open-source ou prévoyez-vous de le rendre accessible ?
6. Seriez-vous intéressés par un projet pilote sur Galien De Placitis comme intersection de nos deux corpus ?
