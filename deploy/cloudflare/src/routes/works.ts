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

type PassageRefRow = {
  passage_id: string;
  canonical_ref?: string | null;
  sequence_number?: number | null;
  book?: string | null;
  chapter?: string | null;
  section?: string | null;
};

function buildPassageRef(row: PassageRefRow) {
  const canonicalRef = row.canonical_ref || [
    row.book,
    row.chapter,
    row.section,
  ].filter(Boolean).join('.');

  return {
    passage_id: row.passage_id,
    canonical_ref: canonicalRef,
    sequence_number: row.sequence_number || 0,
  };
}

function buildTableOfContents(rows: PassageRefRow[]) {
  const toc: {
    books: Record<string, { chapters: Record<string, { sections: Array<ReturnType<typeof buildPassageRef>>; passages: Array<ReturnType<typeof buildPassageRef>> }>; passages: Array<ReturnType<typeof buildPassageRef>> }>;
    chapters: Record<string, { sections: Array<ReturnType<typeof buildPassageRef>>; passages: Array<ReturnType<typeof buildPassageRef>> }>;
    sections: Array<ReturnType<typeof buildPassageRef>>;
    flat: Array<ReturnType<typeof buildPassageRef>>;
  } = {
    books: {},
    chapters: {},
    sections: [],
    flat: [],
  };

  for (const row of rows) {
    const entry = buildPassageRef(row);
    toc.flat.push(entry);

    if (row.book) {
      const bookKey = String(row.book);
      const book = toc.books[bookKey] ||= { chapters: {}, passages: [] };

      if (row.chapter) {
        const chapterKey = String(row.chapter);
        const chapter = book.chapters[chapterKey] ||= { sections: [], passages: [] };
        chapter.sections.push(entry);
        chapter.passages.push(entry);
      } else {
        book.passages.push(entry);
      }
      continue;
    }

    if (row.chapter) {
      const chapterKey = String(row.chapter);
      const chapter = toc.chapters[chapterKey] ||= { sections: [], passages: [] };
      chapter.sections.push(entry);
      chapter.passages.push(entry);
      continue;
    }

    toc.sections.push(entry);
  }

  return toc;
}

function normalizeReference(reference: string): string {
  return reference
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[;,]+$/g, '');
}

function buildReferenceCandidates(row: PassageRefRow): string[] {
  const candidates = new Set<string>();
  const add = (value?: string | null) => {
    if (value) {
      candidates.add(normalizeReference(value));
    }
  };

  add(row.canonical_ref);
  if (row.canonical_ref) {
    const trimmed = row.canonical_ref.trim();
    const lastToken = trimmed.split(/\s+/).pop();
    add(lastToken);
  }

  const parts = [row.book, row.chapter, row.section].filter(Boolean).map(String);
  if (parts.length > 0) {
    add(parts.join('.'));
    add(parts.join(':'));
  }
  if (row.book && row.section) {
    add(`${row.book}.${row.section}`);
  }
  if (row.chapter && row.section) {
    add(`${row.chapter}.${row.section}`);
  }
  add(row.section || null);

  return Array.from(candidates);
}

function matchesCanonicalReference(row: PassageRefRow, reference: string): boolean {
  const needle = normalizeReference(reference);
  if (!needle) {
    return false;
  }

  const canonical = normalizeReference(row.canonical_ref || '');
  if (canonical === needle) {
    return true;
  }

  const lastToken = normalizeReference((row.canonical_ref || '').trim().split(/\s+/).pop() || '');
  return lastToken === needle;
}

function matchesReference(row: PassageRefRow, reference: string): boolean {
  const needle = normalizeReference(reference);
  if (!needle) {
    return false;
  }

  return buildReferenceCandidates(row).includes(needle);
}

async function getCachedPassageRefs(cache: CacheService, db: DatabaseService, workId: string) {
  const cacheKey = CacheService.generateKey('passage-refs', workId);
  return cache.cached(
    cacheKey,
    () => db.getPassageRefs(workId),
    CACHE_TTL.PASSAGES,
  );
}

async function searchPassagesResponse(c: any, query: string | null) {
  const db = new DatabaseService(c.env);
  const limit = parseInt(c.req.query('limit') || '20');
  const author = c.req.query('author') || undefined;
  const language = c.req.query('language') || undefined;
  const period = c.req.query('period') || undefined;

  if (!query) {
    return c.json({ error: 'Query parameter is required' }, 400);
  }

  const results = await db.searchPassages(query, limit, {
    author,
    language,
    period,
  });

  return c.json({
    query,
    results,
    total: results.length,
  });
}

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
    return await searchPassagesResponse(c, c.req.query('q') || c.req.query('query'));
  } catch (error) {
    logger.error('Error searching passages', error);
    return c.json({ error: 'Failed to search passages' }, 500);
  }
});

// Frontend compatibility alias used by AdvancedSearchPage
worksRoutes.get('/search', async (c) => {
  try {
    return await searchPassagesResponse(c, c.req.query('query') || c.req.query('q'));
  } catch (error) {
    logger.error('Error searching works', error);
    return c.json({ error: 'Failed to search works' }, 500);
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

worksRoutes.get('/:workId/table-of-contents', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const cache = new CacheService(c.env);
    const workId = c.req.param('workId');
    const refs = await getCachedPassageRefs(cache, db, workId);

    return c.json({
      work_id: workId,
      total_passages: refs.rowCount,
      toc: buildTableOfContents(refs.rows as PassageRefRow[]),
    });
  } catch (error) {
    logger.error('Error fetching table of contents', error);
    return c.json({ error: 'Failed to fetch table of contents' }, 500);
  }
});

worksRoutes.get('/:workId/passages/by-reference', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const cache = new CacheService(c.env);
    const workId = c.req.param('workId');
    const reference = c.req.query('reference');

    if (!reference) {
      return c.json({ error: 'Reference parameter is required' }, 400);
    }

    const refs = (await getCachedPassageRefs(cache, db, workId)).rows as PassageRefRow[];
    const exactMatches = refs.filter((row) => matchesCanonicalReference(row, reference));
    const fallbackMatches = exactMatches.length === 0
      ? refs.filter((row) => matchesReference(row, reference))
      : exactMatches;

    const passages = fallbackMatches
      .slice(0, 20)
      .map((row) => ({
        passage_id: row.passage_id,
        canonical_ref: row.canonical_ref,
        sequence_number: row.sequence_number || 0,
        book: row.book || null,
        chapter: row.chapter || null,
        section: row.section || null,
      }));

    return c.json({
      reference,
      passages,
      total: passages.length,
    });
  } catch (error) {
    logger.error('Error fetching passages by reference', error);
    return c.json({ error: 'Failed to fetch passages by reference' }, 500);
  }
});

worksRoutes.get('/:workId/kg-nodes', async (c) => {
  try {
    const db = new DatabaseService(c.env);
    const workId = c.req.param('workId');

    const [work, kgNodes] = await Promise.all([
      db.getText(workId),
      db.getWorkKGNodes(workId),
    ]);

    if (!work) {
      return c.json({ error: 'Work not found' }, 404);
    }

    return c.json({
      work_id: workId,
      work_title: work.title || 'Unknown Work',
      work_author: work.author || 'Unknown Author',
      kg_nodes: kgNodes,
      total_nodes: kgNodes.length,
    });
  } catch (error) {
    logger.error('Error fetching work KG nodes', error);
    return c.json({ error: 'Failed to fetch work KG nodes' }, 500);
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
