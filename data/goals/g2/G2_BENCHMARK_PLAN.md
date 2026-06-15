# G2 — Benchmark Plan: gold merge, judged eval, 3-way comparison, CI regression gate

This plan turns the freshly annotated gold (`data/goals/g2/gold_*.yaml`) into a
repeatable benchmark: it (1) merges the annotations into `tests/eval/queries.yaml`,
(2) runs `run_eval.py` with `ELEUTHERIA_EVAL_JUDGE=1` to produce **citation-F1** +
**faithfulness verified-rate**, (3) compares the agentic GraphRAG backend against
the BM25 and vanilla-RAG floors, and (4) proposes a CI regression gate.

The harness is already wired for all of this: `load_queries()` reads
`expected_passages` (→ citation P/R/F1 via `eval_lib/scoring.py`) and `gold_claims`
(→ adversarial judge via `CitationVerifierV2`, gated by `ELEUTHERIA_EVAL_JUDGE`).
The only missing piece is moving the gold fields from `data/goals/g2/` into the
query set the harness loads.

---

## 0. What exists today

| File | IDs | `expected_passages` | `gold_claims` | Notes |
|------|-----|--------------------|---------------|-------|
| `gold_thesis_1.yaml` | r001–r008 (r004/r006 = coverage gaps) | 15 | 19 (bare strings) | correct schema |
| `gold_thesis_2_last7.yaml` | r009–r015 | 18 | uses `- claim: "..."` dict form | **schema mismatch, see §1.2** |
| `gold_hard.yaml` | q008,q013,q016,q023,q024,q026,q027,q028 | 20 | 23 | hard concept-author |

Every gold `id` already exists in `tests/eval/queries.yaml` (r001–r015 +
q001–q030), so the merge is a **per-id join**, not an append. None of the 45
queries in `queries.yaml` currently carry `expected_passages`/`gold_claims`, so the
rigorous metrics never fire — that is exactly what this plan fixes.

---

## 1. Merge the annotations into `queries.yaml`

### 1.1 Mechanism

`run_eval.py` only ever loads **one** `--queries` file, and `load_queries()` pulls
`expected_passages` + `gold_claims` straight off each entry. So the gold must live
on the same entries the harness loads. Two acceptable shapes:

- **(A) Merge in place** (recommended): for each gold `id`, copy its
  `expected_passages` + `gold_claims` onto the matching entry in
  `tests/eval/queries.yaml`. Entities/works already present are left untouched
  (the gold files deliberately only add the two gold fields).
- **(B) Keep a separate gold superset file** and point `--queries` at it. Simpler
  for G2 reporting, but drifts from the canonical query set and from the
  `build_gold_from_audit.py --check` sync gate. Use (A) for anything that lands in CI.

A small idempotent merge script (deep-merges by `id`, fails loudly on an unknown
id or a passage_id absent from `data/corpus/passages.jsonl`) should write the
result back to `queries.yaml`:

```bash
.venv/bin/python scripts/goals/g2_baselines/merge_gold.py \
    --queries tests/eval/queries.yaml \
    --gold data/goals/g2/gold_thesis_1.yaml \
           data/goals/g2/gold_thesis_2_last7.yaml \
           data/goals/g2/gold_hard.yaml \
    --in-place
```

(If that script is not yet written, do the merge by hand — it is a pure per-id
field copy — but validate every passage_id against the corpus before committing.)

### 1.2 BLOCKER to fix during the merge — `gold_claims` shape

`gold_thesis_1.yaml` / `gold_hard.yaml` use **bare strings**:

```yaml
gold_claims:
  - "Justin argues that if all things happen by fate..."
```

`gold_thesis_2_last7.yaml` uses a **dict** form:

```yaml
gold_claims:
  - claim: "The term τὸ αὐτεξούσιον was already in Stoic usage..."
```

`load_queries()` does `list(entry.get("gold_claims", []))`, and `judge_claims()`
passes each element to `judge.verify_one(claim, pid)` expecting a **string**. The
dict form will break the judge. **Normalize r009–r015 to bare strings** (drop the
`claim:` key, keep the text) as part of the merge. Verify post-merge that every
`gold_claims` entry is a scalar string.

### 1.3 Coverage gaps are fine

r004 (Tertullian *De Anima* 21), r006 (Pseudo-Clementine *Recognitions* III), and
the thin r003 (Ben Sira via Augustine) carry no/partial `expected_passages` by
design — they are documented gaps, not bugs. `citation_prf` treats empty-gold as
vacuous (not scored), and `aggregate()` only averages F1 over queries that *have*
gold, so gaps neither inflate nor deflate the headline. Leave them annotated as-is.

### 1.4 Keep the sync gate honest

CI runs `scripts/eval/build_gold_from_audit.py --check`. Confirm that script
regenerates the **forbidden-string** fixtures, not the new gold passage/claim
fields; if it also owns `queries.yaml`, extend it (or its allowlist) so the merged
gold doesn't trip `git diff --exit-code`. Run `--check` locally after the merge.

