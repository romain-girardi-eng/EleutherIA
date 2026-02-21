# GraphRAG Implementation Checklist (Cloudflare Route Mapping)

Date: 2026-02-21  
Status: Execution checklist  
Companion spec: `docs/plans/2026-02-21-graphrag-citation-philology-quality-plan.md`

## 1. Scope

This checklist maps every agreed quality recommendation to exact Cloudflare backend files and functions.

Primary codepaths in scope:
- `deploy/cloudflare/src/routes/graphrag.ts`
  - `graphragRoutes.post('/answer', ...)`
  - `graphragRoutes.get('/query/stream', ...)`
- `deploy/cloudflare/src/services/pageindex-retrieval.ts`
  - `buildPageIndexContext(...)`
- `deploy/cloudflare/src/services/evidence-chain-builder.ts`
  - `buildEvidencePackage(...)`

Supporting codepaths:
- `deploy/cloudflare/src/services/llm.ts`
  - `generateForTask(...)`
- `deploy/cloudflare/src/services/database.ts`
  - `getNode(...)`, `getNodesByIds(...)`, `getPassage(...)`
- `deploy/cloudflare/src/types/index.ts`
  - GraphRAG response contracts
- `deploy/cloudflare/tests/*`
  - Vitest test suite

## 2. Implementation Order (Recommended)

1. Citation integrity hard guardrail
2. Claim extraction + verification
3. Deterministic normalization
4. Targeted claim repair (self-RAG patch)
5. Philological mode prompt branch
6. Fallback gates + observability
7. Tests + rollout flags

## 3. Workstream A: Citation Integrity Guardrail

### A.1 Create shared citation integrity service

- [ ] Add `deploy/cloudflare/src/services/citation-integrity.ts` with:
  - `extractCitationMarkers(answer: string): number[]`
  - `validateCitationRange(answer: string, sourceCount: number): { ok: boolean; outOfRange: number[] }`
  - `renumberCitations(answer: string, usedSourceIdsInOrder: string[]): { answer: string; remap: Record<number, number> }`
  - `reindexSources(sources: SourceCitationLike[], usedNodeIds: Set<string>): SourceCitationLike[]`
  - `findOrphanSources(answer: string, sources: SourceCitationLike[]): string[]`
  - `assertCitationIntegrity(...)` returning final diagnostics object

- [ ] Add local interface in this file (or shared type):
  - `SourceCitationLike = { id: number; nodeId: string; nodeLabel: string; nodeType: string; content: string; metadata: Record<string, any> }`

### A.2 Integrate in `/answer` route

File: `deploy/cloudflare/src/routes/graphrag.ts`  
Function: `graphragRoutes.post('/answer', ...)`

- [ ] After `answer` generation and after `structuredSources` assembly, run `assertCitationIntegrity(...)`.
- [ ] If out-of-range markers exist:
  - First attempt repair pass (workstream D).
  - If still failing, strip unsupported claims or trigger insufficiency fallback (workstream F).
- [ ] Ensure returned `sources` list matches markers actually present in answer.

### A.3 Integrate in `/query/stream` route

File: `deploy/cloudflare/src/routes/graphrag.ts`  
Function: `graphragRoutes.get('/query/stream', ...)`

- [ ] Before `sendEvent('complete', ...)`, run the same citation integrity check on `fullAnswer` and `formattedSources`.
- [ ] If correction was required, emit `status` event indicating post-processing correction.
- [ ] Ensure SSE final payload cannot contain out-of-range markers.

### A.4 Known bug explicitly covered

- [ ] Add regression check for scenario where answer includes `[18]` but `sources.length = 10`.

Acceptance criteria:
- No final payload from `/answer` or `/query/stream` can contain out-of-range citations.

## 4. Workstream B: Claim Extraction + Verification

### B.1 Create claim verifier service

- [ ] Add `deploy/cloudflare/src/services/claim-verifier.ts` with:
  - `extractClaims(answer: string): ClaimUnit[]`
  - `attachClaimSources(claims: ClaimUnit[], answer: string, sources: SourceCitationLike[]): ClaimUnit[]`
  - `buildVerificationContext(claim: ClaimUnit, sourcesByNodeId: Map<string, SourceEvidence>): string`
  - `verifyClaimsWithLLM(...)` using `LLMService.generateForTask(..., 'citation_verification')`
  - `classifyClaim(score: number): 'supported' | 'partial' | 'unsupported'`

- [ ] Define types:
  - `ClaimUnit`
  - `ClaimVerificationResult`
  - `VerificationBatchResult`

### B.2 Reuse/align existing agentic verification types

File: `deploy/cloudflare/src/types/agentic.ts`

- [ ] Reuse semantics from:
  - `ClaimVerification`
  - `VerificationResult`
- [ ] Do not directly couple `/answer` to agentic types; create shared minimal types in `types/index.ts` if needed.

### B.3 Source evidence hydration

