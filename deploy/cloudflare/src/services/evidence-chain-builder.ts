/**
 * Evidence Chain Builder Service
 * Builds structured evidence chains with CTS URNs and scholarly citations
 */

import { AncientCitation, ModernCitation, EvidenceChain } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('EvidenceChainBuilder');

/**
 * Known modern scholars and their works for citation extraction
 */
const MODERN_SCHOLARS: Record<string, { fullName: string; works: Record<string, { year: number; title: string }> }> = {
  'bobzien': {
    fullName: 'Susanne Bobzien',
    works: {
      '1998': { year: 1998, title: 'Determinism and Freedom in Stoic Philosophy' },
      '2001': { year: 2001, title: 'Chrysippus and the Epistemic Theory of Vagueness' },
    }
  },
  'frede': {
    fullName: 'Michael Frede',
    works: {
      '2011': { year: 2011, title: 'A Free Will: Origins of the Notion in Ancient Thought' },
    }
  },
  'long': {
    fullName: 'A.A. Long',
    works: {
      '1987': { year: 1987, title: 'The Hellenistic Philosophers (with Sedley)' },
      '2002': { year: 2002, title: 'Epictetus: A Stoic and Socratic Guide to Life' },
    }
  },
  'sedley': {
    fullName: 'David Sedley',
    works: {
      '1987': { year: 1987, title: 'The Hellenistic Philosophers (with Long)' },
    }
  },
  'inwood': {
    fullName: 'Brad Inwood',
    works: {
      '1985': { year: 1985, title: 'Ethics and Human Action in Early Stoicism' },
    }
  },
  'brennan': {
    fullName: 'Tad Brennan',
    works: {
      '2005': { year: 2005, title: 'The Stoic Life' },
    }
  },
  'sorabji': {
    fullName: 'Richard Sorabji',
    works: {
      '1980': { year: 1980, title: 'Necessity, Cause and Blame' },
    }
  },
};

/**
 * Extract CTS URN from node - ONLY returns verified URNs, NEVER fabricates
 */
export function extractCtsUrn(node: any): string | undefined {
  // Check all possible locations for CTS URN
  // Qdrant stores it in payload directly or in payload.metadata
  const payload = node.payload || node;

  // Direct cts_urn field (most common for Qdrant data)
  if (payload.cts_urn) {
    return payload.cts_urn;
  }

  // Nested in metadata
  if (payload.metadata?.cts_urn) {
    return payload.metadata.cts_urn;
  }

  // On the node directly (PostgreSQL format)
  if (node.metadata?.cts_urn) {
    return node.metadata.cts_urn;
  }
  if (node.cts_urn) {
    return node.cts_urn;
  }

  // Try to extract from description if embedded (format: urn:cts:greekLit:...)
  const description = payload.description || node.description || '';
  const urnMatch = description.match(/urn:cts:[a-zA-Z]+:[a-zA-Z0-9.:_-]+/);
  if (urnMatch) {
    return urnMatch[0];
  }

  // NO FABRICATION - if we don't have a real CTS URN, return undefined
  return undefined;
}

/**
 * Determine if a node is a passage node (actual ancient text source)
 * STRICT: Only returns true for explicit passage nodes, not concepts/arguments with Greek terms
 */
export function isPassageNode(node: any): boolean {
  // Check explicit type - must be passage, text, source, or quote
  if (node.type === 'passage' || node.type === 'text' || node.type === 'source' || node.type === 'quote') {
    return true;
  }

  // Check for passage indicators in node_id
  const nodeId = node.node_id || node.id || '';
  if (nodeId.startsWith('passage_') || nodeId.includes('_passage_')) {
    return true;
  }

  // Check for CTS URN in metadata - definitive passage indicator
  if (node.metadata?.cts_urn || node.cts_urn) {
    return true;
  }

  // Check for text_embeddings results (from Qdrant searchTexts)
  // These have passage_id, text_content/text_preview, author, title
  if (node.passage_id && (node.text_content || node.text_preview)) {
    return true;
  }

  // DO NOT treat concept/argument nodes as passages just because they contain Greek
  // Concepts like "Heimarmenê" and arguments like "Cylinder Analogy" are NOT passages
  return false;
}

/**
 * Extract ancient text from node description
 * Returns the Greek/Latin portion if found
 */
