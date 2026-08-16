/**
 * `research_note` SSE wiring — the abandoned-lead journal.
 *
 * Each frame must land TWICE: once as its own timeline row (so the ACTIVITY
 * view narrates the dropped lead inside the phase where it died) and once
 * appended to the single research-journal step the Reasoning tab falls back to
 * when the model streams no chain-of-thought.
 */

import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

// The RightPanel stub serialises the agentSteps it receives so the test can
// assert on the SSE state machine without rendering the panel tree.
vi.mock('../../components/graphrag/RightPanel', () => ({
  default: ({ agentSteps }: { agentSteps?: AgentStep[] }) => (
    <div data-testid="right-panel" data-steps={JSON.stringify(agentSteps ?? [])} />
  ),
}));

vi.mock('./MobileGraphSheet', () => ({ default: () => null }));
vi.mock('./WelcomeHero', () => ({ default: () => <div data-testid="welcome-hero" /> }));
vi.mock('../../components/AuthModal', () => ({ default: () => null }));
vi.mock('../../components/NodeDetailPanel', () => ({ default: () => null }));
vi.mock('../../components/ReasoningPanel', () => ({ ReasoningPanel: () => null }));
vi.mock('./ChatPanel', () => ({ default: () => <div data-testid="chat-panel" /> }));

import GraphRAGPage from './index';

const QUESTION = 'Did Chrysippus hold that assent is up to us?';

const NOTE_ONE =
  'data: {"type":"research_note","data":{"kind":"dead_end","stage":"agent_loop",' +
  '"summary":"Searched \\"autexousion\\" via search_passages — no evidence came back.",' +
  '"detail":"looking for a Stoic anchor"}}\n\n';
const NOTE_TWO =
  'data: {"type":"research_note","data":{"kind":"rejected_claim","stage":"claim_ledger",' +
  '"summary":"Claim dropped — its evidence did not hold up."}}\n\n';
const NOTE_EMPTY =
  'data: {"type":"research_note","data":{"kind":"gap","stage":"quality_gate","summary":"  "}}\n\n';

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

const stubFetch = (frames: string[]) =>
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (String(url).includes('/api/graphrag/models')) {
        return { ok: true, json: async () => [] } as unknown as Response;
      }
      return sseResponse(frames) as unknown as Response;
    }),
  );

const readSteps = async (): Promise<AgentStep[]> => {
  const panel = await screen.findByTestId('right-panel');
  return JSON.parse(panel.getAttribute('data-steps') ?? '[]') as AgentStep[];
};

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('GraphRAGPage — research_note frames', () => {
  it('records each note as its own timeline step', async () => {
    stubFetch([NOTE_ONE, NOTE_TWO]);
    renderPage();

    await waitFor(async () => {
      const notes = (await readSteps()).filter((s) => s.type === 'research_note');
      expect(notes).toHaveLength(2);
    });

    const notes = (await readSteps()).filter((s) => s.type === 'research_note');
    expect(notes[0].noteKind).toBe('dead_end');
    expect(notes[0].stage).toBe('agent_loop');
    expect(notes[0].summary).toMatch(/no evidence came back/);
    expect(notes[0].detail).toBe('looking for a Stoic anchor');
    expect(notes[1].noteKind).toBe('rejected_claim');
    expect(notes[1].stage).toBe('claim_ledger');
  });

  it('accumulates the summaries into ONE research-journal step', async () => {
    stubFetch([NOTE_ONE, NOTE_TWO]);
    renderPage();

    await waitFor(async () => {
      const journal = (await readSteps()).filter((s) => s.type === 'research_journal');
      expect(journal).toHaveLength(1);
      expect(journal[0].reasoning).toMatch(/no evidence came back/);
      expect(journal[0].reasoning).toMatch(/its evidence did not hold up/);
    });

    const [journal] = (await readSteps()).filter((s) => s.type === 'research_journal');
    // The detail rides along under its summary, and the notes stay separated.
    expect(journal.reasoning).toContain('looking for a Stoic anchor');
    expect(journal.reasoning?.split('\n\n')).toHaveLength(2);
  });

  it('ignores a note with no summary', async () => {
    stubFetch([NOTE_EMPTY]);
    renderPage();

    const panel = await screen.findByTestId('right-panel');
    await waitFor(() => {
      expect(panel).toHaveAttribute('data-steps');
    });
    const steps = await readSteps();
    expect(steps.filter((s) => s.type === 'research_note')).toHaveLength(0);
    expect(steps.filter((s) => s.type === 'research_journal')).toHaveLength(0);
  });

  it('never lets a note reach the answer prose', async () => {
    stubFetch([
      NOTE_ONE,
      'data: {"type":"answer_chunk","data":"Chrysippus argues that assent is up to us."}\n\n',
    ]);
    renderPage();

    await waitFor(async () => {
      expect((await readSteps()).some((s) => s.type === 'research_note')).toBe(true);
    });
    expect(screen.queryByText(/no evidence came back/)).not.toBeInTheDocument();
  });
});
