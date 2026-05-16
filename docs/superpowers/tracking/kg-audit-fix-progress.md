# KG Audit Fix — Progress Tracker

Source plan: `docs/superpowers/plans/2026-05-16-kg-audit-comprehensive-fix.md`
Started: 2026-05-16

## Status

| Wave | Status | Script | Commit | Counters |
|------|--------|--------|--------|----------|
| Pre-flight | in_progress | — | — | rdflib 7.6.0 / pyshacl 0.31.0 OK; baseline 19840 nodes / 46288 edges; A2 already done by user (commit 56db8776) — evidence_for→discusses, teacher_of→influences |
| A — Structural P0 | completed | scripts/wave_a_structural_p0_2026_05_16.py | — | dangling_rerouted=65 (+ 16 satisfied by stub creation = 81 total) ; pe_stubs_created=15 ; expanded_renamed=2 ; influenced_merged=87 ; redundant_inverses_dropped=25 ; belongs_to_school_fixed=1 ; tertullien_backfilled=1 ; period_backfilled=26 (25 aug_gla + 1 pub destree) ; source_language_set=1 ; ontology widened (influences) ; dangling=0 post-run ; SHACL invariants conform |
| B — Citation Integrity P0 | pending | — | — | |
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
