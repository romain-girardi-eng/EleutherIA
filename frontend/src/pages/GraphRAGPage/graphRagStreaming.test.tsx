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
  provisionalAnswer?: string | null;
}

vi.mock('./ChatPanel', () => ({
  default: ({ messages, error, provisionalAnswer }: ChatPanelStubProps) => (
    <div
      data-testid="chat-panel"
      data-error={error ?? ''}
      data-provisional={provisionalAnswer ?? ''}
    >
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

describe('GraphRAGPage — blocked publication', () => {
  it('explains verification withholding instead of showing an empty answer', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse([
          `data: ${JSON.stringify({
            type: 'complete',
            data: {
              answer: '',
              citations: {},
              sources: [],
              metadata: {
                publication_gate: {
                  publishable: false,
                  reasons: ['content_gate_not_passed'],
                },
              },
            },
          })}\n\n`,
        ]) as unknown as Response;
      }),
    );

    renderPage();

    const message = await screen.findByTestId('msg-assistant');
    expect(message).toHaveTextContent(/withheld because its citations/i);
    expect(message).not.toHaveTextContent(/No answer generated/i);
  });
});

/**
 * An SSE body that delivers `before`, then blocks until `release()` is
 * called, then delivers `after` and closes — so a test can observe the page
 * mid-stream, between the provisional draft and the verdict.
 */
function gatedSseResponse(before: string[], after: string[]) {
  const encoder = new TextEncoder();
  const queue = [...before];
  let released = false;
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const reader = {
    read: async () => {
      if (queue.length === 0 && !released) {
        await gate;
        released = true;
        queue.push(...after);
      }
      const next = queue.shift();
      return next === undefined
        ? { done: true, value: undefined }
        : { done: false, value: encoder.encode(next) };
    },
    cancel: async () => undefined,
    releaseLock: () => undefined,
  };
  const response = {
    ok: true,
    status: 200,
    headers: { get: () => 'text/event-stream' },
    body: { getReader: () => reader },
    text: async () => '',
  };
  return { response, release: () => release() };
}

const DRAFT_ONE = 'DRAFT-ONE Chrysippus perhaps held that assent is up to us. ';
const DRAFT_TWO = 'DRAFT-TWO The dating remains open.';
const VERIFIED = 'Chrysippus distinguishes the impulse from the assent.';

const provisionalFrames = [
  'data: {"type":"status","data":{"message":"Synthesizing","stage":"dialectical_synthesis"}}\n\n',
  `data: ${JSON.stringify({ type: 'answer_provisional', data: DRAFT_ONE, provisional: true })}\n\n`,
  `data: ${JSON.stringify({ type: 'answer_provisional', data: DRAFT_TWO, provisional: true })}\n\n`,
];

function stubGatedFetch(before: string[], after: string[]) {
  const gated = gatedSseResponse(before, after);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (String(url).includes('/api/graphrag/models')) {
        return { ok: true, json: async () => [] } as unknown as Response;
      }
      return gated.response as unknown as Response;
    }),
  );
  return gated;
}

