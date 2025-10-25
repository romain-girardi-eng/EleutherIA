# Continuation Plan - 100% Retrieval
## Ancient Free Will Database Text Retrieval

**Date:** 2025-10-25
**Goal:** Retrieve ALL 1,491 citations with 100% verified texts and complete metadata
**Status:** Foundation complete (7.2%), continuing to 100%
**Estimated Total Time:** 120-150 hours

---

## Current Status

### ✅ Completed (7.2% - 107 citations)
- Cicero, De Fato: 83 citations (48 sections, Latin)
- Lucretius, De Rerum Natura: 24 citations (all 6 books, Latin)

### ✅ Infrastructure Ready
- Scaife CTS retrieval system
- Citation analysis complete
- Academic standards established
- CTS URN catalog built

---

## Systematic Retrieval Plan

### Phase 1: CTS Works with Simple Sections (20-30 hours)
**Target:** Works using simple section numbers like Cicero

| Work | Citations | CTS URN | Sections | Priority |
|------|-----------|---------|----------|----------|
| ✅ Cicero, De Fato | 83 | phi0474.phi054 | 1-48 | DONE |
| Cicero, Academica | 13 | phi0474.phi006 | TBD | HIGH |
| Cicero, De Natura Deorum | 8 | phi0474.phi038 | TBD | HIGH |
| Cicero, De Divinatione | 8 | phi0474.phi024 | TBD | HIGH |
| Cicero, De Legibus | TBD | phi0474.phi031 | TBD | MEDIUM |

**Action:** Test each CTS URN, determine section ranges, batch retrieve

### Phase 2: Greek Works with Bekker Pages (30-40 hours)
**Target:** Aristotle and similar works

| Work | Citations | Challenge | Solution |
|------|-----------|-----------|----------|
| Aristotle, NE | 38 | Bekker pages (1109b-1114b) | Build Bekker→CTS mapper |
| Aristotle, De Interp | 18 | Bekker pages | Use same mapper |
| Aristotle, Eudemian Ethics | 15 | Bekker pages | Use same mapper |
| Alexander, De Fato | 35 | Bekker pages | Use same mapper |

**Action:**
1. Build Bekker page parser
2. Map database citations to Bekker ranges
3. Retrieve via CTS using Bekker references

### Phase 3: Book.Chapter Works (15-20 hours)
**Target:** Works using hierarchical citations

| Work | Citations | Format | Example |
|------|-----------|--------|---------|
| Aulus Gellius, NA | 27 | Book.Chapter | VII.2, XIV.1 |
| Plotinus, Enneads | 24 | Ennead.Tractate | III.1, I.6 |
| Epictetus, Discourses | 13 | Book.Chapter | I.1, II.2 |
| Plutarch, De Stoic. Rep. | 16 | Sections | Various |

**Action:**
1. Parse book.chapter citations
2. Test CTS URN patterns
3. Batch retrieve

### Phase 4: Patristic Texts (OGL Sources) (25-35 hours)
**Target:** Early Christian authors

| Work | Citations | Source | Format |
|------|-----------|--------|--------|
| Origen, De Principiis | 26 | OGL CSEL or PG | TEI-XML |
| Origen, Contra Celsum | 18 | OGL or PG | TEI-XML |
| Augustine (various) | 138 | OGL CSEL | TEI-XML |
| Eusebius, Praep. Evang. | 15 | OGL or PG | TEI-XML |
| Nemesius, De Nat. Hom. | 14 | PG | TEI-XML |

**Action:**
1. Explore OGL GitHub repositories
2. Identify specific work files
3. Parse TEI-XML format
4. Extract cited passages
5. Fallback to PG digitized texts where needed

### Phase 5: Biblical Texts (15-20 hours)
**Target:** NT and OT citations

| Text | Citations | Source | Standard |
|------|-----------|--------|----------|
| Romans | 29 | BibleHub / STEP Bible | NA28 Greek |
| Hebrew Bible | 25 | Sefaria / WTT | BHS/WTT |
| Galatians | 15 | BibleHub | NA28 |
| Septuagint (LXX) | 16 | CCAT / Rahlfs | Rahlfs-Hanhart |
| Other NT books | ~30 | BibleHub | NA28 |

**Action:**
1. Use BibleHub API/scraping for NT Greek
2. Use Sefaria API for Hebrew Bible
3. Source LXX from CCAT or academic repositories
4. Parse by chapter.verse

### Phase 6: Long Tail (30-40 hours)
**Target:** 1,000+ works with 1-5 citations each

**Strategy:**
1. **Triage:** Classify by source availability
   - CTS available → Automated retrieval
   - OGL available → TEI-XML parsing
   - Perseus old → Custom URL retrieval
   - Not digital → Flag for manual sourcing

2. **Batch by similarity:**
   - Group works by same author/corpus
   - Use similar citation patterns
   - Parallel processing

3. **Manual review queue:**
   - Fragmentary texts
   - Uncertain citations
   - Missing digital sources

---

## Technical Implementation

### Citation Parser (Priority #1)
```python
class CitationParser:
    """Parse database citations to retrieval parameters"""

    def parse(self, citation: str) -> dict:
        """
        Input: "Aristotle, NE III.5 (1113b-1114b)"
        Output: {
            'author': 'Aristotle',
            'work': 'Nicomachean Ethics',
            'book': 'III',
            'chapter': '5',
            'bekker_start': '1113b',
            'bekker_end': '1114b',
            'urn_base': 'urn:cts:greekLit:tlg0086.tlg010'
        }
        """
```

