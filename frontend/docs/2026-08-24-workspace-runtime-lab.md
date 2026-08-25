# Knowledge-graph workspace runtime lab — 2026-08-24

Status: diagnostic laboratory evidence, not a field-performance certification.

## Protocol

- Production frontend build served by Vite Preview on `127.0.0.1:4173`.
- FastAPI served the local immutable KG snapshot on `127.0.0.1:8000` with
  PostgreSQL deliberately unavailable.
- Production API requests were intercepted in Playwright and routed to that
  local FastAPI process. This avoids measuring Internet latency while keeping
  the production response shapes.
- Chromium 1223 headless, 1440 × 1000 CSS pixels, DPR 1, cold browser context
  for each mode.
- The Atlas renderer used SwiftShader. GPU/frame results therefore identify
  compatibility and main-thread risks; they do not certify a hardware-GPU FPS.
- Snapshot at measurement time: 20,265 served nodes and 101,720 served edges,
  including ontology-derived inverse edges.
- `works/stats` returned two expected 500 responses in snapshot-only mode. KG
  loading still completed, but those errors are recorded and must be fixed
  separately before claiming a clean offline/snapshot runtime.

## Results

| Mode | Workspace ready | API bytes | CDP JS heap | DOM nodes | LCP | Long-task max | rAF p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scholar | 2,080 ms | 130.46 MB | 187.8 MB | 2,637 | 272 ms | 123 ms | 9.6 ms |
| Chronos | 2,083 ms | 130.46 MB | 176.9 MB | 24,366 | 260 ms | 132 ms | 9.5 ms |
| Atlas | 3,511 ms | 130.46 MB | 310.4 MB | 4,129 | 4,640 ms | 618 ms | 9.9 ms |

Additional observations:

- Frontend resource transfer excluding intercepted API responses was about
  0.44 MB in Scholar/Chronos and 4.86 MB in Atlas. Code splitting is working.
- All three modes nevertheless download the same roughly 130 MB graph payload.
  The current list endpoints expose full node/edge records and the in-memory
  snapshot materializes inverse edges. The workspace only consumes a small
  projection of those records.
- Chronos renders an order of magnitude more DOM than a research interface
  should keep live. Its timeline must use bounded progressive/virtual rendering
  while retaining explicit access to every result.
- Atlas emitted repeated `luma.gl` shader link errors under headless
  SwiftShader. This may be a software-renderer limitation, but a graceful
  compatibility path and a hardware-browser trace are required.
- Atlas `performance.memory.usedJSHeapSize` peaked near 1.58 GB while CDP's JS
  heap metric reported 310 MB. The disagreement suggests large external/
  ArrayBuffer/WebAssembly allocations; both are risk signals, not a precise
  production memory certificate.

## Blocking performance gates

1. Introduce a release-bound workspace projection: only fields consumed by
   Atlas/Chronos/Scholar, compact asserted-edge view, view-specific exact totals,
   duplicate detection, and release mismatch failure.
2. Bound Chronos DOM and prove that progressive disclosure/search still reaches
   every matching KG node.
3. Make snapshot-only `works/stats` degrade cleanly instead of returning 500.
4. Re-run this lab after the compact contract, then run hardware Chrome traces
   on representative desktop and mobile devices. Do not call the result
   “AAA”, “60 FPS”, or Core Web Vitals compliant until those traces pass fixed
   budgets.

Initial budgets for the next trace:

- Workspace graph API transfer: ≤ 20 MB uncompressed and ≤ 5 MB compressed.
- Scholar/Chronos ready: ≤ 1.5 s on the local cold laboratory run.
- Atlas ready: ≤ 2.5 s on the local cold laboratory run.
- Chronos live DOM: ≤ 3,500 elements at the default view.
- No task over 200 ms after the initial graph response; p95 interaction frame
  ≤ 16.7 ms on hardware Chrome.
- No console/page errors in any mode.

## Post-P0 counter-trace

Root repeated the same cold-context protocol after introducing the compact,
release-pinned workspace API and bounded Chronos rendering. The snapshot had
23,246 nodes and 55,792 asserted edges. Intercepted API responses were served
uncompressed by local FastAPI, so the byte column below is the conservative
raw transfer rather than the projected production gzip size.

