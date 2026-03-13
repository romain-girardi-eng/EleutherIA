# GraphRAG Split-View DAG Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the right panel's vertical scroll list with a split-view: interactive D3 hierarchical DAG graph (top) showing AI traversal logic, and an inline detail area (bottom) that swaps between sources deck and node detail card.

**Architecture:** The `RightPanel` component gets two zones rendered in a flex-col layout. The top zone holds a new `TraversalDAG` component that uses D3.js + dagre for hierarchical layout of the reasoning path. The bottom zone shows either `SourcesDeck` (default) or an inline `NodeDetailCard` (on node click). The `source-detail` panel state is removed — clicking a source highlights the DAG node and shows detail inline. The existing `CosmographView` vertical list is replaced entirely.

**Tech Stack:** D3.js v7 (already installed), `@dagrejs/dagre` (new dep), React 19, Framer Motion, existing `graphTheme.ts` palette.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/package.json` | Modify | Add `@dagrejs/dagre` dependency |
| `frontend/src/components/graphrag/TraversalDAG.tsx` | **Create** | D3 dagre SVG graph with zoom/pan, node click, traversal animation |
| `frontend/src/components/graphrag/NodeDetailCard.tsx` | **Create** | Inline detail card for clicked node (replaces SourceDetailCard usage in right panel) |
| `frontend/src/components/graphrag/RightPanel.tsx` | Modify | Replace GraphWorkspace with split-view layout, remove `source-detail` state |
| `frontend/src/components/graphrag/CosmographView.tsx` | Delete contents | Will be emptied — all logic moves to TraversalDAG |
| `frontend/src/pages/GraphRAGPage/index.tsx` | Modify | Remove `source-detail` state transitions, simplify `handleSourceSelect` |

---

## Chunk 1: Dependencies & TraversalDAG Component

### Task 1: Install dagre

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install @dagrejs/dagre**

```bash
cd frontend && npm install @dagrejs/dagre && npm install -D @types/dagre
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend && node -e "require('@dagrejs/dagre')" && echo "OK"
```

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): add @dagrejs/dagre for graph layout"
```

---

### Task 2: Create TraversalDAG component

**Files:**
- Create: `frontend/src/components/graphrag/TraversalDAG.tsx`

This is the core new component. It takes the same `GraphRAGResponse` data and renders an interactive SVG DAG.

- [ ] **Step 1: Create TraversalDAG.tsx**

