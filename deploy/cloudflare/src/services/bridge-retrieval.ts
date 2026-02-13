/**
 * Bridge Retrieval Service - HiRAG Bridge Mode Implementation
 *
 * Implements the CRITICAL missing component for multi-hop reasoning:
 * - Identifies source and target entities from query
 * - Finds shortest paths between disparate nodes
 * - Extracts minimal connecting subgraphs
 * - Augments with hierarchical context from upper layers
 *
 * This enables reasoning chains like:
 * "How did Stoic determinism influence Christian free will debates?"
 * → Find path: Chrysippus → Heimarmene → Apostolic Fathers → Libertarian Free Will
 */

import { Env } from '../types';
import { DatabaseService } from './database';
import { LLMService } from './llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('BridgeRetrieval');

// Node and edge types for graph traversal
interface GraphNode {
  id: string;
  label: string;
  type: string;
  school?: string;
  period?: string;
  description?: string;
  concepts?: string[];
  community_id?: string;
  level?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  label?: string;
  weight?: number;
}

interface PathSegment {
  nodes: GraphNode[];
  edges: GraphEdge[];
  distance: number;
  reasoning?: string;
}

interface BridgeContext {
  sourceEntities: string[];
  targetEntities: string[];
  paths: PathSegment[];
  hierarchicalContext: Map<number, string>; // level -> summary
  bridgingConcepts: string[];
  totalTokens: number;
}

// Query decomposition for bridge identification
interface BridgeQuery {
  sourceContext: string;  // "Stoic determinism"
  targetContext: string;  // "Christian free will debates"
  relationshipType: 'influence' | 'evolution' | 'contrast' | 'connection';
  inferredEntities: {
    source: string[];     // ["Chrysippus", "heimarmene", "Stoic"]
    target: string[];     // ["Apostolic Fathers", "libertarian", "Christian"]
  };
}

export class BridgeRetrievalService {
  private env: Env;
  private db: DatabaseService;
  private llm: LLMService;

  // Graph cache for efficient traversal
  private nodeCache: Map<string, GraphNode> = new Map();
  private edgeIndex: Map<string, GraphEdge[]> = new Map(); // node_id -> adjacent edges

  constructor(env: Env) {
    this.env = env;
    this.db = new DatabaseService(env);
    this.llm = new LLMService(env);
  }

  /**
   * Load graph structure from database
   */
  async loadGraph(): Promise<void> {
    try {
      // Load nodes
      const nodes = await this.db.query<GraphNode>(
        `SELECT id, label, type, school, period, description, concepts
         FROM nodes
         WHERE type IN ('philosopher', 'concept', 'argument', 'school')`
      );

      nodes.forEach(node => {
        this.nodeCache.set(node.id, node);
      });

      // Load edges and build adjacency index
      const edges = await this.db.query<GraphEdge>(
        `SELECT source, target, type, label, weight
         FROM edges
         WHERE type IN ('influenced', 'responded_to', 'developed', 'criticized', 'member_of')`
      );

      edges.forEach(edge => {
        // Index by source
        if (!this.edgeIndex.has(edge.source)) {
          this.edgeIndex.set(edge.source, []);
        }
        this.edgeIndex.get(edge.source)!.push(edge);

        // Also index reverse for bidirectional traversal
        const reverseEdge = { ...edge, source: edge.target, target: edge.source };
        if (!this.edgeIndex.has(edge.target)) {
          this.edgeIndex.set(edge.target, []);
        }
        this.edgeIndex.get(edge.target)!.push(reverseEdge);
      });

      logger.info(`Loaded graph: ${nodes.length} nodes, ${edges.length} edges`);
    } catch (error) {
      logger.error('Error loading graph', error);
      // Fallback to mock data for testing
      this.loadMockGraph();
    }
  }

