# Scholar workspace visual QA — 2026-08-24

Status: production-bundle UI/UX review complete. This is browser-laboratory
evidence, not a WCAG, Core Web Vitals, hardware-GPU, or FPS certification.

## Scope and protocol

- Audience and direction: the committed `.impeccable.md` scholar persona and
  light-dominant “luminous intellectual atlas” moodboard.
- Browser: headless Chromium against the Vite production bundle on
  `127.0.0.1:4175`.
- Viewports: 1440 × 1000, 1024 × 768, and touch-enabled 390 × 844 CSS pixels.
- Data: a deterministic, release-pinned wire fixture with 82 nodes, 81 asserted
  edges, eight periods, long/Greek/Latin labels, and 38 Classical Greek nodes
  to force Chronos pagination. The current remote deployment did not expose the
  new `/api/kg/workspace/*` endpoints during this review, so the compiled UI was
  tested against their exact fail-closed response contract rather than an
  unpinned legacy list.
- Exercised: Scholar search, dense table, comparison, lazy detail, local retry,
  Evidence Thread, permalink copy/reload; Chronos search, time window and
  pagination; mode tabs, roving focus, layout-safe shortcuts, undo/redo,
  browser back and shared selection; Atlas compatibility fallback.
- Checks: screenshots inspected at native viewport size; console, page errors,
  failed requests, document/component overflow, effective touch geometry,
  focus rendering, heading order, contrast, and automated axe-core scans.

## Before evidence and fixes

| Severity | Before evidence | Fix and after evidence |
| --- | --- | --- |
| P1 | `src/index.css` suppressed `*:focus-visible`, component rings, outlines and ring variables with `!important`. Keyboard traversal computed no visible focus treatment. | Removed blanket suppression; only pointer focus uses `:focus:not(:focus-visible)`. Final keyboard evidence on the Scholar tab computes a solid 2 px outline. |
| P1 | A lazy node-detail 503 set the provider's fatal graph error and replaced a valid Scholar release with “The graph release could not be opened.” | Added per-node loading/error state, an announced local message and “Retry full detail”. A 503 now preserves the release-bound summary; the second request recovers in place. API 409 plus `detail.code=kg_release_mismatch` and `served_release_id` is still normalized to the fatal release mismatch path. |
| P1 | At 390 px, Chronos' grid item kept a roughly 1,050 px min-content width; its card, search and timeline were clipped far beyond the viewport (measured right edge 1,081 px). | Added the missing `min-width: 0` shrink boundary. Final right edge and document width are 390 px, with vertically stacked periods and no unintended mobile overflow. |
| P1 | Scholar compare checkboxes exposed only their 20 × 20 visual control as the tap target. Mode tabs were 36 px tall. | Kept the checkbox visual size but wrapped it in a 44 × 44 label; mode tabs are now at least 44 px. Final effective-target audit found no workspace target below 44 px at any requested viewport. |
| P1 | Workspace modes and global skip links both advertised/handled Alt+1/2/3, so one chord could move focus and change mode. `event.key` was also locale-sensitive under Option/Alt. | Skip links own exact Alt+Digit; modes own Alt+Shift+Digit. Both use `event.code` (`Digit1`–`Digit4`), ignore editing fields, and expose matching title/ARIA copy. Exact Alt+3 leaves Chronos selected; Alt+Shift+3 opens Scholar. |
| P1 | At exactly 1024 px, the left release/thread metadata rendered behind the centered mode switcher. At 390 px, the chrome's right action edge measured 392 px. | Metadata now enters at `xl`; compact mobile tab padding retains visible labels while fitting undo/redo. Final 1024 and 390 screenshots show clean separation and zero workspace overflow. |
| P1 | Chronos “Visible interval” used `stone-500` at 10 px on `#f7f2e9`, approximately 4.30:1. Automated contrast audit flagged it. | Changed that selector to `stone-600`, approximately 6.84:1 on the same surface. Final automated scans report no contrast violation. Ratios are calculated values, not certification. |
| P1 | Chronos jumped from the page `h1` to the generic accordion `h3`; axe reported `heading-order`. Full-screen pages also advertised a footer skip target that was intentionally absent. | Accordion titles now accept a semantic level and Chronos uses `h2`. The full-screen shell omits its absent footer skip link; normal pages expose a real `id="footer"`. Final axe scans report zero violations in both light modes at all three sizes. |

The long-node fixture also verified wrapping without horizontal document
overflow. Scholar's 240-row render bound and Chronos' 24-node period pages
remained intact; searching reached nodes outside the mounted Chronos page.

## Device matrix

| Viewport | Scholar | Chronos | Shared interaction | Automated/layout result |
| --- | --- | --- | --- | --- |
| 1440 × 1000 | Dense table and inspector visible together; long labels wrap; search, compare, thread and detail pass. | Search and pagination pass; timeline remains an intentionally contained horizontal chronology. | Selection, comparison and thread survive mode changes, permalink reload and browser back. | axe 0; clean console/page/request log; document width 1440; effective targets ≥44 px. |
| 1024 × 768 | Full-width table with inspector below; chrome collision removed. | Time controls and contained horizontal chronology remain usable with touch or pointer. | Mode tabs, undo/redo and permalink remain separated and keyboard reachable. | axe 0; clean console/page/request log; document width 1024; effective targets ≥44 px. |
| 390 × 844 | Single-column header, full-width search/permalink and readable three-column table; long text wraps. | Header/time controls stack; timeline card shrinks to viewport and period blocks stack vertically. | Visible labelled modes fit beside undo/redo; exact Alt and Alt+Shift chords do not double-fire. | axe 0; clean console/page/request log; document width 390; no unintended workspace overflow; effective targets ≥44 px. |

