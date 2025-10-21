# Controlled Vocabularies Reference

**CRITICAL**: Use ONLY these controlled vocabularies when creating or modifying database content. These are the ONLY valid values for their respective fields.

## Node Types

Valid values for `node.type` (EXHAUSTIVE LIST):

| Type | Count | Description | Example |
|------|-------|-------------|---------|
| `person` | 164 | Philosophers, theologians, authors | Aristotle, Cicero, Origen |
| `argument` | 117 | Specific philosophical arguments | CAFMA, Sea Battle Argument |
| `concept` | 85 | Philosophical concepts and terms | eph' hêmin, heimarmenê |
| `reformulation` | 53 | Conceptual reformulations | Greek → Latin terminology |
| `work` | 50 | Treatises, dialogues, letters | Nicomachean Ethics, De Fato |
| `quote` | 13 | Textual quotations | Direct quotations from sources |
| `debate` | 12 | Major philosophical controversies | Fate vs. Free Will debate |
| `controversy` | 5 | Specific disputes or polemics | Academic vs. Stoic dispute |
| `group` | 3 | Philosophical groups or circles | Early Stoics |
| `conceptual_evolution` | 3 | Evolution of concepts over time | Development of autexousion |
| `event` | 2 | Historical events | Founding of Lyceum |
| `argument_framework` | 1 | Systematic argument structures | Modal logic framework |
| `school` | 1 | Philosophical schools | Stoicism |

**DO NOT** create nodes with types outside this list. If you need a new type, consult the maintainer.

---

## Relation Types (Edge Relations)

Valid values for `edge.relation` (EXHAUSTIVE LIST):

### Authorship Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `formulated` | Created concept/argument | Aristotle → eph' hêmin |
| `authored` | Wrote work | Cicero → De Fato |
| `developed` | Elaborated concept | Stoics → heimarmenê |

### Influence Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `influenced` | General influence | Plato → Aristotle |
| `transmitted` | Passed on ideas | Cicero → Latin philosophy |
| `transmitted_in_writing_by` | Textual transmission | Carneades → Cicero (via De Fato) |

### Logical Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `refutes` | Critiques/rejects argument | Alexander → Chrysippus |
| `supports` | Endorses/defends position | Stoics → heimarmenê |
| `defends` | Protects from critique | Chrysippus → compatibilism |
| `opposes` | Contradicts position | Incompatibilism → compatibilism |
| `targets` | Aims critique at | CAFMA → Stoic fate |

### Usage Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `appropriates` | Adopts for new purpose | Origen → Carneadean arguments |
| `employs` | Uses in argument | De Fato → CAFMA |
| `used` | Applied concept | Cicero → Greek terminology |
| `adapted` | Modified for context | Christians → Greek philosophy |

### Analysis Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `reinterprets` | New interpretation | Stoics → eph' hêmin |
| `develops` | Builds upon | Autexousion → eph' hêmin |
| `synthesizes` | Combines elements | Boethius → ancient debates |
| `exemplifies` | Represents position | Autexousion → libertarianism |

### Structural Relations
| Relation | Description | Example |
|----------|-------------|---------|
| `component_of` | Part of larger whole | Chapter → book |
| `related_to` | Generic relation | Concept A → concept B |
| `reformulated_as` | Reconceptualized | Greek term → Latin term |
| `centers_on` | Focuses on | Debate → concept |
| `includes` | Contains | Framework → argument |
| `structures` | Organizes | Debate → positions |
| `translates` | Linguistic translation | Greek → Latin |

**DO NOT** use relation types outside this list. Each relation has specific semantic meaning.

---

## Historical Periods

Valid values for `node.period`:

| Period | Timeframe | Key Figures | Description |
|--------|-----------|-------------|-------------|
| `Classical Greek` | 5th-4th c. BCE | Socrates, Plato, Aristotle | Classical Athens, founding of major schools |
| `Hellenistic Greek` | 3rd-1st c. BCE | Epicurus, Zeno, Chrysippus, Carneades | Hellenistic kingdoms, philosophical schools flourish |
| `Roman Republican` | 2nd-1st c. BCE | Cicero | Roman Republic, transmission to Latin |
| `Roman Imperial` | 1st-3rd c. CE | Seneca, Epictetus, Marcus Aurelius | Roman Empire, later Stoicism |
| `Patristic` | 2nd-5th c. CE | Origen, Tertullian, Augustine | Early Christian Fathers, integration with philosophy |
| `Late Antiquity` | 4th-6th c. CE | Neoplatonists, Boethius | Late Roman Empire, Neoplatonism, end of classical period |

**Note**: Some persons span multiple periods. Use the period of their most significant work on free will.

---

## Philosophical Schools

Valid values for `node.school`:

