/**
 * doctoral.ts — types for the doctoral workflow UI.
 *
 * These shapes mirror the four backend endpoints added by the Y2 wave:
 *   - GET /api/passages/{id}
 *   - GET /api/works/{id}/section?around={passage_id}&before=N&after=N
 *   - GET /api/kg/nodes/{id}/neighbors
 *   - GET /api/graphrag/query/{trace_id}/audit
 *
 * `services/doctoralApi.ts` adapts the backend's raw field names
 * (`text_content_original`, `text_content_english`, `target`, …) into the
 * UI-internal shape declared here. Adding a field requires updating the
 * normaliser in that file as well.
 */

export type TranslationProvenance =
  | 'ai_batch'
  | 'crisp_2000'
  | 'loeb'
  | 'editor'
  | 'unknown';

/** Full passage with original text + transliteration + translation + provenance. */
export interface PassageDetail {
  passage_id: string;
  work_id: string;
  work_label?: string;
  cts_urn?: string;
  reference?: string;
  language?: 'grc' | 'lat' | 'fr' | 'en' | string;
  text_original: string;
  transliteration?: string;
  translation?: string;
  translation_provenance?: TranslationProvenance;
  translation_source?: string;
  edition?: string;
  editor?: string;
  year?: number;
  lemmas?: string[];
}

export interface PassageSection {
  passage_id: string;
  reference?: string;
  text_original: string;
  translation?: string;
}

export interface SectionResponse {
  before: PassageSection[];
  passage: PassageSection;
  after: PassageSection[];
}

export interface KGNeighbor {
  node_id: string;
  label: string;
  node_type: string;
  period?: string;
  /** edge type from this passage to the neighbor (e.g. "cites_primary_source"). */
  edge_type: string;
  /** "outgoing" = passage→neighbor; "incoming" = neighbor→passage. */
  direction: 'outgoing' | 'incoming';
  edge_metadata?: Record<string, unknown>;
}

export interface NeighborsResponse {
  node_id: string;
  neighbors: KGNeighbor[];
}

/** A single sub-agent invocation in the orchestrator tree. */
export interface AgentInvocation {
  agent_id: string;
  parent_agent_id: string | null;
  agent_name: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  tokens_used?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  cost_usd?: number;
  model?: string;
  provider?: string;
  tool_calls: AgentInvocationToolCall[];
  status: 'started' | 'complete' | 'failed';
  error?: string;
}

export interface AgentInvocationToolCall {
  tool_call_id: string;
  tool: string;
  args: Record<string, unknown>;
  result_summary?: string;
  duration_ms?: number;
}

export interface AuditResponse {
  trace_id: string;
  query: string;
  started_at: string;
  completed_at?: string;
  total_duration_ms?: number;
  total_tokens?: number;
  total_cost_usd?: number;
  token_breakdown?: {
    by_agent?: Record<string, { tokens: number; cost_usd: number; calls: number }>;
    by_model?: Record<string, { tokens: number; cost_usd: number; calls: number }>;
  };
  provider_usage?: Record<
    string,
    {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      cost_usd: number;
      calls: number;
    }
  >;
  invocations: AgentInvocation[];
}
