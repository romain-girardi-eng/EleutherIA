# KG Affordance Inventory for Scholar-RAG (G6)

Derived from live analysis of `data/kg/nodes.jsonl` (20,002 nodes) and `data/kg/edges.jsonl` (57,279 edges).

---

## 1. Debate / Controversy / Position Nodes

| Type | Count |
|------|-------|
| `debate` | 20 |
| `controversy` | 5 |
| `position` | 8 |
| **Total** | **33** |

### All 20 debate nodes

| ID | Label |
|----|-------|
| `debate_alexander_stoics_determinism` | Alexander vs Stoics on Determinism |
| `debate_augustine_pelagius_grace` | Augustine-Pelagius on Grace and Free Will |
| `debate_carneadean_antiastrology_tradition` | The Carneadean Anti-Astrology / Anti-Fatalist Tradition |
| `debate_christian_gnostic_freedom` | Christian-Gnostic Debate on Freedom |
| `debate_compatibility_question_ea55e118` | The Compatibility Question |
| `debate_discovery_of_will` | The "Discovery of the Will" Debate |
| `debate_divine_foreknowledge_235f2530` | Providence, Foreknowledge, and Freedom |
| `debate_divine_foreknowledge_future_contingents_a7b8c9d0` | Divine Foreknowledge and Future Contingents Debate |
| `debate_epicurus_free_will` | The Epicurus and Free Will Problem Debate |
| `debate_intellectualism_vs_voluntarism_w3x4y5z6` | Intellectualism vs Voluntarism Debate |
| `debate_lazy_argument` | The Lazy Argument (Argos Logos / Ignava Ratio) |
| `debate_middle_platonist_fate_interpretation` | Interpretation of Middle Platonist Fate Theory |
| `debate_monothelite_dyothelite_controversy` | The Monothelite–Dyothelite Controversy (7th c.) |
| `debate_occasionalism_vs_secondary_causation_e1f2g3h4` | Occasionalism vs Secondary Causation Debate |
| `debate_origins_notion_of_will_modern_paradigm` | Origins of the Notion of Will (Modern Scholarly Paradigm) |
| `debate_prohairesis_meaning` | The Meaning and Role of Prohairesis |
| `debate_randomness_objection_ae34a974` | The Randomness/Luck Objection to Libertarianism |
| `debate_source_of_action_90c57974` | Internal vs External Causes |
| `debate_stoic_academic_hellenistic` | Stoic-Academic Debate on Fate |
| `debate_stoic_compatibilism` | Stoic Compatibilism and Moral Responsibility |

### Position nodes

| ID | Label |
|----|-------|
| `position_academic_skepticism_fate` | Academic skeptical suspension on fate |
| `position_compatibilism` | Compatibilism |
| `position_fatalism` | Fatalism |
| `position_hard_determinism` | Hard determinism |
| `position_indeterminism` | Indeterminism |
| `position_libertarianism_freewill` | Libertarian free will |
| `position_soft_determinism` | Soft determinism |
| `position_theological_determinism` | Theological determinism |

---

## 2. Dialectical Edge Counts

| Relation | Count | Notes |
|----------|-------|-------|
| `critiques` | 244 | most productive dialectical signal |
| `responds_to` | 57 | direct reply structure |
| `advanced_in` | 905 | scholar_argument → publication (not person-to-person) |
| `supports` | 178 | positive alignment |
| `agrees_with` | 13 | explicit agreement |
| `opposes` | 11 | direct contradiction (see §4) |
| `contrasts_with` | 5 | structural contrast |
| `refutes` | 1 | formal refutation |

Key insight: the graph has **far more dialectical signal than the current synthesis uses** — 244 `critiques` + 57 `responds_to` + 11 `opposes` = 312 explicit position-vs-position edges currently ignored by the facet template.

---

## 3. Reception Layer

| Category | Count |
|----------|-------|
| `scholar_*` person nodes | 252 |
| `scholarly_argument_*` nodes | 988 |
| `scholar_position_*` nodes | 22 |
| `publication` type nodes | 322 |
| **Total reception nodes** | **~1,584** |

