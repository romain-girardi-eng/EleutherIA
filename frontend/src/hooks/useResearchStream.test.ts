import { describe, it, expect } from 'vitest';
import { reduce } from './useResearchStream';
import type {
  CitationFoundEvent,
  FinalAnswerEvent,
  KGNodeActivatedEvent,
  ToolCallEvent,
  ToolResultEvent,
} from '../types/agent-events';

const initial = reduce(undefined as never, { type: 'reset' });

describe('useResearchStream reducer', () => {
  it('tracks agent_start trace id', () => {
    const state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'agent_start',
        agent: 'Orchestrator',
        query: 'q',
        trace_id: 'trace-1',
      },
    });
    expect(state.traceId).toBe('trace-1');
    expect(state.events).toHaveLength(1);
  });

  it('records active subagent on started and removes on complete', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'agent_step',
        agent: 'O',
        subagent: 'SourceFinder',
        status: 'started',
      },
    });
    expect(Object.keys(state.activeSubagents)).toHaveLength(1);
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: {
        type: 'agent_step',
        agent: 'O',
        subagent: 'SourceFinder',
        status: 'complete',
      },
    });
    expect(Object.keys(state.activeSubagents)).toHaveLength(0);
  });

  it('pairs tool_call with tool_result', () => {
    const call: ToolCallEvent = {
      type: 'tool_call',
      agent: 'A',
      tool: 'search_nodes',
      args: { q: 'x' },
      id: 'c1',
    };
    const result: ToolResultEvent = {
      type: 'tool_result',
      tool_call_id: 'c1',
      result_summary: 'ok',
      nodes_touched: ['n1'],
    };
    let state = reduce(initial, { type: 'event', at: 1, event: call });
    state = reduce(state, { type: 'event', at: 2, event: result });
    expect(state.toolCallOrder).toEqual(['c1']);
    expect(state.toolCallsById.c1.result?.result_summary).toBe('ok');
    expect(state.toolCallsById.c1.completed_at).toBe(2);
  });

  it('accumulates citations and respects insertion order', () => {
    const cit1: CitationFoundEvent = {
      type: 'citation_found',
      passage_id: 'p1',
      excerpt: 'one',
      node_ids: [],
      confidence: 0.8,
    };
    const cit2: CitationFoundEvent = {
      type: 'citation_found',
      passage_id: 'p2',
      excerpt: 'two',
      node_ids: [],
      confidence: 0.5,
    };
    let state = reduce(initial, { type: 'event', at: 1, event: cit1 });
    state = reduce(state, { type: 'event', at: 2, event: cit2 });
    expect(state.citationOrder).toEqual(['p1', 'p2']);
  });

  it('counts kg node hits across repeated activations', () => {
    const ev: KGNodeActivatedEvent = {
      type: 'kg_node_activated',
      node_id: 'n1',
      label: 'Node One',
      node_type: 'concept',
    };
    let state = reduce(initial, { type: 'event', at: 1, event: ev });
    state = reduce(state, { type: 'event', at: 2, event: ev });
    state = reduce(state, { type: 'event', at: 3, event: ev });
    expect(state.kgActivationsById.n1.hits).toBe(3);
    expect(state.kgActivationsById.n1.last_seen).toBe(3);
  });

  it('appends streamed tokens to the answer', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: { type: 'token', delta: 'Hello ' },
    });
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: { type: 'token', delta: 'world' },
    });
    expect(state.streamedAnswer).toBe('Hello world');
  });

  it('accumulates tokens_used events into running totals', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'tokens_used',
        agent_id: 'scholar-orchestrator',
        model: 'kimi-k2p6',
        provider: 'fireworks',
        prompt_tokens: 4_000,
        completion_tokens: 500,
        total_tokens: 4_500,
        estimated_cost_usd: 0.0051,
      },
    });
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: {
        type: 'tokens_used',
        agent_id: 'concept-mapper',
        model: 'kimi-k2p6',
        provider: 'fireworks',
        prompt_tokens: 2_000,
        completion_tokens: 200,
        total_tokens: 2_200,
        estimated_cost_usd: 0.00238,
      },
    });
    expect(state.tokenUsage.total_tokens).toBe(6_700);
    expect(state.tokenUsage.total_cost_usd).toBeCloseTo(0.00748, 6);
    expect(state.tokenUsage.by_agent['scholar-orchestrator'].tokens).toBe(
      4_500,
    );
    expect(state.tokenUsage.by_agent['concept-mapper'].tokens).toBe(2_200);
    expect(state.tokenUsage.by_model['kimi-k2p6'].calls).toBe(2);
    expect(state.tokenUsage.by_provider['fireworks'].prompt_tokens).toBe(6_000);
  });

  it('replaces totals on cost_summary without losing breakdown', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'tokens_used',
        agent_id: 'scholar-orchestrator',
        model: 'kimi-k2p6',
        provider: 'fireworks',
        prompt_tokens: 10,
        completion_tokens: 2,
        total_tokens: 12,
        estimated_cost_usd: 0.000017,
      },
    });
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: {
        type: 'cost_summary',
        total_tokens: 12_348,
        total_cost_usd: 0.0212,
        by_model: { 'kimi-k2p6': { tokens: 12_348, cost_usd: 0.0212, calls: 7 } },
        by_agent: {
          'scholar-orchestrator': { tokens: 12_348, cost_usd: 0.0212, calls: 7 },
        },
      },
    });
    expect(state.tokenUsage.total_tokens).toBe(12_348);
    expect(state.tokenUsage.total_cost_usd).toBeCloseTo(0.0212, 6);
    expect(state.tokenUsage.by_model['kimi-k2p6'].calls).toBe(7);
  });

  it('raises the floor on tokens_used_rollup but keeps higher totals', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'tokens_used',
        agent_id: 'scholar-orchestrator',
        model: 'kimi-k2p6',
        provider: 'fireworks',
        prompt_tokens: 1_000,
        completion_tokens: 200,
        total_tokens: 1_200,
        estimated_cost_usd: 0.00153,
      },
    });
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: {
        type: 'tokens_used_rollup',
        total_tokens: 800,
        total_cost_usd: 0.001,
      },
    });
    // Should not lose the 1,200 already accumulated.
    expect(state.tokenUsage.total_tokens).toBe(1_200);
  });

  it('reconciles citation verification flags on final_answer', () => {
    const cit: CitationFoundEvent = {
      type: 'citation_found',
      passage_id: 'p1',
      excerpt: 'one',
      node_ids: [],
      confidence: 0.8,
    };
    const final: FinalAnswerEvent = {
      type: 'final_answer',
      answer: 'answer',
      citations: [{ passage_id: 'p1', claim: 'c', verified: true }],
      trace_id: 't1',
    };
    let state = reduce(initial, { type: 'event', at: 1, event: cit });
    state = reduce(state, { type: 'event', at: 2, event: final });
    expect(state.citationsById.p1.verified).toBe(true);
    expect(state.finalAnswer?.trace_id).toBe('t1');
    expect(state.status).toBe('complete');
  });

  it('accumulates citation_verified verdicts for unknown ids instead of dropping them', () => {
    // Verdict arrives BEFORE its citation_found (node-shaped id / audit race).
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'citation_verified',
        passage_id: 'p-early',
        verified: false,
        reason: '[REJECTED] does not support the claim',
      },
    });
    expect(state.citationsById['p-early']).toBeUndefined();
    expect(state.pendingVerifications['p-early']).toEqual({
      verified: false,
      reason: '[REJECTED] does not support the claim',
    });

    // The citation lands later — the stored verdict must be applied.
    const cit: CitationFoundEvent = {
      type: 'citation_found',
      passage_id: 'p-early',
      excerpt: 'one',
      node_ids: [],
      confidence: 0.8,
    };
    state = reduce(state, { type: 'event', at: 2, event: cit });
    expect(state.citationsById['p-early'].verified).toBe(false);
    expect(state.citationsById['p-early'].verification_reason).toBe(
      '[REJECTED] does not support the claim',
    );
  });

  it('reconciles pending verdicts on final_answer', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: {
        type: 'citation_verified',
        passage_id: 'p1',
        verified: true,
        reason: '[VERIFIED] ok',
      },
    });
    const cit: CitationFoundEvent = {
      type: 'citation_found',
      passage_id: 'p1',
      excerpt: 'one',
      node_ids: [],
      confidence: 0.8,
    };
    state = reduce(state, { type: 'event', at: 2, event: cit });
    const final: FinalAnswerEvent = {
      type: 'final_answer',
      answer: 'answer',
      citations: [],
      trace_id: 't1',
    };
    state = reduce(state, { type: 'event', at: 3, event: final });
    expect(state.citationsById.p1.verified).toBe(true);
  });

  it('flags streamed prose as pending verification until citation_audit completes', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: { type: 'token', delta: 'Chrysippus ' },
    });
    expect(state.answerVerification).toBe('pending');

    state = reduce(state, {
      type: 'event',
      at: 2,
      event: { type: 'stage_complete', stage: 'citation_audit', duration_ms: 1200 },
    });
    expect(state.answerVerification).toBe('verified');
  });

  it('marks the answer verified on final_answer even without a citation_audit stage', () => {
    let state = reduce(initial, {
      type: 'event',
      at: 1,
      event: { type: 'token', delta: 'text' },
    });
    state = reduce(state, {
      type: 'event',
      at: 2,
      event: {
        type: 'final_answer',
        answer: 'answer',
        citations: [],
        trace_id: 't1',
      },
    });
    expect(state.answerVerification).toBe('verified');
  });
});
