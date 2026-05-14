/**
 * useOpencodeStream — companion to `useResearchStream` that drives the UI from
 * opencode's global `/event` SSE channel instead of EleutherIA's own backend.
 *
 * The opencode `/event` channel is GLOBAL: events from every active session are
 * multiplexed onto a single stream. Clients de-multiplex client-side by
 * `properties.sessionID`. This hook owns a `Map<sessionID, OpencodeEventAdapter>`
 * so the global stream can route deltas to the right adapter once the user
 * starts a session.
 *
 * Return shape mirrors `useResearchStream` so the Research page can swap hooks
 * via a runtime toggle without rewriting downstream components.
 *
 * Wire format reference: docs/plans/2026-05-14-opencode-event-protocol.md
 *
 * SECURITY: when `VITE_OPENCODE_EVENT_URL` is set, the browser connects directly
 * and Basic Auth is read from `VITE_OPENCODE_SERVER_PASSWORD` — only acceptable
 * for dev / staging. In production prefer the default proxied path
 * `/api/opencode/event` so the backend injects credentials server-side.
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
  /** Override the SSE URL. Defaults to `VITE_OPENCODE_EVENT_URL` or `/api/opencode/event`. */
  eventUrl?: string;
  /** Override the session-creation URL. Defaults to `/api/opencode/session`. */
  sessionCreateUrl?: string;
}

const DEFAULT_OPTIONS: Required<Pick<
  UseOpencodeStreamOptions,
  'retryDelayMs' | 'maxRetries' | 'includeAuth'
>> = {
  retryDelayMs: 5_000,
  maxRetries: 3,
  includeAuth: true,
};

interface ImportMetaEnv {
  readonly VITE_OPENCODE_EVENT_URL?: string;
  readonly VITE_OPENCODE_SERVER_PASSWORD?: string;
  readonly VITE_OPENCODE_SESSION_URL?: string;
}

function readEnv(): ImportMetaEnv {
  // import.meta.env is replaced statically by Vite; cast for non-Vite test envs.
  const meta = (
    import.meta as unknown as { env?: ImportMetaEnv }
  ).env;
  return meta ?? {};
}

function defaultEventUrl(): string {
  return readEnv().VITE_OPENCODE_EVENT_URL ?? '/api/opencode/event';
}

function defaultSessionUrl(): string {
  return readEnv().VITE_OPENCODE_SESSION_URL ?? '/api/opencode/session';
}

function basicAuthHeader(): string | null {
  const password = readEnv().VITE_OPENCODE_SERVER_PASSWORD;
  if (!password) return null;
  // opencode docs: Basic Auth with empty username + server password.
  const encoded =
    typeof btoa === 'function'
      ? btoa(`:${password}`)
      : Buffer.from(`:${password}`).toString('base64');
  return `Basic ${encoded}`;
}

const initialState = reduce(undefined as never, { type: 'reset' });

export interface CreateSessionFn {
  (query: string, signal: AbortSignal): Promise<string>;
}

/** Default session creator — POSTs to a backend route that proxies opencode. */
async function defaultCreateSession(
  query: string,
  signal: AbortSignal,
  url: string,
  includeAuth: boolean,
): Promise<string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (includeAuth) {
    const token = Cookies.get('auth_token');
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const basic = basicAuthHeader();
  if (basic && !headers.Authorization) headers.Authorization = basic;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query }),
    signal,
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const body = (await response.json()) as { session_id?: string; sessionID?: string };
  const id = body.session_id ?? body.sessionID;
  if (!id) throw new Error('no_session_id_in_response');
  return id;
}

async function defaultCancelSession(
  sessionId: string,
  baseUrl: string,
  includeAuth: boolean,
): Promise<void> {
  const headers: Record<string, string> = {};
  if (includeAuth) {
    const token = Cookies.get('auth_token');
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const basic = basicAuthHeader();
  if (basic && !headers.Authorization) headers.Authorization = basic;

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
        options?.sessionCreateUrl ?? defaultSessionUrl(),
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
          const sessionId = await defaultCreateSession(
            query,
            controller.signal,
            options?.sessionCreateUrl ?? defaultSessionUrl(),
            opts.includeAuth,
          );
          activeSessionIdRef.current = sessionId;
          const adapter = new OpencodeEventAdapter({ sessionId });
          adaptersRef.current.set(sessionId, adapter);

          const headers: Record<string, string> = {
            Accept: 'text/event-stream',
          };
          if (opts.includeAuth) {
            const token = Cookies.get('auth_token');
            if (token) headers.Authorization = `Bearer ${token}`;
          }
          const basic = basicAuthHeader();
          if (basic && !headers.Authorization) headers.Authorization = basic;

          const eventUrl = options?.eventUrl ?? defaultEventUrl();
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
