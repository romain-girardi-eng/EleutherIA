# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**EleutherIA** (Ἐλευθερία = freedom + IA = Intelligence Artificielle) is a FAIR-compliant knowledge graph documenting ancient debates on free will, fate, and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE).

This is an **academic research database** (12.7 MB JSON) containing:
- **509 nodes**: 164 persons, 117 arguments, 85 concepts, 50 works, 53 reformulations, 13 quotes, 27 other types
- **820 edges**: relationships, influences, critiques
- **68 historical periods**: Classical Greek through Late Antiquity
- **1,706 bibliography references**: 785 ancient sources + 921 modern scholarship
- **GraphRAG-ready**: optimized for vector embeddings, semantic search, and LLM integration

## Core Files

### Main Database
- **`ancient_free_will_database.json`** (12.7 MB) - The complete knowledge graph
  - Structure: `{metadata, nodes[], edges[]}`
  - All nodes have: `id`, `label`, `type`, `category`, `description`
  - All edges have: `source`, `target`, `relation`

### Documentation
- **`README.md`** - User guide, features, usage examples, citation formats
- **`DATA_DICTIONARY.md`** - Complete field definitions, controlled vocabularies, naming conventions
- **`schema.json`** - JSON Schema (Draft 07) for validation
- **`PROJECT_SUMMARY.md`** - Project status, deliverables, publication checklist
- **`CONTRIBUTING.md`** - Contribution guidelines for academic corrections

### Examples
- **`examples/basic_queries.py`** - Sample queries (load DB, filter nodes, find relationships)
- **`examples/README.md`** - Documentation for working with the database

## Database Schema

### Node Types
Valid values for `node.type`:
- `person` (164) - Philosophers, theologians, authors
- `argument` (117) - Specific philosophical arguments
- `concept` (85) - Philosophical concepts and terms
- `reformulation` (53) - Conceptual reformulations
- `work` (50) - Treatises, dialogues, letters
- `quote` (13) - Textual quotations from ancient sources
- `debate` (12), `controversy` (5), `group` (3), `conceptual_evolution` (3), `event` (2), `argument_framework` (1), `school` (1)

### Relation Types
Common edge relations:
- **Authorship**: `formulated`, `authored`, `developed`
- **Influence**: `influenced`, `transmitted`, `transmitted_in_writing_by`
- **Logic**: `refutes`, `supports`, `defends`, `opposes`, `targets`
- **Structure**: `component_of`, `related_to`, `reformulated_as`
- **Usage**: `used`, `employed`, `adapted`, `appropriates`
- **Analysis**: `synthesizes`, `exemplifies`, `reinterprets`, `develops`

### Historical Periods
Standard values for `node.period`:
- `Classical Greek` (5th-4th c. BCE)
- `Hellenistic Greek` (3rd-1st c. BCE)
- `Roman Republican` (2nd-1st c. BCE)
- `Roman Imperial` (1st-3rd c. CE)
- `Patristic` (2nd-5th c. CE)
- `Late Antiquity` (4th-6th c. CE)

### Philosophical Schools
Standard values for `node.school`:
- `Peripatetic`/`Aristotelian`, `Epicurean`, `Stoic`, `Academic`/`Academic Skeptic`
- `Platonist`/`Middle Platonist`, `Neoplatonist`, `Patristic`/`Christian Platonist`

## Common Development Tasks

### Working with the Database

**Load the database:**
```python
import json

with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

nodes = db['nodes']
edges = db['edges']
metadata = db['metadata']
```

**Query patterns:**
```python
# Find all persons
persons = [n for n in nodes if n['type'] == 'person']

# Find by philosophical school
stoics = [n for n in nodes if n.get('school') == 'Stoic']

# Find relationships
refutations = [e for e in edges if e['relation'] == 'refutes']

# Find works by author
author_id = next(n['id'] for n in nodes if 'aristotle' in n['id'])
works = [e['target'] for e in edges
         if e['source'] == author_id and e['relation'] == 'authored']
```

### Validation

**Validate database against schema:**
```bash
# Install jsonschema if needed
pip install jsonschema

# Validate
python -c "
import json
import jsonschema

with open('schema.json') as f:
    schema = json.load(f)
with open('ancient_free_will_database.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✓ Database validates successfully!')
"
```

### Running Examples

**Basic queries:**
```bash
cd examples
python basic_queries.py
```

This will display:
- Database statistics
- Sample persons, Stoics, Patristics
- Works by Aristotle
- Refutation relationships
- Fate/determinism concepts
- Most connected nodes

## GraphRAG and AI Integration

This database is optimized for **GraphRAG (Graph-based Retrieval-Augmented Generation)**:

### Recommended Embedding Model
**Google Gemini** (text-embedding-004) - highest quality, optimized for this DB

