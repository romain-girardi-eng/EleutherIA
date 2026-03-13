import { afterEach, describe, expect, it, vi } from 'vitest';
import { DatabaseService } from '../src/services/database';

describe('DatabaseService RPC schema routing', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('uses the public profile for RPCs by default', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const db = new DatabaseService({
      SUPABASE_URL: 'https://example.supabase.co/rest/v1',
      SUPABASE_KEY: 'test-key',
    } as any);

    await db.rpc('get_text_stats');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;

    expect(url).toBe('https://example.supabase.co/rest/v1/rpc/get_text_stats');
    expect(headers['Accept-Profile']).toBe('public');
    expect(headers['Content-Profile']).toBe('public');
  });

  it('keeps explicit schema overrides when provided', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const db = new DatabaseService({
      SUPABASE_URL: 'https://example.supabase.co',
      SUPABASE_KEY: 'test-key',
    } as any);

    await db.rpc('custom_function', { foo: 'bar' }, 'free_will');

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;

    expect(headers['Accept-Profile']).toBe('free_will');
    expect(headers['Content-Profile']).toBe('free_will');
  });
});
