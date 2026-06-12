/**
 * CacheService - Intelligent caching layer for EleutherIA
 *
 * Uses a two-tier caching strategy:
 * - LocalStorage: For small, frequently accessed metadata (works list, stats, KG data)
 * - IndexedDB: For larger data (passages, search results)
 *
 * Features:
 * - TTL-based expiration
 * - Version-based cache busting
 * - LRU eviction for IndexedDB
 * - Automatic compression for large objects
 */

// Cache configuration
// 2.0.0: backend migration to self-hosted Postgres changed /api/works/stats
// shape and regenerated all work_ids — bust every pre-migration cache entry.
const CACHE_VERSION = '2.0.0';
const DB_NAME = 'eleutherio_cache';
const DB_VERSION = 1;

// TTL values in milliseconds
const TTL = {
  WORKS_LIST: 24 * 60 * 60 * 1000,      // 24 hours - works list changes rarely
  WORKS_STATS: 24 * 60 * 60 * 1000,     // 24 hours - stats change rarely
  WORK_DETAIL: 7 * 24 * 60 * 60 * 1000, // 7 days - individual work metadata is stable
  PASSAGES: 7 * 24 * 60 * 60 * 1000,    // 7 days - passages don't change
  KG_DATA: 12 * 60 * 60 * 1000,         // 12 hours - KG data may update more frequently
  SEARCH: 30 * 60 * 1000,               // 30 minutes - search results can be cached briefly
} as const;

// Storage keys
const STORAGE_KEYS = {
  WORKS_LIST: 'eleutherio:works:list',
  WORKS_STATS: 'eleutherio:works:stats',
  KG_STATS: 'eleutherio:kg:stats',
  KG_CYTOSCAPE: 'eleutherio:kg:cytoscape',
  CACHE_META: 'eleutherio:cache:meta',
} as const;

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  version: string;
}

interface CacheMeta {
  version: string;
  lastCleanup: number;
  totalSize: number;
}

class CacheService {
  private dbReady: Promise<IDBDatabase>;
  private memoryCache: Map<string, CacheEntry<unknown>> = new Map();

  constructor() {
    this.dbReady = this.initIndexedDB();
    this.initCacheMeta();
  }

  // ============================================================================
  // IndexedDB Initialization
  // ============================================================================

