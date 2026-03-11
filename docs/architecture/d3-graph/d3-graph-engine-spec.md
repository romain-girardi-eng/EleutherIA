# D3GraphEngine Spec

## Scope

A canvas-based D3 force alternative with feature parity to the current Cosmograph UX.

## Components

- Main component: [`frontend/src/components/D3ForceKGVisualizer.tsx`](../frontend/src/components/D3ForceKGVisualizer.tsx)
- Worker simulation: [`frontend/src/workers/d3ForceWorker.ts`](../frontend/src/workers/d3ForceWorker.ts)
- Route integration: [`frontend/src/pages/CosmographPage.tsx`](../frontend/src/pages/CosmographPage.tsx)

## Data Path

1. Fetch KG data from existing `apiClient.getCytoscapeData()`.
2. Reuse current conversion policy (node typing, sizing, clustering, edge weighting).
3. Initialize worker with precomputed node/edge metadata (index, type, clusterGroup, distance/strength).
4. Stream positions from worker to main thread for render + interaction.

## Worker Protocol

Input messages:
- `init`: `{ nodes, links, seed, profile, running }`
- `set-running`: `{ running }`
- `pin-node`: `{ index, x, y }`
- `release-node`: `{ index }`
- `reheat`: `{ alpha? }`

Output messages:
- `ready`: initial stabilized positions
- `positions`: streaming position updates
- `error`: worker/runtime errors

## Render/Interaction Contract

- Pan/zoom canvas transform with cursor-anchored wheel zoom.
- Node hit-testing via spatial grid index.
- Single-click: select + zoom + open node panel.
- Double-click: focus mode on ego network.
- Rect selection mode for multi-select.
- Keyboard: `Esc`, `R`, `F`.

## Parity UX Surface

- Search dropdown
- Type/school filters
- Passage toggle
- Labels/clusters mode
- Controls (zoom/fit/pause/selection)
- Stats pill + legend
- URL-selected node sync

## Performance Controls

- Edge thinning by zoom/profile
- Label budget by zoom/profile/salience
- Viewport culling
- Worker simulation decoupled from render thread
- Profile auto-selection (`default`, `balanced`, `performance`)
