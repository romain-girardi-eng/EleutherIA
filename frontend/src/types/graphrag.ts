/**
 * GraphRAG TypeScript Type Definitions
 * Interfaces for reasoning paths, steps, and GraphRAG responses
 */

export type ReasoningStepType = 'search' | 'traverse' | 'context' | 'synthesis' | 'complete';
export type StepStatus = 'pending' | 'active' | 'complete' | 'error';
export type ResearchStageStatus = 'complete' | 'skipped' | 'degraded';

export interface ResearchGraphMetric {
  label: string;
  value: string | number | boolean | null | undefined;
}

export interface ResearchGraphStage {
  id: string;
  title: string;
  status: ResearchStageStatus;
  summary: string;
  metrics?: ResearchGraphMetric[];
  details?: Record<string, unknown> | null;
}

export interface ResearchGraphFacet {
  facet_id: string;
  title: string;
  question: string;
  summary?: string;
  required_support?: string;
  priority?: number;
  primary_count: number;
  testimony_count: number;
  counter_count: number;
  metadata_count: number;
  note_count: number;
  uncertainty_count: number;
}

export interface ResearchGraphWorkSection {
  node_id?: string;
  title?: string;
  path?: string;
}

export interface ResearchGraphWork {
  work_id: string;
  title: string;
  author?: string;
  bundle_count: number;
  section_count: number;
  primary_count: number;
  testimony_count: number;
  counter_count: number;
  has_translation: boolean;
  languages: string[];
  canonical_refs: string[];
  sections: ResearchGraphWorkSection[];
}

export interface ResearchGraphClaim {
  claim: string;
  facet_id?: string | null;
  evidence_class: string;
  support_type: string;
  confidence: number;
  status: string;
  evidence_ids: string[];
  refs: string[];
  quote_original?: string | null;
  quote_translation?: string | null;
}

export interface ResearchGraphToolCall {
  tool_call_id: string;
  tool_name: string;
  stage_id: string;
  status: string;
  query?: string | null;
  rationale?: string | null;
  work_id?: string | null;
  work_title?: string | null;
  section_path?: string | null;
  selected_ids: string[];
  detail_count: number;
  details?: Record<string, unknown> | null;
}

export interface ResearchGraphDecision {
  decision_id: string;
  stage_id: string;
  decision_type: string;
  title: string;
  rationale: string;
  facet_id?: string | null;
  selected_ids: string[];
  rejected_ids: string[];
  supporting_refs: string[];
  metadata?: Record<string, unknown> | null;
}

export interface ResearchGraphOverview {
  query_type?: string;
  complexity?: string;
  grounding_policy?: string;
  quality_badge?: string;
  pipeline_degraded?: boolean;
  claim_ledger_mode?: string;
  render_answer_mode?: string;
  scholarly_polish_mode?: string;
  seed_node_count?: number;
  context_node_count?: number;
  bundle_count?: number;
  work_count?: number;
  claim_count?: number;
  citation_count?: number;
  tool_call_count?: number;
  decision_count?: number;
}

export interface ResearchGraphPayload {
  overview: ResearchGraphOverview;
  stages: ResearchGraphStage[];
  facets: ResearchGraphFacet[];
  works: ResearchGraphWork[];
  claims: ResearchGraphClaim[];
  hypotheses: string[];
  open_questions: string[];
  counter_evidence: string[];
  uncertainties: string[];
  tool_calls: ResearchGraphToolCall[];
  reading_decisions: ResearchGraphDecision[];
}

export interface GraphRAGMetadata {
  research_graph?: ResearchGraphPayload;
  debug_trace?: Record<string, unknown>;
  query_type?: string;
  complexity?: string;
  iterations?: number;
  sub_queries?: string[];
  quality_badge?: string;
  grounding_policy?: string;
  claim_ledger_mode?: string;
  render_answer_mode?: string;
  scholarly_polish_mode?: string;
  pipeline_degraded?: boolean;
  [key: string]: unknown;
}

export interface ReasoningStep {
  id: number;
  type: ReasoningStepType;
  label: string;
  description: string;
  nodes?: string[];
  edges?: string[];
  duration?: number;
  status: StepStatus;
  metadata?: {
    nodeCount?: number;
    edgeCount?: number;
    similarity?: number;
    contextLength?: number;
    [key: string]: number | string | boolean | undefined;
  };
}

