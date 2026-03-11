# D3 KG UX and Performance Notes

## Product patterns worth copying

- Sigma.js: keep labels sparse, promote hovered/selected nodes into a higher-priority render state, and treat the camera as the core interaction primitive rather than the graph itself.
- Cytoscape.js: reduce work during motion with viewport-specific settings like hiding edges and lowering render cost while panning and zooming.
- Neo4j Bloom: make search the primary entry point, keep detail-on-demand in a side panel, and favor scene exploration over showing every relationship equally at once.
- yFiles: use overview/minimap and level-of-detail aggressively so large graphs stay navigable before they are fully readable.

## Immediate UX direction for this graph

- Search-first: search, focus, and node panel should remain the dominant path into the graph.
- Semantic zoom: low zoom should show structure and clusters, medium zoom should show important edges, high zoom should show labels and relationship detail.
- Motion-aware detail: while the camera moves, prioritize nodes and selection state; restore edges and labels only when the viewport settles.
- Stable detail on demand: hover and selection should feel deterministic, with no layout popping and no sudden label churn.

## Immediate performance direction

- Cap canvas pixel ratio on dense scenes.
- Avoid constant rerendering when nothing changed.
- Precompute style data outside the render loop.
- Treat edges and labels as optional layers that can be dropped during motion or hot simulation.
- Rebuild spatial indices on a cadence, not on every worker message.

## Next high-value features

- Add a minimap or overview inset for long-distance navigation.
- Add explicit density presets: `presentation`, `balanced`, `analysis`.
- Separate hovered/selected render layers from the bulk graph.
- Consider WebGL rendering if the target dataset grows beyond comfortable Canvas limits.

## Sources

- D3 force: <https://d3js.org/d3-force/simulation>
- MDN OffscreenCanvas: <https://developer.mozilla.org/en-US/docs/Web/API/OffscreenCanvas>
- MDN Web Workers: <https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers>
- Sigma.js docs: <https://www.sigmajs.org/docs/>
- Cytoscape.js docs: <https://js.cytoscape.org/>
- Neo4j Bloom docs: <https://neo4j.com/docs/bloom-user-guide/current/>
- yWorks graph visualization docs: <https://www.yworks.com/pages/graph-visualization>
