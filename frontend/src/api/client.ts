import axios from 'axios';
import Cookies from 'js-cookie';
import type { AxiosInstance } from 'axios';
import type {
  KGEdgePage,
  KGNode,
  KGNodePage,
  KGWorkspaceNodeDetail,
  KGWorkspaceStats,
  CytoscapeData,
  HybridSearchResponse,
  SearchQuery,
  GraphRAGQuery,
  GraphRAGResponse,
  SemativersePermissionRequest,
  SemativersePermissionResponse,
  TimelineOverview,
  InfluenceMatrixOverview,
  KGFilterState,
  KGPathRequest,
  KGPathResponse,
  Conversation,
  ConversationMessage,
} from '../types';
import type { User } from '../context/AuthContext';
import { API_BASE } from './baseUrl';

const API_URL = API_BASE;

const KG_RELEASE_ID_HEADER = 'x-eleutheria-kg-release-id';
const KG_SERVED_NODES_HEADER = 'x-eleutheria-kg-served-total-nodes';
const KG_SERVED_EDGES_HEADER = 'x-eleutheria-kg-served-total-edges';

function headerValue(headers: Record<string, unknown>, name: string): unknown {
  const getter = (headers as { get?: (key: string) => unknown }).get;
  return getter?.call(headers, name) ?? headers[name];
}

function headerCount(headers: Record<string, unknown>, name: string): number | undefined {
  const raw = headerValue(headers, name);
  const parsed = typeof raw === 'number' ? raw : typeof raw === 'string' ? Number(raw) : NaN;
  return Number.isSafeInteger(parsed) && parsed >= 0 ? parsed : undefined;
}

function releaseContract(
  headers: Record<string, unknown>,
  data: Record<string, unknown> | null,
) {
  const headerRelease = headerValue(headers, KG_RELEASE_ID_HEADER);
  return {
    release_id:
      (typeof data?.release_id === 'string' ? data.release_id : undefined) ??
      (typeof headerRelease === 'string' ? headerRelease : undefined),
    served_total_nodes:
      (typeof data?.served_total_nodes === 'number' ? data.served_total_nodes : undefined) ??
      headerCount(headers, KG_SERVED_NODES_HEADER),
    served_total_edges:
      (typeof data?.served_total_edges === 'number' ? data.served_total_edges : undefined) ??
      headerCount(headers, KG_SERVED_EDGES_HEADER),
  };
}

export interface WorkspaceReleaseMismatch {
  requestedReleaseId?: string;
  servedReleaseId: string;
}

/** Normalize the backend's release-precondition response without treating
 * unrelated 409 responses as graph identity failures. */
export function workspaceReleaseMismatchFromError(
  error: unknown,
): WorkspaceReleaseMismatch | null {
  if (!axios.isAxiosError(error) || error.response?.status !== 409) return null;
  const responseData = error.response.data;
  if (!responseData || typeof responseData !== 'object' || Array.isArray(responseData)) {
    return null;
  }
  const rawDetail = (responseData as Record<string, unknown>).detail;
  if (!rawDetail || typeof rawDetail !== 'object' || Array.isArray(rawDetail)) return null;
  const detail = rawDetail as Record<string, unknown>;
  if (detail.code !== 'kg_release_mismatch' || typeof detail.served_release_id !== 'string') {
    return null;
  }
  return {
    requestedReleaseId:
      typeof detail.requested_release_id === 'string'
        ? detail.requested_release_id
        : undefined,
    servedReleaseId: detail.served_release_id,
  };
}

export type AccountRequestRole =
  | 'doctoral_researcher'
  | 'researcher'
  | 'student'
  | 'teacher'
  | 'independent_scholar'
  | 'other';

export type AccountRequestUse =
  | 'research'
  | 'teaching'
  | 'writing'
  | 'data_exploration'
  | 'other';

export interface AccountRequestPayload {
  full_name: string;
  email: string;
  affiliation?: string;
  role: AccountRequestRole;
  research_focus: string;
  intended_use: AccountRequestUse[];
  privacy_acknowledged: true;
  privacy_notice_version: '2026-08-24';
  locale: string;
  website: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000, // 60 second timeout for GraphRAG queries
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      // Prevent accidental double "/api/api/..." when baseURL already includes "/api"
      // and route paths are still written with an "/api" prefix.
      const baseUrl = (config.baseURL ?? '').replace(/\/+$/, '');
      if (typeof config.url === 'string' && baseUrl.endsWith('/api') && config.url.startsWith('/api/')) {
        config.url = config.url.slice(4);
      }

