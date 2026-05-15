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
