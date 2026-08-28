/**
 * Per-run state container for the GraphRAG Q&A page.
 *
 * The page used to hold ONE stream's state (streaming, agentSteps, response,
 * cost, …) alongside a half-parallel set of tab-keyed maps (tabMessages,
 * tabResponses, reasoningTraces). Everything now lives in a single keyed
 * structure: one `GraphRagRun` per question, addressed by `runId`. The
 * "current" view is simply the active run — there is no second source of
 * truth to keep in sync.
 *
 * Anything that cannot be described as data (AbortController, watchdog
 * timers, SSE step counters) lives outside the reducer, in the page's
 * `runtimesRef` map, keyed by the same `runId`.
 */

import type { GraphRAGChatMessage, GraphRAGResponse } from '../../types';
import type { AgentStep, PassageContext } from '../../types/graphrag';
import type { RightPanelState } from '../../components/graphrag/RightPanel';
import type { ReasoningTraceStep } from '../../components/ReasoningPanel';
import type { CacheBadgeInfo } from '../../components/research/CostCounter';
import type { TokenCost } from '../../components/graphrag/ResearchTimelinePanel';

/**
 * UI cap on concurrent SSE runs. The backend accepts 4 (the 5th gets a 429 +
 * Retry-After); we stop at 3 so a retry or a deep link always has headroom.
 */
export const MAX_CONCURRENT_RUNS = 3;

export type RunStatus = 'streaming' | 'done' | 'error' | 'stopped';

export interface RunMetrics {
  modelLabel: string;
  retrievalMode: string;
  estimatedCost: number | null;
  answerLengthChars: number;
  modelContext: number;
}

export interface GraphRagRun {
  id: string;
  /** The question that opened this run — also the tab label. */
  question: string;
  model: string;
  mode: string;
  status: RunStatus;
  createdAt: number;
  /** Chat transcript for this run only. */
  messages: GraphRAGChatMessage[];
  /** Live agent timeline (status / tool / reasoning / research-note steps). */
  agentSteps: AgentStep[];
  agentActive: boolean;
  streamStatus: string;
  /** Raw backend stage id from the latest SSE status frame. */
  currentStage: string;
  /** True once the SSE stream has closed, however it ended. */
  streamEnded: boolean;
  /**
   * Live, UN-VERIFIED draft prose (SSE `answer_provisional`). Transient by
   * contract: replaced atomically by `answer_final` and cleared at stream
   * teardown, so it never survives the stream nor reaches storage.
   */
  provisionalAnswer: string | null;
  /**
   * Compact reader notice for a partial verdict (SSE `verification_warning`):
   * how many sentences the citation audit withheld, and why.
   */
  verificationNotice: string | null;
  error: string | null;
  response: GraphRAGResponse | null;
  cost: TokenCost | null;
  cacheInfo: CacheBadgeInfo | null;
  metrics: RunMetrics | null;
  reasoningTrace: ReasoningTraceStep[];
  /** Right-panel view state — swapped wholesale when the tab changes. */
  rightPanelState: RightPanelState;
  activeSourceIndex: number | null;
  passageContext: PassageContext | null;
  passageWindow: number;
}

export interface RunsState {
  runs: Record<string, GraphRagRun>;
  /** Tab order, oldest first. */
  order: string[];
  activeRunId: string | null;
}

export const initialRunsState: RunsState = {
  runs: {},
  order: [],
  activeRunId: null,
};

export function createRun(
  init: Pick<GraphRagRun, 'id' | 'question' | 'model' | 'mode'> &
    Partial<GraphRagRun>,
): GraphRagRun {
  return {
    status: 'streaming',
    createdAt: Date.now(),
    messages: [],
    agentSteps: [],
    agentActive: false,
    streamStatus: '',
    currentStage: 'connecting',
    streamEnded: false,
    provisionalAnswer: null,
    verificationNotice: null,
    error: null,
    response: null,
    cost: null,
    cacheInfo: null,
    metrics: null,
    reasoningTrace: [],
    rightPanelState: 'idle',
    activeSourceIndex: null,
    passageContext: null,
    passageWindow: 5,
    ...init,
  };
}

