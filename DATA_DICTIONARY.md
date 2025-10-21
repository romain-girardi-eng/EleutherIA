# Ancient Free Will Database: Data Dictionary

**Version 1.0.0 | October 17, 2025**

This data dictionary provides detailed documentation of all fields, data types, and controlled vocabularies used in the Ancient Free Will Database.

## Table of Contents

1. [Database Structure](#database-structure)
2. [Node Fields](#node-fields)
3. [Edge Fields](#edge-fields)
4. [Controlled Vocabularies](#controlled-vocabularies)
5. [Naming Conventions](#naming-conventions)
6. [Data Types](#data-types)

---

## Database Structure

The database follows a graph structure with three top-level components:

```json
{
  "metadata": {...},  // FAIR-compliant metadata
  "nodes": [...],     // Array of all entities
  "edges": [...]      // Array of all relationships
}
```

---

## Metadata Fields

### Core Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✓ | Full title of the database |
| `short_title` | string | ✓ | Abbreviated title |
| `version` | string | ✓ | Semantic version number (e.g., "1.0.0") |
| `date_created` | date | ✓ | Original creation date (YYYY-MM-DD) |
| `date_published` | datetime | ✓ | Publication timestamp (ISO 8601) |
| `language` | string | ✓ | Primary language code (ISO 639-1, e.g., "en") |

### Author Information

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `author.primary` | string | ✓ | Primary author name |
| `author.affiliation` | string | ✓ | Institutional affiliation |
| `author.email` | string | - | Contact email |
| `author.orcid` | string | - | ORCID identifier |

### License

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `license.type` | string | ✓ | License identifier (e.g., "CC BY 4.0") |
| `license.name` | string | ✓ | Full license name |
| `license.url` | URI | ✓ | Link to license text |
| `license.description` | string | ✓ | Human-readable license summary |

---

## Node Fields

### Required Fields (All Node Types)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | ✓ | Unique identifier | `person_aristotle_384_322bce_b2c3d4e5` |
| `label` | string | ✓ | Human-readable name | `Aristotle of Stagira` |
| `type` | enum | ✓ | Node type classification | `person` |
| `category` | string | ✓ | Topical category | `free_will` |
| `description` | string | ✓ | Comprehensive description | `Aristotle was...` |

### Node Type Enumeration

Valid values for `type` field:

- **`person`**: Individual philosophers, theologians, authors
- **`work`**: Treatises, dialogues, letters, commentaries
- **`concept`**: Philosophical concepts and technical terms
- **`argument`**: Specific philosophical arguments or positions
- **`debate`**: Major philosophical controversies or debates
- **`controversy`**: Specific disputes or polemics
- **`reformulation`**: Conceptual reformulations or reinterpretations
- **`event`**: Historical events relevant to free will debates
- **`school`**: Philosophical schools or movements
- **`group`**: Philosophical groups or circles
- **`argument_framework`**: Systematic argument structures

### Common Optional Fields (All Node Types)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `period` | string | - | Historical period | `Classical Greek`, `Hellenistic`, `Patristic` |
| `dates` | string | - | Dates (persons/works) | `384-322 BCE`, `c. 44 BCE` |
| `ancient_sources` | array[string] | - | Primary sources | `["Aristotle, NE III", "Cicero, De Fato 28"]` |
| `modern_scholarship` | array[string] | - | Secondary literature | `["Bobzien 1998", "Frede 2011"]` |
| `key_concepts` | array[string] | - | Associated concepts | `["hekousion", "prohairesis", "eph' hêmin"]` |

### Person-Specific Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `school` | string | - | Philosophical school | `Stoic`, `Peripatetic`, `Academic Skeptic` |
| `birth_place` | string | - | Place of birth | `Athens`, `Stagira` |
| `death_place` | string | - | Place of death | `Chalcis`, `Rome` |
| `role` | string | - | Historical role | `Founder of Lyceum`, `Third head of Stoa` |
| `major_works` | array[string] | - | Key writings | `["Nicomachean Ethics", "De Interpretatione"]` |
| `teachers` | array[string] | - | Teachers/influences | `["Plato"]` |
| `students` | array[string] | - | Students/followers | `["Alexander the Great", "Theophrastus"]` |
| `affiliations` | array[string] | - | Institutional ties | `["Lyceum (founder)"]` |
| `languages` | array[string] | - | Languages used | `["Greek"]` |
| `position_on_free_will` | string | - | Free will position | `Compatibilist/incompatibilist/other` |
| `historical_importance` | string | - | Legacy and influence | `Foundational for...` |

### Work-Specific Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `author` | string | - | Author name | `Aristotle` |
| `date` | string | - | Composition date | `c. 350 BCE` |
| `language` | string | - | Original language | `Greek`, `Latin` |
| `genre` | string | - | Literary genre | `dialogue`, `treatise`, `letter` |
| `key_passages` | array[string] | - | Important passages | `["Book III, chapters 1-5", "§§28-33"]` |
| `content_summary` | string | - | Work summary | `The work addresses...` |
| `transmission` | string | - | Textual transmission | `Survives in Greek manuscripts...` |
| `influence` | string | - | Historical influence | `Shaped medieval debates on...` |

### Concept-Specific Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `formulated_by` | string | - | Origin | `Aristotle`, `Stoics` |
| `greek_term` | string | - | Greek term | `ἐφ' ἡμῖν (eph' hêmin)` |
| `latin_term` | string | - | Latin equivalent | `in nostra potestate` |
| `english_term` | string | - | English translation | `in our power` |
| `relation_to_free_will` | string | - | Relevance | `Central to Aristotelian...` |
| `related_concepts` | array[string] | - | Related terms | `["hekousion", "prohairesis"]` |

### Argument-Specific Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `formulated_by` | string | - | Originator | `Carneades` |
| `source_text` | string | - | Primary source | `Cicero, De Fato §§28-33` |
| `argument_type` | string | - | Argument class | `compatibilist defense`, `incompatibilist critique` |
| `formal_structure` | array[string] | - | Logical structure | `["Premise 1: ...", "Premise 2: ...", "Conclusion: ..."]` |
| `philosophical_importance` | string | - | Significance | `Paradigmatic ancient...` |
| `position_in_debate` | string | - | Debate role | `Classic compatibilist argument` |

---

## Edge Fields

### Required Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `source` | string | ✓ | Source node ID | `person_aristotle_384_322bce_b2c3d4e5` |
| `target` | string | ✓ | Target node ID | `concept_eph_hemin_in_our_power_d4e5f6g7` |
| `relation` | enum | ✓ | Relationship type | `formulated` |

### Optional Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `description` | string | - | Relationship detail | `Aristotle formulated the concept of eph' hêmin in Nicomachean Ethics III` |
| `ancient_source` | string | - | Primary source | `Aristotle, NE III.1-5` |
| `type` | string | - | Edge classification | `conceptual`, `historical`, `polemical` |

---

## Controlled Vocabularies

### Relation Types

| Relation | Category | Description | Example |
|----------|----------|-------------|---------|
| `formulated` | Authorship | Created concept/argument | Aristotle → eph' hêmin |
| `authored` | Authorship | Wrote work | Cicero → De Fato |
| `developed` | Authorship | Elaborated concept | Stoics → heimarmenê |
| `influenced` | Influence | General influence | Plato → Aristotle |
| `transmitted` | Influence | Passed on ideas | Cicero → Latin philosophy |
| `transmitted_in_writing_by` | Influence | Textual transmission | Carneades → Cicero (via De Fato) |
| `refutes` | Logic | Critiques/rejects | Alexander → Chrysippus |
| `supports` | Logic | Endorses/defends | Stoics → heimarmenê |
| `defends` | Logic | Protects from critique | Chrysippus → compatibilism |
| `opposes` | Logic | Contradicts | Incompatibilism → compatibilism |
| `targets` | Logic | Aims critique at | CAFMA → Stoic fate |
| `appropriates` | Usage | Adopts for new purpose | Origen → Carneadean arguments |
| `employs` | Usage | Uses in argument | De Fato → CAFMA |
| `used` | Usage | Applied concept | Cicero → Greek terminology |
| `adapted` | Usage | Modified for context | Christians → Greek philosophy |
| `reinterprets` | Analysis | New interpretation | Stoics → eph' hêmin |
| `develops` | Analysis | Builds upon | Autexousion → eph' hêmin |
| `synthesizes` | Analysis | Combines elements | Boethius → ancient debates |
| `exemplifies` | Analysis | Represents position | Autexousion → libertarianism |
| `component_of` | Structure | Part of larger whole | Chapter → book |
| `related_to` | Structure | Generic relation | Concept A → concept B |
| `reformulated_as` | Structure | Reconceptualized | Greek term → Latin term |
| `centers_on` | Structure | Focuses on | Debate → concept |
| `includes` | Structure | Contains | Framework → argument |
| `structures` | Structure | Organizes | Debate → positions |
| `translates` | Structure | Linguistic translation | Greek → Latin |

### Historical Periods

**Note:** This database tracks ancient free will concepts (4th BCE - 6th CE) **and their reception history** through modern philosophy (Medieval - Contemporary).

Standard values for `period` field:

#### Ancient Periods (4th BCE - 6th CE) - Core Focus

- **Presocratic**: 6th-5th century BCE (Parmenides, Leucippus, Democritus)
- **Classical Greek**: 5th-4th century BCE (Socrates, Plato, Aristotle)
- **Hellenistic Greek**: 3rd-1st century BCE (Epicurus, Stoics, Skeptics)
- **Roman Republican**: 2nd-1st century BCE (Cicero, Lucretius)
- **Roman Imperial**: 1st-3rd century CE (Seneca, Epictetus, Marcus Aurelius, Philo, Alexander of Aphrodisias)
- **Patristic**: 2nd-5th century CE (Early Christian Fathers - Justin, Origen, Augustine)
- **Late Antiquity**: 4th-6th century CE (Neoplatonism, late Patristics, Boethius)

#### Medieval Periods (7th-15th c. CE) - Reception History

- **Early Medieval**: 7th-11th century CE (John of Damascus, Anselm, early Islamic philosophy)
- **High Medieval**: 12th-13th century CE (Thomas Aquinas, high Scholasticism)
- **Late Medieval**: 14th-15th century CE (Duns Scotus, Ockham, Buridan, late Scholasticism)

#### Early Modern Periods (15th-18th c. CE) - Reception History

- **Renaissance**: 15th-16th century CE (Erasmus, humanist debates)
- **Reformation**: 16th-17th century CE (Luther, Calvin, Protestant theology)
- **Counter-Reformation**: 16th-17th century CE (Molina, Suárez, Jansenism, De Auxiliis controversy)
- **Early Modern Rationalism**: 17th century CE (Descartes, Spinoza, Leibniz)
- **Early Modern Empiricism**: 17th-18th century CE (Hobbes, Locke, Hume, Reid)
- **Enlightenment**: 18th century CE (Kant, Wolff, Edwards)

#### Modern and Contemporary Periods (19th-21st c. CE) - Reception History

- **19th Century**: 1800-1900 CE (Schopenhauer, Mill, Nietzsche, James, Bergson)
- **20th Century Analytic**: 1900-2000 CE (Ayer, Strawson, Frankfurt, van Inwagen, Kane)
- **20th Century Continental**: 1900-2000 CE (Sartre, Camus, existentialism)
- **21st Century**: 2000-present (contemporary debates, neuroscience)

#### Special Categories

- **Second Temple Judaism**: c. 516 BCE - 70 CE (Dead Sea Scrolls, Philo, Biblical texts)
- **Rabbinic Judaism**: c. 70 CE - 600 CE (early rabbinic concepts)

### Philosophical Schools

Standard values for `school` field:

- **Peripatetic** / **Aristotelian**: Followers of Aristotle
- **Epicurean**: Followers of Epicurus
- **Stoic**: Stoic school (Early, Middle, Late Stoa)
- **Academic** / **Academic Skeptic**: Platonic Academy (esp. New Academy)
- **Platonist** / **Middle Platonist**: Platonic tradition (1st BCE - 3rd CE)
- **Neoplatonist**: Late Platonic tradition (3rd CE onward)
- **Patristic** / **Christian Platonist**: Early Christian thinkers
- **Presocratic**: Pre-Socratic philosophers

---

## Naming Conventions

### Node IDs

Node IDs follow this pattern:

```
<type>_<descriptive-name>_<dates-or-hash>
```

**Examples:**
- Person: `person_aristotle_384_322bce_b2c3d4e5`
- Work: `work_de_fato_cicero_44bce_b9c4e5d2`
- Concept: `concept_eph_hemin_in_our_power_aristotle_d4e5f6g7`
- Argument: `argument_cafma_carneades_m3n4o5p6`

**Rules:**
- All lowercase
- Words separated by underscores `_`
- Dates in format: `384_322bce` or `44bce` or `2nd_century_ce`
- Random hash suffix (8 chars) for uniqueness

### Labels

Human-readable names following these conventions:

- **Persons**: Full name, sometimes with epithet
  - `Aristotle of Stagira`
  - `Carneades of Cyrene`
  - `Origen of Alexandria`

- **Works**: Title, sometimes with author
  - `Nicomachean Ethics`
  - `De Fato - Cicero`
  - `Consolation of Philosophy Book V - Boethius`

- **Concepts**: Descriptive name, often with Greek/Latin term
  - `Eph' hêmin (τὸ ἐφ' ἡμῖν) - In Our Power`
  - `Heimarmenê (Εἱμαρμένη) - Stoic Fate`
  - `Autexousion (Αὐτεξούσιον) - Christian Free Will`

- **Arguments**: Descriptive name with originator
  - `Cylinder Analogy - Chrysippus`
  - `CAFMA: Carneadean Anti-Fatalist Moral Argumentation`
  - `Sea Battle Argument - Aristotle`

---

## Data Types

### Strings

- **Plain text**: Standard UTF-8 encoded strings
- **Greek text**: Unicode Greek characters (e.g., `ἐφ' ἡμῖν`)
- **Transliterations**: Latin alphabet with diacritics (e.g., `eph' hêmin`)
- **Dates**: Flexible format (e.g., `384-322 BCE`, `c. 200 CE`, `2nd century CE`)

### Arrays

- Arrays of strings for multiple values
- Empty arrays `[]` indicate "none" or "unknown"
- Order may be significant (e.g., chronological for `major_works`)

### Booleans

Not currently used in node/edge schemas (presence/absence of optional fields indicates true/false)

### Numbers

Used only in metadata statistics:
- `total_nodes`: integer
- `total_edges`: integer
- `node_types.<type>`: integer (count)

---

## Special Conventions

### Greek and Latin Terms

Greek and Latin terms are preserved with:
1. **Original script** (Greek: `ἐφ' ἡμῖν`, Latin: `liberum arbitrium`)
2. **Transliteration** (Greek: `eph' hêmin`, Latin: `liberum arbitrium`)
3. **English translation** (`in our power`, `free judgment`)

Example:
```
"greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
"latin_term": "in nostra potestate",
"english_term": "in our power"
```

### Citations

Citations follow conventional formats:

**Ancient sources:**
- `Aristotle, Nicomachean Ethics III.1-5`
- `Cicero, De Fato §§28-33`
- `Origen, De Principiis III.1.2-4`

**Modern scholarship:**
- `Bobzien, Susanne. Determinism and Freedom in Stoic Philosophy. Oxford, 1998.`
- `Frede, Michael. A Free Will: Origins of the Notion in Ancient Thought. Berkeley, 2011.`

### Unknown or Uncertain Information

- Use `"[uncertain]"`, `"[debated]"`, `"[to be added]"` for unknown data
- Use `c.` prefix for approximate dates: `"c. 280 BCE"`
- Use `"possibly"`, `"probably"` for uncertain attributions

---

## Validation

To validate data against the schema:

```bash
# Using Python jsonschema
pip install jsonschema
python -c "
import json
import jsonschema

with open('ancient_free_will_database_schema.json') as f:
    schema = json.load(f)
with open('ancient_free_will_database.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✓ Database validates successfully!')
"
```

---

**Document version:** 1.0.0
**Last updated:** October 17, 2025
**Maintained by:** Romain Girardi (romain.girardi@univ-cotedazur.fr)
**ORCID:** [0000-0002-5310-5346](https://orcid.org/0000-0002-5310-5346)
**Affiliation:** Université Côte d'Azur, CEPAM; Université de Genève, Faculté de Théologie Jean Calvin
