import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { StrictMode } from 'react';

import { apiClient } from '../api/client';
import ModeSwitcher from '../components/canvas/ModeSwitcher';
import {
  DEFAULT_GRAPH_WORKSPACE_STATE,
  deserializeGraphWorkspaceState,
  GraphWorkspaceProvider,
  graphWorkspaceReducer,
  normalizeGraphWorkspaceState,
  serializeGraphWorkspaceState,
  useGraphWorkspace,
  type GraphWorkspaceHistory,
} from './GraphWorkspaceContext';

vi.mock('../components/workspace/workspaceLoaders', () => ({
  preloadWorkspace: vi.fn(),
}));

describe('GraphWorkspace state', () => {
  it('normalizes comparison, time and filter invariants', () => {
    const normalized = normalizeGraphWorkspaceState({
      compareIds: ['a', 'b', 'a', 'c', 'd', 'e'],
      filters: {
        periods: ['Patristic', 'Classical Greek', 'Patristic'],
        types: ['concept', 'argument'],
        schools: [],
      },
      timeWindow: { start: 600, end: -500 },
    });

    expect(normalized.compareIds).toEqual(['a', 'b', 'c', 'd']);
    expect(normalized.filters.periods).toEqual(['Classical Greek', 'Patristic']);
    expect(normalized.timeWindow).toEqual({ start: -500, end: 600 });
  });

  it('round-trips a permalink without losing synchronized mode state', () => {
    const original = normalizeGraphWorkspaceState({
      ...DEFAULT_GRAPH_WORKSPACE_STATE,
      mode: 'scholar',
      releaseId: 'kg-sha256-release',
      primarySelection: 'concept_eph_hemin',
      compareIds: ['aristotle', 'chrysippus'],
      evidenceThread: ['claim', 'passage', 'edition'],
      filters: {
        types: ['argument', 'passage'],
        periods: ['Classical Greek'],
        schools: ['Peripatetics'],
      },
      timeWindow: { start: -450, end: 250 },
      cameraByMode: {
        atlas: { x: 12.5, y: -3, zoom: 2.25 },
        chronos: null,
        scholar: null,
      },
    });

    const serialized = serializeGraphWorkspaceState(original);
    expect(deserializeGraphWorkspaceState(serialized)).toEqual(original);
  });

  it('supports bounded undo and redo', () => {
    const initial: GraphWorkspaceHistory = {
      past: [],
      present: DEFAULT_GRAPH_WORKSPACE_STATE,
      future: [],
    };
    const chronos = graphWorkspaceReducer(initial, {
      type: 'commit',
      next: { ...DEFAULT_GRAPH_WORKSPACE_STATE, mode: 'chronos' },
    });
    const scholar = graphWorkspaceReducer(chronos, {
      type: 'commit',
      next: { ...chronos.present, mode: 'scholar' },
    });

    const undone = graphWorkspaceReducer(scholar, { type: 'undo' });
    expect(undone.present.mode).toBe('chronos');
    expect(graphWorkspaceReducer(undone, { type: 'redo' }).present.mode).toBe('scholar');
  });
});

function WorkspaceHarness() {
  const { state, error } = useGraphWorkspace();
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <ModeSwitcher />
      <output data-testid="mode">{state.mode}</output>
      <output data-testid="selection">{state.primarySelection ?? 'none'}</output>
      <output data-testid="search">{location.search}</output>
      <output data-testid="pathname">{location.pathname}</output>
      <output data-testid="error">{error?.message ?? 'none'}</output>
      <button type="button" onClick={() => navigate(-1)}>Browser back</button>
      <button type="button" onClick={() => navigate(1)}>Browser forward</button>
    </>
  );
}

function DetailHarness() {
  const { state, data, error, nodeDetailStates, ensureNodeDetail } = useGraphWorkspace();
  const detailState = nodeDetailStates.get('n1');
  return (
    <>
      <output data-testid="detail-release">{state.releaseId ?? 'loading'}</output>
      <output data-testid="detail">{data.rawById.get('n1')?.description ?? 'summary-only'}</output>
      <output data-testid="detail-error">{error?.message ?? 'none'}</output>
      <output data-testid="detail-loading">{detailState?.loading ? 'loading' : 'idle'}</output>
      <output data-testid="detail-local-error">{detailState?.error?.message ?? 'none'}</output>
      <button type="button" onClick={() => void ensureNodeDetail('n1')}>Load detail</button>
    </>
  );
}