---

## 2. Produce citation-F1 + faithfulness verified-rate

The judge needs an LLM key (provider chain in `LLMService`) and the `graphrag`
package importable (`CitationVerifierV2`, `LLMService`). Citation-F1 needs neither.

```bash
# from repo root, root venv (.venv has fastapi/uvicorn/httpx/pyyaml)
GEMINI_API_KEY=...                 # or MOONSHOT_API_KEY / OPENROUTER_API_KEY
export ELEUTHERIA_EVAL_JUDGE=1     # turns on the faithfulness judge

.venv/bin/python tests/eval/run_eval.py \
    --base-url http://localhost:8000 \
    --queries tests/eval/queries.yaml \
    --output data/goals/g2/run_graphrag.json
```

What lands in the JSON / stdout:

- **`aggregate.citation_f1_mean`** (+ `citation_scored_queries`) — mean citation F1
  over queries with `expected_passages`. Per-query `citation_precision/recall/f1`
  are in `results[]`.
- **`results[].judge.verified_rate`** — fraction of that query's `gold_claims` the
  judge rated `VERIFIED` against the cited passages (best verdict per claim across
  `MISSING < REJECTED < WEAK < VERIFIED`). The judge fetches each cited passage via
  `GET /api/passages/{id}` for `text_content` + `canonical_ref`.

To roll the judge up to one headline number, mean `verified_rate` over judged
queries (the harness stores it per-query; a one-liner over `run_graphrag.json`
gives the corpus-level **faithfulness verified-rate**):

```bash
.venv/bin/python - <<'PY'
import json, statistics
d = json.load(open("data/goals/g2/run_graphrag.json"))
vr = [r["judge"]["verified_rate"] for r in d["results"] if r.get("judge")]
print("judged queries:", len(vr), "verified_rate (mean):", round(statistics.mean(vr),4) if vr else None)
print("citation_f1_mean:", d["aggregate"]["citation_f1_mean"],
      "scored:", d["aggregate"]["citation_scored_queries"])
print("forbidden_hits_total:", d["aggregate"]["forbidden_hits_total"])
PY
```

> Always run the judged eval against the **real backend** for the headline; run it
> against the floors too if you want a judged 3-way (costs LLM calls × claims ×
> citations). For routine CI, citation-F1 (no key) is the cheap gate; the judge is
> a heavier, scheduled job (see §4).

---

## 3. The 3-way comparison table (agentic vs BM25 vs vanilla-RAG)

All three speak the same `POST /api/graphrag/query` + `GET /api/passages/{id}`
contract, so they are scored identically on the same merged gold. Boot the two
floors (from `scripts/goals/g2_baselines/`, see `baselines_README.md`) and capture
three runs:

```bash
QUERIES=tests/eval/queries.yaml

# Baseline 1 — BM25 / FTS-only, no LLM (port 8011)
.venv/bin/python -m uvicorn scripts.goals.g2_baselines.bm25_service:app --port 8011 &
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8011 \
    --queries "$QUERIES" --output data/goals/g2/run_bm25.json

# Baseline 2 — vanilla LLM + FTS RAG, no agent/KG (port 8012)
G2_LLM_PROVIDER=openrouter OPENROUTER_API_KEY=... G2_OPENAI_MODEL=openai/gpt-4o-mini \
.venv/bin/python -m uvicorn scripts.goals.g2_baselines.vanilla_rag_service:app --port 8012 &
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8012 \
    --queries "$QUERIES" --output data/goals/g2/run_vanilla.json

# System under test — agentic GraphRAG (the real EleutherIA API, port 8000)
.venv/bin/python tests/eval/run_eval.py --base-url http://localhost:8000 \
    --queries "$QUERIES" --output data/goals/g2/run_graphrag.json
```

`--compare` takes **exactly two** files, so produce two pairwise deltas:

```bash
.venv/bin/python tests/eval/run_eval.py --compare \
    data/goals/g2/run_bm25.json data/goals/g2/run_graphrag.json
.venv/bin/python tests/eval/run_eval.py --compare \
    data/goals/g2/run_vanilla.json data/goals/g2/run_graphrag.json
```

Headline table to fill from the three `aggregate` blocks (+ the §2 verified-rate
one-liner per run; add `ELEUTHERIA_EVAL_JUDGE=1` to all three for the last column):

| Metric (source field) | BM25 (8011) | Vanilla-RAG (8012) | **Agentic GraphRAG (8000)** |
|---|---|---|---|
| Citation F1, gold (`citation_f1_mean`) | … | … | … |
| Citation recall (mean of `results[].citation_recall`) | … | … | … |
| Faithfulness verified-rate (§2 one-liner) | … | … | … |
| Entity recall (`entity_recall_mean`) | ~0 (by design) | ~0 (by design) | … |
| Work recall (`work_recall_mean`) | ~0 (by design) | ~0 (by design) | … |
| Forbidden hits (`forbidden_hits_total`) | … | … | **must be 0** |
| Latency p50 / p95 ms | … | … | … |

