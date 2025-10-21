# NEXT SESSION PRIORITIES
## Continuation Guide for Academic Source Integration

**Current Version:** 1.0.2 (506 nodes, 818 edges)
**Last Session:** Session 7 - Bobzien integration
**Status:** ✅ COMMITTED TO GIT

---

## WHAT WAS COMPLETED (Sessions 6-7)

### Session 6 (v1.0.1):
✅ Added 10 Patristic concept descriptions
✅ Removed 2 duplicate nodes
✅ Enhanced 2 contemporary concepts
✅ 100% concept description coverage

### Session 7 (v1.0.2):
✅ Enhanced eph' hêmin with Bobzien's two-sidedness distinction
✅ Created exousia (ἐξουσία) concept - Alexander's innovation
✅ Created epi ison (ἐπὶ ἴσον) concept - Middle-Platonist
✅ Enhanced Alexander of Aphrodisias person node

---

## HIGH-PRIORITY NEXT STEPS

### 1. **Add SVF References to Chrysippus** (Bobzien 2001)
**Source:** `bobzien_2001_extraction_summary.txt`
**Data Available:** 50 Chrysippus-specific passages, 17 SVF fragments

**Node to Enhance:** `person_chrysippus_280_206bce_i9j0k1l2`

**SVF References to Add:**
- SVF I 98, I 160
- SVF II 198, 202, 912, 943, 957, 963, 973, 978, 981, 988, 991, 998, 1007
- SVF III 356, 359

**Key Arguments to Reference:**
- Cylinder analogy (84 passages)
- Confatalia (7 passages)
- Modal logic (30 passages)

---

### 2. **Update Middle-Platonist Person Nodes**
**Source:** Bobzien 1998 extraction summary

**Nodes to Enhance:**

#### **Alcinous:**
Currently: `work_didaskalikos_alcinous_2nd_ce_q7r8s9t0` (work node)
Need: Find/create person node for Alcinous

**Add Citations:**
- Didaskalikos 26 (179.8-33) - threefold contingency
- Didaskalikos 179.10-11 - soul as master
- Didaskalikos 179.20-23 - nature of possible
- Didaskalikos 179.31-33 - possible and eph' hêmin

**Add Quote:**
```
Ἡ δὲ τοῦ δυνατοῦ φύσις πέπτωκε μὲν πως μεταξὺ τοῦ τε ἀληθοῦς καὶ τοῦ ψεύδους
```

#### **Nemesius:**
Node: `person_nemesius_of_emesa_5t0u2w98`

**Add Citations:**
- De Natura Hominis 103-104 - classification of non-necessary things
- De Natura Hominis 104.1-7 - threefold contingency
- De Natura Hominis 114.19-22, 115.22-28, 116.3-5 - epi ison = eph' hêmin
- Definition: "αὐτό τε δυνάμεθα καὶ τὸ ἀντικείμενον αὐτῷ"

#### **Calcidius:**
Not currently in database - CREATE NEW

**Create:** `person_calcidius_4th_ce_[hash]`
**Add Citations:**
- In Timaeum 142-187 - fate theory
- In Timaeum 151 - freedom of decision
- In Timaeum 154 - Plato's "αἰτία ἑλομένου" (Rep. 617e)
- In Timaeum 155-156 - things not fated
- In Timaeum 160-161 - critique of Stoic fate

**Add Latin Quote:**
```
Collocati autem in alterutram partem... quae sunt in nobis posita,
quoniam tam horum quam eorum quae his contraria sunt optio penes nos est.
```

---

### 3. **Enhance Stoic Argument Nodes**

#### **Cylinder Analogy:**
Node: `argument_cylinder_analogy_chrysippus_k1l2m3n4`

**Add Precise Sources (Bobzien 2001):**
- Gellius, Noctes Atticae VII.2.6-13 (primary source)
- Cicero, De Fato §§42-43
- Aulus Gellius VII.2
- Alexander of Aphrodisias, De Fato 13

**Add Analysis:** 84 passages extracted from Bobzien 2001

#### **Confatalia (Co-fated Events):**
Node: `argument_the_cofated_events_argument_confatalia_b7715646`

