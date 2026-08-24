export type AtlasTab = 'explore' | 'atlas' | 'full' | 'path' | 'filter';
export type AtlasZoomTier = 'overview' | 'mid' | 'close';

export interface AtlasSemanticZoomConfig {
  linkVisibilityDistanceRange: [number, number];
  linkVisibilityMinTransparency: number;
  showTopLabelsLimit: number;
}

export interface AtlasAutoFitState {
  cameraTransitionActive: boolean;
  focusedNodeId: string | null;
  focusedConstellation: string | null;
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
      linkVisibilityDistanceRange: [32, 120],
      linkVisibilityMinTransparency: 0.02,
      showTopLabelsLimit: isMobile ? 6 : 8,
    };
  }
  if (tier === 'close') {
    return {
      linkVisibilityDistanceRange: [20, 90],
      linkVisibilityMinTransparency: 0.09,
      showTopLabelsLimit: 120,
    };
  }
  if (tier === 'mid') {
    return {
      linkVisibilityDistanceRange: [40, 140],
      linkVisibilityMinTransparency: 0.05,
      showTopLabelsLimit: 36,
    };
  }
  return {
    linkVisibilityDistanceRange: [60, 200],
    linkVisibilityMinTransparency: 0.02,
    showTopLabelsLimit: 12,
  };
}
