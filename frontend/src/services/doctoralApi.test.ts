import { describe, expect, it } from 'vitest';

import { doctoralAuthorizationHeader } from './doctoralApi';

describe('doctoral API authorization', () => {
  it('uses the same explicit Bearer contract as the main API client', () => {
    expect(doctoralAuthorizationHeader('signed-token')).toBe('Bearer signed-token');
    expect(doctoralAuthorizationHeader(undefined)).toBeUndefined();
  });
});
