import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeAll, describe, expect, it, vi } from 'vitest';

import i18n from '../i18n/config';
import de from '../i18n/locales/de.json';
import el from '../i18n/locales/el.json';
import en from '../i18n/locales/en.json';
import fr from '../i18n/locales/fr.json';
import it_ from '../i18n/locales/it.json';
import NodeDetailPanel from './NodeDetailPanel';
import {
  buildNodeCitation,
  isNodeCitationEligible,
} from './nodeCitation';
import { groupRelations, type RelatedNode } from './nodeDetail/nodeDetailModel';

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

describe('NodeDetailPanel release-bound detail', () => {
  it('rerenders when full detail arrives for the same node id', () => {
    const summary = { id: 'concept_choice', label: 'Choice', type: 'concept' };
    const onClose = vi.fn();
    const view = render(
      <MemoryRouter>
        <NodeDetailPanel
          node={summary}
          onClose={onClose}
          detailState={{ loading: true, error: null }}
          releaseId="kg-sha256-release"
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('status')).toHaveTextContent(/Loading the full record/i);
    expect(screen.queryByText(/No description has been written/i)).not.toBeInTheDocument();

    view.rerender(
      <MemoryRouter>
        <NodeDetailPanel
          node={{
            ...summary,
            description: 'Verified editorial detail.',
            metadata: { citation_verified: true },
          }}
          onClose={onClose}
          detailState={{ loading: false, error: null }}
          releaseId="kg-sha256-release"
        />
      </MemoryRouter>,
    );

    expect(screen.getByText('Verified editorial detail.')).toBeInTheDocument();
    expect(screen.queryByText(/Loading the full record/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /citation\s*unavailable/i })).toBeDisabled();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('builds an existing, release-bound visualizer citation', () => {
    const citation = buildNodeCitation(
      { id: 'concept_eph_hemin', label: "What is up to us" },
      'kg-sha256-abc123',
      {
        versionDoi: '10.5281/zenodo.99999999',
        commit: '4be75c43880d1f25d3f7b32922d9af8af569d3ac',
        snapshotDate: '2026-08-24',
        releaseId: 'kg-sha256-abc123',
      },
      new Date('2026-08-24T12:00:00Z'),
    );

    expect(citation).toContain('KG release kg-sha256-abc123');
    expect(citation).toContain('Zenodo version DOI 10.5281/zenodo.99999999');
    expect(citation).toContain('Git commit 4be75c43880d1f25d3f7b32922d9af8af569d3ac');
    expect(citation).toContain('KG snapshot 2026-08-24');
    expect(citation).toContain('Accessed 2026-08-24');
    expect(citation).toContain(
      'https://free-will.app/visualizer?node=concept_eph_hemin&release=kg-sha256-abc123&mode=atlas',
    );
    expect(citation).not.toContain('/node/');

    expect(() => buildNodeCitation(
      { id: 'concept_eph_hemin', label: "What is up to us" },
      'kg-sha256-other',
      {
        versionDoi: '10.5281/zenodo.99999999',
        commit: '4be75c43880d1f25d3f7b32922d9af8af569d3ac',
        snapshotDate: '2026-08-24',
        releaseId: 'kg-sha256-abc123',
      },
      new Date('2026-08-24T12:00:00Z'),
    )).toThrow(/does not match the served KG release/i);
  });

  it('fails citation eligibility closed unless curation is positively verified', () => {
    expect(isNodeCitationEligible({ metadata: { citability: 'discoverable_only' } })).toBe(false);
    expect(isNodeCitationEligible({ metadata: { citation_verdict: 'pending review' } })).toBe(false);
    expect(isNodeCitationEligible({ metadata: {} })).toBe(false);
    expect(isNodeCitationEligible({ metadata: { citation_verified: true } })).toBe(true);
    expect(isNodeCitationEligible({ metadata: { citation_verdict: 'corrected' } })).toBe(true);
  });
});

it('surfaces outstanding page verification instead of a stale verified badge', () => {
  render(<MemoryRouter><NodeDetailPanel onClose={vi.fn()} node={{
    id: 'position_with_offsets', label: 'A scholarly position', type: 'argument',
    metadata: { citation_verdict: 'verified', citation_verified: true,
      needs_page_verification: 'Four-digit values: offsets, not page ranges.' },
  }} /></MemoryRouter>);
  expect(screen.getByText('Source verification required')).toBeInTheDocument();
  expect(screen.getByRole('note')).toHaveTextContent('offsets, not page ranges');
  expect(screen.queryByText(/References checked against the sources/)).not.toBeInTheDocument();
});

it('does not flag an ancient passage merely because its edition page is absent', () => {
  render(<MemoryRouter><NodeDetailPanel onClose={vi.fn()} node={{
    id: 'passage_conventional_locus', label: 'Cicero, De Fato 41', type: 'passage',
    metadata: { language: 'lat', author: 'Cicero', work_title: 'De Fato', canonical_ref: '41',
      needs_page_verification: 'No printed page available' },
  }} /></MemoryRouter>);
  expect(screen.queryByText('Source verification required')).not.toBeInTheDocument();
});

describe('NodeDetailPanel dossier', () => {
  const relations: RelatedNode[] = [
    ...Array.from({ length: 8 }, (_, index) => ({
      id: `passage_${index}`,
      label: `Passage ${index}`,
      type: 'passage',
      relation: 'authored_by',
      direction: 'incoming' as const,
    })),
    { id: 'school_stoa', label: 'Stoa', type: 'school', relation: 'member_of', direction: 'outgoing' },
    { id: 'school_stoa', label: 'Stoa', type: 'school', relation: 'member_of', direction: 'outgoing' },
  ];

  it('groups relations by predicate and direction, deduplicating repeats', () => {
    const groups = groupRelations(relations);
    expect(groups.map((group) => [group.key, group.items.length])).toEqual([
      ['incoming:authored_by', 8],
      ['outgoing:member_of', 1],
    ]);
  });

  it('labels inverse relations from the reader’s side, caps long groups and navigates', () => {
    const onNavigate = vi.fn();
    render(
      <MemoryRouter>
        <NodeDetailPanel
          node={{ id: 'person_chrysippus', label: 'Chrysippus', type: 'person', description: 'Stoic.' }}
          relationships={relations}
          onClose={vi.fn()}
          onNavigateToNode={onNavigate}
        />
      </MemoryRouter>,
    );

    const authorOf = screen.getByRole('button', { name: /Author of/i });
    expect(authorOf).toHaveAttribute('aria-expanded', 'true');
    const group = authorOf.closest('li');
    expect(group).not.toBeNull();
    expect(within(group as HTMLElement).getAllByRole('button', { name: /^Passage \d/ })).toHaveLength(5);

    fireEvent.click(within(group as HTMLElement).getByRole('button', { name: /Show 3 more/i }));
    expect(within(group as HTMLElement).getAllByRole('button', { name: /^Passage \d/ })).toHaveLength(8);

    fireEvent.click(screen.getByRole('button', { name: /^Stoa/ }));
    expect(onNavigate).toHaveBeenCalledWith('school_stoa');
    expect(screen.getByRole('button', { name: /Member of/i })).toBeInTheDocument();
  });

  it('renders primary text verbatim, never through Markdown', () => {
    const text = 'κατηγοροῦσι τινε\\ς *̓ιούδα __καὶ__';
    render(
      <MemoryRouter>
        <NodeDetailPanel
          node={{
            id: 'passage_x',
            label: 'Hegesippus fr.',
            type: 'passage',
            description: text,
            metadata: { cts_urn: 'urn:cts:greekLit:tlg0000.tlg001:1' },
          }}
          onClose={vi.fn()}
        />
      </MemoryRouter>,
    );
    const body = screen.getByText(text);
    expect(body).toHaveAttribute('lang', 'grc');
    expect(screen.getAllByText('urn:cts:greekLit:tlg0000.tlg001:1', { selector: 'dd' }).length).toBeGreaterThan(0);
  });

  it('offers a retry when full detail fails, and has a labelled close control', () => {
    const onRetry = vi.fn();
    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <NodeDetailPanel
          node={{ id: 'concept_x', label: 'Fate', type: 'concept' }}
          onClose={onClose}
          detailState={{ loading: false, error: new Error('boom') }}
          onRetryDetail={onRetry}
        />
      </MemoryRouter>,
    );
    expect(screen.getByRole('alert')).toHaveTextContent(/could not be loaded/i);
    fireEvent.click(screen.getByRole('button', { name: /Try again/i }));
    expect(onRetry).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole('button', { name: /Close record/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('focuses the title on open and ignores Escape typed into an outside field', () => {
    const onClose = vi.fn();
    render(
      <MemoryRouter>
        <input aria-label="outside search" />
        <NodeDetailPanel node={{ id: 'concept_x', label: 'Fate', type: 'concept' }} onClose={onClose} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('heading', { level: 2, name: 'Fate' })).toHaveFocus();
    fireEvent.keyDown(screen.getByLabelText('outside search'), { key: 'Escape' });
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe('nodeDetail locale strings', () => {
  const locales = { en, fr, de, it: it_, el };

  it('defines every English key in all five languages', () => {
    const keys = (value: unknown, prefix = ''): string[] => (
      typeof value === 'object' && value !== null
        ? Object.entries(value).flatMap(([key, child]) => keys(child, `${prefix}${key}.`))
        : [prefix.slice(0, -1)]
    );
    const reference = keys(en.kg.nodeDetail).filter((key) => !key.endsWith('_many'));
    Object.values(locales).forEach((locale) => {
      const present = new Set(keys(locale.kg.nodeDetail));
      expect(reference.filter((key) => !present.has(key))).toEqual([]);
    });
  });

  it('uses French non-breaking spaces before high punctuation', () => {
    const strings = JSON.stringify(fr.kg.nodeDetail);
    expect(strings).not.toMatch(/ [:;!?%€»]/);
    expect(strings).not.toMatch(/« /);
  });
});
