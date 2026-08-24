# Multi-mode workspace code-splitting audit

Measured on 2026-08-24 with the production Vite build at the original
code-splitting cut. Sizes below are historical; the current
renderer-isolation extraction must be remeasured in the final RC build. Shared
application/runtime chunks that are equal before and after are excluded from
the comparison.

## Before

The route module statically imported `@cosmograph/react`. Opening Atlas,
Chronos, or Scholar therefore made the WebGL dependency part of the route's
mandatory module graph.

| Chunk | Raw | Gzip |
|---|---:|---:|
| `CosmographPage` | 106.08 kB | 30.10 kB |
| `cosmograph-vendor` | 1,850.71 kB | 419.85 kB |
| Mode-specific mandatory total | 1,956.79 kB | 449.95 kB |

## After

The route is now a state-preserving shell. Each surface is a dynamic import,
and only `AtlasWorkspace` statically imports Cosmograph.

| Chunk | Raw | Gzip |
|---|---:|---:|
| `CosmographPage` shell | 23.88 kB | 8.66 kB |
| `ScholarWorkspace` | 10.31 kB | 3.14 kB |
| `ChronosWorkspace` | 12.97 kB | 4.41 kB |
| `AtlasWorkspace` | 62.13 kB | 17.90 kB |
| `cosmograph-vendor` (Atlas only) | 1,850.71 kB | 419.85 kB |

Mode-specific route cost from these chunks:

- Scholar: 11.80 kB gzip, 438.15 kB less than before (about 97.4%).
- Chronos: 13.07 kB gzip, 436.88 kB less than before (about 97.1%).
- Atlas: 446.41 kB gzip, 3.54 kB less than before. Atlas still intentionally
  pays the renderer cost, but only when selected.

`npm run test:workspace-split` inspects the generated chunks and fails if:

- the route shell statically imports `cosmograph-vendor`;
- Chronos or Scholar statically imports it;
- Atlas stops owning the renderer import; or
- Atlas ceases to be a dynamic import from the shell.

Unit tests separately guard the source boundary and require the loading state
to be announced with motion gated behind `motion-safe`.

## Measurement limits

No connected browser performance trace was available for this audit. These
results prove build/module boundaries and transfer-size changes; they do not
prove FPS, LCP, INP, CLS, parse time, GPU time, or real-network latency. Those
metrics must be measured later with a browser trace on representative desktop
and mobile hardware. The 1.85 MB raw Cosmograph vendor remains a valid Atlas
optimization target even though it no longer affects Chronos or Scholar.
