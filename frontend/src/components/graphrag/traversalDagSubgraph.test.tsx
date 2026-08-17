import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import TraversalDAG from './TraversalDAG';
import {
  layoutAnswerSubgraph,
  spreadAngles,
  wrapLabel,
  QUERY_NODE_ID,
  type RadialNode,
} from './answerSubgraphLayout';
import type { AnswerSubgraph, GraphRAGResponse } from '../../types';

/**
 * The graph tab must render the CURATED subgraph the backend ships for an
 * answer — real debate nodes, real position holders, and the contested
 * passages grounding them — as a radial fan. A rank
 * layout degenerates the common shape (one frame, dozens of positions) into
 * an unreadable single column, so the layout is deterministic polar maths and
 * is unit-tested as such.
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
          id: 'question',
          label: 'Did Chrysippus have a notion of free will?',
          type: 'question',
          origin: 'question_anchor',
          synthetic: true,
          root: true,
        },
        {
          id: 'debate_fate',
          label: 'Is assent up to us?',
          type: 'debate',
          origin: 'controversy_debate',
          root: true,
        },
        {
          id: 'person_bobzien',
          label: 'Susanne Bobzien',
          type: 'person',
          origin: 'position_holder',
          detail: 'Chrysippus has no notion of freedom of decision.',
        },
        {
          id: 'person_frede',
          label: 'Michael Frede',
          type: 'person',
          origin: 'position_holder',
        },
        {
          id: 'passage_1',
          label: 'Epictetus 1.1.7',
          type: 'passage',
          origin: 'contested_passage',
        },
      ],
      edges: [
        {
          source: 'question',
          target: 'debate_fate',
          relation: 'frames_question',
          origin: 'runtime_inference',
        },
        {
          source: 'debate_fate',
          target: 'person_bobzien',
          relation: 'has_position',
          origin: 'runtime_inference',
        },
        {
          source: 'person_frede',
          target: 'debate_fate',
          relation: 'responds_to',
          origin: 'kg',
        },
        {
          source: 'person_frede',
          target: 'person_bobzien',
          relation: 'opposes',
          origin: 'kg',
        },
        {
          source: 'person_bobzien',
          target: 'passage_1',
          relation: 'grounded_in',
          origin: 'kg',
        },
      ],
      stats: {
        node_count: 5,
        edge_count: 5,
        frame_count: 1,
        position_count: 2,
        passage_count: 1,
        kg_node_count: 0,
        candidate_nodes: 5,
        candidate_edges: 5,
        truncated: false,
      },
    },
  },
  nodes_used: 4,
  edges_traversed: 5,
});

/* ---------- layout fixtures ---------- */

/** Production shape that broke the rank layout: one frame, a long fan. */
function wideSubgraph(positionCount: number, frameCount = 1): AnswerSubgraph {
  const nodes: AnswerSubgraph['nodes'] = [
    {
      id: 'question',
      label: 'Is anything up to us?',
      type: 'question',
      origin: 'question_anchor',
      synthetic: true,
    },
  ];
  const edges: AnswerSubgraph['edges'] = [];

  for (let f = 0; f < frameCount; f += 1) {
    nodes.push({
      id: `debate_${f}`,
      label: `Fault line number ${f}`,
      type: 'debate',
      origin: 'controversy_debate',
      root: true,
    });
    edges.push({
      source: 'question',
      target: `debate_${f}`,
      relation: 'frames_question',
      origin: 'runtime_inference',
    });
  }

  for (let i = 0; i < positionCount; i += 1) {
    const frame = `debate_${i % frameCount}`;
    nodes.push({
      id: `person_${i}`,
      label: `Scholar number ${i}`,
      type: 'person',
      origin: 'position_holder',
    });
    edges.push({
      source: frame,
      target: `person_${i}`,
      relation: 'has_position',
      origin: 'runtime_inference',
    });

    if (i % 3 === 0) {
      nodes.push({
        id: `passage_${i}`,
        label: `Epictetus 1.${i}.7`,
        type: 'passage',
        origin: 'contested_passage',
      });
      edges.push({
        source: `person_${i}`,
        target: `passage_${i}`,
        relation: 'grounded_in',
        origin: 'kg',
      });
    }
    if (i > 0 && i % 5 === 0) {
      edges.push({
        source: `person_${i}`,
        target: `person_${i - 1}`,
        relation: 'opposes',
        origin: 'kg',
      });
    }
  }

  return { nodes, edges };
}

const layoutOf = (subgraph: AnswerSubgraph) =>
  layoutAnswerSubgraph(subgraph, { queryLabel: 'Is anything up to us?' });

