import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { I18nextProvider } from 'react-i18next';
import { axe } from 'jest-axe';
import i18n from '../../i18n/config';
import EvidenceReview from './EvidenceReview';
import { responseFromVerdict } from './streamVerdict';

beforeEach(async () => { await i18n.changeLanguage('en'); });
const response = (status: string, publishable: boolean) => responseFromVerdict({
  answer: 'A supported claim [P1].', withheld: !publishable,
  citations: [{ id: 'p1', ref: 'P1', type: 'passage', label: 'A primary source', layer: 'primary', verified: true }],
  claim_ledger: [{ claim: 'A supported claim', status: 'supported', evidence_ids: ['p1'], support_type: 'direct' }],
  publication_gate: { status, publishable, reasons: publishable ? [] : ['citation_audit_not_passed'], withholding: { withheld_sentences: status === 'partial' ? 2 : 0 } },
}, 'Question', 1)!;

describe('scholarly evidence review', () => {
  it('reports automatic checks with their limits and opens the exact supporting passage', async () => {
    const onPassageClick = vi.fn();
    const { container } = render(<I18nextProvider i18n={i18n}><EvidenceReview response={response('passed', true)} onPassageClick={onPassageClick} /></I18nextProvider>);
    expect(screen.getByRole('status')).toHaveTextContent('Citation checks passed');
    expect(screen.getByText(/Check the passages and editions/)).toBeInTheDocument();
    fireEvent.click(screen.getByText('Inspect evidence and limitations'));
    fireEvent.click(screen.getByRole('button', { name: 'A primary source' }));
    expect(onPassageClick).toHaveBeenCalledWith('p1');
    expect((await axe(container)).violations).toEqual([]);
  });
  it('distinguishes partial publication from a complete answer', () => {
    render(<I18nextProvider i18n={i18n}><EvidenceReview response={response('partial', true)} /></I18nextProvider>);
    expect(screen.getByRole('status')).toHaveTextContent('Published with omissions');
    expect(screen.getByText('Statements withheld: 2')).toBeInTheDocument();
  });
  it('explains abstention and offers a narrower research path', () => {
    render(<I18nextProvider i18n={i18n}><EvidenceReview response={response('blocked', false)} /></I18nextProvider>);
    expect(screen.getByRole('status')).toHaveTextContent('Answer withheld');
    expect(screen.getByRole('status')).toHaveTextContent('Try a narrower question');
    expect(screen.queryByText('A supported claim')).not.toBeInTheDocument();
  });
  it('does not infer verification from a missing report or a demo', () => {
    render(<I18nextProvider i18n={i18n}><EvidenceReview /></I18nextProvider>);
    expect(screen.getByRole('status')).toHaveTextContent('Verification not available');
    expect(screen.queryByText('Citation checks passed')).not.toBeInTheDocument();
  });
});
