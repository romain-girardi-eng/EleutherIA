// frontend/src/components/kg/NodeReducer.ts
import type { KGNodeAttributes } from '@/types/sigma';
import { shouldShowNode } from './SemanticZoomController';
import type { ZoomLevel } from '@/types/sigma';

export interface NodeReducerState {
  zoomLevel: ZoomLevel;
  hoveredNode: string | null;
  selectedNode: string | null;
  hiddenNodes: Set<string>;
  nodeDegrees: Map<string, number>;
  expandedWorks: Set<string>;
  hoveredNeighbors: Set<string>;
}

export function createNodeReducer(state: NodeReducerState) {
  return (
    node: string,
    data: KGNodeAttributes,
  ): Partial<KGNodeAttributes> & { hidden?: boolean } => {
    const { zoomLevel, hoveredNode, selectedNode, hiddenNodes, nodeDegrees, expandedWorks, hoveredNeighbors } = state;

    if (hiddenNodes.has(node)) {
      return { hidden: true };
    }

    // Safety net: Sigma crashes if any visible node has non-finite x/y.
    // Catch any position corruption that slipped past layout sanitization.
    if (!Number.isFinite(data.x) || !Number.isFinite(data.y)) {
      return { hidden: true };
    }

    const degree = nodeDegrees.get(node) ?? 0;
    const isExpanded = data.nodeType === 'passage' && expandedWorks.size > 0;

    if (!shouldShowNode(data.nodeType, zoomLevel, degree, isExpanded)) {
      return { hidden: true };
    }

    if (node === hoveredNode || node === selectedNode) {
      return { zIndex: 2, forceLabel: true };
    }

    if (hoveredNode) {
      if (hoveredNeighbors.has(node)) {
        return { forceLabel: true };
      }
      return { color: 'rgba(255,255,255,0.1)', label: '' };
    }

    if (data.isAggregate && !data.passagesExpanded && data.passageCount) {
      return { label: `${data.label} (${data.passageCount})` };
    }

    return {};
  };
}
