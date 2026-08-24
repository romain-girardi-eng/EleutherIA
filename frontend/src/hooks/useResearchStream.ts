/**
 * useResearchStream — consumes the agentic-research SSE stream and exposes
 * derived state ready for the UI (timeline, citations, live answer, KG hits).
 *
 * Wire-protocol details live in `types/agent-events.ts`. This hook is the only
 * file that touches `fetch` / SSE parsing for the new research experience.
 */

import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import Cookies from 'js-cookie';
import { apiEndpoint } from '../api/baseUrl';
import {
  type AgentEvent,
  type CitationFoundEvent,
  type CitationVerifiedEvent,
  type CostSummaryEvent,
  type FinalAnswerCitation,
  type FinalAnswerEvent,
  type KGNodeActivatedEvent,
  type SessionStatus,
  type SubagentStatus,
  type TokensUsedEvent,
  type TokensUsedRollupEvent,
  type ToolCallEvent,
  type ToolResultEvent,
  isAgentEvent,
} from '../types/agent-events';

export interface TokenUsageAgentRow {
  tokens: number;
  cost_usd: number;
  calls: number;
}

export interface TokenUsageState {
  total_tokens: number;
  total_cost_usd: number;
  by_agent: Record<string, TokenUsageAgentRow>;
  by_model: Record<string, TokenUsageAgentRow>;
  by_provider: Record<
    string,
    {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      cost_usd: number;
      calls: number;
    }
  >;
}

const emptyTokenUsage: TokenUsageState = {
  total_tokens: 0,
  total_cost_usd: 0,
  by_agent: {},
  by_model: {},
  by_provider: {},
};

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

