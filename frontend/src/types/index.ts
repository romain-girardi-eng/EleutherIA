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
  id: number;
  score?: number;
  payload: {
    text_id?: string;
    title: string;
    author: string;
    category: string;
    language: string;
    text_length?: number;
    generated_at?: number;
  };
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
  tokens_used?: number;
  llm_provider?: string;
  llm_model?: string;
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

export interface CommunityAlgorithmOption {
  name: string;
  available: boolean;
  description: string;
}

export interface CommunitySummary {
  id: number;
  size: number;
  order: number;
  color: string;
  label: string;
}

export interface CommunityMeta {
  algorithmRequested: string;
  algorithmUsed: string;
  quality: number | null;
  communities: CommunitySummary[];
  availableAlgorithms: CommunityAlgorithmOption[];
}

export interface CytoscapeData {
  elements: {
    nodes: CytoscapeElement[];
    edges: CytoscapeElement[];
  };
  meta?: {
    community?: CommunityMeta;
    [key: string]: unknown;
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
  tokens_used?: number;
  llm_provider?: string;
  llm_model?: string;
  timestamp: Date;
}

// Visualization Aggregates
export interface TimelineNodeSummary {
  id: string;
  label: string;
  type: string;
  period?: string | null;
  school?: string | null;
  startYear?: number | null;
  endYear?: number | null;
  description?: string | null;
  significance?: string | null;
  relationCount?: number;
  relatedTypes?: string[];
}

export interface TimelinePeriodSummary {
  key: string;
  label: string;
  startYear?: number | null;
  endYear?: number | null;
  counts: Record<string, number>;
  nodes: TimelineNodeSummary[];
}

export interface TimelineOverview {
  periods: TimelinePeriodSummary[];
  totals: {
    nodes: number;
    edges: number;
    byType: Record<string, number>;
  };
  range: {
    minYear?: number | null;
    maxYear?: number | null;
  };
}

export type EvidenceNodeGroup = 'argument' | 'ancient_source' | 'modern_reception';

export interface EvidenceNode {
  id: string;
  label: string;
  group: EvidenceNodeGroup;
  size: number;
  argumentIds?: string[];
  metadata?: Record<string, any>;
}

export interface EvidenceLink {
  source: string;
  target: string;
  value: number;
  argumentId?: string;
  relation?: string;
}

export interface ArgumentEvidenceSummary {
  id: string;
  label: string;
  period?: string | null;
  school?: string | null;
  ancientCount: number;
  modernCount: number;
  totalConnections: number;
  description?: string | null;
}

export interface ArgumentEvidenceOverview {
  nodes: EvidenceNode[];
  links: EvidenceLink[];
  arguments: ArgumentEvidenceSummary[];
  stats: {
    totalArguments: number;
    totalAncientSources: number;
    totalModernReception: number;
  };
}

export interface ConceptClusterNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
  period?: string | null;
  school?: string | null;
  keywords?: string[];
}

export interface ConceptClusterSummary {
  id: string;
  label: string;
  size: number;
  keywords: string[];
  nodes: ConceptClusterNode[];
  metadata?: Record<string, any>;
}

export interface ConceptClusterOverview {
  clusters: ConceptClusterSummary[];
  stats: {
    totalConcepts: number;
    clusterCount: number;
  };
}

export interface MatrixAxis {
  key: string;
  label: string;
  type: 'school' | 'relation' | 'period' | 'node_type';
  order?: number;
  metadata?: Record<string, any>;
}

export interface InfluenceMatrixCell {
  rowKey: string;
  columnKey: string;
  count: number;
  sampleEdges?: string[];
}

export interface InfluenceMatrixOverview {
  rows: MatrixAxis[];
  columns: MatrixAxis[];
  cells: InfluenceMatrixCell[];
  totals: {
    relationsConsidered: number;
    schoolsCovered: number;
    edgesMapped: number;
  };
}

export interface KGPathNode {
  id: string;
  label: string;
  type: string;
  period?: string | null;
  school?: string | null;
  description?: string | null;
}

export interface KGPathEdge {
  source: string;
  target: string;
  relation: string;
  description?: string | null;
}

export interface KGPathResponse {
  nodes: KGPathNode[];
  edges: KGPathEdge[];
  length: number;
  summary?: string;
  warnings?: string[];
}

export interface KGPathRequest {
  sourceId: string;
  targetId: string;
  maxDepth?: number;
  allowBidirectional?: boolean;
  relationWhitelist?: string[];
  relationBlacklist?: string[];
}

export interface KGFilterState {
  nodeTypes: string[];
  periods: string[];
  schools: string[];
  relations: string[];
  searchTerm?: string;
}

export interface KGSelectionState {
  nodes: string[];
  edges: string[];
  focusNodeId?: string | null;
}
