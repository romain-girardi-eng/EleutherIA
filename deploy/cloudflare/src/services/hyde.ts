/**
 * HyDE (Hypothetical Document Embeddings) Service
 *
 * Generates a hypothetical scholarly passage that would answer the query,
 * then embeds that passage to search for semantically similar real passages.
 *
 * Research shows 12-18% recall improvement on paraphrased queries.
 */

import { Env } from '../types';
import { LLMService } from './llm';
import { QdrantService } from './qdrant';
import { getLogger } from '../utils/logger';

const logger = getLogger('HyDEService');

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
 * Generate a hypothetical scholarly passage that would answer the query
 */
export async function generateHypotheticalDocument(
  query: string,
  llm: LLMService
): Promise<string> {
  const prompt = `You are an expert classicist specializing in ancient Greek and Roman philosophy, particularly debates about fate, free will, and moral responsibility.

Write a scholarly passage (150-200 words) that would perfectly answer this question:
"${query}"

Requirements:
- Include specific philosophers by name (Chrysippus, Epictetus, Epicurus, Alexander of Aphrodisias, etc.)
- Include Greek philosophical terms with transliterations:
  - τὸ ἐφ' ἡμῖν (to eph' hēmin) - what is in our power
  - αὐτεξούσιον (autexousion) - self-determination
  - εἱμαρμένη (heimarmenē) - fate
  - συγκατάθεσις (synkatathesis) - assent
  - προαίρεσις (prohairesis) - moral choice
  - κλίναμεν/clinamen - atomic swerve
- Reference specific ancient works (De Fato, Meditations, Letter to Menoeceus, etc.)
- Use academic register and precision

Write only the passage, no preamble:`;

  try {
    const response = await llm.generate(prompt, 'gemini-3-flash-preview', false);
    logger.info(`Generated hypothetical document: ${response.length} chars`);
    return response;
  } catch (error) {
    logger.error('Error generating hypothetical document', error);
    throw error;
  }
}

/**
 * HyDE Search: Generate hypothetical document, embed it, search with that embedding
 */
export async function hydeSearch(
  query: string,
  llm: LLMService,
  qdrant: QdrantService,
  env: Env,
  limit: number = 10
): Promise<HyDEResult> {
  const startTime = Date.now();

  try {
    // Step 1: Generate hypothetical document that would answer the query
    const hypotheticalDocument = await generateHypotheticalDocument(query, llm);

    // Step 2: Embed the hypothetical document (not the query)
    const embedding = await llm.embed(hypotheticalDocument);

    // Step 3: Search text_embeddings with hypothetical embedding
    const searchResults = await qdrant.searchTexts(
      embedding,
      limit,
      undefined,  // no filters
      0.5  // threshold lowered for better recall
    );

    // Transform results
    const results: HyDESearchResult[] = searchResults.map(r => ({
      id: r.id,
      score: r.score,
      passageId: r.payload?.passage_id,
      author: r.payload?.author,
      work: r.payload?.title,
      text: r.payload?.text_preview || r.payload?.text_content,
      language: r.payload?.language,
      payload: r.payload,
    }));

    const searchTime = Date.now() - startTime;
    logger.info(`HyDE search completed: ${results.length} results in ${searchTime}ms`);

    return {
      hypotheticalDocument,
      searchResults: results,
      searchTime,
    };
  } catch (error) {
    logger.error('HyDE search error', error);
    throw error;
  }
}

/**
 * HyDE search for KG nodes
 */
export async function hydeSearchNodes(
  query: string,
  llm: LLMService,
  qdrant: QdrantService,
  env: Env,
  limit: number = 10
): Promise<HyDEResult> {
  const startTime = Date.now();

  try {
    // Generate hypothetical document
    const hypotheticalDocument = await generateHypotheticalDocument(query, llm);

    // Embed the hypothetical document
    const embedding = await llm.embed(hypotheticalDocument);

    // Search KG nodes with hypothetical embedding
    const searchResults = await qdrant.searchNodes(
      embedding,
      limit,
      0.5  // threshold
    );

    // Transform results
    const results: HyDESearchResult[] = searchResults.map(r => ({
      id: r.id,
      score: r.score,
      payload: r.payload,
    }));

    const searchTime = Date.now() - startTime;
    logger.info(`HyDE node search completed: ${results.length} results in ${searchTime}ms`);

    return {
      hypotheticalDocument,
      searchResults: results,
      searchTime,
    };
  } catch (error) {
    logger.error('HyDE node search error', error);
    throw error;
  }
}

/**
 * Combined HyDE + Standard search with RRF fusion
 * Gets best of both worlds: semantic gap bridging + direct matching
 */
export async function hydeEnhancedSearch(
  query: string,
  llm: LLMService,
  qdrant: QdrantService,
  env: Env,
  limit: number = 10
): Promise<{
  results: HyDESearchResult[];
  hydeResults: HyDESearchResult[];
  standardResults: HyDESearchResult[];
  hypotheticalDocument: string;
  searchTime: number;
}> {
  const startTime = Date.now();

  try {
    // Run HyDE search and standard search in parallel
    const [hydeResult, queryEmbedding] = await Promise.all([
      hydeSearch(query, llm, qdrant, env, limit * 2),
      llm.embed(query),
    ]);

    // Standard search with query embedding
    const standardSearchResults = await qdrant.searchTexts(
      queryEmbedding,
      limit * 2,
      undefined,
      0.5
    );

    const standardResults: HyDESearchResult[] = standardSearchResults.map(r => ({
      id: r.id,
      score: r.score,
      passageId: r.payload?.passage_id,
      author: r.payload?.author,
      work: r.payload?.title,
      text: r.payload?.text_preview || r.payload?.text_content,
      language: r.payload?.language,
      payload: r.payload,
    }));

    // RRF Fusion
    const k = 60;  // RRF constant
    const scores = new Map<string, number>();
    const items = new Map<string, HyDESearchResult>();

    // Score HyDE results
    hydeResult.searchResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    // Score standard results
    standardResults.forEach((item, rank) => {
      const id = String(item.id);
      scores.set(id, (scores.get(id) || 0) + 1 / (k + rank + 1));
      if (!items.has(id)) items.set(id, item);
    });

    // Sort by RRF score
    const sortedIds = Array.from(scores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([id]) => id);

    const results = sortedIds.map(id => items.get(id)!);

    const searchTime = Date.now() - startTime;
    logger.info(`HyDE-enhanced search: ${results.length} results (HyDE: ${hydeResult.searchResults.length}, Standard: ${standardResults.length}) in ${searchTime}ms`);

    return {
      results,
      hydeResults: hydeResult.searchResults.slice(0, limit),
      standardResults: standardResults.slice(0, limit),
      hypotheticalDocument: hydeResult.hypotheticalDocument,
      searchTime,
    };
  } catch (error) {
    logger.error('HyDE-enhanced search error', error);
    throw error;
  }
}
