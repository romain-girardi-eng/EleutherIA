# KG Passage Node Expansion Plan

**Date:** 2026-02-25
**Status:** TODO
**Goal:** Create KG passage nodes (+ English translations) for all 16,246 passages that exist in the DB but have no KG representation.

## Current State

- **KG passage nodes:** 2,815 source + 2,815 `_en` = 5,630 total
- **DB passages without KG nodes:** 16,246 across 91 works
- **Old-pipeline nodes:** 791 passage nodes exist from the pre-SC import (Epictetus, Augustine, Boethius, Seneca, Cicero, Marcus Aurelius, Plutarch, Methodius) but are **UNLINKED** to the passages table (no `db_passage_id` in metadata)

## Two Separate Problems

### Problem 1: Old-pipeline nodes are unlinked

791 KG passage nodes exist but have no `db_passage_id` in metadata, meaning they're disconnected from the passages table. These need to be reconciled:

| Author | KG nodes | DB passages | Status |
|--------|----------|-------------|--------|
| Augustine (mixed) | 201 | 170 + 158 + 39 + 25 + 21 + 26 = 439 | UNLINKED |
| Epictetus | 187 | 185 | UNLINKED |
| Boethius | 129 | 129 | UNLINKED |
| Seneca | 68 | 2,135 + 68 = 2,203 | UNLINKED |
| Cicero | 48 | 48 | UNLINKED |
| Marcus Aurelius | 19 | 577 | UNLINKED |
| Plutarch | 19 | 47 + 19 + 6 = 72 | UNLINKED |
| Methodius | 7 | 97 | UNLINKED |
| Justin Martyr | 6 | 750 + 68 + 15 = 833 | UNLINKED |
| Tatian | 3 | 98 | UNLINKED |
| Others (7 authors) | 10 | various | UNLINKED |

**Action:** Write a reconciliation script that matches old KG nodes to DB passages by text similarity or reference matching, then adds `db_passage_id` to metadata. For works where the old KG nodes are a subset (e.g., 19 Marcus Aurelius nodes vs 577 passages), keep the old nodes and create new ones for the rest.

### Problem 2: Works with zero KG passage nodes

These works have passages in the DB but no KG representation at all.

## Priority Tiers

### Tier 1 — Core Free Will Texts (do first)

These are the primary sources for the project's focus on free will, fate, and moral responsibility.

| # | Author | Work | Passages | Language | Canonical ID | Why |
|---|--------|------|----------|----------|-------------|-----|
| 1 | Marcus Aurelius | Meditations | 577 | grc | `urn:cts:greekLit:tlg0562.tlg001` | Stoic agency, self-determination, fate acceptance |
| 2 | Seneca | Epistulae Morales | 2,135 | lat | `urn:cts:latinLit:phi1017.phi015` | Stoic ethics, providence, moral progress |
| 3 | Seneca | De Providentia | 68 | lat | `urn:cts:latinLit:stoa0255.stoa012` | Why bad things happen to good men — core fate text |
| 4 | Lucretius | De Rerum Natura | 300 | lat | `urn:cts:latinLit:phi0550.phi001` | Epicurean clinamen/swerve, anti-determinism |
| 5 | Aristotle | Nicomachean Ethics | 116 | grc | `oga:tlg0086.tlg010.perseus-grc2` | Voluntary action, moral responsibility |
| 6 | Aristotle | Eudemian Ethics | 41 | grc | `oga:tlg0086.tlg009.perseus-grc2` | Alternative ethics, parallel to EN |
| 7 | Aristotle | De Interpretatione | 29 | grc | `first1k:tlg0086.tlg017.1st1K-grc1` | Ch. 9 = sea battle argument, future contingents |
| 8 | Epicurus | Letters and Fragments | 193 | grc | `usener:epicurus` | Anti-fate, atomic swerve, Letter to Menoeceus |
| 9 | Cicero | De Fato | 48 | lat | `urn:cts:latinLit:phi0474.phi049` | Survey of Stoic/Epicurean/Academic positions on fate |
| 10 | Plutarch | De Stoicorum Repugnantiis | 47 | grc | `urn:cts:greekLit:tlg0007.tlg136` | Stoic self-contradictions on fate |
| 11 | Plutarch | De fato | 19 | grc | `urn:cts:greekLit:tlg0007.tlg099` | Platonist critique of determinism |
| 12 | Methodius | De Libero Arbitrio | 97 | grc | `urn:cts:greekLit:tlg2959.tlg001` | Early Christian free will treatise |
| 13 | Augustine | De Libero Arbitrio | 170 | lat | `urn:cts:latinLit:stoa0040.stoa003` | Foundation of Western free will theology |
| 14 | Augustine | De Civitate Dei (V, XII, XIV) | 158 | lat | `urn:cts:latinLit:stoa0040.stoa001:v-xii-xiv` | Fate, foreknowledge, original sin |
| 15 | Augustine | De Gratia et Libero Arbitrio | 25 | lat | `urn:cts:latinLit:stoa0040.stoa044` | Grace vs. free will |
| 16 | Boethius | De Consolatione Philosophiae | 129 | lat | `urn:cts:latinLit:phi2089.phi002` | Providence, foreknowledge, Prosa V |
| 17 | Epictetus | Discourses + Enchiridion | 185 | grc | `urn:cts:greekLit:tlg0557` | Prohairesis, what is "up to us" |

