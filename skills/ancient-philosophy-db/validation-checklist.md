# Database Validation Checklist

**Use this checklist BEFORE adding, modifying, or committing any database content.**

---

## Pre-Modification Checklist

### 1. Verify Source Grounding

- [ ] **Ancient sources cited** using conventional format (see `citation-standards.md`)
- [ ] **Modern scholarship referenced** where available (author + year minimum)
- [ ] **No hallucinated content** - all claims verifiable
- [ ] **Uncertain data marked** with `[uncertain]`, `[debated]`, or `c.` for dates

**Examples of ACCEPTABLE citations**:
```json
"ancient_sources": ["Aristotle, NE III.1-5", "Cicero, De Fato §§28-33"]
"modern_scholarship": ["Bobzien 1998", "Frede 2011"]
```

**Examples of UNACCEPTABLE**:
```json
"ancient_sources": []  // NO CITATIONS!
"description": "This philosopher probably thought..."  // GUESSING!
```

---

### 2. Check Controlled Vocabularies

Verify all values against `controlled-vocabularies.md`:

#### Node Types
- [ ] `type` field uses ONLY these values:
  - `person`, `work`, `concept`, `argument`, `debate`, `controversy`, `reformulation`, `event`, `school`, `group`, `argument_framework`, `quote`, `conceptual_evolution`

#### Relation Types
- [ ] `relation` field uses ONLY approved values:
  - Authorship: `formulated`, `authored`, `developed`
  - Influence: `influenced`, `transmitted`, `transmitted_in_writing_by`
  - Logic: `refutes`, `supports`, `defends`, `opposes`, `targets`
  - Usage: `appropriates`, `employs`, `used`, `adapted`
  - Analysis: `reinterprets`, `develops`, `synthesizes`, `exemplifies`
  - Structure: `component_of`, `related_to`, `reformulated_as`, `centers_on`, `includes`, `structures`, `translates`

#### Historical Periods
- [ ] `period` field (if used) is one of:
  - `Classical Greek`, `Hellenistic Greek`, `Roman Republican`, `Roman Imperial`, `Patristic`, `Late Antiquity`

#### Philosophical Schools
- [ ] `school` field (if used) is one of:
  - `Peripatetic`/`Aristotelian`, `Epicurean`, `Stoic`, `Academic`/`Academic Skeptic`, `Platonist`/`Middle Platonist`, `Neoplatonist`, `Patristic`/`Christian Platonist`, `Presocratic`

---

### 3. Validate Node ID Format

- [ ] **Follows pattern**: `<type>_<descriptive-name>_<dates-or-hash>`
- [ ] **All lowercase**
- [ ] **Words separated by underscores** (`_`)
- [ ] **Dates formatted correctly**: `384_322bce` or `44bce` or `2nd_century_ce`
- [ ] **Hash suffix** (8 alphanumeric chars) for uniqueness

**Valid Examples**:
```
person_aristotle_384_322bce_b2c3d4e5
concept_eph_hemin_in_our_power_d4e5f6g7
argument_cafma_carneades_m3n4o5p6
work_de_fato_cicero_44bce_a1b2c3d4
```

**Invalid Examples**:
```
Person_Aristotle  // Wrong case
aristotle-384-322  // Hyphens instead of underscores
person_aristotle  // Missing dates/hash
person_aristotle_384-322BCE  // Wrong date format
```

---

### 4. Check Greek/Latin Terminology

See `terminology-conventions.md` for complete rules:

- [ ] **Greek terms** use proper Unicode characters (ἐφ' ἡμῖν, not eph' hemin)
- [ ] **Transliterations** follow Modified ALA-LC standard
- [ ] **Long vowels** marked with macrons (ê, ô, â)
- [ ] **Three-part format** for concepts:
  ```json
  {
    "greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
    "latin_term": "in nostra potestate",
    "english_term": "in our power"
  }
  ```
