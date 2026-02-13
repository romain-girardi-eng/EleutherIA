/**
 * Refinement Agent
 *
 * Iteratively improves answers through multiple refinement cycles.
 *
 * Capabilities:
 * - Answer quality assessment
 * - Gap identification
 * - Additional context retrieval
 * - Iterative improvement
 * - Convergence detection
 */

import { LLMService } from '../llm';
import { HierarchicalRetrievalService } from '../hierarchical-retrieval';
import { ReasoningAgent } from './reasoning-agent';
import { VerificationAgent } from './verification-agent';
import {
  RefinementIteration,
  Evidence,
  QualityAssessment,
} from '../../types/agentic';
import { getLogger } from '../../utils/logger';

const logger = getLogger('RefinementAgent');

export class RefinementAgent {
  private llm: LLMService;
  private retrieval: HierarchicalRetrievalService;
  private reasoning: ReasoningAgent;
  private verification: VerificationAgent;

  constructor(
    llm: LLMService,
    retrieval: HierarchicalRetrievalService,
    reasoning: ReasoningAgent,
    verification: VerificationAgent
  ) {
    this.llm = llm;
    this.retrieval = retrieval;
    this.reasoning = reasoning;
    this.verification = verification;
  }

  /**
   * Iteratively refine answer until quality threshold met
   */
  async refine(
    query: string,
    initialAnswer: string,
    initialEvidence: Evidence[],
    maxIterations: number = 3,
    confidenceThreshold: number = 0.8
  ): Promise<{
    finalAnswer: string;
    confidence: number;
    iterations: RefinementIteration[];
  }> {
    logger.info(`Starting refinement loop: max ${maxIterations} iterations, threshold ${confidenceThreshold}`);

    const iterations: RefinementIteration[] = [];
    let currentAnswer = initialAnswer;
    let currentEvidence = initialEvidence;
    let iteration = 0;

    while (iteration < maxIterations) {
      iteration++;
      logger.info(`--- Refinement Iteration ${iteration} ---`);

      // Step 1: Assess current answer quality
      const quality = await this.assessQuality(currentAnswer, query, currentEvidence);
      logger.info(
        `Quality: confidence=${quality.confidence.toFixed(2)}, ` +
        `completeness=${quality.completeness.toFixed(2)}, ` +
        `gaps=${quality.gaps.length}`
      );

      // Step 2: Record iteration
      iterations.push({
        iteration,
        answer: currentAnswer,
        confidence: quality.confidence,
        gaps: quality.gaps,
        additionalRetrieval: [],
        improvements: quality.strengths,
      });

      // Step 3: Check if we've reached quality threshold
      if (quality.confidence >= confidenceThreshold && quality.gaps.length === 0) {
        logger.info(`✓ Quality threshold reached at iteration ${iteration}`);
        return {
          finalAnswer: currentAnswer,
          confidence: quality.confidence,
          iterations,
        };
      }

      // Step 4: Check if we're stuck (no improvement)
      if (iteration > 1) {
        const previousConfidence = iterations[iteration - 2].confidence;
        const improvement = quality.confidence - previousConfidence;

        if (improvement < 0.05) {
          logger.warn(`Minimal improvement (${improvement.toFixed(3)}), stopping refinement`);
          return {
            finalAnswer: currentAnswer,
            confidence: quality.confidence,
            iterations,
          };
        }
      }

      // Step 5: Identify what needs improvement
      if (quality.gaps.length > 0) {
        logger.info(`Addressing ${quality.gaps.length} gap(s): ${quality.gaps.join(', ')}`);

        // Retrieve additional context for gaps
        const additionalEvidence = await this.retrieveForGaps(query, quality.gaps);
        iterations[iterations.length - 1].additionalRetrieval = additionalEvidence;

        logger.info(`Retrieved ${additionalEvidence.length} additional pieces of evidence`);

        // Combine with existing evidence
        currentEvidence = [...currentEvidence, ...additionalEvidence];

        // Re-synthesize answer with enhanced context
        currentAnswer = await this.synthesizeImprovedAnswer(
          query,
          currentAnswer,
          currentEvidence,
          quality.gaps
        );
      } else if (quality.confidence < confidenceThreshold) {
        // Low confidence but no specific gaps - try deepening context
        logger.info('Low confidence without specific gaps - deepening context');

        const deeperContext = await this.deepenContext(query);
        currentEvidence = [...currentEvidence, ...deeperContext];

        currentAnswer = await this.synthesizeImprovedAnswer(
          query,
          currentAnswer,
          currentEvidence,
          []
        );
      }
    }

    // Max iterations reached
    logger.warn(`Max iterations (${maxIterations}) reached without meeting threshold`);
    return {
      finalAnswer: currentAnswer,
      confidence: iterations[iterations.length - 1].confidence,
      iterations,
    };
  }

