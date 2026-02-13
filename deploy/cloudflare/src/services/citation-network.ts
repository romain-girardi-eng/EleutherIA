/**
 * Citation Network Analytics Service
 *
 * Analyzes influence patterns and citation networks in the knowledge graph.
 * Implements PageRank-based influence scoring, community detection, and temporal analysis.
 */

import { DatabaseService } from './database';
import { getLogger } from '../utils/logger';

const logger = getLogger('CitationNetworkAnalyzer');

interface Node {
  id: string;
  label: string;
  node_type: string;
  description?: string;
  period?: string;
  school?: string;
  century_start?: string;
  century_end?: string;
}

interface Edge {
  source_id: string;
  target_id: string;
  edge_type: string;
  weight: number;
  metadata?: Record<string, any>;
}

interface InfluentialNode {
  id: string;
  label: string;
  type: string;
  period: string;
  school: string;
  influence_score: number;
  in_degree: number;
  out_degree: number;
}

interface BridgeFigure {
  id: string;
  label: string;
  type: string;
  school: string;
  period: string;
  connected_schools: string[];
  connected_periods: string[];
  bridge_score: number;
}

export class CitationNetworkAnalyzer {
  private db: DatabaseService;
  private nodes: Map<string, Node> = new Map();
  private edges: Edge[] = [];

  constructor(db: DatabaseService) {
    this.db = db;
  }

  /**
   * Load knowledge graph data from database
   */
  async loadGraphData(): Promise<void> {
    logger.info('Loading graph data for citation network analysis');

    // Load nodes
    const nodesQuery = `
      SELECT
        node_id as id,
        label,
        type as node_type,
        description,
        COALESCE(period, metadata->>'period') as period,
        metadata->>'school' as school,
        metadata->>'century_start' as century_start,
        metadata->>'century_end' as century_end
      FROM public.kg_nodes
    `;

    const nodesResult = await this.db.query<Node>(nodesQuery);
    this.nodes = new Map(nodesResult.map(node => [node.id, node]));

    // Load edges (citations/influences)
    const edgesQuery = `
      SELECT
        source_id,
        target_id,
        relation as edge_type,
        COALESCE((metadata->>'weight')::float, 1.0) as weight,
        metadata
      FROM public.kg_edges
      WHERE relation IN ('cites', 'influences', 'responds_to', 'develops', 'critiques')
    `;

    this.edges = await this.db.query<Edge>(edgesQuery);

    logger.info(`Loaded ${this.nodes.size} nodes and ${this.edges.length} edges`);
  }

  /**
   * Calculate influence scores using simplified PageRank algorithm
   */
  calculateInfluenceScores(): Record<string, number> {
    if (this.nodes.size === 0) {
      return {};
    }

    // Initialize scores
    const scores: Record<string, number> = {};
    for (const nodeId of this.nodes.keys()) {
      scores[nodeId] = 1.0 / this.nodes.size;
    }

    // Build adjacency lists
    const outgoing: Record<string, string[]> = {};
    const incoming: Record<string, string[]> = {};

    for (const nodeId of this.nodes.keys()) {
      outgoing[nodeId] = [];
      incoming[nodeId] = [];
    }

    for (const edge of this.edges) {
      if (this.nodes.has(edge.source_id) && this.nodes.has(edge.target_id)) {
        outgoing[edge.source_id].push(edge.target_id);
        incoming[edge.target_id].push(edge.source_id);
      }
    }

    // PageRank iterations
    const damping = 0.85;
    const iterations = 20;

    for (let i = 0; i < iterations; i++) {
      const newScores: Record<string, number> = {};

      for (const nodeId of this.nodes.keys()) {
        // Base score from random jump
        let rank = (1 - damping) / this.nodes.size;

        // Add contributions from incoming links
        for (const source of incoming[nodeId]) {
          if (outgoing[source].length > 0) {
            rank += (damping * scores[source]) / outgoing[source].length;
          }
        }

        newScores[nodeId] = rank;
      }

      Object.assign(scores, newScores);
    }

    // Normalize to 0-100 scale
    const maxScore = Math.max(...Object.values(scores));
    const normalized: Record<string, number> = {};

    for (const [nodeId, score] of Object.entries(scores)) {
      normalized[nodeId] = Math.round((score / maxScore) * 100 * 100) / 100;
    }

    return normalized;
  }

