/**
 * Authentication and Rate Limiting Middleware
 */

import { Context, Next } from 'hono';
import { Env } from '../types';
import { getCurrentUser, checkRateLimit, getRateLimitInfo } from '../services/auth';
import { getLogger } from '../utils/logger';

const logger = getLogger('AuthMiddleware');

/**
 * Extract JWT token from Authorization header
 */
function extractToken(authHeader: string | undefined): string | null {
  if (!authHeader) return null;

  // Support both "Bearer <token>" and just "<token>"
  if (authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  return authHeader;
}

/**
 * Authentication middleware - Requires valid JWT token
 */
export async function authMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  try {
    const authHeader = c.req.header('Authorization');
    const token = extractToken(authHeader);

    if (!token) {
      return c.json({
        error: 'Authentication required',
        message: 'Missing or invalid Authorization header'
      }, 401);
    }

    const user = await getCurrentUser(token, c.env);

    if (!user) {
      return c.json({
        error: 'Invalid authentication',
        message: 'Token is invalid or expired'
      }, 401);
    }

    // Store user in context for downstream handlers
    c.set('user', user);

    await next();
  } catch (error) {
    logger.error('Authentication error', error);
    return c.json({
      error: 'Authentication failed',
      message: 'Unable to verify credentials'
    }, 500);
  }
}

/**
 * Optional authentication - Continues even if no token provided
 * But validates token if present
 */
export async function optionalAuthMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  try {
    const authHeader = c.req.header('Authorization');
    const token = extractToken(authHeader);

    if (token) {
      const user = await getCurrentUser(token, c.env);
      if (user) {
        c.set('user', user);
      }
    }

    await next();
  } catch (error) {
    logger.warn('Optional auth check failed, continuing anyway', error);
    await next();
  }
}

/**
 * Rate limiting middleware
 * Limits requests per user (if authenticated) or per IP (if anonymous)
 */
export function rateLimitMiddleware(
  limit: number = 30,
  windowMinutes: number = 15
) {
  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    try {
      // Get identifier: username if authenticated, otherwise IP
      const user = c.get('user');
      const clientIp = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For') || 'unknown';
      const identifier = user ? `user:${user.username}` : `ip:${clientIp}`;

      // Check rate limit
      const allowed = checkRateLimit(identifier, limit, windowMinutes);

      if (!allowed) {
        const info = getRateLimitInfo(identifier, limit, windowMinutes);
        const resetDate = new Date(info.reset_time * 1000);

        logger.warn(`Rate limit exceeded for ${identifier}`);

        return c.json({
          error: 'Rate limit exceeded',
          message: `Too many requests. Please try again after ${resetDate.toISOString()}`,
          retry_after: Math.ceil(info.reset_time - Date.now() / 1000)
        }, 429);
      }

      // Add rate limit info to response headers
      const info = getRateLimitInfo(identifier, limit, windowMinutes);
      c.header('X-RateLimit-Limit', info.limit.toString());
      c.header('X-RateLimit-Remaining', info.remaining.toString());
      c.header('X-RateLimit-Reset', Math.ceil(info.reset_time).toString());

      await next();
    } catch (error) {
      logger.error('Rate limiting error', error);
      // Continue on rate limit errors (fail open)
      await next();
    }
  };
}

/**
 * Input validation middleware for GraphRAG queries
 */
export async function validateGraphRAGInput(c: Context, next: Next) {
  try {
    // Get query from query params (GET) or body (POST)
    let query: string | undefined;

    if (c.req.method === 'GET') {
      query = c.req.query('query');
    } else {
      // POST request - read from body
      try {
        const body = await c.req.json();
        query = body.query;
      } catch {
        query = undefined;
      }
    }

    if (!query || typeof query !== 'string') {
      return c.json({
        error: 'Invalid input',
        message: 'Query parameter is required and must be a string'
      }, 400);
    }

    // Check query length
    if (query.length === 0) {
      return c.json({
        error: 'Invalid input',
        message: 'Query cannot be empty'
      }, 400);
    }

    if (query.length > 1000) {
      return c.json({
        error: 'Invalid input',
        message: 'Query is too long (maximum 1000 characters)'
      }, 400);
    }

    // Basic sanitization - remove potentially dangerous patterns
    const dangerous = /ignore previous|forget everything|disregard|system prompt|<script>/gi;
    if (dangerous.test(query)) {
      logger.warn('Potentially malicious query detected', { query: query.substring(0, 100) });
      return c.json({
        error: 'Invalid input',
        message: 'Query contains prohibited patterns'
      }, 400);
    }

    await next();
  } catch (error) {
    logger.error('Input validation error', error);
    return c.json({
      error: 'Validation failed',
      message: 'Unable to validate input'
    }, 500);
  }
}
