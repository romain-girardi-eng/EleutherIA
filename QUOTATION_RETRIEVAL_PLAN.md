# Complete Quotation Retrieval Plan

**Goal:** Add full original texts (Latin/Greek + English translations) for all 1,491 unique citations in the Ancient Free Will Database

**Anti-Hallucination Policy:** ZERO tolerance - only verified texts from authoritative sources

---

## Current Status

### ✅ Completed
- [x] Analyzed database structure (534 nodes, 923 edges)
- [x] Extracted all 2,494 citation instances → 1,491 unique citations
- [x] Identified top cited works (83x Cicero De Fato, 38x Aristotle NE, etc.)
- [x] **Successfully retrieved complete Cicero De Fato (48 sections, Latin)**
- [x] Built Perseus Digital Library retrieval infrastructure
- [x] Established provenance tracking system

### 📊 Citation Inventory

**Top 20 Most Cited Works:**
```
 83  Cicero, De Fato                              ✓ RETRIEVED (48 sections, Latin)
 38  Aristotle, Nicomachean Ethics                ⏳ Next priority
 35  Alexander of Aphrodisias, De Fato            ⏳ Next priority
 29  Romans (Biblical)
 27  Aulus Gellius, Noctes Atticae
 26  Origen, De Principiis
 25  Hebrew Bible (Masoretic Text)
 24  Lucretius, De Rerum Natura
 24  Plotinus, Enneads
 18  Aristotle, De Interpretatione
 18  Origen, Contra Celsum
 16  Plutarch, De Stoicorum Repugnantiis
 16  Sirach (Ecclesiasticus)
 16  Septuagint (LXX)
 15  Aristotle, Eudemian Ethics
 15  Alcinous, Didaskalikos
 15  Galatians (Biblical)
 13  Cicero, Academica
 13  Epictetus, Discourses
 10  Eusebius, Praeparatio Evangelica
```

**Total:** 1,072 unique works cited

---

## Retrieval Strategy

### Phase 1: Perseus Digital Library (Primary Source)
**Status:** Infrastructure built, first work retrieved

**Coverage:**
- ✅ Complete Latin texts (Cicero, Lucretius, etc.)
- ✅ Complete Greek texts (Aristotle, Plutarch, Epictetus, etc.)
- ⚠️ English translations: LIMITED (not all works have translations in Perseus)

**Methodology:**
1. Retrieve work-by-work (most efficient for frequently cited texts)
2. Section-by-section parsing with provenance tracking
3. Cross-validation where multiple editions exist
4. Flag gaps for manual review

### Phase 2: English Translations
**Status:** Needs sourcing strategy

**Options:**
1. **Loeb Classical Library** (authoritative, but copyright protected - fair use only)
   - Can cite specific passages for academic purposes
   - Must document which Loeb edition

2. **Public Domain Translations**
   - Archive.org classical texts
   - Wikisource verified texts
   - Older Loeb editions (pre-1928 = public domain)

3. **Perseus Translations** (where available)
   - Some works have parallel English
   - Quality varies

**Action Required:** You need to decide on translation sourcing strategy:
- Option A: Fair use academic citations from modern Loeb
- Option B: Public domain translations only (older, sometimes less accurate)
- Option C: Mix of both with clear licensing documentation

### Phase 3: Non-Perseus Sources
**Status:** Needs identification

**Works NOT in Perseus:**
- Origen, De Principiis (Patristic text)
- Augustine (most works)
- Nemesius, De Natura Hominis
- Dead Sea Scrolls fragments
- Rabbinic literature

**Alternative Sources:**
- **Early Church Fathers:** CCEL (Christian Classics Ethereal Library)
- **Patristic:** Patrologia Latina/Graeca (digitized)
- **Biblical/Jewish:** Bible Hub, Sefaria
- **Scholarly editions:** Individual work-by-work sourcing

---

## Technical Implementation

### Data Model

