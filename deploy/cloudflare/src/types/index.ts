/**
 * Type definitions for Ancient Free Will Database API
 */

// Cloudflare Workers Environment
export interface Env {
  // Supabase
  SUPABASE_URL: string;
  SUPABASE_KEY: string;

  // Qdrant
  QDRANT_HOST: string;
  QDRANT_API_KEY: string;

  // Gemini
  GEMINI_API_KEY: string;

  // Moonshot (Kimi K2 Thinking)
  MOONSHOT_API_KEY?: string;
  MOONSHOT_BASE_URL?: string;

  // Cloudflare bindings
  TEXT_CACHE: KVNamespace;
  API_ANALYTICS?: AnalyticsEngineDataset;

  // Configuration
  ALLOWED_ORIGINS: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
  EMBEDDING_DIMENSIONS: string;

  // Authentication
  JWT_SECRET_KEY: string;
  SEMATIVERSE_ACCESS_KEY: string;
}

// Knowledge Graph Types
export interface KGNode {
  id: string;
  name: string;
  type: string;
  description: string;
  period?: string;
  school?: string;
  [key: string]: any;
}

// Alias for compatibility
export type GraphNode = KGNode;

// Query classification types
export type QueryType =
  | 'global_abstract'       // "What is Stoic free will?"
  | 'specific_entity'       // "What did Chrysippus say?"
  | 'comparative'           // "How do Stoics differ from Epicureans?"
  | 'temporal_evolution'    // "How did prohairesis evolve?"
  | 'dialectical'          // "Arguments for compatibilism"
  | 'multi_hop';           // "How did Stoic determinism influence Christian debates?"

export interface QueryClassification {
  type: QueryType;
  confidence: number;
  entities?: string[];
  concepts?: string[];
  schools?: string[];
}

export interface KGEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  description?: string;
  [key: string]: any;
}

// Alias for compatibility
export type GraphEdge = KGEdge;

export interface KGData {
  nodes: KGNode[];
  edges: KGEdge[];
}

export interface CytoscapeElement {
  data: {
    id: string;
    [key: string]: any;
  };
  classes?: string;
}

export interface CytoscapeData {
  elements: CytoscapeElement[];
  meta?: {
    community?: {
      algorithmRequested: string;
      algorithmUsed: string;
      quality: number | null;
      communities: Array<{
        id: number;
        size: number;
        order: number;
        color: string;
        label: string;
      }>;
      availableAlgorithms: Array<{
        name: string;
        available: boolean;
        description: string;
      }>;
    };
  };
}

// Search Types
export interface SearchQuery {
  query: string;
  limit?: number;
  filters?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  score: number;
  content: string;
  metadata: Record<string, any>;
}

export interface HybridSearchResponse {
  results: SearchResult[];
  query: string;
  totalResults: number;
}

// GraphRAG Types
export interface GraphRAGQuery {
  query: string;
  mode?: 'local' | 'global';
  maxCommunities?: number;
  includeEvidence?: boolean;
}

export interface GraphRAGResponse {
  answer: string;
  communities?: any[];
  evidence?: any[];
  sources?: string[];
  processingTime?: number;
}

// Text Types
export interface AncientText {
  id: string;
  title: string;
  author: string;
  language: string;
  category: string;
  content: any;
  metadata?: Record<string, any>;
}

// Database Query Result
export interface QueryResult<T = any> {
  rows: T[];
  rowCount: number;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Health Check
export interface HealthCheck {
  status: string;
  database: string;
  qdrant: string;
  llm: string;
  timestamp: string;
}

// =============================================================================
// ADVANCED RAG ENHANCEMENT TYPES (2025 State-of-the-Art)
// =============================================================================

/**
 * HyDE (Hypothetical Document Embeddings) result
 */
export interface HyDEResult {
  hypotheticalDocument: string;
  searchResults: HyDESearchResult[];
  searchTime: number;
}

export interface HyDESearchResult {
  id: string | number;
  score: number;
  passageId?: string;
  author?: string;
  work?: string;
  text?: string;
  language?: string;
  payload: Record<string, any>;
}

/**
 * Query expansion result
 */
export interface ExpandedQuery {
  originalQuery: string;
  greekTerms: Array<{ greek: string; transliteration: string; translation: string }>;
  latinTerms: Array<{ latin: string; translation: string }>;
  philosophers: string[];
  concepts: string[];
  schools: string[];
  periods: string[];
  expandedSearchTerms: string[];
}

/**
 * Reranking result
 */
export interface RerankResult {
  id: string | number;
  originalScore?: number;
  rerankScore: number;
  relevanceReason: string;
  text: string;
  author?: string;
  work?: string;
  metadata?: Record<string, any>;
}

/**
 * CRAG (Corrective RAG) validation result
 */
export interface CRAGValidationResult {
  isValid: boolean;
  relevanceScore: number;
  completenessScore: number;
  confidenceScore: number;
  needsSecondaryRetrieval: boolean;
  missingAspects: string[];
  suggestions: string[];
  validationTime: number;
}

/**
 * SELF-RAG evaluation result
 */
export interface SelfRAGEvaluation {
  relevanceScore: number;
  groundingScore: number;
  completenessScore: number;
  confidenceScore: number;
  qualityBadge: 'High' | 'Medium' | 'Low';
  shouldRefine: boolean;
  caveats: string[];
  improvements: string[];
  evaluationTime: number;
}

/**
 * Evidence trace for explainability
 */
export interface EvidenceTrace {
  nodeId: string;
  nodeLabel: string;
  nodeType: string;
  school?: string;
  selectionPath: Array<{
    method: string;
    score?: number;
    relation?: string;
    reason: string;
    timestamp: number;
  }>;
  finalScore: number;
  confidenceLevel: 'high' | 'medium' | 'low';
}

/**
 * Debate intensity score
 */
export interface DebateScore {
  score: number;
  level: 'MAJOR' | 'SIGNIFICANT' | 'MINOR';
  schools: string[];
  periods: string[];
  keyFigures: string[];
  conflictCount: number;
  metrics: {
    conflictIntensity: number;
    temporalSpan: number;
    schoolDiversity: number;
    philosopherCentrality: number;
  };
}

/**
 * Identified philosophical debate
 */
export interface IdentifiedDebate {
  topic: string;
  description: string;
  score: DebateScore;
}

/**
 * Enhanced GraphRAG response with all 2025 features
 */
export interface EnhancedGraphRAGResponseV2 extends EnhancedGraphRAGResponse {
  // Quality metrics
  qualityScore: number;
  qualityBadge: 'High' | 'Medium' | 'Low';
  caveats: string[];

