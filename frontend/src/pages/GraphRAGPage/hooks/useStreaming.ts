import { useCallback, useRef } from 'react';
import Cookies from 'js-cookie';
import type { GraphRAGResponse, GraphRAGStreamEvent } from '../../../types';
import type { ReasoningStep } from '../../../types/graphrag';
import type { GraphRAGSettings } from './useGraphRAGState';

export interface StreamingCallbacks {
  onStatus: (message: string) => void;
  onThinkingChunk: (chunk: string) => void;
  onThinkingComplete: () => void;
  onAnswerChunk: (answer: string) => void;
  onComplete: (response: GraphRAGResponse) => void;
  onError: (message: string) => void;
  onReasoningStep: (stepId: number, status: 'pending' | 'active' | 'complete' | 'error') => void;
  onAIGenerating: (show: boolean) => void;
}

export interface StreamingOptions {
  query: string;
  settings: GraphRAGSettings;
  conversationId: string | null;
}

export function useStreaming(callbacks: StreamingCallbacks) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const initializeReasoningSteps = useCallback((_query: string): ReasoningStep[] => {
    return [
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
  }, []);

  const updateReasoningFromStatus = useCallback((statusMsg: string) => {
    const msg = statusMsg.toLowerCase();

    if (msg.includes('embedding') || msg.includes('searching')) {
      callbacks.onReasoningStep(1, 'active');
    } else if (msg.includes('retrieving') || msg.includes('found')) {
      callbacks.onReasoningStep(1, 'complete');
      callbacks.onReasoningStep(2, 'active');
    } else if (msg.includes('expand') || msg.includes('travers')) {
      callbacks.onReasoningStep(2, 'active');
    } else if (msg.includes('context') || msg.includes('citation')) {
      callbacks.onReasoningStep(2, 'complete');
      callbacks.onReasoningStep(3, 'active');
    } else if (msg.includes('generat') || msg.includes('synthesis')) {
      callbacks.onReasoningStep(3, 'complete');
      callbacks.onReasoningStep(4, 'active');
      callbacks.onAIGenerating(true);
    }
  }, [callbacks]);

  const startStreaming = useCallback(async (options: StreamingOptions): Promise<{
    finalResponse: GraphRAGResponse | null;
    fullAnswer: string;
  }> => {
    const { query, settings, conversationId } = options;
    const token = Cookies.get('auth_token');
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    // Create abort controller for cancellation
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Add timeout for connection (2 minutes to handle cold starts)
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, 120000);

    // Build query parameters
    const params = new URLSearchParams({
      query,
      semantic_k: settings.semanticK.toString(),
      graph_depth: settings.graphDepth.toString(),
      max_context: settings.maxContext.toString(),
      use_thinking: settings.useThinking.toString(),
    });

    if (conversationId) {
      params.set('conversation_id', conversationId);
    }

    try {
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
              const parsed = JSON.parse(line.substring(6));
              // Backend sends { type, data } - payload may be in data.data or data
              const data = parsed as GraphRAGStreamEvent & { data?: { message?: string; data?: string } };
              const payload = data.data;
              const statusMsg = typeof payload === 'object' && payload && 'message' in payload
                ? (payload as { message?: string }).message
                : data.message;

              switch (data.type) {
                case 'status':
                  callbacks.onStatus(statusMsg || 'Loading...');
                  updateReasoningFromStatus(statusMsg || '');
                  break;

                case 'thinking_chunk': {
                  const chunk = typeof payload === 'object' && payload && 'data' in payload
                    ? (payload as { data?: string }).data
                    : (typeof payload === 'string' ? payload : '');
                  callbacks.onThinkingChunk(chunk || '');
                  callbacks.onStatus('Kimi K2 is reasoning...');
                  break;
                }

                case 'thinking_complete':
                  callbacks.onThinkingComplete();
                  callbacks.onStatus('Thinking complete, generating answer...');
                  break;

                case 'answer_chunk': {
                  const chunk = typeof payload === 'object' && payload && 'data' in payload
                    ? (payload as { data?: string }).data
                    : (typeof payload === 'string' ? payload : '');
                  fullAnswer += chunk || '';
                  callbacks.onAnswerChunk(fullAnswer);
                  callbacks.onAIGenerating(false);
                  break;
                }

                case 'complete':
                  finalResponse = (typeof payload === 'object' && payload ? payload : data.data) as GraphRAGResponse;
                  callbacks.onReasoningStep(5, 'complete');
                  callbacks.onAIGenerating(false);
                  callbacks.onComplete(finalResponse);
                  break;

                case 'error': {
                  const errMsg = typeof payload === 'object' && payload && 'message' in payload
                    ? (payload as { message?: string }).message
                    : data.message;
                  callbacks.onError(errMsg || 'Stream error');
                  break;
                }
              }
            } catch (err) {
              console.error('Error parsing SSE line:', line, err);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      return { finalResponse, fullAnswer };
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        throw new Error('Request was cancelled');
      }
      throw err;
    }
  }, [callbacks, updateReasoningFromStatus]);

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  return {
    startStreaming,
    cancelStreaming,
    initializeReasoningSteps,
  };
}
