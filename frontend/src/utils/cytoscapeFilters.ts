import type { CytoscapeData, CytoscapeElement, KGFilterState, KGSelectionState } from '../types';

interface FilterOptions {
  maxNodes?: number;
}

export function filterCytoscapeData(
  data: CytoscapeData | null,
  filters: KGFilterState,
  selection?: KGSelectionState,
  options?: FilterOptions,
): CytoscapeData | null {
  if (!data) {
    return null;
  }

  const { nodeTypes, periods, schools, relations, searchTerm } = filters;
  const search = (searchTerm || '').trim().toLowerCase();
  const maxNodes = options?.maxNodes ?? 200;
  const selectionState: KGSelectionState = selection || { nodes: [], edges: [], focusNodeId: null };

  const degreeMap = new Map<string, number>();
  data.elements.edges.forEach((edge) => {
    const src = edge.data.source ?? '';
    const tgt = edge.data.target ?? '';
    if (src) degreeMap.set(src, (degreeMap.get(src) || 0) + 1);
    if (tgt) degreeMap.set(tgt, (degreeMap.get(tgt) || 0) + 1);
  });

  const matchesNode = (element: CytoscapeElement) => {
    const nodeData = element.data;
    if (nodeTypes.length && nodeData.type && !nodeTypes.includes(nodeData.type)) {
      return false;
    }
    if (periods.length && nodeData.period && !periods.includes(nodeData.period)) {
      return false;
    }
    if (schools.length && nodeData.school && !schools.includes(nodeData.school)) {
      return false;
    }
    if (search) {
      const haystack = [
        nodeData.label,
        nodeData.description,
        nodeData.summary,
        nodeData.period,
        nodeData.school,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      if (!haystack.includes(search)) {
        return false;
      }
    }
    return true;
  };

  const nodeMap = new Map(data.elements.nodes.map((node) => [node.data.id, node]));
  const baseNodes: CytoscapeElement[] = data.elements.nodes.filter(matchesNode);

  selectionState.nodes.forEach((nodeId) => {
    if (!baseNodes.some((node) => node.data.id === nodeId)) {
      const selectedNode = nodeMap.get(nodeId);
      if (selectedNode) {
        baseNodes.push(selectedNode);
      }
    }
  });

  const relationFilter = new Set(relations);
  const nodeIdSet = new Set(baseNodes.map((node) => node.data.id));

  const filteredEdges = data.elements.edges.filter((edge) => {
    const relation = edge.data.relation ?? '';
    const source = edge.data.source ?? '';
    const target = edge.data.target ?? '';

    if (relationFilter.size && relation && !relationFilter.has(relation)) {
      return false;
    }

    return source && target && nodeIdSet.has(source) && nodeIdSet.has(target);
  });

  filteredEdges.forEach((edge) => {
    const source = edge.data.source ?? '';
    const target = edge.data.target ?? '';
    if (source) nodeIdSet.add(source);
    if (target) nodeIdSet.add(target);
  });

  let finalNodes = data.elements.nodes.filter((node) => nodeIdSet.has(node.data.id));

  if (finalNodes.length > maxNodes) {
    finalNodes = finalNodes
      .slice()
      .sort((a, b) => {
        const degreeDiff = (degreeMap.get(b.data.id) || 0) - (degreeMap.get(a.data.id) || 0);
        if (degreeDiff !== 0) {
          return degreeDiff;
        }
        return (a.data.label || '').localeCompare(b.data.label || '');
      })
      .slice(0, maxNodes);
    const limitedSet = new Set(finalNodes.map((node) => node.data.id));
    const limitedEdges = filteredEdges.filter((edge) => {
      const source = edge.data.source ?? '';
      const target = edge.data.target ?? '';
      return source && target && limitedSet.has(source) && limitedSet.has(target);
    });

    return {
      elements: {
        nodes: finalNodes,
        edges: limitedEdges,
      },
      meta: data.meta,
    };
  }

  return {
    elements: {
      nodes: finalNodes,
      edges: filteredEdges,
    },
    meta: data.meta,
  };
}
