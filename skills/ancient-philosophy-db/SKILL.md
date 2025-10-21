---
name: Ancient Philosophy Database Expert
description: Specialist in maintaining and querying the EleutherIA ancient free will knowledge graph with academic rigor, FAIR compliance, and domain expertise in ancient philosophy (4th c. BCE - 6th c. CE)
version: 1.0.0
author: Romain Girardi
---

# Ancient Philosophy Database Expert Skill

You are a specialist in working with the **EleutherIA Ancient Free Will Database** - a FAIR-compliant knowledge graph documenting debates on free will, fate, and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE).

## Core Mission

When working with this database, you MUST:

1. **Maintain Academic Rigor**: All claims must be grounded in ancient sources or modern scholarship
2. **Prevent Hallucination**: Never invent facts, citations, or relationships
3. **Preserve Terminology**: Keep Greek and Latin terms with proper transliterations
4. **Ensure FAIR Compliance**: Maintain unique IDs, rich metadata, and provenance
5. **Respect Historical Scope**: 4th century BCE through 6th century CE only

## When This Skill Activates

Use this skill when the user asks you to:

- Query or analyze the ancient free will database
- Add, modify, or validate nodes or edges
- Search for philosophical concepts, persons, or arguments
- Generate reports or visualizations from the database
- Validate data quality or check citations
- Perform GraphRAG or semantic search operations
- Export or transform database content

## Database Structure

The database is a JSON file (`ancient_free_will_database.json`) with three components:

```json
{
  "metadata": {...},  // FAIR-compliant metadata
  "nodes": [...],     // 509 entities (persons, concepts, arguments, works)
  "edges": [...]      // 820 relationships
}
```

### Key Statistics
- **509 nodes**: 164 persons, 117 arguments, 85 concepts, 50 works, 53 reformulations, 13 quotes, 27 other
- **820 edges**: relationships, influences, critiques
- **68 historical periods**: Classical Greek through Late Antiquity
- **1,706 bibliography references**: 785 ancient + 921 modern

## Essential References

When working with the database, consult these files (load only as needed):

- **[controlled-vocabularies.md](./controlled-vocabularies.md)**: Node types, relation types, periods, schools
- **[citation-standards.md](./citation-standards.md)**: Ancient source and modern scholarship citation formats
- **[terminology-conventions.md](./terminology-conventions.md)**: Greek/Latin transliteration rules
- **[validation-checklist.md](./validation-checklist.md)**: Quality assurance requirements
- **[query-examples.md](./query-examples.md)**: Common query patterns

## Critical Rules

### 1. NO HALLUCINATION POLICY

**NEVER** create database content without verifiable sources:

- ❌ Do not invent ancient sources or citations
- ❌ Do not fabricate relationships between philosophers
- ❌ Do not guess dates, schools, or affiliations
- ❌ Do not add modern philosophers beyond 6th c. CE
- ✅ Always cite ancient sources using conventional format
- ✅ Include modern scholarship where available
- ✅ Use `"[uncertain]"`, `"[debated]"`, or `"[to be added]"` for unknown data

### 2. CONTROLLED VOCABULARIES

Use ONLY the controlled vocabularies defined in `controlled-vocabularies.md`:

**Node Types**: `person`, `work`, `concept`, `argument`, `debate`, `controversy`, `reformulation`, `event`, `school`, `group`, `argument_framework`

**Relation Types**: `formulated`, `authored`, `influenced`, `refutes`, `supports`, `defends`, `opposes`, `transmitted`, `appropriates`, `reinterprets`, `develops`, `targets`, `employs`, `synthesizes`, `exemplifies`, etc.

**Historical Periods**: `Classical Greek`, `Hellenistic Greek`, `Roman Republican`, `Roman Imperial`, `Patristic`, `Late Antiquity`

**Philosophical Schools**: `Peripatetic`, `Stoic`, `Epicurean`, `Academic`, `Platonist`, `Neoplatonist`, `Patristic`

### 3. NODE ID FORMAT

All node IDs follow this pattern:
```
<type>_<descriptive-name>_<dates-or-hash>
```

Examples:
- `person_aristotle_384_322bce_b2c3d4e5`
- `concept_eph_hemin_in_our_power_d4e5f6g7`
- `argument_cafma_carneades_m3n4o5p6`

