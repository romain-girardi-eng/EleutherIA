# GraphRAG evaluation runbook (schema v2)

This runbook produces auditable measurements. It does not certify that
EleutherIA is state of the art.

## What changed from schema v1

The old harness mixed context nodes, answer citations, sources and evidence-map
keys into one “returned entities” set. It also recorded failed HTTP requests at
zero milliseconds, discarded the HTTP body/trace, and averaged safety-critical
dimensions into ordinary quality summaries. A run could therefore be both
unreproducible and deceptively clean.

Schema v2 makes these distinctions explicit:

- retrieval nodes, KG work nodes, corpus manifestations and passage UUIDs are
  separate channels;
- citations belong to generation and are never used as a proxy for retrieval;
- unobserved channels are `null` / `not_run`, not an empty list and not zero;
- complete-evidence-set recall requires every passage in each conjunctive gold
  group;
- every query retains its raw trace and its individual gate failures;
- identity, quote fidelity, publication safety and forbidden strings each have
  their own observed count, failures and failed-query list;
- latency, tokens and cost are separately nullable and include an observation
  count;
- no composite score is emitted.

## Artifact binding

Every valid run records:

- `release_id`, `runner_id`, exact `model_id` (or explicit null for retrieval
  only), `config_id` and `config_sha256`;
- `query_sha256`, computed over the selected questions and all gold fields;
- git revision, dirty-worktree flag and `code_sha256` over the harness,
  scorer, schema, gates and offline runner;
- Python version and implementation;
- individual SHA-256 values for `passages.jsonl`, `nodes.jsonl`, `edges.jsonl`,
  `citations.jsonl`, and `manifest.jsonl`, plus a combined snapshot digest.

A dirty-worktree artifact is a valid diagnostic bound to exact bytes, but it is
not a release baseline until those bytes are frozen and reviewed.

## 1. Validate gold before running

The runner fails closed if an expected passage UUID is absent or if a supplied
identity field (`work_canonical_id`, canonical reference, language, CTS URN)
does not match the bound corpus row.

The ordinary 46 cases live in `tests/eval/queries.yaml`; `r016` (Origen,
*De Principiis* III.1, Bobzien/Frede on Stoic-Origenian continuity) is the
reference benchmark question named in `data/eval/baselines/README.md`.
Optional strata are:

- `tests/eval/ood_queries.yaml`: four out-of-domain/unanswerable cases;
- `tests/eval/repair_wave_2026_08_24.yaml`: six strictly admitted exact-ID cases
  for Alexander, Pseudo-Plutarch, Calcidius, Irenaeus, Origen Exhortatio, and
  Sextus;
- `tests/eval/repair_gold_queue.yaml`: claims deliberately excluded because
  their evidence/review is not yet sufficient, including Aristotle EN until
  its English manifestation exists in the corpus manifest;
- `tests/eval/legacy_gold_migration_queue.yaml`: 29 stale/misfiled legacy
  entity/work identifiers that block release comparison.

Load the optional suites with `--include-ood` and `--include-repair-wave`.

## 2. Run the key-free snapshot baselines

Lexical/BM25:

```bash
python tests/eval/run_eval.py \
  --runner snapshot-lexical \
  --include-ood \
  --include-repair-wave \
  --output /tmp/eval-v2-lexical.json
```

PPR has two explicit adjacency policies:

```bash
python tests/eval/run_eval.py \
  --runner snapshot-ppr-directed \
  --output /tmp/eval-v2-ppr-directed.json

python tests/eval/run_eval.py \
  --runner snapshot-ppr-bidirectional \
  --output /tmp/eval-v2-ppr-bidirectional.json
```

Both use only rows in `data/kg/edges.jsonl` that are not explicitly marked
inferred/derived. Directed PPR follows source→target. Bidirectional PPR adds
traversal access target→source over the same asserted row so incoming evidence
can be reached; it does not create, label or emit an inverse relation. No
transitive or ontology inverse edge is synthesized. The per-query trace records
the mode and asserted/excluded edge counts.

The offline runner scores retrieval only. An empty OOD retrieval is not an
abstention success. Abstention is scored only from an explicit structured
`abstained` or `insufficient_evidence` boolean in a generation payload.

## 3. Capture a live release

Do not point this command at production casually: it executes the real query
pipeline and may incur provider cost. Freeze and record the backend release,
model and configuration first.

```bash
python tests/eval/run_eval.py \
  --runner live-http \
  --base-url http://localhost:8000 \
  --release-id <release-or-image-digest> \
  --model-id <provider/model-version> \
  --config-id <immutable-config-id> \
  --mode fast \
  --include-ood \
  --include-repair-wave \
  --output /tmp/eval-v2-live.json
```

`release-id`, `model-id`, and `config-id` are mandatory. HTTP 4xx/5xx captures
retain status and body and use the measured elapsed time. Retrieval latency and
generation latency remain null unless the response exposes those exact stage
fields; total HTTP latency remains observed. Token and cost fields likewise
remain null unless emitted by the backend.

Raw response headers are allowlisted to avoid persisting cookies or
credentials. Request authorization headers are never written.

## 4. Validate and compare

```bash
python tests/eval/run_eval.py --validate /tmp/eval-v2-live.json
python tests/eval/run_eval.py --compare \
  /tmp/eval-v2-lexical.json /tmp/eval-v2-live.json
```

The comparator first requires identical query/gold digest and case order. Its
release result is the logical conjunction of named decisions, not a weighted
average. A candidate fails for a critical safety failure even if retrieval
improves elsewhere. A generation-enabled run additionally fails coverage when
successful answers do not expose quote-fidelity and publication-gate verdicts.
Any invalid gold makes the artifacts non-comparable. Affected channels are
reported as `not_scored_invalid_gold`; valid-subset metrics remain separate and
cannot turn the release gate green.

Review before publishing:

1. `summary.counts.failed_queries` and every per-query `error`/`raw_trace`;
2. per-query `gate_failures`, not just means;
3. passage and complete-evidence-set regressions;
4. KG `work` versus corpus `manifestation` channels (never merge them);
5. source-identity, quote, publication and forbidden-string observed coverage;
6. latency p50/p95/max by stage and mode;
7. token/cost observation counts and nulls;
8. binding hashes and `workspace_dirty`.

## 5. Publish without rewriting history

Never modify `data/eval/EVAL_REPORT_2026-05-15.md` or its 0/10 schema-v1 JSON.
Write a separately dated schema-v2 artifact under `data/eval/baselines/` only
after validation and review. Use a name that identifies the runner/release,
for example `eval-v2-2026-08-24-snapshot-lexical.json`.

Committed answer-bearing artifacts remain subject to
`tests/eval/test_must_not_appear.py`.
