/**
 * Supabase PostgreSQL Database Service
 */

import { Env, QueryResult } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('DatabaseService');

export class DatabaseService {
  private supabaseUrl: string;
  private supabaseKey: string;
  private baseUrl: string;

  constructor(env: Env) {
    // Accept either:
    // - https://<project>.supabase.co
    // - https://<project>.supabase.co/rest/v1
    // and normalize to a single base URL.
    this.supabaseUrl = env.SUPABASE_URL
      .replace(/\/+$/, '')
      .replace(/\/rest\/v1$/i, '');
    this.supabaseKey = env.SUPABASE_KEY;
    this.baseUrl = `${this.supabaseUrl}/rest/v1`;
  }

  /**
   * Execute a SQL query using Supabase REST API
   */
  private async query<T = any>(
    table: string,
    params?: {
      select?: string;
      filters?: Record<string, any>;
      limit?: number;
      offset?: number;
      order?: string;
      schema?: string;
    }
  ): Promise<QueryResult<T>> {
    try {
      let url = `${this.baseUrl}/${table}`;
      const urlParams = new URLSearchParams();

      if (params?.select) {
        urlParams.append('select', params.select);
      } else {
        urlParams.append('select', '*');
      }

      if (params?.filters) {
        Object.entries(params.filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            urlParams.append(key, `eq.${value}`);
          }
        });
      }

      if (params?.limit) {
        urlParams.append('limit', params.limit.toString());
      }

      if (params?.offset) {
        urlParams.append('offset', params.offset.toString());
      }

      if (params?.order) {
        urlParams.append('order', params.order);
      }

      url += `?${urlParams.toString()}`;

      const headers: Record<string, string> = {
        'apikey': this.supabaseKey,
        'Authorization': `Bearer ${this.supabaseKey}`,
        'Content-Type': 'application/json',
      };

      // Add schema header for non-public schemas
      if (params?.schema) {
        headers['Accept-Profile'] = params.schema;
      }

      const response = await fetch(url, { headers });

      if (!response.ok) {
        const errorText = await response.text();

        // Fallback: some deployments host tables in `free_will` instead of `public`.
        if (response.status === 404 && !params?.schema) {
          logger.warn(`Table ${table} not found in default schema, retrying in free_will`);
          return this.query<T>(table, {
            ...params,
            schema: 'free_will',
          });
        }

        throw new Error(
          `Database query failed: ${response.status} ${response.statusText}${
            errorText ? ` - ${errorText}` : ''
          }`,
        );
      }

