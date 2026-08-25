import type { KGEdge, KGNode } from '../../types';
import type { AtlasEdgeMeta, AtlasNodeMeta } from './AtlasHelpers';

export const GRAPH_PAGE_SIZE = 50_000;
export const MAX_PANEL_RELATIONSHIPS = 32;

export type GraphResource = 'nodes' | 'edges' | 'snapshot';
export type GraphDataIntegrityCode =
  | 'invalid_total'
  | 'invalid_release'
  | 'release_mismatch'
  | 'invalid_page'
  | 'invalid_item'
  | 'duplicate_item'
  | 'count_mismatch';

export class GraphDataIntegrityError extends Error {
  readonly name = 'GraphDataIntegrityError';
  readonly code: GraphDataIntegrityCode;
  readonly resource: GraphResource;
  readonly details: {
    expected?: number;
    actual?: number;
    id?: string;
    expectedRelease?: string;
    actualRelease?: string;
  };

  constructor(
    code: GraphDataIntegrityCode,
    resource: GraphResource,
    message: string,
    details: {
      expected?: number;
      actual?: number;
      id?: string;
      expectedRelease?: string;
      actualRelease?: string;
    } = {},
  ) {
    super(message);
    this.code = code;
    this.resource = resource;
    this.details = details;
  }
}

export interface GraphRelationship {
  id: string;
  label: string;
  type: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
}

export type GraphRelationships = Map<string, GraphRelationship[]>;

interface GraphReleaseContract {
  release_id?: unknown;
  served_total_nodes?: unknown;
  served_total_edges?: unknown;
}

interface GraphStatsResponse extends GraphReleaseContract {
  snapshot_stale?: unknown;
}

export interface GraphPageClient {
  getWorkspaceStats(): Promise<GraphStatsResponse>;
  getWorkspaceNodes(filters: { limit: number; offset: number; release_id: string }): Promise<
    GraphReleaseContract & { nodes: KGNode[] }
  >;
  getWorkspaceEdges(filters: { limit: number; offset: number; release_id: string }): Promise<
    GraphReleaseContract & { edges: KGEdge[] }
  >;
}

interface GraphPageItem {
  id?: unknown;
  edge_id?: unknown;
}

interface ValidatedGraphRelease {
  releaseId: string;
  servedTotalNodes: number;
  servedTotalEdges: number;
}

interface SnapshotPage<T extends GraphPageItem> extends GraphReleaseContract {
  items: T[];
}

interface FetchAllPagesOptions<T extends GraphPageItem> {
  resource: 'nodes' | 'edges';
  expectedRelease: ValidatedGraphRelease;
  pageSize?: number;
  firstPage?: SnapshotPage<T>;
  fetchPage: (request: { limit: number; offset: number }) => Promise<SnapshotPage<T>>;
}

function validatedTotal(resource: GraphResource, value: unknown): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) {
    throw new GraphDataIntegrityError(
      'invalid_total',
      resource,
      `The knowledge-graph statistics API returned an invalid ${resource} total.`,
    );
  }
  return value;
}

function validatedStatsRelease(stats: GraphStatsResponse): ValidatedGraphRelease {
  if (typeof stats?.release_id !== 'string' || stats.release_id.length === 0) {
    throw new GraphDataIntegrityError(
      'invalid_release',
      'snapshot',
      'The knowledge-graph statistics API did not identify its served release.',
    );
  }
  return {
    releaseId: stats.release_id,
    servedTotalNodes: validatedTotal('nodes', stats.served_total_nodes),
    servedTotalEdges: validatedTotal('edges', stats.served_total_edges),
  };
}