Reception-to-ancient edges: **3,949 total**, broken down:

| Relation | Count |
|----------|-------|
| `discusses` | 1,711 |
| `created_by` | 959 |
| `cites_primary_source` | 426 |
| `authored_by` | 324 |
| `engages_with` | 273 |
| `interprets` | 83 |
| `contributes_to` | 33 |
| `critiques` | 12 |
| `opposes` | 8 |
| `responds_to` | 11 |

The most-published scholarly works in `advanced_in` edges:
- Frede 2011 *A Free Will* (`pub_frede_2011_free_will`): 23 arguments
- Bobzien 1998 *Determinism and Freedom* (`scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso`): 22 arguments
- Bobzien 1998 *The Inadvertent Conception* (`pub_bobzien_1998_inadvertent`): 20 arguments
- Dihle 1982 *Theory of Will* (`pub_dihle_1982_theory_of_will`): 13 arguments

---

## 4. Bilingual Passages (Original + English)

| Metric | Count |
|--------|-------|
| `has_translation` edges | 2,953 |
| `translation_of` edges | 2,953 |
| Passages with `_en` ID suffix | 2,992 |
| Language of translation nodes | **eng (100%)** |

Translation metadata keys on each `_en` node: `language`, `cts_urn`, `edition`, `source_model`, `translation_source`, `translation_type`, `greek_node_id`, `canonical_ref`.

The current synthesis never retrieves `_en` counterparts. Ideal Scholar-RAG should always pair `passage_X` with `passage_X_en` to give: (a) the exact original text, (b) an English rendering the model can reason over.

---

## 5. The 11 `opposes` Edges — Full Enumeration

These are the graph's sharpest dialectical signals. Organized by debate cluster:

### Cluster A: Discovery-of-will debate (6 edges)

1. `scholarly_argument_irwin_greek_concept_of_the_will_0` **OPPOSES** `scholar_position_frede_will_originates_epictetus`
   — Irwin: Aristotle may already have had a will-concept; Frede mis-dates the emergence

2. `scholarly_argument_irwin_greek_concept_of_the_will_0` **OPPOSES** `scholar_position_dihle_will_christian_innovation`
   — Irwin challenges both the Dihle thesis (Augustine) and Frede's counter-thesis (Epictetus)

3. `scholar_position_frede_will_originates_epictetus` **OPPOSES** `scholar_position_dihle_will_christian_innovation`
   — Frede (Epictetus/Stoics) vs Dihle (Augustine/Paul): the central historiographical dispute

4. `scholar_position_frede_will_originates_epictetus` **OPPOSES** `scholar_position_bobzien_no_free_will_problem_ancients`
   — Frede (will exists in Epictetus) vs Bobzien (no free-will problem in the ancients at all)

5. `scholar_position_kahn_will_emerges_seneca_epictetus` **OPPOSES** `scholar_position_dihle_will_christian_innovation`
   — Kahn (Seneca/Epictetus gradual emergence) vs Dihle (Augustine leap)

6. `scholarly_argument_blackson_e_vs_d_object_of_choice` **OPPOSES** `scholar_position_frede_will_originates_epictetus`
   — Blackson: Frede misspecifies the object of choice; early Stoics already had a will-notion (predates Epictetus)

### Cluster B: Modern free will debate (2 edges, background)

7. `person_frankfurt_harry_1929_2023` **OPPOSES** `person_van_inwagen_peter_9s0t1u2v`
   — Frankfurt (PAP is false; compatibilism) vs van Inwagen (consequence argument; incompatibilism)

8. `person_strawson_galen_contemporary` **OPPOSES** `person_kane_robert_1938_2022`
   — Strawson (basic argument; skepticism) vs Kane (libertarian self-forming actions)

### Cluster C: Stoic-Bobzien vs Alexander-Sorabji (2 edges)

9. `argument_dihle_1982_augustine_invents_philosophical_voluntas` **OPPOSES** `scholar_frede_michael`
   — Dihle's argument directly targets Frede (the argument node opposes the person)

