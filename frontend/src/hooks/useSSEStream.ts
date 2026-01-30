/**
 * useSSEStream - Reusable hook for Server-Sent Events streaming
 * Provides connection management, error handling, and retry logic
 */

import { useState, useRef, useCallback } from 'react';
import Cookies from 'js-cookie';

export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'error' | 'complete';

export interface SSEStreamEvent<T = unknown> {
  type: 'status' | 'nodes' | 'citations' | 'answer_chunk' | 'complete' | 'error';
  message?: string;
  data?: T;
}

export interface UseSSEStreamOptions {
  /** Request timeout in ms (default: 120000 = 2 minutes) */
  timeout?: number;
  /** Maximum retry attempts (default: 2) */
  maxRetries?: number;
  /** Delay between retries in ms (default: 1000) */
  retryDelay?: number;
  /** Include auth token (default: true) */
  includeAuth?: boolean;
}

export interface UseSSEStreamReturn<T> {
  /** Current stream status */
  status: StreamStatus;
  /** Error message if status is 'error' */
  error: string | null;
  /** Status message from the stream */
  statusMessage: string;
  /** Accumulated streaming data */
  streamedData: string;
  /** Final complete response */
  finalResponse: T | null;
  /** Number of retry attempts */
  retryCount: number;
  /** Start streaming from URL with params */
  startStream: (url: string, params?: Record<string, string>) => Promise<void>;
  /** Stop the current stream */
  stopStream: () => void;
  /** Reset stream state */
  resetStream: () => void;
  /** Whether streaming is active */
  isStreaming: boolean;
}

const DEFAULT_OPTIONS: Required<UseSSEStreamOptions> = {
  timeout: 120000,
  maxRetries: 2,
  retryDelay: 1000,
  includeAuth: true,
};

export function useSSEStream<T = unknown>(
  onEvent?: (event: SSEStreamEvent<T>) => void,
  options?: UseSSEStreamOptions
): UseSSEStreamReturn<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  const [status, setStatus] = useState<StreamStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [streamedData, setStreamedData] = useState('');
  const [finalResponse, setFinalResponse] = useState<T | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const abortControllerRef = useRef<AbortController | null>(null);
  const retriesRef = useRef(0);

  const resetStream = useCallback(() => {
    setStatus('idle');
    setError(null);
    setStatusMessage('');
    setStreamedData('');
    setFinalResponse(null);
    setRetryCount(0);
    retriesRef.current = 0;
  }, []);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus('idle');
    setStatusMessage('');
    setStreamedData('');
  }, []);

  const startStream = useCallback(
    async (url: string, params?: Record<string, string>) => {
      // Reset state
      setError(null);
      setStreamedData('');
      setFinalResponse(null);
      setStatus('connecting');
      setStatusMessage('Connecting to server...');

      const attemptStream = async (): Promise<void> => {
        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        // Set timeout
        const timeoutId = setTimeout(() => {
          abortController.abort();
        }, opts.timeout);

        try {
          // Build URL with params
          const queryParams = new URLSearchParams(params || {});
          const fullUrl = `${url}?${queryParams.toString()}`;

          // Build headers
          const headers: Record<string, string> = {};
          if (opts.includeAuth) {
            const token = Cookies.get('auth_token');
            if (token) {
              headers['Authorization'] = `Bearer ${token}`;
            }
          }

          const response = await fetch(fullUrl, {
            method: 'GET',
            headers,
            signal: abortController.signal,
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText || 'Server error'}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error('No response body available');
          }

          setStatus('streaming');
          let buffer = '';
          let accumulated = '';

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
                  const event: SSEStreamEvent<T> = JSON.parse(line.substring(6));

                  // Handle events
                  switch (event.type) {
                    case 'status':
                      setStatusMessage(event.message || '');
                      break;

                    case 'answer_chunk':
                      accumulated += event.data as string;
                      setStreamedData(accumulated);
                      break;

                    case 'complete':
                      setFinalResponse(event.data as T);
                      setStatus('complete');
                      break;

                    case 'error':
                      setError(event.message || 'Stream error');
                      setStatus('error');
                      break;
                  }

                  // Call external handler
                  onEvent?.(event);
                } catch (parseError) {
                  console.warn('Failed to parse SSE line:', line, parseError);
                }
              }
            }
          } finally {
            reader.releaseLock();
          }

          // Stream completed successfully
          if (status !== 'error') {
            setStatus('complete');
          }
          retriesRef.current = 0;
        } catch (err) {
          clearTimeout(timeoutId);

          if (err instanceof Error && err.name === 'AbortError') {
            // User cancelled or timeout
            if (abortControllerRef.current === null) {
              // User cancelled
              setStatus('idle');
            } else {
              // Timeout - attempt retry
              if (retriesRef.current < opts.maxRetries) {
                retriesRef.current++;
                setRetryCount(retriesRef.current);
                setStatusMessage(
                  `Connection timeout. Retrying... (${retriesRef.current}/${opts.maxRetries})`
                );
                await new Promise((resolve) => setTimeout(resolve, opts.retryDelay));
                return attemptStream();
              } else {
                setError('Connection timed out. Please try again.');
                setStatus('error');
              }
            }
          } else if (err instanceof TypeError && err.message.includes('fetch')) {
            // Network error - attempt retry
            if (retriesRef.current < opts.maxRetries) {
              retriesRef.current++;
              setRetryCount(retriesRef.current);
              setStatusMessage(
                `Network error. Retrying... (${retriesRef.current}/${opts.maxRetries})`
              );
              await new Promise((resolve) => setTimeout(resolve, opts.retryDelay * 2));
              return attemptStream();
            } else {
              setError('Network error. Please check your connection.');
              setStatus('error');
            }
          } else {
            // Other errors
            setError(err instanceof Error ? err.message : 'Unknown error');
            setStatus('error');
          }
        }
      };

      await attemptStream();
    },
    [opts.timeout, opts.maxRetries, opts.retryDelay, opts.includeAuth, onEvent, status]
  );

  return {
    status,
    error,
    statusMessage,
    streamedData,
    finalResponse,
    retryCount,
    startStream,
    stopStream,
    resetStream,
    isStreaming: status === 'connecting' || status === 'streaming',
  };
}

export default useSSEStream;
