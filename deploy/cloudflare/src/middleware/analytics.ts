/**
 * Analytics Middleware using Cloudflare Analytics Engine
 */

import { Context, Next } from 'hono';
import { Env } from '../types';
import { getLogger } from '../utils/logger';

const logger = getLogger('Analytics');

export const analyticsMiddleware = async (
  c: Context<{ Bindings: Env }>,
  next: Next
) => {
  const startTime = Date.now();
  const path = c.req.path;
  const method = c.req.method;

  // Execute the request
  await next();

  // Calculate response time
  const responseTime = Date.now() - startTime;
  const status = c.res.status;

  // Log analytics data
  try {
    if (c.env.API_ANALYTICS) {
      await c.env.API_ANALYTICS.writeDataPoint({
        blobs: [
          path,                    // Request path
          method,                  // HTTP method
          status.toString(),       // Status code
          c.req.header('User-Agent') || 'unknown',  // User agent
        ],
        doubles: [responseTime],   // Response time in ms
        indexes: [path],           // Index by path for faster queries
      });

      logger.info('Analytics logged', {
        path,
        method,
        status,
        responseTime,
      });
    }
  } catch (error) {
    // Don't fail the request if analytics fails
    logger.error('Analytics write failed', error);
  }
};
