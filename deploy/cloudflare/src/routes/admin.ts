/**
 * Admin Routes for Citation Network Analytics
 * Provides endpoints for citation network analysis and data quality monitoring
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { CitationNetworkAnalyzer } from '../services/citation-network';
import { getLogger } from '../utils/logger';

const logger = getLogger('AdminRoutes');

export const adminRoutes = new Hono<{ Bindings: Env }>();

/**
 * GET /api/admin/qdrant/info
 * Diagnostic endpoint to check Qdrant Cloud collections and configuration
 */
adminRoutes.get('/qdrant/info', async (c) => {
  try {
    const qdrantHost = c.env.QDRANT_HOST;
    const hasApiKey = !!c.env.QDRANT_API_KEY;

    // Get collection info using QdrantService
    const response = await fetch(`https://${qdrantHost}/collections`, {
      headers: {
        'api-key': c.env.QDRANT_API_KEY,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Qdrant request failed: ${response.statusText}`);
    }

    const data = await response.json();

    return c.json({
      qdrant_host: qdrantHost,
      has_api_key: hasApiKey,
      collections: data.result.collections.map((col: any) => ({
        name: col.name,
        points_count: col.points_count,
        vectors_count: col.vectors_count,
      })),
      total_collections: data.result.collections.length,
    });
  } catch (error) {
    logger.error('Error fetching Qdrant info', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        qdrant_host: c.env.QDRANT_HOST || 'not set',
        has_api_key: !!c.env.QDRANT_API_KEY,
      },
      500
    );
  }
});

/**
 * POST /api/admin/qdrant/create-dual-collections
 * Create dual-vector collections in Qdrant Cloud for dual-embedding system
 */
adminRoutes.post('/qdrant/create-dual-collections', async (c) => {
  try {
    const qdrantHost = c.env.QDRANT_HOST;
    const qdrantApiKey = c.env.QDRANT_API_KEY;

    logger.info('Creating dual-vector collections in Qdrant Cloud');

    const collections = [
      { name: 'passages_dual', description: 'Passage chunks with SPhilBERTa + Gemini embeddings' },
      { name: 'kg_nodes_dual', description: 'KG nodes with SPhilBERTa + Gemini embeddings' },
      { name: 'kg_edges_dual', description: 'KG edges with SPhilBERTa + Gemini embeddings' },
    ];

    const results = [];

    for (const collection of collections) {
      logger.info(`Creating collection: ${collection.name}`);

      try {
        const createResponse = await fetch(
          `https://${qdrantHost}/collections/${collection.name}`,
          {
            method: 'PUT',
            headers: {
              'api-key': qdrantApiKey,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              vectors: {
                sphilberta: { size: 768, distance: 'Cosine' },
                gemini: { size: 3072, distance: 'Cosine' },
              },
            }),
          }
        );

        if (!createResponse.ok) {
          const errorText = await createResponse.text();
          throw new Error(`${createResponse.statusText} - ${errorText}`);
        }

        results.push({ name: collection.name, status: 'created', description: collection.description });
        logger.info(`✓ Created ${collection.name}`);
      } catch (error) {
        results.push({
          name: collection.name,
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error',
        });
        logger.error(`✗ Failed to create ${collection.name}`, error);
      }
    }

    return c.json({
      message: 'Dual-vector collections creation completed',
      results,
      total_attempted: collections.length,
      successful: results.filter((r) => r.status === 'created').length,
      failed: results.filter((r) => r.status === 'error').length,
    });
  } catch (error) {
    logger.error('Error creating dual-vector collections', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'Failed to create dual-vector collections',
      },
      500
    );
  }
});

/**
 * POST /api/admin/qdrant/upload-batch
 * Upload batch of points to Qdrant Cloud collection
 * Body: { collection_name: string, points: Point[] }
 */
adminRoutes.post('/qdrant/upload-batch', async (c) => {
  try {
    const body = await c.req.json();
    const { collection_name, points } = body;

    if (!collection_name || !points || !Array.isArray(points)) {
      return c.json({ error: 'collection_name and points array required' }, 400);
    }

    const qdrantHost = c.env.QDRANT_HOST;
    const qdrantApiKey = c.env.QDRANT_API_KEY;

    // Upload points to Qdrant Cloud
    const uploadResponse = await fetch(
      `https://${qdrantHost}/collections/${collection_name}/points`,
      {
        method: 'PUT',
        headers: {
          'api-key': qdrantApiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ points }),
      }
    );

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      throw new Error(`Upload failed: ${uploadResponse.statusText} - ${errorText}`);
    }

    const result = await uploadResponse.json();

    return c.json({
      success: true,
      collection: collection_name,
      uploaded: points.length,
      result,
    });
  } catch (error) {
    logger.error('Error uploading batch to Qdrant', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        success: false,
      },
      500
    );
  }
});

/**
 * Get comprehensive citation network analysis
 *
 * Returns:
 * - Top influential nodes (PageRank-based)
 * - Citation clusters (community detection)
 * - Bridge figures (connecting different schools/periods)
 * - Temporal influence flow
 */
adminRoutes.get('/citation-network', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analyzer = new CitationNetworkAnalyzer(db);

    const analysis = await analyzer.getFullAnalysis();

    logger.info(
      `Citation network analysis served - top_influential: ${analysis.top_influential.length}`
    );

    return c.json(analysis);
  } catch (error) {
    logger.error('Error in citation network analysis', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
      },
      500
    );
  }
});

/**
 * Export citation network in Gephi-compatible format
 *
 * Returns nodes and edges suitable for GraphML import into Gephi
 */
adminRoutes.get('/citation-network/export-gephi', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analyzer = new CitationNetworkAnalyzer(db);

    await analyzer.loadGraphData();
    const gephiData = analyzer.exportForGephi();

    logger.info(
      `Citation network Gephi export - nodes: ${gephiData.metadata.node_count}, edges: ${gephiData.metadata.edge_count}`
    );

    return c.json(gephiData);
  } catch (error) {
    logger.error('Error exporting for Gephi', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
      },
      500
    );
  }
});

/**
 * Get top N most influential nodes in the knowledge graph
 *
 * Uses PageRank-based algorithm to calculate influence scores
 */
adminRoutes.get('/citation-network/top-influential', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') || '20');
    const db = new DatabaseService(c.env);
    const analyzer = new CitationNetworkAnalyzer(db);

    await analyzer.loadGraphData();
    const topNodes = analyzer.getTopInfluential(limit);

    return c.json({
      top_influential: topNodes,
      count: topNodes.length,
    });
  } catch (error) {
    logger.error('Error getting top influential', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
      },
      500
    );
  }
});

/**
 * Identify bridge figures that connect different philosophical traditions
 *
 * These are nodes that cite or are cited across multiple schools/periods
 */
adminRoutes.get('/citation-network/bridges', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analyzer = new CitationNetworkAnalyzer(db);

    await analyzer.loadGraphData();
    const bridges = analyzer.findBridgeFigures();

    return c.json({
      bridges,
      count: bridges.length,
    });
  } catch (error) {
    logger.error('Error finding bridges', error);
    return c.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
      },
      500
    );
  }
});
