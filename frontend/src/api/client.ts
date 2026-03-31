import axios from 'axios';
import Cookies from 'js-cookie';
import type { AxiosInstance } from 'axios';
import type {
  KGData,
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
import type { User, LoginCredentials } from '../context/AuthContext';

const rawApiUrl = import.meta.env.VITE_API_URL;
const API_URL = (
  typeof rawApiUrl === 'string' && rawApiUrl.trim().length > 0
    ? rawApiUrl.trim()
    : 'http://localhost:8000'
).replace(/\/+$/, '');

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
  async getNodes(filters?: { type?: string; period?: string; school?: string; limit?: number; offset?: number }): Promise<{ nodes: KGData['nodes'] }> {
    const response = await this.client.get('/api/kg/nodes', { params: filters });
    const data = response.data;
    // Backend returns a raw array; normalize to { nodes: [...] }
    if (Array.isArray(data)) {
      return { nodes: data };
    }
    return data;
  }

  async getEdges(filters?: { relation?: string; limit?: number; offset?: number }): Promise<KGData['edges']> {
    const response = await this.client.get('/api/kg/edges', { params: filters });
    const data = response.data;
    // Backend returns a raw array; normalize
    return Array.isArray(data) ? data : (data?.edges ?? []);
  }

  async getNode(id: string) {
    const response = await this.client.get(`/api/kg/node/${id}`);
    return response.data;
  }

  async getNodeConnections(id: string) {
    const response = await this.client.get(`/api/kg/node/${id}/connections`);
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

  async semanticSearch(query: string, limit: number = 10, collection: string = 'text_embeddings') {
    const response = await this.client.post('/api/search/semantic', {
      query,
      limit,
      collection,
    });
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
              reason: 'Retrieved via semantic search',
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
    return response.data;
  }

  async getWorkKGNodes(workId: string) {
    const response = await this.client.get(`/api/works/${workId}/kg-nodes`);
    return response.data;
  }

  // Authentication Endpoints
  async login(credentials: LoginCredentials): Promise<{ access_token: string; token_type: string; expires_in: number }> {
    const response = await this.client.post('/api/auth/login', credentials);
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
