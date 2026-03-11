// frontend/src/components/kg/EdgeFilterReducer.ts
import type { KGEdgeAttributes } from '@/types/sigma';
import { shouldShowEdge } from './SemanticZoomController';
import type { ZoomLevel } from '@/types/sigma';

export interface EdgeReducerState {
  zoomLevel: ZoomLevel;
  hoveredNode: string | null;
  selectedNode: string | null;
  hiddenNodes: Set<string>;
}

export function createEdgeReducer(state: EdgeReducerState) {
  return (
    edge: string,
    data: KGEdgeAttributes & { source: string; target: string },
  ): Partial<KGEdgeAttributes> & { hidden?: boolean } => {
    const { zoomLevel, hoveredNode, selectedNode, hiddenNodes } = state;

    if (hiddenNodes.has(data.source) || hiddenNodes.has(data.target)) {
      return { hidden: true };
    }

    const isHovered =
      hoveredNode === data.source ||
      hoveredNode === data.target ||
      selectedNode === data.source ||
      selectedNode === data.target;

    if (!shouldShowEdge(data.category, zoomLevel, isHovered)) {
      return { hidden: true };
    }

    if (hoveredNode && !isHovered) {
      return { color: 'rgba(255,255,255,0.05)', size: 0.5 };
    }

    return {};
  };
}
