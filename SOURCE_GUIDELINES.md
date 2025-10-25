# Source Guidelines for Text Retrieval

**Established:** 2025-10-25
**Authority:** Romain Girardi, project maintainer

---

## Translation Policy

### English Translations
1. **Prefer:** Modern Loeb Classical Library (cite edition, fair use academic)
2. **Fallback:** Public domain translations (pre-1928)
3. **Always:** Document translator, edition, year, and licensing

### Original Language Texts
- Use critical editions when available
- Document edition explicitly in provenance
- Prefer standard scholarly texts (OCT, Teubner, Budé, etc.)

---

## Source Priorities by Text Type

### Classical Greek/Latin Texts
**Primary Sources (equal priority):**

1. **Perseus Digital Library** (http://www.perseus.tufts.edu)
   - Standard scholarly editions (Teubner, OCT, etc.)
   - Well-documented provenance
   - Web interface + API access
   - Strong coverage: Cicero, Aristotle, Epictetus, Plutarch, Lucretius

2. **Open Greek and Latin (OGL)** (https://github.com/OpenGreekAndLatin)
   - TEI-compliant XML files
   - CTS protocol compatible
   - **First1KGreek**: ~30 million words of Greek through 600 CE
   - **CSEL corpus**: Patristic Latin (Origen Latin, Augustine, etc.)
   - **Patrologia Latina (PL)**: Machine-corrected selections
   - GitHub repositories allow bulk download
   - Excellent for: Patristic authors, fragmentary texts, alternative editions

**Secondary:** Archive.org, Wikisource (public domain editions)

### New Testament
**Standard:** NA28 (Nestle-Aland 28th edition)
- Critical Greek text
- Industry standard for NT scholarship

### Old Testament / Hebrew Bible
**Masoretic Text:** BHS (Biblia Hebraica Stuttgartensia) or WTT
**Septuagint (LXX):** Rahlfs-Hanhart edition

### Patristic Texts
**Preference Order:**
1. **Critical editions** (Sources Chrétiennes, CCSL, CSEL, GCS)
2. **Patrologia Graeca (PG) / Patrologia Latina (PL)** - Acceptable when critical edition unavailable
3. **Digital editions:** CCEL (Christian Classics Ethereal Library) - verify against print

**Key Patristic Works in Database:**
- Origen, De Principiis (26 citations) → GCS critical edition preferred, PG acceptable
- Origen, Contra Celsum (18 citations) → GCS/SC preferred
- Augustine works → CCSL preferred, PL acceptable
- Justin Martyr, Nemesius → PG acceptable

### Dead Sea Scrolls
- Use standard scholarly editions (DJD series)
- Cite fragment numbers precisely
- Multiple translations acceptable if documented

### Rabbinic Literature
- Standard critical editions (e.g., Vilna Talmud)
- Sefaria.org acceptable for digitized texts
- Always cite tractate, chapter, page (e.g., "b. Berakhot 33b")

---

## Citation Requirements

Every retrieved text must include:

```json
{
  "text": "[original text]",
  "translation": "[English translation]",
  "provenance": {
    "original_source": "Perseus Digital Library",
    "original_edition": "I. Bywater, Oxford: Oxford University Press, 1894",
    "original_url": "http://...",
    "translation_source": "Loeb Classical Library",
    "translator": "H. Rackham",
    "translation_year": "1926",
    "translation_edition": "Loeb Classical Library No. 73",
    "license": "Fair use academic citation / Public domain / CC-BY",
    "retrieved_date": "2025-10-25",
    "verification_status": "perseus_verified / manually_verified / needs_review"
  }
}
```

---

## Retrieval Priority (Automated Strategy)

### Phase 1: Perseus-Available Classical Texts (Highest ROI)
**Works with complete Perseus availability:**
- ✅ Cicero, De Fato (83 citations) - COMPLETE
- Aristotle, Nicomachean Ethics (38 citations)
- Lucretius, De Rerum Natura (24 citations)
- Aristotle, De Interpretatione (18 citations)
- Aristotle, Eudemian Ethics (15 citations)
- Cicero, Academica (13 citations)
- Epictetus, Discourses (13 citations)
- Plutarch, De Stoicorum Repugnantiis (16 citations)
- Cicero, De Natura Deorum (8 citations)
- Cicero, De Divinatione (8 citations)

**Estimated:** ~300 citations, ~20% database coverage

### Phase 2: Biblical Texts (High Citation Count)
- Romans (29 citations) → NA28
- Galatians (15 citations) → NA28
- 1 Corinthians (8 citations) → NA28
- Hebrew Bible (25 citations) → BHS/WTT + standard translations
- Septuagint (16 citations) → Rahlfs-Hanhart
- Sirach/Ecclesiasticus (16 citations) → LXX

**Estimated:** ~100+ citations

### Phase 3: Patristic Texts (Mixed Availability)
- Origen, De Principiis (26 citations) → GCS or PG
- Origen, Contra Celsum (18 citations) → GCS/SC or PG
- Augustine works (~30+ citations total) → CCSL or PL
- Nemesius, De Natura Hominis (9 citations) → PG
- Eusebius, Praeparatio Evangelica (10 citations) → GCS or PG

**Requires:** Individual work assessment for critical edition availability

### Phase 4: Specialized/Fragmentary Sources
- Alexander of Aphrodisias, De Fato (35 citations) → Check Perseus, else scholarly edition
- Aulus Gellius, Noctes Atticae (27 citations) → Perseus available
- Plotinus, Enneads (24 citations) → Perseus available
- Dead Sea Scrolls (8 citations) → DJD series
- Fragmentary authors → Diels-Kranz, Loeb Fragments collections

### Phase 5: Long Tail (1-5 citations each)
- ~1,000 works
- Individual assessment required
- Many may be secondary citations (e.g., "mentioned in Cicero")

---

## Quality Gates

### Automatic Acceptance
- Perseus Digital Library texts
- NA28 New Testament
- Standard critical editions (OCT, Teubner, Budé, GCS, CCSL)

### Manual Review Required
- Non-standard editions
- Fragmentary texts
- Uncertain section references
- Failed automatic retrieval

### Red Flags (Must Review)
- Citation doesn't match retrieved text
- Multiple significantly different editions exist
- Work not found in expected source
- Ambiguous passage reference

---

## License Compliance

### Fair Use Academic Citation
- Short passages for scholarly commentary
- Always cite source fully
- Non-commercial academic use
- Transformative purpose (knowledge graph)

### Public Domain (Pre-1928 in US)
- Freely usable
- Still cite for academic integrity

### Modern Critical Editions
- Use sparingly, cite fully
- Prefer Perseus/public domain where available
- Fair use applies for scholarly database

---

**This document guides all text retrieval. Any deviation requires maintainer approval.**
