# Data Dictionary

Schema reference for the EleutherIA database.

## Schema: `free_will`

### ancient_works

Canonical ancient texts with metadata.

| Column | Type | Description |
|--------|------|-------------|
| work_id | UUID | Primary key |
| canonical_id | TEXT | Unique identifier (e.g., `chrysippus_on_fate`) |
| title | TEXT | Work title |
| title_original | TEXT | Original Greek/Latin title |
| author | TEXT | Author name |
| author_original | TEXT | Original Greek/Latin author name |
| language | TEXT | Language code: `grc`, `lat`, `eng`, `hbo`, `ara` |
| period | TEXT | Historical period (e.g., `Hellenistic Greek`) |
| date_composed | TEXT | Approximate date (e.g., `3rd c. BCE`) |
| school | TEXT | Philosophical school |
| source | TEXT | Data source (perseus, tlg, sblgnt) |
| cts_urn | TEXT | Canonical Text Services URN |
| citation_levels | TEXT[] | Citation hierarchy (e.g., `['book', 'chapter']`) |
| has_morphology | BOOLEAN | Whether OGA lemmatization exists |
| total_words | INTEGER | Word count |
| created_at | TIMESTAMPTZ | Creation timestamp |

### passages

Hierarchical text units within works.

| Column | Type | Description |
|--------|------|-------------|
| passage_id | UUID | Primary key |
| work_id | UUID | Foreign key to ancient_works |
| canonical_ref | TEXT | Reference (e.g., `3.191`, `Matthew 5:3`) |
| cts_urn | TEXT | Full CTS URN for this passage |
| book | TEXT | Book identifier |
| chapter | TEXT | Chapter identifier |
| section | TEXT | Section identifier |
| sequence_number | INTEGER | Order within work |
| text_content | TEXT | Passage text |
| char_length | INTEGER | Character count |
| word_count | INTEGER | Word count |
| morphology | JSONB | Lemmatization data |
| created_at | TIMESTAMPTZ | Creation timestamp |

### passage_citations

Links between passages and knowledge graph nodes.

| Column | Type | Description |
|--------|------|-------------|
| citation_id | UUID | Primary key |
| passage_id | UUID | Foreign key to passages |
| kg_node_id | TEXT | Knowledge graph node ID |
| citation_type | TEXT | Type: `primary_source`, `secondary_source` |
| confidence | FLOAT | Confidence score (0.0-1.0) |
| notes | TEXT | Citation notes |
| created_at | TIMESTAMPTZ | Creation timestamp |

### kg_nodes

Knowledge graph nodes (concepts, persons, arguments).

| Column | Type | Description |
|--------|------|-------------|
| node_id | TEXT | Primary key (unique identifier) |
| label | TEXT | Display label |
| type | TEXT | Node type (Person, Concept, etc.) |
| description | TEXT | Full description |
| period | TEXT | Historical period |
| school | TEXT | Philosophical school |
| role | TEXT | Role (ancient_primary, modern_scholar) |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMPTZ | Creation timestamp |

### kg_edges

Knowledge graph edges (relationships).

| Column | Type | Description |
|--------|------|-------------|
| edge_id | UUID | Primary key |
| source_id | TEXT | Source node ID |
| target_id | TEXT | Target node ID |
| relation | TEXT | Relationship type |
| description | TEXT | Relationship description |
| weight | FLOAT | Edge weight |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMPTZ | Creation timestamp |

## Node Types (15)

| Type | Description | Example |
|------|-------------|---------|
| Person | Philosopher or scholar | Chrysippus |
| Concept | Philosophical concept | fate, determinism |
| Argument | Philosophical argument | lazy argument |
| Work | Text or book | On Fate |
| School | Philosophical school | Stoicism |
| Passage | Specific text passage | SVF 3.191 |
| Debate | Philosophical debate | fate vs free will |
| Position | Philosophical stance | compatibilism |
| Event | Historical event | Death of Chrysippus |
| Institution | Academy, Stoa | Platonic Academy |
| Text_Fragment | Fragment preserved elsewhere | Chrysippus fr. 1 |
| Modern_Interpretation | Scholarly interpretation | Bobzien's reading |
| Term | Technical term | to eph' hemin |
| Source_Collection | Collection like SVF | SVF |
| Doctrine | Formal doctrine | Stoic determinism |

### Two-Node Passage Architecture

Every passage has two KG nodes:

1. **Source node** — Original Greek/Latin text in `description`. Node ID: `passage_alex_fat_1`. `metadata.language`: `grc` or `lat`.
2. **Translation node** — English AI translation in `description`. Node ID: `passage_alex_fat_1_en`. `metadata.language`: `eng`, `metadata.source`: `ai_translation`.

The translation node links to the source via a `translation_of` edge. This keeps authoritative text untouched while making passages discoverable via English semantic search (Qdrant).

See [Passage Translation Architecture](../plans/2026-02-24-passage-translation-architecture.md) for full design.

## Edge Types (32)

See [kg/ontology/edge_types.json](../../kg/ontology/edge_types.json) for complete list.

Categories:
- **Argumentative:** argues_for, argues_against, refutes
- **Intellectual:** influences, influenced_by, taught_by
- **Affiliation:** belongs_to_school, founded
- **Authorship:** wrote, authored_by
- **Citation:** cites, cited_by
- **Semantic:** discusses, defines, related_to
- **Translation:** translation_of (English node → source node)

## Views

### passage_search

Lightweight view joining passages with work metadata.

```sql
SELECT passage_id, work_id, canonical_ref, text_content,
       title, author, language, period, school
FROM passage_search
WHERE to_tsvector('simple', text_content) @@ plainto_tsquery('simple', 'fate')
```

### works_statistics

Aggregate statistics for ancient_works.

### passages_statistics

Aggregate statistics for passages.

## Indexes

| Table | Index | Type | Columns |
|-------|-------|------|---------|
| passages | idx_passages_fulltext | GIN | to_tsvector(text_content) |
| passages | idx_passages_cts_urn | B-tree | cts_urn |
| passages | idx_passages_work_id | B-tree | work_id |
| ancient_works | idx_ancient_works_cts_urn | B-tree | cts_urn |
| ancient_works | idx_ancient_works_author | B-tree | author |
| passage_citations | idx_passage_citations_kg_node_id | B-tree | kg_node_id |
