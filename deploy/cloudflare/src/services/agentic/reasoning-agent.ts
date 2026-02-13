/**
 * Reasoning Agent
 *
 * Performs multi-hop reasoning, contradiction detection, and evidence synthesis.
 *
 * Capabilities:
 * - Chain-of-thought reasoning
 * - Evidence synthesis
 * - Contradiction detection
 * - Confidence scoring
 * - Multi-hop inference across knowledge graph
 */

import { LLMService } from '../llm';
import {
  ReasoningChain,
  ReasoningStep,
  Contradiction,
  Evidence,
  ReasoningPath,
} from '../../types/agentic';
import { getLogger } from '../../utils/logger';

const logger = getLogger('ReasoningAgent');

export class ReasoningAgent {
  private llm: LLMService;

  constructor(llm: LLMService) {
    this.llm = llm;
  }

  /**
   * Perform comprehensive reasoning over retrieved context
   */
  async reason(
    query: string,
    context: string,
    evidence: Evidence[]
  ): Promise<ReasoningChain> {
    logger.info(`Reasoning for query: "${query.substring(0, 50)}..."`);

    const steps: ReasoningStep[] = [];
    const startTime = Date.now();

    // Step 1: Understand the query intent
    const understanding = await this.understandQuery(query);
    steps.push({
      id: 'understand',
      thought: 'Understanding query intent and requirements',
      action: 'infer',
      input: { query },
      output: understanding,
      confidence: 0.95,
      timestamp: Date.now(),
    });

    // Step 2: Analyze evidence quality
    const evidenceAnalysis = this.analyzeEvidence(evidence);
    steps.push({
      id: 'analyze_evidence',
      thought: `Analyzing ${evidence.length} pieces of evidence`,
      action: 'verify',
      input: { evidence },
      output: evidenceAnalysis,
      confidence: 1.0,
      timestamp: Date.now(),
    });

    // Step 3: Synthesize evidence into answer
    const synthesis = await this.synthesizeEvidence(query, context, evidence);
    steps.push({
      id: 'synthesize',
      thought: 'Synthesizing evidence into coherent answer',
      action: 'synthesize',
      input: { query, context, evidence },
      output: synthesis,
      confidence: synthesis.confidence,
      timestamp: Date.now(),
    });

    // Step 4: Detect contradictions
    const contradictions = await this.detectContradictions(evidence, synthesis.answer);
    if (contradictions.length > 0) {
      steps.push({
        id: 'detect_contradictions',
        thought: `Found ${contradictions.length} contradiction(s) in evidence`,
        action: 'verify',
        input: { evidence, answer: synthesis.answer },
        output: { contradictions },
        confidence: 0.9,
        timestamp: Date.now(),
      });
    }

    // Step 5: Multi-hop reasoning if needed (low confidence or complex query)
    let finalAnswer = synthesis.answer;
    let finalConfidence = synthesis.confidence;

    if (synthesis.confidence < 0.75 && evidence.length >= 3) {
      logger.info('Low confidence detected, attempting multi-hop reasoning');
      const multiHop = await this.multiHopReasoning(query, evidence);

      if (multiHop.confidence > synthesis.confidence) {
        steps.push({
          id: 'multihop',
          thought: 'Performing multi-hop inference to improve answer',
          action: 'infer',
          input: { query, evidence },
          output: multiHop,
          confidence: multiHop.confidence,
          timestamp: Date.now(),
        });
        finalAnswer = multiHop.answer;
        finalConfidence = multiHop.confidence;
      }
    }

    const reasoningTime = Date.now() - startTime;
    logger.info(`Reasoning complete: ${steps.length} steps, confidence=${finalConfidence.toFixed(2)} (${reasoningTime}ms)`);

    return {
      steps,
      contradictions,
      confidence: finalConfidence,
      evidence,
    };
  }