| School | Alternative Names | Period | Key Doctrines |
|--------|-------------------|--------|---------------|
| `Peripatetic` | `Aristotelian` | Classical → Hellenistic | Followers of Aristotle, moderate compatibilism |
| `Epicurean` | - | Hellenistic → Roman | Followers of Epicurus, atomic swerve, limited freedom |
| `Stoic` | `Early Stoa`, `Middle Stoa`, `Late Stoa` | Hellenistic → Roman Imperial | Fate (heimarmenê), compatibilism, determinism |
| `Academic` | `Academic Skeptic` | Hellenistic | Platonic Academy, skepticism, probabilism |
| `Platonist` | `Middle Platonist` | Roman (1st BCE - 3rd CE) | Platonic tradition, transcendent Forms |
| `Neoplatonist` | - | Late Antiquity (3rd CE →) | Late Platonic tradition, emanation, hierarchy |
| `Patristic` | `Christian Platonist` | Patristic → Late Antiquity | Early Christian thinkers, often influenced by Platonism |
| `Presocratic` | - | Archaic-Classical (6th-5th BCE) | Pre-Socratic philosophers (rare in this database) |

**Usage Notes**:
- Use `Stoic` as primary, specify `Early Stoa`, `Middle Stoa`, or `Late Stoa` in description if needed
- `Peripatetic` and `Aristotelian` are interchangeable
- `Academic` and `Academic Skeptic` are interchangeable
- `Patristic` and `Christian Platonist` may overlap; use context

---

## Categories

Valid values for `node.category`:

| Category | Description |
|----------|-------------|
| `free_will` | All nodes in this database use this category |

**Note**: This database focuses exclusively on free will, fate, and moral responsibility. All nodes should have `category: "free_will"`.

---

## Common Argument Types

For `argument` nodes, use these values for `argument_type`:

- `compatibilist defense` - Arguments defending compatibilism
- `incompatibilist critique` - Arguments against compatibilism
- `deterministic argument` - Arguments supporting determinism
- `libertarian argument` - Arguments for genuine free choice
- `modal argument` - Arguments using modal logic (necessity/possibility)
- `moral responsibility argument` - Arguments about moral accountability
- `conditional analysis` - Arguments analyzing conditional propositions
- `theological argument` - Arguments involving divine foreknowledge/providence

---

## Philosophical Positions on Free Will

For `person` nodes, use these values for `position_on_free_will`:

- `Compatibilist` - Accepts both determinism and free will
- `Incompatibilist` - Rejects compatibility of determinism and free will
- `Libertarian` - Affirms free will, denies determinism
- `Hard determinist` - Affirms determinism, denies free will
- `Skeptic` - Suspends judgment on free will
- `Synthesizer` - Attempts to synthesize multiple positions
- `[uncertain]` - Position unclear or debated

---

## Work Genres

For `work` nodes, use these values for `genre`:

- `treatise` - Systematic philosophical treatise
- `dialogue` - Platonic/Ciceronian dialogue
- `letter` - Philosophical letter or epistle
- `commentary` - Commentary on another work
- `doxography` - Collection of philosophical opinions
- `sermon` - Homily or sermon
- `handbook` - Manual or introductory text
- `fragment` - Surviving fragment

---

## Languages

For `node.language` or `node.languages`:

- `Greek` - Ancient Greek
- `Latin` - Classical/Late Latin
- `Syriac` - Syriac (rare in this database)
- `Hebrew` - Ancient Hebrew (rare in this database)

---

## Quality Markers for Uncertain Data

When data is uncertain or incomplete, use these standard markers:

- `[uncertain]` - Information is debated or unclear
- `[debated]` - Scholarly disagreement exists
- `[to be added]` - Information exists but not yet researched
- `c. <date>` - Approximate date (e.g., "c. 280 BCE")
- `possibly` - Tentative attribution
- `probably` - Likely but not certain
- `attributed to` - Traditional attribution, possibly incorrect

**Example**:
```json
{
  "dates": "c. 280-206 BCE",
  "birth_place": "[uncertain]",
  "position_on_free_will": "Compatibilist (debated)"
}
```

---

## Validation Rules

### When Creating Nodes:
1. `type` MUST be from node types list
2. `category` MUST be `"free_will"`
3. `period` SHOULD be from historical periods list (if applicable)
4. `school` SHOULD be from philosophical schools list (if applicable)

### When Creating Edges:
1. `relation` MUST be from relation types list
2. `source` and `target` MUST reference existing node IDs
3. Choose most specific relation (e.g., `refutes` over `related_to`)

### When in Doubt:
- Consult `DATA_DICTIONARY.md` for field definitions
- Check existing nodes for examples
- Ask maintainer if new vocabulary is needed
- Use generic relation (`related_to`) rather than inventing new ones

---

**Last Updated**: 2025-10-21
**Source**: Extracted from `DATA_DICTIONARY.md` and `schema.json`
