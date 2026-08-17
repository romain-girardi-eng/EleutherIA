import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../i18n/config';
import { extraResources } from '../../i18n/extraResources';
import WaitingExperience, { ScholarlyWaitExpectation } from './WaitingExperience';
import { formatWaitingElapsed, resolveWaitingPhase } from './waitingExperienceUtils';

function renderWithI18n(ui: React.ReactNode) {
  return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

beforeEach(async () => {
  await i18n.changeLanguage('en');
});

afterEach(() => {
  vi.useRealTimers();
});

describe('waiting phase helpers', () => {
  it('maps raw SSE stages and messages to human phases', () => {
    expect(resolveWaitingPhase('draft_claim_ledger')).toBe('synthesize');
    expect(resolveWaitingPhase('citation_verification')).toBe('verify');
    expect(resolveWaitingPhase('tool:read_passages')).toBe('read');
    expect(resolveWaitingPhase(undefined, 'Classifying query...')).toBe('classify');
    expect(resolveWaitingPhase(undefined, 'Retrieving knowledge graph nodes')).toBe('search');
  });

  it('formats a stable minute-second timer', () => {
    expect(formatWaitingElapsed(0)).toBe('00:00');
    expect(formatWaitingElapsed(5 * 60_000 + 9_000)).toBe('05:09');
  });
});

describe('WaitingExperience', () => {
  it('shows elapsed time, the current phase, and long-stage reassurance', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-17T12:00:00Z'));
    const startedAt = Date.now();

    renderWithI18n(
      <WaitingExperience
        startedAt={startedAt}
        stage="draft_claim_ledger"
        statusMessage="Drafting claim ledger…"
      />,
    );

    expect(screen.getByTestId('waiting-elapsed')).toHaveTextContent('00:00');
    expect(screen.getByTestId('waiting-phase')).toHaveTextContent(
      'Composing the scholarly synthesis',
    );
    expect(screen.queryByTestId('waiting-reassurance')).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(46_000);
    });

    expect(screen.getByTestId('waiting-elapsed')).toHaveTextContent('00:46');
    expect(screen.getByTestId('waiting-reassurance')).toHaveTextContent(
      'Still working',
    );
  });

  it('rotates the corpus-grounded aside every 20 seconds and can dismiss it', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-17T12:00:00Z'));

    renderWithI18n(
      <WaitingExperience startedAt={Date.now()} stage="search_nodes" />,
    );

    expect(screen.getByTestId('waiting-wisdom')).toHaveTextContent(
      'capacity to act otherwise',
    );

    act(() => {
      vi.advanceTimersByTime(20_000);
    });

    expect(screen.getByTestId('waiting-wisdom')).toHaveTextContent(
      'The Lazy Argument',
    );

    fireEvent.click(
      screen.getByRole('button', { name: 'Hide philosophical asides' }),
    );
    expect(screen.queryByTestId('waiting-wisdom')).not.toBeInTheDocument();
  });

  it('publishes the upfront five-to-ten-minute expectation', () => {
    renderWithI18n(<ScholarlyWaitExpectation />);
    expect(screen.getByTestId('scholarly-wait-expectation')).toHaveTextContent(
      '5 to 10 minutes',
    );
  });
});

describe('waiting translations', () => {
  const lineKeys = [
    'capacity',
    'lazyArgument',
    'carneades',
    'epictetus',
    'origen',
    'alexander',
    'chrysippus',
  ] as const;

  it('ships every waiting line in all five interface languages', () => {
    for (const locale of ['en', 'fr', 'de', 'it', 'el'] as const) {
      const waiting = extraResources[locale].graphRagUi.waiting;
      expect(waiting.expectation.length).toBeGreaterThan(20);
      for (const key of lineKeys) {
        expect(waiting.lines[key].length).toBeGreaterThan(40);
      }
    }
  });

  it('keeps the three required French lines verbatim with non-breaking spaces', () => {
    const lines = extraResources.fr.graphRagUi.waiting.lines;
    expect(lines.capacity).toBe(
      "« Vous avez, bien sûr, la capacité d'agir autrement — fermer cet onglet, par exemple. Mais votre patience prouvera que vous n'êtes pas esclave du destin. Ou… que vous étiez quelqu'un de patient. »",
    );
    expect(lines.lazyArgument).toBe(
      "« L'Argument paresseux conclut qu'il est inutile d'attendre. Chrysippe l'a réfuté. Malheureusement pour vous. »",
    );
    expect(lines.carneades).toBe(
      "« Carnéade doutait qu'on puisse rien savoir avec certitude. Nous, nous vérifions chaque citation — c'est ce qui prend du temps. »",
    );
  });
});