  /**
   * Get top N most influential nodes with metadata
   */
  getTopInfluential(n: number = 20): InfluentialNode[] {
    const scores = this.calculateInfluenceScores();

    // Sort by score
    const sortedNodes = Object.entries(scores)
      .sort(([, a], [, b]) => b - a)
      .slice(0, n);

    const results: InfluentialNode[] = [];

    for (const [nodeId, score] of sortedNodes) {
      const node = this.nodes.get(nodeId);
      if (!node) continue;

      const inDegree = this.edges.filter(e => e.target_id === nodeId).length;
      const outDegree = this.edges.filter(e => e.source_id === nodeId).length;

      results.push({
        id: nodeId,
        label: node.label || 'Unknown',
        type: node.node_type || 'unknown',
        period: node.period || 'Unknown',
        school: node.school || 'Unknown',
        influence_score: score,
        in_degree: inDegree,
        out_degree: outDegree,
      });
    }

    return results;
  }

  /**
   * Detect citation clusters using label propagation community detection
   */
  detectCitationClusters(): string[][] {
    if (this.nodes.size === 0 || this.edges.length === 0) {
      return [];
    }

    // Build undirected adjacency
    const neighbors: Record<string, Set<string>> = {};
    for (const nodeId of this.nodes.keys()) {
      neighbors[nodeId] = new Set();
    }

    for (const edge of this.edges) {
      if (neighbors[edge.source_id] && neighbors[edge.target_id]) {
        neighbors[edge.source_id].add(edge.target_id);
        neighbors[edge.target_id].add(edge.source_id);
      }
    }

    // Label propagation for community detection
    const labels: Record<string, number> = {};
    let labelId = 0;
    for (const nodeId of this.nodes.keys()) {
      labels[nodeId] = labelId++;
    }

    // Iterate
    for (let iter = 0; iter < 10; iter++) {
      let changed = false;

      for (const nodeId of this.nodes.keys()) {
        if (neighbors[nodeId].size === 0) continue;

        // Find most common label among neighbors
        const neighborLabels: number[] = [];
        for (const neighbor of neighbors[nodeId]) {
          neighborLabels.push(labels[neighbor]);
        }

        if (neighborLabels.length > 0) {
          const labelCounts: Record<number, number> = {};
          for (const label of neighborLabels) {
            labelCounts[label] = (labelCounts[label] || 0) + 1;
          }

          const mostCommon = Object.entries(labelCounts)
            .sort(([, a], [, b]) => b - a)[0][0];
          const mostCommonLabel = parseInt(mostCommon);

          if (labels[nodeId] !== mostCommonLabel) {
            labels[nodeId] = mostCommonLabel;
            changed = true;
          }
        }
      }

      if (!changed) break;
    }

    // Group nodes by label
    const clusters: Record<number, string[]> = {};
    for (const [nodeId, label] of Object.entries(labels)) {
      if (!clusters[label]) {
        clusters[label] = [];
      }
      clusters[label].push(nodeId);
    }

    // Filter single-node clusters and sort by size
    const result = Object.values(clusters)
      .filter(cluster => cluster.length > 1)
      .sort((a, b) => b.length - a.length)
      .slice(0, 10);

    return result;
  }

