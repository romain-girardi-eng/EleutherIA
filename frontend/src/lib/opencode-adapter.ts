/**
 * opencode-adapter.ts — translate opencode `/event` SSE envelopes into the
 * EleutherIA AgentEvent protocol that the streaming Research UI already speaks.
 *
 * Wire format reference: docs/plans/2026-05-14-opencode-event-protocol.md
 *
 * Mapping rules (one-line each):
 *   - session.created            → agent_start (carries the user query)
 *   - session.status (busy/idle) → agent_step (orchestrator lifecycle)
 *   - session.idle (terminal)    → final_answer (synthesised from buffered text)
 *   - message.part.delta text    → token { delta }
 *   - message.part.updated tool  → tool_call on first sighting, tool_result + synthetic
 *                                  citation_found / kg_node_activated on `completed`
 *   - tool state.status=failed   → error
 *   - server.connected/heartbeat → []
 *
 * The adapter is per-session: instantiate one `OpencodeEventAdapter` per
 * `sessionID` you care about and feed it the raw envelopes after the consumer
 * has filtered the global stream.
 */

import type {
  AgentEvent,
  AgentStartEvent,
  AgentStepEvent,
  CitationFoundEvent,
  ErrorEvent,
  FinalAnswerCitation,
  FinalAnswerEvent,
  KGNodeActivatedEvent,
  TokenEvent,
  ToolArgs,
  ToolCallEvent,
  ToolResultEvent,
} from '../types/agent-events';

/* -------------------------------------------------------------------------- */
/*  Opencode envelope types (subset of the protocol we consume)               */
/* -------------------------------------------------------------------------- */

export interface OpencodeEnvelope<P = unknown> {
  type: string;
  properties: P;
}

export interface OpencodeSessionCreated {
  sessionID: string;
  title?: string;
  prompt?: string;
}

export interface OpencodeSessionStatus {
  sessionID: string;
  status: { type: 'busy' | 'idle' } | string;
}

export interface OpencodeSessionIdle {
  sessionID: string;
}

export interface OpencodeMessagePartDelta {
  sessionID: string;
  messageID: string;
  partID: string;
  field: 'text' | 'reasoning' | string;
  delta: string;
}

export interface OpencodeMessagePartTool {
  type: 'tool';
  tool: string;
  callID: string;
  state: {
    status: 'pending' | 'running' | 'completed' | 'failed' | string;
    input?: ToolArgs;
    output?: unknown;
    error?: string;
    metadata?: Record<string, unknown>;
    time?: { start?: number; end?: number };
  };
}

export interface OpencodeMessagePartText {
  type: 'text';
  text: string;
}

export type OpencodeMessagePart =
  | OpencodeMessagePartTool
  | OpencodeMessagePartText
  | { type: string; [k: string]: unknown };

export interface OpencodeMessagePartUpdated {
  sessionID: string;
  messageID?: string;
  partID?: string;
  part: OpencodeMessagePart;
  role?: 'user' | 'assistant' | string;
}

export interface OpencodeError {
  sessionID: string;
  message?: string;
  error?: string;
}

export type OpencodeEvent =
  | OpencodeEnvelope<OpencodeSessionCreated> & { type: 'session.created' }
  | (OpencodeEnvelope<OpencodeSessionStatus> & { type: 'session.status' })
  | (OpencodeEnvelope<OpencodeSessionIdle> & { type: 'session.idle' })
  | (OpencodeEnvelope<OpencodeMessagePartDelta> & { type: 'message.part.delta' })
  | (OpencodeEnvelope<OpencodeMessagePartUpdated> & { type: 'message.part.updated' })
  | (OpencodeEnvelope<OpencodeError> & { type: 'session.error' })
  | (OpencodeEnvelope<unknown> & { type: string });

/* -------------------------------------------------------------------------- */
/*  MCP tool-result parser                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Caller-supplied hook so additional tools (counter-evidence, citation
 * verifier) can be wired in without modifying the adapter.
 */
