# Agent Skill Installation Guide

**Created**: 2025-10-21
**Skill Version**: 1.0.0

This project now includes an **Anthropic Agent Skill** that teaches Claude to be an expert in working with the EleutherIA Ancient Free Will Database.

---

## What Was Created

A complete Agent Skill at:
```
skills/ancient-philosophy-db/
├── SKILL.md                           # Main skill file (8.3 KB)
├── README.md                          # Skill documentation (10 KB)
├── controlled-vocabularies.md         # Node types, relations, periods (9.5 KB)
├── citation-standards.md              # Ancient source formats (9.1 KB)
├── terminology-conventions.md         # Greek/Latin rules (10 KB)
├── validation-checklist.md            # Quality assurance (10 KB)
└── query-examples.md                  # Database queries (15 KB)
```

**Total**: 7 files, ~72 KB of specialized knowledge

---

## What This Skill Does

When you work with Claude on database tasks, the skill automatically teaches Claude to:

1. **Maintain Academic Rigor** - Never hallucinate facts or citations
2. **Use Controlled Vocabularies** - Only valid node types, relations, periods, schools
3. **Preserve Terminology** - Keep Greek/Latin with proper transliterations
4. **Ensure FAIR Compliance** - Unique IDs, metadata, provenance
5. **Respect Historical Scope** - 4th c. BCE - 6th c. CE only
6. **Validate Data Quality** - Check citations, formats, schema compliance

---

## How It Works (Progressive Disclosure)

The skill follows Anthropic's **progressive disclosure** pattern:

### Level 1: Metadata (Always Loaded)
```yaml
name: Ancient Philosophy Database Expert
description: Specialist in maintaining and querying the EleutherIA ancient free will knowledge graph...
```

Claude reads this to decide if the skill is relevant to your request.

### Level 2: Core Instructions (Loaded When Relevant)
When you ask about the database, Claude loads `SKILL.md` containing:
- Core mission (academic rigor, no hallucination)
- Database structure overview
- Critical rules (IDs, vocabularies, citations)
- References to other files

### Level 3: Reference Files (Loaded On Demand)
Claude loads specific reference files only when needed:
- Creating a node → loads `controlled-vocabularies.md`
- Adding citations → loads `citation-standards.md`
- Handling Greek terms → loads `terminology-conventions.md`
- Validating content → loads `validation-checklist.md`
- Writing queries → loads `query-examples.md`

This keeps Claude's context efficient while providing deep expertise.

---

## Usage Examples

### Example 1: Query Assistance

**You**: "Find all Stoic philosophers in the database"

**Claude**:
1. Recognizes database query
2. Loads SKILL.md + query-examples.md
3. Provides Python code using controlled vocabulary
4. Validates "Stoic" is a valid school

### Example 2: Adding Content

**You**: "Add a concept node for 'autexousion'"

**Claude**:
1. Loads SKILL.md (recognizes modification)
2. Loads controlled-vocabularies.md (verifies "concept" type)
3. Loads terminology-conventions.md (Greek transliteration)
4. Loads citation-standards.md (asks for sources)
5. Loads validation-checklist.md (validates before creating)
6. Creates properly formatted node with citations

### Example 3: Validation

**You**: "Is this edge valid: {relation: 'invented'}?"

**Claude**:
1. Loads controlled-vocabularies.md
2. Checks "invented" against relation types
3. Reports: "❌ Use 'formulated' for concepts"

---

## Key Features

### No Hallucination Policy

Claude will **NEVER**:
- Invent ancient sources or citations
- Fabricate philosopher relationships
- Guess dates, schools, or affiliations
- Add content beyond 6th c. CE

Claude will **ALWAYS**:
- Cite ancient sources (Aristotle, NE III.1-5)
- Include modern scholarship (Bobzien 1998)
- Use `[uncertain]` for unknown data
- Ask for clarification when needed

### Controlled Vocabularies

**Node Types**: person, work, concept, argument, debate, controversy, reformulation, event, school, group, argument_framework, quote, conceptual_evolution

**Relation Types**: formulated, authored, influenced, refutes, supports, defends, opposes, transmitted, appropriates, reinterprets, develops, targets, employs, synthesizes, exemplifies, component_of, related_to, reformulated_as, centers_on, includes, structures, translates

**Periods**: Classical Greek, Hellenistic Greek, Roman Republican, Roman Imperial, Patristic, Late Antiquity

**Schools**: Peripatetic, Stoic, Epicurean, Academic, Platonist, Neoplatonist, Patristic, Presocratic

### Greek/Latin Preservation

All philosophical terms preserved in three forms:
```json
{
  "greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
  "latin_term": "in nostra potestate",
  "english_term": "in our power"
}
```

---

## Testing the Skill

### Test 1: Query the Database

