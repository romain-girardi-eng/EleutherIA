# Primary Sources Audit — 2026-06-10/11

Multi-agent workflow (95 agents) + deterministic TLG E re-verification over the git-tracked
mirror (`data/kg/*.jsonl`, `data/corpus/*.jsonl`). Focus: exact verbatim ancient Greek/Latin
with proper references. Nothing was applied to KG or corpus — all findings are staged queues.

New tooling: `scripts/tlg_search.py` — accent-insensitive search of the full local TLG E disk
(`~/Desktop/Romain/TLGE`, 1,823 authors) in ~1s. Every fabrication/undetermined/attested-external
verdict was machine-rechecked against it (`data/audit/primary_wave/tlg_recheck.json`).

## 1. Greek quotations in KG descriptions (179 runs judged, 159 nodes)

| Verdict | n | Meaning |
|---|---|---|
| verbatim_in_local_edition | 73 | found verbatim in DOCTORAT critical editions |
| verbatim_in_corpus_variant | 57 | in corpus (prefilter false positives: terminology lists, ellipses) |
| attested_external | 21 | confirmed at source via First1KGreek/Perseus/Migne (mostly work titles — titles are absent from TLG body text by nature) |
| **fabricated** | **24** | composed Greek / back-translations from Amand's French / fake loci |
| undetermined | 4 | unverifiable with available editions |

**TLG E recheck:** 20/24 fabrications absent from the *entire* TLG — decisive confirmation.
The 4 "found" are short generic collocations located in *other* authors (Corpus Hermeticum,
Test. XII Patr., Sallustius) — the misattribution stands; verdicts unchanged. Two title checks
upgraded: `δυνάμεις μετὰ λόγου` (Met. Θ.2 1046b verbatim in TLG0086 *and* Alexander TLG0732);
`θεανδρικὴ ἐνέργεια` genuine in Ps-Dionysius Ep. 4 as **καινήν** τινα θεανδρικὴν ἐνέργειαν —
the **μία** variant (Cyrus of Alexandria, Pact §7) is not in TLG E (ACO not covered): keep, but
flag as quoted via conciliar acta.

Recurring fabrication pattern (same as Wave 1b): Greek back-translated from Amand 1945's French
paraphrases and presented in guillemets as Alexander's text, e.g.:
- « φιλανθρωπίας ἕνεκα » → genuine reading **διὰ φιλανθρωπίαν** (De Fato 18 ad fin., passage f9f32da1)
- « ὥσπερ τὰ τῶν βαρέων σωμάτων κάτω φέρεσθαι » → genuine **ὡς τοῖς βαρέσιν ἀφεθεῖσιν ἄνωθεν τὸ φέρεσθαι κάτω** (De Fato 19, passage 4975cde6)
- « αἴτιον οὐκ ἀναγκαστικόν » as Alexander's terminology — stem ἀναγκαστικ- occurs **zero** times in the whole De Fato

Queues:
- `data/audit/primary_wave/fabrications_confirmed.jsonl` (26 = 24 grc + 2 lat) — each with evidence + recommended action
- `data/audit/primary_wave/greek_replacements_deferred.jsonl` (9) — fabrications/omissions where the **verbatim corpus reading is supplied with passage_id**; per policy Romain approves each Greek insertion

Note: the adversarial refute pass was partially killed by a session rate limit (27 agent failures);
the TLG recheck deterministically covers what the refuters would have checked, and is stronger.

## 2. Latin quotations (17 judged, 9 nodes — first Latin audit)

13 verified (corpus or local edition), 2 need reference fixes, **2 fabricated**:
- `concept_non_causa_sed_occasio`: "Quomodo sol non est causa caecitatis... sed occasio tantum" — unverifiable as quoted
- `concept_providentia_fatum_boethius_h3i4j5k6`: "fatum ex providentiae fonte proficiscitur" — genuine Boethius (Cons. IV.6) reads *ordo namque fatalis ex providentiae simplicitate procedit*; node also has a *verified* verbatim quote of the same doctrine

Latin caveat: no PHI disk locally — Latin attestation relied on corpus + DOCTORAT + web critical
editions. **If a PHI Latin CD exists, wire it like TLGE.**

