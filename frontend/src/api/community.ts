import Cookies from 'js-cookie';
import { apiClient } from './client';
import type { SourceCitation } from '../types';
import type { PassageCitationEntry } from '../components/CitationRenderer';

/**
 * Mirror of backend `CommunityListItem`. Returned by
 * `GET /api/graphrag/community/queries`.
 */
export interface CommunityListItem {
  slug: string;
  query: string;
  excerpt: string;
  citation_count: number;
  section_count: number;
  quote_count: number;
  model: string | null;
  total_cost_usd: number;
  total_tokens: number;
  created_at: string;
  topic_tags: string[];
}

export interface CommunityListResponse {
  items: CommunityListItem[];
  next_cursor: string | null;
}

/**
 * Minimal `reasoning_path` shape we render in the detail page. The backend
 * may include extra fields; we keep them as a permissive record so this
 * stays forward-compatible.
 */
export interface CommunityReasoningPath {
  starting_nodes?: Array<{ id: string; label: string; type: string; reason?: string }>;
  expanded_nodes?: Array<{ id: string; label: string; type: string; reason?: string }>;
  traversed_edges?: Array<{
    source: string;
    target: string;
    relation: string;
    description?: string;
  }>;
  total_nodes?: number;
  total_edges?: number;
  [key: string]: unknown;
}

/**
 * Mirror of backend `CommunityDetailResponse`. Returned by
 * `GET /api/graphrag/community/queries/{slug}`.
 */
export interface CommunityDetail extends CommunityListItem {
  trace_id: string | null;
  answer: string;
  passage_citations: PassageCitationEntry[];
  sources: SourceCitation[];
  reasoning_path: CommunityReasoningPath | null;
}

export interface ListCommunityQueriesParams {
  sort?: 'recent' | 'popular';
  period?: string;
  philosopher?: string;
  limit?: number;
  cursor?: string;
}

export async function listCommunityQueries(
  params: ListCommunityQueriesParams = {}
): Promise<CommunityListResponse> {
  const response = await apiClient.get<CommunityListResponse>(
    '/api/graphrag/community/queries',
    { params }
  );
  return response.data;
}

export async function getCommunityQuery(slug: string): Promise<CommunityDetail> {
  const response = await apiClient.get<CommunityDetail>(
    `/api/graphrag/community/queries/${encodeURIComponent(slug)}`
  );
  return response.data;
}

/**
 * Mirror of backend `ReproducibilityStatus`. Returned by
 * `GET /api/graphrag/community/queries/{slug}/reproducibility`.
 */
export type ReproducibilityState = 'unchanged' | 'kg_advanced' | 'stale_unknown';

export interface ReproducibilityStatus {
  slug: string;
  cached_at_kg_version: number;
  current_kg_version: number;
  kg_advanced_by: number;
  status: ReproducibilityState;
  cached_at: string;
  current_kg_updated_at: string;
}

export async function getReproducibility(slug: string): Promise<ReproducibilityStatus> {
  const response = await apiClient.get<ReproducibilityStatus>(
    `/api/graphrag/community/queries/${encodeURIComponent(slug)}/reproducibility`
  );
  return response.data;
}

/**
 * Mirror of backend `ReverifyResponse`. Emitted as the final SSE payload
 * (`type: complete`) of the reverify stream.
 */
export interface ReverifyCitationDiff {
  added: string[];
  removed: string[];
}

export interface ReverifyResponse {
  slug: string;
  original_trace_id: string;
  new_trace_id: string;
  char_count_diff: number;
  citation_diff: ReverifyCitationDiff;
  similarity: number;
  kg_advanced_by: number;
  new_answer_excerpt: string;
}

export type ReverifyStage =
  | 'classify'
  | 'search'
  | 'reading'
  | 'synthesis'
  | 'verify';

export interface ReverifyProgressEvent {
  type: 'progress';
  stage: ReverifyStage;
  elapsed_s: number;
}

export interface ReverifyCompleteEvent {
  type: 'complete';
  data: ReverifyResponse;
}

export interface ReverifyErrorEvent {
  type: 'error';
  message: string;
}

export type ReverifyEvent =
  | ReverifyProgressEvent
  | ReverifyCompleteEvent
  | ReverifyErrorEvent;

export interface ReverifyCallbacks {
  onProgress?: (event: ReverifyProgressEvent) => void;
  onComplete?: (event: ReverifyCompleteEvent) => void;
  onError?: (event: ReverifyErrorEvent) => void;
  /** Called when the stream finishes (success, error, or abort). */
  onClose?: () => void;
  signal?: AbortSignal;
}

interface ReverifyStreamHandle {
  /** Promise that resolves when the stream completes or aborts. */
  done: Promise<void>;
  /** Abort the in-flight stream. */
  cancel: () => void;
}

function isReverifyEvent(value: unknown): value is ReverifyEvent {
  if (!value || typeof value !== 'object') return false;
  const v = value as { type?: unknown };
  return v.type === 'progress' || v.type === 'complete' || v.type === 'error';
}

/**
 * Open the reverify SSE stream and dispatch typed events to the caller.
 *
 * Returns a handle whose `cancel()` aborts the in-flight fetch and whose
 * `done` promise resolves once the stream is closed.
 */
export function streamReverify(
  slug: string,
  callbacks: ReverifyCallbacks = {}
): ReverifyStreamHandle {
  const controller = new AbortController();
  const externalSignal = callbacks.signal;
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener('abort', () => controller.abort(), {
        once: true,
      });
    }
  }

  const done = (async () => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    };
    const token = Cookies.get('auth_token');
    if (token) headers.Authorization = `Bearer ${token}`;

    try {
      const response = await fetch(
        `/api/graphrag/community/queries/${encodeURIComponent(slug)}/reverify`,
        {
          method: 'POST',
          headers,
          signal: controller.signal,
        }
      );

      if (!response.ok) {
        callbacks.onError?.({
          type: 'error',
          message: `HTTP ${response.status}`,
        });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.({ type: 'error', message: 'no_response_body' });
        return;
      }
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done: streamDone, value } = await reader.read();
        if (streamDone) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const payload = trimmed.slice(6);
          if (!payload || payload === '[DONE]') continue;
          try {
            const parsed: unknown = JSON.parse(payload);
            if (!isReverifyEvent(parsed)) continue;
            switch (parsed.type) {
              case 'progress':
                callbacks.onProgress?.(parsed);
                break;
              case 'complete':
                callbacks.onComplete?.(parsed);
                break;
              case 'error':
                callbacks.onError?.(parsed);
                break;
            }
          } catch {
            // Ignore malformed lines / keepalives.
          }
        }
      }
    } catch (err) {
      const isAbort = err instanceof DOMException && err.name === 'AbortError';
      if (isAbort) return;
      callbacks.onError?.({
        type: 'error',
        message: err instanceof Error ? err.message : 'stream_failed',
      });
    } finally {
      callbacks.onClose?.();
    }
  })();

  return {
    done,
    cancel: () => controller.abort(),
  };
}