10. `scholar_position_sorabji_aristotle_indeterminist` **OPPOSES** `scholarly_argument_bobzien_origin_of_free_will_problem_in_0`
    — Sorabji (Aristotle already indeterminist) vs Bobzien's origin-of-free-will dating

### Cluster D: Carneadean transmission dispute (1 edge)

11. `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0` **OPPOSES** `scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0`
    — Amand de Mendieta (Origen's source = Carneadean tradition) vs Ramelli (Origen's source = Alexander of Aphrodisias directly)

---

## 6. The Three Named Debate Nodes from the Goal Doc

### `debate_origins_notion_of_will_modern_paradigm`

A historiographical meta-debate over when a discrete notion of 'the will' emerged in antiquity. Contributors:
- `argument_dihle_1982_augustine_invents_philosophical_voluntas` → `contributes_to`
- `argument_frede_2011_epictetus_first_free_will` → `contributes_to`
- `argument_frede_2011_augustine_no_new_notion_vs_dihle` → `contributes_to`
- `pub_dihle_1982_theory_of_will` → `contributes_to`
- `pub_frede_2011_free_will` → `contributes_to`

No outgoing edges — this debate node has no `has_position` links (structural gap: needs `participates_in` from Bobzien, Kahn, Irwin, Fürst).

### `debate_monothelite_dyothelite_controversy`

7th-century Christological controversy over Christ's one or two wills. Outgoing: `discusses` → `concept_monothelitism`, `concept_thelema_physikon_natural_will`, `concept_gnomic_will_gnome`. Incoming (13 edges): 6 persons contributing (Maximus, Pyrrhus, Sophronius, Sergius, Cyrus, Pope Martin I) + 4 argument nodes. Strongly connected.

### `debate_carneadean_antiastrology_tradition`

Transmission of Carneades' anti-astrological and anti-fatalist arguments (Amand de Mendieta's thesis). Incoming (15 edges): 14 persons `participates_in` (Carneades → Clitomachus → Cicero → Philo → Origen → Eusebius → Basil → Gregory of Nyssa → Diodore of Tarsus). No outgoing edges and 0 grounded passages — the debate node exists but its sub-arguments are in the `argument_cafma_*` cluster rather than being pointed at the debate directly.

---

## 7. What the Current Synthesis Ignores (G6 diagnosis)

The deterministic facet-template at `graph_nodes.py` L4308 pastes `truncate_text(node.description, 220)` for each node — it:

1. **Never traverses edges** — the 244 `critiques`, 57 `responds_to`, 11 `opposes` edges are invisible to synthesis
2. **Never retrieves reception nodes** — 988 `scholarly_argument_*` + 22 `scholar_position_*` + 252 `scholar_*` persons + 322 publications
3. **Never pairs passages with translations** — 2,953 bilingual pairs available, 0 used
4. **Never reads debate-participant topology** — 33 debate/controversy/position nodes and their `participates_in` / `contributes_to` / `has_position` edges
5. **Never follows the opposes chain** — the 11 edges that encode the actual scholarly fault lines

---

## 8. Ideal Subgraph for "Open debates today about free will in antiquity"

### Step 1 — Enter via debate nodes

Start with 5 open scholarly debates about antiquity (exclude Medieval/Modern controversies):

| Debate ID | Label | Edge count incoming |
|-----------|-------|---------------------|
| `debate_discovery_of_will` | "Discovery of the Will" | 31 inc. (16 scholarly, 5 persons, 5 passages) |
| `debate_origins_notion_of_will_modern_paradigm` | Origins of the Notion of Will | 5 inc. (3 args, 2 pubs) |
| `debate_stoic_compatibilism` | Stoic Compatibilism and Moral Responsibility | 21 inc. (3 pubs, 5 persons, 8 passages) |
| `debate_alexander_stoics_determinism` | Alexander vs Stoics on Determinism | 43 inc. (1 pub, 1 person, 39 passages) |
| `debate_carneadean_antiastrology_tradition` | Carneadean Anti-Astrology Tradition | 15 inc. (1 pub, 14 persons) |

