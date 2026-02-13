/**
 * Embedding Generation Routes
 * Provides batch embedding generation using Cloudflare Workers (US datacenter)
 * Bypasses Gemini API location restrictions by executing in Cloudflare's infrastructure
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { LLMService } from '../services/llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('EmbeddingsRoutes');

export const embeddingsRoutes = new Hono<{ Bindings: Env }>();

/**
 * POST /api/embeddings/batch
 * Generate embeddings for multiple texts
 *
 * Body: {
 *   texts: string[],
 *   model?: string,
 *   output_dimensionality?: number
 * }
 *
 * Returns: {
 *   embeddings: number[][],
 *   count: number,
 *   model: string,
 *   dimensions: number
 * }
 */
embeddingsRoutes.post('/batch', async (c) => {
  try {
    const body = await c.req.json();
    const { texts, model = 'models/gemini-embedding-001', output_dimensionality = 3072 } = body;

    // Validation
    if (!texts || !Array.isArray(texts)) {
      return c.json({ error: 'texts array is required' }, 400);
    }

    if (texts.length === 0) {
      return c.json({ error: 'texts array cannot be empty' }, 400);
    }

    if (texts.length > 100) {
      return c.json({ error: 'Maximum 100 texts per batch to avoid timeouts' }, 400);
    }

    // Validate all texts are strings
    const invalidTexts = texts.filter((t: any) => typeof t !== 'string');
    if (invalidTexts.length > 0) {
      return c.json({ error: 'All texts must be strings' }, 400);
    }

    logger.info(`Generating ${texts.length} embeddings with ${model} (${output_dimensionality}d)`);

    const llm = new LLMService(c.env);
    const embeddings = await llm.batchEmbed(texts);

    logger.info(`✓ Successfully generated ${embeddings.length} embeddings`);

    return c.json({
      embeddings,
      count: embeddings.length,
      model,
      dimensions: output_dimensionality,
      worker_region: c.req.header('cf-ray')?.split('-')[1] || 'unknown',
    });

  } catch (error: any) {
    logger.error('Batch embedding generation failed', error);
    return c.json({
      error: error.message || 'Internal server error',
      details: error.toString(),
      hint: 'Check Cloudflare Worker logs for details'
    }, 500);
  }
});

/**
 * POST /api/embeddings/single
 * Generate embedding for single text
 *
 * Body: {
 *   text: string,
 *   model?: string
 * }
 */
embeddingsRoutes.post('/single', async (c) => {
  try {
    const body = await c.req.json();
    const { text, model = 'models/gemini-embedding-001' } = body;

    if (!text || typeof text !== 'string') {
      return c.json({ error: 'text string is required' }, 400);
    }

    if (text.length === 0) {
      return c.json({ error: 'text cannot be empty' }, 400);
    }

    if (text.length > 20000) {
      return c.json({ error: 'text too long (max 20,000 characters)' }, 400);
    }

    logger.info(`Generating single embedding with ${model}`);

    const llm = new LLMService(c.env);
    const embedding = await llm.embed(text);

    return c.json({
      embedding,
      dimensions: embedding.length,
      model,
      worker_region: c.req.header('cf-ray')?.split('-')[1] || 'unknown',
    });

  } catch (error: any) {
    logger.error('Single embedding generation failed', error);
    return c.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, 500);
  }
});

/**
 * GET /api/embeddings/health
 * Health check for embedding service
 * Tests embedding generation with a simple text
 */
