/**
 * Query Mode Service
 *
 * Detects whether a query should trigger philological mode
 * (close-reading, exact arguments, grammatical analysis).
 */

import { getLogger } from '../utils/logger';

const logger = getLogger('QueryMode');

/**
 * Patterns that trigger philological mode.
 */
const PHILOLOGICAL_PATTERNS: RegExp[] = [
  /exact\s+arguments?/i,
  /close\s+reading/i,
  /philological/i,
  /what\s+exactly\s+does\s+\w+\s+say/i,
  /what\s+exactly\s+did\s+\w+\s+say/i,
  /what\s+are\s+the\s+exact/i,
  /greek\s+term/i,
  /latin\s+term/i,
  /grammatical\s+analysis/i,
  /syntactic\s+analysis/i,
  /original\s+(?:greek|latin)\s+(?:text|passage)/i,
  /exegesis\s+of/i,
  /close\s+analysis/i,
  /textual\s+analysis/i,
  /what\s+does\s+the\s+(?:greek|latin)\s+(?:say|mean)/i,
  /literal\s+meaning/i,
  /parse\s+the\s+(?:greek|latin)/i,
];

/**
 * Detect whether a query should trigger philological mode.
 */
export function isPhilologicalQuery(query: string): boolean {
  for (const pattern of PHILOLOGICAL_PATTERNS) {
    if (pattern.test(query)) {
      logger.info(`Philological mode triggered by pattern: ${pattern.source}`);
      return true;
    }
  }
  return false;
}