export function extractAncientText(description: string): string | undefined {
  if (!description) return undefined;

  // Try to find Greek text (polytonic Greek Unicode range)
  const greekMatch = description.match(/[\u0370-\u03FF\u1F00-\u1FFF][^.!?]*[\u0370-\u03FF\u1F00-\u1FFF][^.!?]*/g);
  if (greekMatch && greekMatch[0].length > 10) {
    return greekMatch[0].trim();
  }

  // Try to find quoted Latin text
  const latinMatch = description.match(/[""]([A-Za-z][^""]+)[""]/);
  if (latinMatch && latinMatch[1].length > 20) {
    return latinMatch[1].trim();
  }

  return undefined;
}

/**
 * Parse author and work from node label or metadata
 * Handles passage labels like "Cicero, De Fato 30: Chrysippus on Confatalia"
 */
function parseAuthorWork(node: any): { author: string; work: string; reference?: string } {
  const label = node.label || node.name || '';
  const metadata = node.metadata || {};
  const payload = node.payload || node;

  // Priority 1: Check metadata/payload for structured data
  const author = metadata.author || payload.author;
  const work = metadata.work || metadata.title || payload.work || payload.title;
  if (author && work) {
    return {
      author,
      work,
      reference: metadata.reference || metadata.section || payload.reference || payload.section,
    };
  }

  // Priority 2: Parse from label patterns
  const patterns = [
    // "Cicero, De Fato 30: Description" or "Cicero, De Fato 30"
    /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+)(?::|$)/,
    // "Author, Work Reference" - general pattern
    /^([^,:]+),\s*([^,\d]+)\s*([\d.IVXLCivxlc-]+)?/,
    // "Author: Work Reference"
    /^([^:]+):\s*(.+?)\s*([\d.IVXLCivxlc-]+)?$/,
  ];

  for (const pattern of patterns) {
    const match = label.match(pattern);
    if (match) {
      return {
        author: match[1].trim(),
        work: match[2].trim(),
        reference: match[3]?.trim(),
      };
    }
  }

  // Priority 3: Extract from node_id pattern like "passage_cicero_fat_30"
  const nodeId = node.node_id || payload.node_id || node.id || '';

  // Map common abbreviations
  const authorMap: Record<string, string> = {
    'alex': 'Alexander of Aphrodisias',
    'alexander': 'Alexander of Aphrodisias',
    'cic': 'Cicero',
    'cicero': 'Cicero',
    'epict': 'Epictetus',
    'epictetus': 'Epictetus',
    'aug': 'Augustine',
    'plut': 'Plutarch',
    'aristotle': 'Aristotle',
    'lucretius': 'Lucretius',
    'marcus': 'Marcus Aurelius',
    'justin': 'Justin Martyr',
    'origen': 'Origen',
    'tatian': 'Tatian',
    'irenaeus': 'Irenaeus',
    'melito': 'Melito of Sardis',
    'theophilus': 'Theophilus of Antioch',
    'plotinus': 'Plotinus',
    'plato': 'Plato',
  };

  const workMap: Record<string, string> = {
    'fat': 'De Fato',
    'de_fato': 'De Fato',
    'lib_arb': 'De Libero Arbitrio',
    'disc': 'Discourses',
    'drn': 'De Rerum Natura',
    'drn_ii': 'De Rerum Natura',
    'dial': 'Dialogue with Trypho',
    '1apol': 'First Apology',
    'pa': 'De Principiis',
    'orat': 'Oratio ad Graecos',
    'ah': 'Adversus Haereses',
    'pasch': 'Peri Pascha',
    'autol': 'Ad Autolycum',
    'enn': 'Enneads',
    'timaeus': 'Timaeus',
    'en': 'Nicomachean Ethics',
  };

  // Try multiple node_id patterns
  const nodeIdPatterns = [
    /^passage_([a-z]+)_([a-z_]+)_(\d+[\d_]*)$/i,           // passage_cicero_fat_30
    /^passage_([a-z]+)_([a-z]+)_([ivxlc]+)_(\d+)$/i,       // passage_lucretius_drn_ii_284
    /^passage_([a-z]+)_([a-z_]+)$/i,                        // passage_epict_131 (no separate work)
  ];

  for (const pattern of nodeIdPatterns) {
    const nodeIdMatch = nodeId.match(pattern);
    if (nodeIdMatch) {
      const authorAbbrev = nodeIdMatch[1];
      const workParts = nodeIdMatch.slice(2, -1).join('_');
      const ref = nodeIdMatch[nodeIdMatch.length - 1];

      return {
        author: authorMap[authorAbbrev.toLowerCase()] || authorAbbrev,
        work: workMap[workParts?.toLowerCase()] || workMap[nodeIdMatch[2]?.toLowerCase()] || (workParts || '').replace(/_/g, ' '),
        reference: ref,
      };
    }
  }

  // Fallback: use label as work, author unknown
  return { author: 'Unknown', work: label };
}