Secondary debates to surface:
- `debate_stoic_academic_hellenistic` (7 passages grounded)
- `debate_epicurus_free_will` (3 passages + Bobzien's 2000 paper)

---

### Step 2 — Retrieve opposing scholarly positions (the fault lines)

**Fault line 1: When did free will originate?**

```
scholar_position_dihle_will_christian_innovation   (Augustine invents will)
  ←OPPOSES← scholar_position_frede_will_originates_epictetus  (Epictetus first)
  ←OPPOSES← scholar_position_kahn_will_emerges_seneca_epictetus  (Seneca/Epictetus gradual)
  ←OPPOSES← scholarly_argument_irwin_greek_concept_of_the_will_0  (Aristotle already had it)
  ←OPPOSES← scholarly_argument_blackson_e_vs_d_object_of_choice  (early Stoics already had it)
scholar_position_frede_will_originates_epictetus
  →OPPOSES→ scholar_position_bobzien_no_free_will_problem_ancients  (no free-will problem at all)
scholar_position_sorabji_aristotle_indeterminist
  →OPPOSES→ scholarly_argument_bobzien_origin_of_free_will_problem_in_0
```

Publication anchors:
- `pub_frede_2011_free_will` — 23 arguments, responds_to Bobzien/Sorabji/Broadie/Kahn/Kenny/Crouzel
- `pub_dihle_1982_theory_of_will` — 13 arguments, critiqued by Frede, Fürst, Horn, Irwin
- `scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso` — 22 arguments
- `pub_bobzien_1998_inadvertent` — 20 arguments, the "inadvertent conception" paper
- `pub_irwin_1992_who_discovered_will` — critiques Dihle

Key `critiques` edges to surface:
- `pub_frede_2011_free_will` → CRITIQUES → `pub_dihle_1982_theory_of_will`
- `pub_frede_2011_free_will` → CRITIQUES → `pub_bobzien_1998_inadvertent`
- `pub_bobzien_2000_epicurus_free_will` → CRITIQUES → `pub_huby_1967_first_discovery`
- `pub_boysstones_2007_middle_platonists` → CRITIQUES → `pub_amand_1945_fatalisme`
- `argument_bobzien_2001_b1_critique_anachronistic_freewill` → CRITIQUES → `scholarly_work_long_sedley_1987_hellenistic_philosophers`

Person-level signal:
- `person_bobzien_susanne_contemporary` → CRITIQUES → `scholar_frede_michael`, `scholar_long_anthony`, `scholar_sedley_david`
- `scholar_furst_alfons` → CRITIQUES → `scholar_albrecht_dihle`
- `scholar_furst_alfons` → responds_to → `scholar_frede_michael`

---

**Fault line 2: Is Alexander a libertarian?**

```
scholarly_position_sharples_alexander_libertarian_unsupported
  — "Alexander stipulates libertarianism but does not demonstrate it philosophically" (Sharples 1983, p. 22)
  →CRITIQUES→ pub_frede_2011_free_will
scholarly_argument_sharples_accident_of_determinism_2008
  — Sharples 2008 half-recants: the near-modern free-will problem in De Fato is an "accident of history"
```

Primary text grounding (35+ passages in De Fato):
- `passage_alex_fat_12` — τὸ ἐφ' ἡμῖν argument: if determinism abolishes deliberation, it abolishes what is up to us. Cited by 17 argument nodes.
- `passage_alex_fat_20` — humans as the cause/origin of their own actions (ἀρχὴν αὐτὸν ὄντα). Cited by 16 nodes.
- `passage_alex_fat_14` — Stoics cannot save τὸ ἐφ' ἡμῖν without the word. Cited by 13 nodes.

Modern positions in conflict:
- `scholar_position_sharples_chrysippus_early_compatibilist` → De Fato is the principal ancient anti-compatibilist text
- `argument_bobzien_2001_b1_no_free_will_in_stoa` — Stoics had NO free-will notion in the libertarian sense
- `argument_salles_2014_epictetus_causal_eph_hemin_continuity_chrysippus` → CRITIQUES → `scholar_brennan_tad`, `scholar_long_anthony`

---

**Fault line 3: Carneades' transmission — Amand vs Ramelli**

```
scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0
  →OPPOSES→ scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0
```

Amand thesis (1945): Origen's anti-fatalism comes from the Carneadean tradition (via Cicero, Philo).
Ramelli thesis: Origen probably knew Alexander of Aphrodisias' works directly (read in Plotinus's circle).

