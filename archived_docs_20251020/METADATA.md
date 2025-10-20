# Metadata Standards

EleutherIA uses multiple metadata standards to ensure maximum discoverability, interoperability, and compliance with academic best practices.

---

## 📋 Metadata Files

### 1. **codemeta.json** (CodeMeta 2.0)

**Standard:** [CodeMeta 2.0](https://codemeta.github.io/)
**Purpose:** Software and data metadata

**What it provides:**
- Software identification and versioning
- Author information with ORCID
- Institutional affiliations
- Programming language support
- Dependencies and requirements
- License information
- Keywords for discoverability
- Related publications
- File formats and technical details

**Used by:**
- Zenodo (automatic metadata extraction)
- Software Heritage (long-term preservation)
- Research data repositories
- Package managers
- Citation tools

**Validation:**
```bash
# Validate with CodeMeta validator
curl -X POST https://codemeta.github.io/codemeta-generator/validate \
  -H "Content-Type: application/json" \
  -d @codemeta.json
```

---

### 2. **CITATION.cff** (Citation File Format)

**Standard:** [Citation File Format](https://citation-file-format.github.io/)
**Purpose:** Academic citation

**What it provides:**
- Standardized citation format
- Author information with ORCID
- DOI (when assigned)
- Version information
- Keywords
- License
- Reference publications

**Used by:**
- GitHub (native support - "Cite this repository" button)
- Zenodo (automatic integration)
- Zotero (citation manager)
- Academic citation tools

**Validation:**
```bash
# Validate with cffconvert
pip install cffconvert
cffconvert --validate
```

---

### 3. **schema.json** (JSON Schema)

**Standard:** [JSON Schema Draft 07](https://json-schema.org/)
**Purpose:** Data structure validation

**What it provides:**
- Formal schema definition
- Required/optional field specifications
- Data type constraints
- Enumerated values
- Pattern validation

**Used by:**
- Data validation tools
- API documentation
- Schema registries
- IDE autocomplete

**Validation:**
```bash
# Validate database against schema
jsonschema -i ancient_free_will_database.json schema.json
```

---

### 4. **Database Metadata** (JSON-LD)

**Location:** Inside `ancient_free_will_database.json`
**Standard:** FAIR principles + custom schema

**What it provides:**
- FAIR compliance documentation (Findable, Accessible, Interoperable, Reusable)
- Project description and scope
- Statistics (465 nodes, 745 edges)
- Version information
- Author and advisor information
- GraphRAG capabilities
- AI integration details
- Provenance and methodology

---

## 🎯 Why Multiple Metadata Standards?

Each standard serves a different purpose and ecosystem:

| Standard | Primary Use | Ecosystem |
|----------|-------------|-----------|
| **CodeMeta** | Software repositories | Zenodo, Software Heritage, DOI minting |
| **CITATION.cff** | Academic citations | GitHub, citation managers, papers |
| **JSON Schema** | Data validation | APIs, IDEs, data pipelines |
| **Database Metadata** | FAIR compliance | Research data, digital humanities |

**Together, they ensure:**
✅ **Discoverability** - Found by researchers and tools
✅ **Citability** - Proper academic attribution
✅ **Interoperability** - Works with various tools
✅ **Reusability** - Clear structure and usage
✅ **Preservation** - Long-term archiving

---

## 📊 Coverage Map

```
┌─────────────────────────────────────────────────┐
│                EleutherIA Metadata              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────┐  ┌──────────────┐           │
│  │ codemeta.json │  │ CITATION.cff │           │
│  │ (Software)    │  │ (Citation)   │           │
│  └───────┬───────┘  └──────┬───────┘           │
│          │                  │                   │
│          ├──────────────────┤                   │
│          │                  │                   │
│  ┌───────▼──────┐  ┌────────▼────────┐         │
│  │ schema.json  │  │ DB metadata     │         │
│  │ (Structure)  │  │ (FAIR)          │         │
│  └──────────────┘  └─────────────────┘         │
│                                                 │
│  All synchronized with:                        │
│  - Version: 1.0.0                              │
│  - Author: Romain Girardi                      │
│  - ORCID: 0000-0002-5310-5346                 │
│  - License: CC BY 4.0                          │
│  - Date: 2025-10-17                            │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Maintenance

When updating EleutherIA, synchronize all metadata files:

### Version Update Checklist

- [ ] Update `version` in `codemeta.json`
- [ ] Update `version` in `CITATION.cff`
- [ ] Update `metadata.version` in `ancient_free_will_database.json`
- [ ] Update `README.md` version badge
- [ ] Update `dateModified` in `codemeta.json`
- [ ] Add entry to `CHANGELOG.md`

### Author Information Checklist

- [ ] Consistent across all files
- [ ] ORCID included
- [ ] Affiliations up to date
- [ ] Email correct

### DOI Assignment (When Available)

Once Zenodo assigns a DOI:

- [ ] Update `identifier` in `codemeta.json`
- [ ] Update `doi` in `CITATION.cff`
- [ ] Update all README citations
- [ ] Update `sameAs` links

---

## 🔗 Related Standards

EleutherIA also follows:

- **FAIR Principles** - Findable, Accessible, Interoperable, Reusable
- **Semantic Versioning** - Version numbering (1.0.0)
- **CC BY 4.0** - Open licensing
- **JSON** - Data interchange format
- **UTF-8** - Character encoding
- **ISO 8601** - Date formats

---

## 📚 Resources

### Standards Documentation

- **CodeMeta:** https://codemeta.github.io/
- **CITATION.cff:** https://citation-file-format.github.io/
- **JSON Schema:** https://json-schema.org/
- **FAIR Principles:** https://www.go-fair.org/fair-principles/
- **Schema.org:** https://schema.org/ (used in CodeMeta)

### Validation Tools

- **CodeMeta Generator:** https://codemeta.github.io/codemeta-generator/
- **CITATION.cff Validator:** https://github.com/citation-file-format/cffconvert
- **JSON Schema Validator:** https://www.jsonschemavalidator.net/
- **FAIR Assessment:** https://fair-checker.france-bioinformatique.fr/

### Integration Services

- **Zenodo:** https://zenodo.org/ (automatic metadata extraction)
- **Software Heritage:** https://www.softwareheritage.org/
- **GitHub:** Native CITATION.cff support
- **ORCID:** https://orcid.org/ (author identification)

---

## ✅ Compliance Checklist

EleutherIA is compliant with:

- [x] CodeMeta 2.0
- [x] Citation File Format
- [x] JSON Schema Draft 07
- [x] FAIR Principles (F, A, I, R)
- [x] Semantic Versioning
- [x] Open License (CC BY 4.0)
- [x] ORCID Author Identification
- [x] UTF-8 Encoding
- [x] ISO 8601 Dates

---

**Questions about metadata?**
Contact: romain.girardi@univ-cotedazur.fr

---

**Last Updated:** October 17, 2025
**Version:** 1.0.0
