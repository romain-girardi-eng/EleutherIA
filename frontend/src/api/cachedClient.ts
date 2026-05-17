/**
 * CachedApiClient - API client wrapper with intelligent caching
 *
 * This wraps the original apiClient and adds caching for expensive operations.
 * It dramatically reduces Supabase egress by:
 * 1. Caching works list and stats (doesn't change often)
 * 2. Caching individual work metadata (stable data)
 * 3. Caching passages in IndexedDB (the BIG egress saver - 13K+ passages)
 * 4. Caching KG data (moderate frequency updates)
 */

import { apiClient } from './client';
import { cacheService } from '../services/CacheService';
import type {
  CytoscapeData,
  HybridSearchResponse,
  SearchQuery,
} from '../types';

// Types for API responses
interface WorksListResponse {
  works: unknown[];
  total: number;
  offset: number;
  limit: number;
}

interface PassagesResponse {
  passages: unknown[];
  total: number;
  work_id: string;
}

interface WorksStatsResponse {
  total_works: number;
  total_passages: number;
  total_citations: number;
  featured_works: unknown[];
  top_authors: unknown[];
}

class CachedApiClient {
  // ============================================================================
  // Works API (heavily cached)
  // ============================================================================

  /**
   * List works with caching
   * Cache: 24 hours (works list rarely changes)
   */
  async listWorks(filters?: {
    author?: string;
    language?: string;
    period?: string;
    source?: string;
    search?: string;
    offset?: number;
    limit?: number;
  }): Promise<WorksListResponse> {
    // Try cache first
    const cached = await cacheService.getWorksList(filters);
    if (cached) {
      console.debug('[Cache] HIT: works list');
      return cached as WorksListResponse;
    }

    console.debug('[Cache] MISS: works list, fetching from API');
    const response = await apiClient.listWorks(filters);

    // Cache the response
    await cacheService.setWorksList(response, filters);

    return response;
  }

  /**
   * Get works stats with caching
   * Cache: 24 hours
   */
  async getWorksStats(): Promise<WorksStatsResponse> {
    const cached = await cacheService.getWorksStats();
    if (cached) {
      console.debug('[Cache] HIT: works stats');
      return cached as WorksStatsResponse;
    }

    console.debug('[Cache] MISS: works stats, fetching from API');
    const response = await apiClient.getWorksStats();

    await cacheService.setWorksStats(response);

    return response;
  }

  /**
   * Get individual work with caching
   * Cache: 7 days (work metadata is very stable)
   */
  async getWork(workId: string): Promise<unknown> {
    const cached = await cacheService.getWork(workId);
    if (cached) {
      console.debug(`[Cache] HIT: work ${workId.slice(0, 8)}`);
      return cached;
    }

    console.debug(`[Cache] MISS: work ${workId.slice(0, 8)}, fetching from API`);
    const response = await apiClient.getWork(workId);

    await cacheService.setWork(workId, response);

    return response;
  }

  // ============================================================================
  // Passages API (the BIG egress saver!)
  // ============================================================================

  /**
   * Get work passages with caching and lazy loading support
   * Cache: 7 days (passages are immutable)
   *
   * @param workId - Work ID
   * @param options - Pagination options
   * @param options.offset - Starting position (default: 0)
   * @param options.limit - Number of passages to fetch (default: 50)
   * @param options.forceRefresh - Bypass cache and fetch fresh data
   */
  async getWorkPassages(
    workId: string,
    options?: {
      offset?: number;
      limit?: number;
      forceRefresh?: boolean;
      includeTranslations?: boolean;
    }
  ): Promise<PassagesResponse> {
    const offset = options?.offset ?? 0;
    const limit = options?.limit ?? 50;

    // Check cache unless force refresh
    if (!options?.forceRefresh) {
      const cached = await cacheService.getPassages(workId, offset, limit);
      if (cached) {
        console.debug(`[Cache] HIT: passages ${workId.slice(0, 8)} [${offset}-${offset + limit}]`);
        return cached as PassagesResponse;
      }
    }

    console.debug(`[Cache] MISS: passages ${workId.slice(0, 8)} [${offset}-${offset + limit}], fetching from API`);
    const response = await apiClient.getWorkPassages(workId, {
      offset,
      limit,
      ...(options?.includeTranslations ? { include_translations: true } : {}),
    });

    // Cache the response
    await cacheService.setPassages(workId, response, offset, limit);

    return response;
  }

  /**
   * Prefetch passages for a work (background loading)
   * Useful for preloading next pages while user reads current page
   */
  async prefetchPassages(workId: string, offset: number, limit: number = 50): Promise<void> {
    // Check if already cached
    const cached = await cacheService.getPassages(workId, offset, limit);
    if (cached) {
      return; // Already cached, no need to fetch
    }

    // Fetch in background (low priority)
    try {
      const response = await apiClient.getWorkPassages(workId, { offset, limit });
      await cacheService.setPassages(workId, response, offset, limit);
      console.debug(`[Prefetch] Cached passages ${workId.slice(0, 8)} [${offset}-${offset + limit}]`);
    } catch (error) {
      console.warn('[Prefetch] Failed:', error);
    }
  }

