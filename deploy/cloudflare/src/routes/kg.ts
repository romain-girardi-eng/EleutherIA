/**
 * Knowledge Graph Routes
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { KGAnalyticsService, KGFilterState } from '../services/kg-analytics';
import { getLogger } from '../utils/logger';
import { sanitizeNodePayload } from '../utils/graph';

const logger = getLogger('KGRoutes');

export const kgRoutes = new Hono<{ Bindings: Env }>();

/**
 * Parse filter parameters from query string
 */
function parseFilters(c: any): KGFilterState {
  const nodeTypes = c.req.query('nodeTypes');
  const periods = c.req.query('periods');
  const schools = c.req.query('schools');
  const relations = c.req.query('relations');
  const searchTerm = c.req.query('searchTerm');

  return {
    nodeTypes: nodeTypes ? nodeTypes.split(',').filter(Boolean) : undefined,
    periods: periods ? periods.split(',').filter(Boolean) : undefined,
    schools: schools ? schools.split(',').filter(Boolean) : undefined,
    relations: relations ? relations.split(',').filter(Boolean) : undefined,
    searchTerm: searchTerm || undefined,
  };
}

// Get all nodes with optional filters
kgRoutes.get('/nodes', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const type = c.req.query('type');
    const period = c.req.query('period');
    const school = c.req.query('school');

    const filters: any = {};
    if (type) filters.type = type;
    if (period) filters.period = period;
    if (school) filters.school = school;

    const result = await db.getNodes(Object.keys(filters).length > 0 ? filters : undefined);
    return c.json({ nodes: result.rows, total: result.rows.length });
  } catch (error) {
    logger.error('Error fetching nodes', error);
    return c.json({ error: 'Failed to fetch nodes' }, 500);
  }
});

// Get all edges with optional filters
kgRoutes.get('/edges', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const relation = c.req.query('relation');

    const filters: any = {};
    if (relation) filters.relation = relation;

    const result = await db.getEdges(Object.keys(filters).length > 0 ? filters : undefined);
    return c.json({ edges: result.rows, total: result.rows.length });
  } catch (error) {
    logger.error('Error fetching edges', error);
    return c.json({ error: 'Failed to fetch edges' }, 500);
  }
});

// Get specific node by ID
kgRoutes.get('/node/:id', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const id = c.req.param('id');

    const node = await db.getNode(id);

    if (!node) {
      return c.json({ error: 'Node not found' }, 404);
    }

    return c.json(node);
  } catch (error) {
    logger.error('Error fetching node', error);
    return c.json({ error: 'Failed to fetch node' }, 500);
  }
});

// Get node connections
kgRoutes.get('/node/:id/connections', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const id = c.req.param('id');

    const connections = await db.getNodeConnections(id);
    return c.json(connections);
  } catch (error) {
    logger.error('Error fetching node connections', error);
    return c.json({ error: 'Failed to fetch node connections' }, 500);
  }
});

// Get KG statistics
kgRoutes.get('/stats', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const stats = await db.getKGStats();
    return c.json(stats);
  } catch (error) {
    logger.error('Error fetching KG stats', error);
    return c.json({ error: 'Failed to fetch KG stats' }, 500);
  }
});

// Get Cytoscape visualization data
kgRoutes.get('/viz/cytoscape', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analytics = new KGAnalyticsService(db);
    const algorithm = c.req.query('communityAlgorithm') || 'auto';

    // Get nodes and edges (DatabaseService normalizes column names: node_id→id, source_id→source, etc.)
    const [nodesResult, edgesResult] = await Promise.all([
      db.getNodes(),
      db.getEdges(),
    ]);

    const sanitizedNodes = nodesResult.rows.map(sanitizeNodePayload);
    const rawEdges = edgesResult.rows as Array<Record<string, any>>;

    // Run community detection
    const communityResult = await analytics.detectCommunities(algorithm);

    // Create a set of valid node IDs for edge validation
    const validNodeIds = new Set(sanitizedNodes.map(node => node.id));

    // Transform to Cytoscape format with community IDs
    const nodes = sanitizedNodes.map(node => ({
      data: {
        ...node,
        communityId: communityResult.nodeAssignments[node.id] ?? null,
        communityColor: communityResult.nodeAssignments[node.id] !== undefined
          ? communityResult.colors[communityResult.nodeAssignments[node.id]]
          : null,
      },
    }));

    // Filter edges to only include those where both source and target nodes exist
    const validEdges = rawEdges.filter(edge =>
      validNodeIds.has(edge.source) && validNodeIds.has(edge.target)
    );

    const edges = validEdges.map(edge => ({
      data: {
        ...edge,
      },
    }));

    // Build metadata with community info
    const meta = {
      community: {
        algorithmRequested: algorithm,
        algorithmUsed: communityResult.algorithmUsed,
        quality: communityResult.quality,
        communities: communityResult.communities,
        availableAlgorithms: communityResult.availableAlgorithms,
      },
    };

    return c.json({
      elements: { nodes, edges },
      meta
    });
  } catch (error) {
    logger.error('Error generating Cytoscape data', error);
    return c.json({ error: 'Failed to generate visualization data' }, 500);
  }
});

// Analytics endpoints
kgRoutes.get('/analytics/timeline', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analytics = new KGAnalyticsService(db);
    const filters = parseFilters(c);

    const result = await analytics.buildTimelineOverview(filters);
    return c.json(result);
  } catch (error) {
    logger.error('Error building timeline overview', error);
    return c.json({ error: 'Failed to build timeline overview' }, 500);
  }
});

kgRoutes.get('/analytics/argument-flow', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analytics = new KGAnalyticsService(db);
    const filters = parseFilters(c);

    const result = await analytics.buildArgumentEvidence(filters);
    return c.json(result);
  } catch (error) {
    logger.error('Error building argument evidence', error);
    return c.json({ error: 'Failed to build argument evidence' }, 500);
  }
});

kgRoutes.get('/analytics/concept-clusters', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analytics = new KGAnalyticsService(db);
    const filters = parseFilters(c);

    const result = await analytics.buildConceptClusters(filters);
    return c.json(result);
  } catch (error) {
    logger.error('Error building concept clusters', error);
    return c.json({ error: 'Failed to build concept clusters' }, 500);
  }
});

kgRoutes.get('/analytics/influence-matrix', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const analytics = new KGAnalyticsService(db);
    const filters = parseFilters(c);

    const result = await analytics.buildInfluenceMatrix(filters);
    return c.json(result);
  } catch (error) {
    logger.error('Error building influence matrix', error);
    return c.json({ error: 'Failed to build influence matrix' }, 500);
  }
});

kgRoutes.post('/analytics/path', async (c) => {
  return c.json({ message: 'Path computation not yet implemented' }, 501);
});
