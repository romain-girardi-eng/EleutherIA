# Sigma.js KG Visualizer — Design Spec

**Date:** 2026-03-11
**Status:** Approved
**Replaces:** CosmographKGVisualizer + D3ForceKGVisualizer

## Problem

The current Cosmograph-based KG visualizer is unreadable:
- 13,541 passage nodes (78% of graph) overwhelm the layout
- No label collision avoidance (Cosmograph lacks a label grid)
- No semantic zoom (same detail at every zoom level)
- Weak community separation (d3-force vs ForceAtlas2)

## Solution

Replace Cosmograph with **Sigma.js v3 + Graphology** — the stack powering Gephi Lite. Add passage aggregation, semantic zoom, and smart edge filtering.

## Architecture

```
API /api/kg/viz/cytoscape
  │
  ▼
graphologyAdapter.ts     — converts CytoscapeData → Graphology graph
  │
  ├──▶ aggregationService.ts    — passage aggregation (13k → ~180 work badges)
  ├──▶ communityDetection.ts    — Louvain via graphology-communities-louvain
  ├──▶ layoutWorker.ts          — ForceAtlas2 in Web Worker (500 iterations, freeze)
  │
  ▼
SigmaKGVisualizer.tsx    — main React component
  │
  ├──▶ @react-sigma/core        — Sigma.js React bindings
  ├──▶ CommunityHullsLayer.tsx  — canvas overlay for convex hulls
  ├──▶ EdgeFilterReducer.ts     — smart edge visibility by category
  ├──▶ SemanticZoomController.ts — 4-level zoom LOD
  └──▶ NodeTooltip.tsx / DetailPanel.tsx — hover + click UI
```

## Semantic Zoom (4 Levels)

Zoom levels are driven by Sigma's `camera.ratio` (lower = more zoomed in):

| Level | Name | Camera Ratio | Nodes | Labels | Edges | Communities |
|-------|------|-------------|-------|--------|-------|-------------|
| 1 | Overview | > 1.2 | High-degree as dots | None | None | Labeled hulls |
| 2 | Community | 0.4 – 1.2 | All non-passage | Person, school, debate | Inter-community "always-visible" edges (see Edge Visibility) | Fading hulls (opacity = ratio - 0.4) |
| 3 | Neighborhood | 0.08 – 0.4 | All non-passage + expanded passages | All via Sigma label grid | "Always-visible" edges on, "hover-only" edges on hover | Gone |
| 4 | Detail | < 0.08 | All including passages | All including passages | All for visible nodes | Gone |

Thresholds are initial values — tune empirically after first integration.

## Edge Visibility Strategy

**Always visible (past zoom level 1):**
- argumentative: argues_for, argues_against, refutes, responds_to, supports, critiques
- intellectual: influences, influenced_by, taught_by, teaches, extends
- doctrinal: holds_position, endorses, rejects
- semantic: contrasts_with, presupposes

**On hover/select only:**
- structural: contains, part_of, has_section, has_chapter, belongs_to_corpus
- authorship: wrote, authored_by, created_by, developed_by
- citation: cites, cited_by, source_for, evidenced_by
- affiliation: belongs_to_school, member_of, has_member
- textual: preserves, preserved_in, translation_of

## Passage Aggregation

- **Default (passages OFF):** 13,541 passages grouped under 183 parent works. Each work node shows a badge count (e.g., "De Interpretatione (47)"). Visible node count: ~1,030.
- **Click a work node:** Passages expand in a fixed circular layout (radius = 80px * sqrt(count/10), capped at 200px) around the parent work. Only one work can be expanded at a time — clicking another work collapses the previous expansion. Click the same work again or press Escape to collapse.
- **Passages toggle ON:** Expands passages for all works currently selected (pinned via click). If no selection, expands for all works visible in the viewport. Cap at 500 passage nodes max — if exceeded, show highest-cited passages first with a "+N more" indicator on the work badge. Toggle OFF collapses all.
- **Overlap prevention:** When a work's passages are expanded, nearby nodes are pushed outward using `graphology-layout-noverlap` on the local subset (50ms, non-blocking).

## Interaction Model

**Hover:** Highlight node + direct neighbors, dim everything else, show tooltip (type, period, description), reveal structural edges for that node.

**Click:** Pin selection, open detail panel (right sidebar), option to expand passages if work node, zoom into community if hull clicked.

**Search:** Persistent search bar (top), type-ahead with node type icons, select result → camera animates to node, shows 2-hop ego network.

## Community Visualization

- Louvain community detection via `graphology-communities-louvain`
- At overview zoom: translucent convex hulls with community labels
- Hulls fade as user zooms into a community
- Custom canvas layer behind Sigma WebGL layer

## Dependencies

**Add:**
- `graphology` — graph data model
- `graphology-types` — TypeScript types
- `sigma` — WebGL renderer (v3)
- `@react-sigma/core` — React bindings
- `graphology-layout-forceatlas2` — ForceAtlas2 + Web Worker
- `graphology-communities-louvain` — community detection
- `graphology-layout-noverlap` — anti-overlap post-processing

