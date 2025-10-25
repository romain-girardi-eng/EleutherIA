/**
 * GraphRAG TypeScript Type Definitions
 * Interfaces for reasoning paths, steps, and GraphRAG responses
 */

export type ReasoningStepType = 'search' | 'traverse' | 'context' | 'synthesis' | 'complete';
export type StepStatus = 'pending' | 'active' | 'complete' | 'error';

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
    [key: string]: any;
  };
}

export interface GraphRAGNode {
  id: string;
  label: string;
  type: string;
  description?: string;
  properties?: Record<string, any>;
}

export interface GraphRAGEdge {
  source: string;
  target: string;
  relation: string;
  properties?: Record<string, any>;
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
  citationCount: number;
  sourceCount: number;
  nodeRelevanceScore: number;
  contextCoherence: number;
  answerCompleteness: number;
  overallQuality: number; // 0-100
}
