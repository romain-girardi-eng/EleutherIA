import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';

// Heavy leaf components are stubbed: this suite exercises the SSE state
// machine of GraphRAGPage, not the graph/chat rendering.
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

vi.mock('../../api/client', () => ({
  apiClient: { getNode: vi.fn() },
}));

interface RightPanelStubProps {
  agentActive?: boolean;
  isStreaming?: boolean;
  streamEnded?: boolean;
  response: {
    query?: string;
    degraded?: boolean;
    reasoning_path?: { total_nodes?: number };
  } | null;
}

vi.mock('../../components/graphrag/RightPanel', () => ({
  default: ({ agentActive, isStreaming, streamEnded, response }: RightPanelStubProps) => (
    <div
      data-testid="right-panel"
      data-agent-active={String(Boolean(agentActive))}
      data-streaming={String(Boolean(isStreaming))}
      data-stream-ended={String(Boolean(streamEnded))}
      data-response-query={response?.query ?? ''}
      data-response-nodes={String(response?.reasoning_path?.total_nodes ?? '')}
      data-response-degraded={String(Boolean(response?.degraded))}
    />
  ),
}));

vi.mock('./MobileGraphSheet', () => ({ default: () => null }));
vi.mock('./WelcomeHero', () => ({ default: () => <div data-testid="welcome-hero" /> }));
vi.mock('../../components/AuthModal', () => ({ default: () => null }));
vi.mock('../../components/NodeDetailPanel', () => ({ default: () => null }));
vi.mock('../../components/ReasoningPanel', () => ({ ReasoningPanel: () => null }));

interface ChatPanelStubProps {
  messages: Array<{ role: string; content: string }>;
  error: string | null;
}

vi.mock('./ChatPanel', () => ({
  default: ({ messages, error }: ChatPanelStubProps) => (
    <div data-testid="chat-panel" data-error={error ?? ''}>
      {messages.map((m, i) => (
        <p key={i} data-testid={`msg-${m.role}`}>
          {m.content}
        </p>
      ))}
    </div>
  ),
}));

import GraphRAGPage from './index';

const QUESTION = 'Did Chrysippus hold that assent is up to us?';

function sseResponse(frames: string[]) {
  const encoder = new TextEncoder();
  let index = 0;
  const reader = {
    read: async () =>
      index < frames.length
        ? { done: false, value: encoder.encode(frames[index++]) }
        : { done: true, value: undefined },
    cancel: async () => undefined,
    releaseLock: () => undefined,
  };
  return {
    ok: true,
    status: 200,
    headers: { get: () => 'text/event-stream' },
    body: { getReader: () => reader },
    text: async () => '',
  };
}

const renderPage = () =>
  render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={[{ pathname: '/ask', state: { initialQuery: QUESTION } }]}>
        <GraphRAGPage />
      </MemoryRouter>
    </I18nextProvider>,
  );

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('GraphRAGPage — stream ending without a `complete` event', () => {
  beforeEach(() => {
    const frames = [
      'data: {"type":"status","data":{"message":"Retrieving from the knowledge graph"}}\n\n',
      'data: {"type":"tool_result","data":{"tool":"search_nodes","summary":"7 nodes","duration_ms":420,"node_count":7,"passage_count":3}}\n\n',
      `data: {"type":"answer_chunk","data":"${'Chrysippus argues that assent is up to us. '.repeat(8)}"}\n\n`,
    ];

    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse(frames) as unknown as Response;
      }),
    );
  });

  it('clears the live/active state on every exit path', async () => {
    renderPage();

    const panel = await screen.findByTestId('right-panel');
    await waitFor(() => {
      expect(panel).toHaveAttribute('data-agent-active', 'false');
    });
    expect(panel).toHaveAttribute('data-streaming', 'false');
    expect(panel).toHaveAttribute('data-stream-ended', 'true');
  });

  it('populates a degraded right-panel response bound to the run', async () => {
    renderPage();

    const panel = await screen.findByTestId('right-panel');
    await waitFor(() => {
      expect(panel).toHaveAttribute('data-response-degraded', 'true');
    });
    expect(panel).toHaveAttribute('data-response-query', QUESTION);
    // 7 nodes summed from the single tool_result frame.
    expect(panel).toHaveAttribute('data-response-nodes', '7');
  });

  it('keeps the streamed partial answer in the chat', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('msg-assistant')).toHaveTextContent(
        /Chrysippus argues that assent is up to us/,
      );
    });
  });
});

