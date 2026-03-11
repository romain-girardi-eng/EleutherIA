// frontend/src/workers/layoutWorkerEntry.ts
/// <reference lib="webworker" />
import Graph from 'graphology';
import { computeLayout } from './layoutWorker';
import type { LayoutOptions } from './layoutWorker';
import type { KGNodeAttributes, KGEdgeAttributes } from '../../types/sigma';

self.onmessage = (event: MessageEvent) => {
  const { type, payload } = event.data;

  if (type === 'run-layout') {
    const { nodes, edges, options } = payload as {
      nodes: [string, KGNodeAttributes][];
      edges: [string, string, string, KGEdgeAttributes][];
      options: LayoutOptions;
    };

    const graph = new Graph<KGNodeAttributes, KGEdgeAttributes>();

    for (const [key, attrs] of nodes) {
      graph.addNode(key, attrs);
    }
    for (const [key, source, target, attrs] of edges) {
      graph.addEdgeWithKey(key, source, target, attrs);
    }

    // Run all iterations at once (FA2 internal state doesn't survive between calls)
    computeLayout(graph, options);

    const positions: Record<string, { x: number; y: number }> = {};
    graph.forEachNode((node: string, attrs: KGNodeAttributes) => {
      positions[node] = { x: attrs.x, y: attrs.y };
    });

    self.postMessage({ type: 'layout-complete', positions });
  }
};
