/**
 * Hierarchical Retrieval Service
 *
 * Implements ArchRAG-style hierarchical community-based retrieval:
 * - Level 2 (Abstract): Broad schools/movements (10-15 communities)
 * - Level 1 (Medium): Thematic clusters (30-50 communities)
 * - Level 0 (Detailed): Specific subgraphs (100-200 communities)
 *
 * Benefits:
 * - 250× token reduction on global questions
 * - Progressive disclosure (start abstract, drill down)
 * - Query-adaptive depth selection
 */

import { Env } from '../types';
import { RetrievalDiagnostics } from '../types/agentic';
import { DatabaseService } from './database';
import { LLMService } from './llm';
import { BridgeRetrievalService, BridgeContext } from './bridge-retrieval';
import { getLogger } from '../utils/logger';

const logger = getLogger('HierarchicalRetrieval');

// Community hierarchy structure
interface Community {
  id: string;
  level: number;
  size: number;
  member_node_ids: string[];
  dominant_period: string | null;
  dominant_school: string | null;
  node_types: Record<string, number>;
  summary: string;
  members?: string[];
  nodes?: any[];
  relevanceScore?: number;
  matchReasons?: string[];
}

interface HierarchyLevel {
  level: number;
  resolution: number;
  num_communities: number;
  communities: Community[];
}

interface Hierarchy {
  metadata: {
    generated_at: string;
    num_nodes: number;
    num_levels: number;
    total_communities: number;
  };
  hierarchy: {
    levels: HierarchyLevel[];
  };
}

// Query classification types
type QueryType =
  | 'global_abstract'       // "What is Stoic free will?"
  | 'specific_entity'       // "What did Chrysippus say?"
  | 'comparative'           // "How do Stoics differ from Epicureans?"
  | 'temporal_evolution'    // "How did prohairesis evolve?"
  | 'dialectical'          // "Arguments for compatibilism"
  | 'multi_hop';           // "How did Stoic determinism influence Christian debates?"

interface QueryClassification {
  type: QueryType;
  confidence: number;
  entities?: string[];
  concepts?: string[];
  schools?: string[];
  suggestedLevel: number;
}

interface RetrievalStrategy {
  startLevel: number;
  maxDepth: number;
  expandMode: 'on_demand' | 'full' | 'progressive' | 'bridge';
  maxCommunities: number;
  useBridge?: boolean;
}

interface ScoredCommunity {
  community: Community;
  score: number;
  matchReasons: string[];
}

export class HierarchicalRetrievalService {
  private env: Env;
  private db: DatabaseService;
  private llm: LLMService;
  private bridge: BridgeRetrievalService;
  private hierarchy: Hierarchy | null = null;
  private readonly relevanceThreshold = 0.25;
  private readonly fallbackLevels = 1;

  constructor(env: Env) {
    this.env = env;
    this.db = new DatabaseService(env);
    this.llm = new LLMService(env);
    this.bridge = new BridgeRetrievalService(env);
  }

  /**
   * Load hierarchy from KV storage or database
   */
  async loadHierarchy(): Promise<Hierarchy> {
    if (this.hierarchy) {
      return this.hierarchy;
    }

    try {
      // Try KV cache first (fast)
      const cached = await this.env.TEXT_CACHE?.get('hierarchical_communities', 'json');
      if (cached) {
        logger.info('Loaded hierarchy from KV cache');
        this.hierarchy = cached as Hierarchy;
        return this.hierarchy;
      }

      // Fall back to database or external source
      // For now, return mock hierarchy - replace with actual database query
      logger.warn('Hierarchy not in cache - using mock data');
      this.hierarchy = this.getMockHierarchy();
      return this.hierarchy;
    } catch (error) {
      logger.error('Error loading hierarchy', error);
      throw error;
    }
  }

