# Critical Fact-Checking Instructions for EleutherIA Database
## Essential Context for Continuing Deep Verification

---

## 🎯 MISSION CRITICAL
**ZERO TOLERANCE FOR ERRORS** - Every single fact, quote, date, and attribution must be 100% accurate for academic publication.

---

## 📋 COMPLETED FIXES (October 20, 2025)

### Biblical Corrections
1. **Ezekiel 18:20** - Fixed "that sins" → "who sins" (ESV), added Hebrew
2. **Romans 7:15** - Corrected Greek: οὐ γὰρ ὃ θέλω τοῦτο ποιῶ, ἀλλ' ὃ μισῶ τοῦτο πράσσω (NA28)

### Attribution Corrections
3. **Master Argument** - Added Diodorus Cronus (fl. 4th c. BCE, Megarian)
4. **Dog and Cart** - Attributed to Zeno/Chrysippus via Hippolytus

### Historical Corrections
5. **Augustine** - Removed "double predestination" error
6. **Origen** - Fixed double description, added dates (c. 185-254 CE)
7. **Epicurus** - Added dates (341-270 BCE), fixed swerve sources
8. **Carneades** - Period: Hellenistic (not Ancient Greek), dates 214-129 BCE

### Terminology Corrections
9. **CAFMA** - Clarified as MODERN acronym in Carneades and Clement
10. **Confatalia** - Added Greek συμπεπλεγμένα and proper explanation

---

## 🔍 VERIFICATION METHODOLOGY

### For Biblical Quotes
**ALWAYS CHECK:**
- **Greek NT**: NA28 (Nestle-Aland 28th edition)
- **Hebrew OT**: BHS (Biblia Hebraica Stuttgartensia)
- **LXX**: Rahlfs-Hanhart edition
- **English**: ESV for translation (specify when used)

**FORMAT:**
```
'Quote text here' (Book Chapter:Verse, Translation).
[Original: Greek/Hebrew text if relevant]
```

### For Ancient Philosophers
**VERIFY:**
1. **Dates**: Birth-death BCE/CE
2. **School/Period**:
   - Classical (5th-4th c. BCE)
   - Hellenistic (3rd-1st c. BCE)
   - Roman Imperial (1st-3rd c. CE)
   - Patristic (2nd-5th c. CE)
3. **Key Works**: Correct titles in original language
4. **Attributions**: Primary sources for doctrines

### For Philosophical Arguments
**CHECK:**
1. **Creator**: Who formulated it?
2. **Source**: Where is it preserved? (e.g., "preserved in Epictetus, Diss. 2.19")
3. **Content**: Is the description accurate?
4. **Technical Terms**: Greek/Latin with proper diacriticals

---

## ⚠️ COMMON ERRORS TO WATCH FOR

### 1. Anachronisms
- **CAFMA** - Modern scholarly acronym, NOT ancient
- **"Double predestination"** - Reformed, not Augustinian
- Modern philosophical terms projected onto ancients

### 2. Wrong Attributions
- Master Argument → **Diodorus Cronus** (not anonymous)
- Cylinder analogy → **Chrysippus** (not generic Stoic)
- Swerve → Known through **Lucretius/Cicero** (not Epicurus directly)

### 3. Period Misclassifications
- Carneades → **Hellenistic** (not Ancient Greek)
- Chrysippus → **Hellenistic** (not Ancient Greek)
- Marcus Aurelius → **Roman Imperial** (not Hellenistic)

### 4. Incomplete Quotes
- Check Greek/Hebrew is COMPLETE
- Romans 7:15 was missing second half
- Verify against critical editions

### 5. Missing Context
- Diodorus Cronus died c. 284 BCE
- Carneades headed Academy from 155 BCE
- Alexander of Aphrodisias fl. 200 CE

---

## 📚 CRITICAL SOURCES TO USE

### Primary Source Collections
- **SVF** - Stoicorum Veterum Fragmenta (von Arnim)
- **DL** - Diogenes Laertius, Lives of Philosophers
- **LS** - Long & Sedley, The Hellenistic Philosophers

### For Specific Traditions
- **Stoics**: Cicero De Fato, Marcus Aurelius Meditations
- **Epicureans**: Lucretius DRN, Cicero De Finibus
- **Academics**: Cicero Academica, Sextus Empiricus
- **Christians**: Origen De Principiis, Augustine De Libero Arbitrio

---

## 🔄 VERIFICATION PROCESS

### Step 1: Random Sampling
```python
import random
random.seed(XXX)  # Use different seeds
# Select random nodes of each type
# Check for accuracy
```

### Step 2: Deep Research
For EACH error found:
1. Research the correct information
2. Find primary sources
3. Verify in multiple references
4. Fix with full context

### Step 3: NO AUTOMATED SCRIPTS
- Manual checking ensures deep thinking
- Read each correction carefully
- Understand WHY it's wrong
- Choose the BEST fix

---

## 🚨 CURRENT DATABASE STATUS

**File**: `ancient_free_will_database.json`
- **Nodes**: 3,414
- **Edges**: 813
- **Last Major Fix**: October 20, 2025

**Known Issues Still to Check:**
- Other biblical quotes for accuracy
- All person dates and periods
- Technical philosophical terms
- Argument attributions
- Work authorship claims
- Concept definitions

---

## 📝 WHEN CONTINUING WORK

### Load Database
```python
import json
with open('ancient_free_will_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
```

### Find Specific Issues
```python
# Example: Find all biblical quotes
biblical = [n for n in db['nodes']
           if n.get('type') == 'quote'
           and any(book in str(n) for book in ['Romans', 'Corinthians', 'Genesis'])]

# Example: Find persons missing dates
no_dates = [n for n in db['nodes']
           if n.get('type') == 'person'
           and 'BCE' not in str(n) and 'CE' not in str(n)]
```

### Fix Pattern
```python
# ALWAYS use Edit tool for precise fixes
# NEVER use replace_all without checking each instance
# Document what you're fixing and why
```

---

## ⚡ PRIORITY CHECKS REMAINING

1. **All Biblical quotes** against NA28/BHS
2. **All Hellenistic philosophers** - verify periods
3. **All "modern" terms** - check for anachronisms
4. **All argument attributions** - verify creators
5. **All dates** - check against standard references
6. **All Greek/Latin terms** - verify spelling/diacriticals
7. **All "receptions"** - ensure ancient/modern distinction clear

---

## 🎯 REMEMBER

**Every error matters!** This is for academic publication. When in doubt:
1. Research thoroughly
2. Cite primary sources
3. Use critical editions
4. Specify translations
5. Add dates and context
6. Distinguish ancient from modern terminology

**THE GOAL**: A database with ZERO errors, suitable for peer-reviewed academic publication.

---

*Created: October 20, 2025*
*Purpose: Preserve context for continued fact-checking of EleutherIA database*
*Critical: NO AUTOMATED FIXES - only careful, researched corrections*