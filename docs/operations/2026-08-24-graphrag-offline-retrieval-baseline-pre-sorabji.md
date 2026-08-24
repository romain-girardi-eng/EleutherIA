# GraphRAG offline retrieval diagnostic — PRE-SORABJI — 2026-08-24

Status: real, schema-validated diagnostic on snapshot
`2320758561d37eef9d556122c20adcd9b1a5b3e72bc58fe8c04b6edcb153975c`.
This is explicitly **PRE-SORABJI**: the pending Sorabji wave changes 11 KG
nodes and 2 edges, so these commands must be re-run afterward. This is not a
production baseline and not a SOTA claim.

No service, DB, model, key, paid call, generation or LLM judge was used.
Generation/citation/abstention/quote/publication/token/cost metrics remain
`null` / `not_run`, never zero.

## Binding

- git revision `c8bd221e098cbd8eb6cfef87ceeda82f1d5aeff5`; dirty worktree `true`;
- CPython 3.14.5 via `.venv/bin/python`;
- harness code SHA-256
  `439b06bf3f6076858a08605edf3482cfd53252a99e0ec7643a3962021c2cf94b`;
- snapshot files: passages
  `18e295d2c02e9f72f341d6d9a9f96a91249da7e602a64746ac4a80abd11ea935`,
  nodes `245b647974a994d0c053e6c14e1d66781f870ff1970d7d1cb7e1e0875f3f0af0`,
  edges `68044d12e6dd53fa602ab232e4b1dc9b4f97af7c47ea806c9e3730b00b8f9496`,
  citations `3fa555efad53ad2795f04fb28959442e42630b4f33187c1c7a1b78890af0d248`,
  manifest `56d925cdeb268b9e68521615ce328c8beddafeb8b0c6e63019359cc9b223efc0`.

## Critical gold finding

The legacy 45-query suite contains 29 invalid entity/work gold identifiers
across 20 queries. They are listed in
`tests/eval/legacy_gold_migration_queue.yaml`. Affected channel/query pairs are
`not_scored_invalid_gold`; they are not false misses. Metrics below are the
fully-valid-gold subset only. The run is **not release-comparable**, and the
deterministic comparator fails with `invalid gold identifiers`.

An earlier diagnostic incorrectly treated all repair cases as fully validated.
The bug was an existence check limited to passage/identity gold. It is fixed:
proof-backed repair cases now fail closed on entity, KG work, manifestation,
passage and identity. The Sextus person ID was corrected to
`person_sextus_empiricus_c160_210ce_d4f8a2b1`.

The Aristotle EN case is temporarily blocked in
`tests/eval/repair_gold_queue.yaml`: its exact English passage points to
`oga_tlg0086_tlg010_perseus_grc2_eng`, absent from the corpus manifest at this
snapshot. It must be re-admitted only after the manifest repair passes strict
validation.

## Legacy 45-query diagnostic (not comparable)

Query/gold SHA-256:
`f05b39ebf53f070749538614bfbe3b0724baa8841d2f749d29ca95d7f956db3f`.
All modes completed 45/45 without runner errors.

| Valid-gold metric | Lexical | PPR directed | PPR bidirectional |
| --- | ---: | ---: | ---: |
| Entity recall (25 scored) | 0.4193 | 0.6253 | 0.6000 |
| KG work recall (9 scored) | 0.6111 | 0.6111 | 0.5000 |
| Passage recall (13 scored) | 0.1795 | 0.1154 | 0.1346 |
| Complete-set recall (13 scored) | 0.0769 | 0.0769 | 0.0769 |
| Latency p50 | 21.698 ms | 60.001 ms | 604.064 ms |
| Latency p95 | 32.454 ms | 73.724 ms | 634.265 ms |
| Latency max | 110.879 ms | 155.076 ms | 765.782 ms |

PPR is not selected on entity recall. Both variants regress valid passage
recall; bidirectional also regresses valid KG-work recall. Directed PPR follows
source→target; bidirectional traversal reuses each asserted row in both
directions without creating an inverse relation.

Artifacts: lexical `eval-2026-08-24-9bb70fcdffe2` / SHA-256
`61709784b1a24c88f22d4e7c0bc637fa605f8128dec94c01f94f745bc06a8166`;
directed `eval-2026-08-24-d68efbbb5f33` /
`5d3a66de6f5b9cdbbe5106a97aea261a44e6ab7047ae13285d8525d6221df7ff`;
bidirectional `eval-2026-08-24-e58e9bde0d04` /
`543c6beffd5d76daf0a6d5d8c4320e67e1e1573dc04c05c9df24a46bb919305f`.

## Expanded 55-query diagnostic

The legacy 45 + four OOD + six strictly admitted repair cases use query/gold
SHA-256 `8476a1b32137b56970861d339d7595da5c81f189844bf5ad1423cf6482be7f38`.
The legacy invalid gold still makes this full run non-comparable.

- 55/55 completed, error rate 0;
- valid-subset entity recall 0.4511 (31 scored);
- valid-subset KG-work recall 0.7000 (15 scored);
- manifestation recall 0.1667 (6 scored);
- passage recall 0.1754 (19 scored);
- complete-evidence-set recall **0.1053** (19 scored): P0 blocker;
- zero forbidden passage-ID hits;
- latency p50/p95/max 21.258 / 33.209 / 111.842 ms;
- OOD abstention remains unscored/null: retrieval absence is never implicit
  abstention.

Artifact `eval-2026-08-24-42e21a339965`, SHA-256
`4cddc0daee098c7a71e6b6e1da1f65c5e6357e2ceb67939b4eced2f2d41aa300`.

## Strict repair-only diagnostic

The six admitted repair cases have zero invalid gold and are release-comparable
as a retrieval-only suite. Query/gold SHA-256
`79b3a04487310f64fa4086f96e2bb66c5402600f3cd80b32ccd6935e205ccdb9`.

- entity/work/manifestation/passage recall: 0.5833 / 0.8333 / 0.1667 / 0.1667;
- complete-evidence-set recall 0.1667 (6 scored), still a P0 gap;
- latency p50/p95 32.402 / 40.277 ms.

Artifact `eval-2026-08-24-20a462fd8cfd`, SHA-256
`646cdaeea8ac0269277b1771a7faab3402fa681218b29cec146d4ece966d93e8`.

## Exact commands

```bash
.venv/bin/python tests/eval/run_eval.py --runner snapshot-lexical \
  --output /tmp/pre-sorabji-v2b-45-lex.json
.venv/bin/python tests/eval/run_eval.py --runner snapshot-ppr-directed \
  --output /tmp/pre-sorabji-v2b-45-dir.json
.venv/bin/python tests/eval/run_eval.py --runner snapshot-ppr-bidirectional \
  --output /tmp/pre-sorabji-v2b-45-bi.json
.venv/bin/python tests/eval/run_eval.py --compare \
  /tmp/pre-sorabji-v2b-45-lex.json /tmp/pre-sorabji-v2b-45-bi.json
.venv/bin/python tests/eval/run_eval.py --runner snapshot-lexical \
  --include-ood --include-repair-wave \
  --output /tmp/pre-sorabji-v2b-55-lex.json
.venv/bin/python tests/eval/run_eval.py --runner snapshot-lexical \
  --queries tests/eval/repair_wave_2026_08_24.yaml \
  --output /tmp/pre-sorabji-v2b-repair6-lex.json
PYTHONPATH=graphrag/src .venv/bin/python -m pytest -q \
  tests/eval -m 'not eval'
```

After Sorabji and the English Aristotle manifest repair, re-run. Snapshot,
query, code and artifact hashes must be reviewed anew.
