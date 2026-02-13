/**
 * GraphRAGPage - Modular Implementation
 *
 * Decomposed from 2,186 lines to ~400 lines via:
 * - hooks/useGraphRAGState.ts - State management
 * - hooks/useConversation.ts - Conversation memory
 * - hooks/useStreaming.ts - SSE streaming logic
 * - components/MessageBubble.tsx - Message display
 * - components/BenefitsContent.tsx - Info section
 */

import { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

// UI Components
import AuthModal from '../../components/AuthModal';
import { ShineBorder } from '../../components/ui/shine-border';
import { AuroraBackground } from '../../components/ui/aurora-background';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import NodeDetailPanel from '../../components/NodeDetailPanel';
import { StreamingOverlay } from '../../components/ui/streaming-loader';
import { ReasoningPathVisualizer } from '../../components/graphrag/ReasoningPathVisualizer';
import { ThinkingProcessPanel } from '../../components/graphrag/ThinkingProcessPanel';
import { ConversationSidebar } from '../../components/graphrag/ConversationSidebar';
import { SmartQuerySuggestions } from '../../components/SmartQuerySuggestions';

// Local components
import { MessageBubble, BenefitsContent } from './components';
import { useGraphRAGState, useConversation, useStreaming } from './hooks';

// Types
import type { GraphRAGChatMessage } from '../../types';

// Mock data for demo mode
import { mockGraphRAGResponse, mockReasoningSteps } from '../../data/mockGraphRAGData';

export default function GraphRAGPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  // Initialize state
  const state = useGraphRAGState();

  // Conversation management
  const conversation = useConversation(
    isAuthenticated,
    (messages) => {
      state.setMessages(messages);
      state.setStreamedAnswer('');
      state.setStreamedThinking('');
      state.setThinkingComplete(false);
    },
    () => {
      state.setMessages([]);
      state.setStreamedAnswer('');
      state.setStreamedThinking('');
      state.setThinkingComplete(false);
      state.setReasoningSteps([]);
      state.setCurrentQuery('');
    }
  );

  // Streaming handlers
  const streaming = useStreaming({
    onStatus: state.setStreamStatus,
    onThinkingChunk: (chunk) => state.setStreamedThinking(prev => prev + chunk),
    onThinkingComplete: () => state.setThinkingComplete(true),
    onAnswerChunk: state.setStreamedAnswer,
    onComplete: () => {},
    onError: state.setError,
    onReasoningStep: (stepId, status) => {
      state.setReasoningSteps(prev =>
        prev.map(step =>
          step.id === stepId
            ? { ...step, status }
            : step.id < stepId && step.status !== 'complete'
            ? { ...step, status: 'complete' }
            : step
        )
      );
    },
    onAIGenerating: state.setShowAIGenerating,
  });

  // Fetch KG stats on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const kgStatsResponse = await apiClient.getKGStats();
        const worksStatsResponse = await apiClient.getWorksStats();
        state.setKgStats({
          nodes: kgStatsResponse.totalNodes || 0,
          edges: kgStatsResponse.totalEdges || 0,
          sources: worksStatsResponse.total_passages || 0,
          hierarchyLayers: 3,
        });
      } catch (err) {
        console.error('Failed to fetch KG stats:', err);
      }
    };
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally mount-only: state.setKgStats is a stable setState dispatcher
  }, []);

  // Scroll to bottom during streaming
  useEffect(() => {
    if (state.streaming) {
      state.messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- state.messagesEndRef is a stable useRef; destructuring state on every render would cause unnecessary re-runs
  }, [state.messages, state.streamedAnswer, state.streaming]);

  // Process query (main handler)
  const processQuery = useCallback(async (queryText: string) => {
    const userMessage: GraphRAGChatMessage = {
      role: 'user',
      content: queryText,
      timestamp: new Date(),
    };

    state.setMessages(prev => [...prev, userMessage]);
    state.setQuery('');
    state.setError(null);

    if (state.settings.useStreaming) {
      await handleStreamingQuery(queryText);
    } else {
      await handleStandardQuery(queryText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleStreamingQuery/handleStandardQuery are non-memoized closures that capture current state; adding them would cause infinite re-creation. state.setMessages/setQuery/setError are stable setState dispatchers.
  }, [state.settings.useStreaming]);

  // Handle initial query from location state
  useEffect(() => {
    const locationState = location.state as { initialQuery?: string } | null;
    if (locationState?.initialQuery) {
      if (isAuthenticated) {
        processQuery(locationState.initialQuery);
        window.history.replaceState({}, document.title);
      } else {
        state.setPendingQuery(locationState.initialQuery);
        state.setShowAuthModal(true);
        window.history.replaceState({}, document.title);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- state.setPendingQuery and state.setShowAuthModal are stable setState dispatchers
  }, [location.state, isAuthenticated, processQuery]);

  // Streaming query handler
  const handleStreamingQuery = async (queryText: string) => {
    state.setStreaming(true);
    state.setStreamedAnswer('');
    state.setStreamedThinking('');
    state.setThinkingComplete(false);
    state.setStreamStatus('Connecting to server...');
    state.setReasoningSteps(streaming.initializeReasoningSteps(queryText));
    state.setCurrentQuery(queryText);

    // Create conversation if needed
    let activeConversationId = conversation.conversationId;
    if (!activeConversationId && isAuthenticated) {
      activeConversationId = await conversation.createConversation({
        semantic_k: state.settings.semanticK,
        graph_depth: state.settings.graphDepth,
        max_context: state.settings.maxContext,
        use_thinking: state.settings.useThinking,
      });
    }

    try {
      const { finalResponse, fullAnswer } = await streaming.startStreaming({
        query: queryText,
        settings: state.settings,
        conversationId: activeConversationId,
      });

      if (finalResponse) {
        const assistantMessage: GraphRAGChatMessage = {
          role: 'assistant',
          content: finalResponse.answer || fullAnswer,
          citations: finalResponse.citations,
          reasoning_path: finalResponse.reasoning_path,
          thinking_process: state.streamedThinking || undefined,
          tokens_used: finalResponse.tokens_used,
          llm_provider: finalResponse.llm_provider,
          llm_model: finalResponse.llm_model,
          timestamp: new Date(),
          graphrag_response: finalResponse,
        };

        state.setMessages(prev => [...prev, assistantMessage]);

        if (activeConversationId) {
          conversation.loadConversations();
        }
      }
    } catch (err) {
      console.error('Streaming error:', err);
      state.setError(err instanceof Error ? err.message : 'Streaming failed');
    } finally {
      state.setStreaming(false);
      state.setStreamStatus('');
    }
  };

  // Standard (non-streaming) query handler
  const handleStandardQuery = async (queryText: string) => {
    state.setLoading(true);

    try {
      let activeConversationId = conversation.conversationId;
      if (!activeConversationId && isAuthenticated) {
        activeConversationId = await conversation.createConversation({
          semantic_k: state.settings.semanticK,
          graph_depth: state.settings.graphDepth,
          max_context: state.settings.maxContext,
        });
      }

      const response = await apiClient.graphragQuery({
        query: queryText,
        semantic_k: state.settings.semanticK,
        graph_depth: state.settings.graphDepth,
        max_context: state.settings.maxContext,
        conversation_id: activeConversationId || undefined,
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
        graphrag_response: response,
      };

      state.setMessages(prev => [...prev, assistantMessage]);

      if (activeConversationId) {
        conversation.loadConversations();
      }
    } catch (err) {
      console.error('GraphRAG error:', err);
      state.setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      state.setLoading(false);
    }
  };

  // Form submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.query.trim() || state.loading || state.streaming) return;

    if (!isAuthenticated) {
      state.setPendingQuery(state.query.trim());
      state.setShowAuthModal(true);
      return;
    }

    await processQuery(state.query.trim());
  };

  // Auth success handler
  const handleAuthSuccess = () => {
    if (state.pendingQuery) {
      processQuery(state.pendingQuery);
      state.setPendingQuery(null);
    }
  };

  // Demo mode handler
  const loadDemoMode = () => {
    const demoMessage: GraphRAGChatMessage = {
      role: 'user',
      content: mockGraphRAGResponse.query,
      timestamp: new Date(),
    };

    const assistantMessage: GraphRAGChatMessage = {
      role: 'assistant',
      content: mockGraphRAGResponse.answer,
      timestamp: new Date(),
      citations: mockGraphRAGResponse.citations,
      reasoning_path: mockGraphRAGResponse.reasoning_path,
      graphrag_response: mockGraphRAGResponse,
      reasoning_steps: mockReasoningSteps,
    };

    state.setMessages([demoMessage, assistantMessage]);
    state.setReasoningSteps(mockReasoningSteps);
    state.setCurrentQuery(mockGraphRAGResponse.query);
    state.setQuery('');
  };

  // Node click handler
  const handleNodeClick = async (nodeId: string) => {
    try {
      const node = await apiClient.getNode(nodeId);
      state.setSelectedNode(node);
    } catch (err) {
      console.error('Failed to load node:', err);
    }
  };

  // Cancel streaming handler
  const handleCancelStreaming = () => {
    streaming.cancelStreaming();
    state.setStreaming(false);
    state.setStreamStatus('');
  };

  return (
    <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
      <div className="relative min-h-screen overflow-hidden pt-12">
        {/* AI Loader */}
        {state.showAIGenerating && (
          <StreamingOverlay
            status="Synthesizing Answer"
            substatus="Analyzing knowledge graph context..."
          />
        )}

        {/* Main Layout */}
        <div className="relative z-10 flex flex-col lg:flex-row gap-3 lg:gap-4 p-4 lg:p-6 min-h-0 h-[calc(100vh-5rem)] lg:h-[calc(100vh-6rem)]">

          {/* Left Sidebar - Title & Stats */}
          <LeftSidebar
            t={t}
            kgStats={state.kgStats}
            showSettings={state.showSettings}
            setShowSettings={state.setShowSettings}
            showHowItWorks={state.showHowItWorks}
            setShowHowItWorks={state.setShowHowItWorks}
            showBenefits={state.showBenefits}
            setShowBenefits={state.setShowBenefits}
            isAuthenticated={isAuthenticated}
            showSidebar={conversation.showSidebar}
            setShowSidebar={conversation.setShowSidebar}
          />

          {/* Conversation Sidebar */}
          {isAuthenticated && conversation.showSidebar && (
            <ConversationSidebar
              conversations={conversation.conversations}
              activeConversationId={conversation.conversationId}
              isLoading={conversation.conversationsLoading}
              isCollapsed={conversation.sidebarCollapsed}
              onNewConversation={conversation.handleNewConversation}
              onSelectConversation={async (id) => {
                state.setLoading(true);
                try {
                  await conversation.handleSelectConversation(id);
                } finally {
                  state.setLoading(false);
                }
              }}
              onDeleteConversation={conversation.handleDeleteConversation}
              onRefreshConversations={conversation.loadConversations}
              onToggleCollapse={() => conversation.setSidebarCollapsed(!conversation.sidebarCollapsed)}
            />
          )}

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col min-w-0 min-h-0">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
              {state.messages.length === 0 ? (
                <WelcomeScreen
                  t={t}
                  loadDemoMode={loadDemoMode}
                  setQuery={state.setQuery}
                  inputRef={state.inputRef}
                />
              ) : (
                <>
                  {state.messages.map((message, index) => (
                    <MessageBubble
                      key={index}
                      message={message}
                      onNodeClick={handleNodeClick}
                    />
                  ))}

                  {/* Streaming Answer */}
                  {state.streaming && state.streamedAnswer && (
                    <div className="mr-auto max-w-[95%] lg:max-w-full animate-in fade-in-0 slide-in-from-bottom-2 duration-500">
                      <div className="rounded-xl p-4 sm:p-5 lg:p-6 shadow-lg bg-white/80 backdrop-blur-xl border border-gray-200/50">
                        <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                          <ReactMarkdown>{state.streamedAnswer}</ReactMarkdown>
                        </div>
                        <div className="text-xs mt-2 opacity-70">{state.streamStatus}</div>
                      </div>
                    </div>
                  )}

                  {/* Thinking Panel */}
                  {state.streaming && state.settings.useThinking && state.streamedThinking && (
                    <ThinkingProcessPanel
                      thinking={state.streamedThinking}
                      isComplete={state.thinkingComplete}
                    />
                  )}

                  {/* Reasoning Steps */}
                  {state.streaming && state.reasoningSteps.length > 0 && (
                    <ReasoningPathVisualizer
                      steps={state.reasoningSteps}
                      query={state.currentQuery}
                    />
                  )}

                  <div ref={state.messagesEndRef} />
                </>
              )}
            </div>

            {/* Query Input */}
            <QueryInput
              t={t}
              query={state.query}
              setQuery={state.setQuery}
              loading={state.loading}
              streaming={state.streaming}
              error={state.error}
              onSubmit={handleSubmit}
              onCancel={handleCancelStreaming}
              inputRef={state.inputRef}
            />
          </div>
        </div>

        {/* Modals */}
        <AuthModal
          isOpen={state.showAuthModal}
          onClose={() => {
            state.setShowAuthModal(false);
            state.setPendingQuery(null);
          }}
          onSuccess={handleAuthSuccess}
          title="Authentication Required"
          message="Please log in to use HiRAG Q&A. This feature uses AI to provide scholarly answers."
        />

        {state.selectedNode && (
          <NodeDetailPanel
            node={state.selectedNode}
            onClose={() => state.setSelectedNode(null)}
          />
        )}
      </div>
    </AuroraBackground>
  );
}

// Sub-components (kept in same file for simplicity)

interface LeftSidebarProps {
  t: (key: string) => string;
  kgStats: { nodes: number; edges: number; sources: number; hierarchyLayers: number };
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  showHowItWorks: boolean;
  setShowHowItWorks: (show: boolean) => void;
  showBenefits: boolean;
  setShowBenefits: (show: boolean) => void;
  isAuthenticated: boolean;
  showSidebar: boolean;
  setShowSidebar: (show: boolean) => void;
}

function LeftSidebar({ t, kgStats, showSettings, setShowSettings, showHowItWorks, setShowHowItWorks, showBenefits, setShowBenefits, isAuthenticated, showSidebar, setShowSidebar }: LeftSidebarProps) {
  return (
    <div className="hidden lg:flex lg:flex-col lg:w-48 xl:w-56 gap-3 flex-shrink-0">
      {/* Title Card */}
      <Card variant="default" padding="md">
        <CardHeader className="p-0 mb-3">
          <CardTitle className="text-lg xl:text-xl bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
            {t('graphrag.title')}
          </CardTitle>
          <CardDescription className="text-xs leading-relaxed">
            {t('graphrag.description')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Button onClick={() => setShowSettings(!showSettings)} variant="outline" size="sm" fullWidth>
            ⚙️ {t('graphrag.settings')}
          </Button>
          {isAuthenticated && (
            <Button onClick={() => setShowSidebar(!showSidebar)} variant={showSidebar ? "default" : "outline"} size="sm" fullWidth className="mt-2">
              💬 {showSidebar ? 'Hide' : 'Show'} History
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Stats Card */}
      <Card variant="elevated" padding="md" className="bg-gradient-to-br from-primary-50 via-blue-50 to-indigo-50 border-primary-200">
        <div className="text-center space-y-2">
          <div className="text-xs font-semibold text-primary-800 uppercase tracking-wider">{t('graphrag.snapshot')}</div>
          <div className="grid grid-cols-1 gap-2 text-sm">
            <StatItem value={kgStats.nodes} label={t('kg.nodes')} />
            <StatItem value={kgStats.edges} label={t('kg.edges')} />
            <StatItem value={kgStats.sources} label={t('graphrag.sources')} />
            <StatItem value={kgStats.hierarchyLayers} label="Hierarchy Layers" />
          </div>
        </div>
      </Card>

      {/* How It Works */}
      <CollapsibleCard
        title="How HiRAG Works"
        icon="⚡"
        isOpen={showHowItWorks}
        onToggle={() => setShowHowItWorks(!showHowItWorks)}
        variant="blue"
      >
        <HowItWorksContent />
      </CollapsibleCard>

      {/* Benefits */}
      <CollapsibleCard
        title="Why It's Brilliant"
        icon="💡"
        isOpen={showBenefits}
        onToggle={() => setShowBenefits(!showBenefits)}
        variant="green"
      >
        <BenefitsContent />
      </CollapsibleCard>
    </div>
  );
}

function StatItem({ value, label }: { value: number; label: string }) {
  return (
    <div className="py-1.5 px-2 bg-white/60 rounded-lg">
      <div className="text-2xl font-bold text-primary-600 mb-0.5">{value.toLocaleString()}</div>
      <div className="text-xs text-academic-muted font-medium">{label}</div>
    </div>
  );
}

interface CollapsibleCardProps {
  title: string;
  icon: string;
  isOpen: boolean;
  onToggle: () => void;
  variant: 'blue' | 'green';
  children: React.ReactNode;
}

function CollapsibleCard({ title, icon, isOpen, onToggle, variant, children }: CollapsibleCardProps) {
  const colors = variant === 'blue'
    ? 'from-blue-50/80 via-indigo-50/80 to-purple-50/80 border-primary-200/50'
    : 'from-green-50/80 via-emerald-50/80 to-teal-50/80 border-green-200/50';

  return (
    <div className={`academic-card bg-gradient-to-br ${colors} backdrop-blur-xl`}>
      <button onClick={onToggle} className="w-full flex items-center justify-between text-left hover:opacity-80 transition-all">
        <h3 className="font-semibold text-base xl:text-lg text-primary-900 flex items-center gap-2">
          {icon} {title}
        </h3>
        <span className="text-primary-700 text-sm font-medium">{isOpen ? '▼' : '▶'}</span>
      </button>
      {isOpen && <div className="mt-3 pt-3 border-t border-primary-200 text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">{children}</div>}
    </div>
  );
}

function HowItWorksContent() {
  const steps = [
    { title: '1. HiIndex Hierarchy', desc: 'The knowledge graph is clustered into layered communities.' },
    { title: '2. Local Retrieval', desc: 'Queries seed level-2 entities via embedding search.' },
    { title: '3. Bridge Mode', desc: 'Cross-community connectors complete multi-hop reasoning.' },
    { title: '4. Global Summaries', desc: 'Level-0 and level-1 digests provide thematic framing.' },
    { title: '5. LLM Synthesis', desc: 'Gemini assembles the layered bundle into a narrative.' },
    { title: '6. Evidence Tracking', desc: 'Citations and reasoning paths are logged for auditability.' },
  ];

  return (
    <>
      {steps.map((step, i) => (
        <div key={i} className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
          <div className="font-semibold text-primary-800 mb-1.5">{step.title}</div>
          <p className="text-academic-muted leading-relaxed text-xs">{step.desc}</p>
        </div>
      ))}
    </>
  );
}

interface WelcomeScreenProps {
  t: (key: string) => string;
  loadDemoMode: () => void;
  setQuery: (query: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

function WelcomeScreen({ t, loadDemoMode, setQuery, inputRef }: WelcomeScreenProps) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center max-w-2xl px-4">
        <div className="text-5xl mb-4">🏛️</div>
        <h2 className="text-xl sm:text-2xl font-bold text-academic-heading mb-2">{t('graphrag.welcomeTitle')}</h2>
        <p className="text-sm sm:text-base text-academic-muted mb-6">{t('graphrag.welcomeSubtitle')}</p>

        <SmartQuerySuggestions
          currentQuery=""
          onSuggestionClick={(suggestion: string) => {
            setQuery(suggestion);
            inputRef.current?.focus();
          }}
          className="mb-6"
        />

        <button onClick={loadDemoMode} className="text-sm text-primary-600 hover:text-primary-700 underline">
          {t('graphrag.tryDemo')}
        </button>
      </div>
    </div>
  );
}

interface QueryInputProps {
  t: (key: string) => string;
  query: string;
  setQuery: (query: string) => void;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

function QueryInput({ t, query, setQuery, loading, streaming, error, onSubmit, onCancel, inputRef }: QueryInputProps) {
  return (
    <ShineBorder
      color={loading || streaming ? ["#A07CFE", "#FE8FB5", "#FFBE7B"] : ["#D4D4D4"]}
      duration={loading || streaming ? 3 : 0}
      className={`w-full bg-white/90 backdrop-blur-xl rounded-2xl border shadow-lg ${loading || streaming ? 'animate-pulse' : ''}`}
    >
      {error && (
        <div className="px-4 py-2 text-xs sm:text-sm text-red-600 bg-red-50 border-b border-red-100">{error}</div>
      )}
      <form onSubmit={onSubmit} className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('graphrag.placeholder')}
          className="w-full px-4 sm:px-6 py-3 sm:py-4 pr-24 sm:pr-32 bg-transparent rounded-xl focus:outline-none text-base sm:text-lg"
          disabled={loading || streaming}
        />
        {streaming ? (
          <button
            type="button"
            onClick={onCancel}
            className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 px-3 sm:px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-xs sm:text-sm"
          >
            {t('graphrag.stop')}
          </button>
        ) : (
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 px-3 sm:px-5 py-1.5 sm:py-2 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-lg hover:shadow-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm"
          >
            {loading ? t('graphrag.thinking') : t('graphrag.ask')}
          </button>
        )}
      </form>
    </ShineBorder>
  );
}