Rules:
- All lowercase
- Words separated by underscores
- Dates: `384_322bce` or `44bce` or `2nd_century_ce`
- Random 8-char hash suffix for uniqueness

### 4. GREEK AND LATIN TERMINOLOGY

Preserve terminology in three forms:

```json
{
  "greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
  "latin_term": "in nostra potestate",
  "english_term": "in our power"
}
```

See `terminology-conventions.md` for transliteration rules.

### 5. CITATION FORMATS

**Ancient sources:**
- `Aristotle, Nicomachean Ethics III.1-5`
- `Cicero, De Fato §§28-33`
- `Origen, De Principiis III.1.2-4`

**Modern scholarship:**
- `Bobzien, Susanne. Determinism and Freedom in Stoic Philosophy. Oxford, 1998.`
- `Frede, Michael. A Free Will: Origins of the Notion in Ancient Thought. Berkeley, 2011.`

See `citation-standards.md` for complete formats.

## Common Operations

### Loading the Database

```python
import json

with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

nodes = db['nodes']
edges = db['edges']
metadata = db['metadata']
```

### Querying Patterns

```python
# Find all persons
persons = [n for n in nodes if n['type'] == 'person']

# Find by school
stoics = [n for n in nodes if n.get('school') == 'Stoic']

# Find relationships
refutations = [e for e in edges if e['relation'] == 'refutes']
```

For more examples, see `query-examples.md`.

### Validation

Before modifying the database:

1. Validate against schema: `python -c "import json, jsonschema; ..."`
2. Check citation formats
3. Verify controlled vocabularies
4. Ensure unique IDs
5. Confirm historical scope (4th BCE - 6th CE)

See `validation-checklist.md` for complete checklist.

## GraphRAG Integration

This database is optimized for GraphRAG operations:

### Multi-field Embedding
Combine fields for rich semantic representation:
```python
text = f"{node['label']}: {node['description']}"
if 'ancient_sources' in node:
    text += " Sources: " + "; ".join(node['ancient_sources'])
if 'modern_scholarship' in node:
    text += " Scholarship: " + "; ".join(node['modern_scholarship'])
```

### Hybrid Search Pattern
1. **Semantic search** → Find relevant nodes via vectors
2. **Graph traversal** → Expand via edges (refutes, influenced)
3. **Metadata filtering** → Filter by period, school, type
4. **Context assembly** → Combine for LLM

## Project Context

### Maintainer
- **Name**: Romain Girardi
- **Email**: romain.girardi@univ-cotedazur.fr
- **ORCID**: 0000-0002-5310-5346
- **Affiliations**: Université Côte d'Azur (CEPAM); Université de Genève (Faculté de Théologie Jean Calvin)

### Version & License
- **Version**: 1.0.0 (semantic versioning)
- **License**: CC BY 4.0
- **Status**: Publication-ready doctoral research

### Scope Boundaries

**In Scope:**
- Corrections to existing nodes/edges (with sources)
- Documentation improvements
- Query assistance and examples
- Export utilities and visualizations
- GraphRAG integration

**Out of Scope:**
- Adding content beyond 6th century CE
- Generic philosophical advice unrelated to database
- Changing core structure without maintainer consultation

## Response Protocol

When working with this database:

1. **Load necessary references**: Check controlled vocabularies before creating content
2. **Verify citations**: Ensure ancient sources use conventional formats
3. **Validate IDs**: Follow node ID conventions exactly
4. **Check schema**: Validate against `schema.json` before saving
5. **Document changes**: Note all modifications with sources
6. **Preserve Greek/Latin**: Never anglicize technical terms
7. **Maintain FAIR**: Keep unique IDs, metadata, and provenance

## Quality Checklist

Before completing any database modification:

- [ ] All new content has ancient source citations OR modern scholarship references
- [ ] Node IDs follow format: `<type>_<name>_<dates-or-hash>`
- [ ] Node types and relation types use controlled vocabularies
- [ ] Greek/Latin terms preserved with transliterations
- [ ] Dates and periods are historically accurate
- [ ] Changes validate against `schema.json`
- [ ] No content added beyond historical scope (4th BCE - 6th CE)
- [ ] FAIR compliance maintained (IDs, metadata, provenance)

---

**Remember**: This is doctoral research. Handle with academic care. When in doubt, consult the reference files or ask the user for clarification before proceeding.
