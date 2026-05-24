# Corpus Recovery & Passage-Level Grounding — Design

**Date:** 2026-05-24
**Status:** Design (awaiting review)
**Author:** Romain Girardi

## Problem

The deleted Supabase project took the full corpus with it. The replacement
project (`alqwfeddgigzpxrdbdbo`) was rebuilt from the git KG mirror, which only
carries the **KG-linked** passages — so the corpus is now **174 works / 16,620
passages** vs the documented **487 / ~69k**. Worse, the rebuild left **19,971
`passage_citations` pointing at only 16,620 passages** — dangling references
where the cited passage no longer exists.

Two structural lessons:
1. The corpus had no git-backed, gated, reproducible pipeline (only the KG did),
   so it wasn't recoverable when the DB died.
2. Corpus and KG drifted into two partly-overlapping passage representations.

## Goals

- Make the corpus **recoverable from git** and reproducible from a manifest, so
  a future DB loss is not catastrophic.
- Scope the corpus to **free-will-relevant works only**, each ingested as a
  **full work** at passage level.
- Keep the KG as a **thin overlay** of only the passages that participate in the
  graph (cited), referencing the corpus rather than duplicating text.
- Use the recovery as a **grounding-quality pass**: add missing citations, verify
  existing ones, remove spurious ones.
- Enforce the invariant that **every citation and every overlay node resolves to
  a corpus passage that exists** (no dangling references).

## Non-goals

- Restoring the full broad ~69k corpus. Out of scope by decision — corpus =
  free-will-relevant works only. A broad-recall expansion is a possible later,
  separate project.
- Turning every corpus passage into a KG node. Rejected: it conflates the search
  layer with the reasoning layer, adds ~tens-of-thousands of near-isolated nodes,
  and breaks the git-mirror / SHACL-gate discipline.
- Ingesting critical apparatus, editors' commentary, introductions, or modern
  translations. Only the **ancient text** is ingested.

## Key constraints

- **Academic integrity (golden rule):** never fabricate ancient text. Every
  passage must come from a critical edition (Migne PG/PL, SC, GCS, CCSL, PTS,
  Loeb, BT) or an openly-licensed digital edition (Perseus/Scaife). Preserve
  diacritics exactly.
- **Copyright:** the ancient text itself is not copyrightable, even in SC
  editions — only apparatus/commentary/introductions/translations are. Therefore
  the corpus **text may be committed to the public git repo**. We never store or
  expose the protected editorial layers.
- **Git size:** `nodes.jsonl` is already ~54MB and tripping GitHub's 50MB
  warning. The overlay must not duplicate passage text; corpus text lives once,
  in a dedicated corpus file.

## Architecture — four layers

1. **Corpus manifest** — `data/corpus/manifest.jsonl`, git-tracked. One row per
   in-scope work: `canonical_id`, CTS work URN, author, period, `source`
   (`scaife:<urn>` | `doctorat:<path>`), ingest status, expected passage count.
   This is simultaneously the curated relevant-works list and the **deterministic
   rebuild recipe**.

2. **Corpus passages** — `passages` table + git-tracked
   `data/corpus/passages.jsonl`. The **full text** of each in-scope work at
   passage level, **ancient text only**. System of record for text, full-text
   search (`ts_rank`), lemmas (`morphology`), and work→book→chapter→passage
   hierarchy. Git-tracked = durable backup.

3. **KG passage overlay** — `kg_nodes type=passage`, in `nodes.jsonl`. Only
   passages that participate in the graph (have a `passage_citation`). Each is a
   **thin reference** to its corpus passage by CTS URN / `passage_id` — not a
   copy of the text (existing overlay nodes get slimmed: text dropped, reference
   kept).

4. **Bridge** — `passage_citations` (`passage_id ↔ kg_node_id`, `citation_type`,
   `confidence`). Defines which passages earn an overlay node.

**Core invariant (gate-enforced):** every `passage_citation` and every overlay
node resolves to a corpus passage that exists. No dangling references.

## Data flow

