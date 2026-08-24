import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from '../../api/client';
import { GraphWorkspaceProvider } from '../../context/GraphWorkspaceContext';
import ScholarWorkspace from './ScholarWorkspace';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ScholarWorkspace resilience', () => {
  it('keeps lazy-detail failure local, exposes retry, and gives compare a 44px effective target', async () => {
    const user = userEvent.setup();
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode')
      .mockRejectedValueOnce(new Error('Request failed with status code 503'))
      .mockResolvedValueOnce({
        node: {
          id: 'n1',
          label: 'Aristotle',
          type: 'person',
          description: 'Recovered editorial detail.',
        },
        release_id: 'kg-sha256-scholar',
        served_total_nodes: 1,
        served_total_edges: 0,
      });
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Aristotle', type: 'person', period: 'Classical Greek' }],
      edges: [],
      release_id: 'kg-sha256-scholar',
    }));

    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1&mode=scholar&node=n1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <ScholarWorkspace />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Scholar workspace' })).toBeVisible();
    const checkbox = await screen.findByRole('checkbox', { name: 'Add Aristotle to comparison' });
    expect(checkbox).toHaveClass('h-5', 'w-5');
    expect(checkbox.closest('label')).toHaveClass('min-h-11', 'min-w-11');

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The release-bound summary remains available.',
    );
    expect(screen.getByRole('heading', { name: 'Scholar workspace' })).toBeVisible();

    await user.click(checkbox);
    const comparison = screen.getByText('Comparison').closest('section');
    expect(comparison).not.toBeNull();
    expect(within(comparison!).getByRole('button', { name: 'Aristotle' })).toHaveClass('min-h-11');
    await user.click(screen.getByRole('button', { name: 'Add to evidence thread' }));
    const thread = screen.getByText('Evidence thread · 1').closest('section');
    expect(thread).not.toBeNull();
    expect(within(thread!).getByRole('button', { name: 'Aristotle' })).toHaveClass('min-h-11');

    await user.click(screen.getByRole('button', { name: 'Retry full detail' }));
    await waitFor(() => expect(screen.getByText('Recovered editorial detail.')).toBeVisible());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(detail).toHaveBeenCalledTimes(2);
  });
});
