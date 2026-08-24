# EleutherIA Documentation

## Quick Links

| Guide | Description |
|-------|-------------|
| [Quick Start](guides/QUICK_START.md) | Get running in 5 minutes |
| [Architecture](architecture/OVERVIEW.md) | System design and components |
| [API Reference](reference/API.md) | REST API documentation |
| [Data Dictionary](reference/DATA_DICTIONARY.md) | Database schema reference |

## For Developers

- [Development Setup](development/SETUP.md) - Environment setup, testing, code quality
- [Browser Automation](development/agents.md) - Using browser-use for automation tasks
- [API Examples](examples/) - cURL and Python usage examples
- [Contributing](../.github/CONTRIBUTING.md) - How to contribute

## For Researchers

- [Methodology](academic/METHODOLOGY.md) - Scholarly methodology, FAIR principles, citation standards
- [Academic Integrity](ACADEMIC_INTEGRITY.md) - Authenticity policy and enforcement gates
- [SOTA Program (2026-08-24)](goals/SOTA-2026-08-24.md) - Living evidence, GraphRAG, multi-mode atlas, performance and SEO/GEO execution program
- [SOTA Audit (2026-08-24)](reports/2026-08-24-sota-audit.md) - Evidence-backed findings, applied P0 repairs and remaining blockers
- [Irenaeus Witness Audit (2026-08-24)](data-audit/2026-08-24-irenaeus-free-will-data-audit.md) - Latin, Armenian, Greek-fragment, retroversion and false-twin matrix
- [Sextus Boundary Audit (2026-08-24)](academic/2026-08-24-sextus-boundary-concatenation-audit.md) - Exhaustive PH/AM chunk-boundary and CTS review
- [Origen Manifestation Audit (2026-08-24)](../data/audit/2026-08-24_origen_manifestation_conflicts_readonly_audit.md) - De principiis, Philocalia, Romans and Exhortatio witness/language matrix
- [Sorabji PDF Audit (2026-08-24)](academic/2026-08-24-sorabji-necessity-cause-blame-pdf-audit.md) - Full scan/page map, claim inventory and manifestation cautions
- [Sorabji P0 Independent Review v4](academic/2026-08-24-sorabji-p0-independent-review-v4.md) - Hash-bounded PASS for the applied transaction; scholarly issues remain open
- [Long–Sedley Volume 2 Audit (2026-08-24)](academic/2026-08-24-long-sedley-volume2-pdf-audit.md) - Volume/printing identity and exact LS 20/55/62 witness map
- [Tatian SAPERE 28 Audit (2026-08-24)](academic/2026-08-24-tatian-sapere28-pdf-audit.md) - Copyright-bounded collation, false snapshots and edition-specific loci
- [Tatian P0 Independent Review](academic/2026-08-24-tatian-p0-independent-review.md) - Current FAIL report and executable blockers; not an apply authorization
- [Tatian P0 Independent Review v2](academic/2026-08-24-tatian-p0-independent-review-v2.md) - Second FAIL: 15.9 evidence alignment, generic verification flags and concurrent-drift rollback
- [Tatian P0 Independent Review v4](academic/2026-08-24-tatian-p0-independent-review-v4.md) - Final post-Hildebrandt PASS for the applied Tatian transaction; broader debts remain open
- [Tatian Postwrite Test Review](academic/2026-08-24-tatian-postwrite-test-review.md) - Independent PASS on the composable postwrite harness
- [Hildebrandt Lazy Argument Audit (2026-08-24)](academic/2026-08-24-hildebrandt-lazy-arguments-pdf-audit.md) - Full-article read and bibliographic/provenance defects
- [Hildebrandt P0 Independent Review](academic/2026-08-24-hildebrandt-p0-independent-review.md) - FAIL-NO APPLY on the frozen executable tuple; scholarly checks pass
- [Hildebrandt P0 Independent Review v2](academic/2026-08-24-hildebrandt-p0-independent-review-v2.md) - Final PASS on the rebased transaction and exact postwrite state
- [Sharples, Alexander on Fate Audit (2026-08-24)](academic/2026-08-24-sharples-alexander-on-fate-pdf-audit.md) - Full-volume structure and reopened agent-causation debt
- [Sharples P0 Independent Review](academic/2026-08-24-alexander-sharples-global-p0-independent-review.md) - FAIL-NO APPLY on page maps, corpus transaction scope and postwrite robustness
- [Sharples P0 Independent Review v3](academic/2026-08-24-alexander-sharples-global-p0-independent-review-v3.md) - Final PASS on the post-Hildebrandt/Tatian transaction
- [Sharples Postwrite Test Review](academic/2026-08-24-alexander-sharples-postwrite-test-review.md) - Independent PASS on the composable postwrite harness
- [Glossary Entity Audit A–I](academic/2026-08-24-glossary-entities-a-i-audit.md) - Four revise, five block, zero approved; SEO publication manifest remains fail-closed
- [Glossary Entity Audit J–R](academic/2026-08-24-glossary-entities-j-r-audit.md) - One approved, six revise and two blocked definitions before repair
- [Glossary Entity Audit S–Z](academic/2026-08-24-glossary-entities-s-z-audit.md) - Six revise and three blocked definitions before repair
- [Glossary Publication Repair](academic/2026-08-24-glossary-publication-repair.md) - 27/27 independently reviewed definitions; adversarial SEO approval remains fail-closed

