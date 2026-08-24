# Alexander / Sharples global P0 preview v3 final rebase

Date: 2026-08-24  
Mode: dry-run only; **no data write**.  
Status: `ready_for_independent_review_no_apply`.

This v3 rebases the semantically approved Sharples v2 delta on the live
post-Hildebrandt and post-Tatian base. It does not add or reinterpret a scholarly
claim. The former independent reviewer is no longer available; this tuple is
ready for a root reviewer or another available independent agent.

## Frozen tuple

| Artifact | SHA-256 |
|---|---|
| applier | `1e740dbbec59ccac951468ecee6ec6f7016ea57e72c3c6e71fc96f48780ba6dd` |
| targeted tests | `daa919764e6cd0bd65c40e4a71e84f20734ddc84ec7b6b2899fd5877781be31d` |
| corrected scholarly audit | `7c1fbfcbabb5904c0a35818c5927c8f92913b05feaaf75fe19bbd9ad415efce0` |
| independent v2 semantic review | `1dada7cdccd0f4384c21d33dd7cb24969cb9781507d6355aebe448281b1c7f25` |
| dry-run JSON v3 | `a503f6a0f7393875d49cafdc2a1faa3dedf387d3697463ce7faac74e5ee7b317` |

JSON path:
`/tmp/2026-08-24-alexander-sharples-global-p0-v3-preview.json`.

The independent v2 report signed:

- semantic verdict: PASS;
- transaction verdict: PASS on its reviewed base;
- application verdict then: base stale pending this rebase.

## Post-Hildebrandt + Tatian Snapshot-A

All twelve surfaces are frozen. Corpus passages and corpus manifest are
read-only dependencies included in pre-stage and pre-commit gates, not outputs.

| Surface | Before SHA-256 |
|---|---|
| `data/kg/nodes.jsonl` | `60082c52cddfa3e5441a2ae491af2d9c00c386f4f9ed8a8c4b836390a4e24f83` |
| `data/kg/edges.jsonl` | `2e417ac429988f1df282fbb0576f34b51e327479d0043738b9cf073715de6b72` |
| `data/corpus/citations.jsonl` | `3aea9ad22b6fe42c78429ce68fbb041c57d532e530463a01b18353d7c11a9c64` |
| `data/corpus/passages.jsonl` | `e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3` |
| `data/corpus/manifest.jsonl` | `2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e` |
| `data/kg/publications.bib` | `e4cc9a15bdbe756446518a09f9a97f9405c98a7b54886de39afc07892941c44a` |
| `data/kg/publications_bibtex_report.json` | `7612db557443d1c6c27507a130aa283a115e8a765075b297a7c019ef6104b68a` |
| `data/scholarly_sources/manifest.jsonl` | `33f304aee1a3882c75f47e212bae778e64c23da6cb9f39cda0790416f0c9e9b6` |
| registry sources | `cc34488366f86d56726e99c1113195f2e8c128f2f44f2b1535d0dabdcd8cf7ac` |
| registry evidence | `90aaa8fab0d4c5fbbb830b60f38d992514b6d5a512a0698397042cc090aa2307` |
| registry issues | `5dca524033ebe628d5d9cd3431ebeddd9e8830314e430440d057a22e73d8ef17` |
| dedicated Sharples wave | absent |

The following durable base artifacts are hash-gated and excluded from outputs:

```text
Hildebrandt report      cb30674aff6f4a6012cbb4a6266b9d1b49138da615c14147837f29820dfec59c
Hildebrandt quarantine  3f35c44a02a000db342097a274e50a0398b822c363fb13c59ce0a03a1cbb7714
Tatian report            b832d77849e1de9a767457afd1cb773609adf58a3d0165d47a9489743f9ee98c
Tatian quarantine        906013db5a2201252e67e2ff5b13ca88af1419c21c970a1cdddb9c5ad89963c7
```

## Rebase proof: semantic v2 delta unchanged

Direct v2/v3 preview comparison gives:

```text
counts                         equal
touched_node_ids               equal
touched_edge_ids               equal
touched_citation_keys          equal
after_record_hashes            equal
page_map_validation            equal
changed_paths                  equal
open_issue_ids / reviews       equal
quarantine count               126 / 126
```

The fifteen touched nodes have exactly their v2 before-hashes on the live base.
The old edge cohort still contains 56 records with digest
`ef35bc8267196b2edc20b683c243a4732b516fe2e08b8d4f0f5cc39c92af4d3b`.
The old citation cohort still contains 33 records with digest
`68f2d38c8762209531165fa77f670aa3e41eb3082201945e0000ac9c5846f2d0`.
The ancient source record retains canonical before-hash
`5f2fd3b1e2615334f666d315737efad1f3ce1eab409d31ab69808489a3954cd5`.

Therefore Hildebrandt and Tatian changed only out-of-cohort bytes and global
files. Serialization preserves every such line byte-for-byte.

## Semantic scope retained

