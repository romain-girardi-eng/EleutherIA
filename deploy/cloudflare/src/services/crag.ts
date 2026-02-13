/**
 * CRAG (Corrective RAG) Service
 *
 * Validates retrieval sufficiency BEFORE generation to catch retrieval failures
 * and trigger secondary retrieval when needed.
 *
 * Research shows 19-36% accuracy improvement by catching retrieval failures early.
 */

import { LLMService } from './llm';
import { QdrantService } from './qdrant';
import { getLogger } from '../utils/logger';

const logger = getLogger('CRAGService');

export interface CRAGValidationResult {
  isValid: boolean;
  relevanceScore: number;      // 0-100
  completenessScore: number;   // 0-100
  confidenceScore: number;     // 0-100
  needsSecondaryRetrieval: boolean;
  missingAspects: string[];
  suggestions: string[];
  validationTime: number;
}

export interface CRAGSecondaryResult {
  additionalResults: any[];
  aspectsCovered: string[];
  searchTime: number;
}

/**
 * Validate if retrieved context is sufficient to answer the query
 */
export async function validateRetrievalSufficiency(
  query: string,
  retrievedContext: string,
  llm: LLMService
): Promise<CRAGValidationResult> {
  const startTime = Date.now();

  const prompt = `You are a scholarly validation system for ancient philosophy research.

TASK: Evaluate if the retrieved context can adequately answer the research question.

RESEARCH QUESTION: "${query}"

RETRIEVED CONTEXT:
"""
${retrievedContext.slice(0, 3000)}
"""

EVALUATE on 0-100 scale:
1. RELEVANCE: Does the context address the question topic?
2. COMPLETENESS: Is sufficient information present to answer fully?
3. CONFIDENCE: Can a good scholarly answer be generated from this?

Return ONLY valid JSON (no markdown):
{
  "relevance": 80,
  "completeness": 60,
  "confidence": 70,
  "missing": ["specific quote from Chrysippus", "comparison with Epicurean view"],
  "suggestions": ["search for De Fato passages", "add Epicurus Letter to Menoeceus"]
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
      logger.warn('Failed to parse CRAG validation, assuming valid');
      return {
        isValid: true,
        relevanceScore: 70,
        completenessScore: 70,
        confidenceScore: 70,
        needsSecondaryRetrieval: false,
        missingAspects: [],
        suggestions: [],
        validationTime: Date.now() - startTime,
      };
    }

    const relevanceScore = parsed.relevance || 50;
    const completenessScore = parsed.completeness || 50;
    const confidenceScore = parsed.confidence || 50;

    // Decision thresholds
    const isValid = confidenceScore >= 60;
    const needsSecondaryRetrieval = confidenceScore < 60;

    const result: CRAGValidationResult = {
      isValid,
      relevanceScore,
      completenessScore,
      confidenceScore,
      needsSecondaryRetrieval,
      missingAspects: parsed.missing || [],
      suggestions: parsed.suggestions || [],
      validationTime: Date.now() - startTime,
    };

    logger.info(`CRAG validation: relevance=${relevanceScore}, completeness=${completenessScore}, confidence=${confidenceScore}, valid=${isValid}`);

    return result;
  } catch (error) {
    logger.error('CRAG validation error', error);
    // On error, assume valid to avoid blocking
    return {
      isValid: true,
      relevanceScore: 50,
      completenessScore: 50,
      confidenceScore: 50,
      needsSecondaryRetrieval: false,
      missingAspects: [],
      suggestions: [],
      validationTime: Date.now() - startTime,
    };
  }
}

/**
 * Perform secondary retrieval to fill gaps identified by CRAG
 */
export async function secondaryRetrieval(
  missingAspects: string[],
  suggestions: string[],
  llm: LLMService,
  qdrant: QdrantService,
  limit: number = 5
): Promise<CRAGSecondaryResult> {
  const startTime = Date.now();

  if (missingAspects.length === 0 && suggestions.length === 0) {
    return {
      additionalResults: [],
      aspectsCovered: [],
      searchTime: 0,
    };
  }

  try {
    // Combine missing aspects and suggestions into search queries
    const searchQueries = [
      ...missingAspects.slice(0, 3),
      ...suggestions.slice(0, 2),
    ].filter(Boolean);

    // Generate embeddings and search
    const results: any[] = [];
    const aspectsCovered: string[] = [];

    for (const searchQuery of searchQueries) {
      try {
        const embedding = await llm.embed(searchQuery);
        const searchResults = await qdrant.searchTexts(
          embedding,
          limit,
          undefined,
          0.4  // Lower threshold for secondary retrieval
        );

        if (searchResults.length > 0) {
          results.push(...searchResults);
          aspectsCovered.push(searchQuery);
        }
      } catch (err) {
        logger.warn(`Secondary retrieval failed for "${searchQuery}"`, err);
      }
    }

    // Deduplicate results by ID
    const seen = new Set<string>();
    const deduplicated = results.filter(r => {
      const id = String(r.id);
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });

    const searchTime = Date.now() - startTime;
    logger.info(`Secondary retrieval: ${searchQueries.length} queries → ${deduplicated.length} results in ${searchTime}ms`);

    return {
      additionalResults: deduplicated.slice(0, limit * 2),
      aspectsCovered,
      searchTime,
    };
  } catch (error) {
    logger.error('Secondary retrieval error', error);
    return {
      additionalResults: [],
      aspectsCovered: [],
      searchTime: Date.now() - startTime,
    };
  }
}

/**
 * Full CRAG pipeline: validate + secondary retrieval if needed
 */
export async function cragPipeline(
  query: string,
  initialContext: string,
  initialResults: any[],
  llm: LLMService,
  qdrant: QdrantService
): Promise<{
  finalContext: string;
  finalResults: any[];
  validation: CRAGValidationResult;
  secondaryResults?: CRAGSecondaryResult;
}> {
  // Step 1: Validate retrieval sufficiency
  const validation = await validateRetrievalSufficiency(query, initialContext, llm);

  // If retrieval is sufficient, return as-is
  if (validation.isValid && !validation.needsSecondaryRetrieval) {
    return {
      finalContext: initialContext,
      finalResults: initialResults,
      validation,
    };
  }

  // Step 2: Secondary retrieval to fill gaps
  const secondaryResults = await secondaryRetrieval(
    validation.missingAspects,
    validation.suggestions,
    llm,
    qdrant
  );

  // Step 3: Merge results
  const mergedResults = [...initialResults];
  const existingIds = new Set(initialResults.map(r => String(r.id)));

  for (const result of secondaryResults.additionalResults) {
    if (!existingIds.has(String(result.id))) {
      mergedResults.push(result);
      existingIds.add(String(result.id));
    }
  }

  // Step 4: Build enhanced context
  const additionalContext = secondaryResults.additionalResults
    .map(r => {
      const payload = r.payload || {};
      return `${payload.author || 'Unknown'}, ${payload.title || 'Unknown'}: ${payload.text_content || payload.text_preview || ''}`;
    })
    .join('\n\n');

  const finalContext = additionalContext
    ? `${initialContext}\n\n--- ADDITIONAL SOURCES (from secondary retrieval) ---\n\n${additionalContext}`
    : initialContext;

  logger.info(`CRAG pipeline: ${validation.needsSecondaryRetrieval ? 'triggered secondary retrieval' : 'passed validation'}, ${mergedResults.length} total results`);

  return {
    finalContext,
    finalResults: mergedResults,
    validation,
    secondaryResults,
  };
}

/**
 * Quick validation check (fast, less accurate)
 */
export function quickValidation(
  query: string,
  context: string,
  resultCount: number
): { isLikelyValid: boolean; reason: string } {
  // Simple heuristics
  if (resultCount === 0) {
    return { isLikelyValid: false, reason: 'No results retrieved' };
  }

  if (context.length < 200) {
    return { isLikelyValid: false, reason: 'Context too short' };
  }

  // Check if query keywords appear in context
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const contextLower = context.toLowerCase();
  const matchedWords = queryWords.filter(w => contextLower.includes(w));
  const matchRatio = matchedWords.length / queryWords.length;

  if (matchRatio < 0.3) {
    return { isLikelyValid: false, reason: 'Low keyword match ratio' };
  }

  return { isLikelyValid: true, reason: 'Passes basic checks' };
}
