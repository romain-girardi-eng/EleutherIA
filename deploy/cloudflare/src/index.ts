/**
 * Ancient Free Will Database API - Cloudflare Workers
 * Main application entry point using Hono framework
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger as honoLogger } from 'hono/logger';
import { prettyJSON } from 'hono/pretty-json';
import { Env } from './types';
import { DatabaseService } from './services/database';
import { QdrantService } from './services/qdrant';
import { LLMService } from './services/llm';
import { getLogger } from './utils/logger';
import { analyticsMiddleware } from './middleware/analytics';
import { resolveCorsOrigin } from './utils/cors';

// Import routes
import { kgRoutes } from './routes/kg';
import { searchRoutes } from './routes/search';
import { graphragRoutes } from './routes/graphrag';
import { graphragHierarchicalRoutes } from './routes/graphrag-hierarchical';
import { graphragAgenticRoutes } from './routes/graphrag-agentic';
import { graphragWorkflowRoutes } from './routes/graphrag-workflow';
import { textRoutes } from './routes/texts';
import { worksRoutes } from './routes/works';
import { authRoutes } from './routes/auth';
import { adminRoutes } from './routes/admin';
import { embeddingsRoutes } from './routes/embeddings';
import { lemmaRoutes } from './routes/lemma';
import { visualPulpitRoutes } from './routes/visual-pulpit';

const logger = getLogger('MainApp');

// Create Hono app
const app = new Hono<{ Bindings: Env }>();

// Middleware
app.use('*', honoLogger());
app.use('*', prettyJSON());
app.use('*', analyticsMiddleware);

// CORS middleware
app.use('*', async (c, next) => {
  const allowedOrigins = c.env.ALLOWED_ORIGINS || '*';

  const corsMiddleware = cors({
    origin: (requestOrigin) => {
      return resolveCorsOrigin(requestOrigin, allowedOrigins) ?? undefined;
    },
    allowHeaders: ['Content-Type', 'Authorization'],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    exposeHeaders: ['Content-Length'],
    maxAge: 600,
    credentials: true,
  });

  return corsMiddleware(c, next);
});

// Root endpoint
app.get('/', (c) => {
  return c.json({
    message: 'Ancient Free Will Database API',
    version: '5.0.0',
    runtime: 'Cloudflare Workers',
    docs: '/api/docs',
    health: '/api/health',
  });
});

// Health check endpoint
app.get('/api/health', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const qdrant = new QdrantService(c.env);
    const llm = new LLMService(c.env);

    const [dbHealth, qdrantHealth, llmHealth] = await Promise.all([
      db.healthCheck(),
      qdrant.healthCheck(),
      llm.healthCheck(),
    ]);

    const status = dbHealth && qdrantHealth && llmHealth ? 'healthy' : 'degraded';

    return c.json({
      status,
      database: dbHealth ? 'connected' : 'disconnected',
      qdrant: qdrantHealth ? 'connected' : 'disconnected',
      llm: llmHealth ? 'available' : 'unavailable',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    logger.error('Health check failed', error);
    return c.json({
      status: 'unhealthy',
      database: 'unknown',
      qdrant: 'unknown',
      llm: 'unknown',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    }, 503);
  }
});

// Mount route modules
app.route('/api/kg', kgRoutes);
app.route('/api/search', searchRoutes);
app.route('/api/graphrag', graphragRoutes);
app.route('/api/graphrag/hierarchical', graphragHierarchicalRoutes);
app.route('/api/graphrag/agentic', graphragAgenticRoutes);
app.route('/api/graphrag/workflow', graphragWorkflowRoutes);
app.route('/api/works', worksRoutes);  // Ancient works API (primary)
app.route('/api/texts', textRoutes);   // Legacy texts API (deprecated)
app.route('/api/text', textRoutes);    // Alias for texts API (used by citation service)
app.route('/api/auth', authRoutes);
app.route('/api/admin', adminRoutes);  // Admin and citation network analytics
app.route('/api/embeddings', embeddingsRoutes);  // Embedding generation (bypasses location restrictions)
app.route('/api/lemma', lemmaRoutes);  // Lemma Intelligence API (dictionary, stats, related)
app.route('/api/visual-pulpit', visualPulpitRoutes);  // Visual Pulpit sermon presentation generator

// 404 handler
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    path: c.req.path,
  }, 404);
});

// Error handler
app.onError((err, c) => {
  logger.error('Unhandled error', err);
  return c.json({
    error: 'Internal Server Error',
    message: err.message,
  }, 500);
});

// Export the app
export default app;
