/**
 * Evidence Chain Tracing Service
 *
 * Explains WHY each source was selected, building trust through transparency.
 * Traces evidence from query → semantic search → graph expansion → final selection.
 */

import { getLogger } from '../utils/logger';

const logger = getLogger('EvidenceTracer');

export interface SelectionStep {
  method: 'semantic_search' | 'graph_expansion' | 'community_context' | 'hyde' | 'query_expansion' | 'reranking' | 'crag';
  score?: number;
  relation?: string;
  reason: string;
  timestamp: number;
}

export interface EvidenceTrace {
  nodeId: string;
  nodeLabel: string;
  nodeType: string;
  school?: string;
  selectionPath: SelectionStep[];
  finalScore: number;
  confidenceLevel: 'high' | 'medium' | 'low';
}

export interface EvidenceTraceResult {
  traces: EvidenceTrace[];
  summary: string;
  totalSources: number;
  methodBreakdown: Record<string, number>;
  tracingTime: number;
}

/**
 * Build evidence trace for selected nodes
 */
export function buildEvidenceTraces(
  selectedNodes: any[],
  searchScores: Map<string, number>,
  graphExpansions: Map<string, { relation: string; sourceNode: string }>,
  communityInfo: Map<string, string>,
  hydeUsed: boolean,
  queryExpansionUsed: boolean,
  rerankingScores?: Map<string, number>,
  query: string = ''
): EvidenceTraceResult {
  const startTime = Date.now();
  const traces: EvidenceTrace[] = [];
  const methodCount: Record<string, number> = {};

  for (const node of selectedNodes) {
    const nodeId = node.node_id || node.id;
    const selectionPath: SelectionStep[] = [];

    // Step 1: Initial retrieval method
    const searchScore = searchScores.get(nodeId);
    if (searchScore !== undefined) {
      if (hydeUsed) {
        selectionPath.push({
          method: 'hyde',
          score: searchScore,
          reason: `Matched hypothetical document embedding (score: ${searchScore.toFixed(3)})`,
          timestamp: Date.now(),
        });
        methodCount['hyde'] = (methodCount['hyde'] || 0) + 1;
      } else if (queryExpansionUsed) {
        selectionPath.push({
          method: 'query_expansion',
          score: searchScore,
          reason: `Matched expanded query terms (score: ${searchScore.toFixed(3)})`,
          timestamp: Date.now(),
        });
        methodCount['query_expansion'] = (methodCount['query_expansion'] || 0) + 1;
      } else {
        selectionPath.push({
          method: 'semantic_search',
          score: searchScore,
          reason: `Semantic similarity to query "${query.slice(0, 50)}..." (score: ${searchScore.toFixed(3)})`,
          timestamp: Date.now(),
        });
        methodCount['semantic_search'] = (methodCount['semantic_search'] || 0) + 1;
      }
    }

    // Step 2: Graph expansion (if applicable)
    const expansion = graphExpansions.get(nodeId);
    if (expansion) {
      selectionPath.push({
        method: 'graph_expansion',
        relation: expansion.relation,
        reason: `Connected via "${expansion.relation}" from ${expansion.sourceNode}`,
        timestamp: Date.now(),
      });
      methodCount['graph_expansion'] = (methodCount['graph_expansion'] || 0) + 1;
    }

    // Step 3: Community context (if applicable)
    const community = communityInfo.get(nodeId);
    if (community) {
      selectionPath.push({
        method: 'community_context',
        reason: `Part of "${community}" thematic cluster`,
        timestamp: Date.now(),
      });
      methodCount['community_context'] = (methodCount['community_context'] || 0) + 1;
    }

    // Step 4: Reranking (if applicable)
    const rerankScore = rerankingScores?.get(nodeId);
    if (rerankScore !== undefined) {
      selectionPath.push({
        method: 'reranking',
        score: rerankScore,
        reason: `Reranked for relevance (score: ${rerankScore}/100)`,
        timestamp: Date.now(),
      });
      methodCount['reranking'] = (methodCount['reranking'] || 0) + 1;
    }

    // Calculate final score and confidence
    const finalScore = rerankScore !== undefined
      ? rerankScore / 100
      : searchScore || 0.5;

    let confidenceLevel: 'high' | 'medium' | 'low';
    if (finalScore >= 0.8 || selectionPath.length >= 3) {
      confidenceLevel = 'high';
    } else if (finalScore >= 0.5 || selectionPath.length >= 2) {
      confidenceLevel = 'medium';
    } else {
      confidenceLevel = 'low';
    }

    traces.push({
      nodeId,
      nodeLabel: node.name || node.label || nodeId,
      nodeType: node.type || 'concept',
      school: node.school,
      selectionPath,
      finalScore,
      confidenceLevel,
    });
  }

  // Generate summary
  const summary = generateTraceSummary(traces, methodCount);

  const result: EvidenceTraceResult = {
    traces,
    summary,
    totalSources: traces.length,
    methodBreakdown: methodCount,
    tracingTime: Date.now() - startTime,
  };

  logger.info(`Built ${traces.length} evidence traces in ${result.tracingTime}ms`);

  return result;
}

