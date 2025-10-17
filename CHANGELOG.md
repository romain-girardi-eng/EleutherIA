# Changelog

All notable changes to the EleutherIA Ancient Free Will Database will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-17

### Added
- **Initial Release** - Complete database with 465 nodes and 745 edges
- **8 Historical Phases** - Comprehensive coverage from 4th century BCE to 6th century CE
- **FAIR Compliance** - Findable, Accessible, Interoperable, Reusable data principles
- **GraphRAG Integration** - Optimized for Google Gemini embeddings and semantic search
- **Comprehensive Documentation** - README, data dictionary, schema, and examples

### Database Content
- **465 Nodes:**
  - 156 persons (philosophers, theologians, authors)
  - 113 arguments (specific philosophical positions)
  - 80 concepts (philosophical terms and ideas)
  - 53 reformulations (conceptual developments)
  - 48 works (treatises, dialogues, letters)
  - 5 controversies (specific disputes)
  - 3 debates (major philosophical controversies)
  - 3 groups (philosophical circles)
  - 2 events (historical occurrences)
  - 1 school (philosophical institution)
  - 1 argument framework (systematic structure)

- **745 Edges:**
  - 25+ relationship types (influenced, refutes, supports, formulated, etc.)
  - Complete provenance with ancient source citations
  - Modern scholarship references for all major claims

### Historical Coverage
- **Phase 1:** Critical Foundations (Aristotle, Epicurus, Alexander of Aphrodisias)
- **Phase 2:** Platonic Foundations (Plato, Socrates, Democritus)
- **Phase 3:** Stoic Synthesis (Chrysippus, compatibilism, heimarmenê)
- **Phase 4:** Academic Skepticism (Carneades, CAFMA, incompatibilism)
- **Phase 5:** Middle Platonism (Alcinous, providence/fate distinction)
- **Phase 6:** Patristic Theology (Origen, Justin Martyr, autexousion)
- **Phases 7-8:** Synthesis (Boethius, terminology evolution, debate structure)

### Philosophical Positions
- **Aristotelian Framework** - Voluntary action, deliberation, eph' hêmin
- **Stoic Compatibilism** - Universal fate + internal causation = responsibility
- **Epicurean Indeterminism** - Atomic swerve breaks causal necessity
- **Academic Incompatibilism** - Carneades' CAFMA critique
- **Alexandrian Libertarianism** - Self-initiated action
- **Middle Platonist Synthesis** - Providence ≠ fate distinction
- **Christian Autexousion** - Self-determining power for divine justice
- **Boethian Solution** - Divine eternity reconciles foreknowledge and freedom

### Technical Features
- **JSON Format** - Human-readable, machine-parsable
- **UTF-8 Encoding** - Full Greek/Latin character support
- **Schema Validation** - JSON Schema Draft 07 compliance
- **Semantic Versioning** - 1.0.0 initial release
- **13 MB Database** - Comprehensive yet manageable size

