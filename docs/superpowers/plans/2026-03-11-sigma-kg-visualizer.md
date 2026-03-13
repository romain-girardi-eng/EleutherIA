# Sigma.js KG Visualizer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unreadable Cosmograph KG visualizer with Sigma.js v3 + Graphology, adding passage aggregation, semantic zoom, community hulls, and smart edge filtering.

**Architecture:** API returns CytoscapeData → `graphologyAdapter` converts to Graphology graph → `aggregationService` collapses passages under works → Louvain community detection → ForceAtlas2 layout in Web Worker → Sigma.js renders with semantic zoom, edge filtering, and community hulls.

**Tech Stack:** Sigma.js v3, Graphology, @react-sigma/core, graphology-layout-forceatlas2, graphology-communities-louvain, graphology-layout-noverlap, d3-polygon (for hulls)

**Spec:** `docs/superpowers/specs/2026-03-11-sigma-kg-visualizer-design.md`

---

## File Structure

```
frontend/src/
  components/
    kg/
      SigmaKGVisualizer.tsx         — main React component (orchestrator)
      CommunityHullsLayer.tsx       — canvas overlay for convex hulls
      SemanticZoomController.ts     — 4-level zoom LOD logic
      EdgeFilterReducer.ts          — edge visibility by category + zoom
      NodeReducer.ts                — node visibility + styling by zoom
      PassageAggregation.ts         — passage collapse/expand logic
      NodeTooltip.tsx               — hover tooltip component
      DetailPanel.tsx               — click detail sidebar
      SearchBar.tsx                 — type-ahead node search
      KGLegend.tsx                  — node type legend
      KGControls.tsx                — zoom/fit/filter controls
  services/
    graphologyAdapter.ts            — CytoscapeData → Graphology conversion
  workers/
    layoutWorker.ts                 — ForceAtlas2 Web Worker
  types/
    sigma.ts                        — Sigma-specific type definitions
  pages/
    CosmographPage.tsx              — update imports (keep filename for route stability)
```

---

## Chunk 1: Foundation — Dependencies, Adapter, Layout Worker

### Task 1: Install Dependencies

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts:46-59` (update manual chunks)

- [ ] **Step 1: Install Sigma.js + Graphology packages**

```bash
cd frontend
npm install graphology graphology-types sigma @react-sigma/core \
  graphology-layout-forceatlas2 graphology-communities-louvain \
  graphology-layout-noverlap d3-polygon
```

- [ ] **Step 2: Remove Cosmograph + d3-force-webgpu**

```bash
cd frontend
npm uninstall @cosmograph/react d3-force-webgpu
```

- [ ] **Step 3: Update vite.config.ts manual chunks**

In `frontend/vite.config.ts`, replace the `cosmograph-vendor` chunk and add sigma:

```typescript
// Replace these lines in manualChunks (lines ~46-59):
'sigma-vendor': ['sigma', '@react-sigma/core', 'graphology'],
// Remove: 'cosmograph-vendor': ['@cosmograph/react'],
// Keep: 'three-vendor', 'charts-vendor', 'animation-vendor', 'react-vendor', 'ui-vendor'
```

Also remove `@cosmograph/react` from `optimizeDeps.include` (line ~23).

- [ ] **Step 4: Verify build compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds (existing Cosmograph imports will break — that's expected and fixed in Task 6).

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts
git commit -m "feat(frontend): add sigma.js + graphology deps, remove cosmograph"
```

---

### Task 2: Sigma Type Definitions

**Files:**
- Create: `frontend/src/types/sigma.ts`

- [ ] **Step 1: Write type definitions**

```typescript
// frontend/src/types/sigma.ts
import type { Attributes } from 'graphology-types';

/** Node attributes stored in the Graphology graph */
export interface KGNodeAttributes extends Attributes {
  label: string;
  type: string;
  x: number;
  y: number;
  size: number;
  color: string;
  period?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  community?: number;
  // Aggregation
  isAggregate?: boolean;
  passageCount?: number;
  passagesExpanded?: boolean;
  // Original data for detail panel
  originalId: string;
}

/** Edge attributes stored in the Graphology graph */
export interface KGEdgeAttributes extends Attributes {
  relation: string;
  category: EdgeCategory;
  description?: string;
  color?: string;
  size?: number;
}

/** Edge categories from ontology, driving visibility */
export type EdgeCategory =
  | 'argumentative'
  | 'intellectual'
  | 'doctrinal'
  | 'semantic'
  | 'structural'
  | 'authorship'
  | 'citation'
  | 'affiliation'
  | 'textual'
  | 'debate'
  | 'hermeneutic'
  | 'temporal';

/** Categories always visible past zoom level 1 */
export const ALWAYS_VISIBLE_CATEGORIES: EdgeCategory[] = [
  'argumentative',
  'intellectual',
  'doctrinal',
  'semantic',
];

/** Categories only visible on hover/select */
export const HOVER_ONLY_CATEGORIES: EdgeCategory[] = [
  'structural',
  'authorship',
  'citation',
  'affiliation',
  'textual',
  'debate',
  'hermeneutic',
  'temporal',
];

/** Zoom levels driven by camera.ratio */
export enum ZoomLevel {
  Overview = 1,      // ratio > 1.2
  Community = 2,     // 0.4 – 1.2
  Neighborhood = 3,  // 0.08 – 0.4
  Detail = 4,        // < 0.08
}

/** Map relation type → edge category (from knowledge graph/ontology/edge_types.json) */
export const RELATION_TO_CATEGORY: Record<string, EdgeCategory> = {
  // argumentative
  argues_for: 'argumentative',
  argues_against: 'argumentative',
  refutes: 'argumentative',
  responds_to: 'argumentative',
  supports: 'argumentative',
  critiques: 'argumentative',
  // intellectual
  influences: 'intellectual',
  influenced_by: 'intellectual',
  taught_by: 'intellectual',
  teaches: 'intellectual',
  student_of: 'intellectual',
  extends: 'intellectual',
  // affiliation
  belongs_to_school: 'affiliation',
  has_member: 'affiliation',
  member_of: 'affiliation',
  founded: 'affiliation',
  // authorship
  wrote: 'authorship',
  authored_by: 'authorship',
  created_by: 'authorship',
  developed_by: 'authorship',
  // citation
  cites: 'citation',
  cited_by: 'citation',
  source_for: 'citation',
  evidenced_by: 'citation',
  // textual
  preserves: 'textual',
  preserved_in: 'textual',
  translation_of: 'structural', // ontology categorizes as structural
  // structural
  contains: 'structural',
  part_of: 'structural',
  has_section: 'structural',
  has_chapter: 'structural',
  belongs_to_corpus: 'structural',
  // semantic
  discusses: 'semantic',
  discussed_in: 'semantic',
  defines: 'semantic',
  related_to: 'semantic',
  contrasts_with: 'semantic',
  parallel_to: 'semantic',
  employs: 'semantic',
  presupposes: 'semantic',
  grounded_in: 'semantic',
  // doctrinal
  holds_position: 'doctrinal',
  endorses: 'doctrinal',
  rejects: 'doctrinal',
  // debate
  participates_in: 'debate',
  contributes_to: 'debate',
  // hermeneutic
  interprets: 'hermeneutic',
  interpreted_by: 'hermeneutic',
  represents: 'hermeneutic',
  exemplifies: 'hermeneutic',
  specializes_in: 'hermeneutic',
  // temporal
  contemporary_of: 'temporal',
  precedes: 'temporal',
  follows: 'temporal',
};

/** Node type → base size (for Sigma rendering) */
export const TYPE_SIZES: Record<string, number> = {
  person: 11,
  school: 10,
  concept: 9,
  argument: 8,
  debate: 8,
  work: 8,
  event: 7,
  quote: 7,
  publication: 7,
  synthesis: 7,
  controversy: 7,
  reformulation: 6,
  conceptual_evolution: 6,
  group: 6,
  argument_framework: 6,
  passage: 4,
  default: 5,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/sigma.ts
git commit -m "feat(frontend): add Sigma.js type definitions with edge categories"
```

---

### Task 3: Graphology Adapter

