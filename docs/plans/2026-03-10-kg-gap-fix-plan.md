# KG Gap Fix Plan

Date: 2026-03-10

## Principles

1. **Zero hallucination.** Every text comes from a verified digital critical edition.
2. **Scientific editions only.** Perseus/Scaife (OCT, Teubner, Loeb-aligned), Sources Chretiennes, First1K, OGA.
3. **Existing pipelines.** Reuse `fetch_de_fato_cts.py` (Scaife CTS), SC import pipeline, `create_kg_passage_nodes.py`, `create_passage_translations.py`.
4. **Incremental.** Each phase is independently valuable and testable.

## Source Availability Matrix

Verified 2026-03-10 against Scaife CTS API (`GetValidReff`).

### Available on Scaife (HTTP 200)

| CTS URN | Work | Edition | Lang |
|---------|------|---------|------|
| `tlg4090.tlg001` | Nemesius, De Natura Hominis | Morani 1987 (Teubner) | grc |
| `tlg0057.tlg010` | Galen, De Placitis Hippocratis et Platonis | De Lacy 1978-84 (CMG) | grc |
| `tlg2042.tlg012` | Clement of Alexandria, Stromata | Stahlin 1906-09 (GCS) | grc |
| `tlg2042.tlg007` | Clement of Alexandria, Protrepticus | Stahlin 1905 (GCS) | grc |
| `tlg2042.tlg001` | Clement of Alexandria, Paedagogus | Stahlin 1905 (GCS) | grc |
| `tlg0093.tlg001` | Simplicius, In Epicteti Enchiridion | Dubner 1842 (Didot) | grc |
| `tlg2018.tlg001` | Basil, Hexaemeron | Giet 1968 (SC 26bis) | grc |
| `tlg0086.tlg003` | Aristotle, De Generatione et Corruptione | Bekker/OCT | grc |
| `tlg0059.tlg034` | Plato, Laws | Burnet (OCT) | grc |
| `tlg0059.tlg030` | Plato, Republic | Burnet (OCT) | grc |
| `phi0474.phi042` | Cicero, De Divinatione | Muller (Teubner) | lat |
| `phi0474.phi041` | Cicero, De Natura Deorum | Plasberg/Ax (Teubner) | lat |
| `stoa0275.stoa015` | Tertullian, Adversus Marcionem | Kroymann (CSEL) | lat |
| `stoa0275.stoa007` | Tertullian, De Anima | Waszink (CCSL) | lat |
| `tlg0013.tlg001` | Cleanthes, Hymn to Zeus | Powell (Coll. Alex.) | grc |

### NOT Available on Scaife (HTTP 404)

| TLG/PHI Code | Work | Alternative Source |
|--------------|------|--------------------|
| `tlg0526.tlg001/004` | Josephus, BJ + AJ | Perseus XML (older) or TLG |
| `tlg0443.tlg001/025` | Philo, De Opificio + De Providentia | TLG or Cohn-Wendland (Loeb aligned) |
| `tlg0086.tlg048` | Aristotle, De Motu Animalium | First1K or TLG |
| `tlg2017.tlg009/014` | Gregory of Nyssa, De Hom. Opif. / Contra Fatum | TLG or GNO edition |
| `tlg2040.tlg002` | John of Damascus, De Fide Orthodoxa | TLG or Kotter (PTS) |
| `tlg4089.tlg001` | Proclus, In Timaeum | TLG |
| `tlg4036.tlg002` | Iamblichus, De Mysteriis | TLG |

---

## Phase 0: Structural Repairs (no new text needed)

**Effort:** 1 session. Scripts only, no external data.

### 0A. Fix `work_canonical_id` metadata on old SC passage nodes

The 2,816 old-style SC passage nodes lack `work_canonical_id` in their metadata, making them invisible to the `--list` audit. Write a script to backfill from the `part_of` edge chain: passage → work node → look up `ancient_works.canonical_id` via `kg_work_id`.

**Nodes affected:** ~2,816 (SC Origen CC, Pamphilus, Hermas, Ignatius, etc.)

### 0B. Fix 1,534 passage nodes missing `authored_by` edge

Query: find passage nodes with `part_of` → work → `authored_by` → person, then propagate the person edge to the passage.

### 0C. Fill 35 work nodes missing `authored_by`

Cross-reference `ancient_works.author` with existing person nodes. Add edges where unambiguous.

### 0D. Deduplicate school nodes

Merge `school_stoic_school` and `school_stoicism` (39 vs 3 incoming edges). Keep the one with more edges.

