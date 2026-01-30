# Methodology

Scholarly methodology for the EleutherIA knowledge graph.

## Dual-Layer Structure

EleutherIA employs a dual-layer epistemological structure:

### Primary Layer (Ancient Sources)
- Philosophers, concepts, arguments, and texts from antiquity
- The core scholarly focus of the database
- Includes both extant works and fragments

### Secondary Layer (Modern Reception)
- Contemporary scholars and their interpretative frameworks
- Essential because "free will" is not a realia but a construct
- Meaning depends on which scholarly lens you apply

This structure reflects the reality that ancient concepts like τὸ ἐφ' ἡμῖν, αὐτεξούσιον, and προαίρεσις do not map directly to modern "free will" - interpretation is constitutive of the subject matter.

## Historical Periods

| Period | Dates | Key Figures |
|--------|-------|-------------|
| Presocratic | 6th-5th c. BCE | Heraclitus, Parmenides |
| Classical Greek | 5th-4th c. BCE | Plato, Aristotle |
| Hellenistic Greek | 4th-1st c. BCE | Zeno, Chrysippus, Epicurus |
| Roman Republican | 2nd-1st c. BCE | Cicero, Lucretius |
| Roman Imperial | 1st-3rd c. CE | Seneca, Epictetus, Marcus Aurelius |
| Patristic | 2nd-5th c. CE | Origen, Augustine |
| Late Antiquity | 4th-6th c. CE | Boethius, Proclus |

## Philosophical Schools

| School | Position on Fate/Free Will |
|--------|---------------------------|
| Stoic | Compatibilist - fate and moral responsibility coexist |
| Epicurean | Libertarian - atomic swerve allows genuine freedom |
| Academic | Skeptical - suspends judgment on determinism |
| Peripatetic | Qualified determinism - some things up to us |
| Pyrrhonist | Epochē - no dogmatic position |

## Citation Standards

### Ancient Sources
- **CTS URN format:** `urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1`
- **SVF references:** Stoicorum Veterum Fragmenta numbers
- **LS references:** Long & Sedley collection numbers

### Modern Scholarship
- Chicago 17th edition preferred
- Include page numbers for all claims
- Distinguish primary source editions from secondary analysis

## Data Quality

### Confidence Scoring
Citation links have confidence scores (0.0-1.0):
- **0.9-1.0:** Explicit textual evidence
- **0.7-0.89:** Strong contextual support
- **0.5-0.69:** Scholarly inference
- **<0.5:** Tentative attribution

### Verification Process
1. Extract claims from secondary literature
2. Verify Greek/Latin quotations against passages table
3. Cross-reference with primary sources
4. Apply confidence scores
5. Document scholarly debates

## Ancient Text Authenticity Policy

**100% Academic Integrity - Zero Tolerance for Fabrication**

This project is a scholarly database. AI-generated ancient Greek or Latin text is academic fraud.

### Absolute Prohibitions
- Never generate, compose, or fabricate ancient Greek/Latin
- Never reconstruct what an author "might have said"
- Never complete fragmentary quotations
- Never modernize ancient quotations

### Required Practice
- Query the passages table before quoting
- Include CTS URN or passage_id for every quotation
- When uncertain, paraphrase in English
- Acknowledge when text is not in database

## FAIR Principles

| Principle | Implementation |
|-----------|----------------|
| **Findable** | DOI via Zenodo, persistent identifiers |
| **Accessible** | Open REST API, HTTPS access |
| **Interoperable** | CTS URNs, JSON-LD, RDF ontology |
| **Reusable** | CC BY 4.0 license, documentation |

## Bibliography

Key secondary sources informing the database:

- Bobzien, S. (1998). *Determinism and Freedom in Stoic Philosophy*
- Frede, M. (2011). *A Free Will: Origins of the Notion in Ancient Thought*
- Long, A.A. & Sedley, D.N. (1987). *The Hellenistic Philosophers*
- Inwood, B. (1985). *Ethics and Human Action in Early Stoicism*
- O'Keefe, T. (2005). *Epicurus on Freedom*

See [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md) for complete references.