The component:
1. Computes graph data from `response.reasoning_path` + `response.sources` (reuses logic from CosmographView's `useMemo`)
2. Runs dagre layout to assign x/y positions
3. Renders SVG with:
   - Nodes as rounded rects colored by `graphTheme`
   - Edges as curved paths with arrowheads
   - Query node at far left, entry nodes next, sources + expanded right
4. Interactions: click node → calls `onNodeSelect`, hover → tooltip, zoom/pan via D3 zoom
5. Animated edge drawing on mount (staggered left-to-right)

```tsx
// frontend/src/components/graphrag/TraversalDAG.tsx
//
// Key structure:
// - useMemo: build dagre graph from response data
// - useEffect: D3 zoom behavior on SVG container
// - useEffect: animate edges on mount
// - Render: <svg> with <g> for zoom transform
//   - <defs> for arrowhead marker
//   - edges as <path> elements (d3.linkHorizontal)
//   - nodes as <g> with <rect> + <text>
//   - highlighted node gets ring glow via <rect> with stroke

// Props interface:
interface TraversalDAGProps {
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  highlightedSourceIndex: number | null;
  onNodeSelect: (nodeId: string, citationIndex?: number) => void;
  className?: string;
}
```

**Node types in the DAG:**
- `query` — single root node (amber), positioned at rank 0
- `entry` — starting_nodes from reasoning_path, rank 1
- `source` — evidence sources, rank 2
- `expanded` — expanded_nodes, rank 3

**Dagre config:**
- `rankdir: 'LR'` (left-to-right)
- `ranksep: 80`, `nodesep: 40`, `edgesep: 20`
- Node dimensions: width 140, height 48

**Edge rendering:**
- Use `d3.linkHorizontal()` for smooth curves
- Arrowhead via SVG `<marker>` in `<defs>`
- Color: source node's theme color at 60% opacity

**Zoom/pan:**
- `d3.zoom()` attached to SVG, transforms inner `<g>`
- Min zoom 0.4, max zoom 2.5
- Double-click resets to fit-all

**Hover tooltip:**
- On node hover: show full label + type in a positioned `<div>` (React portal or absolute positioned)

**Click:**
- Source nodes → call `onNodeSelect(nodeId, citationIndex)`
- Other nodes → call `onNodeSelect(nodeId)`
- Highlighted node gets amber ring glow

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/graphrag/TraversalDAG.tsx
git commit -m "feat(frontend): add TraversalDAG component with D3 dagre layout"
```

---

### Task 3: Create NodeDetailCard component

**Files:**
- Create: `frontend/src/components/graphrag/NodeDetailCard.tsx`

A compact inline detail card that shows when a node is clicked in the DAG. Simpler than `SourceDetailCard` — no prev/next navigation since the DAG provides that. Includes a close button to return to the sources deck.

- [ ] **Step 1: Create NodeDetailCard.tsx**

```tsx
// frontend/src/components/graphrag/NodeDetailCard.tsx
//
// Props:
interface NodeDetailCardProps {
  source: SourceCitation;
  citationText?: { original: string; originalLanguage: string; translation: string };
  onClose: () => void;
  onOpenInDatabase: () => void;
}

// Renders:
// - Header: type badge (themed) + label + close button
// - Body (scrollable):
//   - "Why it matters" section with source.content
//   - Original text (if citationText exists) with theme-colored left bar
//   - Translation (if exists)
//   - Metadata row: period, school, confidence
// - Footer: "View in database" button
//
// Uses: getGraphTypeTheme, formatGraphNodeType from graphTheme.ts
// Animation: framer-motion fade-in
// Style: rounded-[22px] border, white/92 bg, same parchment aesthetic
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/graphrag/NodeDetailCard.tsx
git commit -m "feat(frontend): add NodeDetailCard for inline source detail"
```

---

## Chunk 2: Rewire RightPanel & GraphRAGPage

### Task 4: Rewrite RightPanel with split-view layout

**Files:**
- Modify: `frontend/src/components/graphrag/RightPanel.tsx`

**Key changes:**
1. Remove `GraphWorkspace` component entirely (it wrapped CosmographView + deck tabs)
2. In the `'graph'` state, render split-view:
   - Top: `<TraversalDAG>` in a container with `h-[45%] min-h-[260px]`
   - Bottom: `<div className="h-[55%] overflow-y-auto">` containing either:
     - `SourcesDeck` (default, when no node is selected)
     - `NodeDetailCard` (when a node is clicked)
3. Remove `'source-detail'` from `AnimatePresence` — it no longer exists as a panel state
4. Keep `'passage-reader'` state — it takes over the full bottom area
5. Add local state `selectedNodeId: string | null` to track which node is clicked in the DAG
6. When `selectedNodeId` is set, find the matching source and render `NodeDetailCard`
7. When `NodeDetailCard.onClose` is called, clear `selectedNodeId` → shows SourcesDeck again
8. Remove the deck tab bar (Sources/Reasoning/Overview) — the DAG itself shows reasoning, and overview metrics are already in the header
9. Keep `ReasoningDeck` and `OverviewDeck` accessible via small toggle buttons below the DAG (optional, can be phase 2)

**Split-view layout structure:**
```tsx
{state === 'graph' && (
  <motion.div className="flex flex-1 min-h-0 flex-col p-4 gap-3">
    {/* TOP: DAG */}
    <div className="h-[45%] min-h-[260px] shrink-0">
      <TraversalDAG
        response={response}
        allResponses={allResponses}
        highlightedSourceIndex={activeSourceIndex}
        onNodeSelect={handleDAGNodeSelect}
      />
    </div>
    {/* BOTTOM: Detail or Sources */}
    <div className="flex-1 min-h-0 overflow-y-auto">
      <AnimatePresence mode="wait">
        {selectedNodeId ? (
          <NodeDetailCard ... onClose={() => setSelectedNodeId(null)} />
        ) : (
          <SourcesDeck ... />
        )}
      </AnimatePresence>
    </div>
  </motion.div>
)}
```

- [ ] **Step 1: Add TraversalDAG and NodeDetailCard imports to RightPanel.tsx**

- [ ] **Step 2: Add `selectedNodeId` local state**

- [ ] **Step 3: Replace `GraphWorkspace` render block with split-view layout**

- [ ] **Step 4: Remove the `source-detail` AnimatePresence block** (lines 777-825)

- [ ] **Step 5: Add `handleDAGNodeSelect` callback**
  - If node has a `citationIndex`, also call `onSourceSelect`
  - Set `selectedNodeId` to show detail card
  - If node is a passage/UUID, call passage reader flow instead

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/graphrag/RightPanel.tsx
git commit -m "feat(frontend): split-view layout with DAG + inline detail"
```

---

### Task 5: Simplify GraphRAGPage state management

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

**Key changes:**
1. `handleSourceSelect` (line 120-124): change from setting `'source-detail'` state to just setting `activeSourceIndex`. The RightPanel now handles detail display internally.
2. `handleCitationClick` (line 96-109): simplify — just set `activeSourceIndex` and let RightPanel handle the rest. Keep passage reader fallback.
3. Remove `onPrevSource` / `onNextSource` — no longer needed since NodeDetailCard doesn't have prev/next navigation (the DAG provides spatial navigation instead).
4. Update `RightPanelState` type: remove `'source-detail'` option.

- [ ] **Step 1: Update handleSourceSelect to not change panel state**

```tsx
const handleSourceSelect = useCallback((sourceIndex: number) => {
  setActiveSourceIndex(sourceIndex);
  highlightNodeRef.current?.(sourceIndex);
}, []);
```

- [ ] **Step 2: Simplify handleCitationClick**

```tsx
const handleCitationClick = (citationIndex: number) => {
  const sources = rightPanelResponse?.sources ?? [];
  const source = sources[citationIndex];
  setActiveSourceIndex(citationIndex);
  if (source?.nodeId) {
    handlePassageCitationClick(source.nodeId, citationIndex);
    return;
  }
  highlightNodeRef.current?.(citationIndex);
};
```

- [ ] **Step 3: Remove onPrevSource / onNextSource**

- [ ] **Step 4: Update RightPanel props — remove onPrevSource, onNextSource**

- [ ] **Step 5: Update RightPanelState type to remove 'source-detail'**

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/GraphRAGPage/index.tsx frontend/src/components/graphrag/RightPanel.tsx
git commit -m "fix(frontend): remove source-detail state, simplify citation flow"
```

---

### Task 6: Clean up old code

**Files:**
- Modify: `frontend/src/components/graphrag/CosmographView.tsx` — gut the file, re-export nothing (or delete if no other imports)
- Check: `frontend/src/components/graphrag/SourceDetailCard.tsx` — verify it's not imported elsewhere, mark for removal if only used in old RightPanel source-detail state

- [ ] **Step 1: Check all imports of CosmographView**

```bash
cd frontend && grep -r "CosmographView" src/ --include="*.tsx" --include="*.ts"
```

- [ ] **Step 2: Check all imports of SourceDetailCard**

```bash
cd frontend && grep -r "SourceDetailCard" src/ --include="*.tsx" --include="*.ts"
```

- [ ] **Step 3: Remove or empty unused files based on import check**

- [ ] **Step 4: Verify build**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add -u frontend/src/components/graphrag/
git commit -m "chore(frontend): remove unused CosmographView and SourceDetailCard"
```

---

## Chunk 3: Polish & Deploy

### Task 7: Visual polish and edge animations

**Files:**
- Modify: `frontend/src/components/graphrag/TraversalDAG.tsx`

- [ ] **Step 1: Add staggered edge animation on mount**
  - Each edge path starts with `stroke-dashoffset` equal to its length
  - Animate to 0 with CSS transition, staggered by dagre rank (left edges first)

- [ ] **Step 2: Add node entrance animation**
  - Nodes fade in + scale from 0.8 → 1.0, staggered by rank

- [ ] **Step 3: Add highlighted node glow effect**
  - When `highlightedSourceIndex` changes, the matching node gets an animated amber ring
  - Use SVG `<animate>` or CSS keyframes

- [ ] **Step 4: Verify visual behavior in dev server**

```bash
cd frontend && npm run dev
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/graphrag/TraversalDAG.tsx
git commit -m "feat(frontend): add traversal animation and node highlight glow"
```

---

### Task 8: Final build verification & deploy

- [ ] **Step 1: Run TypeScript check**

```bash
cd frontend && npx tsc -b
```

- [ ] **Step 2: Run build**

```bash
cd frontend && npx vite build
```

- [ ] **Step 3: Fix any build errors**

- [ ] **Step 4: Commit all remaining changes**

- [ ] **Step 5: Push to main**

```bash
git push
```

- [ ] **Step 6: Verify Cloudflare deployment succeeds**
