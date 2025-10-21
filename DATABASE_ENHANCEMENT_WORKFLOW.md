# Database Enhancement Workflow

**Using the Agent Skill to Systematically Improve Academic Quality**

This guide shows you how to use the Agent Skill to audit and enhance your entire Ancient Free Will Database to the highest academic standards.

---

## Overview

The Agent Skill provides:
1. **Automated Audit** - Python script identifies all issues
2. **Systematic Enhancement** - Claude fixes issues using skill standards
3. **Quality Assurance** - Validation at each step
4. **Progress Tracking** - Track improvements over time

---

## Step 1: Run the Audit

### Generate Audit Report

```bash
cd "/Users/romaingirardi/Documents/Ancient Free Will Database"
python3 scripts/audit_database_academic_quality.py
```

This creates `DATABASE_AUDIT_REPORT.md` with:
- **Academic Quality Score** (0-100)
- **Critical Issues** - Must fix
- **Warnings** - Should fix
- **Enhancement Opportunities** - Nice to have
- **Statistics** - Node/edge counts

### Review the Report

Open `DATABASE_AUDIT_REPORT.md` and note:
- Overall quality score
- Number of critical issues
- Top issue categories
- Priority areas for improvement

---

## Step 2: Systematic Enhancement with Claude

### Enhancement Priority Levels

**Priority 1: Critical Issues** (Fix First)
- Missing required fields
- Invalid controlled vocabulary
- Malformed node IDs
- Missing citations on critical nodes

**Priority 2: Academic Completeness** (Fix Second)
- Missing ancient sources
- Missing modern scholarship
- Incomplete person/concept/argument data
- Missing Greek/Latin terminology

**Priority 3: Quality Enhancements** (Optional)
- Expand brief descriptions
- Add key concepts
- Cross-reference related nodes
- Verify citation accuracy

---

## Step 3: Work with Claude

### Example Workflow: Fix Critical Issues

**You**:
```
I've run the audit script and found 15 nodes with critical issues.
Here's the first one:

{
  "node_id": "concept_xyz",
  "label": "Some Concept",
  "issues": [
    "Missing both ancient sources AND modern scholarship",
    "Missing Greek or Latin terminology"
  ]
}

Can you help me fix this node?
```

**Claude** (using the Agent Skill will):
1. Load SKILL.md + relevant reference files
2. Ask you for:
   - Ancient sources where this concept appears
   - Greek/Latin terminology
   - Modern scholarship (if available)
3. Generate properly formatted updates:
```json
{
  "ancient_sources": ["Aristotle, NE III.1-5"],
  "greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
  "english_term": "in our power",
  "modern_scholarship": ["Bobzien 1998"]
}
```
4. Validate against skill standards
5. Apply updates to database

---

### Example Workflow: Batch Enhancement

**For Multiple Similar Issues**:

```
I have 20 concept nodes missing Greek terminology. Can you help me
create a systematic approach to add Greek terms to all of them?

Here are the first 5 concepts:
1. "Voluntary Action"
2. "Rational Choice"
3. "Self-Determination"
4. "Fate"
5. "Necessity"
```

**Claude will**:
1. Load terminology-conventions.md
2. For each concept:
   - Identify the Greek term
   - Provide proper Unicode
   - Give transliteration
   - Format according to skill standards
3. Generate batch updates you can apply

---

### Example Workflow: Validate Existing Content

**You**:
```
Can you check if all my Stoic philosopher nodes have proper citations
and complete information according to the skill standards?
```

**Claude will**:
1. Load controlled-vocabularies.md (verify "Stoic")
2. Load validation-checklist.md
3. Query database for Stoic persons
4. Check each against standards:
   - Ancient sources present?
   - Dates formatted correctly?
   - School field uses "Stoic"?
   - Position on free will stated?
5. Report findings with specific recommendations

---

## Step 4: Enhancement Patterns

### Pattern 1: Add Missing Citations

**For nodes missing ancient sources**:

1. Identify the person/concept/argument
2. Research primary sources (Perseus, TLG, etc.)
3. Ask Claude: "What's the proper citation format for Aristotle's Nicomachean Ethics Book 3?"
4. Claude loads citation-standards.md and provides: `Aristotle, NE III.1-5`
5. Add to node's `ancient_sources` array
6. Validate with skill

### Pattern 2: Complete Greek/Latin Terminology

**For concepts missing terminology**:

1. Identify the Greek or Latin term
2. Ask Claude: "How should I format the Greek term 'eph' hemin'?"
3. Claude loads terminology-conventions.md
4. Provides three-part format:
   - Original: `ἐφ' ἡμῖν`
   - Transliteration: `eph' hêmin`
   - English: `in our power`
