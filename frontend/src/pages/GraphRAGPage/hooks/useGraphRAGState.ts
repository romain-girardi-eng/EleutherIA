import { useState, useRef, useCallback } from 'react';
import type { GraphRAGChatMessage, KGNode } from '../../../types';
import type { ReasoningStep } from '../../../types/graphrag';

export interface GraphRAGSettings {
  semanticK: number;
  graphDepth: number;
  maxContext: number;
  useStreaming: boolean;
  useThinking: boolean;
  academicMode: boolean;
  rigorLevel: 'standard' | 'high' | 'maximum';
  citationStyle: 'chicago' | 'apa' | 'harvard';
}

export interface KGStats {
  nodes: number;
  edges: number;
  sources: number;
  hierarchyLayers: number;
}

export interface GraphRAGState {
  // Messages
  messages: GraphRAGChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<GraphRAGChatMessage[]>>;

  // Query input
  query: string;
  setQuery: React.Dispatch<React.SetStateAction<string>>;
  currentQuery: string;
  setCurrentQuery: React.Dispatch<React.SetStateAction<string>>;

  // Loading states
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  streaming: boolean;
  setStreaming: React.Dispatch<React.SetStateAction<boolean>>;

  // Streaming state
  streamedAnswer: string;
  setStreamedAnswer: React.Dispatch<React.SetStateAction<string>>;
  streamedThinking: string;
  setStreamedThinking: React.Dispatch<React.SetStateAction<string>>;
  thinkingComplete: boolean;
  setThinkingComplete: React.Dispatch<React.SetStateAction<boolean>>;
  streamStatus: string;
  setStreamStatus: React.Dispatch<React.SetStateAction<string>>;

  // Error handling
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;

  // UI state
  showAuthModal: boolean;
  setShowAuthModal: React.Dispatch<React.SetStateAction<boolean>>;
  showSettings: boolean;
  setShowSettings: React.Dispatch<React.SetStateAction<boolean>>;
  showSuggestions: boolean;
  setShowSuggestions: React.Dispatch<React.SetStateAction<boolean>>;
  showAIGenerating: boolean;
  setShowAIGenerating: React.Dispatch<React.SetStateAction<boolean>>;
  showHowItWorks: boolean;
  setShowHowItWorks: React.Dispatch<React.SetStateAction<boolean>>;
  showBenefits: boolean;
  setShowBenefits: React.Dispatch<React.SetStateAction<boolean>>;

  // Pending query for auth flow
  pendingQuery: string | null;
  setPendingQuery: React.Dispatch<React.SetStateAction<string | null>>;

  // Selected node for detail panel
  selectedNode: KGNode | null;
  setSelectedNode: React.Dispatch<React.SetStateAction<KGNode | null>>;

  // Reasoning visualization
  reasoningSteps: ReasoningStep[];
  setReasoningSteps: React.Dispatch<React.SetStateAction<ReasoningStep[]>>;

  // Settings
  settings: GraphRAGSettings;
  updateSettings: (updates: Partial<GraphRAGSettings>) => void;

  // KG stats
  kgStats: KGStats;
  setKgStats: React.Dispatch<React.SetStateAction<KGStats>>;

  // Refs
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

const DEFAULT_SETTINGS: GraphRAGSettings = {
  semanticK: 10,
  graphDepth: 2,
  maxContext: 15,
  useStreaming: true,
  useThinking: false,
  academicMode: false,
  rigorLevel: 'high',
  citationStyle: 'chicago',
};

const DEFAULT_KG_STATS: KGStats = {
  nodes: 0,
  edges: 0,
  sources: 0,
  hierarchyLayers: 3,
};

export function useGraphRAGState(): GraphRAGState {
  // Messages
  const [messages, setMessages] = useState<GraphRAGChatMessage[]>([]);

  // Query input
  const [query, setQuery] = useState('');
  const [currentQuery, setCurrentQuery] = useState('');

  // Loading states
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  // Streaming state
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [streamedThinking, setStreamedThinking] = useState('');
  const [thinkingComplete, setThinkingComplete] = useState(false);
  const [streamStatus, setStreamStatus] = useState('');

  // Error handling
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAIGenerating, setShowAIGenerating] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [showBenefits, setShowBenefits] = useState(false);

  // Pending query for auth flow
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);

  // Selected node
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);

  // Reasoning steps
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);

  // Settings
  const [settings, setSettings] = useState<GraphRAGSettings>(DEFAULT_SETTINGS);

  const updateSettings = useCallback((updates: Partial<GraphRAGSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  // KG stats
  const [kgStats, setKgStats] = useState<KGStats>(DEFAULT_KG_STATS);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  return {
    // Messages
    messages,
    setMessages,

    // Query input
    query,
    setQuery,
    currentQuery,
    setCurrentQuery,

    // Loading states
    loading,
    setLoading,
    streaming,
    setStreaming,

    // Streaming state
    streamedAnswer,
    setStreamedAnswer,
    streamedThinking,
    setStreamedThinking,
    thinkingComplete,
    setThinkingComplete,
    streamStatus,
    setStreamStatus,

    // Error handling
    error,
    setError,

    // UI state
    showAuthModal,
    setShowAuthModal,
    showSettings,
    setShowSettings,
    showSuggestions,
    setShowSuggestions,
    showAIGenerating,
    setShowAIGenerating,
    showHowItWorks,
    setShowHowItWorks,
    showBenefits,
    setShowBenefits,

    // Pending query
    pendingQuery,
    setPendingQuery,

    // Selected node
    selectedNode,
    setSelectedNode,

    // Reasoning steps
    reasoningSteps,
    setReasoningSteps,

    // Settings
    settings,
    updateSettings,

    // KG stats
    kgStats,
    setKgStats,

    // Refs
    messagesEndRef,
    abortControllerRef,
    inputRef,
  };
}