  // ============================================================================
  // Knowledge Graph API (cached)
  // ============================================================================

  /**
   * Get KG stats with caching
   * Cache: 12 hours
   */
  async getKGStats(): Promise<unknown> {
    const cached = await cacheService.getKGStats();
    if (cached) {
      console.debug('[Cache] HIT: KG stats');
      return cached;
    }

    console.debug('[Cache] MISS: KG stats, fetching from API');
    const response = await apiClient.getKGStats();

    await cacheService.setKGStats(response);

    return response;
  }

  /**
   * Get Cytoscape visualization data with caching
   * Cache: 12 hours
   */
  async getCytoscapeData(options?: {
    algorithm?: string;
    ancientOnly?: boolean;
  }): Promise<CytoscapeData> {
    const cached = await cacheService.getCytoscapeData(options);
    if (cached) {
      console.debug('[Cache] HIT: Cytoscape data');
      return cached as CytoscapeData;
    }

    console.debug('[Cache] MISS: Cytoscape data, fetching from API');
    const response = await apiClient.getCytoscapeData(options);

    await cacheService.setCytoscapeData(response, options);

    return response;
  }

  // ============================================================================
  // Search API (short-term caching)
  // ============================================================================

  /**
   * Hybrid search with short-term caching
   * Cache: 30 minutes (search results may change with DB updates)
   */
  async hybridSearch(query: SearchQuery): Promise<HybridSearchResponse> {
    const queryKey = JSON.stringify(query);

    const cached = await cacheService.getSearchResults(queryKey);
    if (cached) {
      console.debug('[Cache] HIT: search results');
      return cached as HybridSearchResponse;
    }

    console.debug('[Cache] MISS: search results, fetching from API');
    const response = await apiClient.hybridSearch(query);

    await cacheService.setSearchResults(queryKey, response);

    return response;
  }

  // ============================================================================
  // Pass-through methods (no caching - real-time or write operations)
  // ============================================================================

  // These methods don't benefit from caching or need real-time data

  // Authentication
  login = apiClient.login.bind(apiClient);
  getCurrentUser = apiClient.getCurrentUser.bind(apiClient);
  getRateLimitStatus = apiClient.getRateLimitStatus.bind(apiClient);

  // GraphRAG (real-time, AI-generated)
  graphragQuery = apiClient.graphragQuery.bind(apiClient);
  graphragQueryStream = apiClient.graphragQueryStream.bind(apiClient);
  graphragQueryAdvanced = apiClient.graphragQueryAdvanced.bind(apiClient);
  graphragCompare = apiClient.graphragCompare.bind(apiClient);
  graphragStatus = apiClient.graphragStatus.bind(apiClient);
  getNodeRelationships = apiClient.getNodeRelationships.bind(apiClient);
  getPhilosophicalDebates = apiClient.getPhilosophicalDebates.bind(apiClient);
  getInfluenceChains = apiClient.getInfluenceChains.bind(apiClient);
  getGraphRAGStats = apiClient.getGraphRAGStats.bind(apiClient);

  // KG nodes/edges (could cache, but changes more frequently)
  getNodes = apiClient.getNodes.bind(apiClient);
  getEdges = apiClient.getEdges.bind(apiClient);
  getNode = apiClient.getNode.bind(apiClient);
  getNodeConnections = apiClient.getNodeConnections.bind(apiClient);
  getTimelineOverview = apiClient.getTimelineOverview.bind(apiClient);
  getInfluenceMatrix = apiClient.getInfluenceMatrix.bind(apiClient);
  computeGraphPath = apiClient.computeGraphPath.bind(apiClient);

  // Works extras
  searchWorks = apiClient.searchWorks.bind(apiClient);
  getWorkKGNodes = apiClient.getWorkKGNodes.bind(apiClient);

  // Other search
  fulltextSearch = apiClient.fulltextSearch.bind(apiClient);
  lemmaticSearch = apiClient.lemmaticSearch.bind(apiClient);
  searchKG = apiClient.searchKG.bind(apiClient);

  // Generic methods
  get = apiClient.get.bind(apiClient);
  post = apiClient.post.bind(apiClient);
  put = apiClient.put.bind(apiClient);
  delete = apiClient.delete.bind(apiClient);

  // Health check
  healthCheck = apiClient.healthCheck.bind(apiClient);

  // Semativerse
  checkSemativersePermission = apiClient.checkSemativersePermission.bind(apiClient);
  getSemativerseStatus = apiClient.getSemativerseStatus.bind(apiClient);

  // ============================================================================
  // Cache Management
  // ============================================================================

  /**
   * Clear all caches
   */
  async clearCache(): Promise<void> {
    await cacheService.clearAll();
    console.debug('[Cache] All caches cleared');
  }

  /**
   * Clear cache for a specific work
   */
  async clearWorkCache(workId: string): Promise<void> {
    await cacheService.clearWorkCache(workId);
    console.debug(`[Cache] Cleared cache for work ${workId.slice(0, 8)}`);
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<{
    memoryEntries: number;
    localStorageSize: number;
    indexedDBSize: number;
  }> {
    return cacheService.getStats();
  }
}

// Export singleton instance
export const cachedApiClient = new CachedApiClient();
export default cachedApiClient;
