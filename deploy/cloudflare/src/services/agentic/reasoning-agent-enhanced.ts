/**
 * Enhanced Reasoning Agent with Citation Support
 *
 * Performs multi-hop reasoning with full citation tracking for scholarly verifiability.
 * All evidence is mapped to specific graph nodes with numbered citations.
 *
 * Features:
 * - Deterministic evidence synthesis
 * - Numbered citations [1], [2], [3]
 * - Full source traceability
 * - Node ID mapping for clickable references
 * - Contradiction detection with sources
 */

import { LLMService } from '../llm';
import { citationMapper } from './citation-mapper';
import { GraphNode } from '../../types';
import {
  ReasoningChain,
  ReasoningStep,
  Contradiction,
  Evidence,
  ReasoningPath,
  SourceCitation,
  EvidenceMap,
} from '../../types/agentic';
import { getLogger } from '../../utils/logger';

const logger = getLogger('EnhancedReasoningAgent');

export class EnhancedReasoningAgent {
  private llm: LLMService;

  constructor(llm: LLMService) {
    this.llm = llm;
  }

  /**
   * Perform comprehensive reasoning with full citation tracking
   */
  async reasonWithCitations(
    query: string,
    context: string,
    evidence: Evidence[],
    nodes: GraphNode[]
  ): Promise<{
    answer: string;
    confidence: number;
    sources: SourceCitation[];
    evidenceMap: EvidenceMap;
    reasoningChain: ReasoningChain;
  }> {
    logger.info(`Enhanced reasoning for: "${query.substring(0, 50)}..."`);

    // Reset citation mapper for new query
    citationMapper.reset();
    citationMapper.registerNodes(nodes);

    const steps: ReasoningStep[] = [];
    const startTime = Date.now();

    // Step 1: Understand the query intent (deterministic)
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

    // Step 3: Generate citations for all evidence
    const citedEvidence = this.generateCitationsForEvidence(evidence);

    // Step 4: Synthesize evidence with citations (deterministic)
    const synthesis = await this.synthesizeWithCitations(
      query,
      context,
      citedEvidence
    );
    steps.push({
      id: 'synthesize',
      thought: 'Synthesizing evidence with proper citations',
      action: 'synthesize',
      input: { query, context, evidence: citedEvidence },
      output: synthesis,
      confidence: synthesis.confidence,
      timestamp: Date.now(),
    });

    // Step 5: Detect contradictions
    const contradictions = await this.detectContradictions(citedEvidence, synthesis.answer);
    if (contradictions.length > 0) {
      steps.push({
        id: 'detect_contradictions',
        thought: `Found ${contradictions.length} contradiction(s) in evidence`,
        action: 'verify',
        input: { evidence: citedEvidence, answer: synthesis.answer },
        output: { contradictions },
        confidence: 0.9,
        timestamp: Date.now(),
      });
    }

    // Step 6: Multi-hop reasoning if needed (with citations)
    let finalAnswer = synthesis.answer;
    let finalConfidence = synthesis.confidence;

    if (synthesis.confidence < 0.75 && evidence.length >= 3) {
      logger.info('Low confidence detected, attempting multi-hop reasoning');
      const multiHop = await this.multiHopReasoningWithCitations(query, citedEvidence);

      if (multiHop.confidence > synthesis.confidence) {
        steps.push({
          id: 'multihop',
          thought: 'Performing multi-hop inference with citations',
          action: 'infer',
          input: { query, evidence: citedEvidence },
          output: multiHop,
          confidence: multiHop.confidence,
          timestamp: Date.now(),
        });
        finalAnswer = multiHop.answer;
        finalConfidence = multiHop.confidence;
      }
    }

    // Step 7: Format final answer with citations
    const citedAnswer = this.formatAnswerWithCitations(finalAnswer, citedEvidence);

    // Step 8: Validate all citations
    if (!citationMapper.validateCitations(citedAnswer)) {
      logger.warn('Citation validation failed, some citations missing sources');
    }

    const reasoningTime = Date.now() - startTime;
    logger.info(`Enhanced reasoning complete: ${steps.length} steps, confidence=${finalConfidence.toFixed(2)}, citations=${citationMapper.getStats().totalCitations} (${reasoningTime}ms)`);

    return {
      answer: citedAnswer,
      confidence: finalConfidence,
      sources: citationMapper.getSourceCitations(),
      evidenceMap: citationMapper.getEvidenceMap(),
      reasoningChain: {
        steps,
        contradictions,
        confidence: finalConfidence,
        evidence: citedEvidence,
      },
    };
  }