Files:
- `deploy/cloudflare/src/services/database.ts`
- `deploy/cloudflare/src/services/claim-verifier.ts` (new)

- [ ] Build a helper that hydrates verification text by `nodeId`:
  - passage text first
  - node description second
  - selected metadata (`premises`, `conclusion`, `reference`, `cts_urn`) third

Acceptance criteria:
- Each major claim in the final answer has an explicit verification status.

## 5. Workstream C: Deterministic Normalization (`partial` claims)

### C.1 Create normalization service

- [ ] Add `deploy/cloudflare/src/services/citation-normalizer.ts` with pure transforms:
  - `normalizeReferenceLabels(...)` (`De Orat. 6` vs `De Oratione 6`)
  - `normalizeAuthorWorkForms(...)`
  - `normalizeGreekLatinPunctuation(...)`
  - `downtoneOverclaiming(...)` (e.g., "proves" -> "argues")

### C.2 Hook into both routes

File: `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] Apply normalization for all claims classified `partial` before any LLM repair.
- [ ] Log normalization actions in diagnostics (internal only).

Acceptance criteria:
- Minor mismatches are fixed without introducing new facts or new sources.

## 6. Workstream D: Targeted Self-RAG Patch (`unsupported` claims)

### D.1 Create claim repair service

- [ ] Add `deploy/cloudflare/src/services/claim-repair.ts` with:
  - `repairUnsupportedClaim(claim, sourceContext, llm): Promise<RepairResult>`
  - `repairUnsupportedClaimsBatch(...)`
  - strict policy: return `REMOVE` when unsupported

### D.2 LLM usage

File: `deploy/cloudflare/src/services/llm.ts`

- [ ] Use existing `generateForTask(..., 'self_rag')` for repair prompts.
- [ ] Keep JSON-only response format for deterministic parsing.

### D.3 Route integration

File: `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] In `/answer` and `/query/stream` finalize phase:
  - run verifier
  - normalize partial claims
  - repair unsupported claims
  - re-verify
  - drop still-unsupported claims

Acceptance criteria:
- Unsupported claims never survive final output as factual assertions.

## 7. Workstream E: Philological Mode

### E.1 Add prompt profiles

- [ ] Add `deploy/cloudflare/src/prompts/graphrag.ts`:
  - `BASE_SYNTHESIS_PROMPT_BLOCK`
  - `PHILOLOGICAL_MODE_BLOCK`
  - `INSUFFICIENCY_BLOCK`

### E.2 Add query classifier for mode

- [ ] Add `deploy/cloudflare/src/services/query-mode.ts`:
  - `isPhilologicalQuery(query: string): boolean`
  - trigger patterns:
    - "exact arguments"
    - "close reading"
    - "philological"
    - "what exactly does X say"

### E.3 Route integration

File: `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] In `/answer`, branch prompt composition:
  - base mode
  - philological mode
- [ ] In `/query/stream`, apply same mode branch for prompt parity.

### E.4 Output structure requirements (philological mode)

- [ ] Enforce sections:
  - Textual Evidence
  - Grammatical Exegesis
  - Rhetorical Exegesis
  - Doctrinal Conclusion
  - Limits of Evidence

Acceptance criteria:
- "Exact arguments" queries produce structured close-reading output with explicit textual limits.

## 8. Workstream F: Quality Gates and Fallback

### F.1 Add gate evaluator service

- [ ] Add `deploy/cloudflare/src/services/quality-gates.ts`:
  - `evaluateUnsupportedRatio(...)`
  - `hasFabricatedQuotes(...)`
  - `shouldFallbackInsufficientEvidence(...)`

### F.2 Integrate hard gates

File: `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] Gate conditions:
  - out-of-range citations > 0 after repair
  - fabricated quote detection true
  - unsupported ratio > threshold (e.g., 0.20) after repair
- [ ] On failure, replace answer with insufficiency-safe response.

Acceptance criteria:
- System prefers explicit insufficiency over speculative output.

## 9. Workstream G: Data Contracts and Response Metadata

### G.1 Extend response types

File: `deploy/cloudflare/src/types/index.ts`

- [ ] Add optional fields to GraphRAG response contract:
  - `citationIntegrity?: { passed: boolean; outOfRange: number[]; orphanSources: string[] }`
  - `claimVerificationSummary?: { total: number; supported: number; partial: number; unsupported: number }`
  - `qualityGates?: { insufficientEvidenceTriggered: boolean; unsupportedRatio: number }`

- [ ] Keep backward compatibility by making new fields optional.

### G.2 Frontend compatibility check

- [ ] Confirm `frontend/src/api/client.ts` and renderer tolerate additional optional fields.

Acceptance criteria:
- Existing frontend remains compatible; new diagnostics available for admin/debug.

## 10. Workstream H: Context/Source Numbering Consistency

### H.1 Verify numbering contract between context and returned sources

