import { describe, expect, it, vi } from 'vitest';
import type { KGEdge, KGNode } from '../../types';
import type { AtlasEdgeMeta, AtlasNodeMeta } from './AtlasHelpers';
import {
  buildRelationships,
  fetchAllGraphPages,
  GraphDataIntegrityError,
  loadCompleteKnowledgeGraph,
  shouldShowKnowledgeGraphLoader,
  type GraphPageClient,
} from './graphRuntime';

function atlasNode(id: string, importance: number): AtlasNodeMeta {
  return {
    id,
    label: `Node ${id}`,
    type: 'concept',
    typeKey: 'concept',
    typeLabel: 'Concept',
    layer: 'ancient',
    periodLabel: 'Classical Greek',
    schoolLabel: 'Peripatetics',
    degree: importance,
    importance,
    color: '#60a5fa',
    opacity: 1,
    size: 8,
    description: '',
    greekTerm: '',
    latinTerm: '',
  };
}

function atlasEdge(id: string, source: string, target: string): AtlasEdgeMeta {
  return {
    id,
    source,
    target,
    relation: 'supports',
    relationLabel: 'Supports',
    category: 'doctrinal',
    width: 1,
    opacity: 0.5,
    color: '#94a3b8',
  };
}

function node(id: string): KGNode {
  return { id, label: id, type: 'concept' };
}

function edge(id: string, source = 'n1', target = 'n2'): KGEdge {
  return { id, source, target, relation: 'supports' };
}

const RELEASE_ID = 'kg-sha256-release-a';

function wireContract(
  servedTotalNodes: number,
  servedTotalEdges: number,
  releaseId = RELEASE_ID,
) {
  return {
    release_id: releaseId,
    served_total_nodes: servedTotalNodes,
    served_total_edges: servedTotalEdges,
  };
}

function expectedRelease(servedTotalNodes: number, servedTotalEdges: number) {
  return {
    releaseId: RELEASE_ID,
    servedTotalNodes,
    servedTotalEdges,
  };
}

describe('knowledge-graph loader readiness', () => {
  it('does not keep the intro mounted after real graph readiness', () => {
    expect(
      shouldShowKnowledgeGraphLoader({
        loading: false,
        graphReady: true,
        hasError: false,
      }),
    ).toBe(false);
  });

  it('keeps the cover only for real work and never over an error', () => {
    expect(
      shouldShowKnowledgeGraphLoader({
        loading: false,
        graphReady: false,
        hasError: false,
      }),
    ).toBe(true);
    expect(
      shouldShowKnowledgeGraphLoader({
        loading: true,
        graphReady: false,
        hasError: true,
      }),
    ).toBe(false);
  });
});

describe('buildRelationships', () => {
  it('indexes nodes once and builds correctly directed relationships', () => {
    const meta = [atlasNode('a', 1), atlasNode('b', 5), atlasNode('c', 3)];
    // Regression guard for the former E×N implementation: any Array.find()
    // lookup on the node collection makes this test fail immediately.
    Object.defineProperty(meta, 'find', {
      value: () => {
        throw new Error('linear node lookup used');
      },
    });

    const result = buildRelationships(meta, [
      atlasEdge('e1', 'a', 'b'),
      atlasEdge('e2', 'c', 'a'),
    ]);

    expect(result.get('a')).toEqual([
      {
        id: 'b',
        label: 'Node b',
        type: 'concept',
        relation: 'supports',
        direction: 'outgoing',
      },
      {
        id: 'c',
        label: 'Node c',
        type: 'concept',
        relation: 'supports',
        direction: 'incoming',
      },
    ]);
  });

  it('keeps only the 32 most important neighbours for the detail panel', () => {
    const center = atlasNode('center', 100);
    const neighbours = Array.from({ length: 40 }, (_, index) =>
      atlasNode(`n${index}`, index),
    );
    const edges = neighbours.map((item, index) =>
      atlasEdge(`e${index}`, center.id, item.id),
    );

    const result = buildRelationships([center, ...neighbours], edges);
    const centerRelationships = result.get(center.id) ?? [];

    expect(centerRelationships).toHaveLength(32);
    expect(centerRelationships[0]?.id).toBe('n39');
    expect(centerRelationships.at(-1)?.id).toBe('n8');
  });
});

