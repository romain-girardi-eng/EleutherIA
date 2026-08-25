import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import BilingualLocus from './BilingualLocus';
import type { LocusState } from './types';

const wrap = (ui: React.ReactNode) =>
  render(<MemoryRouter>{ui}</MemoryRouter>);

const GREEK: LocusState = {
  status: 'ready',
  locus: {
    original: 'τὰ μέν ἐστιν ἐφ᾿ ἡμῖν',
    originalLang: 'grc',
    translation: 'some things are up to us',
    reference: 'Encheiridion 1.1',
    urn: 'urn:cts:greekLit:tlg0557.tlg001:1.1',
  },
};

const LATIN: LocusState = {
  status: 'ready',
  locus: {
    original: 'Aeternitas igitur est interminabilis vitae possessio.',
    originalLang: 'la',
    translation: 'Eternity, then, is the possession of unbounded life.',
  },
};

describe('BilingualLocus', () => {
  it('marks the original with its own language and the translation with English', () => {
    const { container } = wrap(<BilingualLocus state={GREEK} tone="greek" />);
    const quote = container.querySelector('blockquote');
    expect(quote?.getAttribute('lang')).toBe('grc');
    expect(quote?.textContent).toBe('τὰ μέν ἐστιν ἐφ᾿ ἡμῖν');
    expect(
      screen.getByText('some things are up to us').getAttribute('lang'),
    ).toBe('en');
  });

  it('renders the original whole, with no ellipsis anywhere near it', () => {
    const long = 'ἀλλὰ '.repeat(200).trim();
    const { container } = wrap(
      <BilingualLocus
        state={{ status: 'ready', locus: { original: long, originalLang: 'grc' } }}
        tone="greek"
      />,
    );
    const quote = container.querySelector('blockquote');
    expect(quote?.textContent).toBe(long);
    expect(quote?.textContent).not.toContain('…');
  });

  it('switches off the locl substitution that would respell Latin u as v', () => {
    const { container } = wrap(<BilingualLocus state={LATIN} tone="latin" />);
    const quote = container.querySelector('blockquote');
    expect(quote?.className).toContain("font-feature-settings:'locl'_0");
    expect(quote?.textContent).toContain('igitur');
  });

  it('leaves the Greek run alone: nothing there needs overriding', () => {
    const { container } = wrap(<BilingualLocus state={GREEK} tone="greek" />);
    expect(container.querySelector('blockquote')?.className).not.toContain(
      'locl',
    );
  });

  it('exposes the CTS URN as selectable text', () => {
    wrap(<BilingualLocus state={GREEK} tone="greek" />);
    const urn = screen.getByText('urn:cts:greekLit:tlg0557.tlg001:1.1');
    expect(urn.className).toContain('select-all');
  });

  it('announces loading politely rather than jumping the layout silently', () => {
    wrap(<BilingualLocus state={{ status: 'loading' }} tone="greek" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('offers a way out of an error instead of an apology', async () => {
    const onRetry = vi.fn();
    wrap(
      <BilingualLocus state={{ status: 'error' }} tone="greek" onRetry={onRetry} />,
    );
    await userEvent.click(screen.getByRole('button', { name: 'Ask again' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('distinguishes an empty corpus answer from a failed request', () => {
    wrap(<BilingualLocus state={{ status: 'empty' }} tone="greek" />);
    expect(screen.getByRole('status').textContent).toContain(
      'No passage indexed',
    );
    expect(screen.queryByRole('button')).toBeNull();
  });
});
