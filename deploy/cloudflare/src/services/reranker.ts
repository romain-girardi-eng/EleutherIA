/**
 * LLM-based Reranker Service
 *
 * Since we can't run CrossEncoder models on Cloudflare Workers,
 * we use LLM-based reranking which achieves 80% of CrossEncoder benefit.
 *
 * Research shows +15-25% precision improvement over RRF-only ranking.
 */

import { LLMService } from './llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('RerankerService');

export interface RerankCandidate {
  id: string | number;
  score?: number;
  text: string;
  author?: string;
  work?: string;
  metadata?: Record<string, any>;
}

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

export interface RerankResponse {
  results: RerankResult[];
  rerankTime: number;
  candidatesEvaluated: number;
}

/**
 * LLM-based reranking of search results
 * Evaluates each candidate's relevance to the query on a 0-100 scale
 */
export async function llmRerank(
  query: string,
  candidates: RerankCandidate[],
  llm: LLMService,
  topK: number = 10
): Promise<RerankResponse> {
  const startTime = Date.now();

  if (candidates.length === 0) {
    return {
      results: [],
      rerankTime: 0,
      candidatesEvaluated: 0,
    };
  }

  // Limit candidates to avoid token overflow (rerank top 30)
  const candidatesToEvaluate = candidates.slice(0, 30);

  // Build reranking prompt
  const candidateDescriptions = candidatesToEvaluate
    .map((c, i) => {
      const authorWork = c.author && c.work
        ? `${c.author}, ${c.work}`
        : c.author || c.work || 'Unknown source';
      const textPreview = c.text.slice(0, 400).replace(/\n/g, ' ');
      return `[${i + 1}] ${authorWork}: "${textPreview}..."`;
    })
    .join('\n\n');

  const prompt = `You are an expert in ancient philosophy, specializing in Greek and Roman debates about fate, free will, and moral responsibility.

TASK: Rate each passage's relevance to the research question on a scale of 0-100.

RESEARCH QUESTION: "${query}"

CANDIDATE PASSAGES:
${candidateDescriptions}

SCORING GUIDELINES:
- 90-100: Directly addresses the question with specific relevant content
- 70-89: Highly relevant, discusses key concepts/philosophers mentioned
- 50-69: Moderately relevant, related topic but not directly answering
- 30-49: Tangentially relevant, mentions some related terms
- 0-29: Not relevant to the question

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{"rankings": [{"id": 1, "score": 85, "reason": "Brief 5-10 word explanation"}, {"id": 2, "score": 72, "reason": "Brief explanation"}, ...]}

Include ALL ${candidatesToEvaluate.length} passages in your rankings.`;

  try {
    const response = await llm.generate(prompt, 'gemini-3-flash-preview', true);

    // Parse JSON response
    let rankings: Array<{ id: number; score: number; reason: string }>;
    try {
      // Clean response (remove markdown code blocks if present)
      const cleanedResponse = response
        .replace(/```json\n?/g, '')
        .replace(/```\n?/g, '')
        .trim();
      const parsed = JSON.parse(cleanedResponse);
      rankings = parsed.rankings || [];
    } catch (parseError) {
      logger.warn('Failed to parse reranking response, using original order', parseError);
      // Fallback: return original order with default scores
      const results: RerankResult[] = candidatesToEvaluate.slice(0, topK).map((c, i) => ({
        id: c.id,
        originalScore: c.score,
        rerankScore: 50 - i,  // Decreasing scores
        relevanceReason: 'Reranking failed, using original order',
        text: c.text,
        author: c.author,
        work: c.work,
        metadata: c.metadata,
      }));
      return {
        results,
        rerankTime: Date.now() - startTime,
        candidatesEvaluated: candidatesToEvaluate.length,
      };
    }

    // Map rankings back to candidates
    const scoreMap = new Map<number, { score: number; reason: string }>();
    for (const r of rankings) {
      scoreMap.set(r.id, { score: r.score, reason: r.reason });
    }

    // Build results with rerank scores
    const resultsWithScores: RerankResult[] = candidatesToEvaluate.map((c, i) => {
      const ranking = scoreMap.get(i + 1) || { score: 50, reason: 'Not ranked' };
      return {
        id: c.id,
        originalScore: c.score,
        rerankScore: ranking.score,
        relevanceReason: ranking.reason,
        text: c.text,
        author: c.author,
        work: c.work,
        metadata: c.metadata,
      };
    });

    // Sort by rerank score descending
    resultsWithScores.sort((a, b) => b.rerankScore - a.rerankScore);

    // Take top K
    const results = resultsWithScores.slice(0, topK);

    const rerankTime = Date.now() - startTime;
    logger.info(`Reranked ${candidatesToEvaluate.length} candidates → ${results.length} results in ${rerankTime}ms`);

    return {
      results,
      rerankTime,
      candidatesEvaluated: candidatesToEvaluate.length,
    };
  } catch (error) {
    logger.error('LLM reranking error', error);
    throw error;
  }
}

