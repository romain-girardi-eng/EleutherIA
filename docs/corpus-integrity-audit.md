# Corpus Integrity Audit — `original`-role passages

> **STATUS: REMEDIATED (2026-05-30).** All tiers fixed. Summary of actions at the bottom; the analysis below is the pre-fix state.


**Scope:** every `passage_role='original'` passage (14,745) classified by *actual text content* (Greek / Latin / English / French / German), cross-checked against the work's declared language. Read-only audit. Translations (`role='translation'`, expected English) and paraphrases (`role='paraphrase'`, expected summaries) are reported separately.

## Headline

The corpus core is **sound**: of 14,745 `original` passages, **10,392 are genuine Greek** and **3,914 genuine Latin** (≈ 97%). The integrity exposure is a concentrated, enumerable tail of ~250 passages, in three tiers.

## Tier 1 — Not original-language text at all (highest severity: ~66 passages)

These claim `role='original'` but contain a modern translation, edition apparatus, a placeholder, or a scrape artifact — no ancient text.

| Count | Work | What the text actually is |
|---|---|---|
| **30** | Origen, *Philocalia* (`tlg2042.tlg02…`) | **French** SC translation — 100% of the work's "original" passages. The Greek is absent here (one Greek *De Princ.* III.1.3 exists under a different node — used in the stub fix). |
| **18** | Methodius, *De Libero Arbitrio* | **German** (GCS critical apparatus / translation). The other 79 passages of this work *are* genuine Greek. |
| **8** | Plato (*Timaeus*, *Republic*), Aristotle *EN*, Alexander *De Fato*, Epictetus | `**Reference:** … **Author:** …` **metadata-only stubs** — no body text. |
| **5** | Calcidius, *In Timaeum* | **Placeholders**: "Section 142: On fate — to be fetched from digilibLT". |
| **3** | Augustine, *De Libero Arbitrio* | **Scrape artifacts**: page navigation ("…The Latin Library  The Classics Page") captured as passage text. |
| **2** | (misc) | "Central text:" English-summary openers. |

## Tier 2 — Real Greek lemmata, but degraded study-note format (~186 passages)

**Epictetus, *Discourses*** — of 235 `original` passages, only **~49 are clean running Greek**. The rest are in a `Greek: • <lemma> — <English gloss>` key-phrase format (or English/French glosses). They contain authentic Greek *words* with CTS anchors, so they're not fabrications — but they are lemma-gloss study notes, not running primary text. This is why GraphRAG cited "Key phrases:" entries for *Disc.* I.1 in the stub fix (no running Greek for I.1 exists in the corpus). Genuine clean Greek *Discourses* text exists for other books (I.18, II.x, etc.).

## Tier 3 — Bilingual "summary + embedded original" (~60 passages, lowest severity)

`original` passages that open with an English analytical summary then carry the real text under a `Latin:` / Greek marker (e.g. Cicero *De Fato* "Carneades's argument… **Latin:** Itaque premebat…"). The ancient text **is present** — only the structure/labeling is impure. These are usable as-is (the stub re-points landed on several of them).

## Explicitly cleared (classifier false positives — NOT problems)

- **Chrysippus, SVF** (~26 "Latin"): legitimate **Latin *testimonia*** (Servius *ad Aen.* etc.) — a fragment collection correctly contains Greek + Latin source witnesses.
- **Aulus Gellius, *NA* VII.2**: Latin prose quoting Greek (`Περὶ Προνοίας…`) — legitimate code-switching.
- **Cleanthes Hymn, Seneca *Ep.***: misdetections — the text is genuine Greek / Latin.

## Other roles (for completeness)

- **`translation` (2,891, English):** expected and correct by design — modern English renderings. Not masquerade.
- **`paraphrase` (~154, mostly Augustine `kg_snapshot` analytical notes):** honestly labeled summaries. The 10 keystone paraphrase *stubs* were already remediated (see stub-fix work); these remaining ones are lower priority but worth a pass for the "summary presented next to a real CTS" pattern.

## Recommended remediation (priority order)

