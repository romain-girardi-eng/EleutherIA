import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useOpencodeStream } from './useOpencodeStream';

const fetchMock = vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>();

function encodedSseFromLines(lines: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const line of lines) {
        controller.enqueue(encoder.encode(`data: ${line}\n\n`));
      }
      controller.close();
    },
  });
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

function sseResponse(events: unknown[]): Response {
  const stream = encodedSseFromLines(events.map((e) => JSON.stringify(e)));
  return new Response(stream, {
    status: 200,
    headers: { 'content-type': 'text/event-stream' },
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock as unknown as typeof fetch);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useOpencodeStream', () => {
  it('creates a session, connects the SSE channel, and routes events for matching sessionID', async () => {
    const sessionId = 'ses_abc';
    fetchMock.mockImplementation(async (input) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
      if (url.includes('/session')) {
        return jsonResponse({ session_id: sessionId });
      }
      if (url.includes('/event')) {
        return sseResponse([
          { type: 'session.created', properties: { sessionID: sessionId, prompt: 'what is fate' } },
          {
            type: 'message.part.delta',
            properties: {
              sessionID: sessionId,
              messageID: 'm',
              partID: 'p',
              field: 'text',
              delta: 'Hello',
            },
          },
          {
            type: 'message.part.delta',
            properties: {
              sessionID: 'ses_OTHER',
              messageID: 'm',
              partID: 'p',
              field: 'text',
              delta: 'should-be-ignored',
            },
          },
          { type: 'session.idle', properties: { sessionID: sessionId } },
        ]);
      }
      throw new Error(`unexpected fetch: ${url}`);
    });

    const { result } = renderHook(() => useOpencodeStream({ retryDelayMs: 0 }));
    await act(async () => {
      await result.current.start('what is fate');
    });

    await waitFor(() => {
      expect(result.current.finalAnswer).not.toBeNull();
    });
    expect(result.current.streamedAnswer).toBe('Hello');
    expect(result.current.traceId).toBe(sessionId);
    // Cross-session delta must NOT appear in token output.
    expect(result.current.streamedAnswer).not.toContain('should-be-ignored');
  });

  it('reports an error when the session POST fails', async () => {
    fetchMock.mockImplementation(async () => new Response('boom', { status: 500 }));
    const { result } = renderHook(() => useOpencodeStream({ retryDelayMs: 0, maxRetries: 0 }));
    await act(async () => {
      await result.current.start('q');
    });
    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });
    expect(result.current.error).toContain('HTTP 500');
  });

  it('cancels mid-stream and POSTs an abort to the session URL', async () => {
    const sessionId = 'ses_cancel';
    let resolveReader: (() => void) | null = null;

    fetchMock.mockImplementation(async (input, init) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
      if (url.includes('/session') && !url.includes('/abort')) {
        return jsonResponse({ session_id: sessionId });
      }
      if (url.endsWith('/abort')) {
        return new Response(null, { status: 204 });
      }
      if (url.includes('/event')) {
        // A stream that hangs until externally aborted.
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            const encoder = new TextEncoder();
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({
                  type: 'session.created',
                  properties: { sessionID: sessionId, prompt: 'q' },
                })}\n\n`,
              ),
            );
            // Never close — wait for abort.
            resolveReader = () => controller.close();
            init?.signal?.addEventListener('abort', () => controller.close());
          },
        });
        return new Response(stream, {
          status: 200,
          headers: { 'content-type': 'text/event-stream' },
        });
      }
      throw new Error(`unexpected fetch: ${url}`);
    });

    const { result } = renderHook(() => useOpencodeStream({ retryDelayMs: 0 }));
    act(() => {
      void result.current.start('q');
    });
    await waitFor(() => {
      expect(result.current.traceId).toBe(sessionId);
    });
    act(() => {
      result.current.cancel();
    });
    await waitFor(() => {
      expect(result.current.status).toBe('cancelled');
    });
    expect(
      fetchMock.mock.calls.some(([url]) =>
        typeof url === 'string' ? url.endsWith('/abort') : false,
      ),
    ).toBe(true);
    // No further drain needed — the abort handler closed the controller.
    void resolveReader;
  });
});