```json
{
  "citation_database": {
    "works": [
      {
        "work_id": "cicero_de_fato",
        "metadata": {
          "author": "Marcus Tullius Cicero",
          "work": "De Fato",
          "language": "Latin",
          "source": "Perseus Digital Library",
          "perseus_id": "Perseus:text:2007.01.0035",
          "edition": "C. F. W. Müller, Leipzig: Teubner, 1915",
          "retrieved_date": "2025-10-25",
          "verification_status": "perseus_verified"
        },
        "sections": {
          "43": {
            "latin": "Ut igitur, inquit, qui protrusit cylindrum...",
            "english": "[Translation source TBD]",
            "url_latin": "http://...",
            "url_english": null,
            "provenance": {
              "latin_source": "Perseus Digital Library",
              "latin_edition": "Müller 1915",
              "english_source": null,
              "verification_date": "2025-10-25",
              "verified_by": "Automated retrieval from Perseus"
            }
          }
        }
      }
    ]
  }
}
```

### Citation Matching System

```python
# Map database citations → retrieved texts
"Cicero, De Fato 43" → works['cicero_de_fato']['sections']['43']
"Cicero, De Fato 28-33" → works['cicero_de_fato']['sections']['28'] through '33'
```

---

## Retrieval Priorities

### Tier 1: HIGH PRIORITY (80+ citations)
- [x] Cicero, De Fato (83 citations) - **COMPLETE**

### Tier 2: VERY HIGH (30-40 citations)
- [ ] Aristotle, Nicomachean Ethics (38 citations)
- [ ] Alexander of Aphrodisias, De Fato (35 citations)

### Tier 3: HIGH (20-30 citations)
- [ ] Romans (29 citations) - Biblical source
- [ ] Aulus Gellius, Noctes Atticae (27 citations)
- [ ] Origen, De Principiis (26 citations)
- [ ] Hebrew Bible (25 citations)
- [ ] Lucretius, De Rerum Natura (24 citations)
- [ ] Plotinus, Enneads (24 citations)

### Tier 4: MEDIUM (10-20 citations)
- 15 works in this range

### Tier 5: LOW (1-10 citations)
- ~1,050 works (long tail)

**Strategy:** Focus on Tiers 1-3 first (top 10 works = 346 citations = 23% coverage)

---

## Quality Control

### Verification Levels

1. **VERIFIED** - Retrieved from authoritative source (Perseus, scholarly edition)
2. **SINGLE_SOURCE** - One source only, needs cross-checking
3. **REQUIRES_REVIEW** - Retrieval failed or uncertain
4. **NOT_AVAILABLE** - Source doesn't exist in digital form

### Manual Review Queue

All retrieved texts with status:
- Significant edition variants
- Ambiguous section references
- Failed retrievals
- Non-standard citations

**Your role:** Final verification for:
- Accuracy of citation parsing
- Correctness of retrieved passages
- Translation quality (if using automated sources)

---

## Next Steps

### Immediate (Today)
1. **Decision needed:** English translation sourcing strategy
2. **Retrieve:** Aristotle Nicomachean Ethics (Greek text from Perseus)
3. **Retrieve:** Alexander De Fato (if available in Perseus)

### Short-term (This Week)
4. Build citation→text matching system
5. Retrieve top 10 works (Tiers 1-3)
6. Create verification report
7. Generate manual review queue for failed retrievals

### Medium-term (This Month)
8. Source non-Perseus texts (Patristic, Biblical)
9. Complete top 50 works
10. Build import script to add texts to main database
11. Update schema.json with citation fields

### Long-term
12. Complete all 1,072 works
13. Cross-validate multi-source texts
14. Final quality audit
15. Publication-ready citation database

---

## Files Generated

- `all_citations_inventory.csv` - All 1,491 unique citations with frequency
- `works_citation_frequency.txt` - All 1,072 works ranked by frequency
- `cicero_de_fato_complete.json` - Complete De Fato (48 sections, Latin)
- `scripts/retrieve_classical_texts.py` - Automated retrieval system

---

## Questions for You

1. **Translation strategy:** Loeb fair use vs. public domain only?
2. **Biblical texts:** Which edition/translation? (ESV, NRSV, original Hebrew/Greek?)
3. **Patristic texts:** Acceptable to use CCEL/digitized PL/PG?
4. **Priority adjustment:** Focus on specific works first?
5. **Review capacity:** How many citations can you manually verify per day?

---

**Last Updated:** 2025-10-25
**Status:** Phase 1 infrastructure complete, first work retrieved, awaiting decisions on translation sourcing
