# KG Audit Fix — Progress Tracker

Source plan: `docs/superpowers/plans/2026-05-16-kg-audit-comprehensive-fix.md`
Started: 2026-05-16

## Status

| Wave | Status | Script | Commit | Counters |
|------|--------|--------|--------|----------|
| Pre-flight | in_progress | — | — | rdflib 7.6.0 / pyshacl 0.31.0 OK; baseline 19840 nodes / 46288 edges; A2 already done by user (commit 56db8776) — evidence_for→discusses, teacher_of→influences |
| A — Structural P0 | completed | scripts/wave_a_structural_p0_2026_05_16.py | `646dd5a7` (+ fixup `c5434f44`) | dangling_rerouted=65 (+ 16 satisfied by stub creation = 81 total) ; pe_stubs_created=15 ; expanded_renamed=2 ; influenced_merged=87 ; redundant_inverses_dropped=25 ; belongs_to_school_fixed=1 ; tertullien_backfilled=1 ; period_backfilled=26 (25 aug_gla + 1 pub destree) ; source_language_set=1 ; ontology widened (influences) ; dangling=0 post-run ; SHACL invariants conform ; mypy clean after fixup |
| B — Citation Integrity P0 | completed | scripts/wave_b_citation_integrity_2026_05_16.py | `bbcba004` | sc227_removed=2 (work_origen_de_oratione + work_origen_exhortation_martyrdom — fabricated "SC 227 (Junod)" replaced with GCS 2/3 Koetschau 1899 + Bardy 1932 Cerf) ; sc31_branch=A (disk evidence: `SC31_Melito_…_bilingue.txt` cites `Eus. HE IV.XXVI.3 ; SC 31, 209 (Bardy)` — confirmed real extract, cascade-renamed 3 nodes `sc31_melito_peri_pascha_iv*` → `passage_eusebius_he_iv_26_melito_fr_iv*`, 8 edges rewired) ; sc31_updated=1 ; justin_variant_recorded=1 (argument_justin_antifatalism: SC 507 Munier reading promoted to primary, Goodspeed/Otto recorded as variant) ; SHACL invariants Conforms=True ; ruff + mypy strict clean ; idempotent
| C — Doxographic foundations | completed | scripts/wave_c_doxographic_foundations_2026_05_16.py | `1a8bfd22` | collections_added=4 (collection_aetius_placita, collection_dk, collection_ls, collection_dox_graeci_diels) ; publications_added=1 (pub_amand_1973_fatalisme_liberte — Hakkert 1973 reprint of Amand 1944 Louvain thesis, eponym of 2026-05-16-pre-amand-coherence-patches snapshot) ; amand_eponym_added=True ; nodes 19,855 → 19,860 ; SHACL invariants Conforms=True ; mypy strict + ruff clean ; idempotent (2nd run zeros) |
| D — Deduplication | completed | scripts/wave_d_deduplication_2026_05_16.py | `19902e45` | merges_applied=4 ; already_merged=0 ; edges_rerouted=8 ; edges_deduped=10 ; argument_dihle_kept=`scholarly_argument_dihle_greek_philosophical_theology_v_0` (2 edge-refs) dropping `…_dihle_greek_vs_biblical_cosmology_an_4` (0 refs) ; argument_double_kept=`scholarly_argument_double_methodological_reframing_of_fr_1` (tie at 0 refs, lex-smaller wins) dropping `…_double_taxonomy_of_free_will_position_1` ; publisher_correction_applied=True (Long 1996 publisher pub_long_… listed California UP → canonical Cambridge UP, correction trace recorded) ; Inwood scholarly_work_ retained over pub_ duplicate (richer metadata: ISBN, topic_tags, author_id) ; nodes 19,860 → 19,856 ; edges 46,264 → 46,254 ; SHACL invariants Conforms=True (0 violations) ; ruff + mypy strict clean ; idempotent (2nd run: all-zero counters) |
| E — Missing persons | completed | scripts/wave_e_missing_persons_2026_05_16.py | `d27cb30c` | persons_added=20 (3 Patristic Latin Fathers: Athanase/Ambroise/Jérôme ; 3 Hellenistic Stoa+New Academy: Panétius/Diogène Bab/Philon Larissa ; 4 Origen-Maxime specialists: Harl/Perrone/Daley/Louth ; 7 modern free-will/patristics: Stump/Vargas/Timpe/Plantinga/Tieleman/Daniélou/Jacobsen ; 3 ancient: Apulée/Philopon/Cyrille Jérusalem) ; persons_skipped_existing=0 ; teacher_edges_added=4 (Chrysippe→Diog Bab→Panétius→Posidonius + Clitomaque→Philon Larissa, KG convention is `student_of` from student to teacher — no `teaches` inverse exists in ontology) ; school_member_edges_added=4 (Panétius+Diog Bab → school_stoics ; Philon Larissa → school_academics ; Apulée → school_middle_platonism) ; doctorat_refs_found=0 (no local file matches found via filename search for these specific authors) ; scholar naming convention: `scholar_<lastname>_<initial>` (dominant 134/191 existing nodes — matches `scholar_amand_de_mendieta_e`, `scholar_chamberlain_c` reference style) ; nodes 19,856 → 19,876 ; edges 46,254 → 46,262 ; SHACL invariants Conforms=True (0 violations — 58 unrelated quality WARNINGS on Origen passage_role) ; ruff + mypy strict clean ; idempotent (2nd run zeros) |
| F — Missing works | pending | — | — | |
| G — Schools & factions | pending | — | — | |
| H — Ancrage Chrysippe/Carnéade/Cicéron | pending | — | — | |
| I — Position ↔ Debate wiring | pending | — | — | |
| J — Scholarly depth | pending | — | — | |
| K — Maxime monothelite | pending | — | — | |
| L — Synthesis cross-link | pending | — | — | |
| M — Anachronism hedging | pending | — | — | |
| N — SHACL tooling | pending | — | — | |
| O — Bibliography ingestion | pending | — | — | |
| P — Final polish | pending | — | — | |
| Final Gate G1-G7 | pending | — | — | |

