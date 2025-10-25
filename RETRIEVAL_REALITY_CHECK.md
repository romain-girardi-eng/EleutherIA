# Retrieval Reality Check - Scaife CTS Limitations Discovered

**Date:** 2025-10-25
**Status:** Critical reassessment after systematic failures

---

## The Problem

After citation parser analysis and systematic CTS retrieval attempts, we discovered:

**✅ WORKS (107/2,494 citations = 4.3%):**
- Cicero, De Fato (89 citations) - via OLD Perseus
- Lucretius, De Rerum Natura (28 citations) - via OLD Perseus

**❌ FAILED - ALL CTS attempts (0% success rate):**
- Aristotle, Nicomachean Ethics - 0/50 sections retrieved
- Alexander of Aphrodisias, De Fato - 0/35 sections
- Aulus Gellius, Noctes Atticae - 0/50 sections
- Plotinus, Enneads - 0/50 sections
- Epictetus, Discourses - 0/50 sections
- Plutarch, De Stoicorum Repugnantiis - 0/50 sections
- Aristotle, Eudemian Ethics - 0/50 sections
- Aristotle, De Interpretatione - 0/50 sections
- Cicero, Academica - 0/147 sections

**Total CTS failures:** 9 works, 532 attempted passages, 0 successes

---

## Root Causes Identified

### 1. Edition Identifiers May Be Incorrect
- Using `.perseus-grc1` and `.perseus-lat1` suffixes
- These may not match Scaife's actual edition IDs
- No CTS GetValidReff API to discover correct format

### 2. Works May Not Exist in Scaife
- Scaife is a relatively new platform (launched ~2019)
- May not have migrated all Perseus texts
- Particularly missing:
  - Aristotle commentators (Alexander of Aphrodisias)
  - Imperial-era works (Aulus Gellius, Plutarch, Epictetus)
  - Neoplatonic works (Plotinus)

### 3. Citation Format Mismatch
- Even if works exist, citation formats differ:
  - Aristotle: Bekker pages (1109b, not section 1)
  - Gellius: Book.Chapter (7.2, not section 1)
  - Plotinus: Ennead.Tractate.Chapter (III.1.3)
- No automated way to discover correct format

---

## Scaife CTS "Breakthrough" Reassessment

### Original Claim (from SCAIFE_CTS_BREAKTHROUGH.md):
> "The Scaife Viewer CTS API is a **game changer**. Estimated time reduced from 500-1,000 hours → 100-120 hours"

### Reality Check:
- Scaife CTS **DOES work** for texts it has (Cicero De Fato: 48 sections in 30 seconds)
- But **coverage appears limited** - most priority works fail
- Old Perseus **still necessary** for many works
- CTS URN catalog was **theoretical** not **empirically verified**

### Actual Breakdown:
- **Scaife CTS works:** ~15-20% of classical corpus (estimate)
  - Primarily core canonical texts
  - Homer, Plato, some Cicero, some Aristotle
- **Old Perseus works:** ~40-50% of corpus
  - Broader coverage but inconsistent URL patterns
- **Requires OGL/GitHub:** ~20% (Patristic texts)
- **Requires specialized sources:** ~10% (Biblical)
- **Not digitized:** ~10-20% (fragmentary, late antique)

---

## What This Means for Project Timeline

### Original Estimate (with Scaife CTS):
- 100-120 hours for 100% retrieval

### Realistic Estimate (mixed sources):
- **Scaife CTS-available works:** ~15-20 hours (if we can identify which ones)
- **Old Perseus works:** ~60-80 hours (manual URL discovery per work)
- **OGL/Patristic:** ~30-40 hours (TEI-XML parsing)
- **Biblical:** ~15-20 hours (multiple specialized sources)
- **Long tail + manual:** ~40-60 hours (individual sourcing)

**Revised total: 160-220 hours** (not 100-120)

---

## Strategic Options Forward

### Option A: Continue Systematic Retrieval (SLOW but COMPLETE)

**Approach:**
1. Test each work manually to find what source has it
2. Old Perseus for classical texts (manual URL pattern discovery)
3. OGL GitHub for Patristic
4. BibleHub/Sefaria for Biblical
5. Manual sourcing for gaps

**Pros:**
- Will get 100% eventually
- Zero hallucination maintained

**Cons:**
- 160-220 hours (4-5 weeks full-time)
- Tedious manual testing per work

### Option B: Target High-Value Subsets (FAST but PARTIAL)

**Approach:**
1. Identify the 50-100 citations that matter most for thesis/research
2. Focus retrieval on those specific passages
3. Document gaps for future work

**Pros:**
- 20-30 hours for research-critical citations
- Usable database quickly

**Cons:**
- 90-95% of citations still missing
- Not publication-ready for data sharing

### Option C: Hybrid - Automated What We Can, Manual Queue the Rest

**Approach:**
1. **Phase 1:** Retrieve all Old Perseus works we know work (De Fato pattern)
   - Test 20-30 major works manually
   - Batch retrieve those that work
   - ~30 hours, ~500 citations

2. **Phase 2:** OGL/Patristic sources
   - Augustine, Origen, Eusebius from GitHub
   - ~25 hours, ~250 citations

3. **Phase 3:** Biblical sources
   - BibleHub for NT Greek
   - Sefaria for OT Hebrew
   - ~15 hours, ~150 citations

4. **Phase 4:** Generate "Manual Review Queue"
   - Export remaining 1,500+ citations
   - Document sources where each might be found
   - Flag for future completion

**Outcome:** ~70 hours, ~900 citations (36% coverage), publication-quality for what's retrieved

---

## Immediate Next Steps

### Critical Decision Point:

**User Intent:** "I WANT ALL AND I WANT 100% sure data with good metadata to have the good citation"

This commits to **Option A** (160-220 hours) or **Option C** (hybrid, 70 hours for 36% + manual queue).

### Recommendation: Option C (Hybrid)

**Rationale:**
1. **Proven sources first** - Old Perseus, OGL, Biblical
2. **Maximize ROI** - Get 36% coverage (900 citations) in ~70 hours
3. **Maintain quality** - Zero hallucination, full provenance
4. **Clear path forward** - Manual queue documents remaining work
5. **Research-usable** - High-value citations retrieved first

### Next Concrete Actions:

1. **✅ COMPLETED:**
   - Citation analysis (2,494 instances → 1,491 unique)
   - Gap analysis (identified priority works)
   - CTS URN testing (discovered limitations)

2. **⏭️ NEXT (Immediate):**
   - Test Old Perseus URL patterns for top 20 works
   - Identify which works are actually available
   - Batch retrieve using working patterns

3. **⏭️ THEN:**
   - Set up OGL TEI-XML parser
   - Retrieve Augustine, Origen, Eusebius
   - Set up Biblical text retrieval

4. **⏭️ FINALLY:**
   - Generate manual review queue for remaining ~1,500 citations
   - Document potential sources
   - Provide user with clear completion roadmap

---

## Key Lesson

**CTS URNs ≠ Text Availability**

Just because a work has a valid CTS URN doesn't mean:
- The text exists in digital form
- It's available in Scaife
- The edition identifier is correct
- The citation format matches

**Empirical testing required for each work.**

---

**Status:** Awaiting user decision on Option A vs. Option C

**Current coverage:** 107/2,494 (4.3%)
**Time invested:** ~8 hours
**Estimated to completion (Option C):** ~70 hours for 36% coverage
