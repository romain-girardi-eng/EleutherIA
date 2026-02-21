/**
 * Claim Verifier Service
 *
 * Extracts atomic claims from the answer, attaches source references,
 * and verifies each claim against the cited source content.
 * Classifies claims as supported / partial / unsupported.
 */

import { SourceCitationLike, ClaimUnit, ClaimVerificationSummary } from '../types';
import { LLMService } from './llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('ClaimVerifier');

/**
 * Extract atomic claims from an answer.
 * Splits on sentence boundaries while keeping citation markers attached.
 */
export function extractClaims(answer: string): ClaimUnit[] {
  // Split into sentences, keeping citation markers attached
  const sentences = answer
    .split(/(?<=[.!?;·])\s+/)
    .filter(s => s.trim().length > 10);

  const claims: ClaimUnit[] = [];

  for (let i = 0; i < sentences.length; i++) {
    const text = sentences[i].trim();

    // Skip section headers (markdown)
    if (text.startsWith('#') || text.startsWith('---')) continue;

    // Extract citation markers from this sentence
    const markerRegex = /\[(\d+)\]/g;
    const citationMarkers: number[] = [];
    let match: RegExpExecArray | null;
    while ((match = markerRegex.exec(text)) !== null) {
      citationMarkers.push(parseInt(match[1], 10));
    }

    // Determine claim type heuristically
    let claimType: ClaimUnit['claimType'] = 'interpretive';
    if (/[""«»]/.test(text) || /[α-ωΑ-Ω]{3,}/.test(text)) {
      claimType = 'quote';
    } else if (/according to|argues|wrote|stated|held that|maintained/i.test(text)) {
      claimType = 'paraphrase';
    } else if (/\b(in|during|century|BCE|CE|AD|BC)\b/i.test(text)) {
      claimType = 'historical';
    }

    claims.push({
      claimId: `claim_${i}`,
      text,
      sourceNodeIds: [],
      citationMarkers,
      claimType,
    });
  }

  return claims;
}

/**
 * Attach source node IDs to claims based on their citation markers.
 */
export function attachClaimSources(
  claims: ClaimUnit[],
  sources: SourceCitationLike[],
): ClaimUnit[] {
  const sourceById = new Map(sources.map(s => [s.id, s]));

  return claims.map(claim => {
    const nodeIds = claim.citationMarkers
      .map(m => sourceById.get(m)?.nodeId)
      .filter((id): id is string => !!id);

    return { ...claim, sourceNodeIds: nodeIds };
  });
}

/**
 * Build verification context for a single claim from its cited sources.
 */
export function buildVerificationContext(
  claim: ClaimUnit,
  sources: SourceCitationLike[],
): string {
  const sourceById = new Map(sources.map(s => [s.nodeId, s]));
  const parts: string[] = [];

  for (const nodeId of claim.sourceNodeIds) {
    const source = sourceById.get(nodeId);
    if (!source) continue;
    parts.push(`Source [${source.nodeLabel}]:`);
    parts.push(source.content || '(no content)');
    if (source.metadata?.author) parts.push(`Author: ${source.metadata.author}`);
    if (source.metadata?.ctsUrn) parts.push(`Reference: ${source.metadata.ctsUrn}`);
    parts.push('');
  }

  return parts.join('\n');
}

/**
 * Classify a claim based on its verification score.
 */
export function classifyClaim(score: number): 'supported' | 'partial' | 'unsupported' {
  if (score >= 0.78) return 'supported';
  if (score >= 0.50) return 'partial';
  return 'unsupported';
}

/**
 * Verify claims against their cited sources using an LLM.
 * Returns updated claims with status and score.
 */
export async function verifyClaimsWithLLM(
  claims: ClaimUnit[],
  sources: SourceCitationLike[],
  llm: LLMService,
): Promise<ClaimUnit[]> {
  // Only verify claims that have citations
  const citedClaims = claims.filter(c => c.citationMarkers.length > 0);
  const uncitedClaims = claims.filter(c => c.citationMarkers.length === 0);

  // Mark uncited substantive claims as unsupported
  const processedUncited = uncitedClaims.map(c => ({
    ...c,
    status: 'unsupported' as const,
    score: 0.0,
  }));

  if (citedClaims.length === 0) {
    return [...processedUncited];
  }

  // Batch verify claims (max 10 at a time to avoid token limits)
  const batchSize = 10;
  const verified: ClaimUnit[] = [];

  for (let i = 0; i < citedClaims.length; i += batchSize) {
    const batch = citedClaims.slice(i, i + batchSize);
    const batchResults = await verifyBatch(batch, sources, llm);
    verified.push(...batchResults);
  }

  return [...verified, ...processedUncited];
}

async function verifyBatch(
  claims: ClaimUnit[],
  sources: SourceCitationLike[],
  llm: LLMService,
): Promise<ClaimUnit[]> {
  const claimEntries = claims.map((c, i) => {
    const context = buildVerificationContext(c, sources);
    return `CLAIM ${i + 1}: "${c.text}"\nCITED SOURCES:\n${context || '(none)'}`;
  }).join('\n---\n');

  const prompt = `You are a scholarly fact-checker for ancient philosophy research.
For each claim below, assess whether the cited sources support it.

${claimEntries}

Respond with a JSON array. For each claim, give:
- "claim_index": the 1-based index
- "score": 0.0 to 1.0 (how well the source supports the claim)
- "reason": brief explanation (1 sentence)

Score guidelines:
- 1.0: Claim is directly stated in source text
- 0.8: Claim is clearly entailed by source
- 0.6: Core meaning matches but wording differs
- 0.4: Weak or tangential support
- 0.2: Mostly unsupported
- 0.0: No support or contradicts source

Respond ONLY with valid JSON: [{"claim_index": 1, "score": 0.8, "reason": "..."}]`;

  try {
    const response = await llm.generateForTask(prompt, 'citation_verification');
    const parsed = parseVerificationResponse(response, claims.length);

    return claims.map((claim, i) => {
      const result = parsed.find(r => r.claim_index === i + 1);
      const score = result?.score ?? 0.0;
      return {
        ...claim,
        score,
        status: classifyClaim(score),
      };
    });
  } catch (error) {
    logger.error('LLM verification failed, marking all as partial', error);
    // Fail safe: mark as partial rather than dropping
    return claims.map(c => ({
      ...c,
      score: 0.5,
      status: 'partial' as const,
    }));
  }
}

function parseVerificationResponse(
  response: string,
  expectedCount: number,
): Array<{ claim_index: number; score: number; reason: string }> {
  try {
    // Extract JSON array from response (may contain markdown fences)
    const jsonMatch = response.match(/\[[\s\S]*\]/);
    if (!jsonMatch) return [];
    const parsed = JSON.parse(jsonMatch[0]);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(item => ({
      claim_index: typeof item.claim_index === 'number' ? item.claim_index : 0,
      score: typeof item.score === 'number' ? Math.max(0, Math.min(1, item.score)) : 0,
      reason: String(item.reason || ''),
    }));
  } catch {
    logger.warn('Failed to parse verification response');
    return [];
  }
}

/**
 * Compute a summary of claim verification results.
 */
export function summarizeVerification(claims: ClaimUnit[]): ClaimVerificationSummary {
  return {
    total: claims.length,
    supported: claims.filter(c => c.status === 'supported').length,
    partial: claims.filter(c => c.status === 'partial').length,
    unsupported: claims.filter(c => c.status === 'unsupported').length,
  };
}