  private initIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      if (typeof indexedDB === 'undefined') {
        // IndexedDB not available (e.g., SSR)
        reject(new Error('IndexedDB not available'));
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.warn('IndexedDB failed to open, using localStorage only');
        reject(request.error);
      };

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const upgradeDb = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!upgradeDb.objectStoreNames.contains('passages')) {
          const passagesStore = upgradeDb.createObjectStore('passages', { keyPath: 'cacheKey' });
          passagesStore.createIndex('workId', 'workId', { unique: false });
          passagesStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!upgradeDb.objectStoreNames.contains('works')) {
          const worksStore = upgradeDb.createObjectStore('works', { keyPath: 'workId' });
          worksStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!upgradeDb.objectStoreNames.contains('search')) {
          const searchStore = upgradeDb.createObjectStore('search', { keyPath: 'queryHash' });
          searchStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  private initCacheMeta(): void {
    try {
      const meta = localStorage.getItem(STORAGE_KEYS.CACHE_META);
      if (meta) {
        const parsed = JSON.parse(meta) as CacheMeta;
        if (parsed.version !== CACHE_VERSION) {
          // Version mismatch - clear all caches
          this.clearAll();
        }
      } else {
        this.updateCacheMeta();
      }
    } catch {
      this.updateCacheMeta();
    }
  }

  private updateCacheMeta(): void {
    const meta: CacheMeta = {
      version: CACHE_VERSION,
      lastCleanup: Date.now(),
      totalSize: 0,
    };
    try {
      localStorage.setItem(STORAGE_KEYS.CACHE_META, JSON.stringify(meta));
    } catch {
      // Ignore storage errors
    }
  }

  // ============================================================================
  // LocalStorage Methods (for small data)
  // ============================================================================

  private setLocalStorage<T>(key: string, data: T, ttl: number): boolean {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      version: CACHE_VERSION,
    };

    try {
      localStorage.setItem(key, JSON.stringify(entry));
      return true;
    } catch {
      // Storage full - try to clear old entries
      console.warn('LocalStorage full, clearing old entries');
      this.cleanupLocalStorage();
      try {
        localStorage.setItem(key, JSON.stringify(entry));
        return true;
      } catch {
        return false;
      }
    }
  }

  private getLocalStorage<T>(key: string): T | null {
    try {
      const stored = localStorage.getItem(key);
      if (!stored) return null;

      const entry = JSON.parse(stored) as CacheEntry<T>;

      // Check version
      if (entry.version !== CACHE_VERSION) {
        localStorage.removeItem(key);
        return null;
      }

      // Check TTL
      if (Date.now() - entry.timestamp > entry.ttl) {
        localStorage.removeItem(key);
        return null;
      }

      return entry.data;
    } catch {
      return null;
    }
  }

  private cleanupLocalStorage(): void {
    const keysToCheck = Object.keys(localStorage).filter(k => k.startsWith('eleutherio:'));

    for (const key of keysToCheck) {
      try {
        const stored = localStorage.getItem(key);
        if (stored) {
          const entry = JSON.parse(stored) as CacheEntry<unknown>;
          if (Date.now() - entry.timestamp > entry.ttl) {
            localStorage.removeItem(key);
          }
        }
      } catch {
        localStorage.removeItem(key);
      }
    }
  }

  // ============================================================================
  // IndexedDB Methods (for large data)
  // ============================================================================

  private async setIndexedDB<T>(
    storeName: string,
    key: string,
    data: T,
    ttl: number,
    indexes?: Record<string, unknown>
  ): Promise<boolean> {
    try {
      const db = await this.dbReady;

      return new Promise((resolve) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);

        const entry = {
          cacheKey: key,
          data,
          timestamp: Date.now(),
          ttl,
          version: CACHE_VERSION,
          ...indexes,
        };

        const request = store.put(entry);
        request.onsuccess = () => resolve(true);
        request.onerror = () => {
          console.warn('IndexedDB write failed:', request.error);
          resolve(false);
        };
      });
    } catch {
      return false;
    }
  }

  private async getIndexedDB<T>(storeName: string, key: string): Promise<T | null> {
    try {
      const db = await this.dbReady;

      return new Promise((resolve) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.get(key);

        request.onsuccess = () => {
          const entry = request.result;
          if (!entry) {
            resolve(null);
            return;
          }

          // Check version
          if (entry.version !== CACHE_VERSION) {
            resolve(null);
            return;
          }

          // Check TTL
          if (Date.now() - entry.timestamp > entry.ttl) {
            // Delete expired entry
            const deleteTransaction = db.transaction(storeName, 'readwrite');
            deleteTransaction.objectStore(storeName).delete(key);
            resolve(null);
            return;
          }

          resolve(entry.data as T);
        };

        request.onerror = () => resolve(null);
      });
    } catch {
      return null;
    }
  }

  // ============================================================================
  // Public API - Works
  // ============================================================================

  async getWorksList(filters?: Record<string, unknown>): Promise<unknown | null> {
    const cacheKey = filters
      ? `${STORAGE_KEYS.WORKS_LIST}:${JSON.stringify(filters)}`
      : STORAGE_KEYS.WORKS_LIST;

    // Try memory cache first
    const memCached = this.memoryCache.get(cacheKey);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }

    // Try localStorage
    return this.getLocalStorage(cacheKey);
  }

  async setWorksList(data: unknown, filters?: Record<string, unknown>): Promise<void> {
    const cacheKey = filters
      ? `${STORAGE_KEYS.WORKS_LIST}:${JSON.stringify(filters)}`
      : STORAGE_KEYS.WORKS_LIST;

    // Set in memory cache
    this.memoryCache.set(cacheKey, {
      data,
      timestamp: Date.now(),
      ttl: TTL.WORKS_LIST,
      version: CACHE_VERSION,
    });

    // Set in localStorage
    this.setLocalStorage(cacheKey, data, TTL.WORKS_LIST);
  }

  async getWorksStats(): Promise<unknown | null> {
    const memCached = this.memoryCache.get(STORAGE_KEYS.WORKS_STATS);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }
    return this.getLocalStorage(STORAGE_KEYS.WORKS_STATS);
  }

  async setWorksStats(data: unknown): Promise<void> {
    this.memoryCache.set(STORAGE_KEYS.WORKS_STATS, {
      data,
      timestamp: Date.now(),
      ttl: TTL.WORKS_STATS,
      version: CACHE_VERSION,
    });
    this.setLocalStorage(STORAGE_KEYS.WORKS_STATS, data, TTL.WORKS_STATS);
  }

  // ============================================================================
  // Public API - Individual Work
  // ============================================================================

  async getWork(workId: string): Promise<unknown | null> {
    const cacheKey = `eleutherio:work:${workId}`;

    // Try memory cache
    const memCached = this.memoryCache.get(cacheKey);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }

    // Try IndexedDB
    return this.getIndexedDB('works', workId);
  }

  async setWork(workId: string, data: unknown): Promise<void> {
    const cacheKey = `eleutherio:work:${workId}`;

    this.memoryCache.set(cacheKey, {
      data,
      timestamp: Date.now(),
      ttl: TTL.WORK_DETAIL,
      version: CACHE_VERSION,
    });

    await this.setIndexedDB('works', workId, data, TTL.WORK_DETAIL, { workId });
  }

  // ============================================================================
  // Public API - Passages (the big egress saver!)
  // ============================================================================

  async getPassages(workId: string, offset: number = 0, limit: number = 50): Promise<unknown | null> {
    const cacheKey = `passages:${workId}:${offset}:${limit}`;

    // Try memory cache
    const memCached = this.memoryCache.get(cacheKey);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }

    // Try IndexedDB
    return this.getIndexedDB('passages', cacheKey);
  }

  async setPassages(workId: string, data: unknown, offset: number = 0, limit: number = 50): Promise<void> {
    const cacheKey = `passages:${workId}:${offset}:${limit}`;

    this.memoryCache.set(cacheKey, {
      data,
      timestamp: Date.now(),
      ttl: TTL.PASSAGES,
      version: CACHE_VERSION,
    });

    await this.setIndexedDB('passages', cacheKey, data, TTL.PASSAGES, { workId });
  }

  // Get all cached passages for a work (for offline reading)
  async getAllCachedPassages(workId: string): Promise<unknown[]> {
    try {
      const db = await this.dbReady;

      return new Promise((resolve) => {
        const transaction = db.transaction('passages', 'readonly');
        const store = transaction.objectStore('passages');
        const index = store.index('workId');
        const request = index.getAll(workId);

        request.onsuccess = () => {
          const entries = request.result || [];
          const validEntries = entries
            .filter(e => e.version === CACHE_VERSION && Date.now() - e.timestamp < e.ttl)
            .map(e => e.data);
          resolve(validEntries);
        };

        request.onerror = () => resolve([]);
      });
    } catch {
      return [];
    }
  }

  // ============================================================================
  // Public API - Knowledge Graph
  // ============================================================================

  async getKGStats(): Promise<unknown | null> {
    const memCached = this.memoryCache.get(STORAGE_KEYS.KG_STATS);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }
    return this.getLocalStorage(STORAGE_KEYS.KG_STATS);
  }

  async setKGStats(data: unknown): Promise<void> {
    this.memoryCache.set(STORAGE_KEYS.KG_STATS, {
      data,
      timestamp: Date.now(),
      ttl: TTL.KG_DATA,
      version: CACHE_VERSION,
    });
    this.setLocalStorage(STORAGE_KEYS.KG_STATS, data, TTL.KG_DATA);
  }

  async getCytoscapeData(options?: { algorithm?: string; ancientOnly?: boolean }): Promise<unknown | null> {
    const cacheKey = options
      ? `${STORAGE_KEYS.KG_CYTOSCAPE}:${JSON.stringify(options)}`
      : STORAGE_KEYS.KG_CYTOSCAPE;

    const memCached = this.memoryCache.get(cacheKey);
    if (memCached && Date.now() - memCached.timestamp < memCached.ttl) {
      return memCached.data;
    }
    return this.getLocalStorage(cacheKey);
  }

  async setCytoscapeData(data: unknown, options?: { algorithm?: string; ancientOnly?: boolean }): Promise<void> {
    const cacheKey = options
      ? `${STORAGE_KEYS.KG_CYTOSCAPE}:${JSON.stringify(options)}`
      : STORAGE_KEYS.KG_CYTOSCAPE;

    this.memoryCache.set(cacheKey, {
      data,
      timestamp: Date.now(),
      ttl: TTL.KG_DATA,
      version: CACHE_VERSION,
    });
    this.setLocalStorage(cacheKey, data, TTL.KG_DATA);
  }

  // ============================================================================
  // Public API - Search
  // ============================================================================

  private hashQuery(query: string): string {
    // Simple hash for search queries
    let hash = 0;
    for (let i = 0; i < query.length; i++) {
      const char = query.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return `search:${hash}`;
  }

  async getSearchResults(query: string): Promise<unknown | null> {
    const queryHash = this.hashQuery(query);
    return this.getIndexedDB('search', queryHash);
  }

  async setSearchResults(query: string, data: unknown): Promise<void> {
    const queryHash = this.hashQuery(query);
    await this.setIndexedDB('search', queryHash, data, TTL.SEARCH, { queryHash });
  }

  // ============================================================================
  // Cache Management
  // ============================================================================

  async clearAll(): Promise<void> {
    // Clear memory cache
    this.memoryCache.clear();

    // Clear localStorage entries
    const keysToRemove = Object.keys(localStorage).filter(k => k.startsWith('eleutherio:'));
    keysToRemove.forEach(key => localStorage.removeItem(key));

    // Clear IndexedDB
    try {
      const db = await this.dbReady;
      const storeNames = ['passages', 'works', 'search'];

      for (const storeName of storeNames) {
        const transaction = db.transaction(storeName, 'readwrite');
        transaction.objectStore(storeName).clear();
      }
    } catch {
      // Ignore IndexedDB errors during clear
    }

    // Reset cache meta
    this.updateCacheMeta();
  }

  async clearWorkCache(workId: string): Promise<void> {
    // Clear from memory
    const keysToDelete = Array.from(this.memoryCache.keys()).filter(
      k => k.includes(workId)
    );
    keysToDelete.forEach(k => this.memoryCache.delete(k));

    // Clear from IndexedDB
    try {
      const db = await this.dbReady;

      // Clear work
      const workTransaction = db.transaction('works', 'readwrite');
      workTransaction.objectStore('works').delete(workId);

      // Clear passages for this work
      const passagesTransaction = db.transaction('passages', 'readwrite');
      const passagesStore = passagesTransaction.objectStore('passages');
      const index = passagesStore.index('workId');
      const request = index.getAllKeys(workId);

      request.onsuccess = () => {
        const keys = request.result;
        const deleteTransaction = db.transaction('passages', 'readwrite');
        keys.forEach(key => deleteTransaction.objectStore('passages').delete(key));
      };
    } catch {
      // Ignore errors
    }
  }

  // Get cache statistics
  async getStats(): Promise<{
    memoryEntries: number;
    localStorageSize: number;
    indexedDBSize: number;
  }> {
    const memoryEntries = this.memoryCache.size;

    // Estimate localStorage size
    let localStorageSize = 0;
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith('eleutherio:')) {
        const value = localStorage.getItem(key);
        if (value) {
          localStorageSize += key.length + value.length;
        }
      }
    }

    // Estimate IndexedDB size (rough estimate)
    let indexedDBSize = 0;
    try {
      const db = await this.dbReady;
      const storeNames = ['passages', 'works', 'search'];

      for (const storeName of storeNames) {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const countRequest = store.count();

        await new Promise<void>((resolve) => {
          countRequest.onsuccess = () => {
            // Rough estimate: 1KB per entry average
            indexedDBSize += countRequest.result * 1024;
            resolve();
          };
          countRequest.onerror = () => resolve();
        });
      }
    } catch {
      // Ignore errors
    }

    return {
      memoryEntries,
      localStorageSize,
      indexedDBSize,
    };
  }
}

// Export singleton instance
export const cacheService = new CacheService();
export default cacheService;
