/**
 * useResearchStream — consumes the agentic-research SSE stream and exposes
 * derived state ready for the UI (timeline, citations, live answer, KG hits).
 *
 * Wire-protocol details live in `types/agent-events.ts`. This hook is the only
 * file that touches `fetch` / SSE parsing for the new research experience.
 */

import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import Cookies from 'js-cookie';
import {
  type AgentEvent,
  type CitationFoundEvent,
  type CitationVerifiedEvent,
  type FinalAnswerCitation,
  type FinalAnswerEvent,
  type KGNodeActivatedEvent,
  type SessionStatus,
  type SubagentStatus,
  type ToolCallEvent,
  type ToolResultEvent,
  isAgentEvent,
} from '../types/agent-events';

export interface CitationEntry {
  passage_id: string;
  cts_urn?: string;
  work_label?: string;
  excerpt: string;
  node_ids: string[];
  confidence: number;
  verified?: boolean;
  verification_reason?: string;
  /** Wall-clock at which the citation arrived; used for ordering and UI fade-in. */
  arrived_at: number;
}

export interface ActiveSubagent {
  agent: string;
  subagent: string;
  status: SubagentStatus;
  message?: string;
  started_at: number;
}

export interface PairedToolCall {
  call: ToolCallEvent;
  result?: ToolResultEvent;
  started_at: number;
  completed_at?: number;
}

export interface KGActivation {
  node_id: string;
  label: string;
  node_type: string;
  period?: string;
  /** Number of times this node has been touched; used for fade intensity. */
  hits: number;
  last_seen: number;
}

export interface UseResearchStreamOptions {
  /** Default: 5_000ms backoff between retry attempts. */
  retryDelayMs?: number;
  /** Default: 3 retries on transient network failure. */
  maxRetries?: number;
  /** Default: include the auth_token cookie as a Bearer header. */
  includeAuth?: boolean;
}

export interface UseResearchStreamReturn {
  status: SessionStatus;
  events: AgentEvent[];
  citations: CitationEntry[];
  activeSubagents: ActiveSubagent[];
  toolCalls: PairedToolCall[];
  kgActivations: KGActivation[];
  streamedAnswer: string;
  finalAnswer: FinalAnswerEvent | null;
  traceId: string | null;
  error: string | null;
  retryCount: number;
  /** Begin a streaming session. Resolves once the stream ends. */
  start: (query: string) => Promise<void>;
  /** Abort the in-flight stream and notify the backend if a trace_id is known. */
  cancel: () => void;
  /** Clear all derived state — used when starting a fresh query. */
  reset: () => void;
}

interface State {
  status: SessionStatus;
  events: AgentEvent[];
  citationsById: Record<string, CitationEntry>;
  citationOrder: string[];
  activeSubagents: Record<string, ActiveSubagent>;
  toolCallsById: Record<string, PairedToolCall>;
  toolCallOrder: string[];
  kgActivationsById: Record<string, KGActivation>;
  streamedAnswer: string;
  finalAnswer: FinalAnswerEvent | null;
  traceId: string | null;
  error: string | null;
  retryCount: number;
}

const initialState: State = {
  status: 'idle',
  events: [],
  citationsById: {},
  citationOrder: [],
  activeSubagents: {},
  toolCallsById: {},
  toolCallOrder: [],
  kgActivationsById: {},
  streamedAnswer: '',
  finalAnswer: null,
  traceId: null,
  error: null,
  retryCount: 0,
};

type Action =
  | { type: 'reset' }
  | { type: 'connecting' }
  | { type: 'streaming' }
  | { type: 'event'; event: AgentEvent; at: number }
  | { type: 'retry'; attempt: number }
  | { type: 'error'; message: string }
  | { type: 'cancelled' }
  | { type: 'complete' };

function subagentKey(agent: string, subagent: string): string {
  return `${agent}::${subagent}`;
}

