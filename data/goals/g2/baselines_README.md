# G2 — Retrieval Baselines (3-way comparison)

Two reference baselines that speak the **same POST contract** the eval harness
(`tests/eval/run_eval.py`) uses, so the agentic GraphRAG backend can be compared
against a pure-retrieval floor and a vanilla-RAG floor on the **same gold set**.

The harness POSTs `{"question", "stream": false}` to `/api/graphrag/query` and
reads `answer` + `citations[]`. Citation P/R/F1 is scored against
`expected_passages`; with `ELEUTHERIA_EVAL_JUDGE=1` it also fetches each cited
passage via `GET /api/passages/{id}` and judges `gold_claims` with
CitationVerifierV2. Both baselines implement **both** endpoints.

Code: `scripts/goals/g2_baselines/`
- `corpus_index.py` — loads `data/corpus/passages.jsonl`; dependency-free Okapi
  BM25 (no `rank_bm25`), Unicode + accent-folded tokeniser (Greek-aware).
- `bm25_service.py` — **Baseline 1**: BM25/FTS-only, thin template answer, **no LLM**.
- `vanilla_rag_service.py` — **Baseline 2**: top-k FTS context → one LLM call, no agent/KG.
- `providers.py` — pluggable LLM providers; default `extractive` needs **no API key**.

Every citation carries a **real `passage_id`** from the corpus, so citation
scoring and the faithfulness judge work identically to the production backend.

## Gold set

`data/goals/g2/` already holds the gold annotations the harness consumes:
- `gold_thesis_1.yaml` — r001–r008 (`expected_passages` + `gold_claims`)
- `gold_thesis_2_last7.yaml` — r009–r015
- `gold_hard.yaml` — the 8 hard q0xx queries

Pass any of these to `--queries`. (Queries with documented coverage gaps carry no
`expected_passages` and are simply not citation-scored.)

## Provider selection (Baseline 2)

`G2_LLM_PROVIDER` (default `extractive`):

| value        | key env var          | notes                                         |
|--------------|----------------------|-----------------------------------------------|
| `extractive` | none                 | no LLM; echoes retrieved context (key-free)   |
| `openai`     | `G2_OPENAI_API_KEY`  | any OpenAI-compatible endpoint (`G2_OPENAI_BASE_URL`, `G2_OPENAI_MODEL`) |
| `openrouter` | `OPENROUTER_API_KEY` | `G2_OPENAI_MODEL` (e.g. `openai/gpt-4o-mini`)  |
| `moonshot`   | `MOONSHOT_API_KEY`   | Kimi (`G2_OPENAI_MODEL`, e.g. `kimi-k2-thinking`) |
| `gemini`     | `GEMINI_API_KEY`     | `G2_OPENAI_MODEL` (e.g. `gemini-2.5-flash`)    |

Other env: `G2_TOP_K` (default 8), `G2_LLM_TIMEOUT` (default 120s).

## Run the 3-way comparison

All commands run from the repo root with the root venv (`.venv`, which has
fastapi / uvicorn / httpx). Use one gold file consistently as `$GOLD`.

```bash
GOLD=data/goals/g2/gold_thesis_1.yaml

# --- Baseline 1: BM25 / FTS-only (port 8011) ---
.venv/bin/python -m uvicorn scripts.goals.g2_baselines.bm25_service:app --port 8011 &
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8011 \
    --queries "$GOLD" --output data/goals/g2/run_bm25.json

# --- Baseline 2: vanilla LLM + FTS RAG (port 8012) ---
# key-free smoke test:
G2_LLM_PROVIDER=extractive \
.venv/bin/python -m uvicorn scripts.goals.g2_baselines.vanilla_rag_service:app --port 8012 &
# OR a real model, e.g.:
# G2_LLM_PROVIDER=openrouter OPENROUTER_API_KEY=sk-... G2_OPENAI_MODEL=openai/gpt-4o-mini \
# .venv/bin/python -m uvicorn scripts.goals.g2_baselines.vanilla_rag_service:app --port 8012 &
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8012 \
    --queries "$GOLD" --output data/goals/g2/run_vanilla.json

# --- System under test: agentic GraphRAG backend (the real EleutherIA API) ---
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8000 \
    --queries "$GOLD" --output data/goals/g2/run_graphrag.json
```

To run the faithfulness judge on any of the three, prefix with
`ELEUTHERIA_EVAL_JUDGE=1` and provide an LLM key (see `run_eval.py` header).

### Compare runs pairwise

`run_eval.py --compare` takes exactly two JSON files:

```bash
.venv/bin/python tests/eval/run_eval.py --compare \
    data/goals/g2/run_bm25.json data/goals/g2/run_graphrag.json

.venv/bin/python tests/eval/run_eval.py --compare \
    data/goals/g2/run_vanilla.json data/goals/g2/run_graphrag.json
```

The delta tables surface `citation_f1_mean`, `citation_count_mean`,
`forbidden_hits_total`, latency, and per-query-type recall/precision — the
metrics that separate true retrieval/grounding quality from the floors.

## Reading the numbers

- **Entity recall / precision / keyword / work recall** measure KG-*node* surfacing.
  Both baselines are passage-only and **score ~0** on these by design — that gap
  is itself the value of the comparison (it shows what the KG layer buys).
- **Citation F1 (gold)** and the **judge `verified_rate`** are the apples-to-apples
  metrics: all three systems cite real `passage_id`s and are scored identically.
- BM25-only is a *lexical* floor: on scholarly **English** questions over a
  **Greek/Latin** corpus it often misses the original-language gold passages —
  expected, and exactly the weakness the agentic pipeline (lemma expansion + KG)
  is meant to overcome.