      const token = Cookies.get('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor to handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 || error.response?.status === 403) {
          // Token expired, invalid, or missing - clear it
          Cookies.remove('auth_token');
          // Redirect to login for authenticated pages
          const authenticatedPages = ['/graphrag', '/graphrag-showcase', '/citation-network', '/admin'];
          if (authenticatedPages.includes(window.location.pathname)) {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/api/health');
    return response.data;
  }

  // Knowledge Graph Endpoints
  async getNodes(filters?: { type?: string; period?: string; school?: string; limit?: number; offset?: number }): Promise<KGNodePage> {
    // Backend expects `node_type`, not `type`
    const { type, ...rest } = filters ?? {};
    const params = type ? { ...rest, node_type: type } : rest;
    const response = await this.client.get('/api/kg/nodes', { params });
    const data = response.data;
    const objectData = data && typeof data === 'object' && !Array.isArray(data)
      ? data as Record<string, unknown>
      : null;
    return {
      nodes: Array.isArray(data) ? data : Array.isArray(objectData?.nodes) ? objectData.nodes : [],
      ...releaseContract(response.headers, objectData),
    };
  }

  async getEdges(filters?: { relation?: string; limit?: number; offset?: number }): Promise<KGEdgePage> {
    const response = await this.client.get('/api/kg/edges', { params: filters });
    const data = response.data;
    const objectData = data && typeof data === 'object' && !Array.isArray(data)
      ? data as Record<string, unknown>
      : null;
    return {
      edges: Array.isArray(data) ? data : Array.isArray(objectData?.edges) ? objectData.edges : [],
      ...releaseContract(response.headers, objectData),
    };
  }

  async getWorkspaceStats(releaseId?: string): Promise<KGWorkspaceStats> {
    const response = await this.client.get('/api/kg/workspace/stats', {
      params: releaseId ? { release_id: releaseId } : undefined,
    });
    const data = response.data && typeof response.data === 'object'
      ? response.data as Record<string, unknown>
      : null;
    return {
      ...(data ?? {}),
      ...releaseContract(response.headers, data),
    } as KGWorkspaceStats;
  }

  async getWorkspaceNodes(filters: {
    limit: number;
    offset: number;
    release_id: string;
  }): Promise<KGNodePage> {
    const response = await this.client.get('/api/kg/workspace/nodes', { params: filters });
    const data = response.data && typeof response.data === 'object' && !Array.isArray(response.data)
      ? response.data as Record<string, unknown>
      : null;
    return {
      nodes: Array.isArray(data?.nodes) ? data.nodes : [],
      ...releaseContract(response.headers, data),
    };
  }

  async getWorkspaceEdges(filters: {
    limit: number;
    offset: number;
    release_id: string;
  }): Promise<KGEdgePage> {
    const response = await this.client.get('/api/kg/workspace/edges', { params: filters });
    const data = response.data && typeof response.data === 'object' && !Array.isArray(response.data)
      ? response.data as Record<string, unknown>
      : null;
    return {
      edges: Array.isArray(data?.edges) ? data.edges : [],
      ...releaseContract(response.headers, data),
    };
  }

  async getWorkspaceNode(id: string, releaseId: string): Promise<KGWorkspaceNodeDetail> {
    const response = await this.client.get(
      `/api/kg/workspace/nodes/${encodeURIComponent(id)}`,
      { params: { release_id: releaseId } },
    );
    const data = response.data && typeof response.data === 'object' && !Array.isArray(response.data)
      ? response.data as Record<string, unknown>
      : null;
    const rawNode = data?.node;
    if (!rawNode || typeof rawNode !== 'object' || Array.isArray(rawNode)) {
      throw new Error('The workspace node-detail API returned an invalid node.');
    }
    if (!Object.prototype.hasOwnProperty.call(rawNode, 'description')) {
      throw new Error('The workspace node-detail API omitted its detail sentinel.');
    }
    const rawDescription = (rawNode as Record<string, unknown>).description;
    if (rawDescription !== null && typeof rawDescription !== 'string') {
      throw new Error('The workspace node-detail API returned an invalid description.');
    }
    const node = { ...(rawNode as KGNode) };
    // The detail endpoint always includes `description`; an empty string means
    // the record was loaded and reviewed but has no editorial description.
    // Preserve that distinction from a compact summary where the key is absent.
    if (rawDescription === null) node.description = '';
    return {
      node,
      ...releaseContract(response.headers, data),
    };
  }

  async getBibliography(): Promise<{ references: string[]; count: number }> {
    const response = await this.client.get('/api/kg/bibliography');
    return response.data;
  }

  async getNode(id: string) {
    const response = await this.client.get(`/api/kg/node/${id}`);
    return response.data;
  }

  async getNodeConnections(id: string) {
    const response = await this.client.get(`/api/kg/node/${id}/connections`);
    return response.data;
  }

  // Canonical single-node lookup (REST-clean plural path).
  async getNodeById(id: string): Promise<KGNode> {
    const response = await this.client.get<KGNode>(`/api/kg/nodes/${encodeURIComponent(id)}`);
    return response.data;
  }

  // Grouped neighbours for a node: { node_id, node, neighbors: { outgoing, incoming }, total_count }
  async getNodeNeighbors(
    id: string,
    options?: { depth?: number }
  ): Promise<KGNodeNeighborsResponse> {
    const response = await this.client.get<KGNodeNeighborsResponse>(
      `/api/kg/nodes/${encodeURIComponent(id)}/neighbors`,
      { params: { grouped: true, depth: options?.depth ?? 1 } }
    );
    return response.data;
  }

  async getCytoscapeData(options?: { algorithm?: string; ancientOnly?: boolean }): Promise<CytoscapeData> {
    const params: Record<string, string | boolean> = {};

    if (options?.algorithm) {
      params.communityAlgorithm = options.algorithm;
    }
    if (options?.ancientOnly) {
      params.ancientOnly = true;
    }

    // Add random timestamp to bypass browser cache
    params._t = Date.now().toString();

    const response = await this.client.get('/api/kg/viz/cytoscape', { params });
    const data = response.data as CytoscapeData & {
      meta?: {
        community?: {
          algorithmRequested?: string;
          algorithm_requested?: string;
          algorithmUsed?: string;
          algorithm_used?: string;
          quality?: number | string | null;
          communities?: Array<{
            id?: number;
            community_id?: number;
            size?: number;
            order?: number;
            color?: string;
            label?: string;
          }>;
          availableAlgorithms?: Array<{
            name?: string;
            available?: boolean;
            description?: string;
          }>;
          available_algorithms?: Array<{
            name?: string;
            available?: boolean;
            description?: string;
          }>;
        };
      };
    };

    if (!data.meta?.community) {
      return data;
    }

    const community = data.meta.community;

    const transformed: CytoscapeData = {
      elements: data.elements,
      meta: {
        ...data.meta,
        community: {
          algorithmRequested:
            community.algorithmRequested ??
            community.algorithm_requested ??
            (options?.algorithm ?? 'auto'),
          algorithmUsed:
            community.algorithmUsed ??
            community.algorithm_used ??
            'none',
          quality:
            typeof community.quality === 'number'
              ? community.quality
              : community.quality != null
                ? Number(community.quality)
                : null,
          communities: Array.isArray(community.communities)
            ? community.communities.map((entry: {
                id?: number;
                community_id?: number;
                size?: number;
                order?: number;
                color?: string;
                label?: string;
              }) => ({
                id: Number(entry.id ?? entry.community_id ?? 0),
                size: Number(entry.size ?? 0),
                order: Number(entry.order ?? 0),
                color: entry.color ?? '#3b82f6',
                label:
                  entry.label ??
                  `Community ${
                    typeof entry.order === 'number'
                      ? entry.order + 1
                      : Number(entry.id ?? 0) + 1
                  }`,
              }))
            : [],
          availableAlgorithms: Array.isArray(community.availableAlgorithms ?? community.available_algorithms)
            ? (community.availableAlgorithms ?? community.available_algorithms).map((option: {
                name?: string;
                available?: boolean;
                description?: string;
              }) => ({
                name: option.name ?? 'unknown',
                available: Boolean(option.available ?? false),
                description: option.description ?? '',
              }))
            : [],
        },
      },
    };

    return transformed;
  }

  async getKGStats() {
    const response = await this.client.get('/api/kg/stats');
    return response.data;
  }

  async getTimelineOverview(filters?: Partial<KGFilterState>): Promise<TimelineOverview> {
    const response = await this.client.get('/api/kg/analytics/timeline', { params: filters });
    return response.data;
  }

  async getInfluenceMatrix(filters?: Partial<KGFilterState>): Promise<InfluenceMatrixOverview> {
    const response = await this.client.get('/api/kg/analytics/influence-matrix', { params: filters });
    return response.data;
  }

  async computeGraphPath(request: KGPathRequest): Promise<KGPathResponse> {
    const response = await this.client.post('/api/kg/analytics/path', request);
    return response.data;
  }

  // Search Endpoints
  async hybridSearch(query: SearchQuery): Promise<HybridSearchResponse> {
    const response = await this.client.post('/api/search/hybrid', query);
    return response.data;
  }

  async fulltextSearch(query: string, limit: number = 10) {
    const response = await this.client.post('/api/search/fulltext', { query, limit });
    return response.data;
  }

  async lemmaticSearch(query: string, limit: number = 10) {
    const response = await this.client.post('/api/search/lemmatic', { query, limit });
    return response.data;
  }

  // Lemma Autocomplete - supports Latin-to-Greek transliteration
  async autocompleteLemmas(query: string, options?: {
    language?: string;
    limit?: number;
    minCount?: number;
    fuzzy?: boolean;
  }): Promise<{
    suggestions: Array<{
      lemma: string;
      lemma_latin: string;
      language: string;
      pos: string;
      count: number;
      passage_count: number;
      forms: string[];
    }>;
    query: string;
    mode: 'latin-to-greek' | 'direct';
    fuzzy: boolean;
  }> {
    const params = new URLSearchParams();
    params.append('q', query);
    if (options?.language) params.append('lang', options.language);
    if (options?.limit) params.append('limit', String(options.limit));
    if (options?.minCount) params.append('min_count', String(options.minCount));
    if (options?.fuzzy) params.append('fuzzy', 'true');

    const response = await this.client.get(`/api/search/autocomplete/lemmas?${params}`);
    return response.data;
  }

  async searchKG(query: string, limit: number = 10) {
    const response = await this.client.post('/api/search/kg', { query, limit });
    return response.data;
  }

  // GraphRAG Endpoints
  async graphragQuery(query: GraphRAGQuery): Promise<GraphRAGResponse> {
    // NORMAL MODE: Fast response (~45-60s) with essential features only
    // Tested: hierarchy=true is FASTER than without (uses community summaries)
    // Disables: HyDE, expansion, CRAG, SELF-RAG, debates (each adds 30-60s)
    const enhancedQuery = {
      ...query,
      enhanced_mode: query.enhanced_mode !== false,
      mode: query.mode || 'fast',
      semantic_k: query.semantic_k || 5, // Reduced for speed
      graph_depth: query.graph_depth || 1,
      use_hyde: false,
      use_expansion: false,
      use_crag: false,
      use_selfrag: false,
      use_debates: false,
      use_hierarchy: true, // FASTER with hierarchy (uses community summaries)
      use_reranking: true, // Keep for relevance
    };
    const response = await this.client.post('/api/graphrag/answer', enhancedQuery, {
      timeout: 90000, // 90 seconds for fast mode
    });
    return response.data;
  }

  // GraphRAG Streaming (returns EventSource)
  graphragQueryStream(query: GraphRAGQuery): EventSource {
    const params = new URLSearchParams(
      Object.fromEntries(
        Object.entries(query).map(([key, value]) => [key, String(value)])
      )
    );
    const base = API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`;
    const url = `${base}/graphrag/query/stream?${params}`;

    return new EventSource(url, {
      withCredentials: false,
    });
  }

  async graphragStatus() {
    const response = await this.client.get('/api/graphrag/status');
    return response.data;
  }

  // Advanced GraphRAG with academic mode - FULL SOTA PIPELINE via Workflows
  async graphragQueryAdvanced(query: GraphRAGQuery): Promise<GraphRAGResponse> {
    // ACADEMIC MODE: Full SOTA pipeline via Cloudflare Workflows (~50-90s)
    // Uses: HyDE, LLM Reranking, CRAG validation, SELF-RAG evaluation
    // Much faster than before (50s vs 5min) thanks to Gemini primary + Kimi reasoning

    // Start workflow
    const startResponse = await this.client.post('/api/graphrag/workflow/start', {
      query: query.query,
      mode: 'thorough', // Full SOTA techniques
      options: {
        use_hyde: true,
        use_rerank: true,
        use_crag: true,
        use_selfrag: true,
        limit: query.semantic_k || 8,
      },
    }, {
      timeout: 30000, // 30s to start workflow
    });

    const { instanceId } = startResponse.data;

    // Poll for completion (workflow typically completes in 50-90s, but complex queries may take longer)
    const maxWait = 300000; // 5 minutes max for academic mode
    const pollInterval = 3000; // 3 seconds
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const statusResponse = await this.client.get(`/api/graphrag/workflow/status/${instanceId}`);
      const { status, result } = statusResponse.data;

      if (status === 'complete') {
        // Transform workflow response to GraphRAGResponse format
        // Sources need nodeId, nodeLabel, nodeType for the frontend CitationRenderer
        interface WorkflowSource {
          id: number;
          author: string;
          work: string;
          text: string;
          language?: string;
          score?: number;
          passage_id?: string;
          work_id?: string;
        }
        const workflowSources = (result.sources || []) as WorkflowSource[];

        // Build source labels for citations.ancient_sources
        const sourceLabels = workflowSources.map(s => `${s.author}, ${s.work}`);

        return {
          answer: result.answer,
          query: query.query,
          // Provide structured sources with nodeId for CitationRenderer
          sources: workflowSources.map((s, index) => ({
            id: index + 1,
            nodeId: s.passage_id || s.work_id || `passage_${index}`,
            nodeLabel: `${s.author}, ${s.work}`,
            nodeType: 'passage' as const,
            content: s.text,
            metadata: {
              author: s.author,
              school: undefined,
              period: undefined,
              confidence: s.score,
              workId: s.work_id, // Include workId for navigation to text reader
            },
          })),
          // Citations in the expected format
          citations: {
            ancient_sources: sourceLabels,
            modern_scholarship: [],
          },
          // Required fields with defaults for workflow responses
          reasoning_path: {
            starting_nodes: workflowSources.slice(0, 3).map((s, i) => ({
              id: s.passage_id || `source_${i}`,
              label: `${s.author}, ${s.work}`,
              type: 'passage',
              reason: 'Retrieved via vectorless evidence routing',
            })),
            expanded_nodes: [],
            traversed_edges: [],
            total_nodes: workflowSources.length,
            total_edges: 0,
          },
          nodes_used: workflowSources.length,
          edges_traversed: 0,
          quality_metrics: {
            confidence_score: result.qualityMetrics?.confidenceScore || 75,
            quality_badge: result.qualityMetrics?.qualityBadge || 'Medium',
            relevance_score: result.qualityMetrics?.relevanceScore,
            grounding_score: result.qualityMetrics?.groundingScore,
            completeness_score: result.qualityMetrics?.completenessScore,
            caveats: result.qualityMetrics?.caveats || [],
          },
          retrieval_stats: {
            hyde_used: result.hydeUsed,
            rerank_used: result.rerankUsed,
            crag_used: result.cragUsed,
            selfrag_used: result.selfragUsed,
            refined: result.refined,
          },
          processing_time: result.processingTime,
          service: 'SOTA GraphRAG Workflow',
          success: result.success ?? true,
        } as GraphRAGResponse;
      } else if (status === 'error') {
        throw new Error(result?.error || 'Workflow failed');
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error('Workflow timed out after 5 minutes. The query may be too complex - try simplifying or using non-academic mode.');
  }

  // Compare original vs enhanced GraphRAG
  async graphragCompare(query: string): Promise<Record<string, unknown>> {
    const response = await this.client.get('/api/graphrag/compare', {
      params: { query },
      timeout: 240000, // 4 minutes for comparison
    });
    return response.data;
  }

  // Get node relationships
  async getNodeRelationships(nodeId: string): Promise<Record<string, unknown>> {
    const response = await this.client.get(`/api/graphrag/relationships/${nodeId}`);
    return response.data;
  }

  // Get philosophical debates
  async getPhilosophicalDebates(limit: number = 10): Promise<Record<string, unknown>> {
    const response = await this.client.get('/api/graphrag/debates', {
      params: { limit }
    });
    return response.data;
  }

  // Get influence chains
  async getInfluenceChains(limit: number = 10): Promise<Record<string, unknown>> {
    const response = await this.client.get('/api/graphrag/influence-chains', {
      params: { limit }
    });
    return response.data;
  }

  // Get enhanced GraphRAG statistics
  async getGraphRAGStats(): Promise<Record<string, unknown>> {
    const response = await this.client.get('/api/graphrag/stats');
    return response.data;
  }

  // ============================================================================
  // CONVERSATION ENDPOINTS (NEW)
  // ============================================================================

  // Create a new conversation
  async createConversation(options?: {
    title?: string;
    settings?: {
      semantic_k?: number;
      graph_depth?: number;
      max_context?: number;
      use_thinking?: boolean;
      academic_mode?: boolean;
      rigor_level?: string;
      citation_style?: string;
    };
  }): Promise<{ success: boolean; conversation: Conversation }> {
    const response = await this.client.post('/api/graphrag/conversations', options || {});
    return response.data;
  }

  // List user's conversations
  async listConversations(limit: number = 50, offset: number = 0): Promise<{
    success: boolean;
    conversations: Conversation[];
    count: number;
  }> {
    const response = await this.client.get('/api/graphrag/conversations', {
      params: { limit, offset },
    });
    return response.data;
  }

  // Get a specific conversation
  async getConversation(conversationId: string): Promise<{
    success: boolean;
    conversation: Conversation;
  }> {
    const response = await this.client.get(`/api/graphrag/conversations/${conversationId}`);
    return response.data;
  }

  // Delete a conversation
  async deleteConversation(conversationId: string): Promise<{
    success: boolean;
    deleted: boolean;
  }> {
    const response = await this.client.delete(`/api/graphrag/conversations/${conversationId}`);
    return response.data;
  }

  // Get messages in a conversation
  async getConversationMessages(
    conversationId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<{
    success: boolean;
    messages: ConversationMessage[];
    count: number;
  }> {
    const response = await this.client.get(
      `/api/graphrag/conversations/${conversationId}/messages`,
      { params: { limit, offset } }
    );
    return response.data;
  }

  // Update conversation (title/settings)
  async updateConversation(
    conversationId: string,
    options: {
      title?: string;
      settings?: {
        semantic_k?: number;
        graph_depth?: number;
        max_context?: number;
        use_thinking?: boolean;
        academic_mode?: boolean;
        rigor_level?: string;
        citation_style?: string;
      };
    }
  ): Promise<{ success: boolean; conversation: Conversation }> {
    const response = await this.client.put(
      `/api/graphrag/conversations/${conversationId}`,
      options
    );
    return response.data;
  }

  // Search conversations by content
  async searchConversations(query: string, limit: number = 20): Promise<{
    success: boolean;
    conversations: Conversation[];
    count: number;
  }> {
    const response = await this.client.get('/api/graphrag/conversations/search', {
      params: { q: query, limit },
    });
    return response.data;
  }

  // ============================================================================
  // LEGACY TEXT ENDPOINTS - REMOVED (2025-11-11)
  // ============================================================================
  // The following methods have been permanently removed as the backend /api/texts/*
  // endpoints no longer exist and the legacy texts table (29 texts) has been dropped.
  //
  // Migration Guide:
  // ❌ listTexts()        → ✅ listWorks()        (258 works)
  // ❌ getText(id)        → ✅ getWork(workId)    (full metadata)
  // ❌ getTextStructure() → ✅ getWorkPassages()  (37,839 passages)
  // ❌ getTextStats()     → ✅ getWorksStats()    (current system)
  // ❌ getTextByKgWorkId()→ ✅ getWork(workId)    (direct mapping)
  // ❌ getPassages()      → ✅ getWorkPassages()  (canonical passages)
  // ❌ getPassage()       → ✅ Use passages API
  // ❌ searchPassages()   → ✅ searchWorks() or hybrid search
  //
  // The texts table was dropped from the database on 2025-11-11.
  // All code should now use the Ancient Works API (ancient_works + passages tables).
  // ============================================================================

  // Ancient Works Endpoints (new canonical works system)
  async listWorks(filters?: {
    author?: string;
    language?: string;
    period?: string;
    source?: string;
    search?: string;
    offset?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/api/works', { params: filters });
    return response.data;
  }

  async getWork(workId: string) {
    const response = await this.client.get(`/api/works/${workId}`);
    return response.data;
  }

  async getWorkPassages(workId: string, filters?: {
    offset?: number;
    limit?: number;
    include_translations?: boolean;
  }) {
    const response = await this.client.get(`/api/works/${workId}/passages`, { params: filters });
    return response.data;
  }

  async searchWorks(query: string, filters?: {
    author?: string;
    language?: string;
    limit?: number;
  }) {
    const response = await this.client.get('/api/works/search', {
      params: {
        query,
        ...filters,
      },
    });
    return response.data;
  }

  async getWorksStats() {
    const response = await this.client.get('/api/works/stats');
    const data = response.data;
    // Current backend nests counts under works/passages; normalize to the
    // flat WorksStats shape the pages consume.
    if (data && typeof data === 'object' && 'works' in data) {
      return {
        total_works: data.works?.total_works ?? 0,
        total_passages: data.passages?.total_passages ?? 0,
        total_citations: data.total_citations,
        top_authors: data.top_authors,
        featured_works: data.featured_works,
      };
    }
    return data;
  }

  async getWorkKGNodes(workId: string) {
    const response = await this.client.get(`/api/works/${workId}/kg-nodes`);
    return response.data;
  }

  // Authentication Endpoints
  async requestCode(email: string): Promise<{ message: string }> {
    const response = await this.client.post('/api/auth/request-code', { email });
    return response.data;
  }

  async requestAccount(
    payload: AccountRequestPayload,
  ): Promise<{ message: string; request_id: string }> {
    const response = await this.client.post('/api/auth/request-account', payload);
    return response.data;
  }

  async verifyCode(
    email: string,
    code: string
  ): Promise<{ access_token: string; token_type: string; expires_in: number }> {
    const response = await this.client.post('/api/auth/verify-code', { email, code });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  async getRateLimitStatus(): Promise<{
    user: string;
    ip: string;
    rate_limit: {
      limit: number;
      remaining: number;
      reset: number;
      window: number;
    };
  }> {
    const response = await this.client.get('/api/auth/rate-limit');
    return response.data;
  }

  async checkSemativersePermission(
    request: SemativersePermissionRequest
  ): Promise<SemativersePermissionResponse> {
    const response = await this.client.post('/api/auth/semativerse/check', request);
    return response.data;
  }

  async getSemativerseStatus() {
    const response = await this.client.get('/api/auth/semativerse/status');
    return response.data;
  }

  // Generic HTTP methods for Phase 6 features and future extensions
  // These expose the underlying axios client for direct access

  /**
   * Generic GET request
   * @param url - API endpoint path (e.g., '/api/admin/statistics')
   * @param config - Optional axios config
   */
  async get<T = unknown>(url: string, config?: Parameters<typeof this.client.get>[1]): Promise<{ data: T }> {
    const response = await this.client.get<T>(url, config);
    return response;
  }

  /**
   * Generic POST request
   * @param url - API endpoint path
   * @param data - Request body
   * @param config - Optional axios config
   */
  async post<T = unknown>(url: string, data?: unknown, config?: Parameters<typeof this.client.post>[2]): Promise<{ data: T }> {
    const response = await this.client.post<T>(url, data, config);
    return response;
  }

  /**
   * Generic PUT request
   * @param url - API endpoint path
   * @param data - Request body
   * @param config - Optional axios config
   */
  async put<T = unknown>(url: string, data?: unknown, config?: Parameters<typeof this.client.put>[2]): Promise<{ data: T }> {
    const response = await this.client.put<T>(url, data, config);
    return response;
  }

  /**
   * Generic DELETE request
   * @param url - API endpoint path
   * @param config - Optional axios config
   */
  async delete<T = unknown>(url: string, config?: Parameters<typeof this.client.delete>[1]): Promise<{ data: T }> {
    const response = await this.client.delete<T>(url, config);
    return response;
  }

  // Lemma Intelligence API Endpoints

  /**
   * Look up a lemma in LSJ (Greek) or Lewis & Short (Latin) dictionary
   */
  async getLemmaDictionary(lemma: string, language: 'grc' | 'lat' = 'grc'): Promise<LemmaDictionaryResponse> {
    const response = await this.client.get(`/api/lemma/dictionary/${encodeURIComponent(lemma)}`, {
      params: { language },
    });
    return response.data;
  }

  /**
   * Search dictionary entries by prefix or fuzzy match
   */
  async searchLemmaDictionary(
    query: string,
    options?: { language?: 'grc' | 'lat'; limit?: number; fuzzy?: boolean }
  ): Promise<LemmaDictionarySearchResponse> {
    const response = await this.client.get(`/api/lemma/dictionary/search/${encodeURIComponent(query)}`, {
      params: options,
    });
    return response.data;
  }

  /**
   * Get corpus statistics for a lemma (occurrences, author/work distribution)
   */
  async getLemmaStats(lemma: string, language: 'grc' | 'lat' = 'grc'): Promise<LemmaStatsResponse> {
    const response = await this.client.get(`/api/lemma/stats/${encodeURIComponent(lemma)}`, {
      params: { language },
    });
    return response.data;
  }

  /**
   * Get lemmas that frequently co-occur with the given lemma
   */
  async getRelatedLemmas(
    lemma: string,
    options?: { language?: 'grc' | 'lat'; limit?: number }
  ): Promise<RelatedLemmasResponse> {
    const response = await this.client.get(`/api/lemma/related/${encodeURIComponent(lemma)}`, {
      params: options,
    });
    return response.data;
  }

  /**
   * Find knowledge graph nodes related to a lemma
   */
  async getLemmaKGConnections(
    lemma: string,
    language: 'grc' | 'lat' = 'grc'
  ): Promise<LemmaKGConnectionsResponse> {
    const response = await this.client.get(`/api/lemma/kg-connections/${encodeURIComponent(lemma)}`, {
      params: { language },
    });
    return response.data;
  }
}

// Knowledge-graph neighbour summary (returned by the grouped neighbors endpoint)
export interface KGNeighborSummary {
  node_id: string;
  label: string;
  node_type?: string | null;
  period?: string | null;
}

export interface KGNodeNeighborsResponse {
  node_id: string;
  node: KGNode;
  neighbors: {
    outgoing: Record<string, KGNeighborSummary[]>;
    incoming: Record<string, KGNeighborSummary[]>;
  };
  total_count: number;
}

// Lemma Intelligence Types
export interface LemmaDictionaryResponse {
  found: boolean;
  language: string;
  dictionary?: string;
  lemma: string;
  lemma_latin?: string;
  definition?: string;
  short_def?: string;
  forms?: string[];
  greek_forms?: string[];
  entry_key?: string;
  message?: string;
  external_links: {
    logeion: string;
    perseus?: string;
    bailly?: string;
  };
}

export interface LemmaDictionarySearchResponse {
  query: string;
  language: string;
  fuzzy: boolean;
  results: Array<{
    lemma: string;
    lemma_latin?: string;
    short_def?: string;
    sim?: number;
  }>;
  count: number;
}

export interface LemmaStatsResponse {
  lemma: string;
  language: string;
  total_occurrences: number;
  passage_count: number;
  by_author: Array<{ author: string; passages: number }>;
  by_work: Array<{ author: string; title: string; passages: number }>;
  by_period: Array<{ period: string; passages: number }>;
}

export interface RelatedLemmasResponse {
  lemma: string;
  language: string;
  related: Array<{
    lemma: string;
    pos: string;
    cooccurrences: number;
  }>;
}

export interface LemmaKGConnectionsResponse {
  lemma: string;
  language: string;
  kg_nodes: Array<{
    node_id: string;
    label: string;
    type: string;
    description?: string;
  }>;
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
