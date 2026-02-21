import { useState, useRef, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import AuthModal from '../../components/AuthModal';
import { AuroraBackground } from '../../components/ui/aurora-background';
import NodeDetailPanel from '../../components/NodeDetailPanel';
import RightPanel from '../../components/graphrag/RightPanel';
import type { RightPanelState } from '../../components/graphrag/RightPanel';
import WelcomeHero from './WelcomeHero';
import ChatPanel from './ChatPanel';
import MobileGraphSheet from './MobileGraphSheet';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../../types';
import type { ReasoningStep, PassageContext } from '../../types/graphrag';
import {
  mockGraphRAGResponse,
  mockReasoningSteps,
} from '../../data/mockGraphRAGData';

export default function GraphRAGPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const [messages, setMessages] = useState<GraphRAGChatMessage[]>([]);
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

  // Advanced settings
  const [semanticK, setSemanticK] = useState(10);
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxContext, setMaxContext] = useState(15);
  const [academicMode, setAcademicMode] = useState(true);
  const [useThinking, setUseThinking] = useState(false);
  const [ancientOnly, setAncientOnly] = useState(false);
  const [agenticMode, setAgenticMode] = useState(false);
  const [_reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [_currentQuery, setCurrentQuery] = useState<string>('');

  // Right panel
  const [rightPanelState, setRightPanelState] = useState<RightPanelState>('idle');
  const [activeSourceIndex, setActiveSourceIndex] = useState<number | null>(null);
  const [rightPanelResponse, setRightPanelResponse] = useState<GraphRAGResponse | null>(null);
  const [allResponses, setAllResponses] = useState<GraphRAGResponse[]>([]);
  const highlightNodeRef = useRef<((citationIndex: number) => void) | null>(null);
  const [passageContext, setPassageContext] = useState<PassageContext | null>(null);
  const [passageWindow, setPassageWindow] = useState(5);

  const fetchPassageContext = useCallback(async (passageId: string, window: number = 5) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const resp = await fetch(`${apiUrl}/api/texts/passage/${passageId}/context?window=${window}`);
      if (!resp.ok) return null;
      return await resp.json() as PassageContext;
    } catch (err) {
      console.error('Failed to fetch passage context:', err);
      return null;
    }
  }, []);

  const handlePassageCitationClick = useCallback(async (passageOrNodeId: string) => {
    setRightPanelState('loading');
    const ctx = await fetchPassageContext(passageOrNodeId, passageWindow);
    if (ctx) {
      setPassageContext(ctx);
      setRightPanelState('passage-reader');
    } else {
      // No linked passage found — fall back to source detail or graph
      setRightPanelState(rightPanelResponse ? 'source-detail' : 'graph');
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

  const handleCitationClick = (citationIndex: number) => {
    // Always try the passage reader first — the backend resolves both
    // passage UUIDs and KG node IDs to actual ancient text passages.
    const sources = rightPanelResponse?.sources ?? [];
    const source = sources[citationIndex];
    if (source?.nodeId) {
      // Try passage reader for any citation — backend handles KG→passage resolution
      handlePassageCitationClick(source.nodeId);
      return;
    }
    setActiveSourceIndex(citationIndex);
    setRightPanelState('source-detail');
    highlightNodeRef.current?.(citationIndex);
  };

  const onPrevSource = () => {
    setActiveSourceIndex(prev => (prev !== null && prev > 0 ? prev - 1 : prev));
  };

  const onNextSource = () => {
    const sources = rightPanelResponse?.sources ?? [];
    setActiveSourceIndex(prev => (prev !== null && prev < sources.length - 1 ? prev + 1 : prev));
  };

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
    setReasoningSteps(mockReasoningSteps);
    setCurrentQuery(mockGraphRAGResponse.query);
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

  const processQuery = useCallback(async (queryText: string) => {
    const userMessage: GraphRAGChatMessage = {
      role: 'user',
      content: queryText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setError(null);

    if (agenticMode) {
      await handleAgenticQuery(queryText);
    } else {
      await handleStreamingQuery(queryText);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useThinking, agenticMode]);

  useEffect(() => {
    const state = location.state as { initialQuery?: string } | null;
    if (state?.initialQuery) {
      if (isAuthenticated) {
        processQuery(state.initialQuery);
        window.history.replaceState({}, document.title);
      } else {
        setPendingQuery(state.initialQuery);
        setShowAuthModal(true);
        window.history.replaceState({}, document.title);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, isAuthenticated]);

  const handleAuthSuccess = () => {
    if (pendingQuery) {
      processQuery(pendingQuery);
      setPendingQuery(null);
    }
  };

  const initializeReasoningSteps = (q: string) => {
    const steps: ReasoningStep[] = [
      { id: 1, type: 'search', label: 'Semantic Search', description: 'Embedding query and searching vector database', status: 'pending' },
      { id: 2, type: 'traverse', label: 'Graph Traversal', description: 'Expanding knowledge graph connections', status: 'pending' },
      { id: 3, type: 'context', label: 'Context Building', description: 'Assembling citations and context', status: 'pending' },
      { id: 4, type: 'synthesis', label: 'LLM Synthesis', description: 'Generating scholarly answer', status: 'pending' },
      { id: 5, type: 'complete', label: 'Complete', description: 'Answer ready with citations', status: 'pending' },
    ];
    setReasoningSteps(steps);
    setCurrentQuery(q);
  };

  const updateReasoningStep = (stepId: number, status: 'pending' | 'active' | 'complete' | 'error', nodes?: string[], duration?: number) => {
    setReasoningSteps((prev) =>
      prev.map((step) =>
        step.id === stepId
          ? { ...step, status, nodes, duration }
          : step.id < stepId && step.status !== 'complete'
          ? { ...step, status: 'complete' }
          : step
      )
    );
  };

  const handleAgenticQuery = async (queryText: string) => {
    const agenticUrl = import.meta.env.VITE_AGENTIC_API_URL || 'http://localhost:8000';
    await handleStreamingQuery(queryText, agenticUrl, 'question');
  };

  const handleStreamingQuery = async (queryText: string, apiUrlOverride?: string, queryParamName: string = 'query') => {
    setStreaming(true);
    setRightPanelState('loading');
    setRightPanelResponse(null);
    setActiveSourceIndex(null);
    setStreamStatus('Connecting...');
    initializeReasoningSteps(queryText);

    try {
      const token = Cookies.get('auth_token');
      const apiUrl = apiUrlOverride ?? (import.meta.env.VITE_API_URL || 'http://localhost:8000');

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      const timeoutId = setTimeout(() => {
        abortController.abort();
      }, 120000);

      const params = new URLSearchParams({
        [queryParamName]: queryText,
        semantic_k: semanticK.toString(),
        graph_depth: graphDepth.toString(),
        max_context: maxContext.toString(),
        ancient_only: ancientOnly.toString(),
        use_thinking: useThinking.toString(),
      });

      const response = await fetch(`${apiUrl}/api/graphrag/query/stream?${params.toString()}`, {
        method: 'GET',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        signal: abortController.signal,
      });

      clearTimeout(timeoutId);

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

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
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

                  if (msg.includes('embedding') || msg.includes('searching') || msg.includes('initializ')) {
                    updateReasoningStep(1, 'active');
                  } else if (msg.includes('retrieving') || msg.includes('found') || msg.includes('knowledge graph')) {
                    updateReasoningStep(1, 'complete');
                    updateReasoningStep(2, 'active');
                  } else if (msg.includes('expand') || msg.includes('travers') || msg.includes('node')) {
                    updateReasoningStep(2, 'active');
                  } else if (msg.includes('context') || msg.includes('citation') || msg.includes('building')) {
                    updateReasoningStep(2, 'complete');
                    updateReasoningStep(3, 'active');
                  } else if (msg.includes('generat') || msg.includes('synthesis') || msg.includes('answer')) {
                    updateReasoningStep(3, 'complete');
                    updateReasoningStep(4, 'active');
                  }
                  break;
                }

                case 'answer_chunk': {
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
                  fullAnswer += chunk;
                  if (!fullAnswer) updateReasoningStep(4, 'active');
                  break;
                }

                case 'complete':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  finalResponse = (data.data as any) as GraphRAGResponse;
                  updateReasoningStep(5, 'complete');
                  break;

                case 'error':
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  setError((data as any).data?.message || data.message || 'Stream error');
                  break;
              }
            } catch (err) {
              console.error('Error parsing SSE line:', line, err);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      if (finalResponse) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const serverResp = finalResponse as any;
        const citations = finalResponse.citations || {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ancient_sources: (serverResp.ancientCitations || []).map((c: any) => typeof c === 'string' ? c : (c?.citationText || '')).filter(Boolean),
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          modern_scholarship: (serverResp.modernBibliography || []).map((c: any) => typeof c === 'string' ? c : (c?.citation || c?.citationText || '')).filter(Boolean),
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

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const serverAncientCitations: any[] = (finalResponse as any).ancientCitations || [];
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
          content: finalResponse.answer,
          citations,
          reasoning_path: finalResponse.reasoning_path,
          tokens_used: finalResponse.tokens_used,
          llm_provider: finalResponse.llm_provider || 'gemini',
          llm_model: finalResponse.llm_model || 'gemini-3.1-pro-preview',
          timestamp: new Date(),
          citationTexts: formattedCitationTexts,
          graphrag_response: finalResponse,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setRightPanelResponse(finalResponse);
        setAllResponses((prev) => [...prev, finalResponse]);
        setRightPanelState('graph');
      } else if (fullAnswer) {
        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: fullAnswer,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setRightPanelState('idle');
      }

      setStreaming(false);
      setStreamStatus('');
    } catch (err: unknown) {
      console.error('Streaming error:', err);
      if (err instanceof Error && err.name === 'AbortError') {
        setError(t('errors.networkErrorDesc'));
      } else {
        setError(err instanceof Error ? err.message : 'Streaming failed');
      }
      setStreaming(false);
      setStreamStatus('');
    }
  };

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
    setStreamStatus('');
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

  const advancedProps = {
    academicMode, setAcademicMode,
    useThinking, setUseThinking,
    ancientOnly, setAncientOnly,
    agenticMode, setAgenticMode,
    semanticK, setSemanticK,
    graphDepth, setGraphDepth,
    maxContext, setMaxContext,
  };

  return (
    <AuroraBackground className="!min-h-screen !h-auto">
      <div className="relative min-h-screen overflow-hidden">
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
              className="flex bg-white"
              style={{
                position: 'fixed',
                top: navHeight,
                left: 0,
                right: 0,
                bottom: 0,
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
                agenticMode={agenticMode}
                inputRef={inputRef}
                onSubmit={handleSubmit}
                onStop={stopStreaming}
                onNodeClick={handleNodeClick}
                onCitationClick={handleCitationClick}
                onPassageCitationClick={handlePassageCitationClick}
              />

              {/* RIGHT PANEL - 35% (desktop only) */}
              <div className="hidden lg:flex flex-col w-[35%] h-full bg-[#020617]">
                <div className="shrink-0 px-4 py-3 border-b border-white/10">
                  <h2 className="text-sm font-semibold text-white/40 uppercase tracking-wider">Knowledge Graph</h2>
                </div>
                <div className="flex-1 overflow-hidden">
                  <RightPanel
                    state={rightPanelState}
                    response={rightPanelResponse}
                    allResponses={allResponses}
                    activeSourceIndex={activeSourceIndex}
                    passageContext={passageContext}
                    onNodeClick={handleNodeClick}
                    onCloseDetail={() => { setRightPanelState('graph'); setPassageContext(null); setPassageWindow(5); }}
                    onPrevSource={onPrevSource}
                    onNextSource={onNextSource}
                    onLoadMorePassages={handleLoadMorePassages}
                    onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
                    className="h-full"
                  />
                </div>
              </div>

              {/* MOBILE floating sheet */}
              <MobileGraphSheet
                rightPanelState={rightPanelState}
                response={rightPanelResponse}
                allResponses={allResponses}
                activeSourceIndex={activeSourceIndex}
                onNodeClick={handleNodeClick}
                onCloseDetail={() => setRightPanelState('graph')}
                onPrevSource={onPrevSource}
                onNextSource={onNextSource}
                onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
              />
            </div>
          )}

        </div>

        <AuthModal
          isOpen={showAuthModal}
          onClose={() => { setShowAuthModal(false); setPendingQuery(null); }}
          onSuccess={handleAuthSuccess}
          title="Authentication Required"
          message="Please log in to use HiRAG Q&A"
        />

        {selectedNode && (
          <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
        )}
      </div>
    </AuroraBackground>
  );
}
