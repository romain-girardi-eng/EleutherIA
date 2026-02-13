/**
 * SELF-RAG Service
 *
 * Self-evaluates answer quality after generation to provide confidence scores
 * and identify areas for improvement.
 *
 * Research shows -52% hallucinations with self-evaluation.
 */

import { LLMService } from './llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('SelfRAGService');

export interface SelfRAGEvaluation {
  relevanceScore: number;      // 0-100: Does answer address the question?
  groundingScore: number;      // 0-100: Are claims supported by sources?
  completenessScore: number;   // 0-100: Are key aspects covered?
  confidenceScore: number;     // 0-100: Overall answer reliability
  qualityBadge: 'High' | 'Medium' | 'Low';
  shouldRefine: boolean;
  caveats: string[];
  improvements: string[];
  evaluationTime: number;
}

export interface SelfRAGRefinement {
  refinedAnswer: string;
  changesApplied: string[];
  refinementTime: number;
}

/**
 * Self-evaluate the quality of a generated answer
 */
export async function selfEvaluateAnswer(
  query: string,
  answer: string,
  sourceCount: number,
  sourceLabels: string[],
  llm: LLMService
): Promise<SelfRAGEvaluation> {
  const startTime = Date.now();

  const prompt = `You are a scholarly quality evaluator for ancient philosophy research answers.

TASK: Self-evaluate this answer's quality and reliability.

RESEARCH QUESTION: "${query}"

GENERATED ANSWER:
"""
${answer.slice(0, 2500)}
"""

SOURCES CITED: ${sourceCount} sources
SOURCE LABELS: ${sourceLabels.slice(0, 10).join(', ')}

EVALUATE on 0-100 scale:
1. RELEVANCE: Does the answer directly address the research question?
2. GROUNDING: Are all claims supported by the cited sources? (Not hallucinated)
3. COMPLETENESS: Does it cover the key aspects of the question?
4. CONFIDENCE: Overall reliability for scholarly use?

Return ONLY valid JSON (no markdown):
{
  "relevance": 85,
  "grounding": 90,
  "completeness": 75,
  "confidence": 83,
  "caveats": ["limited coverage of Epicurean view", "needs more primary source quotes"],
  "improvements": ["add specific passage citation from De Fato", "compare with Alexander of Aphrodisias"]
}`;

  try {
    const response = await llm.generate(prompt, 'gemini-3-flash-preview', true);

    // Parse response
    let parsed: any;
    try {
      const cleanedResponse = response
        .replace(/```json\n?/g, '')
        .replace(/```\n?/g, '')
        .trim();
      parsed = JSON.parse(cleanedResponse);
    } catch {
      logger.warn('Failed to parse SELF-RAG evaluation');
      return {
        relevanceScore: 70,
        groundingScore: 70,
        completenessScore: 70,
        confidenceScore: 70,
        qualityBadge: 'Medium',
        shouldRefine: false,
        caveats: ['Evaluation parsing failed'],
        improvements: [],
        evaluationTime: Date.now() - startTime,
      };
    }

    const relevanceScore = parsed.relevance || 50;
    const groundingScore = parsed.grounding || 50;
    const completenessScore = parsed.completeness || 50;
    const confidenceScore = parsed.confidence || 50;

    // Determine quality badge
    let qualityBadge: 'High' | 'Medium' | 'Low';
    if (confidenceScore >= 80) {
      qualityBadge = 'High';
    } else if (confidenceScore >= 60) {
      qualityBadge = 'Medium';
    } else {
      qualityBadge = 'Low';
    }

    // Should refine if confidence is low
    const shouldRefine = confidenceScore < 60;

    const result: SelfRAGEvaluation = {
      relevanceScore,
      groundingScore,
      completenessScore,
      confidenceScore,
      qualityBadge,
      shouldRefine,
      caveats: parsed.caveats || [],
      improvements: parsed.improvements || [],
      evaluationTime: Date.now() - startTime,
    };

    logger.info(`SELF-RAG: relevance=${relevanceScore}, grounding=${groundingScore}, confidence=${confidenceScore}, badge=${qualityBadge}`);

    return result;
  } catch (error) {
    logger.error('SELF-RAG evaluation error', error);
    return {
      relevanceScore: 50,
      groundingScore: 50,
      completenessScore: 50,
      confidenceScore: 50,
      qualityBadge: 'Medium',
      shouldRefine: false,
      caveats: ['Evaluation failed'],
      improvements: [],
      evaluationTime: Date.now() - startTime,
    };
  }
}

