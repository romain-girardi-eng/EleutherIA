/**
 * Authentication Routes
 * Handles JWT authentication and Semativerse permission checking
 */

import { Hono } from 'hono';
import { Env } from '../types';
import { getLogger } from '../utils/logger';
import {
  authenticateUser,
  createAccessToken,
  getCurrentUser,
  getRateLimitInfo,
  type Token,
  type User
} from '../services/auth';

const logger = getLogger('AuthRoutes');

export const authRoutes = new Hono<{ Bindings: Env }>();

interface LoginRequest {
  username: string;
  password: string;
}

interface SemativersePermissionRequest {
  access_key: string;
}

/**
 * Login endpoint - authenticate user and return JWT token
 */
authRoutes.post('/login', async (c) => {
  try {
    const body = await c.req.json<LoginRequest>();

    if (!body.username || !body.password) {
      return c.json({
        error: 'Username and password are required'
      }, 400);
    }

    const user = await authenticateUser(body.username, body.password);

    if (!user) {
      return c.json({
        error: 'Incorrect username or password'
      }, 401);
    }

    const accessToken = await createAccessToken({ sub: user.username }, c.env);

    const token: Token = {
      access_token: accessToken,
      token_type: 'bearer',
      expires_in: 60 * 24 * 7 // 7 days in minutes
    };

    logger.info('User logged in successfully', { username: user.username });

    return c.json(token);
  } catch (error) {
    logger.error('Error during login', error);
    return c.json({
      error: 'Internal server error'
    }, 500);
  }
});

/**
 * Get current user information
 */
authRoutes.get('/me', async (c) => {
  try {
    const authHeader = c.req.header('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return c.json({
        error: 'No authorization token provided'
      }, 401);
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    const user = await getCurrentUser(token, c.env);

    if (!user) {
      return c.json({
        error: 'Invalid or expired token'
      }, 401);
    }

    return c.json(user);
  } catch (error) {
    logger.error('Error getting current user', error);
    return c.json({
      error: 'Internal server error'
    }, 500);
  }
});

/**
 * Get rate limit status for current user
 */
authRoutes.get('/rate-limit', async (c) => {
  try {
    const authHeader = c.req.header('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return c.json({
        error: 'No authorization token provided'
      }, 401);
    }

    const token = authHeader.substring(7);
    const user = await getCurrentUser(token, c.env);

    if (!user) {
      return c.json({
        error: 'Invalid or expired token'
      }, 401);
    }

    // Get client IP from Cloudflare header or fallback
    const clientIp = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For') || 'unknown';
    const identifier = `${user.username}:${clientIp}`;

    const rateInfo = getRateLimitInfo(identifier);

    return c.json({
      user: user.username,
      ip: clientIp,
      rate_limit: rateInfo
    });
  } catch (error) {
    logger.error('Error getting rate limit', error);
    return c.json({
      error: 'Internal server error'
    }, 500);
  }
});

/**
 * Check if user has permission to access Semativerse visualization
 */
authRoutes.post('/semativerse/check', async (c) => {
  try {
    const body = await c.req.json<SemativersePermissionRequest>();

    if (!body.access_key) {
      return c.json({
        error: 'Access key is required'
      }, 400);
    }

    const semativerseKey = c.env.SEMATIVERSE_ACCESS_KEY;
    if (!semativerseKey) {
      logger.error('SEMATIVERSE_ACCESS_KEY not configured');
      return c.json({ error: 'Service not configured' }, 503);
    }
    const hasPermission = body.access_key === semativerseKey;

    return c.json({
      has_permission: hasPermission,
      message: hasPermission ? 'Access granted' : 'Access denied - invalid key'
    });
  } catch (error) {
    logger.error('Error checking Semativerse permission', error);
    return c.json({
      error: 'Internal server error'
    }, 500);
  }
});

/**
 * Get Semativerse service status
 */
authRoutes.get('/semativerse/status', async (c) => {
  return c.json({
    status: 'available',
    requires_permission: true,
    features: [
      '3D/2D visualization',
      'WebGL2 + Three.js + UnrealBloomPass',
      '60 FPS with 5,000+ nodes',
      'Category suns, domain colors',
      'Recording and screenshots',
      'Semantic search integration'
    ]
  });
});
