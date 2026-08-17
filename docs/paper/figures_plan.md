# EleutherIA data paper — figures and tables plan

This plan proposes five submission assets. The two tables already contain their final data; the three figures remain to be drawn. All labels and values must be regenerated from the cited repository files immediately before submission.

## Figure 1 — Dataset layers and provenance boundaries

**Purpose.** Show why EleutherIA is a graph rather than a flat corpus and make the epistemic separation between source text and interpretation visible.

**Proposed layout.** A left-to-right diagram with four bands:

1. named ancient editions and digital witnesses;
2. corpus passages with `canonical_ref`, CTS URN, provenance, and text hash;
3. the asserted knowledge graph (ancient primary layer and modern-reception layer shown separately);
4. derived services and formats: API, GraphRAG, RDF/SKOS/SHACL, and BibTeX.

Use solid arrows for asserted data lineage, dashed arrows for derived inference, and a visibly different edge for modern scholarly interpretation. Mark the semantic layer as read-only and derived. Do not display stale counts from architecture documentation.

**Sources.** `README.md`; `CLAUDE.md`; `docs/academic/METHODOLOGY.md`; `docs/architecture/semantic-layer.md`; `docs/operations/corpus-integrity.md`; `docs/reference/API.md`.

**Caption draft.** “EleutherIA’s data layers and provenance boundaries. Ancient text, graph assertions, modern interpretation, and derived semantic or retrieval services remain distinguishable.”

**Alt text (maximum ten words).** “Editions flow through corpus and graph to reusable services.”

## Table 1 — Deep-audit findings by dimension

**Purpose.** Give the exact size and scope of the four-dimensional audit while stating that a finding is not automatically a confirmed error.

| Dimension | JSONL records | Principal scope |
|---|---:|---|
| Structural | 41 | identity, types, graph integrity, duplicates, orphans |
| Linguistic | 1,589 | OCR, script, encoding, language, translation status |
| Bibliographic | 3,683 | identifiers, loci, references, citation materialisation |
| Semantic | 108 | thesis duplication, vocabulary, relation meaning |
| **Total** | **5,421** | line-level findings before source-based adjudication |

**Counting method.** Count parsed JSON objects, one per line, in the four files. The repository files currently sum to 5,421 records. Do not reproduce the earlier 5,425 narrative total unless the JSONL corpus itself changes and the discrepancy is resolved.

**Sources.**

- `data/audit/2026-08-16_deep_audit_structural.jsonl`
- `data/audit/2026-08-16_deep_audit_linguistic.jsonl`
- `data/audit/2026-08-16_deep_audit_bibliographic.jsonl`
- `data/audit/2026-08-16_deep_audit_semantic.jsonl`

**Caption draft.** “Line-level findings in the four-dimensional deep audit. Counts describe review records, not adjudicated error prevalence.”

## Figure 2 — Reproducible repair and prevention cycle

**Purpose.** Visualise the paper’s main methodological contribution.

**Proposed layout.** A closed cycle:

`detector finding → source-based adjudication → dated data module → dry-run applier → per-item preconditions → invariants → backup and atomic write → applied report → incident-named ingestion rule → later stratified verification`.

Add two exit branches from source-based adjudication: `false positive / keep with evidence` and `blocked on source / preserve visible debt`. Add a loop from a second execution of the applier to `no-op`, illustrating idempotence.

**Sources.** `CLAUDE.md` (“Never hand-edit” and gates); all `data/audit/2026-08-17_*_plan.md` and `data/audit/2026-08-17_*_applied.md`; `docs/development/ingestion-rules.md`; `scripts/check_ingestion_rules.py`.

**Caption draft.** “EleutherIA’s audit–repair–prevention cycle. Corrections are evidence-bearing, conditional, replayable, backed up, and converted into future ingestion gates.”

**Alt text (maximum ten words).** “Findings become evidenced repairs, gates, and later verification.”

## Table 2 — Stratified verification results and Wilson intervals

**Purpose.** Reproduce the report’s actual per-stratum table without converting mechanical verdicts into unqualified error rates.

| Stratum | n | EXACT | MINOR | SUBSTANTIVE | INDISPO | Wilson 95% CI (substantive) | Median CER |
|---|---:|---:|---:|---:|---:|---|---:|
| SC-series OCR | 40 | 15 | 25 | 0 | 0 | [0.0% ; 8.8%] | 0.0% |
| TLG E realignments | 40 | 5 | 15 | 20 | 0 | [35.2% ; 64.8%] | 1.1% |
| Perseus/web | 40 | 0 | 9 | 12 | 19 | [18.1% ; 45.4%] | 1.8% |
| First1KGreek | 40 | 0 | 3 | 37 | 0 | [80.1% ; 97.4%] | 21.0% |

**Mandatory interpretive note.** The SC result measures fidelity to the ingestion files rather than independent editorial correctness. The TLG stratum mixes text re-ingestion and Plotinus reference remapping. Perseus/web includes unavailable local authorities. The First1KGreek result is dominated by span misalignment and is non-conclusive until aligned re-collation. The table must never be captioned simply as “error rate by source.”

**Sources.** `data/audit/2026-08-17_stratified_verification.md`; the 160 unit records in `data/audit/2026-08-17_stratified_verification.jsonl`.

**Caption draft.** “Raw mechanical verdicts from a deterministic stratified sample. Human inspection is required to distinguish corruption, edition variance, and span misalignment.”

## Figure 3 — Snapshot trajectory: expansion and curation contraction

**Purpose.** Replace a simplistic “graph growth” chart with a trajectory that shows corpus expansion alongside graph consolidation.

**Proposed plot.** Two dated snapshot groups, with separate panels or clearly distinct scales for graph and corpus measures:

| Snapshot | Graph nodes | Asserted edges | Work nodes | Corpus passages | Passage citations |
|---|---:|---:|---:|---:|---:|
| v5.1.0 snapshot, 2026-06-05 | 20,060 | 56,737 | 241 | 17,823 | 19,751 |
| Generated snapshot, 2026-08-17 | 19,994 | 49,391 | 249 | 21,103 | 19,917 |

The graphic should explain that fewer asserted edges do not mean data loss: inverse normalisation and semantic/work deduplication intentionally removed redundant or incorrect assertions, while corpus passage coverage increased. Do not connect only two points with a trend line implying a measured rate of change.

**Sources.** `docs/releases/v5.1.0.md`; `data/stats.md`; `data/stats.json`; `data/audit/2026-08-17_inverse_normalization_plan.md`; `data/audit/2026-08-17_semantic_merges_applied.md`; `data/audit/2026-08-17_work_conflation_applied.md`.

**Caption draft.** “Snapshot trajectory from v5.1.0 to the post-audit dataset. Corpus coverage expands while redundant asserted graph structure is consolidated.”

**Alt text (maximum ten words).** “Corpus expands while audited graph assertions contract and consolidate.”

## Production notes

- Produce figures as SVG source plus 300 dpi PNG for submission; keep the repository copy under `docs/paper/` only if later authorised as a new additive asset.
- Use a colour-blind-safe palette and never encode status by colour alone.
- Include direct labels where possible; avoid legends that separate a datum from its meaning.
- State “asserted edges” rather than “all relations” wherever inverse or transitive relations may be derived at runtime.
- Re-run all counts from the cited snapshot before producing final artwork.