embeddingsRoutes.get('/health', async (c) => {
  try {
    const llm = new LLMService(c.env);

    // Test embedding generation
    const startTime = Date.now();
    const testEmbedding = await llm.embed('test');
    const latencyMs = Date.now() - startTime;

    return c.json({
      status: 'healthy',
      embedding_dimensions: testEmbedding.length,
      model: 'models/gemini-embedding-001',
      worker_region: c.req.header('cf-ray')?.split('-')[1] || 'unknown',
      latency_ms: latencyMs,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    logger.error('Embedding health check failed', error);
    return c.json({
      status: 'unhealthy',
      error: error.message,
      details: error.toString(),
      timestamp: new Date().toISOString(),
    }, 500);
  }
});

/**
 * POST /api/embeddings/visualize
 * Generate embedding and find similar items for 3D visualization
 * Returns the embedding, similar nodes, and 3D coordinates
 *
 * Body: {
 *   text: string
 * }
 */
embeddingsRoutes.post('/visualize', async (c) => {
  try {
    const body = await c.req.json();
    const { text } = body;

    if (!text || typeof text !== 'string') {
      return c.json({ error: 'text string is required' }, 400);
    }

    if (text.length > 2000) {
      return c.json({ error: 'text too long (max 2000 characters for visualization)' }, 400);
    }

    logger.info(`Generating embedding for visualization: "${text.slice(0, 50)}..."`);

    // Import Qdrant service
    const { QdrantService } = await import('../services/qdrant');
    const llm = new LLMService(c.env);
    const qdrant = new QdrantService(c.env);

    // Generate embedding
    const startTime = Date.now();
    const embedding = await llm.embed(text);
    const embedTime = Date.now() - startTime;

    // Search for similar KG nodes
    const searchStart = Date.now();
    const similarNodes = await qdrant.searchNodes(embedding, 10, 0.3);
    const searchTime = Date.now() - searchStart;

    // Calculate 3D coordinates using PCA-like projection
    // Take specific dimensions that capture semantic variance
    const dim1 = embedding.slice(0, 256).reduce((a, b) => a + b, 0) / 256;
    const dim2 = embedding.slice(256, 512).reduce((a, b) => a + b, 0) / 256;
    const dim3 = embedding.slice(512, 768).reduce((a, b) => a + b, 0) / 256;

    // Scale to match KG node positions in semantic-space (-40 to 40 range)
    // Embedding averages are ~0.001-0.002, so need large scale
    const scale = 25000;
    const position3d = {
      x: dim1 * scale,
      y: dim2 * scale,
      z: dim3 * scale,
    };

    // Helper to extract school from node_id pattern
    const extractSchoolFromNodeId = (nodeId: string): string => {
      const lower = nodeId.toLowerCase();
      if (lower.includes('stoic') || lower.includes('chrysippus') || lower.includes('epictetus') ||
          lower.includes('marcus_aurelius') || lower.includes('seneca') || lower.includes('zeno_of_citium') ||
          lower.includes('heimarmene') || lower.includes('logos') || lower.includes('cofatal')) {
        return 'Stoic';
      }
      if (lower.includes('epicur') || lower.includes('lucretius') || lower.includes('clinamen') ||
          lower.includes('swerve') || lower.includes('atom')) {
        return 'Epicurean';
      }
      if (lower.includes('aristotl') || lower.includes('peripatetic') || lower.includes('alexander_of_aphrodisias') ||
          lower.includes('deliberat') || lower.includes('potentiality') || lower.includes('actuality')) {
        return 'Aristotelian';
      }
      if (lower.includes('plato') || lower.includes('academic') || lower.includes('socrat') ||
          lower.includes('carneades') || lower.includes('middle_platon') || lower.includes('neoplatonist')) {
        return 'Platonic';
      }
      if (lower.includes('pyrrhon') || lower.includes('sextus') || lower.includes('skeptic')) {
        return 'Skeptic';
      }
      if (lower.includes('augustin') || lower.includes('origen') || lower.includes('pelagian') ||
          lower.includes('boethian') || lower.includes('christian') || lower.includes('church_father')) {
        return 'Christian';
      }
      if (lower.includes('free_will') || lower.includes('determinism') || lower.includes('compatibil') ||
          lower.includes('moral_responsibility') || lower.includes('eph_hemin') || lower.includes('up_to_us') ||
          lower.includes('libert') || lower.includes('freedom') || lower.includes('choice') || lower.includes('volunt')) {
        return 'Core';
      }
      return 'Unknown';
    };

    // Determine semantic cluster based on similar nodes
    const clusterCounts: Record<string, number> = {};
    for (const node of similarNodes) {
      const nodeId = node.payload?.node_id || '';
      const school = node.payload?.school || node.payload?.category || extractSchoolFromNodeId(nodeId);
      clusterCounts[school] = (clusterCounts[school] || 0) + node.score;
    }

    // Filter out Unknown from dominant cluster selection if possible
    const sortedClusters = Object.entries(clusterCounts)
      .filter(([name]) => name !== 'Unknown')
      .sort((a, b) => b[1] - a[1]);

    const dominantCluster = sortedClusters[0]?.[0] || 'Core';

    // Map clusters to colors
    const clusterColors: Record<string, string> = {
      'Stoic': '#60a5fa',
      'Stoicism': '#60a5fa',
      'Epicurean': '#c084fc',
      'Epicureanism': '#c084fc',
      'Peripatetic': '#4ade80',
      'Aristotelian': '#4ade80',
      'Platonic': '#f472b6',
      'Platonism': '#f472b6',
      'Academic': '#f472b6',
      'Core': '#fbbf24',
      'Free Will': '#fbbf24',
      'Unknown': '#ffffff',
    };

    logger.info(`✓ Visualization embedding generated in ${embedTime}ms, search in ${searchTime}ms`);

    return c.json({
      text,
      embedding: embedding.slice(0, 32), // Return first 32 dims for display
      full_dimensions: embedding.length,
      position_3d: position3d,
      cluster: dominantCluster,
      cluster_color: clusterColors[dominantCluster] || '#ffffff',
      similar_nodes: similarNodes.map(node => ({
        id: node.payload?.node_id,
        name: node.payload?.name,
        school: node.payload?.school || node.payload?.category,
        score: node.score,
      })),
      timing: {
        embed_ms: embedTime,
        search_ms: searchTime,
        total_ms: embedTime + searchTime,
      },
      worker_region: c.req.header('cf-ray')?.split('-')[1] || 'unknown',
    });

  } catch (error: any) {
    logger.error('Visualization embedding failed', error);
    return c.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, 500);
  }
});

/**
 * GET /api/embeddings/info
 * Get information about available embedding models
 */
embeddingsRoutes.get('/info', (c) => {
  return c.json({
    available_models: [
      {
        name: 'models/gemini-embedding-001',
        dimensions: '128-3072 (configurable)',
        description: 'Current Gemini embedding model with Matryoshka Representation Learning',
        recommended: true,
        recommended_dimensions: [768, 1536, 3072],
      }
    ],
    batch_limits: {
      max_texts_per_batch: 100,
      max_text_length: 20000,
    },
    worker_info: {
      runtime: 'Cloudflare Workers',
      region: 'Auto-routed (typically US)',
      purpose: 'Bypass Gemini API location restrictions',
    }
  });
});

/**
 * GET /api/embeddings/semantic-space
 * Get real KG nodes with their embeddings for 3D visualization
 * Returns nodes grouped by philosophical school with 3D positions computed from real embeddings
 */
embeddingsRoutes.get('/semantic-space', async (c) => {
  try {
    const { QdrantService } = await import('../services/qdrant');
    const qdrant = new QdrantService(c.env);

    logger.info('Fetching real KG nodes for semantic space visualization');

    // Get sample nodes with vectors (more nodes = richer visualization)
    const nodes = await qdrant.getSampleNodesBySchool(50);

    // School color mapping
    const schoolColors: Record<string, string> = {
      'Stoic': '#60a5fa',      // Blue
      'Stoicism': '#60a5fa',
      'Epicurean': '#c084fc',   // Purple
      'Epicureanism': '#c084fc',
      'Peripatetic': '#4ade80', // Green
      'Aristotelian': '#4ade80',
      'Platonic': '#f472b6',    // Pink
      'Platonism': '#f472b6',
      'Academic': '#f472b6',
      'Skeptic': '#f97316',     // Orange
      'Christian': '#22d3ee',   // Cyan
      'Core': '#fbbf24',        // Yellow/Gold
      'Unknown': '#94a3b8',     // Gray (not white - too bright)
    };

    // Compute 3D positions from real embeddings
    // Use different dimension ranges for x, y, z to get spread
    const nodesWithPositions = nodes.map(node => {
      const vec = node.vector;
      if (!vec || vec.length < 768) {
        // Fallback for nodes without vectors
        return {
          ...node,
          position_3d: {
            x: (Math.random() - 0.5) * 60,
            y: (Math.random() - 0.5) * 60,
            z: (Math.random() - 0.5) * 60,
          },
          color: schoolColors[node.school] || '#ffffff',
          vector: undefined, // Don't send full vector to reduce payload
        };
      }

      // Project 3072-dim embedding to 3D using dimension averaging
      // Use different non-overlapping ranges for x, y, z to get semantic separation
      const dim1 = vec.slice(0, 256).reduce((a: number, b: number) => a + b, 0) / 256;
      const dim2 = vec.slice(256, 512).reduce((a: number, b: number) => a + b, 0) / 256;
      const dim3 = vec.slice(512, 768).reduce((a: number, b: number) => a + b, 0) / 256;

      // Embedding values are VERY small after averaging (-0.002 to 0.002)
      // Scale significantly to get positions in -40 to 40 range
      const scale = 25000;
      return {
        id: node.id,
        node_id: node.node_id,
        name: node.name,
        school: node.school,
        type: node.type,
        position_3d: {
          x: dim1 * scale,
          y: dim2 * scale,
          z: dim3 * scale,
        },
        color: schoolColors[node.school] || '#ffffff',
        // Include first 8 dims for display (like mini sparkline)
        vector_preview: vec.slice(0, 8),
      };
    });

    // Group by school for stats
    const schoolCounts: Record<string, number> = {};
    for (const node of nodesWithPositions) {
      schoolCounts[node.school] = (schoolCounts[node.school] || 0) + 1;
    }

    logger.info(`✓ Returning ${nodesWithPositions.length} real KG nodes for visualization`);

    return c.json({
      nodes: nodesWithPositions,
      total: nodesWithPositions.length,
      schools: schoolCounts,
      metadata: {
        source: 'qdrant',
        collection: 'ancient_free_will_vectors',
        embedding_model: 'gemini-embedding-001',
        dimensions: 3072,
        projection_method: 'dimension_averaging',
      }
    });

  } catch (error: any) {
    logger.error('Semantic space fetch failed', error);
    return c.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, 500);
  }
});