### 0E. Add missing school nodes

Create KG nodes (type=school, description only, no fabricated text):
- Neoplatonic School
- Pyrrhonist / Skeptic School
- Megarian School
- Cappadocian Fathers (group node)

### 0F. Fix 114 claim-bearing nodes still without evidence

These were identified in the audit. Review and either add `source_for` edges or flag with `needs_evidence` metadata.

---

## Phase 1: English Translations for Existing Passages (9,856 nodes)

**Effort:** Batch LLM job. No new text ingestion.

### 1A. Write batch translation script

Extend the existing pipeline:
1. Read all passage KG nodes without a corresponding `_en` node
2. Group into batches of ~50 (respecting LLM context limits)
3. Call Gemini/Claude with: "Translate the following {language} passage. Scholarly register. Preserve technical terms in transliteration. Do NOT paraphrase or add commentary."
4. Output JSON in `create_passage_translations.py` format
5. Run `create_passage_translations.py --confirm`

### 1B. Priority order for translations

| Priority | Works | Passages | Rationale |
|----------|-------|----------|-----------|
| P0 | Cicero De Fato, Alexander De Fato (old nodes), Epictetus | ~270 | Core free will texts, highest GraphRAG query frequency |
| P1 | Aristotle NE/Met/DI, Plato Tim/Phd/Phdr, Plutarch De Fato/Stoic Rep | ~800 | Major philosophical sources |
| P2 | Augustine DLA/CivDei/Gratia, Boethius, Methodius | ~500 | Patristic/Late Antique core |
| P3 | Marcus Aurelius, Lucretius, Sextus, Seneca | ~3,300 | Large corpora, high value |
| P4 | Plotinus, DL Lives, Justin, remaining works | ~5,000 | Complete coverage |

### 1C. Estimated cost

~9.8M source characters. At ~4 chars/token, ~2.5M input tokens per pass. With output, ~5M tokens total. At Gemini 2.5 Flash pricing (~$0.15/M input), roughly **$1-2 total** for the translation pass.

---

## Phase 2: Ingest New Primary Sources from Scaife (verified available)

**Effort:** 3-4 sessions. Uses the proven `fetch_de_fato_cts.py` pattern.

### 2A. Generalize the Scaife CTS fetcher

Refactor `fetch_de_fato_cts.py` into a generic `fetch_scaife_work.py`:
- Input: CTS URN, output path, expected language (for validation)
- Rate-limited CTS API calls (0.5s between requests)
- TEI XML stripping, Greek/Latin character ratio validation
- Output: clean JSON ready for `create_kg_passage_nodes.py`

### 2B. Tier 1 ingestions (highest free-will relevance)

| Work | URN | Edition | Est. Sections | Lang |
|------|-----|---------|---------------|------|
| Nemesius, De Natura Hominis | `tlg4090.tlg001` | Morani 1987 (Teubner) | ~44 (ch. 1-44) | grc |
| Plato, Republic (Book X: Myth of Er) | `tlg0059.tlg030` | Burnet (OCT) | ~30 (614a-621d) | grc |
| Plato, Laws (Book X) | `tlg0059.tlg034` | Burnet (OCT) | ~40 (884a-910d) | grc |
| Cicero, De Divinatione | `phi0474.phi042` | Muller (Teubner) | ~130 (2 books) | lat |
| Cicero, De Natura Deorum | `phi0474.phi041` | Plasberg/Ax (Teubner) | ~200+ (3 books) | lat |
| Aristotle, De Generatione et Corruptione | `tlg0086.tlg003` | Bekker (OCT) | ~50 (2 books) | grc |

**Process per work:**
1. `fetch_scaife_work.py --urn <URN> --output /tmp/<work>.json`
2. Validate character ratios, section counts
3. Insert into `passages` table (create `ancient_works` entry if missing)
4. `create_kg_passage_nodes.py` → KG nodes
5. Batch translate → `create_passage_translations.py` → `_en` nodes

### 2C. Tier 2 ingestions (important secondary)