export function reduce(state: State, action: Action): State {
  switch (action.type) {
    case 'reset':
      return initialState;

    case 'connecting':
      return { ...initialState, status: 'connecting' };

    case 'streaming':
      return { ...state, status: 'streaming' };

    case 'retry':
      return { ...state, retryCount: action.attempt, status: 'connecting' };

    case 'error':
      return { ...state, status: 'error', error: action.message };

    case 'cancelled':
      return { ...state, status: 'cancelled' };

    case 'complete':
      return { ...state, status: 'complete' };

    case 'event': {
      const { event, at } = action;
      const events = [...state.events, event];

      switch (event.type) {
        case 'agent_start':
          return {
            ...state,
            events,
            traceId: event.trace_id ?? state.traceId,
          };

        case 'agent_step': {
          const key = subagentKey(event.agent, event.subagent);
          const existing = state.activeSubagents[key];
          const nextActive = { ...state.activeSubagents };
          if (event.status === 'complete' || event.status === 'failed') {
            delete nextActive[key];
          } else {
            nextActive[key] = {
              agent: event.agent,
              subagent: event.subagent,
              status: event.status,
              message: event.message,
              started_at: existing?.started_at ?? at,
            };
          }
          return { ...state, events, activeSubagents: nextActive };
        }

        case 'tool_call': {
          const call = event as ToolCallEvent;
          return {
            ...state,
            events,
            toolCallsById: {
              ...state.toolCallsById,
              [call.id]: { call, started_at: at },
            },
            toolCallOrder: state.toolCallOrder.includes(call.id)
              ? state.toolCallOrder
              : [...state.toolCallOrder, call.id],
          };
        }

        case 'tool_result': {
          const result = event as ToolResultEvent;
          const existing = state.toolCallsById[result.tool_call_id];
          if (!existing) {
            return { ...state, events };
          }
          return {
            ...state,
            events,
            toolCallsById: {
              ...state.toolCallsById,
              [result.tool_call_id]: {
                ...existing,
                result,
                completed_at: at,
              },
            },
          };
        }

        case 'citation_found': {
          const cit = event as CitationFoundEvent;
          const id = cit.passage_id;
          const entry: CitationEntry = {
            passage_id: cit.passage_id,
            cts_urn: cit.cts_urn,
            work_label: cit.work_label,
            excerpt: cit.excerpt,
            node_ids: cit.node_ids,
            confidence: cit.confidence,
            verified: state.citationsById[id]?.verified,
            verification_reason: state.citationsById[id]?.verification_reason,
            arrived_at: state.citationsById[id]?.arrived_at ?? at,
          };
          return {
            ...state,
            events,
            citationsById: { ...state.citationsById, [id]: entry },
            citationOrder: state.citationOrder.includes(id)
              ? state.citationOrder
              : [...state.citationOrder, id],
          };
        }

        case 'citation_verified': {
          const v = event as CitationVerifiedEvent;
          const existing = state.citationsById[v.passage_id];
          if (!existing) return { ...state, events };
          return {
            ...state,
            events,
            citationsById: {
              ...state.citationsById,
              [v.passage_id]: {
                ...existing,
                verified: v.verified,
                verification_reason: v.reason,
              },
            },
          };
        }

        case 'kg_node_activated': {
          const k = event as KGNodeActivatedEvent;
          const prev = state.kgActivationsById[k.node_id];
          return {
            ...state,
            events,
            kgActivationsById: {
              ...state.kgActivationsById,
              [k.node_id]: {
                node_id: k.node_id,
                label: k.label,
                node_type: k.node_type,
                period: k.period,
                hits: (prev?.hits ?? 0) + 1,
                last_seen: at,
              },
            },
          };
        }

        case 'token':
          return {
            ...state,
            events,
            streamedAnswer: state.streamedAnswer + event.delta,
            status: state.status === 'streaming' ? 'synthesizing' : state.status,
          };

        case 'final_answer': {
          const final = event as FinalAnswerEvent;
          // Reconcile verification flags from the final citation list.
          const reconciled: Record<string, CitationEntry> = { ...state.citationsById };
          for (const c of final.citations as FinalAnswerCitation[]) {
            const existing = reconciled[c.passage_id];
            if (existing) {
              reconciled[c.passage_id] = { ...existing, verified: c.verified };
            }
          }
          return {
            ...state,
            events,
            citationsById: reconciled,
            finalAnswer: final,
            traceId: final.trace_id,
            status: 'complete',
          };
        }

        case 'error':
          return {
            ...state,
            events,
            status: 'error',
            error: event.message,
          };

        default:
          return { ...state, events };
      }
    }

    default:
      return state;
  }
}

