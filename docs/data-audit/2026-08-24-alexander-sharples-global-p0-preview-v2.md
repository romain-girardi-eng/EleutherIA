# Alexander / Sharples global P0 preview v2

Date: 2026-08-24  
Mode: dry-run only; **no data write**.  
Status: `ready_for_independent_review_no_apply`.

This v2 responds to the independent `FAIL - NO APPLY` report
`docs/academic/2026-08-24-alexander-sharples-global-p0-independent-review.md`,
SHA-256
`44d55137e40aafc86ba7f0007313a1b049e9d2005cd1167727d423bc76296858`.
It does not supersede that verdict; a fresh independent review is required.

## Frozen v2 tuple

| Artifact | SHA-256 |
|---|---|
| applier | `9a611ddecfb1c2e31782954c1174bd3b40e752ac124553bc5607269270f961e5` |
| targeted tests | `14a3d460063b4bab425f8aecc62ebb3e63f1e123b0e8b6ed8d8f08bd30e9eab1` |
| corrected scholarly audit | `7c1fbfcbabb5904c0a35818c5927c8f92913b05feaaf75fe19bbd9ad415efce0` |
| dry-run JSON | `07b37b03d10dca1b1b75e7f3312860b98f70ffe51978ed5aaaef0d21a34b1cae` |

The dry-run JSON is
`/tmp/2026-08-24-alexander-sharples-global-p0-v2-preview.json`.

## Frozen Snapshot-A

The entire twelve-file before state is hash-gated. Corpus passages and corpus
manifest are read-only transaction dependencies: they are included in
Snapshot-A and both pre-stage/pre-commit gates, but are never outputs.

| Surface | Before SHA-256 |
|---|---|
| `data/kg/nodes.jsonl` | `57fb90da476ebdf98bc59f4a0cb4bad0c4871d5d829c0dc05063b4752b6c8664` |
| `data/kg/edges.jsonl` | `22efd267ac194d67d23ffd9985d2c68d93e1cfb4129e1a91cc3fda4871fadd70` |
| `data/corpus/citations.jsonl` | `3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248` |
| `data/corpus/passages.jsonl` | `4e2e7b8789de06f3b3cf897c3f9b6d63bc92db5ee24657dabee6c9ba510f51ec` |
| `data/corpus/manifest.jsonl` | `aa4d446f32b5d47d4fb3d002dec3b49398862f8f3f8515b6076655ea8e414cd6` |
| `data/kg/publications.bib` | `2bf6ea54d93bb86249997a076e73dde025b8e765e1edcab59f641ad77c5f4dcc` |
| `data/kg/publications_bibtex_report.json` | `66355e056418b9c446a278e9d29b0119d60628504f73bc10af08d73d155b6f72` |
| `data/scholarly_sources/manifest.jsonl` | `e326abbe07e78f6c8ca873e1ef99ab5ca77e64066a838bcf93ff360e466bcbe5` |
| registry sources | `ceba6d9e9ec188d943abdd345f0149dca017b70a82404f7d858774f812bcd650` |
| registry evidence | `41683cdb6df1b826dbc625853c08a3fcd66c0579a7ca96883c5e326ecd82cbe7` |
| registry issues | `1aa809df5ebfc5f81d31963ce84fa37ab7563a4d61d9007fc7009399819a130a` |
| dedicated wave | absent |

Other pinned inputs:

- Sharples scan:
  `7d42b5aba139136d8e32c12ab1c9946471066f95b05a5ce5357a420150810638`;
- OCR derivative:
  `ec154e4d3607f887299ac3faf6ec1853b0a4da117eaa464d70331d7c55727ebb`;
- Bruns/OGL TEI:
  `184b01f38061cfa00b276ed8d9580f3f842f564856851e4bcc124adcc2edbb2f`.

The scan has 161 PDF spreads/pages and remains an internal,
all-rights-reserved verification artifact. OCR is navigation-only.

## Corrected page maps

All fourteen evidence intervals and all twenty-four argument intervals are now
derived and checked from the verified rule
`PDF = floor(printed / 2) + 5`.

| Record | Printed | Correct PDF |
|---|---:|---:|
| SHA-01 | 19-21 | 14-15 |
| SHA-06 | 146-149 | 78-79 |
| SHA-09 | 146-149 | 78-79 |
| SHA-12 | 152-153 | 81 |
| `argument_deliberation_alex` translation layer | 56-60 | 33-35 |

The audit table, `ARGUMENT_SPECS`, `EVIDENCE_SPECS`, node after-hash and
registry evidence output were recalculated together. A generic test derives
every interval; it does not compare duplicated hand-entered constants.

