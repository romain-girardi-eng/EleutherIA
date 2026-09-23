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
  /** A permalink camera was just restored and owns the first frame. */
  cameraRestored?: boolean;
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
  cameraRestored = false,
}: AtlasAutoFitState): boolean {
  return !cameraTransitionActive
    && !cameraRestored
    && focusedNodeId === null
    && focusedConstellation === null;
}

/** The complete release is the desktop entry point: its layout is frozen, so
 * it renders as cheaply as the curated projection. Touch devices enter the
 * relational Explore surface before allocating the WebGL canvas. */
export function defaultAtlasTab(isMobile: boolean): AtlasTab {
  return isMobile ? 'explore' : 'full';
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

export interface AtlasSpaceBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface AtlasSpaceCamera {
  /** Space coordinate under the canvas centre, not a d3 screen translate. */
  x: number;
  y: number;
  zoom: number;
}

/** Bounding box of an interleaved `[x0, y0, x1, y1, …]` position buffer. */
export function atlasPositionBounds(
  positions: ArrayLike<number> | null | undefined,
): AtlasSpaceBounds | null {
  if (!positions || positions.length < 2) return null;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (let index = 0; index + 1 < positions.length; index += 2) {
    const x = positions[index];
    const y = positions[index + 1];
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  return Number.isFinite(minX) ? { minX, minY, maxX, maxY } : null;
}

/** Links written before the camera stored space coordinates carry d3
 * translates (often negative, thousands of pixels). They fall outside the
 * data bounds and must be ignored rather than flying the camera into void. */
export function resolveAtlasCameraRestore(
  camera: AtlasSpaceCamera | null | undefined,
  bounds: AtlasSpaceBounds | null,
): AtlasSpaceCamera | null {
  if (!camera || !bounds) return null;
  const { x, y, zoom } = camera;
  if (![x, y, zoom].every(Number.isFinite) || zoom <= 0) return null;
  if (x < bounds.minX || x > bounds.maxX || y < bounds.minY || y > bounds.maxY) {
    return null;
  }
  return { x, y, zoom };
}

/** Zoom that `fitView(duration, padding)` reaches for these bounds. A
 * restored camera skips the fit, so semantic-zoom tiers need this baseline. */
export function atlasFitZoom(
  bounds: AtlasSpaceBounds,
  screen: readonly [number, number],
  padding: number,
): number {
  const [width, height] = screen;
  const spanX = Math.max(1, bounds.maxX - bounds.minX);
  const spanY = Math.max(1, bounds.maxY - bounds.minY);
  const usable = 1 - padding * 2;
  return Math.min((width * usable) / spanX, (height * usable) / spanY);
}

/** Only the complete release has a stable coordinate space: filtered and
 * curated slices are rescaled by the renderer around their own extent. */
export function atlasTabPersistsCamera(tab: AtlasTab): boolean {
  return tab === 'full' || tab === 'path';
}

/** In the complete graph a constellation is spread over thousands of loci.
 * Dive to the members nearest its hub so the camera lands somewhere legible
 * instead of re-framing the whole release. */
export function nearestAtlasIndices(
  positions: ArrayLike<number>,
  hubIndex: number,
  candidates: readonly number[],
  limit: number,
): number[] {
  const hubX = positions[hubIndex * 2];
  const hubY = positions[hubIndex * 2 + 1];
  if (!Number.isFinite(hubX) || !Number.isFinite(hubY)) return [hubIndex];
  const ranked = candidates
    .filter((index) => index !== hubIndex
      && Number.isFinite(positions[index * 2])
      && Number.isFinite(positions[index * 2 + 1]))
    .map((index) => ({
      index,
      distance: Math.hypot(positions[index * 2] - hubX, positions[index * 2 + 1] - hubY),
    }))
    .sort((left, right) => left.distance - right.distance || left.index - right.index)
    .slice(0, Math.max(0, limit - 1))
    .map(({ index }) => index);
  return [hubIndex, ...ranked];
}
