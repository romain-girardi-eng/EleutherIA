// frontend/src/components/kg/PassageAggregation.ts
import type Graph from 'graphology';
import type { KGNodeAttributes, KGEdgeAttributes } from '@/types/sigma';

export function aggregatePassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
): Set<string> {
  const hidden = new Set<string>();
  const workPassageCounts = new Map<string, number>();

  graph.forEachNode((nodeId, attrs) => {
    if (attrs.type !== 'passage') return;
    hidden.add(nodeId);

    // Find parent work via incoming 'contains' edge
    graph.forEachInEdge(nodeId, (_edgeId, edgeAttrs, sourceId, _targetId, sourceAttrs) => {
      if (edgeAttrs.relation === 'contains' && sourceAttrs.type === 'work') {
        workPassageCounts.set(sourceId, (workPassageCounts.get(sourceId) ?? 0) + 1);
      }
    });
  });

  // Also check outgoing 'part_of' edges (inverse of contains)
  graph.forEachNode((nodeId, attrs) => {
    if (attrs.type !== 'passage' || !hidden.has(nodeId)) return;
    graph.forEachOutEdge(nodeId, (_edgeId, edgeAttrs, _sourceId, targetId, _sourceAttrs, targetAttrs) => {
      if (edgeAttrs.relation === 'part_of' && targetAttrs.type === 'work') {
        if (!workPassageCounts.has(targetId)) {
          workPassageCounts.set(targetId, 0);
        }
        workPassageCounts.set(targetId, workPassageCounts.get(targetId)! + 1);
      }
    });
  });

  for (const [workId, count] of workPassageCounts) {
    graph.setNodeAttribute(workId, 'passageCount', count);
    graph.setNodeAttribute(workId, 'isAggregate', true);
    graph.setNodeAttribute(workId, 'passagesExpanded', false);
  }

  return hidden;
}

export function expandWorkPassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  workId: string,
  hidden: Set<string>,
): string[] {
  const workX = graph.getNodeAttribute(workId, 'x');
  const workY = graph.getNodeAttribute(workId, 'y');
  const restored: string[] = [];

  graph.forEachOutEdge(workId, (_edgeId, edgeAttrs, _sourceId, targetId, _sourceAttrs, targetAttrs) => {
    if (edgeAttrs.relation === 'contains' && targetAttrs.type === 'passage' && hidden.has(targetId)) {
      restored.push(targetId);
    }
  });

  const count = restored.length;
  const radius = Math.min(80 * Math.sqrt(count / 10), 200);

  restored.forEach((nodeId, i) => {
    const angle = (2 * Math.PI * i) / count;
    graph.setNodeAttribute(nodeId, 'x', workX + radius * Math.cos(angle));
    graph.setNodeAttribute(nodeId, 'y', workY + radius * Math.sin(angle));
    hidden.delete(nodeId);
  });

  graph.setNodeAttribute(workId, 'passagesExpanded', true);
  return restored;
}

export function collapseWorkPassages(
  graph: Graph<KGNodeAttributes, KGEdgeAttributes>,
  workId: string,
  hidden: Set<string>,
): void {
  graph.forEachOutEdge(workId, (_edgeId, edgeAttrs, _sourceId, targetId, _sourceAttrs, targetAttrs) => {
    if (edgeAttrs.relation === 'contains' && targetAttrs.type === 'passage') {
      hidden.add(targetId);
    }
  });
  graph.setNodeAttribute(workId, 'passagesExpanded', false);
}
