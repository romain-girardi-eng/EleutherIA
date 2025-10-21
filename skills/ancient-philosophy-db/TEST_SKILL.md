# Agent Skill Test Cases

Use these test cases to verify the skill works correctly with Claude.

---

## Test 1: Basic Query (Expected: Success)

**Your Request:**
```
Find all Stoic philosophers in the database and show their dates.
```

**Expected Claude Behavior:**
1. Loads SKILL.md (recognizes database query)
2. Loads query-examples.md (finds query pattern)
3. Loads controlled-vocabularies.md (verifies "Stoic" is valid school)
4. Returns Python code similar to:
```python
stoics = [n for n in nodes
          if n['type'] == 'person' and
          n.get('school') == 'Stoic']

for stoic in stoics:
    print(f"{stoic['label']} ({stoic.get('dates', 'unknown')})")
```

**Success Criteria:**
- ✓ Uses `n['type'] == 'person'` (correct node type)
- ✓ Uses `n.get('school') == 'Stoic'` (correct controlled vocabulary)
- ✓ Does not invent person names
- ✓ Returns only actual database content

---

## Test 2: Invalid Node Type (Expected: Rejection)

**Your Request:**
```
Create a new node with type: "philosopher"
```

**Expected Claude Behavior:**
1. Loads SKILL.md
2. Loads controlled-vocabularies.md
3. Reports: "❌ 'philosopher' is not a valid node type. Use 'person' instead."

**Success Criteria:**
- ✓ Rejects invalid type "philosopher"
- ✓ Suggests correct type "person"
- ✓ Does not create the node
- ✓ References controlled vocabularies

---

## Test 3: Invalid Relation (Expected: Rejection)

**Your Request:**
```
Create an edge with relation: "invented"
```

**Expected Claude Behavior:**
1. Loads SKILL.md
2. Loads controlled-vocabularies.md
3. Reports: "❌ 'invented' is not a valid relation type. For concepts, use 'formulated'. For works, use 'authored'."

**Success Criteria:**
- ✓ Rejects invalid relation "invented"
- ✓ Suggests appropriate alternatives
- ✓ Does not create the edge

---

## Test 4: Invalid Node ID Format (Expected: Correction)

**Your Request:**
```
Check if this node ID is valid: "Person_Aristotle"
```

**Expected Claude Behavior:**
1. Loads SKILL.md
2. Loads validation-checklist.md
3. Reports errors:
   - "❌ Wrong case: should be all lowercase"
   - "❌ Missing dates or hash suffix"
   - "✓ Correct format: `person_aristotle_384_322bce_b2c3d4e5`"

**Success Criteria:**
- ✓ Identifies case error
- ✓ Identifies missing dates/hash
- ✓ Provides correctly formatted example

---

## Test 5: Greek Term Formatting (Expected: Success)

**Your Request:**
```
How should I format the Greek term "eph' hêmin" in a concept node?
```

**Expected Claude Behavior:**
1. Loads SKILL.md
2. Loads terminology-conventions.md
3. Provides three-part format:
```json
{
  "greek_term": "ἐφ' ἡμῖν (eph' hêmin)",
  "english_term": "in our power",
  "label": "Eph' hêmin (τὸ ἐφ' ἡμῖν) - In Our Power"
}
```

