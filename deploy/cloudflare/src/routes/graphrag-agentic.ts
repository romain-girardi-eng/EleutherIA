/**
 * Agentic GraphRAG Routes
 *
 * Endpoints for multi-agent reasoning system with planning, reasoning,
 * verification, and refinement capabilities.
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { AgenticOrchestrator } from '../services/agentic/orchestrator';
import { getLogger } from '../utils/logger';

const logger = getLogger('GraphRAGAgenticRoutes');

export const graphragAgenticRoutes = new Hono<{ Bindings: Env }>();

/**
 * POST /query - Main agentic GraphRAG endpoint
 *
 * Executes full reasoning pipeline: Plan → Retrieve → Reason → Verify → Refine
 */
graphragAgenticRoutes.post('/query', async (c) => {
  try {
    const body = await c.req.json();
    const {
      query,
      mode, // New: explicit mode selection (auto|local|global|bridge|full)
      maxIterations = 3,
      confidenceThreshold = 0.8,
      skipRefinement = false,
      includeTrace = true,
    } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    // Validate mode if provided
    const validModes = ['auto', 'local', 'global', 'bridge', 'full', 'multi_hop'];
    if (mode && !validModes.includes(mode)) {
      return c.json({
        error: 'Invalid mode',
        details: `Mode must be one of: ${validModes.join(', ')}`
      }, 400);
    }

    const orchestrator = new AgenticOrchestrator(c.env);

    const result = await orchestrator.execute(query, {
      mode, // Pass mode to orchestrator
      maxIterations,
      confidenceThreshold,
      skipRefinement,
    });

    // Build response based on includeTrace flag
    const response: any = {
      answer: result.answer,
      confidence: result.confidence,
      sources: result.sources || [], // Add source citations
      evidenceMap: result.evidenceMap || {}, // Add evidence mapping
      metadata: {
        totalSteps: result.metadata.totalSteps,
        retrievalCalls: result.metadata.retrievalCalls,
        tokensUsed: result.metadata.tokensUsed,
        processingTime: result.metadata.processingTime,
        finalConfidence: result.metadata.finalConfidence,
      },
    };

    if (includeTrace) {
      response.reasoningTrace = {
        steps: result.reasoningTrace.steps.map(step => ({
          id: step.id,
          thought: step.thought,
          action: step.action,
          confidence: step.confidence,
        })),
        contradictions: result.reasoningTrace.contradictions,
      };

      response.verification = {
        isValid: result.verificationResults[0].isValid,
        confidence: result.verificationResults[0].confidence,
        issues: result.verificationResults[0].issues,
      };

      response.refinement = {
        iterations: result.refinementIterations.length,
        finalConfidence: result.confidence,
        gaps: result.refinementIterations.flatMap(i => i.gaps),
      };
    }

    return c.json(response);
  } catch (error) {
    logger.error('Agentic query failed', error);
    return c.json({
      error: 'Agentic query failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

/**
 * POST /query/simple - Simplified agentic query (no refinement)
 *
 * Faster execution: Plan → Retrieve → Reason → Verify (skip refinement)
 */
graphragAgenticRoutes.post('/query/simple', async (c) => {
  try {
    const body = await c.req.json();
    const { query } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const orchestrator = new AgenticOrchestrator(c.env);

    const result = await orchestrator.execute(query, {
      skipRefinement: true,
    });

    return c.json({
      answer: result.answer,
      confidence: result.confidence,
      processingTime: result.metadata.processingTime,
    });
  } catch (error) {
    logger.error('Simple agentic query failed', error);
    return c.json({
      error: 'Simple agentic query failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

/**
 * POST /compare - Compare agentic vs hierarchical performance
 */
graphragAgenticRoutes.post('/compare', async (c) => {
  try {
    const body = await c.req.json();
    const { query } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const orchestrator = new AgenticOrchestrator(c.env);

    // Time agentic execution
    const agenticStart = Date.now();
    const agenticResult = await orchestrator.execute(query);
    const agenticTime = Date.now() - agenticStart;

    return c.json({
      query,
      agentic: {
        confidence: agenticResult.confidence,
        time: agenticTime,
        steps: agenticResult.metadata.totalSteps,
        refinementIterations: agenticResult.refinementIterations.length,
        tokensUsed: agenticResult.metadata.tokensUsed,
      },
      hierarchical: {
        // Would need to run hierarchical query for comparison
        note: 'Run /api/graphrag/hierarchical/query for comparison',
      },
      improvement: {
        confidenceGain: 'Agentic provides confidence scoring',
        verification: 'Agentic includes verification step',
        refinement: `Agentic refined answer ${agenticResult.refinementIterations.length} times`,
      },
    });
  } catch (error) {
    logger.error('Comparison failed', error);
    return c.json({ error: 'Comparison failed' }, 500);
  }
});

/**
 * GET /health - Health check for agentic system
 */
graphragAgenticRoutes.get('/health', async (c) => {
  try {
    const orchestrator = new AgenticOrchestrator(c.env);
    const health = await orchestrator.healthCheck();

    return c.json(health);
  } catch (error) {
    logger.error('Health check failed', error);
    return c.json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

/**
 * POST /debug - Debug endpoint showing detailed reasoning trace
 */
graphragAgenticRoutes.post('/debug', async (c) => {
  try {
    const body = await c.req.json();
    const { query } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const orchestrator = new AgenticOrchestrator(c.env);
    const result = await orchestrator.execute(query);

    // Return full detailed trace for debugging
    return c.json({
      query,
      answer: result.answer,
      fullTrace: {
        plan: result.metadata.plan,
        reasoning: result.reasoningTrace,
        verification: result.verificationResults,
        refinement: result.refinementIterations,
      },
      metadata: result.metadata,
    });
  } catch (error) {
    logger.error('Debug query failed', error);
    return c.json({
      error: 'Debug query failed',
      details: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
    }, 500);
  }
});