**Subtotal: 4,337 passages**

### Tier 2 — Major Philosophical Works

Important for context but less directly about free will.

| # | Author | Work | Passages | Language | Canonical ID | Why |
|---|--------|------|----------|----------|-------------|-----|
| 18 | Plotinus | Enneades | 1,355 | grc | `urn:cts:greekLit:tlg2000.tlg001` | Ennead VI.8 on freedom, III.1 on fate |
| 19 | Sextus Empiricus | Against the Professors + PH | 534 | grc | `urn:cts:greekLit:tlg0544` | Skeptical critique of causation |
| 20 | Diogenes Laertius | Vitae Philosophorum | 1,203 | grc | `urn:cts:greekLit:tlg0004.tlg001` | Doxographic source for all schools |
| 21 | Plato | Phaedrus | 261 | grc | `urn:cts:greekLit:tlg0059.tlg012` | Soul's self-motion, chariot allegory |
| 22 | Plato | Phaedo | 59 | grc | `urn:cts:greekLit:tlg0059.tlg004` | Soul, immortality, choice |
| 23 | Plato | Timaeus | 76 | grc | `urn:cts:greekLit:tlg0059.tlg031` | Cosmology, necessity, Demiurge |
| 24 | Plato | Apology | 125 | grc | `urn:cts:greekLit:tlg0059.tlg002` | Socratic moral autonomy |
| 25 | Aristotle | De Anima | 30 | grc | `first1k:tlg0086.tlg002.1st1K-grc1` | Will, desire, rational agency |
| 26 | Aristotle | Physics | 71 | grc | `oga:tlg0086.tlg031.1st1K-grc1` | Causation, chance, necessity |
| 27 | Aristotle | Metaphysics | 142 | grc | `oga:tlg0086.tlg025.perseus-grc2` | Potentiality/actuality, causation |
| 28 | Aristotle | Magna Moralia | 434 | grc | `first1k:tlg0086.tlg022.1st1K-grc1` | Parallel ethics text |
| 29 | Porphyry | Ad Marcellam | 35 | grc | `urn:cts:greekLit:tlg2034.tlg009` | Neoplatonist ethics |
| 30 | Aspasius | In EN Commentaria | 6 | grc | `aspasius_in_en_cag` | Earliest EN commentary, on voluntary action |
| 31 | Calcidius | In Timaeum | 5 | lat | `digiliblt:DLT000607` | Latin Platonist on fate/providence |
| 32 | Alcinous | Didaskalikos | 1 | grc | `urn:cts:greekLit:tlg0720.tlg001` | Middle Platonist handbook |

