import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import NodeDetailPanel, { buildNodeCitation } from './NodeDetailPanel';

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
          node={{ ...summary, description: 'Verified editorial detail.' }}
          onClose={onClose}
          detailState={{ loading: false, error: null }}
          releaseId="kg-sha256-release"
        />
      </MemoryRouter>,
    );

    expect(screen.getByText('Verified editorial detail.')).toBeInTheDocument();
    expect(screen.queryByText(/Loading release-bound editorial detail/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /copy\s*citation/i })).toBeEnabled();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('builds an existing, release-bound visualizer citation', () => {
    const citation = buildNodeCitation(
      { id: 'concept_eph_hemin', label: "What is up to us" },
      'kg-sha256-abc123',
      new Date('2026-08-24T12:00:00Z'),
    );

    expect(citation).toContain('Release kg-sha256-abc123');
    expect(citation).toContain('Accessed 2026-08-24');
    expect(citation).toContain(
      'https://free-will.app/visualizer?node=concept_eph_hemin&release=kg-sha256-abc123&mode=atlas',
    );
    expect(citation).not.toContain('/node/');
  });
});