  /**
   * Decompose query to identify bridge endpoints
   */
  async decomposeQuery(query: string): Promise<BridgeQuery> {
    const prompt = `Analyze this query to identify source and target contexts that need bridging:

Query: "${query}"

Identify:
1. Source context (starting point/subject)
2. Target context (ending point/object)
3. Relationship type (influence/evolution/contrast/connection)
4. Key entities for each context

Example:
Query: "How did Stoic determinism influence Christian free will debates?"
Source: "Stoic determinism"
Target: "Christian free will debates"
Relationship: "influence"
Source entities: ["Stoic", "determinism", "Chrysippus", "heimarmene"]
Target entities: ["Christian", "free will", "Apostolic Fathers", "libertarian"]

Respond in JSON:
{
  "sourceContext": "...",
  "targetContext": "...",
  "relationshipType": "influence|evolution|contrast|connection",
  "inferredEntities": {
    "source": ["entity1", "entity2"],
    "target": ["entity3", "entity4"]
  }
}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      return JSON.parse(response);
    } catch (error) {
      logger.error('Query decomposition failed', error);
      // Fallback to rule-based decomposition
      return this.decomposeByRules(query);
    }
  }

  /**
   * Rule-based query decomposition fallback
   */
  private decomposeByRules(query: string): BridgeQuery {
    const lower = query.toLowerCase();

    // Pattern matching for common multi-hop queries
    const patterns = [
      {
        regex: /how did (.*?) influence (.*?)\?/i,
        type: 'influence' as const,
        sourceGroup: 1,
        targetGroup: 2
      },
      {
        regex: /evolution (?:of|from) (.*?) to (.*)/i,
        type: 'evolution' as const,
        sourceGroup: 1,
        targetGroup: 2
      },
      {
        regex: /compare (.*?) (?:with|and|to|versus|vs\.?) (.*)/i,
        type: 'contrast' as const,
        sourceGroup: 1,
        targetGroup: 2
      },
      {
        regex: /connection between (.*?) and (.*)/i,
        type: 'connection' as const,
        sourceGroup: 1,
        targetGroup: 2
      }
    ];

    for (const pattern of patterns) {
      const match = query.match(pattern.regex);
      if (match) {
        const source = match[pattern.sourceGroup].trim();
        const target = match[pattern.targetGroup].trim();

        return {
          sourceContext: source,
          targetContext: target,
          relationshipType: pattern.type,
          inferredEntities: {
            source: this.extractEntities(source),
            target: this.extractEntities(target)
          }
        };
      }
    }

    // Default: treat as connection query
    const entities = this.extractEntities(query);
    const midpoint = Math.floor(entities.length / 2);

    return {
      sourceContext: entities.slice(0, midpoint).join(' '),
      targetContext: entities.slice(midpoint).join(' '),
      relationshipType: 'connection',
      inferredEntities: {
        source: entities.slice(0, midpoint),
        target: entities.slice(midpoint)
      }
    };
  }

  /**
   * Extract entities from text
   */
  private extractEntities(text: string): string[] {
    const entities: string[] = [];
    const lower = text.toLowerCase();

    // Known philosophers
    const philosophers = ['chrysippus', 'epictetus', 'aristotle', 'plato', 'augustine', 'aquinas'];
    philosophers.forEach(p => {
      if (lower.includes(p)) entities.push(p);
    });

    // Known schools
    const schools = ['stoic', 'epicurean', 'platonist', 'peripatetic', 'christian', 'patristic'];
    schools.forEach(s => {
      if (lower.includes(s)) entities.push(s);
    });

    // Known concepts
    const concepts = ['determinism', 'free will', 'heimarmene', 'prohairesis', 'libertarian', 'compatibilism'];
    concepts.forEach(c => {
      if (lower.includes(c)) entities.push(c);
    });

    return entities;
  }

  /**
   * Find nodes matching entity names
   */
  private findNodes(entities: string[]): GraphNode[] {
    const nodes: GraphNode[] = [];
    const seen = new Set<string>();

    for (const entity of entities) {
      const entityLower = entity.toLowerCase();

      for (const node of this.nodeCache.values()) {
        if (seen.has(node.id)) continue;

        const label = node.label.toLowerCase();
        const desc = (node.description || '').toLowerCase();
        const school = (node.school || '').toLowerCase();

        if (label.includes(entityLower) ||
            desc.includes(entityLower) ||
            school.includes(entityLower)) {
          nodes.push(node);
          seen.add(node.id);
        }
      }
    }

    return nodes;
  }

  /**
   * Bidirectional BFS to find shortest path between nodes
   */
  private findShortestPath(source: GraphNode, target: GraphNode): PathSegment | null {
    if (source.id === target.id) {
      return { nodes: [source], edges: [], distance: 0 };
    }

    // Bidirectional search queues
    const forwardQueue: string[] = [source.id];
    const backwardQueue: string[] = [target.id];

    const forwardParent = new Map<string, string>();
    const backwardParent = new Map<string, string>();

    const forwardVisited = new Set<string>([source.id]);
    const backwardVisited = new Set<string>([target.id]);

    let meetingPoint: string | null = null;

    // Alternating BFS from both ends
    while (forwardQueue.length > 0 || backwardQueue.length > 0) {
      // Forward step
      if (forwardQueue.length > 0) {
        const current = forwardQueue.shift()!;
        const edges = this.edgeIndex.get(current) || [];

        for (const edge of edges) {
          const neighbor = edge.target;

          if (backwardVisited.has(neighbor)) {
            // Found meeting point!
            meetingPoint = neighbor;
            forwardParent.set(neighbor, current);
            break;
          }

          if (!forwardVisited.has(neighbor)) {
            forwardVisited.add(neighbor);
            forwardParent.set(neighbor, current);
            forwardQueue.push(neighbor);
          }
        }

        if (meetingPoint) break;
      }

      // Backward step
      if (backwardQueue.length > 0) {
        const current = backwardQueue.shift()!;
        const edges = this.edgeIndex.get(current) || [];

        for (const edge of edges) {
          const neighbor = edge.target;

          if (forwardVisited.has(neighbor)) {
            // Found meeting point!
            meetingPoint = neighbor;
            backwardParent.set(neighbor, current);
            break;
          }

          if (!backwardVisited.has(neighbor)) {
            backwardVisited.add(neighbor);
            backwardParent.set(neighbor, current);
            backwardQueue.push(neighbor);
          }
        }

        if (meetingPoint) break;
      }
    }

    if (!meetingPoint) {
      return null; // No path found
    }

    // Reconstruct path
    const path: string[] = [];
    const pathEdges: GraphEdge[] = [];

    // Build forward path to meeting point
    let current = meetingPoint;
    const forwardPath: string[] = [current];

    while (forwardParent.has(current)) {
      const parent = forwardParent.get(current)!;
      forwardPath.unshift(parent);

      // Find edge
      const edge = this.edgeIndex.get(parent)?.find(e => e.target === current);
      if (edge) pathEdges.unshift(edge);

      current = parent;
    }

    // Build backward path from meeting point
    current = meetingPoint;
    while (backwardParent.has(current)) {
      const parent = backwardParent.get(current)!;
      forwardPath.push(parent);

      // Find edge
      const edge = this.edgeIndex.get(current)?.find(e => e.target === parent);
      if (edge) pathEdges.push(edge);

      current = parent;
    }

    // Convert IDs to nodes
    const pathNodes = forwardPath.map(id => this.nodeCache.get(id)!).filter(n => n);

    return {
      nodes: pathNodes,
      edges: pathEdges,
      distance: pathNodes.length - 1
    };
  }

  /**
   * Extract subgraph around a path
   */
  private extractSubgraph(path: PathSegment, depth: number = 1): PathSegment {
    const expanded = { ...path };
    const nodeSet = new Set(path.nodes.map(n => n.id));
    const edgeSet = new Set(path.edges.map(e => `${e.source}-${e.target}`));

    // Expand neighborhood around path nodes
    for (let d = 0; d < depth; d++) {
      const currentNodes = [...nodeSet];

      for (const nodeId of currentNodes) {
        const edges = this.edgeIndex.get(nodeId) || [];

        for (const edge of edges) {
          const edgeKey = `${edge.source}-${edge.target}`;

          if (!edgeSet.has(edgeKey)) {
            edgeSet.add(edgeKey);
            expanded.edges.push(edge);

            // Add neighbor node
            const neighbor = this.nodeCache.get(edge.target);
            if (neighbor && !nodeSet.has(neighbor.id)) {
              nodeSet.add(neighbor.id);
              expanded.nodes.push(neighbor);
            }
          }
        }
      }
    }

    return expanded;
  }

  /**
   * Get hierarchical context for path nodes
   */
  async getHierarchicalContext(nodes: GraphNode[]): Promise<Map<number, string>> {
    const context = new Map<number, string>();

    try {
      // Load hierarchy from cache
      const hierarchy = await this.env.TEXT_CACHE?.get('hierarchical_communities', 'json') as any;
      if (!hierarchy) return context;

      // Find communities containing path nodes
      const nodeIds = new Set(nodes.map(n => n.id));
      const relevantCommunities = new Map<number, Set<string>>();

      for (const level of hierarchy.hierarchy.levels) {
        for (const community of level.communities) {
          const intersection = community.member_node_ids.filter((id: string) => nodeIds.has(id));

          if (intersection.length > 0) {
            if (!relevantCommunities.has(level.level)) {
              relevantCommunities.set(level.level, new Set());
            }
            relevantCommunities.get(level.level)!.add(community.summary);
          }
        }
      }

      // Build context strings for each level
      for (const [level, summaries] of relevantCommunities.entries()) {
        const contextStr = Array.from(summaries).join('\n');
        context.set(level, contextStr);
      }

    } catch (error) {
      logger.error('Error getting hierarchical context', error);
    }

    return context;
  }

  /**
   * Main bridge retrieval method
   */
  async retrieveBridge(query: string): Promise<BridgeContext> {
    // Ensure graph is loaded
    if (this.nodeCache.size === 0) {
      await this.loadGraph();
    }

    // 1. Decompose query to identify endpoints
    const bridgeQuery = await this.decomposeQuery(query);
    logger.info(`Bridge query: ${bridgeQuery.sourceContext} → ${bridgeQuery.targetContext}`);

    // 2. Find source and target nodes
    const sourceNodes = this.findNodes(bridgeQuery.inferredEntities.source);
    const targetNodes = this.findNodes(bridgeQuery.inferredEntities.target);

    logger.info(`Found ${sourceNodes.length} source nodes, ${targetNodes.length} target nodes`);

    // 3. Find shortest paths between all source-target pairs
    const paths: PathSegment[] = [];
    const MAX_PATHS = 3; // Limit for performance

    outerLoop:
    for (const source of sourceNodes) {
      for (const target of targetNodes) {
        const path = this.findShortestPath(source, target);

        if (path && path.distance > 0) {
          // Expand subgraph around path
          const expanded = this.extractSubgraph(path, 1);

          // Generate reasoning for this path
          expanded.reasoning = await this.generatePathReasoning(expanded, bridgeQuery.relationshipType);

          paths.push(expanded);

          if (paths.length >= MAX_PATHS) break outerLoop;
        }
      }
    }

    logger.info(`Found ${paths.length} bridging paths`);

    // 4. Get hierarchical context
    const allPathNodes = paths.flatMap(p => p.nodes);
    const hierarchicalContext = await this.getHierarchicalContext(allPathNodes);

    // 5. Extract bridging concepts
    const bridgingConcepts = this.extractBridgingConcepts(paths);

    // 6. Calculate tokens
    const totalTokens = this.estimateTokens(paths, hierarchicalContext);

    return {
      sourceEntities: bridgeQuery.inferredEntities.source,
      targetEntities: bridgeQuery.inferredEntities.target,
      paths,
      hierarchicalContext,
      bridgingConcepts,
      totalTokens
    };
  }

  /**
   * Generate reasoning explanation for a path
   */
  private async generatePathReasoning(
    path: PathSegment,
    relationshipType: string
  ): Promise<string> {
    const nodeDescriptions = path.nodes.map(n =>
      `${n.label} (${n.type}${n.school ? ', ' + n.school : ''})`
    ).join(' → ');

    const prompt = `Explain this ${relationshipType} connection:

Path: ${nodeDescriptions}

Key edges: ${path.edges.slice(0, 5).map(e => e.label || e.type).join(', ')}

Provide a 2-3 sentence explanation of how these entities connect.`;

    try {
      return await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview', 1);
    } catch {
      // Fallback to template
      return `This path shows the ${relationshipType} from ${path.nodes[0].label} to ${path.nodes[path.nodes.length-1].label} through ${path.distance} intermediate connections.`;
    }
  }

  /**
   * Extract key bridging concepts from paths
   */
  private extractBridgingConcepts(paths: PathSegment[]): string[] {
    const concepts = new Set<string>();

    for (const path of paths) {
      // Add node concepts
      path.nodes.forEach(node => {
        if (node.concepts) {
          node.concepts.forEach(c => concepts.add(c));
        }
        if (node.type === 'concept') {
          concepts.add(node.label);
        }
      });

      // Add edge types as concepts
      path.edges.forEach(edge => {
        if (edge.label) concepts.add(edge.label);
      });
    }

    return Array.from(concepts).slice(0, 10); // Limit to top 10
  }

  /**
   * Estimate token count for context
   */
  private estimateTokens(paths: PathSegment[], context: Map<number, string>): number {
    let tokens = 0;

    // Path descriptions
    paths.forEach(path => {
      tokens += path.nodes.length * 20; // ~20 tokens per node
      tokens += path.edges.length * 10; // ~10 tokens per edge
      tokens += 50; // reasoning text
    });

    // Hierarchical context
    for (const summary of context.values()) {
      tokens += Math.ceil(summary.length / 4); // ~4 chars per token
    }

    return tokens;
  }

  /**
   * Load mock graph for testing
   */
  private loadMockGraph(): void {
    // Mock nodes
    const mockNodes: GraphNode[] = [
      { id: 'n1', label: 'Chrysippus', type: 'philosopher', school: 'Stoic', period: 'Hellenistic' },
      { id: 'n2', label: 'Heimarmene', type: 'concept', school: 'Stoic', description: 'Cosmic determinism' },
      { id: 'n3', label: 'Apostolic Fathers', type: 'group', school: 'Christian', period: 'Patristic' },
      { id: 'n4', label: 'Libertarian Free Will', type: 'concept', school: 'Christian' },
      { id: 'n5', label: 'Epictetus', type: 'philosopher', school: 'Stoic', period: 'Roman' },
      { id: 'n6', label: 'Augustine', type: 'philosopher', school: 'Christian', period: 'Patristic' }
    ];

    mockNodes.forEach(node => this.nodeCache.set(node.id, node));

    // Mock edges
    const mockEdges: GraphEdge[] = [
      { source: 'n1', target: 'n2', type: 'developed', label: 'developed concept' },
      { source: 'n2', target: 'n3', type: 'criticized_by', label: 'criticized by' },
      { source: 'n3', target: 'n4', type: 'developed', label: 'developed' },
      { source: 'n1', target: 'n5', type: 'influenced', label: 'influenced' },
      { source: 'n5', target: 'n6', type: 'influenced', label: 'influenced' },
      { source: 'n6', target: 'n4', type: 'developed', label: 'developed' }
    ];

    mockEdges.forEach(edge => {
      if (!this.edgeIndex.has(edge.source)) {
        this.edgeIndex.set(edge.source, []);
      }
      this.edgeIndex.get(edge.source)!.push(edge);

      // Bidirectional
      const reverse = { ...edge, source: edge.target, target: edge.source };
      if (!this.edgeIndex.has(edge.target)) {
        this.edgeIndex.set(edge.target, []);
      }
      this.edgeIndex.get(edge.target)!.push(reverse);
    });

    logger.info('Loaded mock graph for testing');
  }
}

export type { BridgeContext, PathSegment, BridgeQuery };
