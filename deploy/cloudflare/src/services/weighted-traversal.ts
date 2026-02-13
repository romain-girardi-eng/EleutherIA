/**
 * Weighted Graph Traversal — priority-queue BFS with edge/node scoring.
 *
 * Ported from Python's WeightedTraversal class. Replaces naive BFS with
 * Dijkstra-like expansion considering edge weights, edge type relevance,
 * and target node centrality (PageRank).
 */

import { getLogger } from '../utils/logger';

const logger = getLogger('WeightedTraversal');

// ============================================================================
// Edge-type relevance multipliers by category
// ============================================================================

const EDGE_CATEGORY_MULTIPLIERS: Record<string, number> = {
  argumentative: 1.5,
  intellectual: 1.2,
  doctrinal: 1.3,
  semantic: 1.1,
  authorship: 1.0,
  textual: 1.0,
  citation: 0.9,
  structural: 0.7,
  affiliation: 0.8,
  hermeneutic: 0.6,
  debate: 1.0,
  temporal: 0.5,
};

const RELATION_TO_CATEGORY: Record<string, string> = {
  argues_for: 'argumentative',
  argues_against: 'argumentative',
  refutes: 'argumentative',
  responds_to: 'argumentative',
  influences: 'intellectual',
  influenced_by: 'intellectual',
  taught_by: 'intellectual',
  teaches: 'intellectual',
  belongs_to_school: 'affiliation',
  has_member: 'affiliation',
  founded: 'affiliation',
  founded_by: 'affiliation',
  wrote: 'authorship',
  authored_by: 'authorship',
  cites: 'citation',
  cited_by: 'citation',
  preserves: 'textual',
  preserved_in: 'textual',
  contains: 'structural',
  part_of: 'structural',
  discusses: 'semantic',
  discussed_in: 'semantic',
  defines: 'semantic',
  defined_by: 'semantic',
  related_to: 'semantic',
  contrasts_with: 'semantic',
  holds_position: 'doctrinal',
  endorses: 'doctrinal',
  rejects: 'doctrinal',
  participates_in: 'debate',
  has_participant: 'debate',
  interprets: 'hermeneutic',
  interpreted_by: 'hermeneutic',
  contemporary_of: 'temporal',
  precedes: 'temporal',
  follows: 'temporal',
};

// ============================================================================
// Types
// ============================================================================

export interface TraversalNode {
  id: string;
  label?: string;
  type?: string;
  [key: string]: any;
}

export interface TraversalEdge {
  source: string;
  target: string;
  relation?: string;
  weight?: number;
  [key: string]: any;
}

// ============================================================================
// Min-Heap (priority queue) implementation
// ============================================================================

class MinHeap {
  private heap: Array<[number, string]> = [];

  push(score: number, nodeId: string): void {
    this.heap.push([score, nodeId]);
    this.bubbleUp(this.heap.length - 1);
  }

  pop(): [number, string] | undefined {
    if (this.heap.length === 0) return undefined;
    const top = this.heap[0];
    const last = this.heap.pop()!;
    if (this.heap.length > 0) {
      this.heap[0] = last;
      this.sinkDown(0);
    }
    return top;
  }

  get size(): number {
    return this.heap.length;
  }

  private bubbleUp(i: number): void {
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (this.heap[parent][0] <= this.heap[i][0]) break;
      [this.heap[parent], this.heap[i]] = [this.heap[i], this.heap[parent]];
      i = parent;
    }
  }

  private sinkDown(i: number): void {
    const n = this.heap.length;
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < n && this.heap[left][0] < this.heap[smallest][0]) smallest = left;
      if (right < n && this.heap[right][0] < this.heap[smallest][0]) smallest = right;
      if (smallest === i) break;
      [this.heap[smallest], this.heap[i]] = [this.heap[i], this.heap[smallest]];
      i = smallest;
    }
  }
}

// ============================================================================
// WeightedTraversal
// ============================================================================

