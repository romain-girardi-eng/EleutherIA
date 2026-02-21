# GraphRAG Citation Integrity and Philological Quality Plan

Date: 2026-02-21  
Status: Proposed (implementation-ready)  
Owner: GraphRAG / API team  
Scope: Production answer quality for citation grounding, claim reliability, and scholar-grade philological output

## 1. Executive Summary

This plan consolidates all recommendations and decisions from the Origen audit and follow-up design discussion.

Primary objective:
- Move from "good RAG answers" to "scholar-grade, citation-safe answers" with strict DB grounding.

Core strategy:
- Add a citation integrity guardrail.
- Add claim-level support verification.
- Add targeted self-correction (self-RAG patching) for unsupported claims.
- Add deterministic normalization for minor mismatches.
- Add a philological response mode for "exact arguments" questions.

## 2. Audit Findings That Drive This Plan

From the production audit of the query "what are Origen's exact arguments for free will?":

- 10/10 cited sources existed in DB with matching IDs and labels.
- Key Origen claims were present in retrieved KG nodes and passage nodes.
- Answer quality was strong but below top scholarly standards.
- A citation integrity bug appeared: answer text included an out-of-range marker `[18]` while `sources.length == 10`.
- Retrieved passage nodes used metadata with `database_verified=false` and external critical edition references.
- Primary vs secondary evidence separation was not strict enough for philological-grade output.

Implication:
- We do not have a pure hallucination problem only.
- We have a reliability and scholarly-rigor consistency problem at synthesis time.

## 3. Product Decisions (Agreed)

Decision 1:
- Citation markers in final answer must always map to a real source in the returned `sources[]` list.

Decision 2:
- Any claim without support must be rewritten or removed.
- Never remove a citation marker alone while keeping the unsupported claim.

Decision 3:
- Introduce claim status classes:
- `supported`
- `partial`
- `unsupported`

Decision 4:
- For `unsupported` claims, run targeted correction (self-RAG patch) or remove claim if correction fails.

Decision 5:
- For `partial` claims, run deterministic normalization before any LLM correction.

Decision 6:
- Use stable source IDs (`nodeId`) internally through the full pipeline.
- Render `[1]...[N]` markers only at the final formatting stage.

Decision 7:
- If unsupported ratio is above threshold, return an explicit insufficiency response instead of speculative synthesis.

Decision 8:
- Add a "philological mode" for "exact arguments" / close-reading queries:
- grammar + rhetoric + doctrinal layers
- strict source-first behavior
- explicit uncertainty when evidence is insufficient

## 4. Target Architecture

Pipeline stages for `/api/graphrag/answer`:

1. Retrieval
- Existing retrieval pipeline (nodes/passages/edges).
- Keep current context builder.

2. Draft Synthesis
- LLM generates initial draft with internal source anchors by `nodeId`.
- No final numeric citation formatting yet.

3. Citation and Claim Extraction
- Split into atomic claims.
- Extract source anchors per claim.

4. Support Verification
- Compare each claim to cited source content from DB.
- Classify each claim as `supported`, `partial`, or `unsupported`.

5. Automatic Repair
- `partial`: normalization script (deterministic transforms).
- `unsupported`: targeted self-RAG correction prompt with constrained edit scope.

6. Re-Verification
- Verify repaired claims.
- Drop claim if still unsupported.

7. Final Formatting
- Build final deduplicated `sources[]`.
- Renumber citations in appearance order.
- Ensure all markers are in range.

8. Fail-Safe Gate
- If unsupported ratio remains above threshold, return "insufficient evidence" answer template.

## 5. Verification Model

### 5.1 Claim Unit

A claim unit is:
- one sentence or clause-level assertion
- one rhetorical quotation interpretation statement
- one historical/attribution statement

Each claim unit contains:
- `claim_id`
- `text`
- `source_node_ids[]`
- `claim_type` (`quote`, `paraphrase`, `interpretive`, `historical`)

### 5.2 Source Text for Verification

For each cited source:
- Prefer passage raw text fields when available.
- Fallback order:
- passage text
- node description
- structured metadata (`premises`, `conclusion`, `author`, `reference`, `cts_urn`)

### 5.3 Claim Classification Rules

`supported`:
- Claim is directly entailed by source text/metadata.
- Quotes match source excerpt (after normalization of punctuation/diacritics if configured).

`partial`:
- Core meaning supported but wording has minor drift.
- Canonical references or terminology can be normalized to DB form.

`unsupported`:
- No direct support.
- Wrong attribution.
- Fabricated quote.
- Citation marker maps to no source.

### 5.4 Confidence Scoring (suggested)

Weighted score per claim:
- lexical overlap score (0-1)
- semantic entailment score (0-1)
- metadata match score (0-1)

Status threshold baseline:
- `supported`: >= 0.78
- `partial`: >= 0.50 and < 0.78
- `unsupported`: < 0.50

## 6. Normalization Rules for Minor Mismatches

Deterministic normalization layer should run before LLM correction.

Rules:
- normalize author/work names to DB canonical labels.
- normalize reference format (`De Orat. 6` vs `De Oratione 6`).
- normalize Greek/Latin punctuation and spacing.
- normalize citation marker positions.
- replace vague source mention with canonical source label if unambiguous.
- soften over-strong language:
- "proves" -> "argues"
- "exactly means" -> "can be read as"

Hard constraints:
- no addition of new factual content.
- no creation of new source markers.

## 7. Targeted Self-RAG Patch Flow

When claim status is `unsupported`:

Patch prompt input:
- original claim
- cited source text snippets
- allowed operations: `rewrite`, `remove`, `mark_insufficient`
- forbidden operation: introducing unsupported new claims

