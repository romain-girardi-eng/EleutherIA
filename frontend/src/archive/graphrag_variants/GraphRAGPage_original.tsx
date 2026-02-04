import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import Cookies from 'js-cookie';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import AuthModal from '../components/AuthModal';
import { ShineBorder } from '../components/ui/shine-border';
import { GradientButton } from '../components/ui/gradient-button';
import { AuroraBackground } from '../components/ui/aurora-background';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import NodeDetailPanel from '../components/NodeDetailPanel';
import { CitationPreview } from '../components/ui/citation-preview';
import { ColdStartLoaderMinimal } from '../components/ColdStartLoader';
import { StreamingLoader, StreamingOverlay, GeneratingIndicator } from '../components/ui/streaming-loader';
import { ReasoningPathVisualizer } from '../components/graphrag/ReasoningPathVisualizer';
import { ThinkingProcessPanel, ThinkingProcessCompact } from '../components/graphrag/ThinkingProcessPanel';
import { ConversationSidebar, type Conversation } from '../components/graphrag/ConversationSidebar';
import { SmartQuerySuggestions } from '../components/SmartQuerySuggestions';
import { ArgumentMapper } from '../components/ArgumentMapper';
import { ConceptEvolutionTimeline } from '../components/ConceptEvolutionTimeline';
import { CitationGenerator } from '../components/CitationGenerator';
import { AnswerQualityMetrics } from '../components/AnswerQualityMetrics';
import { WorkTextLink } from '../components/WorkTextLink';
import { CitationRenderer, SourcesPanel } from '../components/CitationRenderer';
import BibliographyPanel from '../components/BibliographyPanel';
import EvidenceChainPanel from '../components/EvidenceChainPanel';
import { VerifiedPassageDisplay } from '../components/graphrag/VerifiedPassageDisplay';
import type { GraphRAGResponse, GraphRAGStreamEvent, GraphRAGChatMessage, KGNode } from '../types';
import type { ReasoningStep } from '../types/graphrag';
import {
  mockGraphRAGResponse,
  mockReasoningSteps,
  // mockQualityMetrics,
  // mockArgumentMapping,
  // mockConceptEvolution
} from '../data/mockGraphRAGData';

