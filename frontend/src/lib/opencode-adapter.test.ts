import { describe, it, expect } from 'vitest';
import {
  OpencodeEventAdapter,
  type OpencodeEvent,
} from './opencode-adapter';
import type {
  AgentStartEvent,
  CitationFoundEvent,
  FinalAnswerEvent,
  KGNodeActivatedEvent,
  ToolCallEvent,
  ToolResultEvent,
} from '../types/agent-events';

const SID = 'ses_test_001';

function adapter(): OpencodeEventAdapter {
  return new OpencodeEventAdapter({ sessionId: SID });
}

describe('OpencodeEventAdapter', () => {
  it('emits agent_start from session.created with prompt', () => {
    const a = adapter();
    const events = a.transform({
      type: 'session.created',
      properties: { sessionID: SID, prompt: 'What is fate?' },
    } as OpencodeEvent);
    expect(events).toHaveLength(1);
    const start = events[0] as AgentStartEvent;
    expect(start.type).toBe('agent_start');
    expect(start.query).toBe('What is fate?');
    expect(start.trace_id).toBe(SID);
  });

  it('emits agent_start only once even on duplicates', () => {
    const a = adapter();
    a.transform({
      type: 'session.created',
      properties: { sessionID: SID, prompt: 'q' },
    } as OpencodeEvent);
    const second = a.transform({
      type: 'session.created',
      properties: { sessionID: SID, prompt: 'q' },
    } as OpencodeEvent);
    expect(second).toHaveLength(0);
  });

  it('drops events whose sessionID does not match', () => {
    const a = adapter();
    const events = a.transform({
      type: 'message.part.delta',
      properties: {
        sessionID: 'ses_other',
        messageID: 'm',
        partID: 'p',
        field: 'text',
        delta: 'hi',
      },
    } as OpencodeEvent);
    expect(events).toHaveLength(0);
  });

  it('maps message.part.delta text → token', () => {
    const a = adapter();
    const events = a.transform({
      type: 'message.part.delta',
      properties: {
        sessionID: SID,
        messageID: 'm',
        partID: 'p',
        field: 'text',
        delta: 'hello',
      },
    } as OpencodeEvent);
    expect(events).toHaveLength(1);
    expect(events[0]).toEqual({ type: 'token', delta: 'hello' });
  });

  it('ignores message.part.delta reasoning field', () => {
    const a = adapter();
    const events = a.transform({
      type: 'message.part.delta',
      properties: {
        sessionID: SID,
        messageID: 'm',
        partID: 'p',
        field: 'reasoning',
        delta: 'thinking',
      },
    } as OpencodeEvent);
    expect(events).toHaveLength(0);
  });

  it('maps session.status busy/idle → agent_step thinking/complete', () => {
    const a = adapter();
    const busy = a.transform({
      type: 'session.status',
      properties: { sessionID: SID, status: { type: 'busy' } },
    } as OpencodeEvent);
    expect(busy[0]).toMatchObject({ type: 'agent_step', status: 'thinking' });
    const idle = a.transform({
      type: 'session.status',
      properties: { sessionID: SID, status: { type: 'idle' } },
    } as OpencodeEvent);
    expect(idle[0]).toMatchObject({ type: 'agent_step', status: 'complete' });
  });

  it('emits tool_call once and tool_result + citation_found on completed search_passages', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_search_passages',
          callID: 'c1',
          state: {
            status: 'completed',
            input: { query: 'fate' },
            output: JSON.stringify({
              passages: [
                {
                  passage_id: 'p_42',
                  cts_urn: 'urn:cts:foo:bar:42',
                  excerpt: 'text',
                  node_ids: ['n1'],
                  confidence: 0.88,
                },
              ],
            }),
            time: { start: 100, end: 240 },
          },
        },
      },
    } as OpencodeEvent);
    const types = out.map((e) => e.type);
    expect(types).toEqual(['tool_call', 'tool_result', 'citation_found']);
    expect((out[0] as ToolCallEvent).id).toBe('c1');
    expect((out[1] as ToolResultEvent).passages_touched).toEqual(['p_42']);
    expect((out[1] as ToolResultEvent).duration_ms).toBe(140);
    expect((out[2] as CitationFoundEvent).passage_id).toBe('p_42');
  });

  it('emits kg_node_activated for search_nodes results', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_search_nodes',
          callID: 'c2',
          state: {
            status: 'completed',
            output: JSON.stringify({
              nodes: [
                { node_id: 'person_chrysippus', label: 'Chrysippus', node_type: 'person' },
                { node_id: 'concept_fate', label: 'Fate', node_type: 'concept' },
              ],
            }),
          },
        },
      },
    } as OpencodeEvent);
    const acts = out.filter(
      (e): e is KGNodeActivatedEvent => e.type === 'kg_node_activated',
    );
    expect(acts).toHaveLength(2);
    expect(acts.map((a) => a.node_id)).toEqual([
      'person_chrysippus',
      'concept_fate',
    ]);
  });

  it('parses single-node get_node_detail responses', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_get_node_detail',
          callID: 'c3',
          state: {
            status: 'completed',
            output: JSON.stringify({
              node_id: 'concept_fate',
              label: 'Fate',
              node_type: 'concept',
              period: 'Hellenistic',
            }),
          },
        },
      },
    } as OpencodeEvent);
    const acts = out.filter((e) => e.type === 'kg_node_activated');
    expect(acts).toHaveLength(1);
    expect((acts[0] as KGNodeActivatedEvent).period).toBe('Hellenistic');
  });

  it('does not re-emit tool_call or tool_result on repeated updates', () => {
    const a = adapter();
    const part = {
      type: 'message.part.updated' as const,
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_search_passages',
          callID: 'c4',
          state: {
            status: 'completed',
            output: JSON.stringify({ passages: [] }),
          },
        },
      },
    };
    const first = a.transform(part as OpencodeEvent);
    const second = a.transform(part as OpencodeEvent);
    expect(first.map((e) => e.type)).toContain('tool_call');
    expect(second).toHaveLength(0);
  });

  it('emits error on failed tool state', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_search_passages',
          callID: 'c5',
          state: { status: 'failed', error: 'timeout' },
        },
      },
    } as OpencodeEvent);
    expect(out.map((e) => e.type)).toContain('error');
  });

  it('synthesises final_answer on session.idle using buffered text', () => {
    const a = adapter();
    a.transform({
      type: 'session.created',
      properties: { sessionID: SID, prompt: 'q' },
    } as OpencodeEvent);
    a.transform({
      type: 'message.part.delta',
      properties: {
        sessionID: SID,
        messageID: 'm',
        partID: 'p',
        field: 'text',
        delta: 'Hello world',
      },
    } as OpencodeEvent);
    const out = a.transform({
      type: 'session.idle',
      properties: { sessionID: SID },
    } as OpencodeEvent);
    const final = out.find(
      (e): e is FinalAnswerEvent => e.type === 'final_answer',
    );
    expect(final).toBeTruthy();
    expect(final?.answer).toBe('Hello world');
    expect(final?.trace_id).toBe(SID);
  });

  it('emits final_answer only once on duplicate session.idle', () => {
    const a = adapter();
    a.transform({
      type: 'session.idle',
      properties: { sessionID: SID },
    } as OpencodeEvent);
    const second = a.transform({
      type: 'session.idle',
      properties: { sessionID: SID },
    } as OpencodeEvent);
    expect(second).toHaveLength(0);
  });

  it('parses verifier tool results into citation_verified', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_verify_citation',
          callID: 'cv1',
          state: {
            status: 'completed',
            output: JSON.stringify({
              passage_id: 'p_42',
              verified: true,
              claim: 'cylinder analogy',
              reason: 'matches edition',
            }),
          },
        },
      },
    } as OpencodeEvent);
    const verified = out.find((e) => e.type === 'citation_verified');
    expect(verified).toMatchObject({ passage_id: 'p_42', verified: true });
  });

  it('parses counter-evidence tool results as citation_found with capped confidence', () => {
    const a = adapter();
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'eleutheria_find_counter_evidence',
          callID: 'ce1',
          state: {
            status: 'completed',
            output: JSON.stringify({
              passages: [
                {
                  passage_id: 'p_99',
                  excerpt: 'against',
                  node_ids: [],
                  confidence: 0.95,
                },
              ],
            }),
          },
        },
      },
    } as OpencodeEvent);
    const cit = out.find(
      (e): e is CitationFoundEvent => e.type === 'citation_found',
    );
    expect(cit?.confidence).toBeLessThanOrEqual(0.5);
  });

  it('honours custom mcpResultParser', () => {
    const a = new OpencodeEventAdapter({
      sessionId: SID,
      mcpResultParser: (tool, _parsed, callId) =>
        tool === 'custom_tool'
          ? [{ type: 'error', agent: 'opencode', message: `custom:${callId}` }]
          : [],
    });
    const out = a.transform({
      type: 'message.part.updated',
      properties: {
        sessionID: SID,
        part: {
          type: 'tool',
          tool: 'custom_tool',
          callID: 'cx1',
          state: { status: 'completed', output: '{}' },
        },
      },
    } as OpencodeEvent);
    expect(out.some((e) => e.type === 'error')).toBe(true);
  });

  it('ignores server.heartbeat / server.connected envelopes', () => {
    const a = adapter();
    expect(
      a.transform({
        type: 'server.heartbeat',
        properties: {},
      } as OpencodeEvent),
    ).toHaveLength(0);
    expect(
      a.transform({
        type: 'server.connected',
        properties: {},
      } as OpencodeEvent),
    ).toHaveLength(0);
  });
});
