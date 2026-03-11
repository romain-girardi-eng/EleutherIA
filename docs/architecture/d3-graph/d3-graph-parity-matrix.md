# D3 Graph Parity Matrix

## Baseline Freeze (Cosmograph)

Baseline artifacts should be captured from `/visualizer?engine=cosmograph` and stored in `docs/assets/graph-baseline/`:

| Artifact | Filename | Scenario | Status |
|---|---|---|---|
| Screenshot | `01-default-overview.png` | Initial load (default filters, passages off) | Pending capture |
| Screenshot | `02-search-result-selected.png` | Search + node selection | Pending capture |
| Screenshot | `03-focus-mode.png` | Double-click focus mode | Pending capture |
| Screenshot | `04-filters-types-schools.png` | Type + school filters active | Pending capture |
| Screenshot | `05-clusters-mode.png` | Cluster labels mode | Pending capture |
| Screenshot | `06-legend-stats-controls.png` | Legend, stats pill, controls visible | Pending capture |
| Video | `baseline-interactions.mp4` | Pan/zoom/select/pause/rect-selection/shortcuts | Pending capture |

Capture helper: [`scripts/capture_graph_baseline.py`](../scripts/capture_graph_baseline.py).

## Parity Checklist

| Feature | Cosmograph baseline | D3 implementation | Parity |
|---|---|---|---|
| Search | Inline search + dropdown + zoom/select | Same UX in [`frontend/src/components/D3ForceKGVisualizer.tsx`](../frontend/src/components/D3ForceKGVisualizer.tsx) | ✅ |
| Node click panel | Select node -> right panel | `onNodeClick` wiring preserved in D3 + page | ✅ |
| Double-click focus mode | Ego network focus + banner + Esc exit | Same behavior in D3 (`enterFocusMode`/`exitFocusMode`) | ✅ |
| Type/school filters | Compact filter panel | Same panel + same filter sets | ✅ |
| Passage toggle | Explicit passages ON/OFF toggle | Same toggle semantics | ✅ |
| Labels/clusters mode | Labels vs cluster mode switch | Same toggle + label/cluster rendering paths | ✅ |
| Zoom/fit/pause/selection controls | Zoom, fit, pause/play, rectangular selection | Same controls, mapped to canvas/worker actions | ✅ |
| Keyboard shortcuts | `Esc`, `R`, `F` | Same shortcuts in D3 | ✅ |
| Stats pill | Nodes/edges counts with filtered totals | Same stats pill + profile tag | ✅ |
| Legend | Type-color legend | Same type legend | ✅ |
| URL-selected node | `/visualizer/:nodeId` selects + centers | Same via `selectedNodeId` effect in D3 | ✅ |
| Route toggle | N/A (single engine) | Same page engine toggle (`Cosmograph`/`D3`) | ✅ |

## A/B Decision Criteria (Fixed)

Use the same dataset and viewport for both engines (`/visualizer?engine=cosmograph` vs `/visualizer?engine=d3`):

1. Initial readability: median nearest-neighbor distance and visible label count at t=3s.
2. Overlap/clutter score: node overlap ratio + edge density in viewport center.
3. Interaction smoothness: median FPS during 20s pan/zoom sequence.
4. Search-to-node speed: time from search enter to focused node frame.
5. Focus-mode clarity: ego-network edge/node retention and fit success.

## Acceptance Gates

1. No center-collapse during live simulation.
2. Initial view occupies readable viewport area (not tiny, not exploded).
3. Equal or better UX than Cosmograph on the parity checklist.
4. Stable interactions under full dataset.
