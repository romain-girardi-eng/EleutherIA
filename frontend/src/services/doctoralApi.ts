/**
 * doctoralApi — thin adapter over the four Y2 endpoints used by the
 * doctoral workflow components.
 *
 * The Y2 backend returns slightly different field names than the UI uses
 * internally (e.g. `text_content_original` vs `text_original`). This
 * adapter does the translation in one place so the components stay
 * decoupled from backend churn.
 *
 * If any endpoint 404s (Y2 not yet deployed), each call falls back to a
 * minimal stub of the expected UI shape so the UI degrades gracefully.
 */

import axios, { type AxiosResponse } from 'axios';
import type {
  AuditResponse,
  KGNeighbor,
  NeighborsResponse,
  PassageDetail,
  SectionResponse,
  TranslationProvenance,
} from '../types/doctoral';

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '';

const warned = new Set<string>();
const warnOnce = (key: string, message: string): void => {
  if (warned.has(key)) return;
  warned.add(key);
  console.warn(`[doctoralApi] ${message}`);
};

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

interface RawPassageResponse {
  passage_id: string;
  work_id?: string | null;
  work_label?: string | null;
  cts_urn?: string | null;
  label?: string | null;
  text_content_original?: string | null;
  text_content_english?: string | null;
  translation_metadata?: {
    translator?: string | null;
    source?: string | null;
  } | null;
  edition_metadata?: {
    edition?: string | null;
    publisher?: string | null;
    section?: string | null;
  } | null;
  language?: string | null;
  lemmas?: string[] | Record<string, unknown> | null;
}

const mapProvenance = (
  source: string | null | undefined,
): TranslationProvenance => {
  if (!source) return 'unknown';
  const s = source.toLowerCase();
  if (s.includes('crisp')) return 'crisp_2000';
  if (s.includes('loeb')) return 'loeb';
  if (s.includes('ai') || s.includes('gemini') || s.includes('batch')) {
    return 'ai_batch';
  }
  return 'editor';
};

const normalisePassage = (raw: RawPassageResponse): PassageDetail => ({
  passage_id: raw.passage_id,
  work_id: raw.work_id ?? 'unknown',
  work_label: raw.work_label ?? undefined,
  cts_urn: raw.cts_urn ?? undefined,
  reference: raw.label ?? undefined,
  language: (raw.language as PassageDetail['language']) ?? undefined,
  text_original: raw.text_content_original ?? '',
  translation: raw.text_content_english ?? undefined,
  translation_provenance: mapProvenance(raw.translation_metadata?.source),
  translation_source: raw.translation_metadata?.source ?? undefined,
  edition: raw.edition_metadata?.edition ?? undefined,
  editor: raw.translation_metadata?.translator ?? undefined,
  lemmas: Array.isArray(raw.lemmas) ? (raw.lemmas as string[]) : undefined,
});

interface RawSectionItem {
  passage_id: string;
  label?: string | null;
  text_content_original?: string | null;
  text_content_english?: string | null;
}

interface RawSectionResponse {
  target_passage_id: string;
  before: RawSectionItem[];
  target: RawSectionItem;
  after: RawSectionItem[];
}

const normaliseSectionItem = (raw: RawSectionItem) => ({
  passage_id: raw.passage_id,
  reference: raw.label ?? undefined,
  text_original: raw.text_content_original ?? '',
  translation: raw.text_content_english ?? undefined,
});

const normaliseSection = (raw: RawSectionResponse): SectionResponse => ({
  before: (raw.before ?? []).map(normaliseSectionItem),
  passage: normaliseSectionItem(raw.target),
  after: (raw.after ?? []).map(normaliseSectionItem),
});

interface RawNeighborSummary {
  node_id: string;
  label?: string;
  node_type?: string | null;
  period?: string | null;
}

interface RawGroupedNeighborsResponse {
  node_id: string;
  neighbors?: {
    outgoing?: Record<string, RawNeighborSummary[]>;
    incoming?: Record<string, RawNeighborSummary[]>;
  };
  total_count?: number;
}

const flattenNeighbors = (
  raw: RawGroupedNeighborsResponse,
): NeighborsResponse => {
  const flat: KGNeighbor[] = [];
  const groups = raw.neighbors ?? {};
  for (const [relation, list] of Object.entries(groups.outgoing ?? {})) {
    for (const n of list) {
      flat.push({
        node_id: n.node_id,
        label: n.label ?? n.node_id,
        node_type: n.node_type ?? 'unknown',
        period: n.period ?? undefined,
        edge_type: relation,
        direction: 'outgoing',
      });
    }
  }
  for (const [relation, list] of Object.entries(groups.incoming ?? {})) {
    for (const n of list) {
      flat.push({
        node_id: n.node_id,
        label: n.label ?? n.node_id,
        node_type: n.node_type ?? 'unknown',
        period: n.period ?? undefined,
        edge_type: relation,
        direction: 'incoming',
      });
    }
  }
  return { node_id: raw.node_id, neighbors: flat };
};

const safeGet = async <RawT, UIT>(
  url: string,
  fallbackKey: string,
  fallback: () => UIT,
  normalise: (raw: RawT) => UIT,
): Promise<UIT> => {
  try {
    const res: AxiosResponse<RawT> = await client.get(url);
    return normalise(res.data);
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      warnOnce(
        fallbackKey,
        `Endpoint ${url} returned 404 — falling back to stub.`,
      );
      return fallback();
    }
    throw err;
  }
};

