# Zero-debt checkpoint: parity, dialectical attestations, Plutarch identity

Date: 2026-08-18  
Status: applied, idempotent, strict gates green

## Before / after

| Debt class | Before | After |
|---|---:|---:|
| KG/corpus parity violations | 3,051 | **0** |
| Missing corpus twins | 78 | **0** |
| CTS-URN mismatches | 1,828 | **0** |
| Canonical-reference mismatches | 1,145 | **0** |
| Unattested rendered dialectical edges | 518 | **0** |
| Work/child canonical mismatches | 1 | **0** |

Final snapshot counts:

```text
KG nodes: 20,272
KG asserted edges: 49,841
KG works: 251
Corpus passages: 21,158
Corpus citations: 19,836
Exact declared/resolved twins: 10,780 / 10,780
```

## Parity repair

The global package resolved 3,045 violations across 2,084 KG nodes:

- 1,620 genuine twins synchronized from the corpus authority;
- 172 Philo corpus URNs reconciled to the manifest's `opp-grc1` witness;
- 292 false or stale `db_passage_id` declarations demoted to explicit
  non-identical relationships without changing ancient text;
- all 78 missing UUID declarations removed honestly;
- six source-specific Plutarch rows reserved for the separate adjudication.

The 289 useful non-identical relationships were subsequently retyped from
`snapshot_passage_node` to `related_passage_non_exact`. Exact passage and
translation endpoints reject them; GraphRAG keeps them textless and
discovery-only. Thus the zero count is also enforced semantically at runtime,
not only by removal of `db_passage_id`.

The Plutarch repair resolved those final six. The versioned parity baseline now
contains three empty lists. Full-graph parity runs in strict CI mode.

## Dialectical repair

All 518 historical unattested fault-line edges were reviewed individually:

- 189 retained with a specific existing page, primary locus, or verified
  endpoint attestation;
- 329 unsupported directed assertions deleted;
- zero `attested_by` values were invented from dates, weights, confidence
  scores, or generic bibliography.

R16 now has a dedicated `--strict-r16` whole-graph CI gate. It can fail
independently of unrelated historical ingestion-rule debt.

## Plutarch source adjudication

Local TLG E IDT/TXT evidence and pinned Perseus CTS/TEI files establish:

- `tlg0007.tlg135` = *Epitome libri de animae procreatione in Timaeo*,
  Moralia 1030d-1032f;
- `tlg0007.tlg138` = *De communibus notitiis adversus Stoicos*,
  Moralia 1058e-1086b.

The six `tlg135` passages were rehomed under a new work node, their KG/corpus
references and manifest title were corrected, and all fifty genuine `tlg138`
passages were left unchanged. The exact ambiguity allowlist entry was removed.

## Integrity guarantees

- ancient KG descriptions and corpus `text_content` were byte-preserved;
- citations were byte-preserved by the parity package;
- every applier was dry-run-first, preconditioned, backed up, and byte-level
  idempotent on its second application;
- corpus integrity, work-ID uniqueness, work/child canonical consistency,
  full strict parity, and strict R16 all pass;
- blocking SHACL conforms with zero violations;
- regression suites passed: 53 root integrity tests, 112 GraphRAG/dialectical
  tests, 11 staged-deploy/parity tests, and 100 focused related-link runtime
  tests;
- Greek provenance and citation-fabrication gates pass;
- the repairs are local and not yet deployed to production.

Detailed reports:

- `data/audit/2026-08-18_parity_zero.md`
- `data/audit/2026-08-18_dialectic_zero.md`
- `data/audit/2026-08-18_plutarch_split.md`
- `data/audit/2026-08-18_related_citation_types.md`