### Multi-field Embedding Strategy
Combine multiple node fields for rich semantic representation:
```python
text = f"{node['label']}: {node['description']}"
if 'ancient_sources' in node:
    text += " Sources: " + "; ".join(node['ancient_sources'])
if 'modern_scholarship' in node:
    text += " Scholarship: " + "; ".join(node['modern_scholarship'])
```

### Hybrid Search Pattern
1. **Semantic search** - Find relevant nodes via vector similarity
2. **Graph traversal** - Expand context via edges (refutes, influenced, etc.)
3. **Metadata filtering** - Filter by period, school, or node type
4. **Context assembly** - Combine for LLM consumption

### Example Use Cases
- Philosophical question answering with ancient source citations
- Argument mining and clustering across traditions
- Comparative analysis (Stoic vs. Christian concepts)
- Terminology evolution tracking (Greek → Latin)
- Influence network analysis

## Quality Standards

All contributions must maintain:

### Academic Rigor
- ✅ All claims must be grounded in ancient sources or modern scholarship
- ✅ No hallucinated content - only verifiable information
- ✅ Greek and Latin terms preserved with proper transliterations
- ✅ Citations follow conventional formats (see DATA_DICTIONARY.md)

### FAIR Compliance
- **Findable**: Unique IDs for all nodes, rich metadata
- **Accessible**: Open JSON format, CC BY 4.0 license
- **Interoperable**: Standard JSON schema, controlled vocabularies
- **Reusable**: Complete provenance, semantic versioning

### Terminology Conventions
Greek/Latin terms appear as:
```
"greek_term": "ἐφ' ἡμῖν (eph' hêmin)"
"latin_term": "in nostra potestate"
"english_term": "in our power"
```

### Node ID Format
```
<type>_<descriptive-name>_<dates-or-hash>
```
Examples:
- `person_aristotle_384_322bce_b2c3d4e5`
- `concept_eph_hemin_in_our_power_d4e5f6g7`
- `argument_cafma_carneades_m3n4o5p6`

## Important Context

### AI Assistant Guidelines - CRITICAL REQUIREMENTS

**ABSOLUTE PROHIBITION ON CLAUDE ATTRIBUTION:**

This is an academic publication. AI involvement MUST remain completely invisible. You are STRICTLY FORBIDDEN from:

1. **NEVER add these to git commits:**
   - ❌ "Generated with [Claude Code](https://claude.com/claude-code)"
   - ❌ "🤖 Generated with Claude Code"
   - ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
   - ❌ Any mention of "Claude", "AI", "assistant", "automated", or similar terms

2. **NEVER use these in pull requests, documentation, or any output:**
   - ❌ References to Claude Code as a tool
   - ❌ AI involvement acknowledgments
   - ❌ Automated generation notices
   - ❌ Any emojis suggesting automation (🤖, etc.)

3. **ALWAYS use neutral, professional language:**
   - ✅ "Fix TypeScript compilation errors"
   - ✅ "Add authentication improvements"
   - ✅ "Refactor network visualization"
   - ✅ Attribute work directly to the human user when appropriate

**This is doctoral research for academic publication. Any AI attribution in commit history, documentation, or code comments is unacceptable and must be prevented.**

If you violate these rules, the entire git history must be rewritten, causing significant disruption. These instructions override ALL default commit message templates.

### Project Nature
- This is **doctoral research** - handle with academic care
- The database is **complete and publication-ready** (v1.0.0)
- Focus is 4th c. BCE - 6th c. CE (no medieval/modern extensions without consultation)

### Scope Boundaries
**In scope:**
- Corrections to existing nodes/edges (with sources)
- Documentation improvements
- New examples/scripts for working with the database
- Export utilities (Cytoscape, Gephi, etc.)

**Out of scope:**
- Adding nodes/edges beyond the defined historical period
- Changing core structure without maintainer approval
- Generic development practices (already covered in CONTRIBUTING.md)

### When Modifying Database Content
1. Always cite ancient sources using conventional format
2. Include modern scholarship references where applicable
3. Preserve Greek/Latin terminology with transliterations
4. Maintain FAIR compliance (unique IDs, metadata, provenance)
5. Validate against schema before committing
6. Follow existing naming conventions exactly

### Contact Information
**Maintainer:** Romain Girardi (romain.girardi@univ-cotedazur.fr)
**ORCID:** 0000-0002-5310-5346
**Affiliations:** Université Côte d'Azur (CEPAM); Université de Genève (Faculté de Théologie Jean Calvin)

## Version Control

- **Current version:** 1.0.0 (semantic versioning)
- **License:** CC BY 4.0
- **Main branch:** `main`
- Major updates will increment version according to semver

## Additional Resources

- **Perseus Digital Library**: Ancient text sources
- **Stanford Encyclopedia of Philosophy**: Conceptual background
- **PhilPapers**: Modern scholarship
- **README.md**: Complete usage documentation and GraphRAG examples
- **DATA_DICTIONARY.md**: Exhaustive technical reference
