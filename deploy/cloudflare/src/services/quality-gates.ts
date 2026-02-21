/**
 * Quality Gates Service
 *
 * Evaluates whether the final answer meets quality thresholds.
 * Triggers insufficiency fallback when evidence is too weak.
 */

import { ClaimUnit, ClaimVerificationSummary, QualityGatesResult } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('QualityGates');

/** Threshold above which we trigger insufficiency fallback */
const UNSUPPORTED_RATIO_THRESHOLD = 0.20;

/**
 * Compute the ratio of unsupported claims.
 */
export function computeUnsupportedRatio(summary: ClaimVerificationSummary): number {
  if (summary.total === 0) return 0;
  return summary.unsupported / summary.total;
}

/**
 * Detect potentially fabricated quotes in the answer.
 * Looks for Greek/Latin text in quotes that doesn't appear in any source content.
 */
export function hasFabricatedQuotes(
  answer: string,
  sourceContents: string[],
): boolean {
  // Extract quoted Greek/Latin text
  const quotedRegex = /[""«»]([^""«»]*[α-ωΑ-Ωά-ώἀ-ῷ][^""«»]*)[""«»]/g;
  let match: RegExpExecArray | null;
  const joinedSources = sourceContents.join(' ').toLowerCase();

  while ((match = quotedRegex.exec(answer)) !== null) {
    const quoted = match[1].trim();
    if (quoted.length < 5) continue; // Skip very short fragments

    // Check if this Greek/Latin text appears in any source
    const normalizedQuote = quoted.toLowerCase().replace(/\s+/g, ' ');
    if (!joinedSources.includes(normalizedQuote)) {
      // Check for partial match (first 20 chars)
      const prefix = normalizedQuote.slice(0, 20);
      if (prefix.length >= 5 && !joinedSources.includes(prefix)) {
        logger.warn(`Potentially fabricated quote detected: "${quoted.slice(0, 50)}..."`);
        return true;
      }
    }
  }

  return false;
}

/**
 * Determine if we should return an insufficiency fallback response.
 */
export function shouldFallbackInsufficientEvidence(
  summary: ClaimVerificationSummary,
  fabricatedQuoteDetected: boolean,
  outOfRangeCitations: boolean,
): boolean {
  // Hard fail: fabricated quotes or out-of-range citations after repair
  if (fabricatedQuoteDetected) return true;
  if (outOfRangeCitations) return true;

  // Soft fail: too many unsupported claims
  const ratio = computeUnsupportedRatio(summary);
  return ratio > UNSUPPORTED_RATIO_THRESHOLD;
}

/**
 * Evaluate all quality gates and return a summary.
 */
export function evaluateQualityGates(
  summary: ClaimVerificationSummary,
  answer: string,
  sourceContents: string[],
  outOfRangeCitations: boolean,
): QualityGatesResult {
  const unsupportedRatio = computeUnsupportedRatio(summary);
  const fabricatedQuoteDetected = hasFabricatedQuotes(answer, sourceContents);
  const insufficientEvidenceTriggered = shouldFallbackInsufficientEvidence(
    summary,
    fabricatedQuoteDetected,
    outOfRangeCitations,
  );

  if (insufficientEvidenceTriggered) {
    logger.warn(`Quality gates triggered: unsupported=${unsupportedRatio.toFixed(2)}, fabricated=${fabricatedQuoteDetected}, outOfRange=${outOfRangeCitations}`);
  }

  return {
    insufficientEvidenceTriggered,
    unsupportedRatio,
    fabricatedQuoteDetected,
    outOfRangeCitations,
  };
}

/**
 * Build the insufficiency fallback answer.
 */
export function buildInsufficientEvidenceAnswer(
  query: string,
  supportedClaims: ClaimUnit[],
  totalSources: number,
): string {
  const parts: string[] = [];

  parts.push('## Insufficient Evidence for a Complete Answer\n');
  parts.push(`The available sources in our database do not provide sufficient evidence to fully answer: "${query}"\n`);

  if (supportedClaims.length > 0) {
    parts.push('### What We Can Confirm\n');
    parts.push('Based on verified evidence from our sources:\n');
    for (const claim of supportedClaims.slice(0, 5)) {
      const markers = claim.citationMarkers.map(m => `[${m}]`).join('');
      parts.push(`- ${claim.text} ${markers}`);
    }
    parts.push('');
  }

  parts.push('### Limitations\n');
  parts.push(`While ${totalSources} sources were consulted, several claims could not be verified against the textual evidence in our database. `);
  parts.push('Scholars should consult the primary texts directly for a comprehensive analysis.');

  return parts.join('\n');
}
