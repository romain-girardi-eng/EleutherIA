# EleutherIA v1.0.0 - Initial Release

**Release Date:** October 17, 2025

[![DOI](https://zenodo.org/badge/DOI/[ZENODO-DOI-HERE].svg)](https://doi.org/[ZENODO-DOI-HERE])

---

## 🎉 First Public Release

**EleutherIA** (Ἐλευθερία + IA) - The first comprehensive FAIR-compliant knowledge graph of ancient free will debates, combining ancient Greek philosophy with modern AI (GraphRAG) capabilities.

---

## 📊 Database Statistics

- **465 nodes** documenting persons, works, concepts, and arguments
- **745 edges** mapping relationships, influences, and critiques
- **8 historical phases** from Aristotle (4th c. BCE) to Boethius (6th c. CE)
- **200+ bibliography references** (ancient sources + modern scholarship)
- **~13 MB** JSON database file

---

## 🎯 Key Features

### Academic Content

- ✅ **Comprehensive coverage** of ancient free will debates
- ✅ **8 philosophical positions** documented in depth:
  - Aristotelian Framework (eph' hêmin)
  - Stoic Compatibilism (heimarmenê + internal causation)
  - Epicurean Indeterminism (atomic swerve)
  - Academic Incompatibilism (Carneades' CAFMA)
  - Alexandrian Libertarianism (self-originated action)
  - Middle Platonist Synthesis (providence ≠ fate)
  - Christian Autexousion (self-determining power)
  - Boethian Solution (divine eternity)

### FAIR Compliance

- ✅ **Findable:** Unique DOI, rich metadata, comprehensive keywords
- ✅ **Accessible:** Open JSON format, CC BY 4.0 license
- ✅ **Interoperable:** Standard JSON Schema, controlled vocabulary
- ✅ **Reusable:** Clear provenance, detailed documentation

### Modern AI Integration (GraphRAG)

- ✅ **Google Gemini embeddings** (text-embedding-004 optimized)
- ✅ **Semantic search** capabilities
- ✅ **Vector database** integration (Chroma, Qdrant, Pinecone, FAISS)
- ✅ **LangChain/LlamaIndex** compatible
- ✅ **RAG pipelines** ready for philosophical question answering

### Metadata Standards

- ✅ **CodeMeta 2.0** - Software/data metadata
- ✅ **CITATION.cff** - Academic citation format
- ✅ **JSON Schema** - Data validation
- ✅ **ORCID** - Author identification (0000-0002-5310-5346)

---

## 📦 What's Included

### Core Files

- `ancient_free_will_database.json` (13 MB) - Main database
- `schema.json` - JSON Schema validation
- `codemeta.json` - CodeMeta 2.0 metadata
- `CITATION.cff` - Citation metadata
- `LICENSE` - CC BY 4.0 license

### Documentation

- `README.md` - Project overview and quick start
- `DATA_DICTIONARY.md` - Complete field reference
- `BRANDING.md` - Logo usage guidelines
- `METADATA.md` - Metadata standards documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `RELATIONSHIP_TO_SEMATIKA.md` - Project separation documentation

### Examples & Assets

- `examples/basic_queries.py` - Python query examples
- `examples/README.md` - Usage guide
- `assets/branding/` - Logo files (SVG, PNG, PDF)

### Wiki

- Comprehensive 8-page wiki with tutorials
- GraphRAG integration guide
- Database schema reference
- Philosophical positions overview
- Citation guide

---

## 🚀 Getting Started

### Download

```bash
# Clone repository
git clone https://github.com/romain-girardi-eng/EleutherIA.git
cd EleutherIA
```

### Load Database (Python)

```python
import json

with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

nodes = db['nodes']  # 465 nodes
edges = db['edges']  # 745 edges

print(f"Loaded {len(nodes)} nodes and {len(edges)} edges")
```

### Generate Embeddings (Gemini)

```python
import google.generativeai as genai

genai.configure(api_key='YOUR_GEMINI_API_KEY')

for node in db['nodes']:
    text = f"{node['label']}: {node['description']}"
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"
    )
    node['embedding'] = result['embedding']
```

---

## 📚 Documentation

- **Wiki:** https://github.com/romain-girardi-eng/EleutherIA/wiki
- **Getting Started:** https://github.com/romain-girardi-eng/EleutherIA/wiki/Getting-Started
- **GraphRAG Guide:** https://github.com/romain-girardi-eng/EleutherIA/wiki/GraphRAG-Guide
- **API Reference:** See DATA_DICTIONARY.md

---

## 📖 Citation

### APA

> Girardi, R. (2025). *EleutherIA - Ancient Free Will Database: A Comprehensive Knowledge Graph of Greco-Roman and Early Christian Debates on Freedom, Fate, and Moral Responsibility* (Version 1.0.0) [Data set]. Zenodo. https://doi.org/[ZENODO-DOI-HERE]

### BibTeX

```bibtex
@dataset{girardi2025eleutheria,
  author = {Girardi, Romain},
  title = {EleutherIA - Ancient Free Will Database},
  year = {2025},
  version = {1.0.0},
  publisher = {Zenodo},
  doi = {[ZENODO-DOI-HERE]},
  url = {https://github.com/romain-girardi-eng/EleutherIA}
}
```

---

## 👨‍🎓 Author

**Romain Girardi**
- Email: romain.girardi@univ-cotedazur.fr
- ORCID: [0000-0002-5310-5346](https://orcid.org/0000-0002-5310-5346)
- Affiliations:
  - Université Côte d'Azur, CEPAM
  - Université de Genève, Faculté de Théologie Jean Calvin

**Doctoral Advisors:**
- Arnaud Zucker (CEPAM, Université Côte d'Azur)
- Andreas Dettwiler (Faculté de Théologie Jean Calvin, Université de Genève)

---

## 📊 Coverage

### Historical Periods

- Classical Greek (5th-4th c. BCE)
- Hellenistic Greek (3rd-1st c. BCE)
- Roman Imperial (1st-2nd c. CE)
- Patristic (2nd-6th c. CE)
- Late Antique (4th-6th c. CE)

### Philosophical Schools

- Peripatetic (Aristotelian)
- Stoic
- Epicurean
- Academic Skeptic
- Middle Platonist
- Neoplatonist
- Patristic/Christian

### Key Figures

Aristotle • Plato • Epicurus • Lucretius • Chrysippus • Carneades • Cicero • Alexander of Aphrodisias • Alcinous • Origen • Justin Martyr • Boethius

---

## 🔬 Use Cases

- **Doctoral research** in ancient philosophy/theology
- **GraphRAG applications** for philosophical question answering
- **Digital humanities** network analysis
- **Teaching** ancient philosophy courses
- **Comparative philosophy** across traditions
- **AI training data** for philosophical reasoning
- **Semantic search** across ancient arguments

---

## ⚖️ License

**CC BY 4.0** (Creative Commons Attribution 4.0 International)

You are free to:
- ✅ Share and redistribute
- ✅ Adapt and build upon
- ✅ Use commercially

Requirements:
- 📝 Provide proper attribution
- 📝 Indicate if changes were made

---

## 🙏 Acknowledgments

This database was created as part of doctoral research at Université Côte d'Azur (CEPAM) and Université de Genève (Faculté de Théologie Jean Calvin).

Special thanks to:
- Doctoral advisors: Arnaud Zucker and Andreas Dettwiler
- Research communities at both institutions
- Benjamin Mathias (Semativerse co-developer)

---

## 🔗 Links

- **Repository:** https://github.com/romain-girardi-eng/EleutherIA
- **Wiki:** https://github.com/romain-girardi-eng/EleutherIA/wiki
- **Issues:** https://github.com/romain-girardi-eng/EleutherIA/issues
- **Zenodo:** https://zenodo.org/[TO-BE-ASSIGNED]
- **DOI:** [TO-BE-ASSIGNED]

---

## 📅 Version History

### v1.0.0 (2025-10-17) - Initial Release

**Core Database:**
- 465 nodes across 8 historical phases
- 745 edges mapping relationships
- Complete ancient source citations
- 200+ modern scholarship references

**Features:**
- FAIR-compliant metadata
- GraphRAG capabilities with Gemini optimization
- CodeMeta 2.0 and CITATION.cff
- Comprehensive wiki documentation
- Vector database examples (Chroma, Qdrant, Pinecone)
- Professional branding (logo, visual identity)

**Documentation:**
- README with GraphRAG guide
- Complete data dictionary
- Database schema (JSON Schema)
- Example queries (Python)
- 8-page wiki with tutorials

---

## 🚧 Future Plans

**Version 1.1** (Planned):
- Additional biographical details for persons
- More Middle Platonist figures
- Extended bibliography

**Version 1.2** (Tentative):
- Late Neoplatonist developments
- Additional reformulation nodes

**Version 2.0** (Long-term):
- Extension to medieval period (tentative)

---

## 🐛 Known Issues

None reported for v1.0.0.

Report issues at: https://github.com/romain-girardi-eng/EleutherIA/issues

---

## 📬 Contact

Questions, corrections, or collaborations:
- Email: romain.girardi@univ-cotedazur.fr
- GitHub Issues: https://github.com/romain-girardi-eng/EleutherIA/issues

---

**EleutherIA v1.0.0** - Ancient Philosophy × Modern AI

*Ἐλευθερία (freedom) + IA (Intelligence Artificielle)*
