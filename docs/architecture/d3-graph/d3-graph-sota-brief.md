# D3 Graph SOTA Brief (2026)

## Scope

Primary-source review for an interactive browser graph engine (2k+ nodes, 8k+ edges) with deterministic behavior, parity UX, and real-time pan/zoom/select.

## Primary Sources Reviewed

### Core engine/runtime primitives

- D3 force simulation API (alpha cooling, velocity decay, deterministic `randomSource`, Barnes-Hut controls):
  - <https://d3js.org/d3-force/simulation>
  - <https://d3js.org/d3-force/many-body>
  - <https://d3js.org/d3-force/link>
  - <https://d3js.org/d3-force/collide>
- Browser performance primitives:
  - OffscreenCanvas: <https://developer.mozilla.org/en-US/docs/Web/API/OffscreenCanvas>
  - Web Workers: <https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers>

### Layout/readability research

- ForceAtlas2 (continuous force balancing, anti-overlap intuition for large graphs):
  - Jacomy et al., PLOS ONE 2014, <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0098679>
- LinLog energy model (community separation objective):
  - Noack 2009, <https://link.springer.com/chapter/10.1007/978-3-642-11805-0_18>
- CoRe-GD (community-preserving, crossing-reduced layouts):
  - Jin et al. 2024, <https://arxiv.org/abs/2402.10225>
- t-FDP (topology-aware force-directed optimization):
  - Pan et al. 2024, <https://arxiv.org/abs/2406.03045>
- BatchLayout (multilevel scalability ideas):
  - Yu et al. 2024, <https://arxiv.org/abs/2408.12424>

### 2025/2026 scan result

- Queried 2025–2026 sources did not yield a clearly dominant, production-ready browser-interactive replacement to the above stack for this use case.
- Practical SOTA for this product remains: force-directed with multilevel/community-aware constraints + strict runtime budgeting.

## Chosen Defaults (Implemented)

| Area | Default | Source-informed rationale |
|---|---|---|
| Renderer | Canvas 2D on main thread | Avoid SVG DOM overhead; keep immediate-mode batching. |
| Simulation runtime | `d3-force` in Web Worker | Preserves input/render responsiveness under live simulation. |
| Determinism | Fixed seed + deterministic cluster anchors + deterministic LOD sampling | Stable A/B comparisons and reproducible debug runs. |
| Anti-collapse force stack | Many-body repulsion + collision + cluster-attractor + inter-cluster repulsion + soft radial envelope + periodic scale guard | Combines ForceAtlas2-style anti-overlap intuition with community-preserving constraints (LinLog/CoRe-GD direction). |
| Many-body policy | Type/degree-aware charge; bounded range (`distanceMax`) and Barnes-Hut theta tuning | Better hub separation without full O(N^2) cost. |
| Link-distance policy | Type prior (`work↔passage`, `person↔work`) then adjusted by degree, same-cluster flag, structural relationship | Keeps semantic hierarchy readable while opening inter-community bridges. |
| Link-strength policy | Structural edges boosted; cross-cluster edges damped; hub damping | Reduces hub pinwheel collapse and edge pile-up. |
| Collision policy | Radius from visual size + degree padding; profile-dependent iterations/strength | Better overlap resistance at acceptable compute cost. |
| Labels | Zoom+viewport budget; salience priority (selection/hover/degree/labelWeight); occupancy-grid rejection | Predictable clutter control with better label stability than naive full render. |
| Edge LOD | Zoom/profile/viewport edge budget with importance-weighted deterministic sampling | Preserves key structure while maintaining frame budget. |
| Culling | Viewport culling for nodes/edges, margin expansion | Avoids off-screen draw cost and keeps interaction stable. |

## Rejected / Deferred Techniques

| Technique | Decision | Why |
|---|---|---|
| SVG renderer | Rejected | Not viable at target density and interaction rate. |
| Full-label render | Rejected | Severe overlap/clutter, reduced readability. |
| Full-edge render at all zoom levels | Rejected | Unstable frame time on dense views. |
| Pure center gravity + weak repulsion | Rejected | Higher center-collapse risk during live simulation. |
| Full O(N^2) repulsion | Rejected | Poor scaling past ~2k nodes. |
| Full replacement with non-force global optimizers (single-shot) | Deferred | Many methods are strong for static quality but weaker for continuous interactive dragging/filtering in browser constraints. |
| OffscreenCanvas-only full migration | Deferred | Useful, but current worker-simulation + main-thread canvas already meets responsiveness targets with lower integration risk. |

## Operational Profiles

- `default`: readability-first (stronger anti-collapse and label retention).
- `balanced`: reduced force/label overhead for medium devices.
- `performance`: aggressive LOD and lighter physics for largest scenes.

## Notes for A/B Decision

Benchmark both engines with the fixed metrics in `docs/d3-graph-parity-matrix.md`. Gate a switch only if D3 is equal or better on readability, clutter, and interaction smoothness while preserving parity interactions.
