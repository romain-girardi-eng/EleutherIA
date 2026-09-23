import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import type { AtlasEdgeMeta, AtlasNodeMeta } from './AtlasHelpers';
import KgFilters from './KgFilters';
import KgSearchBar from './KgSearchBar';
import PathFinder from './PathFinder';
import { facetCounts } from './filterFacets';

beforeAll(async () => {
  await i18next.use(initReactI18next).init({
    lng: 'en',
    resources: { en: { translation: { cosmograph: { explore: { inverse: { critiques: 'critiqued by' } } } } } },
    interpolation: { escapeValue: false },
  });
});

// Plain functions rather than vi.fn: a spied rejected promise is reported
// as unhandled even when the component awaits and catches it.
const pathCalls: unknown[] = [];
let pathResponses: Array<() => Promise<unknown>> = [];
vi.mock('../../api/client', () => ({
  apiClient: {
    computeGraphPath: (body: unknown) => {
      pathCalls.push(body);
      const next = pathResponses.length > 1 ? pathResponses.shift() : pathResponses[0];
      return next ? next() : new Promise(() => undefined);
    },
  },
}));
const respondWith = (...responses: Array<() => Promise<unknown>>) => {
  pathResponses = responses;
};

function node(partial: Partial<AtlasNodeMeta> & Pick<AtlasNodeMeta, 'id' | 'label'>): AtlasNodeMeta {
  return {
    type: 'concept',
    typeKey: 'concept',
    typeLabel: 'Concept',
    layer: 'ancient',
    periodLabel: 'Unspecified',
    schoolLabel: 'Unattached',
    degree: 1,
    importance: 1,
    color: '#000000',
    opacity: 1,
    size: 3,
    description: '',
    greekTerm: '',
    latinTerm: '',
    ...partial,
  };
}

const NODES: AtlasNodeMeta[] = [
  node({ id: 'chrysippus', label: 'Chrysippus of Soli', type: 'person', typeKey: 'person', degree: 300, periodLabel: 'Hellenistic', schoolLabel: 'Stoic' }),
  node({ id: 'fate', label: 'Fate', degree: 200, periodLabel: 'Hellenistic', schoolLabel: 'Stoic' }),
  node({ id: 'augustine', label: 'Augustine of Hippo', type: 'person', typeKey: 'person', degree: 250, periodLabel: 'Late Antiquity' }),
  node({ id: 'frede', label: 'Michael Frede', type: 'person', typeKey: 'person', layer: 'modern', degree: 40, periodLabel: 'Contemporary' }),
];

const EDGES: AtlasEdgeMeta[] = [
  { id: 'e1', source: 'chrysippus', target: 'fate', relation: 'discusses', relationLabel: 'Discusses', category: 'doctrinal', width: 1, opacity: 1, color: '#000' },
  { id: 'e2', source: 'augustine', target: 'fate', relation: 'critiques', relationLabel: 'Critiques', category: 'doctrinal', width: 1, opacity: 1, color: '#000' },
];

function renderSearch(onPick = vi.fn()) {
  render(
    <KgSearchBar
      placeholder="Search"
      nodes={NODES}
      onPick={onPick}
      ariaLabel="Search the graph"
      emptyLabel="Nothing found"
      resultsLabel="Results"
    />,
  );
  return { input: screen.getByRole('combobox', { name: 'Search the graph' }), onPick };
}

describe('KgSearchBar', () => {
  it('exposes the combobox pattern and suggests the most connected nodes on focus', () => {
    const { input } = renderSearch();
    expect(input).toHaveAttribute('aria-expanded', 'false');
    fireEvent.focus(input);
    expect(input).toHaveAttribute('aria-expanded', 'true');
    const listbox = screen.getByRole('listbox', { name: 'Results' });
    expect(input).toHaveAttribute('aria-controls', listbox.id);
    expect(within(listbox).getAllByRole('option')[0]).toHaveTextContent('Chrysippus of Soli');
  });

  it('filters, groups by kind and picks with the keyboard', async () => {
    const { input, onPick } = renderSearch();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'aug' } });
    await waitFor(() => {
      expect(screen.getAllByRole('option')).toHaveLength(1);
    });
    expect(screen.getByRole('group', { name: /person/i })).toBeInTheDocument();
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(input.getAttribute('aria-activedescendant')).toBeTruthy();
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ id: 'augustine' }));
    expect(input).toHaveAttribute('aria-expanded', 'false');
  });

  it('commits the best match when Enter beats the debounce', () => {
    const { input, onPick } = renderSearch();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'frede' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ id: 'frede' }));
  });

  it('shows the empty message and closes on Escape', async () => {
    const { input } = renderSearch();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'zzzz' } });
    await waitFor(() => expect(screen.getByRole('listbox')).toHaveTextContent('Nothing found'));
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input).toHaveAttribute('aria-expanded', 'false');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input).toHaveValue('');
  });
});

