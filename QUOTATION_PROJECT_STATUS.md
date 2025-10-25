# Quotation Retrieval Project - Status Report

**Date:** 2025-10-25
**Goal:** Add full original texts (Greek/Latin + English) for all 1,491 unique citations
**Status:** Foundation complete, systematic retrieval ready to begin

---

## ✅ What's Been Accomplished

### 1. Database Analysis Complete
- **Total citations analyzed:** 2,494 instances → 1,491 unique citations
- **Works identified:** 1,072 unique works
- **Top work identified:** Cicero De Fato (83 citations)
- **Generated inventories:**
  - `all_citations_inventory.csv` - Full citation list
  - `works_citation_frequency.txt` - All works ranked by frequency

### 2. Source Guidelines Established
**File:** `SOURCE_GUIDELINES.md`

**Translation Policy:**
- ✅ Prefer modern Loeb (fair use academic)
- ✅ Fallback to public domain
- ✅ Always cite translator/edition

**Primary Sources:**
- ✅ Perseus Digital Library (classical texts)
- ✅ Open Greek and Latin (OGL) - First1KGreek, CSEL corpus
- ✅ NA28 for New Testament
- ✅ Critical editions for Patristic (GCS/SC preferred, PG/PL acceptable)

### 3. First Work Retrieved Successfully
**✓ Cicero, De Fato - COMPLETE**
- 48 sections retrieved (Latin original)
- Source: Perseus Digital Library
- Edition: C. F. W. Müller, Leipzig: Teubner, 1915
- Full provenance documented
- File: `cicero_de_fato_complete.json`
- **Coverage:** 83 citations (5.6% of database)

### 4. Infrastructure Built
- **File:** `scripts/retrieve_classical_texts.py`
- Automated Perseus retrieval system
- Provenance tracking
- Error handling and retry logic
- Rate limiting (respectful to Perseus)

### 5. Documentation Created
- `QUOTATION_RETRIEVAL_PLAN.md` - Complete roadmap
- `SOURCE_GUIDELINES.md` - Academic standards
- This status document

---

## 🚧 Challenges Identified

### Perseus Complexity
Different works use different citation systems:
- **Cicero De Fato:** Simple sections (1-48) ✅ WORKS
- **Aristotle NE:** Bekker pages (1094a-1181b) ⚠️ Needs custom parser
- **Plato:** Stephanus pages
- **Plutarch:** Various systems

**Solution Needed:** Work-specific URL parsers

### English Translation Availability
- Perseus has LIMITED English translations
- Many works: Greek/Latin only
- **Action Required:** Source from alternative repositories or use public domain translations

### Scale
- 1,072 works total
- Manual configuration per work not feasible
- **Solution:** Tiered approach (automate top works, batch remaining)

---

## 📊 Citation Coverage Analysis

### Tier 1: HIGHEST IMPACT (Top 10 Works = 346 citations = 23%)
| Rank | Work | Citations | Status |
|------|------|-----------|--------|
| 1 | Cicero, De Fato | 83 | ✅ COMPLETE |
| 2 | Aristotle, Nicomachean Ethics | 38 | ⏳ In progress |
| 3 | Alexander of Aphrodisias, De Fato | 35 | 🔍 To retrieve |
| 4 | Romans (Biblical) | 29 | 🔍 NA28 needed |
| 5 | Aulus Gellius, Noctes Atticae | 27 | 🔍 Perseus available |
| 6 | Origen, De Principiis | 26 | 🔍 OGL/PG needed |
| 7 | Hebrew Bible (Masoretic) | 25 | 🔍 BHS needed |
| 8 | Lucretius, De Rerum Natura | 24 | 🔍 Perseus available |
| 9 | Plotinus, Enneads | 24 | 🔍 Perseus available |
| 10 | Aristotle, De Interpretatione | 18 | 🔍 Perseus available |

**Completion: 1/10 works (83/346 citations = 24% of Tier 1)**

### Tier 2: HIGH IMPACT (Next 10 Works = 138 citations = 9%)
| Rank | Work | Citations |
|------|------|-----------|
| 11 | Origen, Contra Celsum | 18 |
| 12 | Plutarch, De Stoicorum Repugnantiis | 16 |
| 13 | Sirach | 16 |
| 14 | Septuagint (LXX) | 16 |
| 15 | Aristotle, Eudemian Ethics | 15 |
| 16 | Alcinous, Didaskalikos | 15 |
| 17 | Galatians | 15 |
| 18 | Cicero, Academica | 13 |
| 19 | Epictetus, Discourses | 13 |
| 20 | Eusebius, Praeparatio Evangelica | 10 |

### Tier 3: MEDIUM IMPACT (Next 30 Works = ~200 citations = 13%)
Works with 5-10 citations each

### Tier 4: LONG TAIL (~1,030 Works = ~900 citations = 60%)
Works with 1-4 citations each

**Key Insight:** Top 20 works = 484 citations = 32% of total database

---

## 🎯 Recommended Next Steps

