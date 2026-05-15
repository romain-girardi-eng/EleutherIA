import { apiClient } from './client';

/**
 * Mirror of backend `CanonicalPassageItem`. Returned by
 * `GET /api/graphrag/community/canonical-passages`.
 */
export interface CanonicalPassageItem {
  passage_id: string;
  label: string;
  citation_count: number;
  distinct_answer_count: number;
  canonical_ref: string | null;
  language: string | null;
  work_title: string | null;
  author: string | null;
  period: string | null;
  preview_text: string | null;
  preview_slugs: string[];
}

export interface CanonicalPassagesResponse {
  items: CanonicalPassageItem[];
  total: number;
}

export interface CitingAnswer {
  slug: string;
  query: string;
  excerpt: string;
  citation_count: number;
  created_at: string;
}

/**
 * Mirror of backend `CanonicalPassageDetail`. Returned by
 * `GET /api/graphrag/community/canonical-passages/{passage_id}`.
 */
export interface CanonicalPassageDetail extends CanonicalPassageItem {
  full_text: string | null;
  citing_answers: CitingAnswer[];
}

export interface ListCanonicalPassagesParams {
  limit?: number;
  period?: string;
  author?: string;
}

export async function listCanonicalPassages(
  params: ListCanonicalPassagesParams = {}
): Promise<CanonicalPassagesResponse> {
  const response = await apiClient.get<CanonicalPassagesResponse>(
    '/api/graphrag/community/canonical-passages',
    { params }
  );
  return response.data;
}

export async function getCanonicalPassage(
  passageId: string
): Promise<CanonicalPassageDetail> {
  const response = await apiClient.get<CanonicalPassageDetail>(
    `/api/graphrag/community/canonical-passages/${encodeURIComponent(passageId)}`
  );
  return response.data;
}
