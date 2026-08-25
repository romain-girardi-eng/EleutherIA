import { describe, it, expect } from 'vitest';
import { classifyResearchError } from './researchErrors';

describe('classifyResearchError', () => {
  it('returns null when there is no error', () => {
    expect(classifyResearchError(null)).toBeNull();
    expect(classifyResearchError('')).toBeNull();
  });

  it('maps 401 to an actionable auth prompt', () => {
    const info = classifyResearchError('HTTP 401');
    expect(info?.kind).toBe('authRequired');
    expect(info?.needsAuth).toBe(true);
    // Retrying the same query without signing in cannot succeed.
    expect(info?.retryable).toBe(false);
    expect(info?.i18nKey).toBe('research.errors.authRequired');
  });

  it('treats 402 and 403 as an exhausted budget rather than a bug', () => {
    expect(classifyResearchError('HTTP 402')?.kind).toBe('quotaExceeded');
    expect(classifyResearchError('HTTP 403')?.kind).toBe('quotaExceeded');
    expect(classifyResearchError('HTTP 403')?.retryable).toBe(false);
  });

  it('maps 410 to the stale-session case the opencode proxy documents', () => {
    const info = classifyResearchError('HTTP 410');
    expect(info?.kind).toBe('sessionExpired');
    expect(info?.retryable).toBe(true);
  });

  it('separates a missing runtime (503) from an unreachable one (502/504)', () => {
    expect(classifyResearchError('HTTP 503')?.kind).toBe('runtimeUnavailable');
    expect(classifyResearchError('HTTP 503')?.retryable).toBe(false);
    expect(classifyResearchError('HTTP 502')?.kind).toBe('runtimeUnreachable');
    expect(classifyResearchError('HTTP 504')?.kind).toBe('runtimeUnreachable');
  });

  it('maps 429 to rate limiting', () => {
    expect(classifyResearchError('HTTP 429')?.kind).toBe('rateLimited');
  });

  it('maps other 4xx to an invalid request and 5xx to a server error', () => {
    expect(classifyResearchError('HTTP 422')?.kind).toBe('invalidRequest');
    expect(classifyResearchError('HTTP 500')?.kind).toBe('serverError');
  });

  it('recognises the browser-specific network failure messages', () => {
    for (const message of [
      'Failed to fetch',
      'NetworkError when attempting to fetch resource.',
      'Load failed',
    ]) {
      expect(classifyResearchError(message)?.kind).toBe('network');
    }
  });

  it('maps the hooks own sentinel messages to a server error', () => {
    expect(classifyResearchError('no_response_body')?.kind).toBe('serverError');
    expect(classifyResearchError('no_session_id_in_response')?.kind).toBe('serverError');
  });

  it('falls back to the generic key and keeps the raw message', () => {
    const info = classifyResearchError('something_unexpected');
    expect(info?.kind).toBe('unknown');
    expect(info?.i18nKey).toBe('research.errors.streamFailed');
    expect(info?.raw).toBe('something_unexpected');
  });
});