| Mode | Ready before | Ready after | API before | API after | CDP heap before | CDP heap after | DOM before | DOM after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scholar | 2,080 ms | 816 ms | 130.46 MB | 12.76 MB | 187.8 MB | 30.1 MB | 2,637 | 2,651 |
| Chronos | 2,083 ms | 840 ms | 130.46 MB | 12.76 MB | 176.9 MB | 68.9 MB | 24,366 | 1,788 |
| Atlas | 3,511 ms | 2,063 ms | 130.46 MB | 12.76 MB | 310.4 MB | 136.7 MB | 4,129 | 4,129 |

Post-P0 main-thread observations:

- Scholar: one long task, 57 ms maximum; no console/page error.
- Chronos: two long tasks, 72 ms maximum; 316 timeline-node buttons in the
  measured default view; no console/page error.
- Atlas: long-task maximum fell from 618 ms to 364 ms, but repeated luma.gl
  shader/device errors and one uncaught page error remained under SwiftShader.
  `performance.memory` still reported roughly 1.40 GB while CDP reported
  136.7 MB, consistent with substantial non-JS/external graphics allocation.

The compact contract meets the initial raw-transfer, ready-time and Chronos DOM
budgets. The Atlas compatibility/error budget does not pass. Hardware Chrome,
mobile-device and interaction traces also remain required before certification.

## Software-renderer recovery pass

Atlas now performs a strict WebGL2 preflight with
`failIfMajorPerformanceCaveat` and rejects known software renderers before
Cosmograph allocates GPU/Arrow surfaces. In the same SwiftShader laboratory:

- the compatibility surface appeared in 451 ms;
- no canvas was instantiated;
- measured JS heap was about 15.2 MB;
- no console or page error occurred;
- the surface retained explicit Scholar and Chronos continuations;
- selecting Scholar preserved the release permalink and rendered its 240-row
  first table page successfully.

This closes the software-renderer crash/recovery defect. It does not substitute
for a hardware-GPU Atlas FPS/memory trace, and the Atlas-only Cosmograph vendor
chunk is still downloaded before the in-module capability probe. Moving the
probe above that dynamic import remains a possible P1 bandwidth refinement.

## P0 implementation estimate (post-fix code, trace not yet rerun)

This section is a deterministic serialization estimate over the local snapshot,
not a replacement for the Chromium protocol above. The data files were read
only; no KG/corpus row was changed.

At the post-fix measurement point the asserted snapshot contained 23,246 nodes
and 55,792 edges (111,584 rows with materialized inverse twins). FastAPI
`TestClient` serialized every real workspace page at the production 50,000-row
limit; gzip figures use level 6:

| Resource | Uncompressed | gzip level 6 estimate |
| --- | ---: | ---: |
| Workspace stats | 382 B | 256 B |
| Node summaries (one page; descriptions loaded on selection) | 3.63 MiB | 0.30 MiB |
| Asserted edges (two pages) | 8.52 MiB | 1.58 MiB |
| Initial graph total | **12.16 MiB** | **1.88 MiB** |

Including every node description would have made even the projected node list
35.46 MiB (9.38 MiB gzip) and the combined graph about 43.98 MiB. The release-bound
single-node detail endpoint is therefore part of the P0 transfer fix, not only
an optional refinement. Against the 130.46 MB baseline body, the estimated
initial uncompressed graph reduction is about 90.2%.

Chronos now mounts at most 24 node rows per period. The measured snapshot has
16 period labels, so its default row-button ceiling is 384 rather than a
percentage of all 20k nodes. Search still scans every in-memory node and each
period exposes accessible previous/next paging, so off-page results remain
explicitly reachable without allowing the live DOM to grow with corpus size.

`/api/works/stats` now returns either database stats, partial read-only
`data/stats.json` aggregates, or a nullable typed `unavailable` response. A
snapshot-only backend no longer turns missing PostgreSQL into HTTP 500, and
unknown fields are never misreported as zero.

The next action remains a full rerun of the same browser lab. Only that rerun
can report post-fix ready time, CDP heap, DOM total and long-task results.
