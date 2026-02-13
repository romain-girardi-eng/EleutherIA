/**
 * Search Routes
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { QdrantService } from '../services/qdrant';
import { LLMService } from '../services/llm';
import { getLogger } from '../utils/logger';
import { isLatinQuery } from '../utils/transliteration';

const logger = getLogger('SearchRoutes');

export const searchRoutes = new Hono<{ Bindings: Env }>();

// Fulltext search
searchRoutes.post('/fulltext', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5 } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const db = new DatabaseService(c.env);
    const results = await db.fulltextSearch(query, limit);

    return c.json({
      results,
      query,
      totalResults: results.length,
    });
  } catch (error) {
    logger.error('Fulltext search error', error);
    return c.json({ error: 'Fulltext search failed' }, 500);
  }
});

// Lemmatic search (similar to fulltext for now)
searchRoutes.post('/lemmatic', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5 } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const db = new DatabaseService(c.env);
    const results = await db.fulltextSearch(query, limit);

    return c.json({
      results,
      query,
      totalResults: results.length,
    });
  } catch (error) {
    logger.error('Lemmatic search error', error);
    return c.json({ error: 'Lemmatic search failed' }, 500);
  }
});

// Semantic search (Gemini embeddings)
searchRoutes.post('/semantic', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5, collection = 'passages_dual' } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const llm = new LLMService(c.env);
    const qdrant = new QdrantService(c.env);

    // Gemini-only search
    const geminiVector = await llm.embed(query);

    // Use passages_dual collection if available, otherwise fallback to text_embeddings
    const collectionToUse = collection === 'passages_dual' ? 'passages_dual' : 'text_embeddings';

    const results = await qdrant.searchWithNamedVector(
      collectionToUse,
      'gemini',
      geminiVector,
      limit
    );

    return c.json({
      results: results.map(r => ({
        id: r.id,
        score: r.score,
        ...r.payload,
      })),
      query,
      totalResults: results.length,
      mode: 'gemini-only',
      models: ['gemini'],
    });
  } catch (error) {
    logger.error('Semantic search error', error);
    return c.json({ error: 'Semantic search failed' }, 500);
  }
});

// KG search (semantic search on KG nodes)
searchRoutes.post('/kg', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5 } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const llm = new LLMService(c.env);
    const qdrant = new QdrantService(c.env);

    // Gemini-only search
    const geminiVector = await llm.embed(query);
    const results = await qdrant.searchWithNamedVector(
      'kg_nodes_dual',
      'gemini',
      geminiVector,
      limit
    );

    return c.json({
      results: results.map(r => ({
        id: r.id,
        score: r.score,
        ...r.payload,
      })),
      query,
      totalResults: results.length,
      mode: 'gemini-only',
      models: ['gemini'],
    });
  } catch (error) {
    logger.error('KG search error', error);
    return c.json({ error: 'KG search failed' }, 500);
  }
});

// Hybrid search with RRF (fulltext + semantic)
searchRoutes.post('/hybrid', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5, k } = body;
    const searchLimit = k || limit;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const db = new DatabaseService(c.env);
    const llm = new LLMService(c.env);
    const qdrant = new QdrantService(c.env);

    // Run fulltext search (always available)
    const fulltextResults = await db.fulltextSearch(query, searchLimit);

    // Semantic search with Gemini
    let semanticResults: any[] = [];
    let usedSemantic = false;

    try {
      logger.info('Hybrid search using Gemini');
      const geminiVector = await llm.embed(query);
      const qdrantResults = await qdrant.searchWithNamedVector(
        'passages_dual',
        'gemini',
        geminiVector,
        searchLimit
      );
      semanticResults = qdrantResults.map(r => ({ ...r, payload: r.payload }));
      usedSemantic = true;
    } catch (semanticError) {
      logger.warn('Semantic search failed in hybrid mode', semanticError);
      // Continue with fulltext-only
    }

    // Import RRF for combining fulltext + semantic
    const { reciprocalRankFusion } = await import('../utils/rrf');

    // Apply RRF to combine fulltext and semantic results
    const fusedResults = reciprocalRankFusion(
      {
        fulltext: fulltextResults.map((r: any, idx: number) => ({
          id: r.passage_id || r.id,
          score: 1 / (idx + 1), // Rank-based score
          payload: r,
        })),
        semantic: semanticResults.map((r: any) => ({
          id: r.id || r.payload?.passage_id,
          score: r.rrf_score || r.score,
          payload: r.payload || r,
        })),
      },
      60 // k value for RRF
    );

    return c.json({
      combined_results: fusedResults.slice(0, searchLimit).map(r => ({
        ...r.payload,
        rrf_score: r.rrf_score,
        sources: r.sources,
        original_scores: r.original_scores,
      })),
      query,
      totalResults: fusedResults.length,
      usedSemantic,
      mode: usedSemantic ? 'hybrid-gemini-rrf' : 'fulltext-only',
    });
  } catch (error) {
    logger.error('Hybrid search error', error);
    return c.json({
      error: 'Hybrid search failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

// Morphological search - Deprecated (SPhilBERTa removed)
searchRoutes.post('/morphological', async (c) => {
  return c.json({
    error: 'Morphological search is not available',
    message: 'This feature required SPhilBERTa which has been deprecated. Use /semantic for semantic search instead.',
  }, 503);
});

// Dual-level search (Nodes + Edges) - NEW!
searchRoutes.post('/dual', async (c) => {
  try {
    const body = await c.req.json();
    const { query, limit = 5, scoreThreshold } = body;

    if (!query) {
      return c.json({ error: 'Query is required' }, 400);
    }

    const llm = new LLMService(c.env);
    const qdrant = new QdrantService(c.env);

    // Generate embedding for query
    const queryVector = await llm.embed(query);

    // Dual-level search (nodes + edges)
    const dualResults = await qdrant.dualLevelSearch(
      queryVector,
      limit,
      scoreThreshold
    );

    // Format results with relationship context
    const formattedResults = dualResults.combined.map(item => {
      if (item.type === 'node') {
        return {
          type: 'node',
          score: item.score,
          node_id: item.data.payload.node_id,
          label: item.data.payload.label,
          node_type: item.data.payload.node_type,
          description: item.data.payload.text_representation,
        };
      } else {
        return {
          type: 'edge',
          score: item.score,
          edge_id: item.data.payload.edge_id,
          source_id: item.data.payload.source_id,
          target_id: item.data.payload.target_id,
          relation: item.data.payload.relation,
          description: item.data.payload.description,
          text_representation: item.data.payload.text_representation,
        };
      }
    });

    return c.json({
      results: formattedResults,
      query,
      stats: dualResults.stats,
      message: 'Dual-level search combines nodes and edges for relationship-aware retrieval',
    });
  } catch (error) {
    logger.error('Dual-level search error', error);
    return c.json({
      error: 'Dual-level search failed',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

// Lemma autocomplete - Supports Latin-alphabet queries for finding Greek lemmas
searchRoutes.get('/autocomplete/lemmas', async (c) => {
  try {
    const query = c.req.query('q') || '';
    const language = c.req.query('lang') || null;
    const limit = parseInt(c.req.query('limit') || '10', 10);
    const minCount = parseInt(c.req.query('min_count') || '2', 10);
    const fuzzy = c.req.query('fuzzy') === 'true';

    if (!query || query.length < 1) {
      return c.json({ suggestions: [] });
    }

    const db = new DatabaseService(c.env);
    const queryLower = query.toLowerCase();
    const useLatinSearch = isLatinQuery(query);

    let results: any[];

    if (fuzzy) {
      // Fuzzy search using trigram similarity
      results = await db.autocompleteLemmasFuzzy(
        queryLower,
        language,
        limit,
        minCount,
        useLatinSearch
      );
    } else {
      // Prefix search (fast)
      results = await db.autocompleteLemmasPrefix(
        queryLower,
        language,
        limit,
        minCount,
        useLatinSearch
      );
    }

    return c.json({
      suggestions: results.map(r => ({
        lemma: r.lemma,
        lemma_latin: r.lemma_latin,
        language: r.language,
        pos: r.pos,
        count: r.count,
        passage_count: r.passage_count,
        forms: r.forms || [],
      })),
      query,
      mode: useLatinSearch ? 'latin-to-greek' : 'direct',
      fuzzy,
    });
  } catch (error) {
    logger.error('Autocomplete error', error);
    return c.json({ error: 'Autocomplete failed' }, 500);
  }
});