**Remove:**
- `@cosmograph/react` — replaced by Sigma
- `d3-force-webgpu` — no longer needed

## Files: Keep vs Replace

**Keep:**
- `graphTheme.ts` — 18 node type color definitions
- `CosmographView.tsx` — answer flow visualization (SVG, not Cosmograph)
- API endpoints + CytoscapeData format
- Search, filter, legend UI patterns
- Dark theme aesthetic

**Replace:**
- `CosmographKGVisualizer.tsx` → `SigmaKGVisualizer.tsx`
- `D3ForceKGVisualizer.tsx` → remove
- `d3ForceWorker.ts` → `layoutWorker.ts` (ForceAtlas2)
- `CosmographPage.tsx` → update imports, remove engine toggle
- `cosmos.ts` types → sigma types

## ForceAtlas2 Layout Parameters

Starting parameters (tune empirically):

```
gravity: 1.0
scalingRatio: 2.0
barnesHutOptimize: true       // required for 1k+ nodes
barnesHutTheta: 0.5
strongGravityMode: false      // true compresses too much
linLogMode: true              // better community separation
slowDown: 10
iterations: 500               // in Web Worker, then freeze
```

After FA2 converges, run `graphology-layout-noverlap` (300 iterations, ratio: 2.0) to push apart overlapping nodes.

## Data Mapping (CytoscapeData → Graphology)

The `graphologyAdapter.ts` maps CytoscapeData fields to Graphology node/edge attributes:

| CytoscapeData field | Graphology attribute | Notes |
|---------------------|---------------------|-------|
| `node.data.id` | node key | String, unique |
| `node.data.label` | `label` | Used by Sigma label renderer |
| `node.data.type` | `type` | Keys into `graphTheme.ts` colors |
| `node.data.period` | `period` | For filtering/tooltip |
| `node.data.description` | `description` | For tooltip/detail panel |
| `node.data.metadata` | `metadata` | Preserved as-is |
| `node.data.community` | `community` | From API or computed via Louvain |
| `edge.data.id` | edge key | String |
| `edge.data.source` | source node key | |
| `edge.data.target` | target node key | |
| `edge.data.relation` | `relation` | Maps to edge category for visibility |
| `edge.data.description` | `description` | For edge tooltip |

Computed attributes added by the adapter:
- `size`: from `graphTheme.ts` TYPE_SIZES mapping
- `color`: from `graphTheme.ts` node type color
- `x`, `y`: initially random, replaced by FA2 output
- `passageCount`: number of child passages (for work nodes)
- `isAggregate`: true for work nodes with hidden passages

## State Management

The Graphology `Graph` instance is the single source of truth, held as a `useRef` in `SigmaKGVisualizer.tsx`. Sigma.js reads from it directly (it observes graph mutations).

Shared state coordination:
- **Graph data**: `graphRef.current` (Graphology instance) — mutated by aggregationService, communityDetection, passage expansion
- **Camera/zoom level**: read from Sigma's `camera` events → drives `SemanticZoomController`
- **UI state** (selected node, hovered node, active filters, passage toggle): React `useState` in `SigmaKGVisualizer.tsx`, passed to children as props
- **Node/edge reducers**: Sigma's `nodeReducer`/`edgeReducer` functions read UI state to compute dynamic visual attributes (highlight, dim, hide)

No external state library needed — Sigma + Graphology + React local state is sufficient for this component tree.

## Loading & Error States

- **During FA2 computation**: Show a skeleton with the search bar and filter controls active but the graph canvas replaced by a centered spinner + "Computing layout..." text. The spinner shows iteration progress (e.g., "142 / 500").
- **API failure**: Show error banner with retry button. Filters/search disabled.
- **Degenerate Louvain results**: If community detection yields 1 community (everything connected) or N communities where N > node_count * 0.5 (too fragmented), fall back to node `type` as the community grouping. Log a warning.

## Performance Targets

- Initial render (API fetch + FA2 + first paint): < 5s on M1 MacBook
- Pan/zoom FPS with ~1,030 visible nodes: >= 30 FPS sustained
- Passage expansion (click work → passages appear): < 200ms
- Memory: < 300MB heap for full graph loaded

## Hull Computation

Convex hulls computed using `d3-polygon` (already in the dependency tree via d3). For each Louvain community, collect node positions → `d3.polygonHull()` → render as filled path on a custom canvas layer positioned behind Sigma's WebGL canvas.

## New File Structure

```
frontend/src/
  components/
    kg/
      SigmaKGVisualizer.tsx       — main component
      CommunityHullsLayer.tsx     — canvas hull overlay
      EdgeFilterReducer.ts        — edge visibility logic
      SemanticZoomController.ts   — 4-level LOD
      NodeTooltip.tsx             — hover tooltip
      DetailPanel.tsx             — click detail sidebar
      PassageAggregation.ts       — aggregation logic
  services/
    graphologyAdapter.ts          — CytoscapeData → Graphology
    communityDetection.ts         — Louvain wrapper
  workers/
    layoutWorker.ts               — ForceAtlas2 Web Worker
```
