/**
 * Text Routes
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { CacheService } from '../services/cache';
import { getLogger } from '../utils/logger';

const logger = getLogger('TextRoutes');

export const textRoutes = new Hono<{ Bindings: Env }>();

// Cache TTLs
const CACHE_TTL = {
  WORK: 3600,      // 1 hour for individual works
  LIST: 300,       // 5 minutes for lists
  PASSAGES: 1800,  // 30 minutes for passages
  SEARCH: 600,     // 10 minutes for searches
};

// Fetch citation passage - POST endpoint for looking up passages by citation reference
textRoutes.post('/citation-passage', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const body = await c.req.json();
    const { citation } = body;

    if (!citation || typeof citation !== 'string') {
      return c.json({
        error: 'Citation is required',
        citation: citation || '',
        original: null,
        originalLanguage: null,
        translation: null,
      }, 400);
    }

    logger.info(`Looking up citation: ${citation}`);

    const result = await db.searchPassageByCitation(citation);

    return c.json(result);
  } catch (error) {
    logger.error('Error fetching citation passage', error);
    return c.json({
      error: 'Failed to fetch citation passage',
      citation: '',
      original: null,
      originalLanguage: null,
      translation: null,
    }, 500);
  }
});

// List texts with filters
textRoutes.get('/list', async (c) => {
  try {
    const db = new DatabaseService(c.env);

    const category = c.req.query('category');
    const author = c.req.query('author');
    const language = c.req.query('language');
    const offset = parseInt(c.req.query('offset') || '0');
    const limit = parseInt(c.req.query('limit') || '50');

    const filters: any = {};
    if (category) filters.category = category;
    if (author) filters.author = author;
    if (language) filters.language = language;

    const result = await db.listTexts({
      ...filters,
      offset,
      limit,
    });

    return c.json({
      texts: result.rows,
      total: result.rowCount,
      offset,
      limit,
    });
  } catch (error) {
    logger.error('Error listing texts', error);
    return c.json({ error: 'Failed to list texts' }, 500);
  }
});

// Search passages (must be before /:id route)
textRoutes.get('/search/passages', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const query = c.req.query('q');
    const limit = parseInt(c.req.query('limit') || '20');

    if (!query) {
      return c.json({ error: 'Query parameter "q" is required' }, 400);
    }

    const results = await db.searchPassages(query, limit);

    return c.json({
      query,
      results,
      total: results.length,
    });
  } catch (error) {
    logger.error('Error searching passages', error);
    return c.json({ error: 'Failed to search passages' }, 500);
  }
});

// Get text statistics (must be before /:id route)
textRoutes.get('/stats/overview', async (c) => {
  try {
    const db = new DatabaseService(c.env);

    // Get basic stats
    const stats = await db.rpc('get_text_stats');

    return c.json(stats);
  } catch (error) {
    logger.error('Error fetching text stats', error);
    return c.json({ error: 'Failed to fetch text stats' }, 500);
  }
});

// Get passage with surrounding context for the passage reader panel.
// Accepts EITHER a passage UUID or a KG node ID (resolved via passage_citations).
textRoutes.get('/passage/:passageId/context', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const rawId = c.req.param('passageId');
    const window = parseInt(c.req.query('window') || '5');

    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    let resolvedPassageId: string | null = null;

    if (uuidPattern.test(rawId)) {
      // Direct passage UUID
      resolvedPassageId = rawId;
    } else {
      // KG node ID — resolve to best linked passage via passage_citations
      resolvedPassageId = await resolveKgNodeToPassage(rawId, c.env);
      if (!resolvedPassageId) {
        return c.json({ error: 'No linked passage found for this KG node' }, 404);
      }
      logger.info(`Resolved KG node ${rawId} → passage ${resolvedPassageId}`);
    }

    // 1. Get the target passage via RPC
    const target = await db.getPassage(resolvedPassageId);
    if (!target) {
      return c.json({ error: 'Passage not found' }, 404);
    }

    const workId = target.work_id;
    const seqNum = target.sequence_number || 0;

    // 2. Get work metadata
    let workMeta: any = null;
    try {
      workMeta = await db.getText(workId);
    } catch {
      // Work metadata is optional
    }
    const author = workMeta?.author || target.author || 'Unknown';
    const workTitle = workMeta?.title || target.title || 'Unknown Work';
    const language = workMeta?.language || target.language || 'grc';

    // 3. Fetch all passages for the work and find surrounding ones by sequence_number
    const allPassages = await db.getPassages(workId, { limit: 1000 });
    const allRows = allPassages.rows || [];

    const sorted = allRows
      .filter((p: any) => p.sequence_number != null)
      .sort((a: any, b: any) => (a.sequence_number || 0) - (b.sequence_number || 0));

    const minSeq = Math.max(0, seqNum - window);
    const maxSeq = seqNum + window;
    const contextRows = sorted.filter((p: any) =>
      p.sequence_number >= minSeq && p.sequence_number <= maxSeq
    );

    // 4. Build response
    const formatRef = (p: any) => {
      if (p.canonical_ref) return p.canonical_ref;
      const loc: string[] = [];
      if (p.book) loc.push(p.book);
      if (p.chapter) loc.push(p.chapter);
      if (p.section) loc.push(p.section);
      return loc.length > 0 ? loc.join('.') : '';
    };

    const passages = contextRows.map((p: any) => ({
      passageId: p.passage_id,
      textContent: p.text_content || '',
      canonicalRef: formatRef(p),
      author,
      workTitle,
      language: language === 'lat' ? 'lat' : 'grc',
      ctsUrn: p.cts_urn || undefined,
      book: p.book || undefined,
      chapter: p.chapter || undefined,
      section: p.section || undefined,
      sequenceNumber: p.sequence_number || 0,
      isTarget: p.passage_id === resolvedPassageId,
    }));

    const targetPassage = passages.find((p: any) => p.isTarget) || passages[0];

    return c.json({
      target: targetPassage,
      passages,
      workId,
      totalPassagesInWork: sorted.length,
    });
  } catch (error) {
    logger.error('Error fetching passage context', error);
    return c.json({ error: 'Failed to fetch passage context' }, 500);
  }
});

/**
 * Resolve a KG node ID to the best linked passage UUID via passage_citations.
 * Tries free_will schema first, then public schema fallback.
 */
