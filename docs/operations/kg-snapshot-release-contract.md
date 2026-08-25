# KG snapshot release contract

The public graph list endpoints serve one immutable in-memory snapshot at a
time. Every `GET /api/kg/nodes` and `GET /api/kg/edges` response carries:

- `X-EleutherIA-KG-Release-ID`
- `X-EleutherIA-KG-Served-Total-Nodes`
- `X-EleutherIA-KG-Served-Total-Edges`

The headers are exposed through CORS. `GET /api/kg/stats` and
`GET /api/kg/statistics` expose the same values in their JSON bodies as
`release_id`, `served_total_nodes`, and `served_total_edges`. The legacy
`total_nodes` and `total_edges` aliases now describe the served release too.
They must never be overwritten with counts from a database that the process
has not loaded yet.

`release_id` is a SHA-256 digest of the ordered, canonicalized node and edge
rows. Ordering is part of the identity because it defines offset pagination.
`KGAnalytics.set_data()` computes the complete contract synchronously before
the event loop can serve another request.

## Live database drift

`/api/kg/stats` may additionally expose `live_total_nodes`,
`live_total_edges`, `live_node_types`, and `live_edge_types`. These are
diagnostics, not pagination totals. `snapshot_stale` is:

- `false` when the live database matches the loaded snapshot;
- `true` with `snapshot_stale_reasons` when it differs;
- `null` and `snapshot_status: "unknown"` when live counts are unavailable.

The served graph materializes ontology-declared inverse edges. Therefore the
raw live DB edge count is compared with `served_total_asserted_edges`, not with
`served_total_edges`, which includes derived inverses.

The frontend starts from the served totals in `/api/kg/stats`, requires every
node and edge page to repeat the same release ID and totals, and renders only
after all pages pass. A reload during pagination becomes an explicit retryable
integrity error; pages from different releases are never merged.

## Compact workspace view

Atlas, Chronos and Scholar use dedicated endpoints so the public/GraphRAG
records remain backward compatible:

- `GET /api/kg/workspace/stats`
- `GET /api/kg/workspace/nodes`
- `GET /api/kg/workspace/nodes/{node_id}`
- `GET /api/kg/workspace/edges`

The list endpoints are paginated envelopes. They repeat `release_id`,
`served_total_nodes` and view-specific `served_total_edges` in both the body
and release headers. After resolving stats, the browser sends that release as
`release_id` on every page. A process serving another release returns HTTP 409
with `code: "kg_release_mismatch"` before serializing rows.

Node summaries contain only `id`, `label`, `type`, `period`, `school`,
`scholarly_role`, `greek_term` and `latin_term` when present. Editorial
`description` is the dominant snapshot field, so it is loaded from the pinned
single-node endpoint only when a node is selected. Legacy `/nodes` and the
GraphRAG in-memory data keep complete metadata and descriptions.

Workspace edges contain only `id`, `source`, `target` and `relation`, in the
asserted `source -> target` direction. Ontology-derived inverse twins are not
serialized. Incoming relationships are obtained by indexing the target of the
same asserted edge; consumers must not reinterpret the asserted triple as its
ontology inverse relation.

This omission cannot remove weak connectivity or change an undirected shortest
path: every materialized inverse has endpoints `(target, source)` from one
asserted `(source, target)` edge, which is the same unordered endpoint pair.
The contract test compares connected components and all-pairs undirected path
lengths between asserted and materialized fixture graphs. Directed scholarly
meaning remains the asserted direction and relation label, rather than two
redundant triples.

A read-only audit of the 2026-08-24 local measurement snapshot found 54,186
distinct unordered endpoint pairs in both the 55,792 asserted-edge view and
the 111,584-row materialized view (`pairs_equal: true`), with the same 20 weak
components. This is observed confirmation of the endpoint-pair proof, not a
claim that inverse relation labels are interchangeable.

Workspace permalinks serialize that same `release_id`. When a URL names a
release, the shared Atlas/Chronos/Scholar provider compares it with the release
actually returned by the API before exposing graph data. A mismatch produces
an explicit integrity error; it never rewrites the old URL and silently replays
the scholarly state on another graph. URLs without a release are bound to the
served release after the first verified load. Browser back/forward and
undo/redo preserve this invariant.

## Deployment topology and expected-release cutover

`POST /api/kg/reload` atomically swaps the snapshot within one backend process
and returns the new release contract. The current production topology has one
serving `eleutheria-api` container, so there is no rolling multi-replica window:
the exact-SHA runbook stages and verifies PostgreSQL, then recreates that API
and its worker only after the atomic data swap.

`GET /api/health?expected_release_id=…` now applies the same fail-closed
precondition as workspace pagination. A different generation returns HTTP 409;
an uninitialized KG returns 503. The production Make target reads workspace
stats, checks served node/edge totals against the RC snapshot, then sends eight
public expected-release probes before the frontend is eligible for publication.

If production is scaled beyond one API replica, the issue automatically
reopens. A multi-replica controller must then:

1. stage and validate the database update without moving public traffic;
2. reload every candidate replica directly, not through one load-balanced
   `/reload` call;
3. require every replica to report the same `release_id` and served totals;
4. shift traffic to the new replica set in one routing operation;
5. retain the previous replica set until the new release passes health and
   GraphRAG smoke checks, then drain it;
6. alert when `/api/kg/stats` reports `snapshot_status: "stale"` or when active
   replicas advertise more than one release ID.

The compact workspace and health endpoints enforce server-side
expected-release preconditions. Legacy list endpoints intentionally retain
their historical query contract and expose release changes through headers;
clients using those routes must continue to validate pages themselves.