**How to read it** (matches `baselines_README.md`): entity/work recall are
KG-*node* metrics — the passage-only floors score ~0 *by design*, and that gap
quantifies what the KG layer buys. Citation-F1 and verified-rate are the
apples-to-apples columns (all three cite real `passage_id`s, scored identically).
BM25 is a pure lexical floor that visibly misses original-language Greek gold
passages on scholarly-English queries (e.g. r001) — precisely the floor the
agentic lemma-expansion + KG pipeline exists to beat. The agentic column should
dominate on citation-recall/F1 and verified-rate; if it does not, that is a real
finding, not a harness artifact.

---

## 4. CI regression-gate proposal

**Where:** add a new job `g2-benchmark-gate` to `.github/workflows/ci.yml`,
alongside the existing offline `eval-offline` job (which already runs
`pytest tests/eval -q` and the `build_gold_from_audit.py --check` sync). Keep the
heavy/network parts out of the per-PR path.

**Two-tier design** (because the backend + LLM judge can't run on every PR):

### Tier 1 — per-PR, offline, no backend, no key (hard gate)
Runs in `eval-offline`. Cheap, deterministic, blocks merge:

1. **Gold integrity** — every `expected_passages` id resolves in
   `data/corpus/passages.jsonl`; every `gold_claims` entry is a scalar string
   (catches the §1.2 dict-form regression); no gold id missing from
   `queries.yaml`. Add as `tests/eval/test_gold_integrity.py` (pure file checks,
   no network) so it runs inside the existing `pytest tests/eval -q` step.
2. **Forbidden-string fixtures in sync** — already covered by
   `build_gold_from_audit.py --check`.
3. **Scoring unit tests** — `test_scoring.py` already pins `citation_prf`
   semantics; keep it.

### Tier 2 — scheduled (cron) + manual `workflow_dispatch`, real backend (soft→hard gate)
A separate workflow `.github/workflows/g2-benchmark.yml`, `on: schedule` (nightly)
+ `workflow_dispatch`, with `GEMINI_API_KEY`/`OPENROUTER_API_KEY` from repo secrets
and the backend reachable (compose up, or point `--base-url` at staging). It:

1. runs the judged eval against the real backend (§2);
2. asserts thresholds and uploads `run_graphrag.json` as an artifact;
3. optionally captures the two floors and posts the §3 table as a job summary.

**Proposed thresholds** (set after one judged baseline run establishes the floor;
start permissive, ratchet up — mirror the allowlist philosophy of the existing
`kg_work_id` gate):

| Gate | Threshold | Tier | Rationale |
|---|---|---|---|
| `forbidden_hits_total == 0` | hard, **0 tolerance** | 1 (answers from any captured run) & 2 | anti-fabrication is non-negotiable (academic integrity policy) |
| `citation_f1_mean >= BASELINE − 0.05` | hard | 2 | no silent retrieval regression; 0.05 absorbs LLM nondeterminism |
| `citation_recall (mean) >= BASELINE − 0.05` | hard | 2 | recall is the metric the KG layer is meant to lift |
| `verified_rate (mean) >= BASELINE − 0.05` | soft (warn) → hard once stable | 2 | judge is LLM-scored, noisier; warn first |
| `error_rate == 0` | hard | 2 | a 5xx/timeout from the backend fails the run |
| agentic `citation_f1_mean > max(bm25, vanilla)` | soft (warn) | 2 | the system must beat its own floors; warn if it regresses to floor |

Store the committed baseline as `data/goals/g2/baseline_metrics.json` (the headline
aggregate from a blessed `run_graphrag.json`); the gate diffs the fresh run against
it and the job fails if any hard threshold is breached. Re-bless (update the file)
only on an intentional, reviewed improvement — same pattern as the SHACL/quality
reports already in CI.

**Why this split:** the existing `eval-offline` job has no backend and no LLM key,
so it can only gate *static* gold integrity + scoring + forbidden fixtures (Tier
1). Citation-F1/verified-rate require a live backend and (for the judge) a key, so
they belong in a scheduled job with secrets (Tier 2) — keeping PR latency low while
still catching retrieval/faithfulness regressions nightly.

---

## 5. Order of operations

1. Normalize r009–r015 `gold_claims` to bare strings (§1.2).
2. Merge all three gold files into `tests/eval/queries.yaml` by id (§1.1),
   validating every passage_id against `data/corpus/passages.jsonl`.
3. Run `build_gold_from_audit.py --check` + `pytest tests/eval -q` locally; add
   `test_gold_integrity.py` (Tier-1 gate).
4. Capture the three runs (§3) and the judged agentic run (§2); fill the table.
5. Bless `data/goals/g2/baseline_metrics.json`; wire `g2-benchmark.yml` (Tier 2)
   + the Tier-1 checks into `eval-offline` (§4).
