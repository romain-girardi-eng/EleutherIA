/**
 * Parallel questions — one run per question, keyed by runId.
 *
 * Every assertion here is about ISOLATION: two SSE streams interleaved must
 * never bleed into each other, the submission cap must hold, and Stop/Close
 * must only ever touch the run they were aimed at.
 */

import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import type { AgentStep } from '../../types/graphrag';

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

vi.mock('../../api/client', () => ({
  apiClient: { getNode: vi.fn() },
}));

interface RightPanelStubProps {
  agentSteps?: AgentStep[];
  isStreaming?: boolean;
  streamEnded?: boolean;
  response: { query?: string } | null;
}

vi.mock('../../components/graphrag/RightPanel', () => ({
  default: ({ agentSteps, isStreaming, streamEnded, response }: RightPanelStubProps) => (
    <div
      data-testid="right-panel"
      data-steps={JSON.stringify(agentSteps ?? [])}
      data-streaming={String(Boolean(isStreaming))}
      data-stream-ended={String(Boolean(streamEnded))}
      data-response-query={response?.query ?? ''}
    />
  ),
}));

vi.mock('./MobileGraphSheet', () => ({ default: () => null }));
vi.mock('../../components/AuthModal', () => ({ default: () => null }));
vi.mock('../../components/NodeDetailPanel', () => ({ default: () => null }));
vi.mock('../../components/ReasoningPanel', () => ({ ReasoningPanel: () => null }));

interface WelcomeHeroStubProps {
  notice: string | null;
}

vi.mock('./WelcomeHero', () => ({
  default: ({ notice }: WelcomeHeroStubProps) => (
    <div data-testid="welcome-hero">
      <span data-testid="welcome-notice">{notice ?? ''}</span>
    </div>
  ),
}));

interface RunTabStub {
  id: string;
  question: string;
  status: string;
}

interface ChatPanelStubProps {
  messages: Array<{ role: string; content: string }>;
  query: string;
  setQuery: (q: string) => void;
  streaming: boolean;
  canSubmit: boolean;
  error: string | null;
  notice: string | null;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
  runs: RunTabStub[];
  activeRunId: string | null;
  onRunSelect: (id: string) => void;
  onRunClose: (id: string) => void;
}

// The stub renders exactly the per-run wiring the page hands down, so the
// tests drive the real page logic and never the chat chrome.
vi.mock('./ChatPanel', () => ({
  default: ({
    messages,
    query,
    setQuery,
    streaming,
    canSubmit,
    error,
    notice,
    onSubmit,
    onStop,
    runs,
    activeRunId,
    onRunSelect,
    onRunClose,
  }: ChatPanelStubProps) => (
    <div
      data-testid="chat-panel"
      data-error={error ?? ''}
      data-streaming={String(streaming)}
      data-can-submit={String(canSubmit)}
      data-run-count={String(runs.length)}
      data-active-index={String(runs.findIndex((r) => r.id === activeRunId))}
    >
      <span data-testid="notice">{notice ?? ''}</span>
      <form onSubmit={onSubmit}>
        <input
          aria-label="ask"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">ask</button>
      </form>
      <button type="button" data-testid="stop" onClick={onStop}>
        stop
      </button>
      {runs.map((run, index) => (
        <div key={run.id}>
          <button data-testid={`select-${index}`} onClick={() => onRunSelect(run.id)}>
            {run.question}
          </button>
          <span data-testid={`status-${index}`}>{run.status}</span>
          <button data-testid={`close-${index}`} onClick={() => onRunClose(run.id)}>
            close
          </button>
        </div>
      ))}
      {messages.map((m, i) => (
        <p key={i} data-testid={`msg-${m.role}`}>
          {m.content}
        </p>
      ))}
    </div>
  ),
}));

import GraphRAGPage from './index';

const Q1 = 'Did Chrysippus hold that assent is up to us?';
const Q2 = 'What is Alexander of Aphrodisias arguing in De fato 20?';
const Q3 = 'How does Origen read Romans 9?';
const Q4 = 'Does Plotinus have a doctrine of the will?';

