import axios from 'axios';
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

  async getCytoscapeData(): Promise<CytoscapeData> {
    const response = await this.client.get('/api/kg/viz/cytoscape');
    return response.data;
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