**Files:**
- Create: `frontend/src/services/graphologyAdapter.ts`
- Test: `frontend/src/services/__tests__/graphologyAdapter.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/services/__tests__/graphologyAdapter.test.ts
import { describe, it, expect } from 'vitest';
import { buildGraph } from '../graphologyAdapter';
import type { CytoscapeData } from '@/types';

const mockCyData: CytoscapeData = {
  elements: {
    nodes: [
      { data: { id: 'person_chrysippus', label: 'Chrysippus', type: 'person' } },
      { data: { id: 'school_stoics', label: 'Stoics', type: 'school' } },
      { data: { id: 'work_de_fato', label: 'De Fato', type: 'work' } },
      { data: { id: 'passage_1', label: 'De Fato 1.1', type: 'passage' } },
      { data: { id: 'passage_2', label: 'De Fato 1.2', type: 'passage' } },
    ],
    edges: [
      { data: { id: 'e1', source: 'person_chrysippus', target: 'school_stoics', relation: 'member_of' } },
      { data: { id: 'e2', source: 'work_de_fato', target: 'passage_1', relation: 'contains' } },
      { data: { id: 'e3', source: 'work_de_fato', target: 'passage_2', relation: 'contains' } },
    ],
  },
};

describe('buildGraph', () => {
  it('converts CytoscapeData to Graphology graph', () => {
    const graph = buildGraph(mockCyData);
    expect(graph.order).toBe(5); // 5 nodes
    expect(graph.size).toBe(3);  // 3 edges
  });

  it('maps node attributes correctly', () => {
    const graph = buildGraph(mockCyData);
    const attrs = graph.getNodeAttributes('person_chrysippus');
    expect(attrs.label).toBe('Chrysippus');
    expect(attrs.type).toBe('person');
    expect(attrs.size).toBe(11); // person size from TYPE_SIZES
    expect(attrs.color).toBe('#6E85E9'); // person color from graphTheme
    expect(attrs.originalId).toBe('person_chrysippus');
  });

  it('maps edge category from relation', () => {
    const graph = buildGraph(mockCyData);
    const attrs = graph.getEdgeAttributes('e1');
    expect(attrs.relation).toBe('member_of');
    expect(attrs.category).toBe('affiliation');
  });

  it('defaults unknown relations to structural category', () => {
    const data: CytoscapeData = {
      elements: {
        nodes: [
          { data: { id: 'a', label: 'A', type: 'concept' } },
          { data: { id: 'b', label: 'B', type: 'concept' } },
        ],
        edges: [
          { data: { id: 'e', source: 'a', target: 'b', relation: 'unknown_relation' } },
        ],
      },
    };
    const graph = buildGraph(data);
    expect(graph.getEdgeAttributes('e').category).toBe('structural');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/services/__tests__/graphologyAdapter.test.ts
```

Expected: FAIL — `buildGraph` not found.

- [ ] **Step 3: Write the adapter**

```typescript
// frontend/src/services/graphologyAdapter.ts
import Graph from 'graphology';
import type { CytoscapeData } from '@/types';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';
import { RELATION_TO_CATEGORY, TYPE_SIZES } from '@/types/sigma';
import { getGraphTypeTheme } from '@/components/graphrag/graphTheme';

/**
 * Convert CytoscapeData from the API into a Graphology graph
 * with typed node/edge attributes ready for Sigma.js rendering.
 */
export function buildGraph(
  cyData: CytoscapeData,
): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const graph = new Graph<KGNodeAttributes, KGEdgeAttributes>();

  const nodes = cyData.elements?.nodes ?? [];
  const edges = cyData.elements?.edges ?? [];

  for (const node of nodes) {
    const { id, label, type, description, period, metadata, ...rest } = node.data;
    if (!id) continue;

    const nodeType = type ?? 'default';
    const theme = getGraphTypeTheme(nodeType);

    graph.addNode(id, {
      label: label ?? id,
      type: nodeType,
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      size: TYPE_SIZES[nodeType] ?? TYPE_SIZES.default,
      color: theme.color,
      period: period as string | undefined,
      description: description as string | undefined,
      metadata: (metadata as Record<string, unknown>) ?? undefined,
      originalId: id,
    });
  }

  for (const edge of edges) {
    const { id, source, target, relation, description } = edge.data;
    if (!source || !target) continue;
    if (!graph.hasNode(source) || !graph.hasNode(target)) continue;

    const rel = (relation as string) ?? 'related_to';
    const category = RELATION_TO_CATEGORY[rel] ?? 'structural';

    const edgeKey = id ?? `${source}-${rel}-${target}`;
    if (graph.hasEdge(edgeKey)) continue;

    graph.addEdgeWithKey(edgeKey, source, target, {
      relation: rel,
      category,
      description: description as string | undefined,
      size: 1,
    });
  }

  return graph;
}

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npx vitest run src/services/__tests__/graphologyAdapter.test.ts
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/graphologyAdapter.ts frontend/src/services/__tests__/graphologyAdapter.test.ts
git commit -m "feat(frontend): add graphologyAdapter to convert CytoscapeData to Graphology"
```

---

### Task 4: ForceAtlas2 Layout Worker

**Files:**
- Create: `frontend/src/workers/layoutWorker.ts`
- Test: `frontend/src/workers/__tests__/layoutWorker.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/workers/__tests__/layoutWorker.test.ts
import { describe, it, expect } from 'vitest';
import { computeLayout } from '../layoutWorker';
import Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeTestGraph(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  g.addNode('a', { label: 'A', type: 'person', x: 0, y: 0, size: 10, color: '#000', originalId: 'a' });
  g.addNode('b', { label: 'B', type: 'concept', x: 0, y: 0, size: 8, color: '#000', originalId: 'b' });
  g.addNode('c', { label: 'C', type: 'school', x: 0, y: 0, size: 9, color: '#000', originalId: 'c' });
  g.addEdge('a', 'b', { relation: 'discusses', category: 'semantic', size: 1 });
  g.addEdge('a', 'c', { relation: 'member_of', category: 'affiliation', size: 1 });
  return g;
}

describe('computeLayout', () => {
  it('assigns distinct positions to nodes', () => {
    const graph = makeTestGraph();
    computeLayout(graph, { iterations: 50 });

    const posA = { x: graph.getNodeAttribute('a', 'x'), y: graph.getNodeAttribute('a', 'y') };
    const posB = { x: graph.getNodeAttribute('b', 'x'), y: graph.getNodeAttribute('b', 'y') };

    // After layout, nodes should not all be at origin
    const dist = Math.sqrt((posA.x - posB.x) ** 2 + (posA.y - posB.y) ** 2);
    expect(dist).toBeGreaterThan(0.1);
  });

  it('does not throw for empty graph', () => {
    const graph = new Graph<KGNodeAttributes, KGEdgeAttributes>();
    expect(() => computeLayout(graph, { iterations: 10 })).not.toThrow();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/workers/__tests__/layoutWorker.test.ts
```

Expected: FAIL — `computeLayout` not found.

- [ ] **Step 3: Write the layout computation (synchronous, for testing)**

```typescript
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
  iterations: 500,
  gravity: 1.0,
  scalingRatio: 2.0,
  linLogMode: true,
  barnesHutOptimize: true,
  barnesHutTheta: 0.5,
  strongGravityMode: false,
  slowDown: 10,
  noverlapIterations: 300,
};

/**
 * Run ForceAtlas2 layout synchronously on a Graphology graph.
 * Mutates node x/y attributes in place.
 * In production this runs inside a Web Worker via the message handler below.
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

  // Post-process: push apart overlapping nodes
  if (opts.noverlapIterations > 0) {
    noverlap.assign(graph, {
      maxIterations: opts.noverlapIterations,
      ratio: 2.0,
      margin: 5,
    });
  }
}

// --- Web Worker message handler ---
// When loaded as a Worker, listens for serialized graph data and runs layout.
if (typeof self !== 'undefined' && typeof (self as any).WorkerGlobalScope !== 'undefined') {
  self.onmessage = (event: MessageEvent) => {
    const { type, payload } = event.data;

    if (type === 'run-layout') {
      const { nodes, edges, options } = payload;
      const Graph = require('graphology').default;
      const graph = new Graph();

      for (const [key, attrs] of nodes) {
        graph.addNode(key, attrs);
      }
      for (const [key, source, target, attrs] of edges) {
        graph.addEdgeWithKey(key, source, target, attrs);
      }

      computeLayout(graph, options);

      // Send back positions
      const positions: Record<string, { x: number; y: number }> = {};
      graph.forEachNode((node: string, attrs: any) => {
        positions[node] = { x: attrs.x, y: attrs.y };
      });

      self.postMessage({ type: 'layout-complete', positions });
    }
  };
}
```

Note: The Worker message handler uses dynamic `require` which won't work in Vite. In Step 5 we'll refactor it to use proper ES module import. For now the tests validate the synchronous `computeLayout` function.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npx vitest run src/workers/__tests__/layoutWorker.test.ts
```

Expected: Both tests PASS.

- [ ] **Step 5: Refactor worker for Vite compatibility**

Replace the `if (typeof self !== 'undefined' ...)` block with a proper Vite worker entry:

Create a separate file `frontend/src/workers/layoutWorkerEntry.ts`:

```typescript
// frontend/src/workers/layoutWorkerEntry.ts
import Graph from 'graphology';
import { computeLayout } from './layoutWorker';
import type { LayoutOptions } from './layoutWorker';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

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
```

Remove the worker message handler block from `layoutWorker.ts` (the `if (typeof self !== 'undefined'...)` block).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/workers/layoutWorker.ts frontend/src/workers/layoutWorkerEntry.ts \
       frontend/src/workers/__tests__/layoutWorker.test.ts
git commit -m "feat(frontend): add ForceAtlas2 layout worker with progress reporting"
```

