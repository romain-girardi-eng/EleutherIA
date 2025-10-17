# EleutherIA - Ancient Free Will Database - Project Summary

**Version 1.0.0 | October 17, 2025**
**Status:** ✅ **COMPLETE AND READY FOR PUBLICATION**

---

## About the Name

**EleutherIA** is a bilingual wordplay:
- **Ἐλευθερία** (*eleutheria*) - Ancient Greek for "freedom/liberty"
- **IA** - Intelligence Artificielle (Artificial Intelligence)

This name captures the project's essence: ancient philosophical debates on freedom powered by modern AI.

---

## Project Overview

This project delivers a comprehensive, FAIR-compliant digital knowledge graph documenting ancient debates on free will, fate, and moral responsibility from Aristotle (4th c. BCE) to Boethius (6th c. CE). The database represents the first systematic digital mapping of ancient free will philosophy and theology, suitable for doctoral research, teaching, and interdisciplinary scholarship across philosophy, theology, classics, and digital humanities.

**EleutherIA** leverages cutting-edge **GraphRAG (Graph-based Retrieval-Augmented Generation)** techniques, making it ideal for modern AI applications including semantic search, vector embeddings, and LLM integration.

---

## Deliverables

### 1. **Main Database**

**File:** `ancient_free_will_database.json`
- **Size:** 13 MB
- **Format:** JSON (UTF-8)
- **License:** CC BY 4.0
- **Contents:**
  - 465 nodes (persons, works, concepts, arguments, debates)
  - 745 edges (relationships, influences, critiques)
  - FAIR-compliant metadata
  - Complete provenance information
  - 200+ bibliography references

### 2. **Documentation**

#### `ANCIENT_FREE_WILL_DATABASE_README.md` (11 KB)
Complete user guide including:
- Overview and key features
- Coverage (8 historical phases, major philosophical positions)
- Database structure and schemas
- FAIR compliance documentation
- Usage examples (Python, JavaScript)
- Citation formats (APA, BibTeX)
- License information (CC BY 4.0)
- Related resources and contact information

#### `ANCIENT_FREE_WILL_DATA_DICTIONARY.md` (14 KB)
Technical reference documentation:
- Complete field definitions
- Data types and formats
- Controlled vocabularies
- Naming conventions
- Node and edge schemas
- Greek/Latin term conventions
- Citation formats
- Validation procedures

#### `ancient_free_will_database_schema.json` (7 KB)
JSON Schema (Draft 07) for validation:
- Formal schema definition
- Required/optional field specifications
- Data type constraints
- Enumerated values
- Pattern validation
- Machine-readable documentation

---

## Database Statistics

### Nodes by Type

| Type | Count | Description |
|------|-------|-------------|
| person | 156 | Philosophers, theologians, authors |
| argument | 113 | Specific philosophical arguments |
| concept | 80 | Philosophical concepts and terms |
| reformulation | 53 | Conceptual reformulations |
| work | 48 | Treatises, dialogues, letters |
| controversy | 5 | Specific disputes |
| debate | 3 | Major philosophical controversies |
| group | 3 | Philosophical groups |
| event | 2 | Historical events |
| school | 1 | Philosophical schools |
| argument_framework | 1 | Systematic argument structures |
| **TOTAL** | **465** | |

### Edges

- **Total:** 745 relationships
- **Relation types:** 25+ (formulated, refutes, influenced, transmitted, etc.)
- **Average connections per node:** ~3.2

---

## Historical Coverage

### 8 Phases (4th BCE - 6th CE)

1. **Phase 1: Critical Foundations**
   - Cicero, Aristotle, Epicurus/Lucretius, Alexander of Aphrodisias
   - 24 nodes

2. **Phase 2: Plato, Socrates, Presocratics**
   - Platonic psychology, Socratic intellectualism, Democritean necessity
   - 8 nodes

3. **Phase 3: Stoicism**
   - Chrysippus, compatibilism, heimarmenê (fate)
   - 3 nodes

4. **Phase 4: Academic Skepticism**
   - Carneades, CAFMA, incompatibilism
   - 4 nodes

5. **Phase 5: Middle Platonism**
   - Alcinous, providence/fate distinction, soft determinism
   - 3 nodes

6. **Phase 6: Patristics**
   - Origen, Justin Martyr, autexousion (Christian free will)
   - 4 nodes

7-8. **Phases 7-8: Synthesis**
   - Boethius, terminology evolution (Greek → Latin), debate structure
   - 4 nodes

---

## Philosophical Positions Represented

### Major Traditions

✅ **Aristotelian Framework**
- Voluntary (hekousion), deliberation (bouleusis), eph' hêmin

