import type { ClaimLedgerEntry, GraphRAGMetadata } from './graphrag';

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
  // Metadata JSONB field from Supabase that may contain additional properties
  metadata?: {
    modern_scholarship?: string | Array<string | { citation?: string; text?: string; title?: string }>;
    [key: string]: unknown;
  };
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
  enable_ai_enhancements?: boolean;
}

export interface SearchResult {
  // IDs
  id?: number | string;
  passage_id?: string;
  work_id?: string;

  // Content
  canonical_ref?: string;
  text_content?: string;
  snippet?: string;

  // Passage location (for full references)
  book?: string | null;
  chapter?: string | null;
  section?: string | null;

  // Metadata
  title: string;
  author: string;
  category?: string;
  language?: string;

  // Scores
  score?: number;
  rank?: number;
  rrf_score?: number;

  // Source indicator
  source?: string;  // 'fulltext' | 'semantic' | 'lemmatic'
}

export interface HybridSearchResponse {
  combined_results: SearchResult[];
  query: string;
  totalResults: number;
  usedSemantic: boolean;
  warning?: string;
  used_rrf?: boolean;
  modes_used?: string[];
  expansions?: string;
  citation_match?: string;
}

// Citation Types for new citation system
export interface SourceCitation {
  id: number;           // Citation number [1], [2], etc.
  nodeId: string;       // Graph node ID for direct access
  nodeLabel: string;    // Human-readable label
  nodeType: string;     // person/concept/argument/work/quote
  content?: string;     // Full node content or summary
  url?: string;         // Deep link to node: /node/{nodeId}
  metadata?: {
    school?: string;
    period?: string;
    author?: string;
    confidence?: number;
  };
}

export interface EvidenceMap {
  [citationNumber: string]: {
    nodeId: string;
    nodePath?: string[];  // For multi-hop connections
    confidence: number;
    type: string;
  };
}

// GraphRAG Types
export interface GraphRAGQuery {
  query: string;
  semantic_k?: number;
  graph_depth?: number;
  max_context?: number;
  temperature?: number;
  deep_mode?: boolean;
  enhanced_mode?: boolean;  // Use enhanced GraphRAG with edge relationships

  // Pipeline mode: 'fast' (normal) or 'auto' (academic with full features)
  mode?: 'fast' | 'auto' | 'local' | 'global' | 'bridge';

  // Feature flags for fine-grained control
  use_hyde?: boolean;       // Legacy flag; ignored by the current vectorless agentic pipeline
  use_expansion?: boolean;  // Query expansion
  use_crag?: boolean;       // Corrective RAG validation
  use_selfrag?: boolean;    // Self-evaluation
  use_debates?: boolean;    // Philosophical debate identification
  use_hierarchy?: boolean;  // Hierarchical retrieval (recommended: true)
  use_reranking?: boolean;  // Reranking (recommended: true)
  use_bridge?: boolean;     // Multi-hop reasoning

  // Conversation memory
  conversation_id?: string;  // Continue existing conversation

  // Thinking mode (Kimi K2)
  use_thinking?: boolean;  // Show step-by-step reasoning

  // Academic mode fields
  academic_mode?: boolean;
  rigor_level?: 'standard' | 'high' | 'maximum';
  citation_style?: 'chicago' | 'apa' | 'harvard';
}

// Conversation types for GraphRAG memory
export interface ConversationSettings {
  semantic_k?: number;
  graph_depth?: number;
  max_context?: number;
  use_thinking?: boolean;
  academic_mode?: boolean;
  rigor_level?: string;
  citation_style?: string;
}

export interface Conversation {
  conversation_id: string;
  user_id: string;
  title: string | null;
  settings: ConversationSettings;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string | null;
}