1. **Origen *Philocalia* (30)** — re-point any citations to real Greek (Philocalia 21-27 / *De Princ.* III Greek is available via TLG `tlg2042.tlg001`; or ingest), then fix `role`/language. The French belongs as `role='translation'`.
2. **Methodius (18 German)** — strip/relabel the GCS-apparatus passages as `role='translation'`/notes; the 79 Greek are fine.
3. **Epictetus *Discourses* (~186)** — ingest clean running Greek for the gloss-only sections (esp. I.1) from `tlg0557.tlg001`; demote the lemma-gloss notes or convert to `role='annotation'`.
4. **Stubs/artifacts (Tier 1 misc: 18)** — delete the 5 "to-be-fetched" placeholders, 3 scrape artifacts, 8 `**Reference:**` metadata stubs, 2 "Central text:" openers (or backfill real text).
5. **Tier 3 bilingual (~60)** — optional cleanup: split the English summary off into a note and keep the ancient text pure.

Net: ~66 high-severity + ~186 Epictetus + ~60 bilingual. None are fabricated ancient text; the issue is translations/notes/placeholders wearing the `original` label.

---

## Remediation performed (2026-05-30)

All changes transactional with JSON backups (`/tmp/*_backup.json`); each verified zero orphaned citations.

**Phase 1 — relabel masquerading `original` → `translation` (237 passages):**
- Epictetus *Discourses*: **186** Greek-lemma+English gloss notes (49 genuine running-Greek originals kept).
- Methodius *De Lib. Arb.*: **21** German GCS-apparatus passages (76 genuine Greek kept).
- Origen *Philocalia*: **30** French SC-translation passages.
- Citations preserved (role change doesn't orphan); the texts now declare their true role.

**Phase 2 — Tier 1 stubs/artifacts:**
- 8 `**Reference:**` metadata stubs: 6 re-pointed (11 citations) to real Greek in-work + deleted; 2 relabeled `paraphrase`.
- 5 Calcidius placeholders + 2 "Central text:" openers → relabeled `paraphrase`.
- 3 Augustine scrape artifacts (Latin-Library nav text) → deleted (+3 junk citations).

**Phase 3 — Origen Philocalia coherence:**
- Confirmed the full Greek of *De Princ.* III.1 (= Philocalia 21) already exists as a clean digital passage (`a343b50a`, Περὶ αὐτεξουσίου). No re-ingestion of the OCR `.txt` (self-flagged non-citation-quality) or the bilingual SC 226 `.rtf` was needed.
- Linked all 30 French `translation` passages → `source_passage_id` = the Greek III.1. Philocalia is now coherent: Greek original + honestly-labeled, source-linked French translation.

**Post-fix audit:** `**Reference:**`-as-original = 0; grc "English-with-embedded" 204 → 16; no genuine masquerade remains. The ~60 still flagged by the heuristic are confirmed legitimate (Chrysippus SVF Latin *testimonia*, Hermas' Latin version, Gellius' Greek quotations) or classifier misdetections.

## Deferred (enrichment, not integrity)

- **Epictetus running Greek**: masquerade is fixed, but *Disc.* I.1 still lacks clean running Greek (only the relabeled glosses). Ingesting `tlg0557.tlg001` Book I from Perseus would fill it. Optional.
- **Origen *De Principiis* work-node consolidation**: several duplicate Origen *De Princ.* / Philocalia / Contra Celsum work nodes exist; worth a dedup pass.
- **Tier 3 bilingual (~60)**: "English summary … **Latin:** <real text>" `original` passages — real text present, labeling impure. Cosmetic.

## Enrichment performed (2026-05-30, follow-up)

**Epictetus *Disc.* I.1 running Greek (Task: fill the gloss-only gap):**
- Ingested all **32 sections** of *Discourses* I.1 (`περὶ τῶν ἐφʼ ἡμῖν…`) as `original` Greek from Perseus `tlg0557.tlg001.perseus-grc2` (Schenkl editio maior) into the canonical Discourses work.
- Re-pointed the prohairesis citations to **I.1.23** (the authentic "τὴν προαίρεσιν δὲ οὐδʼ ὁ Ζεὺς νικῆσαι δύναται") and eph'-hemin citations to **I.1.7**; this also deduplicated ~85 redundant citations that pointed at many gloss fragments of the same chapter. The heavily-cited concept nodes remain richly connected (207 / 365 citations); 0 orphans.

**Origen work-node consolidation:**
- Merged the Greek/French split pairs that shared a `kg_work_id`: *Contra Celsum* II (French `20b98c14` → Greek `bb9b6b4c`, now 971 orig + 987 trans) and *De Principiis* SC 268 (`cd288395` → `0918025b`). Origen work nodes 11 → 9.
- **Left for review (not auto-fixed):** 3 work nodes titled "Contra Celsum" whose passages are actually *Commentary on Romans* / *De Principiis* III.1.3 / *De Oratione* 6 — **title mislabels** needing a rename, not a merge. And `46407465` vs `0918025b` are two distinct *De Principiis* editions (different `kg_work_id`), correctly kept separate.

## Work-node consolidation (2026-05-30, follow-up 2)

**Mislabeled fragment works (3):** work nodes titled "Contra Celsum" whose passages were actually *Commentary on Romans* VII.16, *De Principiis* III.1.3, and *De Oratione* 6 — merged each into its correct existing work (matched by `kg_work_id`), deleted the mislabeled node.

**Duplicate work nodes (corpus-wide):** Scanned for `ancient_works` rows that are the same work split into multiple nodes. Used **same author + normalized title** as the signal (NOT `kg_work_id` — see bug below), with a **text-overlap safety gate** (skip any group where passage text is duplicated across nodes).
- Merged **12 groups** (15 duplicate work nodes removed): Augustine *De Lib. Arb.* (×3), Alexander *De Fato*, Plato *Republic*, Plotinus *Enneades*, Clement/Athenagoras/Aristides (Greek+French pairs), Gregory *De Filio*, Theophilus, Melito, Irenaeus, Ps-Barnabas.
- **Seneca *De Providentia*** was caught by the gate (7 cross-contaminated passages — translation-side copies that were actually the Latin original); fixed manually: merged + deleted the 7 dup copies + re-pointed their citations.
- `ancient_works`: 167 → **148**. Zero orphaned citations throughout. Backups in `/tmp/*_backup.json`.

## Open bug flagged (NOT auto-fixed — needs careful per-work reassignment)

**`kg_work_id` is mis-assigned across the corpus.** 39 `kg_work_id` values are shared by 2+ *distinct* works — e.g. `work_de_libero_arbitrio` is on 11 different Augustine works (incl. *De fide contra Manichaeos*); `work_nicomachean_ethics` is on *Magna Moralia*; `work_republic_plato` is on the *Apology*. Bulk-merging on this key would **corrupt** the corpus (it would fuse *Republic* with *Apology*), so it must be fixed by reassigning the correct `kg_work_id` per work — a separate, careful pass, not a mechanical merge.

## Corpus-wide duplicate-passage dedup (2026-05-31)

Full exact-text scan of all 17,799 passages → **359 duplicate clusters** at start. Each fix is lossless (a byte-identical twin is always kept; citations re-pointed; FK refs detached; 0 orphans throughout) and verified per cluster/pair.

- **Phase 1 — 4 full-duplicate works collapsed** (redundant work 100% contained): De Lib. Arb. dup `270ecb79` (170), Cicero *De Fato* dup `3138b941` (48), Lucretius dup `ad4c0fb0` (2), Irenaeus dup `792c5e6e` (1). 221 passages removed, empty works deleted.
- **Phase 2 — 12 same-work internal dups collapsed**: De Civitate Dei (6, exposed by the earlier move), Philocalia (3), Commentary on Romans (2), Melito *Peri Pascha* fr. IV (1).
- **Phase 3 — 123 cross-pair contamination dups removed** (bilingual orig/trans nodes where the translation node held copies of the original-language text): Pamphilus (83), Boethius *Consolatio* (30), Epictetus (6), Hermas (3), Melito (1). Legitimate parallel passages preserved; works NOT merged.

**Result: 359 → 3 duplicate clusters.** The remaining 3 are NOT duplicates — they are a **translation-misalignment error** in Melito *Peri Pascha* §29/§32/§33 (English of §6/§8/§9 wrongly attached; Greek originals are correct and distinct). Left intact, flagged for re-translation (not collapsed, not fabricated).

Net dedup: ~356 redundant passages removed, all with kept twins. Final corpus: see snapshot in the session log.