export type MCPResultParser = (
  toolName: string,
  parsedOutput: unknown,
  callId: string,
) => AgentEvent[];

interface KGNodeShape {
  node_id?: string;
  id?: string;
  label?: string;
  node_type?: string;
  type?: string;
  period?: string;
}

interface PassageShape {
  passage_id?: string;
  id?: string;
  cts_urn?: string;
  urn?: string;
  work_label?: string;
  excerpt?: string;
  text?: string;
  node_ids?: string[];
  confidence?: number;
  verified?: boolean;
  reason?: string;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

/** Best-effort JSON parse — MCP tool results travel as opaque strings. */
function safeParseJSON(raw: unknown): unknown {
  if (typeof raw !== 'string') return raw;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return raw;
  }
}

function readPassageList(parsed: unknown): PassageShape[] {
  if (Array.isArray(parsed)) return parsed as PassageShape[];
  if (!isObject(parsed)) return [];
  for (const key of ['passages', 'results', 'items', 'data']) {
    const v = parsed[key];
    if (Array.isArray(v)) return v as PassageShape[];
  }
  return [];
}

function readNodeList(parsed: unknown): KGNodeShape[] {
  if (Array.isArray(parsed)) return parsed as KGNodeShape[];
  if (!isObject(parsed)) return [];
  for (const key of ['nodes', 'results', 'items', 'data']) {
    const v = parsed[key];
    if (Array.isArray(v)) return v as KGNodeShape[];
  }
  // single-node responses (e.g. get_node_detail) — wrap.
  if (typeof parsed.node_id === 'string' || typeof parsed.id === 'string') {
    return [parsed as KGNodeShape];
  }
  return [];
}

function passageToCitation(p: PassageShape): CitationFoundEvent | null {
  const passageId = p.passage_id ?? p.id;
  if (!passageId) return null;
  return {
    type: 'citation_found',
    passage_id: passageId,
    cts_urn: p.cts_urn ?? p.urn,
    work_label: p.work_label,
    excerpt: p.excerpt ?? p.text ?? '',
    node_ids: asArray<string>(p.node_ids),
    confidence: typeof p.confidence === 'number' ? p.confidence : 0.5,
  };
}

function nodeToActivation(n: KGNodeShape): KGNodeActivatedEvent | null {
  const nodeId = n.node_id ?? n.id;
  if (!nodeId) return null;
  return {
    type: 'kg_node_activated',
    node_id: nodeId,
    label: n.label ?? nodeId,
    node_type: n.node_type ?? n.type ?? 'unknown',
    period: n.period,
  };
}

const PASSAGE_TOOLS = new Set([
  'eleutheria_search_passages',
  'eleutheria_read_passages',
  'eleutheria_read_work_section',
  'search_passages',
  'read_passages',
]);

const NODE_TOOLS = new Set([
  'eleutheria_search_nodes',
  'eleutheria_get_node_detail',
  'eleutheria_get_neighbors',
  'eleutheria_explore_subgraph',
  'search_nodes',
  'get_node_detail',
  'get_neighbors',
  'explore_subgraph',
]);

const VERIFIER_TOOLS = new Set([
  'eleutheria_verify_citation',
  'verify_citation',
]);

const COUNTER_EVIDENCE_TOOLS = new Set([
  'eleutheria_find_counter_evidence',
  'find_counter_evidence',
]);

/* -------------------------------------------------------------------------- */
/*  Adapter                                                                   */
/* -------------------------------------------------------------------------- */

export interface OpencodeAdapterOptions {
  sessionId: string;
  /** Optional override / extension for MCP tools we do not natively understand. */
  mcpResultParser?: MCPResultParser;
}

interface ToolCallState {
  id: string;
  tool: string;
  emittedCall: boolean;
  emittedResult: boolean;
}

export class OpencodeEventAdapter {
  private readonly sessionId: string;
  private readonly mcpResultParser?: MCPResultParser;