## Exact bounded semantic delta

The semantic scope remains the reviewed v1 scope:

- exactly 15 nodes modified;
- 55 strong grounding edges removed and 1 publication/work edge corrected;
- 31 citations downgraded to `related_passage_non_exact`;
- 2 false exact snapshots removed;
- 1 scholarly manifestation added;
- 1 ancient source corrected and 1 secondary Sharples source added;
- 14 secondary evidence atoms added, all `in_review` and paraphrase-only;
- 2 issues added OPEN and one blocked wave added;
- 1 BibTeX entry and its companion report changed atomically;
- 126 quarantine records.

`argument_agent_causation_alex` and all six Long/Sorabji overlap nodes remain
byte-identical. Strong duplicates remain `discoverable_only`; direct Alexander
candidate loci, reported Stoic positions, Sharples taxonomy and modern
reconstruction remain separately typed. No uncaused or ultimate
substance-agent is asserted as direct Alexander text.

The publication remains a Duckworth 1983 translation/commentary with a
photographic Bruns facsimile and textual notes, not a newly constituted critical
edition. Scan/OCR and Bruns/OGL remain distinct manifestations.

## Corpus and transaction gates

Every dry-run and postwrite `build_plan()` now executes:

- corpus invariant no-growth;
- snapshot-integrity no-new-fingerprint;
- locus parity;
- work-child canonical consistency;
- work-ID uniqueness;
- strict-ingestion debt delta;
- structural registry audit.

The prospective result reports zero new corpus violations, zero new snapshot
fingerprints, zero parity violations, zero work-child mismatches and zero work-ID
collisions. It checks 13,841 shared parity records.

The transaction now protects read-only corpus dependencies at pre-stage and
pre-commit. It also checks each target immediately before replacement. Rollback
first classifies every target as before/after/foreign; foreign bytes are never
overwritten, and journal/backups remain durable for explicit recovery.

Tests cover:

- read-only corpus drift before commit;
- inter-window target drift after an earlier replacement;
- hard-crash recovery;
- replace/fsync and rollback failure;
- durable second recovery;
- first write, postwrite idempotence and repeated write on a full shadow copy.

The CLI contract is now consistent: dry-run is default; `--write` is available
for a reviewed local transaction; repository-root mutation additionally requires
`--production-write-approved`. This tuple has not been approved or applied.

## Preview output hashes

| Output path | SHA-256 preview |
|---|---|
| `data/kg/nodes.jsonl` | `d6eaf3a0384b9870f3f3366f9b550d9e28f0c6865a57f514078663f3b0b5c5fc` |
| `data/kg/edges.jsonl` | `e614d6151a59e9db1cbeca19bb88e05169640d0d3be83b36867dbc896d706205` |
| `data/corpus/citations.jsonl` | `38c1a647bb37bedc74e52f930efec76faf764eca32a999613d3277624d3ade93` |
| `data/kg/publications.bib` | `2c30e5b067936fedc814fc0e1e6ea46f29807d68ede0f95e9a2740bc92fb58b6` |
| `data/kg/publications_bibtex_report.json` | `b24d34a99e42b1afa68807079d9974221fc4d603d57acd17a936e7ca93b2b0cd` |
| `data/scholarly_sources/manifest.jsonl` | `0c7efe6cafa045fe625b0957c19f1535a35d25fda4223595d462103769432e09` |
| registry sources | `77605ecaad1d0658094ace1f2d7276b30ca9523230158c091d3d8c0d361df3c2` |
| registry evidence | `7ed1b60f6f150e96c295ec8ba1e65c050ba938bf0efc1369660e5058cf3c4777` |
| registry issues | `fda16eebbd848739bc0da96cc9dc4c00d1674eb221707a921a1f7b25e7a52545` |
| blocked wave | `76d3182a9c027e6272e46d6ed9a8c3a1b235e688963e4c05f38c0479ff264405` |

The read-only corpus dependency hashes are unchanged in both before and after
states. The frozen after state covers all twelve files, not only changed paths.

## Verification results

- targeted v2 suite: **25 PASS**;
- local Alexander 12/20 plus Long/Sedley regressions: **28 PASS**;
- corpus/snapshot/parity/work/registry global gates: **36 PASS**;
- ruff: **PASS**;
- exact touched-set and raw-line preservation: **PASS**;
- normative Draft7 registry delta: 41 inherited before, 41 after, zero new;
- strict ingestion debt: 1155 BLOCK / 768 WARN before, 1154 / 767 after;
- no independent, adversarial or human PASS added.

This preview is ready only for a new independent/adversarial review. No data
write or deployment is authorized or performed.