5. Update node with all three forms
6. Update label: `Eph' hêmin (τὸ ἐφ' ἡμῖν) - In Our Power`

### Pattern 3: Fix Invalid Controlled Vocabulary

**For nodes with invalid types/relations**:

1. Audit identifies: "Invalid node type: 'philosopher'"
2. Ask Claude: "What's the correct node type for individual philosophers?"
3. Claude loads controlled-vocabularies.md
4. Reports: "Use 'person' for individual philosophers"
5. Update node type
6. Validate schema

### Pattern 4: Expand Brief Descriptions

**For nodes with short descriptions**:

1. Audit flags: "Description too brief (< 50 chars)"
2. Ask Claude: "Can you help expand the description for [node] based on these sources: [citations]?"
3. Claude:
   - Checks sources (if you provide)
   - Generates academically rigorous description
   - Includes key concepts
   - Maintains citation trail
4. Review and approve
5. Update node

---

## Step 5: Quality Assurance

### After Each Batch of Changes

**Run Validation**:

```bash
# Validate against schema
python3 -c "
import json
import jsonschema

with open('schema.json') as f:
    schema = json.load(f)
with open('ancient_free_will_database.json') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print('✓ Database validates successfully!')
"
```

**Re-run Audit**:

```bash
python3 scripts/audit_database_academic_quality.py
```

**Check Progress**:
- Has the Academic Quality Score improved?
- How many critical issues remain?
- What's the next priority?

---

## Step 6: Track Progress

### Create Enhancement Log

Keep a log of enhancements:

```markdown
# Database Enhancement Log

## 2025-10-21 - Initial Audit
- Quality Score: 72/100
- Critical Issues: 25
- Warnings: 48

## 2025-10-22 - Session 1: Fix Citations
- Added ancient sources to 15 concept nodes
- Added modern scholarship to 10 person nodes
- Quality Score: 78/100 (+6)

## 2025-10-23 - Session 2: Greek Terminology
- Added Greek terms to 20 concept nodes
- Fixed 12 transliteration errors
- Quality Score: 84/100 (+6)

## Goal: 90/100 by end of month
```

---

## Common Enhancement Scenarios

### Scenario 1: Node Missing Ancient Sources

**Before**:
```json
{
  "id": "concept_xyz",
  "label": "Free Will",
  "type": "concept",
  "description": "The concept of free will...",
  "ancient_sources": []
}
```

**With Claude + Skill**:

You: "This concept node has no citations. Where should I cite for the general concept of free will in Stoicism?"

Claude: "For Stoic free will, cite:
- `Epictetus, Discourses I.1.1-5` (core treatment)
- `Cicero, De Fato §§39-44` (Latin transmission)
- Modern: `Bobzien, Susanne. Determinism and Freedom in Stoic Philosophy. Oxford, 1998.`"

**After**:
```json
{
  "id": "concept_xyz",
  "label": "Free Will",
  "type": "concept",
  "description": "The Stoic concept of free will...",
  "ancient_sources": [
    "Epictetus, Discourses I.1.1-5",
    "Cicero, De Fato §§39-44"
  ],
  "modern_scholarship": [
    "Bobzien, Susanne. Determinism and Freedom in Stoic Philosophy. Oxford, 1998."
  ]
}
```

---

### Scenario 2: Concept Missing Greek Terminology

**Before**:
```json
{
  "id": "concept_voluntary_action",
  "label": "Voluntary Action",
  "type": "concept",
  "description": "Aristotelian concept of voluntary action..."
}
```

**With Claude + Skill**:

You: "Add Greek terminology for Aristotelian voluntary action"

Claude: "The Greek term is hekousion. Here's the complete format:
```json
{
  "greek_term": "ἑκούσιον (hekousion)",
  "english_term": "voluntary",
  "label": "Hekousion (Ἑκούσιον) - Voluntary Action"
}
```"

**After**:
```json
{
  "id": "concept_voluntary_action",
  "label": "Hekousion (Ἑκούσιον) - Voluntary Action",
  "type": "concept",
  "description": "Aristotelian concept of voluntary action...",
  "greek_term": "ἑκούσιον (hekousion)",
  "english_term": "voluntary"
}
```

---

### Scenario 3: Person Node Incomplete

**Before**:
```json
{
  "id": "person_chrysippus",
  "label": "Chrysippus",
  "type": "person",
  "description": "Stoic philosopher...",
  "dates": "c. 279-206 BCE"
}
```

**With Claude + Skill**:

You: "Complete this Chrysippus node according to skill standards"

Claude: "Based on validation checklist, Chrysippus needs:

