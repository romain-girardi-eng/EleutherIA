# Ancient Philosophy Database Expert Skill

**Version**: 1.0.0
**Author**: Romain Girardi
**Created**: 2025-10-21

This is an Anthropic Agent Skill for working with the **EleutherIA Ancient Free Will Database** - a FAIR-compliant knowledge graph documenting debates on free will, fate, and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE).

---

## What This Skill Does

This skill teaches Claude to be an expert in:

1. **Maintaining Academic Rigor** - All claims grounded in ancient sources or modern scholarship
2. **Preventing Hallucination** - Never inventing facts, citations, or relationships
3. **Preserving Terminology** - Keeping Greek and Latin terms with proper transliterations
4. **Ensuring FAIR Compliance** - Maintaining unique IDs, rich metadata, and provenance
5. **Respecting Historical Scope** - 4th century BCE through 6th century CE only

---

## Skill Structure

```
skills/ancient-philosophy-db/
├── SKILL.md                           # Main skill file (loaded by Claude)
├── README.md                          # This file
├── controlled-vocabularies.md         # Node types, relations, periods, schools
├── citation-standards.md              # Ancient source & modern scholarship formats
├── terminology-conventions.md         # Greek/Latin transliteration rules
├── validation-checklist.md            # Quality assurance requirements
└── query-examples.md                  # Common database query patterns
```

### Progressive Disclosure

The skill follows Anthropic's **progressive disclosure** pattern:

1. **Metadata Layer** (SKILL.md frontmatter) - Claude reads this to determine relevance
2. **Core Instructions** (SKILL.md body) - Loaded when skill activates
3. **Reference Files** - Loaded only when Claude needs specific information

This keeps Claude's context window efficient while providing deep expertise when needed.

---

## When This Skill Activates

Claude will automatically invoke this skill when you:

- Query or analyze the ancient free will database
- Add, modify, or validate nodes or edges
- Search for philosophical concepts, persons, or arguments
- Generate reports or visualizations from the database
- Validate data quality or check citations
- Perform GraphRAG or semantic search operations
- Export or transform database content

---

## File Descriptions

### SKILL.md (Core Skill File)

The main skill file containing:
- YAML frontmatter with skill metadata
- Core mission and activation triggers
- Critical rules (no hallucination, controlled vocabularies, ID formats)
- Database structure overview
- References to supplementary files
- Quality checklist

**When Claude loads this**: When you ask about the ancient philosophy database

### controlled-vocabularies.md

**Exhaustive lists** of valid values for:
- Node types (person, work, concept, argument, etc.)
- Relation types (formulated, influenced, refutes, etc.)
- Historical periods (Classical Greek, Hellenistic, etc.)
- Philosophical schools (Stoic, Peripatetic, etc.)

**When Claude loads this**: When creating or validating nodes/edges

### citation-standards.md

**Standard formats** for:
- Ancient source citations (Aristotle, NE III.1-5)
- Modern scholarship citations (Bobzien 1998)
- Special cases (fragments, lost works, pseudo-epigrapha)
- Abbreviations (SVF, DK, LS)

**When Claude loads this**: When adding citations or verifying sources

### terminology-conventions.md

