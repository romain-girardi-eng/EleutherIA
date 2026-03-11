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

/**
 * Sigma v3 nodeReducer must return a COMPLETE object (not merged with
 * originals). Every code path must spread `data` so x/y and other
 * required attributes are always present.
 */
export function createNodeReducer(state: NodeReducerState) {
  return (
    node: string,
    data: KGNodeAttributes,
  ): Partial<KGNodeAttributes> & { hidden?: boolean; forceLabel?: boolean; zIndex?: number } => {
    const { zoomLevel, hoveredNode, selectedNode, hiddenNodes, nodeDegrees, expandedWorks, hoveredNeighbors } = state;

    if (hiddenNodes.has(node)) {
      return { ...data, hidden: true };
    }

    // Safety net: hide nodes with corrupt positions instead of crashing
    if (!Number.isFinite(data.x) || !Number.isFinite(data.y)) {
      return { ...data, x: 0, y: 0, hidden: true };
    }

    const degree = nodeDegrees.get(node) ?? 0;
    const isExpanded = data.nodeType === 'passage' && expandedWorks.size > 0;

    if (!shouldShowNode(data.nodeType, zoomLevel, degree, isExpanded)) {
      return { ...data, hidden: true };
    }

    if (node === hoveredNode || node === selectedNode) {
      return { ...data, zIndex: 2, forceLabel: true };
    }

    if (hoveredNode) {
      if (hoveredNeighbors.has(node)) {
        return { ...data, forceLabel: true };
      }
      return { ...data, color: 'rgba(255,255,255,0.1)', label: '' };
    }

    if (data.isAggregate && !data.passagesExpanded && data.passageCount) {
      return { ...data, label: `${data.label} (${data.passageCount})` };
    }

    return { ...data };
  };
}
