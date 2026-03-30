# Meeting Preparation — ATLOMY, Hebrew University of Jerusalem

**Contacts:** Dr. Orly Lewis (PI), ATLOMY team (ERC Starting Grant #852550)
**Their project:** 3D anatomical atlas of the Greco-Roman world (5th c. BCE → 2nd c. CE)
**Overlap:** Same period, same languages (Greek/Latin), same challenge (structuring ancient texts digitally)

---

## 1. CORPUS & TEXTUAL DATA

### Q: Where do your texts come from?

**Primary sources:**
- **Scaife/Perseus** via the CTS API (`https://scaife-cts.perseus.org/api/cts`) — automated workflow:
  1. `GetValidReff` retrieves all section URNs at the configured depth
  2. `GetPassage` per section fetches TEI-XML
  3. TEI cleaning: remove `<note>`, skip `<pb>/<lb>/<milestone>`, `<gap>` → `[...]`, remove `<del>`
  4. Validation: Greek character ratio (U+0370-03FF + U+1F00-1FFF) or Latin > 70% (strict threshold)
- **SBLGNT** for the Greek New Testament
- **Sources Chrétiennes** (pseudo-CTS URNs `urn:sc:{number}:{ref}`)
- Raw TEI-XML stored in `ancient_works.tei_xml` field when available

**Scripts:**
- `database/scripts/fetch_scaife_work.py` — generic fetcher, rate-limited (0.5s between requests)
- `database/scripts/ingest_scaife_work.py` — batch ingestion (`execute_values`, page_size=100)

**Numbers:** 487 works, 69,277 passages (schema migration note), 5 languages (`grc`, `lat`, `eng`, `hbo`, `ara`)

### Q: How do you handle fragments?

- Fragments (Chrysippus via Stobaeus/Plutarch, SVF, etc.) are typed `text_fragment` in the KG, with `source_work` and `svf_number` as properties
- A `source_collection` node exists for the SVF
- `preserves`/`preserved_in` relations link fragment → transmitting work
- 50+ argument nodes without textual grounding are flagged `needs_evidence=true` (Phase 0F)

### Q: Copyright and licensing?

- Perseus/Scaife texts: public domain or CC
- No TLG texts (paid, copyrighted)
- Modern critical editions (Teubner, Budé, SC): we store references (editor, series, date) in `work` node metadata, not the edition text itself
- Project license: **CC BY 4.0**, Zenodo DOI `10.5281/zenodo.17379489`

### Q: Coverage rate?

- **Exhaustive** for: Epictetus (Discourses, Encheiridion), Cicero De Fato, Alexander De Fato, Boethius Consolation V
- **Partial** for: Aristotle (NE, Met, De Interp, De Gen et Corr, Physics), Plato (Rep., Laws, Timaeus, Phaedrus, Phaedo), Augustine, Origen
- **Selection criteria:** relevance to free will, fate, moral responsibility; prioritized in P0/P1/P2/P3

### Q: Polytonic Greek and lemmatization?

- **UTF-8 storage** with full polytonic diacritics
- **Pre-computed lemmatization** via **OGA** (Open Greek and Latin Annotator) — no runtime NLP
- Dedicated tables:
  - `oga_tokens`: word-level morphological analysis (`surface_form`, `lemma`, `pos`, `morphology JSONB`, `cts_urn`)
  - `oga_dependencies`: syntactic tree (Universal Dependencies: `nsubj`, `obj`, `amod`, etc.)
  - `passages.morphology`: passage-level JSONB cache (format `[{"l": "<lemma>"}]`) for lemmatic search
- `ancient_works.has_morphology` flag indicates processed works
- **No CLTK, spaCy, or Stanza** — everything is pre-computed, imported as data

---

## 2. KNOWLEDGE GRAPH & ONTOLOGY

### Q: How did you define your ontology?

**Hybrid top-down / bottom-up approach:**
- Formal ontology in `knowledge graph/ontology/` (JSON, version 3.0.0)
- **22 node types:** person, concept, argument, work, school, passage, debate, position, event, institution, text_fragment, modern_interpretation, term, source_collection, doctrine, publication, quote, synthesis, controversy, conceptual_evolution, group, argument_framework
- **56 relation types** in **12 categories:** Argumentative (argues_for/against, refutes, responds_to, supports, critiques), Intellectual (influences, taught_by, student_of, extends), Affiliation (belongs_to_school, member_of, founded), Authorship (wrote, authored_by, created_by), Citation (cites, source_for, evidenced_by), Textual (preserves, preserved_in), Structural (contains, part_of, translation_of), Semantic (discusses, defines, related_to, contrasts_with, employs, presupposes), Doctrinal (holds_position, endorses, rejects), Debate (participates_in, contributes_to), Hermeneutic (interprets, represents, exemplifies), Temporal (contemporary_of, precedes, follows)

### Q: Who validates the relations?

- **Initial phase:** semi-automatic import + manual validation
- **Automated audit** (`scripts/audit_kg_quality.py`) runs continuously:
  - Ontological constraints (`source_types`/`target_types` per relation)
  - Orphan/isolated nodes, self-loops, exact duplicates
  - Near-duplicates (Jaccard tokens ≥ 0.8 AND SequenceMatcher ≥ 0.8)
  - Assertion nodes without textual evidence (regex on assertive language)
  - Ontological drift (unknown types, invalid periods)
  - Formatting artifacts (markdown, underscores, inconsistent prefixes)
- **12 manual correction phases** documented (Phases 0-12), including:
  - 6 major misattribution fixes (DL passages → Diogenes Laertius, Pseudo-Plutarch, Porphyry, etc.)
  - Systematic qualification of 41 anachronistic labels ("compatibilism" → "what modern scholars term...")
  - 229 nodes cleaned of ALL CAPS, 68 passages cleaned of HYPERLINK artifacts
  - 3 duplicates merged, 4 reversed edges fixed

### Q: Confidence scores?

- `passage_citations` table: `confidence DOUBLE PRECISION CHECK 0.0-1.0`
- Values assigned by source:
  - Direct quote found: **1.0**
  - KG-backed claim: **0.7**
  - Metadata summary: **0.6**
  - Generic passage (fallback without facets): **0.65**
  - Insufficient evidence: **0.45**
  - Auto-linked (Phase 8): recalibrated to **0.5**
- Partial index on `confidence >= 0.7` for frequent queries
- GraphRAG pipeline sorts by `confidence DESC` then `sequence_number`

### Q: FAIR interoperability? RDF/OWL?

**What exists:**
- **Zenodo DOI:** `10.5281/zenodo.17379489` (concept DOI, rolling archive)
- **CTS URNs** throughout (Perseus/TLG/PHI standard)
- **CodeMeta 2.0** (`docs/codemeta.json`) — valid JSON-LD with `@context: "https://doi.org/10.5063/schema/codemeta-2.0"`
- **CITATION.cff** (CFF 1.2.0)
- **ORCID:** `0000-0002-5310-5346`
- **CC BY 4.0**

**What does not exist yet:**
- No native RDF/OWL/Turtle export of the KG — the CLI has a stub `--format rdf` that prints "not yet implemented"
- Ontology is in JSON, not OWL/RDFS
- No CIDOC-CRM mapping

**Honest answer:** The JSON ontology is designed to be convertible to OWL (types, source/target constraints are documented). RDF export is on the roadmap. CodeMeta is already valid JSON-LD. Current priority is corpus completeness and data quality.

---

## 3. AI & GRAPHRAG

### Q: Why Gemini?

- **1M token context** — allows sending the FULL context without truncation (budget: 850k tokens available after 15% reserve)
- **Primary model:** `gemini-3.1-pro-preview` (30 req/min)
- **Fallback chain (normal mode):** Gemini → Kimi (`kimi-latest`, 20 req/min) → OpenRouter (`google/gemini-3-flash-preview`, 60 req/min)
- **Fallback chain (thinking mode):** Gemini → OpenRouter → Kimi (for extended reasoning)
- **Gemini prompt caching:** SHA-256 cache key, 15 min TTL, minimum threshold 4096 tokens (pro) / 1024 (flash) — reduces costs on repeated queries
- **Embedding:** `models/gemini-embedding-001` (3072 dimensions, Matryoshka Representation Learning)

### Q: How do you prevent hallucinations?

**Zero-tolerance policy + technical controls:**

1. **No ancient text generation** — absolute rule in system instructions
2. **Grounded pipeline** — the LLM synthesizes ONLY from passages actually retrieved from the database
3. **Programmatic verification** (`ProgrammaticVerify` FSM node) — no LLM call, pure verification:
   - Every citation in the answer is validated against actual `passage_citations` + `passages`
   - `ScholarlyAnswer` built with verified references only
4. **Claim Ledger** — each assertion is decomposed into claims with confidence scores (0.0-1.0), linked to specific evidence bundles
5. **Counter-evidence seeking** — dedicated node (`SeekCounterEvidence`) that actively searches for contradictory evidence
6. **Evidence sufficiency check** — multi-factor heuristic before synthesis: `0.12*bundles + 0.08*works + 0.1*counter + 0.08*facets`
7. **Continuous audit** — 143 nodes flagged `needs_evidence`, 63 modern nodes flagged as potentially out of scope

### Q: GraphRAG pipeline — full architecture?

**pydantic-graph FSM, 12 active nodes:**

```
1.  ClassifyQueryType     → 5 types: specific_entity, global_abstract, multi_hop, comparative, temporal
                            Deterministic heuristic for SPECIFIC_ENTITY (conf=0.75), otherwise LLM (temp=0.0)

2.  ExpandQuery           → Expansion with Greek/Latin terms, philosophers, concepts, schools
                            Skipped for SPECIFIC_ENTITY/SIMPLE

3.  DiscoverCorpus        → Broad search: KG nodes + linked passages via Qdrant

4.  BuildResearchNotebook → Research framing (LLM)

5.  PlanReading           → Structured reading plan (LLM)

6.  TreeNavigateWorks     → Hierarchical navigation through the work tree index
                            Per work: LLM or heuristic section selection

7.  ExpandEvidenceBundles → Load passage bundles from selected sections

8.  SeekCounterEvidence   → Active counter-evidence search (LLM)
                            Skipped for SPECIFIC_ENTITY/SIMPLE

9.  EvidenceSufficiency   → Multi-factor heuristic score + optional LLM validation

10. DraftClaimLedger      → 6-12 structured claims, JSON schema enforced (temp=0.0)
                            Fast path if direct quote found (conf=1.0)

11. RenderGroundedAnswer  → Scholarly synthesis (temp=0.2) + optional polish (temp=0.1)
                            + compression repair if needed

12. ProgrammaticVerify    → Pure verification (ZERO LLM) → final ScholarlyAnswer
```

**LLM call count:**
- Simple (SPECIFIC_ENTITY): **1-2 calls** (DraftClaimLedger + RenderGroundedAnswer)
- Complex (COMPARATIVE/TEMPORAL): **up to 11 calls** (classification, expansion, framing, reading plan, navigation ×N, counter-evidence, sufficiency, claims, render, polish)

### Q: Embedding model? Performance on ancient Greek?

- **Model:** `models/gemini-embedding-001` (Google)
- **Dimensions:** 3072 (configurable via `EMBEDDING_DIMENSIONS`)
- **Distance:** Cosine (Qdrant)
- **Matryoshka Representation Learning** — allows truncating vectors to lower dimensions if needed

**Qdrant collections (6):**

| Collection | Usage |
|---|---|
| `kg_nodes_dual` | Production, named vector "gemini" (preferred) |
| `kg_nodes_gemini` | Legacy, fallback |
| `ancient_free_will_vectors` | Historical, fallback filtered by `node_id` |
| `text_embeddings` | Passage embeddings |
| `passages_contextual` | Passages re-embedded with contextual header (author/work/period) — **preferred** |
| `kg_edges` | Edge embeddings |

**Ancient Greek performance:** The Gemini model is multilingual and handles polytonic Greek. The `passages_contextual` collection improves results by adding context (author, work, period) before the Greek text during embedding, which disambiguates polysemous terms.

### Q: Hybrid search — how does it work?

**3 modes merged by Reciprocal Rank Fusion (RRF, k=60):**

1. **Full-text** (PostgreSQL): `to_tsvector('simple')` + `plainto_tsquery('simple')` + `ts_rank()` — `'simple'` config for language-agnostic matching of Greek/Latin
2. **Lemmatic:** JSONB query `passages.morphology @> '[{"l": "<lemma>"}]'` — searches the pre-computed morphological cache
3. **Semantic:** Gemini embedding of the query → Qdrant search → normalized scores

RRF formula: `score(d) = Σ 1/(k + rank_i(d))` — results present in multiple lists have their source concatenated (e.g., "fulltext, lemmatic").

Toggleable flags: `enable_fulltext`, `enable_lemmatic`, `enable_semantic` on `POST /search/hybrid`.

---

## 4. METHODOLOGY & ACADEMIC STANDARDS

### Q: How does a computer scientist ensure rigor?

1. **Systematic verification against sources** — library of PDFs, markdown, and text extractions (~50 major works: Bobzien 1998/2001, Dihle 1982, Frede 2011, Long & Sedley, etc.)
2. **Scholarly review phases** (Phases 9-11): node-by-node fact-check for Origen, Justin Martyr, then the 7 major philosophers (Epictetus, Chrysippus, Alexander, Epicurus, Augustine, Boethius, Cicero)
   - Concrete fixes: fabricated SC 290 reference removed (Justin), "explicitly citing Carneades" claim removed (Origen), dates corrected, anachronistic labels qualified
3. **Continuous automated audit** (`scripts/audit_kg_quality.py`) — 6 analysis dimensions
4. **Affiliation:** Université Côte d'Azur (CEPAM) + Université de Genève
5. **Published dataset:** Zenodo DOI `10.5281/zenodo.17379489`, CC BY 4.0, linked ORCID

### Q: Anachronistic labels — how do you flag them?

Dedicated Phase 12 — **41 nodes** where "compatibilism/incompatibilism" was presented as historical fact:
- Systematic pattern: "Stoic compatibilism" → "what modern scholars term Stoic compatibilism"
- "soft/hard determinism" qualified as modern terminology
- 8 priority claims hedged: "First systematic" → "Often considered the first systematic"
- 1 superlative softened: "was the most important" → "is widely regarded as the most important"
- 1 assertion corrected: "This proves that" → "This is taken to show that"

### Q: Does the KG encode interpretations or facts?

**Explicit distinction in the ontology:**
- `modern_interpretation` type dedicated to scholarly interpretations (with `interpreter`, `publication_year`)
- `publication` type for modern works (with `key_claim`, `zotero_key`)
- `interprets` / `interpreted_by` relations to link interpretation → source
- **Dual-layer structure:** primary layer (ancient sources) vs. secondary layer (modern reception: Bobzien, Frede, Kane, etc.)
- Graduated confidence: auto-linked citations at 0.5, manually verified citations at 0.7-1.0

---

## 5. TECHNICAL INFRASTRUCTURE

### Q: Deployment architecture?

**3 modes:**

| Mode | Stack | Usage |
|---|---|---|
| **Local** | Docker Compose (PostgreSQL 16-alpine, Qdrant 1.13.3, FastAPI, Nginx) | Development |
| **Production Docker** | Supabase (pgbouncer:6543, SSL) + Qdrant Cloud + Docker backend/frontend | Staging |
| **Production live** | **Cloudflare Workers** (Hono, TypeScript) + Supabase + Qdrant Cloud | `free-will.app` |

**Docker Compose:**
- 4 core services + 3 optional (pgAdmin 8, Prometheus 2.51, Grafana 10.4)
- Isolated networks: `internal` (bridge, no external access), `frontend` (backend+frontend), `monitoring`
- Security: `read_only: true`, `no-new-privileges`, tmpfs for `/tmp`
- Memory limits: Postgres 1G, Qdrant 2G, Backend 1G/2CPU, Frontend 256M/1CPU

**Cloudflare Workers (production):**
- Hono framework, full TypeScript services: GraphRAG agentic/hierarchical/workflow, KG, cache, auth
- Agents: planning, reasoning (enhanced), refinement, verification, citation-mapper

### Q: CI/CD?

**GitHub Actions** (`ci.yml`) on push/PR to `main`:
- `lint`: Ruff (linter + formatter) on all 3 Python packages
- `typecheck`: mypy
- `test-database` / `test-kg` / `test-graphrag`: separate pytest runs
- `test-frontend`: ESLint + Vitest + `npm run build`
- `docker`: image builds (after lint+typecheck)

**Publishing** (`publish.yml`): PyPI via trusted publishing (OIDC, no password)

### Q: How to reproduce the setup?

1. `git clone` + `cp .env.example .env` + add API key(s)
2. `docker compose -f deploy/docker-compose.yml up`
3. Full dataset on Zenodo (`10.5281/zenodo.17379489`)
4. **Gap:** Qdrant embeddings are not in the Zenodo dataset — must re-embed with `scripts/reembed_kg_nodes.py` (requires a Gemini key)

---

## 6. FRONTEND & VISUALIZATION

### Q: Frontend stack?

- **React 19.1** + **TypeScript 5.9** + **Vite 7.1**
- **Cosmograph** (2D graph visualization, GPU-accelerated)
- **Three.js / React Three Fiber** (3D semantic embedding space)
- **D3.js 7** (timelines, charts)
- **Framer Motion 12** (animations)
- **Radix UI + Tailwind CSS** (UI components)
- **i18next:** 5 languages (EN, FR, DE, IT, EL), detection via localStorage → navigator → htmlTag
- **Accessibility:** axe-core integrated

### Q: Code splitting?

6 manual chunks in Vite: `cosmograph-vendor`, `three-vendor`, `charts-vendor`, `animation-vendor`, `react-vendor`, `ui-vendor`

---

## 7. POTENTIAL SYNERGIES WITH ATLOMY

### Direct textual overlap

| Text | EleutherIA | ATLOMY |
|---|---|---|
| **Galen, De Placitis** (De Plac. Hipp. et Plat.) | 3 passages ingested | Central anatomical source |
| **Aristotle, De Anima** | KG nodes + passages | Physiology of perception |
| **Aristotle, De Gen. et Corr.** | 69 passages (Scaife) | Theory of elements/body |
| **Hippocratic corpus** | Fragmentary references | Foundational source for ATLOMY |
| **Galen** (other treatises) | References in the KG | Core of the ATLOMY project |

### Thematic bridges

1. **Physiological determinism in Galen** — the relationship between bodily constitution and free will (De Plac. = direct bridge)
2. **Soul and body in the Stoics** — pneuma, tonos, hegemonikon: concepts shared between anatomy and moral philosophy
3. **Aristotle De Anima** — perception, desire, prohairesis: from anatomy to ethics
4. **Alexander of Aphrodisias** — commentator on Aristotle's De Anima AND author of De Fato
5. **Shared technical lexicon** — Greek terms in common: ψυχή, πνεῦμα, ἡγεμονικόν, αἴσθησις, ὄρεξις

### Technical complementarity

| ATLOMY | EleutherIA | Possible synergy |
|---|---|---|
| 3D anatomical atlas | Philosophical knowledge graph | Integrated visualization: click on an organ → see associated philosophical debates |
| Structured anatomical lexicon | OGA lemmatization + hybrid search | Cross-enrichment of lexicons |
| TEI-XML (presumably) | CTS URNs + PostgreSQL | Interoperable standards |
| Focus text → 3D image | Focus text → knowledge graph | Two modalities of "augmented reading" |

### Concrete proposal

- **Data exchange:** if ATLOMY has a structured lexicon of Greek anatomical terms, it could enrich EleutherIA's `term` nodes for psycho-physiological concepts
- **Galen De Placitis as pilot project:** this text sits at the exact intersection of both projects (brain anatomy AND free will)
- **Common standard:** CTS URNs for textual references, potential convergence toward a shared RDF/LOD export

---

## 8. KEY FIGURES (cheat sheet)

| Metric | Value |
|---|---|
| KG nodes | 17,746 |
| KG edges | 42,925 |
| Node types | 22 |
| Relation types | 56 (12 categories) |
| Works | 487 |
| Passages | 69,277 |
| Passage-KG citations | 13,293 |
| Source languages | 5 (grc, lat, eng, hbo, ara) |
| UI languages | 5 (EN, FR, DE, IT, EL) |
| Temporal coverage | ~1,200 years (6th c. BCE → 6th c. CE) |
| Tests | 330+ (208 Python + 122 TypeScript) |
| Embedding dimensions | 3,072 (Gemini, cosine) |
| Max LLM context | 1M tokens (850k available) |
| Passage bundle budget | 552,500 tokens (65% of budget) |
| Qdrant collections | 6 |
| DOI | 10.5281/zenodo.17379489 |
| License | CC BY 4.0 |
| ORCID | 0000-0002-5310-5346 |
| Prod URL | https://free-will.app |

---

## 9. QUESTIONS TO ASK ATLOMY

1. Do you use CTS URNs or another textual referencing system?
2. Is your anatomical lexicon exportable in a structured format (JSON, CSV, RDF)?
3. Have you considered connecting anatomical terms to philosophical debates about the soul (De Anima, Stoic pneuma)?
4. What is your tech stack? (TEI-XML? Database? Search engine?)
5. Is the project open-source or do you plan to make it accessible?
6. Would you be interested in a pilot project on Galen De Placitis as an intersection of our two corpora?
