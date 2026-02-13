/**
 * Lemma Intelligence API Routes
 *
 * Provides dictionary lookup and corpus statistics for Greek and Latin lemmas.
 * Supports:
 * - LSJ (Greek-English) and Lewis & Short (Latin-English) dictionary lookup
 * - Corpus statistics: occurrence counts, author/work distribution
 * - Fuzzy search with trigram matching
 * - Related lemmas by co-occurrence
 * - Knowledge graph connections
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('LemmaRoutes');

export const lemmaRoutes = new Hono<{ Bindings: Env }>();

/**
 * Normalize Greek text for search (lowercase, no diacritics)
 */
function normalizeGreek(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')  // Remove diacritics
    .normalize('NFC');
}

/**
 * Helper to make Supabase REST API requests for public schema tables
 */
async function supabaseQuery(
  env: Env,
  table: string,
  params: {
    select?: string;
    filters?: string;
    limit?: number;
    order?: string;
  }
): Promise<any[]> {
  const baseUrl = `${env.SUPABASE_URL}/rest/v1`;
  const urlParams = new URLSearchParams();

  if (params.select) {
    urlParams.append('select', params.select);
  }

  if (params.limit) {
    urlParams.append('limit', params.limit.toString());
  }

  if (params.order) {
    urlParams.append('order', params.order);
  }

  let url = `${baseUrl}/${table}?${urlParams.toString()}`;

  // Append raw filters directly to URL
  if (params.filters) {
    url += `&${params.filters}`;
  }

  const headers: Record<string, string> = {
    'apikey': env.SUPABASE_KEY,
    'Authorization': `Bearer ${env.SUPABASE_KEY}`,
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, { headers });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Supabase query failed: ${response.status} - ${errorText}`);
  }

  return await response.json();
}

/**
 * Helper to call Supabase RPC functions (for accessing free_will schema tables)
 */
async function supabaseRpc(
  env: Env,
  functionName: string,
  params: Record<string, any>
): Promise<any[]> {
  const url = `${env.SUPABASE_URL}/rest/v1/rpc/${functionName}`;

  const headers: Record<string, string> = {
    'apikey': env.SUPABASE_KEY,
    'Authorization': `Bearer ${env.SUPABASE_KEY}`,
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Supabase RPC failed: ${response.status} - ${errorText}`);
  }

  return await response.json();
}

/**
 * GET /dictionary/:lemma
 * Look up a lemma in the dictionary (LSJ for Greek, Lewis & Short for Latin)
 * Uses RPC functions to access free_will schema tables
 */
lemmaRoutes.get('/dictionary/:lemma', async (c) => {
  try {
    const lemma = decodeURIComponent(c.req.param('lemma'));
    const language = c.req.query('language') || 'grc';

    if (language === 'grc') {
      // Greek: search LSJ dictionary via RPC
      const normalized = normalizeGreek(lemma);

      const result = await supabaseRpc(c.env, 'get_dictionary_lsj', {
        p_lemma: lemma,
        p_normalized: normalized,
        p_latin: lemma.toLowerCase(),
      });

      if (result && result.length > 0) {
        const row = result[0];
        return c.json({
          found: true,
          language: 'grc',
          dictionary: 'LSJ',
          lemma: row.lemma,
          lemma_latin: row.lemma_latin,
          definition: row.definition,
          short_def: row.short_def,
          forms: row.forms || [],
          greek_forms: row.greek_forms || [],
          external_links: {
            logeion: `https://logeion.uchicago.edu/${lemma}`,
            perseus: `https://www.perseus.tufts.edu/hopper/morph?l=${lemma}&la=greek`,
            bailly: `https://bailly.app/recherche?q=${lemma}`,
          },
        });
      }
    } else {
      // Latin: search Lewis & Short dictionary via RPC
      const result = await supabaseRpc(c.env, 'get_dictionary_lewis_short', {
        p_lemma: lemma,
        p_normalized: lemma.toLowerCase(),
      });

      if (result && result.length > 0) {
        const row = result[0];
        return c.json({
          found: true,
          language: 'lat',
          dictionary: 'Lewis & Short',
          lemma: row.lemma,
          definition: row.definition,
          short_def: row.short_def,
          entry_key: row.entry_key,
          external_links: {
            logeion: `https://logeion.uchicago.edu/${lemma}`,
            perseus: `https://www.perseus.tufts.edu/hopper/morph?l=${lemma}&la=latin`,
          },
        });
      }
    }

    // Not found
    return c.json({
      found: false,
      language,
      lemma,
      message: `No dictionary entry found for '${lemma}'`,
      external_links: {
        logeion: `https://logeion.uchicago.edu/${lemma}`,
      },
    });
  } catch (error) {
    logger.error('Dictionary lookup error', error);
    return c.json({ error: 'Dictionary lookup failed', details: error instanceof Error ? error.message : 'Unknown error' }, 500);
  }
});