export interface ConversationMessage {
  message_id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: {
    ancient_sources: string[];
    modern_scholarship: string[];
  };
  reasoning_path?: Record<string, unknown>;
  thinking_process?: string;
  quality_metrics?: Record<string, unknown>;
  tokens_used?: number;
  llm_provider?: string;
  llm_model?: string;
  sequence_number: number;
  created_at: string;
  response_time_ms?: number;
}

// Evidence Chain types for academic mode
export interface AncientCitation {
  citation_text: string;
  confidence: number;
  cts_urn?: string;
}

/** Typed claim-ledger citation emitted by the GraphRAG backend.
 *  Mirrors the backend `Citation` Pydantic model: a resolved id + a
 *  human-readable, deleaked `label`, split by `layer`. */
export interface PassageCitation {
  ref?: string | null;
  type?: string | null;
  id?: string | null;
  label?: string | null;
  layer?: 'primary' | 'secondary' | string | null;
  confidence?: number | null;
  verified?: boolean;
  cts_urn?: string | null;
  doi?: string | null;
  /** Optional structured fields the backend may attach for modern works. */
  author?: string | null;
  year?: number | null;
  title?: string | null;
  publisher?: string | null;
  bibtex_key?: string | null;
}

export interface ModernBibliographyEntry {
  citation_key: string;
  author: string;
  year?: number;
  title: string;
  full_citation_chicago: string;
  full_citation_apa?: string;
  full_citation_harvard?: string;
  bibtex: string;
  page_reference?: string;
}

export interface EvidenceChain {
  claim: string;
  kg_nodes: string[];
  ancient_sources: AncientCitation[];
  modern_sources: ModernBibliographyEntry[];
  confidence: number;
}

/** One node of the curated per-answer subgraph (`reasoning_path.subgraph`). */
export interface AnswerSubgraphNode {
  /** Graph-unique id (`frame:…`, `pos:…`, a passage id, or a KG node id). */
  id: string;
  /** Clickable KG node / passage id, when this node resolves to one. */
  ref?: string;
  label: string;
  /** KG node type (`debate`, `person`, `concept`, `passage`, …) — drives color. */
  type: string;
  /** Where the node came from: `controversy_frame`, `position`,
   *  `contested_passage`, `seed`, `activated`. */
  origin?: string;
  /** Retrieval salience, 0-1 — drives node size. */
  score?: number;
  /** True for the nodes that hang directly off the question. */
  root?: boolean;
  detail?: string;
  publication?: string;
  cts_urn?: string;
}

export interface AnswerSubgraphEdge {
  source: string;
  target: string;
  relation: string;
  gloss?: string;
}

export interface AnswerSubgraph {
  nodes: AnswerSubgraphNode[];
  edges: AnswerSubgraphEdge[];
  stats?: {
    node_count: number;
    edge_count: number;
    frame_count: number;
    position_count: number;
    passage_count: number;
    kg_node_count: number;
    candidate_nodes: number;
    candidate_edges: number;
    truncated: boolean;
  };
}

