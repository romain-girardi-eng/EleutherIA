// Knowledge Graph Types
export interface KGNode {
  id: string;
  label: string;
  type: string;
  category?: string;
  description?: string;
  period?: string;
  school?: string;
  dates?: string;
  position_on_free_will?: string;
  ancient_sources?: string[];
  modern_scholarship?: string[];
  greek_term?: string;
  latin_term?: string;
  english_term?: string;
}

export interface KGEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  description?: string;
}

export interface KGData {
  nodes: KGNode[];
  edges: KGEdge[];
}

// Search Types
export interface SearchQuery {
  query: string;
  limit?: number;
  enable_fulltext?: boolean;
  enable_lemmatic?: boolean;
  enable_semantic?: boolean;
}

export interface SearchResult {
  id: string;
  title: string;
  author: string;
  category: string;
  language: string;
  rank?: number;
  rrf_score?: number;
  snippet?: string;
}

export interface HybridSearchResponse {
  combined_results: SearchResult[];
  fulltext_results: SearchResult[];
  lemmatic_results: SearchResult[];
  semantic_results: SearchResult[];
  total_found: number;
}

// GraphRAG Types
export interface GraphRAGQuery {
  query: string;
  semantic_k?: number;
  graph_depth?: number;
  max_context?: number;
  temperature?: number;
  deep_mode?: boolean;
}

export interface GraphRAGResponse {
  query: string;
  answer: string;
  citations: {
    ancient_sources: string[];
    modern_scholarship: string[];
  };
  reasoning_path: {
    starting_nodes: Array<{
      id: string;
      label: string;
      type: string;
      reason: string;
    }>;
    expanded_nodes: Array<{
      id: string;
      label: string;
      type: string;
      reason: string;
    }>;
    traversed_edges: Array<{
      source: string;
      target: string;
      relation: string;
      description: string;
    }>;
    total_nodes: number;
    total_edges: number;
  };
  nodes_used: number;
  edges_traversed: number;
  success: boolean;
}

// GraphRAG SSE Event Types
export interface GraphRAGStreamEvent {
  type: 'status' | 'nodes' | 'citations' | 'answer_chunk' | 'complete' | 'error';
  message?: string;
  step?: number;
  total_steps?: number;
  data?: any;
  progress?: number;
}

// Text Types
export interface AncientText {
  id: string;
  kg_work_id: string;
  title: string;
  author: string;
  category: string;
  language: string;
  date_created: string;
  source: string;
  raw_text: string;
  normalized_text: string;
  lemmas?: any;
  metadata?: any;
}

// Cytoscape Types
export interface CytoscapeElement {
  data: {
    id: string;
    label?: string;
    type?: string;
    source?: string;
    target?: string;
    relation?: string;
    [key: string]: any;
  };
  classes?: string;
}

export interface CytoscapeData {
  elements: {
    nodes: CytoscapeElement[];
    edges: CytoscapeElement[];
  };
}

// Auth Types
export interface SemativersePermissionRequest {
  access_key: string;
}

export interface SemativersePermissionResponse {
  has_permission: boolean;
  message: string;
}

// API Response Wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// Component Props Types
export interface VisualizerMode {
  mode: 'cytoscape' | 'semativerse';
}

export interface GraphRAGChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: GraphRAGResponse['citations'];
  reasoning_path?: GraphRAGResponse['reasoning_path'];
  timestamp: Date;
}
