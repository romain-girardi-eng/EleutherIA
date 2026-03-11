// frontend/src/components/kg/SemanticZoomController.ts
import { ZoomLevel, ALWAYS_VISIBLE_CATEGORIES, type EdgeCategory } from '@/types/sigma';


export function getZoomLevel(cameraRatio: number): ZoomLevel {
  if (cameraRatio > 1.2) return ZoomLevel.Overview;
  if (cameraRatio >= 0.4) return ZoomLevel.Community;
  if (cameraRatio >= 0.08) return ZoomLevel.Neighborhood;
  return ZoomLevel.Detail;
}

export function shouldShowNode(
  nodeType: string,
  zoom: ZoomLevel,
  _degree: number,
  isExpanded: boolean,
): boolean {
  if (zoom === ZoomLevel.Detail) return true;
  // Always hide aggregated passages unless expanded
  if (nodeType === 'passage') {
    return isExpanded;
  }
  // Show all non-passage nodes at every zoom level
  return true;
}

export function shouldShowEdge(
  category: EdgeCategory,
  zoom: ZoomLevel,
  isHovered: boolean,
): boolean {
  if (zoom === ZoomLevel.Overview) return false;
  if (zoom === ZoomLevel.Detail) return true;
  if (ALWAYS_VISIBLE_CATEGORIES.includes(category)) return true;
  return isHovered;
}

export function getHullOpacity(cameraRatio: number): number {
  if (cameraRatio >= 1.2) return 0.15;
  if (cameraRatio < 0.4) return 0;
  return 0.15 * ((cameraRatio - 0.4) / 0.8);
}
