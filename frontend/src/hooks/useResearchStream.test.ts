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
});