export interface GraphRAGResponse {
  /** Provenance id emitted by the streaming endpoint and persisted in query_traces. */
  trace_id?: string;
  query: string;
  answer: string;
  metadata?: GraphRAGMetadata;
  /** Atomic, evidence-linked claims; inferred edges carry a proof_chain. */
  claim_ledger?: ClaimLedgerEntry[];
  citations: {
    ancient_sources: string[];
    modern_scholarship: string[];
  };
  // New citation system fields
  sources?: SourceCitation[];
  /** Typed, resolved claim-ledger citations from the backend (B-backend).
   *  Each entry carries a real node/passage id + a deleaked display label,
   *  split by `layer` (primary = ancient sources, secondary = modern
   *  scholarship). Drives clickable inline badges and the References panel. */
  passage_citations?: PassageCitation[];
  evidenceMap?: EvidenceMap;
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
    /** Curated per-answer knowledge graph: the controversy frames the retrieval
     *  surfaced (positions, dialectical links, contested passages) joined with
     *  the KG nodes the agent actually activated. Optional — legacy responses
     *  and cached rows written before it existed simply omit it. */
    subgraph?: AnswerSubgraph;
    total_nodes: number;
    total_edges: number;
  };
  quality_metrics?: {
    // Legacy fields
    citationCount?: number;
    sourceCount?: number;
    nodeRelevanceScore?: number;
    contextCoherence?: number;
    answerCompleteness?: number;
    overallQuality?: number;
    // New workflow fields (SOTA GraphRAG)
    confidence_score?: number;
    quality_badge?: 'High' | 'Medium' | 'Low' | string;
    relevance_score?: number;
    grounding_score?: number;
    completeness_score?: number;
    caveats?: string[];
  };
  retrieval_stats?: {
    hyde_used?: boolean;
    rerank_used?: boolean;
    crag_used?: boolean;
    selfrag_used?: boolean;
    refined?: boolean;
  };
  processing_time?: number;
  argument_mapping?: {
    id: string;
    claim: string;
    premises: Array<{
      id: string;
      text: string;
      source: string;
    }>;
    objections?: Array<{
      id: string;
      text: string;
      source: string;
    }>;
    responses?: Array<{
      id: string;
      text: string;
      source: string;
    }>;
    conclusion: string;
    relatedConcepts: string[];
  };
  concept_evolution?: {
    conceptId: string;
    conceptLabel: string;
    timeline: Array<{
      period: string;
      dateRange: string;
      formulation: string;
      author?: string;
      work?: string;
      greekTerm?: string;
      latinTerm?: string;
      significance: string;
    }>;
  };
  nodes_used: number;
  edges_traversed: number;
  /** Client-side flag: the stream ended without a terminal `complete` event,
   *  so this response was reconstructed from what the run had already emitted. */
  degraded?: boolean;
  service?: string;  // e.g., "Agentic GraphRAG" or "GraphRAG (fallback)"
  hierarchy_stats?: {
    level_0_used: number;
    level_1_used: number;
    level_2_used: number;
    bridges_used: number;
  };
  context_levels?: {
    local: number;
    global: number;
    bridge: number;
  };
  tokens_used?: number;
  llm_provider?: string;
  llm_model?: string;
  thinking_process?: string;  // Kimi K2 thinking process
  conversation_id?: string;  // Conversation ID for memory
  reasoning_trace?: Array<{
    node: string;
    duration_ms: number;
    model: string | null;
    skipped: boolean;
    skip_reason: string | null;
    raw_output: string;
    thinking: string | null;
    parsed_result: Record<string, unknown> | null;
  }>;
  success: boolean;
  // Academic mode evidence and bibliography
  evidence_chains?: EvidenceChain[];
  modern_bibliography?: ModernBibliographyEntry[];
  chicago_bibliography?: string;
  apa_bibliography?: string;
  harvard_bibliography?: string;
  bibtex_bibliography?: string;
  cts_urns?: string[];

  // Verified passages with original Greek/Latin text
  verified_passages?: Array<{
    passage_id: string;
    cts_urn: string | null;
    work_title: string;
    work_title_original: string | null;
    author: string;
    author_original: string | null;
    language: string;
    reference: string;
    original_text: string;
    transliteration: string;
    char_start: number;
    char_end: number;
    confidence: number;
  }>;

  // Response metrics (cost, model, context usage)
  metrics?: {
    processing_time_s?: number;
    model_key?: string;
    model_label?: string;
    retrieval_mode_used?: string;
    estimated_cost_usd?: number;
    answer_length_chars?: number;
  };

  // Enhanced GraphRAG fields
  enhanced?: boolean;
  relationship_types_used?: number;
  debates_found?: number;
  influence_chains?: number;
  enhancements?: {
    mode: 'original' | 'enhanced';
    relationship_types_used?: number;
    debates_found?: number;
    influence_chains?: number;
  };
}

