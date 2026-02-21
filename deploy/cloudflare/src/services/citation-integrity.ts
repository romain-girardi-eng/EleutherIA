/**
 * Citation Integrity Service
 *
 * Ensures every [N] marker in the answer maps to a real source,
 * and every source in sources[] is cited at least once.
 * Prevents the observed [18]-with-10-sources bug.
 */

import { SourceCitationLike, CitationIntegrityResult } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('CitationIntegrity');

/**
 * Extract all unique citation markers [N] from an answer string.
 * Returns sorted, deduplicated array of marker numbers.
 */
export function extractCitationMarkers(answer: string): number[] {
  const regex = /\[(\d+)\]/g;
  const markers = new Set<number>();
  let match: RegExpExecArray | null;
  while ((match = regex.exec(answer)) !== null) {
    markers.add(parseInt(match[1], 10));
  }
  return Array.from(markers).sort((a, b) => a - b);
}

/**
 * Check whether all citation markers are within the valid source range [1..sourceCount].
 */
export function validateCitationRange(
  answer: string,
  sourceCount: number,
): { ok: boolean; outOfRange: number[] } {
  const markers = extractCitationMarkers(answer);
  const outOfRange = markers.filter(m => m < 1 || m > sourceCount);
  return { ok: outOfRange.length === 0, outOfRange };
}

/**
 * Find sources that exist in the sources list but are never cited in the answer.
 */
export function findOrphanSources(
  answer: string,
  sources: SourceCitationLike[],
): string[] {
  const cited = new Set(extractCitationMarkers(answer));
  return sources
    .filter(s => !cited.has(s.id))
    .map(s => s.nodeId);
}

/**
 * Renumber citations in the answer so markers are consecutive [1]..[N]
 * based on order of first appearance. Also returns the remapping.
 *
 * This also strips any markers that reference non-existent sources.
 */
export function renumberCitations(
  answer: string,
  sources: SourceCitationLike[],
): { answer: string; sources: SourceCitationLike[]; remap: Record<number, number> } {
  const validIds = new Set(sources.map(s => s.id));
  const markers = extractCitationMarkers(answer);
  const validMarkers = markers.filter(m => validIds.has(m));

  // Build appearance-order mapping: old id -> new sequential id
  const seen: number[] = [];
  const regex = /\[(\d+)\]/g;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(answer)) !== null) {
    const num = parseInt(match[1], 10);
    if (validIds.has(num) && !seen.includes(num)) {
      seen.push(num);
    }
  }

  const remap: Record<number, number> = {};
  seen.forEach((oldId, i) => {
    remap[oldId] = i + 1;
  });

  // Replace markers in answer
  let newAnswer = answer.replace(/\[(\d+)\]/g, (fullMatch, numStr) => {
    const num = parseInt(numStr, 10);
    if (remap[num] !== undefined) {
      return `[${remap[num]}]`;
    }
    // Strip out-of-range or invalid markers entirely
    return '';
  });

  // Clean up double spaces left by removed markers
  newAnswer = newAnswer.replace(/  +/g, ' ').replace(/ ([.,;:!?])/g, '$1');

  // Reorder sources to match new numbering
  const newSources = seen.map((oldId, i) => {
    const original = sources.find(s => s.id === oldId)!;
    return { ...original, id: i + 1 };
  });

  return { answer: newAnswer, sources: newSources, remap };
}

/**
 * Reindex sources to remove unused ones. Keeps only sources that are
 * actually cited in the answer.
 */
export function reindexSources(
  sources: SourceCitationLike[],
  usedNodeIds: Set<string>,
): SourceCitationLike[] {
  return sources
    .filter(s => usedNodeIds.has(s.nodeId))
    .map((s, i) => ({ ...s, id: i + 1 }));
}

/**
 * Run the full citation integrity assertion. Returns a diagnostic object.
 * This is the main entry point for the guardrail.
 */
export function assertCitationIntegrity(
  answer: string,
  sources: SourceCitationLike[],
): CitationIntegrityResult {
  const markers = extractCitationMarkers(answer);
  const sourceCount = sources.length;
  const outOfRange = markers.filter(m => m < 1 || m > sourceCount);
  const orphanSources = findOrphanSources(answer, sources);

  const result: CitationIntegrityResult = {
    passed: outOfRange.length === 0,
    outOfRange,
    orphanSources,
    totalMarkers: markers.length,
    totalSources: sourceCount,
  };

  if (!result.passed) {
    logger.warn(`Citation integrity FAILED: out-of-range markers ${JSON.stringify(outOfRange)} with ${sourceCount} sources`);
  }

  return result;
}

/**
 * Strip all out-of-range citation markers from the answer text.
 * Used as a last-resort safety measure.
 */
export function stripOutOfRangeMarkers(answer: string, sourceCount: number): string {
  return answer.replace(/\[(\d+)\]/g, (fullMatch, numStr) => {
    const num = parseInt(numStr, 10);
    if (num >= 1 && num <= sourceCount) return fullMatch;
    return '';
  }).replace(/  +/g, ' ').replace(/ ([.,;:!?])/g, '$1');
}
