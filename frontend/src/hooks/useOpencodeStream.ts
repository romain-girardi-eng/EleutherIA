/**
 * useOpencodeStream — drives the UI from opencode's global `/event` SSE
 * channel via the EleutherIA backend proxy at `/api/opencode/*`.
 *
 * All traffic flows through the backend so the upstream
 * `OPENCODE_SERVER_PASSWORD` never transits the browser. The session-create
 * call returns a short-lived `sse_token` JWT bound to the new `session_id`;
 * the hook passes it as `?token=...` on the SSE long-poll because browser
 * `fetch` based EventSource shims cannot append `Authorization` headers.
 *
 * Return shape mirrors `useResearchStream` so the Research page can swap
 * hooks via a runtime toggle without rewriting downstream components.
 *
 * Wire format reference: docs/plans/2026-05-14-opencode-event-protocol.md
 */

import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import Cookies from 'js-cookie';
import {
  OpencodeEventAdapter,
  type OpencodeEvent,
} from '../lib/opencode-adapter';
import { reduce } from './useResearchStream';
import type {
  ActiveSubagent,
  CitationEntry,
  KGActivation,
  PairedToolCall,
  UseResearchStreamReturn,
} from './useResearchStream';
import type { FinalAnswerEvent, SessionStatus } from '../types/agent-events';

export type UseOpencodeStreamReturn = UseResearchStreamReturn;

export interface UseOpencodeStreamOptions {
  /** Default: 5_000ms backoff between reconnect attempts. */
  retryDelayMs?: number;
  /** Default: 3 retries on transient network failure. */
  maxRetries?: number;
  /** Default: include the EleutherIA `auth_token` cookie as a Bearer header. */
  includeAuth?: boolean;
  /** Override the SSE URL. Defaults to `/api/opencode/event`. */
  eventUrl?: string;
  /** Override the session-creation URL. Defaults to `/api/opencode/session`. */
  sessionCreateUrl?: string;
  /** Override the opencode agent slug. Defaults to `scholar-orchestrator`. */
  agent?: string;
}

const DEFAULT_OPTIONS: Required<Pick<
  UseOpencodeStreamOptions,
  'retryDelayMs' | 'maxRetries' | 'includeAuth' | 'agent'
>> = {
  retryDelayMs: 5_000,
  maxRetries: 3,
  includeAuth: true,
  agent: 'scholar-orchestrator',
};

// Same reasoning as in useResearchStream: relative URLs resolve against
// free-will.app where there is no /api/* proxy. Build absolute defaults
// from VITE_API_URL at module load.
const _API_BASE = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
).replace(/\/+$/, '');
const DEFAULT_EVENT_URL = `${_API_BASE}/api/opencode/event`;
const DEFAULT_SESSION_URL = `${_API_BASE}/api/opencode/session`;

const initialState = reduce(undefined as never, { type: 'reset' });

interface CreateSessionResult {
  sessionId: string;
  sseToken: string | null;
}

function authHeader(includeAuth: boolean): string | null {
  if (!includeAuth) return null;
  const token = Cookies.get('auth_token');
  return token ? `Bearer ${token}` : null;
}

/** POST to the backend proxy to create an opencode session. */
async function defaultCreateSession(
  query: string,
  signal: AbortSignal,
  url: string,
  agent: string,
  includeAuth: boolean,
): Promise<CreateSessionResult> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const auth = authHeader(includeAuth);
  if (auth) headers.Authorization = auth;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ agent, title: query.slice(0, 80) }),
    signal,
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const body = (await response.json()) as {
    session_id?: string;
    sessionID?: string;
    sse_token?: string;
  };
  const id = body.session_id ?? body.sessionID;
  if (!id) throw new Error('no_session_id_in_response');
  return { sessionId: id, sseToken: body.sse_token ?? null };
}

async function defaultSubmitPrompt(
  sessionId: string,
  prompt: string,
  baseUrl: string,
  includeAuth: boolean,
  signal: AbortSignal,
): Promise<void> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const auth = authHeader(includeAuth);
  if (auth) headers.Authorization = auth;
  const response = await fetch(
    `${baseUrl}/${encodeURIComponent(sessionId)}/prompt`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({ prompt }),
      signal,
    },
  );
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
}

async function defaultCancelSession(
  sessionId: string,
  baseUrl: string,
  includeAuth: boolean,
): Promise<void> {
  const headers: Record<string, string> = {};
  const auth = authHeader(includeAuth);
  if (auth) headers.Authorization = auth;

  await fetch(`${baseUrl}/${encodeURIComponent(sessionId)}/abort`, {
    method: 'POST',
    headers,
  }).catch(() => {
    // Best-effort cancellation — the local stream is aborted regardless.
  });
}