---

### Task 5: Passage Aggregation Service

**Files:**
- Create: `frontend/src/components/kg/PassageAggregation.ts`
- Test: `frontend/src/components/kg/__tests__/PassageAggregation.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/components/kg/__tests__/PassageAggregation.test.ts
import { describe, it, expect } from 'vitest';
import Graph from 'graphology';
import { aggregatePassages, expandWorkPassages, collapseWorkPassages } from '../PassageAggregation';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeGraphWithPassages(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  g.addNode('work_1', { label: 'De Fato', type: 'work', x: 0, y: 0, size: 8, color: '#C79A31', originalId: 'work_1' });
  g.addNode('p1', { label: 'De Fato 1.1', type: 'passage', x: 1, y: 1, size: 4, color: '#8992A6', originalId: 'p1' });
  g.addNode('p2', { label: 'De Fato 1.2', type: 'passage', x: 2, y: 2, size: 4, color: '#8992A6', originalId: 'p2' });
  g.addNode('p3', { label: 'De Fato 2.1', type: 'passage', x: 3, y: 3, size: 4, color: '#8992A6', originalId: 'p3' });
  g.addNode('person_1', { label: 'Cicero', type: 'person', x: 5, y: 5, size: 11, color: '#6E85E9', originalId: 'person_1' });

  g.addEdgeWithKey('e1', 'work_1', 'p1', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e2', 'work_1', 'p2', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e3', 'work_1', 'p3', { relation: 'contains', category: 'structural', size: 1 });
  g.addEdgeWithKey('e4', 'person_1', 'work_1', { relation: 'wrote', category: 'authorship', size: 1 });

  return g;
}

describe('aggregatePassages', () => {
  it('hides passage nodes and updates work badge count', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);

    expect(hidden.size).toBe(3); // 3 passages hidden
    expect(graph.getNodeAttribute('work_1', 'passageCount')).toBe(3);
    expect(graph.getNodeAttribute('work_1', 'isAggregate')).toBe(true);
  });

  it('does not hide non-passage nodes', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);

    expect(hidden.has('person_1')).toBe(false);
    expect(hidden.has('work_1')).toBe(false);
  });
});

describe('expandWorkPassages', () => {
  it('restores hidden passages for a specific work', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);

    expect(hidden.has('p1')).toBe(true);

    const restored = expandWorkPassages(graph, 'work_1', hidden);
    expect(restored).toEqual(['p1', 'p2', 'p3']);
    expect(hidden.has('p1')).toBe(false);
    expect(graph.getNodeAttribute('work_1', 'passagesExpanded')).toBe(true);
  });
});

describe('collapseWorkPassages', () => {
  it('re-hides passages for a specific work', () => {
    const graph = makeGraphWithPassages();
    const hidden = aggregatePassages(graph);
    expandWorkPassages(graph, 'work_1', hidden);

    collapseWorkPassages(graph, 'work_1', hidden);
    expect(hidden.has('p1')).toBe(true);
    expect(hidden.has('p2')).toBe(true);
    expect(hidden.has('p3')).toBe(true);
    expect(graph.getNodeAttribute('work_1', 'passagesExpanded')).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/components/kg/__tests__/PassageAggregation.test.ts
```

Expected: FAIL — imports not found.

- [ ] **Step 3: Write the aggregation service**

```typescript
// frontend/src/components/kg/PassageAggregation.ts
import type Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

/**
 * Hide all passage nodes, recording them in a Set.
 * Updates parent work nodes with passageCount and isAggregate flags.
 * Returns the set of hidden node IDs (used by node reducer to skip rendering).
 */
export function aggregatePassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
): Set<string> {
  const hidden = new Set<string>();
  const workPassageCounts = new Map<string, number>();

  // Find all passage nodes and their parent works
  graph.forEachNode((nodeId, attrs) => {
    if (attrs.type !== 'passage') return;

    hidden.add(nodeId);

    // Find parent work via incoming 'contains' edge
    graph.forEachInEdge(nodeId, (_edgeId, edgeAttrs, sourceId, _targetId, sourceAttrs) => {
      if (edgeAttrs.relation === 'contains' && sourceAttrs.type === 'work') {
        workPassageCounts.set(sourceId, (workPassageCounts.get(sourceId) ?? 0) + 1);
      }
    });
  });

  // Also check outgoing 'part_of' edges (inverse of contains)
  graph.forEachNode((nodeId, attrs) => {
    if (attrs.type !== 'passage' || !hidden.has(nodeId)) return;

    graph.forEachOutEdge(nodeId, (_edgeId, edgeAttrs, _sourceId, targetId, targetAttrs) => {
      if (edgeAttrs.relation === 'part_of' && targetAttrs.type === 'work') {
        if (!workPassageCounts.has(targetId)) {
          workPassageCounts.set(targetId, 0);
        }
        workPassageCounts.set(targetId, workPassageCounts.get(targetId)! + 1);
      }
    });
  });

  // Update work nodes
  for (const [workId, count] of workPassageCounts) {
    graph.setNodeAttribute(workId, 'passageCount', count);
    graph.setNodeAttribute(workId, 'isAggregate', true);
    graph.setNodeAttribute(workId, 'passagesExpanded', false);
  }

  return hidden;
}

/**
 * Expand passages for a specific work node.
 * Removes them from the hidden set and positions them radially.
 */
export function expandWorkPassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  workId: string,
  hidden: Set<string>,
): string[] {
  const workX = graph.getNodeAttribute(workId, 'x');
  const workY = graph.getNodeAttribute(workId, 'y');
  const restored: string[] = [];

  // Find passages belonging to this work
  graph.forEachOutEdge(workId, (_edgeId, edgeAttrs, _sourceId, targetId, targetAttrs) => {
    if (edgeAttrs.relation === 'contains' && targetAttrs.type === 'passage' && hidden.has(targetId)) {
      restored.push(targetId);
    }
  });

  // Position radially around work
  const count = restored.length;
  const radius = Math.min(80 * Math.sqrt(count / 10), 200);

  restored.forEach((nodeId, i) => {
    const angle = (2 * Math.PI * i) / count;
    graph.setNodeAttribute(nodeId, 'x', workX + radius * Math.cos(angle));
    graph.setNodeAttribute(nodeId, 'y', workY + radius * Math.sin(angle));
    hidden.delete(nodeId);
  });

  graph.setNodeAttribute(workId, 'passagesExpanded', true);
  return restored;
}

/**
 * Collapse passages for a specific work node.
 * Adds them back to the hidden set.
 */
export function collapseWorkPassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  workId: string,
  hidden: Set<string>,
): void {
  graph.forEachOutEdge(workId, (_edgeId, edgeAttrs, _sourceId, targetId, targetAttrs) => {
    if (edgeAttrs.relation === 'contains' && targetAttrs.type === 'passage') {
      hidden.add(targetId);
    }
  });

  graph.setNodeAttribute(workId, 'passagesExpanded', false);
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npx vitest run src/components/kg/__tests__/PassageAggregation.test.ts
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/kg/PassageAggregation.ts \
       frontend/src/components/kg/__tests__/PassageAggregation.test.ts
git commit -m "feat(frontend): add passage aggregation with expand/collapse"
```

---

### Task 6: Community Detection Service

**Files:**
- Create: `frontend/src/services/communityDetection.ts`
- Test: `frontend/src/services/__tests__/communityDetection.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/services/__tests__/communityDetection.test.ts
import { describe, it, expect } from 'vitest';
import Graph from 'graphology';
import { detectCommunities } from '../communityDetection';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

function makeTwoClusterGraph(): Graph<KGNodeAttributes, KGEdgeAttributes> {
  const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
  // Cluster 1: tightly connected
  const attrs = (label: string) => ({ label, type: 'person' as const, x: 0, y: 0, size: 10, color: '#000', originalId: label });
  g.addNode('a', attrs('A'));
  g.addNode('b', attrs('B'));
  g.addNode('c', attrs('C'));
  g.addEdge('a', 'b', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('b', 'c', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('a', 'c', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  // Cluster 2: tightly connected
  g.addNode('d', attrs('D'));
  g.addNode('e', attrs('E'));
  g.addNode('f', attrs('F'));
  g.addEdge('d', 'e', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('e', 'f', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  g.addEdge('d', 'f', { relation: 'influences', category: 'intellectual' as const, size: 1 });
  // Weak cross-cluster link
  g.addEdge('c', 'd', { relation: 'responds_to', category: 'argumentative' as const, size: 1 });
  return g;
}

describe('detectCommunities', () => {
  it('assigns community attribute to all nodes', () => {
    const graph = makeTwoClusterGraph();
    const communities = detectCommunities(graph);

    graph.forEachNode((nodeId) => {
      expect(graph.getNodeAttribute(nodeId, 'community')).toBeDefined();
    });
    expect(communities.size).toBeGreaterThanOrEqual(1);
  });

  it('falls back to type-based communities for degenerate results', () => {
    // Single node = degenerate
    const g = new Graph<KGNodeAttributes, KGEdgeAttributes>();
    g.addNode('a', { label: 'A', type: 'person', x: 0, y: 0, size: 10, color: '#000', originalId: 'a' });
    const communities = detectCommunities(g);
    expect(communities.size).toBe(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/services/__tests__/communityDetection.test.ts
```

