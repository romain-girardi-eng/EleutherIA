import { useState, useRef, useEffect, useCallback, useMemo, useReducer } from 'react';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../api/client';
import { apiEndpoint } from '../../api/baseUrl';
import { useAuth } from '../../context/AuthContext';
import AuthModal from '../../components/AuthModal';
import NodeDetailPanel from '../../components/NodeDetailPanel';
import RightPanel from '../../components/graphrag/RightPanel';
import { ReasoningPanel } from '../../components/ReasoningPanel';
import type { ReasoningTraceStep } from '../../components/ReasoningPanel';
import WelcomeHero from './WelcomeHero';
import ChatPanel from './ChatPanel';
import type { GraphRagModelOption } from './ChatInput';
import MobileGraphSheet from './MobileGraphSheet';
import type { RunTabItem } from './RunTabs';
import {
  MAX_CONCURRENT_RUNS,
  canStartRun,
  createRun,
  initialRunsState,
  runsReducer,
  selectActiveRun,
  selectAllResponses,
  selectOrderedRuns,
  type GraphRagRun,
  type RunStatus,
  type RunsState,
} from './runs';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../../types';
import type { AgentStep, PassageContext, ResearchNoteKind } from '../../types/graphrag';
import {
  mockGraphRAGResponse,
  mockReasoningSteps,
} from '../../data/mockGraphRAGData';

// Survive navigation away/back: if the user clicks a citation badge that
// routes to /texts (or anywhere else) and then comes back via the browser
// back button, we want their Q&A to still be on screen. We snapshot the
// last successful messages + right-panel response into sessionStorage and
// rehydrate on mount. Keys are scoped to the page so other consumers
// don't get blasted.
const SESSION_KEY_MESSAGES = 'eleutheria.graphrag.messages.v1';
const SESSION_KEY_RESPONSE = 'eleutheria.graphrag.response.v1';
const MODEL_SELECTION_KEY = 'eleutheria.graphrag.model-selection.v1';

// Time-to-first-byte budget for the SSE handshake.
const STREAM_HEADER_TIMEOUT_MS = 120_000;
// Mid-stream silence budget: the backend heartbeats far more often than this,
// so a longer gap means the connection died without an SSE `error` frame
// (Cloudflare tunnel drop, worker OOM, …).
const STREAM_IDLE_TIMEOUT_MS = 95_000;

// Model + retrieval mode are no longer user-facing — the backend runs a single
// vectorless agentic pipeline. Kept as constants so retry-with-model and the
// run metadata still have something honest to record.
const DEFAULT_MODEL = 'auto';
const DEFAULT_MODE = 'auto';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Everything about a run that is NOT state: the abort controller, the two
 * watchdog timers, and the SSE bookkeeping counters. Lives in a ref map keyed
 * by runId, never in the reducer.
 */
interface RunRuntime {
  abort: AbortController;
  headerTimeout: ReturnType<typeof setTimeout> | null;
  idleTimeout: ReturnType<typeof setTimeout> | null;
  connectionLost: boolean;
  userStopped: boolean;
  stepCounter: number;
  synthesisStepId: string | null;
  journalStepId: string | null;
}

function disposeRuntime(runtime: RunRuntime) {
  if (runtime.headerTimeout !== null) {
    clearTimeout(runtime.headerTimeout);
    runtime.headerTimeout = null;
  }
  if (runtime.idleTimeout !== null) {
    clearTimeout(runtime.idleTimeout);
    runtime.idleTimeout = null;
  }
}

function _restoreMessages(): GraphRAGChatMessage[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY_MESSAGES);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as GraphRAGChatMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function _restoreResponse(): GraphRAGResponse | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY_RESPONSE);
    if (!raw) return null;
    return JSON.parse(raw) as GraphRAGResponse;
  } catch {
    return null;
  }
}

function _restoreModelSelection(): string {
  try {
    return localStorage.getItem(MODEL_SELECTION_KEY) || DEFAULT_MODEL;
  } catch {
    return DEFAULT_MODEL;
  }
}

/** Rehydrate the last answered question as a single, already-finished run. */
function restoreRunsState(): RunsState {
  const messages = _restoreMessages();
  if (messages.length === 0) return initialRunsState;
  const response = _restoreResponse();
  const run = createRun({
    id: 'run_restored',
    question: messages.find((m) => m.role === 'user')?.content ?? '',
    model: DEFAULT_MODEL,
    mode: DEFAULT_MODE,
    status: 'done',
    messages,
    response,
    streamEnded: true,
    rightPanelState: response ? 'graph' : 'idle',
  });
  return { runs: { [run.id]: run }, order: [run.id], activeRunId: run.id };
}