export class WeightedTraversal {
  private nodeLookup: Map<string, TraversalNode>;
  private outgoingEdges: Map<string, TraversalEdge[]>;
  private incomingEdges: Map<string, TraversalEdge[]>;
  private normPageRank: Map<string, number>;

  constructor(
    nodeLookup: Map<string, TraversalNode>,
    outgoingEdges: Map<string, TraversalEdge[]>,
    incomingEdges: Map<string, TraversalEdge[]>,
    pageRankScores?: Map<string, number>
  ) {
    this.nodeLookup = nodeLookup;
    this.outgoingEdges = outgoingEdges;
    this.incomingEdges = incomingEdges;

    // Normalise PageRank to [0, 1]
    this.normPageRank = new Map();
    if (pageRankScores && pageRankScores.size > 0) {
      let maxPR = 0;
      for (const score of pageRankScores.values()) {
        if (score > maxPR) maxPR = score;
      }
      maxPR = maxPR || 1.0;
      for (const [nid, score] of pageRankScores) {
        this.normPageRank.set(nid, score / maxPR);
      }
    }
  }

  /**
   * Expand from seed nodes using weighted priority-queue BFS.
   */
  expand(
    seedIds: string[],
    options: {
      edgeFilter?: Set<string>;
      maxNodes?: number;
      scoreThreshold?: number;
    } = {}
  ): Set<string> {
    const { edgeFilter, maxNodes = 30, scoreThreshold = 0.05 } = options;
    const visited = new Set<string>();
    const heap = new MinHeap();

    // Seeds get max score (use negative for min-heap → max priority)
    for (const nid of seedIds) {
      if (this.nodeLookup.has(nid)) {
        visited.add(nid);
        heap.push(-1.0, nid); // Negative because min-heap
      }
    }

    while (heap.size > 0 && visited.size < maxNodes) {
      const entry = heap.pop()!;
      const currentScore = -entry[0]; // Un-negate
      const nodeId = entry[1];

      if (currentScore < scoreThreshold) break;

      // Expand outgoing edges
      for (const edge of this.outgoingEdges.get(nodeId) || []) {
        const target = edge.target;
        if (visited.has(target) || !this.nodeLookup.has(target)) continue;
        const relation = edge.relation || '';
        if (edgeFilter && !edgeFilter.has(relation)) continue;

        const score = this.scoreEdge(edge, target, currentScore);
        if (score >= scoreThreshold) {
          visited.add(target);
          heap.push(-score, target);
        }
      }

      // Expand incoming edges
      for (const edge of this.incomingEdges.get(nodeId) || []) {
        const source = edge.source;
        if (visited.has(source) || !this.nodeLookup.has(source)) continue;
        const relation = edge.relation || '';
        if (edgeFilter && !edgeFilter.has(relation)) continue;

        const score = this.scoreEdge(edge, source, currentScore);
        if (score >= scoreThreshold) {
          visited.add(source);
          heap.push(-score, source);
        }
      }
    }

    logger.info(`WeightedTraversal: ${seedIds.length} seeds → ${visited.size} nodes visited`);
    return visited;
  }

  /**
   * Compute composite score for traversing an edge.
   * score = parentScore * edgeWeight * typeMultiplier * (0.5 + centrality) * decay
   */
  private scoreEdge(edge: TraversalEdge, targetId: string, parentScore: number): number {
    const edgeWeight = edge.weight ?? 1.0;
    const relation = edge.relation || '';
    const category = RELATION_TO_CATEGORY[relation] || 'semantic';
    const typeMultiplier = EDGE_CATEGORY_MULTIPLIERS[category] || 1.0;
    const centrality = this.normPageRank.get(targetId) || 0.0;
    const decay = 0.7;

    return parentScore * edgeWeight * typeMultiplier * (0.5 + centrality) * decay;
  }
}

export { EDGE_CATEGORY_MULTIPLIERS, RELATION_TO_CATEGORY };
