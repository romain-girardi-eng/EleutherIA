/**
 * Citation Normalizer Service
 *
 * Deterministic transforms for partial claims:
 * - Normalize author/work name forms to DB canonical labels
 * - Normalize reference formats
 * - Normalize Greek/Latin punctuation
 * - Soften overclaiming language
 *
 * Hard constraints: No new facts, no new source markers.
 */

import { ClaimUnit, SourceCitationLike } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('CitationNormalizer');

/**
 * Common author/work abbreviation expansions.
 */
const REFERENCE_EXPANSIONS: Record<string, string> = {
  'De Orat.': 'De Oratione',
  'De Princ.': 'De Principiis',
  'De Fato': 'De Fato',
  'SVF': 'Stoicorum Veterum Fragmenta',
  'DL': 'Diogenes Laertius',
  'D.L.': 'Diogenes Laertius',
  'Ep.': 'Epistulae',
  'Enn.': 'Enneads',
  'Met.': 'Metaphysics',
  'Eth. Nic.': 'Nicomachean Ethics',
  'EN': 'Nicomachean Ethics',
  'NE': 'Nicomachean Ethics',
  'De An.': 'De Anima',
  'Conf.': 'Confessiones',
  'Civ. Dei': 'De Civitate Dei',
  'De Lib. Arb.': 'De Libero Arbitrio',
};

/**
 * Over-strong language replacements.
 */
const OVERCLAIMING_REPLACEMENTS: Array<[RegExp, string]> = [
  [/\bproves\b/gi, 'argues'],
  [/\bdefinitively shows\b/gi, 'suggests'],
  [/\bexactly means\b/gi, 'can be read as'],
  [/\bundeniably\b/gi, 'arguably'],
  [/\bclearly demonstrates\b/gi, 'indicates'],
  [/\bwithout doubt\b/gi, 'plausibly'],
  [/\bcertainly\b/gi, 'likely'],
  [/\bobviously\b/gi, 'apparently'],
  [/\bconclusive(?:ly)?\b/gi, 'suggestive$1'],
  [/\birrefutabl[ey]\b/gi, 'compellingly'],
];

/**
 * Normalize reference labels in a claim text.
 * Expands common abbreviations to canonical forms.
 */
export function normalizeReferenceLabels(text: string): string {
  let normalized = text;
  // Sort entries longest-first so multi-word abbreviations match before substrings
  const entries = Object.entries(REFERENCE_EXPANSIONS)
    .sort((a, b) => b[0].length - a[0].length);
  for (const [abbrev, full] of entries) {
    const escaped = abbrev.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Use word boundary at start; at end, use word boundary only if abbrev
    // doesn't end with a period (periods aren't word chars so \b fails)
    const suffix = abbrev.endsWith('.') ? '(?=\\s|$|[,;:)])' : '\\b';
    const regex = new RegExp(`\\b${escaped}${suffix}`, 'g');
    normalized = normalized.replace(regex, full);
  }
  return normalized;
}

/**
 * Normalize author and work name forms to match DB labels.
 * Uses the actual source labels from the returned sources.
 */
export function normalizeAuthorWorkForms(
  text: string,
  sources: SourceCitationLike[],
): string {
  let normalized = text;

  for (const source of sources) {
    const label = source.nodeLabel;
    if (!label || label === 'Unknown') continue;

    // Build variations of the canonical label
    const author = source.metadata?.author;
    if (author) {
      // If the text mentions a common variant, replace with canonical
      const variants = getAuthorVariants(author);
      for (const variant of variants) {
        if (variant === author) continue;
        const escaped = variant.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`\\b${escaped}\\b`, 'g');
        if (regex.test(normalized)) {
          normalized = normalized.replace(regex, author);
        }
      }
    }
  }

  return normalized;
}

/**
 * Get common name variants for an ancient author.
 */
function getAuthorVariants(canonical: string): string[] {
  const variants: Record<string, string[]> = {
    'Chrysippus': ['Chrysippos', 'Khrysippos'],
    'Epictetus': ['Epictetos', 'Epiktetos'],
    'Aristotle': ['Aristoteles'],
    'Plato': ['Platon'],
    'Seneca': ['Seneca the Younger', 'L. Annaeus Seneca'],
    'Cicero': ['M. Tullius Cicero', 'Tully'],
    'Augustine': ['Augustinus', 'St. Augustine', 'Saint Augustine'],
    'Origen': ['Origenes'],
    'Alexander of Aphrodisias': ['Alexander Aphrodisiensis'],
    'Diogenes Laertius': ['Diogenes Laërtius'],
    'Marcus Aurelius': ['M. Aurelius'],
    'Plotinus': ['Plotinos'],
    'Irenaeus': ['Irenaeus of Lyon', 'Saint Irenaeus'],
  };

  return variants[canonical] || [];
}

/**
 * Normalize Greek and Latin punctuation and spacing.
 */
export function normalizeGreekLatinPunctuation(text: string): string {
  let normalized = text;

  // Normalize Greek ano teleia (middle dot) spacing
  normalized = normalized.replace(/\s*·\s*/g, '· ');

  // Normalize em-dash variants to standard en-dash for references
  normalized = normalized.replace(/—/g, '–');

  // Normalize smart quotes to standard (U+201C, U+201D, U+2018, U+2019)
  normalized = normalized.replace(/[\u201C\u201D\u201E\u201F\u00AB\u00BB]/g, '"');
  normalized = normalized.replace(/[\u2018\u2019\u201A\u201B]/g, "'");

  // Normalize multiple spaces
  normalized = normalized.replace(/  +/g, ' ');

  return normalized;
}

/**
 * Soften over-strong language that overclaims certainty.
 */
export function downtoneOverclaiming(text: string): string {
  let normalized = text;
  for (const [pattern, replacement] of OVERCLAIMING_REPLACEMENTS) {
    normalized = normalized.replace(pattern, replacement);
  }
  return normalized;
}

/**
 * Apply all deterministic normalizations to a claim text.
 * Returns the normalized text. No new facts or sources are added.
 */
export function normalizeClaim(
  claim: ClaimUnit,
  sources: SourceCitationLike[],
): ClaimUnit {
  let text = claim.text;

  text = normalizeReferenceLabels(text);
  text = normalizeAuthorWorkForms(text, sources);
  text = normalizeGreekLatinPunctuation(text);
  text = downtoneOverclaiming(text);

  // Ensure no new citation markers were introduced
  const originalMarkers = new Set(claim.citationMarkers);
  const newMarkerRegex = /\[(\d+)\]/g;
  let match: RegExpExecArray | null;
  while ((match = newMarkerRegex.exec(text)) !== null) {
    const num = parseInt(match[1], 10);
    if (!originalMarkers.has(num)) {
      // Strip any accidentally introduced marker
      text = text.replace(`[${num}]`, '');
    }
  }

  if (text !== claim.text) {
    logger.info(`Normalized claim ${claim.claimId}: "${claim.text.slice(0, 60)}..." → "${text.slice(0, 60)}..."`);
  }

  return { ...claim, text };
}

/**
 * Normalize all partial claims in a list.
 */
export function normalizePartialClaims(
  claims: ClaimUnit[],
  sources: SourceCitationLike[],
): ClaimUnit[] {
  return claims.map(claim => {
    if (claim.status === 'partial') {
      return normalizeClaim(claim, sources);
    }
    return claim;
  });
}
