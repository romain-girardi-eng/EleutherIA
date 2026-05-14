#!/usr/bin/env node
/**
 * mock-sse-server.mjs — dev-only mock of the agentic research SSE backend.
 *
 * Implements the AgentEvent contract defined in
 * `frontend/src/types/agent-events.ts`. A single canned sequence is streamed
 * over ~12 seconds with realistic spacing.
 *
 * Usage:
 *   node frontend/scripts/mock-sse-server.mjs            # listens on :8765
 *   VITE_API_PROXY_TARGET=http://localhost:8765 npm run dev
 *
 *   curl -N -X POST http://localhost:8765/api/graphrag/query/stream \
 *        -H 'content-type: application/json' \
 *        -d '{"query":"hello"}'
 */

import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';

const PORT = Number.parseInt(process.env.PORT ?? '8765', 10);

const ALLOW_HEADERS =
  'authorization, content-type, accept, cache-control, x-requested-with';

const buildScript = (query, traceId) => [
  {
    delayMs: 0,
    event: { type: 'agent_start', agent: 'Orchestrator', query, trace_id: traceId },
  },
  {
    delayMs: 150,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'ConceptMapper',
      status: 'started',
      message: 'Identifying key philosophical concepts',
    },
  },
  {
    delayMs: 600,
    event: {
      type: 'tool_call',
      agent: 'ConceptMapper',
      tool: 'search_nodes',
      args: { query, node_types: ['concept', 'person'], limit: 8 },
      id: 'call-1',
    },
  },
  {
    delayMs: 800,
    event: {
      type: 'kg_node_activated',
      node_id: 'person_chrysippus',
      label: 'Chrysippus of Soli',
      node_type: 'person',
      period: 'Hellenistic',
    },
  },
  {
    delayMs: 80,
    event: {
      type: 'kg_node_activated',
      node_id: 'concept_fate',
      label: 'Heimarmenê',
      node_type: 'concept',
      period: 'Hellenistic',
    },
  },
  {
    delayMs: 80,
    event: {
      type: 'kg_node_activated',
      node_id: 'concept_prohairesis',
      label: 'Prohairesis',
      node_type: 'concept',
    },
  },
  {
    delayMs: 200,
    event: {
      type: 'tool_result',
      tool_call_id: 'call-1',
      result_summary: 'Found 12 relevant concept and person nodes.',
      nodes_touched: ['person_chrysippus', 'concept_fate', 'concept_prohairesis'],
      duration_ms: 240,
    },
  },
  {
    delayMs: 400,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'ConceptMapper',
      status: 'complete',
    },
  },
  {
    delayMs: 200,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'SourceFinder',
      status: 'started',
      message: 'Looking up canonical passages',
    },
  },
  {
    delayMs: 400,
    event: {
      type: 'tool_call',
      agent: 'SourceFinder',
      tool: 'search_passages',
      args: { query, work_ids: ['cicero_de_fato'], limit: 5 },
      id: 'call-2',
    },
  },
  {
    delayMs: 1100,
    event: {
      type: 'citation_found',
      passage_id: 'cicero_de_fato_40',
      cts_urn: 'urn:cts:latinLit:phi0474.phi051:40',
      work_label: 'Cicero, De Fato 40',
      excerpt:
        "Chrysippus likens the cylinder rolled down a slope: the external push is the antecedent cause, but the cylinder's own form is its own cause of motion.",
      node_ids: ['person_chrysippus', 'concept_fate'],
      confidence: 0.91,
    },
  },
  {
    delayMs: 350,
    event: {
      type: 'kg_node_activated',
      node_id: 'work_cicero_de_fato',
      label: 'Cicero, De Fato',
      node_type: 'work',
      period: 'Roman Republican',
    },
  },
  {
    delayMs: 250,
    event: {
      type: 'citation_found',
      passage_id: 'gellius_na_7_2',
      cts_urn: 'urn:cts:latinLit:phi1254.phi001:7.2',
      work_label: 'Gellius, Noctes Atticae 7.2',
      excerpt:
        'Gellius reports the cylinder analogy in nearly identical terms, attributing it explicitly to Chrysippus.',
      node_ids: ['person_chrysippus'],
      confidence: 0.78,
    },
  },
  {
    delayMs: 300,
    event: {
      type: 'tool_result',
      tool_call_id: 'call-2',
      result_summary: '2 high-confidence citations retrieved.',
      passages_touched: ['cicero_de_fato_40', 'gellius_na_7_2'],
      duration_ms: 1620,
    },
  },
  {
    delayMs: 300,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'SourceFinder',
      status: 'complete',
    },
  },
  {
    delayMs: 300,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'TextVerifier',
      status: 'thinking',
      message: 'Cross-checking quotations against canonical text',
    },
  },
  {
    delayMs: 700,
    event: {
      type: 'citation_verified',
      passage_id: 'cicero_de_fato_40',
      verified: true,
      reason: 'Exact match against TLG critical edition.',
    },
  },
  {
    delayMs: 200,
    event: {
      type: 'citation_verified',
      passage_id: 'gellius_na_7_2',
      verified: true,
      reason: 'Paraphrase consistent with attested wording.',
    },
  },
  {
    delayMs: 300,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'TextVerifier',
      status: 'complete',
    },
  },
  {
    delayMs: 200,
    event: {
      type: 'agent_step',
      agent: 'Orchestrator',
      subagent: 'Synthesizer',
      status: 'started',
      message: 'Composing the scholarly answer',
    },
  },
  ...[
    'Chrysippus distinguishes ',
    '**antecedent** from ',
    '**principal** causes ',
    'to preserve moral responsibility within a fated cosmos. ',
    'The clearest formulation survives in Cicero, *De Fato* 40 [Source 1], ',
    'and is independently confirmed by Gellius [Source 2]. ',
    'On this reading, the soul\'s assent (συγκατάθεσις) ',
    'is the cylinder\'s own form: external impressions move us, ',
    'but the manner of rolling is determined by what we are.',
  ].map((delta, i) => ({
    delayMs: 220 + i * 30,
    event: { type: 'token', delta },
  })),
  {
    delayMs: 300,
    event: {
      type: 'final_answer',
      answer: [
        'Chrysippus distinguishes **antecedent** from **principal** causes ',
        'to preserve moral responsibility within a fated cosmos. ',
        'The clearest formulation survives in Cicero, *De Fato* 40 [Source 1], ',
        'and is independently confirmed by Gellius [Source 2]. ',
        "On this reading, the soul's assent (συγκατάθεσις) ",
        "is the cylinder's own form: external impressions move us, ",
        'but the manner of rolling is determined by what we are.',
      ].join(''),
      citations: [
        {
          passage_id: 'cicero_de_fato_40',
          claim: 'Distinction between antecedent and principal causes',
          verified: true,
        },
        {
          passage_id: 'gellius_na_7_2',
          claim: 'Independent confirmation of the cylinder analogy',
          verified: true,
        },
      ],
      trace_id: traceId,
    },
  },
];

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://${req.headers.host}`);

  res.setHeader('access-control-allow-origin', '*');
  res.setHeader('access-control-allow-methods', 'GET, POST, OPTIONS');
  res.setHeader('access-control-allow-headers', ALLOW_HEADERS);

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (url.pathname === '/api/graphrag/query/stream' && req.method === 'POST') {
    let body = '';
    for await (const chunk of req) body += chunk;
    let query = 'mock-query';
    try {
      query = JSON.parse(body || '{}').query ?? query;
    } catch {
      // ignore malformed body — use default
    }

    const traceId = randomUUID();
    res.writeHead(200, {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache',
      connection: 'keep-alive',
    });
    res.write(': mock-sse-server ready\n\n');

    const script = buildScript(query, traceId);
    let aborted = false;
    req.on('close', () => {
      aborted = true;
    });

    for (const step of script) {
      if (aborted) break;
      await new Promise((r) => setTimeout(r, step.delayMs));
      res.write(`data: ${JSON.stringify(step.event)}\n\n`);
    }
    res.end();
    return;
  }

  if (
    url.pathname.startsWith('/api/graphrag/query/') &&
    url.pathname.endsWith('/cancel') &&
    req.method === 'POST'
  ) {
    res.writeHead(204);
    res.end();
    return;
  }

  res.writeHead(404, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ error: 'not_found', path: url.pathname }));
});

server.listen(PORT, () => {
  process.stdout.write(`mock-sse-server listening on http://localhost:${PORT}\n`);
});