function validatePageRelease(
  resource: 'nodes' | 'edges',
  page: GraphReleaseContract | null | undefined,
  expected: ValidatedGraphRelease,
): void {
  if (page?.release_id !== expected.releaseId) {
    throw new GraphDataIntegrityError(
      'release_mismatch',
      resource,
      `The ${resource} page belongs to a different knowledge-graph release.`,
      {
        expectedRelease: expected.releaseId,
        actualRelease: typeof page?.release_id === 'string' ? page.release_id : undefined,
      },
    );
  }

  const pageNodes = validatedTotal('nodes', page.served_total_nodes);
  const pageEdges = validatedTotal('edges', page.served_total_edges);
  if (
    pageNodes !== expected.servedTotalNodes ||
    pageEdges !== expected.servedTotalEdges
  ) {
    throw new GraphDataIntegrityError(
      'release_mismatch',
      resource,
      `The ${resource} page advertises totals that differ from its release statistics.`,
      {
        expected:
          resource === 'nodes' ? expected.servedTotalNodes : expected.servedTotalEdges,
        actual: resource === 'nodes' ? pageNodes : pageEdges,
        expectedRelease: expected.releaseId,
        actualRelease: expected.releaseId,
      },
    );
  }
}

/**
 * Fetch every page of a graph resource and prove that the assembled result
 * matches the count advertised by `/api/kg/stats`.
 *
 * A full final page is followed by one probe request. This matters when the
 * total is an exact multiple of the API page limit: stopping at 50,000 would
 * otherwise be indistinguishable from silent truncation. Duplicate IDs are
 * rejected as an explicit pagination/snapshot integrity failure.
 */
export async function fetchAllGraphPages<T extends GraphPageItem>({
  resource,
  expectedRelease,
  pageSize = GRAPH_PAGE_SIZE,
  firstPage,
  fetchPage,
}: FetchAllPagesOptions<T>): Promise<T[]> {
  if (!Number.isSafeInteger(pageSize) || pageSize <= 0) {
    throw new Error(`Invalid graph page size: ${pageSize}`);
  }

  const items: T[] = [];
  const seenIds = new Set<string>();
  let offset = 0;
  let pageIndex = 0;
  const expectedTotal = resource === 'nodes'
    ? expectedRelease.servedTotalNodes
    : expectedRelease.servedTotalEdges;

  while (true) {
    const response = pageIndex === 0 && firstPage
      ? firstPage
      : await fetchPage({ limit: pageSize, offset });
    validatePageRelease(resource, response, expectedRelease);
    const page = response.items;

    if (!Array.isArray(page) || page.length > pageSize) {
      throw new GraphDataIntegrityError(
        'invalid_page',
        resource,
        `The paginated ${resource} API returned an invalid page at offset ${offset}.`,
        { actual: Array.isArray(page) ? page.length : undefined },
      );
    }

    for (const item of page) {
      if (!item || typeof item !== 'object') {
        throw new GraphDataIntegrityError(
          'invalid_item',
          resource,
          `The paginated ${resource} API returned an invalid item at offset ${offset}.`,
        );
      }

      const stableId = typeof item.id === 'string' && item.id.length > 0
        ? item.id
        : typeof item.edge_id === 'string' && item.edge_id.length > 0
          ? item.edge_id
          : null;

      // Nodes are addressable objects and must always have an ID. The legacy
      // edge endpoint omits its DB edge_id in some deployments; edge count,
      // terminal-page and overrun checks still prove pagination completeness.
      if (resource === 'nodes' && !stableId) {
        throw new GraphDataIntegrityError(
          'invalid_item',
          resource,
          `The paginated nodes API returned an item without a stable ID at offset ${offset}.`,
        );
      }
      if (stableId && seenIds.has(stableId)) {
        throw new GraphDataIntegrityError(
          'duplicate_item',
          resource,
          `The paginated ${resource} API returned duplicate ID ${stableId}.`,
          { id: stableId, actual: items.length },
        );
      }
      if (stableId) seenIds.add(stableId);
      items.push(item);
    }

    if (items.length > expectedTotal) {
      throw new GraphDataIntegrityError(
        'count_mismatch',
        resource,
        `The ${resource} API returned more rows than /api/kg/stats advertises.`,
        { expected: expectedTotal, actual: items.length },
      );
    }

    if (page.length < pageSize) break;

    offset += page.length;
    pageIndex += 1;
  }

  if (items.length !== expectedTotal) {
    throw new GraphDataIntegrityError(
      'count_mismatch',
      resource,
      `The ${resource} API count does not match /api/kg/stats.`,
      { expected: expectedTotal, actual: items.length },
    );
  }

  return items;
}