## Conventions

- Python: `.venv/bin/python` (Python 3.14.3, rdflib 7.6.0, pyshacl 0.31.0)
- Ontology: `knowledge graph/ontology/edge_types.json` — wrapped under `edge_types` key
- Snapshot per wave: `data/kg/snapshots/2026-05-16-pre-<wave_tag>/`
- Commit per wave (one wave = one commit, sub-tasks J/K/O may have multiple)
- Authorship: Romain alone — NEVER `Co-Authored-By` Claude/AI

## Adjustments vs original plan

- **Wave A.A2 skipped**: already done by user (commit 56db8776) with different but valid mapping (`evidence_for→discusses`, `teacher_of→influences`). Re-use existing ontology preference saved as memory.
- **Wave A residual scope**: re-route 81 dangling, drop 25 redundant inverses (18+7), merge 87 `influenced→influences`, fix 1 `belongs_to_school`, Tertullien backfill, 25 passage_aug_gla period, Epict source_language, 2 _expanded renames.

## Lessons learned (apply to Wave B+)

1. **Don't reflow whole JSON files** — `json.dumps(ontology, indent=2)` re-writes every array as one-item-per-line, blowing up diff surface (731+/146− for one widening). Read+modify selectively or accept the cost in commit message.
2. **Count BEFORE mutation, not via snapshot re-load** — for delta counters like `dangling_rerouted`, compute the count on the in-memory edges list before mutating, not by re-loading the snapshot file after. Cleaner template for reuse.
3. **Type annotations**: use precise `dict[str, dict[str, list[str]]]` not lazy `dict[str, list[str]]` (mypy strict catches this).
4. **`datetime.UTC` over `timezone.utc`** (Python 3.11+ alias; repo is 3.14+).
5. **English identifiers throughout code** — Wave A had `tertullien_backfilled` (FR/EN mix). Use `tertullian_backfilled`.
6. **Snapshot dir convention codified**: `data/kg/snapshots/2026-05-16-pre-<WAVE_TAG>/{nodes,edges}.jsonl` — every wave script uses this.
7. **Always stage explicit paths**, never `git add -A` (main has unrelated dirty files that must not leak into wave commits).