  // Evidence explainability
  evidenceTraces: EvidenceTrace[];

  // Temporal context
  temporalDistribution?: {
    presocratic?: string[];
    classical?: string[];
    hellenistic?: string[];
    imperial?: string[];
    late_antiquity?: string[];
  };

  // Debates identified
  debatesIdentified: IdentifiedDebate[];

  // Retrieval strategy used
  retrievalStrategy: {
    hydeUsed: boolean;
    queryExpanded: boolean;
    reranked: boolean;
    cragValidated: boolean;
    cragTriggeredSecondary: boolean;
    selfEvaluated: boolean;
  };

  // Query expansion details
  queryExpansion?: ExpandedQuery;

  // CRAG validation result
  cragValidation?: CRAGValidationResult;

  // SELF-RAG evaluation
  selfEvaluation?: SelfRAGEvaluation;
}

// =============================================================================
// EVIDENCE CHAINS & CITATION TYPES
// =============================================================================

/**
 * Ancient source citation with full scholarly metadata
 */
export interface AncientCitation {
  /** Display text for the citation */
  citationText: string;
  /** Database passage ID if available */
  passageId?: string;
  /** Database work ID */
  workId?: string;
  /** CTS URN for canonical reference */
  ctsUrn?: string;
  /** Work title */
  title: string;
  /** Author name */
  author: string;
  /** Original Greek or Latin text */
  originalText?: string;
  /** English translation */
  translation?: string;
  /** Language: 'greek' or 'latin' */
  language?: string;
  /** Reference within work (e.g., "1.1", "43") */
  reference?: string;
  /** Confidence score 0.0-1.0 */
  confidence: number;
}

/**
 * Modern scholarship bibliography entry
 */
export interface ModernCitation {
  /** Citation key for reference */
  citationKey: string;
  /** Author name(s) */
  author: string;
  /** Publication year */
  year: number;
  /** Title of work */
  title: string;
  /** Publisher */
  publisher?: string;
  /** Journal name if article */
  journal?: string;
  /** Page range */
  pages?: string;
  /** DOI if available */
  doi?: string;
  /** Formatted citation (Chicago style) */
  formattedCitation?: string;
}

/**
 * Evidence chain linking a claim to its sources
 */
export interface EvidenceChain {
  /** The claim being supported */
  claim: string;
  /** KG node IDs used as evidence */
  kgNodes: string[];
  /** Ancient source citations */
  ancientSources: AncientCitation[];
  /** Modern scholarship citations */
  modernSources: ModernCitation[];
  /** Overall confidence score 0.0-1.0 */
  confidence: number;
}

/**
 * Enhanced GraphRAG response with full scholarly apparatus
 */
export interface EnhancedGraphRAGResponse {
  /** The generated answer */
  answer: string;
  /** Query that was asked */
  query: string;
  /** Source labels used */
  sources: string[];
  /** Structured evidence chains */
  evidenceChains: EvidenceChain[];
  /** CTS URNs for all cited passages */
  ctsUrns: string[];
  /** Ancient citations with metadata */
  ancientCitations: AncientCitation[];
  /** Modern bibliography */
  modernBibliography: ModernCitation[];
  /** Retrieval statistics */
  retrievalStats: {
    totalNodes: number;
    totalEdges: number;
    passageNodes: number;
  };
  /** Processing time in ms */
  processingTime: number;
  /** Whether request succeeded */
  success: boolean;
}
