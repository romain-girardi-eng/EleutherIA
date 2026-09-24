# Jev campaign, 2026-09-24 — common brief

Goal: while Jev is free on the Vercel AI Gateway (until 2026-09-25), collect as many useful,
reproducible CLOSED-QUESTION judgments on EleutherIA's data as possible. Judgments are
EVIDENCE for later human adjudication, never KG writes.

## Access (verified 2026-09-24, cost reported "0")
- Key: `set -a; . ~/.config/vercel-ai-gateway/env; set +a` → `$AI_GATEWAY_API_KEY`. Never print it.
- `POST https://ai-gateway.vercel.sh/v4/ai/evaluation-model`
  headers: `Authorization: Bearer $AI_GATEWAY_API_KEY`, `ai-model-id: typesafe-ai/jev`,
  `ai-evaluation-model-specification-version: 4`, `ai-gateway-auth-method: api-key`,
  `ai-gateway-protocol-version: 0.0.1`, `content-type: application/json`
  body: `{"state": <string|object>, "questions": {<id>: {"type":"boolean","instructions":"..."} | {"type":"choice","instructions":"...","options":[...]} | {"type":"score", ...}}}`
  (check the exact choice/score schema with one probe call first; see
  `graphrag/src/eleutheria_graphrag/services/jev_reranker.py` and
  `~/Projects/Veille/2026-09-17-jev-gold/` — `probe.py`, `run_gold.mjs`, `eleutheria-full/` — for working examples).
- Response: `answers.<id>.probability` (boolean) / distribution for choice/score,
  `providerMetadata.typesafe.confidence`, `providerMetadata.gateway.{cost,generationId,routing.canonicalSlug}`, `usage.inputTokens`.
- Limits: 64k tokens state+questions (Greek ≈ 1.4 tokens/char). Rate limits are dynamic:
  use a small async pool (the concurrency given in your task), exponential backoff on 429/5xx,
  and a resumable runner (skip ids already in results.jsonl). Python: `httpx` from the repo venv
  `.venv/bin/python` (or node fetch). Run long jobs in the background and poll.

## What Jev is good / bad at (measured 2026-09-17/18)
Good: closed factual questions over one text, many questions in parallel, calibrated
(≥0.9 → ~93 % right). Bad: arithmetic, counting, dates, multi-hop, broad multi-author questions,
very literal reading, texts that argue for their own classification. So: atomic, literal,
observable questions; one fact per question; no date questions.

## HARD RULES (EleutherIA)
- Do NOT modify `data/kg/*`, `data/corpus/*`, the DB or production. Write ONLY under your
  campaign directory `data/quality/jev_2026_09_24/<campaign>/`. Do not git commit.
- Never ask Jev (or yourself) to attribute doctrinal positions (libertarian, compatibilist,
  determinist…) — contested modern labels. Ask observable facts only.
- Never generate Ancient Greek/Latin. Passage text is sent verbatim from the corpus.
- Record for reproducibility: exact question texts (questions.json), candidate construction
  (build script), model slug + generationId per call, run date, errors.
- Large raw outputs: gzip them (`results.jsonl.gz`) if > 20 MB.

## Deliverables in your campaign dir
1. `build_*.py` / `run_*.py` (reproducible), `questions.json`, `candidates.jsonl`, `results.jsonl(.gz)`, `errors.jsonl`.
2. `REPORT.md` (French, Romain's voice, concise, NBSP typography): what was asked, coverage
   (N done / N planned, errors), cost, distribution of answers by confidence tier
   (≥0.9, 0.7–0.9, 0.3–0.7, ≤0.3), headline findings with 5–10 concrete verified examples
   (you read the text yourself for those), known limits.
3. Review queues as CSV sorted by expected value (e.g. `queue_contradictions.csv`,
   `queue_new_high_conf.csv`, `queue_uncertain.csv`) with node ids, labels, the question,
   probability and a short text excerpt — ready for item-by-item adjudication.