describe('complete graph pagination', () => {
  it('loads every node and edge page and probes after an exactly full page', async () => {
    const getWorkspaceNodes = vi.fn(async ({ offset }: { limit: number; offset: number; release_id: string }) => ({
      nodes: offset === 0 ? [node('n1'), node('n2')] : [],
      ...wireContract(2, 3),
    }));
    const getWorkspaceEdges = vi.fn(async ({ offset }: { limit: number; offset: number; release_id: string }) => ({
      edges: offset === 0 ? [edge('e1'), edge('e2')] : [edge('e3')],
      ...wireContract(2, 3),
    }));
    const client: GraphPageClient = {
      getWorkspaceStats: vi.fn(async () => wireContract(2, 3)),
      getWorkspaceNodes,
      getWorkspaceEdges,
    };

    const result = await loadCompleteKnowledgeGraph(client, 2);

    expect(result.nodes.map((item) => item.id)).toEqual(['n1', 'n2']);
    expect(result.edges.map((item) => item.id)).toEqual(['e1', 'e2', 'e3']);
    expect(getWorkspaceNodes).toHaveBeenNthCalledWith(1, {
      limit: 2,
      offset: 0,
      release_id: RELEASE_ID,
    });
    expect(getWorkspaceNodes).toHaveBeenNthCalledWith(2, {
      limit: 2,
      offset: 2,
      release_id: RELEASE_ID,
    });
    expect(getWorkspaceEdges).toHaveBeenNthCalledWith(1, {
      limit: 2,
      offset: 0,
      release_id: RELEASE_ID,
    });
    expect(getWorkspaceEdges).toHaveBeenNthCalledWith(2, {
      limit: 2,
      offset: 2,
      release_id: RELEASE_ID,
    });
  });

  it('fails explicitly when paginated rows do not match the stats total', async () => {
    const promise = fetchAllGraphPages({
      resource: 'edges',
      expectedRelease: expectedRelease(2, 4),
      pageSize: 2,
      firstPage: {
        items: [edge('e1'), edge('e2')],
        ...wireContract(2, 4),
      },
      fetchPage: vi.fn(async () => ({
        items: [edge('e3')],
        ...wireContract(2, 4),
      })),
    });

    await expect(promise).rejects.toMatchObject({
      name: 'GraphDataIntegrityError',
      code: 'count_mismatch',
      resource: 'edges',
      details: { expected: 4, actual: 3 },
    } satisfies Partial<GraphDataIntegrityError>);
  });

  it('supports the legacy edge payload while still proving its total count', async () => {
    const legacyEdges: KGEdge[] = [
      { source: 'n1', target: 'n2', relation: 'supports' },
      { source: 'n2', target: 'n3', relation: 'opposes' },
    ];

    await expect(
      fetchAllGraphPages({
        resource: 'edges',
        expectedRelease: expectedRelease(3, 2),
        pageSize: 3,
        firstPage: { items: legacyEdges, ...wireContract(3, 2) },
        fetchPage: vi.fn(),
      }),
    ).resolves.toEqual(legacyEdges);
  });

  it('fails visibly instead of looping when an API repeats a page', async () => {
    const promise = fetchAllGraphPages({
      resource: 'edges',
      expectedRelease: expectedRelease(2, 3),
      pageSize: 2,
      firstPage: {
        items: [edge('e1'), edge('e2')],
        ...wireContract(2, 3),
      },
      fetchPage: vi.fn(async () => ({
        items: [edge('e2')],
        ...wireContract(2, 3),
      })),
    });

    await expect(promise).rejects.toMatchObject({
      name: 'GraphDataIntegrityError',
      code: 'duplicate_item',
      resource: 'edges',
      details: { id: 'e2' },
    } satisfies Partial<GraphDataIntegrityError>);
  });

  it('rejects a release change between edge pages', async () => {
    const client: GraphPageClient = {
      getWorkspaceStats: vi.fn(async () => wireContract(1, 3)),
      getWorkspaceNodes: vi.fn(async () => ({
        nodes: [node('n1')],
        ...wireContract(1, 3),
      })),
      getWorkspaceEdges: vi.fn(async ({ offset }) => ({
        edges: offset === 0 ? [edge('e1'), edge('e2')] : [edge('e3')],
        ...wireContract(
          1,
          3,
          offset === 0 ? RELEASE_ID : 'kg-sha256-release-b',
        ),
      })),
    };

    await expect(loadCompleteKnowledgeGraph(client, 2)).rejects.toMatchObject({
      name: 'GraphDataIntegrityError',
      code: 'release_mismatch',
      resource: 'edges',
      details: {
        expectedRelease: RELEASE_ID,
        actualRelease: 'kg-sha256-release-b',
      },
    } satisfies Partial<GraphDataIntegrityError>);
  });

  it('paginates against served totals, never ambiguous live total aliases', async () => {
    const client: GraphPageClient = {
      getWorkspaceStats: vi.fn(async () => ({
        ...wireContract(1, 1),
        total_nodes: 999,
        total_edges: 999,
        live_total_nodes: 999,
        live_total_edges: 999,
        snapshot_stale: true,
      })),
      getWorkspaceNodes: vi.fn(async () => ({
        nodes: [node('n1')],
        ...wireContract(1, 1),
      })),
      getWorkspaceEdges: vi.fn(async () => ({
        edges: [edge('e1')],
        ...wireContract(1, 1),
      })),
    };

    await expect(loadCompleteKnowledgeGraph(client, 2)).resolves.toMatchObject({
      nodes: [{ id: 'n1' }],
      edges: [{ id: 'e1' }],
      release_id: RELEASE_ID,
    });
  });
});