Expected output:
- corrected claim text
- action used
- mapped `nodeId` list

Patch retry policy:
- max 2 retries per claim.
- if still unsupported after retries, remove claim.

## 8. Citation Integrity Guardrail (Non-Negotiable)

Validation checks before response returns:

- every `[n]` marker references an existing entry in final `sources[]`.
- every source in `sources[]` is actually cited at least once unless explicitly marked as "background".
- no out-of-range markers.
- no duplicate conflicting numbering.
- reference section exactly matches final citation markers.

This directly prevents the observed `[18]` out-of-range issue.

## 9. Philological Mode (Scholar-Level Output)

Trigger conditions:
- query contains patterns like:
- "exact arguments"
- "philological"
- "close reading"
- "Greek term"
- "what exactly does X say"

Mode-specific output schema (mandatory sections):

1. Textual Evidence
- exact citation
- quoted original language from provided context only

2. Grammatical Exegesis
- key lemma/form/syntactic role for crucial terms

3. Rhetorical Exegesis
- function in context (objection, refutation, prosopopoiia, diatribe, etc.)

4. Doctrinal/Argumentative Conclusion
- premise-conclusion mapping
- confidence level

5. Limits of Evidence
- explicit statement if direct textual support is missing

Hard rule:
- no reconstruction of Greek/Latin from memory.
- if absent from context, explicitly state insufficiency.

## 10. Prompting Specification

### 10.1 Base Synthesis Addendum

```text
Ground every substantive claim in provided sources only.
Keep internal source IDs (nodeId) attached to each claim.
Do not output final numeric citations yet.
If evidence is insufficient, state that explicitly.
```

### 10.2 Philological Addendum

```text
Adopt a philological method.
For each major claim provide:
(1) exact citation,
(2) grammatical analysis of key terms,
(3) rhetorical function in context,
(4) doctrinal implication.
Do not reconstruct Greek/Latin from memory.
Separate textual facts from interpretation.
```

### 10.3 Patch Prompt (Unsupported Claims)

```text
Claim: <text>
Cited sources: <source snippets>
Task: Rewrite only this claim so it is fully supported by cited sources, or return REMOVE.
No new facts. No new sources.
```

## 11. Data Contract Additions

Add to internal pipeline objects:

- `claim_verification[]`:
- `claim_id`
- `status`
- `score`
- `source_node_ids`
- `repair_action`

- `citation_integrity`:
- `out_of_range_markers`
- `orphan_sources`
- `integrity_passed`

- `quality_gates`:
- `unsupported_claim_ratio`
- `insufficient_evidence_triggered`
- `philological_mode_enabled`

Expose selected debug fields behind internal/admin flag only.

## 12. Quality Gates and Fail-Safes

Recommended thresholds:
- hard fail if out-of-range markers > 0.
- hard fail if fabricated quote detected.
- insufficiency fallback if unsupported ratio > 0.20 after repair.
- insufficiency fallback if primary-source-backed claims < required minimum for query class.

Fallback template behavior:
- return concise answer with explicit limitation note.
- include what sources are available and what is missing.

## 13. Testing Plan

Unit tests:
- citation renumbering correctness.
- out-of-range detection.
- claim classifier status boundaries.
- normalization rule safety.

Integration tests:
- "exact arguments" query set (Origen, Alexander, Epictetus, Augustine).
- adversarial prompts requesting fabricated citations.
- multilingual term handling (Greek/Latin markers).

Regression tests:
- snapshot tests that ensure no citation marker exists without source.
- ensure repaired claim text remains semantically faithful.

Production canary checks:
- monitor unsupported ratio distribution.
- monitor percentage of answers entering insufficiency fallback.
- monitor correction pass latency impact.

## 14. Metrics and Success Criteria

Primary KPIs:
- citation integrity error rate (target: 0%).
- unsupported claim rate post-repair (target: < 3%).
- scholar review acceptance rate (target defined by editorial team).

Secondary KPIs:
- fraction of responses with explicit primary-source anchors.
- average citations per major claim.
- philological mode activation and completion quality.

Operational KPIs:
- added latency from verification + repair.
- cost delta per answer.

## 15. Rollout Plan

Phase 0:
- instrumentation only.
- no answer mutation.

Phase 1:
- enable citation integrity hard checks.
- enable deterministic normalization.

Phase 2:
- enable targeted claim repair for `unsupported`.
- keep kill switch.

Phase 3:
- enable philological mode for selected query classes.
- monitor scholar feedback.

Phase 4:
- full rollout.
- enforce insufficiency fallback policy globally.

## 16. Risks and Mitigations

Risk:
- over-pruning makes answers too terse.
Mitigation:
- controlled thresholds and patch retries.

Risk:
- verifier false negatives on subtle interpretations.
Mitigation:
- hybrid verifier with lexical + semantic + metadata channels.

Risk:
- latency increase.
Mitigation:
- batch verification, claim chunking, cache source text.

Risk:
- "philological mode" used without enough text.
Mitigation:
- strict insufficiency behavior.

## 17. Immediate Backlog (Concrete)

1. Implement citation integrity validator in answer finalization.
2. Add claim extraction + status classifier.
3. Implement deterministic normalization module.
4. Add targeted patch prompt for unsupported claims.
5. Add philological mode prompt branch and output template.
6. Add gating and fallback policy.
7. Add tests for out-of-range marker bug.
8. Add admin observability for claim verification outcomes.

## 18. Definition of Done

Done means all of the following are true:

- No out-of-range citation markers can be returned.
- Unsupported claims are never returned as supported facts.
- Every major claim in "exact arguments" responses has explicit grounded evidence or explicit insufficiency.
- Primary and secondary evidence are clearly separated in output.
- All critical paths covered by tests and production dashboards.

