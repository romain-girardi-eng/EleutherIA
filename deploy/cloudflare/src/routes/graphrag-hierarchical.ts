/**
 * Hierarchical GraphRAG Routes
 *
 * Implements ArchRAG-style hierarchical retrieval for massive token reduction
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { HierarchicalRetrievalService } from '../services/hierarchical-retrieval';
import { LLMService } from '../services/llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('GraphRAGHierarchicalRoutes');

export const graphragHierarchicalRoutes = new Hono<{ Bindings: Env }>();

// Hierarchical GraphRAG query endpoint
graphragHierarchicalRoutes.post('/query', async (c) => {
  try {
    const body = await c.req.json();
    const { query, maxCommunities = 5, includeStats = true } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const startTime = Date.now();

    const hierarchical = new HierarchicalRetrievalService(c.env);
    const llm = new LLMService(c.env);

    // 1. Hierarchical retrieval (replaces flat vector search)
    const retrieval = await hierarchical.retrieve(query);

    logger.info(
      `Hierarchical retrieval: ${retrieval.communities.length} communities, ~${retrieval.tokenCount} tokens`
    );

    // 2. Generate answer using community summaries as context
    const prompt = `You are a scholarly expert on ancient philosophy and free will debates.

Context from hierarchical knowledge graph (Level ${retrieval.strategy.startLevel}):
${retrieval.context}

Question: ${query}

Provide a comprehensive answer based on the hierarchical context above. Be precise and cite specific philosophical schools or periods when relevant.`;

    const answer = await llm.generate(prompt, 'gemini-3-flash-preview');

    const processingTime = Date.now() - startTime;

    // 3. Build response
    const response: any = {
      answer,
      queryType: retrieval.classification.type,
      retrievalLevel: retrieval.strategy.startLevel,
      communitiesUsed: retrieval.communities.length,
      tokenEstimate: retrieval.tokenCount,
      processingTime,
    };

    if (includeStats) {
      response.stats = {
        classification: retrieval.classification,
        strategy: retrieval.strategy,
        communities: retrieval.communities.map(c => ({
          id: c.id,
          school: c.dominant_school,
          period: c.dominant_period,
          size: c.size,
        })),
      };
    }

    return c.json(response);
  } catch (error) {
    logger.error('Hierarchical GraphRAG query error', error);
    return c.json({
      error: 'Hierarchical GraphRAG query failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

// Compare hierarchical vs standard retrieval
graphragHierarchicalRoutes.post('/compare', async (c) => {
  try {
    const body = await c.req.json();
    const { query } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const hierarchical = new HierarchicalRetrievalService(c.env);

    // Hierarchical retrieval
    const startHier = Date.now();
    const hierRetrieval = await hierarchical.retrieve(query);
    const hierTime = Date.now() - startHier;

    // Comparison metrics
    return c.json({
      query,
      hierarchical: {
        tokenCount: hierRetrieval.tokenCount,
        communitiesRetrieved: hierRetrieval.communities.length,
        level: hierRetrieval.strategy.startLevel,
        time: hierTime,
      },
      standard: {
        tokenCount: 15000, // Estimated for standard retrieval
        nodesRetrieved: 10,
        level: 'atomic',
        time: 'N/A',
      },
      improvement: {
        tokenReduction: `${Math.round((1 - hierRetrieval.tokenCount / 15000) * 100)}%`,
        speedup: 'N/A',
      },
    });
  } catch (error) {
    logger.error('Comparison error', error);
    return c.json({ error: 'Comparison failed' }, 500);
  }
});

// Get hierarchy metadata
graphragHierarchicalRoutes.get('/hierarchy/info', async (c) => {
  try {
    const hierarchical = new HierarchicalRetrievalService(c.env);
    const hierarchy = await hierarchical.loadHierarchy();

    return c.json({
      metadata: hierarchy.metadata,
      levels: hierarchy.hierarchy.levels.map(l => ({
        level: l.level,
        resolution: l.resolution,
        communities: l.num_communities,
      })),
    });
  } catch (error) {
    logger.error('Hierarchy info error', error);
    return c.json({ error: 'Failed to load hierarchy info' }, 500);
  }
});