  /**
   * Assess answer quality across multiple dimensions
   */
  private async assessQuality(
    answer: string,
    query: string,
    evidence: Evidence[]
  ): Promise<QualityAssessment> {
    const prompt = `Assess the quality of this answer to a philosophical question.

Question: ${query}

Answer: ${answer}

Evidence used: ${evidence.length} sources

Assessment dimensions:
1. **Completeness**: Does it fully answer the question? (0.0-1.0)
2. **Accuracy**: Is it supported by evidence? (0.0-1.0)
3. **Clarity**: Is it well-structured and clear? (0.0-1.0)
4. **Gaps**: What specific information is missing or unclear?
5. **Strengths**: What does it do well?
6. **Weaknesses**: What needs improvement?

Respond with JSON (no markdown):
{
  "completeness": 0.0-1.0,
  "accuracy": 0.0-1.0,
  "clarity": 0.0-1.0,
  "gaps": ["specific gap 1", "specific gap 2", ...],
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...]
}`;

    try {
      const response = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      const cleaned = response.replace(/```json\n?|\n?```/g, '').trim();
      const result = JSON.parse(cleaned);

      // Calculate overall confidence as weighted average
      const confidence = (
        result.completeness * 0.4 +
        result.accuracy * 0.4 +
        result.clarity * 0.2
      );

      return {
        confidence,
        completeness: result.completeness,
        accuracy: result.accuracy,
        clarity: result.clarity,
        gaps: result.gaps || [],
        strengths: result.strengths || [],
        weaknesses: result.weaknesses || [],
      };
    } catch (error) {
      logger.error('Quality assessment failed', error);
      return {
        confidence: 0.5,
        completeness: 0.5,
        accuracy: 0.5,
        clarity: 0.5,
        gaps: [],
        strengths: [],
        weaknesses: ['Assessment failed'],
      };
    }
  }

  /**
   * Retrieve additional context for identified gaps
   */
  private async retrieveForGaps(
    query: string,
    gaps: string[]
  ): Promise<Evidence[]> {
    const additionalEvidence: Evidence[] = [];

    // Limit to top 2 gaps to avoid excessive retrieval
    const priorityGaps = gaps.slice(0, 2);

    for (const gap of priorityGaps) {
      logger.info(`Retrieving for gap: "${gap}"`);

      // Formulate targeted query for this gap
      const gapQuery = `${query} - specifically: ${gap}`;

      try {
        const retrieval = await this.retrieval.retrieve(gapQuery);

        // Convert communities to evidence
        for (const community of retrieval.communities) {
          additionalEvidence.push({
            source: `${community.dominant_school || 'Mixed'} Community`,
            content: community.summary,
            type: 'community',
            confidence: 0.75, // Community summaries have moderate confidence
            isPrimary: false,
            metadata: {
              period: community.dominant_period || undefined,
              school: community.dominant_school || undefined,
            },
          });
        }
      } catch (error) {
        logger.error(`Failed to retrieve for gap: ${gap}`, error);
      }
    }

    return additionalEvidence;
  }

  /**
   * Deepen context by drilling down in hierarchy
   */
  private async deepenContext(query: string): Promise<Evidence[]> {
    logger.info('Deepening context through hierarchical drill-down');

    // Retrieve at more detailed level
    const retrieval = await this.retrieval.retrieve(query);

    return retrieval.communities.map(community => ({
      source: `${community.dominant_school || 'Mixed'} (Level ${community.level})`,
      content: community.summary,
      type: 'community' as const,
      confidence: 0.8,
      isPrimary: false,
      metadata: {
        period: community.dominant_period || undefined,
        school: community.dominant_school || undefined,
      },
    }));
  }

  /**
   * Synthesize improved answer with additional context
   */
  private async synthesizeImprovedAnswer(
    query: string,
    currentAnswer: string,
    allEvidence: Evidence[],
    gaps: string[]
  ): Promise<string> {
    const gapsText = gaps.length > 0
      ? `\n\nSpecific gaps to address:\n${gaps.map((g, i) => `${i + 1}. ${g}`).join('\n')}`
      : '';

    const prompt = `Improve this answer by incorporating additional evidence and addressing gaps.

Question: ${query}

Current Answer:
${currentAnswer}
${gapsText}

All Available Evidence:
${allEvidence.map((e, i) => `[${i + 1}] ${e.source}: ${e.content}`).join('\n\n')}

Instructions:
1. Maintain the strengths of the current answer
2. Address the identified gaps with the new evidence
3. Integrate all relevant evidence smoothly
4. Keep scholarly tone and citations
5. Make the answer more complete without adding unnecessary length

Provide the improved answer (plain text, no JSON):`;

    try {
      const improved = await this.llm.generateWithRetry(prompt, 'gemini-3-flash-preview');
      return improved.trim();
    } catch (error) {
      logger.error('Answer synthesis failed', error);
      // Return current answer if refinement fails
      return currentAnswer;
    }
  }

  /**
   * Check if refinement has converged (no further improvement likely)
   */
  hasConverged(iterations: RefinementIteration[]): boolean {
    if (iterations.length < 2) return false;

    // Check last 2 iterations
    const recent = iterations.slice(-2);
    const confidenceDiff = Math.abs(recent[1].confidence - recent[0].confidence);

    // Converged if confidence change < 3%
    return confidenceDiff < 0.03;
  }
}