Expected: FAIL.

- [ ] **Step 3: Write the community detection service**

```typescript
// frontend/src/services/communityDetection.ts
import louvain from 'graphology-communities-louvain';
import type Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

/**
 * Run Louvain community detection on the graph.
 * Assigns a `community` number attribute to each node.
 * Returns a Map of community ID → set of node IDs.
 *
 * Falls back to type-based grouping if Louvain produces degenerate results
 * (1 community or > 50% of nodes are their own community).
 */
export function detectCommunities(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
): Map<number, Set<string>> {
  if (graph.order === 0) return new Map();

  let useLouvain = true;

  if (graph.order <= 1 || graph.size === 0) {
    useLouvain = false;
  }

  if (useLouvain) {
    try {
      const communities = louvain.assign(graph, { resolution: 1.0 });
      // Check for degenerate results
      const communitySet = new Set<number>();
      graph.forEachNode((_nodeId, attrs) => {
        communitySet.add(attrs.community as number);
      });

      if (communitySet.size <= 1 || communitySet.size > graph.order * 0.5) {
        useLouvain = false;
      }
    } catch {
      useLouvain = false;
    }
  }

  if (!useLouvain) {
    // Fallback: group by node type
    const typeIndex = new Map<string, number>();
    let nextId = 0;
    graph.forEachNode((nodeId, attrs) => {
      const t = attrs.type ?? 'default';
      if (!typeIndex.has(t)) typeIndex.set(t, nextId++);
      graph.setNodeAttribute(nodeId, 'community', typeIndex.get(t)!);
    });
  }

  // Build community map
  const result = new Map<number, Set<string>>();
  graph.forEachNode((nodeId, attrs) => {
    const c = attrs.community as number;
    if (!result.has(c)) result.set(c, new Set());
    result.get(c)!.add(nodeId);
  });

  return result;
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npx vitest run src/services/__tests__/communityDetection.test.ts
```

Expected: Both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/communityDetection.ts \
       frontend/src/services/__tests__/communityDetection.test.ts
git commit -m "feat(frontend): add Louvain community detection with type-based fallback"
```

---

## Chunk 2: Rendering — Sigma Components

### Task 7: Semantic Zoom Controller

**Files:**
- Create: `frontend/src/components/kg/SemanticZoomController.ts`
- Test: `frontend/src/components/kg/__tests__/SemanticZoomController.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/components/kg/__tests__/SemanticZoomController.test.ts
import { describe, it, expect } from 'vitest';
import { getZoomLevel, shouldShowNode, shouldShowEdge } from '../SemanticZoomController';
import { ZoomLevel } from '@/types/sigma';

describe('getZoomLevel', () => {
  it('returns Overview for ratio > 1.2', () => {
    expect(getZoomLevel(1.5)).toBe(ZoomLevel.Overview);
    expect(getZoomLevel(2.0)).toBe(ZoomLevel.Overview);
  });

  it('returns Community for ratio 0.4 - 1.2', () => {
    expect(getZoomLevel(0.8)).toBe(ZoomLevel.Community);
    expect(getZoomLevel(0.4)).toBe(ZoomLevel.Community);
  });

  it('returns Neighborhood for ratio 0.08 - 0.4', () => {
    expect(getZoomLevel(0.2)).toBe(ZoomLevel.Neighborhood);
  });

  it('returns Detail for ratio < 0.08', () => {
    expect(getZoomLevel(0.05)).toBe(ZoomLevel.Detail);
  });
});

describe('shouldShowNode', () => {
  it('hides passages at Overview', () => {
    expect(shouldShowNode('passage', ZoomLevel.Overview, 5, false)).toBe(false);
  });

  it('shows high-degree nodes at Overview', () => {
    expect(shouldShowNode('person', ZoomLevel.Overview, 10, false)).toBe(true);
  });

  it('shows all non-passage nodes at Community', () => {
    expect(shouldShowNode('concept', ZoomLevel.Community, 1, false)).toBe(true);
  });

  it('shows passages at Detail', () => {
    expect(shouldShowNode('passage', ZoomLevel.Detail, 1, false)).toBe(true);
  });
});

describe('shouldShowEdge', () => {
  it('hides all edges at Overview', () => {
    expect(shouldShowEdge('argumentative', ZoomLevel.Overview, false)).toBe(false);
  });

  it('shows argumentative edges at Community', () => {
    expect(shouldShowEdge('argumentative', ZoomLevel.Community, false)).toBe(true);
  });

  it('hides structural edges at Community without hover', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Community, false)).toBe(false);
  });

  it('shows structural edges at Community on hover', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Community, true)).toBe(true);
  });

  it('shows all edges at Detail', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Detail, false)).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/components/kg/__tests__/SemanticZoomController.test.ts
```

- [ ] **Step 3: Implement**

```typescript
// frontend/src/components/kg/SemanticZoomController.ts
import { ZoomLevel, ALWAYS_VISIBLE_CATEGORIES, type EdgeCategory } from '@/types/sigma';

const OVERVIEW_MIN_DEGREE = 5;

export function getZoomLevel(cameraRatio: number): ZoomLevel {
  if (cameraRatio > 1.2) return ZoomLevel.Overview;
  if (cameraRatio >= 0.4) return ZoomLevel.Community;
  if (cameraRatio >= 0.08) return ZoomLevel.Neighborhood;
  return ZoomLevel.Detail;
}

/**
 * Whether a node should be rendered at the current zoom level.
 * @param nodeType - The node's type attribute
 * @param zoom - Current zoom level
 * @param degree - Node's degree (number of edges)
 * @param isExpanded - Whether this passage's parent work is expanded
 */
export function shouldShowNode(
  nodeType: string,
  zoom: ZoomLevel,
  degree: number,
  isExpanded: boolean,
): boolean {
  if (zoom === ZoomLevel.Detail) return true;

  if (nodeType === 'passage') {
    // Passages only visible at Neighborhood (if expanded) or Detail
    if (zoom === ZoomLevel.Neighborhood) return isExpanded;
    return false;
  }

  if (zoom === ZoomLevel.Overview) {
    // Only show nodes with enough connections to be meaningful
    return degree >= OVERVIEW_MIN_DEGREE;
  }

  // Community and Neighborhood: show all non-passage nodes
  return true;
}

/**
 * Whether an edge should be rendered at the current zoom level.
 * @param category - The edge's category
 * @param zoom - Current zoom level
 * @param isHovered - Whether source or target node is hovered/selected
 */
export function shouldShowEdge(
  category: EdgeCategory,
  zoom: ZoomLevel,
  isHovered: boolean,
): boolean {
  if (zoom === ZoomLevel.Overview) return false;
  if (zoom === ZoomLevel.Detail) return true;

  // Community and Neighborhood: always-visible categories show, hover-only on hover
  if (ALWAYS_VISIBLE_CATEGORIES.includes(category)) return true;
  return isHovered;
}

/**
 * Hull opacity based on camera ratio.
 * Fully opaque at ratio >= 1.2, fades out at 0.4, gone below 0.4.
 */
