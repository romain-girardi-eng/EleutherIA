# GraphRAG benchmark on the reference question — 2026-08-28

Decision record for the pipeline overhaul of 2026-08-28. Everything below was
measured in production (free-will.app, host `ben`) on the reference question
`r016` of `tests/eval/queries.yaml`:

> How does Origen in *De Principiis* III.1 argue for self-determination
> (to eph hemin) against Stoic determinism, and how do Bobzien and Frede
> assess the continuity between the Stoic and the Origenian conceptions?

All runs: `mode=fast`, `force_refresh=true`, SSE endpoint called from inside
the Docker network (Cloudflare challenges `curl`). Captures live on the host
as `/home/ben/eleutheria_bench_*.sse`; the trace rows in
`free_will.query_traces` carry `stage_metrics`, the pair-level audit report
and `metadata.lead` where applicable.

## Decision

**Production stays on the `react` pipeline with the scholar-judge.** The
lead-researcher pipeline (`pipeline=lead`) remains available per request,
tested, and off by default. It did not beat the reference after four rounds
(see below); its real gains (a 20× smaller synthesis context, facet-structured
prose) do not translate into speed or into more surviving citations.

## Before / after on the reference question

| | 2026-08-22 (old gate, sampled audit) | 2026-08-28 final (`ac2f789`) |
|---|---|---|
| Citations audited | 8 of 32–40 (sample; audit aborted at 75 % rejection) | **95 pairs, all** |
| Verdicts | 3 OK · 2 weak · 3 rejected / 2 OK · 4 rejected · 2 missing | **89 verified** · 4 weak · 1 rejected · 1 missing |
| Publication | whole text published, badge Low, 27–34 citations shown as "verified" | **219 sentences published / 6 withheld**, badge Partial, **81 citations verified** |
| Latency / cost (API-equivalent) | 558–599 s / 3.43–3.71 $ | 862 s / 6.45 $ |

The old system published everything and labelled unaudited citations
"verified"; the new one audits every (sentence, citation) pair and withholds
only the sentences whose own pair failed.

## Rounds

| Run | Pipeline · models | s | $ | pairs audited → verified | sentences pub. / withheld | citations kept |
|---|---|---|---|---|---|---|
| 10:13 | react · Opus, sentence gate only (cap 64) | 776 | 5.00 | 64/84 → 50 | 182 / 36 | 48 |
| 10:42 | react · **Codex only** (gpt-5.6-sol) | 656 | 0.82 | 50 → 20 (11 rejected) | 113 / 49 | 14 |
| 11:11 | react · **Gemini Flash** (GEMINI_MODEL wins over the request) | 160 | 0.79 | 33 → 16 | 84 / 21 | 16 |
| 11:32 | react · **Gemini 3.1 Pro (low)** | 471 | 0.49 | — | blocked: 0 of 23 refs resolved (citation grammar ignored) | 0 |
| 11:47 | react · Codex, scholar-judge (id-level) | 813 | 1.03 | 37 → 13 | 31 / 85 | 6 |
| 12:30 | react · **Opus + scholar-judge** | 845 | 7.11 | 103 → 98 | 209 / 6 | 96 |
| 12:23 | lead (round 1) · Opus lead, Flash sub-agents | 529 | 2.74 | 9 → 4 | 116 / 23 | 3 |
| 13:00 | react · Codex, pair-level judge | 810 | 1.51 | 106 → 61 (36 weak) | 110 / 42 | 33 |
| 13:14 | lead (round 2) · dossiers citable | 861 | 5.93 | 90 → 69 | 170 / 28 | 51 |
| 13:49 | **react · Opus + judge (reference)** | **862** | **6.45** | **95 → 89** | **219 / 6** | **81** |
| 14:04 | lead (round 3) | 530 | 1.44 | — | blocked by the old content gate (2 unattested `[edge:]`) | 0 |
| 14:33 | lead (round 4) · substance gate | 835 | 7.57 | 123 → 101 | 179 / 25 | 54 |

## Defects found by the benchmark and fixed (all on `main`, deployed)

1. Publication gate was all-or-nothing: one WEAK among 64 blocked the answer
   (79/79 audited production traces blocked). → sentence-level, then
   **pair-level** withholding (`publication_gate.py`).
2. The verifier could not re-fetch knowledge-graph **node** citations
   (54 of 55 "missing" on the first run). → node statements audited with a
   secondary-layer framing (`NODE_VERIFY_PROMPT`).
3. Whole-sentence claims made multi-source sentences fail ("says nothing
   about Y"). → clause-level claims, companion sources, tool loop
   (`fetch_passage`, `fetch_node`, `search_corpus`, `neighbors`).
4. Judge literalism ("does not *explicitly* say"). → substance standard with
   paired examples in the prompt.
5. Judge verdict calls sent `max_tokens=700`; claude-opus-5's thinking ate the
   budget → empty or truncated verdicts, 3 retries, WEAK. → 4000 first call,
   8000 recovery, failure classes logged.
6. `corpus_passage()` refused "original" rows in a modern language (works
   ingested in English) → MISSING. → translation-tier evidence.
7. Streamed audit abandoned at 180 s → "no auditable citations". → 900 s
   (`ELEUTHERIA_CITATION_AUDIT_MAX_WAIT_S`).
8. Content gate required an attested fault line — a template requirement that
   blocked a 49 k-char, 105-marker answer. → substance gate (≥ 1 grounded
   passage, ≥ ¼ markers resolved, anti-template guard; fault lines are a
   metric).
9. Text verifier deleted attested Greek: bounded probe on common tokens
   (Ench. 51), term lists, short phrases, duplicated Contra Celsum rows. →
   re-attribution, term-list and short-phrase policies, accent-tolerant
   anchors.
10. Raw `[edge:…]` markers leaked into prose; graph seed unused on the react
    path; observability columns never written; PEP 758 syntax vs the 3.12
    deploy container; prompt injection surface in retrieved text. → all fixed
    (see git log 2026-08-28).

## What the benchmark taught

- **Synthesis latency is output-bound.** A 22 k-token context and a 420 k one
  both take ~390 s for Opus to write 37–50 k characters. Shrinking the input
  saves money, not time.
- **The judge dominates cost on every pipeline** (95–123 Opus verdicts per
  answer). The lever is the judge model, not the architecture.
- **Model behaviour differs more than architecture does.** Opus: 0 rejected of
  95–103. Codex: writes shorter, over-attributes, and judges literally (36 weak
  of 106 even after calibration). Gemini Pro (low): ignores the citation
  grammar. Flash: fast and thin.
- **Remaining citation loss is bibliographic**: `pub_*` / `scholarly_work_*`
  nodes cited as sources carry no auditable text (identity records) and come
  back MISSING; their sentences are withheld and their co-citations orphaned.

## Follow-ups (not done)

- Treat bibliographic nodes as reference pointers, not evidence, in both the
  writer's grammar and the judge.
- Judge on a cheaper subscription model (Sonnet to measure; Codex measured too
  strict on Codex-written text).
- Simplification pass now that a reference benchmark exists: legacy FSM path,
  opencode runtime duplicate, `deep` chain (counter-evidence → methodology ×2
  → polishing), referee, `SCHOLAR_RAG` bifurcation, ~35 env flags.
- Live baseline capture (`tests/eval`, schema v2) has still never been run.
- Data: Contra Celsum 2.20 duplicated rows (`1.20` mislabel); `pub_*` nodes
  with 19–43 characters of text.
