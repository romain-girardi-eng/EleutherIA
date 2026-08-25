import { apiClient } from './client';

export type AnswerReportType =
  | 'factual_error'
  | 'wrong_citation'
  | 'missing_source'
  | 'ui_issue'
  | 'accessibility'
  | 'performance'
  | 'account_access'
  | 'feature_request'
  | 'improvement'
  | 'other';

export interface AnswerFeedbackPayload {
  trace_id: string;
  rating?: number;
  comment?: string;
  app_commit?: string;
  model?: string;
}

export interface AnswerReportPayload {
  trace_id: string;
  report_type: AnswerReportType;
  report_text: string;
  answer_excerpt?: string;
  app_commit?: string;
  model?: string;
}

export interface AnswerFeedbackRecord {
  id: string;
  trace_id: string | null;
  rating: number | null;
  comment: string | null;
  report_type: AnswerReportType | null;
  report_text: string | null;
  answer_excerpt: string | null;
  app_commit: string | null;
  model: string | null;
  created_at: string;
}

export interface MyAnswerFeedback {
  trace_id: string;
  rating: number | null;
  comment: string | null;
}

export type FeedbackScope = 'answer' | 'page' | 'node' | 'source' | 'data' | 'ux' | 'account' | 'other';
export type FeedbackSeverity = 'low' | 'normal' | 'high' | 'critical';

export interface GeneralFeedbackPayload {
  scope: FeedbackScope;
  report_type: AnswerReportType;
  message: string;
  severity: FeedbackSeverity;
  page_url?: string;
  entity_id?: string;
  contact_allowed: boolean;
  app_commit?: string;
}

export async function submitAnswerFeedback(
  payload: AnswerFeedbackPayload,
): Promise<AnswerFeedbackRecord> {
  const response = await apiClient.post<AnswerFeedbackRecord>('/api/feedback', payload);
  return response.data;
}

export async function submitAnswerReport(
  payload: AnswerReportPayload,
): Promise<AnswerFeedbackRecord> {
  const response = await apiClient.post<AnswerFeedbackRecord>(
    '/api/feedback/report',
    payload,
  );
  return response.data;
}

export async function getMyAnswerFeedback(
  traceId: string,
  signal?: AbortSignal,
): Promise<MyAnswerFeedback> {
  const response = await apiClient.get<MyAnswerFeedback>('/api/feedback/mine', {
    params: { trace_id: traceId },
    signal,
  });
  return response.data;
}

export async function submitGeneralFeedback(
  payload: GeneralFeedbackPayload,
): Promise<AnswerFeedbackRecord> {
  const response = await apiClient.post<AnswerFeedbackRecord>(
    '/api/feedback/general',
    payload,
  );
  return response.data;
}