export function getHullOpacity(cameraRatio: number): number {
  if (cameraRatio >= 1.2) return 0.15;
  if (cameraRatio < 0.4) return 0;
  // Linear fade from 0.15 to 0 between 1.2 and 0.4
  return 0.15 * ((cameraRatio - 0.4) / 0.8);
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && npx vitest run src/components/kg/__tests__/SemanticZoomController.test.ts
```

Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/kg/SemanticZoomController.ts \
       frontend/src/components/kg/__tests__/SemanticZoomController.test.ts
git commit -m "feat(frontend): add semantic zoom controller with 4-level LOD"
```

---

### Task 8: Edge Filter Reducer

**Files:**
- Create: `frontend/src/components/kg/EdgeFilterReducer.ts`

- [ ] **Step 1: Write the reducer**

This is a Sigma.js `edgeReducer` function — it receives edge key + attributes and returns visual overrides.

```typescript
// frontend/src/components/kg/EdgeFilterReducer.ts
import type { KGEdgeAttributes } from '@/types/sigma';
import { shouldShowEdge } from './SemanticZoomController';
import type { ZoomLevel } from '@/types/sigma';

export interface EdgeReducerState {
  zoomLevel: ZoomLevel;
  hoveredNode: string | null;
  selectedNode: string | null;
  hiddenNodes: Set<string>;
}

/**
 * Create a Sigma edge reducer that filters edges by category and zoom level.
 * Returns a function compatible with Sigma's `edgeReducer` prop.
 */
export function createEdgeReducer(state: EdgeReducerState) {
  return (
    edge: string,
    data: KGEdgeAttributes & { source: string; target: string },
  ): Partial<KGEdgeAttributes> & { hidden?: boolean } => {
    const { zoomLevel, hoveredNode, selectedNode, hiddenNodes } = state;

    // Hide edges connected to hidden nodes
    if (hiddenNodes.has(data.source) || hiddenNodes.has(data.target)) {
      return { hidden: true };
    }

    const isHovered =
      hoveredNode === data.source ||
      hoveredNode === data.target ||
      selectedNode === data.source ||
      selectedNode === data.target;

    if (!shouldShowEdge(data.category, zoomLevel, isHovered)) {
      return { hidden: true };
    }

    // Dim edges not connected to hovered node (when something is hovered)
    if (hoveredNode && !isHovered) {
      return { color: 'rgba(255,255,255,0.05)', size: 0.5 };
    }

    return {};
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/kg/EdgeFilterReducer.ts
git commit -m "feat(frontend): add edge filter reducer for Sigma.js"
```

---

### Task 9: Node Reducer

**Files:**
- Create: `frontend/src/components/kg/NodeReducer.ts`

- [ ] **Step 1: Write the reducer**

```typescript
// frontend/src/components/kg/NodeReducer.ts
import type { KGNodeAttributes } from '@/types/sigma';
import { shouldShowNode } from './SemanticZoomController';
import type { ZoomLevel } from '@/types/sigma';

export interface NodeReducerState {
  zoomLevel: ZoomLevel;
  hoveredNode: string | null;
  selectedNode: string | null;
  hiddenNodes: Set<string>;
  nodeDegrees: Map<string, number>;
  expandedWorks: Set<string>;
  hoveredNeighbors: Set<string>; // pre-computed neighbors of hoveredNode
}

/**
 * Create a Sigma node reducer that controls visibility and styling by zoom level.
 */
export function createNodeReducer(state: NodeReducerState) {
  return (
    node: string,
    data: KGNodeAttributes,
  ): Partial<KGNodeAttributes> & { hidden?: boolean } => {
    const { zoomLevel, hoveredNode, selectedNode, hiddenNodes, nodeDegrees, expandedWorks, hoveredNeighbors } = state;

    // Hidden by passage aggregation
    if (hiddenNodes.has(node)) {
      return { hidden: true };
    }

    const degree = nodeDegrees.get(node) ?? 0;
    const isExpanded = data.type === 'passage' && expandedWorks.size > 0;

    if (!shouldShowNode(data.type, zoomLevel, degree, isExpanded)) {
      return { hidden: true };
    }

    // Highlight hovered/selected
    if (node === hoveredNode || node === selectedNode) {
      return { zIndex: 2, forceLabel: true };
    }

    // Dim non-neighbors when something is hovered (but keep neighbors bright)
    if (hoveredNode) {
      if (hoveredNeighbors.has(node)) {
        return { forceLabel: true }; // neighbor: keep visible with label
      }
      return { color: 'rgba(255,255,255,0.1)', label: '' };
    }

    // Work nodes with aggregated passages: append count to label
    if (data.isAggregate && !data.passagesExpanded && data.passageCount) {
      return { label: `${data.label} (${data.passageCount})` };
    }

    return {};
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/kg/NodeReducer.ts
git commit -m "feat(frontend): add node reducer for Sigma.js with aggregation labels"
```

---

### Task 10: Community Hulls Canvas Layer

**Files:**
- Create: `frontend/src/components/kg/CommunityHullsLayer.tsx`

- [ ] **Step 1: Write the hull layer component**

```tsx
// frontend/src/components/kg/CommunityHullsLayer.tsx
import { useEffect, useRef, useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { polygonHull } from 'd3-polygon';
import { getHullOpacity } from './SemanticZoomController';
import type { KGNodeAttributes } from '@/types/sigma';

interface CommunityHullsLayerProps {
  communities: Map<number, Set<string>>;
  communityColors: Map<number, string>;
  communityLabels: Map<number, string>;
}

// Pad hull points outward for visual breathing room
function padHull(points: [number, number][], padding: number): [number, number][] {
  if (points.length < 3) return points;
  const cx = points.reduce((s, p) => s + p[0], 0) / points.length;
  const cy = points.reduce((s, p) => s + p[1], 0) / points.length;
  return points.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d === 0) return [x, y] as [number, number];
    return [x + (dx / d) * padding, y + (dy / d) * padding] as [number, number];
  });
}

export default function CommunityHullsLayer({
  communities,
  communityColors,
  communityLabels,
}: CommunityHullsLayerProps) {
  const sigma = useSigma();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const camera = sigma.getCamera();
    const ratio = camera.ratio;
    const opacity = getHullOpacity(ratio);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (opacity <= 0) return;

    for (const [communityId, nodeIds] of communities) {
      if (nodeIds.size < 3) continue;

      const points: [number, number][] = [];
      for (const nodeId of nodeIds) {
        try {
          const attrs = sigma.getGraph().getNodeAttributes(nodeId);
          const pos = sigma.graphToViewport({ x: attrs.x as number, y: attrs.y as number });
          points.push([pos.x, pos.y]);
        } catch {
          // Node may be hidden
        }
      }

      if (points.length < 3) continue;

      const hull = polygonHull(points);
      if (!hull) continue;

      const padded = padHull(hull, 30);
      const color = communityColors.get(communityId) ?? 'rgba(255,255,255,0.1)';

      ctx.beginPath();
      ctx.moveTo(padded[0][0], padded[0][1]);
      for (let i = 1; i < padded.length; i++) {
        ctx.lineTo(padded[i][0], padded[i][1]);
      }
      ctx.closePath();
      ctx.fillStyle = color.replace(/[\d.]+\)$/, `${opacity})`);
      ctx.fill();
      ctx.strokeStyle = color.replace(/[\d.]+\)$/, `${opacity * 2})`);
      ctx.lineWidth = 1;
      ctx.stroke();

      // Community label at centroid
      if (ratio > 0.6) {
        const cx = padded.reduce((s, p) => s + p[0], 0) / padded.length;
        const cy = padded.reduce((s, p) => s + p[1], 0) / padded.length;
        const label = communityLabels.get(communityId);
        if (label) {
          ctx.font = `${Math.max(12, 16 / ratio)}px sans-serif`;
          ctx.fillStyle = `rgba(255,255,255,${Math.min(opacity * 4, 0.8)})`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(label, cx, cy);
        }
      }
    }
  }, [sigma, communities, communityColors, communityLabels]);

  useEffect(() => {
    // Create canvas overlay behind Sigma
    const container = sigma.getContainer();
    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    container.style.position = 'relative';
    container.insertBefore(canvas, container.firstChild);
    canvasRef.current = canvas;

    const resizeObserver = new ResizeObserver(() => {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
      draw();
    });
    resizeObserver.observe(container);

    // Redraw on camera updates
    const camera = sigma.getCamera();
    camera.on('updated', draw);

    return () => {
      camera.removeListener('updated', draw);
      resizeObserver.disconnect();
      canvas.remove();
    };
  }, [sigma, draw]);

  useEffect(() => {
    draw();
  }, [draw]);

  return null;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/kg/CommunityHullsLayer.tsx
git commit -m "feat(frontend): add community hulls canvas overlay for Sigma.js"
```

---

### Task 11: Main SigmaKGVisualizer Component

**Files:**
- Create: `frontend/src/components/kg/SigmaKGVisualizer.tsx`

This is the orchestrator component. It wires together all the pieces.

- [ ] **Step 1: Write the component**

