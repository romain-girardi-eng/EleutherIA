# EleutherIA — SOTA Roadmap (June 2026)

Goal: make EleutherIA the reference academic agentic GraphRAG system — where "SOTA" means
**enforced** (not prompted) zero-fabrication, measured faithfulness, and full provenance
from critical edition to rendered claim.

## Cross-cutting diagnosis (from full-codebase audit, 2026-06-10)

The zero-hallucination guarantee is currently prompt-only:

- `text_verifier.py` (deterministic Greek-fabrication check against the corpus) is fully
  implemented but **disabled** — call site commented out in `scholarly_agent.py` ("too many
  false positives").
- `CitationVerifierV2` (adversarial per-claim audit, fail-closed, fresh re-fetch) is the
  best-engineered component in the codebase and is **never constructed in production** —
  `Deps()` in `graphrag_service.py` omits it.
- The only live gate, `ProgrammaticVerify`, checks ref-marker *existence*, not quote
  *fidelity*: the SYSTEM_PROMPT-mandated `> Greek (Author, ref) [P1]` blockquote format is
  the one place fabricated Greek would appear, and the one format never text-checked
  (`QUOTE_RE` matches only double-quoted spans). Unsupported quotes were laundered into
  prose instead of dropped.
- `tests/eval/` is broken and excluded from CI; the only committed baseline is an all-500
  run. No citation precision/recall, no faithfulness metric, no regression gate.
- Fabrication also exists *upstream of retrieval*: 9 confirmed-fabricated Greek strings and
  173 unadjudicated Greek runs sit in served KG node descriptions
  (`data/audit/*_deferred.jsonl`) — answer-time verification alone never catches these.

Nearly every fix is wiring/integration of components that already exist and are unit-tested.

## Ranked goals

| # | Goal | Effort | Wave |
|---|------|--------|------|
| G1 | Close ProgrammaticVerify holes: blockquote Greek containment check, drop (not launder) unsupported quotes, no free pass for short ancient spans, honest `verified` semantics | S | **A** |
| G8 | Lift evidence truncation: full passage text in bundles/context pack (keep 400-char in-loop summaries) | S | **A** |
| G7 | Translation provenance: stop labeling AI translations as scholarly (`works.py` LIKE-bug), real model names in provenance, `ai_generated` flag in MCP results | S | **A** |
| G13 | Security: remove committed prod DSN (+rotate), `compare_digest`, API key out of URL, rate-limit LLM endpoints, authz on traces/drafts | S | **A** |
| G2 | Wire CitationVerifierV2 into both production paths (env-gated, claim-sampled), act on REJECTED/MISSING, honest grounding score | M | **B** |
| G3 | Golden eval set + CI harness, gold seeded from audit corpus (cite_fix triples → citation P/R; greek_insertions → must-not-appear suite) | M | **B** |
| G5 | Retrieval bug cluster: oga_tokens passage_id, anchor passage UUID survival, unified FTS config, `passage_role` filter, errors ≠ empty results | M | **B** |
| G6 | Integrity-flag known-fabricated KG content (metadata-additive), unified review queue + item-by-item CLI | S/M | **B** |
| G4 | Re-enable text_verifier rebuilt (bundle-span whitelist, accent-folded matching, Latin extractor, FP regression tests first) | M | **C** |
| G9 | One citation/claim-ledger contract on every product path (streaming complete, cache replay, /answer metrics, share, text_verification banner) | M | **C** |
| G10 | Semantic-layer soundness: inverse-pair fabrication bug (`argues_for`), asserted vs inferred named graphs, edge provenance in RDF, VoID/DCAT | M | **C** |
| G11 | Activate dormant quality machinery: deep mode (CounterEvidenceHunter), cross-encoder reranker, EvidenceSufficiency in react path | S | **C** |
| G12 | kg_work_id collisions (39 groups): manual per-work remediation via G6 queue + CI uniqueness gate | M | **D** |
| G14 | Corpus tamper-evidence: text_sha256 at ingest, drift audit, per-passage edition provenance JSONB | S/M | **D** |
| G15 | Dead-code excision (half of graph_nodes.py is unreachable FSM), generated stats (README/prompts misstate corpus 3-4×) | M | **D** |

## Do-not-do (constraints that outrank the goals)

1. **No vector DB / embeddings leg.** Vectorless is the methodological identity; retrieval
   problems are bugs (G5), not architecture.
2. **No bulk auto-fix of any data queue** — 1,988 mechanical findings, 173 Greek runs,
   39 kg_work_id groups, 33 mismatch nodes: item-by-item review only. Build queue *tooling*,
   never queue *automation*.
3. **Never apply the deferred "replacement Greek"** without per-item verification against
   the critical editions in `DOCTORAT/Doctorat SHAL/`. Until verified: flag-and-filter.
4. **Don't re-enable text_verifier as-is** — rework first (G4), FP regression tests before
   the flag flips.
5. **Don't ship the agent loop's terminal answer directly** — ledger→render→verify is the
   faithfulness architecture; change the loop's output contract instead (G15).
6. **No RAGAS/deepeval wholesale** — the faithfulness judge is our own CitationVerifierV2
   offline; embedding-based metrics contradict the vectorless stance.
7. **No full OWL-RL materialization** (benchmarked: 120× cost, zero useful inferences).
   The closure needs narrowing (G10), not widening.
8. **No single-migration ontology consolidation** (influences/influenced_by, wrote/authored_by)
   — per-edge verification, slow background queue.
9. **Verification must not block streaming** — label chunks `preview`, retract post-hoc via
   SSE; never buffer the whole render.
10. **No new auto-generated citation/translation/edge waves** until G3 measures the precision
    of the existing ones.
11. **Never generate, complete, or back-translate ancient text anywhere** — including test
    fixtures (copy must-not-appear strings from the audit JSONLs, never re-type).

## Definition of SOTA (acceptance)

- Every rendered claim carries a machine-checked evidence link; every ancient-language
  quotation is verbatim-verified against the corpus at answer time (deterministic) and
  claim-semantics-verified (adversarial LLM) on sampled claims.
- CI fails on: citation precision/recall regression, any must-not-appear string surfacing,
  SHACL invariant violation, fabricated-inference in the RDF closure.
- Every passage traces to a named critical edition with checksum; every AI translation is
  labeled as such on every surface (API, MCP, UI, share, export).
- The eval harness publishes per-release faithfulness numbers usable in the methodology
  chapter.
