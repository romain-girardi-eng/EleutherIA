# KG Audit Fix — Progress Tracker

Source plan: `docs/superpowers/plans/2026-05-16-kg-audit-comprehensive-fix.md`
Started: 2026-05-16

## Status

| Wave | Status | Script | Commit | Counters |
|------|--------|--------|--------|----------|
| Pre-flight | in_progress | — | — | rdflib 7.6.0 / pyshacl 0.31.0 OK; baseline 19840 nodes / 46288 edges; A2 already done by user (commit 56db8776) — evidence_for→discusses, teacher_of→influences |
| A — Structural P0 | completed | scripts/wave_a_structural_p0_2026_05_16.py | `646dd5a7` (+ fixup `c5434f44`) | dangling_rerouted=65 (+ 16 satisfied by stub creation = 81 total) ; pe_stubs_created=15 ; expanded_renamed=2 ; influenced_merged=87 ; redundant_inverses_dropped=25 ; belongs_to_school_fixed=1 ; tertullien_backfilled=1 ; period_backfilled=26 (25 aug_gla + 1 pub destree) ; source_language_set=1 ; ontology widened (influences) ; dangling=0 post-run ; SHACL invariants conform ; mypy clean after fixup |
| B — Citation Integrity P0 | completed | scripts/wave_b_citation_integrity_2026_05_16.py | _pending_commit_ | sc227_removed=2 (work_origen_de_oratione + work_origen_exhortation_martyrdom — fabricated "SC 227 (Junod)" replaced with GCS 2/3 Koetschau 1899 + Bardy 1932 Cerf) ; sc31_branch=A (disk evidence: `SC31_Melito_…_bilingue.txt` cites `Eus. HE IV.XXVI.3 ; SC 31, 209 (Bardy)` — confirmed real extract, cascade-renamed 3 nodes `sc31_melito_peri_pascha_iv*` → `passage_eusebius_he_iv_26_melito_fr_iv*`, 8 edges rewired) ; sc31_updated=1 ; justin_variant_recorded=1 (argument_justin_antifatalism: SC 507 Munier reading promoted to primary, Goodspeed/Otto recorded as variant) ; SHACL invariants Conforms=True ; ruff + mypy strict clean ; idempotent
| C — Doxographic foundations | pending | — | — | |
| D — Deduplication | pending | — | — | |
| E — Missing persons | pending | — | — | |
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