describe('GraphRAGPage — degraded stream with no answer text', () => {
  beforeEach(() => {
    const frames = [
      'data: {"type":"tool_result","data":{"tool":"search_nodes","summary":"5 nodes","node_count":5,"passage_count":2}}\n\n',
    ];

    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse(frames) as unknown as Response;
      }),
    );
  });

  it('explains the interrupted run and reports what was retrieved', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('msg-assistant')).toHaveTextContent(
        /stopped before the final synthesis \(5 nodes, 2 passages retrieved\)/i,
      );
    });
  });
});

describe('GraphRAGPage — mid-stream silence', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: { signal?: AbortSignal }) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        const signal = init?.signal;
        // A stream that opens and then never sends anything again.
        const reader = {
          read: () =>
            new Promise((_resolve, reject) => {
              signal?.addEventListener('abort', () => {
                const err = new Error('aborted');
                err.name = 'AbortError';
                reject(err);
              });
            }),
          cancel: async () => undefined,
          releaseLock: () => undefined,
        };
        return {
          ok: true,
          status: 200,
          headers: { get: () => 'text/event-stream' },
          body: { getReader: () => reader },
          text: async () => '',
        } as unknown as Response;
      }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('aborts after the idle timeout and surfaces a connection-lost error', async () => {
    renderPage();

    // Let the handshake resolve, then burn through the idle budget.
    await vi.advanceTimersByTimeAsync(1_000);
    await vi.advanceTimersByTimeAsync(96_000);

    const panel = screen.getByTestId('right-panel');
    expect(panel).toHaveAttribute('data-agent-active', 'false');
    expect(panel).toHaveAttribute('data-streaming', 'false');
    expect(panel).toHaveAttribute('data-stream-ended', 'true');
    expect(screen.getByTestId('chat-panel').getAttribute('data-error')).toMatch(
      /Connection lost/i,
    );
  });
});

describe('GraphRAGPage — stream ending with a `complete` event', () => {
  beforeEach(() => {
    const complete = {
      type: 'complete',
      data: {
        query: QUESTION,
        answer: 'Chrysippus distinguishes the impulse from the assent.',
        citations: { ancient_sources: [], modern_scholarship: [] },
        sources: [],
        reasoning_path: {
          starting_nodes: [],
          expanded_nodes: [],
          traversed_edges: [],
          total_nodes: 12,
          total_edges: 30,
        },
        nodes_used: 12,
        edges_traversed: 30,
        success: true,
      },
    };
    const frames = [`data: ${JSON.stringify(complete)}\n\n`];

    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse(frames) as unknown as Response;
      }),
    );
  });

  it('clears the live state and keeps the authoritative response', async () => {
    renderPage();

    const panel = await screen.findByTestId('right-panel');
    await waitFor(() => {
      expect(panel).toHaveAttribute('data-response-nodes', '12');
    });
    expect(panel).toHaveAttribute('data-agent-active', 'false');
    expect(panel).toHaveAttribute('data-streaming', 'false');
    expect(panel).toHaveAttribute('data-stream-ended', 'true');
    expect(panel).toHaveAttribute('data-response-degraded', 'false');
  });
});

describe('GraphRAGPage — explicit model routing', () => {
  it('sends the persisted Gemini selection with the next question', async () => {
    localStorage.setItem(
      'eleutheria.graphrag.model-selection.v1',
      'gemini-3.1-pro',
    );
    const requestedUrls: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        const raw = String(url);
        if (raw.includes('/api/graphrag/models')) {
          return {
            ok: true,
            json: async () => [
              {
                key: 'gemini-3.1-pro',
                label: 'Gemini 3.1 Pro',
                provider: 'gemini',
                context: 1_000_000,
                available: true,
              },
            ],
          } as unknown as Response;
        }
        requestedUrls.push(raw);
        return sseResponse([
          'data: {"type":"complete","data":{"answer":"ok","citations":{},"sources":[]}}\n\n',
        ]) as unknown as Response;
      }),
    );

    renderPage();

    await waitFor(() => {
      expect(requestedUrls.some((url) => url.includes('model=gemini-3.1-pro'))).toBe(true);
    });
  });
});

describe('GraphRAGPage — failing stream', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return {
          ok: false,
          status: 502,
          headers: { get: () => 'text/plain' },
          text: async () => 'bad gateway',
        } as unknown as Response;
      }),
    );
  });

  it('clears the live state and surfaces the error', async () => {
    renderPage();

    const panel = await screen.findByTestId('right-panel');
    await waitFor(() => {
      expect(panel).toHaveAttribute('data-stream-ended', 'true');
    });
    expect(panel).toHaveAttribute('data-agent-active', 'false');
    expect(panel).toHaveAttribute('data-streaming', 'false');
    expect(screen.getByTestId('chat-panel').getAttribute('data-error')).toContain('502');
  });
});
