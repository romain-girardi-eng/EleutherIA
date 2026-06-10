# GraphRAG Eval Baselines

Run documents captured by the online eval harness (`tests/eval/run_eval.py`).
This is the **manual / nightly** half of the eval gate — it needs a running
backend and is never executed in CI. The offline half (citation P/R scorer,
quote-gate adversarial suite, must-not-appear scans) runs on every PR via
`pytest tests/eval`.

## Workflow

1. **Capture a baseline** against a healthy backend:

   ```bash
   python tests/eval/run_eval.py \
       --base-url http://localhost:8000 \
       --output data/eval/baselines/baseline-$(date +%Y-%m-%d)-<label>.json
   ```

   Name files `baseline-YYYY-MM-DD-<label>.json` where `<label>` identifies
   the pipeline variant (e.g. `prod`, `vectorless`, `kimi-fallback`).

2. **Compare a candidate run** against the last committed baseline:

   ```bash
   python tests/eval/run_eval.py --compare \
       data/eval/baselines/baseline-<old>.json \
       data/eval/baselines/baseline-<new>.json
   ```

3. **Commit the run document** once reviewed. Committed baselines are scanned
   by `tests/eval/test_must_not_appear.py` on every PR: any answer text they
   contain must be free of audit-confirmed fabricated ancient strings.

## Gold annotations

Per-query gold lives in `tests/eval/queries.yaml`:

- `expected_passages` — passage ids a correct answer must cite. Scored as
  citation precision/recall/F1 (`tests/eval/eval_lib/scoring.py`) and reported
  in the run document as `citation_precision` / `citation_recall` /
  `citation_f1` plus the `citation_f1_mean` aggregate.
- `gold_claims` — atomic claims the answer must support. Judged adversarially
  by `CitationVerifierV2` when `ELEUTHERIA_EVAL_JUDGE=1` is set (requires an
  LLM API key); verdicts land in the per-query `judge` block.

Annotation is manual and item-by-item (per the no-bulk-edit policy). The
machine-derived fixture `data/eval/citation_gold.jsonl` (built from the audit
corpus by `scripts/eval/build_gold_from_audit.py`) is the source to draw from
when annotating: its `wrong_passage_id` values are citations the audit
rejected, its `right_passage_id` values are verified repointings.

## Fabrication scan

Every answer captured by `run_eval.py` is scanned against
`data/eval/must_not_appear.jsonl` (audit-confirmed fabricated Greek). Hits are
recorded per query (`forbidden_hits`) and aggregated
(`forbidden_hits_total`) — any non-zero value is a release blocker.
