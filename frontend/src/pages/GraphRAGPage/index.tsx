import { useState, useRef, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import AuthModal from '../../components/AuthModal';
import NodeDetailPanel from '../../components/NodeDetailPanel';
import RightPanel from '../../components/graphrag/RightPanel';
import type { RightPanelState } from '../../components/graphrag/RightPanel';
import { ReasoningPanel } from '../../components/ReasoningPanel';
import type { ReasoningTraceStep } from '../../components/ReasoningPanel';
import type { ResponseTab } from '../../components/ResponseTabs';
import WelcomeHero from './WelcomeHero';
import ChatPanel from './ChatPanel';
import MobileGraphSheet from './MobileGraphSheet';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../../types';
import type { AgentStep, PassageContext, ResearchNoteKind } from '../../types/graphrag';
import type { CacheBadgeInfo } from '../../components/research/CostCounter';
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

// Time-to-first-byte budget for the SSE handshake.
const STREAM_HEADER_TIMEOUT_MS = 120_000;
// Mid-stream silence budget: the backend heartbeats far more often than this,
// so a longer gap means the connection died without an SSE `error` frame
// (Cloudflare tunnel drop, worker OOM, …).
const STREAM_IDLE_TIMEOUT_MS = 95_000;

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

export default function GraphRAGPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const [messages, setMessages] = useState<GraphRAGChatMessage[]>(() =>
    _restoreMessages(),
  );
  const [query, setQuery] = useState('');
  const [loading, _setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [_streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { isAuthenticated } = useAuth();

  // Model & mode selection
  // Model + retrieval mode are no longer user-facing — backend is Kimi K2.6
  // on Fireworks via vectorless agentic RAG. Kept as locals (not state) so
  // any legacy code path that still references them compiles.
  const selectedModel = 'kimi-k2.6';
  const selectedMode = 'auto';

  // Advanced settings
  const [ancientOnly, setAncientOnly] = useState(false);
  const [showRetryDropdown, setShowRetryDropdown] = useState(false);
  const [selectedRetryModel] = useState('kimi-k2.6');

  // Right panel
  const [rightPanelState, setRightPanelState] = useState<RightPanelState>('idle');
  const [activeSourceIndex, setActiveSourceIndex] = useState<number | null>(null);
  const [rightPanelResponse, setRightPanelResponse] = useState<GraphRAGResponse | null>(
    () => _restoreResponse(),
  );
  const [allResponses, setAllResponses] = useState<GraphRAGResponse[]>([]);
  const highlightNodeRef = useRef<((citationIndex: number) => void) | null>(null);
  const [passageContext, setPassageContext] = useState<PassageContext | null>(null);
  const [passageWindow, setPassageWindow] = useState(5);

  // Response tabs (for retry-with-different-model)
  const [responseTabs, setResponseTabs] = useState<ResponseTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>('');
  const [tabMessages, setTabMessages] = useState<Record<string, GraphRAGChatMessage[]>>({});
  const [tabResponses, setTabResponses] = useState<Record<string, GraphRAGResponse | null>>({});
  const [reasoningTraces, setReasoningTraces] = useState<Record<string, ReasoningTraceStep[]>>({});
  const [initialQuestion, setInitialQuestion] = useState<string>('');

  // Right panel reasoning trace toggle
  const [showReasoningTrace, setShowReasoningTrace] = useState(false);

  // Agent activity tracking (ReAct loop)
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [agentActive, setAgentActive] = useState(false);
  // True once a run's SSE stream has closed, however it ended. Lets the right
  // panel tell "no trace captured" apart from "synthesis hasn't started yet".
  const [streamEnded, setStreamEnded] = useState(false);
  const [streamCost, setStreamCost] = useState<{ total_tokens: number; total_cost_usd: number } | null>(null);
  const agentStepCounterRef = useRef(0);
  // Set by stopStreaming so the resulting AbortError isn't surfaced as a failure.
  const userStoppedRef = useRef(false);
  // Live dialectical-synthesis reasoning accumulates into ONE growing step
  // (the right-panel AGENT REASONING card), so we track its id across deltas.
  const synthesisReasoningStepIdRef = useRef<string | null>(null);
  // The pipeline's own research journal (abandoned leads) also accumulates into
  // ONE growing step, so the Reasoning tab has something honest to show on the
  // models that expose no chain-of-thought (the Claude rung, by design).
  const researchJournalStepIdRef = useRef<string | null>(null);

  // Cache replay state: populated when backend emits a `cache_hit` SSE event
  // before the `complete` event. Reset to null at the start of every query so
  // a fresh run never displays a stale cache badge.
  const [cacheInfo, setCacheInfo] = useState<CacheBadgeInfo | null>(null);
  // When true, the next streaming query appends `force_refresh=true` to the
  // SSE URL, bypassing the backend answer cache. Auto-resets to false after
  // the URL is built so subsequent natural queries don't auto-bypass.
  const [forceRefresh, setForceRefresh] = useState(false);

  // Token budget / cost metrics from last response
  interface LastMetrics {
    modelLabel: string;
    retrievalMode: string;
    estimatedCost: number | null;
    answerLengthChars: number;
    modelContext: number;
  }
  const [lastMetrics, setLastMetrics] = useState<LastMetrics | null>(null);
  const [modelContextMap, setModelContextMap] = useState<Record<string, number>>({});

  useEffect(() => {
    const apiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') ?? '';
    fetch(`${apiUrl}/api/graphrag/models`)
      .then((r) => r.json())
      .then((models: Array<{ key: string; context: number }>) => {
        const map: Record<string, number> = {};
        models.forEach((m) => { map[m.key] = m.context; });
        setModelContextMap(map);
      })
      .catch(console.error);
  }, []);

  const fetchPassageContext = useCallback(async (passageId: string, window: number = 5) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const resp = await fetch(`${apiUrl}/api/texts/passage/${passageId}/context?window=${window}`);
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
    setRightPanelState('loading');
    const ctx = await fetchPassageContext(passageOrNodeId, passageWindow);
    if (ctx) {
      setPassageContext(ctx);
      setRightPanelState('passage-reader');
    } else {
      if (fallbackSourceIndex !== undefined) {
        setActiveSourceIndex(fallbackSourceIndex);
        setRightPanelState(rightPanelResponse ? 'graph' : 'idle');
      } else {
        setRightPanelState(rightPanelResponse ? 'graph' : 'idle');
      }
    }
  }, [fetchPassageContext, passageWindow, rightPanelResponse]);

  const handleLoadMorePassages = useCallback(async (_direction: 'up' | 'down') => {
    if (!passageContext) return;
    const newWindow = passageWindow + 5;
    setPassageWindow(newWindow);
    const ctx = await fetchPassageContext(passageContext.target.passageId, newWindow);
    if (ctx) {
      setPassageContext(ctx);
    }
  }, [passageContext, passageWindow, fetchPassageContext]);

  const handleNodeCitationClick = useCallback((nodeId: string) => {
    // B12 — open ONLY the right panel for KG scholar/argument/concept
    // citations ([P_<node_id>: ...] markers). When the cited node is part of
    // the visible answer graph, highlight it there (single surface); only fall
    // back to the NodeDetailPanel overlay when it isn't in the graph at all.
    const idx = rightPanelResponse?.sources?.findIndex((s) => s.nodeId === nodeId) ?? -1;
    if (idx >= 0) {
      setActiveSourceIndex(idx);
      setPassageContext(null);
      setPassageWindow(5);
      setRightPanelState(rightPanelResponse ? 'graph' : 'idle');
      highlightNodeRef.current?.(idx);
    } else {
      // Not in the current answer graph — open the standalone detail overlay.
      handleNodeClick(nodeId);
    }
  }, [rightPanelResponse]); // handleNodeClick is stable (no deps that change)

  const handleCitationClick = useCallback((citationIndex: number) => {
    setActiveSourceIndex(citationIndex);
    setPassageContext(null);
    setPassageWindow(5);
    setRightPanelState(rightPanelResponse ? 'graph' : 'idle');
    highlightNodeRef.current?.(citationIndex);
  }, [rightPanelResponse]);


  const handleSourceSelect = useCallback((sourceIndex: number) => {
    setActiveSourceIndex(sourceIndex);
    highlightNodeRef.current?.(sourceIndex);
  }, []);

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

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  // Demo Mode
  const loadDemoMode = () => {
    const demoMessage: GraphRAGChatMessage = {
      role: 'user',
      content: mockGraphRAGResponse.query,
      timestamp: new Date()
    };

    const citationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};

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

    setMessages([demoMessage, assistantMessage]);
    setRightPanelResponse(mockGraphRAGResponse);
    setAllResponses((prev) => [...prev, mockGraphRAGResponse]);
    setRightPanelState('graph');
    setQuery('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading || streaming) return;

    if (!isAuthenticated) {
      setPendingQuery(query.trim());
      setShowAuthModal(true);
      return;
    }

    await processQuery(query.trim());
  };

  const processQuery = useCallback(async (queryText: string, retryModel?: string, retryMode?: string) => {
    const isRetry = retryModel !== undefined;
    const model = retryModel ?? selectedModel;
    const mode = retryMode ?? selectedMode;

    if (!isRetry) {
      // First query: create initial tab
      const tabId = `tab_${Date.now()}`;
      const userMessage: GraphRAGChatMessage = {
        role: 'user',
        content: queryText,
        timestamp: new Date(),
      };

      setMessages([userMessage]);
      setInitialQuestion(queryText);
      setResponseTabs([{ id: tabId, label: model.split('-').slice(0, 2).join('-'), model, mode }]);
      setActiveTabId(tabId);
      setTabMessages((prev) => ({ ...prev, [tabId]: [userMessage] }));
      setTabResponses((prev) => ({ ...prev, [tabId]: null }));
      setQuery('');
      setError(null);

      await handleStreamingQuery(queryText, tabId, model, mode);
    } else {
      // Retry: create new tab, re-send the same question
      const tabId = `tab_${Date.now()}`;
      const userMessage: GraphRAGChatMessage = {
        role: 'user',
        content: queryText,
        timestamp: new Date(),
      };

      setResponseTabs((prev) => [...prev, { id: tabId, label: model.split('-').slice(0, 2).join('-'), model, mode }]);
      setActiveTabId(tabId);
      setMessages([userMessage]);
      setTabMessages((prev) => ({ ...prev, [tabId]: [userMessage] }));
      setTabResponses((prev) => ({ ...prev, [tabId]: null }));
      setError(null);

      await handleStreamingQuery(queryText, tabId, model, mode);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedModel, selectedMode]);

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

  const handleAuthSuccess = () => {
    if (pendingQuery) {
      processQuery(pendingQuery);
      setPendingQuery(null);
    }
  };

  const handleStreamingQuery = async (queryText: string, tabId?: string, model?: string, mode?: string) => {
    const effectiveModel = model ?? selectedModel;
    const effectiveMode = mode ?? selectedMode;

    setStreaming(true);
    setStreamEnded(false);
    setRightPanelState('reasoning');
    setRightPanelResponse(null);
    setActiveSourceIndex(null);
    setStreamStatus('Connecting...');
    setAgentSteps([]);
    setAgentActive(true);
    setStreamCost(null);
    setCacheInfo(null);
    agentStepCounterRef.current = 0;
    synthesisReasoningStepIdRef.current = null;
    researchJournalStepIdRef.current = null;
    userStoppedRef.current = false;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Header (time-to-first-byte) timeout + mid-stream idle watchdog. The
    // watchdog is re-armed on every received chunk and fires only when the
    // server has gone silent for good.
    let headerTimeoutId: ReturnType<typeof setTimeout> | null = null;
    let idleTimeoutId: ReturnType<typeof setTimeout> | null = null;
    let connectionLost = false;

    const clearIdleWatchdog = () => {
      if (idleTimeoutId !== null) {
        clearTimeout(idleTimeoutId);
        idleTimeoutId = null;
      }
    };
    const armIdleWatchdog = () => {
      clearIdleWatchdog();
      idleTimeoutId = setTimeout(() => {
        connectionLost = true;
        abortController.abort();
      }, STREAM_IDLE_TIMEOUT_MS);
    };

    try {
      const token = Cookies.get('auth_token');
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      headerTimeoutId = setTimeout(() => {
        abortController.abort();
      }, STREAM_HEADER_TIMEOUT_MS);

      const params = new URLSearchParams({
        question: queryText,
        ancient_only: ancientOnly.toString(),
        model: effectiveModel,
        retrieval_mode: effectiveMode,
      });
      if (forceRefresh) {
        params.set('force_refresh', 'true');
        // Reset immediately so the next *natural* query doesn't auto-bypass
        // the cache.
        setForceRefresh(false);
      }

      const response = await fetch(`${apiUrl}/api/graphrag/query/stream?${params.toString()}`, {
        method: 'GET',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        signal: abortController.signal,
      });

      clearTimeout(headerTimeoutId);
      headerTimeoutId = null;
      armIdleWatchdog();

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
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const payload = data.data as any;
                  const msg = (payload?.message || data.message || '').toLowerCase();
                  setStreamStatus(msg);

                  // Also surface status events in the agent activity panel
                  agentStepCounterRef.current += 1;
                  setAgentSteps((prev) => [...prev, {
                    id: `step-${agentStepCounterRef.current}`,
                    type: 'status' as const,
                    summary: payload?.message || data.message || 'Processing...',
                    timestamp: Date.now(),
                  }]);

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
                  let chunk = '';
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const chunkData = data.data as any;
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const eventObj = data as any;
                  if (typeof chunkData === 'string') {
                    chunk = chunkData;
                  } else if (typeof eventObj.content === 'string') {
                    chunk = eventObj.content;
                  } else if (chunkData && typeof chunkData === 'object') {
                    chunk = String(chunkData.data || chunkData.chunk || chunkData.text || '');
                  }
                  const trimmed = chunk.trim();
                  const looksLikeInnerEvent =
                    trimmed.startsWith('{"type"') ||
                    trimmed.startsWith('{ "type"');
                  if (chunk && !looksLikeInnerEvent) {
                    fullAnswer += chunk;
                  }
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
                  setStreamStatus('reasoning over the controversy map…');
                  if (synthesisReasoningStepIdRef.current === null) {
                    agentStepCounterRef.current += 1;
                    const id = `step-${agentStepCounterRef.current}`;
                    synthesisReasoningStepIdRef.current = id;
                    setAgentSteps((prev) => [...prev, {
                      id,
                      type: 'synthesis_reasoning',
                      reasoning: delta,
                      stage,
                      timestamp: Date.now(),
                    }]);
                  } else {
                    const id = synthesisReasoningStepIdRef.current;
                    setAgentSteps((prev) =>
                      prev.map((s) =>
                        s.id === id
                          ? { ...s, reasoning: (s.reasoning ?? '') + delta, stage }
                          : s
                      )
                    );
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

                  agentStepCounterRef.current += 1;
                  setAgentSteps((prev) => [...prev, {
                    id: `step-${agentStepCounterRef.current}`,
                    type: 'research_note',
                    noteKind,
                    summary: noteSummary,
                    detail: noteDetail,
                    stage: noteStage,
                    timestamp: Date.now(),
                  }]);

                  const journalLine = noteDetail
                    ? `— ${noteSummary}\n  ${noteDetail}`
                    : `— ${noteSummary}`;
                  if (researchJournalStepIdRef.current === null) {
                    agentStepCounterRef.current += 1;
                    const journalId = `step-${agentStepCounterRef.current}`;
                    researchJournalStepIdRef.current = journalId;
                    setAgentSteps((prev) => [...prev, {
                      id: journalId,
                      type: 'research_journal',
                      reasoning: journalLine,
                      timestamp: Date.now(),
                    }]);
                  } else {
                    const journalId = researchJournalStepIdRef.current;
                    setAgentSteps((prev) =>
                      prev.map((s) =>
                        s.id === journalId
                          ? { ...s, reasoning: `${s.reasoning ?? ''}\n\n${journalLine}` }
                          : s
                      )
                    );
                  }
                  break;
                }

                case 'tokens_used_rollup': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const p = (data.data ?? data) as any;
                  setStreamCost({
                    total_tokens: Number(p.total_tokens ?? 0),
                    total_cost_usd: Number(p.total_cost_usd ?? 0),
                  });
                  break;
                }

                case 'cost_summary': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const p = (data.data ?? data) as any;
                  setStreamCost({
                    total_tokens: Number(p.total_tokens ?? 0),
                    total_cost_usd: Number(p.total_cost_usd ?? 0),
                  });
                  break;
                }

                case 'cache_hit': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const p = (data.data ?? data) as any;
                  setCacheInfo({
                    cacheKeyShort: String(p.cache_key_short ?? ''),
                    originalTraceId:
                      p.original_trace_id != null && p.original_trace_id !== ''
                        ? String(p.original_trace_id)
                        : null,
                    originalCostUsd: Number(p.original_cost_usd ?? 0),
                    originalTokens: Number(p.original_tokens ?? 0),
                    cachedAt: String(p.cached_at ?? ''),
                    hitCount: Number(p.hit_count ?? 0),
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
                  break;

                case 'complete':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  finalResponse = (data.data as any) as GraphRAGResponse;
                  break;

                case 'agent_thinking': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const thinkPayload = data.data as any;
                  agentStepCounterRef.current += 1;
                  setAgentSteps((prev) => [...prev, {
                    id: `step-${agentStepCounterRef.current}`,
                    type: 'thinking',
                    thinking: thinkPayload?.thinking || '',
                    summary: thinkPayload?.summary || '',
                    remaining: thinkPayload?.remaining,
                    timestamp: Date.now(),
                  }]);
                  break;
                }

                case 'tool_start': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const startPayload = data.data as any;
                  agentStepCounterRef.current += 1;
                  setAgentSteps((prev) => [...prev, {
                    id: `step-${agentStepCounterRef.current}`,
                    type: 'tool_start',
                    tool: startPayload?.tool,
                    args: startPayload?.args,
                    reason: startPayload?.reason,
                    timestamp: Date.now(),
                  }]);
                  break;
                }

                case 'tool_result': {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const resultPayload = data.data as any;
                  agentStepCounterRef.current += 1;
                  setAgentSteps((prev) => [...prev, {
                    id: `step-${agentStepCounterRef.current}`,
                    type: 'tool_result',
                    tool: resultPayload?.tool,
                    summary: resultPayload?.summary,
                    durationMs: resultPayload?.duration_ms,
                    nodeCount: resultPayload?.node_count,
                    passageCount: resultPayload?.passage_count,
                    timestamp: Date.now(),
                  }]);
                  streamedNodeCount += Number(resultPayload?.node_count ?? 0);
                  streamedPassageCount += Number(resultPayload?.passage_count ?? 0);
                  break;
                }

                case 'error':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  streamError = (data as any).data?.message || data.message || 'Stream error';
                  setError(streamError);
                  break;
              }
            } catch (err) {
              console.error('Error parsing SSE line:', line, err);
            }
          }

          // An explicit `error` frame terminates the run — stop reading so the
          // stream teardown (and the finally block below) happens right away.
          if (streamError) break;
        }
      } finally {
        clearIdleWatchdog();
        await reader.cancel().catch(() => {});
        reader.releaseLock();
      }

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

        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: finalResponse.answer?.trim() || fullAnswer || '(No answer generated)',
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
        setMessages((prev) => [
          ...prev.filter(m => m.role !== 'assistant'),
          assistantMessage,
        ]);
        setRightPanelResponse(finalResponse);
        setAllResponses((prev) => [...prev, finalResponse]);
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
              ...messages.filter((m) => m.role !== 'assistant'),
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

        // Update token budget display
        if (finalResponse.metrics) {
          const m = finalResponse.metrics;
          setLastMetrics({
            modelLabel: m.model_label ?? effectiveModel,
            retrievalMode: m.retrieval_mode_used ?? effectiveMode,
            estimatedCost: m.estimated_cost_usd ?? null,
            answerLengthChars: m.answer_length_chars ?? assistantMessage.content.length,
            modelContext: modelContextMap[m.model_key ?? effectiveModel] ?? 1_000_000,
          });
        }

        // Store tab-specific data
        if (tabId) {
          setTabMessages((prev) => ({
            ...prev,
            [tabId]: [...(prev[tabId] ?? []).filter(m => m.role === 'user'), assistantMessage],
          }));
          setTabResponses((prev) => ({ ...prev, [tabId]: finalResponse }));
          if (finalResponse.reasoning_trace) {
            setReasoningTraces((prev) => ({
              ...prev,
              [tabId]: finalResponse.reasoning_trace as ReasoningTraceStep[],
            }));
          }
        }
      } else {
        // The agent loop finished without a `complete` event (synthesis cut
        // mid-stream, CF tunnel idle-timeout, etc.). Render a clean error
        // bubble instead of dumping raw chunks, and keep the reasoning
        // timeline visible so the user can see how far the agent got.
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
        setMessages((prev) => [...prev, degradedMessage]);

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
        setRightPanelResponse(degradedResponse);
        if (tabId) {
          setTabResponses((prev) => ({ ...prev, [tabId]: degradedResponse }));
        }
        // Stay on the reasoning timeline so the user retains context.
      }
    } catch (err: unknown) {
      console.error('Streaming error:', err);
      if (userStoppedRef.current) {
        // Deliberate stop — not an error worth surfacing.
      } else if (connectionLost) {
        setError(t('graphRagUi.stream.connectionLost'));
      } else if (err instanceof Error && err.name === 'AbortError') {
        setError(t('errors.networkErrorDesc'));
      } else {
        setError(err instanceof Error ? err.message : 'Streaming failed');
      }
      if (!connectionLost) {
        setRightPanelState('idle');
      }
    } finally {
      // Single teardown for every exit path — normal completion, degraded
      // stream, SSE `error` frame, idle watchdog abort, user stop, throw.
      if (headerTimeoutId !== null) clearTimeout(headerTimeoutId);
      clearIdleWatchdog();
      setStreaming(false);
      setAgentActive(false);
      setStreamStatus('');
      setStreamEnded(true);
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    }
  };

  const stopStreaming = () => {
    userStoppedRef.current = true;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
    setAgentActive(false);
    setStreamStatus('');
    setStreamEnded(true);
  };

  const handleNodeClick = async (nodeId: string) => {
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) return;
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidPattern.test(nodeId) || nodeId.startsWith('passage_')) return;
    try {
      const node = await apiClient.getNode(nodeId);
      if (node) setSelectedNode(node);
    } catch (err) {
      console.error('Failed to fetch node:', err);
    }
  };

  // Tab switching: restore messages + right panel for the selected tab
  const handleTabChange = useCallback((tabId: string) => {
    setActiveTabId(tabId);
    const savedMessages = tabMessages[tabId];
    if (savedMessages) {
      setMessages(savedMessages);
    }
    const savedResponse = tabResponses[tabId] ?? null;
    setRightPanelResponse(savedResponse);
    setRightPanelState(savedResponse ? 'graph' : 'idle');
    setActiveSourceIndex(null);
  }, [tabMessages, tabResponses]);

  // Retry with a different model: prompt user via simple inline select
  const availableModels = Object.keys(modelContextMap).length > 0
    ? Object.keys(modelContextMap)
    : ['kimi-k2.6', 'gemini-3.1-pro-preview', 'kimi-k2.5-thinking'];

  const handleRetry = useCallback(() => {
    if (!initialQuestion) return;
    setShowRetryDropdown((p) => !p);
  }, [initialQuestion]);

  const handleRetryWithModel = useCallback((model: string) => {
    setShowRetryDropdown(false);
    processQuery(initialQuestion, model, selectedMode);
  }, [initialQuestion, selectedMode, processQuery]);

  // Force a fresh (non-cached) run of the last user question. Re-uses the
  // same processQuery code path as a normal submission; ``setForceRefresh``
  // primes the next handleStreamingQuery call to append force_refresh=true.
  const handleRegenerate = useCallback(() => {
    if (!initialQuestion || streaming) return;
    setForceRefresh(true);
    processQuery(initialQuestion);
  }, [initialQuestion, streaming, processQuery]);

  const advancedProps = {
    ancientOnly, setAncientOnly,
  };

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="relative w-full min-h-screen overflow-hidden">
        <div className="relative z-10 min-h-screen">

          {/* WELCOME STATE */}
          {messages.length === 0 && !streaming && (
            <WelcomeHero
              query={query}
              setQuery={setQuery}
              loading={loading}
              streaming={streaming}
              error={error}
              inputRef={inputRef}
              onSubmit={handleSubmit}
              onDemo={loadDemoMode}
              advancedProps={advancedProps}
            />
          )}

          {/* TWO-COLUMN LAYOUT */}
          {(messages.length > 0 || streaming) && (
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
                messages={messages}
                query={query}
                setQuery={setQuery}
                loading={loading}
                streaming={streaming}
                error={error}
                setError={setError}
                inputRef={inputRef}
                onSubmit={handleSubmit}
                onStop={stopStreaming}
                onNodeClick={handleNodeClick}
                onCitationClick={handleCitationClick}
                onPassageCitationClick={handlePassageCitationClick}
                onNodeCitationClick={handleNodeCitationClick}
                responseTabs={responseTabs}
                activeTabId={activeTabId}
                onTabChange={handleTabChange}
                onRetry={handleRetry}
                lastMetrics={lastMetrics}
                cacheInfo={cacheInfo}
                onRegenerate={handleRegenerate}
              />

              {/* RIGHT PANEL - desktop graph workspace */}
              <div className="hidden lg:flex flex-col w-[40%] h-full bg-parchment-50 border-l border-amber-200/40">
                <div className="flex-1 min-h-0 overflow-hidden p-3 xl:p-4 flex flex-col">
                  {/* Main graph panel */}
                  <div className={`${showReasoningTrace && (reasoningTraces[activeTabId]?.length ?? 0) > 0 ? 'h-[60%]' : 'flex-1'} min-h-0`}>
                    <RightPanel
                      state={rightPanelState}
                      response={rightPanelResponse}
                      allResponses={allResponses}
                      activeSourceIndex={activeSourceIndex}
                      passageContext={passageContext}
                      agentSteps={agentSteps}
                      agentActive={agentActive}
                      isStreaming={streaming}
                      streamEnded={streamEnded}
                      cost={streamCost}
                      onNodeClick={handleNodeClick}
                      onSourceSelect={handleSourceSelect}
                      onCloseDetail={() => { setRightPanelState('graph'); setPassageContext(null); setPassageWindow(5); }}
                      onLoadMorePassages={handleLoadMorePassages}
                      onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
                      onOpenGraphView={() => setRightPanelState('graph')}
                      className="h-full"
                    />
                  </div>

                  {/* Reasoning Trace toggle + panel */}
                  {(reasoningTraces[activeTabId]?.length ?? 0) > 0 && (
                    <div className="shrink-0 mt-2">
                      <button
                        onClick={() => setShowReasoningTrace(!showReasoningTrace)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-500 hover:text-stone-700 transition-colors w-full border-t border-amber-200/40 pt-2"
                      >
                        <span className="inline-block w-2 h-2 rounded-full bg-amber-400" />
                        {showReasoningTrace ? 'Hide' : 'Show'} FSM Reasoning Trace ({reasoningTraces[activeTabId]?.length ?? 0} steps)
                      </button>
                    </div>
                  )}
                  {showReasoningTrace && (reasoningTraces[activeTabId]?.length ?? 0) > 0 && (
                    <div className="h-[38%] min-h-[180px] overflow-y-auto border-t border-amber-200/40 mt-1 rounded-lg bg-white/60">
                      <ReasoningPanel steps={reasoningTraces[activeTabId] ?? []} />
                    </div>
                  )}
                </div>
              </div>

              {/* MOBILE floating sheet */}
              <MobileGraphSheet
                rightPanelState={rightPanelState}
                response={rightPanelResponse}
                allResponses={allResponses}
                activeSourceIndex={activeSourceIndex}
                passageContext={passageContext}
                agentSteps={agentSteps}
                agentActive={agentActive}
                isStreaming={streaming}
                streamEnded={streamEnded}
                cost={streamCost}
                onNodeClick={handleNodeClick}
                onSourceSelect={handleSourceSelect}
                onCloseDetail={() => { setRightPanelState('graph'); setPassageContext(null); setPassageWindow(5); }}
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
                      Retry with model
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