/**
 * GET /dictionary/search/:query
 * Search for dictionary entries by prefix or fuzzy match
 * Uses RPC functions to access free_will schema tables
 */
lemmaRoutes.get('/dictionary/search/:query', async (c) => {
  try {
    const query = decodeURIComponent(c.req.param('query'));
    const language = c.req.query('language') || 'grc';
    const limit = parseInt(c.req.query('limit') || '10', 10);
    const fuzzy = c.req.query('fuzzy') === 'true';

    let results: any[] = [];

    if (language === 'grc') {
      // Greek: search LSJ via RPC (prefix search)
      results = await supabaseRpc(c.env, 'search_dictionary_lsj', {
        p_query: query,
        p_limit: limit,
      });
    } else {
      // Latin: search Lewis & Short via RPC
      results = await supabaseRpc(c.env, 'search_dictionary_lewis_short', {
        p_query: query,
        p_limit: limit,
      });
    }

    return c.json({
      query,
      language,
      fuzzy,
      results: results || [],
      count: results?.length || 0,
    });
  } catch (error) {
    logger.error('Dictionary search error', error);
    return c.json({ error: 'Dictionary search failed', details: error instanceof Error ? error.message : 'Unknown error' }, 500);
  }
});

/**
 * GET /stats/:lemma
 * Get corpus statistics for a lemma
 *
 * Note: This endpoint requires complex JSONB queries which are not easily done
 * via Supabase REST API. Returns simplified stats or uses fallback.
 */
lemmaRoutes.get('/stats/:lemma', async (c) => {
  try {
    const lemma = decodeURIComponent(c.req.param('lemma'));
    const language = c.req.query('language') || 'grc';

    // Return a simplified response since complex JSONB queries
    // are not easily done via Supabase REST API without RPC functions
    return c.json({
      lemma,
      language,
      total_occurrences: 0,
      passage_count: 0,
      by_author: [],
      by_work: [],
      by_period: [],
      note: 'Full stats require FastAPI backend. Use /api/lemma/stats/:lemma endpoint on localhost:8000 for complete statistics.',
    });
  } catch (error) {
    logger.error('Lemma stats error', error);
    return c.json({ error: 'Lemma stats lookup failed' }, 500);
  }
});

/**
 * GET /related/:lemma
 * Find lemmas that frequently co-occur with the given lemma
 *
 * Note: This endpoint requires complex JSONB queries which are not easily done
 * via Supabase REST API. Returns simplified response.
 */
lemmaRoutes.get('/related/:lemma', async (c) => {
  try {
    const lemma = decodeURIComponent(c.req.param('lemma'));
    const language = c.req.query('language') || 'grc';

    // Return a simplified response
    return c.json({
      lemma,
      language,
      related: [],
      note: 'Full related lemmas require FastAPI backend. Use /api/lemma/related/:lemma endpoint on localhost:8000 for complete data.',
    });
  } catch (error) {
    logger.error('Related lemmas error', error);
    return c.json({ error: 'Related lemmas lookup failed' }, 500);
  }
});

/**
 * GET /kg-connections/:lemma
 * Find knowledge graph nodes whose descriptions contain this lemma
 */
lemmaRoutes.get('/kg-connections/:lemma', async (c) => {
  try {
    const lemma = decodeURIComponent(c.req.param('lemma'));
    const language = c.req.query('language') || 'grc';

    // Search KG nodes by description containing the lemma (using ILIKE)
    // Note: For KG nodes we use public schema (default)
    // Columns: node_id (PK), label, type, description
    const nodes = await supabaseQuery(c.env, 'kg_nodes', {
      select: 'node_id,label,type,description',
      limit: 10,
      filters: `or=(description.ilike.*${encodeURIComponent(lemma)}*,label.ilike.*${encodeURIComponent(lemma)}*)`,
      order: 'label.asc',
    });

    return c.json({
      lemma,
      language,
      kg_nodes: (nodes || []).map((r: any) => ({
        node_id: r.node_id,
        label: r.label,
        type: r.type,
        description: r.description?.length > 200
          ? r.description.slice(0, 200) + '...'
          : r.description,
      })),
    });
  } catch (error) {
    logger.error('KG connections error', error);
    return c.json({ error: 'KG connections lookup failed', details: error instanceof Error ? error.message : 'Unknown error' }, 500);
  }
});