export default function GraphRAGPage() {
  const { t } = useTranslation();
  const location = useLocation();

  // ── The one per-run store ────────────────────────────────────────────────
  const [runsState, dispatch] = useReducer(runsReducer, undefined, restoreRunsState);
  // Mirror for async code paths (SSE handlers, submission cap) that must read
  // the CURRENT store rather than the closure they were created in.
  const runsStateRef = useRef(runsState);
  runsStateRef.current = runsState;
  const runtimesRef = useRef(new Map<string, RunRuntime>());
  const runSeqRef = useRef(0);

  const activeRun = selectActiveRun(runsState);
  const activeRunId = runsState.activeRunId;

  const orderedRuns = useMemo(() => selectOrderedRuns(runsState), [runsState]);
  const allResponses = useMemo(() => selectAllResponses(runsState), [runsState]);
  const streamingCount = useMemo(
    () => orderedRuns.filter((r) => r.status === 'streaming').length,
    [orderedRuns],
  );
  const canSubmit = streamingCount < MAX_CONCURRENT_RUNS;
  const runTabs: RunTabItem[] = useMemo(
    () => orderedRuns.map((r) => ({ id: r.id, question: r.question, status: r.status })),
    [orderedRuns],
  );

  const [query, setQuery] = useState('');
  /** Page-level, run-independent message (cap reached, server busy, …). */
  const [notice, setNotice] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { isAuthenticated } = useAuth();

  // Advanced settings
  const [ancientOnly, setAncientOnly] = useState(false);
  const [showRetryDropdown, setShowRetryDropdown] = useState(false);
  const [selectedRetryModel] = useState(DEFAULT_MODEL);

  const highlightNodeRef = useRef<((citationIndex: number) => void) | null>(null);

  // Right panel reasoning trace toggle (a view preference, not run state)
  const [showReasoningTrace, setShowReasoningTrace] = useState(false);

  const [modelContextMap, setModelContextMap] = useState<Record<string, number>>({});
  const [modelOptions, setModelOptions] = useState<GraphRagModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState(_restoreModelSelection);
  const modelContextMapRef = useRef(modelContextMap);
  modelContextMapRef.current = modelContextMap;

  /**
   * True once the UI cap is reached. Checks the live runtime map as well as
   * the reducer state so two submissions in the same tick (before a re-render
   * refreshes `runsStateRef`) can never slip past the cap.
   */
  const atCapacity = useCallback(
    () =>
      runtimesRef.current.size >= MAX_CONCURRENT_RUNS ||
      !canStartRun(runsStateRef.current),
    [],
  );

  const patchRun = useCallback((id: string, patch: Partial<GraphRagRun>) => {
    dispatch({ type: 'run/patch', id, patch });
  }, []);

  const patchActiveRun = useCallback(
    (patch: Partial<GraphRagRun>) => {
      if (runsStateRef.current.activeRunId) {
        dispatch({ type: 'run/patch', id: runsStateRef.current.activeRunId, patch });
      }
    },
    [],
  );

  useEffect(() => {
    fetch(apiEndpoint('/api/graphrag/models'))
      .then((r) => r.json())
      .then((models: Array<{
        key: string;
        label?: string;
        provider?: string;
        context: number;
        available?: boolean;
      }>) => {
        const map: Record<string, number> = {};
        models.forEach((m) => { map[m.key] = m.context; });
        setModelContextMap(map);
        setModelOptions(models.map((m) => ({
          key: m.key,
          label: m.label || m.key,
          provider: m.provider || '',
          available: m.available,
        })));
        setSelectedModel((current) => (
          current === DEFAULT_MODEL
          || models.some((m) => m.key === current && m.available !== false)
            ? current
            : DEFAULT_MODEL
        ));
      })
      .catch(console.error);
  }, []);

  const handleModelChange = useCallback((model: string) => {
    setSelectedModel(model);
    try {
      localStorage.setItem(MODEL_SELECTION_KEY, model);
    } catch {
      // Storage disabled — the selection still applies for this page session.
    }
  }, []);

  const fetchPassageContext = useCallback(async (passageId: string, window: number = 5) => {
    try {
      const resp = await fetch(`${apiEndpoint(`/api/texts/passage/${passageId}/context`)}?window=${window}`);
      if (!resp.ok) return null;
      // The backend adds workIsComplete + textEnglish; cast is safe as-is since
      // both fields are optional in the type.
      return await resp.json() as PassageContext;
    } catch (err) {
      console.error('Failed to fetch passage context:', err);
      return null;
    }
  }, []);

  const handlePassageCitationClick = useCallback(async (passageOrNodeId: string, fallbackSourceIndex?: number) => {
    const runId = runsStateRef.current.activeRunId;
    if (!runId) return;
    const run = runsStateRef.current.runs[runId];
    patchRun(runId, { rightPanelState: 'loading' });
    const ctx = await fetchPassageContext(passageOrNodeId, run?.passageWindow ?? 5);
    if (ctx) {
      patchRun(runId, { passageContext: ctx, rightPanelState: 'passage-reader' });
    } else {
      patchRun(runId, {
        rightPanelState: run?.response ? 'graph' : 'idle',
        ...(fallbackSourceIndex !== undefined ? { activeSourceIndex: fallbackSourceIndex } : {}),
      });
    }
  }, [fetchPassageContext, patchRun]);

  const handleLoadMorePassages = useCallback(async (_direction: 'up' | 'down') => {
    const runId = runsStateRef.current.activeRunId;
    if (!runId) return;
    const run = runsStateRef.current.runs[runId];
    if (!run?.passageContext) return;
    const newWindow = run.passageWindow + 5;
    patchRun(runId, { passageWindow: newWindow });
    const ctx = await fetchPassageContext(run.passageContext.target.passageId, newWindow);
    if (ctx) patchRun(runId, { passageContext: ctx });
  }, [fetchPassageContext, patchRun]);

  const handleNodeClick = useCallback(async (nodeId: string) => {
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) return;
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidPattern.test(nodeId) || nodeId.startsWith('passage_')) return;
    try {
      const node = await apiClient.getNode(nodeId);
      if (node) setSelectedNode(node);
    } catch (err) {
      console.error('Failed to fetch node:', err);
    }
  }, []);

  const handleNodeCitationClick = useCallback((nodeId: string) => {
    // B12 — open ONLY the right panel for KG scholar/argument/concept
    // citations ([P_<node_id>: ...] markers). When the cited node is part of
    // the visible answer graph, highlight it there (single surface); only fall
    // back to the NodeDetailPanel overlay when it isn't in the graph at all.
    const runId = runsStateRef.current.activeRunId;
    const run = runId ? runsStateRef.current.runs[runId] : null;
    const idx = run?.response?.sources?.findIndex((s) => s.nodeId === nodeId) ?? -1;
    if (runId && idx >= 0) {
      patchRun(runId, {
        activeSourceIndex: idx,
        passageContext: null,
        passageWindow: 5,
        rightPanelState: 'graph',
      });
      highlightNodeRef.current?.(idx);
    } else {
      // Not in the current answer graph — open the standalone detail overlay.
      handleNodeClick(nodeId);
    }
  }, [handleNodeClick, patchRun]);

  const handleCitationClick = useCallback((citationIndex: number) => {
    const runId = runsStateRef.current.activeRunId;
    if (!runId) return;
    const run = runsStateRef.current.runs[runId];
    patchRun(runId, {
      activeSourceIndex: citationIndex,
      passageContext: null,
      passageWindow: 5,
      rightPanelState: run?.response ? 'graph' : 'idle',
    });
    highlightNodeRef.current?.(citationIndex);
  }, [patchRun]);

  const handleSourceSelect = useCallback((sourceIndex: number) => {
    patchActiveRun({ activeSourceIndex: sourceIndex });
    highlightNodeRef.current?.(sourceIndex);
  }, [patchActiveRun]);

  const handleCloseDetail = useCallback(() => {
    patchActiveRun({ rightPanelState: 'graph', passageContext: null, passageWindow: 5 });
  }, [patchActiveRun]);

  // Measure nav height so two-column layout sits flush below the fixed nav
  const [navHeight, setNavHeight] = useState(57);
  useEffect(() => {
    const nav = document.getElementById('navigation');
    if (!nav) return;
    setNavHeight(nav.offsetHeight);
    const ro = new ResizeObserver(() => setNavHeight(nav.offsetHeight));
    ro.observe(nav);
    return () => ro.disconnect();
  }, []);

  // Abort every live run on unmount.
  useEffect(() => {
    const runtimes = runtimesRef.current;
    return () => {
      runtimes.forEach((runtime) => {
        runtime.userStopped = true;
        disposeRuntime(runtime);
        runtime.abort.abort();
      });
      runtimes.clear();
    };
  }, []);

  // ── Streaming ────────────────────────────────────────────────────────────

  const streamRun = useCallback(async (
    runId: string,
    queryText: string,
    effectiveModel: string,
    effectiveMode: string,
    forceRefresh: boolean,
  ) => {
    const abortController = new AbortController();
    const runtime: RunRuntime = {
      abort: abortController,
      headerTimeout: null,
      idleTimeout: null,
      connectionLost: false,
      userStopped: false,
      stepCounter: 0,
      synthesisStepId: null,
      journalStepId: null,
    };
    runtimesRef.current.set(runId, runtime);

    const patch = (p: Partial<GraphRagRun>) => dispatch({ type: 'run/patch', id: runId, patch: p });
    const addStep = (step: Omit<AgentStep, 'id' | 'timestamp'>): string => {
      runtime.stepCounter += 1;
      const stepId = `step-${runtime.stepCounter}`;
      dispatch({
        type: 'run/appendStep',
        id: runId,
        step: { ...step, id: stepId, timestamp: Date.now() } as AgentStep,
      });
      return stepId;
    };

    const clearIdleWatchdog = () => {
      if (runtime.idleTimeout !== null) {
        clearTimeout(runtime.idleTimeout);
        runtime.idleTimeout = null;
      }
    };
    const armIdleWatchdog = () => {
      clearIdleWatchdog();
      runtime.idleTimeout = setTimeout(() => {
        runtime.connectionLost = true;
        abortController.abort();
      }, STREAM_IDLE_TIMEOUT_MS);
    };

    let outcome: RunStatus = 'done';
    let rejectedByServer = false;

    try {
      const token = Cookies.get('auth_token');
      runtime.headerTimeout = setTimeout(() => {
        abortController.abort();
      }, STREAM_HEADER_TIMEOUT_MS);

      const params = new URLSearchParams({
        question: queryText,
        ancient_only: ancientOnly.toString(),
        model: effectiveModel,
        retrieval_mode: effectiveMode,
      });
      if (forceRefresh) params.set('force_refresh', 'true');

      const response = await fetch(`${apiEndpoint('/api/graphrag/query/stream')}?${params.toString()}`, {
        method: 'GET',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        signal: abortController.signal,
      });

      if (runtime.headerTimeout !== null) {
        clearTimeout(runtime.headerTimeout);
        runtime.headerTimeout = null;
      }
      armIdleWatchdog();

      if (response.status === 429) {
        // Server is at capacity. Don't leave a dead tab behind — drop the run
        // and surface a page-level notice instead.
        const retryAfter = Number(response.headers?.get?.('Retry-After'));
        rejectedByServer = true;
        setNotice(
          Number.isFinite(retryAfter) && retryAfter > 0
            ? t('graphRagUi.runs.serverBusySeconds', { seconds: Math.ceil(retryAfter) })
            : t('graphRagUi.runs.serverBusy'),
        );
        dispatch({ type: 'run/close', id: runId });
        return;
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No response body');

      let fullAnswer = '';
      let finalResponse: GraphRAGResponse | null = null;
      let buffer = '';
      // Retrieval counters accumulated from tool_result frames — the only
      // node/passage figures a degraded run leaves behind.
      let streamedNodeCount = 0;
      let streamedPassageCount = 0;
      let streamError: string | null = null;
      // UN-AUDITED draft prose (`answer_provisional`). Lives here and in the
      // run's transient `provisionalAnswer` only — never in `fullAnswer`, the
      // messages, or sessionStorage — and is cleared at teardown.
      let provisionalAnswer = '';
      // The parsed `answer_final` verdict: gated text, or an explicit
      // withholding. Authoritative fallback for every ending where the
      // terminal `complete` is missing or empty (clean EOF, trace-only
      // synthetic frame, error right after the verdict) — it must never be
      // demoted to an "incomplete" notice nor overridden by a partial buffer.
      let finalVerdict: { answer: string; withheld: boolean; reasons: string[] } | null =
        null;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          armIdleWatchdog();

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;

            try {
              const data: GraphRAGStreamEvent = JSON.parse(line.substring(6));

              switch (data.type) {
                case 'status': {
                  const payload = isRecord(data.data) ? data.data : {};
                  const messageValue = payload.message ?? data.message ?? '';
                  const msg = typeof messageValue === 'string' ? messageValue : String(messageValue);
                  const stageValue = payload.stage;
                  const stage =
                    typeof stageValue === 'string' && stageValue.trim()
                      ? stageValue
                      : msg || 'connecting';
                  patch({ streamStatus: msg, currentStage: stage });

                  // Also surface status events in the agent activity panel
                  addStep({
                    type: 'status',
                    summary: msg || 'Processing...',
                    stage,
                  });
                  break;
                }

                case 'answer_chunk': {
                  // Backend wraps any non-typed SSE payload from the agent in
                  // an `answer_chunk` envelope — including inner JSON events
                  // (citation_found, kg_node_activated, stage_complete, …)
                  // that are NOT answer text. Concatenating those blindly is
                  // what produced the wall of Unicode-escaped JSON in the
                  // chat pane. We extract the raw chunk string, skip any
                  // payload that looks like a serialized inner event, and
                  // accumulate the rest as a `complete`-event fallback only.
                  if (data.provisional === true) {
                    // A provisional-flagged chunk is a draft, not the answer.
                    const draft = typeof data.data === 'string' ? data.data : '';
                    if (draft) {
                      provisionalAnswer += draft;
                      patch({ provisionalAnswer });
                    }
                    break;
                  }
                  let answerChunk = '';
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const chunkData = data.data as any;
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const eventObj = data as any;
                  if (typeof chunkData === 'string') {
                    answerChunk = chunkData;
                  } else if (typeof eventObj.content === 'string') {
                    answerChunk = eventObj.content;
                  } else if (chunkData && typeof chunkData === 'object') {
                    answerChunk = String(chunkData.data || chunkData.chunk || chunkData.text || '');
                  }
                  const trimmed = answerChunk.trim();
                  const looksLikeInnerEvent =
                    trimmed.startsWith('{"type"') ||
                    trimmed.startsWith('{ "type"');
                  if (answerChunk && !looksLikeInnerEvent) {
                    fullAnswer += answerChunk;
                  }
                  break;
                }

                case 'answer_provisional': {
                  // UN-AUDITED prose from the synthesis, flagged provisional by
                  // the backend until the content gate, the ancient-text
                  // verifier and the citation audit have ruled. Rendered muted
                  // under a "verification pending" watermark, kept out of
                  // `fullAnswer` (the degraded-stream fallback) and cleared at
                  // teardown, so it can never be mistaken for — or persist
                  // as — the answer.
                  const draft = typeof data.data === 'string' ? data.data : '';
                  if (!draft) break;
                  provisionalAnswer += draft;
                  patch({ provisionalAnswer });
                  break;
                }

                case 'answer_final': {
                  // The verdict. Replace the provisional preview atomically:
                  // the gated text, or the withholding notice. The
                  // authoritative `complete` frame (citations, sources, graph)
                  // supersedes this bubble on arrival.
                  const verdict = isRecord(data.data) ? data.data : {};
                  const withheld = verdict.withheld === true;
                  const finalText =
                    typeof verdict.answer === 'string' ? verdict.answer.trim() : '';
                  provisionalAnswer = '';
                  if (withheld || finalText) {
                    finalVerdict = {
                      answer: withheld ? '' : finalText,
                      withheld,
                      reasons: Array.isArray(verdict.reasons)
                        ? verdict.reasons.filter((r): r is string => typeof r === 'string')
                        : [],
                    };
                    dispatch({
                      type: 'run/replaceAssistant',
                      id: runId,
                      message: {
                        role: 'assistant',
                        content: withheld ? t('graphRagUi.stream.answerWithheld') : finalText,
                        timestamp: new Date(),
                      },
                    });
                  }
                  patch({ provisionalAnswer: null, currentStage: 'finalize' });
                  break;
                }

                case 'verification_warning': {
                  // The machine-readable verdict. On a partial verdict the
                  // prose arrives holed (`*[withheld: …]*` markers) and the
                  // reader is owed a count of what was withheld and why; a
                  // blocked verdict is already explained by the answer_final
                  // withholding notice.
                  const payload = isRecord(data.data) ? data.data : {};
                  if (payload.status !== 'partial') break;
                  const withholding = isRecord(payload.withholding) ? payload.withholding : {};
                  const withheldCount =
                    typeof withholding.withheld_sentences === 'number'
                      ? withholding.withheld_sentences
                      : 0;
                  const reasons = isRecord(withholding.reasons)
                    ? Object.keys(withholding.reasons).join(', ')
                    : '';
                  patch({
                    verificationNotice: t('graphRagUi.stream.sentencesWithheld', {
                      n: withheldCount,
                      reasons: reasons || 'unverified',
                    }),
                  });
                  break;
                }

                case 'synthesis_reasoning': {
                  // LIVE chain-of-thought from the dialectical synthesis (a
                  // thinking model, ~5-10 min). Accumulate the deltas into ONE
                  // growing AGENT REASONING card in the right-panel workspace —
                  // strictly the reasoning channel, NEVER the answer.
                  const rp = data.data as
                    | string
                    | { reasoning?: string; stage?: string }
                    | undefined;
                  const delta: string =
                    typeof rp === 'string' ? rp : String(rp?.reasoning ?? '');
                  const stage: string =
                    (typeof rp === 'object' && rp?.stage) ||
                    'Reasoning over the controversy map';
                  if (!delta) break;
                  patch({
                    streamStatus: 'reasoning over the controversy map…',
                    currentStage: 'dialectical_synthesis',
                  });
                  if (runtime.synthesisStepId === null) {
                    runtime.synthesisStepId = addStep({
                      type: 'synthesis_reasoning',
                      reasoning: delta,
                      stage,
                    });
                  } else {
                    dispatch({
                      type: 'run/growStep',
                      id: runId,
                      stepId: runtime.synthesisStepId,
                      text: delta,
                      separator: '',
                      stage,
                    });
                  }
                  break;
                }

                case 'research_note': {
                  // A line of inquiry the pipeline opened and then DROPPED —
                  // real state (an empty search, a rejected claim, a gap the
                  // critic named), never a narrative. Rendered twice:
                  //   1. as its own row in the ACTIVITY timeline, inside the
                  //      phase where it happened;
                  //   2. appended to a single growing research-journal step so
                  //      the Reasoning tab has the pipeline's own reasoning to
                  //      show when the model streams no chain-of-thought.
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const notePayload = (data.data ?? data) as any;
                  const noteSummary = String(notePayload?.summary ?? '').trim();
                  if (!noteSummary) break;
                  const noteKind = (notePayload?.kind ?? 'abandoned') as ResearchNoteKind;
                  const noteDetail = notePayload?.detail
                    ? String(notePayload.detail)
                    : undefined;
                  const noteStage = notePayload?.stage
                    ? String(notePayload.stage)
                    : undefined;

                  addStep({
                    type: 'research_note',
                    noteKind,
                    summary: noteSummary,
                    detail: noteDetail,
                    stage: noteStage,
                  });

                  const journalLine = noteDetail
                    ? `— ${noteSummary}\n  ${noteDetail}`
                    : `— ${noteSummary}`;
                  if (runtime.journalStepId === null) {
                    runtime.journalStepId = addStep({
                      type: 'research_journal',
                      reasoning: journalLine,
                    });
                  } else {
                    dispatch({
                      type: 'run/growStep',
                      id: runId,
                      stepId: runtime.journalStepId,
                      text: journalLine,
                      separator: '\n\n',
                    });
                  }
                  break;
                }

                case 'tokens_used_rollup':
                case 'cost_summary': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const p = (data.data ?? data) as any;
                  patch({
                    cost: {
                      total_tokens: Number(p.total_tokens ?? 0),
                      total_cost_usd: Number(p.total_cost_usd ?? 0),
                    },
                  });
                  break;
                }

                case 'cache_hit': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const p = (data.data ?? data) as any;
                  patch({
                    cacheInfo: {
                      cacheKeyShort: String(p.cache_key_short ?? ''),
                      originalTraceId:
                        p.original_trace_id != null && p.original_trace_id !== ''
                          ? String(p.original_trace_id)
                          : null,
                      originalCostUsd: Number(p.original_cost_usd ?? 0),
                      originalTokens: Number(p.original_tokens ?? 0),
                      cachedAt: String(p.cached_at ?? ''),
                      hitCount: Number(p.hit_count ?? 0),
                    },
                  });
                  break;
                }

                case 'citations_preview':
                  // Early structured-citation frame emitted by the agent right
                  // after ProgrammaticVerify, BEFORE the long verifier-v2 audit
                  // (which can push the terminal `complete` past Cloudflare's
                  // ~100s cut). Adopt it as the working `finalResponse` so the
                  // UI has clickable citations even if the connection drops
                  // before the authoritative `complete` arrives. The real
                  // `complete` (audited) supersedes it on arrival.
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  finalResponse = (data.data as any) as GraphRAGResponse;
                  patch({ currentStage: 'citation_verification' });
                  break;

                case 'complete':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  finalResponse = (data.data as any) as GraphRAGResponse;
                  patch({ currentStage: 'finalize' });
                  break;

                case 'agent_thinking': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const thinkPayload = data.data as any;
                  addStep({
                    type: 'thinking',
                    thinking: thinkPayload?.thinking || '',
                    summary: thinkPayload?.summary || '',
                    remaining: thinkPayload?.remaining,
                  });
                  break;
                }

                case 'tool_start': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const startPayload = data.data as any;
                  addStep({
                    type: 'tool_start',
                    tool: startPayload?.tool,
                    args: startPayload?.args,
                    reason: startPayload?.reason,
                  });
                  if (typeof startPayload?.tool === 'string') {
                    patch({ currentStage: `tool:${startPayload.tool}` });
                  }
                  break;
                }

                case 'tool_result': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const resultPayload = data.data as any;
                  addStep({
                    type: 'tool_result',
                    tool: resultPayload?.tool,
                    summary: resultPayload?.summary,
                    durationMs: resultPayload?.duration_ms,
                    nodeCount: resultPayload?.node_count,
                    passageCount: resultPayload?.passage_count,
                  });
                  streamedNodeCount += Number(resultPayload?.node_count ?? 0);
                  streamedPassageCount += Number(resultPayload?.passage_count ?? 0);
                  break;
                }

                case 'error':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  streamError = (data as any).data?.message || data.message || 'Stream error';
                  patch({ error: streamError });
                  break;
              }
            } catch (err) {
              console.error('Error parsing SSE line:', line, err);
            }
          }

          // An explicit `error` frame does NOT stop the read: the server
          // always follows it with a terminal `complete` carrying whatever
          // gated answer already shipped (and the trace id). Stopping here
          // would drop that frame; a stalled stream is the idle watchdog's job.
        }
      } finally {
        clearIdleWatchdog();
        await reader.cancel().catch(() => {});
        reader.releaseLock();
      }

      if (streamError) outcome = 'error';

      if (finalResponse) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const serverResp = finalResponse as any;
        const rawCitations = finalResponse.citations || {};
        const ancientRaw = Array.isArray(rawCitations.ancient_sources)
          ? rawCitations.ancient_sources
          : Array.isArray(serverResp.ancientCitations)
            ? serverResp.ancientCitations
            : [];
        const modernRaw = Array.isArray(rawCitations.modern_scholarship)
          ? rawCitations.modern_scholarship
          : Array.isArray(serverResp.modernBibliography)
            ? serverResp.modernBibliography
            : [];
        const citations = {
          ancient_sources: ancientRaw.map((c: unknown) =>
            typeof c === 'string'
              ? c
              : ((c as { citationText?: string; label?: string })?.citationText
                  || (c as { citationText?: string; label?: string })?.label
                  || '')
          ).filter(Boolean),
          modern_scholarship: modernRaw.map((c: unknown) =>
            typeof c === 'string'
              ? c
              : ((c as { citation?: string; citationText?: string })?.citation
                  || (c as { citation?: string; citationText?: string })?.citationText
                  || '')
          ).filter(Boolean),
        };

        if (finalResponse.sources && Array.isArray(finalResponse.sources)) {
          const firstSource = finalResponse.sources[0] as unknown;
          if (firstSource && typeof firstSource === 'string') {
            const stringArray = finalResponse.sources as unknown as string[];
            finalResponse.sources = stringArray.map((label: string, index: number) => ({
              id: index + 1,
              nodeId: `source_${index}`,
              nodeLabel: label || 'Unknown',
              nodeType: 'Unknown',
              metadata: {}
            }));
          }
        } else if (!finalResponse.sources) {
          const reasoningPath = finalResponse.reasoning_path;
          if (reasoningPath) {
            const startingNodes = (reasoningPath.starting_nodes || []).map((node, index) => ({
              id: index + 1,
              nodeId: node.id,
              nodeLabel: node.label || 'Unknown',
              nodeType: node.type || 'Unknown',
              metadata: { confidence: (node as { semantic_score?: number }).semantic_score }
            }));
            const expandedNodes = (reasoningPath.expanded_nodes || []).map((node, index) => ({
              id: startingNodes.length + index + 1,
              nodeId: node.id,
              nodeLabel: node.label || 'Unknown',
              nodeType: node.type || 'Unknown',
              metadata: {}
            }));
            finalResponse.sources = [...startingNodes, ...expandedNodes];
          }
        }

        const serverAncientCitations = Array.isArray((finalResponse as unknown as Record<string, unknown>).ancientCitations)
          ? (finalResponse as unknown as Record<string, unknown>).ancientCitations as unknown[]
          : [];
        const allCitations = serverAncientCitations
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          .map((c: any) => (typeof c === 'string' ? c : c?.citationText))
          .filter((c: unknown): c is string => typeof c === 'string' && c.trim().length > 0);

        const formattedCitationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};
        if (allCitations.length > 0) {
          try {
            const { fetchCitationPassages } = await import('../../services/citationService');
            const citationTexts = await fetchCitationPassages(allCitations);
            Object.entries(citationTexts).forEach(([citation, passage]) => {
              if (passage.original || passage.translation) {
                formattedCitationTexts[citation] = {
                  original: passage.original || '',
                  originalLanguage: passage.originalLanguage || '',
                  translation: passage.translation || ''
                };
              }
            });
          } catch (err) {
            console.error('Failed to fetch citation texts:', err);
          }
        }

        const responseMetadata = isRecord(serverResp.metadata)
          ? serverResp.metadata
          : {};
        const publicationGate = isRecord(responseMetadata.publication_gate)
          ? responseMetadata.publication_gate
          : {};
        // Fail closed across the two sources of truth: a withheld verdict is
        // never overridden by a terminal frame, and a terminal frame that
        // carries no answer (trace-only synthetic `complete`, error path)
        // falls back to the gated verdict text before the raw chunk buffer.
        const publicationBlocked =
          publicationGate.publishable === false || finalVerdict?.withheld === true;
        if (!publicationBlocked && !finalResponse.answer?.trim() && finalVerdict?.answer) {
          finalResponse.answer = finalVerdict.answer;
        }
        const assistantContent = publicationBlocked
          ? t('graphRagUi.stream.answerWithheld')
          : finalResponse.answer?.trim() || fullAnswer || '(No answer generated)';

        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: assistantContent,
          citations,
          reasoning_path: finalResponse.reasoning_path,
          tokens_used: finalResponse.tokens_used,
          llm_provider: finalResponse.llm_provider || 'gemini',
          llm_model: finalResponse.llm_model || 'gemini-3.1-pro-preview',
          retrieval_mode: effectiveMode,
          timestamp: new Date(),
          citationTexts: formattedCitationTexts,
          graphrag_response: finalResponse,
        };
        // Replace ALL assistant messages with the final enriched one
        // (streaming may have created one or more partial assistant messages)
        dispatch({ type: 'run/replaceAssistant', id: runId, message: assistantMessage });
        patch({
          response: finalResponse,
          ...(finalResponse.reasoning_trace
            ? { reasoningTrace: finalResponse.reasoning_trace as ReasoningTraceStep[] }
            : {}),
          ...(finalResponse.metrics
            ? {
                metrics: {
                  modelLabel: finalResponse.metrics.model_label ?? effectiveModel,
                  retrievalMode: finalResponse.metrics.retrieval_mode_used ?? effectiveMode,
                  estimatedCost: finalResponse.metrics.estimated_cost_usd ?? null,
                  answerLengthChars:
                    finalResponse.metrics.answer_length_chars ?? assistantMessage.content.length,
                  modelContext:
                    modelContextMapRef.current[finalResponse.metrics.model_key ?? effectiveModel]
                    ?? 1_000_000,
                },
              }
            : {}),
        });
        // Keep the right panel on the reasoning timeline after completion —
        // the timeline auto-collapses phases and grows a Sources/KG/Cost
        // footer. The user can drill into the graph view via the footer.

        // Survive navigation: snapshot the answer + response so a click on
        // a citation badge that opens /texts (or any other route) followed
        // by a browser back returns the user to their Q&A intact.
        try {
          sessionStorage.setItem(
            SESSION_KEY_MESSAGES,
            JSON.stringify([
              { role: 'user', content: queryText, timestamp: new Date() },
              assistantMessage,
            ]),
          );
          sessionStorage.setItem(
            SESSION_KEY_RESPONSE,
            JSON.stringify(finalResponse),
          );
        } catch {
          // Quota exceeded or storage disabled — degrade silently.
        }
      } else if (finalVerdict) {
        // The verdict ruled but the terminal `complete` never arrived (clean
        // EOF or a cut right after `answer_final`). The verdict is
        // authoritative — gated text, or an explicit withholding — so it is
        // kept as the answer rather than demoted to an "incomplete" notice.
        const verdictMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: finalVerdict.withheld
            ? t('graphRagUi.stream.answerWithheld')
            : finalVerdict.answer,
          timestamp: new Date(),
        };
        dispatch({ type: 'run/replaceAssistant', id: runId, message: verdictMessage });
        const verdictResponse: GraphRAGResponse = {
          query: queryText,
          answer: finalVerdict.answer,
          citations: { ancient_sources: [], modern_scholarship: [] },
          sources: [],
          reasoning_path: {
            starting_nodes: [],
            expanded_nodes: [],
            traversed_edges: [],
            total_nodes: streamedNodeCount,
            total_edges: 0,
          },
          nodes_used: streamedNodeCount,
          edges_traversed: 0,
          degraded: false,
          success: !finalVerdict.withheld,
        };
        patch({ response: verdictResponse });
        try {
          sessionStorage.setItem(
            SESSION_KEY_MESSAGES,
            JSON.stringify([
              { role: 'user', content: queryText, timestamp: new Date() },
              verdictMessage,
            ]),
          );
          sessionStorage.setItem(SESSION_KEY_RESPONSE, JSON.stringify(verdictResponse));
        } catch {
          // Quota exceeded or storage disabled — degrade silently.
        }
      } else {
        // The agent loop finished without a `complete` event (synthesis cut
        // mid-stream, CF tunnel idle-timeout, etc.). Render a clean error
        // bubble instead of dumping raw chunks, and keep the reasoning
        // timeline visible so the user can see how far the agent got.
        outcome = 'error';
        const partialAnswer = fullAnswer.trim();
        const degradedMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content:
            partialAnswer.length > 200
              ? partialAnswer
              : t('graphRagUi.stream.incomplete', {
                  nodes: streamedNodeCount,
                  passages: streamedPassageCount,
                }),
          timestamp: new Date(),
        };
        // Replace rather than append so the run never shows two assistant
        // bubbles. (A run that received an `answer_final` verdict never gets
        // here — the branch above keeps the verdict.)
        dispatch({ type: 'run/replaceAssistant', id: runId, message: degradedMessage });

        // Bind the right-panel header to what the run actually produced,
        // instead of leaving it on the empty pre-query placeholder.
        const degradedResponse: GraphRAGResponse = {
          query: queryText,
          answer: partialAnswer,
          citations: { ancient_sources: [], modern_scholarship: [] },
          sources: [],
          reasoning_path: {
            starting_nodes: [],
            expanded_nodes: [],
            traversed_edges: [],
            total_nodes: streamedNodeCount,
            total_edges: 0,
          },
          nodes_used: streamedNodeCount,
          edges_traversed: 0,
          degraded: true,
          success: false,
        };
        patch({ response: degradedResponse });
        // Stay on the reasoning timeline so the user retains context.
      }
    } catch (err: unknown) {
      console.error('Streaming error:', err);
      if (runtime.userStopped) {
        // Deliberate stop — not an error worth surfacing.
        outcome = 'stopped';
      } else if (runtime.connectionLost) {
        outcome = 'error';
        patch({ error: t('graphRagUi.stream.connectionLost') });
      } else if (err instanceof Error && err.name === 'AbortError') {
        outcome = 'error';
        patch({ error: t('errors.networkErrorDesc'), rightPanelState: 'idle' });
      } else {
        outcome = 'error';
        patch({
          error: err instanceof Error ? err.message : 'Streaming failed',
          rightPanelState: 'idle',
        });
      }
    } finally {
      // Single teardown for every exit path — normal completion, degraded
      // stream, SSE `error` frame, idle watchdog abort, user stop, throw,
      // 429 rejection (whose run no longer exists — the patch is a no-op).
      disposeRuntime(runtime);
      runtimesRef.current.delete(runId);
      if (!rejectedByServer) {
        patch({
          status: runtime.userStopped ? 'stopped' : outcome,
          agentActive: false,
          streamStatus: '',
          streamEnded: true,
          // Un-audited draft never outlives the stream.
          provisionalAnswer: null,
        });
      }
    }
  }, [ancientOnly, t]);

  const processQuery = useCallback(async (
    queryText: string,
    options?: { model?: string; mode?: string; forceRefresh?: boolean },
  ) => {
    const text = queryText.trim();
    if (!text) return;

    if (atCapacity()) {
      setNotice(t('graphRagUi.runs.capReached', { max: MAX_CONCURRENT_RUNS }));
      return;
    }

    const model = options?.model ?? selectedModel;
    const mode = options?.mode ?? DEFAULT_MODE;
    runSeqRef.current += 1;
    const runId = `run_${Date.now()}_${runSeqRef.current}`;

    const userMessage: GraphRAGChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    // Creating the run also makes it the active tab.
    dispatch({
      type: 'run/open',
      run: createRun({
        id: runId,
        question: text,
        model,
        mode,
        status: 'streaming',
        agentActive: true,
        streamStatus: 'Connecting...',
        rightPanelState: 'reasoning',
        messages: [userMessage],
      }),
    });
    setQuery('');
    setNotice(null);

    await streamRun(runId, text, model, mode, options?.forceRefresh ?? false);
  }, [atCapacity, selectedModel, streamRun, t]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const text = query.trim();
    if (!text) return;

    if (atCapacity()) {
      setNotice(t('graphRagUi.runs.capReached', { max: MAX_CONCURRENT_RUNS }));
      return;
    }

    if (!isAuthenticated) {
      setPendingQuery(text);
      setShowAuthModal(true);
      return;
    }

    void processQuery(text);
  }, [query, isAuthenticated, atCapacity, processQuery, t]);

  const initialQueryProcessedRef = useRef(false);
  useEffect(() => {
    const state = location.state as { initialQuery?: string } | null;
    // Accept an initial question from router state (in-app navigation) or from
    // a `?q=` query param (deep links, schema.org SearchAction).
    const queryParam = new URLSearchParams(location.search).get('q')?.trim();
    const initialQuery = state?.initialQuery ?? (queryParam || undefined);
    if (initialQuery && !initialQueryProcessedRef.current) {
      if (isAuthenticated) {
        initialQueryProcessedRef.current = true;
        processQuery(initialQuery);
        window.history.replaceState({}, document.title);
      } else {
        setPendingQuery(initialQuery);
        setShowAuthModal(true);
        window.history.replaceState({}, document.title);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, location.search, isAuthenticated]);

  const handleAuthSuccess = useCallback(() => {
    if (pendingQuery) {
      void processQuery(pendingQuery);
      setPendingQuery(null);
    }
  }, [pendingQuery, processQuery]);

  /** Stops ONE run — the active tab's, from the Stop button. */
  const stopRun = useCallback((runId: string) => {
    const runtime = runtimesRef.current.get(runId);
    if (!runtime) return;
    runtime.userStopped = true;
    disposeRuntime(runtime);
    runtime.abort.abort();
    dispatch({
      type: 'run/patch',
      id: runId,
      patch: { status: 'stopped', agentActive: false, streamStatus: '', streamEnded: true },
    });
  }, []);

  const handleStop = useCallback(() => {
    if (activeRunId) stopRun(activeRunId);
  }, [activeRunId, stopRun]);

  /** Closing a tab aborts its stream if it is still live. */
  const handleCloseRun = useCallback((runId: string) => {
    const runtime = runtimesRef.current.get(runId);
    if (runtime) {
      runtime.userStopped = true;
      disposeRuntime(runtime);
      runtime.abort.abort();
      runtimesRef.current.delete(runId);
    }
    // Closing the last tab is an explicit "clear my workspace" — drop the
    // navigation snapshot too, so a browser back doesn't resurrect it.
    const { order } = runsStateRef.current;
    if (order.length === 1 && order[0] === runId) {
      try {
        sessionStorage.removeItem(SESSION_KEY_MESSAGES);
        sessionStorage.removeItem(SESSION_KEY_RESPONSE);
      } catch {
        // Storage disabled — nothing to clear.
      }
    }
    dispatch({ type: 'run/close', id: runId });
  }, []);

  const handleRunSelect = useCallback((runId: string) => {
    dispatch({ type: 'run/activate', id: runId });
  }, []);

  // Demo Mode — a fully-formed run, no stream.
  const loadDemoMode = useCallback(() => {
    const citationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};

    const demoMessage: GraphRAGChatMessage = {
      role: 'user',
      content: mockGraphRAGResponse.query,
      timestamp: new Date(),
    };

    const assistantMessage: GraphRAGChatMessage = {
      role: 'assistant',
      content: mockGraphRAGResponse.answer,
      timestamp: new Date(),
      citations: {
        ancient_sources: [
          "Cicero, On Fate 41-43",
          "Cicero, On Fate 42-43; Aulus Gellius, Attic Nights 7.2.11",
          "Epictetus, Discourses 1.1; SVF 2.974-975",
        ],
        modern_scholarship: [
          "Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy.",
          "Frede, M. (2011). A Free Will: Origins of the Notion in Ancient Thought.",
        ]
      },
      citationTexts,
      reasoning_path: mockGraphRAGResponse.reasoning_path,
      graphrag_response: mockGraphRAGResponse,
      reasoning_steps: mockReasoningSteps
    };

    runSeqRef.current += 1;
    dispatch({
      type: 'run/open',
      run: createRun({
        id: `run_demo_${runSeqRef.current}`,
        question: mockGraphRAGResponse.query,
        model: DEFAULT_MODEL,
        mode: DEFAULT_MODE,
        status: 'done',
        streamEnded: true,
        messages: [demoMessage, assistantMessage],
        response: mockGraphRAGResponse,
        rightPanelState: 'graph',
      }),
    });
    setQuery('');
  }, []);

  // Retry with a different model: prompt user via simple inline select
  const availableModels = Object.keys(modelContextMap).length > 0
    ? Object.keys(modelContextMap)
    : [DEFAULT_MODEL, 'gemini-3.1-pro-preview', 'kimi-k2.5-thinking'];

  const handleRetry = useCallback(() => {
    if (!activeRun?.question) return;
    setShowRetryDropdown((p) => !p);
  }, [activeRun?.question]);

  const handleRetryWithModel = useCallback((model: string) => {
    setShowRetryDropdown(false);
    if (!activeRun?.question) return;
    void processQuery(activeRun.question, { model, mode: DEFAULT_MODE });
  }, [activeRun?.question, processQuery]);

  // Force a fresh (non-cached) run of the active question. Same code path as a
  // normal submission — it simply opens another run with force_refresh=true.
  const handleRegenerate = useCallback(() => {
    if (!activeRun?.question) return;
    void processQuery(activeRun.question, { forceRefresh: true });
  }, [activeRun?.question, processQuery]);

  const advancedProps = {
    ancientOnly, setAncientOnly,
  };

  const activeStreaming = activeRun?.status === 'streaming';
  const activeMessages = activeRun?.messages ?? [];
  const activeReasoningTrace = activeRun?.reasoningTrace ?? [];
  const rightPanelState = activeRun?.rightPanelState ?? 'idle';

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="relative w-full min-h-screen overflow-hidden">
        <div className="relative z-10 min-h-screen">

          {/* WELCOME STATE */}
          {orderedRuns.length === 0 && (
            <WelcomeHero
              query={query}
              setQuery={setQuery}
              notice={notice}
              inputRef={inputRef}
              onSubmit={handleSubmit}
              onDemo={loadDemoMode}
              selectedModel={selectedModel}
              modelOptions={modelOptions}
              onModelChange={handleModelChange}
              advancedProps={advancedProps}
            />
          )}

          {/* TWO-COLUMN LAYOUT */}
          {orderedRuns.length > 0 && (
            <div
              className="flex bg-parchment-50 relative"
              style={{
                position: 'fixed',
                top: navHeight,
                left: 0,
                right: 0,
                bottom: 0,
                height: `calc(100vh - ${navHeight}px)`,
                zIndex: 20,
              }}
            >
              <ChatPanel
                messages={activeMessages}
                query={query}
                setQuery={setQuery}
                streaming={Boolean(activeStreaming)}
                canSubmit={canSubmit}
                maxConcurrentRuns={MAX_CONCURRENT_RUNS}
                runStartedAt={activeRun?.createdAt}
                currentStage={activeRun?.currentStage}
                streamStatus={activeRun?.streamStatus}
                provisionalAnswer={activeRun?.provisionalAnswer ?? null}
                verificationNotice={activeRun?.verificationNotice ?? null}
                error={activeRun?.error ?? null}
                onDismissError={() => patchActiveRun({ error: null })}
                notice={notice}
                onDismissNotice={() => setNotice(null)}
                inputRef={inputRef}
                onSubmit={handleSubmit}
                onStop={handleStop}
                onNodeClick={handleNodeClick}
                onCitationClick={handleCitationClick}
                onPassageCitationClick={handlePassageCitationClick}
                onNodeCitationClick={handleNodeCitationClick}
                runs={runTabs}
                activeRunId={activeRunId}
                onRunSelect={handleRunSelect}
                onRunClose={handleCloseRun}
                onRetry={handleRetry}
                lastMetrics={activeRun?.metrics ?? null}
                cacheInfo={activeRun?.cacheInfo ?? null}
                onRegenerate={handleRegenerate}
                selectedModel={selectedModel}
                modelOptions={modelOptions}
                onModelChange={handleModelChange}
              />

              {/* RIGHT PANEL - desktop graph workspace */}
              <div className="hidden lg:flex flex-col w-[40%] h-full bg-parchment-50 border-l border-amber-200/40">
                <div className="flex-1 min-h-0 overflow-hidden p-3 xl:p-4 flex flex-col">
                  {/* Main graph panel */}
                  <div className={`${showReasoningTrace && activeReasoningTrace.length > 0 ? 'h-[60%]' : 'flex-1'} min-h-0`}>
                    <RightPanel
                      state={rightPanelState}
                      response={activeRun?.response ?? null}
                      allResponses={allResponses}
                      activeSourceIndex={activeRun?.activeSourceIndex ?? null}
                      passageContext={activeRun?.passageContext ?? null}
                      agentSteps={activeRun?.agentSteps ?? []}
                      agentActive={Boolean(activeRun?.agentActive)}
                      isStreaming={Boolean(activeStreaming)}
                      streamEnded={Boolean(activeRun?.streamEnded)}
                      cost={activeRun?.cost ?? null}
                      onNodeClick={handleNodeClick}
                      onSourceSelect={handleSourceSelect}
                      onCloseDetail={handleCloseDetail}
                      onLoadMorePassages={handleLoadMorePassages}
                      onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
                      onOpenGraphView={() => patchActiveRun({ rightPanelState: 'graph' })}
                      className="h-full"
                    />
                  </div>

                  {/* Reasoning Trace toggle + panel */}
                  {activeReasoningTrace.length > 0 && (
                    <div className="shrink-0 mt-2">
                      <button
                        onClick={() => setShowReasoningTrace(!showReasoningTrace)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-500 hover:text-stone-700 transition-colors w-full border-t border-amber-200/40 pt-2"
                      >
                        <span className="inline-block w-2 h-2 rounded-full bg-amber-400" />
                        {showReasoningTrace ? 'Hide' : 'Show'} FSM Reasoning Trace ({activeReasoningTrace.length} steps)
                      </button>
                    </div>
                  )}
                  {showReasoningTrace && activeReasoningTrace.length > 0 && (
                    <div className="h-[38%] min-h-[180px] overflow-y-auto border-t border-amber-200/40 mt-1 rounded-lg bg-white/60">
                      <ReasoningPanel steps={activeReasoningTrace} />
                    </div>
                  )}
                </div>
              </div>

              {/* MOBILE floating sheet */}
              <MobileGraphSheet
                rightPanelState={rightPanelState}
                response={activeRun?.response ?? null}
                allResponses={allResponses}
                activeSourceIndex={activeRun?.activeSourceIndex ?? null}
                passageContext={activeRun?.passageContext ?? null}
                agentSteps={activeRun?.agentSteps ?? []}
                agentActive={Boolean(activeRun?.agentActive)}
                isStreaming={Boolean(activeStreaming)}
                streamEnded={Boolean(activeRun?.streamEnded)}
                cost={activeRun?.cost ?? null}
                onNodeClick={handleNodeClick}
                onSourceSelect={handleSourceSelect}
                onCloseDetail={handleCloseDetail}
                onLoadMorePassages={handleLoadMorePassages}
                onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
              />

              {/* Retry-with-model dropdown overlay */}
              {showRetryDropdown && (
                <div
                  className="absolute top-0 left-0 right-0 bottom-0 z-50 flex items-start justify-center pt-16 bg-black/20"
                  onClick={() => setShowRetryDropdown(false)}
                >
                  <div
                    className="bg-white rounded-2xl shadow-xl border border-amber-200/60 p-4 w-72"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
                      {t('graphRagUi.runs.retryTooltip')}
                    </p>
                    <div className="space-y-1">
                      {availableModels.map((model) => (
                        <button
                          key={model}
                          onClick={() => handleRetryWithModel(model)}
                          className={[
                            'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                            model === selectedRetryModel
                              ? 'bg-amber-50 text-amber-900 font-medium border border-amber-200/60'
                              : 'text-stone-700 hover:bg-stone-50',
                          ].join(' ')}
                        >
                          {model}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        <AuthModal
          isOpen={showAuthModal}
          onClose={() => { setShowAuthModal(false); setPendingQuery(null); }}
          onSuccess={handleAuthSuccess}
          title="Authentication Required"
          message="Please log in to use GraphRAG Q&A"
        />

        {selectedNode && (
          <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
        )}
      </div>
    </div>
  );
}
