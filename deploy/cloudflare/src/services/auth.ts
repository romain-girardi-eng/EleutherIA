/**
 * Authentication Service
 * Handles JWT token creation, verification, and user management
 */

import { SignJWT, jwtVerify } from 'jose';
import { Env } from '../types';

// Algorithm for JWT
const ALGORITHM = 'HS256';
const ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7; // 7 days

export interface User {
  username: string;
  email: string;
  role: string;
}

export interface UserInDB extends User {
  hashedPassword: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenData {
  username: string;
}

export interface RateLimitInfo {
  remaining: number;
  reset_time: number;
  limit: number;
}

/**
 * Simple hash function using Web Crypto API (SHA-256)
 */
async function simpleHash(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}

/**
 * Simple user store (in production, use a database)
 */
const USERS_DB: Record<string, UserInDB> = {
  admin: {
    username: 'admin',
    email: 'admin@example.com',
    hashedPassword: '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', // admin123
    role: 'admin'
  },
  researcher: {
    username: 'researcher',
    email: 'researcher@example.com',
    hashedPassword: '381fa94c49882e0a06845ff8aa9df705412448592bc9a4e637dc3dcd0e543968', // research123
    role: 'researcher'
  }
};

/**
 * Verify a password against its hash
 */
export async function verifyPassword(plainPassword: string, hashedPassword: string): Promise<boolean> {
  const hash = await simpleHash(plainPassword);
  return hash === hashedPassword;
}

/**
 * Get user from database
 */
export function getUser(username: string): UserInDB | null {
  return USERS_DB[username] || null;
}

/**
 * Authenticate a user
 */
export async function authenticateUser(username: string, password: string): Promise<UserInDB | null> {
  const user = getUser(username);
  if (!user) {
    return null;
  }
  if (!await verifyPassword(password, user.hashedPassword)) {
    return null;
  }
  return user;
}

/**
 * Create a JWT access token
 */
export async function createAccessToken(data: { sub: string }, env: Env): Promise<string> {
  const secret = new TextEncoder().encode(env.JWT_SECRET_KEY || 'your-secret-key-change-in-production');

  const jwt = await new SignJWT({ sub: data.sub })
    .setProtectedHeader({ alg: ALGORITHM })
    .setIssuedAt()
    .setExpirationTime(`${ACCESS_TOKEN_EXPIRE_MINUTES}m`)
    .sign(secret);

  return jwt;
}

/**
 * Verify and decode a JWT token
 */
export async function verifyToken(token: string, env: Env): Promise<TokenData | null> {
  try {
    const secret = new TextEncoder().encode(env.JWT_SECRET_KEY || 'your-secret-key-change-in-production');
    const { payload } = await jwtVerify(token, secret);

    const username = payload.sub;
    if (!username) {
      return null;
    }

    return { username };
  } catch (error) {
    return null;
  }
}

/**
 * Get current user from token
 */
export async function getCurrentUser(token: string, env: Env): Promise<User | null> {
  const tokenData = await verifyToken(token, env);
  if (!tokenData) {
    return null;
  }

  const user = getUser(tokenData.username);
  if (!user) {
    return null;
  }

  return {
    username: user.username,
    email: user.email,
    role: user.role
  };
}

/**
 * Rate limiting storage
 * In production, use Cloudflare KV or Durable Objects
 */
interface RateLimitStorage {
  requests: number[];
  lastCleanup: number;
}

const rateLimitStorage = new Map<string, RateLimitStorage>();

/**
 * Check if user/IP has exceeded rate limit
 */
export function checkRateLimit(
  identifier: string,
  limit: number = 30,
  windowMinutes: number = 15
): boolean {
  const now = Date.now() / 1000; // Unix timestamp in seconds
  const windowSeconds = windowMinutes * 60;

  if (!rateLimitStorage.has(identifier)) {
    rateLimitStorage.set(identifier, {
      requests: [],
      lastCleanup: now
    });
  }

  const userData = rateLimitStorage.get(identifier)!;
  const requests = userData.requests;

  // Clean old requests outside the window
  const cutoffTime = now - windowSeconds;
  userData.requests = requests.filter(reqTime => reqTime > cutoffTime);

  // Check if limit exceeded
  if (userData.requests.length >= limit) {
    return false;
  }

  // Add current request
  userData.requests.push(now);
  userData.lastCleanup = now;

  return true;
}

/**
 * Get rate limit information for an identifier
 */
export function getRateLimitInfo(
  identifier: string,
  limit: number = 30,
  windowMinutes: number = 15
): RateLimitInfo {
  const now = Date.now() / 1000; // Unix timestamp in seconds
  const windowSeconds = windowMinutes * 60;

  if (!rateLimitStorage.has(identifier)) {
    return {
      remaining: limit,
      reset_time: now + windowSeconds,
      limit: limit
    };
  }

  const userData = rateLimitStorage.get(identifier)!;
  const requests = userData.requests;

  // Clean old requests
  const cutoffTime = now - windowSeconds;
  userData.requests = requests.filter(reqTime => reqTime > cutoffTime);

  const remaining = Math.max(0, limit - userData.requests.length);
  const resetTime = now + windowSeconds;

  return {
    remaining: remaining,
    reset_time: resetTime,
    limit: limit
  };
}