- exactly 15 nodes modified;
- 11 strong reconstructions remain `discoverable_only`;
- 55 strong grounding edges removed and 1 publication/work edge corrected;
- 31 citations downgraded to `related_passage_non_exact`;
- 2 false exact snapshots removed;
- Sharples remains a Duckworth 1983 translation/commentary with photographic
  Bruns facsimile, not a newly constituted critical edition;
- ancient Bruns/OGL and secondary Sharples manifestations remain separate;
- 14 evidence records stay paraphrase-only and `in_review`;
- 2 issues remain OPEN and one dedicated wave remains blocked;
- no independent, adversarial or human PASS is added to registry data.

`argument_agent_causation_alex` and all six Long/Sorabji overlap nodes remain
byte-identical to the live post-Tatian base. No uncaused ultimate
substance-agent is asserted as direct Alexander text.

## Page maps unchanged

The generic scan-spread rule still checks 14 evidence intervals and 24 argument
intervals:

```text
PDF = floor(printed / 2) + 5
```

Priority corrections retained:

| Record | Printed | PDF |
|---|---:|---:|
| SHA-01 | 19-21 | 14-15 |
| SHA-06 | 146-149 | 78-79 |
| SHA-09 | 146-149 | 78-79 |
| SHA-12 | 152-153 | 81 |
| deliberation translation layer | 56-60 | 33-35 |

## Prospective outputs

| Output path | SHA-256 |
|---|---|
| `data/kg/nodes.jsonl` | `92a0cd13dcab0d1749119e8ef0b772392e7920177096213deca2906e88821817` |
| `data/kg/edges.jsonl` | `b1ce4f5e594d846c0d64ad1a33b4e0b0970230c11641010df8ea9b58e8ebfd2a` |
| `data/corpus/citations.jsonl` | `5bd6657adb6aa006bc12a33285c399e00fc7ab467932b603369e119bdc9e089a` |
| `data/kg/publications.bib` | `3e21f88fe06e9e61d7444f724d66a1eabdadd2af27ec42dca22bd8651e94b825` |
| `data/kg/publications_bibtex_report.json` | `bba25a9d4d57dd9f82fe1eeb4b410f262312050345fb27fc9fb4b7cce2478e69` |
| `data/scholarly_sources/manifest.jsonl` | `c16553ff02c6cfdcd8402551bcd128fcf8cf0f6d5855a7b38d0be670fbe2a42e` |
| registry sources | `511a4550dd3d61c36e5fa2b85fb0e0ad66f055141ba5ee4829256b62ea2e7d46` |
| registry evidence | `165e13fb58e951c76b2efbdcfa17c1938166677af8f60b1d8e2fa5390d84c23c` |
| registry issues | `188a746de924bf4086ecf66bbd812a332095e7c03e4b6f4d7b72034a93c0c509` |
| dedicated wave | `76d3182a9c027e6272e46d6ed9a8c3a1b235e688963e4c05f38c0479ff264405` |

Read-only after hashes remain:

```text
corpus passages  e8e79f62fb27198f3bfa93755a9f0615ad79e67037eaedd0d61fed5453f176f3
corpus manifest  2e2bf033c11ae48af93902be02816a86de9d4c8422cd6800c6f388cab8f5026e
```

Prospective first-write audit artifacts:

```text
repair report  98b9b76ebe1a6f2f608ef52cdc6f7b0d7c96bfb675a0087656859fbba2a6733b
quarantine     bc6fa40a1cd461dfe13550d26a03d750aa42c41233c316af608fa3c0ff7d8d63
records        126
```

## Gates and transaction

The current preview reports:

```text
new snapshot fingerprints  0
new corpus violations      0
parity shared checked      13844
parity violations          0
work-child mismatches      0
work-ID collisions         0
strict debt before         1152 BLOCK / 760 WARN
strict debt after          1151 BLOCK / 759 WARN
new strict debt            0
normative registry         41 inherited / 0 new
```

The twelve-surface transaction remains unchanged: dual Snapshot-A gates,
per-target before gate, durable stages/backups/journal, foreign-byte preflight,
rollback and hard-crash recovery. A full shadow apply reaches the frozen after
state, reruns postwrite integrity gates, then returns `already_applied` on
repeat.

## Verification run

```text
tests/test_alexander_sharples_global_p0.py  25 passed
global corpus/snapshot/parity/work/registry suite  36 passed
ruff  PASS
```

The local exact Alexander 12/20 suite passes its seven tests. The old
Long-Sedley postwrite suite is itself stale after later Hildebrandt/Tatian
changes: its reconstruction expects pre-later-wave edge and BibTeX hashes and
fails before exercising Sharples. This is an external test-harness debt, not an
accepted regression or a reason to weaken any Sharples gate.

## Handoff

This tuple is ready for a final hash-bounded review by root or another available
independent agent. It is **not authorized for apply** by this preview. No data
write or deployment was performed.
