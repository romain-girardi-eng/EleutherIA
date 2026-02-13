import { Hono } from 'hono';
import { Env } from '../types';
import { getLogger } from '../utils/logger';
import { graphragRoutes } from './graphrag';

const logger = getLogger('GraphRAGWorkflow');
const WORKFLOW_PREFIX = 'graphrag-workflow:job:';

type WorkflowStatus = 'pending' | 'running' | 'complete' | 'failed';

interface WorkflowJob {
  id: string;
  query: string;
  options?: Record<string, any>;
  status: WorkflowStatus;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: any;
  error?: string;
}

export const graphragWorkflowRoutes = new Hono<{ Bindings: Env }>();

function workflowKey(id: string) {
  return `${WORKFLOW_PREFIX}${id}`;
}

async function saveJob(env: Env, job: WorkflowJob) {
  await env.TEXT_CACHE.put(workflowKey(job.id), JSON.stringify(job), {
    expirationTtl: 60 * 60 * 24, // 24 hours
  });
}

async function loadJob(env: Env, id: string): Promise<WorkflowJob | null> {
  const raw = await env.TEXT_CACHE.get(workflowKey(id));
  if (!raw) return null;
  try {
    return JSON.parse(raw) as WorkflowJob;
  } catch (error) {
    logger.error('Failed to parse workflow job', error);
    return null;
  }
}

async function runWorkflowJob(env: Env, job: WorkflowJob, executionCtx: ExecutionContext) {
  const updateJob = async (patch: Partial<WorkflowJob>) => {
    Object.assign(job, patch, { updatedAt: new Date().toISOString() });
    await saveJob(env, job);
  };

  await updateJob({
    status: 'running',
    startedAt: new Date().toISOString(),
  });

  try {
    const payload = {
      query: job.query,
      mode: job.options?.mode ?? 'auto',
      semantic_k: job.options?.limit ?? 12,
      graph_depth: job.options?.graph_depth ?? 3,
      max_context: job.options?.limit ?? 12,
      use_hyde: job.options?.use_hyde ?? true,
      use_expansion: job.options?.use_expansion ?? true,
      use_crag: job.options?.use_crag ?? true,
      use_selfrag: job.options?.use_selfrag ?? true,
      use_reranking: job.options?.use_rerank ?? true,
      use_debates: job.options?.use_debates ?? true,
      use_hierarchy: true,
      use_bridge: true,
      academic_mode: true,
      enhanced_mode: true,
      rigor_level: 'high',
      citation_style: 'chicago',
      mode_label: 'workflow',
    };

    const internalUrl = new URL('/answer', 'https://graphrag-workflow.internal');
    const response = await graphragRoutes.fetch(
      new Request(internalUrl.toString(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
      env as any,
      executionCtx
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`GraphRAG workflow failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();

    await updateJob({
      status: 'complete',
      completedAt: new Date().toISOString(),
      result,
    });
  } catch (error) {
    logger.error('Workflow execution failed', error);
    await updateJob({
      status: 'failed',
      error: error instanceof Error ? error.message : 'Unknown workflow error',
    });
  }
}

graphragWorkflowRoutes.post('/start', async (c) => {
  try {
    const body = await c.req.json<{ query?: string; options?: Record<string, any> }>();
    const query = body.query?.trim();

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const instanceId = crypto.randomUUID();
    const now = new Date().toISOString();
    const job: WorkflowJob = {
      id: instanceId,
      query,
      options: body.options || {},
      status: 'pending',
      createdAt: now,
      updatedAt: now,
    };

    await saveJob(c.env, job);

    c.executionCtx.waitUntil(runWorkflowJob(c.env, job, c.executionCtx));

    return c.json({ instanceId, status: job.status });
  } catch (error) {
    logger.error('Failed to start workflow', error);
    return c.json({ error: 'Failed to start workflow' }, 500);
  }
});

graphragWorkflowRoutes.get('/status/:id', async (c) => {
  const id = c.req.param('id');
  const job = await loadJob(c.env, id);

  if (!job) {
    return c.json({ error: 'Workflow instance not found', status: 'not_found' }, 404);
  }

  return c.json({
    instanceId: id,
    status: job.status,
    result: job.status === 'complete' ? job.result : undefined,
    error: job.status === 'failed' ? job.error : undefined,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    startedAt: job.startedAt,
    completedAt: job.completedAt,
  });
});