async function resolveKgNodeToPassage(kgNodeId: string, env: Env): Promise<string | null> {
  const supabaseUrl = env.SUPABASE_URL.replace(/\/+$/, '').replace(/\/rest\/v1$/i, '');
  const supabaseKey = env.SUPABASE_KEY;
  const encodedId = encodeURIComponent(kgNodeId);

  // Strategy 1: Try passage_citations table (with free_will → public fallback)
  const select = 'confidence,passage_id';
  const url = `${supabaseUrl}/rest/v1/passage_citations?kg_node_id=eq.${encodedId}&select=${select}&order=confidence.desc.nullslast&limit=1`;

  for (const headers of [
    { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}`, 'Accept-Profile': 'free_will' },
    { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}` },
  ]) {
    try {
      const response = await fetch(url, { headers });
      if (response.ok) {
        const rows = await response.json() as any[];
        if (Array.isArray(rows) && rows.length > 0 && rows[0].passage_id) {
          return rows[0].passage_id;
        }
        logger.info(`passage_citations query OK but no rows for ${kgNodeId}`);
        break; // Table accessible but no data — no point trying next schema
      }
      const errText = await response.text().catch(() => '');
      logger.warn(`passage_citations query (${response.status}): ${errText.slice(0, 200)}`);
    } catch (e) {
      logger.warn(`passage_citations fetch error: ${e}`);
    }
  }

  // Strategy 2: Parse KG node ID to find work + chapter/section
  // Pattern: passage_{author}_{work_abbrev}_{chapter}_{section}
  // e.g. "passage_tatian_orat_8_9" → author=tatian, work≈orat, chapter=8 or 9
  try {
    const db = new DatabaseService(env);
    const stripped = kgNodeId.replace(/^passage_/, '');
    // Extract trailing numbers (chapter/section candidates)
    const parts = stripped.split('_');
    const numbers: string[] = [];
    const words: string[] = [];
    for (const p of parts) {
      if (/^\d+$/.test(p)) numbers.push(p);
      else words.push(p);
    }
    const authorHint = words[0] || '';
    // List all works, find one matching the author hint
    if (authorHint) {
      const worksResult = await db.listTexts({ limit: 200, offset: 0 });
      const works = (worksResult as any)?.rows || [];
      const matchedWork = works.find((w: any) =>
        w.author?.toLowerCase().includes(authorHint.toLowerCase())
      );
      if (matchedWork) {
        const workId = matchedWork.work_id || matchedWork.id;
        // Try chapter/section combinations from the numbers
        for (const chapter of numbers) {
          // Try each remaining number as section, or section "1"
          const sections = numbers.filter(n => n !== chapter);
          if (sections.length === 0) sections.push('1');
          for (const section of sections) {
            const passagesResult = await db.getPassages(workId, { chapter, section, limit: 1 });
            const rows = passagesResult?.rows || [];
            if (rows.length > 0 && rows[0].passage_id) {
              logger.info(`Resolved ${kgNodeId} → ${matchedWork.author} ch${chapter}.${section}: ${rows[0].passage_id}`);
              return rows[0].passage_id;
            }
          }
        }
        // If no chapter/section match, just get the first passage of the last number as chapter
        if (numbers.length > 0) {
          const passagesResult = await db.getPassages(workId, { chapter: numbers[numbers.length - 1], limit: 1 });
          const rows = passagesResult?.rows || [];
          if (rows.length > 0 && rows[0].passage_id) {
            logger.info(`Resolved ${kgNodeId} → ${matchedWork.author} ch${numbers[numbers.length - 1]}: ${rows[0].passage_id}`);
            return rows[0].passage_id;
          }
        }
      }
    }
  } catch (e) {
    logger.warn(`Structured resolve failed for ${kgNodeId}: ${e}`);
  }

  logger.warn(`No passage found for KG node ${kgNodeId}`);
  return null;
}