  /**
   * Generate citations for all evidence pieces
   */
  private generateCitationsForEvidence(evidence: Evidence[]): Evidence[] {
    return evidence.map(e => {
      const citationId = citationMapper.generateCitation(e);
      return { ...e, citationId };
    });
  }

  /**
   * Format answer with proper citations
   */
  private formatAnswerWithCitations(answer: string, evidence: Evidence[]): string {
    // Look for claims in the answer and add citations
    let citedAnswer = answer;

    // For each high-confidence evidence, find relevant claims
    const primaryEvidence = evidence.filter(e => e.isPrimary && e.confidence > 0.7);

    for (const e of primaryEvidence) {
      if (!e.citationId) continue;

      // Find sentences that relate to this evidence
      // This is simplified - production would use NLP
      const keywords = this.extractKeywords(e.content);

      for (const keyword of keywords) {
        const pattern = new RegExp(`([^.]*${keyword}[^.]*)(\\.)`);
        const match = citedAnswer.match(pattern);

        if (match && !match[0].includes('[')) {
          // Add citation if not already cited
          citedAnswer = citedAnswer.replace(
            match[0],
            `${match[1]} [${e.citationId}]${match[2]}`
          );
        }
      }
    }

    // Add citation summary at the end
    const citationSummary = citationMapper.generateCitationSummary();
    if (citationSummary) {
      citedAnswer += citationSummary;
    }

    return citedAnswer;
  }

  /**
   * Extract keywords from content for citation matching
   */
  private extractKeywords(content: string): string[] {
    // Extract important terms (simplified version)
    const words = content.split(/\s+/);
    return words
      .filter(w => w.length > 4)
      .filter(w => /^[A-Z]/.test(w)) // Capitalized words (names, concepts)
      .slice(0, 3); // Top 3 keywords
  }