export interface GraphRAGNode {
  id: string;
  label: string;
  type: string;
  description?: string;
  properties?: Record<string, unknown>;
}

export interface GraphRAGEdge {
  source: string;
  target: string;
  relation: string;
  properties?: Record<string, unknown>;
}

export interface ReasoningPath {
  query: string;
  steps: ReasoningStep[];
  startTime: string;
  endTime?: string;
  totalDuration?: number;
  status: 'pending' | 'processing' | 'complete' | 'error';
}

export interface GraphRAGAnswer {
  answer: string;
  reasoning_path: {
    query_embedding: number[];
    retrieved_nodes: GraphRAGNode[];
    graph_context: {
      nodes: GraphRAGNode[];
      edges: GraphRAGEdge[];
    };
    relevant_citations: string[];
    synthesis_prompt: string;
  };
  citations: Array<{
    text: string;
    source: string;
    node_id: string;
  }>;
  confidence_score?: number;
  metadata?: {
    total_nodes_searched: number;
    total_edges_traversed: number;
    llm_model: string;
    processing_time_ms: number;
  };
}

export interface QuerySuggestion {
  text: string;
  category: 'philosophical' | 'comparative' | 'historical' | 'conceptual';
  description: string;
  estimatedComplexity: 'simple' | 'moderate' | 'complex';
  exampleNodes?: string[];
}


export interface ArgumentMapping {
  id: string;
  claim: string;
  premises: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  objections?: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  responses?: Array<{
    id: string;
    text: string;
    source?: string;
  }>;
  conclusion: string;
  relatedConcepts: string[];
}

export interface ConceptEvolution {
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
}

export interface InfluenceRelationship {
  source: string;
  target: string;
  type: 'influenced' | 'opposed' | 'synthesized' | 'transmitted';
  strength: number; // 0-1
  description?: string;
  period?: string;
}

export interface ComparisonResult {
  entities: Array<{
    id: string;
    label: string;
    type: string;
  }>;
  dimensions: Array<{
    name: string;
    values: Record<string, string | number>;
  }>;
  similarities: string[];
  differences: string[];
  synthesis?: string;
}

export interface Citation {
  id: string;
  text: string;
  source: string;
  format: 'apa' | 'mla' | 'chicago' | 'bibtex';
  citation: string;
  url?: string;
  doi?: string;
}

export interface DebatePosition {
  id: string;
  position: string;
  philosopher: string;
  arguments: string[];
  evidence: string[];
  counterarguments?: string[];
}

export interface DebateSession {
  id: string;
  topic: string;
  positions: DebatePosition[];
  turns: Array<{
    positionId: string;
    statement: string;
    timestamp: string;
  }>;
  synthesis?: string;
}

export interface ResearchNote {
  id: string;
  content: string;
  type: 'query' | 'note' | 'code' | 'visualization';
  timestamp: string;
  relatedNodes?: string[];
  graphragQuery?: string;
  graphragAnswer?: GraphRAGAnswer;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: 'exploration' | 'learning' | 'contribution' | 'mastery';
  progress: number;
  maxProgress: number;
  unlocked: boolean;
  unlockedAt?: string;
}

export interface QualityMetrics {
  // Legacy fields (optional for backwards compat)
  citationCount?: number;
  sourceCount?: number;
  nodeRelevanceScore?: number;
  contextCoherence?: number;
  answerCompleteness?: number;
  overallQuality?: number; // 0-100
  // New SOTA workflow fields
  confidence_score?: number;
  quality_badge?: 'High' | 'Medium' | 'Low' | string;
  relevance_score?: number;
  grounding_score?: number;
  completeness_score?: number;
  caveats?: string[];
}

export interface ContextPassage {
  passageId: string;
  textContent: string;
  canonicalRef: string;
  author: string;
  workTitle: string;
  language: 'grc' | 'lat' | string;
  ctsUrn?: string;
  book?: string;
  chapter?: string;
  section?: string;
  sequenceNumber: number;
  isTarget: boolean;
}

export interface PassageContext {
  target: ContextPassage;
  passages: ContextPassage[];
  workId: string;
  totalPassagesInWork: number;
}
