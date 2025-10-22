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
  AncientText,
  SemativersePermissionRequest,
  SemativersePermissionResponse,
  TimelineOverview,
  ArgumentEvidenceOverview,
  ConceptClusterOverview,
  InfluenceMatrixOverview,
  KGFilterState,
  KGPathRequest,
  KGPathResponse,
} from '../types';
import type { User, LoginCredentials } from '../context/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
        if (error.response?.status === 401) {
          // Token expired or invalid, clear it
          Cookies.remove('auth_token');
          // Optionally redirect to login
          if (window.location.pathname !== '/login') {
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
  async getNodes(filters?: { type?: string; period?: string; school?: string }): Promise<KGData['nodes']> {
    const response = await this.client.get('/api/kg/nodes', { params: filters });
    return response.data;
  }

  async getEdges(filters?: { relation?: string }): Promise<KGData['edges']> {
    const response = await this.client.get('/api/kg/edges', { params: filters });
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

  async getCytoscapeData(options?: { algorithm?: string }): Promise<CytoscapeData> {
    const params = options?.algorithm
      ? { communityAlgorithm: options.algorithm }
      : undefined;
    const response = await this.client.get('/api/kg/viz/cytoscape', { params });
    const data = response.data as CytoscapeData & {
      meta?: {
        community?: any;
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
            ? community.communities.map((entry: any) => ({
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
            ? (community.availableAlgorithms ?? community.available_algorithms).map((option: any) => ({
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

  async getArgumentEvidenceOverview(filters?: Partial<KGFilterState>): Promise<ArgumentEvidenceOverview> {
    const response = await this.client.get('/api/kg/analytics/argument-flow', { params: filters });
    return response.data;
  }

  async getConceptClusterOverview(filters?: Partial<KGFilterState>): Promise<ConceptClusterOverview> {
    const response = await this.client.get('/api/kg/analytics/concept-clusters', { params: filters });
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

  async searchKG(query: string, limit: number = 10) {
    const response = await this.client.post('/api/search/kg', { query, limit });
    return response.data;
  }

  // GraphRAG Endpoints
  async graphragQuery(query: GraphRAGQuery): Promise<GraphRAGResponse> {
    const response = await this.client.post('/api/graphrag/query', query, {
      timeout: 120000, // 2 minutes for complex queries
    });
    return response.data;
  }

  // GraphRAG Streaming (returns EventSource)
  graphragQueryStream(query: GraphRAGQuery): EventSource {
    const params = new URLSearchParams(query as any);
    const url = `${API_URL}/api/graphrag/query/stream?${params}`;

    return new EventSource(url, {
      withCredentials: false,
    });
  }

  async graphragStatus() {
    const response = await this.client.get('/api/graphrag/status');
    return response.data;
  }

  // Text Endpoints
  async listTexts(filters?: {
    category?: string;
    author?: string;
    language?: string;
    offset?: number;
    limit?: number;
  }) {
    const response = await this.client.get('/api/texts/list', { params: filters });
    return response.data;
  }

  async getText(id: string): Promise<AncientText> {
    const response = await this.client.get(`/api/texts/${id}`);
    return response.data;
  }

  async getTextStructure(id: string) {
    const response = await this.client.get(`/api/texts/${id}/structure`);
    return response.data;
  }

  async getTextStats() {
    const response = await this.client.get('/api/texts/stats/overview');
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

  async getRateLimitStatus(): Promise<{ user: string; ip: string; rate_limit: any }> {
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
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
