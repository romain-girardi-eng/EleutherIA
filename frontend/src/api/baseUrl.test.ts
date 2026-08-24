import { describe, expect, it } from 'vitest';

import { apiEndpoint, resolveApiBase } from './baseUrl';

describe('API base resolution', () => {
  it('routes every EleutherIA Pages preview to the public API origin', () => {
    expect(resolveApiBase(
      'https://ancient-free-will-api.romain-girardi-eng.workers.dev',
      'ef8c8d0c.eleutheria.pages.dev',
    )).toBe('https://free-will.app');
    expect(resolveApiBase('http://localhost:8000', 'eleutheria.pages.dev')).toBe(
      'https://free-will.app',
    );
  });

  it('fails over from the retired Worker on every runtime host', () => {
    expect(resolveApiBase(
      'https://ancient-free-will-api.romain-girardi-eng.workers.dev/',
      'free-will.app',
    )).toBe('https://free-will.app');
  });

  it('preserves explicit local and supported custom API bases', () => {
    expect(resolveApiBase('http://localhost:8000/', 'localhost')).toBe(
      'http://localhost:8000',
    );
    expect(resolveApiBase('https://api.example.test', 'research.example.test')).toBe(
      'https://api.example.test',
    );
  });
});

describe('API endpoint joining', () => {
  it('does not duplicate the local Vite proxy prefix', () => {
    expect(apiEndpoint('/api/kg/stats', '/api')).toBe('/api/kg/stats');
    expect(apiEndpoint('api/health', '/api/')).toBe('/api/health');
  });

  it('keeps the API prefix on an origin base', () => {
    expect(apiEndpoint('/api/kg/stats', 'https://free-will.app/')).toBe(
      'https://free-will.app/api/kg/stats',
    );
  });

  it('supports an origin whose deployment base already ends in api', () => {
    expect(apiEndpoint('/api/health', 'https://example.test/api')).toBe(
      'https://example.test/api/health',
    );
  });
});
