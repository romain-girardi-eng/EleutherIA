import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import NodeDetailPanel, {
  buildNodeCitation,
  isNodeCitationEligible,
} from './NodeDetailPanel';

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

    expect(screen.getByText(/Loading release-bound editorial detail/i)).toBeInTheDocument();
    expect(screen.getByText(/No description available/i)).toBeInTheDocument();

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
    expect(screen.queryByText(/Loading release-bound editorial detail/i)).not.toBeInTheDocument();
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