      const rows = await response.json();
      return {
        rows,
        rowCount: rows.length,
      };
    } catch (error) {
      logger.error('Database query error', error);
      throw error;
    }
  }

  /**
   * Execute raw SQL using Supabase RPC
   * @param functionName - Name of the RPC function
   * @param params - Parameters to pass to the function
   * @param schema - Optional schema name (for functions in non-public schemas)
   */
  async rpc<T = any>(functionName: string, params?: Record<string, any>, schema?: string): Promise<T> {
    try {
      const url = `${this.baseUrl}/rpc/${functionName}`;

      const headers: Record<string, string> = {
        'apikey': this.supabaseKey,
        'Authorization': `Bearer ${this.supabaseKey}`,
        'Content-Type': 'application/json',
      };

      // Add Content-Profile header for non-public schemas
      if (schema) {
        headers['Content-Profile'] = schema;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(params || {}),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`RPC call failed: ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('RPC call error', error);
      throw error;
    }
  }

  // KG Queries
  // Use RPC pagination (public.list_kg_nodes) to bypass Supabase REST API limits
  async getNodes(filters?: { type?: string; period?: string; school?: string }) {
    // list_kg_nodes signature: (p_limit, p_offset, p_type)
    const allRows: any[] = [];
    let offset = 0;
    const pageSize = 1000;
    const requestedType = filters?.type || null;

    while (true) {
      const rows = await this.rpc<any[]>('list_kg_nodes', {
        p_limit: pageSize,
        p_offset: offset,
        p_type: requestedType,
      });
      const page = Array.isArray(rows) ? rows : [];
      allRows.push(...page);

      if (page.length < pageSize) {
        break; // No more pages
      }
      offset += pageSize;
    }

    // Apply additional client-side filters not supported by RPC signature
    let filteredRows = allRows;
    if (filters?.period) {
      filteredRows = filteredRows.filter((row) => row.period === filters.period);
    }
    if (filters?.school) {
      filteredRows = filteredRows.filter((row) => row.school === filters.school);
    }

    // Normalize column names: map node_id to id for consistency with frontend/analytics
    return {
      rows: filteredRows.map((row: any) => ({
        ...row,
        id: row.node_id,  // Add 'id' field mapped from 'node_id'
      })),
      rowCount: filteredRows.length,
    };
  }

  async getEdges(filters?: { relation?: string }) {
    // list_kg_edges signature: (p_limit, p_offset, p_relation)
    const allRows: any[] = [];
    let offset = 0;
    const pageSize = 1000;
    const requestedRelation = filters?.relation || null;

    while (true) {
      const rows = await this.rpc<any[]>('list_kg_edges', {
        p_limit: pageSize,
        p_offset: offset,
        p_relation: requestedRelation,
      });
      const page = Array.isArray(rows) ? rows : [];
      allRows.push(...page);

      if (page.length < pageSize) {
        break; // No more pages
      }
      offset += pageSize;
    }

    // Normalize column names: map source_id/target_id to source/target
    return {
      rows: allRows.map((row: any) => ({
        ...row,
        id: row.edge_id,      // Add 'id' field mapped from 'edge_id'
        source: row.source_id, // Add 'source' field mapped from 'source_id'
        target: row.target_id, // Add 'target' field mapped from 'target_id'
      })),
      rowCount: allRows.length,
    };
  }

  async getNode(id: string) {
    // Try dedicated RPC if available
    const candidateParamNames = ['p_node_id', 'node_id', 'p_id', 'id'];

    for (const paramName of candidateParamNames) {
      try {
        const payload = await this.rpc<any>('get_kg_node', { [paramName]: id });
        const row = Array.isArray(payload) ? payload[0] : payload;
        if (row && typeof row === 'object') {
          return { ...row, id: row.node_id || row.id };
        }
      } catch {
        // Continue trying alternate signatures.
      }
    }

    // Fallback: scan paginated RPC list and find by node_id.
    const allNodes = await this.getNodes();
    const row = allNodes.rows.find((n: any) => n.node_id === id || n.id === id);
    if (!row) return null;
    return { ...row, id: row.node_id || row.id };
  }

  async getNodesByIds(ids: string[]) {
    if (!ids || ids.length === 0) {
      return [];
    }

    // Supabase doesn't support simple IN queries via REST API
    // We'll need to fetch them individually or use RPC
    const promises = ids.map(id => this.getNode(id));
    const nodes = await Promise.all(promises);

    // Filter out nulls
    return nodes.filter(node => node !== null);
  }

  async getNodeConnections(id: string) {
    // Get edges where node is source or target
    try {
      // list_kg_edges does not expose source/target filters, so filter in memory.
      const allEdgesResult = await this.getEdges();
      const allEdges = allEdgesResult.rows as any[];
      const matchingEdges = allEdges.filter(
        (edge) => edge.source_id === id || edge.target_id === id || edge.source === id || edge.target === id,
      );
      const seen = new Set<string>();
      const uniqueEdges = matchingEdges.filter(edge => {
        const key = edge.edge_id || edge.id || `${edge.source_id}-${edge.target_id}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      // Get connected node IDs
      const connectedNodeIds = new Set<string>();
      uniqueEdges.forEach(edge => {
        if (edge.source_id !== id) connectedNodeIds.add(edge.source_id);
        if (edge.target_id !== id) connectedNodeIds.add(edge.target_id);
      });

      // Fetch connected nodes
      const connectedNodes = await this.getNodesByIds(Array.from(connectedNodeIds));

      return {
        edges: uniqueEdges,
        nodes: connectedNodes,
        totalEdges: uniqueEdges.length,
        totalNodes: connectedNodes.length,
      };
    } catch (error) {
      logger.error('Error fetching node connections', error);
      throw error;
    }
  }

  async getKGStats() {
    // Use RPC function to get accurate stats (bypasses Supabase 1000 row limit)
    // The get_kg_stats() function runs SQL directly in the database
    const result = await this.rpc<{
      totalNodes: number;
      totalEdges: number;
      nodeTypes: Record<string, number>;
    }>('get_kg_stats');

    return result;
  }

  // Text Queries (using RPC functions to access free_will schema)
  async listTexts(filters?: {
    category?: string;
    author?: string;
    language?: string;
    sort_by?: string;
    offset?: number;
    limit?: number;
  }) {
    const rows = await this.rpc('list_ancient_works', {
      p_author: filters?.author || null,
      p_language: filters?.language || null,
      p_sort_by: filters?.sort_by || 'author',
      p_limit: filters?.limit || 50,
      p_offset: filters?.offset || 0,
    });

    return {
      rows: Array.isArray(rows) ? rows : [],
      rowCount: Array.isArray(rows) ? rows.length : 0,
    };
  }

  async countTexts(filters?: {
    author?: string;
    language?: string;
  }) {
    try {
      const count = await this.rpc('count_ancient_works', {
        p_author: filters?.author || null,
        p_language: filters?.language || null,
      });
      return typeof count === 'number' ? count : 0;
    } catch (error) {
      logger.error('Error counting texts', error);
      // Fallback to known total if RPC fails
      return 487;
    }
  }

  async getText(id: string) {
    const rows = await this.rpc('get_ancient_work', { p_work_id: id });
    return Array.isArray(rows) && rows.length > 0 ? rows[0] : null;
  }

  async getTextByKgWorkId(kgWorkId: string) {
    const rows = await this.rpc('get_ancient_work_by_kg_id', { p_kg_work_id: kgWorkId });
    return Array.isArray(rows) && rows.length > 0 ? rows[0] : null;
  }

  async getPassages(workId: string, filters?: {
    book?: string;
    chapter?: string;
    section?: string;
    offset?: number;
    limit?: number;
  }) {
    const rows = await this.rpc('list_passages', {
      p_work_id: workId,
      p_book: filters?.book || null,
      p_chapter: filters?.chapter || null,
      p_section: filters?.section || null,
      p_limit: filters?.limit || 100,
      p_offset: filters?.offset || 0,
    });

    return {
      rows: Array.isArray(rows) ? rows : [],
      rowCount: Array.isArray(rows) ? rows.length : 0,
    };
  }

  async getPassage(passageId: string) {
    const rows = await this.rpc('get_passage', { p_passage_id: passageId });
    return Array.isArray(rows) && rows.length > 0 ? rows[0] : null;
  }

  async searchPassages(query: string, limit: number = 20) {
    const rows = await this.rpc('search_passages', {
      p_search_query: query,
      p_limit: limit,
    });
    return Array.isArray(rows) ? rows : [];
  }

  // Search Queries
  async fulltextSearch(query: string, limit: number = 10) {
    try {
      // Strategy 1: Try optimized RPC function with full-text search + ranking
      try {
        const results = await this.rpc('search_passages', {
          query_text: query,
          max_results: limit,
        });

        if (results && Array.isArray(results) && results.length > 0) {
          logger.info(`Fulltext search via RPC returned ${results.length} results`);
          return results;
        }
      } catch (rpcError) {
        logger.warn('RPC search_passages failed, trying fallback', rpcError);
      }

      // Strategy 2: Try simple RPC function (ILIKE-based, slower but works)
      try {
        const results = await this.rpc('search_passages_simple', {
          query_text: query,
          max_results: limit,
        });

        if (results && Array.isArray(results) && results.length > 0) {
          logger.info(`Fulltext search via simple RPC returned ${results.length} results`);
          return results;
        }
      } catch (simpleError) {
        logger.warn('RPC search_passages_simple failed, trying direct query', simpleError);
      }

      // Strategy 3: Direct REST API query (works without RPC functions)
      const url = `${this.baseUrl}/passages?select=passage_id,work_id,canonical_ref,text_content&text_content=ilike.*${encodeURIComponent(query)}*&limit=${limit}`;

      const response = await fetch(url, {
        headers: {
          'apikey': this.supabaseKey,
          'Authorization': `Bearer ${this.supabaseKey}`,
        },
      });

      if (response.ok) {
        const results = await response.json();
        if (results && results.length > 0) {
          logger.info(`Fulltext search via REST API returned ${results.length} results`);
          return results;
        }
      }

      // All strategies failed or returned no results
      logger.warn(`All search strategies returned no results for query: "${query}"`);
      return [];
    } catch (error) {
      logger.error('Fulltext search error', error);
      // Return empty array instead of throwing to allow hybrid search to continue
      return [];
    }
  }

  /**
   * Search for a passage by citation reference
   * Parses citations like "Cicero, On Fate 41-43" or "Aristotle, NE 3.5"
   */
  async searchPassageByCitation(citation: string): Promise<{
    citation: string;
    original: string | null;
    originalLanguage: string | null;
    translation: string | null;
    text_id?: string;
    title?: string;
    author?: string;
    note?: string;
  }> {
    try {
      // Parse citation to extract author and work
      const citationLower = citation.toLowerCase();

      // Try to search passages by text content or canonical reference
      // First try full-text search on the citation
      const searchResults = await this.searchPassages(citation, 5);

      if (searchResults && searchResults.length > 0) {
        const best = searchResults[0];
        return {
          citation,
          original: best.text_content || best.content || null,
          originalLanguage: best.language || null,
          translation: best.translation || null,
          text_id: best.work_id || best.text_id,
          title: best.title || best.work_title,
          author: best.author,
        };
      }

      // Try searching with just author name if we can extract it
      const authorMatch = citation.match(/^([^,]+),/);
      if (authorMatch) {
        const authorName = authorMatch[1].trim();
        // Search for passages containing the author name
        const authorResults = await this.searchPassages(authorName, 10);

        if (authorResults && authorResults.length > 0) {
          // Find the best matching result
          for (const result of authorResults) {
            if (result.author?.toLowerCase().includes(authorName.toLowerCase()) ||
                result.title?.toLowerCase().includes(citationLower)) {
              return {
                citation,
                original: result.text_content || result.content || null,
                originalLanguage: result.language || null,
                translation: result.translation || null,
                text_id: result.work_id || result.text_id,
                title: result.title || result.work_title,
                author: result.author,
                note: 'Best match found by author search',
              };
            }
          }
        }
      }

      // No match found
      return {
        citation,
        original: null,
        originalLanguage: null,
        translation: null,
        note: 'No matching passage found in the database',
      };
    } catch (error) {
      logger.error('Error searching passage by citation', error);
      return {
        citation,
        original: null,
        originalLanguage: null,
        translation: null,
        note: 'Error searching for passage',
      };
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      // Use RPC path used by production endpoints.
      await this.rpc('get_kg_stats');
      return true;
    } catch {
      return false;
    }
  }

  // Lemma Autocomplete
  /**
   * Prefix-based autocomplete for lemmas
   * Supports Latin-alphabet queries for finding Greek lemmas via lemma_latin column
   */
  async autocompleteLemmasPrefix(
    query: string,
    language: string | null,
    limit: number,
    minCount: number,
    useLatinSearch: boolean
  ): Promise<any[]> {
    try {
      // Use RPC function for autocomplete (public schema wrapper)
      const results = await this.rpc('autocomplete_lemmas_prefix', {
        p_query: query,
        p_language: language,
        p_limit: limit,
        p_min_count: minCount,
        p_use_latin: useLatinSearch,
      });

      return Array.isArray(results) ? results : [];
    } catch (rpcError) {
      logger.warn('RPC autocomplete_lemmas_prefix failed, trying direct query', rpcError);

      // Fallback: direct REST API query on lemma_index
      // Note: This is less efficient but works without RPC functions
      try {
        const searchColumn = useLatinSearch && (language === 'grc' || !language)
          ? 'lemma_latin'
          : 'lemma';

        let url = `${this.baseUrl}/lemma_index?select=lemma,lemma_latin,language,primary_pos,total_count,passage_count,sample_forms&${searchColumn}=ilike.${encodeURIComponent(query)}*&total_count=gte.${minCount}&order=total_count.desc&limit=${limit}`;

        if (language) {
          url += `&language=eq.${language}`;
        }

        const response = await fetch(url, {
          headers: {
            'apikey': this.supabaseKey,
            'Authorization': `Bearer ${this.supabaseKey}`,
            'Accept-Profile': 'free_will',
          },
        });

        if (response.ok) {
          const results = await response.json();
          return results.map((r: any) => ({
            lemma: r.lemma,
            lemma_latin: r.lemma_latin,
            language: r.language,
            pos: r.primary_pos,
            count: r.total_count,
            passage_count: r.passage_count,
            forms: r.sample_forms || [],
          }));
        }
      } catch (fallbackError) {
        logger.error('Fallback autocomplete query failed', fallbackError);
      }

      return [];
    }
  }

  /**
   * Fuzzy autocomplete for lemmas using trigram similarity
   */
  async autocompleteLemmasFuzzy(
    query: string,
    language: string | null,
    limit: number,
    minCount: number,
    useLatinSearch: boolean
  ): Promise<any[]> {
    try {
      // Use RPC function for fuzzy autocomplete (public schema wrapper)
      const results = await this.rpc('autocomplete_lemmas_fuzzy', {
        p_query: query,
        p_language: language,
        p_limit: limit,
        p_min_count: minCount,
        p_use_latin: useLatinSearch,
      });

      return Array.isArray(results) ? results : [];
    } catch (rpcError) {
      logger.warn('RPC autocomplete_lemmas_fuzzy failed, falling back to prefix search', rpcError);

      // Fallback to prefix search (trigram not available via REST API)
      return this.autocompleteLemmasPrefix(query, language, limit, minCount, useLatinSearch);
    }
  }
}