Participant chain (`participates_in` → `debate_carneadean_antiastrology_tradition`):
Carneades → Clitomachus → Cicero → Philo → Origen → Eusebius → Basil → Gregory of Nyssa → Diodore of Tarsus → Nemesius

Key passages: `passage_eusebius_praep_ev_6_6_5` (cited 11x), CAFMA argument cluster (`argument_cafma_*`)

---

**Fault line 4: Stoic compatibilism — was it genuine?**

Persons in `debate_stoic_compatibilism`:
- `person_bobzien_susanne_contemporary` (`participates_in`)
- `person_inwood_brad_contemporary` (`contributes_to`)
- `scholar_brennan_tad` (`contributes_to`)
- `scholar_long_anthony` (`participates_in`)
- `scholar_sharples_robert` (`participates_in`)

Primary texts:
- Cicero De Fato 39–43 (`passage_cic_fat_39` through `_43`): the cylinder analogy, most-cited passages in the graph (25–35 citations each)
  - Fat. 41: Chrysippus's two-kinds-of-cause distinction (perfect vs antecedent)
  - Fat. 43: "as the man who pushes the cylinder gives it a beginning of motion but not rolling" — the compatibilist paradigm
- Alexander De Fato 10, 13, 15, 33, 34, 37, 38, 9 (`contributes_to` → `debate_stoic_compatibilism`)

Scholarly tension: `scholar_position_salles_chrysippus_frankfurt_style` (Chrysippus anticipates Frankfurt) vs `argument_argument_cafma_carneades_m3n4o5p6` (Carneades demolishes Stoic compatibilism).

---

### Step 3 — Ground in bilingual primary text

For each fault line, the retrieval pairs:
```
passage_cic_fat_41  (Latin original: "Causarum enim, inquit, aliae sunt perfectae et principales...")
passage_cic_fat_41_en  (English: "Chrysippus, rejecting necessity, yet believing nothing can happen without antecedent causes, distinguishes causes...")

passage_alex_fat_12  (Greek original: "Ἀναιρουμένου δὲ ὡς ἐδείχθη τοῦ βουλεύσασθαι...")
passage_alex_fat_12_en  (English: "Since deliberation is abolished on their account, as has been shown, what depends on us is also manifestly abolished...")
```

---

### Step 4 — Full ideal subgraph specification

**Nodes to retrieve (ordered by importance):**

1. Debate nodes (5): `debate_discovery_of_will`, `debate_stoic_compatibilism`, `debate_alexander_stoics_determinism`, `debate_carneadean_antiastrology_tradition`, `debate_origins_notion_of_will_modern_paradigm`

2. Scholar positions in conflict (6): `scholar_position_frede_will_originates_epictetus`, `scholar_position_dihle_will_christian_innovation`, `scholar_position_bobzien_no_free_will_problem_ancients`, `scholar_position_kahn_will_emerges_seneca_epictetus`, `scholarly_argument_irwin_greek_concept_of_the_will_0`, `scholarly_argument_blackson_e_vs_d_object_of_choice`

3. Key publications (5): `pub_frede_2011_free_will`, `pub_dihle_1982_theory_of_will`, `scholarly_work_bobzien_1998_determinism_and_freedom_in_stoic_philoso`, `pub_bobzien_1998_inadvertent`, `pub_amand_1945_fatalisme`

4. Ancient person nodes (3): `person_alexander_aphrodisias_fl200ce_n5o6p7q8`, `person_chrysippus_280_206bce_i9j0k1l2`, `person_carneades_214_129bce_l2m3n4o5`

