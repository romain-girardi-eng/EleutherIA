import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';
import Research from './Research';
import { resetResearchRuntimeCache } from '../hooks/useResearchRuntimes';

const startQuick = vi.fn();
const startDeep = vi.fn();

const idleStream = (start: typeof startQuick) => ({
  status: 'idle' as const,
  events: [],
  citations: [],
  activeSubagents: [],
  toolCalls: [],
  kgActivations: [],
  stageTimings: [],
  streamedAnswer: '',
  finalAnswer: null,
  answerVerification: 'none' as const,
  traceId: null,
  error: null,
  retryCount: 0,
  start,
  cancel: vi.fn(),
  reset: vi.fn(),
});

vi.mock('../hooks/useResearchStream', () => ({
  useResearchStream: () => idleStream(startQuick),
}));

vi.mock('../hooks/useOpencodeStream', () => ({
  useOpencodeStream: () => idleStream(startDeep),
}));

let authed = true;
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: authed, isLoading: false }),
}));

vi.mock('../components/AuthModal', () => ({
  default: ({ isOpen }: { isOpen: boolean }) =>
    isOpen ? <div data-testid="auth-modal" /> : null,
}));

const MODE_KEY = 'eleutheria.research.mode';

/** `configured` drives whether the deep runtime is offered. */
function mockRuntimeProbe(configured: boolean) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      json: async () => ({ configured, agents: ['scholar-orchestrator'] }),
    })) as unknown as typeof fetch,
  );
}

const renderPage = () =>
  render(
    <I18nextProvider i18n={i18n}>
      <Research />
    </I18nextProvider>,
  );

const deepRadio = () =>
  screen.getByRole('radio', { name: /Analyse approfondie|Deep analysis/i });
const quickRadio = () =>
  screen.getByRole('radio', { name: /Réponse rapide|Quick answer/i });

beforeEach(() => {
  window.localStorage.clear();
  resetResearchRuntimeCache();
  authed = true;
  startQuick.mockClear();
  startDeep.mockClear();
  mockRuntimeProbe(true);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Research page — runtime mode toggle', () => {
  it('defaults to quick mode when no preference is stored', () => {
    renderPage();
    expect(quickRadio()).toHaveAttribute('aria-checked', 'true');
  });

  it('honours a stored "deep" preference once the runtime is available', async () => {
    window.localStorage.setItem(MODE_KEY, 'deep');
    renderPage();
    await waitFor(() => {
      expect(deepRadio()).toHaveAttribute('aria-checked', 'true');
    });
  });

  it('persists the selected mode to localStorage', async () => {
    renderPage();
    await waitFor(() => expect(deepRadio()).toBeEnabled());
    fireEvent.click(deepRadio());
    expect(window.localStorage.getItem(MODE_KEY)).toBe('deep');
  });

  it('renders both mode latency badges', () => {
    renderPage();
    expect(screen.getByText('~2 min')).toBeInTheDocument();
    expect(screen.getByText(/~10.15 min/)).toBeInTheDocument();
  });
});

describe('Research page — unavailable deep runtime', () => {
  beforeEach(() => {
    mockRuntimeProbe(false);
  });

  it('disables the deep option when the backend reports it unconfigured', async () => {
    renderPage();
    await waitFor(() => expect(deepRadio()).toBeDisabled());
    expect(deepRadio()).toHaveAttribute('aria-disabled', 'true');
  });

  it('falls back to quick even when "deep" is the stored preference', async () => {
    window.localStorage.setItem(MODE_KEY, 'deep');
    renderPage();
    await waitFor(() => expect(deepRadio()).toBeDisabled());
    expect(quickRadio()).toHaveAttribute('aria-checked', 'true');
  });

  it('routes a submitted query to the quick runtime', async () => {
    window.localStorage.setItem(MODE_KEY, 'deep');
    renderPage();
    await waitFor(() => expect(deepRadio()).toBeDisabled());
    fireEvent.change(screen.getByLabelText(/Research question|Question de recherche/i), {
      target: { value: 'Chrysippus on fate' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Send|Envoyer/i }));
    expect(startQuick).toHaveBeenCalledWith('Chrysippus on fate');
    expect(startDeep).not.toHaveBeenCalled();
  });
});

describe('Research page — authentication gate', () => {
  beforeEach(() => {
    authed = false;
  });

  it('opens the auth modal instead of firing a query that can only 401', () => {
    renderPage();
    fireEvent.change(screen.getByLabelText(/Research question|Question de recherche/i), {
      target: { value: 'Alexander against Stoic fate' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Send|Envoyer/i }));
    expect(startQuick).not.toHaveBeenCalled();
    expect(screen.getByTestId('auth-modal')).toBeInTheDocument();
  });

  it('shows a sign-in notice for logged-out visitors', () => {
    renderPage();
    expect(
      screen.getByRole('button', { name: /Sign in|Se connecter/i }),
    ).toBeInTheDocument();
  });
});
