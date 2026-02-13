/**
 * Works Routes (Ancient Works API)
 * This routes module serves ancient_works and passages via RPC functions
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { DatabaseService } from '../services/database';
import { CacheService } from '../services/cache';
import { getLogger } from '../utils/logger';

const logger = getLogger('WorksRoutes');

export const worksRoutes = new Hono<{ Bindings: Env }>();

// Cache TTLs
const CACHE_TTL = {
  WORK: 3600,      // 1 hour for individual works
  LIST: 300,       // 5 minutes for lists
  PASSAGES: 1800,  // 30 minutes for passages
  SEARCH: 600,     // 10 minutes for searches
};

// List works with filters
worksRoutes.get('/', async (c) => {
  try {
    const db = new DatabaseService(c.env);

    const author = c.req.query('author');
    const language = c.req.query('language');
    const sortBy = c.req.query('sort_by');
    const offset = parseInt(c.req.query('offset') || '0');
    const limit = parseInt(c.req.query('limit') || '50');

    const filters: any = {};
    if (author) filters.author = author;
    if (language) filters.language = language;
    if (sortBy) filters.sort_by = sortBy;

    // Get both the paginated results and the total count
    const [result, totalCount] = await Promise.all([
      db.listTexts({
        ...filters,
        offset,
        limit,
      }),
      db.countTexts(filters),
    ]);

    return c.json({
      works: result.rows,
      total: totalCount,
      offset,
      limit,
    });
  } catch (error) {
    logger.error('Error listing works', error);
    return c.json({ error: 'Failed to list works' }, 500);
  }
});

// Search passages (must be before /:id route)
worksRoutes.get('/search/passages', async (c) => {
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

// Get work statistics (must be before /:id route)
worksRoutes.get('/stats', async (c) => {
  try {
    const cache = new CacheService(c.env);
    const db = new DatabaseService(c.env);

    // Cache key for stats
    const cacheKey = 'works:stats:global:v2';

    // Try to get from cache first
    const cachedStats = await cache.get(cacheKey);
    if (cachedStats) {
      return c.json(cachedStats);
    }

    // Query Supabase RPC for live counts
    const rawStats = await db.rpc('get_text_stats');
    const parsedStats = typeof rawStats === 'string' ? JSON.parse(rawStats) : rawStats;

    const languagesField = parsedStats?.languages;
    let languages: string[] = [];
    let worksByLanguage: Record<string, number> = {};

    if (Array.isArray(languagesField)) {
      languages = languagesField.filter(Boolean);
    } else if (languagesField && typeof languagesField === 'object') {
      languages = Object.keys(languagesField);
      worksByLanguage = languagesField;
    }

    if (parsedStats?.works_by_language && typeof parsedStats.works_by_language === 'object') {
      worksByLanguage = parsedStats.works_by_language;
      if (languages.length === 0) {
        languages = Object.keys(worksByLanguage);
      }
    }

    const stats = {
      total_works: parsedStats?.total_works ?? 0,
      total_passages: parsedStats?.total_passages ?? 0,
      total_characters: parsedStats?.total_characters ?? 0,
      languages,
      works_by_language: worksByLanguage,
      periods: parsedStats?.periods ?? null,
      source: 'rpc:get_text_stats',
      refreshed_at: new Date().toISOString()
    };

    // Cache for 1 hour since these are relatively stable
    await cache.set(cacheKey, stats, 3600);

    return c.json(stats);
  } catch (error) {
    logger.error('Error fetching work stats', error);
    return c.json({
      error: 'Failed to fetch work stats',
      details: error instanceof Error ? error.message : String(error)
    }, 500);
  }
});

// Get work statistics (legacy overview endpoint)
worksRoutes.get('/stats/overview', async (c) => {
  try {
    const db = new DatabaseService(c.env);

    // Get basic stats
    const stats = await db.rpc('get_text_stats');

    return c.json(stats);
  } catch (error) {
    logger.error('Error fetching work stats', error);
    return c.json({ error: 'Failed to fetch work stats' }, 500);
  }
});

// Get a specific passage (must be before /:id route)
worksRoutes.get('/passage/:passageId', async (c) => {
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

// Get work by KG work ID (must be before /:id route)
worksRoutes.get('/by-kg/:kgWorkId', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const kgWorkId = c.req.param('kgWorkId');

    const work = await db.getTextByKgWorkId(kgWorkId);

    if (!work) {
      return c.json({ error: 'Work not found' }, 404);
    }

    return c.json(work);
  } catch (error) {
    logger.error('Error fetching work by KG work ID', error);
    return c.json({ error: 'Failed to fetch work' }, 500);
  }
});

// Get passages for a work
worksRoutes.get('/:workId/passages', async (c) => {
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

// Get work structure
worksRoutes.get('/:id/structure', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const id = c.req.param('id');

    const work = await db.getText(id);

    if (!work) {
      return c.json({ error: 'Work not found' }, 404);
    }

    // Extract structure from work metadata or content
    const structure = {
      id: work.id,
      title: work.title,
      author: work.author,
      books: work.structure?.books || [],
      chapters: work.structure?.chapters || [],
    };

    return c.json(structure);
  } catch (error) {
    logger.error('Error fetching work structure', error);
    return c.json({ error: 'Failed to fetch work structure' }, 500);
  }
});

// Get work by ID (must be last among /:id routes)
worksRoutes.get('/:id', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const cache = new CacheService(c.env);
    const id = c.req.param('id');

    const cacheKey = CacheService.generateKey('work', id);
    const work = await cache.cached(
      cacheKey,
      () => db.getText(id),
      CACHE_TTL.WORK
    );

    if (!work) {
      return c.json({ error: 'Work not found' }, 404);
    }

    return c.json(work);
  } catch (error) {
    logger.error('Error fetching work', error);
    return c.json({ error: 'Failed to fetch work' }, 500);
  }
});
