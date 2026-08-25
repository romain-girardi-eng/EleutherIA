export type AtlasTab = 'explore' | 'atlas' | 'full' | 'path' | 'filter';
export type AtlasZoomTier = 'overview' | 'mid' | 'close';

/** Resolve detail relative to the fitted scale of the current projection.
 * A complete 23k-node fit can start near 0.06 while the curated Atlas starts
 * near 1, so absolute thresholds make semantic zoom unreachable in Full KG. */
export function semanticZoomTier(zoom: number, baseline: number): AtlasZoomTier {
  const ratio = zoom / Math.max(0.0001, baseline);
  if (ratio >= 4.2) return 'close';
  if (ratio >= 1.7) return 'mid';
  return 'overview';
}

export interface AtlasSemanticZoomConfig {
  linkVisibilityDistanceRange: [number, number];
  linkVisibilityMinTransparency: number;
  showTopLabelsLimit: number;
  showDynamicLabels: boolean;
  showDynamicLabelsLimit: number;
  pointSamplingDistance: number;
  pointSizeScale: number;
  linkWidthScale: number;
}

export interface AtlasAutoFitState {
  cameraTransitionActive: boolean;
  focusedNodeId: string | null;
  focusedConstellation: string | null;
}

/** Stable semantic identity for filter state. Camera/history updates can
 * recreate the surrounding workspace object without changing these values;
 * sorting also prevents selection order from rebuilding the GPU dataset. */
export function atlasFilterKey(filters: {
  periods: readonly string[];
  types: readonly string[];
  schools: readonly string[];
}): string {
  return JSON.stringify({
    periods: [...filters.periods].sort(),
    types: [...filters.types].sort(),
    schools: [...filters.schools].sort(),
  });
}

/** Only dataset/layout/device changes may reconfigure the heavy renderer. */
export function atlasRendererRevision<T>(
  dataset: T,
  isMobile: boolean,
): { dataset: T; isMobile: boolean } {
  return { dataset, isMobile };
}

/** Startup re-framing is allowed only while the landing overview is still
 * untouched. Delayed fit callbacks must never override a scholar's node focus
 * or an authored constellation dive. */
export function shouldAutoFitAtlasView({
  cameraTransitionActive,
  focusedNodeId,
  focusedConstellation,
}: AtlasAutoFitState): boolean {
  return !cameraTransitionActive && focusedNodeId === null && focusedConstellation === null;
}

/** The legible curated projection is the desktop entry point; touch devices
 * enter the relational Explore surface before allocating the WebGL canvas. */
export function defaultAtlasTab(isMobile: boolean): AtlasTab {
  return isMobile ? 'explore' : 'atlas';
}

/** Only these lightweight renderer values change during camera movement.
 * Point/link data and the authored Atlas layout never re-enter React. */
export function semanticZoomConfig(
  tab: AtlasTab,
  tier: AtlasZoomTier,
  isMobile: boolean,
): AtlasSemanticZoomConfig {
  if (tab === 'atlas') {
    return {
      linkVisibilityDistanceRange: tier === 'close' ? [18, 110] : [34, 150],
      linkVisibilityMinTransparency: tier === 'overview' ? 0.025 : 0.075,
      showTopLabelsLimit: isMobile ? (tier === 'close' ? 18 : 8) : tier === 'close' ? 42 : tier === 'mid' ? 24 : 14,
      showDynamicLabels: tier !== 'overview',
      showDynamicLabelsLimit: isMobile ? 18 : tier === 'close' ? 56 : 28,
      pointSamplingDistance: tier === 'close' ? 18 : tier === 'mid' ? 34 : 72,
      pointSizeScale: tier === 'close' ? 1.34 : tier === 'mid' ? 1.12 : 0.92,
      linkWidthScale: tier === 'overview' ? 0.72 : tier === 'mid' ? 0.9 : 1,
    };
  }
  if (tier === 'close') {
    return {
      linkVisibilityDistanceRange: [16, 84],
      linkVisibilityMinTransparency: 0.12,
      showTopLabelsLimit: isMobile ? 48 : 180,
      showDynamicLabels: true,
      showDynamicLabelsLimit: isMobile ? 40 : 140,
      pointSamplingDistance: 16,
      pointSizeScale: 1.45,
      linkWidthScale: 1,
    };
  }
  if (tier === 'mid') {
    return {
      linkVisibilityDistanceRange: [34, 132],
      linkVisibilityMinTransparency: 0.06,
      showTopLabelsLimit: isMobile ? 22 : 64,
      showDynamicLabels: true,
      showDynamicLabelsLimit: isMobile ? 22 : 54,
      pointSamplingDistance: 34,
      pointSizeScale: 1.08,
      linkWidthScale: 0.7,
    };
  }
  return {
    linkVisibilityDistanceRange: [86, 260],
    linkVisibilityMinTransparency: 0.012,
    showTopLabelsLimit: isMobile ? 8 : 18,
    showDynamicLabels: false,
    showDynamicLabelsLimit: 0,
    pointSamplingDistance: 110,
    pointSizeScale: 0.72,
    linkWidthScale: 0.1,
  };
}