## Architecture Deep Dives

- [PageIndex V3](architecture/PAGEINDEX_V3.md) - GraphRAG pipeline specification
- [GraphRAG Convergence](architecture/graphrag-convergence.md) - Pipeline convergence analysis
- [GraphRAG Same-turn Tool Parallelism](operations/2026-08-24-graphrag-parallel-tool-batches.md) - Bounded concurrent I/O with deterministic evidence/trace commit order
- [Post-Sharples Retrieval Diagnostic](operations/2026-08-24-graphrag-offline-retrieval-post-sharples.md) - Separate work-identity leg, measured recall/F1 gains and explicit non-comparability
- [D3 Graph Engine](architecture/d3-graph/) - Graph visualization design decisions
- [KG Snapshot Release Contract](operations/kg-snapshot-release-contract.md) - Immutable pagination, permalink and deploy invariants
- [Workspace Code Splitting](../frontend/docs/workspace-code-splitting.md) - Atlas-only WebGL boundary and measured mode chunks
- [Atlas Multi-mode Browser QA](operations/2026-08-24-atlas-multimode-browser-qa.md) - Light Atlas, Chronos fact safety, console closure and 637 kB complete-release transfer gate
- [SEO/GEO Entity Release Contract](operations/2026-08-24-seo-geo-entity-release-contract.md) - Release-bound entity SSG, hydration-safe canonicals and real unknown-ID 404 boundary
- [Previous Integrity Proof](../data/audit/2026-08-24_integrity_suite_partial.json) - Historical 14/15 artifact, now stale after the current gate, loader and Atlas changes; do not use as RC proof
- [Post-Sharples Snapshot Ratchet](../data/audit/2026-08-24_snapshot_baseline_ratchet_post_sharples.json) - Frozen integrity debt reduced to 5,940 with zero new fingerprints
- [Reviewed Secondary Page Evidence](../database/README.md#reviewed-secondary-page-evidence) - Private page schema, ingestion and backfill policy

## The Three Packages

Each package can be installed independently:

```bash
pip install eleutheria-database   # Ancient texts corpus
pip install eleutheria-kg         # Knowledge graph framework
pip install eleutheria-graphrag   # Agentic RAG engine
```

See the [Architecture Overview](architecture/OVERVIEW.md) for how they work together.

## Documentation Structure

```
docs/
├── INDEX.md                   # This file
├── CHANGELOG.md               # Version history
├── codemeta.json              # CodeMeta scholarly metadata
├── guides/
│   └── QUICK_START.md         # Getting started
├── architecture/
│   ├── OVERVIEW.md            # System design
│   ├── PAGEINDEX_V3.md        # GraphRAG pipeline spec
│   ├── graphrag-convergence.md
│   └── d3-graph/              # Graph visualization decisions
├── reference/
│   ├── API.md                 # REST API docs
│   └── DATA_DICTIONARY.md     # Database schema
├── development/
│   ├── SETUP.md               # Dev environment
│   └── agents.md              # Browser automation
├── academic/
│   └── METHODOLOGY.md         # Research methodology
├── examples/
│   ├── curl/                  # cURL examples
│   └── python/                # Python examples
├── plans/                     # Design documents (internal)
├── reports/                   # Audit reports (internal)
└── assets/                    # Images, posters
```
