/**
 * Debate Intensity Scoring Service
 *
 * Scores philosophical debates based on conflict edges, temporal span,
 * school diversity, and philosopher centrality.
 *
 * This is a domain-specific innovation unique to EleutherIA.
 */

import { getLogger } from '../utils/logger';

const logger = getLogger('DebateScorer');

export interface DebateNode {
  id: string;
  label: string;
  type: string;
  school?: string;
  period?: string;
}

export interface DebateEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
}

export interface DebateScore {
  score: number;                    // 0-1 intensity
  level: 'MAJOR' | 'SIGNIFICANT' | 'MINOR';
  schools: string[];                // Schools involved
  periods: string[];                // Historical periods spanned
  keyFigures: string[];             // Central philosophers
  conflictCount: number;            // Number of conflict edges
  metrics: DebateMetrics;
}

export interface DebateMetrics {
  conflictIntensity: number;        // Weight from conflict edges
  temporalSpan: number;             // How many periods
  schoolDiversity: number;          // How many schools
  philosopherCentrality: number;    // Key figures involvement
}

export interface IdentifiedDebate {
  topic: string;
  description: string;
  score: DebateScore;
  nodes: DebateNode[];
  edges: DebateEdge[];
}

// Conflict relation types (direct disagreement)
const CONFLICT_RELATIONS = [
  'criticized', 'refuted', 'opposed', 'rejected', 'disputed',
  'attacked', 'challenged', 'contradicted', 'denied', 'countered',
  'polemicized_against', 'disagreed_with', 'argued_against',
];

// Period ordering for temporal span calculation
const PERIOD_ORDER: Record<string, number> = {
  'Presocratic': 1,
  'Classical': 2,
  'Hellenistic': 3,
  'Imperial': 4,
  'Late Antiquity': 5,
  'Early Christian': 5,
  'Medieval': 6,
};

/**
 * Score the intensity of a philosophical debate
 */
export function scoreDebateIntensity(
  nodes: DebateNode[],
  edges: DebateEdge[]
): DebateScore {
  // Count conflict edges
  const conflictEdges = edges.filter(e =>
    CONFLICT_RELATIONS.some(r => e.relation.toLowerCase().includes(r))
  );

  // Extract unique schools
  const schools = new Set<string>();
  for (const node of nodes) {
    if (node.school) schools.add(node.school);
  }

  // Extract unique periods
  const periods = new Set<string>();
  for (const node of nodes) {
    if (node.period) periods.add(node.period);
  }

  // Extract key figures (person-type nodes)
  const keyFigures = nodes
    .filter(n => n.type === 'person' || n.type === 'philosopher')
    .map(n => n.label);

  // Calculate metrics
  const conflictIntensity = Math.min(conflictEdges.length * 0.15, 1.0);
  const temporalSpan = calculateTemporalSpan(Array.from(periods));
  const schoolDiversity = Math.min(schools.size * 0.2, 1.0);
  const philosopherCentrality = Math.min(keyFigures.length * 0.1, 1.0);

  // Weighted combination
  const score =
    conflictIntensity * 0.4 +
    temporalSpan * 0.25 +
    schoolDiversity * 0.2 +
    philosopherCentrality * 0.15;

  // Determine level
  let level: 'MAJOR' | 'SIGNIFICANT' | 'MINOR';
  if (score >= 0.7) {
    level = 'MAJOR';
  } else if (score >= 0.4) {
    level = 'SIGNIFICANT';
  } else {
    level = 'MINOR';
  }

  const result: DebateScore = {
    score,
    level,
    schools: Array.from(schools),
    periods: Array.from(periods),
    keyFigures,
    conflictCount: conflictEdges.length,
    metrics: {
      conflictIntensity,
      temporalSpan,
      schoolDiversity,
      philosopherCentrality,
    },
  };

  logger.info(`Debate scored: ${level} (${score.toFixed(2)}), ${conflictEdges.length} conflicts, ${schools.size} schools`);

  return result;
}

/**
 * Calculate temporal span (0-1)
 */
function calculateTemporalSpan(periods: string[]): number {
  if (periods.length === 0) return 0;
  if (periods.length === 1) return 0.2;

  const orderValues = periods
    .map(p => PERIOD_ORDER[p] || 0)
    .filter(v => v > 0);

  if (orderValues.length < 2) return 0.2;

  const minOrder = Math.min(...orderValues);
  const maxOrder = Math.max(...orderValues);
  const span = maxOrder - minOrder;

  // Normalize to 0-1 (max span is 5 periods)
  return Math.min(span / 5, 1.0);
}

/**
 * Identify distinct debates within a set of nodes/edges
 */
