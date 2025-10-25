import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import AuthModal from '../components/AuthModal';
import { ShineBorder } from '../components/ui/shine-border';
import NodeDetailPanel from '../components/NodeDetailPanel';
import { CitationPreview } from '../components/ui/citation-preview';
import { ColdStartLoaderMinimal } from '../components/ColdStartLoader';
import { ReasoningPathVisualizer } from '../components/graphrag/ReasoningPathVisualizer';
import { SmartQuerySuggestions } from '../components/SmartQuerySuggestions';
import { ArgumentMapper } from '../components/ArgumentMapper';
import { ConceptEvolutionTimeline } from '../components/ConceptEvolutionTimeline';
import { CitationGenerator } from '../components/CitationGenerator';
import { AnswerQualityMetrics } from '../components/AnswerQualityMetrics';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../types';
import type { ReasoningStep } from '../types/graphrag';
import {
  mockGraphRAGResponse,
  mockReasoningSteps,
  mockQualityMetrics,
  mockArgumentMapping,
  mockConceptEvolution
} from '../data/mockGraphRAGData';

export default function GraphRAGPage() {
  const location = useLocation();
  const [messages, setMessages] = useState<GraphRAGChatMessage[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const { isAuthenticated } = useAuth();

  // Advanced settings
  const [semanticK, setSemanticK] = useState(10);
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxContext, setMaxContext] = useState(15);
  const [useStreaming, setUseStreaming] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false); // Collapsible How It Works
  const [showBenefits, setShowBenefits] = useState(false); // Start collapsed to prevent layout issues
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamedAnswer]);

  // Handle initial query from floating button/showcase (via location state)
  useEffect(() => {
    const state = location.state as { initialQuery?: string } | null;
    if (state?.initialQuery) {
      if (isAuthenticated) {
        // Auto-submit the query if authenticated
        processQuery(state.initialQuery);
        // Clear the state to prevent re-processing on re-render
        window.history.replaceState({}, document.title);
      } else {
        // If not authenticated, set as pending query and show auth modal
        setPendingQuery(state.initialQuery);
        setShowAuthModal(true);
        // Clear the state
        window.history.replaceState({}, document.title);
      }
    }
  }, [location.state, isAuthenticated]);

  // Cleanup abort controller and streaming on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  // Demo Mode - Load mock data without authentication
  const loadDemoMode = () => {
    const demoMessage: GraphRAGChatMessage = {
      role: 'user',
      content: mockGraphRAGResponse.query,
      timestamp: new Date().toISOString()
    };

    // NOTE: Source texts should come from the actual database
    // For demo purposes only - DO NOT USE FABRICATED TEXTS IN PRODUCTION
    const citationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};

    // Transform mock data to match expected structure
    const assistantMessage: GraphRAGChatMessage = {
      role: 'assistant',
      content: mockGraphRAGResponse.answer,
      timestamp: new Date().toISOString(),
      citations: {
        ancient_sources: [
          "Cicero, On Fate 41-43",
          "Cicero, On Fate 42-43; Aulus Gellius, Attic Nights 7.2.11",
          "Epictetus, Discourses 1.1; SVF 2.974-975",
          "Diogenes Laertius, Lives 7.149; SVF 2.913-944",
          "Cicero, On Fate 31-33; Academica 2.97",
          "Alexander of Aphrodisias, On Fate 13-14, 26-27"
        ],
        modern_scholarship: [
          "Bobzien, S. (1998). Determinism and Freedom in Stoic Philosophy. Oxford University Press.",
          "Frede, M. (2011). A Free Will: Origins of the Notion in Ancient Thought. University of California Press.",
          "Long, A.A. & Sedley, D.N. (1987). The Hellenistic Philosophers. Cambridge University Press."
        ]
      },
      citationTexts,
      reasoning_path: {
        starting_nodes: [
          {
            id: "person_chrysippus",
            label: "Chrysippus",
            type: "person",
            reason: "Primary Stoic philosopher who developed compatibilist theory"
          },
          {
            id: "concept_heimarmene",
            label: "Fate (heimarmenē)",
            type: "concept",
            reason: "Central concept in Stoic determinism"
          }
        ],
        expanded_nodes: [
          {
            id: "concept_eph_hemin",
            label: "eph' hēmin (in our power)",
            type: "concept",
            reason: "Key term for moral responsibility in Stoicism"
          },
          {
            id: "concept_sunkatathesis",
            label: "Assent (sunkatathesis)",
            type: "concept",
            reason: "Locus of Stoic freedom and responsibility"
          },
          {
            id: "person_carneades",
            label: "Carneades",
            type: "person",
            reason: "Academic Skeptic critic of Stoic compatibilism"
          },
          {
            id: "person_alexander_aphrodisias",
            label: "Alexander of Aphrodisias",
            type: "person",
            reason: "Peripatetic defender of incompatibilism"
          },
          {
            id: "concept_pronoia",
            label: "Providence (pronoia)",
            type: "concept",
            reason: "Stoic identification of fate with divine providence"
          },
          {
            id: "concept_logos",
            label: "Logos",
            type: "concept",
            reason: "Rational structure governing cosmos"
          }
        ],
        traversed_edges: [
          {
            source: "person_chrysippus",
            target: "concept_heimarmene",
            relation: "developed",
            description: "Chrysippus developed sophisticated theory of fate"
          },
          {
            source: "person_chrysippus",
            target: "concept_sunkatathesis",
            relation: "formulated",
            description: "Formulated doctrine of rational assent"
          },
          {
            source: "person_carneades",
            target: "person_chrysippus",
            relation: "refutes",
            description: "Academic Skeptic critique of Stoic position"
          },
          {
            source: "concept_heimarmene",
            target: "concept_pronoia",
            relation: "identified_with",
            description: "Stoics identified fate with providence"
          }
        ],
        total_nodes: 10,
        total_edges: 4
      },
      graphrag_response: mockGraphRAGResponse as GraphRAGResponse,
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

    // Check authentication first
    if (!isAuthenticated) {
      setPendingQuery(query.trim());
      setShowAuthModal(true);
      return;
    }

    // Proceed with authenticated query
    await processQuery(query.trim());
  };

  const processQuery = async (queryText: string) => {
    // Add user message
    const userMessage: GraphRAGChatMessage = {
      role: 'user',
      content: queryText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setError(null);

    if (useStreaming) {
      await handleStreamingQuery(queryText);
    } else {
      await handleStandardQuery(queryText);
    }
  };

  const handleAuthSuccess = () => {
    if (pendingQuery) {
      processQuery(pendingQuery);
      setPendingQuery(null);
    }
  };

  const handleStandardQuery = async (queryText: string) => {
    setLoading(true);

    try {
      const response = await apiClient.graphragQuery({
        query: queryText,
        semantic_k: semanticK,
        graph_depth: graphDepth,
        max_context: maxContext,
      });

      const assistantMessage: GraphRAGChatMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        reasoning_path: response.reasoning_path,
        tokens_used: response.tokens_used,
        llm_provider: response.llm_provider,
        llm_model: response.llm_model,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('GraphRAG error:', err);
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const initializeReasoningSteps = (query: string) => {
    const steps: ReasoningStep[] = [
      {
        id: 1,
        type: 'search',
        label: 'Semantic Search',
        description: 'Embedding query and searching vector database for relevant nodes',
        status: 'pending',
      },
      {
        id: 2,
        type: 'traverse',
        label: 'Graph Traversal',
        description: 'Expanding knowledge graph connections from starting nodes',
        status: 'pending',
      },
      {
        id: 3,
        type: 'context',
        label: 'Context Building',
        description: 'Assembling citations and building comprehensive context',
        status: 'pending',
      },
      {
        id: 4,
        type: 'synthesis',
        label: 'LLM Synthesis',
        description: 'Generating scholarly answer with automatic citations',
        status: 'pending',
      },
      {
        id: 5,
        type: 'complete',
        label: 'Complete',
        description: 'Answer ready with citations and reasoning path',
        status: 'pending',
      },
    ];
    setReasoningSteps(steps);
    setCurrentQuery(query);
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

  const handleStreamingQuery = async (queryText: string) => {
    setStreaming(true);
    setStreamedAnswer('');
    setStreamStatus('Connecting to server... (This may take 30-60s if the server is waking up)');
    initializeReasoningSteps(queryText);

    try {
      const token = Cookies.get('auth_token');
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // Create abort controller for cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Add timeout for connection (2 minutes to handle cold starts)
      const timeoutId = setTimeout(() => {
        abortController.abort();
      }, 120000); // 120 seconds

      const response = await fetch(`${apiUrl}/api/graphrag/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: queryText,
          semantic_k: semanticK,
          graph_depth: graphDepth,
          max_context: maxContext,
        }),
        signal: abortController.signal,
      });

      clearTimeout(timeoutId); // Clear timeout once connected

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

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
                case 'status':
                  setStreamStatus(data.message || 'Processing...');

                  // Update reasoning steps based on status messages
                  const statusMsg = (data.message || '').toLowerCase();
                  if (statusMsg.includes('embedding') || statusMsg.includes('searching')) {
                    updateReasoningStep(1, 'active');
                  } else if (statusMsg.includes('retrieving') || statusMsg.includes('found')) {
                    updateReasoningStep(1, 'complete');
                    updateReasoningStep(2, 'active');
                  } else if (statusMsg.includes('expand') || statusMsg.includes('travers')) {
                    updateReasoningStep(2, 'active');
                  } else if (statusMsg.includes('context') || statusMsg.includes('citation')) {
                    updateReasoningStep(2, 'complete');
                    updateReasoningStep(3, 'active');
                  } else if (statusMsg.includes('generat') || statusMsg.includes('synthesis')) {
                    updateReasoningStep(3, 'complete');
                    updateReasoningStep(4, 'active');
                  }
                  break;

                case 'answer_chunk':
                  fullAnswer += data.data;
                  setStreamedAnswer(fullAnswer);
                  // Mark synthesis as active when answer starts streaming
                  if (!fullAnswer) {
                    updateReasoningStep(4, 'active');
                  }
                  break;

                case 'complete':
                  finalResponse = data.data as GraphRAGResponse;
                  // Mark all steps complete
                  updateReasoningStep(5, 'complete');
                  break;

                case 'error':
                  setError(data.message || 'Stream error');
                  break;
              }
            } catch (err) {
              console.error('Error parsing SSE line:', line, err);
            }
          }
        }
      } finally {
        // CRITICAL: Always release the reader to prevent memory leaks
        reader.releaseLock();
      }

      // After stream completes
      if (finalResponse) {
        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: finalResponse.answer,
          citations: finalResponse.citations,
          reasoning_path: finalResponse.reasoning_path,
          tokens_used: finalResponse.tokens_used,
          llm_provider: finalResponse.llm_provider,
          llm_model: finalResponse.llm_model,
          timestamp: new Date(),
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
    } catch (err: any) {
      console.error('Streaming error:', err);

      // Check if it was an abort (timeout or user cancel)
      if (err.name === 'AbortError') {
        setError('Connection timeout. The server may be waking up from sleep (Render free tier). Please try again in a moment.');
      } else {
        setError(err.message || 'Failed to stream answer');
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
    try {
      const node = await apiClient.getNode(nodeId);
      if (node) {
        setSelectedNode(node);
      }
    } catch (err) {
      console.error('Failed to fetch node:', err);
    }
  };

  return (
    <>
    <div className="flex flex-col lg:flex-row gap-3 lg:gap-4 pb-8 lg:pb-4 lg:h-[calc(100vh-180px)]">
      {/* Left Sidebar - Title & Settings (Desktop) */}
      <div className="hidden lg:flex lg:flex-col lg:w-48 xl:w-56 gap-3 flex-shrink-0">
        {/* Title Section */}
        <div className="academic-card">
          <h1 className="text-lg xl:text-xl font-serif font-bold mb-1.5 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
            GraphRAG
          </h1>
          <p className="text-xs text-academic-muted leading-relaxed mb-3">
            Graph-based RAG with semantic search
          </p>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-full academic-button-outline text-xs py-1.5"
          >
            ⚙️ Settings
          </button>
        </div>

        {/* Stats Card */}
        <div className="academic-card bg-gradient-to-br from-primary-50 via-blue-50 to-indigo-50 border-primary-200 hover:shadow-md transition-all overflow-hidden relative">
          {/* Modern geometric background */}
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-primary-200/20 to-blue-200/20 rounded-full blur-2xl"></div>
          <div className="absolute bottom-0 left-0 w-16 h-16 bg-gradient-to-tr from-indigo-200/20 to-purple-200/20 rounded-full blur-xl"></div>

          <div className="text-center space-y-2 relative z-10">
            {/* Modern network graph icon */}
            <div className="mb-0.5 flex justify-center">
              <svg className="w-9 h-9" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Connection lines */}
                <line x1="24" y1="10" x2="14" y2="24" stroke="url(#gradient1)" strokeWidth="1.5" opacity="0.6"/>
                <line x1="24" y1="10" x2="34" y2="24" stroke="url(#gradient1)" strokeWidth="1.5" opacity="0.6"/>
                <line x1="14" y1="24" x2="24" y2="38" stroke="url(#gradient1)" strokeWidth="1.5" opacity="0.6"/>
                <line x1="34" y1="24" x2="24" y2="38" stroke="url(#gradient1)" strokeWidth="1.5" opacity="0.6"/>
                <line x1="14" y1="24" x2="34" y2="24" stroke="url(#gradient1)" strokeWidth="1.5" opacity="0.4"/>

                {/* Nodes */}
                <circle cx="24" cy="10" r="4" fill="url(#gradient2)" stroke="url(#gradient1)" strokeWidth="2"/>
                <circle cx="14" cy="24" r="3.5" fill="url(#gradient2)" stroke="url(#gradient1)" strokeWidth="2"/>
                <circle cx="34" cy="24" r="3.5" fill="url(#gradient2)" stroke="url(#gradient1)" strokeWidth="2"/>
                <circle cx="24" cy="38" r="4" fill="url(#gradient2)" stroke="url(#gradient1)" strokeWidth="2"/>

                {/* Small accent nodes */}
                <circle cx="8" cy="18" r="2" fill="#769687" opacity="0.4"/>
                <circle cx="40" cy="18" r="2" fill="#769687" opacity="0.4"/>
                <circle cx="24" cy="24" r="2" fill="#8baf9f" opacity="0.5"/>

                {/* Gradients */}
                <defs>
                  <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#769687"/>
                    <stop offset="100%" stopColor="#8baf9f"/>
                  </linearGradient>
                  <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#a8c3b7"/>
                    <stop offset="100%" stopColor="#ffffff"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="text-xs font-semibold text-primary-800 uppercase tracking-wider mb-1.5">Knowledge Graph</div>
            <div className="grid grid-cols-1 gap-2 text-sm">
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">534</div>
                <div className="text-xs text-academic-muted font-medium">Nodes</div>
              </div>
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">923</div>
                <div className="text-xs text-academic-muted font-medium">Relations</div>
              </div>
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">1,706</div>
                <div className="text-xs text-academic-muted font-medium">Sources</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden academic-card mb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold mb-1 sm:mb-2 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
              GraphRAG Question Answering
            </h1>
            <p className="text-sm sm:text-base text-academic-muted leading-relaxed">
              Graph-based Retrieval-Augmented Generation combines vector search with knowledge graph
              traversal to provide scholarly answers grounded in primary sources and modern scholarship.
            </p>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="academic-button-outline whitespace-nowrap self-start sm:self-auto"
          >
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col lg:h-full min-w-0">

        {/* Settings Modal Overlay */}
        {showSettings && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowSettings(false)}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <h3 className="text-xl font-bold">Search Settings</h3>
                </div>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-white/80 hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6">
            <p className="text-sm text-gray-600 mb-6">
              Adjust how GraphRAG searches and processes your questions. The defaults work well for most queries.
            </p>

            <div className="space-y-5">
              {/* Search Breadth */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Search Breadth
                  </label>
                  <span className="text-sm font-semibold text-primary-600">{semanticK} nodes</span>
                </div>
                <input
                  type="range"
                  value={semanticK}
                  onChange={(e) => setSemanticK(Number(e.target.value))}
                  min={5}
                  max={20}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Narrow</span>
                  <span className="text-xs text-gray-500">Broad</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How many starting points to find from your question
                </p>
              </div>

              {/* Connection Depth */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Connection Depth
                  </label>
                  <span className="text-sm font-semibold text-primary-600">{graphDepth} levels</span>
                </div>
                <input
                  type="range"
                  value={graphDepth}
                  onChange={(e) => setGraphDepth(Number(e.target.value))}
                  min={1}
                  max={3}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Shallow</span>
                  <span className="text-xs text-gray-500">Deep</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How far to explore connections from starting points
                </p>
              </div>

              {/* Context Size */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Context Size
                  </label>
                  <span className="text-sm font-semibold text-primary-600">{maxContext} nodes</span>
                </div>
                <input
                  type="range"
                  value={maxContext}
                  onChange={(e) => setMaxContext(Number(e.target.value))}
                  min={10}
                  max={25}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Concise</span>
                  <span className="text-xs text-gray-500">Detailed</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How much information to include in the answer
                </p>
              </div>

              {/* Streaming Toggle */}
              <div className="border-b border-gray-100 pb-5">
                <label className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <span className="text-sm font-medium text-gray-900">Real-time Updates</span>
                    <p className="text-xs text-gray-500 mt-0.5">Show progress as answer generates</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={useStreaming}
                    onChange={(e) => setUseStreaming(e.target.checked)}
                    className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-primary-600 relative transition-colors
                    before:content-[''] before:absolute before:top-0.5 before:left-0.5 before:w-5 before:h-5 before:bg-white before:rounded-full before:transition-transform
                    checked:before:translate-x-5"
                  />
                </label>
              </div>

              {/* Preset Buttons */}
              <div className="pt-2">
                <p className="text-xs font-medium text-gray-500 mb-3">Quick Presets</p>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => {
                      setSemanticK(8);
                      setGraphDepth(2);
                      setMaxContext(12);
                    }}
                    className="px-3 py-2 text-xs bg-white border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all font-medium text-gray-700"
                  >
                    Fast
                  </button>
                  <button
                    onClick={() => {
                      setSemanticK(10);
                      setGraphDepth(2);
                      setMaxContext(15);
                    }}
                    className="px-3 py-2 text-xs bg-primary-50 border border-primary-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all font-medium text-primary-700"
                  >
                    Balanced
                  </button>
                  <button
                    onClick={() => {
                      setSemanticK(15);
                      setGraphDepth(3);
                      setMaxContext(20);
                    }}
                    className="px-3 py-2 text-xs bg-white border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all font-medium text-gray-700"
                  >
                    Deep
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Modal Footer */}
          <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-2xl border-t border-gray-200 flex justify-end">
            <button
              onClick={() => setShowSettings(false)}
              className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium transition-all hover:shadow-lg"
            >
              Done
            </button>
          </div>
        </div>
        </div>
        )}

        {/* Why It's Brilliant Section - Mobile Only */}
        <div className="lg:hidden mb-4">
          <div className="academic-card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
            <button
              onClick={() => setShowBenefits(!showBenefits)}
              className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
            >
              <h3 className="font-semibold text-base text-green-900 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Why It's Brilliant
              </h3>
              <span className="text-green-700 text-sm font-medium">
                {showBenefits ? '▼ Hide' : '▶ Show'}
              </span>
            </button>
            {showBenefits && <div className="mt-3 pt-3 border-t border-green-200"></div>}
            {showBenefits && (
              <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto">
                <BenefitsContent />
              </div>
            )}
          </div>
        </div>

        {/* How GraphRAG Works Section - Mobile Only */}
        <div className="lg:hidden mb-4">
          <div className="academic-card bg-gradient-to-br from-blue-50 to-indigo-50 border-primary-200">
            <button
              onClick={() => setShowHowItWorks(!showHowItWorks)}
              className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
            >
              <h3 className="font-semibold text-base text-primary-900 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                How GraphRAG Works
              </h3>
              <span className="text-primary-700 text-sm font-medium">
                {showHowItWorks ? '▼ Hide' : '▶ Show'}
              </span>
            </button>
            {showHowItWorks && <div className="mt-3 pt-3 border-t border-primary-200"></div>}
            {showHowItWorks && (
              <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">1. Vector Search</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    Your query is embedded using Gemini and compared against 534 KG node embeddings
                    in Qdrant to find semantically relevant starting points.
                  </p>
                </div>
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">2. Graph Expansion</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    Breadth-first search traverses relationships (authored, influenced, refutes)
                    to gather connected nodes, creating rich contextual networks.
                  </p>
                </div>
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">3. Context Building</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    Retrieved nodes are formatted with their descriptions, ancient sources,
                    and modern scholarship to create comprehensive context.
                  </p>
                </div>
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">4. LLM Synthesis</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    Gemini generates a scholarly answer grounded in the knowledge graph context,
                    ensuring accuracy and academic rigor.
                  </p>
                </div>
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">5. Citation Extraction</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    Ancient sources and modern scholarship are automatically extracted and
                    formatted for proper academic citation.
                  </p>
                </div>
                <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                  <div className="font-semibold text-primary-800 mb-1.5">6. Reasoning Path</div>
                  <p className="text-academic-muted leading-relaxed text-xs">
                    The system tracks which nodes and relationships were used, providing
                    transparency and allowing verification of the reasoning process.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Messages Area - Now much larger */}
        <ShineBorder
          className="flex-1 w-full !p-0 bg-white dark:bg-black min-w-0 mb-4"
          borderRadius={16}
          borderWidth={2}
          duration={14}
          color={["#769687", "#8baf9f", "#a8c3b7"]}
        >
          <div className="overflow-y-auto p-4 sm:p-6 space-y-5 min-h-[400px] lg:min-h-0 lg:h-[calc(100vh-320px)]">
            {messages.length === 0 && !streaming && (
            <div className="py-8 lg:py-12">
              <div className="text-center mb-8 lg:mb-10">
                <div className="text-6xl lg:text-7xl mb-4 lg:mb-6">💬</div>
                <h2 className="text-3xl lg:text-4xl font-serif font-semibold mb-3 lg:mb-4">
                  Ask <span className="bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent" style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>EleutherIA</span>
                </h2>
                <p className="text-base lg:text-lg text-academic-muted mb-6 px-4 lg:px-8 leading-relaxed max-w-2xl mx-auto">
                  GraphRAG retrieves relevant nodes from the knowledge graph, traverses their connections,
                  and synthesizes scholarly answers with automatic citations.
                </p>

                {/* Demo Mode Button */}
                <div className="flex justify-center mb-6">
                  <button
                    onClick={loadDemoMode}
                    className="group relative px-8 py-4 bg-white border-2 border-primary-300 rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 hover:scale-105 overflow-hidden"
                  >
                    {/* Animated background gradient on hover */}
                    <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 via-primary-600/20 to-primary-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

                    {/* Shimmer effect */}
                    <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>

                    <div className="relative flex items-center gap-3">
                      {/* Play icon */}
                      <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow">
                        <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                      </div>

                      <div className="text-left">
                        <div className="font-bold text-primary-700 text-lg">Try Live Demo</div>
                        <div className="text-xs text-primary-600">No authentication required</div>
                      </div>

                      <svg className="w-5 h-5 text-primary-600 group-hover:translate-x-2 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </div>
                  </button>
                </div>

                <div className="lg:hidden mt-4 pt-4 border-t border-academic-border max-w-md mx-auto">
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <div className="text-xl font-bold text-primary-600">534</div>
                      <div className="text-xs text-academic-muted">Nodes</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-primary-600">923</div>
                      <div className="text-xs text-academic-muted">Relationships</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-primary-600">1,706</div>
                      <div className="text-xs text-academic-muted">Sources</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Smart Query Suggestions Toggle */}
              {!showSuggestions ? (
                <div className="flex justify-center">
                  <button
                    onClick={() => setShowSuggestions(true)}
                    className="group relative px-5 py-2.5 bg-gradient-to-r from-primary-600 via-primary-700 to-primary-600 rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02]"
                  >
                    {/* Animated shimmer effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>

                    <div className="relative flex items-center gap-2">
                      <svg className="w-4 h-4 text-white animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span className="text-sm font-semibold text-white">
                        Explore Smart Suggestions
                      </span>
                      <svg className="w-4 h-4 text-white/80 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">Smart Suggestions</h3>
                    <button
                      onClick={() => setShowSuggestions(false)}
                      className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                    >
                      Hide
                    </button>
                  </div>
                  <SmartQuerySuggestions
                    currentQuery={query}
                    onSuggestionClick={(suggestion) => {
                      setQuery(suggestion);
                      setShowSuggestions(false);
                      // Auto-focus the input after selecting a suggestion
                      setTimeout(() => {
                        const input = document.querySelector('input[type="text"]') as HTMLInputElement;
                        input?.focus();
                      }, 100);
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} onNodeClick={handleNodeClick} />
          ))}

          {streaming && (
            <div className="space-y-4">
              {/* Reasoning Path Visualizer */}
              {reasoningSteps.length > 0 && (
                <ReasoningPathVisualizer
                  query={currentQuery}
                  steps={reasoningSteps}
                  isActive={true}
                />
              )}

              {/* Streamed Answer */}
              <div className="bg-white border border-primary-200 rounded-xl p-4 sm:p-5 lg:p-6 shadow-sm">
                {/* Show cold start loader if no answer yet and taking a while */}
                {!streamedAnswer && streamStatus.includes('waking') ? (
                  <ColdStartLoaderMinimal isLoading={true} />
                ) : (
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="spinner w-5 h-5 flex-shrink-0"></div>
                    <span className="text-sm sm:text-base text-primary-700 font-medium break-words">{streamStatus}</span>
                  </div>
                )}
                {streamedAnswer && (
                  <div className="markdown-content prose prose-base lg:prose-lg max-w-none overflow-x-auto">
                    <ReactMarkdown>{streamedAnswer}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 sm:p-4 text-red-800">
                <p className="font-medium text-sm sm:text-base break-words">Error: {error}</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ShineBorder>

        {/* Input Area - Enhanced */}
        <ShineBorder
          className="w-full !p-0 bg-white dark:bg-black min-w-0"
          borderRadius={16}
          borderWidth={2}
          duration={12}
          color={["#769687", "#8baf9f", "#a8c3b7"]}
        >
          <form onSubmit={handleSubmit}>
            <div className="relative flex items-center">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about ancient free will debates..."
                disabled={loading || streaming}
                className="w-full pl-5 sm:pl-6 pr-24 sm:pr-32 py-4 sm:py-5 bg-transparent focus:outline-none disabled:opacity-50 text-base sm:text-lg rounded-2xl"
              />
              {streaming ? (
                <button
                  type="button"
                  onClick={stopStreaming}
                  className="absolute right-3 sm:right-4 px-5 sm:px-7 py-2.5 sm:py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium whitespace-nowrap transition-all hover:shadow-md text-sm sm:text-base"
                >
                  Stop
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="absolute right-3 sm:right-4 px-5 sm:px-7 py-2.5 sm:py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap transition-all hover:shadow-md text-sm sm:text-base"
                >
                  {loading ? 'Thinking...' : 'Ask'}
                </button>
              )}
            </div>
          </form>
        </ShineBorder>
      </div>

      {/* Right Sidebar - Info panels (Desktop) */}
      <div className="hidden lg:flex lg:flex-col lg:w-64 xl:w-72 gap-3 flex-shrink-0 h-full overflow-y-auto">
        {/* How GraphRAG Works Section - Collapsible */}
        <div className="academic-card bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-primary-200 hover:shadow-md transition-all">
          <button
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="w-full flex items-center justify-between text-left hover:opacity-80 transition-all group"
          >
            <h3 className="font-semibold text-base xl:text-lg text-primary-900 flex items-center gap-2 group-hover:text-primary-700 transition-colors">
              <svg className="w-5 h-5 xl:w-6 xl:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              How It Works
            </h3>
            <span className="text-primary-700 text-sm font-medium group-hover:scale-110 transition-transform">
              {showHowItWorks ? '▼' : '▶'}
            </span>
          </button>
          {showHowItWorks && <div className="mt-3 pt-3 border-t border-primary-200"></div>}
          {showHowItWorks && (
            <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">1. Vector Search</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Your query is embedded using Gemini and compared against 534 KG node embeddings
                  in Qdrant to find semantically relevant starting points.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">2. Graph Expansion</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Breadth-first search traverses relationships (authored, influenced, refutes)
                  to gather connected nodes, creating rich contextual networks.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">3. Context Building</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Ancient sources and modern scholarship are extracted from retrieved nodes,
                  prioritized by node type (persons, arguments, concepts).
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">4. LLM Synthesis</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  An LLM generates a scholarly answer grounded exclusively in the retrieved
                  Knowledge Graph context, with strict citation requirements.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Why It's Brilliant Section */}
        <div className="academic-card bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-200 hover:shadow-md transition-all">
          <button
            onClick={() => setShowBenefits(!showBenefits)}
            className="w-full flex items-center justify-between text-left hover:opacity-80 transition-all group"
          >
            <h3 className="font-semibold text-base xl:text-lg text-green-900 flex items-center gap-2 group-hover:text-green-700 transition-colors">
              <svg className="w-5 h-5 xl:w-6 xl:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Why It's Brilliant
            </h3>
            <span className="text-green-700 text-sm font-medium group-hover:scale-110 transition-transform">
              {showBenefits ? '▼' : '▶'}
            </span>
          </button>
          {showBenefits && <div className="mt-3 pt-3 border-t border-green-200"></div>}
          {showBenefits && (
            <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
              <BenefitsContent />
            </div>
          )}
        </div>

        {/* Last Response Stats */}
        {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
          <div className="academic-card bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 border-amber-200 hover:shadow-md transition-all">
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="font-semibold text-base xl:text-lg text-amber-900">Response Metrics</h3>
            </div>
            {messages[messages.length - 1].citations && (
              <div className="space-y-2.5 text-sm">
                <div className="flex justify-between items-center py-2 px-3 bg-white/60 rounded-lg">
                  <span className="font-medium text-amber-900">Ancient Sources</span>
                  <span className="text-primary-600 font-bold text-lg">
                    {messages[messages.length - 1].citations!.ancient_sources.length}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 px-3 bg-white/60 rounded-lg">
                  <span className="font-medium text-amber-900">Modern Scholarship</span>
                  <span className="text-primary-600 font-bold text-lg">
                    {messages[messages.length - 1].citations!.modern_scholarship.length}
                  </span>
                </div>
                {messages[messages.length - 1].reasoning_path && (
                  <div className="flex justify-between items-center py-2 px-3 bg-white/60 rounded-lg">
                    <span className="font-medium text-amber-900">Nodes Used</span>
                    <span className="text-primary-600 font-bold text-lg">
                      {messages[messages.length - 1].reasoning_path!.total_nodes}
                    </span>
                  </div>
                )}
                {messages[messages.length - 1].tokens_used !== undefined && (
                  <div className="flex justify-between items-center py-2 px-3 bg-white/60 rounded-lg">
                    <span className="font-medium text-amber-900">Tokens Used</span>
                    <span className="text-primary-600 font-bold text-lg">
                      {messages[messages.length - 1].tokens_used!.toLocaleString()}
                    </span>
                  </div>
                )}
                {messages[messages.length - 1].llm_model && (
                  <div className="flex justify-between items-center py-2 px-3 bg-white/60 rounded-lg">
                    <span className="font-medium text-amber-900">Model</span>
                    <span className="text-xs text-academic-muted font-mono">
                      {messages[messages.length - 1].llm_model}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
    
    {/* Authentication Modal */}
    <AuthModal
      isOpen={showAuthModal}
      onClose={() => {
        setShowAuthModal(false);
        setPendingQuery(null);
      }}
      onSuccess={handleAuthSuccess}
      title="Authentication Required"
      message="Please log in to use GraphRAG Q&A. This feature uses AI to provide scholarly answers."
    />

    {/* Node Detail Panel */}
    {selectedNode && (
      <NodeDetailPanel
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
      />
    )}
    </>
  );
}

// Benefits Content Component (reusable for mobile and desktop)
function BenefitsContent() {
  return (
    <>
      {/* Benefit 1: Relationship Discovery */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Discovers Hidden Relationships
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Traditional search:</strong> "Augustine free will" → finds Augustine's writings.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Finds Augustine → traverses to Pelagius (opponent) →
          discovers the Pelagian Controversy → connects to earlier Stoic concepts Augustine adapted
          → reveals the complete debate context.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You understand Augustine's position through his intellectual battles and sources.
        </p>
      </div>

      {/* Benefit 2: Contextual Understanding */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Provides Rich Historical Context
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Simple RAG:</strong> Retrieves isolated text chunks about "ἐφ' ἡμῖν" (in our power).
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Shows how the concept evolved from Aristotle (4th c. BCE) →
          adopted by Stoics → critiqued by Carneades → reformulated by Epictetus →
          transmitted to Latin as "in nostra potestate" → influenced Christian theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You see the intellectual genealogy spanning 800 years.
        </p>
      </div>

      {/* Benefit 3: Argument Networks */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Maps Complete Argument Networks
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Keyword search:</strong> "Chrysippus determinism" → scattered mentions.
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Retrieves Chrysippus's arguments → follows "refutes" edges to
          Carneades's counter-arguments → finds Cicero's synthesis → discovers later Neoplatonic
          responses → extracts all cited sources.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → You get the full dialectical landscape, not isolated opinions.
        </p>
      </div>

      {/* Benefit 4: Automatic Citations */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Grounds Every Claim in Sources
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Standard LLM:</strong> Might hallucinate "Plato discussed compatibilism in Republic X."
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG:</strong> Only uses information from retrieved nodes. Automatically extracts
          ancient sources (e.g., "Aristotle, <em>EN</em> III.1, 1110a1-4") and modern scholarship
          (e.g., "Bobzien 1998, Frede 2011") from node metadata.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Verifiable, academically rigorous answers you can cite in your own research.
        </p>
      </div>

      {/* Benefit 5: Multi-hop Reasoning */}
      <div className="bg-white/80 rounded-lg p-2.5 border border-green-100">
        <div className="font-semibold text-green-800 mb-1.5">
          Enables Multi-Hop Reasoning
        </div>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>Question:</strong> "How did Aristotelian ethics influence Christian theology?"
        </p>
        <p className="text-academic-muted leading-relaxed mb-1.5 text-xs">
          <strong>GraphRAG path:</strong> Aristotle → "influenced" → Alexander of Aphrodisias →
          "transmitted_by" → Arabic commentators → "influenced" → Thomas Aquinas →
          "synthesized_with" → Augustine's theology.
        </p>
        <p className="text-green-700 text-xs font-medium italic">
          → Traces intellectual transmission across cultures and centuries in a single query.
        </p>
      </div>
    </>
  );
}

// Message Bubble Component
function MessageBubble({
  message,
  onNodeClick
}: {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
}) {
  const [showCitations, setShowCitations] = useState(false);
  const [showAllAncient, setShowAllAncient] = useState(false);
  const [showAllModern, setShowAllModern] = useState(false);
  const [showReasoningPath, setShowReasoningPath] = useState(false);
  const [showQualityMetrics, setShowQualityMetrics] = useState(false);
  const [showCitationGenerator, setShowCitationGenerator] = useState(false);
  const [showArgumentMap, setShowArgumentMap] = useState(false);
  const [showConceptEvolution, setShowConceptEvolution] = useState(false);

  return (
    <div className={`${message.role === 'user' ? 'ml-auto max-w-[85%] lg:max-w-2xl' : 'mr-auto max-w-[95%] lg:max-w-full'}`}>
      <div
        className={`rounded-xl p-4 sm:p-5 lg:p-6 shadow-sm hover:shadow-md transition-shadow ${
          message.role === 'user'
            ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white'
            : 'bg-white border border-academic-border'
        }`}
      >
        {message.role === 'user' ? (
          <p className="text-base sm:text-lg break-words leading-relaxed">{message.content}</p>
        ) : (
          <div className="space-y-3">
            <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {/* Reasoning Path with Clickable Nodes */}
            {message.reasoning_path && (
              <div className="border-t border-academic-border pt-3">
                <button
                  onClick={() => setShowReasoningPath(!showReasoningPath)}
                  className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  {showReasoningPath ? '▼' : '▶'} View Knowledge Graph Path (
                  {message.reasoning_path.total_nodes} nodes)
                </button>

                {showReasoningPath && (
                  <div className="mt-3 space-y-3 text-xs sm:text-sm">
                    {/* Starting Nodes */}
                    {message.reasoning_path.starting_nodes.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Starting Points ({message.reasoning_path.starting_nodes.length}):</h4>
                        <div className="space-y-2">
                          {message.reasoning_path.starting_nodes.map((node, i) => (
                            <button
                              key={i}
                              onClick={() => onNodeClick(node.id)}
                              className="w-full text-left p-2 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors"
                            >
                              <div className="flex items-start gap-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-200 text-blue-800">
                                  {node.type}
                                </span>
                                <div className="flex-1">
                                  <div className="font-semibold text-blue-900">{node.label}</div>
                                  <div className="text-xs text-blue-700 mt-0.5">{node.reason}</div>
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Expanded Nodes */}
                    {message.reasoning_path.expanded_nodes.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Related Nodes ({message.reasoning_path.expanded_nodes.length}):</h4>
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {message.reasoning_path.expanded_nodes.map((node, i) => (
                            <button
                              key={i}
                              onClick={() => onNodeClick(node.id)}
                              className="w-full text-left p-2 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
                            >
                              <div className="flex items-start gap-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-800">
                                  {node.type}
                                </span>
                                <div className="flex-1">
                                  <div className="font-semibold text-gray-900">{node.label}</div>
                                  <div className="text-xs text-gray-700 mt-0.5">{node.reason}</div>
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Citations */}
            {message.citations && (
              <div className="border-t border-academic-border pt-3 mt-3">
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  {showCitations ? '▼' : '▶'} View Citations (
                  {message.citations.ancient_sources.length +
                    message.citations.modern_scholarship.length}
                  )
                </button>

                {showCitations && (
                  <div className="mt-3 space-y-3 text-xs sm:text-sm">
                    {message.citations.ancient_sources.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Ancient Sources ({message.citations.ancient_sources.length}):</h4>
                        <ul className="list-disc list-inside space-y-1.5 text-academic-muted pl-2">
                          {(showAllAncient
                            ? message.citations.ancient_sources
                            : message.citations.ancient_sources.slice(0, 5)
                          ).map((source, i) => (
                            <li key={i} className="citation break-words">
                              <CitationPreview
                                citation={source}
                                type="ancient"
                                sourceText={message.citationTexts?.[source]}
                              >
                                {source}
                              </CitationPreview>
                            </li>
                          ))}
                        </ul>
                        {message.citations.ancient_sources.length > 5 && (
                          <button
                            onClick={() => setShowAllAncient(!showAllAncient)}
                            className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
                          >
                            {showAllAncient
                              ? '▲ Show less'
                              : `▼ Show all ${message.citations.ancient_sources.length} sources`
                            }
                          </button>
                        )}
                      </div>
                    )}

                    {message.citations.modern_scholarship.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Modern Scholarship ({message.citations.modern_scholarship.length}):</h4>
                        <ul className="list-disc list-inside space-y-1.5 text-academic-muted pl-2">
                          {(showAllModern
                            ? message.citations.modern_scholarship
                            : message.citations.modern_scholarship.slice(0, 3)
                          ).map((source, i) => (
                            <li key={i} className="citation break-words">
                              <CitationPreview
                                citation={source}
                                type="modern"
                              >
                                {source}
                              </CitationPreview>
                            </li>
                          ))}
                        </ul>
                        {message.citations.modern_scholarship.length > 3 && (
                          <button
                            onClick={() => setShowAllModern(!showAllModern)}
                            className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
                          >
                            {showAllModern
                              ? '▲ Show less'
                              : `▼ Show all ${message.citations.modern_scholarship.length} sources`
                            }
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Advanced GraphRAG Visualizations - Only for demo/graphrag responses */}
            {message.graphrag_response && (
              <div className="space-y-4 mt-6">
                {/* Answer Quality Metrics */}
                <div className="border-t border-academic-border pt-4">
                  <button
                    onClick={() => setShowQualityMetrics(!showQualityMetrics)}
                    className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-2"
                  >
                    {showQualityMetrics ? '▼' : '▶'} Answer Quality Metrics
                    <span className="text-xs text-gray-500">(Confidence: {mockQualityMetrics.overallQuality}%)</span>
                  </button>
                  {showQualityMetrics && (
                    <div className="mt-4">
                      <AnswerQualityMetrics metrics={mockQualityMetrics} />
                    </div>
                  )}
                </div>

                {/* Citation Generator */}
                <div className="border-t border-academic-border pt-4">
                  <button
                    onClick={() => setShowCitationGenerator(!showCitationGenerator)}
                    className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                  >
                    {showCitationGenerator ? '▼' : '▶'} Export Citations (APA, MLA, Chicago, BibTeX)
                  </button>
                  {showCitationGenerator && (
                    <div className="mt-4">
                      <CitationGenerator citations={mockGraphRAGResponse.citations} />
                    </div>
                  )}
                </div>

                {/* Argument Mapper */}
                <div className="border-t border-academic-border pt-4">
                  <button
                    onClick={() => setShowArgumentMap(!showArgumentMap)}
                    className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                  >
                    {showArgumentMap ? '▼' : '▶'} Argument Structure Map
                  </button>
                  {showArgumentMap && (
                    <div className="mt-4">
                      <ArgumentMapper argument={mockArgumentMapping} />
                    </div>
                  )}
                </div>

                {/* Concept Evolution Timeline */}
                <div className="border-t border-academic-border pt-4">
                  <button
                    onClick={() => setShowConceptEvolution(!showConceptEvolution)}
                    className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                  >
                    {showConceptEvolution ? '▼' : '▶'} Concept Evolution Timeline
                  </button>
                  {showConceptEvolution && (
                    <div className="mt-4">
                      <ConceptEvolutionTimeline evolution={mockConceptEvolution} />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="text-xs mt-2 opacity-70">
          {typeof message.timestamp === 'string'
            ? new Date(message.timestamp).toLocaleTimeString()
            : message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