The desktop headless browser had no acceptable hardware WebGL 2 renderer. The
Atlas guard rendered before canvas allocation (`canvasCount = 0`), explained
the limitation, and “Open Scholar” restored the same release successfully. A
separate SwiftShader check by the Atlas guard owner reached the software
fallback in about 451 ms with zero canvases or console errors. Neither run
proves supported-hardware Atlas performance.

## Persona scores

Scores are qualitative task-walkthrough ratings out of 10, not survey data.

| Persona | Before | After | Walkthrough result |
| --- | ---: | ---: | --- |
| Dr Helena, publication-focused scholar | 6.2 | 9.1 | Can search a locus, inspect release-bound detail, compare it, append an Evidence Thread, move through Chronos and restore the citable permalink without losing context. The former fatal detail cliff is gone. |
| Sam, keyboard/screen-reader-dependent researcher | 4.3 | 8.8 | Visible focus, coherent `h1`→`h2` structure, unique shortcuts, live loading/error status, labelled tabs and recovery controls pass the scripted flow. No manual NVDA/VoiceOver session was performed. |
| Casey, distracted touch user | 4.8 | 8.7 | 390 px layout no longer clips Chronos, core targets meet the 44 px audit floor, long labels wrap, and state survives navigation. The inspector remains below the bounded table, so a deliberate vertical move is still required. |

Cognitive-load checklist: 1/8 failures (low). Grouping, hierarchy, visible
location, preserved context and progressive disclosure pass. “One thing at a
time” is the sole partial failure because Scholar intentionally exposes table,
comparison and Evidence Thread in one research surface.

## Design health score

| # | Nielsen heuristic | Before | After | Remaining note |
| ---: | --- | ---: | ---: | --- |
| 1 | Visibility of system status | 2 | 3 | Loading, match/page counts and local detail status are explicit; clipboard failure still has no dedicated recovery copy. |
| 2 | Match with scholarly practice | 4 | 4 | Locus, witness, release, comparison and Evidence Thread language fit the audience. |
| 3 | User control and freedom | 2 | 4 | Back, undo/redo, all-time reset, local retry and mode preservation work. |
| 4 | Consistency and standards | 2 | 3 | Shared chrome/state are coherent; Scholar's sharp editorial table and Chronos' legacy rounded accordion still differ slightly. |
| 5 | Error prevention | 2 | 3 | Release mismatch remains fail-closed and comparison stays bounded; time inputs still rely on normalization rather than inline validation copy. |
| 6 | Recognition rather than recall | 3 | 4 | Modes are labelled, shortcuts are announced, and current selection persists visibly. |
| 7 | Flexibility and efficiency | 2 | 4 | Search, page controls, keyboard modes, history and permalinks support expert paths. |
| 8 | Aesthetic and minimalist design | 3 | 3 | Strong editorial hierarchy and restrained palette; Chronos remains information-dense by design. |
| 9 | Error recognition and recovery | 1 | 4 | Ordinary detail failures are local and retryable; release identity failures remain explicit and blocking. |
| 10 | Help and documentation | 2 | 2 | Inline guidance is useful, but there is no contextual shortcut/help surface within the workspace. |
| **Total** |  | **23/40** | **34/40 — Good** | No remaining P0/P1 UI finding in this bounded pass. |

## Anti-pattern verdict

Pass. Scholar and Chronos do not read as generic AI dashboard output: the
Instrument Serif / DM Sans / EB Garamond hierarchy, parchment and terracotta
palette, asymmetrical research layouts, explicit scholarly provenance and
mode-preserved Evidence Thread are project-specific. There is no decorative
gradient text, dark neon default, glass-card grid, hero metric template, or
gratuitous motion. Chronos' rounded `academic-card` is the only mild legacy
dashboard tell; it groups a real interactive chronology rather than repeating
decorative cards.

## Remaining issues and limits

- P2: Chronos intentionally uses a contained horizontal chronology at tablet
  and desktop sizes. Search and page controls make every node reachable, but a
  stronger scroll/orientation cue would improve discovery of later periods.
- P2: at 390 px, the visible “Chrono-Storyline” accordion title truncates while
  its full accessible name and period badge remain available.
- P2: Scholar's inspector follows the bounded table below `xl`; on mobile this
  requires leaving the table's inner scroll and continuing down the page.
- The remote deployment must ship the release-pinned workspace endpoints
  before this exact compiled flow can be validated end-to-end without request
  interception.
- Browser emulation cannot substitute for an iPhone, Android handset, tablet,
  manual screen-reader session, 200% zoom study, or supported-hardware Atlas
  trace. No WCAG or performance certification is claimed.

## Release gates

- `npm test -- --run`: 30 files, 210 tests passed.
- `npm run test:seo`: SEO output contract passed.
- `npm run test:workspace-split`: production build, 24-route prerender and
  workspace split contract passed.
- Final split: shell 25.01 kB raw / 8.99 kB gzip; Scholar 11.31 / 3.40;
  Chronos 17.21 / 5.61; Atlas 67.38 / 19.30. The 1.81 MB raw Cosmograph vendor
  remains Atlas-only.