// GraphRAG SSE Event Types
export interface GraphRAGStreamEvent {
  type:
    | 'status'
    | 'nodes'
    | 'citations'
    | 'thinking_chunk'
    | 'thinking_complete'
    | 'answer_chunk'
    | 'synthesis_reasoning'
    | 'research_note'
    | 'citations_preview'
    | 'complete'
    | 'error'
    | 'agent_thinking'
    | 'tool_start'
    | 'tool_result'
    | 'tokens_used_rollup'
    | 'cost_summary'
    | 'cache_hit';
  message?: string;
  step?: number;
  total_steps?: number;
  data?: GraphRAGResponse | string | AgentToolEvent | Record<string, unknown>;
  progress?: number;
}

// Agent tool call events (ReAct loop)
export interface AgentToolEvent {
  tool?: string;
  args?: Record<string, unknown>;
  reason?: string;
  thinking?: string;
  summary?: string;
  duration_ms?: number;
  node_count?: number;
  passage_count?: number;
  step?: number;
  remaining?: number;
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
  lemmas?: string[];
  metadata?: Record<string, unknown>;
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
    [key: string]: string | number | boolean | undefined;
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
  quality?: number | null;
  communities: CommunitySummary[];
  availableAlgorithms: CommunityAlgorithmOption[];
}

export interface CytoscapeData {
  elements?: {
    nodes?: CytoscapeElement[];
    edges?: CytoscapeElement[];
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
  thinking_process?: string;  // NEW: Kimi K2 thinking process
  tokens_used?: number;
  llm_provider?: string;
  llm_model?: string;
  retrieval_mode?: string;
  timestamp: Date;
  citationTexts?: Record<string, { original: string; originalLanguage: string; translation: string }>;
  graphrag_response?: GraphRAGResponse;
  reasoning_steps?: Array<{
    id: number;
    type: string;
    label: string;
    description: string;
    status: string;
    nodes?: string[];
    edges?: string[];
    duration?: number;
    metadata?: Record<string, unknown>;
  }>;
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

export interface MatrixAxis {
  key: string;
  label: string;
  type: 'school' | 'relation' | 'period' | 'node_type';
  order?: number;
  metadata?: Record<string, unknown>;
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
  dateRange?: [number, number] | null;
}

export interface KGSelectionState {
  nodes: string[];
  edges: string[];
  focusNodeId?: string | null;
}

// Ancient Works Types (new canonical works system)
export interface AncientWork {
  work_id: string;
  canonical_id: string;
  title: string;
  author: string;
  language: string;
  period?: string | null;
  source: string;
  tlg_code?: string | null;
  passage_count: number;
  total_chars: number;
  date_composed?: string | null;
  school?: string | null;
  source_url?: string | null;
  license?: string | null;
  notes?: string | null;
  metadata?: Record<string, unknown> | null;
  kg_citations?: number;
}

export interface FeaturedWork {
  work_id: string;
  title: string;
  author: string;
}

export interface AuthorStats {
  author: string;
  passage_count: number;
}

export interface WorksStats {
  total_works: number;
  total_passages: number;
  total_citations?: number;
  top_authors?: AuthorStats[];
  featured_works?: FeaturedWork[];
}

export interface WorksListResponse {
  works: AncientWork[];
  total: number;
  offset: number;
  limit: number;
}

export interface WorkPassage {
  passage_id: string;
  work_id: string;
  reference: string;
  book?: string | null;
  chapter?: string | null;
  section?: string | null;
  content: string;
  lemmatized_content?: string | null;
  morphology?: Record<string, unknown> | null;
}

export interface WorkKGNode {
  kg_node_id: string;
  citation_count: number;
  passage_ids: string[];
  canonical_refs: string[];
  first_sequence: number;
  first_passage_id: string;
  first_canonical_ref: string;
}

export interface WorkKGNodesResponse {
  work_id: string;
  work_title: string;
  work_author: string;
  kg_nodes: WorkKGNode[];
  total_nodes: number;
}