✅ **Stoic Compatibilism**
- Universal fate + internal causation = responsibility
- Chrysippus' cylinder analogy

✅ **Epicurean Indeterminism**
- Atomic swerve (parenklisis/clinamen) breaks necessity

✅ **Academic Incompatibilism**
- Carneades' CAFMA: fate destroys freedom, justice, responsibility

✅ **Alexandrian Libertarianism**
- Self-initiated action, originating principle (archē)

✅ **Middle Platonist Synthesis**
- Providence ≠ fate; soft determinism

✅ **Christian Autexousion**
- Self-determining power, necessary for divine justice, theodicy

✅ **Boethian Solution**
- Divine eternity reconciles foreknowledge and freedom

---

## Key Features

### FAIR Compliance

**Findable:**
- Unique persistent identifier (DOI to be assigned)
- Rich metadata with keywords, descriptions, provenance
- Unique IDs for all 465 nodes
- Registered in research repositories (Zenodo, etc.)

**Accessible:**
- Open JSON format via HTTP/HTTPS
- Metadata always accessible
- CC BY 4.0 open license

**Interoperable:**
- Standard JSON format with formal schema
- Controlled vocabularies (Greek/Latin terms, relation types)
- Links to external resources (Perseus, Stanford Encyclopedia, PhilPapers)

**Reusable:**
- Clear CC BY 4.0 license
- Complete provenance documentation
- Semantic versioning (1.0.0)
- Domain-specific standards

### Quality Assurance

✅ All nodes include ancient source citations
✅ Modern scholarship references (200+ sources)
✅ Greek/Latin terminology preserved
✅ No hallucinated content - all claims grounded in sources
✅ Comprehensive descriptions
✅ Consistent naming conventions
✅ Schema validation

### AI Integration: GraphRAG

**EleutherIA** implements cutting-edge **GraphRAG (Graph-based Retrieval-Augmented Generation)** capabilities:

✅ **Google Gemini Embeddings**
- Optimized for Gemini text-embedding-004 (highest quality)
- Multi-field embeddings combining labels, descriptions, and sources
- 768-dimensional semantic vectors for all 465 nodes

✅ **Semantic Search**
- Find conceptually related arguments across philosophical schools
- Query by meaning rather than exact keywords
- Cross-lingual search (Greek/Latin/English)
- Discover implicit connections between traditions

✅ **Hybrid Graph + Vector Search**
- Combine graph traversal with semantic similarity
- Filter by period, school, or node type before semantic ranking
- Multi-hop relationship queries (e.g., "who refuted those influenced by Stoics?")

✅ **RAG Pipeline Integration**
- Structured context for LLM reasoning
- Navigate relationships: concepts → arguments → persons → works
- Compatible with LangChain, LlamaIndex, Haystack
- Metadata filtering and contextual retrieval

✅ **Use Cases**
- Philosophical question answering with citations
- Argument mining and clustering
- Comparative analysis across traditions
- Interactive research assistants
- Terminology evolution tracking
- Influence network analysis

**Why GraphRAG for Philosophy:**
- Preserves logical structure of arguments (refutes, supports, influenced)
- Maintains historical and conceptual context
- Combines semantic similarity with explicit relationships
- Enables multi-lingual reasoning with preserved Greek/Latin terminology

---

## Usage Scenarios

### Research Applications

1. **Doctoral Research**
   - Comprehensive primary and secondary source mapping
   - Systematic coverage of ancient positions
   - Network analysis of philosophical influences

2. **Teaching**
   - Course material on ancient free will debates
   - Visual knowledge graph exploration
   - Student assignments and projects

3. **Comparative Philosophy**
   - Ancient vs. modern free will debates
   - Cross-tradition analysis
   - Historical development tracking

4. **Digital Humanities**
   - Network analysis of philosophical ideas
   - Citation network studies
   - Conceptual evolution tracking

5. **Interdisciplinary Work**
   - Philosophy + theology + classics
   - History of ideas
   - Intellectual history

---

## Technical Specifications

### Format

- **Type:** JSON (JavaScript Object Notation)
- **Encoding:** UTF-8
- **Schema:** JSON Schema Draft 07
- **Version:** Semantic versioning (1.0.0)

### Structure

```
ancient_free_will_database.json
├── metadata (FAIR-compliant)
│   ├── title, version, dates
│   ├── author, license, citation
│   ├── description, keywords
│   ├── FAIR principles documentation
│   ├── data provenance
│   └── statistics
├── nodes (465 entities)
│   ├── Required: id, label, type, category, description
│   └── Optional: dates, sources, scholarship, etc.
└── edges (745 relationships)
    ├── Required: source, target, relation
    └── Optional: description, sources
```

