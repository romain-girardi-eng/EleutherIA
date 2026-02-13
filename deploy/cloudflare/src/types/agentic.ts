/**
 * Agentic GraphRAG Type Definitions
 *
 * Types for multi-agent reasoning system with planning, reasoning,
 * verification, and refinement capabilities.
 */

import { QueryType } from '.';

// ============================================================================
// PLANNING AGENT TYPES
// ============================================================================

export interface QueryPlan {
  originalQuery: string;
  subQuestions: SubQuestion[];
  strategy: ExecutionStrategy;
  estimatedSteps: number;
}

export interface SubQuestion {
  id: string;
  question: string;
  type: QueryType;
  dependencies: string[]; // IDs of sub-questions this depends on
  priority: number;
  status: 'pending' | 'in_progress' | 'completed';
  result?: any;
}

export interface ExecutionStrategy {
  mode: 'sequential' | 'parallel' | 'adaptive';
  maxIterations: number;
  confidenceThreshold: number;
}

// ============================================================================
// REASONING AGENT TYPES
// ============================================================================

export interface ReasoningChain {
  steps: ReasoningStep[];
  contradictions: Contradiction[];
  confidence: number;
  evidence: Evidence[];
}

export interface ReasoningStep {
  id: string;
  thought: string;
  action: 'retrieve' | 'infer' | 'verify' | 'synthesize';
  input: any;
  output: any;
  confidence: number;
  timestamp?: number;
}

export interface Contradiction {
  claim1: string;
  claim2: string;
  source1: string;
  source2: string;
  severity: 'minor' | 'major';
  explanation?: string;
}

export interface Evidence {
  source: string;
  content: string;
  type: 'node' | 'edge' | 'community' | 'bridge' | 'context' | 'concepts';
  confidence: number;
  isPrimary: boolean;
  citationId?: number;  // Unique citation number for [1], [2], etc.
  nodeId?: string;      // Original graph node ID for traceability
  nodeLabel?: string;   // Human-readable node name
  nodeType?: string;    // Type: person/concept/argument/work/quote
  nodePath?: string[];  // For bridge evidence: chain of node IDs
  metadata?: {
    period?: string;
    school?: string;
    author?: string;
    pathLength?: number;
    nodeCount?: number;
    level?: number;
    conceptCount?: number;
  };
}

// ============================================================================
// CITATION TYPES
// ============================================================================

export interface SourceCitation {
  id: number;           // Citation number [1], [2], etc.
  nodeId: string;       // Graph node ID for direct access
  nodeLabel: string;    // Human-readable label
  nodeType: string;     // person/concept/argument/work/quote
  content: string;      // Full node content or summary
  url?: string;         // Deep link to node: /node/{nodeId}
  metadata: {
    school?: string;
    period?: string;
    author?: string;
    confidence: number;
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

// ============================================================================
// VERIFICATION AGENT TYPES
// ============================================================================

export interface VerificationResult {
  isValid: boolean;
  citationExists: boolean;
  claimSupported: boolean;
  sourceQuality: 'primary' | 'secondary' | 'tertiary';
  confidence: number;
  issues: string[];
  checkedClaims?: ClaimVerification[];
}

export interface ClaimVerification {
  claim: string;
  isSupported: boolean;
  supportingEvidence: string[];
  confidence: number;
}

// ============================================================================
// REFINEMENT AGENT TYPES
// ============================================================================

export interface RefinementIteration {
  iteration: number;
  answer: string;
  confidence: number;
  gaps: string[];
  additionalRetrieval: Evidence[];
  improvements?: string[];
}

export interface QualityAssessment {
  confidence: number;
  completeness: number;
  accuracy: number;
  clarity: number;
  gaps: string[];
  strengths: string[];
  weaknesses: string[];
}

// ============================================================================
// AGENTIC ANSWER TYPES
// ============================================================================

export interface AgenticAnswer {
  answer: string;
  confidence: number;
  sources: SourceCitation[];  // All cited sources with full details
  evidenceMap: EvidenceMap;   // Maps citation numbers to evidence
  reasoningTrace: ReasoningChain;
  verificationResults: VerificationResult[];
  refinementIterations: RefinementIteration[];
  metadata: AgenticMetadata;
}

export interface RetrievalDiagnostics {
  levels: Array<{
    level: number;
    communities: number;
    maxScore: number;
    fallbackApplied: boolean;
    reason?: string;
  }>;
  finalLevelCount: number;
}

export interface AgenticMetadata {
  totalSteps: number;
  retrievalCalls: number;
  tokensUsed: number;
  processingTime: number;
  plan?: QueryPlan;
  finalConfidence: number;
  retrievalDiagnostics?: RetrievalDiagnostics;
  qualityMetrics?: {
    completeness: number;
    accuracy: number;
    clarity: number;
  };
}

// ============================================================================
// MULTI-HOP REASONING TYPES
// ============================================================================

export interface ReasoningPath {
  nodes: string[];
  edges: string[];
  hops: number;
  confidence: number;
  explanation: string;
}

export interface InferenceStep {
  from: string;
  to: string;
  relation: string;
  confidence: number;
  evidence: string;
}

// ============================================================================
// AGENT COMMUNICATION TYPES
// ============================================================================

export interface AgentMessage {
  from: 'planning' | 'reasoning' | 'verification' | 'refinement' | 'orchestrator';
  to: 'planning' | 'reasoning' | 'verification' | 'refinement' | 'orchestrator';
  type: 'request' | 'response' | 'notification';
  payload: any;
  timestamp: number;
}

export interface AgentState {
  currentStep: number;
  totalSteps: number;
  status: 'idle' | 'planning' | 'retrieving' | 'reasoning' | 'verifying' | 'refining' | 'complete' | 'error';
  error?: string;
}