```
sources (Scaife/Perseus, DOCTORAT critical editions)
      │  Phase 1 ingest (full works, text-only)
      ▼
data/corpus/passages.jsonl  ──deploy gate──▶  Supabase free_will.passages
      ▲                                              │
manifest.jsonl (scope + recipe)                      │ passage_citations
      │                                              ▼
   Phase 0 derive+curate              kg_nodes (overlay = cited passages)
                                                      ▲
                                          nodes.jsonl (git) ──KG deploy──▶ Supabase
```

## Build sequence

- **Phase 0 — Manifest.** Derive in-scope works from the KG (work nodes + works
  behind the 19,971 citations + works behind argument/concept nodes), emit
  `manifest.jsonl` with a proposed source per work. **User curates** (add/remove).
  Output freezes the agreed scope.

- **Phase 1 — Ingest full works** (priority-ordered by citation density /
  thesis-centrality). Per manifest work: fetch full text at passage level from
  its source — Scaife/Perseus, or DOCTORAT critical editions where not on Scaife
  — text-only, stable CTS URNs, with lemmas + hierarchy. Idempotent, snapshotted.

- **Phase 2 — Reconcile citations.** Re-link `passage_citations` to the
  now-present passages by CTS URN. Report any citation that still cannot resolve
  (genuinely missing source) for manual handling.

- **Phase 3 — Curate & verify the overlay** (bidirectional, human-reviewed; not a
  blind prune):
  - *Uncited overlay nodes* → review queue. If a KG argument/concept actually
    rests on the passage → **add the missing citation** (enrich). Only if
    genuinely irrelevant → demote to corpus-only.
  - *Newly-surfaced corpus passages* (revealed by full-work ingestion) →
    relevance-ranked, presented as **citation candidates** for relevant
    arguments/concepts. Suggestions only, verified before linking (honors the
    "no forced connections" rule).
  - *Verify existing citations* against the re-ingested text (reuse the GraphRAG
    text-verifier): confirm each cited passage still supports the citing claim;
    flag drift.
  - Output: a reviewed curation report; overlay ends up genuinely grounded.

- **Phase 4 — Git + gate.** Commit `data/corpus/{manifest,passages}.jsonl`. Add a
  **corpus deploy gate + snapshot** mirroring the KG `git → Supabase` pipeline.
  Deploy. The corpus now has the same idempotent, gated, recoverable discipline
  as the KG.

## Components to build

- `scripts/derive_corpus_manifest.py` — Phase 0: emit `manifest.jsonl` from KG.
- `scripts/ingest_work.py` (or extend `ingest_scaife_work.py`) — Phase 1:
  manifest-driven full-work ingestion → corpus.
- `scripts/reconcile_citations.py` — Phase 2: re-link + dangling report.
- `scripts/curate_overlay.py` — Phase 3: build review/candidate queues + verify.
- `scripts/deploy_corpus_to_supabase.py` + `scripts/export_corpus_snapshot.py` —
  Phase 4: gated deploy + git export (mirror the KG scripts).
- A **corpus invariants gate** (extend the SHACL/CI gate or a sibling check):
  0 dangling citations; every overlay node resolves; every manifest work has ≥1
  passage.

## Success criteria

- 0 dangling citations; every overlay node resolves to a corpus passage; every
  manifest work has ≥1 ingested passage.
- **Reproducible:** wipe + rebuild corpus from `manifest.jsonl` → identical
  passage set (checksums match).
- **Round-trips** git ↔ Supabase (as the KG superset sync now does).
- **Integrity:** spot-check ingested text vs critical editions; no
  apparatus/commentary leaked; diacritics intact; zero fabricated text.
- Coverage report: per-work passage counts vs expected (De Int. 9 present, EN III
  present, De Principiis present, etc.).

## Risks / open questions

- **Source availability:** some in-scope works are not on Scaife (per memory:
  Nemesius, Cleanthes Hymn, Philo De Providentia, Aristotle De Motu). These need
  DOCTORAT critical-edition ingestion or are blocked pending an edition.
- **CTS URN stability:** re-ingestion must reproduce the *same* URNs the existing
  citations use, or Phase 2 can't relink. Where the deleted corpus used
  non-standard refs, a mapping table may be needed.
- **Overlay slimming churn:** dropping duplicated text from existing overlay
  nodes is a large one-time diff to `nodes.jsonl` (acceptable; reduces size).
- **Phase 3 is iterative,** not one-shot — curation runs in reviewed batches
  (like the prior E2 verification waves).