### Validation

```bash
# Validate against schema
jsonschema -i ancient_free_will_database.json \
           ancient_free_will_database_schema.json
```

---

## Citation

### APA Format

> Girardi, R. (2025). *Ancient Free Will Database: A Comprehensive Knowledge Graph of Greco-Roman and Early Christian Debates on Freedom, Fate, and Moral Responsibility* (Version 1.0.0) [Data set]. https://doi.org/[to-be-assigned]

### BibTeX Format

```bibtex
@dataset{girardi2025ancient,
  author = {Girardi, Romain},
  title = {Ancient Free Will Database: A Comprehensive Knowledge Graph of Greco-Roman and Early Christian Debates on Freedom, Fate, and Moral Responsibility},
  year = {2025},
  version = {1.0.0},
  publisher = {[To be assigned]},
  doi = {[To be assigned]},
  url = {[To be assigned]},
  license = {CC BY 4.0}
}
```

---

## Next Steps for Publication

### Immediate Actions

1. ✅ **Database Creation** - COMPLETE
2. ✅ **Documentation** - COMPLETE
3. ✅ **Schema Definition** - COMPLETE
4. ✅ **FAIR Compliance** - COMPLETE

### Publication Preparation

5. ⏳ **DOI Assignment**
   - Upload to Zenodo or institutional repository
   - Obtain persistent identifier (DOI)
   - Update metadata with DOI

6. ⏳ **Institutional Information**
   - Add university affiliation
   - Add advisor acknowledgments
   - Add institutional contact information

7. ⏳ **Repository Publication**
   - Create GitHub repository (public)
   - Add version control
   - Enable issue tracking for corrections

8. ⏳ **Academic Announcement**
   - Announce on PhilPapers
   - Share on academic social media
   - Notify relevant research communities

### Future Enhancements

- **Version 1.1:** Add biographical details for persons
- **Version 1.2:** Add more Middle Platonist figures
- **Version 1.3:** Add late Neoplatonist developments
- **Version 2.0:** Extend to medieval period (Latin, Arabic, Byzantine)

---

## License

**CC BY 4.0** - Creative Commons Attribution 4.0 International

Users are free to:
- **Share** — copy and redistribute
- **Adapt** — remix, transform, build upon

Under these terms:
- **Attribution** — Must give appropriate credit

[https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)

---

## Contact

**Author:** Romain Girardi
**Email:** romain.girardi@univ-cotedazur.fr
**ORCID:** [0000-0002-5310-5346](https://orcid.org/0000-0002-5310-5346)
**Affiliation:** Université Côte d'Azur, CEPAM; Université de Genève, Faculté de Théologie Jean Calvin

**For questions:** romain.girardi@univ-cotedazur.fr
**For corrections:** Submit issues via GitHub repository or email romain.girardi@univ-cotedazur.fr
**For collaborations:** romain.girardi@univ-cotedazur.fr

---

## File Inventory

### Main Deliverables

| File | Size | Description |
|------|------|-------------|
| `ancient_free_will_database.json` | 13 MB | Main database (465 nodes, 745 edges) |
| `ANCIENT_FREE_WILL_DATABASE_README.md` | 11 KB | User guide and documentation |
| `ANCIENT_FREE_WILL_DATA_DICTIONARY.md` | 14 KB | Technical reference (fields, types, vocabularies) |
| `ancient_free_will_database_schema.json` | 7 KB | JSON Schema for validation |
| `ANCIENT_FREE_WILL_PROJECT_SUMMARY.md` | this file | Project overview and status |

### Supporting Files

| File | Size | Description |
|------|------|-------------|
| `create_fair_database.py` | 10 KB | Script to generate database from unified KG |
| `additions/phase*.json` | 8 files | Source files for each phase |
| `merge_phase*.py` | 7 files | Merge scripts for integration |

---

## Acknowledgments

This database was created as part of doctoral research on ancient free will debates at **Université Côte d'Azur (CEPAM)** and **Université de Genève (Faculté de Théologie Jean Calvin)**.

Special thanks to my doctoral advisors: **Arnaud Zucker** (CEPAM, Université Côte d'Azur) and **Andreas Dettwiler** (Faculté de Théologie Jean Calvin, Université de Genève), and to the research communities at both institutions.

---

**Project Status:** ✅ COMPLETE
**Ready for:** PhD submission, academic publication, open research sharing
**Disciplines:** Philosophy, Theology, Classics, Digital Humanities
**Last updated:** October 17, 2025
**Version:** 1.0.0