export function useOpencodeStream(
  options?: UseOpencodeStreamOptions,
): UseOpencodeStreamReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const [state, dispatch] = useReducer(reduce, initialState);
  const abortRef = useRef<AbortController | null>(null);
  const cancelledRef = useRef<boolean>(false);
  const adaptersRef = useRef<Map<string, OpencodeEventAdapter>>(new Map());
  const activeSessionIdRef = useRef<string | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    cancelledRef.current = false;
    adaptersRef.current.clear();
    activeSessionIdRef.current = null;
    dispatch({ type: 'reset' });
  }, []);

  const cancel = useCallback(() => {
    cancelledRef.current = true;
    const sessionId = activeSessionIdRef.current ?? state.traceId;
    abortRef.current?.abort();
    abortRef.current = null;
    if (sessionId) {
      void defaultCancelSession(
        sessionId,
        options?.sessionCreateUrl ?? DEFAULT_SESSION_URL,
        opts.includeAuth,
      );
    }
    dispatch({ type: 'cancelled' });
  }, [opts.includeAuth, options?.sessionCreateUrl, state.traceId]);

  const start = useCallback(
    async (query: string): Promise<void> => {
      cancelledRef.current = false;
      dispatch({ type: 'reset' });
      dispatch({ type: 'connecting' });
      adaptersRef.current.clear();
      activeSessionIdRef.current = null;

      const attempt = async (attemptNumber: number): Promise<void> => {
        if (cancelledRef.current) return;

        const controller = new AbortController();
        abortRef.current = controller;

        try {
          const sessionUrl = options?.sessionCreateUrl ?? DEFAULT_SESSION_URL;
          const { sessionId, sseToken } = await defaultCreateSession(
            query,
            controller.signal,
            sessionUrl,
            opts.agent,
            opts.includeAuth,
          );
          activeSessionIdRef.current = sessionId;
          const adapter = new OpencodeEventAdapter({ sessionId });
          adaptersRef.current.set(sessionId, adapter);

          // Queue the user prompt on the freshly-created session. We do not
          // await — the SSE channel surfaces ack/progress.
          void defaultSubmitPrompt(
            sessionId,
            query,
            sessionUrl,
            opts.includeAuth,
            controller.signal,
          ).catch(() => {
            // Errors surface via the SSE error event.
          });

          const headers: Record<string, string> = {
            Accept: 'text/event-stream',
          };
          const auth = authHeader(opts.includeAuth);
          if (auth) headers.Authorization = auth;

          const baseEventUrl = options?.eventUrl ?? DEFAULT_EVENT_URL;
          const params = new URLSearchParams({ session_id: sessionId });
          if (sseToken) params.set('token', sseToken);
          const separator = baseEventUrl.includes('?') ? '&' : '?';
          const eventUrl = `${baseEventUrl}${separator}${params.toString()}`;
          const response = await fetch(eventUrl, {
            method: 'GET',
            headers,
            signal: controller.signal,
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const reader = response.body?.getReader();
          if (!reader) throw new Error('no_response_body');
          const decoder = new TextDecoder();

          dispatch({ type: 'streaming' });
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';
            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed.startsWith('data:')) continue;
              const payload = trimmed.slice(5).trim();
              if (!payload || payload === '[DONE]') continue;
              let parsed: unknown;
              try {
                parsed = JSON.parse(payload);
              } catch {
                continue;
              }
              if (!isOpencodeEnvelope(parsed)) continue;
              const sessionRef = sessionIdOf(parsed);
              if (!sessionRef) continue;
              const adapterForSession = adaptersRef.current.get(sessionRef);
              if (!adapterForSession) continue;
              const transformed = adapterForSession.transform(parsed);
              const at = Date.now();
              for (const ev of transformed) {
                dispatch({ type: 'event', event: ev, at });
                if (ev.type === 'final_answer') {
                  // Terminal — close the stream cooperatively.
                  controller.abort();
                }
              }
            }
          }

          if (!cancelledRef.current) {
            dispatch({ type: 'complete' });
          }
        } catch (err) {
          if (cancelledRef.current) return;
          const isAbort = err instanceof DOMException && err.name === 'AbortError';
          if (isAbort) return;
          const transient =
            err instanceof TypeError ||
            (err instanceof Error && /HTTP 5\d\d/.test(err.message));
          if (transient && attemptNumber < opts.maxRetries) {
            dispatch({ type: 'retry', attempt: attemptNumber + 1 });
            await new Promise((r) => setTimeout(r, opts.retryDelayMs));
            return attempt(attemptNumber + 1);
          }
          dispatch({
            type: 'error',
            message: err instanceof Error ? err.message : 'stream_failed',
          });
        }
      };

      await attempt(0);
    },
    [
      opts.agent,
      opts.includeAuth,
      opts.maxRetries,
      opts.retryDelayMs,
      options?.eventUrl,
      options?.sessionCreateUrl,
    ],
  );

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const citations = useMemo<CitationEntry[]>(
    () =>
      state.citationOrder
        .map((id) => state.citationsById[id])
        .filter((c): c is CitationEntry => Boolean(c)),
    [state.citationOrder, state.citationsById],
  );

  const activeSubagents = useMemo<ActiveSubagent[]>(
    () => Object.values(state.activeSubagents),
    [state.activeSubagents],
  );

  const toolCalls = useMemo<PairedToolCall[]>(
    () =>
      state.toolCallOrder
        .map((id) => state.toolCallsById[id])
        .filter((c): c is PairedToolCall => Boolean(c)),
    [state.toolCallOrder, state.toolCallsById],
  );

  const kgActivations = useMemo<KGActivation[]>(
    () => Object.values(state.kgActivationsById),
    [state.kgActivationsById],
  );

  return {
    status: state.status as SessionStatus,
    events: state.events,
    citations,
    activeSubagents,
    toolCalls,
    kgActivations,
    stageTimings: state.stageTimings,
    tokenUsage: state.tokenUsage,
    streamedAnswer: state.streamedAnswer,
    finalAnswer: state.finalAnswer as FinalAnswerEvent | null,
    traceId: state.traceId,
    error: state.error,
    retryCount: state.retryCount,
    start,
    cancel,
    reset,
  };
}

function isOpencodeEnvelope(value: unknown): value is OpencodeEvent {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as { type?: unknown; properties?: unknown };
  return (
    typeof candidate.type === 'string' &&
    typeof candidate.properties === 'object'
  );
}

function sessionIdOf(event: OpencodeEvent): string | null {
  const props = event.properties as { sessionID?: string } | null;
  if (!props) return null;
  return typeof props.sessionID === 'string' ? props.sessionID : null;
}

export default useOpencodeStream;