  private toolCalls = new Map<string, ToolCallState>();
  private assistantText = '';
  private finalCitations: FinalAnswerCitation[] = [];
  private agentStarted = false;
  private finalEmitted = false;
  private currentQuery = '';

  constructor(opts: OpencodeAdapterOptions) {
    this.sessionId = opts.sessionId;
    this.mcpResultParser = opts.mcpResultParser;
  }

  /** Transform a single opencode SSE envelope into zero or more AgentEvents. */
  transform(event: OpencodeEvent): AgentEvent[] {
    if (!event || typeof event.type !== 'string') return [];
    // Drop events meant for other sessions.
    const props = (event.properties ?? {}) as { sessionID?: string };
    if (props.sessionID && props.sessionID !== this.sessionId) return [];

    switch (event.type) {
      case 'session.created':
        return this.handleSessionCreated(event.properties as OpencodeSessionCreated);
      case 'session.status':
        return this.handleSessionStatus(event.properties as OpencodeSessionStatus);
      case 'session.idle':
        return this.handleSessionIdle();
      case 'message.part.delta':
        return this.handlePartDelta(event.properties as OpencodeMessagePartDelta);
      case 'message.part.updated':
        return this.handlePartUpdated(event.properties as OpencodeMessagePartUpdated);
      case 'session.error':
        return this.handleSessionError(event.properties as OpencodeError);
      default:
        return [];
    }
  }

  /** Public for testing — parse a tool result into synthetic AgentEvents. */
  parseToolResult(
    toolName: string,
    toolOutput: unknown,
    callId: string,
  ): AgentEvent[] {
    const parsed = safeParseJSON(toolOutput);
    const out: AgentEvent[] = [];

    if (PASSAGE_TOOLS.has(toolName)) {
      for (const p of readPassageList(parsed)) {
        const cit = passageToCitation(p);
        if (cit) out.push(cit);
      }
    }

    if (NODE_TOOLS.has(toolName)) {
      for (const n of readNodeList(parsed)) {
        const act = nodeToActivation(n);
        if (act) out.push(act);
      }
    }

    if (VERIFIER_TOOLS.has(toolName) && isObject(parsed)) {
      const passageId =
        typeof parsed.passage_id === 'string' ? parsed.passage_id : undefined;
      if (passageId) {
        out.push({
          type: 'citation_verified',
          passage_id: passageId,
          verified: Boolean(parsed.verified),
          reason:
            typeof parsed.reason === 'string' ? parsed.reason : undefined,
        });
        this.finalCitations.push({
          passage_id: passageId,
          claim: typeof parsed.claim === 'string' ? parsed.claim : '',
          verified: Boolean(parsed.verified),
        });
      }
    }

    if (COUNTER_EVIDENCE_TOOLS.has(toolName)) {
      for (const p of readPassageList(parsed)) {
        const cit = passageToCitation(p);
        if (cit) {
          out.push({
            ...cit,
            // Carry a low confidence floor; the UI consumes counter-evidence as
            // a normal citation_found and the StreamingAnswer flags it via the
            // verified=false flow.
            confidence: Math.min(cit.confidence, 0.5),
          });
        }
      }
    }

    if (this.mcpResultParser) {
      out.push(...this.mcpResultParser(toolName, parsed, callId));
    }

    return out;
  }

  /* ------------------------------ handlers ------------------------------ */

  private handleSessionCreated(p: OpencodeSessionCreated): AgentEvent[] {
    if (this.agentStarted) return [];
    this.agentStarted = true;
    this.currentQuery = p.prompt ?? p.title ?? '';
    const ev: AgentStartEvent = {
      type: 'agent_start',
      agent: 'opencode',
      query: this.currentQuery,
      trace_id: this.sessionId,
    };
    return [ev];
  }

  private handleSessionStatus(p: OpencodeSessionStatus): AgentEvent[] {
    const statusType =
      typeof p.status === 'object' && p.status !== null
        ? (p.status as { type?: string }).type
        : typeof p.status === 'string'
          ? p.status
          : undefined;
    if (statusType !== 'busy' && statusType !== 'idle') return [];
    const ev: AgentStepEvent = {
      type: 'agent_step',
      agent: 'opencode',
      subagent: 'orchestrator',
      status: statusType === 'busy' ? 'thinking' : 'complete',
    };
    return [ev];
  }