/** A hand-fed SSE stream: frames arrive only when the test pushes them. */
function makeStream() {
  const encoder = new TextEncoder();
  const frames: string[] = [];
  let finished = false;
  let notify: (() => void) | null = null;
  const state = { aborted: false };

  const reader = (signal?: AbortSignal) => ({
    read: () =>
      new Promise<{ done: boolean; value?: Uint8Array }>((resolve, reject) => {
        const fail = () => {
          state.aborted = true;
          const err = new Error('aborted');
          err.name = 'AbortError';
          reject(err);
        };
        if (signal?.aborted) {
          fail();
          return;
        }
        signal?.addEventListener('abort', fail);
        const drain = () => {
          if (frames.length > 0) {
            resolve({ done: false, value: encoder.encode(frames.shift()!) });
            return true;
          }
          if (finished) {
            resolve({ done: true, value: undefined });
            return true;
          }
          return false;
        };
        if (drain()) return;
        notify = () => {
          if (drain()) notify = null;
        };
      }),
    cancel: async () => undefined,
    releaseLock: () => undefined,
  });

  return {
    state,
    push: async (frame: string) => {
      frames.push(frame);
      await act(async () => {
        notify?.();
        await Promise.resolve();
      });
    },
    end: async () => {
      finished = true;
      await act(async () => {
        notify?.();
        await Promise.resolve();
      });
    },
    reader,
  };
}

type Stream = ReturnType<typeof makeStream>;

/** question → stream, created lazily so a test only wires what it uses. */
function stubFetch(options?: { status?: (question: string) => number }) {
  const streams = new Map<string, Stream>();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: { signal?: AbortSignal }) => {
      const raw = String(url);
      if (raw.includes('/api/graphrag/models')) {
        return { ok: true, json: async () => [] } as unknown as Response;
      }
      const question =
        new URL(raw, 'http://localhost').searchParams.get('question') ?? '';
      const status = options?.status?.(question) ?? 200;
      if (status !== 200) {
        return {
          ok: false,
          status,
          headers: { get: (k: string) => (k === 'Retry-After' ? '5' : null) },
          text: async () => 'busy',
        } as unknown as Response;
      }
      const stream = makeStream();
      streams.set(question, stream);
      return {
        ok: true,
        status: 200,
        headers: { get: () => 'text/event-stream' },
        body: { getReader: () => stream.reader(init?.signal) },
        text: async () => '',
      } as unknown as Response;
    }),
  );
  return {
    get: async (question: string) => {
      await waitFor(() => expect(streams.has(question)).toBe(true));
      return streams.get(question)!;
    },
  };
}

const toolFrame = (tool: string) =>
  `data: {"type":"tool_result","data":{"tool":"${tool}","summary":"hit","node_count":3,"passage_count":1}}\n\n`;

const completeFrame = (question: string, answer: string) =>
  `data: ${JSON.stringify({
    type: 'complete',
    data: {
      query: question,
      answer,
      citations: { ancient_sources: [], modern_scholarship: [] },
      sources: [],
      reasoning_path: {
        starting_nodes: [],
        expanded_nodes: [],
        traversed_edges: [],
        total_nodes: 1,
        total_edges: 0,
      },
      nodes_used: 1,
      edges_traversed: 0,
      success: true,
    },
  })}\n\n`;

const renderPage = (initialQuery: string = Q1) =>
  render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={[{ pathname: '/ask', state: { initialQuery } }]}>
        <GraphRAGPage />
      </MemoryRouter>
    </I18nextProvider>,
  );

const ask = async (question: string) => {
  const input = screen.getByLabelText('ask');
  fireEvent.change(input, { target: { value: question } });
  await act(async () => {
    fireEvent.click(screen.getByText('ask'));
    await Promise.resolve();
  });
};

const readSteps = (): AgentStep[] =>
  JSON.parse(screen.getByTestId('right-panel').getAttribute('data-steps') ?? '[]');