describe('GraphRAGPage — provisional answer protocol', () => {
  it('shows the un-audited draft as provisional, then replaces it atomically with the verdict', async () => {
    const gated = stubGatedFetch(provisionalFrames, [
      `data: ${JSON.stringify({
        type: 'answer_final',
        provisional: false,
        data: { answer: VERIFIED, withheld: false, reasons: [], citations: [] },
      })}\n\n`,
      `data: ${JSON.stringify({ type: 'answer_chunk', data: VERIFIED })}\n\n`,
      `data: ${JSON.stringify({
        type: 'complete',
        data: {
          query: QUESTION,
          answer: VERIFIED,
          citations: { ancient_sources: [], modern_scholarship: [] },
          sources: [],
          success: true,
        },
      })}\n\n`,
    ]);

    renderPage();

    // Mid-stream: the draft is on screen, flagged provisional, and it is NOT
    // an assistant message.
    const panel = await screen.findByTestId('chat-panel');
    await waitFor(() => {
      expect(panel.getAttribute('data-provisional')).toBe(DRAFT_ONE + DRAFT_TWO);
    });
    expect(screen.queryByTestId('msg-assistant')).toBeNull();

    gated.release();

    // The verdict lands: the gated text is the answer and the draft is gone —
    // from the run state and from what survives the stream.
    await waitFor(() => {
      expect(screen.getByTestId('msg-assistant')).toHaveTextContent(VERIFIED);
    });
    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    expect(panel.getAttribute('data-provisional')).toBe('');
    expect(screen.getByTestId('msg-assistant')).not.toHaveTextContent(/DRAFT-/);
    expect(sessionStorage.getItem('eleutheria.graphrag.messages.v1') ?? '').not.toContain('DRAFT-');
  });

  it('replaces the draft with the withholding notice when the verdict blocks it', async () => {
    const gated = stubGatedFetch(provisionalFrames, [
      `data: ${JSON.stringify({
        type: 'answer_final',
        provisional: false,
        data: { answer: '', withheld: true, reasons: ['citation_audit_not_passed'], citations: [] },
      })}\n\n`,
      `data: ${JSON.stringify({
        type: 'complete',
        data: {
          query: QUESTION,
          answer: '',
          citations: {},
          sources: [],
          metadata: {
            publication_gate: { publishable: false, reasons: ['citation_audit_not_passed'] },
          },
        },
      })}\n\n`,
    ]);

    renderPage();

    const panel = await screen.findByTestId('chat-panel');
    await waitFor(() => {
      expect(panel.getAttribute('data-provisional')).toContain('DRAFT-ONE');
    });

    gated.release();

    const message = await screen.findByTestId('msg-assistant');
    await waitFor(() => {
      expect(message).toHaveTextContent(/withheld because its citations/i);
    });
    expect(message).not.toHaveTextContent(/DRAFT-/);
    expect(panel.getAttribute('data-provisional')).toBe('');
  });

  it('never keeps the draft when the stream drops before the verdict', async () => {
    const longDraft = `DRAFT-LONG ${'Chrysippus perhaps held that assent is up to us. '.repeat(8)}`;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse([
          'data: {"type":"tool_result","data":{"tool":"search_nodes","summary":"5 nodes","node_count":5,"passage_count":2}}\n\n',
          `data: ${JSON.stringify({ type: 'answer_provisional', data: longDraft, provisional: true })}\n\n`,
          // A provisional-flagged answer_chunk is a draft too.
          `data: ${JSON.stringify({ type: 'answer_chunk', data: longDraft, provisional: true })}\n\n`,
        ]) as unknown as Response;
      }),
    );

    renderPage();

    const message = await screen.findByTestId('msg-assistant');
    await waitFor(() => {
      expect(message).toHaveTextContent(/stopped before the final synthesis/i);
    });
    expect(message).not.toHaveTextContent(/DRAFT-LONG/);
    expect(screen.getByTestId('chat-panel').getAttribute('data-provisional')).toBe('');
    expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-degraded', 'true');
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

/**
 * The verdict must outlive the stream that carried it. Whatever happens after
 * `answer_final` — a clean EOF, a trace-only synthetic `complete`, an `error`
 * frame — the gated text (or the withholding notice) stays on screen and is
 * never demoted to an "incomplete" notice.
 */
describe('GraphRAGPage — the verdict survives every ending', () => {
  const publishableFinal = `data: ${JSON.stringify({
    type: 'answer_final',
    provisional: false,
    data: { answer: VERIFIED, withheld: false, reasons: [], citations: [] },
  })}\n\n`;
  const withheldFinal = `data: ${JSON.stringify({
    type: 'answer_final',
    provisional: false,
    data: { answer: '', withheld: true, reasons: ['citation_audit_not_passed'], citations: [] },
  })}\n\n`;
  const retrieval =
    'data: {"type":"tool_result","data":{"tool":"search_nodes","summary":"5 nodes","node_count":5,"passage_count":2}}\n\n';

  function stubFetch(frames: string[]) {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/graphrag/models')) {
          return { ok: true, json: async () => [] } as unknown as Response;
        }
        return sseResponse(frames) as unknown as Response;
      }),
    );
  }

  it('keeps the verified answer on a clean EOF right after the verdict', async () => {
    stubFetch([retrieval, ...provisionalFrames, publishableFinal]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(VERIFIED);
    expect(message).not.toHaveTextContent(/stopped before the final synthesis/i);
    expect(message).not.toHaveTextContent(/DRAFT-/);
    expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-degraded', 'false');
    expect(screen.getByTestId('chat-panel').getAttribute('data-provisional')).toBe('');
  });

  it('keeps the withholding notice on a clean EOF right after a withheld verdict', async () => {
    stubFetch([retrieval, ...provisionalFrames, withheldFinal]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(/withheld because its citations/i);
    expect(message).not.toHaveTextContent(/stopped before the final synthesis/i);
    expect(message).not.toHaveTextContent(/DRAFT-/);
  });

  it('keeps the verified answer when the terminal frame is trace-only', async () => {
    stubFetch([
      ...provisionalFrames,
      publishableFinal,
      'data: {"type":"complete","data":{"trace_id":"t-1"}}\n\n',
    ]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(VERIFIED);
    expect(message).not.toHaveTextContent(/No answer generated/i);
  });

  it('keeps the withholding notice when the terminal frame is trace-only', async () => {
    stubFetch([
      ...provisionalFrames,
      withheldFinal,
      'data: {"type":"complete","data":{"trace_id":"t-1"}}\n\n',
    ]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(/withheld because its citations/i);
    expect(message).not.toHaveTextContent(/No answer generated/i);
    expect(message).not.toHaveTextContent(/DRAFT-/);
  });

  it('reads through an error frame to the terminal complete and keeps the verified answer', async () => {
    stubFetch([
      ...provisionalFrames,
      publishableFinal,
      'data: {"type":"error","message":"The audit database went away."}\n\n',
      `data: ${JSON.stringify({
        type: 'complete',
        data: { trace_id: 't-2', answer: VERIFIED, error: 'The audit database went away.' },
      })}\n\n`,
    ]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(VERIFIED);
    expect(message).not.toHaveTextContent(/stopped before the final synthesis/i);
    expect(screen.getByTestId('chat-panel').getAttribute('data-error')).toMatch(
      /audit database went away/i,
    );
    expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-degraded', 'false');
  });

  it('keeps the withholding notice when an error follows a withheld verdict', async () => {
    stubFetch([
      ...provisionalFrames,
      withheldFinal,
      'data: {"type":"error","message":"The audit database went away."}\n\n',
      `data: ${JSON.stringify({
        type: 'complete',
        data: {
          trace_id: 't-3',
          answer: '',
          error: 'The audit database went away.',
          metadata: { publication_gate: { publishable: false, reasons: ['citation_audit_not_passed'] } },
        },
      })}\n\n`,
    ]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-stream-ended', 'true');
    });
    const message = screen.getByTestId('msg-assistant');
    expect(message).toHaveTextContent(/withheld because its citations/i);
    expect(message).not.toHaveTextContent(/DRAFT-/);
  });
});