  private handleSessionIdle(): AgentEvent[] {
    if (this.finalEmitted) return [];
    this.finalEmitted = true;
    const finalEvent: FinalAnswerEvent = {
      type: 'final_answer',
      answer: this.assistantText.trim(),
      citations: [...this.finalCitations],
      trace_id: this.sessionId,
    };
    return [finalEvent];
  }

  private handlePartDelta(p: OpencodeMessagePartDelta): AgentEvent[] {
    if (p.field !== 'text') return [];
    if (typeof p.delta !== 'string' || p.delta.length === 0) return [];
    this.assistantText += p.delta;
    const ev: TokenEvent = { type: 'token', delta: p.delta };
    return [ev];
  }

  private handlePartUpdated(p: OpencodeMessagePartUpdated): AgentEvent[] {
    if (!p.part || typeof p.part !== 'object') return [];
    const part = p.part as OpencodeMessagePart;

    if (part.type === 'tool') {
      return this.handleToolPart(part as OpencodeMessagePartTool);
    }
    // text snapshots accumulate via deltas; ignore for streaming flow.
    return [];
  }

  private handleToolPart(part: OpencodeMessagePartTool): AgentEvent[] {
    const callId = part.callID;
    if (!callId) return [];
    const tool = part.tool;
    const state = part.state ?? { status: 'pending' };
    const out: AgentEvent[] = [];

    let entry = this.toolCalls.get(callId);
    if (!entry) {
      entry = { id: callId, tool, emittedCall: false, emittedResult: false };
      this.toolCalls.set(callId, entry);
    }

    if (!entry.emittedCall) {
      const call: ToolCallEvent = {
        type: 'tool_call',
        agent: 'opencode',
        tool,
        args: (state.input ?? {}) as ToolArgs,
        id: callId,
      };
      entry.emittedCall = true;
      out.push(call);
    }

    if (state.status === 'failed') {
      const err: ErrorEvent = {
        type: 'error',
        agent: 'opencode',
        message: state.error ?? `tool ${tool} failed`,
      };
      out.push(err);
      return out;
    }

    if (state.status === 'completed' && !entry.emittedResult) {
      entry.emittedResult = true;
      const synthetic = this.parseToolResult(tool, state.output, callId);

      const nodesTouched: string[] = [];
      const passagesTouched: string[] = [];
      for (const ev of synthetic) {
        if (ev.type === 'kg_node_activated') nodesTouched.push(ev.node_id);
        if (ev.type === 'citation_found') passagesTouched.push(ev.passage_id);
      }

      const result: ToolResultEvent = {
        type: 'tool_result',
        tool_call_id: callId,
        result_summary: summariseResult(tool, synthetic),
        nodes_touched: nodesTouched.length ? nodesTouched : undefined,
        passages_touched: passagesTouched.length ? passagesTouched : undefined,
        duration_ms:
          state.time?.start && state.time?.end
            ? state.time.end - state.time.start
            : undefined,
      };
      out.push(result, ...synthetic);
    }

    return out;
  }

  private handleSessionError(p: OpencodeError): AgentEvent[] {
    const message = p.message ?? p.error ?? 'opencode session error';
    const ev: ErrorEvent = { type: 'error', agent: 'opencode', message };
    return [ev];
  }
}

function summariseResult(tool: string, synthetic: AgentEvent[]): string {
  const cits = synthetic.filter((e) => e.type === 'citation_found').length;
  const nodes = synthetic.filter((e) => e.type === 'kg_node_activated').length;
  if (cits && nodes) return `${tool}: ${cits} citation(s), ${nodes} node(s)`;
  if (cits) return `${tool}: ${cits} citation(s)`;
  if (nodes) return `${tool}: ${nodes} node(s)`;
  return `${tool}: completed`;
}