/**
 * Build AncientCitation from a passage node
 */
export function buildAncientCitation(node: any, score: number = 0.8): AncientCitation {
  const { author, work, reference } = parseAuthorWork(node);
  const ctsUrn = extractCtsUrn(node);
  const originalText = extractAncientText(node.description);

  // Determine language
  let language: string | undefined;
  if (node.metadata?.language) {
    language = node.metadata.language;
  } else if (/[\u0370-\u03FF\u1F00-\u1FFF]/.test(node.description || '')) {
    language = 'greek';
  } else if (ctsUrn?.includes('latinLit')) {
    language = 'latin';
  }

  return {
    citationText: `${author}, ${work}${reference ? ' ' + reference : ''}`,
    passageId: node.passage_id || node.metadata?.passage_id,
    workId: node.work_id || node.metadata?.work_id,
    ctsUrn,
    title: work,
    author,
    originalText,
    language,
    reference,
    confidence: Math.min(1.0, score),
  };
}

/**
 * Extract modern scholarship citations from answer text
 */
export function extractModernCitations(answer: string | null | undefined): ModernCitation[] {
  const citations: ModernCitation[] = [];
  if (!answer) return citations;

  const seen = new Set<string>();

  // Pattern: "Scholar (Year)" or "Scholar Year" or "(Scholar Year)"
  const patterns = [
    /\b([A-Z][a-z]+(?:\s+(?:&|and)\s+[A-Z][a-z]+)?)\s*\((\d{4})[^)]*\)/g,
    /\b([A-Z][a-z]+)\s+(\d{4})\b/g,
    /\(([A-Z][a-z]+)\s+(\d{4})\)/g,
  ];

  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(answer)) !== null) {
      if (!match[1] || !match[2]) continue;
      const authorName = (match[1] || '').trim();
      if (!authorName) continue;
      const year = parseInt(match[2], 10);
      if (isNaN(year)) continue;
      const key = `${authorName.toLowerCase()}_${year}`;

      if (seen.has(key)) continue;
      seen.add(key);

      // Look up in known scholars
      const scholarKey = (authorName.toLowerCase() || '').split(/\s+/)[0] || '';
      const scholar = MODERN_SCHOLARS[scholarKey];

      if (scholar) {
        const work = scholar.works[String(year)];
        citations.push({
          citationKey: key,
          author: scholar.fullName,
          year,
          title: work?.title || 'Unknown work',
          formattedCitation: `${scholar.fullName} (${year})`,
        });
      } else {
        // Generic citation
        citations.push({
          citationKey: key,
          author: authorName,
          year,
          title: 'Unknown work',
          formattedCitation: `${authorName} (${year})`,
        });
      }
    }
  }

  return citations;
}

/**
 * Build evidence chains from answer and nodes
 */
