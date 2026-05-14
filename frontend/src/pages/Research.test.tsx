import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';
import Research from './Research';

// Stub both stream hooks so the page renders without network or framer-motion side effects.
vi.mock('../hooks/useResearchStream', () => ({
  useResearchStream: () => ({
    status: 'idle',
    events: [],
    citations: [],
    activeSubagents: [],
    toolCalls: [],
    kgActivations: [],
    streamedAnswer: '',
    finalAnswer: null,
    traceId: null,
    error: null,
    retryCount: 0,
    start: vi.fn(),
    cancel: vi.fn(),
    reset: vi.fn(),
  }),
}));

vi.mock('../hooks/useOpencodeStream', () => ({
  useOpencodeStream: () => ({
    status: 'idle',
    events: [],
    citations: [],
    activeSubagents: [],
    toolCalls: [],
    kgActivations: [],
    streamedAnswer: '',
    finalAnswer: null,
    traceId: null,
    error: null,
    retryCount: 0,
    start: vi.fn(),
    cancel: vi.fn(),
    reset: vi.fn(),
  }),
}));

const MODE_KEY = 'eleutheria.research.mode';

const renderPage = () =>
  render(
    <I18nextProvider i18n={i18n}>
      <Research />
    </I18nextProvider>,
  );

beforeEach(() => {
  window.localStorage.clear();
});

describe('Research page — runtime mode toggle', () => {
  it('defaults to deep mode when no preference is stored', () => {
    renderPage();
    const deepRadio = screen.getByRole('radio', { name: /Analyse approfondie|Deep analysis/i });
    expect(deepRadio).toHaveAttribute('aria-checked', 'true');
  });

  it('honours a stored "quick" preference', () => {
    window.localStorage.setItem(MODE_KEY, 'quick');
    renderPage();
    const quickRadio = screen.getByRole('radio', {
      name: /Réponse rapide|Quick answer/i,
    });
    expect(quickRadio).toHaveAttribute('aria-checked', 'true');
  });

  it('persists the selected mode to localStorage', () => {
    renderPage();
    const quickRadio = screen.getByRole('radio', {
      name: /Réponse rapide|Quick answer/i,
    });
    fireEvent.click(quickRadio);
    expect(window.localStorage.getItem(MODE_KEY)).toBe('quick');
  });

  it('renders both mode latency badges', () => {
    renderPage();
    expect(screen.getByText('~2 min')).toBeInTheDocument();
    expect(screen.getByText(/~10.15 min/)).toBeInTheDocument();
  });
});