  /**
   * Rule-based pre-classification for common query patterns
   * Returns classification if pattern matches, null otherwise
   */
  private preClassifyByRules(query: string): QueryClassification | null {
    logger.info(`preClassifyByRules called with query: "${query.slice(0, 60)}..."`);

    // Multi-hop patterns (highest priority - connection between distant concepts)
    const multiHopPatterns = [
      /how did (.*?) influence (.*?)\??$/i,
      /what is the connection between (.*?) and (.*?)\??$/i,
      /how (.*?) led to (.*?)\??$/i,
      /relationship between (.*?) and (.*?)\??$/i,
      /link between (.*?) and (.*?)\??$/i,
      /how (.*?) affected (.*?)\??$/i,
      /impact of (.*?) on (.*?)\??$/i,
    ];

    for (const pattern of multiHopPatterns) {
      logger.info(`Testing multi_hop pattern: ${pattern.toString()}`);
      if (pattern.test(query)) {
        logger.info(`Rule-based classification: multi_hop (pattern ${pattern.toString()} matched)`);
        return {
          type: 'multi_hop',
          confidence: 0.95,
          suggestedLevel: 0,
        };
      }
    }
    logger.info('No multi_hop pattern matched');

    // Comparative patterns
    const comparativePatterns = [
      /how do (.*?) (?:and|vs\.?|versus) (.*?) differ/i,
      /compare (.*?) (?:with|and|to|versus|vs\.?) (.*)/i,
      /difference between (.*?) and (.*)/i,
      /(.*?) vs\.? (.*)/i,
    ];

    for (const pattern of comparativePatterns) {
      if (pattern.test(query)) {
        logger.info(`Rule-based classification: comparative (pattern match)`);
        return {
          type: 'comparative',
          confidence: 0.9,
          suggestedLevel: 1,
        };
      }
    }

    // Temporal evolution patterns
    const temporalPatterns = [
      /how did (.*?) evolve/i,
      /evolution of (.*?) from (.*?) to/i,
      /development of (.*?) over time/i,
      /history of (.*?) concept/i,
    ];

    for (const pattern of temporalPatterns) {
      if (pattern.test(query)) {
        logger.info(`Rule-based classification: temporal_evolution (pattern match)`);
        return {
          type: 'temporal_evolution',
          confidence: 0.9,
          suggestedLevel: 1,
        };
      }
    }

    // Specific entity patterns (person/text questions)
    const specificPatterns = [
      /what did (\w+) say/i,
      /according to (\w+)/i,
      /(\w+)'s view on/i,
      /in (\w+)'s (.*?)(writings|works|texts)/i,
    ];

    for (const pattern of specificPatterns) {
      if (pattern.test(query)) {
        logger.info(`Rule-based classification: specific_entity (pattern match)`);
        return {
          type: 'specific_entity',
          confidence: 0.85,
          suggestedLevel: 0,
        };
      }
    }

    // No rule match - fall back to LLM
    return null;
  }