**Add Enhanced Description (Bobzien 2001):**
- Chrysippus' distinction: simple vs. conjoined events
- Example: "You will recover" vs. "You will recover IF you call a doctor"
- Key to refuting Lazy Argument
- 7 passages extracted from Bobzien 2001

**Add Modern Scholarship:**
- Bobzien 2001, detailed analysis of confatalia

---

### 4. **Create New Argument Nodes**

Based on Bobzien 1998, create:

#### **Middle-Platonist Synthesis Argument:**
- Integration of Aristotle's EN III + Int. 9 + Int. 12-13 + Met. Θ
- Threefold contingency framework
- Connection of future contingents with ethics
- Representatives: Alcinous, Nemesius, Calcidius

#### **Bobzien's "Mix-Up Thesis":**
- Free-will problem emerged from misinterpretation
- Aristotle's non-indeterminist two-sided eph' hêmin
- Misread in light of Stoic determinism
- Alexander's indeterminist resolution

---

### 5. **Create Edges for New Concepts**

**Connect exousia concept to:**
- Alexander of Aphrodisias (formulated relation)
- Epictetus (influenced relation)
- eph' hêmin concept (related_to)

**Connect epi ison concept to:**
- Alcinous (employed relation)
- Nemesius (employed relation)
- Calcidius (employed relation)
- [Plutarch] De Fato (employed relation)
- eph' hêmin concept (identified_with)

---

## ADDITIONAL SOURCES AVAILABLE

### In `.archive_20251019/01_pdf_text_chunks/`:

1. **Frede 2011** - *A Free Will: Origins of the Notion in Ancient Thought*
   - Available for extraction
   - Focus on ἐλευθερία vs. ἐφ' ἡμῖν

2. **Dihle 1982** - *The Theory of Will in Classical Antiquity*
   - Available for extraction

3. **Fürst 2022** - *Wege zur Freiheit* (French translation)
   - Available for extraction
   - Homer to Origen

---

## SKILL AGENT GUIDANCE

**Location:** `skills/ancient-philosophy-db/`

**Key Files:**
- `SKILL.md` - Main guidelines
- `controlled-vocabularies.md` - Node types, relations, periods, schools
- `citation-standards.md` - Ancient source formats
- `terminology-conventions.md` - Greek/Latin transliterations
- `validation-checklist.md` - Quality assurance

**Remember:**
- ✅ Zero hallucination policy
- ✅ Controlled vocabularies only
- ✅ Specific passage citations
- ✅ Greek/Latin terminology preserved
- ✅ FAIR compliance

---

## STARTING YOUR NEXT SESSION

**Recommended Opening Prompt:**

```
Continue enhancing the Ancient Free Will Database using PhD source
materials in .archive_20251019.

Last session (Session 7) completed:
- Enhanced eph' hêmin concept with Bobzien's two-sidedness
- Created exousia and epi ison concepts
- Enhanced Alexander of Aphrodisias
- Database now at v1.0.2 (506 nodes, 818 edges)

Next priorities from NEXT_SESSION_PRIORITIES.md:
1. Add SVF references to Chrysippus (50+ passages from Bobzien 2001)
2. Update Middle-Platonist persons (Alcinous, Nemesius, Calcidius)
3. Enhance Stoic argument nodes (cylinder analogy, confatalia)
4. Create edges connecting new exousia and epi ison concepts

Use skill agent in skills/ancient-philosophy-db/ for guidance.
Continue with zero-hallucination academic rigor.
```

---

## EXPECTED OUTCOMES

**Next Session Target:**
- Enhance 10-15 more nodes
- Add 50-100 ancient source citations from Bobzien
- Create 5-10 new edges
- Version: 1.0.3 or 1.0.4

**Long-Term Goal:**
- Integrate all PhD source materials
- 20-30 total enhancements from Bobzien 1998, 2001
- Extract key findings from Frede 2011, Dihle 1982
- Create comprehensive edge network
- Version: 1.1.0 (major enhancement milestone)

---

**Status:** ✅ READY TO CONTINUE
**Current Version:** 1.0.2
**Git:** All changes committed
**Quality:** TOP-LEVEL ACADEMIC STANDARD

---

END OF NEXT SESSION PRIORITIES
