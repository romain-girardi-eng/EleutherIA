import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import ProofChainBadge from './ProofChainBadge';
import ProofChainPanel from './ProofChainPanel';
import { shortenIri } from './iri';
import type { ProofChainStep } from '../../types/graphrag';

import '../../i18n/config';

const inverseStep: ProofChainStep = {
  rule: 'inverseOf',
  premises: [
    [
      'https://free-will.app/kg/person_plato',
      'https://free-will.app/ontology/wrote',
      'https://free-will.app/kg/work_republic',
    ],
  ],
  conclusion: [
    'https://free-will.app/kg/work_republic',
    'https://free-will.app/ontology/authoredBy',
    'https://free-will.app/kg/person_plato',
  ],
  confidence: 1.0,
};

describe('shortenIri', () => {
  it('shortens KG resource IRIs to res:<local>', () => {
    expect(shortenIri('https://free-will.app/kg/person_plato')).toMatchObject({
      display: 'res:person_plato',
      prefix: 'res',
    });
  });

  it('shortens ontology IRIs to kg:<local>', () => {
    expect(shortenIri('https://free-will.app/ontology/wrote')).toMatchObject({
      display: 'kg:wrote',
      prefix: 'kg',
    });
  });

  it('returns the original IRI when no prefix matches', () => {
    expect(shortenIri('urn:cts:greekLit:tlg0012.tlg001:1.1')).toMatchObject({
      display: 'urn:cts:greekLit:tlg0012.tlg001:1.1',
      prefix: null,
    });
  });
});

describe('ProofChainPanel', () => {
  it('renders shortened premises and conclusion for an inverseOf step', () => {
    render(<ProofChainPanel steps={[inverseStep]} />);

    // Plato + Republic appear twice (once in premise, once in conclusion)
    expect(screen.getAllByText('res:person_plato').length).toBe(2);
    expect(screen.getAllByText('res:work_republic').length).toBe(2);
    expect(screen.getByText('kg:wrote')).toBeInTheDocument();
    expect(screen.getByText('kg:authoredBy')).toBeInTheDocument();
  });

  it('renders nothing for an empty step list', () => {
    const { container } = render(<ProofChainPanel steps={[]} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('ProofChainBadge', () => {
  it('is hidden when no proof chain is provided', () => {
    const { container } = render(<ProofChainBadge steps={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('toggles the panel on click', async () => {
    const user = userEvent.setup();
    render(<ProofChainBadge steps={[inverseStep]} />);

    expect(screen.queryByTestId('proof-chain-panel')).toBeNull();

    const toggle = screen.getByRole('button');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await user.click(toggle);

    expect(screen.getByTestId('proof-chain-panel')).toBeInTheDocument();
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });
});