```tsx
// frontend/src/components/kg/SigmaKGVisualizer.tsx
import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import Graph from 'graphology';
import { SigmaContainer, useRegisterEvents, useSigma } from '@react-sigma/core';
import '@react-sigma/core/lib/style.css';

import { buildGraph } from '@/services/graphologyAdapter';
import { detectCommunities } from '@/services/communityDetection';
import { aggregatePassages, expandWorkPassages, collapseWorkPassages } from './PassageAggregation';
import { getZoomLevel } from './SemanticZoomController';
import { createEdgeReducer } from './EdgeFilterReducer';
import { createNodeReducer } from './NodeReducer';
import CommunityHullsLayer from './CommunityHullsLayer';
import { getGraphTypeTheme } from '@/components/graphrag/graphTheme';
import { ZoomLevel } from '@/types/sigma';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';
import type { CytoscapeData, KGNode } from '@/types';

interface SigmaKGVisualizerProps {
  cyData: CytoscapeData;
  onNodeSelect?: (node: KGNode | null) => void;
  className?: string;
}

/** Inner component that has access to Sigma context */
function SigmaGraph({
  graphRef,
  hiddenNodesRef,
  communities,
  communityColors,
  communityLabels,
  onNodeSelect,
}: {
  graphRef: React.RefObject<Graph<KGNodeAttributes, KGEdgeAttributes>>;
  hiddenNodesRef: React.RefObject<Set<string>>;
  communities: Map<number, Set<string>>;
  communityColors: Map<number, string>;
  communityLabels: Map<number, string>;
  onNodeSelect?: (node: KGNode | null) => void;
}) {
  const sigma = useSigma();
  const registerEvents = useRegisterEvents();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<ZoomLevel>(ZoomLevel.Overview);
  const expandedWorksRef = useRef(new Set<string>());

  // Pre-compute hovered node's neighbors for the reducer
  const hoveredNeighbors = useMemo(() => {
    const graph = graphRef.current;
    if (!graph || !hoveredNode) return new Set<string>();
    const neighbors = new Set<string>();
    graph.forEachNeighbor(hoveredNode, (neighbor) => neighbors.add(neighbor));
    return neighbors;
  }, [graphRef, hoveredNode]);

  // Track zoom level
  useEffect(() => {
    const camera = sigma.getCamera();
    const handleUpdate = () => {
      setZoomLevel(getZoomLevel(camera.ratio));
    };
    camera.on('updated', handleUpdate);
    handleUpdate();
    return () => { camera.removeListener('updated', handleUpdate); };
  }, [sigma]);

  // Compute node degrees
  const nodeDegrees = useMemo(() => {
    const graph = graphRef.current;
    if (!graph) return new Map<string, number>();
    const degrees = new Map<string, number>();
    graph.forEachNode((node) => {
      degrees.set(node, graph.degree(node));
    });
    return degrees;
  }, [graphRef]);

  // Register hover/click events
  useEffect(() => {
    registerEvents({
      enterNode: ({ node }) => setHoveredNode(node),
      leaveNode: () => setHoveredNode(null),
      clickNode: ({ node }) => {
        const graph = graphRef.current;
        if (!graph) return;

        const attrs = graph.getNodeAttributes(node);

        // Toggle passage expansion for work nodes
        if (attrs.type === 'work' && attrs.isAggregate) {
          const hidden = hiddenNodesRef.current;
          if (!hidden) return;

          if (attrs.passagesExpanded) {
            collapseWorkPassages(graph, node, hidden);
            expandedWorksRef.current.delete(node);
          } else {
            // Collapse any previously expanded work
            for (const workId of expandedWorksRef.current) {
              collapseWorkPassages(graph, workId, hidden);
            }
            expandedWorksRef.current.clear();
            expandWorkPassages(graph, node, hidden);
            expandedWorksRef.current.add(node);
          }
          sigma.refresh();
        }

        setSelectedNode((prev) => (prev === node ? null : node));

        if (onNodeSelect) {
          onNodeSelect({
            id: attrs.originalId,
            label: attrs.label,
            type: attrs.type,
            description: attrs.description ?? '',
          } as KGNode);
        }
      },
      clickStage: () => {
        setSelectedNode(null);
        if (onNodeSelect) onNodeSelect(null);
      },
    });
  }, [registerEvents, graphRef, hiddenNodesRef, sigma, onNodeSelect]);

  // Apply node reducer
  useEffect(() => {
    const reducer = createNodeReducer({
      zoomLevel,
      hoveredNode,
      selectedNode,
      hiddenNodes: hiddenNodesRef.current ?? new Set(),
      nodeDegrees,
      expandedWorks: expandedWorksRef.current,
      hoveredNeighbors,
    });
    sigma.setSetting('nodeReducer', reducer as any);
  }, [sigma, zoomLevel, hoveredNode, selectedNode, hiddenNodesRef, nodeDegrees, hoveredNeighbors]);

  // Apply edge reducer
  useEffect(() => {
    const reducer = createEdgeReducer({
      zoomLevel,
      hoveredNode,
      selectedNode,
      hiddenNodes: hiddenNodesRef.current ?? new Set(),
    });
    sigma.setSetting('edgeReducer', reducer as any);
  }, [sigma, zoomLevel, hoveredNode, selectedNode, hiddenNodesRef]);

  return (
    <CommunityHullsLayer
      communities={communities}
      communityColors={communityColors}
      communityLabels={communityLabels}
    />
  );
}

export default function SigmaKGVisualizer({
  cyData,
  onNodeSelect,
  className,
}: SigmaKGVisualizerProps) {
  const graphRef = useRef<Graph<KGNodeAttributes, KGEdgeAttributes> | null>(null);
  const hiddenNodesRef = useRef<Set<string>>(new Set());
  const [isLayoutReady, setIsLayoutReady] = useState(false);
  const [layoutProgress, setLayoutProgress] = useState(0);
  const [communities, setCommunities] = useState<Map<number, Set<string>>>(new Map());
  const [communityColors, setCommunityColors] = useState<Map<number, string>>(new Map());
  const [communityLabels, setCommunityLabels] = useState<Map<number, string>>(new Map());

  // Build graph, detect communities, run layout, aggregate passages
  useEffect(() => {
    if (!cyData?.elements?.nodes?.length) return;

    setIsLayoutReady(false);
    setLayoutProgress(0);

    const graph = buildGraph(cyData);
    graphRef.current = graph;

    // Detect communities
    const comms = detectCommunities(graph);
    setCommunities(comms);

    // Assign community colors (use most common node type's color per community)
    const colors = new Map<number, string>();
    const labels = new Map<number, string>();
    for (const [commId, nodeIds] of comms) {
      const typeCounts = new Map<string, number>();
      for (const nodeId of nodeIds) {
        const t = graph.getNodeAttribute(nodeId, 'type');
        typeCounts.set(t, (typeCounts.get(t) ?? 0) + 1);
      }
      const dominantType = [...typeCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'default';
      const theme = getGraphTypeTheme(dominantType);
      colors.set(commId, theme.color);

      // Find highest-degree node as community label
      let bestNode = '';
      let bestDegree = -1;
      for (const nodeId of nodeIds) {
        const degree = graph.degree(nodeId);
        if (degree > bestDegree) {
          bestDegree = degree;
          bestNode = nodeId;
        }
      }
      labels.set(commId, graph.getNodeAttribute(bestNode, 'label'));
    }
    setCommunityColors(colors);
    setCommunityLabels(labels);

    // Aggregate passages
    hiddenNodesRef.current = aggregatePassages(graph);

    // Run layout in Web Worker to avoid blocking UI
    const worker = new Worker(
      new URL('@/workers/layoutWorkerEntry.ts', import.meta.url),
      { type: 'module' },
    );

    // Serialize graph for worker
    const nodes: [string, any][] = [];
    graph.forEachNode((key, attrs) => nodes.push([key, attrs]));
    const edges: [string, string, string, any][] = [];
    graph.forEachEdge((key, attrs, source, target) => edges.push([key, source, target, attrs]));

    worker.postMessage({
      type: 'run-layout',
      payload: { nodes, edges, options: { iterations: 500 } },
    });

    worker.onmessage = (event) => {
      if (event.data.type === 'layout-complete') {
        const { positions } = event.data;
        for (const [nodeId, pos] of Object.entries(positions)) {
          graph.setNodeAttribute(nodeId, 'x', (pos as any).x);
          graph.setNodeAttribute(nodeId, 'y', (pos as any).y);
        }
        setLayoutProgress(100);
        setIsLayoutReady(true);
        worker.terminate();
      }
    };

    return () => worker.terminate();
  }, [cyData]);

  if (!isLayoutReady) {
    return (
      <div className={`flex items-center justify-center h-full ${className ?? ''}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Computing layout... {layoutProgress}%</p>
        </div>
      </div>
    );
  }

  if (!graphRef.current) return null;

  return (
    <div className={`relative w-full h-full ${className ?? ''}`} style={{ background: '#0f0b1e' }}>
      <SigmaContainer
        graph={graphRef.current}
        style={{ width: '100%', height: '100%' }}
        settings={{
          renderLabels: true,
          labelRenderedSizeThreshold: 6,
          labelFont: 'Inter, system-ui, sans-serif',
          labelColor: { color: '#e2e8f0' },
          labelSize: 12,
          defaultEdgeColor: 'rgba(255,255,255,0.15)',
          defaultEdgeType: 'line',
          defaultNodeColor: '#8A8F98',
          minCameraRatio: 0.02,
          maxCameraRatio: 5,
          zoomToSizeRatioFunction: (ratio) => ratio,
          itemSizesReference: 'positions',
          zoomDuration: 300,
          inertiaDuration: 300,
        }}
      >
        <SigmaGraph
          graphRef={graphRef as React.RefObject<Graph<KGNodeAttributes, KGEdgeAttributes>>}
          hiddenNodesRef={hiddenNodesRef as React.RefObject<Set<string>>}
          communities={communities}
          communityColors={communityColors}
          communityLabels={communityLabels}
          onNodeSelect={onNodeSelect}
        />
      </SigmaContainer>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add SigmaKGVisualizer orchestrator component"
```

---

### Task 12: Update CosmographPage to Use Sigma

**Files:**
- Modify: `frontend/src/pages/CosmographPage.tsx`

- [ ] **Step 1: Update imports and remove engine toggle**

In `CosmographPage.tsx`:
- Replace import of `CosmographKGVisualizer` (line 11) with `SigmaKGVisualizer` from `@/components/kg/SigmaKGVisualizer`
- Remove import of `D3ForceKGVisualizer` (line 12)
- Remove the engine toggle buttons (lines ~264-288)
- Replace the conditional render of `CosmographKGVisualizer`/`D3ForceKGVisualizer` with `<SigmaKGVisualizer cyData={cyData} onNodeSelect={handleNodeSelect} />`
- Remove the `engine` state variable and related logic

Read the full file first, then make targeted edits to:
1. Replace visualizer import
2. Remove engine state + toggle UI
3. Replace visualizer render

- [ ] **Step 2: Verify the app compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds. There may be unused imports to clean up from the old Cosmograph types.

- [ ] **Step 3: Clean up unused Cosmograph references**

- Delete `frontend/src/types/cosmos.ts` (248 lines, no longer needed)
- Delete `frontend/src/components/CosmographKGVisualizer.tsx` (1,912 lines)
- Delete `frontend/src/components/D3ForceKGVisualizer.tsx` (2,382 lines)
- Delete `frontend/src/workers/d3ForceWorker.ts` (605 lines)
- Remove any remaining imports of these files across the codebase

```bash
cd frontend && grep -r "CosmographKGVisualizer\|D3ForceKGVisualizer\|cosmos.ts\|d3ForceWorker" src/ --include="*.ts" --include="*.tsx" -l
```

Fix any remaining references.

- [ ] **Step 4: Verify build again**

```bash
cd frontend && npm run build
```

Expected: Clean build, no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/CosmographPage.tsx
git rm frontend/src/types/cosmos.ts frontend/src/components/CosmographKGVisualizer.tsx \
      frontend/src/components/D3ForceKGVisualizer.tsx frontend/src/workers/d3ForceWorker.ts
git commit -m "feat(frontend): replace Cosmograph with SigmaKGVisualizer, remove old engines"
```

---

## Chunk 3: Polish — UI Controls, Tooltips, and Cleanup

### Task 13: Node Tooltip Component

**Files:**
- Create: `frontend/src/components/kg/NodeTooltip.tsx`

- [ ] **Step 1: Write the tooltip**

```tsx
// frontend/src/components/kg/NodeTooltip.tsx
import { useEffect, useState } from 'react';
import { useSigma } from '@react-sigma/core';
import { getGraphTypeTheme, formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNodeAttributes } from '@/types/sigma';

export default function NodeTooltip() {
  const sigma = useSigma();
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    attrs: KGNodeAttributes;
  } | null>(null);

  useEffect(() => {
    const graph = sigma.getGraph();

    const handleEnter = ({ node }: { node: string }) => {
      const attrs = graph.getNodeAttributes(node) as KGNodeAttributes;
      const pos = sigma.graphToViewport({ x: attrs.x, y: attrs.y });
      setTooltip({ x: pos.x, y: pos.y, attrs });
    };

    const handleLeave = () => setTooltip(null);

    sigma.on('enterNode', handleEnter);
    sigma.on('leaveNode', handleLeave);

    return () => {
      sigma.removeListener('enterNode', handleEnter);
      sigma.removeListener('leaveNode', handleLeave);
    };
  }, [sigma]);

  if (!tooltip) return null;

  const theme = getGraphTypeTheme(tooltip.attrs.type);

  return (
    <div
      className="absolute pointer-events-none z-50"
      style={{
        left: tooltip.x + 15,
        top: tooltip.y - 10,
        maxWidth: 320,
      }}
    >
      <div className="bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl p-3 text-sm">
        <div className="flex items-center gap-2 mb-1">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: theme.color }}
          />
          <span className="font-semibold text-slate-100">{tooltip.attrs.label}</span>
        </div>
        <span
          className="text-xs px-1.5 py-0.5 rounded"
          style={{ backgroundColor: theme.tint, color: theme.text, border: `1px solid ${theme.border}` }}
        >
          {formatGraphNodeType(tooltip.attrs.type)}
        </span>
        {tooltip.attrs.period && (
          <p className="text-xs text-slate-400 mt-1">{tooltip.attrs.period}</p>
        )}
        {tooltip.attrs.description && (
          <p className="text-xs text-slate-300 mt-1 line-clamp-3">{tooltip.attrs.description}</p>
        )}
        {tooltip.attrs.passageCount && !tooltip.attrs.passagesExpanded && (
          <p className="text-xs text-blue-400 mt-1">
            Click to expand {tooltip.attrs.passageCount} passages
          </p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add NodeTooltip to SigmaGraph in SigmaKGVisualizer.tsx**

In the `SigmaGraph` component's return statement, add `<NodeTooltip />` alongside `<CommunityHullsLayer ... />`:

```tsx
return (
  <>
    <CommunityHullsLayer ... />
    <NodeTooltip />
  </>
);
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/kg/NodeTooltip.tsx frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add hover tooltip for Sigma.js nodes"
```

---

### Task 14: Search Bar Component

**Files:**
- Create: `frontend/src/components/kg/SearchBar.tsx`

- [ ] **Step 1: Write the search bar**

```tsx
// frontend/src/components/kg/SearchBar.tsx
import { useState, useMemo, useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { Search } from 'lucide-react';
import { getGraphTypeTheme, formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNodeAttributes } from '@/types/sigma';

interface SearchResult {
  id: string;
  label: string;
  type: string;
  color: string;
}

export default function SearchBar() {
  const sigma = useSigma();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const results = useMemo(() => {
    if (query.length < 2) return [];
    const graph = sigma.getGraph();
    const q = query.toLowerCase();
    const matches: SearchResult[] = [];

    graph.forEachNode((nodeId, attrs: KGNodeAttributes) => {
      if (matches.length >= 20) return;
      if (attrs.label.toLowerCase().includes(q)) {
        matches.push({
          id: nodeId,
          label: attrs.label,
          type: attrs.type,
          color: attrs.color,
        });
      }
    });

    // Sort: exact start matches first, then by label length
    matches.sort((a, b) => {
      const aStarts = a.label.toLowerCase().startsWith(q) ? 0 : 1;
      const bStarts = b.label.toLowerCase().startsWith(q) ? 0 : 1;
      if (aStarts !== bStarts) return aStarts - bStarts;
      return a.label.length - b.label.length;
    });

    return matches;
  }, [query, sigma]);

  const handleSelect = useCallback((nodeId: string) => {
    const graph = sigma.getGraph();
    const attrs = graph.getNodeAttributes(nodeId) as KGNodeAttributes;
    const camera = sigma.getCamera();
    camera.animate({ x: attrs.x, y: attrs.y, ratio: 0.15 }, { duration: 500 });
    setQuery('');
    setIsOpen(false);
  }, [sigma]);

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-lg px-3 py-2 backdrop-blur-sm">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder="Search nodes..."
          className="bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none w-48"
        />
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 w-72 bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl max-h-64 overflow-y-auto z-50">
          {results.map((r) => {
            const theme = getGraphTypeTheme(r.type);
            return (
              <button
                key={r.id}
                onMouseDown={() => handleSelect(r.id)}
                className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center gap-2 text-sm"
              >
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: r.color }} />
                <span className="text-slate-100 truncate">{r.label}</span>
                <span className="text-xs text-slate-500 ml-auto flex-shrink-0">
                  {formatGraphNodeType(r.type)}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add SearchBar to SigmaKGVisualizer's render output**

Add it as an overlay above the SigmaContainer, positioned top-left:

```tsx
// In SigmaKGVisualizer's return, wrap SigmaContainer with SearchBar overlay:
<div className="absolute top-4 left-4 z-10">
  <SearchBar />
</div>
```

Note: SearchBar uses `useSigma()` so it must be inside `<SigmaContainer>`. Move it inside the `<SigmaGraph>` component's return, or restructure so it's a sibling inside `<SigmaContainer>`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/kg/SearchBar.tsx frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add type-ahead search bar for Sigma.js graph"
```

---

### Task 15: KG Controls (Zoom, Fit, Passages Toggle)

**Files:**
- Create: `frontend/src/components/kg/KGControls.tsx`

- [ ] **Step 1: Write the controls**

```tsx
// frontend/src/components/kg/KGControls.tsx
import { useCallback } from 'react';
import { useSigma } from '@react-sigma/core';
import { ZoomIn, ZoomOut, Maximize2, Eye, EyeOff } from 'lucide-react';

interface KGControlsProps {
  passagesVisible: boolean;
  onTogglePassages: () => void;
  nodeCount: number;
  edgeCount: number;
}

export default function KGControls({
  passagesVisible,
  onTogglePassages,
  nodeCount,
  edgeCount,
}: KGControlsProps) {
  const sigma = useSigma();

  const zoomIn = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedZoom({ duration: 300 });
  }, [sigma]);

  const zoomOut = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedUnzoom({ duration: 300 });
  }, [sigma]);

  const fitView = useCallback(() => {
    const camera = sigma.getCamera();
    camera.animatedReset({ duration: 500 });
  }, [sigma]);

  return (
    <>
      {/* Stats bar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-slate-900/80 border border-slate-700 rounded-full px-4 py-1.5 text-xs text-slate-300 backdrop-blur-sm flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {nodeCount.toLocaleString()} nodes
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {edgeCount.toLocaleString()} edges
          </span>
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute left-3 bottom-20 z-10 flex flex-col gap-1">
        <button onClick={zoomIn} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={zoomOut} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <ZoomOut className="w-4 h-4" />
        </button>
        <button onClick={fitView} className="p-1.5 bg-slate-900/80 border border-slate-700 rounded-lg hover:bg-slate-800 text-slate-300">
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Passages toggle */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={onTogglePassages}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border backdrop-blur-sm ${
            passagesVisible
              ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
              : 'bg-slate-900/80 border-slate-700 text-slate-400'
          }`}
        >
          {passagesVisible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          Passages {passagesVisible ? 'ON' : 'OFF'}
        </button>
      </div>
    </>
  );
}
```

- [ ] **Step 2: Integrate into SigmaKGVisualizer**

Add KGControls inside SigmaContainer (needs `useSigma()`). Add state for `passagesVisible` and wire the toggle to expand/collapse all passages in selected neighborhood.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/kg/KGControls.tsx frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add zoom controls, stats bar, and passages toggle"
```

---

### Task 16: KG Legend Component

**Files:**
- Create: `frontend/src/components/kg/KGLegend.tsx`

- [ ] **Step 1: Write the legend**

```tsx
// frontend/src/components/kg/KGLegend.tsx
import { GRAPH_TYPE_THEMES, formatGraphNodeType } from '@/components/graphrag/graphTheme';

const LEGEND_TYPES = [
  'person', 'work', 'concept', 'argument', 'debate', 'school',
  'event', 'quote', 'passage', 'publication', 'synthesis', 'controversy',
];

export default function KGLegend() {
  return (
    <div className="absolute bottom-4 right-4 z-10 bg-slate-900/80 border border-slate-700 rounded-lg p-3 backdrop-blur-sm">
      <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Legend</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1">
        {LEGEND_TYPES.map((type) => {
          const theme = (GRAPH_TYPE_THEMES as any)[type];
          if (!theme) return null;
          return (
            <div key={type} className="flex items-center gap-1.5 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: theme.color }} />
              {formatGraphNodeType(type)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add to SigmaKGVisualizer render output** (outside SigmaContainer, as plain overlay — no Sigma hooks needed)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/kg/KGLegend.tsx frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add node type legend overlay"
```

---

### Task 17: Detail Panel (Click Sidebar)

**Files:**
- Create: `frontend/src/components/kg/DetailPanel.tsx`

- [ ] **Step 1: Write the detail panel**

```tsx
// frontend/src/components/kg/DetailPanel.tsx
import { X } from 'lucide-react';
import { getGraphTypeTheme, formatGraphNodeType } from '@/components/graphrag/graphTheme';
import type { KGNode } from '@/types';

interface DetailPanelProps {
  node: KGNode | null;
  onClose: () => void;
}

export default function DetailPanel({ node, onClose }: DetailPanelProps) {
  if (!node) return null;

  const theme = getGraphTypeTheme(node.type);

  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-slate-900/95 border-l border-slate-700 backdrop-blur-sm z-20 overflow-y-auto">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: theme.color }} />
              <h3 className="font-semibold text-slate-100 text-base">{node.label}</h3>
            </div>
            <span
              className="text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: theme.tint, color: theme.text, border: `1px solid ${theme.border}` }}
            >
              {formatGraphNodeType(node.type)}
            </span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>

        {node.period && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Period</div>
            <div className="text-sm text-slate-300">{node.period}</div>
          </div>
        )}

        {node.description && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Description</div>
            <div className="text-sm text-slate-300 leading-relaxed">{node.description}</div>
          </div>
        )}

        {node.school && (
          <div className="mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">School</div>
            <div className="text-sm text-slate-300">{node.school}</div>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Integrate into SigmaKGVisualizer**

Add state for `selectedNodeData` and render `<DetailPanel>` outside `<SigmaContainer>` (no Sigma hooks needed):

```tsx
const [selectedNodeData, setSelectedNodeData] = useState<KGNode | null>(null);

// Pass setSelectedNodeData as onNodeSelect to SigmaGraph
// Render:
<DetailPanel node={selectedNodeData} onClose={() => setSelectedNodeData(null)} />
```

- [ ] **Step 3: Add Escape key handler for passage collapse + panel close**

In `SigmaGraph`, add:

```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      // Collapse any expanded passages
      const graph = graphRef.current;
      const hidden = hiddenNodesRef.current;
      if (graph && hidden) {
        for (const workId of expandedWorksRef.current) {
          collapseWorkPassages(graph, workId, hidden);
        }
        expandedWorksRef.current.clear();
        sigma.refresh();
      }
      setSelectedNode(null);
      if (onNodeSelect) onNodeSelect(null);
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [graphRef, hiddenNodesRef, sigma, onNodeSelect]);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/kg/DetailPanel.tsx frontend/src/components/kg/SigmaKGVisualizer.tsx
git commit -m "feat(frontend): add detail panel sidebar and Escape key handler"
```

---

### Task 18: Update vite.config.ts and Final Cleanup

**Files:**
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/components/graphrag/graphTheme.ts` (export GRAPH_TYPE_THEMES if not already exported as record)

- [ ] **Step 1: Verify all old Cosmograph references are gone**

```bash
cd frontend && grep -r "cosmograph\|Cosmograph\|cosmos\|d3ForceWorker\|d3-force-webgpu" src/ --include="*.ts" --include="*.tsx" -l
```

Fix any remaining references.

- [ ] **Step 2: Run the full build**

```bash
cd frontend && npm run build
```

Expected: Clean build.

- [ ] **Step 3: Run existing tests**

```bash
cd frontend && npx vitest run
```

Expected: All new tests pass (graphologyAdapter, layoutWorker, PassageAggregation, SemanticZoomController, communityDetection).

- [ ] **Step 4: Start dev server and verify visually**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 and navigate to the graph page. Verify:
- Graph loads with ForceAtlas2 layout
- Communities are visually separated
- Labels don't overlap (Sigma label grid)
- Semantic zoom works (zoom in/out changes detail level)
- Hovering highlights node + neighbors
- Clicking a work node expands passages
- Search works
- Legend displays

- [ ] **Step 5: Commit final cleanup**

```bash
git add -A frontend/
git commit -m "chore(frontend): final cleanup, remove all Cosmograph references"
```

---

## Summary

| Task | Description | New Files | Tests |
|------|-------------|-----------|-------|
| 1 | Install deps, update vite config | - | build check |
| 2 | Sigma type definitions | sigma.ts | - |
| 3 | Graphology adapter | graphologyAdapter.ts | 4 tests |
| 4 | ForceAtlas2 layout worker | layoutWorker.ts, layoutWorkerEntry.ts | 2 tests |
| 5 | Passage aggregation | PassageAggregation.ts | 4 tests |
| 6 | Community detection | communityDetection.ts | 2 tests |
| 7 | Semantic zoom controller | SemanticZoomController.ts | 11 tests |
| 8 | Edge filter reducer | EdgeFilterReducer.ts | - |
| 9 | Node reducer | NodeReducer.ts | - |
| 10 | Community hulls layer | CommunityHullsLayer.tsx | - |
| 11 | Main SigmaKGVisualizer | SigmaKGVisualizer.tsx | - |
| 12 | Update page, delete old code | modify CosmographPage.tsx | build check |
| 13 | Node tooltip | NodeTooltip.tsx | - |
| 14 | Search bar | SearchBar.tsx | - |
| 15 | KG controls | KGControls.tsx | - |
| 16 | Legend | KGLegend.tsx | - |
| 17 | Detail panel + Escape key | DetailPanel.tsx | - |
| 18 | Final cleanup | - | full test + visual |

**Total: 18 tasks, ~23 tests, ~4,300 lines removed (old engines), ~1,500 lines added (new engine)**