- [ ] **Concept labels** follow pattern: `Transliteration (Original) - English`
  - Example: `Eph' hêmin (τὸ ἐφ' ἡμῖν) - In Our Power`

---

### 5. Verify Historical Scope

- [ ] **Content is within 4th c. BCE - 6th c. CE**
- [ ] No medieval philosophers (7th century CE onward)
- [ ] No modern philosophers or concepts
- [ ] Period-appropriate language (Greek → Latin → Syriac as appropriate)

**In Scope**:
- Aristotle (384-322 BCE) ✓
- Cicero (106-43 BCE) ✓
- Origen (c. 185-254 CE) ✓
- Boethius (c. 480-524 CE) ✓

**Out of Scope**:
- Anselm (1033-1109 CE) ✗
- Thomas Aquinas (1225-1274 CE) ✗
- Descartes (1596-1650) ✗

---

### 6. Validate Required Fields

#### All Nodes Must Have:
- [ ] `id` (string, unique, follows format)
- [ ] `label` (string, human-readable)
- [ ] `type` (enum, from controlled vocabulary)
- [ ] `category` (string, should be `"free_will"`)
- [ ] `description` (string, comprehensive, cited)

#### All Edges Must Have:
- [ ] `source` (string, valid node ID)
- [ ] `target` (string, valid node ID)
- [ ] `relation` (enum, from controlled vocabulary)

---

### 7. Check Optional Field Quality

#### For Person Nodes:
- [ ] `dates` in format: `384-322 BCE` or `c. 280 BCE`
- [ ] `school` from controlled vocabulary
- [ ] `period` from controlled vocabulary
- [ ] `position_on_free_will` if known
- [ ] `ancient_sources` array with citations
- [ ] `modern_scholarship` array with references

#### For Concept Nodes:
- [ ] `greek_term` and/or `latin_term` provided
- [ ] `english_term` standard scholarly translation
- [ ] `formulated_by` if known
- [ ] `ancient_sources` with where concept appears
- [ ] `related_concepts` array

#### For Argument Nodes:
- [ ] `formulated_by` person or school
- [ ] `source_text` citation where found
- [ ] `argument_type` classification
- [ ] `formal_structure` if applicable
- [ ] `ancient_sources` with primary text

---

### 8. Validate Edge Relationships

- [ ] **Source node exists** in database
- [ ] **Target node exists** in database
- [ ] **Relation is semantically correct**
  - Use `formulated` for concepts/arguments by persons
  - Use `authored` for works by persons
  - Use `refutes` for arguments against arguments
  - Use `influenced` for person-to-person
  - Use specific relation over generic `related_to`
- [ ] **Direction is correct** (source → target makes sense)
- [ ] **Ancient source cited** if relationship needs justification

**Example of well-formed edge**:
```json
{
  "source": "person_aristotle_384_322bce_b2c3d4e5",
  "target": "concept_eph_hemin_in_our_power_d4e5f6g7",
  "relation": "formulated",
  "description": "Aristotle formulated the concept of eph' hêmin in Nicomachean Ethics III",
  "ancient_source": "Aristotle, NE III.1-5"
}
```

---

### 9. Schema Validation

Before committing, validate against JSON schema:

```bash
python3 -c "
import json
import jsonschema

# Load schema
with open('schema.json', 'r') as f:
    schema = json.load(f)

# Load database
with open('ancient_free_will_database.json', 'r') as f:
    db = json.load(f)

# Validate
try:
    jsonschema.validate(db, schema)
    print('✓ Database validates successfully against schema!')
except jsonschema.ValidationError as e:
    print(f'✗ Validation error: {e.message}')
    print(f'  Path: {list(e.path)}')
"
```

- [ ] **Schema validation passes**
- [ ] No validation errors or warnings

---

### 10. FAIR Compliance Check

