/**
 * Graph Data Store — shared loader for KG nodes, edges, and PageRank scores.
 *
 * Centralises data loading from Supabase + KV so that WeightedTraversal,
 * BridgeRetrievalService, and HierarchicalRetrieval can share a single
 * data source without redundant fetches.
 */

import { Env } from '../types';
import { TraversalNode, TraversalEdge } from './weighted-traversal';
import { getLogger } from '../utils/logger';

const logger = getLogger('GraphDataStore');

export interface GraphData {
  nodes: Map<string, TraversalNode>;
  outgoingEdges: Map<string, TraversalEdge[]>;
  incomingEdges: Map<string, TraversalEdge[]>;
  pageRankScores: Map<string, number>;
}

export class GraphDataStore {
  private env: Env;
  private data: GraphData | null = null;

  constructor(env: Env) {
    this.env = env;
  }

  /**
   * Load graph data (cached after first call).
   */
  async load(): Promise<GraphData> {
    if (this.data) return this.data;

    const [nodes, edges, pageRank] = await Promise.all([
      this.loadNodes(),
      this.loadEdges(),
      this.loadPageRank(),
    ]);

    // Build adjacency indices
    const outgoingEdges = new Map<string, TraversalEdge[]>();
    const incomingEdges = new Map<string, TraversalEdge[]>();

    for (const edge of edges) {
      if (!outgoingEdges.has(edge.source)) {
        outgoingEdges.set(edge.source, []);
      }
      outgoingEdges.get(edge.source)!.push(edge);

      if (!incomingEdges.has(edge.target)) {
        incomingEdges.set(edge.target, []);
      }
      incomingEdges.get(edge.target)!.push(edge);
    }

    this.data = {
      nodes,
      outgoingEdges,
      incomingEdges,
      pageRankScores: pageRank,
    };

    logger.info(`GraphDataStore loaded: ${nodes.size} nodes, ${edges.length} edges, ${pageRank.size} PageRank scores`);
    return this.data;
  }

  private async loadNodes(): Promise<Map<string, TraversalNode>> {
    const nodeMap = new Map<string, TraversalNode>();

    try {
      // Try KV cache first
      const cached = await this.env.TEXT_CACHE?.get('kg_nodes_index', 'json') as TraversalNode[] | null;
      if (cached && Array.isArray(cached)) {
        for (const node of cached) {
          nodeMap.set(node.id, node);
        }
        logger.info(`Loaded ${nodeMap.size} nodes from KV cache`);
        return nodeMap;
      }

      // Fallback to Supabase
      const url = `${this.env.SUPABASE_URL}/rest/v1/kg_nodes?select=id,label,type,school,period,description&limit=5000`;
      const response = await fetch(url, {
        headers: {
          'apikey': this.env.SUPABASE_KEY,
          'Authorization': `Bearer ${this.env.SUPABASE_KEY}`,
          'Accept-Profile': 'free_will',
        },
      });

      if (!response.ok) {
        logger.warn(`Failed to load nodes from Supabase: ${response.status}`);
        return nodeMap;
      }

      const nodes = await response.json() as any[];
      for (const node of nodes) {
        nodeMap.set(node.id, {
          id: node.id,
          label: node.label,
          type: node.type,
          school: node.school,
          period: node.period,
          description: node.description,
        });
      }

      logger.info(`Loaded ${nodeMap.size} nodes from Supabase`);
    } catch (error) {
      logger.error('Error loading nodes', error);
    }

    return nodeMap;
  }

  private async loadEdges(): Promise<TraversalEdge[]> {
    try {
      // Try KV cache first
      const cached = await this.env.TEXT_CACHE?.get('kg_edges_index', 'json') as TraversalEdge[] | null;
      if (cached && Array.isArray(cached)) {
        logger.info(`Loaded ${cached.length} edges from KV cache`);
        return cached;
      }

      // Fallback to Supabase
      const url = `${this.env.SUPABASE_URL}/rest/v1/kg_edges?select=source,target,relation,weight&limit=15000`;
      const response = await fetch(url, {
        headers: {
          'apikey': this.env.SUPABASE_KEY,
          'Authorization': `Bearer ${this.env.SUPABASE_KEY}`,
          'Accept-Profile': 'free_will',
        },
      });

      if (!response.ok) {
        logger.warn(`Failed to load edges from Supabase: ${response.status}`);
        return [];
      }

      const edges = await response.json() as any[];
      logger.info(`Loaded ${edges.length} edges from Supabase`);
      return edges.map(e => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
        weight: e.weight ?? 1.0,
      }));
    } catch (error) {
      logger.error('Error loading edges', error);
      return [];
    }
  }

  private async loadPageRank(): Promise<Map<string, number>> {
    const scores = new Map<string, number>();

    try {
      const cached = await this.env.TEXT_CACHE?.get('pagerank_scores', 'json') as Record<string, number> | null;
      if (cached) {
        for (const [nodeId, score] of Object.entries(cached)) {
          scores.set(nodeId, score);
        }
        logger.info(`Loaded ${scores.size} PageRank scores from KV`);
      }
    } catch (error) {
      logger.warn('PageRank scores not available', error);
    }

    return scores;
  }
}