**Subtotal: 4,337 passages**

### Tier 3 — Patristic / Supporting

Already partially covered by SC imports. Important for the Christian reception layer.

| # | Author | Work | Passages | Language | Canonical ID |
|---|--------|------|----------|----------|-------------|
| 33 | Origen | Contra Celsum | 971 | grc | `sc_origenes_contra_celsum` |
| 34 | Origen | Peri Archon (Greek extracts) | 71 | grc | `sc268_origenes_peri_archon` |
| 35 | Augustine | De Natura Boni | 39 | lat | `urn:cts:latinLit:stoa0040.stoa054` |
| 36 | Augustine | De Correptione et Gratia | 21 | lat | `urn:cts:latinLit:stoa0040.stoa045` |
| 37 | Augustine | Adversus Fulgentium | 26 | lat | `urn:cts:latinLit:stoa0040.adv_fulg` |
| 38 | Chrysostom | De Providentia | 174 | grc | `sc79_chrysostomus_de_providentia` |
| 39 | Gregory of Nazianzus | Orations 27-31 | 115 | grc | `urn:cts:greekLit:tlg2022.*` |
| 40 | Evodius | De fide Contra Manicheos | 36 | lat | `cpl:evodius.de_fide` |
| 41 | Justin Martyr | Dialogus cum Tryphone | 750 | grc | `urn:cts:greekLit:tlg0645.tlg003` |
| 42 | Justin Martyr | Apologia I + II | 83 | grc | `urn:cts:greekLit:tlg0645.tlg001/002` |
| 43 | Tatian | Oratio ad Graecos | 98 | grc | `urn:cts:greekLit:tlg1766.tlg001` |
| 44+ | SC imports (already have KG nodes) | Various | ~2,024 | grc/lat | `sc*` |

**Subtotal: ~2,384 passages (excluding already-imported SC works)**

### Tier 4 — Biblical Texts

Relevant for Paul's theology of will and grace, but less directly philosophical.

| # | Work | Passages | Notes |
|---|------|----------|-------|
| 45 | Romans | 430 | Paul on predestination (ch. 8-9) |
| 46 | 1 Corinthians | 437 | Spiritual gifts, body/spirit |
| 47 | Galatians | 149 | Freedom in Christ, law vs. grace |
| 48 | John | 866 | Johannine theology of will |
| 49 | Other NT books | ~1,200 | Supporting context |
| 50 | Septuagint — Psalms | 729 | Background |
| 51 | Vulgate — Ecclesiasticus | 67 | Sirach on free will (15:11-20) |

**Subtotal: ~3,878 passages**

## Procedure (per work)

Follow the pattern established for Alexander De Fato and SC imports:

### Step 1: Create passage KG nodes

```python
# For each passage in free_will.passages for the target work:
INSERT INTO free_will.kg_nodes (node_id, label, type, description, period, school, metadata)
VALUES (
    '{node_id_prefix}_{chapter}',           -- e.g., passage_sen_ep_1
    '{author}, {work}, {ref}',              -- e.g., Seneca, Ep. Mor. 1
    'passage',
    '{text_content}',                        -- original Greek/Latin
    '{period}',                              -- e.g., Imperial
    '{school}',                              -- e.g., Stoic
    jsonb_build_object(
        'language', '{lang}',
        'author', '{author}',
        'work_title', '{title}',
        'canonical_ref', '{ref}',
        'db_passage_id', '{passage_id}',     -- CRITICAL: link to passages table
        'cts_urn', '{urn}',
        'edition', '{edition}'
    )
);
```

### Step 2: Create edges