**Success Criteria:**
- ✓ Includes original Greek Unicode (ἐφ' ἡμῖν)
- ✓ Includes transliteration (eph' hêmin)
- ✓ Includes English translation
- ✓ Shows proper label format

---

## Test 6: Missing Citation (Expected: Request for Source)

**Your Request:**
```
Add a new concept node for "free will" without any sources.
```

**Expected Claude Behavior:**
1. Loads SKILL.md (recognizes modification request)
2. Loads validation-checklist.md
3. Responds: "❌ Cannot create node without citations. Please provide:
   - Ancient sources where this concept appears (e.g., 'Aristotle, NE III.1-5')
   - OR modern scholarship reference (e.g., 'Bobzien 1998')"

**Success Criteria:**
- ✓ Refuses to create node without citations
- ✓ Explains NO HALLUCINATION POLICY
- ✓ Requests ancient sources or modern scholarship
- ✓ Provides citation format examples

---

## Test 7: Out of Scope Content (Expected: Rejection)

**Your Request:**
```
Add Thomas Aquinas (1225-1274 CE) to the database.
```

**Expected Claude Behavior:**
1. Loads SKILL.md
2. Checks historical scope (4th c. BCE - 6th c. CE)
3. Reports: "❌ Thomas Aquinas (1225-1274 CE) is outside the database's historical scope (4th c. BCE - 6th c. CE). This database covers only ancient philosophy through Boethius (6th c. CE)."

**Success Criteria:**
- ✓ Rejects medieval philosopher
- ✓ Explains historical scope
- ✓ Does not create the node

---

## Test 8: Citation Format (Expected: Correction)

**Your Request:**
```
Is this citation correct: "Aristotle's Nicomachean Ethics book 3"?
```

**Expected Claude Behavior:**
1. Loads citation-standards.md
2. Reports: "❌ Incorrect format. Use conventional citation: `Aristotle, Nicomachean Ethics III.1-5` (or specify chapter/section range)"

**Success Criteria:**
- ✓ Identifies format error
- ✓ Provides correct format
- ✓ Uses conventional abbreviation (III not "book 3")

---

## Test 9: Creating Valid Node (Expected: Success)

**Your Request:**
```
Create a concept node for "prohairesis" (rational choice) formulated by Aristotle, found in NE III.2.
```

**Expected Claude Behavior:**
1. Loads SKILL.md + validation-checklist.md + terminology-conventions.md + citation-standards.md
2. Creates properly formatted node:
```json
{
  "id": "concept_prohairesis_rational_choice_<hash>",
  "label": "Prohairesis (Προαίρεσις) - Rational Choice",
  "type": "concept",
  "category": "free_will",
  "description": "Aristotelian concept of deliberate choice or rational preference...",
  "greek_term": "προαίρεσις (prohairesis)",
  "english_term": "rational choice",
  "formulated_by": "Aristotle",
  "ancient_sources": ["Aristotle, NE III.2"],
  "period": "Classical Greek"
}
```
3. Creates edge:
```json
{
  "source": "person_aristotle_384_322bce_<hash>",
  "target": "concept_prohairesis_rational_choice_<hash>",
  "relation": "formulated",
  "ancient_source": "Aristotle, NE III.2"
}
```

**Success Criteria:**
- ✓ Correct ID format (lowercase, underscores, hash)
- ✓ Three-part terminology (Greek, transliteration, English)
- ✓ Valid node type "concept"
- ✓ Proper citation format
- ✓ Valid relation "formulated"
- ✓ Creates both node and edge

---

## Test 10: Graph Traversal Query (Expected: Success)

**Your Request:**
```
Find all concepts formulated by Aristotle.
```

**Expected Claude Behavior:**
1. Loads query-examples.md
2. Provides graph traversal code:
```python
# Find Aristotle's node
aristotle = next(n for n in nodes if 'aristotle' in n['id'].lower())

# Find edges where Aristotle formulated concepts
formulated_edges = [e for e in edges
                    if e['source'] == aristotle['id'] and
                    e['relation'] == 'formulated']

# Get concept nodes
concept_ids = [e['target'] for e in formulated_edges]
concepts = [find_node_by_id(cid) for cid in concept_ids]

for concept in concepts:
    print(f"• {concept['label']}")
```

**Success Criteria:**
- ✓ Uses correct relation "formulated"
- ✓ Filters by node type if needed
- ✓ Traverses graph correctly (source → target)
- ✓ Returns actual database content only

---

## Running These Tests

### In Claude Code

Simply paste each test request into Claude and verify the behavior matches expectations.

### Expected Test Results

| Test | Expected Outcome | What It Validates |
|------|------------------|-------------------|
| 1 | Success | Basic querying, controlled vocabulary |
| 2 | Rejection | Node type validation |
| 3 | Rejection | Relation type validation |
| 4 | Correction | Node ID format validation |
| 5 | Success | Greek terminology handling |
| 6 | Request for source | No hallucination policy |
| 7 | Rejection | Historical scope enforcement |
| 8 | Correction | Citation format validation |
| 9 | Success | Complete node creation workflow |
| 10 | Success | Graph traversal queries |

### Success Rate

**Pass**: 9/10 or 10/10 tests should pass
**Acceptable**: 8/10 tests pass (some edge cases may need skill refinement)
**Needs work**: <8/10 tests pass (skill may need updates)

---

## Debugging Failed Tests

If a test fails:

1. **Check skill loading**
   - Did Claude load the skill at all?
   - Look for references to SKILL.md or reference files

2. **Check progressive disclosure**
   - Did Claude load the right reference files?
   - Test 2/3 should load controlled-vocabularies.md
   - Test 5 should load terminology-conventions.md

3. **Check skill version**
   - Ensure using latest version of skill files
   - Check SKILL.md frontmatter for version number

4. **Update skill if needed**
   - Skill may need clarification or examples
   - Update relevant reference file
   - Test again

---

## Advanced Tests (Optional)

### Test 11: Multi-file Reference Loading

**Request**: "Create a person node for Chrysippus with proper Greek name and citations"

**Expected**: Loads SKILL.md + controlled-vocabularies.md + terminology-conventions.md + citation-standards.md

### Test 12: GraphRAG Context Expansion

**Request**: "Get full context around Aristotle for semantic search"

**Expected**: Loads query-examples.md, uses expand_context() pattern

### Test 13: FAIR Compliance Check

**Request**: "Validate this node for FAIR compliance: {id: 'test', label: 'Test', type: 'person', category: 'free_will'}"

**Expected**: Loads validation-checklist.md, checks all FAIR criteria

---

**Last Updated**: 2025-10-21
**Maintained by**: Romain Girardi