describe('GraphWorkspace Provider navigation', () => {
  it('loads heavyweight editorial detail only on demand and pins it to the release', async () => {
    const user = userEvent.setup();
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode').mockResolvedValue({
      node: { id: 'n1', label: 'Node one', type: 'concept', description: 'Detail' },
      release_id: 'kg-sha256-detail',
      served_total_nodes: 1,
      served_total_edges: 0,
    });
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-detail',
    }));

    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <DetailHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('detail-release')).toHaveTextContent('kg-sha256-detail'));
    expect(screen.getByTestId('detail')).toHaveTextContent('summary-only');
    expect(detail).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Load detail' }));
    await waitFor(() => expect(screen.getByTestId('detail')).toHaveTextContent('Detail'));
    expect(detail).toHaveBeenCalledWith('n1', 'kg-sha256-detail');
    detail.mockRestore();
  });

  it('refuses a lazy node detail from a different release', async () => {
    const user = userEvent.setup();
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode').mockResolvedValue({
      node: { id: 'n1', label: 'Node one', type: 'concept', description: 'Wrong release' },
      release_id: 'kg-sha256-other',
      served_total_nodes: 1,
      served_total_edges: 0,
    });
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-expected',
    }));

    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <DetailHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('detail-release')).toHaveTextContent('kg-sha256-expected'));
    await user.click(screen.getByRole('button', { name: 'Load detail' }));
    await waitFor(() => expect(screen.getByTestId('detail-error')).toHaveTextContent(
      'will not silently substitute a different scholarly release',
    ));
    expect(screen.getByTestId('detail')).toHaveTextContent('summary-only');
    expect(detail).toHaveBeenCalledWith('n1', 'kg-sha256-expected');
    detail.mockRestore();
  });

  it('promotes the API 409 release-precondition rejection to a fatal mismatch', async () => {
    const user = userEvent.setup();
    const rejectedMismatch = Object.assign(new Error('Request failed with status code 409'), {
      isAxiosError: true,
      response: {
        status: 409,
        data: {
          detail: {
            code: 'kg_release_mismatch',
            requested_release_id: 'kg-sha256-expected',
            served_release_id: 'kg-sha256-other',
          },
        },
      },
    });
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode').mockRejectedValue(rejectedMismatch);
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-expected',
    }));

    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <DetailHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('detail-release')).toHaveTextContent('kg-sha256-expected'));
    await user.click(screen.getByRole('button', { name: 'Load detail' }));
    await waitFor(() => expect(screen.getByTestId('detail-error')).toHaveTextContent(
      'will not silently substitute a different scholarly release',
    ));
    expect(screen.getByTestId('detail-local-error')).toHaveTextContent('none');
    expect(screen.getByTestId('detail')).toHaveTextContent('summary-only');
    detail.mockRestore();
  });

  it('keeps ordinary lazy-detail failures local and retries without discarding the summary', async () => {
    const user = userEvent.setup();
    const detail = vi.spyOn(apiClient, 'getWorkspaceNode')
      .mockRejectedValueOnce(new Error('Request failed with status code 503'))
      .mockResolvedValueOnce({
        node: { id: 'n1', label: 'Node one', type: 'concept', description: 'Recovered detail' },
        release_id: 'kg-sha256-detail',
        served_total_nodes: 1,
        served_total_edges: 0,
      });
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-detail',
    }));

    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <DetailHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('detail-release')).toHaveTextContent('kg-sha256-detail'));
    await user.click(screen.getByRole('button', { name: 'Load detail' }));
    await waitFor(() => expect(screen.getByTestId('detail-local-error')).toHaveTextContent('503'));
    expect(screen.getByTestId('detail-error')).toHaveTextContent('none');
    expect(screen.getByTestId('detail')).toHaveTextContent('summary-only');

    await user.click(screen.getByRole('button', { name: 'Load detail' }));
    await waitFor(() => expect(screen.getByTestId('detail')).toHaveTextContent('Recovered detail'));
    expect(screen.getByTestId('detail-local-error')).toHaveTextContent('none');
    expect(detail).toHaveBeenCalledTimes(2);
    detail.mockRestore();
  });

  it('switches modes with browser back/forward without refetching the graph', async () => {
    const user = userEvent.setup();
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-test-release',
    }));

    render(
      <StrictMode>
        <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
          <Routes>
            <Route
              path="/visualizer"
              element={(
                <GraphWorkspaceProvider graphLoader={graphLoader}>
                  <WorkspaceHarness />
                </GraphWorkspaceProvider>
              )}
            />
          </Routes>
        </MemoryRouter>
      </StrictMode>,
    );

    await waitFor(() => expect(graphLoader).toHaveBeenCalledTimes(1));
    await user.click(screen.getByRole('tab', { name: /Chronos/ }));
    await waitFor(() => expect(screen.getByTestId('mode')).toHaveTextContent('chronos'));
    expect(screen.getByTestId('search')).toHaveTextContent('mode=chronos');

    await user.click(screen.getByRole('tab', { name: /Scholar/ }));
    await waitFor(() => expect(screen.getByTestId('mode')).toHaveTextContent('scholar'));
    expect(graphLoader).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Browser back' }));
    await waitFor(() => expect(screen.getByTestId('mode')).toHaveTextContent('chronos'));
    expect(graphLoader).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Browser forward' }));
    await waitFor(() => expect(screen.getByTestId('mode')).toHaveTextContent('scholar'));
    expect(graphLoader).toHaveBeenCalledTimes(1);
  });

  it('uses roving tab focus and arrow keys', async () => {
    const user = userEvent.setup();
    const graphLoader = vi.fn(async () => ({
      nodes: [],
      edges: [],
      release_id: 'kg-sha256-empty',
    }));
    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <ModeSwitcher />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    const atlas = screen.getByRole('tab', { name: /Atlas/ });
    expect(atlas).toHaveClass('min-h-11', 'px-2', 'sm:px-3');
    atlas.focus();
    await user.keyboard('{ArrowRight}');
    expect(screen.getByRole('tab', { name: /Chronos/ })).toHaveFocus();
    expect(screen.getByRole('tab', { name: /Chronos/ })).toHaveAttribute('aria-selected', 'true');
  });

  it('reserves Alt+Shift+number for modes without consuming skip-link Alt+number', async () => {
    const graphLoader = vi.fn(async () => ({
      nodes: [],
      edges: [],
      release_id: 'kg-sha256-empty',
    }));
    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <WorkspaceHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(graphLoader).toHaveBeenCalledTimes(1));
    fireEvent.keyDown(window, { key: '§', code: 'Digit3', altKey: true });
    expect(screen.getByTestId('mode')).toHaveTextContent('atlas');

    fireEvent.keyDown(window, {
      key: '§',
      code: 'Digit3',
      altKey: true,
      shiftKey: true,
    });
    await waitFor(() => expect(screen.getByTestId('mode')).toHaveTextContent('scholar'));
    expect(screen.getByRole('tab', { name: /Scholar/ })).toHaveAccessibleName(
      /Shortcut Alt\+Shift\+3/,
    );
  });

  it('preserves a public entity path while adding release-bound workspace state', async () => {
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'kg-sha256-node-route',
    }));
    render(
      <MemoryRouter initialEntries={['/visualizer/n1']}>
        <Routes>
          <Route path="/visualizer/:nodeId?" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <WorkspaceHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('selection')).toHaveTextContent('n1'));
    await waitFor(() => expect(screen.getByTestId('search')).toHaveTextContent('node=n1'));
    expect(screen.getByTestId('pathname')).toHaveTextContent('/visualizer/n1');
    expect(graphLoader).toHaveBeenCalledTimes(1);
  });

  it('fails closed instead of replaying a permalink on another graph release', async () => {
    const graphLoader = vi.fn(async () => ({
      nodes: [{ id: 'n1', label: 'Node one', type: 'concept' }],
      edges: [],
      release_id: 'served-release',
    }));
    render(
      <MemoryRouter initialEntries={['/visualizer?workspace=1&release=requested-release']}>
        <Routes>
          <Route path="/visualizer" element={(
            <GraphWorkspaceProvider graphLoader={graphLoader}>
              <WorkspaceHarness />
            </GraphWorkspaceProvider>
          )} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId('error')).toHaveTextContent(
      'will not silently substitute a different scholarly release',
    ));
    expect(screen.getByTestId('search')).toHaveTextContent('release=requested-release');
    expect(graphLoader).toHaveBeenCalledTimes(1);
  });
});
