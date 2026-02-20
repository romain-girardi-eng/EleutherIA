/**
 * Qdrant Vector Database Service
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('QdrantService');

interface QdrantSearchResult {
  id: string | number;
  score: number;
  payload: Record<string, any>;
}

interface QdrantSearchResponse {
  result: QdrantSearchResult[];
}

export interface KGNodeWithVector {
  id: string | number;
  node_id: string;
  name: string;
  school: string;
  type: string;
  vector: number[];
}

export interface KGEdgePayload {
  id: string | number;
  edge_id: string;
  source_id: string;
  target_id: string;
  relation: string;
  description?: string;
  [key: string]: any;
}

export class QdrantService {
  private host: string;
  private apiKey: string;
  private baseUrl: string;

  constructor(env: Env) {
    this.host = env.QDRANT_HOST;
    this.apiKey = env.QDRANT_API_KEY;
    this.baseUrl = `https://${this.host}`;
  }

  private async request<T = any>(
    path: string,
    method: string = 'GET',
    body?: any
  ): Promise<T> {
    try {
      const url = `${this.baseUrl}${path}`;

      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          'api-key': this.apiKey,
        },
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Qdrant request failed: ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('Qdrant request error', error);
      throw error;
    }
  }

  /**
   * Search KG nodes by vector similarity
   */
  async searchNodes(
    queryVector: number[],
    limit: number = 10,
    scoreThreshold?: number
  ): Promise<QdrantSearchResult[]> {
    try {
      const searchParams: any = {
        vector: queryVector,
        limit: limit * 3, // Get more to filter KG nodes
        with_payload: true,
      };

      if (scoreThreshold) {
        searchParams.score_threshold = scoreThreshold;
      }

      const response = await this.request<QdrantSearchResponse>(
        '/collections/ancient_free_will_vectors/points/search',
        'POST',
        searchParams
      );

      // Filter to only KG nodes
      const kgResults = response.result
        .filter(hit => hit.payload && 'node_id' in hit.payload)
        .slice(0, limit);

      logger.info(`Found ${kgResults.length} KG nodes out of ${response.result.length} total results`);

      return kgResults;
    } catch (error) {
      logger.error('Error searching KG nodes', error);
      throw error;
    }
  }

  /**
   * Search text embeddings by vector similarity
   */
  async searchTexts(
    queryVector: number[],
    limit: number = 10,
    filters?: Record<string, any>,
    scoreThreshold?: number
  ): Promise<QdrantSearchResult[]> {
    try {
      const searchParams: any = {
        vector: queryVector,
        limit,
        with_payload: true,
      };

      if (scoreThreshold) {
        searchParams.score_threshold = scoreThreshold;
      }

      if (filters) {
        searchParams.filter = {
          must: Object.entries(filters).map(([key, value]) => ({
            key,
            match: { value },
          })),
        };
      }

      const response = await this.request<QdrantSearchResponse>(
        '/collections/text_embeddings/points/search',
        'POST',
        searchParams
      );

      return response.result;
    } catch (error) {
      logger.error('Error searching text embeddings', error);
      throw error;
    }
  }

  /**
   * Search KG edges by vector similarity
   */
  async searchEdges(
    queryVector: number[],
    limit: number = 10,
    scoreThreshold?: number
  ): Promise<QdrantSearchResult[]> {
    try {
      const searchParams: any = {
        vector: queryVector,
        limit,
        with_payload: true,
      };

      if (scoreThreshold) {
        searchParams.score_threshold = scoreThreshold;
      }

      const response = await this.request<QdrantSearchResponse>(
        '/collections/kg_edges/points/search',
        'POST',
        searchParams
      );

      return response.result;
    } catch (error) {
      logger.error('Error searching KG edges', error);
      throw error;
    }
  }

  /**
   * Get collection info
   */
  async getCollectionInfo(collectionName: string) {
    try {
      const response = await this.request<any>(
        `/collections/${collectionName}`
      );

      return {
        name: collectionName,
        points_count: response.result.points_count,
        vectors_count: response.result.vectors_count,
        status: response.result.status,
      };
    } catch (error) {
      logger.error('Error getting collection info', error);
      throw error;
    }
  }

  /**
   * Dual-level search (Nodes + Edges simultaneously)
   * Provides relationship-aware retrieval
   */
  async dualLevelSearch(
    queryVector: number[],
    limit: number = 10,
    scoreThreshold?: number
  ): Promise<DualLevelSearchResult> {
    try {
      // Search both collections in parallel
      const [nodeResults, edgeResults] = await Promise.all([
        this.searchNodes(queryVector, limit, scoreThreshold),
        this.searchEdges(queryVector, limit, scoreThreshold),
      ]);

      // Fusion strategy: edges get 1.2x boost (more specific than nodes)
      const combined: CombinedSearchResult[] = [];

      // Add nodes
      for (const nodeResult of nodeResults) {
        combined.push({
          type: 'node',
          score: nodeResult.score,
          data: nodeResult,
        });
      }

      // Add edges with boost, and expand to connected nodes
      for (const edgeResult of edgeResults) {
        combined.push({
          type: 'edge',
          score: edgeResult.score * 1.2, // Boost edges
          data: edgeResult,
        });
      }

      // Sort by score descending
      combined.sort((a, b) => b.score - a.score);

      // Deduplicate and limit
      const seen = new Set<string>();
      const deduplicated: CombinedSearchResult[] = [];

      for (const item of combined) {
        let key: string;
        if (item.type === 'node') {
          key = `node_${item.data.payload.node_id}`;
        } else {
          key = `edge_${item.data.payload.edge_id}`;
        }

        if (!seen.has(key) && deduplicated.length < limit) {
          seen.add(key);
          deduplicated.push(item);
        }
      }

      logger.info(
        `Dual-level search: ${nodeResults.length} nodes + ${edgeResults.length} edges → ${deduplicated.length} results`
      );

      return {
        nodes: nodeResults,
        edges: edgeResults,
        combined: deduplicated,
        stats: {
          totalNodes: nodeResults.length,
          totalEdges: edgeResults.length,
          combinedResults: deduplicated.length,
        },
      };
    } catch (error) {
      logger.error('Error in dual-level search', error);
      throw error;
    }
  }

  /**
   * Search with named vector in dual-embedding collection
   */
  async searchWithNamedVector(
    collectionName: string,
    vectorName: 'gemini',
    queryVector: number[],
    limit: number = 10,
    scoreThreshold?: number
  ): Promise<QdrantSearchResult[]> {
    try {
      const searchParams: any = {
        vector: {
          name: vectorName,
          vector: queryVector,
        },
        limit,
        with_payload: true,
      };

      if (scoreThreshold) {
        searchParams.score_threshold = scoreThreshold;
      }

      const response = await this.request<QdrantSearchResponse>(
        `/collections/${collectionName}/points/search`,
        'POST',
        searchParams
      );

      return response.result;
    } catch (error) {
      logger.error(`Error searching ${collectionName} with ${vectorName}`, error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.request('/collections');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Extract philosophical school from node_id pattern
   */
  private extractSchoolFromNodeId(nodeId: string): string {
    const lower = nodeId.toLowerCase();

    // Stoic patterns
    if (lower.includes('stoic') || lower.includes('chrysippus') || lower.includes('epictetus') ||
        lower.includes('marcus_aurelius') || lower.includes('seneca') || lower.includes('zeno_of_citium') ||
        lower.includes('heimarmene') || lower.includes('logos') || lower.includes('cofatal')) {
      return 'Stoic';
    }

    // Epicurean patterns
    if (lower.includes('epicur') || lower.includes('lucretius') || lower.includes('clinamen') ||
        lower.includes('swerve') || lower.includes('atom')) {
      return 'Epicurean';
    }

    // Aristotelian/Peripatetic patterns
    if (lower.includes('aristotl') || lower.includes('peripatetic') || lower.includes('alexander_of_aphrodisias') ||
        lower.includes('deliberat') || lower.includes('potentiality') || lower.includes('actuality')) {
      return 'Aristotelian';
    }

    // Platonic/Academic patterns
    if (lower.includes('plato') || lower.includes('academic') || lower.includes('socrat') ||
        lower.includes('carneades') || lower.includes('middle_platon') || lower.includes('neoplatonist')) {
      return 'Platonic';
    }

    // Pyrrhonist/Skeptic patterns
    if (lower.includes('pyrrhon') || lower.includes('sextus') || lower.includes('skeptic')) {
      return 'Skeptic';
    }

    // Christian patterns
    if (lower.includes('augustin') || lower.includes('origen') || lower.includes('pelagian') ||
        lower.includes('boethian') || lower.includes('christian') || lower.includes('church_father')) {
      return 'Christian';
    }

    // Core concepts
    if (lower.includes('free_will') || lower.includes('determinism') || lower.includes('compatibil') ||
        lower.includes('moral_responsibility') || lower.includes('eph_hemin') || lower.includes('up_to_us')) {
      return 'Core';
    }

    return 'Unknown';
  }

  /**
   * Extract node type from node_id prefix
   */
  private extractTypeFromNodeId(nodeId: string): string {
    const prefixes = ['concept', 'argument', 'person', 'work', 'reformulation', 'group', 'school', 'evidence'];
    for (const prefix of prefixes) {
      if (nodeId.startsWith(prefix + '_')) {
        return prefix;
      }
    }
    return 'concept';
  }

  /**
   * Format node_id into readable name
   */
  private formatNodeName(nodeId: string): string {
    // Remove prefix and hash suffix
    const parts = nodeId.split('_');
    const type = parts[0];
    // Remove first part (type) and last part (hash)
    const nameParts = parts.slice(1, -1);
    // Capitalize each word
    const name = nameParts
      .map(p => p.charAt(0).toUpperCase() + p.slice(1))
      .join(' ');
    return name || nodeId;
  }

  /**
   * Scroll through KG nodes with their vectors
   * Used for visualization of the full semantic space
   */
  async scrollKGNodes(
    limit: number = 100,
    offset?: string
  ): Promise<{ points: KGNodeWithVector[]; nextOffset: string | null }> {
    try {
      const scrollParams: any = {
        limit,
        with_payload: true,
        with_vector: true,
        // No filter - we'll filter KG nodes in post-processing
      };

      // Use scroll API for pagination
      if (offset) {
        scrollParams.offset = offset;
      }

      const response = await this.request<any>(
        '/collections/ancient_free_will_vectors/points/scroll',
        'POST',
        scrollParams
      );

      // Filter to only KG nodes (have node_id in payload)
      const points: KGNodeWithVector[] = response.result.points
        .filter((p: any) => p.payload && p.payload.node_id)
        .map((p: any) => {
          const nodeId = p.payload.node_id;
          // Extract school from node_id pattern
          const school = this.extractSchoolFromNodeId(nodeId);
          // Create readable name from node_id
          const name = this.formatNodeName(nodeId);
          return {
            id: p.id,
            node_id: nodeId,
            name: p.payload.name || name,
            school: p.payload.school || p.payload.category || school,
            type: p.payload.type || this.extractTypeFromNodeId(nodeId),
            vector: p.vector,
          };
        });

      logger.info(`Scrolled ${points.length} KG nodes with vectors (from ${response.result.points.length} total)`);

      return {
        points,
        nextOffset: response.result.next_page_offset || null,
      };
    } catch (error) {
      logger.error('Error scrolling KG nodes', error);
      throw error;
    }
  }

  /**
   * Scroll through KG edges payloads
   */
  async scrollKGEdges(
    limit: number = 500,
    offset?: any,
  ): Promise<{ points: KGEdgePayload[]; nextOffset: any | null }> {
    try {
      const scrollParams: any = {
        limit,
        with_payload: true,
        with_vector: false,
      };

      if (offset !== undefined && offset !== null) {
        scrollParams.offset = offset;
      }

      const response = await this.request<any>(
        '/collections/kg_edges/points/scroll',
        'POST',
        scrollParams,
      );

      const points: KGEdgePayload[] = (response.result?.points || [])
        .map((p: any) => {
          const payload = p.payload || {};
          const sourceId = payload.source_id || payload.source || '';
          const targetId = payload.target_id || payload.target || '';
          const edgeId = payload.edge_id || String(p.id);

          return {
            ...payload,
            id: p.id,
            edge_id: edgeId,
            source_id: sourceId,
            target_id: targetId,
            relation: payload.relation || payload.relationship || 'related_to',
            description: payload.description || payload.evidence || '',
          };
        })
        .filter((edge) => edge.source_id && edge.target_id);

      logger.info(`Scrolled ${points.length} KG edges`);

      return {
        points,
        nextOffset: response.result?.next_page_offset ?? null,
      };
    } catch (error) {
      logger.error('Error scrolling KG edges', error);
      throw error;
    }
  }

  /**
   * Get all KG nodes from Qdrant (deduplicated by node_id)
   */
  async getAllKGNodes(maxNodes: number = 6000): Promise<KGNodeWithVector[]> {
    const allNodes: KGNodeWithVector[] = [];
    let offset: string | undefined;
    let iterations = 0;
    const maxIterations = 40;

    while (iterations < maxIterations && allNodes.length < maxNodes) {
      const { points, nextOffset } = await this.scrollKGNodes(500, offset);
      allNodes.push(...points);
      if (!nextOffset) break;
      offset = nextOffset;
      iterations++;
    }

    const deduped = new Map<string, KGNodeWithVector>();
    for (const node of allNodes) {
      deduped.set(node.node_id, node);
    }
    return Array.from(deduped.values());
  }

  /**
   * Get all KG edges from Qdrant (deduplicated by edge_id)
   */
  async getAllKGEdges(maxEdges: number = 30000): Promise<KGEdgePayload[]> {
    const allEdges: KGEdgePayload[] = [];
    let offset: any = undefined;
    let iterations = 0;
    const maxIterations = 80;

    while (iterations < maxIterations && allEdges.length < maxEdges) {
      const { points, nextOffset } = await this.scrollKGEdges(500, offset);
      allEdges.push(...points);
      if (!nextOffset) break;
      offset = nextOffset;
      iterations++;
    }

    const deduped = new Map<string, KGEdgePayload>();
    for (const edge of allEdges) {
      const key = edge.edge_id || `${edge.source_id}->${edge.target_id}`;
      deduped.set(key, edge);
    }
    return Array.from(deduped.values());
  }

  /**
   * Fallback edge extraction from the main vectors collection.
   * Some deployments store edge payloads in `ancient_free_will_vectors` instead of `kg_edges`.
   */
  async getKGEdgesFromMainCollection(maxEdges: number = 30000): Promise<KGEdgePayload[]> {
    const allEdges: KGEdgePayload[] = [];
    let offset: any = undefined;
    let iterations = 0;
    const maxIterations = 80;

    while (iterations < maxIterations && allEdges.length < maxEdges) {
      const scrollParams: any = {
        limit: 500,
        with_payload: true,
        with_vector: false,
      };

      if (offset !== undefined && offset !== null) {
        scrollParams.offset = offset;
      }

      const response = await this.request<any>(
        '/collections/ancient_free_will_vectors/points/scroll',
        'POST',
        scrollParams,
      );

      const points = (response.result?.points || [])
        .map((p: any) => {
          const payload = p.payload || {};
          const sourceId = payload.source_id || payload.source || '';
          const targetId = payload.target_id || payload.target || '';
          const edgeId = payload.edge_id || '';
          if (!sourceId || !targetId) {
            return null;
          }
          return {
            ...payload,
            id: p.id,
            edge_id: edgeId || `${sourceId}->${targetId}`,
            source_id: sourceId,
            target_id: targetId,
            relation: payload.relation || payload.relationship || 'related_to',
            description: payload.description || payload.evidence || '',
          } as KGEdgePayload;
        })
        .filter(Boolean) as KGEdgePayload[];

      allEdges.push(...points);

      const nextOffset = response.result?.next_page_offset ?? null;
      if (!nextOffset) break;
      offset = nextOffset;
      iterations++;
    }

    const deduped = new Map<string, KGEdgePayload>();
    for (const edge of allEdges) {
      const key = edge.edge_id || `${edge.source_id}->${edge.target_id}`;
      deduped.set(key, edge);
    }

    logger.info(`Recovered ${deduped.size} edges from ancient_free_will_vectors fallback`);
    return Array.from(deduped.values());
  }

  /**
   * Get sample KG nodes by school for visualization
   * Returns a balanced sample across philosophical schools
   */
  async getSampleNodesBySchool(
    nodesPerSchool: number = 20
  ): Promise<KGNodeWithVector[]> {
    try {
      const schools = ['Stoic', 'Stoicism', 'Epicurean', 'Epicureanism', 'Peripatetic', 'Aristotelian', 'Platonic', 'Platonism', 'Academic'];
      const allNodes: KGNodeWithVector[] = [];

      // Scroll to get nodes, filtering by school in post-processing
      // (Qdrant filter on nested payload fields can be tricky)
      let offset: string | undefined;
      let iterations = 0;
      const maxIterations = 10;

      while (iterations < maxIterations) {
        const { points, nextOffset } = await this.scrollKGNodes(200, offset);

        for (const point of points) {
          allNodes.push(point);
        }

        if (!nextOffset || allNodes.length >= 500) break;
        offset = nextOffset;
        iterations++;
      }

      // Group by school and sample
      const bySchool: Record<string, KGNodeWithVector[]> = {};
      for (const node of allNodes) {
        const school = node.school;
        if (!bySchool[school]) bySchool[school] = [];
        bySchool[school].push(node);
      }

      // Sample from each school
      const sampled: KGNodeWithVector[] = [];
      for (const [school, nodes] of Object.entries(bySchool)) {
        // Shuffle and take first N
        const shuffled = nodes.sort(() => Math.random() - 0.5);
        sampled.push(...shuffled.slice(0, nodesPerSchool));
      }

      logger.info(`Sampled ${sampled.length} nodes across ${Object.keys(bySchool).length} schools`);

      return sampled;
    } catch (error) {
      logger.error('Error getting sample nodes by school', error);
      throw error;
    }
  }
}

// Types for dual-level search
interface CombinedSearchResult {
  type: 'node' | 'edge';
  score: number;
  data: QdrantSearchResult;
}

interface DualLevelSearchResult {
  nodes: QdrantSearchResult[];
  edges: QdrantSearchResult[];
  combined: CombinedSearchResult[];
  stats: {
    totalNodes: number;
    totalEdges: number;
    combinedResults: number;
  };
}