  /**
   * Understand query intent (deterministic)
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
      // Use deterministic generation for consistent understanding
      const response = await this.llm.generate(prompt, 'gemini-3-flash-preview', true);
      return response.trim();
    } catch (error) {
      logger.error('Query understanding failed', error);
      return `User is asking: ${query}`;
    }
  }

  /**
   * Synthesize evidence with citations (deterministic)
   */
  private async synthesizeWithCitations(
    query: string,
    context: string,
    evidence: Evidence[]
  ): Promise<{ answer: string; confidence: number; reasoning: string }> {
    // Calculate base confidence from evidence quality
    const analysis = this.analyzeEvidence(evidence);
    const evidenceQuality = analysis.primaryCount > 0
      ? analysis.avgConfidence * 1.15
      : analysis.avgConfidence;

    // Create evidence list with placeholders for citations
    const evidenceList = evidence.map((e, i) => {
      const citation = e.citationId ? `[${e.citationId}]` : `{{cite:${i}}}`;
      return `${citation} ${e.source}: ${e.content}`;
    }).join('\n');

    const prompt = `You are a scholarly expert on ancient philosophy. Answer this question based ONLY on the provided evidence.
Each piece of evidence has a citation number in brackets. You MUST cite these numbers when using the evidence.

Question: ${query}

Evidence from Knowledge Graph:
${evidenceList}

Instructions:
1. Answer based strictly on the evidence provided
2. Include citation numbers [1], [2], etc. when referencing evidence
3. Be precise and scholarly in tone
4. If evidence contains contradictions, acknowledge them with citations
5. If evidence is insufficient, state what's missing
6. ALWAYS include citations for every claim

Format your response as JSON (no markdown):
{
  "answer": "detailed answer with [1], [2] style citations",
  "confidence": 0.0-1.0,
  "reasoning": "explanation of synthesis process",
  "claims_with_citations": [
    {"claim": "statement", "citations": [1, 2]},
    ...
  ]
}`;

    try {
      // Use deterministic generation for reproducible synthesis
      const response = await this.llm.generate(prompt, 'gemini-3-flash-preview', true);
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
   * Multi-hop reasoning with citations
   */
  private async multiHopReasoningWithCitations(
    query: string,
    evidence: Evidence[]
  ): Promise<{ answer: string; confidence: number; paths: ReasoningPath[] }> {
    logger.info('Attempting multi-hop reasoning with citations');

    // Build reasoning paths from evidence
    const paths = this.buildReasoningPaths(evidence);

    if (paths.length === 0) {
      return {
        answer: 'Insufficient evidence for multi-hop reasoning',
        confidence: 0.3,
        paths: [],
      };
    }

    // Create evidence list with citations
    const evidenceList = evidence.map(e => {
      const citation = e.citationId ? `[${e.citationId}]` : '';
      return `${citation} ${e.source}: ${e.content}`;
    }).join('\n');

    const prompt = `Perform multi-hop reasoning to answer this philosophical question.
Use the citation numbers provided for each piece of evidence.

Question: ${query}

Reasoning Paths Available:
${paths.map((p, i) => `Path ${i + 1}: ${p.explanation}`).join('\n')}

Evidence with Citations:
${evidenceList}

Instructions:
1. Connect different pieces of evidence using citations
2. Make inferences across multiple sources
3. Include citation numbers [1], [2] for all claims
4. Synthesize a comprehensive answer with full citations

Format as JSON (no markdown):
{
  "answer": "multi-hop answer with [1], [2] citations",
  "confidence": 0.0-1.0,
  "reasoning_steps": [
    "From [1], we know...",
    "This connects to [2] which shows...",
    ...
  ]
}`;

    try {
      // Use deterministic generation for multi-hop
      const response = await this.llm.generate(prompt, 'gemini-3-flash-preview', true);
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
   * Detect contradictions with source tracking
   */
  private async detectContradictions(
    evidence: Evidence[],
    answer: string
  ): Promise<Contradiction[]> {
    if (evidence.length < 2) {
      return [];
    }

    const evidenceList = evidence.map((e, i) => {
      const citation = e.citationId ? `[${e.citationId}]` : `[${i + 1}]`;
      return `${citation} Source: ${e.source}\n    ${e.content}`;
    }).join('\n\n');

    const prompt = `Review this answer and evidence for contradictions.

Answer: ${answer}

Evidence with Citations:
${evidenceList}

Look for contradictions and cite the specific evidence numbers.

Format as JSON array (no markdown):
[
  {
    "claim1": "specific claim from first source",
    "claim2": "contradicting claim from second source",
    "source1": "name with citation [X]",
    "source2": "name with citation [Y]",
    "severity": "minor" | "major",
    "explanation": "why this is a contradiction"
  }
]

Return empty array [] if no contradictions found.`;

    try {
      const response = await this.llm.generate(prompt, 'gemini-3-flash-preview', true);
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
   * Build reasoning paths from evidence
   */
  private buildReasoningPaths(evidence: Evidence[]): ReasoningPath[] {
    const paths: ReasoningPath[] = [];

    // Look for edge evidence (relationships)
    const edges = evidence.filter(e => e.type === 'edge');

    for (const edge of edges) {
      const citationRef = edge.citationId ? `[${edge.citationId}]` : '';
      paths.push({
        nodes: edge.nodePath || [edge.source],
        edges: [edge.content.substring(0, 50)],
        hops: edge.nodePath?.length || 1,
        confidence: edge.confidence,
        explanation: `${citationRef} ${edge.source}: ${edge.content}`,
      });
    }

    // Look for bridge evidence (multi-hop connections)
    const bridges = evidence.filter(e => e.type === 'bridge');
    for (const bridge of bridges) {
      if (bridge.nodePath && bridge.nodePath.length > 1) {
        const citationRef = bridge.citationId ? `[${bridge.citationId}]` : '';
        paths.push({
          nodes: bridge.nodePath,
          edges: [],
          hops: bridge.nodePath.length - 1,
          confidence: bridge.confidence,
          explanation: `${citationRef} Multi-hop path: ${bridge.nodePath.join(' → ')}`,
        });
      }
    }

    return paths;
  }

  /**
   * Score confidence based on reasoning quality
   */
  scoreConfidence(
    evidenceCount: number,
    contradictionCount: number,
    primarySourceCount: number,
    avgEvidenceConfidence: number,
    citationCount: number
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

    // Citation bonus (properly cited evidence)
    if (citationCount > 0) {
      score += Math.min(citationCount * 0.02, 0.1);
    }

    // Contradiction penalty
    score -= contradictionCount * 0.1;

    return Math.max(0, Math.min(1, score));
  }
}
