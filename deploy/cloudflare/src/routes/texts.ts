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