  /**
   * Understand query intent and requirements
   */
  private async understandQuery(query: string): Promise<string> {
    const prompt = `Analyze this philosophical query and explain what the user is asking:

Query: "${query}"

Provide:
1. The core question being asked
2. Key concepts involved
3. What kind of answer would satisfy this query

Be concise (2-3 sentences).`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      return response.trim();
    } catch (error) {
      logger.error('Query understanding failed', error);
      return `User is asking: ${query}`;
    }
  }

  /**
   * Analyze evidence quality and relevance
   */
  private analyzeEvidence(evidence: Evidence[]): {
    totalCount: number;
    primaryCount: number;
    avgConfidence: number;
    types: Record<string, number>;
  } {
    const primaryCount = evidence.filter(e => e.isPrimary).length;
    const avgConfidence = evidence.length > 0
      ? evidence.reduce((sum, e) => sum + e.confidence, 0) / evidence.length
      : 0;

    const types: Record<string, number> = {};
    for (const e of evidence) {
      types[e.type] = (types[e.type] || 0) + 1;
    }

    return {
      totalCount: evidence.length,
      primaryCount,
      avgConfidence,
      types,
    };
  }

  /**
   * Synthesize evidence into coherent answer
   */
  private async synthesizeEvidence(
    query: string,
    context: string,
    evidence: Evidence[]
  ): Promise<{ answer: string; confidence: number; reasoning: string }> {
    // Calculate base confidence from evidence quality
    const analysis = this.analyzeEvidence(evidence);
    const evidenceQuality = analysis.primaryCount > 0
      ? analysis.avgConfidence * 1.15
      : analysis.avgConfidence;

    const prompt = `You are a scholarly expert on ancient philosophy. Answer this question based ONLY on the provided evidence.

Question: ${query}

Evidence from Knowledge Graph:
${context}

Instructions:
1. Answer based strictly on the evidence provided
2. Cite specific philosophers, texts, or schools when possible
3. Be precise and scholarly in tone
4. If evidence contains contradictions, acknowledge them
5. If evidence is insufficient, state what's missing
6. Provide your reasoning process

Respond with JSON (no markdown):
{
  "answer": "detailed answer with citations",
  "confidence": 0.0-1.0 (based on evidence quality and completeness),
  "reasoning": "brief explanation of how you arrived at this answer",
  "sources_cited": ["source1", "source2", ...]
}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const result = JSON.parse(cleaned);

      // Adjust confidence based on evidence quality
      const adjustedConfidence = Math.min(
        result.confidence * evidenceQuality,
        1.0
      );

      return {
        answer: result.answer,
        confidence: adjustedConfidence,
        reasoning: result.reasoning,
      };
    } catch (error) {
      logger.error('Evidence synthesis failed', error);
      return {
        answer: 'Unable to synthesize answer from provided evidence.',
        confidence: 0.0,
        reasoning: 'Synthesis failed due to error',
      };
    }
  }

  /**
   * Detect contradictions in evidence and answer
   */
  private async detectContradictions(
    evidence: Evidence[],
    answer: string
  ): Promise<Contradiction[]> {
    if (evidence.length < 2) {
      return []; // Need at least 2 pieces of evidence to contradict
    }

    const prompt = `Review this answer and evidence for contradictions or conflicts.

Answer: ${answer}

Evidence:
${evidence.map((e, i) => `[${i + 1}] Source: ${e.source}\n    ${e.content}`).join('\n\n')}

Look for:
1. Contradictions between different evidence sources
2. Conflicts between the answer and evidence
3. Inconsistencies in claims or dates

Respond with JSON array (no markdown):
[
  {
    "claim1": "specific claim from first source",
    "claim2": "contradicting claim from second source",
    "source1": "name of first source",
    "source2": "name of second source",
    "severity": "minor" | "major",
    "explanation": "why this is a contradiction"
  }
]

Return empty array [] if no contradictions found.`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const contradictions = JSON.parse(cleaned);

      if (contradictions.length > 0) {
        logger.warn(`Detected ${contradictions.length} contradiction(s)`);
      }

      return contradictions;
    } catch (error) {
      logger.error('Contradiction detection failed', error);
      return [];
    }
  }

  /**
   * Perform multi-hop reasoning across knowledge graph
   */
  private async multiHopReasoning(
    query: string,
    evidence: Evidence[]
  ): Promise<{ answer: string; confidence: number; paths: ReasoningPath[] }> {
    logger.info('Attempting multi-hop reasoning');

    // Build reasoning paths from evidence
    const paths = this.buildReasoningPaths(evidence);

    if (paths.length === 0) {
      return {
        answer: 'Insufficient evidence for multi-hop reasoning',
        confidence: 0.3,
        paths: [],
      };
    }

    const prompt = `Perform multi-hop reasoning to answer this philosophical question.

Question: ${query}

Reasoning Paths Available:
${paths.map((p, i) => `Path ${i + 1}: ${p.explanation}`).join('\n')}

Evidence:
${evidence.map((e, i) => `[${i + 1}] ${e.source}: ${e.content}`).join('\n')}

Instructions:
1. Use the reasoning paths to connect different pieces of evidence
2. Make inferences across multiple sources
3. Follow chains of influence or argumentation
4. Synthesize a comprehensive answer

Respond with JSON (no markdown):
{
  "answer": "multi-hop synthesized answer",
  "confidence": 0.0-1.0,
  "reasoning_steps": ["step 1", "step 2", ...]
}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const result = JSON.parse(cleaned);

      return {
        answer: result.answer,
        confidence: result.confidence * 0.9, // Slight discount for multi-hop uncertainty
        paths,
      };
    } catch (error) {
      logger.error('Multi-hop reasoning failed', error);
      return {
        answer: 'Multi-hop reasoning failed',
        confidence: 0.2,
        paths: [],
      };
    }
  }

  /**
   * Build reasoning paths from evidence
   */
  private buildReasoningPaths(evidence: Evidence[]): ReasoningPath[] {
    const paths: ReasoningPath[] = [];

    // Look for edge evidence (relationships)
    const edges = evidence.filter(e => e.type === 'edge');

    for (const edge of edges) {
      // Parse edge content to extract source -> target relationship
      // This is simplified - in production, parse actual edge structure
      paths.push({
        nodes: [edge.source],
        edges: [edge.content.substring(0, 50)],
        hops: 1,
        confidence: edge.confidence,
        explanation: `${edge.source}: ${edge.content}`,
      });
    }

    // Look for node sequences that suggest reasoning chains
    // (This is a placeholder - real implementation would analyze actual graph structure)

    return paths;
  }

  /**
   * Score confidence based on reasoning quality
   */
  scoreConfidence(
    evidenceCount: number,
    contradictionCount: number,
    primarySourceCount: number,
    avgEvidenceConfidence: number
  ): number {
    let score = 0.5; // Base score

    // Evidence quantity
    if (evidenceCount >= 5) score += 0.2;
    else if (evidenceCount >= 3) score += 0.1;
    else if (evidenceCount >= 1) score += 0.05;

    // Evidence quality
    score += avgEvidenceConfidence * 0.3;

    // Primary sources bonus
    if (primarySourceCount > 0) {
      score += Math.min(primarySourceCount * 0.05, 0.15);
    }

    // Contradiction penalty
    score -= contradictionCount * 0.1;

    return Math.max(0, Math.min(1, score));
  }
}