export function identifyDebates(
  nodes: DebateNode[],
  edges: DebateEdge[]
): IdentifiedDebate[] {
  const debates: IdentifiedDebate[] = [];

  // Group by connected conflict clusters
  const conflictEdges = edges.filter(e =>
    CONFLICT_RELATIONS.some(r => e.relation.toLowerCase().includes(r))
  );

  if (conflictEdges.length === 0) {
    return debates;
  }

  // Find connected components of conflict edges
  const nodeToDebate = new Map<string, number>();
  let debateId = 0;

  for (const edge of conflictEdges) {
    const sourceDebate = nodeToDebate.get(edge.source);
    const targetDebate = nodeToDebate.get(edge.target);

    if (sourceDebate === undefined && targetDebate === undefined) {
      // New debate cluster
      nodeToDebate.set(edge.source, debateId);
      nodeToDebate.set(edge.target, debateId);
      debateId++;
    } else if (sourceDebate !== undefined && targetDebate === undefined) {
      nodeToDebate.set(edge.target, sourceDebate);
    } else if (sourceDebate === undefined && targetDebate !== undefined) {
      nodeToDebate.set(edge.source, targetDebate);
    } else if (sourceDebate !== targetDebate) {
      // Merge debates (smaller into larger)
      const minDebate = Math.min(sourceDebate!, targetDebate!);
      for (const [nodeId, d] of nodeToDebate) {
        if (d === sourceDebate || d === targetDebate) {
          nodeToDebate.set(nodeId, minDebate);
        }
      }
    }
  }

  // Group nodes/edges by debate
  const debateClusters = new Map<number, { nodes: DebateNode[]; edges: DebateEdge[] }>();
  const nodeMap = new Map<string, DebateNode>();

  for (const node of nodes) {
    nodeMap.set(node.id, node);
  }

  for (const edge of conflictEdges) {
    const debateNum = nodeToDebate.get(edge.source) || nodeToDebate.get(edge.target);
    if (debateNum === undefined) continue;

    if (!debateClusters.has(debateNum)) {
      debateClusters.set(debateNum, { nodes: [], edges: [] });
    }

    const cluster = debateClusters.get(debateNum)!;
    cluster.edges.push(edge);

    const sourceNode = nodeMap.get(edge.source);
    const targetNode = nodeMap.get(edge.target);
    if (sourceNode && !cluster.nodes.find(n => n.id === edge.source)) {
      cluster.nodes.push(sourceNode);
    }
    if (targetNode && !cluster.nodes.find(n => n.id === edge.target)) {
      cluster.nodes.push(targetNode);
    }
  }

  // Create IdentifiedDebate objects
  for (const [, cluster] of debateClusters) {
    if (cluster.edges.length === 0) continue;

    const score = scoreDebateIntensity(cluster.nodes, cluster.edges);

    // Generate topic from key figures/schools
    const topic = generateDebateTopic(cluster.nodes, score);
    const description = generateDebateDescription(cluster.nodes, cluster.edges, score);

    debates.push({
      topic,
      description,
      score,
      nodes: cluster.nodes,
      edges: cluster.edges,
    });
  }

  // Sort by intensity
  debates.sort((a, b) => b.score.score - a.score.score);

  logger.info(`Identified ${debates.length} distinct debates`);

  return debates;
}

/**
 * Generate debate topic from nodes
 */
function generateDebateTopic(nodes: DebateNode[], score: DebateScore): string {
  const schools = score.schools;
  const figures = score.keyFigures.slice(0, 2);

  if (schools.length >= 2) {
    return `${schools[0]} vs ${schools[1]} Debate`;
  }

  if (figures.length >= 2) {
    return `${figures[0]} vs ${figures[1]}`;
  }

  if (schools.length === 1) {
    return `${schools[0]} Internal Debate`;
  }

  const conceptNodes = nodes.filter(n => n.type === 'concept');
  if (conceptNodes.length > 0) {
    return `Debate on ${conceptNodes[0].label}`;
  }

  return 'Philosophical Debate';
}

/**
 * Generate debate description
 */
function generateDebateDescription(
  nodes: DebateNode[],
  edges: DebateEdge[],
  score: DebateScore
): string {
  const parts: string[] = [];

  // Level description
  if (score.level === 'MAJOR') {
    parts.push('A major philosophical controversy');
  } else if (score.level === 'SIGNIFICANT') {
    parts.push('A significant philosophical disagreement');
  } else {
    parts.push('A philosophical discussion');
  }

  // Schools involved
  if (score.schools.length > 0) {
    parts.push(`involving ${score.schools.join(', ')} philosophers`);
  }

  // Key figures
  if (score.keyFigures.length > 0) {
    parts.push(`with key contributions from ${score.keyFigures.slice(0, 3).join(', ')}`);
  }

  // Temporal span
  if (score.periods.length > 1) {
    parts.push(`spanning from the ${score.periods[0]} to ${score.periods[score.periods.length - 1]} period`);
  }

  return parts.join(' ') + '.';
}

/**
 * Get debate level emoji
 */
export function getDebateEmoji(level: 'MAJOR' | 'SIGNIFICANT' | 'MINOR'): string {
  switch (level) {
    case 'MAJOR': return '🔥';
    case 'SIGNIFICANT': return '⚡';
    case 'MINOR': return '💭';
  }
}

/**
 * Format debate for display
 */
export function formatDebateForDisplay(debate: IdentifiedDebate): string {
  const emoji = getDebateEmoji(debate.score.level);
  return `${emoji} ${debate.topic} (${debate.score.level})\n${debate.description}`;
}