```sql
-- PART_OF edge to work node
INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
VALUES ('{node_id}', '{work_node_id}', 'part_of', '{"auto_generated": true}');

-- AUTHORED_BY edge to person node
INSERT INTO free_will.kg_edges (source_id, target_id, relation, metadata)
VALUES ('{node_id}', '{person_node_id}', 'authored_by', '{"auto_generated": true}');
```

### Step 3: Create English translations

Use `database/scripts/create_passage_translations.py`:

```bash
# Generate translations via LLM agents (parallel batches of 100)
# Output: /tmp/translations_{work}.json

# Insert:
python3 database/scripts/create_passage_translations.py \
    --translations /tmp/translations_{work}.json --confirm
```

### Step 4: Verify

```sql
-- Check passage count matches
SELECT COUNT(*) FROM free_will.kg_nodes
WHERE type = 'passage' AND node_id LIKE '{prefix}%' AND node_id NOT LIKE '%_en';

-- Check all have _en counterparts
SELECT COUNT(*) FROM free_will.kg_nodes n
WHERE type = 'passage' AND node_id LIKE '{prefix}%' AND node_id NOT LIKE '%_en'
  AND NOT EXISTS (SELECT 1 FROM free_will.kg_nodes en WHERE en.node_id = n.node_id || '_en');

-- Check all linked to passages table
SELECT COUNT(*) FROM free_will.kg_nodes
WHERE type = 'passage' AND node_id LIKE '{prefix}%' AND node_id NOT LIKE '%_en'
  AND metadata->>'db_passage_id' IS NULL;
```

## Node ID Conventions

| Author | Prefix | Example |
|--------|--------|---------|
| Seneca (Ep.) | `passage_sen_ep_{n}` | `passage_sen_ep_1` |
| Seneca (Prov.) | `passage_sen_prov_{n}` | `passage_sen_prov_1` |
| Marcus Aurelius | `passage_ma_med_{book}_{n}` | `passage_ma_med_3_9` |
| Lucretius | `passage_lucr_{book}_{n}` | `passage_lucr_2_216` |
| Aristotle (EN) | `passage_arist_en_{book}_{n}` | `passage_arist_en_3_1` |
| Aristotle (EE) | `passage_arist_ee_{book}_{n}` | `passage_arist_ee_2_6` |
| Aristotle (DI) | `passage_arist_di_{n}` | `passage_arist_di_9` |
| Epicurus | `passage_epic_let_{n}` | `passage_epic_let_men_127` |
| Plotinus | `passage_plot_{enn}_{tract}_{ch}` | `passage_plot_6_8_1` |
| Sextus Emp. | `passage_sext_{work}_{n}` | `passage_sext_ph_3_1` |
| Diog. Laertius | `passage_dl_{book}_{n}` | `passage_dl_7_1` |
| Plato (various) | `passage_plato_{work}_{ref}` | `passage_plato_phdr_245c` |

## Estimated Work

| Tier | Passages | Est. time | Notes |
|------|----------|-----------|-------|
| Tier 1 | 4,337 | ~2 hours | Mostly scripted, parallel agents for translations |
| Tier 2 | 4,337 | ~2 hours | Same process |
| Tier 3 | 2,384 | ~1 hour | Some overlap with existing SC imports to reconcile |
| Tier 4 | 3,878 | ~1.5 hours | Straightforward but large |
| **Total** | **14,936** | **~6.5 hours** | Can be done in batches |

## Open Questions

1. **Old-pipeline reconciliation:** Should we delete the 791 unlinked old nodes and recreate them from the passages table, or try to match them? Recreating is cleaner.
2. **SC-import overlap:** Some SC works (Origen CC, Theophilus, etc.) already have KG nodes from SC import but also have separate entries in `ancient_works`. Need to decide whether to use SC nodes or create new ones linked to the passages table.
3. **NT / LXX priority:** Biblical texts are large (3,878 passages). Worth doing for completeness, but lower priority for the free will focus. Could do just Romans 8-9, Galatians, and Sirach 15.
