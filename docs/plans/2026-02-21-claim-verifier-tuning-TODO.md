# Claim Verifier Pipeline — Tuning TODO

**Status:** Disabled in production (`wrangler.toml`), code is deployed but feature-flagged OFF.
**Date:** 2026-02-21
**Related commit:** `136fbcb` (disabled flags), `235869a` (original implementation)

## What Broke

Querying "origen ?" (a well-sourced topic with 8 nodes, 10 edges) triggered the
"Insufficient Evidence" fallback, replacing a good answer with a crippled stub.
The second query about Origen's exact arguments in De Principiis produced
fragmented, broken text with citations in wrong positions.

## Root Causes

### 1. Uncited sentences auto-marked unsupported (CRITICAL)

`claim-verifier.ts` lines 123-131: any sentence without a `[N]` marker gets
`score: 0.0, status: 'unsupported'`. Scholarly answers naturally have
introductory sentences, transitions, and summaries that don't cite a specific
source but are valid synthesis.

**Fix:** Classify uncited sentences as `neutral` (a new status) rather than
`unsupported`. Only count claims that cite sources but fail verification as
unsupported. Alternatively, skip uncited sentences entirely — don't count them
in the ratio.

### 2. Unsupported ratio threshold too low

`quality-gates.ts` line 14: `UNSUPPORTED_RATIO_THRESHOLD = 0.20`. With #1,
even 2 uncited sentences in a 10-sentence answer (20%) triggers the fallback.

**Fix:** Raise to 0.40-0.50, and only compute the ratio over claims that
actually cite sources (excluding neutral/uncited sentences).

### 3. Stage F removes still-unsupported claims via string replacement

`graphrag.ts` lines 147-154: after repair, remaining unsupported claims are
removed with `currentAnswer.replace(claim.text, '')`. This breaks text flow,
leaves orphan punctuation, and can mangle Greek/Latin quotations.

**Fix:** Instead of removing, either (a) downgrade to a weaker phrasing using
the normalizer, or (b) just keep them with a footnote marker like `[unverified]`,
or (c) only remove if the claim is truly fabricated (no source match at all).

### 4. `hasFabricatedQuotes` false positives on Greek text

`quality-gates.ts` lines 28-53: checks if quoted Greek text appears verbatim
in source content. But the LLM often paraphrases or normalizes whitespace/
diacritics, so legitimate Greek from real sources fails the exact match.

**Fix:** Use fuzzy matching (Levenshtein distance or ngram overlap) instead of
`includes()`. Or only flag quotes that have zero partial overlap with sources.

### 5. Triple LLM call chain is slow and compounds errors

The pipeline does: verify → repair → re-verify → remove. Each LLM call can
introduce errors. The repair prompt may generate text that the re-verify call
then marks as unsupported, leading to removal.

**Fix:** Simplify to a single verification pass. If a claim is unsupported,
flag it but don't attempt automated repair in v1. Let the human see the
original answer with quality annotations instead.

## Feature Flags (current production state)

| Flag | Value | Effect |
|------|-------|--------|
| `ENABLE_CITATION_GUARDRAIL` | `true` | Fixes [18]-with-10-sources bug (deterministic, safe) |
| `ENABLE_CLAIM_VERIFIER` | `false` | Disabled — too aggressive on uncited sentences |
| `ENABLE_SELF_RAG_REPAIR` | `false` | Disabled — depends on verifier working |
| `ENABLE_PHILOLOGICAL_MODE` | `true` | Close-reading prompt for scholarly queries |
| `ENABLE_INSUFFICIENCY_FALLBACK` | `false` | Disabled — triggers on well-sourced answers |

## Files to Modify

| File | What to change |
|------|---------------|
| `deploy/cloudflare/src/services/claim-verifier.ts` | Add `neutral` status for uncited sentences |
| `deploy/cloudflare/src/types/index.ts` | Add `neutral` to `ClaimUnit.status` union |
| `deploy/cloudflare/src/services/quality-gates.ts` | Raise threshold, exclude neutrals from ratio, fix fuzzy matching |
| `deploy/cloudflare/src/routes/graphrag.ts` | Remove Stage F (string deletion), simplify pipeline |
| `deploy/cloudflare/wrangler.toml` | Re-enable flags once fixes are validated |

## Proposed Approach for v2

1. Add `neutral` status — uncited sentences are not failures
2. Only compute unsupported ratio over cited claims
3. Raise threshold to 0.45
4. Remove Stage F (destructive removal) — keep original text, annotate instead
5. Replace `hasFabricatedQuotes` exact match with ngram overlap (>60% = legit)
6. Single verification pass only (no repair loop in v1)
7. Return quality diagnostics as metadata, not as answer replacement
8. Test with 20+ real queries before re-enabling in production
