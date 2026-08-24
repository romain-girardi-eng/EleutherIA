# Atlas multi-mode browser QA and transfer-budget closure

> **Historical evidence notice:** this inspection predates the 66-node radial
> constellation layout and renderer-stable camera boundary. Its API/release
> observations remain useful, but it is not visual or performance proof for
> the current Atlas. One cold production-build browser pass is still required
> before RC publication.

**Date:** 2026-08-24  
**Status:** local implementation verified; production RUM/GPU trace still open  
**Viewport:** 1280 × 720 CSS px, DPR 2, in-app Chromium browser  
**Release inspected:** `kg-sha256-bf3043e759a50a0648422380413841a066d4f107aef81ee18f0f52994cfd46af`

## Outcome

The knowledge workspace now opens as a light-dominant intellectual Atlas with
three synchronized projections: Atlas, Chronos, and Scholar. Selection,
comparison, Evidence Thread, filters, release identity, URL state, history, and
per-mode camera state remain owned by one provider. Chronos and Scholar mount
without a WebGL canvas.

The first desktop frame is no longer the complete 23,246-node graph. It is a
deterministic, capped landing projection: 40 hand-curated anchors expanded by
ranked one-hop and bounded two-hop context, capped at 220 and pruned of
disconnected satellites. The inspected release yields 218 connected nodes; the
complete graph remains one explicit action away.

## Browser defects found and closed

1. **Full-graph hairball as the default.** Desktop opened all 23,246 nodes.
   Default is now the connected curated Atlas; mobile still enters the
   relational Explore surface.
2. **Dark global Atlas despite the light-dominant design contract.** GPU field,
   labels, search, filters, legend, fallback, loader, mode chrome, and tool
   surfaces now use parchment and ink. The dark dossier is a local focus state.
3. **No semantic labels.** `showTopLabels` was enabled while Cosmograph's master
   `showLabels` gate was false. A bounded 14/36/120 semantic-zoom label budget
   is now active.
4. **Invented Chronos dates.** Every node inherited its period's lower bound,
   producing claims such as “Leibniz — 650 BCE.” Period bands are now explicitly
   separate from node dates. Unknown/cross-period bounds remain null and are
   excluded from date-window filtering rather than guessed.
5. **Missing represented period bounds.** Early Modern, Second Temple Judaism,
   Rabbinic, and First Temple / Pre-exilic Judaism have declared editorial
   bands; Cross-period and Unspecified intentionally do not.
6. **Workspace controls covered the dossier close action.** The local dark
   dossier reserves the global chrome row on desktop.
7. **`/api/api/*` local requests.** Raw fetch callers now use one tested URL
   joiner. Browser/backend logs showed the corrected `/api/kg/stats` and
   `/api/works/stats` paths with 200 responses and no new doubled paths.
8. **Repeated React Fragment console errors.** `Button asChild` wrapped its Link
   in a Fragment, then Radix forwarded `className` to that Fragment. The Slot
   path now receives one concrete child. A fresh browser run produced zero new
   console errors.

## Transfer measurements

The compact JSON fields were already correct, but the origin did not compress
them and workspace edge IDs were not consumed by any projection.

| State | Nodes | Edges page 1 | Edges page 2 | Complete transfer |
|---|---:|---:|---:|---:|
| Gzip before edge-ID removal | 311,441 B | 1,503,491 B | 158,448 B | 1,973,380 B |
| Gzip after edge-ID removal | 311,441 B | 307,467 B | 18,235 B | **637,143 B** |

The current complete workspace release is 67.7% smaller than the already
compressed prior view and 68.1% below the 2,000,000-byte hard budget. The API
now applies origin gzip at level 6 while excluding `text/event-stream`, so SSE
flush semantics are preserved. The renderer derives edge keys from immutable
release order after its exact count/release gate succeeds.

`test_workspace_payload_budget.py` loads the real current nodes/edges, requests
every page through the real release contract and compression middleware, and
fails above 2,000,000 bytes.

## Code and bundle gates

- Frontend after the final glossary/integrity/preload pass: **39 files, 231
  tests passed**.
- ESLint: **zero errors, zero warnings** after fixing the three inherited hook
  warnings encountered by this pass.
- Production build and SEO prerender: PASS, 24 general route HTML files plus 27
  fail-closed entity review pages.
- Lazy workspace bundles (gzip): route shell 9.23 kB; Scholar 3.48 kB; Chronos
  5.94 kB; Atlas 20.49 kB.
- Cosmograph vendor remains isolated and lazy: 419.85 kB gzip. It is absent
  from Scholar and Chronos.
- Mode chunks now preload on pointer, keyboard-focus, or touch intent before
  activation. The shared loader keeps the three `import()` boundaries explicit,
  while the split contract still proves that only Atlas owns Cosmograph.
- Backend/workspace contract and compression tests: PASS.

## Explicitly not certified yet

- No production p75 LCP/INP/CLS claim is made.
- No hardware-specific GPU frame-time, power, thermal, or memory trace is
  certified by this run.
- The force layout is bounded and visually checked, but the target architecture
  still calls for release-built stable coordinates, typed arrays/CSR, a Worker,
  adaptive frame-time quality, and fixed-view visual regression captures.
- The local database was unavailable during browser QA; the API correctly used
  its immutable KG snapshot. This does not substitute for a staged production
  trace against the release deployment.