const byId = (nodes: RadialNode[]) => new Map(nodes.map((node) => [node.id, node]));
const radiusOf = (node: RadialNode) => Math.hypot(node.x, node.y);
const angularGap = (a: number, b: number) => {
  let delta = a - b;
  while (delta > Math.PI) delta -= Math.PI * 2;
  while (delta < -Math.PI) delta += Math.PI * 2;
  return Math.abs(delta);
};

/* ---------- layout unit tests ---------- */

describe('layoutAnswerSubgraph — deterministic radial layout', () => {
  it('puts the question at the centre, frames on ring 1, positions on ring 2', () => {
    const layout = layoutOf(wideSubgraph(40));
    const nodes = byId(layout.nodes);

    const question = nodes.get(QUERY_NODE_ID)!;
    expect(question.x).toBe(0);
    expect(question.y).toBe(0);
    expect(question.tier).toBe('question');

    const frame = nodes.get('debate_0')!;
    expect(frame.tier).toBe('frame');
    // A single fault line is centred on 12 o'clock.
    expect(frame.x).toBeCloseTo(0, 5);
    expect(frame.y).toBeLessThan(0);

    const positions = layout.nodes.filter((node) => node.tier === 'position');
    expect(positions).toHaveLength(40);
    const positionRadii = positions.map(radiusOf);
    // Every position sits on one ring, strictly outside the frame ring.
    expect(Math.max(...positionRadii) - Math.min(...positionRadii)).toBeLessThan(0.5);
    expect(Math.min(...positionRadii)).toBeGreaterThan(radiusOf(frame));
  });

  it('fans the positions around the circle instead of stacking a column', () => {
    const layout = layoutOf(wideSubgraph(80));
    const positions = layout.nodes.filter((node) => node.tier === 'position');

    const xs = positions.map((node) => node.x);
    const ys = positions.map((node) => node.y);
    const width = Math.max(...xs) - Math.min(...xs);
    const height = Math.max(...ys) - Math.min(...ys);

    // The bug being fixed: dagre produced height ≫ width (one tall column).
    expect(width).toBeGreaterThan(200);
    expect(width / height).toBeGreaterThan(0.85);
    expect(width / height).toBeLessThan(1.2);

    // No two neighbours share an angle, and each owns readable arc length.
    const angles = positions.map((node) => node.angle).sort((a, b) => a - b);
    const ring = radiusOf(positions[0]);
    for (let i = 1; i < angles.length; i += 1) {
      expect((angles[i] - angles[i - 1]) * ring).toBeGreaterThan(10);
    }
  });

  it('groups positions in their own frame sector when several frames clash', () => {
    const layout = layoutOf(wideSubgraph(24, 3));
    const nodes = byId(layout.nodes);
    const frames = layout.nodes.filter((node) => node.tier === 'frame');
    expect(frames).toHaveLength(3);

    layout.nodes
      .filter((node) => node.tier === 'position')
      .forEach((position) => {
        const owner = nodes.get(position.groupId)!;
        const nearest = frames.reduce((best, frame) =>
          angularGap(position.angle, frame.angle) < angularGap(position.angle, best.angle)
            ? frame
            : best,
        );
        // A position never drifts into a neighbouring fault line's sector.
        expect(nearest.id).toBe(owner.id);
      });

    expect(layout.sectorBoundaries).toHaveLength(3);
  });

  it('hangs contested passages outward on their position ray', () => {
    const layout = layoutOf(wideSubgraph(40));
    const nodes = byId(layout.nodes);
    const passages = layout.nodes.filter((node) => node.tier === 'passage');
    expect(passages.length).toBeGreaterThan(0);

    passages.forEach((passage) => {
      const holderId = passage.id.replace('passage_', 'person_');
      const holder = nodes.get(holderId)!;
      expect(radiusOf(passage)).toBeGreaterThan(radiusOf(holder));
      expect(angularGap(passage.angle, holder.angle)).toBeLessThan(0.2);
      expect(passage.dotRadius).toBeLessThan(holder.dotRadius);
    });
  });

  it('parks unattached KG nodes on the corona next to what they connect to', () => {
    const subgraph = wideSubgraph(12);
    subgraph.nodes.push({
      id: 'concept_eph_hemin',
      ref: 'concept_eph_hemin',
      label: "ἐφ' ἡμῖν",
      type: 'concept',
      origin: 'activated',
    });
    subgraph.edges.push({
      source: 'person_3',
      target: 'concept_eph_hemin',
      relation: 'invokes',
    });

    const layout = layoutOf(subgraph);
    const nodes = byId(layout.nodes);
    const context = nodes.get('concept_eph_hemin')!;

    expect(context.tier).toBe('context');
    expect(radiusOf(context)).toBeGreaterThan(radiusOf(nodes.get('person_3')!));
    expect(angularGap(context.angle, nodes.get('person_3')!.angle)).toBeLessThan(0.2);
  });

  it('falls back to a plain fan around the question when no frame is shipped', () => {
    const layout = layoutAnswerSubgraph(
      {
        nodes: [
          { id: 'question', label: 'Fate?', type: 'question', origin: 'question_anchor', synthetic: true },
          { id: 'a', label: 'Alexander', type: 'person', origin: 'position_holder', root: true },
          { id: 'b', label: 'Chrysippus', type: 'person', origin: 'position_holder', root: true },
          { id: 'c', label: 'Fate', type: 'concept', origin: 'activated' },
        ],
        edges: [
          { source: 'question', target: 'a', relation: 'frames_question', origin: 'runtime_inference' },
          { source: 'question', target: 'b', relation: 'frames_question', origin: 'runtime_inference' },
          { source: 'a', target: 'c', relation: 'discusses', origin: 'kg' },
        ],
      },
      { queryLabel: 'Fate?' },
    );

    expect(layout.nodes.some((node) => node.tier === 'frame')).toBe(false);
    const ring = layout.nodes.filter((node) => node.tier === 'position');
    expect(ring.map((node) => node.id).sort()).toEqual(['a', 'b']);
    // Roots hang straight off the question when there is no fault line.
    expect(layout.edges.filter((edge) => edge.kind === 'entry')).toHaveLength(2);
  });

  it('keeps a KG-only retrieval connected as a plain star', () => {
    const layout = layoutAnswerSubgraph(
      {
        nodes: [
          { id: 'question', label: 'What is up to us?', type: 'question', origin: 'question_anchor', synthetic: true },
          { id: 'k0', label: "ἐφ' ἡμῖν", type: 'concept', origin: 'activated' },
          { id: 'k1', label: 'Chrysippus', type: 'person', origin: 'activated' },
          { id: 'k2', label: 'Cicero, De fato 40', type: 'passage', origin: 'activated' },
        ],
        edges: [
          { source: 'question', target: 'k0', relation: 'retrieved_for_question', origin: 'runtime_inference' },
          { source: 'question', target: 'k1', relation: 'retrieved_for_question', origin: 'runtime_inference' },
          { source: 'question', target: 'k2', relation: 'retrieved_for_question', origin: 'runtime_inference' },
        ],
      },
      { queryLabel: 'What is up to us?' },
    );

    expect(layout.nodes.filter((node) => node.tier === 'frame')).toHaveLength(0);
    expect(layout.edges).toHaveLength(3);
    expect(layout.edges.every((edge) => edge.kind === 'entry')).toBe(true);
    const radii = layout.nodes
      .filter((node) => node.id !== QUERY_NODE_ID)
      .map(radiusOf);
    expect(Math.min(...radii)).toBeGreaterThan(0);
    expect(Math.max(...radii) - Math.min(...radii)).toBeLessThan(0.5);
  });

  it('never lets a fault-line card sit on the question or on the ring', () => {
    // Two frames land east and west, straight across the question medallion.
    const layout = layoutOf(wideSubgraph(8, 2));
    const frames = layout.nodes.filter((node) => node.tier === 'frame');
    const ring = radiusOf(layout.nodes.find((node) => node.tier === 'position')!);

    frames.forEach((frame) => {
      const inner = radiusOf(frame) - frame.width / 2;
      const outer = radiusOf(frame) + frame.width / 2;
      expect(inner).toBeGreaterThan(100); // question medallion half-width
      expect(outer).toBeLessThan(ring);
    });

    // Opposition arcs hug the ring, so they clear the cards too.
    layout.edges
      .filter((edge) => edge.kind === 'opposition')
      .forEach((edge) => {
        expect(Math.hypot(edge.midX, edge.midY)).toBeGreaterThan(
          Math.max(...frames.map((frame) => radiusOf(frame) + frame.width / 2)),
        );
      });
  });

  it('marks opposition edges as chords and keeps containment quiet', () => {
    const layout = layoutOf(wideSubgraph(20));
    const opposition = layout.edges.filter((edge) => edge.kind === 'opposition');
    expect(opposition.length).toBeGreaterThan(0);
    opposition.forEach((edge) => {
      // A chord cuts across the ring: quadratic, not a radial cubic elbow.
      expect(edge.path).toContain('Q');
      expect(edge.color).toBe('#C1605F');
    });
    expect(layout.edges.some((edge) => edge.kind === 'containment')).toBe(true);
    expect(layout.edges.some((edge) => edge.kind === 'evidence')).toBe(true);
  });

  it('produces finite coordinates inside its own bounds, and is deterministic', () => {
    const layout = layoutOf(wideSubgraph(80));

    layout.nodes.forEach((node) => {
      expect(Number.isFinite(node.x)).toBe(true);
      expect(Number.isFinite(node.y)).toBe(true);
      expect(Number.isFinite(node.angle)).toBe(true);
      expect(node.x).toBeGreaterThanOrEqual(layout.bounds.minX);
      expect(node.x).toBeLessThanOrEqual(layout.bounds.maxX);
      expect(node.y).toBeGreaterThanOrEqual(layout.bounds.minY);
      expect(node.y).toBeLessThanOrEqual(layout.bounds.maxY);
    });
    layout.edges.forEach((edge) => {
      expect(edge.path).not.toContain('NaN');
      expect(Number.isFinite(edge.midX)).toBe(true);
      expect(Number.isFinite(edge.midY)).toBe(true);
    });

    // No simulation, no jitter: the same map always lands on the same pixels.
    expect(JSON.stringify(layoutOf(wideSubgraph(80)))).toBe(JSON.stringify(layout));
  });

  it('flips labels on the left half so nothing reads upside down', () => {
    const layout = layoutOf(wideSubgraph(40));
    layout.nodes
      .filter((node) => node.tier === 'position')
      .forEach((node) => {
        expect(node.flip).toBe(node.x < 0);
      });
  });
});