Try asking Claude:
```
"Show me all Stoic philosophers in the database"
```

Claude should:
- Load the skill automatically
- Use correct controlled vocabulary
- Provide Python code from query-examples.md

### Test 2: Validate Content

Try asking Claude:
```
"Check if this node ID is valid: Person_Aristotle"
```

Claude should:
- Load validation-checklist.md
- Report format errors (wrong case, missing dates/hash)
- Suggest correct format: `person_aristotle_384_322bce_b2c3d4e5`

### Test 3: Handle Greek Terms

Try asking Claude:
```
"How should I format the Greek term eph' hêmin?"
```

Claude should:
- Load terminology-conventions.md
- Provide three-part format (original, transliteration, English)
- Show proper Unicode: `ἐφ' ἡμῖν (eph' hêmin)`

---

## When Claude Uses This Skill

The skill activates automatically when you:
- Query or analyze the ancient free will database
- Add, modify, or validate nodes/edges
- Search for concepts, persons, arguments
- Generate reports or visualizations
- Validate data quality or citations
- Perform GraphRAG operations
- Export or transform data

---

## Skill Architecture

### Why Progressive Disclosure?

Without progressive disclosure:
- 72 KB of skill content would always consume Claude's context
- Slower responses, less room for actual work
- Inefficient for simple queries

With progressive disclosure:
- Metadata (200 bytes) always loaded → fast relevance check
- Core instructions (8.3 KB) loaded when relevant
- Reference files (9-15 KB each) loaded only when needed
- Claude's context remains efficient

### File Purposes

| File | Size | Purpose | When Loaded |
|------|------|---------|-------------|
| SKILL.md | 8.3 KB | Core instructions, rules, overview | Any database task |
| controlled-vocabularies.md | 9.5 KB | Valid node types, relations, periods | Creating/validating nodes |
| citation-standards.md | 9.1 KB | Ancient source formats | Adding citations |
| terminology-conventions.md | 10 KB | Greek/Latin transliteration | Handling technical terms |
| validation-checklist.md | 10 KB | Quality assurance steps | Before modifications |
| query-examples.md | 15 KB | Python query patterns | Writing queries |
| README.md | 10 KB | Skill documentation | Reference/explanation |

---

## Integration with Existing Documentation

This skill **complements** your existing docs:

| Existing Doc | Purpose | Skill Equivalent |
|--------------|---------|------------------|
| CLAUDE.md | General instructions | SKILL.md (more structured) |
| DATA_DICTIONARY.md | Field definitions | controlled-vocabularies.md (extracted) |
| schema.json | JSON Schema validation | validation-checklist.md (includes validation) |
| examples/basic_queries.py | Sample code | query-examples.md (comprehensive) |

The skill extracts and organizes knowledge from these docs into Claude-optimized formats.

---

## Future Enhancements

Potential additions:
1. **Validation script** - Python tool to run validation checklist
2. **GraphRAG examples** - Specific semantic search patterns
3. **Export utilities** - Scripts for Cytoscape, Gephi, NetworkX
4. **Citation helper** - Tool to format citations automatically
5. **Terminology lookup** - Quick reference for Greek/Latin terms

---

## Maintenance

### Updating the Skill

When database structure changes:
1. Update relevant reference files
2. Keep SKILL.md in sync
3. Test with Claude
4. Update version number

### Version History

- **1.0.0** (2025-10-21) - Initial creation
  - Complete documentation suite
  - 7 reference files
  - Progressive disclosure architecture

---

## Benefits

### For You
- Claude automatically maintains academic standards
- No need to repeat instructions about citations
- Consistent Greek/Latin handling
- Faster database work with query templates

### For Collaborators
- Clear standards for data quality
- Comprehensive validation checklist
- Reference for citation formats
- Easy onboarding to database structure

### For Research
- FAIR compliance maintained automatically
- Academic rigor enforced
- Reproducible modifications
- Traceable provenance

---

## Resources

### Skill Documentation
- `skills/ancient-philosophy-db/README.md` - Complete skill guide
- `skills/ancient-philosophy-db/SKILL.md` - Core instructions

### Project Documentation
- `README.md` - Main project documentation
- `DATA_DICTIONARY.md` - Field definitions
- `CLAUDE.md` - General Claude instructions
- `schema.json` - JSON Schema

### Anthropic Resources
- [Agent Skills Blog Post](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Skills Documentation](https://www.anthropic.com/news/skills)

---

## Questions?

**About the skill**: See `skills/ancient-philosophy-db/README.md`
**About the database**: See `DATA_DICTIONARY.md` and `README.md`
**About ancient philosophy**: Contact Romain Girardi (romain.girardi@univ-cotedazur.fr)

---

**Last Updated**: 2025-10-21
**Maintained by**: Romain Girardi
**Skill Version**: 1.0.0