### Phase 1: Complete Top 10 Works (Target: 80% automation)
**Estimated Coverage:** 346 citations (23% of database)

**Priority Order:**
1. ✅ Cicero, De Fato (83) - DONE
2. ⏳ Lucretius, De Rerum Natura (24) - **START HERE** (Perseus, simple structure)
3. ⏳ Aulus Gellius, Noctes Atticae (27) - Perseus available
4. ⏳ Epictetus, Discourses (13) - Perseus available
5. ⏳ Plotinus, Enneads (24) - Perseus available
6. ⏳ Aristotle, De Interpretatione (18) - Perseus, Bekker pages
7. ⏳ Aristotle, Nicomachean Ethics (38) - Perseus, Bekker pages (complex)
8. ⏳ Alexander, De Fato (35) - Check Perseus/OGL availability
9. ⏳ Origen, De Principiis (26) - OGL CSEL or PG
10. ⏳ Biblical texts (Romans 29, Hebrew Bible 25) - NA28/BHS

**Why this order?**
- Start with simpler Perseus structures (Lucretius, Gellius, Epictetus)
- Build Bekker page parser once, apply to multiple Aristotle works
- Tackle non-Perseus sources last (Origen, Biblical)

### Phase 2: Top 20 Works
Add works 11-20 for 32% total coverage

### Phase 3: Long Tail Strategy
- Automated bulk retrieval where possible
- Manual review queue for failed retrievals
- Accept that some fragmentary/obscure citations may require your direct sourcing

---

## 💻 Technical Requirements

### Immediate Development Needs

1. **Work-Specific URL Builders**
```python
def build_perseus_url(work, citation):
    if work == 'cicero_de_fato':
        return f"...section={citation}"
    elif work == 'aristotle_ne':
        bekker = parse_bekker_citation(citation)
        return f"...bekker+page={bekker}"
    elif work == 'lucretius_drn':
        book, line = parse_drn_citation(citation)
        return f"...book={book}:card={line}"
```

2. **Citation Parser**
```python
"Cicero, De Fato 28-33" → {
    'work': 'cicero_de_fato',
    'sections': ['28', '29', '30', '31', '32', '33']
}

"Aristotle, NE III.1-5" → {
    'work': 'aristotle_ne',
    'book': '3',
    'chapters': ['1', '2', '3', '4', '5'],
    'bekker_range': ['1109b', ..., '1115a']
}
```

3. **Batch Retrieval Queue**
- Process top 50 works automatically
- Generate failure report for manual review
- Track completion percentage

4. **Integration Script**
```python
def add_texts_to_database(db, citation_texts):
    """
    Integrate retrieved texts into main database
    - Add new 'full_text' field to nodes/edges with ancient_sources
    - Link citations to retrieved passages
    - Maintain provenance
    """
```

---

## 📈 Success Metrics

### Immediate Goals (This Week)
- [ ] Retrieve 5 more Perseus works (Lucretius, Gellius, Epictetus, Plotinus, +1)
- [ ] Build Bekker page parser
- [ ] Reach 150 citations retrieved (10% of database)

### Short-term Goals (This Month)
- [ ] Complete Top 10 works (346 citations, 23%)
- [ ] Build citation→text matching system
- [ ] Integrate texts into main database JSON

### Long-term Goals (Next 3 Months)
- [ ] Top 50 works retrieved
- [ ] 50%+ citation coverage
- [ ] Comprehensive verification report
- [ ] Publication-ready citation database

---

## 🤝 Your Role

### Decisions Needed
- ✅ Translation policy (Loeb → public domain) - DECIDED
- ✅ Source priorities (critical editions > PG/PL) - DECIDED
- ✅ Biblical editions (NA28, BHS) - DECIDED

### Manual Work Required
1. **Verification:** Review automated retrievals for accuracy
2. **Problem Citations:** Resolve failed retrievals (ambiguous references, missing sources)
3. **Quality Check:** Spot-check that retrieved texts match citations correctly
4. **Final Approval:** Sign off on integrated texts before publication

### Expected Time Commitment
- **Phase 1 (Top 10):** ~2-4 hours review (I do bulk retrieval)
- **Phase 2 (Top 50):** ~10-15 hours review
- **Phase 3 (Long tail):** Variable (many may require your direct sourcing)

---

## 🔄 Next Actions

### Me (Claude):
1. ✅ Complete Perseus retrieval for **Lucretius De Rerum Natura** (straightforward structure)
2. Build Bekker page parser
3. Retrieve **Aulus Gellius, Epictetus, Plotinus**
4. Generate detailed progress report with samples for your verification

### You (Romain):
1. Review retrieved Cicero De Fato samples - verify accuracy
2. Approve continuation with automated retrieval
3. Identify any high-priority citations that need immediate attention
4. Decide if you want daily progress updates or wait for batch completion

---

**Question:** Should I proceed with retrieving Lucretius De Rerum Natura now (24 citations, straightforward Perseus structure)?

This will demonstrate the system works for multiple text types and get us to ~100 citations retrieved (7% of database).
