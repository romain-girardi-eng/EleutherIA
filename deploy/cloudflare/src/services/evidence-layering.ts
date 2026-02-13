/**
 * Evidence Layering Service
 *
 * Partitions evidence into primary (ancient sources) and secondary (modern scholarship),
 * then builds hierarchical context for the LLM with proper academic layering.
 *
 * Ported from Python's _is_primary_node() and _build_hierarchical_context().
 */

import { Evidence } from '../types/agentic';
import { Passage } from './passage-retrieval';
import { getLogger } from '../utils/logger';

const logger = getLogger('EvidenceLayering');

export interface LayeredEvidence {
  primary: Evidence[];
  secondary: Evidence[];
}

// Node types considered primary ancient sources
const PRIMARY_NODE_TYPES = new Set([
  'philosopher', 'concept', 'argument', 'work', 'quote', 'passage',
  'school', 'doctrine', 'text', 'fragment',
]);

// Schools/periods from the ancient world
const ANCIENT_PERIODS = new Set([
  'presocratic', 'classical', 'classical greek', 'hellenistic',
  'roman', 'imperial', 'late antiquity', 'patristic',
]);

const MODERN_INDICATORS = [
  'scholar', 'modern', 'contemporary', 'interpretation', 'bibliography',
  'commentary', 'analysis', 'reception', 'historiography',
];

/**
 * Determine if a piece of evidence is from a primary ancient source.
 * Matches Python's _is_primary_node() logic.
 */
export function isPrimaryEvidence(evidence: Evidence): boolean {
  // Bridge and passage evidence is primary by definition
  if (evidence.type === 'bridge' || evidence.type === 'passage') return true;

  // Community summaries are secondary (they aggregate)
  if (evidence.type === 'community') return false;

  // Context-level evidence is secondary
  if (evidence.type === 'context' || evidence.type === 'concepts') return false;

  // Check node type
  if (evidence.nodeType && PRIMARY_NODE_TYPES.has(evidence.nodeType.toLowerCase())) {
    // But check if it's a modern scholar node
    const label = (evidence.nodeLabel || '').toLowerCase();
    const content = (evidence.content || '').toLowerCase();
    const hasModernIndicator = MODERN_INDICATORS.some(
      ind => label.includes(ind) || content.includes(ind)
    );
    if (hasModernIndicator) return false;
    return true;
  }

  // Check period metadata
  const period = (evidence.metadata?.period || '').toLowerCase();
  if (period && ANCIENT_PERIODS.has(period)) return true;

  // Default: check the isPrimary flag
  return evidence.isPrimary;
}

/**
 * Partition evidence into primary and secondary layers.
 */
export function partitionEvidence(evidence: Evidence[]): LayeredEvidence {
  const primary: Evidence[] = [];
  const secondary: Evidence[] = [];

  for (const e of evidence) {
    if (isPrimaryEvidence(e)) {
      primary.push(e);
    } else {
      secondary.push(e);
    }
  }

  logger.info(`Evidence partitioned: ${primary.length} primary, ${secondary.length} secondary`);
  return { primary, secondary };
}

/**
 * Build hierarchical context string with proper academic layering.
 * Primary sources come first, followed by secondary scholarship.
 */
export function buildHierarchicalContext(
  primary: Evidence[],
  secondary: Evidence[],
  passages: Passage[]
): string {
  const parts: string[] = [];

  // Section 1: Primary source passages (actual ancient texts)
  if (passages.length > 0) {
    parts.push('=== PRIMARY SOURCE TEXTS ===');
    parts.push('Original ancient Greek and Latin passages with scholarly references.\n');

    for (const p of passages) {
      const langLabel = p.language === 'grc' ? 'Greek' : 'Latin';
      const entry = [
        `--- ${p.author}, ${p.canonicalRef} ---`,
        `[${langLabel}] ${p.textContent}`,
        p.ctsUrn ? `CTS URN: ${p.ctsUrn}` : '',
        `Confidence: ${p.confidence.toFixed(2)}`,
        '',
      ].filter(Boolean).join('\n');
      parts.push(entry);
    }
  }

  // Section 2: Primary evidence from KG (philosophers, concepts, arguments)
  if (primary.length > 0) {
    parts.push('\n=== ANCIENT SOURCES & PHILOSOPHICAL CONTEXT ===');
    parts.push('Evidence from ancient philosophers, schools, and doctrinal positions.\n');

    for (const e of primary) {
      const label = e.nodeLabel || e.source;
      const period = e.metadata?.period ? ` (${e.metadata.period})` : '';
      const school = e.metadata?.school ? ` [${e.metadata.school}]` : '';
      parts.push(`• ${label}${period}${school}: ${e.content}`);
    }
  }

  // Section 3: Secondary evidence (modern scholarship, community summaries)
  if (secondary.length > 0) {
    parts.push('\n=== MODERN SCHOLARSHIP & INTERPRETIVE CONTEXT ===');
    parts.push('Community summaries and interpretive frameworks from modern scholars.\n');

    for (const e of secondary) {
      parts.push(`• ${e.source}: ${e.content}`);
    }
  }

  return parts.join('\n');
}