/**
 * Fast reranking for large candidate sets
 * Uses batch processing to evaluate multiple candidates per LLM call
 */
export async function batchRerank(
  query: string,
  candidates: RerankCandidate[],
  llm: LLMService,
  topK: number = 10,
  batchSize: number = 15
): Promise<RerankResponse> {
  const startTime = Date.now();

  if (candidates.length <= batchSize) {
    return llmRerank(query, candidates, llm, topK);
  }

  // Process in batches
  const batches: RerankCandidate[][] = [];
  for (let i = 0; i < candidates.length; i += batchSize) {
    batches.push(candidates.slice(i, i + batchSize));
  }

  // Rerank each batch
  const batchResults = await Promise.all(
    batches.map(batch => llmRerank(query, batch, llm, batchSize))
  );

  // Merge all results
  const allResults: RerankResult[] = batchResults.flatMap(r => r.results);

  // Sort by rerank score
  allResults.sort((a, b) => b.rerankScore - a.rerankScore);

  // Take top K
  const results = allResults.slice(0, topK);

  const rerankTime = Date.now() - startTime;
  logger.info(`Batch reranked ${candidates.length} candidates in ${batches.length} batches → ${results.length} results in ${rerankTime}ms`);

  return {
    results,
    rerankTime,
    candidatesEvaluated: candidates.length,
  };
}

/**
 * Rerank with domain-specific criteria for ancient philosophy
 */
export async function scholarlyRerank(
  query: string,
  candidates: RerankCandidate[],
  llm: LLMService,
  topK: number = 10
): Promise<RerankResponse> {
  const startTime = Date.now();

  if (candidates.length === 0) {
    return {
      results: [],
      rerankTime: 0,
      candidatesEvaluated: 0,
    };
  }

  const candidatesToEvaluate = candidates.slice(0, 30);

  const candidateDescriptions = candidatesToEvaluate
    .map((c, i) => {
      const authorWork = c.author && c.work
        ? `${c.author}, ${c.work}`
        : c.author || c.work || 'Unknown source';
      const textPreview = c.text.slice(0, 400).replace(/\n/g, ' ');
      return `[${i + 1}] ${authorWork}: "${textPreview}..."`;
    })
    .join('\n\n');

  const prompt = `You are a scholar of ancient Greek and Roman philosophy evaluating passages for academic research.

RESEARCH QUESTION: "${query}"

CANDIDATE PASSAGES:
${candidateDescriptions}

EVALUATE each passage on these SCHOLARLY CRITERIA (each 0-25 points):
1. TEXTUAL RELEVANCE: Does the passage directly address the question?
2. PHILOSOPHICAL DEPTH: Does it contain philosophical arguments or key terms?
3. SOURCE AUTHORITY: Is it from a primary source or key ancient author?
4. EVIDENTIAL VALUE: Does it provide quotable evidence for the answer?

Return ONLY valid JSON (no markdown):
{"rankings": [{"id": 1, "total": 85, "textual": 22, "depth": 21, "authority": 20, "evidence": 22, "reason": "Direct Stoic argument"}, ...]}

Rank ALL ${candidatesToEvaluate.length} passages.`;

  try {
    const response = await llm.generate(prompt, 'gemini-3-flash-preview', true);

    let rankings: Array<{
      id: number;
      total: number;
      textual: number;
      depth: number;
      authority: number;
      evidence: number;
      reason: string;
    }>;

    try {
      const cleanedResponse = response
        .replace(/```json\n?/g, '')
        .replace(/```\n?/g, '')
        .trim();
      const parsed = JSON.parse(cleanedResponse);
      rankings = parsed.rankings || [];
    } catch {
      logger.warn('Failed to parse scholarly reranking, falling back to simple rerank');
      return llmRerank(query, candidates, llm, topK);
    }

    const scoreMap = new Map<number, { total: number; reason: string }>();
    for (const r of rankings) {
      scoreMap.set(r.id, { total: r.total, reason: r.reason });
    }

    const resultsWithScores: RerankResult[] = candidatesToEvaluate.map((c, i) => {
      const ranking = scoreMap.get(i + 1) || { total: 50, reason: 'Not ranked' };
      return {
        id: c.id,
        originalScore: c.score,
        rerankScore: ranking.total,
        relevanceReason: ranking.reason,
        text: c.text,
        author: c.author,
        work: c.work,
        metadata: c.metadata,
      };
    });

    resultsWithScores.sort((a, b) => b.rerankScore - a.rerankScore);
    const results = resultsWithScores.slice(0, topK);

    const rerankTime = Date.now() - startTime;
    logger.info(`Scholarly reranked ${candidatesToEvaluate.length} → ${results.length} results in ${rerankTime}ms`);

    return {
      results,
      rerankTime,
      candidatesEvaluated: candidatesToEvaluate.length,
    };
  } catch (error) {
    logger.error('Scholarly reranking error', error);
    throw error;
  }
}