/**
 * Resolve the workspace release first, then pin every node/edge request to it.
 * The graph is returned only after both count checks pass, so neither a
 * partial graph nor pages straddling a backend reload can reach the renderer.
 */
export async function loadCompleteKnowledgeGraph(
  client: GraphPageClient,
  pageSize = GRAPH_PAGE_SIZE,
): Promise<{ nodes: KGNode[]; edges: KGEdge[]; release_id: string }> {
  const stats = await client.getWorkspaceStats();
  const expectedRelease = validatedStatsRelease(stats);
  const pageContract = { release_id: expectedRelease.releaseId };
  const [firstNodesResponse, firstEdges] = await Promise.all([
    client.getWorkspaceNodes({ limit: pageSize, offset: 0, ...pageContract }),
    client.getWorkspaceEdges({ limit: pageSize, offset: 0, ...pageContract }),
  ]);
  const firstNodes = firstNodesResponse?.nodes;
  const firstEdgeItems = firstEdges?.edges;

  if (!Array.isArray(firstNodes)) {
    throw new GraphDataIntegrityError(
      'invalid_page',
      'nodes',
      'The paginated nodes API returned an invalid first page.',
    );
  }
  if (!Array.isArray(firstEdgeItems)) {
    throw new GraphDataIntegrityError(
      'invalid_page',
      'edges',
      'The paginated edges API returned an invalid first page.',
    );
  }

  const [nodes, edges] = await Promise.all([
    fetchAllGraphPages({
      resource: 'nodes',
      expectedRelease,
      pageSize,
      firstPage: { ...firstNodesResponse, items: firstNodes },
      fetchPage: ({ limit, offset }) =>
        client.getWorkspaceNodes({ limit, offset, ...pageContract }).then((page) => ({
          ...page,
          items: page.nodes,
        })),
    }),
    fetchAllGraphPages({
      resource: 'edges',
      expectedRelease,
      pageSize,
      firstPage: { ...firstEdges, items: firstEdgeItems },
      fetchPage: ({ limit, offset }) =>
        client.getWorkspaceEdges({ limit, offset, ...pageContract }).then((page) => ({
          ...page,
          items: page.edges,
        })),
    }),
  ]);

  return { nodes, edges, release_id: expectedRelease.releaseId };
}

/** Build panel relationships with one node index: O(N + E) lookups. */
export function buildRelationships(
  meta: ReadonlyArray<AtlasNodeMeta>,
  edges: ReadonlyArray<AtlasEdgeMeta>,
): GraphRelationships {
  const relationships: GraphRelationships = new Map();
  const metaById = new Map<string, AtlasNodeMeta>();

  for (const node of meta) {
    metaById.set(node.id, node);
    relationships.set(node.id, []);
  }

  for (const edge of edges) {
    const source = metaById.get(edge.source);
    const target = metaById.get(edge.target);

    if (source && target) {
      relationships.get(source.id)?.push({
        id: target.id,
        label: target.label,
        type: target.typeKey,
        relation: edge.relation,
        direction: 'outgoing',
      });
      relationships.get(target.id)?.push({
        id: source.id,
        label: source.label,
        type: source.typeKey,
        relation: edge.relation,
        direction: 'incoming',
      });
    }
  }

  // Keep the detail panel bounded. Sorting uses the same node index and only
  // touches each node's local adjacency list.
  relationships.forEach((relations, id) => {
    relations.sort(
      (a, b) =>
        (metaById.get(b.id)?.importance ?? 0) -
        (metaById.get(a.id)?.importance ?? 0),
    );
    relationships.set(id, relations.slice(0, MAX_PANEL_RELATIONSHIPS));
  });

  return relationships;
}

export function shouldShowKnowledgeGraphLoader({
  loading,
  graphReady,
  hasError,
}: {
  loading: boolean;
  graphReady: boolean;
  hasError: boolean;
}): boolean {
  return !hasError && (loading || !graphReady);
}
