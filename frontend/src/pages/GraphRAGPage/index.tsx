import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import AuthModal from '../../components/AuthModal';
import { ShineBorder } from '../../components/ui/shine-border';
import { AuroraBackground } from '../../components/ui/aurora-background';
import { Typewriter } from '../../components/ui/typewriter';
import NodeDetailPanel from '../../components/NodeDetailPanel';
import { CitationPreview } from '../../components/ui/citation-preview';
import { CitationRenderer, SourcesPanel } from '../../components/CitationRenderer';
import BibliographyPanel from '../../components/BibliographyPanel';
import EvidenceChainPanel from '../../components/EvidenceChainPanel';
import { TerminalLoader } from '../../components/ui/terminal-loader';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../../types';
import type { ReasoningStep } from '../../types/graphrag';
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
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [_streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { isAuthenticated } = useAuth();

  // Advanced settings
  const [semanticK, setSemanticK] = useState(10);
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxContext, setMaxContext] = useState(15);

  // Academic mode settings
  const [academicMode, setAcademicMode] = useState(true);
  const [useThinking, setUseThinking] = useState(false);
  const [_citationStyle, _setCitationStyle] = useState<'chicago' | 'apa' | 'harvard'>('chicago');
  const [ancientOnly, setAncientOnly] = useState(false);
  const [agenticMode, setAgenticMode] = useState(false);
  const [_reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [_currentQuery, setCurrentQuery] = useState<string>('');

  // Dynamic KG stats
  const [kgStats, setKgStats] = useState({
    nodes: 0,
    edges: 0,
    sources: 0,
    hierarchyLayers: 3
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const kgStatsResponse = await apiClient.getKGStats();
        const worksStatsResponse = await apiClient.getWorksStats();
        setKgStats({
          nodes: kgStatsResponse.totalNodes || 0,
          edges: kgStatsResponse.totalEdges || 0,
          sources: worksStatsResponse.total_passages || 0,
          hierarchyLayers: 3
        });
      } catch (err) {
        console.error('Failed to fetch KG stats:', err);
      }
    };
    fetchStats();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamedAnswer]);

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

    // Always use streaming — /api/graphrag/answer and workflow endpoints are non-functional
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

  // handleStandardQuery removed — /api/graphrag/answer and workflow endpoints are non-functional.
  // All queries now go through handleStreamingQuery (/api/graphrag/query/stream).

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
    setStreamedAnswer('');
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
                  // Backend sends message nested: data.data.message
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
                  setStreamedAnswer(fullAnswer);
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
        // Build citations for display: server sends ancientCitations/modernBibliography, not citations.ancient_sources
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const serverResp = finalResponse as any;
        const citations = finalResponse.citations || {
          ancient_sources: (serverResp.ancientCitations || []).map((c: any) => typeof c === 'string' ? c : (c?.citationText || '')).filter(Boolean),
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

        // Server sends ancientCitations: AncientCitation[] (objects with .citationText)
        // Extract string references for the citation lookup API
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
          llm_model: finalResponse.llm_model || 'gemini-2.0-flash-exp',
          timestamp: new Date(),
          citationTexts: formattedCitationTexts,
          graphrag_response: finalResponse,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else if (fullAnswer) {
        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: fullAnswer,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }

      setStreaming(false);
      setStreamedAnswer('');
      setStreamStatus('');
    } catch (err: unknown) {
      console.error('Streaming error:', err);
      if (err instanceof Error && err.name === 'AbortError') {
        setError(t('errors.networkErrorDesc'));
      } else {
        setError(err instanceof Error ? err.message : 'Streaming failed');
      }
      setStreaming(false);
      setStreamedAnswer('');
      setStreamStatus('');
    }
  };

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
    setStreamedAnswer('');
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

  return (
    <AuroraBackground className="!min-h-screen !h-auto">
      <div className="relative min-h-screen overflow-hidden">

        <div className="relative z-10 min-h-screen">

          {/* Welcome / empty state — centered */}
          {messages.length === 0 && !streaming && (
            <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 py-12">
              <div className="w-full max-w-4xl">

                {/* Header */}
                <motion.div
                  className="text-center mb-12"
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                >
                  <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 mb-4 drop-shadow-sm">
                    <Typewriter
                      text={["HiRAG", "Knowledge Graph", "Ancient Philosophy", "Scholarly Q&A"]}
                      speed={100}
                      waitTime={3500}
                      deleteSpeed={60}
                      className="text-gray-900"
                      cursorChar="_"
                    />
                  </h1>
                  <p className="text-lg text-gray-700 max-w-2xl mx-auto">
                    {t('graphrag.description')}
                  </p>

                  {/* Stats pills */}
                  <div className="flex flex-wrap justify-center gap-3 mt-6">
                    <span className="px-4 py-2 bg-white/90 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 shadow-sm border border-gray-200">
                      {kgStats.nodes.toLocaleString()} Nodes
                    </span>
                    <span className="px-4 py-2 bg-white/90 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 shadow-sm border border-gray-200">
                      {kgStats.edges.toLocaleString()} Edges
                    </span>
                    <span className="px-4 py-2 bg-white/90 backdrop-blur-sm rounded-full text-sm font-medium text-gray-700 shadow-sm border border-gray-200">
                      {kgStats.sources.toLocaleString()} Sources
                    </span>
                    <span className="px-4 py-2 bg-blue-50 backdrop-blur-sm rounded-full text-sm font-medium text-blue-700 shadow-sm border border-blue-200">
                      {kgStats.hierarchyLayers} Hierarchy Layers
                    </span>
                  </div>
                </motion.div>

                {/* Input */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  className="space-y-4"
                >
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <ShineBorder
                      className="!p-0 bg-white/95 backdrop-blur-sm"
                      borderRadius={9999}
                      color={["#3B82F6", "#6366F1", "#06B6D4"]}
                    >
                      <div className="flex gap-3 p-2">
                        <input
                          ref={inputRef}
                          type="text"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder={t('graphrag.placeholder')}
                          className="flex-1 px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                          autoFocus
                          disabled={loading || streaming}
                        />
                        <button
                          type="submit"
                          disabled={!query.trim() || loading || streaming}
                          className="px-8 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base font-medium whitespace-nowrap"
                        >
                          {loading ? 'Thinking...' : t('graphrag.ask')}
                        </button>
                      </div>
                    </ShineBorder>

                    {/* Mode toggles */}
                    <div className="space-y-3 px-2">
                      <div className="flex justify-center">
                        <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-sm bg-white/60 backdrop-blur-md px-4 sm:px-6 py-3 rounded-2xl sm:rounded-full border border-gray-200">
                          <span className="text-gray-700 font-medium w-full sm:w-auto text-center">Modes:</span>
                          <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2">
                            <input
                              type="checkbox"
                              checked={academicMode}
                              onChange={(e) => setAcademicMode(e.target.checked)}
                              className="w-5 h-5 sm:w-4 sm:h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span className="text-gray-700">🎓 Academic</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2">
                            <input
                              type="checkbox"
                              checked={useThinking}
                              onChange={(e) => setUseThinking(e.target.checked)}
                              className="w-5 h-5 sm:w-4 sm:h-4 text-purple-600 bg-white border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                            />
                            <span className="text-gray-700 text-xs sm:text-sm">🧠 Deep Reasoning</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2" title="Only use ancient sources (6th c. BCE – 6th c. CE)">
                            <input
                              type="checkbox"
                              checked={ancientOnly}
                              onChange={(e) => setAncientOnly(e.target.checked)}
                              className="w-5 h-5 sm:w-4 sm:h-4 text-amber-600 bg-white border-gray-300 rounded focus:ring-2 focus:ring-amber-500"
                            />
                            <span className="text-gray-700 text-xs sm:text-sm">🏛️ Ancient Only</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2" title="Full pydantic-AI pipeline on Render (experimental, 30s cold start)">
                            <input
                              type="checkbox"
                              checked={agenticMode}
                              onChange={(e) => setAgenticMode(e.target.checked)}
                              className="w-5 h-5 sm:w-4 sm:h-4 text-orange-600 bg-white border-gray-300 rounded focus:ring-2 focus:ring-orange-500"
                            />
                            <span className="text-gray-700 text-xs sm:text-sm">⚡ Agentic</span>
                          </label>
                        </div>
                      </div>

                      {academicMode && (
                        <div className="flex justify-center">
                          <div className="text-xs text-amber-700 bg-amber-50/80 backdrop-blur-md px-4 py-2 rounded-full border border-amber-200 max-w-md text-center">
                            <span className="font-medium">🌟 Academic Mode:</span> Like the Stoics debating εἱμαρμένη, some things take time.
                            <span className="text-amber-600 ml-1">Expect 2–5 minutes for thorough analysis.</span>
                          </div>
                        </div>
                      )}

                      {agenticMode && (
                        <div className="flex justify-center">
                          <div className="text-xs text-orange-700 bg-orange-50/80 backdrop-blur-md px-4 py-2 rounded-full border border-orange-200 max-w-lg text-center">
                            <span className="font-medium">⚡ Agentic Mode (Experimental):</span> Uses the full pydantic-AI pipeline (HyDE · CRAG · Self-RAG · tree reasoning).
                            <span className="text-orange-600 ml-1">First query may take up to 30s while the backend warms up.</span>
                          </div>
                        </div>
                      )}

                      {/* Parameters */}
                      <div className="flex justify-center items-center gap-2 sm:gap-4 flex-wrap">
                        <div className="flex items-center gap-2 text-xs sm:text-sm bg-white/60 backdrop-blur-md px-3 sm:px-6 py-2 rounded-full border border-gray-200">
                          <span className="text-gray-700">Breadth:</span>
                          <select value={semanticK} onChange={(e) => setSemanticK(Number(e.target.value))} className="px-2 sm:px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black min-h-[44px] sm:min-h-0">
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                            <option value={20}>20</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2 text-xs sm:text-sm bg-white/60 backdrop-blur-md px-3 sm:px-6 py-2 rounded-full border border-gray-200">
                          <span className="text-gray-700">Depth:</span>
                          <select value={graphDepth} onChange={(e) => setGraphDepth(Number(e.target.value))} className="px-2 sm:px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black min-h-[44px] sm:min-h-0">
                            <option value={1}>1</option>
                            <option value={2}>2</option>
                            <option value={3}>3</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2 text-xs sm:text-sm bg-white/60 backdrop-blur-md px-3 sm:px-6 py-2 rounded-full border border-gray-200">
                          <span className="text-gray-700">Context:</span>
                          <select value={maxContext} onChange={(e) => setMaxContext(Number(e.target.value))} className="px-2 sm:px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black min-h-[44px] sm:min-h-0">
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                            <option value={20}>20</option>
                            <option value={25}>25</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex justify-center">
                        <button
                          type="button"
                          onClick={loadDemoMode}
                          className="px-4 py-1.5 text-sm text-gray-500 hover:text-gray-900 hover:bg-white/80 rounded-full transition-colors"
                        >
                          Try Demo
                        </button>
                      </div>
                    </div>
                  </form>

                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-6 px-6 py-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl text-sm text-center"
                    >
                      {error}
                    </motion.div>
                  )}
                </motion.div>
              </div>
            </div>
          )}

          {/* Messages view */}
          {(messages.length > 0 || streaming) && (
            <div className="max-w-5xl mx-auto px-4 pt-4 pb-8">

              {/* Compact header */}
              <div className="flex items-center justify-center mb-6">
                <h1 className="text-2xl font-semibold text-gray-800 tracking-tight">
                  <Typewriter
                    text={["HiRAG Q&A", "Knowledge Graph", "Ancient Philosophy"]}
                    speed={100}
                    waitTime={3000}
                    deleteSpeed={60}
                    className="text-gray-800"
                    cursorChar="_"
                    showCursor={false}
                  />
                </h1>
              </div>

              <div className="space-y-6 mb-6">
                <AnimatePresence>
                  {messages.map((message, index) => (
                    <MessageBubble key={index} message={message} onNodeClick={handleNodeClick} />
                  ))}
                </AnimatePresence>

                {streaming && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4 flex flex-col items-center">
                    <div className={`flex justify-center items-center w-full ${streamedAnswer ? 'py-4' : 'min-h-[50vh]'}`}>
                      <TerminalLoader size="large" title={agenticMode ? "Pydantic-AI Engine" : undefined} />
                    </div>

                    {streamedAnswer && (
                      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-sm w-full">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown>{streamedAnswer}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}

                {error && !loading && !streaming && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="px-6 py-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl text-sm text-center">
                    <div className="font-medium mb-1">Query failed</div>
                    {error}
                    <button onClick={() => setError(null)} className="mt-2 text-red-600 hover:text-red-800 underline text-xs block mx-auto">Dismiss</button>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Sticky bottom input */}
              <ShineBorder
                className="!p-0 bg-white/95 backdrop-blur-sm shadow-lg sticky bottom-4"
                borderRadius={9999}
                color={["#3B82F6", "#6366F1", "#06B6D4"]}
              >
                <form onSubmit={handleSubmit} className="p-2">
                  <div className="flex gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder={t('graphrag.placeholder')}
                      disabled={loading || streaming}
                      className="flex-1 px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                    />
                    {streaming ? (
                      <button type="button" onClick={stopStreaming} className="px-6 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all">
                        Stop
                      </button>
                    ) : (
                      <button type="submit" disabled={loading || !query.trim()} className="px-6 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium">
                        {loading ? 'Thinking...' : 'Ask'}
                      </button>
                    )}
                  </div>
                </form>
              </ShineBorder>
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


// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({
  message,
  onNodeClick
}: {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
}) {
  const [showCitations, setShowCitations] = useState(false);
  const [showReasoningPath, setShowReasoningPath] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className={`${message.role === 'user' ? 'ml-auto max-w-2xl' : 'max-w-full'}`}
    >
      <div className={`rounded-2xl shadow-sm ${message.role === 'user' ? 'bg-gradient-to-br from-gray-900 to-gray-800' : 'bg-white/95 backdrop-blur-sm'}`}>
        <div className={`p-6 ${message.role === 'user' ? 'text-white' : 'text-gray-900'}`}>
          {message.role === 'user' ? (
            <p className="text-base leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-4">

              {/* Service badge */}
              {message.graphrag_response?.service && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  {message.graphrag_response.service}
                </span>
              )}

              {/* Content */}
              {message.graphrag_response?.sources ? (
                <div className="prose prose-sm max-w-none">
                  <CitationRenderer content={message.content} sources={message.graphrag_response.sources} onNodeClick={onNodeClick} />
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              {/* Sources */}
              {message.graphrag_response?.sources && message.graphrag_response.sources.length > 0 && (
                <SourcesPanel sources={message.graphrag_response.sources} evidenceMap={message.graphrag_response.evidenceMap} onNodeClick={onNodeClick} />
              )}

              {/* Reasoning path */}
              {message.reasoning_path && (
                <div className="border-t border-gray-200 pt-4">
                  <button onClick={() => setShowReasoningPath(!showReasoningPath)} className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center gap-2">
                    {showReasoningPath ? '▼' : '▶'} Knowledge Graph Path ({message.reasoning_path.total_nodes || 0} nodes)
                  </button>
                  {showReasoningPath && message.reasoning_path.starting_nodes?.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {message.reasoning_path.starting_nodes.map((node, i) => (
                        <button key={i} onClick={() => onNodeClick(node.id)} className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors">
                          <div className="flex items-start gap-2">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-200 text-blue-800">{node.type}</span>
                            <div className="flex-1">
                              <div className="font-semibold text-blue-900 text-sm">{node.label}</div>
                              <div className="text-xs text-blue-700 mt-0.5">{node.reason}</div>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Citations */}
              {message.citations && (message.citations.ancient_sources?.length > 0 || message.citations.modern_scholarship?.length > 0) && (
                <div className="border-t border-gray-200 pt-4">
                  <button onClick={() => setShowCitations(!showCitations)} className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center gap-2">
                    {showCitations ? '▼' : '▶'} Citations ({(message.citations.ancient_sources?.length || 0) + (message.citations.modern_scholarship?.length || 0)})
                  </button>
                  {showCitations && (
                    <div className="mt-4 space-y-3 text-sm">
                      {message.citations.ancient_sources && message.citations.ancient_sources.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2 text-gray-900">Ancient Sources:</h4>
                          <ul className="list-disc list-inside space-y-1 text-gray-700">
                            {message.citations.ancient_sources.map((source, i) => (
                              <li key={i}>
                                <CitationPreview citation={source} type="ancient" sourceText={message.citationTexts?.[source]}>
                                  {source}
                                </CitationPreview>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {message.citations.modern_scholarship && message.citations.modern_scholarship.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2 text-gray-900">Modern Scholarship:</h4>
                          <ul className="list-disc list-inside space-y-1 text-gray-700">
                            {message.citations.modern_scholarship.map((source, i) => (
                              <li key={i}>{source}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Academic panels */}
              {message.graphrag_response && (
                <>
                  {message.graphrag_response.evidence_chains && (
                    <EvidenceChainPanel evidenceChains={message.graphrag_response.evidence_chains} />
                  )}
                  {message.graphrag_response.modern_bibliography && (
                    <BibliographyPanel
                      bibliography={message.graphrag_response.modern_bibliography}
                      chicagoBibliography={message.graphrag_response.chicago_bibliography}
                      apaBibliography={message.graphrag_response.apa_bibliography}
                      harvardBibliography={message.graphrag_response.harvard_bibliography}
                      bibtexBibliography={message.graphrag_response.bibtex_bibliography}
                      ctsUrns={message.graphrag_response.cts_urns ?? []}
                    />
                  )}
                </>
              )}
            </div>
          )}

          <div className={`text-xs mt-3 ${message.role === 'user' ? 'text-white/70' : 'text-gray-500'}`}>
            {typeof message.timestamp === 'string'
              ? new Date(message.timestamp).toLocaleTimeString()
              : message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