5. Primary passages (8 pairs = 16 nodes):
   - Cicero De Fato 39, 40, 41, 43 + `_en` counterparts (cylinder analogy, compatibilist paradigm)
   - Alexander De Fato 12, 14, 20 + `_en` counterparts (τὸ ἐφ' ἡμῖν argument)

6. Dialectical edges to traverse explicitly:
   - All 6 `opposes` edges in Cluster A (discovery-of-will)
   - 1 `opposes` in Cluster D (Amand vs Ramelli)
   - `critiques` edges: Bobzien→Frede, Fürst→Dihle, Frede-pub→Dihle-pub, Bobzien-pub→Long-Sedley
   - `responds_to` edges: Frede-pub→Bobzien, pub-boys-stones→Bobzien, Fürst→Frede

7. Argument nodes grounding each position (sample, 988 total):
   - `argument_bobzien_2001_b1_no_free_will_in_stoa` (Bobzien central thesis)
   - `argument_frede_2011_epictetus_first_free_will`
   - `argument_frede_2011_augustine_no_new_notion_vs_dihle`
   - `argument_dihle_1982_augustine_invents_philosophical_voluntas`
   - `scholarly_argument_sharples_accident_of_determinism_2008` (the "accident" retrospective)
   - `scholarly_argument_amand_de_mendieta_carneades_anti_fatalist_moral__0`
   - `scholarly_argument_ramelli_origen_s_knowledge_of_alexande_0`

**Edges the ideal subgraph traverses (that the current synthesis never uses):**

```
debate_discovery_of_will ←contributes_to← [16 scholarly arguments/publications]
debate_discovery_of_will ←participates_in← [Bobzien, Frede, Dihle, Irwin, Annas]
debate_discovery_of_will ←contributes_to← [passage_alex_fat_12, _14, _18, _19, _20]
scholar_position_frede_will_originates_epictetus →OPPOSES→ scholar_position_dihle_will_christian_innovation
scholar_position_frede_will_originates_epictetus →OPPOSES→ scholar_position_bobzien_no_free_will_problem_ancients
scholarly_argument_irwin_* →OPPOSES→ scholar_position_frede_will_originates_epictetus
scholarly_argument_blackson_* →OPPOSES→ scholar_position_frede_will_originates_epictetus
pub_frede_2011_free_will →CRITIQUES→ pub_dihle_1982_theory_of_will
pub_frede_2011_free_will →CRITIQUES→ pub_bobzien_1998_inadvertent
person_bobzien_susanne_contemporary →CRITIQUES→ scholar_frede_michael
scholar_furst_alfons →CRITIQUES→ scholar_albrecht_dihle
pub_frede_2011_free_will →responds_to→ person_bobzien_susanne_contemporary
debate_stoic_compatibilism ←participates_in← [Bobzien, Long, Sharples, Brennan]
debate_stoic_compatibilism ←contributes_to← [passage_alex_fat_10, _13, _15, ...]
debate_alexander_stoics_determinism ←contributes_to← [39 passages of De Fato]
debate_carneadean_antiastrology_tradition ←participates_in← [14 persons: Carneades→Gregory of Nyssa]
scholarly_argument_amand_* →OPPOSES→ scholarly_argument_ramelli_*
passage_cic_fat_41 ←has_translation→ passage_cic_fat_41_en
passage_alex_fat_12 ←has_translation→ passage_alex_fat_12_en
```

---

## 9. Summary: What Scholar-RAG Must Do That Current Synthesis Never Does

| Affordance | Current synthesis | Scholar-RAG must |
|------------|------------------|-----------------|
| 33 debate/controversy nodes | Never retrieved | Enter via these; they are the answer scaffolding |
| 11 `opposes` edges | Ignored | Traverse first — these ARE the "open debates" |
| 244 `critiques` edges | Ignored | Use to attribute positions (Bobzien critiques Frede) |
| 57 `responds_to` edges | Ignored | Follow to build reply chains |
| 988 `scholarly_argument_*` nodes | Ignored | These carry the actual scholarly positions |
| 22 `scholar_position_*` nodes | Ignored | Named positions in conflict |
| 252 `scholar_*` persons + 322 publications | Ignored | Attribution targets |
| 2,953 bilingual passage pairs | Never paired | Always retrieve original + `_en` together |
| `participates_in` topology | Ignored | Shows who is on which side of each debate |
| `contributes_to` from passages to debates | Ignored | Links primary text to live scholarly question |
