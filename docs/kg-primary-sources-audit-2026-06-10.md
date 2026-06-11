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

## Apply status (Romain approved "fix all", 2026-06-11)

- **A+B — APPLIED**: 55 surgical description patches (53 workflow-generated + 2 manually re-verified)
  + 3 metadata `cts_urn` fixes (Plutarch ×2; Sextus PH was pointing at Origen's tlg2042!).
  Every new Greek machine-gated: must be verbatim in corpus, local edition, or TLG E.
  1 patch superseded (overlap), 1 correctly skipped (evidence didn't confirm — original kept).
  Changelog: `data/audit/primary_wave/description_patch_changelog.jsonl`.
- **C — APPLIED**: 237 passages restored to verbatim originals (236 from gated mappings + De Civ.
  Dei V.9.3 hybrid recovered separately, cross-validated against its DB-verified fragments);
  61 passage cts_urn fixes; 3 footer-junk passages + 3 orphan citations deleted.
  All 242 mapping entries gated (verbatim-in-staged-source check) before write; restored
  Plotinus III.1 verified verbatim in TLG2000. Augustine De Lib. Arb. applied from augustinus.it
  (NBA) — **CSEL 74 collation still recommended**. Changelog: `restore_changelog.jsonl`.
- **D — APPLIED**: 198 duplicate triples + 3 self-loops removed; metadata-wrapper sweep found 28
  (not 2) — 27 stripped to clean Greek, 1 (Aristides SC 470, corrupt OCR) deferred;
  `influenced`→`influences` (88 edges, 87 were importer double-writes) and
  `belongs_to_school`→`member_of` migrated; `has_member.inverse` fixed; alias types marked
  deprecated in `edge_types.json`. Edges 56,737 → 56,448. The 28 "dangling inverses" are
  intentional (vocab.py curates `CLEAN_INVERSE_PAIRS`) — left alone.
- **E — pending**: 10 scaife_ready ingestions (next wave); TLG .IDT locus parsing unlocks
  Theodoret (TLG4089) + direct TLG ingestion.

**Design decisions left for Romain**: prune-or-implement the 7 unused node types / 21 unused
edge types; synonym predicate families (student_of/teaches/taught_by, member_of/has_member);
work_canonical_id strings that misname their work (stoa001 vs stoa003) — invasive FK rename,
belongs in the data-normalization track.

## Follow-up wave (2026-06-11, "do it all")

- **Theodoret, Graec. aff. cur. — INGESTED (1,095 passages)** directly from the local TLG E disk:
  compiled `tlgu` (Marinakis, GPL) to decode TLG4089.001 with full book/section/line citations;
  TLG canon confirms the underlying edition is **Canivet, SC 57 (1958)** — the SC critical
  edition. Section-level passages (median 359 chars), editorial ⟨⟩ normalized. Book 6 = Περὶ
  προνοίας (92 passages) now available for providence/fate work.
- **Aristides SC 470 — FIXED**: the corrupt-OCR papyrus passage replaced with the verbatim
  SC 470 transcription (P.Oxy XV 1778 + Heidelberg G 1013, fol. 1v = Apol. V,2) from the local
  source file, editorial restorations `[...]` preserved as printed.
- **Apuleius De Platone — honestly NOT ingested**: no open critical edition with stated
  provenance exists online (Perseus lacks it; csel-dev none; Bibliotheca Augustana uncredited).
  Blocked-reason recorded in node metadata; needs Thomas BT 1908 scan, Moreschini BT, or PHI disk.
- **CSEL 74 collation of De Lib. Arb. — requires the physical volume** (CSEL 74 in copyright,
  no digital text; csel-dev does not include it). The applied augustinus.it/NBA text keeps full
  per-passage provenance in `restore_changelog.jsonl`; collate when the volume is at hand.
- **Ontology organized via `status` field** on every type: edge types 52 active /
  16 reserved_inverse (zero instances but targets of OWL inverse materialization — keep) /
  5 reserved (true pruning candidates: attested_by, attests, founded, position_in_debate;
  has_member kept as declared inverse) / 2 deprecated (influenced, belongs_to_school).
  Node types: 17 active / 7 reserved. Shapes generator verified tolerant of the new field.

Corpus now **20,415 passages**. Sole remaining text gap: Apuleius De Platone.

## Quality wave (2026-06-11, "fix them all except lemmas")

1. **Zero-fabrication gate** (`scripts/check_greek_gate.py` + pre-commit hook + allowlist with
   provenance): any Greek entering a node description must be verbatim in corpus/allowlist/TLG E.
   On its first full run it caught 2 runs the audit prefilter missed — both verified genuine
   via TLG and allowlisted with provenance.
2. **Fake loci eliminated**: the Sextus/Epictetus chunk corpus carried sequence numbers
   disguised as citations ('M. 100' over Outlines text). Real loci recovered by multi-probe
   alignment against tlgu-decoded TLG E: 1,215 nodes + 339 corpus passages now cite true
   work+locus; 11 unresolvable marked honestly. 66 further malformed URNs normalized.
3. **Coverage ingestions from TLG E** (`scripts/ingest_from_tlge.py`): Ammonius In De Int.
   (CAG 4.5), Alexander Mantissa + Quaestiones + Eth. Probl. (Bruns), John of Damascus
   Expositio fidei (Kotter PTS 12) — 708 passages; KG nodes created/linked.
4. **Citation style**: `docs/reference/CITATION_STYLE.md`; 189 refs normalized, 77 Damascene
   title-units merged.
5. **QID backfill**: 371 persons (each QID's Wikidata entity actually read before acceptance);
   the duplicate-QID gate exposed **4 duplicate person pairs**, merged (incl. the mislabeled
   'Dorothea' node that is in fact Michael Frede).
6. **Citation grounding**: 219 verbatim-gated passage citations for 121 previously uncited
   claim nodes; 36 not-groundable recorded with the precise missing locus.
7. **Prod deploy-up**: Supabase is back; KG deployed (bootstrap --replace-data);
   `scripts/sync_corpus_to_db.py` rebuilds the corpus tables from the mirror
   (free-tier disk requires split transactions). Final sync pending at time of writing.

Skipped on request: lemmatization of new passages.