| Work | URN | Edition | Est. Sections | Lang |
|------|-----|---------|---------------|------|
| Galen, De Placitis Hipp. et Plat. | `tlg0057.tlg010` | De Lacy (CMG) | ~100+ (9 books) | grc |
| Clement, Stromata | `tlg2042.tlg012` | Stahlin (GCS) | ~500+ (8 books) | grc |
| Simplicius, In Epicteti Ench. | `tlg0093.tlg001` | Dubner 1842 | ~100+ | grc |
| Basil, Hexaemeron | `tlg2018.tlg001` | Giet (SC 26bis) | ~80 (9 homilies) | grc |
| Tertullian, Adversus Marcionem | `stoa0275.stoa015` | Kroymann (CSEL) | ~150 (5 books) | lat |
| Tertullian, De Anima | `stoa0275.stoa007` | Waszink (CCSL) | ~58 chapters | lat |
| Cleanthes, Hymn to Zeus | `tlg0013.tlg001` | Powell | 1 (39 lines) | grc |
| Clement, Protrepticus | `tlg2042.tlg007` | Stahlin (GCS) | ~120 | grc |

---

## Phase 3: Metadata-Only Nodes (no text, no hallucination risk)

**Effort:** 1 session. KG node creation only — descriptions from verifiable bibliographic data.

### 3A. Missing person nodes

Create with: name, dates, school affiliation, and 1-sentence description citing standard reference works (OCD, BNP, or established encyclopedias).

| Person | Dates | School | Source for description |
|--------|-------|--------|----------------------|
| Diogenes of Oenoanda | c. 2nd c. CE | Epicurean | Smith 1993 edition |
| Aulus Gellius | c. 125-180 CE | None | OCD s.v. "Gellius" |
| Calcidius | 4th c. CE | Neoplatonic/Christian | Waszink 1962 edition |
| Galen of Pergamon | 129-c.216 CE | Eclectic | OCD s.v. "Galen" |
| Simplicius of Cilicia | c. 490-560 CE | Neoplatonic | OCD s.v. "Simplicius" |
| Nemesius of Emesa | fl. c. 390 CE | Christian Platonist | Sharples/van der Eijk 2008 |
| Cleanthes of Assos | 330-230 BCE | Stoic | OCD s.v. "Cleanthes" |
| Josephus, Flavius | 37-c.100 CE | None | OCD s.v. "Josephus" |
| Philo of Alexandria | c. 20 BCE-50 CE | Hellenistic Jewish / Middle Platonist | OCD s.v. "Philo" |
| Lactantius | c. 250-325 CE | Christian | OCD s.v. "Lactantius" |
| Theodoret of Cyrrhus | c. 393-466 CE | Antiochene | OCD s.v. "Theodoretus" |

### 3B. Missing work nodes (for works we cannot yet ingest text for)

Create work KG nodes with: title, author, date, edition reference. Description = bibliographic metadata only, no content summary.

| Work | Author | Edition of record |
|------|--------|-------------------|
| Fragments (SVF II) | Chrysippus | von Arnim, SVF II (1903) |
| De Providentia | Philo | Cohn-Wendland, vol. VI |
| De Opificio Mundi | Philo | Cohn-Wendland, vol. I |
| De Motu Animalium | Aristotle | Nussbaum 1978 (with commentary) |
| Contra Fatum | Gregory of Nyssa | GNO III.2, McDonough 1987 |
| De Hominis Opificio | Gregory of Nyssa | PG 44, Forbes 1855 |
| De Fide Orthodoxa | John of Damascus | Kotter, PTS 12 (1973) |
| Adversus Marcionem II | Tertullian | Kroymann, CSEL 47 |
| Disputatio cum Pyrrho | Maximus the Confessor | PG 91, Doucet 1972 |
| De Natura Hominis | Nemesius | Morani 1987 (Teubner) |
| Bellum Judaicum | Josephus | Niese 1895 |
| Antiquitates Judaicae | Josephus | Niese 1885-95 |

### 3C. Missing source collection node

- **SVF** (Stoicorum Veterum Fragmenta): von Arnim, 3 vols. + index (1903-1924). Type: `source_collection`. This is the standard fragment collection for Stoic philosophy and should be the anchor for Chrysippus, Cleanthes, and Zeno fragment citations.

### 3D. Link existing person nodes to new work nodes

Add `wrote` / `authored_by` edges for all existing person-work pairs that are currently unlinked (see the 107 persons and 35 works identified in the audit).

---

## Phase 4: Sources Not on Scaife (requires alternative sourcing)

**Effort:** Variable. Requires manual verification of each source.

### 4A. Texts available from other digital sources

| Work | Source | Notes |
|------|--------|-------|
| Josephus BJ + AJ | Perseus XML (legacy TEI) | Available at `github.com/PerseusDL/canonical-greekLit` |
| Philo, De Opificio + others | TLG (subscription) or critical edition PDF | Cohn-Wendland via archive.org |
| Gregory of Nyssa, Contra Fatum | GNO digital (if available) or manual from GNO III.2 | Small text (~15 pages) |
| John of Damascus, De Fide | TLG or PG 94 (Migne, public domain) | Kotter PTS for critical text |
| Proclus, De Providentia + De Decem Dubitationibus | Boese 1960 (Latin translation); Isaac 1977 (Greek fragments) | Partially in Latin translation only |
| Iamblichus, De Mysteriis | Des Places 1966 (Bude); Clarke 2003 | Not freely available digitally |