/**
 * Generate summary of evidence tracing
 */
function generateTraceSummary(
  traces: EvidenceTrace[],
  methodCount: Record<string, number>
): string {
  const parts: string[] = [];

  // Count confidence levels
  const highConf = traces.filter(t => t.confidenceLevel === 'high').length;
  const medConf = traces.filter(t => t.confidenceLevel === 'medium').length;
  const lowConf = traces.filter(t => t.confidenceLevel === 'low').length;

  parts.push(`Selected ${traces.length} sources:`);

  if (highConf > 0) {
    parts.push(`${highConf} high-confidence`);
  }
  if (medConf > 0) {
    parts.push(`${medConf} medium-confidence`);
  }
  if (lowConf > 0) {
    parts.push(`${lowConf} low-confidence`);
  }

  // Method breakdown
  const methods = Object.entries(methodCount)
    .sort((a, b) => b[1] - a[1])
    .map(([method, count]) => `${method.replace('_', ' ')}: ${count}`)
    .join(', ');

  if (methods) {
    parts.push(`Methods: ${methods}`);
  }

  return parts.join('. ');
}

/**
 * Format trace for display
 */
export function formatTraceForDisplay(trace: EvidenceTrace): string {
  const lines: string[] = [];

  lines.push(`📚 ${trace.nodeLabel}`);
  lines.push(`   Type: ${trace.nodeType}${trace.school ? `, School: ${trace.school}` : ''}`);
  lines.push(`   Confidence: ${trace.confidenceLevel.toUpperCase()}`);
  lines.push(`   Selection path:`);

  for (const step of trace.selectionPath) {
    const icon = getMethodIcon(step.method);
    lines.push(`     ${icon} ${step.reason}`);
  }

  return lines.join('\n');
}

/**
 * Get icon for selection method
 */
function getMethodIcon(method: string): string {
  switch (method) {
    case 'semantic_search': return '🔍';
    case 'hyde': return '💡';
    case 'query_expansion': return '📖';
    case 'graph_expansion': return '🔗';
    case 'community_context': return '🏘️';
    case 'reranking': return '⭐';
    case 'crag': return '✅';
    default: return '•';
  }
}

/**
 * Create trace for CRAG validation
 */
export function createCRAGTrace(
  nodeId: string,
  validated: boolean,
  confidence: number
): SelectionStep {
  return {
    method: 'crag',
    score: confidence / 100,
    reason: validated
      ? `Validated by CRAG (confidence: ${confidence}%)`
      : `Recovered via secondary retrieval (CRAG confidence: ${confidence}%)`,
    timestamp: Date.now(),
  };
}

/**
 * Aggregate traces by school
 */
export function aggregateBySchool(traces: EvidenceTrace[]): Map<string, EvidenceTrace[]> {
  const bySchool = new Map<string, EvidenceTrace[]>();

  for (const trace of traces) {
    const school = trace.school || 'Unknown';
    if (!bySchool.has(school)) {
      bySchool.set(school, []);
    }
    bySchool.get(school)!.push(trace);
  }

  return bySchool;
}

/**
 * Get confidence color for UI
 */
export function getConfidenceColor(level: 'high' | 'medium' | 'low'): string {
  switch (level) {
    case 'high': return '#22c55e';   // green
    case 'medium': return '#f59e0b'; // amber
    case 'low': return '#ef4444';    // red
  }
}

/**
 * Calculate overall evidence quality
 */
export function calculateEvidenceQuality(traces: EvidenceTrace[]): {
  overallScore: number;
  badge: 'Excellent' | 'Good' | 'Fair' | 'Poor';
  explanation: string;
} {
  if (traces.length === 0) {
    return {
      overallScore: 0,
      badge: 'Poor',
      explanation: 'No sources found.',
    };
  }

  // Weighted average based on confidence
  const weights = { high: 1.0, medium: 0.7, low: 0.4 };
  let totalWeight = 0;
  let weightedScore = 0;

  for (const trace of traces) {
    const weight = weights[trace.confidenceLevel];
    totalWeight += weight;
    weightedScore += trace.finalScore * weight;
  }

  const overallScore = totalWeight > 0 ? weightedScore / totalWeight : 0;

  let badge: 'Excellent' | 'Good' | 'Fair' | 'Poor';
  let explanation: string;

  if (overallScore >= 0.8 && traces.length >= 5) {
    badge = 'Excellent';
    explanation = 'Strong evidence from multiple high-quality sources.';
  } else if (overallScore >= 0.6 && traces.length >= 3) {
    badge = 'Good';
    explanation = 'Solid evidence with good source coverage.';
  } else if (overallScore >= 0.4 || traces.length >= 2) {
    badge = 'Fair';
    explanation = 'Moderate evidence; some sources may be tangential.';
  } else {
    badge = 'Poor';
    explanation = 'Limited evidence; answer reliability is uncertain.';
  }

  return { overallScore, badge, explanation };
}