export function buildEvidenceChains(
  answer: string | null | undefined,
  nodes: any[],
  ancientCitations: AncientCitation[],
  modernCitations: ModernCitation[]
): EvidenceChain[] {
  const chains: EvidenceChain[] = [];
  if (!answer) return chains;

  // Split answer into sentences/claims
  const sentences = answer.split(/(?<=[.!?])\s+/).filter(s => s && s.length > 30);

  // Build chains for major claims (sentences with citations or key philosophical terms)
  const philosophicalTerms = [
    'fate', 'determinism', 'free will', 'freedom', 'necessity',
    'eph\' hemin', 'to eph\' hemin', 'prohairesis', 'synkatathesis',
    'heimarmene', 'autexousion', 'causa', 'voluntas',
    'stoic', 'epicurean', 'peripatetic', 'academic',
    'chrysippus', 'epictetus', 'cicero', 'alexander', 'aristotle'
  ];

  for (const sentence of sentences.slice(0, 10)) { // Limit to first 10 sentences
    const lowerSentence = sentence.toLowerCase();

    // Check if sentence contains philosophical terms or citations
    const hasPhilosophicalContent = philosophicalTerms.some(term => lowerSentence.includes(term));
    const hasCitation = /\[\d+\]|\(\d{4}\)|\b\d+\.\d+\b/.test(sentence);

    if (!hasPhilosophicalContent && !hasCitation) continue;

    // Find related nodes
    const relatedNodeIds: string[] = [];
    const relatedAncient: AncientCitation[] = [];
    const relatedModern: ModernCitation[] = [];

    // Match nodes by label/description overlap
    const safeNodes = nodes || [];
    for (const nodeResult of safeNodes.slice(0, 20)) {
      const node = nodeResult?.payload || nodeResult;
      if (!node) continue;

      const nodeLabel = (node.label || node.name || '').toLowerCase();
      const nodeDesc = (node.description || '').toLowerCase();

      // Check for term overlap
      const hasOverlap = philosophicalTerms.some(term =>
        (lowerSentence.includes(term) && (nodeLabel.includes(term) || nodeDesc.includes(term)))
      );

      if (hasOverlap) {
        relatedNodeIds.push(node.node_id || node.id);
      }
    }

    // Match ancient citations by author/work mention
    for (const citation of ancientCitations || []) {
      const authorLower = (citation.author || '').toLowerCase();
      const workLower = (citation.title || '').toLowerCase();
      if (authorLower && lowerSentence.includes(authorLower) || workLower && lowerSentence.includes(workLower)) {
        relatedAncient.push(citation);
      }
    }

    // Match modern citations by author/year mention
    for (const citation of modernCitations || []) {
      const authorLower = (citation.author || '').toLowerCase().split(' ').pop() || '';
      if (authorLower && lowerSentence.includes(authorLower) || sentence.includes(String(citation.year))) {
        relatedModern.push(citation);
      }
    }

    // Only create chain if we have evidence
    if (relatedNodeIds.length > 0 || relatedAncient.length > 0 || relatedModern.length > 0) {
      const confidence = Math.min(1.0,
        0.3 +
        relatedNodeIds.length * 0.15 +
        relatedAncient.length * 0.2 +
        relatedModern.length * 0.1
      );

      chains.push({
        claim: sentence.trim(),
        kgNodes: relatedNodeIds.slice(0, 5),
        ancientSources: relatedAncient.slice(0, 3),
        modernSources: relatedModern.slice(0, 2),
        confidence: Math.round(confidence * 100) / 100,
      });
    }
  }

  return chains.slice(0, 5); // Return top 5 evidence chains
}

/**
 * Process all nodes and build complete evidence package
 */
export function buildEvidencePackage(
  answer: string | null | undefined,
  nodes: any[] | null | undefined,
  edges: any[] | null | undefined
): {
  ancientCitations: AncientCitation[];
  modernCitations: ModernCitation[];
  evidenceChains: EvidenceChain[];
  ctsUrns: string[];
  passageCount: number;
} {
  // Return empty package if answer is not a string
  const emptyPackage = {
    ancientCitations: [],
    modernCitations: [],
    evidenceChains: [],
    ctsUrns: [],
    passageCount: 0,
  };

  try {
    // Ensure answer is a string
    const safeAnswer = typeof answer === 'string' ? answer : '';
    const safeNodes = Array.isArray(nodes) ? nodes : [];
    const safeEdges = Array.isArray(edges) ? edges : [];

    if (!safeAnswer) {
      logger.warn('buildEvidencePackage: No answer provided, returning empty package');
      return emptyPackage;
    }

    logger.info(`Building evidence package from ${safeNodes.length} nodes`);

    // Identify passage nodes and build ancient citations
    const ancientCitations: AncientCitation[] = [];
    const ctsUrns: string[] = [];
    let passageCount = 0;

    for (const nodeResult of safeNodes) {
      const node = nodeResult?.payload || nodeResult;
      if (!node) continue;

      try {
        if (isPassageNode(node)) {
          passageCount++;
          const citation = buildAncientCitation(node, nodeResult?.score || 0.8);
          ancientCitations.push(citation);

          if (citation.ctsUrn) {
            ctsUrns.push(citation.ctsUrn);
          }
        }
      } catch (nodeError) {
        logger.warn(`Error processing node: ${nodeError}`);
      }
    }

    // Extract modern citations from answer
    const modernCitations = extractModernCitations(safeAnswer);

    // Build evidence chains
    const evidenceChains = buildEvidenceChains(safeAnswer, safeNodes, ancientCitations, modernCitations);

    logger.info(`Evidence package: ${ancientCitations.length} ancient, ${modernCitations.length} modern, ${evidenceChains.length} chains, ${ctsUrns.length} URNs`);

    return {
      ancientCitations,
      modernCitations,
      evidenceChains,
      ctsUrns,
      passageCount,
    };
  } catch (error) {
    logger.error(`Error building evidence package: ${error}`);
    return emptyPackage;
  }
}
