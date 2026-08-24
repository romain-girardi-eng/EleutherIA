import { describe, expect, it } from 'vitest';

import { apiEndpoint } from './baseUrl';

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