/**
 * Refine answer based on self-evaluation feedback
 */
export async function refineAnswer(
  query: string,
  originalAnswer: string,
  evaluation: SelfRAGEvaluation,
  context: string,
  llm: LLMService
): Promise<SelfRAGRefinement> {
  const startTime = Date.now();

  const prompt = `You are refining a scholarly answer based on quality feedback.

ORIGINAL QUESTION: "${query}"

ORIGINAL ANSWER:
"""
${originalAnswer}
"""

QUALITY ISSUES IDENTIFIED:
- Caveats: ${evaluation.caveats.join('; ') || 'None'}
- Suggested improvements: ${evaluation.improvements.join('; ') || 'None'}
- Grounding score: ${evaluation.groundingScore}/100
- Completeness score: ${evaluation.completenessScore}/100

AVAILABLE CONTEXT:
"""
${context.slice(0, 2000)}
"""

TASK: Rewrite the answer to address the identified issues:
1. Strengthen claims with better source citations
2. Add missing aspects mentioned in improvements
3. Acknowledge limitations mentioned in caveats
4. Maintain scholarly register and accuracy

Write the improved answer directly (no preamble):`;

  try {
    const refinedAnswer = await llm.generate(prompt, 'gemini-3-flash-preview', false);

    const changesApplied = [
      ...evaluation.caveats.map(c => `Addressed caveat: ${c}`),
      ...evaluation.improvements.map(i => `Applied improvement: ${i}`),
    ];

    const result: SelfRAGRefinement = {
      refinedAnswer,
      changesApplied,
      refinementTime: Date.now() - startTime,
    };

    logger.info(`Answer refined: ${changesApplied.length} changes in ${result.refinementTime}ms`);

    return result;
  } catch (error) {
    logger.error('Answer refinement error', error);
    return {
      refinedAnswer: originalAnswer,  // Return original on error
      changesApplied: [],
      refinementTime: Date.now() - startTime,
    };
  }
}

/**
 * Full SELF-RAG pipeline: evaluate + refine if needed
 */
export async function selfRAGPipeline(
  query: string,
  answer: string,
  sourceCount: number,
  sourceLabels: string[],
  context: string,
  llm: LLMService
): Promise<{
  finalAnswer: string;
  evaluation: SelfRAGEvaluation;
  refinement?: SelfRAGRefinement;
  wasRefined: boolean;
}> {
  // Step 1: Evaluate
  const evaluation = await selfEvaluateAnswer(query, answer, sourceCount, sourceLabels, llm);

  // Step 2: Refine if needed
  if (evaluation.shouldRefine) {
    const refinement = await refineAnswer(query, answer, evaluation, context, llm);
    return {
      finalAnswer: refinement.refinedAnswer,
      evaluation,
      refinement,
      wasRefined: true,
    };
  }

  return {
    finalAnswer: answer,
    evaluation,
    wasRefined: false,
  };
}

/**
 * Get quality badge based on scores
 */
export function getQualityBadge(
  relevance: number,
  grounding: number,
  completeness: number
): 'High' | 'Medium' | 'Low' {
  const avg = (relevance + grounding + completeness) / 3;
  if (avg >= 80) return 'High';
  if (avg >= 60) return 'Medium';
  return 'Low';
}

/**
 * Generate confidence explanation for users
 */
export function explainConfidence(evaluation: SelfRAGEvaluation): string {
  const parts: string[] = [];

  if (evaluation.qualityBadge === 'High') {
    parts.push('This answer has high confidence and is well-supported by sources.');
  } else if (evaluation.qualityBadge === 'Medium') {
    parts.push('This answer has moderate confidence.');
  } else {
    parts.push('This answer has limited confidence and should be verified.');
  }

  if (evaluation.caveats.length > 0) {
    parts.push(`Limitations: ${evaluation.caveats.join('; ')}.`);
  }

  return parts.join(' ');
}