const runCount = () =>
  Number(screen.getByTestId('chat-panel').getAttribute('data-run-count'));

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('GraphRAGPage — per-run isolation', () => {
  it('keeps interleaved streams on their own run', async () => {
    const fetchStub = stubFetch();
    renderPage(Q1);

    const s1 = await fetchStub.get(Q1);
    await ask(Q2);
    const s2 = await fetchStub.get(Q2);

    expect(runCount()).toBe(2);
    // Submitting switched to the new run.
    expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-active-index', '1');

    // Interleave: A, B, A, B.
    await s1.push(toolFrame('search_nodes_q1'));
    await s2.push(toolFrame('search_nodes_q2'));
    await s1.push(toolFrame('read_passages_q1'));
    await s2.push(toolFrame('read_passages_q2'));

    // The visible panel is run 2's — and only run 2's.
    await waitFor(() => expect(readSteps()).toHaveLength(2));
    expect(readSteps().map((s) => s.tool)).toEqual([
      'search_nodes_q2',
      'read_passages_q2',
    ]);

    // Switching tabs swaps the whole view over to run 1.
    fireEvent.click(screen.getByTestId('select-0'));
    await waitFor(() => {
      expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-active-index', '0');
    });
    expect(readSteps().map((s) => s.tool)).toEqual([
      'search_nodes_q1',
      'read_passages_q1',
    ]);
  });

  it('lands each answer on the run that asked for it', async () => {
    const fetchStub = stubFetch();
    renderPage(Q1);

    const s1 = await fetchStub.get(Q1);
    await ask(Q2);
    const s2 = await fetchStub.get(Q2);

    // Run 2 finishes FIRST — the later run must not steal run 1's slot.
    await s2.push(completeFrame(Q2, 'Alexander argues against the Stoics.'));
    await s2.end();
    await waitFor(() => {
      expect(screen.getByTestId('status-1')).toHaveTextContent('done');
    });
    expect(screen.getByTestId('status-0')).toHaveTextContent('streaming');
    expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-query', Q2);
    expect(screen.getByTestId('msg-assistant')).toHaveTextContent(
      'Alexander argues against the Stoics.',
    );

    await s1.push(completeFrame(Q1, 'Chrysippus distinguishes impulse from assent.'));
    await s1.end();
    await waitFor(() => {
      expect(screen.getByTestId('status-0')).toHaveTextContent('done');
    });

    // Still on run 2 — a background completion never hijacks the view.
    expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-query', Q2);

    fireEvent.click(screen.getByTestId('select-0'));
    await waitFor(() => {
      expect(screen.getByTestId('right-panel')).toHaveAttribute('data-response-query', Q1);
    });
    expect(screen.getByTestId('msg-assistant')).toHaveTextContent(
      'Chrysippus distinguishes impulse from assent.',
    );
  });
});

describe('GraphRAGPage — submission cap', () => {
  it('allows a third run while two stream, and blocks the fourth', async () => {
    stubFetch();
    renderPage(Q1);

    await ask(Q2);
    expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-can-submit', 'true');

    await ask(Q3);
    await waitFor(() => expect(runCount()).toBe(3));
    expect(screen.getByTestId('chat-panel')).toHaveAttribute('data-can-submit', 'false');

    await ask(Q4);
    await waitFor(() => {
      expect(screen.getByTestId('notice')).toHaveTextContent(
        /Up to 3 questions can run at once/i,
      );
    });
    expect(runCount()).toBe(3);
  });
});

describe('GraphRAGPage — stop and close', () => {
  it('stops only the active run', async () => {
    const fetchStub = stubFetch();
    renderPage(Q1);

    const s1 = await fetchStub.get(Q1);
    await ask(Q2);
    const s2 = await fetchStub.get(Q2);

    await act(async () => {
      fireEvent.click(screen.getByTestId('stop'));
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId('status-1')).toHaveTextContent('stopped');
    });
    expect(screen.getByTestId('status-0')).toHaveTextContent('streaming');
    expect(s2.state.aborted).toBe(true);
    expect(s1.state.aborted).toBe(false);
  });

  it('aborts the stream of a closed tab', async () => {
    const fetchStub = stubFetch();
    renderPage(Q1);

    const s1 = await fetchStub.get(Q1);
    await ask(Q2);
    const s2 = await fetchStub.get(Q2);

    await act(async () => {
      fireEvent.click(screen.getByTestId('close-0'));
      await Promise.resolve();
    });

    await waitFor(() => expect(runCount()).toBe(1));
    expect(s1.state.aborted).toBe(true);
    expect(s2.state.aborted).toBe(false);
    // The surviving run stays active and untouched.
    expect(screen.getByTestId('status-0')).toHaveTextContent('streaming');
  });
});

describe('GraphRAGPage — server at capacity', () => {
  it('shows a busy notice and leaves no dead tab', async () => {
    stubFetch({ status: (question) => (question === Q1 ? 429 : 200) });
    renderPage(Q1);

    await waitFor(() => {
      expect(screen.getByTestId('welcome-notice')).toHaveTextContent(
        /Server busy — retry in 5 seconds/i,
      );
    });
    // No run survived the rejection.
    expect(screen.queryByTestId('chat-panel')).not.toBeInTheDocument();
  });
});