### 4B. Works that remain description-only (no free digital critical edition)

These should exist as work nodes with bibliographic descriptions but no passage text until a digital edition is sourced:

- Epicurus, On Nature Book XXV (PHerc. 1056/1191 — Sedley 1973, Laursen 1995 editions)
- Diogenes of Oenoanda inscription (Smith 1993/2003 edition)
- Maximus the Confessor, Disputatio cum Pyrrho (PG 91)
- Al-Ash'ari, Kitab al-Luma' (McCarthy 1953 edition)

---

## Phase 5: Ongoing Quality Maintenance

### 5A. Re-run KG quality audit after each phase

Use `scripts/audit_kg_quality.py` to verify:
- 0 orphan edges
- 0 provenance gaps on claim-bearing nodes
- All new passages have `passage_citations`
- All new KG passage nodes have `part_of` + `authored_by` edges

### 5B. Qdrant re-embedding

After adding new KG nodes, re-run the Qdrant embedding pipeline to make them discoverable via GraphRAG semantic search.

### 5C. Monitor GraphRAG quality

Test with key queries after each phase:
- "What is Justin Martyr's view on fate?" (should cite Greek, not German)
- "How does Chrysippus respond to the Lazy Argument?" (should cite sources)
- "Compare Stoic and Epicurean views on free will" (should draw from multiple works)

---

## Execution Order

```
Phase 0  (1 session)    Structural repairs, metadata fixes, dedup
  |
Phase 1A (1 session)    Write batch translation script
Phase 1B (batch job)    Run translations: P0 → P1 → P2 → P3 → P4
  |
Phase 2A (1 session)    Generalize Scaife fetcher
Phase 2B (2 sessions)   Ingest Tier 1 Scaife works + translate
Phase 2C (2 sessions)   Ingest Tier 2 Scaife works + translate
  |
Phase 3  (1 session)    Create metadata-only nodes (persons, works, SVF)
  |
Phase 4  (variable)     Alternative-source ingestions
  |
Phase 5  (ongoing)      Quality audits, re-embedding, testing
```

## Appendix: Edition References

All editions cited are standard critical editions used in classical scholarship:

- **Burnet** = J. Burnet, *Platonis Opera* (OCT, 1900-1907)
- **Bekker** = I. Bekker, *Aristotelis Opera* (Berlin Academy, 1831)
- **Morani** = M. Morani, *Nemesii Emeseni De Natura Hominis* (Teubner, 1987)
- **De Lacy** = P. De Lacy, *Galeni De Placitis Hippocratis et Platonis* (CMG V 4,1,2, 1978-84)
- **Stahlin** = O. Stahlin, *Clemens Alexandrinus* (GCS, 1905-09)
- **Dubner** = F. Dubner, *Theophrasti Characteres, Epicteti... Simplicii Commentarius* (Didot, 1842)
- **von Arnim** = H. von Arnim, *Stoicorum Veterum Fragmenta* (Teubner, 1903-1924)
- **Kroymann** = E. Kroymann, *Tertulliani Opera* (CSEL 47, 1906)
- **Waszink** = J.H. Waszink, *Tertullianus De Anima* (CCSL 2, 1954)
- **Cohn-Wendland** = L. Cohn, P. Wendland, *Philonis Alexandrini Opera* (1896-1915)
- **Niese** = B. Niese, *Flavii Iosephi Opera* (1885-1895)
- **Kotter** = B. Kotter, *Die Schriften des Johannes von Damaskos* (PTS 12, 1973)
- **Smith** = M.F. Smith, *Diogenes of Oinoanda: The Epicurean Inscription* (1993; suppl. 2003)
- **Nussbaum** = M. Nussbaum, *Aristotle's De Motu Animalium* (Princeton, 1978)
- **Giet** = S. Giet, *Basile de Cesaree, Homelies sur l'Hexaemeron* (SC 26bis, 1968)
- **Plasberg/Ax** = O. Plasberg, W. Ax, *M. Tulli Ciceronis De Natura Deorum* (Teubner, 1933)
- **Muller** = C.F.W. Muller, *M. Tulli Ciceronis De Divinatione* (Teubner)
