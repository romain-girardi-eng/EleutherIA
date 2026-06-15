# G2 — Provable Quality (rigorous eval + baselines)

**Objective:** Convert EleutherIA's genuinely strong anti-fabrication engine from *unfalsifiable* into
*benchmarked and publishable*.

**Why (from analysis):** The plumbing is excellent and inert. `tests/eval/run_eval.py` already computes entity P/R,
citation **P/R/F1** (`scoring.py`), a 22-string fabrication blocklist, and an **LLM faithfulness judge** reusing the
adversarial `CitationVerifierV2`. But of 45 gold queries in `tests/eval/queries.yaml`, **0 have `expected_passages`
and 0 have `gold_claims`** → the two rigorous metrics never execute. The "academic benchmark" is 4 cases scored by
keyword presence (always 4/4). **No baseline comparison exists anywhere.** So current "100% / High" claims are not
load-bearing.

**Deliverables (artifacts under `data/goals/g2/`):**
1. **Annotated gold set** — the 15 `romain_thesis_queries` + 8 hard concept-author cases get `expected_passages`
   (passage_ids) and 3–5 atomic `gold_claims` each, sourced from the DOCTORAT critical editions on disk.
2. **Baselines** — two endpoints behind the same `--base-url` contract: (a) BM25/FTS-only, (b) vanilla LLM+top-k-FTS RAG.
3. **Benchmark report** — three-way comparison table: citation-F1, faithfulness-verified-rate, entity-recall at equal recall.
4. **CI regression gate** — wire `ELEUTHERIA_EVAL_JUDGE=1 run_eval.py` into CI with thresholds.

**First increment:** Annotate the 15 thesis queries (the highest-value, thesis-relevant set) with expected_passages +
gold_claims, then run the judge and publish the first real citation-F1 + faithfulness numbers.

**Success criteria:** Headline numbers are defensible ("agentic graph traversal lifts citation-F1 from X→Y over BM25");
CI fails on regression; the methodology paper (`docs/academic/METHODOLOGY_PAPER_DSH_DRAFT.md`) can cite real benchmarks.

**Dynamic workflow design:** Phase 1: agents draft gold annotations per query (expected_passages + gold_claims) by
retrieving from corpus + critical editions → staged for human verification (each claim checked). Phase 2: implement
baselines + run the three-way harness. Phase 3: emit report + CI wiring proposal. Self-paced: expand gold set over time.