## 3. English masquerading as original text in the corpus (the big one)

13 works, 182 passages where `text_content` is an English summary under a `_lat`/`_grc` work id
with CTS URNs. All sourced and staged under `data/audit/primary_fetch/<work>/` (+ `.verdict.json`
each, with passage-level `mapping.json`):

| Work | n | Source found | Conf |
|---|---|---|---|
| Augustine De Libero Arbitrio (`stoa0040_stoa003_lat`) | 170 | augustinus.it ⚠ verify edition vs CSEL 74 | 0.97 |
| Cicero De Fato (`phi0474_phi049_lat`) | 48 | **local** `02_Corpus/Cicero_De_Fato_LAT…` | 0.98 |
| De Civ. Dei V.xii-xiv (`stoa0040_stoa001_…_lat`) | 8 | Scaife (5 hybrid + 3 footer-junk deletions) ⚠ verdict cites stoa003 URNs — review | 0.95 |
| Origen Comm. Rom. (grc) | 2 | local SC | 0.7 |
| Plotinus Enneads (4 nodes), Epictetus, Origen De Princ., Alexander De Fato, Lucretius | 1 each | local/First1KGreek | 0.85–0.95 |
| `plotinus_plotinus_enneads` (thematic multi-treatise summary) | 1 | — do not auto-replace | low |

Also fixes recorded for the systematic URN mismatches (work id `phi049` vs URN `phi056`;
`canonical_ref 1.1.1` vs URN `:2.1.1`).

## 4. Ingestion gaps (12 `needs_text_ingestion` works)

10 scaife_ready with verified URNs (4 Macc, Retractationes, Cassian Conl. 13, Cleanthes Hymn
via Stobaeus 1st1K `tlg1269.tlg002:537`, Lactantius Div. Inst., Plato Sophist, Plutarch ×3,
Wisdom — also local Göttingen LXX); 2 other_source (Apuleius De Platone, Theodoret Graec. aff.
cur. — both ARE in TLG E/other; Theodoret = TLG4089, extractable once locus mapping exists).

## 5. Verbatim spot-check vs local SC editions (72 samples, 9 works)

53 exact, 17 normalized (OCR-level diacritic noise), **2 divergent — a real defect class**:
passages whose `text_content` contains a **Markdown metadata wrapper** (`**Reference:** … **Word
Count:** …`) and raw OCR page markers (`--- 102 ---`) instead of clean source text
(Contra Celsum VII.66; Barnabas 4.9b-14). Deterministic sweep recommended: grep corpus for
`**Reference:**` / `--- \d+ ---` inside `text_content`.

## 6. Ontology (read-only conformance audit)

**Fully conformant**: 54/54 relations defined, 0 domain/range violations, 0 dangling endpoints,
all 2,136 citation-bearing edges carry confidence. Cleanup backlog (mechanical):
- 198 exact duplicate triples (187 = `passage_epict_* discusses synthesis_epict_eph_hemin_doctrine`, double-ingested batch)
- 3 self-loop `engages_with` edges (scholars engaging with themselves)
- 28 dangling `inverse` declarations + 6 asymmetric inverse pairs (e.g. influenced/influenced_by/influences fragmentation: 166/88/27)
- 21 defined edge types and 7 node types unused (decide: implement or prune from ontology)

## Proposed apply order (each item individually verified; awaiting go)

1. **A — KG descriptions**: 26 fabrication fixes (English replacement or reference fix) — surgical, per-item evidence in queue.
2. **B — Greek replacements (9)**: verbatim corpus readings supplied; Romain approves each.
3. **C — Corpus restoration**: apply staged `mapping.json` per work; start with Cicero De Fato (local source, 0.98); hold Augustine until edition check vs CSEL 74.
4. **D — Mechanical**: duplicate edges, self-loops, metadata-wrapper sweep (§5), URN mismatch fixes.
5. **E — Ingestions**: 10 scaife_ready works; TLG locus mapping (.IDT parsing) unlocks Theodoret + future Greek ingestion directly from TLG E.
