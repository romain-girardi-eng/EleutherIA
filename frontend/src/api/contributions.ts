import { apiClient } from './client';

export type ContributionStatus =
  | 'uploaded'
  | 'processing'
  | 'ready'
  | 'approved'
  | 'rejected'
  | 'merged'
  | 'failed';

export type ProposalKind =
  | 'node'
  | 'edge'
  | 'passage_citation'
  | 'scholar_ref'
  | 'concept_attestation';

export type ProposalStatus =
  | 'pending'
  | 'accepted'
  | 'rejected'
  | 'superseded'
  | 'applied';

export interface ProposalEvidence {
  page_number?: number;
  excerpt?: string;
  surrounding_context?: string;
}

export interface Proposal {
  proposal_id: string;
  kind: ProposalKind;
  confidence: number;
  payload: Record<string, unknown>;
  target_kg_id: string | null;
  evidence: ProposalEvidence;
  status: ProposalStatus;
  reviewer_notes: string | null;
}

export interface UploadResponse {
  contribution_id: string;
  status: 'uploaded' | 'processing' | 'ready' | 'failed';
  pdf_signed_url: string;
  estimated_processing_seconds: number;
}

export interface ContributionDetail {
  contribution_id: string;
  title: string | null;
  authors: string[];
  doi: string | null;
  publication_year: number | null;
  status: ContributionStatus;
  relevance_score: number | null;
  relevance_summary: string | null;
  free_will_concepts: string[];
  pdf_signed_url: string;
  pdf_metadata: Record<string, unknown>;
  proposals: Proposal[];
  submitted_at: string;
}

export interface UploadMetadata {
  title?: string;
  authors?: string;
  doi?: string;
  publication_year?: number;
}

export interface UploadOptions {
  onUploadProgress?: (progress: number) => void;
  signal?: AbortSignal;
}

export async function uploadContribution(
  file: File,
  metadata: UploadMetadata = {},
  options: UploadOptions = {}
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('pdf', file);
  if (metadata.title) formData.append('title', metadata.title);
  if (metadata.authors) formData.append('authors', metadata.authors);
  if (metadata.doi) formData.append('doi', metadata.doi);
  if (typeof metadata.publication_year === 'number') {
    formData.append('publication_year', String(metadata.publication_year));
  }

  const response = await apiClient.post<UploadResponse>(
    '/api/contributions/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal: options.signal,
      onUploadProgress: (event: { loaded: number; total?: number }) => {
        if (!options.onUploadProgress) return;
        const total = event.total ?? file.size;
        if (!total) return;
        const ratio = Math.min(1, Math.max(0, event.loaded / total));
        options.onUploadProgress(ratio);
      },
    }
  );
  return response.data;
}

export async function getContribution(
  contributionId: string
): Promise<ContributionDetail> {
  const response = await apiClient.get<ContributionDetail>(
    `/api/contributions/${encodeURIComponent(contributionId)}`
  );
  return response.data;
}

export async function rejectContribution(
  contributionId: string,
  reviewerNotes?: string
): Promise<void> {
  await apiClient.post<void>(
    `/api/contributions/${encodeURIComponent(contributionId)}/reject`,
    { reviewer_notes: reviewerNotes ?? null }
  );
}

export interface ContributionListItem {
  contribution_id: string;
  title: string | null;
  authors: string[];
  publication_year: number | null;
  doi: string | null;
  status: ContributionStatus;
  relevance_score: number | null;
  free_will_concepts: string[];
  proposal_count: number;
  submitted_at: string;
  submitter_user_id: string | null;
}

export interface ContributionListResponse {
  items: ContributionListItem[];
  next_cursor: string | null;
}

export async function listContributions(params: {
  status?: ContributionStatus | 'all';
  limit?: number;
  cursor?: string;
} = {}): Promise<ContributionListResponse> {
  const query: Record<string, string> = {};
  if (params.status && params.status !== 'all') query.status = params.status;
  if (params.limit) query.limit = String(params.limit);
  if (params.cursor) query.cursor = params.cursor;
  const response = await apiClient.get<ContributionListResponse>(
    '/api/contributions',
    { params: query }
  );
  return response.data;
}

export async function acceptProposal(
  contributionId: string,
  proposalId: string,
  reviewerNotes?: string
): Promise<void> {
  await apiClient.post<void>(
    `/api/contributions/${encodeURIComponent(contributionId)}/proposals/${encodeURIComponent(proposalId)}/accept`,
    { reviewer_notes: reviewerNotes ?? null }
  );
}

export async function rejectProposal(
  contributionId: string,
  proposalId: string,
  reviewerNotes?: string
): Promise<void> {
  await apiClient.post<void>(
    `/api/contributions/${encodeURIComponent(contributionId)}/proposals/${encodeURIComponent(proposalId)}/reject`,
    { reviewer_notes: reviewerNotes ?? null }
  );
}

export interface ApplyContributionResponse {
  merged_proposals: number;
  contribution_id: string;
  kg_version_after: number;
}

export async function applyContribution(
  contributionId: string,
  reviewerNotes?: string
): Promise<ApplyContributionResponse> {
  const response = await apiClient.post<ApplyContributionResponse>(
    `/api/contributions/${encodeURIComponent(contributionId)}/apply`,
    { reviewer_notes: reviewerNotes ?? null }
  );
  return response.data;
}