### Documentation
- **README.md** - Complete user guide and overview
- **DATA_DICTIONARY.md** - Technical field reference
- **schema.json** - JSON Schema for validation
- **CITATION.cff** - Citation metadata
- **examples/** - Query examples and usage patterns
- **wiki/** - Comprehensive documentation wiki

### Example Scripts
- **generate_embeddings.py** - Generate vector embeddings with Google Gemini, OpenAI, Cohere, and sentence-transformers
- **semantic_search.py** - Perform semantic search with metadata filtering
- **graphrag_example.py** - Complete GraphRAG pipeline demonstration
- **network_analysis.py** - Network analysis with centrality measures and community detection
- **export_cytoscape.py** - Export to Cytoscape-compatible CSV files
- **validate_database.py** - Schema validation and data integrity checks

### Quality Assurance
- **Source Verification** - All claims grounded in ancient texts
- **Modern Scholarship** - 200+ academic references
- **Terminology Preservation** - Greek/Latin terms with transliterations
- **No Hallucinations** - All content verified against sources
- **Consistent Naming** - Standardized conventions throughout

### License and Access
- **CC BY 4.0 License** - Open access for research and commercial use
- **FAIR Principles** - Findable, Accessible, Interoperable, Reusable
- **Academic Use** - Designed for research, teaching, and publication
- **Attribution Required** - Proper citation expected

---

## Future Versions

### Version 1.1 (Planned)
**Target Release:** Q2 2026

#### Planned Additions
- **Enhanced Biographical Data** - Additional details for person nodes
- **Extended Bibliography** - More modern scholarship references
- **Improved Cross-References** - Better linking between related concepts
- **Additional Examples** - More query patterns and use cases

#### Potential Features
- **Timeline Visualization** - Interactive historical timeline
- **Influence Network Analysis** - Enhanced relationship mapping
- **Terminology Glossary** - Comprehensive Greek/Latin/English dictionary

### Version 1.2 (Planned)
**Target Release:** Q4 2026

#### Planned Additions
- **Middle Platonist Expansion** - Additional figures and concepts
- **Late Neoplatonist Coverage** - Plotinus, Porphyry, Proclus
- **Enhanced Patristic Data** - More early Christian thinkers
- **Improved Argument Analysis** - More detailed logical structures

#### Potential Features
- **Interactive Web Interface** - Browser-based query tool
- **API Development** - RESTful API for programmatic access
- **Export Formats** - Additional export options (RDF, GraphML)

### Version 2.0 (Tentative)
**Target Release:** 2027

#### Potential Scope
- **Medieval Extension** - Latin, Arabic, Byzantine developments
- **Cross-Cultural Analysis** - Comparative philosophical traditions
- **Multilingual Support** - Multiple language interfaces
- **Advanced AI Integration** - Enhanced GraphRAG capabilities

#### Research Areas
- **Aquinas and Scholasticism** - Medieval free will debates
- **Islamic Philosophy** - Arabic and Persian developments
- **Byzantine Theology** - Eastern Christian contributions
- **Renaissance Humanism** - Early modern transitions

---

## Known Issues and Limitations

### Current Limitations

#### Scope Limitations
- **Temporal Scope** - Covers only ancient period (4th BCE - 6th CE)
- **Geographic Focus** - Primarily Greco-Roman and early Christian
- **Language Coverage** - Greek and Latin sources only
- **Medieval Gap** - No coverage of medieval developments

#### Technical Limitations
- **Single Format** - Currently only JSON format
- **Static Data** - No real-time updates or corrections
- **Limited Visualization** - No built-in visualization tools
- **Manual Updates** - No automated data integration

#### Content Limitations
- **Selective Coverage** - Focus on major figures and concepts
- **Modern Scholarship** - Primarily English-language sources
- **Interpretation Bias** - Reflects current scholarly consensus
- **Incomplete Sources** - Some ancient texts fragmentary

### Data Quality Issues

#### Minor Inconsistencies
- **Date Formats** - Some variation in date representation
- **Name Variations** - Different forms of ancient names
- **Citation Styles** - Slight variations in source citations
- **Transliteration** - Minor differences in Greek/Latin transliteration

#### Areas for Improvement
- **Cross-References** - Could be more comprehensive
- **Argument Detail** - Some arguments could be more detailed
- **Historical Context** - More background information needed
- **Modern Connections** - Links to contemporary debates

---

## Contribution History

### Major Contributors

#### Primary Author
**Romain Girardi**
- Database design and implementation
- Content creation and curation
- Documentation and examples
- Quality assurance and validation

#### Institutional Support
**Université Côte d'Azur (CEPAM)**
- Research infrastructure
- Academic supervision
- Resource access

**Université de Genève (Faculté de Théologie Jean Calvin)**
- Theological expertise
- Patristic studies support
- Cross-disciplinary collaboration

#### Doctoral Advisors
**Arnaud Zucker (CEPAM)**
- Ancient philosophy guidance
- Research methodology
- Academic standards

**Andreas Dettwiler (UNIGE)**
- Patristic theology expertise
- Historical methodology
- Quality control

### Community Contributions

#### Beta Testers
- Academic researchers in ancient philosophy
- Digital humanities scholars
- Graduate students in relevant fields

#### Feedback Providers
- Conference presentations and workshops
- Academic peer review
- Community feedback via GitHub

---

## Technical Notes

### Database Statistics
- **Total Size:** ~13 MB
- **Node Count:** 465
- **Edge Count:** 745
- **Average Degree:** ~3.2 connections per node
- **Schema Version:** JSON Schema Draft 07
- **Encoding:** UTF-8

### Performance Characteristics
- **Load Time:** < 1 second on modern systems
- **Memory Usage:** ~50 MB when loaded
- **Query Performance:** O(n) for basic operations
- **Export Time:** < 5 seconds for full export

### Compatibility
- **Python:** 3.7+ (tested on 3.8, 3.9, 3.10, 3.11)
- **JavaScript:** ES6+ (Node.js 12+, modern browsers)
- **JSON Parsers:** All major implementations supported
- **Character Encoding:** Full Unicode support

---

## Acknowledgments

### Academic Community
- **Ancient Philosophy Scholars** - For foundational research
- **Patristic Studies Community** - For theological expertise
- **Digital Humanities Researchers** - For methodological guidance
- **Open Access Advocates** - For promoting FAIR principles

### Technical Community
- **JSON Schema Community** - For validation standards
- **Graph Database Developers** - For data modeling insights
- **Open Source Contributors** - For tools and libraries
- **FAIR Data Community** - For best practices

### Institutional Support
- **Université Côte d'Azur** - Research infrastructure and funding
- **Université de Genève** - Academic collaboration and resources
- **CEPAM Research Center** - Ancient studies expertise
- **Faculté de Théologie Jean Calvin** - Theological studies support

---

## Contact and Support

### Primary Contact
**Romain Girardi**
- Email: romain.girardi@univ-cotedazur.fr
- ORCID: 0000-0002-5310-5346
- GitHub: [romain-girardi-eng](https://github.com/romain-girardi-eng)

### Institutional Affiliations
- **Université Côte d'Azur, CEPAM**
- **Université de Genève, Faculté de Théologie Jean Calvin**

### Support Channels
- **GitHub Issues** - Bug reports and feature requests
- **Email Support** - Academic and technical questions
- **Community Forum** - User discussions and tips

---

## License Information

### Database License
**Creative Commons Attribution 4.0 International (CC BY 4.0)**

### Permissions
- ✅ **Share** - Copy and redistribute
- ✅ **Adapt** - Remix, transform, build upon
- ✅ **Commercial Use** - Use for commercial purposes

### Requirements
- **Attribution** - Must give appropriate credit
- **License Notice** - Must include license information
- **Changes Notice** - Must indicate if changes were made

### Full License Text
Available at: https://creativecommons.org/licenses/by/4.0/

---

**Last Updated:** October 17, 2025  
**Version:** 1.0.0  
**Maintained by:** Romain Girardi (romain.girardi@univ-cotedazur.fr)