export type RunsAction =
  | { type: 'run/open'; run: GraphRagRun }
  | { type: 'run/patch'; id: string; patch: Partial<GraphRagRun> }
  | { type: 'run/appendMessage'; id: string; message: GraphRAGChatMessage }
  /** Replaces every assistant message with the final enriched one. */
  | { type: 'run/replaceAssistant'; id: string; message: GraphRAGChatMessage }
  | { type: 'run/appendStep'; id: string; step: AgentStep }
  /** Grows the `reasoning` field of one accumulating step (synthesis / journal). */
  | { type: 'run/growStep'; id: string; stepId: string; text: string; separator: string; stage?: string }
  | { type: 'run/activate'; id: string }
  | { type: 'run/close'; id: string };

function withRun(
  state: RunsState,
  id: string,
  update: (run: GraphRagRun) => GraphRagRun,
): RunsState {
  const run = state.runs[id];
  if (!run) return state;
  const next = update(run);
  if (next === run) return state;
  return { ...state, runs: { ...state.runs, [id]: next } };
}

export function runsReducer(state: RunsState, action: RunsAction): RunsState {
  switch (action.type) {
    case 'run/open': {
      if (state.runs[action.run.id]) return state;
      return {
        runs: { ...state.runs, [action.run.id]: action.run },
        order: [...state.order, action.run.id],
        activeRunId: action.run.id,
      };
    }

    case 'run/patch':
      return withRun(state, action.id, (run) => ({ ...run, ...action.patch }));

    case 'run/appendMessage':
      return withRun(state, action.id, (run) => ({
        ...run,
        messages: [...run.messages, action.message],
      }));

    case 'run/replaceAssistant':
      return withRun(state, action.id, (run) => ({
        ...run,
        messages: [
          ...run.messages.filter((m) => m.role !== 'assistant'),
          action.message,
        ],
      }));

    case 'run/appendStep':
      return withRun(state, action.id, (run) => ({
        ...run,
        agentSteps: [...run.agentSteps, action.step],
      }));

    case 'run/growStep':
      return withRun(state, action.id, (run) => ({
        ...run,
        agentSteps: run.agentSteps.map((step) =>
          step.id === action.stepId
            ? {
                ...step,
                reasoning: step.reasoning
                  ? `${step.reasoning}${action.separator}${action.text}`
                  : action.text,
                ...(action.stage ? { stage: action.stage } : {}),
              }
            : step,
        ),
      }));

    case 'run/activate':
      if (!state.runs[action.id] || state.activeRunId === action.id) return state;
      return { ...state, activeRunId: action.id };

    case 'run/close': {
      if (!state.runs[action.id]) return state;
      const runs = { ...state.runs };
      delete runs[action.id];
      const closedIndex = state.order.indexOf(action.id);
      const order = state.order.filter((id) => id !== action.id);
      let activeRunId = state.activeRunId;
      if (activeRunId === action.id) {
        // Fall back to the neighbour that took the closed tab's slot, else the
        // last remaining run, else nothing (back to the welcome hero).
        activeRunId = order[Math.min(closedIndex, order.length - 1)] ?? null;
      }
      return { runs, order, activeRunId };
    }

    default:
      return state;
  }
}

/* ---------------------------------------------------------------- selectors */

export const selectActiveRun = (state: RunsState): GraphRagRun | null =>
  state.activeRunId ? state.runs[state.activeRunId] ?? null : null;

export const selectOrderedRuns = (state: RunsState): GraphRagRun[] =>
  state.order.map((id) => state.runs[id]).filter(Boolean);

export const selectStreamingCount = (state: RunsState): number =>
  state.order.reduce(
    (n, id) => (state.runs[id]?.status === 'streaming' ? n + 1 : n),
    0,
  );

/** A new question may start whenever fewer than MAX_CONCURRENT_RUNS stream. */
export const canStartRun = (state: RunsState): boolean =>
  selectStreamingCount(state) < MAX_CONCURRENT_RUNS;

export const selectAllResponses = (state: RunsState): GraphRAGResponse[] =>
  selectOrderedRuns(state)
    .map((run) => run.response)
    .filter((r): r is GraphRAGResponse => r !== null);
