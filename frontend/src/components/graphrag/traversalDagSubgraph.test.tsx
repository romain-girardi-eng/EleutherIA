import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import TraversalDAG from './TraversalDAG';
import type { GraphRAGResponse } from '../../types';

/**
 * The graph tab must render the CURATED subgraph the backend ships for an
 * answer — controversy frames, the positions clashing inside them, the
 * contested passages grounding those positions — not a flat dump of node ids.
 */

const response = (): GraphRAGResponse => ({
  query: 'Did Chrysippus have a notion of free will?',
  answer: 'answer',
  citations: { ancient_sources: [], modern_scholarship: [] },
  sources: [
    {
      id: 1,
      nodeId: 'person_bobzien',
      nodeLabel: 'Susanne Bobzien',
      nodeType: 'person',
      metadata: {},
    },
  ],
  reasoning_path: {
    starting_nodes: [],
    expanded_nodes: [],
    traversed_edges: [],
    total_nodes: 4,
    total_edges: 5,
    subgraph: {
      nodes: [
        {
          id: 'frame:f1',
          ref: 'debate_fate',
          label: 'Is assent up to us?',
          type: 'debate',
          origin: 'controversy_frame',
          root: true,
        },
        {
          id: 'pos:p_bobzien',
          ref: 'person_bobzien',
          label: 'Bobzien',
          type: 'person',
          origin: 'position',
          detail: 'Chrysippus has no notion of freedom of decision.',
        },
        {
          id: 'pos:p_frede',
          ref: 'person_frede',
          label: 'Frede',
          type: 'person',
          origin: 'position',
        },
        {
          id: 'passage_1',
          ref: 'passage_1',
          label: 'Epictetus 1.1.7',
          type: 'passage',
          origin: 'contested_passage',
        },
      ],
      edges: [
        { source: 'frame:f1', target: 'pos:p_bobzien', relation: 'has_position' },
        { source: 'frame:f1', target: 'pos:p_frede', relation: 'has_position' },
        { source: 'pos:p_frede', target: 'pos:p_bobzien', relation: 'opposes' },
        { source: 'pos:p_bobzien', target: 'passage_1', relation: 'grounded_in' },
      ],
      stats: {
        node_count: 4,
        edge_count: 4,
        frame_count: 1,
        position_count: 2,
        passage_count: 1,
        kg_node_count: 0,
        candidate_nodes: 4,
        candidate_edges: 4,
        truncated: false,
      },
    },
  },
  nodes_used: 4,
  edges_traversed: 5,
});

describe('TraversalDAG — curated answer subgraph', () => {
  /** Full node labels live in the hover <title>; the drawn <text> is clipped. */
  const hoverLabels = (container: HTMLElement) =>
    Array.from(container.querySelectorAll('title')).map((el) => el.textContent);

  it('renders the frame, its positions and the contested passage', () => {
    const { container } = render(
      <TraversalDAG
        response={response()}
        highlightedSourceIndex={null}
        onNodeSelect={() => {}}
      />,
    );

    const drawn = hoverLabels(container);
    expect(drawn).toContain('Is assent up to us?');
    expect(drawn).toContain(
      'Bobzien — Chrysippus has no notion of freedom of decision.',
    );
    expect(drawn).toContain('Frede');
    expect(drawn).toContain('Epictetus 1.1.7');

    // The map's own dialectical relation is on the wire, not "related".
    const relations = response().reasoning_path.subgraph!.edges.map((e) => e.relation);
    expect(relations).toContain('opposes');

    // 4 subgraph nodes + the question root, and every edge is drawn.
    const paths = container.querySelectorAll('path[marker-end]');
    // 4 curated edges + the query -> frame entry point.
    expect(paths.length).toBe(5);
  });

  it('counters match the rendered graph', () => {
    render(
      <TraversalDAG
        response={response()}
        highlightedSourceIndex={null}
        onNodeSelect={() => {}}
      />,
    );

    const counters = screen.getByTestId('traversal-dag-counters');
    expect(within(counters).getByText('4')).toBeInTheDocument(); // nodes
    expect(within(counters).getByText('5')).toBeInTheDocument(); // edges (+ query link)
    expect(within(counters).getByText('1')).toBeInTheDocument(); // fault lines
    expect(within(counters).getByText(/fault line/)).toBeInTheDocument();
  });

  it('opens the KG node behind a curated node on click', () => {
    const onNodeOpen = vi.fn();
    const onNodeSelect = vi.fn();
    render(
      <TraversalDAG
        response={response()}
        highlightedSourceIndex={null}
        onNodeSelect={onNodeSelect}
        onNodeOpen={onNodeOpen}
      />,
    );

    fireEvent.click(screen.getAllByText('Bobzien')[0].closest('g')!);

    // The position resolves to its holder's KG node id, not the graph-local id.
    expect(onNodeOpen).toHaveBeenCalledWith('person_bobzien');
    expect(onNodeSelect).toHaveBeenCalledWith('person_bobzien', 0);
  });

  it('falls back to the legacy reasoning path when no subgraph is shipped', () => {
    const legacy = response();
    delete legacy.reasoning_path.subgraph;
    legacy.reasoning_path.starting_nodes = [
      { id: 'concept_eph_hemin', label: "ἐφ' ἡμῖν", type: 'concept', reason: 'seed' },
    ];

    const { container } = render(
      <TraversalDAG
        response={legacy}
        highlightedSourceIndex={null}
        onNodeSelect={() => {}}
      />,
    );

    const drawn = hoverLabels(container);
    expect(drawn).toContain("ἐφ' ἡμῖν");
    expect(drawn).not.toContain('Is assent up to us?');
  });
});