export const doctoralApi = {
  async getPassage(passageId: string): Promise<PassageDetail> {
    return safeGet<RawPassageResponse, PassageDetail>(
      `/api/passages/${encodeURIComponent(passageId)}`,
      `passage:${passageId}`,
      () => ({
        passage_id: passageId,
        work_id: 'unknown',
        text_original: '',
        translation_provenance: 'unknown',
      }),
      normalisePassage,
    );
  },

  async getSection(
    workId: string,
    aroundPassageId: string,
    before = 1,
    after = 1,
  ): Promise<SectionResponse> {
    const url = `/api/works/${encodeURIComponent(workId)}/section?around=${encodeURIComponent(
      aroundPassageId,
    )}&before=${before}&after=${after}`;
    return safeGet<RawSectionResponse, SectionResponse>(
      url,
      `section:${workId}`,
      () => ({
        before: [],
        passage: { passage_id: aroundPassageId, text_original: '' },
        after: [],
      }),
      normaliseSection,
    );
  },

  async getNeighbors(nodeId: string): Promise<NeighborsResponse> {
    return safeGet<RawGroupedNeighborsResponse, NeighborsResponse>(
      `/api/kg/nodes/${encodeURIComponent(nodeId)}/neighbors`,
      `neighbors:${nodeId}`,
      () => ({ node_id: nodeId, neighbors: [] }),
      flattenNeighbors,
    );
  },

  async getAudit(traceId: string): Promise<AuditResponse> {
    return safeGet<RawAuditResponse, AuditResponse>(
      `/api/graphrag/query/${encodeURIComponent(traceId)}/audit`,
      `audit:${traceId}`,
      () => ({
        trace_id: traceId,
        query: '',
        started_at: new Date().toISOString(),
        invocations: [],
      }),
      normaliseAudit,
    );
  },

  buildExportUrl(
    traceId: string,
    format: 'markdown' | 'latex' | 'bibtex' | 'zotero' | 'ris' | 'docx',
  ): string {
    return `${API_URL}/api/graphrag/query/${encodeURIComponent(traceId)}/export?format=${format}`;
  },

  async createShareLink(traceId: string): Promise<{ share_url: string; expires_at: string }> {
    const res = await client.post<{ share_url: string; expires_at: string }>(
      `/api/graphrag/query/${encodeURIComponent(traceId)}/share`,
    );
    return res.data;
  },
};

// --- Audit shape adapter ---------------------------------------------------
//
// Y2 returns a nested agent_tree with `sub_agents` recursion. We flatten it
// into the UI's invocation list (each with `parent_agent_id`).

interface RawAgentNode {
  agent_id?: string;
  parent_agent_id?: string | null;
  agent_name?: string;
  name?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  tokens_used?: number;
  status?: 'started' | 'complete' | 'failed';
  error?: string;
  tool_calls?: Array<{
    tool_call_id?: string;
    id?: string;
    tool?: string;
    args?: Record<string, unknown>;
    result_summary?: string;
    duration_ms?: number;
  }>;
  sub_agents?: RawAgentNode[];
}

interface RawAuditResponse {
  trace_id: string;
  query?: string;
  started_at?: string;
  completed_at?: string;
  mode?: string;
  agent_tree?: RawAgentNode | { root_agents?: RawAgentNode[] };
  total_latency_ms?: number;
  total_tool_calls?: number;
}

const normaliseAudit = (raw: RawAuditResponse): AuditResponse => {
  const invocations: AgentInvocationLike[] = [];
  const visit = (node: RawAgentNode, parentId: string | null): void => {
    const id =
      node.agent_id ?? `${node.agent_name ?? node.name ?? 'agent'}-${invocations.length}`;
    invocations.push({
      agent_id: id,
      parent_agent_id: parentId,
      agent_name: node.agent_name ?? node.name ?? 'agent',
      started_at: node.started_at ?? raw.started_at ?? new Date().toISOString(),
      completed_at: node.completed_at,
      duration_ms: node.duration_ms,
      tokens_used: node.tokens_used,
      status: node.status ?? 'complete',
      error: node.error,
      tool_calls: (node.tool_calls ?? []).map((tc, i) => ({
        tool_call_id: tc.tool_call_id ?? tc.id ?? `${id}:${i}`,
        tool: tc.tool ?? 'tool',
        args: tc.args ?? {},
        result_summary: tc.result_summary,
        duration_ms: tc.duration_ms,
      })),
    });
    for (const sub of node.sub_agents ?? []) visit(sub, id);
  };

  const tree = raw.agent_tree;
  if (tree && typeof tree === 'object') {
    if ('root_agents' in tree && Array.isArray(tree.root_agents)) {
      for (const r of tree.root_agents) visit(r, null);
    } else {
      visit(tree as RawAgentNode, null);
    }
  }

  return {
    trace_id: raw.trace_id,
    query: raw.query ?? '',
    started_at: raw.started_at ?? new Date().toISOString(),
    completed_at: raw.completed_at,
    total_duration_ms: raw.total_latency_ms,
    invocations,
  };
};

// Keep this typed locally to avoid a circular import on the type file.
type AgentInvocationLike = AuditResponse['invocations'][number];