export interface StageTiming {
  stage: string;
  duration_ms: number;
  metadata?: Record<string, unknown>;
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
  stageTimings: StageTiming[];
  tokenUsage: TokenUsageState;
  streamedAnswer: string;
  finalAnswer: FinalAnswerEvent | null;
  /** Verification lifecycle of the streamed prose (preview → verified). */
  answerVerification: AnswerVerificationState;
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

/** Verdicts that arrived before (or without) a matching citation_found. */
export interface PendingVerification {
  verified: boolean;
  reason?: string;
}

/**
 * Verification lifecycle of the streamed prose:
 *  - 'none'     — nothing streamed yet
 *  - 'pending'  — prose is on screen but the citation audit hasn't completed
 *  - 'verified' — citation_audit stage completed (or final_answer arrived)
 */
export type AnswerVerificationState = 'none' | 'pending' | 'verified';

interface State {
  status: SessionStatus;
  events: AgentEvent[];
  citationsById: Record<string, CitationEntry>;
  citationOrder: string[];
  /**
   * citation_verified verdicts whose id had no entry in citationsById at
   * arrival time (node-shaped ids, audit racing ahead of citation_found).
   * Reconciled into citationsById on citation_found / final_answer instead
   * of being dropped.
   */
  pendingVerifications: Record<string, PendingVerification>;
  answerVerification: AnswerVerificationState;
  activeSubagents: Record<string, ActiveSubagent>;
  toolCallsById: Record<string, PairedToolCall>;
  toolCallOrder: string[];
  kgActivationsById: Record<string, KGActivation>;
  stageTimings: StageTiming[];
  tokenUsage: TokenUsageState;
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
  pendingVerifications: {},
  answerVerification: 'none',
  activeSubagents: {},
  toolCallsById: {},
  toolCallOrder: [],
  kgActivationsById: {},
  stageTimings: [],
  tokenUsage: emptyTokenUsage,
  streamedAnswer: '',
  finalAnswer: null,
  traceId: null,
  error: null,
  retryCount: 0,
};

function accumulateTokenUsage(
  state: TokenUsageState,
  event: TokensUsedEvent,
): TokenUsageState {
  const agentKey = event.agent_id || 'unknown';
  const modelKey = event.model || 'unknown';
  const providerKey = event.provider || 'unknown';
  const cost = event.estimated_cost_usd ?? 0;
  const tokens = event.total_tokens ?? 0;
  const agentPrev = state.by_agent[agentKey] ?? {
    tokens: 0,
    cost_usd: 0,
    calls: 0,
  };
  const modelPrev = state.by_model[modelKey] ?? {
    tokens: 0,
    cost_usd: 0,
    calls: 0,
  };
  const providerPrev = state.by_provider[providerKey] ?? {
    prompt_tokens: 0,
    completion_tokens: 0,
    total_tokens: 0,
    cost_usd: 0,
    calls: 0,
  };
  return {
    total_tokens: state.total_tokens + tokens,
    total_cost_usd: Number((state.total_cost_usd + cost).toFixed(6)),
    by_agent: {
      ...state.by_agent,
      [agentKey]: {
        tokens: agentPrev.tokens + tokens,
        cost_usd: Number((agentPrev.cost_usd + cost).toFixed(6)),
        calls: agentPrev.calls + 1,
      },
    },
    by_model: {
      ...state.by_model,
      [modelKey]: {
        tokens: modelPrev.tokens + tokens,
        cost_usd: Number((modelPrev.cost_usd + cost).toFixed(6)),
        calls: modelPrev.calls + 1,
      },
    },
    by_provider: {
      ...state.by_provider,
      [providerKey]: {
        prompt_tokens: providerPrev.prompt_tokens + (event.prompt_tokens ?? 0),
        completion_tokens:
          providerPrev.completion_tokens + (event.completion_tokens ?? 0),
        total_tokens: providerPrev.total_tokens + tokens,
        cost_usd: Number((providerPrev.cost_usd + cost).toFixed(6)),
        calls: providerPrev.calls + 1,
      },
    },
  };
}

function applyCostSummary(
  state: TokenUsageState,
  event: CostSummaryEvent,
): TokenUsageState {
  return {
    ...state,
    total_tokens: event.total_tokens,
    total_cost_usd: event.total_cost_usd,
    by_agent: event.by_agent ?? state.by_agent,
    by_model: event.by_model ?? state.by_model,
    by_provider: event.by_provider ?? state.by_provider,
  };
}

function applyRollup(
  state: TokenUsageState,
  event: TokensUsedRollupEvent,
): TokenUsageState {
  // Rollups carry only the running totals — don't clobber per-agent /
  // per-model maps that ``tokens_used`` events have built up.
  return {
    ...state,
    total_tokens: Math.max(state.total_tokens, event.total_tokens),
    total_cost_usd: Math.max(state.total_cost_usd, event.total_cost_usd),
  };
}

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
          // A verdict may have arrived before this citation — apply it now.
          const pending = state.pendingVerifications[id];
          const entry: CitationEntry = {
            passage_id: cit.passage_id,
            cts_urn: cit.cts_urn,
            work_label: cit.work_label,
            excerpt: cit.excerpt,
            node_ids: cit.node_ids,
            confidence: cit.confidence,
            verified: state.citationsById[id]?.verified ?? pending?.verified,
            verification_reason:
              state.citationsById[id]?.verification_reason ?? pending?.reason,
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
          if (!existing) {
            // Node-shaped ids (kg nodes) and audit-before-found races used to
            // be dropped here. Accumulate the verdict in a side map and
            // reconcile when the citation (or final answer) lands.
            return {
              ...state,
              events,
              pendingVerifications: {
                ...state.pendingVerifications,
                [v.passage_id]: { verified: v.verified, reason: v.reason },
              },
            };
          }
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

        case 'stage_complete': {
          return {
            ...state,
            events,
            // The citation audit verdicts are all on the wire once this
            // stage completes — the streamed prose is no longer a preview.
            answerVerification:
              event.stage === 'citation_audit'
                ? 'verified'
                : state.answerVerification,
            stageTimings: [
              ...state.stageTimings,
              {
                stage: event.stage,
                duration_ms: event.duration_ms,
                metadata: event.metadata,
              },
            ],
          };
        }

        case 'tokens_used': {
          return {
            ...state,
            events,
            tokenUsage: accumulateTokenUsage(state.tokenUsage, event),
          };
        }

        case 'tokens_used_rollup': {
          return {
            ...state,
            events,
            tokenUsage: applyRollup(state.tokenUsage, event),
          };
        }

        case 'cost_summary': {
          return {
            ...state,
            events,
            tokenUsage: applyCostSummary(state.tokenUsage, event),
          };
        }

        case 'token':
          return {
            ...state,
            events,
            streamedAnswer: state.streamedAnswer + event.delta,
            // Prose is rendering before the citation audit has run — flag it
            // as a preview until stage_complete(citation_audit) arrives.
            answerVerification:
              state.answerVerification === 'none'
                ? 'pending'
                : state.answerVerification,
            status: state.status === 'streaming' ? 'synthesizing' : state.status,
          };

        case 'final_answer': {
          const final = event as FinalAnswerEvent;
          // Reconcile verification flags from the final citation list and
          // from any verdicts that arrived before their citation_found.
          const reconciled: Record<string, CitationEntry> = { ...state.citationsById };
          for (const [id, pending] of Object.entries(state.pendingVerifications)) {
            const existing = reconciled[id];
            if (existing && existing.verified === undefined) {
              reconciled[id] = {
                ...existing,
                verified: pending.verified,
                verification_reason: pending.reason,
              };
            }
          }
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
            answerVerification:
              state.answerVerification === 'none' ? 'none' : 'verified',
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
      // Use the same absolute VITE_API_URL base the rest of the app uses —
      // a relative URL resolves against free-will.app where no /api route
      // exists (the FE is a static nginx, the API lives elsewhere).
      fetch(
        apiEndpoint(`/api/graphrag/query/${encodeURIComponent(traceId)}/cancel`),
        { method: 'POST' },
      ).catch(() => {
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
          Accept: 'text/event-stream',
        };
        if (opts.includeAuth) {
          const token = Cookies.get('auth_token');
          if (token) headers.Authorization = `Bearer ${token}`;
        }

        try {
          // Backend exposes /api/graphrag/query/stream as a GET endpoint
          // taking `question` as a query-string parameter (not POST + JSON
          // body). The relative URL also has to be resolved against the
          // VITE_API_URL base — the FE is served from free-will.app where
          // no /api/* route is proxied.
          const url =
            `${apiEndpoint('/api/graphrag/query/stream')}?question=${encodeURIComponent(query)}`;
          const response = await fetch(url, {
            method: 'GET',
            headers,
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
    stageTimings: state.stageTimings,
    tokenUsage: state.tokenUsage,
    streamedAnswer: state.streamedAnswer,
    finalAnswer: state.finalAnswer,
    answerVerification: state.answerVerification,
    traceId: state.traceId,
    error: state.error,
    retryCount: state.retryCount,
    start,
    cancel,
    reset,
  };
}

export default useResearchStream;
