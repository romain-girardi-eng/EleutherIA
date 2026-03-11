# Cosmograph vs D3 A/B Decision

## Test Setup

- Cosmograph: `/visualizer?engine=cosmograph`
- D3: `/visualizer?engine=d3`
- Dataset: full production KG via existing API
- Device classes: desktop reference machine + lower-power laptop

## Metrics

1. Initial readability
- Measure at t=3s after load.
- Metrics: visible labels, median node spacing, cluster separability.

2. Overlap/clutter
- Metrics: node overlap ratio, edge crossings proxy (edge density in center viewport).

3. Interaction smoothness
- Metrics: median FPS and p95 frame time during scripted pan/zoom for 20s.

4. Search-to-node navigation speed
- Metric: elapsed time from selecting a search result to node fully centered and panel open.

5. Focus-mode clarity
- Metrics: ego-network containment (selected + 1 hop), fit success, readability score.

## Pass/Fail Thresholds

- D3 must match or beat Cosmograph in 4/5 metrics.
- D3 must not regress any critical interaction:
  - node selection correctness
  - keyboard controls
  - filter correctness
  - URL node selection behavior

## Recommendation Rule

- `Switch to D3` only if all acceptance gates pass and A/B thresholds pass.
- Otherwise `Keep Cosmograph default`, keep D3 toggle active, and iterate.

## Current Recommendation

- **Keep Cosmograph as default for now.**
- D3 engine is integrated behind toggle and ready for side-by-side benchmark runs.
- Switch decision should be finalized after baseline artifacts + metric capture are completed.