### Bekker Page Mapper
```python
class BekkerMapper:
    """Map Bekker pages to CTS passages"""

    BEKKER_PAGES = {
        '1109b': {...},  # Book III starts
        '1113b': {...},  # Eph' hêmin passage
        '1114b': {...},
        # Complete mapping for all Aristotle works
    }

    def bekker_to_cts(self, bekker: str) -> str:
        """Convert '1113b' → CTS passage reference"""
```

### TEI-XML Parser (For OGL)
```python
class TEIParser:
    """Parse TEI-XML from Open Greek & Latin"""

    def parse_file(self, xml_path: str) -> dict:
        """Extract text sections from TEI-XML"""

    def find_passage(self, xml, book, chapter, section):
        """Locate specific passage in TEI structure"""
```

### Master Retrieval Orchestrator
```python
class MasterRetriever:
    """Orchestrate all retrieval systems"""

    def __init__(self):
        self.cts_retriever = ScaifeCTSRetriever()
        self.ogl_retriever = OGLRetriever()
        self.biblical_retriever = BiblicalRetriever()
        self.citation_parser = CitationParser()

    def retrieve_all(self, citations: List[str]):
        """Main retrieval loop for all citations"""
        for citation in citations:
            parsed = self.citation_parser.parse(citation)

            if parsed['source_type'] == 'CTS':
                text = self.cts_retriever.get(parsed)
            elif parsed['source_type'] == 'OGL':
                text = self.ogl_retriever.get(parsed)
            elif parsed['source_type'] == 'BIBLICAL':
                text = self.biblical_retriever.get(parsed)

            self.save_with_metadata(text, parsed)
```

---

## Quality Assurance

### Every Retrieved Text Must Include:

```json
{
  "citation": "Original database citation",
  "text": {
    "original_language": "Greek/Latin/Hebrew text",
    "translation": "English translation"
  },
  "metadata": {
    "source": "Scaife CTS / OGL / etc.",
    "source_url": "Direct URL to text",
    "edition": "Critical edition details",
    "retrieved_date": "2025-10-25",
    "cts_urn": "urn:cts:... (if applicable)",
    "verification_status": "automated / manually_verified",
    "license": "Public domain / Fair use / CC-BY",
    "retrieval_method": "scaife_cts / ogl_xml / perseus_old",
    "confidence": "high / medium / needs_review"
  },
  "provenance": {
    "original_edition": "Specific critical edition",
    "translator": "For translations",
    "translation_year": "Publication year",
    "scholarly_references": ["Supporting scholarship"]
  }
}
```

### Verification Process
1. **Automated checks:**
   - Text not empty
   - Metadata complete
   - Source URL valid
   - License documented

2. **Spot checks:**
   - Sample 5% of retrievals
   - Verify text matches citation
   - Check translation accuracy (if available)

3. **Manual review queue:**
   - Low confidence retrievals
   - Ambiguous citations
   - Failed automated retrievals

---

## Progress Tracking

### Metrics to Monitor
- Citations retrieved / 1,491 total
- Success rate by source type
- Works completed / 1,072 total
- Hours invested / 150 estimated
- Passages needing manual review

### Milestones
- [ ] 10% (149 citations)
- [ ] 25% (373 citations)
- [ ] 50% (746 citations)
- [ ] 75% (1,118 citations)
- [ ] 90% (1,342 citations)
- [ ] 100% (1,491 citations)

### Status Reports
Generate progress report every:
- 50 citations retrieved
- 10 hours of work
- End of each Phase

---

## Next Actions (Immediate)

### Session Continuation Tasks:
1. **Build Citation Parser** (2 hours)
   - Parse all 1,491 citations
   - Classify by source type
   - Generate work queue

2. **Build Bekker Mapper** (3 hours)
   - Map Aristotle Bekker pages
   - Test with NE passages
   - Apply to all Aristotle works

3. **Retrieve Next 10 CTS Works** (5 hours)
   - Test citation patterns
   - Batch retrieve
   - Verify quality

4. **Set up OGL Parser** (4 hours)
   - Clone OGL repositories
   - Parse TEI-XML
   - Test with Origen

5. **Biblical Text Retrieval** (4 hours)
   - BibleHub scraping for NT
   - Sefaria API for OT
   - Parse by chapter:verse

**Target for next session:** 300-400 citations (20-25% coverage)

---

## Risk Mitigation

### Potential Issues:
1. **CTS URNs incorrect** → Test each before batch retrieval
2. **Citation ambiguous** → Flag for manual review
3. **Source unavailable** → Document in "needs_manual" queue
4. **Rate limiting** → Implement delays, respect robots.txt
5. **Parsing errors** → Extensive error handling + logging

### Contingencies:
- Multiple source fallbacks per work
- Manual review queue for failures
- Detailed logging for debugging
- Regular checkpoints/saves

---

## Success Criteria

### 100% Complete When:
- ✅ All 1,491 citations have retrieved texts OR documented as unavailable
- ✅ Every text has complete metadata and provenance
- ✅ All sources properly attributed
- ✅ Verification completed
- ✅ Integration into main database
- ✅ Zero hallucinated content
- ✅ Publication-ready quality

---

**Status:** Ready to continue systematic retrieval
**Next:** Build Citation Parser and start Phase 1
**Estimated completion:** 120-150 hours of focused work
