import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { apiClient } from '../../api/client';
import { GraphWorkspaceProvider } from '../../context/GraphWorkspaceContext';
import i18n from '../../i18n/config';
import ScholarWorkspace from './ScholarWorkspace';

beforeAll(async () => {
  await i18n.changeLanguage('en');
});

afterEach(() => {
  vi.restoreAllMocks();
});

const NODES = [
  { id: 'n1', label: 'Aristotle', type: 'person', period: 'Classical Greek', school: 'Peripatetics' },
  { id: 'n2', label: 'Chrysippus', type: 'person', period: 'Hellenistic Greek', school: 'Stoics' },
  { id: 'n3', label: 'Self-determination', type: 'concept', period: 'Patristic', greek_term: 'αὐτεξούσιον' },
  { id: 'n4', label: 'Epicurus', type: 'person', period: 'Hellenistic Greek', school: 'Epicureans' },
  { id: 'n5', label: 'Carneades', type: 'person', period: 'Hellenistic Greek', school: 'Academics' },
];
const EDGES = [
  { source: 'n2', target: 'n1', relation: 'critiques' },
  { source: 'n4', target: 'n2', relation: 'opposes' },
  { source: 'n3', target: 'n2', relation: 'discussed_by' },
  { source: 'n3', target: 'n4', relation: 'discussed_by' },
];

function renderScholar(url = '/visualizer?workspace=1&mode=scholar') {
  const graphLoader = vi.fn(async () => ({ nodes: NODES, edges: EDGES, release_id: 'kg-sha256-scholar' }));
  render(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <ScholarWorkspace />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>
    </I18nextProvider>,
  );
}

describe('ScholarWorkspace', () => {
  it('keeps lazy-detail failure local, exposes retry, and keeps 44px targets', async () => {
    const user = userEvent.setup();
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode')
      .mockRejectedValueOnce(new Error('Request failed with status code 503'))
      .mockResolvedValueOnce({
        node: { id: 'n1', label: 'Aristotle', type: 'person', description: 'Recovered editorial detail.' },
        release_id: 'kg-sha256-scholar',
        served_total_nodes: 5,
        served_total_edges: 4,
      });
    renderScholar('/visualizer?workspace=1&mode=scholar&node=n1');

    expect(await screen.findByRole('heading', { name: 'Scholar workspace' })).toBeVisible();
    const checkbox = await screen.findByRole('checkbox', { name: 'Add Aristotle to comparison' });
    expect(checkbox).toHaveClass('h-5', 'w-5');
    expect(checkbox.closest('label')).toHaveClass('min-h-11', 'min-w-11');

    expect(await screen.findByRole('alert')).toHaveTextContent('The release-bound summary remains available.');

    await user.click(checkbox);
    const comparison = screen.getByRole('heading', { name: /Comparison · 1\/4/ }).closest('section');
    expect(within(comparison!).getByRole('button', { name: 'Aristotle' })).toHaveClass('min-h-11');

    await user.click(screen.getByRole('button', { name: 'Add to evidence thread' }));
    const thread = screen.getByRole('heading', { name: 'Evidence thread · 1' }).closest('section');
    expect(within(thread!).getByRole('button', { name: /^1\. Aristotle/ })).toHaveClass('min-h-11');

    await user.click(screen.getByRole('button', { name: 'Retry full detail' }));
    await waitFor(() => expect(screen.getByText('Recovered editorial detail.')).toBeVisible());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(detail).toHaveBeenCalledTimes(2);
  });

  it('searches accent-insensitively, sorts with aria-sort, and faceted filters narrow the table', async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, 'getWorkspaceNode').mockResolvedValue({
      node: { id: 'n3', label: 'Self-determination', type: 'concept' },
      release_id: 'kg-sha256-scholar',
      served_total_nodes: 5,
      served_total_edges: 4,
    });
    renderScholar();

    const table = await screen.findByRole('table', { name: /Knowledge-graph nodes/ });
    await within(table).findByRole('button', { name: /^Chrysippus/ });

    await user.type(screen.getByRole('searchbox', { name: 'Search this release' }), 'αυτεξουσιον');
    await waitFor(() => expect(within(table).getAllByRole('rowheader')).toHaveLength(1));
    expect(within(table).getByRole('rowheader')).toHaveTextContent('Self-determination');
    expect(screen.getByText('1 of 5 nodes matches')).toBeInTheDocument();

    await user.clear(screen.getByRole('searchbox', { name: 'Search this release' }));
    const nodeHeader = within(table).getByRole('columnheader', { name: /Node/ });
    expect(nodeHeader).toHaveAttribute('aria-sort', 'none');
    await user.click(within(nodeHeader).getByRole('button'));
    expect(nodeHeader).toHaveAttribute('aria-sort', 'ascending');
    await waitFor(() => expect(within(table).getAllByRole('rowheader')[0]).toHaveTextContent('Aristotle'));

    await user.click(screen.getByRole('button', { name: /^Stoics\s*1$/ }));
    await waitFor(() => expect(within(table).getAllByRole('rowheader')).toHaveLength(1));
    expect(screen.getByRole('button', { name: 'Remove filter: Stoics' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Clear filter' }));
    await waitFor(() => expect(within(table).getAllByRole('rowheader')).toHaveLength(5));
  });

  it('supports keyboard navigation, caps comparison at four, and opens the compare view', async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, 'getWorkspaceNode').mockRejectedValue(new Error('offline'));
    renderScholar();

    const table = await screen.findByRole('table', { name: /Knowledge-graph nodes/ });
    await within(table).findByRole('button', { name: /^Chrysippus/ });
    await user.click(screen.getByRole('searchbox', { name: 'Search this release' }));
    await user.keyboard('{ArrowDown}');
    const firstRow = within(table).getAllByRole('rowheader')[0].querySelector('button');
    expect(firstRow).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    const secondRow = within(table).getAllByRole('rowheader')[1].querySelector('button');
    expect(secondRow).toHaveFocus();
    await user.keyboard('c');
    await user.keyboard('{Home}c{ArrowDown}{ArrowDown}c{ArrowDown}c');
    expect(within(table).getAllByRole('checkbox', { checked: true })).toHaveLength(4);
    const remaining = within(table).getAllByRole('checkbox', { checked: false });
    expect(remaining).toHaveLength(1);
    expect(remaining[0]).toBeDisabled();

    await user.click(screen.getByRole('tab', { name: /Compare/ }));
    expect(await screen.findByRole('table', { name: 'Side-by-side comparison of the selected nodes' })).toBeVisible();
    expect(screen.getByRole('heading', { name: /Shared neighbours/ })).toBeVisible();
  });

  it('finds a path between two nodes chosen from suggestions', async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, 'getWorkspaceNode').mockRejectedValue(new Error('offline'));
    renderScholar();
    await screen.findByRole('table', { name: /Knowledge-graph nodes/ });

    await user.click(screen.getByRole('tab', { name: /Paths/ }));
    const from = await screen.findByRole('combobox', { name: 'From' });
    await user.type(from, 'Aris');
    await user.click(await screen.findByRole('option', { name: /Aristotle/ }));
    await user.type(screen.getByRole('combobox', { name: 'To' }), 'Epic');
    await user.click(await screen.findByRole('option', { name: /Epicurus/ }));
    await user.click(screen.getByRole('button', { name: 'Find path' }));
    expect(await screen.findByRole('heading', { name: '2 steps' })).toBeVisible();
  });
});