const DEFAULT_OPTIONS: Required<UseResearchStreamOptions> = {
  retryDelayMs: 5_000,
  maxRetries: 3,
  includeAuth: true,
};

export function useResearchStream(
  options?: UseResearchStreamOptions,
): UseResearchStreamReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const [state, dispatch] = useReducer(reduce, initialState);
  const abortRef = useRef<AbortController | null>(null);
  const cancelledRef = useRef<boolean>(false);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    cancelledRef.current = false;
    dispatch({ type: 'reset' });
  }, []);

  const cancel = useCallback(() => {
    cancelledRef.current = true;
    const traceId = state.traceId;
    abortRef.current?.abort();
    abortRef.current = null;
    if (traceId) {
      // Fire-and-forget; the server is expected to honor or no-op.
      fetch(`/api/graphrag/query/${encodeURIComponent(traceId)}/cancel`, {
        method: 'POST',
      }).catch(() => {
        // Cancellation is best-effort; the client side already aborted the stream.
      });
    }
    dispatch({ type: 'cancelled' });
  }, [state.traceId]);

  const start = useCallback(
    async (query: string): Promise<void> => {
      cancelledRef.current = false;
      dispatch({ type: 'reset' });
      dispatch({ type: 'connecting' });

      const attempt = async (attemptNumber: number): Promise<void> => {
        if (cancelledRef.current) return;

        const controller = new AbortController();
        abortRef.current = controller;

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        };
        if (opts.includeAuth) {
          const token = Cookies.get('auth_token');
          if (token) headers.Authorization = `Bearer ${token}`;
        }

        try {
          const response = await fetch('/api/graphrag/query/stream', {
            method: 'POST',
            headers,
            body: JSON.stringify({ query }),
            signal: controller.signal,
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const reader = response.body?.getReader();
          if (!reader) throw new Error('no_response_body');
          const decoder = new TextDecoder();

          dispatch({ type: 'streaming' });
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith('data: ')) continue;
              const payload = trimmed.slice(6);
              if (!payload || payload === '[DONE]') continue;
              try {
                const parsed: unknown = JSON.parse(payload);
                if (isAgentEvent(parsed)) {
                  dispatch({ type: 'event', event: parsed, at: Date.now() });
                }
              } catch {
                // Swallow malformed lines; the upstream pipeline occasionally
                // emits non-JSON keepalives.
              }
            }
          }

          if (!cancelledRef.current) {
            dispatch({ type: 'complete' });
          }
        } catch (err) {
          if (cancelledRef.current) return;
          const isAbort = err instanceof DOMException && err.name === 'AbortError';
          if (isAbort) return;

          const transient =
            err instanceof TypeError ||
            (err instanceof Error && /HTTP 5\d\d/.test(err.message));

          if (transient && attemptNumber < opts.maxRetries) {
            dispatch({ type: 'retry', attempt: attemptNumber + 1 });
            await new Promise((r) => setTimeout(r, opts.retryDelayMs));
            return attempt(attemptNumber + 1);
          }
          dispatch({
            type: 'error',
            message: err instanceof Error ? err.message : 'stream_failed',
          });
        }
      };

      await attempt(0);
    },
    [opts.includeAuth, opts.maxRetries, opts.retryDelayMs],
  );

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const citations = useMemo<CitationEntry[]>(
    () => state.citationOrder.map((id) => state.citationsById[id]).filter(Boolean),
    [state.citationOrder, state.citationsById],
  );

  const activeSubagents = useMemo<ActiveSubagent[]>(
    () => Object.values(state.activeSubagents),
    [state.activeSubagents],
  );

  const toolCalls = useMemo<PairedToolCall[]>(
    () => state.toolCallOrder.map((id) => state.toolCallsById[id]).filter(Boolean),
    [state.toolCallOrder, state.toolCallsById],
  );

  const kgActivations = useMemo<KGActivation[]>(
    () => Object.values(state.kgActivationsById),
    [state.kgActivationsById],
  );

  return {
    status: state.status,
    events: state.events,
    citations,
    activeSubagents,
    toolCalls,
    kgActivations,
    streamedAnswer: state.streamedAnswer,
    finalAnswer: state.finalAnswer,
    traceId: state.traceId,
    error: state.error,
    retryCount: state.retryCount,
    start,
    cancel,
    reset,
  };
}

export default useResearchStream;