Files:
- `deploy/cloudflare/src/services/pageindex-retrieval.ts` (`buildPageIndexContext`)
- `deploy/cloudflare/src/routes/graphrag.ts` (`structuredSources`/`formattedSources` builders)

- [ ] Guarantee one-to-one mapping:
  - `[Source N]` in prompt context corresponds to source entry with `id = N`.
- [ ] Ensure any source section included in prompt but omitted from returned `sources[]` cannot be cited.
- [ ] If sections are supplementary and uncited in output, explicitly prevent `[N]` usage beyond returned IDs.

Acceptance criteria:
- Prompt numbering and API numbering are always identical.

## 11. Workstream I: Tests (Vitest)

### I.1 Add new unit tests

- [ ] `deploy/cloudflare/tests/citation-integrity.test.ts`
  - out-of-range marker detection
  - renumbering correctness
  - orphan source detection

- [ ] `deploy/cloudflare/tests/claim-verifier.test.ts`
  - claim extraction
  - status classification boundaries

- [ ] `deploy/cloudflare/tests/citation-normalizer.test.ts`
  - deterministic transforms only
  - no added citations/new facts

- [ ] `deploy/cloudflare/tests/quality-gates.test.ts`
  - fallback trigger logic

### I.2 Add route-level regression tests (lightweight)

- [ ] Add test covering known bug pattern:
  - answer contains `[18]`, source count is 10
  - final post-processed answer passes integrity checks

Acceptance criteria:
- All new tests pass with `cd deploy/cloudflare && npm test`.

## 12. Workstream J: Observability and Rollout Control

### J.1 Logging

File: `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] Log per-answer diagnostics:
  - number of claims
  - unsupported ratio
  - repairs attempted/succeeded
  - citation integrity pass/fail
  - fallback trigger boolean

### J.2 Feature flags

- [ ] Add env-driven flags in `deploy/cloudflare/src/types/index.ts` (Env interface), e.g.:
  - `ENABLE_CITATION_GUARDRAIL`
  - `ENABLE_CLAIM_VERIFIER`
  - `ENABLE_SELF_RAG_REPAIR`
  - `ENABLE_PHILOLOGICAL_MODE`
  - `ENABLE_INSUFFICIENCY_FALLBACK`

- [ ] Use safe defaults (off in first deployment, on in staged rollout).

Acceptance criteria:
- Can enable/disable each quality feature independently in production.

## 13. Concrete Edit Map (By File)

### `deploy/cloudflare/src/routes/graphrag.ts`

- [ ] `/answer`: add finalize pipeline after `answer` generation and `structuredSources` build.
- [ ] `/query/stream`: add finalize pipeline before `sendEvent('complete', ...)`.
- [ ] Add shared helper function in this file or imported service:
  - `finalizeAnswerWithQualityGuards(...)`

### `deploy/cloudflare/src/services/pageindex-retrieval.ts`

- [ ] Verify/update `buildPageIndexContext(...)` numbering comments and behavior to match final sources exactly.

### `deploy/cloudflare/src/services/evidence-chain-builder.ts`

- [ ] Optionally enrich evidence package with nodeId-indexed lookup to support claim verifier context.
- [ ] Do not infer citations from answer text alone for integrity decisions.

### `deploy/cloudflare/src/services/llm.ts`

- [ ] Reuse `generateForTask` for `citation_verification` and `self_rag`.
- [ ] Add strict JSON parse helper if needed (optional improvement).

### `deploy/cloudflare/src/services/database.ts`

- [ ] Add helper used by verifier if needed:
  - `getSourceEvidenceByNodeId(nodeId: string)` (composition over existing methods).

### `deploy/cloudflare/src/types/index.ts`

- [ ] Add optional response diagnostics types.
- [ ] Keep compatibility with current payload consumers.

### `deploy/cloudflare/src/prompts/graphrag.ts` (new)

- [ ] Store reusable base + philological + patch prompt blocks.

### `deploy/cloudflare/tests/*.test.ts`

- [ ] Add four new unit test files plus one regression test.

## 14. Minimal Deliverable by Sprint

### Sprint 1 (must-have)

- [ ] Workstream A (citation guardrail)
- [ ] Workstream H (numbering consistency)
- [ ] Regression test for out-of-range markers

### Sprint 2

- [ ] Workstreams B + C + D (verification, normalization, targeted repair)

### Sprint 3

- [ ] Workstreams E + F + J (philological mode, fallback, flags/logging)

## 15. Definition of Done (Checklist Version)

- [ ] No out-of-range citations in final responses.
- [ ] Unsupported claims are removed or explicitly marked insufficient.
- [ ] `/answer` and `/query/stream` share the same quality-finalization behavior.
- [ ] Philological mode is available and produces the required section structure.
- [ ] Tests cover integrity, verification, normalization, and fallback gates.
- [ ] Feature flags allow gradual rollout and fast rollback.