```json
{
  "school": "Stoic",
  "period": "Hellenistic Greek",
  "position_on_free_will": "Compatibilist",
  "major_works": [
    "On Fate (lost, fragments preserved)",
    "Logical Investigations"
  ],
  "ancient_sources": [
    "Cicero, De Fato (transmits Chrysippean arguments)",
    "Plutarch, On Stoic Self-Contradictions 1055-1057"
  ],
  "modern_scholarship": [
    "Bobzien, Susanne. Determinism and Freedom in Stoic Philosophy. Oxford, 1998."
  ]
}
```"

---

## Advanced: Batch Processing

### For Large-Scale Enhancements

Create a Python script that works with Claude:

```python
# enhancement_batch.py
import json

# Load database
with open('ancient_free_will_database.json') as f:
    db = json.load(f)

# Find all concepts missing Greek terms
concepts_missing_greek = [
    n for n in db['nodes']
    if n['type'] == 'concept' and not n.get('greek_term')
]

print(f"Found {len(concepts_missing_greek)} concepts missing Greek terms:")
for c in concepts_missing_greek:
    print(f"  - {c['label']} ({c['id']})")

# Export list for Claude
with open('concepts_to_enhance.txt', 'w') as f:
    for c in concepts_missing_greek:
        f.write(f"{c['label']}\n")
```

Then ask Claude:
```
I have a list of 30 concepts that need Greek terminology.
Can you help me create a mapping of concept names to Greek terms?
```

Claude will systematically provide Greek terms following skill standards.

---

## Measuring Success

### Quality Metrics

Track these over time:

1. **Academic Quality Score** (from audit script)
   - Target: 90+/100

2. **Citation Coverage**
   - Ancient sources: 100% of critical nodes
   - Modern scholarship: 80%+ of critical nodes

3. **Terminology Completeness**
   - Greek/Latin: 100% of concepts
   - Proper transliteration: 100%

4. **FAIR Compliance**
   - Unique IDs: 100%
   - Proper metadata: 100%
   - Controlled vocabularies: 100%

5. **Description Quality**
   - No descriptions < 50 chars
   - No placeholder text
   - All descriptions cited

### Progress Dashboard

Create simple tracking:

```markdown
| Date | Quality Score | Critical | Warnings | Notes |
|------|---------------|----------|----------|-------|
| 2025-10-21 | 72/100 | 25 | 48 | Initial audit |
| 2025-10-22 | 78/100 | 15 | 45 | Added citations |
| 2025-10-23 | 84/100 | 8 | 40 | Greek terms |
| ... | ... | ... | ... | ... |
| Goal | 90+/100 | 0 | <10 | Publication ready |
```

---

## Tips for Efficient Enhancement

### 1. Work in Batches
- Group similar issues (all missing citations, all missing Greek terms)
- More efficient than one-by-one

### 2. Use Skill References
- Ask Claude to load specific files: "Using citation-standards.md, format this citation..."
- More precise than general questions

### 3. Validate Frequently
- Run audit after each batch
- Catch errors early

### 4. Leverage Query Examples
- Use query-examples.md patterns to find nodes needing work
- Automate identification of issues

### 5. Document Sources
- Keep track of where you found citations
- Helps verify accuracy later

### 6. Collaborate with Claude
- Claude can draft, you verify
- Faster than doing everything manually
- Skill ensures consistency

---

## Final Checklist

Before considering database "publication-ready":

- [ ] Academic Quality Score ≥ 90/100
- [ ] Zero critical issues
- [ ] < 10 warnings (all documented as acceptable)
- [ ] 100% of critical nodes have ancient sources
- [ ] 80%+ have modern scholarship
- [ ] All concepts have Greek/Latin terminology
- [ ] All node IDs follow format
- [ ] All controlled vocabularies validated
- [ ] All descriptions ≥ 50 characters
- [ ] No placeholder text
- [ ] Schema validation passes
- [ ] FAIR compliance verified
- [ ] All citations verified against sources

---

## Next Steps

1. **Run Initial Audit**
   ```bash
   python3 scripts/audit_database_academic_quality.py
   ```

2. **Review Report**
   - Open `DATABASE_AUDIT_REPORT.md`
   - Note quality score and critical issues

3. **Start Enhancement**
   - Begin with Priority 1 (Critical Issues)
   - Work with Claude using skill
   - Validate after each batch

4. **Track Progress**
   - Re-run audit regularly
   - Maintain enhancement log
   - Celebrate improvements!

5. **Reach Publication Quality**
   - Achieve 90+ quality score
   - Zero critical issues
   - Complete FAIR compliance

---

**Remember**: The Agent Skill is your automated quality control system. Let it guide enhancements to ensure every change meets academic standards.

**Contact**: Questions? See `AGENT_SKILL_GUIDE.md` or contact Romain Girardi