// Get a specific passage (must be before /:id route)
textRoutes.get('/passage/:passageId', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const passageId = c.req.param('passageId');

    const passage = await db.getPassage(passageId);

    if (!passage) {
      return c.json({ error: 'Passage not found' }, 404);
    }

    return c.json(passage);
  } catch (error) {
    logger.error('Error fetching passage', error);
    return c.json({ error: 'Failed to fetch passage' }, 500);
  }
});

// Get text by KG work ID (must be before /:id route)
textRoutes.get('/by-kg/:kgWorkId', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const kgWorkId = c.req.param('kgWorkId');

    const text = await db.getTextByKgWorkId(kgWorkId);

    if (!text) {
      return c.json({ error: 'Text not found' }, 404);
    }

    return c.json(text);
  } catch (error) {
    logger.error('Error fetching text by KG work ID', error);
    return c.json({ error: 'Failed to fetch text' }, 500);
  }
});

// Get passages for a work
textRoutes.get('/:workId/passages', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const cache = new CacheService(c.env);
    const workId = c.req.param('workId');

    const book = c.req.query('book');
    const chapter = c.req.query('chapter');
    const section = c.req.query('section');
    const offset = parseInt(c.req.query('offset') || '0');
    const limit = parseInt(c.req.query('limit') || '100');

    const cacheKey = CacheService.generateKey(
      'passages',
      workId,
      book || '',
      chapter || '',
      section || '',
      offset,
      limit
    );

    const result = await cache.cached(
      cacheKey,
      () => db.getPassages(workId, { book, chapter, section, offset, limit }),
      CACHE_TTL.PASSAGES
    );

    return c.json({
      passages: result.rows,
      total: result.rowCount,
      offset,
      limit,
    });
  } catch (error) {
    logger.error('Error fetching passages', error);
    return c.json({ error: 'Failed to fetch passages' }, 500);
  }
});

// Get text structure
textRoutes.get('/:id/structure', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const id = c.req.param('id');

    const text = await db.getText(id);

    if (!text) {
      return c.json({ error: 'Text not found' }, 404);
    }

    // Extract structure from text metadata or content
    const structure = {
      id: text.id,
      title: text.title,
      author: text.author,
      books: text.structure?.books || [],
      chapters: text.structure?.chapters || [],
    };

    return c.json(structure);
  } catch (error) {
    logger.error('Error fetching text structure', error);
    return c.json({ error: 'Failed to fetch text structure' }, 500);
  }
});

// Get text by ID (must be last among /:id routes)
textRoutes.get('/:id', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const cache = new CacheService(c.env);
    const id = c.req.param('id');

    const cacheKey = CacheService.generateKey('work', id);
    const text = await cache.cached(
      cacheKey,
      () => db.getText(id),
      CACHE_TTL.WORK
    );

    if (!text) {
      return c.json({ error: 'Text not found' }, 404);
    }

    return c.json(text);
  } catch (error) {
    logger.error('Error fetching text', error);
    return c.json({ error: 'Failed to fetch text' }, 500);
  }
});