export default function GraphRAGPage() {
  const { t } = useTranslation();
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
  const inputRef = useRef<HTMLInputElement>(null);

  const { isAuthenticated } = useAuth();

  // Advanced settings
  const [semanticK, setSemanticK] = useState(10);
  const [graphDepth, setGraphDepth] = useState(2);
  const [maxContext, setMaxContext] = useState(15);
  const [useStreaming, setUseStreaming] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const enhancedMode = true; // Always use enhanced mode

  // Academic mode settings
  const [academicMode, setAcademicMode] = useState(false);
  const [rigorLevel, setRigorLevel] = useState<'standard' | 'high' | 'maximum'>('high');
  const [citationStyle, setCitationStyle] = useState<'chicago' | 'apa' | 'harvard'>('chicago');
  const [showHowItWorks, setShowHowItWorks] = useState(false); // Collapsible How It Works
  const [showBenefits, setShowBenefits] = useState(false); // Start collapsed to prevent layout issues
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAIGenerating, setShowAIGenerating] = useState(false);

  // NEW: Conversation memory state
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // NEW: Thinking mode state (Kimi K2)
  const [useThinking, setUseThinking] = useState(false);
  const [streamedThinking, setStreamedThinking] = useState('');
  const [thinkingComplete, setThinkingComplete] = useState(false);

  // Dynamic KG stats state
  const [kgStats, setKgStats] = useState({
    nodes: 0,
    edges: 0,
    sources: 0,
    hierarchyLayers: 3  // HiIndex architectural constant (local, intermediate, global)
  });

  // Fetch KG stats on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch KG stats (nodes, edges)
        const kgStatsResponse = await apiClient.getKGStats();
        // Fetch works stats (sources/citations)
        const worksStatsResponse = await apiClient.getWorksStats();

        setKgStats({
          nodes: kgStatsResponse.totalNodes || 0,
          edges: kgStatsResponse.totalEdges || 0,
          sources: worksStatsResponse.total_passages || 0,
          hierarchyLayers: 3
        });
      } catch (err) {
        console.error('Failed to fetch KG stats:', err);
        // Keep default values on error
      }
    };

    fetchStats();
  }, []);

  // Scroll to bottom when messages change - only during streaming
  useEffect(() => {
    if (streaming) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamedAnswer, streaming]);

  // Cleanup abort controller and streaming on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  // NEW: Load conversations when authenticated
  const loadConversations = useCallback(async () => {
    if (!isAuthenticated) return;

    setConversationsLoading(true);
    try {
      const response = await apiClient.listConversations(50, 0);
      if (response.success) {
        setConversations(response.conversations);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setConversationsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // NEW: Create new conversation
  const handleNewConversation = async () => {
    setConversationId(null);
    setMessages([]);
    setStreamedAnswer('');
    setStreamedThinking('');
    setThinkingComplete(false);
    setReasoningSteps([]);
    setCurrentQuery('');
  };

  // NEW: Select existing conversation
  const handleSelectConversation = async (id: string) => {
    setConversationId(id);
    setStreamedAnswer('');
    setStreamedThinking('');
    setThinkingComplete(false);
    setLoading(true);

    try {
      const response = await apiClient.getConversationMessages(id);
      if (response.success) {
        // Convert messages to GraphRAGChatMessage format
        const loadedMessages: GraphRAGChatMessage[] = response.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          citations: msg.citations,
          reasoning_path: msg.reasoning_path,
          thinking_process: msg.thinking_process,
          tokens_used: msg.tokens_used,
          llm_provider: msg.llm_provider,
          llm_model: msg.llm_model,
          timestamp: new Date(msg.created_at),
        }));
        setMessages(loadedMessages);
      }
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
      setError('Failed to load conversation');
    } finally {
      setLoading(false);
    }
  };

  // NEW: Delete conversation
  const handleDeleteConversation = async (id: string) => {
    try {
      const response = await apiClient.deleteConversation(id);
      if (response.success) {
        // Remove from list
        setConversations((prev) => prev.filter((c) => c.conversation_id !== id));
        // Clear if active
        if (conversationId === id) {
          handleNewConversation();
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // Demo Mode - Load mock data without authentication
  const loadDemoMode = () => {
    const demoMessage: GraphRAGChatMessage = {
      role: 'user',
      content: mockGraphRAGResponse.query,
      timestamp: new Date()
    };

    // NOTE: Source texts should come from the actual database
    // For demo purposes only - DO NOT USE FABRICATED TEXTS IN PRODUCTION
    const citationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};

    // Transform mock data to match expected structure
    const assistantMessage: GraphRAGChatMessage = {
      role: 'assistant',
      content: mockGraphRAGResponse.answer,
      timestamp: new Date(),
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

    // Check authentication first
    if (!isAuthenticated) {
      setPendingQuery(query.trim());
      setShowAuthModal(true);
      return;
    }

    // Proceed with authenticated query
    await processQuery(query.trim());
  };

  const processQuery = useCallback(async (queryText: string) => {
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
  // Note: handleStreamingQuery and handleStandardQuery are recreated on each render
  // but they don't cause issues since they're only called, not rendered
  // Including them would cause unnecessary memoization overhead
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useStreaming]);

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
  }, [location.state, isAuthenticated, processQuery]);

  const handleAuthSuccess = () => {
    if (pendingQuery) {
      processQuery(pendingQuery);
      setPendingQuery(null);
    }
  };

  const handleStandardQuery = async (queryText: string) => {
    setLoading(true);

    try {
      // Create conversation if first message and none exists (mirror streaming behavior)
      let activeConversationId = conversationId;
      if (!activeConversationId && isAuthenticated) {
        try {
          const convResponse = await apiClient.createConversation({
            settings: {
              semantic_k: semanticK,
              graph_depth: graphDepth,
              max_context: maxContext,
              academic_mode: academicMode,
              rigor_level: rigorLevel,
              citation_style: citationStyle,
            },
          });
          if (convResponse.success) {
            activeConversationId = convResponse.conversation.conversation_id;
            setConversationId(activeConversationId);
            console.log('[GraphRAG] Created conversation for standard query:', activeConversationId);
          }
        } catch (err) {
          console.error('[GraphRAG] Failed to create conversation:', err);
          // Continue without conversation - degraded experience but still works
        }
      }

      // Use advanced endpoint when academic mode is enabled
      const queryParams = {
        query: queryText,
        semantic_k: semanticK,
        graph_depth: graphDepth,
        max_context: maxContext,
        enhanced_mode: enhancedMode,  // Include enhanced mode
        conversation_id: activeConversationId || undefined,  // Pass conversation context
        ...(academicMode && {
          academic_mode: true,
          rigor_level: rigorLevel,
          citation_style: citationStyle,
        }),
      };

      const response = academicMode
        ? await apiClient.graphragQueryAdvanced(queryParams)
        : await apiClient.graphragQuery(queryParams);

      const assistantMessage: GraphRAGChatMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        reasoning_path: response.reasoning_path,
        tokens_used: response.tokens_used,
        llm_provider: response.llm_provider,
        llm_model: response.llm_model,
        timestamp: new Date(),
        graphrag_response: response, // Store full response for academic features
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Refresh conversations list if we created one
      if (activeConversationId && isAuthenticated) {
        loadConversations();
      }
    } catch (err: unknown) {
      console.error('GraphRAG error:', err);
      setError(err instanceof Error ? err.message : 'Failed to get answer');
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
    console.log('[GraphRAG] Starting streaming query:', queryText);
    console.log('[GraphRAG] Current conversationId state:', conversationId);
    console.log('[GraphRAG] isAuthenticated:', isAuthenticated);
    setStreaming(true);
    setStreamedAnswer('');
    setStreamedThinking('');  // NEW: Reset thinking
    setThinkingComplete(false);  // NEW: Reset thinking complete
    setStreamStatus('Connecting to server... (This may take 30-60s if the server is waking up)');
    initializeReasoningSteps(queryText);

    // NEW: Create conversation if first message and none exists
    let activeConversationId = conversationId;
    console.log('[GraphRAG] activeConversationId (from state):', activeConversationId);
    if (!activeConversationId && isAuthenticated) {
      console.log('[GraphRAG] No conversation exists, creating new one...');
      try {
        const response = await apiClient.createConversation({
          settings: {
            semantic_k: semanticK,
            graph_depth: graphDepth,
            max_context: maxContext,
            use_thinking: useThinking,
            academic_mode: academicMode,
            rigor_level: rigorLevel,
            citation_style: citationStyle,
          },
        });
        if (response.success) {
          activeConversationId = response.conversation.conversation_id;
          console.log('[GraphRAG] Created conversation:', activeConversationId);
          setConversationId(activeConversationId);
        }
      } catch (err) {
        console.error('Failed to create conversation:', err);
        // Continue without conversation tracking
      }
    } else if (activeConversationId) {
      console.log('[GraphRAG] Using existing conversation:', activeConversationId);
    } else {
      console.log('[GraphRAG] No conversation (not authenticated or no ID)');
    }

    try {
      const token = Cookies.get('auth_token');
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      console.log('[GraphRAG] API URL:', apiUrl, 'Token present:', !!token, 'Thinking:', useThinking);

      // Create abort controller for cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Add timeout for connection (2 minutes to handle cold starts)
      const timeoutId = setTimeout(() => {
        abortController.abort();
      }, 120000); // 120 seconds

      // Build query parameters for GET request with configurable settings
      const params = new URLSearchParams({
        query: queryText,
        semantic_k: semanticK.toString(),
        graph_depth: graphDepth.toString(),
        max_context: maxContext.toString(),
        use_thinking: useThinking.toString(),  // NEW: Pass thinking mode
      });

      // NEW: Add conversation_id if available
      if (activeConversationId) {
        params.set('conversation_id', activeConversationId);
        console.log('[GraphRAG] Added conversation_id to params:', activeConversationId);
      } else {
        console.log('[GraphRAG] No conversation_id to add to params');
      }

      console.log('[GraphRAG] Final request params:', params.toString());
      const response = await fetch(`${apiUrl}/api/graphrag/query/stream?${params.toString()}`, {
        method: 'GET',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        signal: abortController.signal,
      });

      clearTimeout(timeoutId); // Clear timeout once connected

      console.log('[GraphRAG] Response status:', response.status, response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[GraphRAG] Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      console.log('[GraphRAG] Got reader:', !!reader);

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
                  setStreamStatus(data.message || t('common.loading'));

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
                    setShowAIGenerating(true); // Show AI loader when synthesis starts
                  }
                  break;

                case 'nodes':
                  // Handle nodes event from backend (contains nodes_found, edges_found)
                  // Nodes info is now in the stream, no need to log
                  break;

                case 'citations':
                  // Handle citations event from backend
                  // Citations will be in final response
                  break;

                case 'thinking_chunk':
                  // NEW: Handle thinking process streaming
                  console.log('[GraphRAG] Received thinking_chunk:', (data.data as string)?.length, 'chars');
                  setStreamedThinking((prev) => prev + (data.data || ''));
                  setStreamStatus('Kimi K2 is reasoning...');
                  break;

                case 'thinking_complete':
                  // NEW: Mark thinking as complete
                  console.log('[GraphRAG] Thinking complete');
                  setThinkingComplete(true);
                  setStreamStatus('Thinking complete, generating answer...');
                  break;

                case 'answer_chunk':
                  fullAnswer += data.data;
                  setStreamedAnswer(fullAnswer);
                  // Mark synthesis as active when answer starts streaming
                  if (!fullAnswer) {
                    updateReasoningStep(4, 'active');
                  }
                  setShowAIGenerating(false); // Hide AI loader when answer starts
                  break;

                case 'complete':
                  finalResponse = data.data as GraphRAGResponse;
                  // Mark all steps complete
                  updateReasoningStep(5, 'complete');
                  setShowAIGenerating(false); // Ensure loader is hidden
                  // Update conversation_id from backend response if we have one
                  if (finalResponse?.conversation_id && !conversationId) {
                    console.log('[GraphRAG] Setting conversationId from response:', finalResponse.conversation_id);
                    setConversationId(finalResponse.conversation_id);
                  }
                  // NEW: Refresh conversations list
                  if (activeConversationId) {
                    loadConversations();
                  }
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
        // Handle Cloudflare backend response (sources as array) vs FastAPI backend (citations object)
        const citations = finalResponse.citations || {
          ancient_sources: finalResponse.sources || [],
          modern_scholarship: []
        };

        // Transform reasoning_path nodes into proper SourceCitation format
        // This fixes the "Unknown" sources issue by using actual node data
        const reasoningPath = finalResponse.reasoning_path;
        if (reasoningPath && !finalResponse.sources) {
          // Starting nodes have semantic_score, expanded nodes don't
          const startingNodes = (reasoningPath.starting_nodes || []).map((node, index) => ({
            id: index + 1,
            nodeId: node.id,
            nodeLabel: node.label || 'Unknown',
            nodeType: node.type || 'Unknown',
            metadata: {
              confidence: (node as { semantic_score?: number }).semantic_score || undefined
            }
          }));
          const expandedNodes = (reasoningPath.expanded_nodes || []).map((node, index) => ({
            id: startingNodes.length + index + 1,
            nodeId: node.id,
            nodeLabel: node.label || 'Unknown',
            nodeType: node.type || 'Unknown',
            metadata: {}
          }));
          // Create properly formatted sources from reasoning path nodes
          finalResponse.sources = [...startingNodes, ...expandedNodes];
        }

        // Fetch citation texts for hover tooltips
        const allCitations = [
          ...(citations.ancient_sources || []),
          ...(citations.modern_scholarship || [])
        ];

        // Import citation service only if we have citations to fetch
        const formattedCitationTexts: Record<string, { original: string; originalLanguage: string; translation: string }> = {};
        if (allCitations.length > 0) {
          try {
            const { fetchCitationPassages } = await import('../services/citationService');
            const citationTexts = await fetchCitationPassages(allCitations);

            // Convert citation passages to the format expected by CitationPreview
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
          citations: citations,
          reasoning_path: finalResponse.reasoning_path,
          thinking_process: finalResponse.thinking_process || streamedThinking || undefined,  // NEW
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
          thinking_process: streamedThinking || undefined,  // NEW
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }

      setStreaming(false);
      setStreamedAnswer('');
      setStreamedThinking('');  // NEW: Reset thinking
      setThinkingComplete(false);  // NEW: Reset thinking complete
      setStreamStatus('');
      setShowAIGenerating(false); // Hide AI loader
    } catch (err: unknown) {
      console.error('[GraphRAG] Streaming error caught:', err);
      console.error('[GraphRAG] Error type:', err instanceof Error ? err.constructor.name : typeof err);
      console.error('[GraphRAG] Error message:', err instanceof Error ? err.message : String(err));

      // Check if it was an abort (timeout or user cancel)
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('[GraphRAG] Setting abort error');
        setError(t('errors.networkErrorDesc'));
      } else {
        const errorMsg = err instanceof Error ? err.message : t('common.error');
        console.log('[GraphRAG] Setting error:', errorMsg);
        setError(errorMsg);
      }

      setStreaming(false);
      setStreamedAnswer('');
      setStreamStatus('');
      setShowAIGenerating(false); // Hide AI loader
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
    setShowAIGenerating(false); // Hide AI loader when stopping
  };

  const handleNodeClick = async (nodeId: string) => {
    // Guard against invalid node IDs
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) {
      console.warn('Invalid node ID:', nodeId);
      return;
    }

    // Check if nodeId is a UUID (passage ID from text_embeddings or vector database)
    // UUIDs have format: 8-4-4-4-12 hex characters
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidPattern.test(nodeId) || nodeId.startsWith('passage_')) {
      // This is a passage reference, not a KG node - skip API call
      console.info('Source is a passage reference (UUID), skipping KG lookup:', nodeId);
      return;
    }

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
    <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
      <div className="relative min-h-screen overflow-hidden pt-12">
        {/* AI Loader - shows during AI generation phase as inline element */}
        {showAIGenerating && (
          <StreamingOverlay
            status="Synthesizing Answer"
            substatus="Analyzing knowledge graph context..."
          />
        )}

      {/* Main content with elevated z-index - accounting for fixed header */}
      <div className="relative z-10 flex flex-col lg:flex-row gap-3 lg:gap-4 p-4 lg:p-6 min-h-0 h-[calc(100vh-5rem)] lg:h-[calc(100vh-6rem)]">
      {/* Left Sidebar - Title & Settings (Desktop) */}
      <div className="hidden lg:flex lg:flex-col lg:w-48 xl:w-56 gap-3 flex-shrink-0">
        {/* Title Section */}
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
            <Button
              onClick={() => setShowSettings(!showSettings)}
              variant="outline"
              size="sm"
              fullWidth
            >
              ⚙️ {t('graphrag.settings')}
            </Button>
            {/* Conversation History Toggle */}
            {isAuthenticated && (
              <Button
                onClick={() => setShowSidebar(!showSidebar)}
                variant={showSidebar ? "default" : "outline"}
                size="sm"
                fullWidth
                className="mt-2"
              >
                💬 {showSidebar ? 'Hide' : 'Show'} History
              </Button>
            )}
            <p className="mt-3 text-[10px] leading-relaxed text-academic-muted">
              {t('graphrag.basedOn')}
            </p>
          </CardContent>
        </Card>

        {/* Stats Card */}
        <Card variant="elevated" padding="md" className="bg-gradient-to-br from-primary-50 via-blue-50 to-indigo-50 border-primary-200 overflow-hidden relative">
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
            <div className="text-xs font-semibold text-primary-800 uppercase tracking-wider mb-1.5">{t('graphrag.snapshot')}</div>
            <div className="grid grid-cols-1 gap-2 text-sm">
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">{kgStats.nodes.toLocaleString()}</div>
                <div className="text-xs text-academic-muted font-medium">{t('kg.nodes')}</div>
              </div>
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">{kgStats.edges.toLocaleString()}</div>
                <div className="text-xs text-academic-muted font-medium">{t('kg.edges')}</div>
              </div>
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">{kgStats.sources.toLocaleString()}</div>
                <div className="text-xs text-academic-muted font-medium">{t('graphrag.sources')}</div>
              </div>
              <div className="py-1.5 px-2 bg-white/60 rounded-lg">
                <div className="text-2xl font-bold text-primary-600 mb-0.5">{kgStats.hierarchyLayers}</div>
                <div className="text-xs text-academic-muted font-medium">Hierarchy Layers (HiIndex)</div>
              </div>
            </div>
          </div>
        </Card>

        {/* How HiRAG Works Section - Moved from right sidebar */}
        <div className="academic-card bg-gradient-to-br from-blue-50/80 via-indigo-50/80 to-purple-50/80 backdrop-blur-xl border-primary-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <button
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="w-full flex items-center justify-between text-left hover:opacity-80 transition-all group"
          >
            <h3 className="font-semibold text-base xl:text-lg text-primary-900 flex items-center gap-2 group-hover:text-primary-700 transition-colors">
              <svg className="w-5 h-5 xl:w-6 xl:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              How HiRAG Works
            </h3>
            <span className="text-primary-700 text-sm font-medium group-hover:scale-110 transition-transform">
              {showHowItWorks ? '▼' : '▶'}
            </span>
          </button>
          {showHowItWorks && <div className="mt-3 pt-3 border-t border-primary-200"></div>}
          {showHowItWorks && (
            <div className="text-xs space-y-2.5 max-h-96 overflow-y-auto pr-2">
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">1. HiIndex Hierarchy</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  The knowledge graph is clustered into layered communities so HiRAG can jump between global themes and local evidence.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">2. Local Retrieval</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Queries seed level-2 entities via embedding search, anchoring the answer in concrete people, works, and arguments.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">3. Bridge Mode</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Cross-community connectors are added to complete multi-hop reasoning paths and surface interdisciplinary touchpoints.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">4. Global Summaries</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Level-0 and level-1 digests blend with local snippets to deliver thematic framing without overwhelming the context window.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">5. LLM Synthesis</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Gemini assembles the layered bundle into a narrative answer, tagging which hierarchy levels contributed evidence.
                </p>
              </div>
              <div className="bg-white/80 rounded-lg p-2.5 border border-blue-100">
                <div className="font-semibold text-primary-800 mb-1.5">6. Evidence Tracking</div>
                <p className="text-academic-muted leading-relaxed text-xs">
                  Citations, reasoning paths, and bridge nodes are logged for auditability and follow-up exploration.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Why It's Brilliant Section - Moved from right sidebar */}
        <div className="academic-card bg-gradient-to-br from-green-50/80 via-emerald-50/80 to-teal-50/80 backdrop-blur-xl border-green-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
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

        {/* Last Response Stats - Moved from right sidebar */}
        {messages.length > 0 && messages[messages.length - 1].role === 'assistant' && (
          <div className="academic-card bg-gradient-to-br from-amber-50/80 via-orange-50/80 to-yellow-50/80 backdrop-blur-xl border-amber-200/50 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 animate-in fade-in-0 slide-in-from-right-2 duration-500">
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

      {/* Mobile Header */}
      <Card variant="default" padding="md" className="lg:hidden mb-2 flex-shrink-0">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-xl font-serif font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
            {t('graphrag.title')}
          </h1>
          <GradientButton
            onClick={() => setShowSettings(!showSettings)}
            variant="default"
            size="sm"
          >
            ⚙️ Settings
          </GradientButton>
        </div>
      </Card>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col lg:h-full min-w-0">

        {/* Settings Modal Overlay */}
        {showSettings && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowSettings(false)}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-r from-gray-900 to-gray-800 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <h3 className="text-xl font-bold">{t('graphrag.searchSettings')}</h3>
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
              Adjust how HiRAG balances local retrieval, bridge expansion, and global summaries. The defaults work well for most queries.
            </p>

            <div className="space-y-5">
              {/* Search Breadth */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Search Breadth (Local Seeds)
                  </label>
                  <span className="text-sm font-semibold text-gray-900">{semanticK} nodes</span>
                </div>
                <input
                  type="range"
                  value={semanticK}
                  onChange={(e) => setSemanticK(Number(e.target.value))}
                  min={5}
                  max={20}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-900"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Narrow</span>
                  <span className="text-xs text-gray-500">Broad</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How many level-2 entities HiRAG selects before climbing the hierarchy.
                </p>
              </div>

              {/* Connection Depth */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Connection Depth (Bridge Reach)
                  </label>
                  <span className="text-sm font-semibold text-gray-900">{graphDepth} levels</span>
                </div>
                <input
                  type="range"
                  value={graphDepth}
                  onChange={(e) => setGraphDepth(Number(e.target.value))}
                  min={1}
                  max={3}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-900"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Shallow</span>
                  <span className="text-xs text-gray-500">Deep</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How many hierarchy levels HiRAG traverses when stitching bridge nodes into the answer.
                </p>
              </div>

              {/* Context Size */}
              <div className="border-b border-gray-100 pb-5">
                <div className="flex items-baseline justify-between mb-3">
                  <label className="text-sm font-medium text-gray-900">
                    Context Size (Global Context Budget)
                  </label>
                  <span className="text-sm font-semibold text-gray-900">{maxContext} nodes</span>
                </div>
                <input
                  type="range"
                  value={maxContext}
                  onChange={(e) => setMaxContext(Number(e.target.value))}
                  min={10}
                  max={25}
                  step={1}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-gray-900"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Concise</span>
                  <span className="text-xs text-gray-500">Detailed</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  How much blended evidence (local + summaries) HiRAG keeps in the prompt for synthesis.
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
                    className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-gray-900 relative transition-colors
                    before:content-[''] before:absolute before:top-0.5 before:left-0.5 before:w-5 before:h-5 before:bg-white before:rounded-full before:transition-transform
                    checked:before:translate-x-5"
                  />
                </label>
              </div>

              {/* Academic Mode Toggle */}
              <div className="border-b border-gray-100 pb-5">
                <label className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <span className="text-sm font-medium text-gray-900 flex items-center gap-2">
                      🎓 Academic Mode
                    </span>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Enhanced scholarly rigor with confidence scores, CTS URNs, and formatted bibliography
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={academicMode}
                    onChange={(e) => setAcademicMode(e.target.checked)}
                    className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-gray-900 relative transition-colors
                    before:content-[''] before:absolute before:top-0.5 before:left-0.5 before:w-5 before:h-5 before:bg-white before:rounded-full before:transition-transform
                    checked:before:translate-x-5"
                  />
                </label>

                {/* Academic Mode Sub-Settings */}
                {academicMode && (
                  <div className="mt-4 ml-4 space-y-4 pl-4 border-l-2 border-primary-200">
                    {/* Rigor Level */}
                    <div>
                      <label className="text-xs font-medium text-gray-700 block mb-2">
                        Rigor Level
                      </label>
                      <select
                        value={rigorLevel}
                        onChange={(e) => setRigorLevel(e.target.value as 'standard' | 'high' | 'maximum')}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                      >
                        <option value="standard">Standard - Balanced scholarly approach</option>
                        <option value="high">High - Enhanced citation density</option>
                        <option value="maximum">Maximum - Maximum scholarly detail</option>
                      </select>
                    </div>

                    {/* Citation Style */}
                    <div>
                      <label className="text-xs font-medium text-gray-700 block mb-2">
                        Citation Style
                      </label>
                      <select
                        value={citationStyle}
                        onChange={(e) => setCitationStyle(e.target.value as 'chicago' | 'apa' | 'harvard')}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                      >
                        <option value="chicago">Chicago - Humanities standard</option>
                        <option value="apa">APA - Social sciences</option>
                        <option value="harvard">Harvard - UK institutions</option>
                      </select>
                    </div>

                    <div className="text-xs text-gray-600 bg-primary-50 p-3 rounded-lg">
                      <p className="font-medium mb-1">Academic Mode Features:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Confidence scores for all citations</li>
                        <li>CTS URNs for canonical references</li>
                        <li>Evidence chains linking claims to sources</li>
                        <li>Formatted bibliography (Chicago/BibTeX)</li>
                        <li>Epistemic hedging in scholarly style</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              {/* Thinking Mode Toggle (Kimi K2) - Very pale aurora palette */}
              <div className="border-b border-gray-100 pb-5">
                <label className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <span className="text-sm font-medium text-gray-900 flex items-center gap-2">
                      <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Thinking Mode
                      <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-500 border border-indigo-100">Kimi K2</span>
                    </span>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Show step-by-step reasoning process before generating answers
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={useThinking}
                    onChange={(e) => setUseThinking(e.target.checked)}
                    className="w-11 h-6 bg-gray-200 rounded-full appearance-none cursor-pointer checked:bg-indigo-400 relative transition-colors
                    before:content-[''] before:absolute before:top-0.5 before:left-0.5 before:w-5 before:h-5 before:bg-white before:rounded-full before:transition-transform
                    checked:before:translate-x-5"
                  />
                </label>

                {/* Thinking Mode Info - Very pale aurora palette */}
                {useThinking && (
                  <div className="mt-4 ml-4 pl-4 border-l-2 border-indigo-100">
                    <div className="text-xs text-slate-500 bg-indigo-50/50 backdrop-blur-sm p-3 rounded-lg border border-indigo-50">
                      <p className="font-medium mb-1 text-indigo-500">Thinking Mode Features:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Uses Kimi K2 model with extended reasoning</li>
                        <li>Shows internal thought process in real-time</li>
                        <li>Better for complex philosophical questions</li>
                        <li>May take longer but provides deeper analysis</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              {/* Preset Buttons */}
              <div className="pt-2">
                <p className="text-xs font-medium text-gray-500 mb-3">Quick Presets</p>
                <div className="grid grid-cols-3 gap-2">
                  <GradientButton
                    onClick={() => {
                      setSemanticK(8);
                      setGraphDepth(2);
                      setMaxContext(12);
                    }}
                    variant="default"
                    size="sm"
                    className="text-xs"
                  >
                    Fast
                  </GradientButton>
                  <GradientButton
                    onClick={() => {
                      setSemanticK(10);
                      setGraphDepth(2);
                      setMaxContext(15);
                    }}
                    variant="academic"
                    size="sm"
                    className="text-xs"
                  >
                    Balanced
                  </GradientButton>
                  <GradientButton
                    onClick={() => {
                      setSemanticK(15);
                      setGraphDepth(3);
                      setMaxContext(20);
                    }}
                    variant="default"
                    size="sm"
                    className="text-xs"
                  >
                    Deep
                  </GradientButton>
                </div>
              </div>
            </div>
          </div>

          {/* Modal Footer */}
          <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-2xl border-t border-gray-200 flex justify-end">
            <GradientButton
              onClick={() => setShowSettings(false)}
              variant="highlight"
              size="md"
            >
              {t('graphrag.done')}
            </GradientButton>
          </div>
        </div>
        </div>
        )}

        {/* Conversation Sidebar - Shows when authenticated */}
        {isAuthenticated && showSidebar && (
          <div className="hidden lg:block flex-shrink-0">
            <ConversationSidebar
              conversations={conversations}
              activeConversationId={conversationId}
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              onDeleteConversation={handleDeleteConversation}
              onRefreshConversations={loadConversations}
              isLoading={conversationsLoading}
              isCollapsed={sidebarCollapsed}
              onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
          </div>
        )}

        {/* Messages Area - Enhanced glass morphism with animated shine border */}
        <ShineBorder
          className="flex-1 w-full !p-0 bg-white/70 dark:bg-black/70 backdrop-blur-2xl min-w-0 mb-2 overflow-hidden shadow-2xl transition-all duration-500 hover:bg-white/75 dark:hover:bg-black/75"
          borderRadius={16}
          borderWidth={1}
          duration={loading || streaming ? 8 : 14}
          color={["#e0e7ff", "#dbeafe", "#ede9fe"]}
        >
          <div className="overflow-y-auto p-3 sm:p-4 lg:p-6 space-y-4 h-full relative">
            {/* Animated gradient overlay when querying */}
            {(loading || streaming) && (
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-t from-purple-500/5 via-transparent to-blue-500/5 animate-pulse" />
              </div>
            )}
            {messages.length === 0 && !streaming && (
            <div className="py-4 lg:py-12">
              <div className="text-center mb-4 lg:mb-10">
                <div className="text-5xl lg:text-7xl mb-3 lg:mb-6">💬</div>
                <h2 className="text-2xl lg:text-4xl font-serif font-semibold mb-2 lg:mb-4">
                  Ask <span className="bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent font-serif">EleutherIA</span>
                </h2>
                <p className="text-sm lg:text-lg text-academic-muted mb-4 px-4 lg:px-8 leading-relaxed max-w-2xl mx-auto">
                  {t('graphrag.description')}
                </p>

                {/* Demo Mode Button */}
                <div className="flex justify-center mb-3">
                  <GradientButton
                    onClick={loadDemoMode}
                    variant="academic"
                    size="md"
                    icon={
                      <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    }
                  >
                    {t('graphrag.tryDemo')}
                  </GradientButton>
                </div>
              </div>

              {/* Smart Query Suggestions Toggle - Hidden on small mobile */}
              {!showSuggestions ? (
                <div className="hidden sm:flex justify-center">
                  <GradientButton
                    onClick={() => setShowSuggestions(true)}
                    variant="academic"
                    size="md"
                    icon={
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    }
                  >
                    Suggestions
                  </GradientButton>
                </div>
              ) : (
                <div className="space-y-2 hidden sm:block">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">{t('graphrag.suggestions')}</h3>
                    <button
                      onClick={() => setShowSuggestions(false)}
                      className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                    >
                      {t('graphrag.hide')}
                    </button>
                  </div>
                  <SmartQuerySuggestions
                    currentQuery={query}
                    onSuggestionClick={(suggestion) => {
                      setQuery(suggestion);
                      setShowSuggestions(false);
                      setTimeout(() => {
                        inputRef.current?.focus();
                      }, 100);
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className="space-y-3">
              <MessageBubble message={message} onNodeClick={handleNodeClick} />

              {/* Show Verified Passages with original Greek/Latin for ALL assistant messages */}
              {message.role === 'assistant' && message.graphrag_response?.verified_passages && message.graphrag_response.verified_passages.length > 0 && (
                <VerifiedPassageDisplay
                  passages={message.graphrag_response.verified_passages}
                  maxInitialDisplay={3}
                />
              )}

              {/* Show Academic Mode Panels for assistant messages */}
              {message.role === 'assistant' && academicMode && message.graphrag_response && (
                <>
                  {/* Evidence Chain Panel */}
                  {message.graphrag_response.evidence_chains && (
                    <EvidenceChainPanel
                      evidenceChains={message.graphrag_response.evidence_chains}
                    />
                  )}

                  {/* Bibliography Panel */}
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

              {/* Thinking Process Panel (Kimi K2) */}
              {useThinking && streamedThinking && (
                <ThinkingProcessPanel
                  thinking={streamedThinking}
                  isStreaming={!thinkingComplete}
                  isComplete={thinkingComplete}
                />
              )}

              {/* Streamed Answer - Academic styled with pale aurora */}
              <div className="bg-white/80 backdrop-blur-xl rounded-xl p-4 sm:p-5 lg:p-6 shadow-lg shadow-slate-100/30">
                {/* Show cold start loader if no answer yet and taking a while */}
                {!streamedAnswer && streamStatus.includes('waking') ? (
                  <ColdStartLoaderMinimal isLoading={true} />
                ) : !streamedAnswer ? (
                  <StreamingLoader
                    status={streamStatus}
                    isStreaming={true}
                    step={streamStatus.includes('Searching') ? 'Search' :
                          streamStatus.includes('Travers') ? 'Explore' :
                          streamStatus.includes('context') ? 'Context' :
                          streamStatus.includes('Generat') ? 'Generate' : undefined}
                  />
                ) : (
                  <>
                    {/* Show generating indicator while answer is streaming */}
                    <GeneratingIndicator
                      label="Writing response..."
                      showCursor={true}
                      className="mb-3"
                    />
                    <div className="markdown-content prose prose-base lg:prose-lg max-w-none overflow-x-auto prose-headings:text-primary-800 prose-a:text-primary-600">
                      <ReactMarkdown>{streamedAnswer}</ReactMarkdown>
                    </div>
                  </>
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

        {/* Input Area - Enhanced glass morphism with pale aurora shine */}
        <ShineBorder
          className="w-full !p-0 bg-white/80 dark:bg-black/70 backdrop-blur-2xl min-w-0 flex-shrink-0 shadow-xl shadow-slate-200/30 transition-all duration-500 hover:bg-white/90 dark:hover:bg-black/80"
          borderRadius={12}
          borderWidth={1}
          duration={query.length > 0 ? 8 : 12}
          color={["#e0e7ff", "#dbeafe", "#ede9fe"]}
        >
          <form onSubmit={handleSubmit}>
            <div className="relative flex items-center">
              {/* Animated gradient background when typing */}
              {query.length > 0 && (
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-blue-500/5 to-green-500/5 rounded-xl animate-pulse pointer-events-none" />
              )}
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t('graphrag.placeholder')}
                disabled={loading || streaming}
                autoComplete="off"
                name="query"
                spellCheck="false"
                data-lpignore="true"
                data-form-type="other"
                data-1p-ignore="true"
                role="searchbox"
                aria-label="GraphRAG search query"
                className="w-full pl-3 sm:pl-4 pr-20 sm:pr-24 py-3 sm:py-4 bg-transparent focus:outline-none disabled:opacity-50 text-sm sm:text-base rounded-xl transition-all duration-300 placeholder:text-gray-500/70"
              />
              {streaming ? (
                <button
                  type="button"
                  onClick={stopStreaming}
                  className="absolute right-2 sm:right-3 px-3 sm:px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium whitespace-nowrap transition-all text-xs sm:text-sm"
                >
                  {t('graphrag.stop')}
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="absolute right-2 sm:right-3 px-3 sm:px-5 py-1.5 sm:py-2 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-lg hover:shadow-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap transition-all text-xs sm:text-sm shadow-sm"
                >
                  {loading ? t('graphrag.thinking') : t('graphrag.ask')}
                </button>
              )}
            </div>
          </form>
        </ShineBorder>
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
      message="Please log in to use HiRAG Q&A. This feature uses AI to provide scholarly answers."
    />

    {/* Node Detail Panel */}
    {selectedNode && (
      <NodeDetailPanel
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
      />
    )}
      </div>
    </AuroraBackground>
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
          <strong>HiRAG:</strong> Finds Augustine → traverses to Pelagius (opponent) →
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
          <strong>HiRAG:</strong> Shows how the concept evolved from Aristotle (4th c. BCE) →
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
          <strong>HiRAG:</strong> Retrieves Chrysippus's arguments → follows "refutes" edges to
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
          <strong>HiRAG:</strong> Only uses information from retrieved nodes. Automatically extracts
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
          <strong>HiRAG path:</strong> Aristotle → "influenced" → Alexander of Aphrodisias →
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
    <div className={`${message.role === 'user' ? 'ml-auto max-w-[85%] lg:max-w-2xl' : 'mr-auto max-w-[95%] lg:max-w-full'} animate-in fade-in-0 slide-in-from-bottom-2 duration-500`}>
      <div
        className={`rounded-xl p-4 sm:p-5 lg:p-6 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 ${
          message.role === 'user'
            ? 'bg-gradient-to-br from-gray-900/95 to-gray-800/95 text-white backdrop-blur-xl'
            : 'bg-white/80 backdrop-blur-xl border border-gray-200/50'
        }`}
      >
        {message.role === 'user' ? (
          <p className="text-base sm:text-lg break-words leading-relaxed">{message.content}</p>
        ) : (
          <div className="space-y-3">
            {/* Service indicator badge - shows HiRAG vs GraphRAG */}
            {message.graphrag_response?.service && (
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  message.graphrag_response.service.includes('HiRAG')
                    ? 'bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-800 border border-purple-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200'
                }`}>
                  <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  {message.graphrag_response.service}
                </span>
                {message.graphrag_response.hierarchy_stats && (
                  <span className="text-xs text-gray-500">
                    L0:{message.graphrag_response.hierarchy_stats.level_0_used} | L1:{message.graphrag_response.hierarchy_stats.level_1_used} | L2:{message.graphrag_response.hierarchy_stats.level_2_used}
                  </span>
                )}
              </div>
            )}
            {/* Use CitationRenderer for new citation system if sources are available */}
            {message.graphrag_response?.sources ? (
              <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                <CitationRenderer
                  content={message.content}
                  sources={message.graphrag_response.sources}
                  onNodeClick={onNodeClick}
                />
              </div>
            ) : (
              <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}

            {/* Sources Panel for new citation system */}
            {message.graphrag_response?.sources && message.graphrag_response.sources.length > 0 && (
              <SourcesPanel
                sources={message.graphrag_response.sources}
                evidenceMap={message.graphrag_response.evidenceMap}
                onNodeClick={onNodeClick}
              />
            )}

            {/* Thinking Process (Kimi K2) - Compact view for historical messages */}
            {message.thinking_process && (
              <ThinkingProcessCompact thinking={message.thinking_process} />
            )}

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
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="font-semibold text-blue-900">{node.label}</div>
                                    <WorkTextLink
                                      nodeId={node.id}
                                      nodeType={node.type}
                                      nodeLabel={node.label}
                                      compact={true}
                                    />
                                  </div>
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
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="font-semibold text-gray-900">{node.label}</div>
                                    <WorkTextLink
                                      nodeId={node.id}
                                      nodeType={node.type}
                                      nodeLabel={node.label}
                                      compact={true}
                                    />
                                  </div>
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
                {message.graphrag_response.quality_metrics && (
                  <div className="border-t border-academic-border pt-4">
                    <button
                      onClick={() => setShowQualityMetrics(!showQualityMetrics)}
                      className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-2"
                    >
                      {showQualityMetrics ? '▼' : '▶'} Answer Quality Metrics
                      <span className="text-xs text-gray-500">(Confidence: {message.graphrag_response.quality_metrics.overallQuality}%)</span>
                    </button>
                    {showQualityMetrics && (
                      <div className="mt-4">
                        <AnswerQualityMetrics metrics={message.graphrag_response.quality_metrics} />
                      </div>
                    )}
                  </div>
                )}

                {/* Citation Generator */}
                {message.citations && (
                  <div className="border-t border-academic-border pt-4">
                    <button
                      onClick={() => setShowCitationGenerator(!showCitationGenerator)}
                      className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                    >
                      {showCitationGenerator ? '▼' : '▶'} Export Citations (APA, MLA, Chicago, BibTeX)
                    </button>
                    {showCitationGenerator && message.citations && (
                      <div className="mt-4">
                        <CitationGenerator
                          citations={[
                            ...message.citations.ancient_sources.map((source, i) => ({
                              id: `ancient-${i}`,
                              text: source,
                              source: 'Ancient Source',
                            })),
                            ...message.citations.modern_scholarship.map((source, i) => ({
                              id: `modern-${i}`,
                              text: source,
                              source: 'Modern Scholarship',
                            })),
                          ]}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Argument Mapper */}
                {message.graphrag_response.argument_mapping && (
                  <div className="border-t border-academic-border pt-4">
                    <button
                      onClick={() => setShowArgumentMap(!showArgumentMap)}
                      className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                    >
                      {showArgumentMap ? '▼' : '▶'} Argument Structure Map
                    </button>
                    {showArgumentMap && (
                      <div className="mt-4">
                        <ArgumentMapper argument={message.graphrag_response.argument_mapping} />
                      </div>
                    )}
                  </div>
                )}

                {/* Concept Evolution Timeline */}
                {message.graphrag_response.concept_evolution && (
                  <div className="border-t border-academic-border pt-4">
                    <button
                      onClick={() => setShowConceptEvolution(!showConceptEvolution)}
                      className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
                    >
                      {showConceptEvolution ? '▼' : '▶'} Concept Evolution Timeline
                    </button>
                    {showConceptEvolution && (
                      <div className="mt-4">
                        <ConceptEvolutionTimeline evolution={message.graphrag_response.concept_evolution} />
                      </div>
                    )}
                  </div>
                )}
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
