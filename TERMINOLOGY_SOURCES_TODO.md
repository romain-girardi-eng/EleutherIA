# TERMINOLOGY & SOURCES - MANUAL WORK REQUIRED

**Status:** Awaiting your guidance on HOW to proceed
**Priority:** HIGH - Needed for publication quality

---

## SUMMARY OF REMAINING WORK

After flagging 129 reception_history nodes, I've identified what still needs manual attention:

### 1. GRECO-ROMAN CONCEPTS NEEDING GREEK/LATIN TERMINOLOGY

**43 ancient Greco-Roman concepts** currently lack `greek_term` or `latin_term` fields.

**Examples:**
- Cosmic Sympathy (Sympathia Universalis) - Stoic concept
- Perfect vs. Antecedent Causes - Chrysippus
- Natal Astrology (Genethlialogia) - Hellenistic
- School Handbooks (Hypomnemata) - Transmission
- Gratia Praeveniens/Operans/Cooperans - Patristic Latin concepts
- Theosis (Deification) - Patristic Greek concept
- Original Sin (Peccatum Originale) - Augustine
- Concupiscence (Concupiscentia) - Patristic

Many of these HAVE the Greek/Latin in their label (e.g., "Sympathia Universalis", "Peccatum Originale") but it's not in a structured field.

### 2. OUT-OF-SCOPE CONCEPTS THAT SLIPPED THROUGH

**Hebrew/Jewish concepts (5):**
- Evil Inclination (Yetzer Ha-Ra) - Rabbinic
- Good Inclination (Yetzer Ha-Tov) - Rabbinic
- Choice/Free Will (Bechirah) - Hebrew
- Will/Desire (Ratzon) - Hebrew
- Two Spirits Doctrine - Qumran

**Modern/Enlightenment concepts (need reception_history flag):**
- Transcendental Freedom - Kant
- Autonomy - Kant
- Categorical Imperative - Kant
- Covenant Nomism - E.P. Sanders (1977)

### 3. NODES MISSING SOURCES (76 total)

**50 person nodes** without `ancient_sources` or `modern_scholarship`
**15 concept nodes** without sources
**9 work nodes** without sources
**2 argument nodes** without sources

---

## MY QUESTIONS FOR YOU

### Question 1: Hebrew/Jewish Concepts

You have 5 Hebrew/Jewish concepts (Yetzer Ha-Ra, Bechirah, Ratzon, etc.) that are:
- Not Greco-Roman
- Not in Greek or Latin
- From Second Temple Judaism / Rabbinic tradition

**Options:**
- A) **Remove them** (strict Greco-Roman scope)
- B) **Keep as reception history** (Jewish context for Paul, Origen, etc.)
- C) **Keep and add Hebrew terms** (expand scope to include Jewish sources)

**Your decision?**

### Question 2: How to Add Terminology - YOUR WORKFLOW PREFERENCE

For the 43 Greco-Roman concepts needing Greek/Latin terms, HOW do you want me to work?

**Option A: I extract from labels**
- Many concepts already have Greek/Latin in their labels
- Example: "Sympathia Universalis" → add `latin_term: "sympathia universalis"`
- Example: "Peccatum Originale" → add `latin_term: "peccatum originale"`
- **Risk:** Low (it's already in the database)
- **Speed:** Fast
- **Your approval?** ___________

**Option B: You provide the terms**
- I give you a list of the 43 concepts
- You tell me the exact Greek/Latin for each
- I add them exactly as you specify
- **Risk:** Zero
- **Speed:** Slow (depends on your time)
- **Your preference?** ___________

**Option C: I search your PhD files**
- I search `.archive_20251019/` for each concept
- Only add if I find the exact Greek/Latin in your research
- Skip if not found
- **Risk:** Very low (your own research)
- **Speed:** Medium
- **Your preference?** ___________

**Option D: Combination**
- Extract from labels when obvious
- Search PhD files for uncertain cases
- Flag remaining for your review
- **Your preference?** ___________

### Question 3: Sources - YOUR WORKFLOW PREFERENCE

For the 76 nodes missing sources:

**Option A: I add from standard references**
- Use top-tier scholarship (Bobzien, Frede, Sorabji, Long & Sedley, etc.)
- Only add sources I'm confident about
- Flag uncertain cases for your review
- **Your approval?** ___________

**Option B: You provide sources**
- I give you list of 76 nodes needing sources
- You specify exact sources
- I add them
- **Your preference?** ___________

**Option C: I search your PhD bibliography**
- Extract sources from your `.archive_20251019/` files
- Only add if explicitly mentioned in your research
- **Your preference?** ___________

### Question 4: Date Field Standardization

Person nodes currently use 4 different date fields. Which format do you prefer?

**Option A: Keep flexible text field**
```json
{
  "date": "c. 384-322 BCE"
}
```

**Option B: Structured numeric fields**
```json
{
  "birth_year": -384,
  "death_year": -322,
  "circa": true
}
```

**Option C: Both (for querying + display)**
```json
{
  "date": "c. 384-322 BCE",
  "birth_year": -384,
  "death_year": -322
}
```

**Your preference?** ___________

---

## WHAT I NEED FROM YOU

Please tell me:

1. **Hebrew concepts:** Remove / Keep as reception / Keep and add Hebrew terms?
2. **Terminology method:** A / B / C / D from above?
3. **Sources method:** A / B / C from above?
4. **Date format:** A / B / C from above?

Once you decide, I'll proceed carefully and manually with zero hallucination risk.

---

## CURRENT STATUS

✅ **DONE:**
- Flagged 129 reception_history nodes
- All 14 quote nodes complete with Greek/Latin
- Database structure sound

⏳ **AWAITING YOUR GUIDANCE:**
- How to add 43 Greek/Latin terms (method?)
- How to add 76 source citations (method?)
- What to do with Hebrew concepts (keep/remove?)
- Date field format preference

**I'm ready to proceed once you provide guidance on your preferred workflow.**