  /**
   * Classify query to determine optimal retrieval strategy
   */
  async classifyQuery(query: string): Promise<QueryClassification> {
    // Try rule-based classification first (fast and reliable)
    const ruleResult = this.preClassifyByRules(query);
    if (ruleResult) {
      return ruleResult;
    }

    // Fall back to LLM for complex queries
    const prompt = `Classify this philosophical query:

Query: "${query}"

Types:
- global_abstract: Broad questions about schools/doctrines (e.g., "What is Stoic free will?")
- specific_entity: Questions about specific philosophers/texts (e.g., "What did Chrysippus say?")
- comparative: Comparing multiple entities/doctrines (e.g., "Stoics vs Epicureans")
- temporal_evolution: How concepts changed over time (e.g., "How did prohairesis evolve?")
- dialectical: Arguments and counter-arguments (e.g., "Arguments for compatibilism")
- multi_hop: Questions requiring connections across distant concepts (e.g., "How did X influence Y?")

Extract: entities mentioned, concepts, philosophical schools

Respond in JSON:
{
  "type": "global_abstract|specific_entity|comparative|temporal_evolution|dialectical|multi_hop",
  "confidence": 0.0-1.0,
  "entities": ["entity1", "entity2"],
  "concepts": ["concept1", "concept2"],
  "schools": ["school1", "school2"],
  "suggestedLevel": 0-2
}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const classification = JSON.parse(response);
      return classification;
    } catch (error) {
      logger.error('Query classification failed', error);
      // Default to medium level
      return {
        type: 'global_abstract',
        confidence: 0.5,
        suggestedLevel: 1,
      };
    }
  }

  /**
   * Determine retrieval strategy based on query classification
   */
  getRetrievalStrategy(classification: QueryClassification): RetrievalStrategy {
    switch (classification.type) {
      case 'global_abstract':
        // Start at highest level (abstract summaries)
        return {
          startLevel: 2,
          maxDepth: 1,
          expandMode: 'on_demand',
          maxCommunities: 5,
        };

      case 'specific_entity':
        // Start at lowest level (detailed nodes)
        return {
          startLevel: 0,
          maxDepth: 1,
          expandMode: 'full',
          maxCommunities: 3,
        };

      case 'comparative':
        // Medium level, multiple communities
        return {
          startLevel: 1,
          maxDepth: 2,
          expandMode: 'progressive',
          maxCommunities: 6,
        };

      case 'temporal_evolution':
        // Multiple levels, chronological
        return {
          startLevel: 1,
          maxDepth: 2,
          expandMode: 'progressive',
          maxCommunities: 8,
        };

      case 'dialectical':
        // Medium level, full expansion
        return {
          startLevel: 1,
          maxDepth: 2,
          expandMode: 'full',
          maxCommunities: 5,
        };

      case 'multi_hop':
        // Use bridge mode for multi-hop reasoning
        return {
          startLevel: 0,
          maxDepth: 3,
          expandMode: 'bridge',
          maxCommunities: 10,
          useBridge: true,
        };

      default:
        return {
          startLevel: 1,
          maxDepth: 1,
          expandMode: 'on_demand',
          maxCommunities: 5,
        };
    }
  }

  /**
   * Score a community for relevance to the query using lightweight lexical cues.
   */
  private scoreCommunity(
    queryLower: string,
    queryTerms: string[],
    community: Community
  ): ScoredCommunity {
    let score = 0;
    const matchReasons: string[] = [];

    const summary = community.summary ? community.summary.toLowerCase() : '';
    const school = community.dominant_school ? community.dominant_school.toLowerCase() : '';
    const period = community.dominant_period ? community.dominant_period.toLowerCase() : '';

    if (summary && summary.includes(queryLower)) {
      score += 0.5;
      matchReasons.push('summary');
    }

    if (school && queryLower.includes(school)) {
      score += 0.25;
      matchReasons.push('school');
    }

    if (period && queryLower.includes(period)) {
      score += 0.15;
      matchReasons.push('period');
    }

    if (summary && queryTerms.length > 0) {
      const termMatches = queryTerms.filter(term => summary.includes(term));
      if (termMatches.length > 0) {
        const termScore = Math.min(0.25, termMatches.length * 0.05);
        score += termScore;
        matchReasons.push(`terms(${termMatches.slice(0, 3).join(', ')})`);
      }
    }

    if (score === 0) {
      score = 0.01;
      matchReasons.push('fallback');
    }

    return { community, score, matchReasons };
  }

  /**
   * Retrieve relevant communities at specified level
   */
  async retrieveCommunities(
    query: string,
    level: number,
    limit: number = 5
  ): Promise<ScoredCommunity[]> {
    const hierarchy = await this.loadHierarchy();
    const levelData = hierarchy.hierarchy.levels.find(l => l.level === level);

    if (!levelData) {
      throw new Error(`Level ${level} not found in hierarchy`);
    }

    const queryLower = query.toLowerCase();
    const queryTerms = Array.from(
      new Set(
        queryLower
          .split(/[\s,;:?]+/)
          .map(term => term.trim())
          .filter(term => term.length > 2)
      )
    );

    const scoredCommunities = levelData.communities
      .map(community => this.scoreCommunity(queryLower, queryTerms, community))
      .sort((a, b) => b.score - a.score);

    return scoredCommunities.slice(0, limit);
  }

  /**
   * Merge scored community results, preserving the highest score per community.
   */
  private mergeCommunityResults(
    store: Map<string, { community: Community; score: number; matchReasons: string[] }>,
    results: ScoredCommunity[]
  ) {
    for (const result of results) {
      const existing = store.get(result.community.id);
      if (!existing || result.score > existing.score) {
        store.set(result.community.id, {
          community: result.community,
          score: result.score,
          matchReasons: [...result.matchReasons],
        });
      } else if (existing) {
        existing.matchReasons = Array.from(
          new Set([...existing.matchReasons, ...result.matchReasons])
        );
      }
    }
  }

  /**
   * Main hierarchical retrieval method
   */
  async retrieve(query: string, explicitMode?: string): Promise<{
    classification: QueryClassification;
    strategy: RetrievalStrategy;
    communities: Community[];
    context: string;
    tokenCount: number;
    bridgeContext?: BridgeContext;
    diagnostics?: RetrievalDiagnostics;
  }> {
    // 1. Classify query (use explicit mode if provided)
    let classification: QueryClassification;

    if (explicitMode) {
      // Map explicit mode to query type
      const modeToType: Record<string, QueryType> = {
        'local': 'specific_entity',
        'global': 'global_abstract',
        'bridge': 'multi_hop',
        'multi_hop': 'multi_hop',
        'full': 'global_abstract', // Default to global for full mode
      };

      classification = {
        type: modeToType[explicitMode] || 'global_abstract',
        confidence: 1.0, // Explicit mode has full confidence
        suggestedLevel: explicitMode === 'local' ? 0 : explicitMode === 'global' ? 2 : 1,
      };
      logger.info(`Using explicit mode: ${explicitMode} → ${classification.type}`);
    } else {
      classification = await this.classifyQuery(query);
      logger.info(`Query classified as: ${classification.type} (confidence: ${classification.confidence})`);
    }

    // 2. Determine strategy
    const strategy = this.getRetrievalStrategy(classification);
    logger.info(`Strategy: Start L${strategy.startLevel}, depth=${strategy.maxDepth}, max=${strategy.maxCommunities}`);

    // 3. Handle bridge mode for multi-hop queries
    if (strategy.useBridge) {
      logger.info('Using BRIDGE MODE for multi-hop reasoning');
      const bridgeContext = await this.bridge.retrieveBridge(query);

      // Build context from bridge paths
      const contextParts: string[] = [];

      // Add hierarchical context
      for (const [level, summary] of bridgeContext.hierarchicalContext.entries()) {
        contextParts.push(`[Level ${level} Context]\n${summary}`);
      }

      // Add path information
      for (const path of bridgeContext.paths) {
        const pathDesc = path.nodes.map(n => n.label).join(' → ');
        contextParts.push(`\n[Path: ${pathDesc}]\n${path.reasoning || ''}`);
      }

      // Add bridging concepts
      if (bridgeContext.bridgingConcepts.length > 0) {
        contextParts.push(`\n[Key Concepts: ${bridgeContext.bridgingConcepts.join(', ')}]`);
      }

      const context = contextParts.join('\n\n');

      return {
        classification,
        strategy,
        communities: [], // Bridge mode doesn't use traditional communities
        context,
        tokenCount: bridgeContext.totalTokens,
        bridgeContext,
      };
    }

    // 4. Standard retrieval with relevance-aware fallbacks for non-bridge queries
    const diagnostics: RetrievalDiagnostics = {
      levels: [],
      finalLevelCount: 0,
    };
    const aggregated = new Map<string, { community: Community; score: number; matchReasons: string[] }>();

    const initialResults = await this.retrieveCommunities(
      query,
      strategy.startLevel,
      strategy.maxCommunities
    );

    const initialMaxScore = initialResults.length > 0
      ? Math.max(...initialResults.map(r => r.score))
      : 0;

    diagnostics.levels.push({
      level: strategy.startLevel,
      communities: initialResults.length,
      maxScore: Number(initialMaxScore.toFixed(3)),
      fallbackApplied: false,
    });

    this.mergeCommunityResults(aggregated, initialResults);

    if (
      !strategy.useBridge &&
      strategy.startLevel > 0 &&
      (initialResults.length === 0 || initialMaxScore < this.relevanceThreshold)
    ) {
      let currentLevel = strategy.startLevel;
      let fallbackSteps = 0;
      let previousReason = initialResults.length === 0 ? 'no_matches' : 'low_relevance';

      while (fallbackSteps < this.fallbackLevels && currentLevel > 0) {
        fallbackSteps += 1;
        currentLevel -= 1;
        const fallbackResults = await this.retrieveCommunities(
          query,
          currentLevel,
          strategy.maxCommunities
        );

        const fallbackMaxScore = fallbackResults.length > 0
          ? Math.max(...fallbackResults.map(r => r.score))
          : 0;

        diagnostics.levels.push({
          level: currentLevel,
          communities: fallbackResults.length,
          maxScore: Number(fallbackMaxScore.toFixed(3)),
          fallbackApplied: true,
          reason: previousReason,
        });

        this.mergeCommunityResults(aggregated, fallbackResults);

        if (fallbackResults.length > 0 && fallbackMaxScore >= this.relevanceThreshold) {
          break;
        }

        previousReason = fallbackResults.length === 0 ? 'no_matches' : 'low_relevance';
      }
    }

    const combinedCommunities = Array.from(aggregated.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, strategy.maxCommunities)
      .map(entry => ({
        ...entry.community,
        relevanceScore: Number(entry.score.toFixed(3)),
        matchReasons: Array.from(new Set(entry.matchReasons)),
      }));

    diagnostics.finalLevelCount = combinedCommunities.length;
    logger.info(`Retrieved ${combinedCommunities.length} communities after fallback processing`);

    // 5. Build context from community summaries
    const contextParts: string[] = [];

    for (const community of combinedCommunities) {
      const header = `[${community.dominant_school || 'Mixed'} - ${community.dominant_period || 'Various periods'} | score ${(community.relevanceScore ?? 0).toFixed(2)}]`;
      const matchNote = community.matchReasons && community.matchReasons.length > 0
        ? `\nMatches: ${community.matchReasons.join(', ')}`
        : '';
      contextParts.push(`${header}\n${community.summary}${matchNote}`);
    }

    const context = contextParts.join('\n\n---\n\n');

    // 6. Estimate token count (rough approximation)
    const tokenCount = Math.ceil(context.length / 4);

    return {
      classification,
      strategy,
      communities: combinedCommunities,
      context,
      tokenCount,
      diagnostics,
    };
  }

  /**
   * Mock hierarchy for testing (replace with actual data)
   */
  private getMockHierarchy(): Hierarchy {
    return {
      metadata: {
        generated_at: new Date().toISOString(),
        num_nodes: 534,
        num_levels: 3,
        total_communities: 0,
      },
      hierarchy: {
        levels: [
          {
            level: 2,
            resolution: 0.3,
            num_communities: 10,
            communities: [
              {
                id: 'L2_C0',
                level: 2,
                size: 120,
                member_node_ids: [],
                dominant_period: 'Hellenistic',
                dominant_school: 'Stoic',
                node_types: {},
                summary:
                  'Stoic compatibilism represents a comprehensive philosophical response to determinism, arguing that freedom and necessity are compatible. Central figures include Chrysippus, who developed the cylinder analogy to show how internal assent remains free even under causal determinism. The Stoics maintained that virtue and moral responsibility persist despite cosmic fate (heimarmene), as voluntary action stems from rational assent to impressions. This tradition profoundly influenced Roman thinkers like Cicero and Seneca.',
              },
              {
                id: 'L2_C1',
                level: 2,
                size: 85,
                member_node_ids: [],
                dominant_period: 'Classical Greek',
                dominant_school: 'Peripatetic',
                node_types: {},
                summary:
                  'Aristotelian voluntary action theory focuses on prohairesis (rational choice) as the locus of moral responsibility. Aristotle distinguished voluntary (hekousion) from involuntary actions based on internal vs. external principles of motion. His analysis in Nicomachean Ethics III establishes that actions from ignorance, force, or compulsion are involuntary, while deliberate choice combined with desire constitutes full voluntariness. This framework dominated medieval discussions of free will.',
              },
            ],
          },
          {
            level: 1,
            resolution: 0.5,
            num_communities: 30,
            communities: [],
          },
          {
            level: 0,
            resolution: 0.8,
            num_communities: 100,
            communities: [],
          },
        ],
      },
    };
  }
}