describe('facetCounts', () => {
  it('counts each facet against the other facets only', () => {
    const counts = facetCounts(NODES, { periods: ['Hellenistic'], types: [], schools: [] });
    expect(counts.visible).toBe(2);
    expect(counts.types.get('person')).toBe(1);
    // The period facet ignores its own selection.
    expect(counts.periods.get('Late Antiquity')).toBe(1);
    expect(counts.types.get('scholar')).toBeUndefined();
  });

  it('matches the modern layer when "scholar" is selected', () => {
    expect(facetCounts(NODES, { periods: [], types: ['scholar'], schools: [] }).visible).toBe(1);
  });
});

describe('KgFilters', () => {
  const labels = { period: 'Period', type: 'Type', school: 'School', clear: 'Clear filters' };

  it('toggles a chip and removes it from the active summary', () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <KgFilters state={{ periods: [], types: [], schools: [] }} nodes={NODES} onChange={onChange} labels={labels} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /^Stoic/ }));
    expect(onChange).toHaveBeenLastCalledWith({ periods: [], types: [], schools: ['Stoic'] });

    rerender(
      <KgFilters state={{ periods: [], types: [], schools: ['Stoic'] }} nodes={NODES} onChange={onChange} labels={labels} />,
    );
    expect(screen.getByRole('button', { name: /^Stoic/ })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Remove filter: Stoic' }));
    expect(onChange).toHaveBeenLastCalledWith({ periods: [], types: [], schools: [] });
    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }));
    expect(onChange).toHaveBeenLastCalledWith({ periods: [], types: [], schools: [] });
  });

  it('disables chips that would empty the view', () => {
    render(
      <KgFilters state={{ periods: ['Late Antiquity'], types: [], schools: [] }} nodes={NODES} onChange={vi.fn()} labels={labels} />,
    );
    expect(screen.getByRole('button', { name: /^Stoic/ })).toBeDisabled();
  });
});

describe('PathFinder', () => {
  const labels = {
    title: 'Find a path',
    description: 'Pick two nodes',
    sourcePlaceholder: 'Source',
    targetPlaceholder: 'Target',
    searchAriaLabel: 'Search a node',
    searchEmpty: 'Nothing',
    searchResults: 'Results',
    computing: 'Computing',
    noPath: 'No path',
    error: 'Could not compute path',
    pathLength: (n: number) => `${n} hops`,
    clear: 'Clear',
    swap: 'Swap source and target',
  };

  beforeEach(() => {
    pathCalls.length = 0;
    pathResponses = [];
  });

  function renderPath(overrides: Partial<Parameters<typeof PathFinder>[0]> = {}) {
    const props = {
      nodes: NODES,
      edges: EDGES,
      source: NODES[0],
      target: NODES[2],
      onSourceChange: vi.fn(),
      onTargetChange: vi.fn(),
      onPathComputed: vi.fn(),
      onNavigateToNode: vi.fn(),
      labels,
      ...overrides,
    };
    render(<PathFinder {...props} />);
    return props;
  }

  it('renders the path as a readable, clickable chain with oriented relations', async () => {
    respondWith(() => Promise.resolve({ path: ['chrysippus', 'fate', 'augustine'] }));
    const props = renderPath();
    expect(pathCalls).toEqual([{ source: 'chrysippus', target: 'augustine' }]);
    await screen.findByText('2 hops');
    expect(screen.getByText('Chrysippus of Soli discusses Fate')).toBeInTheDocument();
    // The second edge points backwards along the chain.
    expect(screen.getByText('Augustine of Hippo critiques Fate')).toBeInTheDocument();
    // ...and is shown top-down through its inverse verb.
    expect(screen.getByText('critiqued by')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^Fate/ }));
    expect(props.onNavigateToNode).toHaveBeenCalledWith('fate');
    expect(props.onPathComputed).toHaveBeenLastCalledWith(expect.objectContaining({ ids: ['chrysippus', 'fate', 'augustine'] }));
  });

  it('never invents a relation it cannot see', async () => {
    respondWith(() => Promise.resolve({ path: ['chrysippus', 'fate'] }));
    renderPath({ edges: [], target: NODES[1] });
    await screen.findByText('1 hops');
    expect(screen.queryByText(/related to/i)).not.toBeInTheDocument();
  });

  it('guides the reader when no path exists', async () => {
    respondWith(() => Promise.reject(new Error('404 Not Found')));
    const props = renderPath();
    await screen.findByText('No connection found');
    fireEvent.click(screen.getByRole('button', { name: 'Change target' }));
    expect(props.onTargetChange).toHaveBeenCalledWith(null);
  });

  it('offers a retry on a server error', async () => {
    respondWith(
      () => Promise.reject(new Error('500 boom')),
      () => Promise.resolve({ path: ['chrysippus', 'fate'] }),
    );
    renderPath({ target: NODES[1] });
    fireEvent.click(await screen.findByRole('button', { name: 'Try again' }));
    await screen.findByText('1 hops');
  });

  it('swaps the endpoints', () => {
    const props = renderPath();
    fireEvent.click(screen.getByRole('button', { name: 'Swap source and target' }));
    expect(props.onSourceChange).toHaveBeenCalledWith(NODES[2]);
    expect(props.onTargetChange).toHaveBeenCalledWith(NODES[0]);
  });
});