**Transliteration rules** for:
- Greek to Latin characters (Modified ALA-LC system)
- Three-part format (original script, transliteration, English)
- Key Greek terms (eph' hêmin, heimarmenê, prohairesis)
- Key Latin terms (liberum arbitrium, in nostra potestate)

**When Claude loads this**: When handling Greek/Latin philosophical terms

### validation-checklist.md

**Quality assurance** covering:
- Pre-modification checklist
- Required field validation
- Schema validation commands
- Common validation errors and fixes
- Final pre-commit checklist

**When Claude loads this**: Before modifying database content

### query-examples.md

**Python code examples** for:
- Loading and querying the database
- Finding nodes by type, school, period
- Traversing relationships
- Network analysis
- GraphRAG-style context expansion
- Export to CSV, NetworkX

**When Claude loads this**: When you ask how to query or analyze the database

---

## Usage Examples

### Example 1: Querying the Database

**User**: "Find all Stoic philosophers in the database"

**Claude**:
1. Loads SKILL.md (recognizes database query)
2. Loads query-examples.md (finds query pattern)
3. Loads controlled-vocabularies.md (verifies "Stoic" is valid school)
4. Executes query and returns results

### Example 2: Adding a New Node

**User**: "Add a new concept node for 'autexousion'"

**Claude**:
1. Loads SKILL.md (recognizes database modification)
2. Loads controlled-vocabularies.md (verifies "concept" is valid type)
3. Loads terminology-conventions.md (gets Greek transliteration rules)
4. Loads citation-standards.md (asks for ancient sources)
5. Loads validation-checklist.md (validates before creating)
6. Creates properly formatted node with citations

### Example 3: Validating Content

**User**: "Check if this edge is valid: {source: 'person_x', target: 'concept_y', relation: 'invented'}"

**Claude**:
1. Loads SKILL.md (recognizes validation request)
2. Loads controlled-vocabularies.md (checks if "invented" is valid relation)
3. Reports: "❌ 'invented' is not a valid relation. Use 'formulated' for concepts."

---

## Key Features

### No Hallucination Policy

Claude will **NEVER**:
- Invent ancient sources or citations
- Fabricate relationships between philosophers
- Guess dates, schools, or affiliations
- Add content beyond 6th century CE

Claude will **ALWAYS**:
- Cite ancient sources using conventional format
- Include modern scholarship where available
- Use `[uncertain]`, `[debated]` for unknown data
- Ask for clarification when information is missing

### Controlled Vocabularies

All node types, relation types, periods, and schools are **strictly controlled**. Claude will:
- Only use approved values from controlled-vocabularies.md
- Reject invalid types/relations
- Suggest corrections for common mistakes

### FAIR Compliance

All database modifications maintain:
- **Findable**: Unique, descriptive IDs
- **Accessible**: Open JSON format
- **Interoperable**: Controlled vocabularies, standard formats
- **Reusable**: Complete citations, CC BY 4.0 license

---

## Technical Details

### Database Format

- **Format**: JSON (12.7 MB)
- **Structure**: `{metadata, nodes[], edges[]}`
- **Nodes**: 509 (164 persons, 117 arguments, 85 concepts, etc.)
- **Edges**: 820 relationships
- **Schema**: `schema.json` (JSON Schema Draft 07)

### Node ID Format

```
<type>_<descriptive-name>_<dates-or-hash>
```

Examples:
- `person_aristotle_384_322bce_b2c3d4e5`
- `concept_eph_hemin_in_our_power_d4e5f6g7`
- `argument_cafma_carneades_m3n4o5p6`

### Required Node Fields

- `id` (unique identifier)
- `label` (human-readable name)
- `type` (from controlled vocabulary)
- `category` (always "free_will")
- `description` (comprehensive, cited)

### Required Edge Fields

- `source` (source node ID)
- `target` (target node ID)
- `relation` (from controlled vocabulary)

---

## Installation

This skill is already installed in your project at:
```
/Users/romaingirardi/Documents/Ancient Free Will Database/skills/ancient-philosophy-db/
```

Claude Code will automatically detect and load this skill when you work with the ancient philosophy database.

---

## Validation

To validate the database against schema:

```bash
cd "/Users/romaingirardi/Documents/Ancient Free Will Database"

python3 -c "
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

---

## Project Context

### Maintainer
- **Name**: Romain Girardi
- **Email**: romain.girardi@univ-cotedazur.fr
- **ORCID**: 0000-0002-5310-5346
- **Affiliations**: Université Côte d'Azur (CEPAM); Université de Genève (Faculté de Théologie Jean Calvin)

### Version & License
- **Database Version**: 1.0.0 (semantic versioning)
- **Skill Version**: 1.0.0
- **License**: CC BY 4.0
- **Status**: Publication-ready doctoral research

### Historical Scope
- **Period**: 4th century BCE - 6th century CE
- **In scope**: Aristotle, Stoics, Epicureans, Cicero, Origen, Augustine, Boethius
- **Out of scope**: Medieval (7th CE+), Modern philosophy

---

## Resources

### Project Documentation
- `README.md` - Main project documentation
- `DATA_DICTIONARY.md` - Complete field definitions
- `CLAUDE.md` - Instructions for Claude Code
- `schema.json` - JSON Schema for validation

### Examples
- `examples/basic_queries.py` - Sample queries
- `examples/network_analysis.py` - Network visualization
- `examples/export_cytoscape.py` - Export utilities

### External Resources
- **Perseus Digital Library**: http://www.perseus.tufts.edu
- **Stanford Encyclopedia of Philosophy**: https://plato.stanford.edu
- **PhilPapers**: https://philpapers.org

---

## Changelog

### Version 1.0.0 (2025-10-21)
- Initial skill creation
- Complete documentation suite
- Controlled vocabularies extracted
- Citation standards formalized
- Greek/Latin conventions documented
- Validation checklist created
- Query examples provided

---

## Contributing

To improve this skill:

1. Update relevant reference files (controlled-vocabularies.md, etc.)
2. Keep SKILL.md in sync with changes
3. Validate against actual database usage
4. Test with Claude to ensure progressive disclosure works
5. Document changes in this README

---

## Support

For questions about:
- **The skill**: Check this README and SKILL.md
- **The database**: See DATA_DICTIONARY.md and README.md
- **Ancient philosophy**: Contact Romain Girardi
- **Agent Skills**: See Anthropic's documentation at https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

---

**Last Updated**: 2025-10-21
**Maintained by**: Romain Girardi
