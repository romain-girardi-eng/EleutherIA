/**
 * Caching Service using Cloudflare KV
 */

import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('CacheService');

export class CacheService {
  private kv: KVNamespace;

  constructor(env: Env) {
    this.kv = env.TEXT_CACHE;
  }

  /**
   * Get cached value
   */
  async get<T = any>(key: string): Promise<T | null> {
    try {
      const value = await this.kv.get(key, 'json');
      if (value) {
        logger.info(`Cache HIT: ${key}`);
      }
      return value as T | null;
    } catch (error) {
      logger.error('Cache get error', error);
      return null;
    }
  }

  /**
   * Set cached value with TTL
   */
  async set(key: string, value: any, ttlSeconds: number = 3600): Promise<void> {
    try {
      await this.kv.put(key, JSON.stringify(value), {
        expirationTtl: ttlSeconds,
      });
      logger.info(`Cache SET: ${key} (TTL: ${ttlSeconds}s)`);
    } catch (error) {
      logger.error('Cache set error', error);
    }
  }

  /**
   * Delete cached value
   */
  async delete(key: string): Promise<void> {
    try {
      await this.kv.delete(key);
      logger.info(`Cache DELETE: ${key}`);
    } catch (error) {
      logger.error('Cache delete error', error);
    }
  }

  /**
   * Generate cache key
   */
  static generateKey(prefix: string, ...parts: (string | number)[]): string {
    return `${prefix}:${parts.join(':')}`;
  }

  /**
   * Cache a function call with automatic get/set
   */
  async cached<T>(
    key: string,
    fetchFn: () => Promise<T>,
    ttlSeconds: number = 3600
  ): Promise<T> {
    // Try to get from cache
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // Fetch fresh data
    const data = await fetchFn();

    // Store in cache (don't await)
    this.set(key, data, ttlSeconds).catch(err => {
      logger.error('Background cache set failed', err);
    });

    return data;
  }
}