describe('answer subgraph text helpers', () => {
  it('wraps a label into at most the requested lines and marks the cut', () => {
    expect(wrapLabel('Is assent up to us?', 28, 2)).toEqual(['Is assent up to us?']);
    const wrapped = wrapLabel(
      'Whether the assent of the wise man is up to us or fated by antecedent causes',
      20,
      2,
    );
    expect(wrapped).toHaveLength(2);
    expect(wrapped[1].endsWith('…')).toBe(true);
  });

  it('pushes crowded angles apart while preserving order', () => {
    const spread = spreadAngles(
      [
        { id: 'a', angle: 0 },
        { id: 'b', angle: 0.01 },
        { id: 'c', angle: 0.02 },
      ],
      0.2,
    );
    const angles = ['a', 'b', 'c'].map((id) => spread.get(id)!);
    expect(angles[1] - angles[0]).toBeCloseTo(0.2, 6);
    expect(angles[2] - angles[1]).toBeCloseTo(0.2, 6);
  });
});

/* ---------- rendering ---------- */

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
      'Susanne Bobzien — Chrysippus has no notion of freedom of decision.',
    );
    expect(drawn).toContain('Michael Frede');
    expect(drawn).toContain('Epictetus 1.1.7');

    // Five serialized edges, including the explicit question anchor.
    expect(container.querySelectorAll('.subgraph-edge')).toHaveLength(5);
  });

  it('draws each tier with its own structural class', () => {
    const { container } = render(
      <TraversalDAG
        response={response()}
        highlightedSourceIndex={null}
        onNodeSelect={() => {}}
      />,
    );

    expect(container.querySelectorAll('.subgraph-node--question')).toHaveLength(1);
    expect(container.querySelectorAll('.subgraph-node--frame')).toHaveLength(1);
    expect(container.querySelectorAll('.subgraph-node--position')).toHaveLength(2);
    expect(container.querySelectorAll('.subgraph-node--passage')).toHaveLength(1);
    // The dialectic is the point: opposition is its own visible stroke.
    expect(container.querySelectorAll('.subgraph-edge--opposition')).toHaveLength(1);
    expect(container.querySelectorAll('.subgraph-edge--entry')).toHaveLength(1);
    expect(container.querySelectorAll('.subgraph-edge--containment')).toHaveLength(2);
    expect(container.querySelectorAll('.subgraph-edge--evidence')).toHaveLength(1);
    expect(container.querySelectorAll('.subgraph-edge--runtime-inference')).toHaveLength(2);
    // Guide rings orient the reader without adding ink to the nodes.
    expect(container.querySelectorAll('.subgraph-rings circle').length).toBeGreaterThan(0);
    expect(screen.getByTestId('traversal-dag-legend')).toBeInTheDocument();
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
    expect(within(counters).getByText(/fault line/)).toBeInTheDocument();
    expect(within(counters).getByText(/opposed/)).toBeInTheDocument();
    expect(within(counters).getAllByText('1')).toHaveLength(2); // 1 fault line, 1 opposed
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

    fireEvent.click(screen.getAllByText('Susanne Bobzien')[0].closest('g')!);

    // The holder id itself is now the real KG id.
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
    // The rank layout keeps its arrowheads; the radial scene is not mounted.
    expect(container.querySelectorAll('path[marker-end]').length).toBeGreaterThan(0);
    expect(container.querySelectorAll('.subgraph-node')).toHaveLength(0);
  });
});
