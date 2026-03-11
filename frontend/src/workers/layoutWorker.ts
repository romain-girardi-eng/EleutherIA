// frontend/src/workers/layoutWorker.ts
import forceAtlas2 from 'graphology-layout-forceatlas2';
import noverlap from 'graphology-layout-noverlap';
import type Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

export interface LayoutOptions {
  iterations?: number;
  gravity?: number;
  scalingRatio?: number;
  linLogMode?: boolean;
  barnesHutOptimize?: boolean;
  barnesHutTheta?: number;
  strongGravityMode?: boolean;
  slowDown?: number;
  noverlapIterations?: number;
}

const DEFAULTS: Required<LayoutOptions> = {
  iterations: 100,
  gravity: 1.0,
  scalingRatio: 2.0,
  linLogMode: true,
  barnesHutOptimize: true,
  barnesHutTheta: 0.5,
  strongGravityMode: false,
  slowDown: 10,
  noverlapIterations: 50,
};

/**
 * Run ForceAtlas2 layout synchronously on a Graphology graph.
 * Mutates node x/y attributes in place.
 */
export function computeLayout(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  options: LayoutOptions = {},
): void {
  if (graph.order === 0) return;

  const opts = { ...DEFAULTS, ...options };

  forceAtlas2.assign(graph, {
    iterations: opts.iterations,
    settings: {
      gravity: opts.gravity,
      scalingRatio: opts.scalingRatio,
      linLogMode: opts.linLogMode,
      barnesHutOptimize: opts.barnesHutOptimize,
      barnesHutTheta: opts.barnesHutTheta,
      strongGravityMode: opts.strongGravityMode,
      slowDown: opts.slowDown,
    },
  });

  if (opts.noverlapIterations > 0) {
    noverlap.assign(graph, {
      maxIterations: opts.noverlapIterations,
      settings: {
        ratio: 2.0,
        margin: 5,
      },
    });
  }

  // Sanitize: ForceAtlas2/noverlap can produce NaN for isolated nodes
  // or degenerate configurations. Sigma requires finite x/y for all nodes.
  graph.forEachNode((node) => {
    const x = graph.getNodeAttribute(node, 'x');
    const y = graph.getNodeAttribute(node, 'y');
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      graph.setNodeAttribute(node, 'x', Math.random() * 1000);
      graph.setNodeAttribute(node, 'y', Math.random() * 1000);
    }
  });
}