- [ ] **Findable**: Node has unique, descriptive ID
- [ ] **Accessible**: Content in open JSON format
- [ ] **Interoperable**: Uses controlled vocabularies, standard formats
- [ ] **Reusable**: Citations provide provenance, CC BY 4.0 license applies

---

## Node Creation Quick Reference

### Minimal Person Node
```json
{
  "id": "person_<name>_<dates>_<hash>",
  "label": "Full Name",
  "type": "person",
  "category": "free_will",
  "description": "Comprehensive description with historical context",
  "dates": "XXX-YYY BCE/CE",
  "period": "Classical Greek",
  "school": "Stoic",
  "ancient_sources": ["Primary source citation"],
  "modern_scholarship": ["Secondary source"]
}
```

### Minimal Concept Node
```json
{
  "id": "concept_<name>_<hash>",
  "label": "Transliteration (Original) - English",
  "type": "concept",
  "category": "free_will",
  "description": "Detailed explanation of concept",
  "greek_term": "Greek (transliteration)",
  "english_term": "English translation",
  "formulated_by": "Philosopher name",
  "ancient_sources": ["Where concept appears"]
}
```

### Minimal Edge
```json
{
  "source": "valid_node_id_1",
  "target": "valid_node_id_2",
  "relation": "formulated",
  "description": "Optional but recommended explanation",
  "ancient_source": "Citation if needed"
}
```

---

## Common Validation Errors

### ❌ ERROR: Missing Citations
```json
{
  "description": "Aristotle thought about free will",
  "ancient_sources": []  // NO!
}
```

**✓ FIXED**:
```json
{
  "description": "Aristotle developed the concept of voluntary action (hekousion)",
  "ancient_sources": ["Aristotle, NE III.1-5"]
}
```

---

### ❌ ERROR: Invalid Node Type
```json
{
  "type": "philosopher"  // Not in controlled vocabulary!
}
```

**✓ FIXED**:
```json
{
  "type": "person"  // Correct type
}
```

---

### ❌ ERROR: Wrong ID Format
```json
{
  "id": "Aristotle-384-322"  // Wrong case, hyphens
}
```

**✓ FIXED**:
```json
{
  "id": "person_aristotle_384_322bce_b2c3d4e5"
}
```

---

### ❌ ERROR: Invalid Relation
```json
{
  "relation": "created_by"  // Not in vocabulary!
}
```

**✓ FIXED**:
```json
{
  "relation": "formulated"  // Correct relation
}
```

---

### ❌ ERROR: Anglicized Terminology
```json
{
  "label": "What is up to us - Aristotle"  // Lost Greek!
}
```

**✓ FIXED**:
```json
{
  "label": "Eph' hêmin (τὸ ἐφ' ἡμῖν) - In Our Power",
  "greek_term": "τὸ ἐφ' ἡμῖν (to eph' hêmin)"
}
```

---

## Final Pre-Commit Checklist

Before saving changes to database:

1. [ ] All new nodes have complete required fields
2. [ ] All node IDs are unique and follow format
3. [ ] All relations use controlled vocabulary
4. [ ] All Greek/Latin preserved with transliterations
5. [ ] All content has ancient source citations OR modern scholarship
6. [ ] Historical scope is 4th BCE - 6th CE only
7. [ ] Schema validation passes
8. [ ] No hallucinated or invented content
9. [ ] FAIR compliance maintained
10. [ ] Documentation updated if needed

---

## When to Ask for Help

If ANY of these apply, consult the maintainer before proceeding:

- Need to add a new node type not in controlled vocabulary
- Need to add a new relation type not in list
- Uncertain about ancient source citation format
- Content is at edge of historical scope (close to 4th BCE or 6th CE)
- Major structural changes to database
- Unsure if scholarship is reliable

**Contact**: Romain Girardi (romain.girardi@univ-cotedazur.fr)

---

**Last Updated**: 2025-10-21
**Maintained by**: Romain Girardi