  /**
   * Find bridge figures connecting different schools/periods
   */
  findBridgeFigures(): BridgeFigure[] {
    const bridges: BridgeFigure[] = [];

    for (const [nodeId, nodeData] of this.nodes.entries()) {
      const connectedSchools = new Set<string>();
      const connectedPeriods = new Set<string>();

      for (const edge of this.edges) {
        let partnerId: string | null = null;

        if (edge.source_id === nodeId) {
          partnerId = edge.target_id;
        } else if (edge.target_id === nodeId) {
          partnerId = edge.source_id;
        }

        if (partnerId && this.nodes.has(partnerId)) {
          const partner = this.nodes.get(partnerId)!;
          if (partner.school) connectedSchools.add(partner.school);
          if (partner.period) connectedPeriods.add(partner.period);
        }
      }

      const schoolDiversity = connectedSchools.size;
      const periodDiversity = connectedPeriods.size;

      // Node is a bridge if it connects 3+ schools or periods
      if (schoolDiversity >= 3 || periodDiversity >= 3) {
        bridges.push({
          id: nodeId,
          label: nodeData.label || 'Unknown',
          type: nodeData.node_type || 'unknown',
          school: nodeData.school || 'Unknown',
          period: nodeData.period || 'Unknown',
          connected_schools: Array.from(connectedSchools),
          connected_periods: Array.from(connectedPeriods),
          bridge_score: schoolDiversity + periodDiversity,
        });
      }
    }

    // Sort by bridge score
    bridges.sort((a, b) => b.bridge_score - a.bridge_score);
    return bridges.slice(0, 15);
  }

  /**
   * Track how influence changes over centuries
   */
  temporalInfluenceFlow(): Record<string, Record<string, number>> {
    // Group nodes by century
    const byCentury: Record<number, string[]> = {};

    for (const [nodeId, nodeData] of this.nodes.entries()) {
      if (nodeData.century_start) {
        try {
          const century = parseInt(nodeData.century_start);
          if (!byCentury[century]) {
            byCentury[century] = [];
          }
          byCentury[century].push(nodeId);
        } catch (e) {
          // Skip invalid century values
        }
      }
    }

    // Calculate influence for each century's nodes
    const allScores = this.calculateInfluenceScores();
    const result: Record<string, Record<string, number>> = {};

    const sortedCenturies = Object.keys(byCentury)
      .map(c => parseInt(c))
      .sort((a, b) => a - b);

    for (const century of sortedCenturies) {
      const centuryNodes = byCentury[century];
      const centuryScores: Record<string, number> = {};

      for (const nodeId of centuryNodes) {
        centuryScores[nodeId] = allScores[nodeId] || 0;
      }

      // Keep top 5 per century
      const sorted = Object.entries(centuryScores)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5);

      result[century.toString()] = Object.fromEntries(sorted);
    }

    return result;
  }

  /**
   * Export network data in Gephi-compatible format
   */
  exportForGephi() {
    const gephiNodes = [];
    for (const [nodeId, nodeData] of this.nodes.entries()) {
      gephiNodes.push({
        id: nodeId,
        label: nodeData.label || 'Unknown',
        type: nodeData.node_type || 'unknown',
        period: nodeData.period || '',
        school: nodeData.school || '',
      });
    }

    const gephiEdges = this.edges.map((edge, i) => ({
      id: `e${i}`,
      source: edge.source_id,
      target: edge.target_id,
      type: edge.edge_type,
      weight: edge.weight,
    }));

    return {
      nodes: gephiNodes,
      edges: gephiEdges,
      metadata: {
        node_count: gephiNodes.length,
        edge_count: gephiEdges.length,
        format: 'gephi_graphml',
      },
    };
  }

  /**
   * Get complete citation network analysis
   */
  async getFullAnalysis() {
    await this.loadGraphData();

    logger.info('Running full citation network analysis');

    const clusters = this.detectCitationClusters();

    const analysis = {
      summary: {
        total_nodes: this.nodes.size,
        total_edges: this.edges.length,
        edge_types: Array.from(new Set(this.edges.map(e => e.edge_type))),
      },
      top_influential: this.getTopInfluential(20),
      clusters: clusters.map((cluster, i) => ({
        id: i,
        size: cluster.length,
        nodes: cluster.slice(0, 10),
        sample_labels: cluster
          .slice(0, 5)
          .map(nodeId => this.nodes.get(nodeId)?.label || 'Unknown'),
      })),
      bridges: this.findBridgeFigures(),
      temporal_flow: this.temporalInfluenceFlow(),
    };

    logger.info(
      `Analysis complete - ${analysis.clusters.length} clusters, ${analysis.bridges.length} bridges`
    );

    return analysis;
  }
}
