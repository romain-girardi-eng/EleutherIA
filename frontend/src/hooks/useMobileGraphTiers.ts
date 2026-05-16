import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CosmographRef } from '@cosmograph/react';

import type {
  AtlasEdgeMeta,
  AtlasNodeMeta,
} from '../components/cosmograph/AtlasHelpers';
import { pickAtlasNodeIds } from '../components/cosmograph/FreeWillAtlas';

export type MobileTier = 'atlas' | 'schools' | 'detail';

export interface MobileTierConfig {
  /** Zoom thresholds (right-inclusive on the lower bound). */
  readonly atlasMax: number;
  readonly schoolsMax: number;
  /** Max nodes allowed in each tier. */
  readonly atlasNodes: number;
  readonly schoolsNodes: number;
  readonly detailNodes: number;
  /** Debounce window for zoom-driven recomputes. */
  readonly debounceMs: number;
  /** Fraction of viewport radius used for in-frustum label visibility. */
  readonly labelVisibilityRadius: number;
}

const DEFAULT_CONFIG: MobileTierConfig = {
  atlasMax: 0.8,
  schoolsMax: 2.0,
  atlasNodes: 12,
  schoolsNodes: 200,
  detailNodes: 1500,
  debounceMs: 150,
  labelVisibilityRadius: 0.25,
};

export interface MobileTierSlice {
  readonly tier: MobileTier;
  readonly visibleNodeIds: ReadonlySet<string>;
  readonly visibleEdgeIds: ReadonlySet<string>;
  readonly labelNodeIds: ReadonlySet<string>;
  readonly metaSlice: ReadonlyArray<AtlasNodeMeta>;
  readonly edgeSlice: ReadonlyArray<AtlasEdgeMeta>;
}

interface UseMobileGraphTiersOptions {
  readonly enabled: boolean;
  readonly meta: ReadonlyArray<AtlasNodeMeta>;
  readonly edges: ReadonlyArray<AtlasEdgeMeta>;
  readonly graphRef: React.RefObject<CosmographRef | undefined>;
  readonly graphReady: boolean;
  readonly config?: Partial<MobileTierConfig>;
}

interface UseMobileGraphTiersResult {
  readonly slice: MobileTierSlice | null;
  readonly tier: MobileTier;
  readonly zoom: number;
  /** Stable callback to pass to Cosmograph's `onZoom`. */
  readonly handleZoom: (_e: unknown, _userDriven: boolean) => void;
  /** Force recompute (call when initial layout settles). */
  readonly invalidate: () => void;
}

/**
 * Build an adjacency map keyed by node id.
 * Only structural / 1-hop neighbour lookups; cheap O(E).
 */
function buildAdjacency(
  edges: ReadonlyArray<AtlasEdgeMeta>,
): Map<string, ReadonlyArray<string>> {
  const adj = new Map<string, string[]>();
  for (const edge of edges) {
    if (!adj.has(edge.source)) adj.set(edge.source, []);
    if (!adj.has(edge.target)) adj.set(edge.target, []);
    adj.get(edge.source)!.push(edge.target);
    adj.get(edge.target)!.push(edge.source);
  }
  return adj;
}

/**
 * Pick the top-N curated Atlas anchors by degree centrality.
 * Falls back to globally most-connected nodes if fewer than N anchors exist.
 */
function pickAtlasAnchors(
  meta: ReadonlyArray<AtlasNodeMeta>,
  cap: number,
): ReadonlyArray<AtlasNodeMeta> {
  const atlasIds = pickAtlasNodeIds(meta.map((m) => ({ id: m.id, type: m.typeKey })));
  const atlasMembers = meta
    .filter((m) => atlasIds.has(m.id))
    .slice()
    .sort((a, b) => b.degree - a.degree);

  if (atlasMembers.length >= cap) {
    return atlasMembers.slice(0, cap);
  }

  const seen = new Set(atlasMembers.map((m) => m.id));
  const filler = meta
    .filter((m) => !seen.has(m.id))
    .slice()
    .sort((a, b) => b.degree - a.degree)
    .slice(0, cap - atlasMembers.length);

  return [...atlasMembers, ...filler];
}

/**
 * Hook that gives a mobile-friendly slice of the KG based on the cosmograph
 * zoom level. Three tiers (Atlas / Schools / Detail) with hard caps on node
 * count to keep the WebGL renderer comfortable on mid-tier phones.
 */
export function useMobileGraphTiers({
  enabled,
  meta,
  edges,
  graphRef,
  graphReady,
  config,
}: UseMobileGraphTiersOptions): UseMobileGraphTiersResult {
  const cfg = useMemo<MobileTierConfig>(() => ({ ...DEFAULT_CONFIG, ...config }), [config]);

  const [zoom, setZoom] = useState<number>(() => 0.5);
  const [recomputeKey, setRecomputeKey] = useState(0);
  // Stay on Atlas tier until the user has actually zoomed. Cosmograph's
  // `fitViewOnInit` fires synthetic onZoom callbacks immediately after mount,
  // which would otherwise jump the user past the curated 12-node landing.
  const [userZoomed, setUserZoomed] = useState(false);

  const debounceRef = useRef<number | null>(null);
  const adjacency = useMemo(() => buildAdjacency(edges), [edges]);
  const metaById = useMemo(() => new Map(meta.map((m) => [m.id, m])), [meta]);
  const edgesBySource = useMemo(() => {
    const map = new Map<string, AtlasEdgeMeta[]>();
    for (const edge of edges) {
      const key = `${edge.source}__${edge.target}`;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(edge);
    }
    return map;
  }, [edges]);

  const atlasAnchors = useMemo(
    () => (enabled ? pickAtlasAnchors(meta, cfg.atlasNodes) : []),
    [enabled, meta, cfg.atlasNodes],
  );

  const tier = useMemo<MobileTier>(() => {
    // Dev-only escape hatch: ?forceTier=atlas|schools|detail
    if (import.meta.env.DEV && typeof window !== 'undefined') {
      const match = window.location.search.match(/[?&]forceTier=(atlas|schools|detail)/);
      if (match) return match[1] as MobileTier;
    }
    if (!userZoomed) return 'atlas';
    if (zoom <= cfg.atlasMax) return 'atlas';
    if (zoom <= cfg.schoolsMax) return 'schools';
    return 'detail';
  }, [zoom, userZoomed, cfg.atlasMax, cfg.schoolsMax]);

  const handleZoom = useCallback(
    (_e: unknown, userDriven: boolean) => {
      if (!enabled) return;
      if (userDriven) {
        setUserZoomed(true);
      }
      if (debounceRef.current !== null) {
        window.clearTimeout(debounceRef.current);
      }
      debounceRef.current = window.setTimeout(() => {
        const next = graphRef.current?.getZoomLevel?.();
        if (typeof next === 'number' && Number.isFinite(next)) {
          setZoom((prev) => (Math.abs(prev - next) < 0.01 ? prev : next));
        }
      }, cfg.debounceMs);
    },
    [enabled, graphRef, cfg.debounceMs],
  );

  const invalidate = useCallback(() => {
    setRecomputeKey((k) => k + 1);
  }, []);

  // Re-sample on tier change OR explicit invalidation. We sample the
  // cosmograph's sampled position map so we know which atlas/cluster nodes are
  // currently in the camera frustum without needing a full projection pass.
  const [viewportSample, setViewportSample] = useState(0);
  useEffect(() => {
    if (!enabled || !graphReady) return;
    setViewportSample((v) => v + 1);
  }, [enabled, graphReady, tier, recomputeKey]);

  const slice = useMemo<MobileTierSlice | null>(() => {
    if (!enabled || meta.length === 0) return null;

    const anchorIds = new Set(atlasAnchors.map((m) => m.id));

    if (tier === 'atlas') {
      const idSet = anchorIds;
      const visibleEdgeIds = new Set<string>();
      const edgeSlice: AtlasEdgeMeta[] = [];
      for (const edge of edges) {
        if (idSet.has(edge.source) && idSet.has(edge.target)) {
          visibleEdgeIds.add(edge.id);
          edgeSlice.push(edge);
        }
      }
      return {
        tier,
        visibleNodeIds: idSet,
        visibleEdgeIds,
        labelNodeIds: idSet,
        metaSlice: atlasAnchors,
        edgeSlice,
      };
    }

    // For Schools + Detail we expand 1 hop from "seeds". The seeds are the
    // sampled in-viewport nodes from cosmograph; if those aren't available
    // (first frame, cosmograph not ready) we fall back to atlas anchors.
    let seeds: ReadonlySet<string> = anchorIds;
    const sampled = graphRef.current?.getSampledPointPositionsMap?.();
    if (sampled && sampled.size > 0) {
      const onScreen = new Set<string>();
      sampled.forEach((space, index) => {
        const id = meta[index]?.id;
        if (!id) return;
        const screen = graphRef.current?.spaceToScreenPosition?.(space);
        if (!screen) return;
        const [sx, sy] = screen;
        if (
          sx >= 0 &&
          sy >= 0 &&
          sx <= window.innerWidth &&
          sy <= window.innerHeight
        ) {
          onScreen.add(id);
        }
      });
      if (onScreen.size > 0) seeds = onScreen;
    }

    // Always keep atlas anchors in the seed set so the user never loses the
    // skeleton when panning into empty space.
    const seedSet = new Set<string>(seeds);
    anchorIds.forEach((id) => seedSet.add(id));

    const visibleNodeIds = new Set<string>(seedSet);
    const cap = tier === 'schools' ? cfg.schoolsNodes : cfg.detailNodes;

    // Sort seeds by degree desc so high-degree nodes get their full neighbour
    // set before we hit the cap.
    const orderedSeeds = Array.from(seedSet)
      .map((id) => metaById.get(id))
      .filter((m): m is AtlasNodeMeta => m !== undefined)
      .sort((a, b) => b.degree - a.degree);

    outer: for (const seed of orderedSeeds) {
      const neighbours = adjacency.get(seed.id);
      if (!neighbours) continue;
      for (const nb of neighbours) {
        if (visibleNodeIds.has(nb)) continue;
        visibleNodeIds.add(nb);
        if (visibleNodeIds.size >= cap) break outer;
      }
    }

    const metaSlice: AtlasNodeMeta[] = [];
    visibleNodeIds.forEach((id) => {
      const node = metaById.get(id);
      if (node) metaSlice.push(node);
    });

    const visibleEdgeIds = new Set<string>();
    const edgeSlice: AtlasEdgeMeta[] = [];
    for (const edge of edges) {
      if (visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)) {
        visibleEdgeIds.add(edge.id);
        edgeSlice.push(edge);
      }
    }

    // Label visibility: top-30 by degree for Schools tier, top-30 *within
    // viewport-radius* for Detail. We re-use the screen sample to compute
    // distance from canvas centre.
    let labelNodeIds: Set<string>;
    if (tier === 'schools') {
      labelNodeIds = new Set(
        metaSlice
          .slice()
          .sort((a, b) => b.degree - a.degree)
          .slice(0, 30)
          .map((m) => m.id),
      );
    } else {
      labelNodeIds = new Set();
      if (sampled && sampled.size > 0) {
        const cx = window.innerWidth / 2;
        const cy = window.innerHeight / 2;
        const radius =
          Math.min(window.innerWidth, window.innerHeight) * cfg.labelVisibilityRadius;
        const scored: Array<{ id: string; distance: number; degree: number }> = [];
        sampled.forEach((space, index) => {
          const id = meta[index]?.id;
          if (!id || !visibleNodeIds.has(id)) return;
          const screen = graphRef.current?.spaceToScreenPosition?.(space);
          if (!screen) return;
          const [sx, sy] = screen;
          const dx = sx - cx;
          const dy = sy - cy;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance > radius) return;
          scored.push({
            id,
            distance,
            degree: metaById.get(id)?.degree ?? 0,
          });
        });
        scored.sort((a, b) => b.degree - a.degree);
        scored.slice(0, 30).forEach((item) => labelNodeIds.add(item.id));
      }
      if (labelNodeIds.size === 0) {
        // Fallback: top 12 anchors so the canvas never feels label-less.
        atlasAnchors.slice(0, 12).forEach((m) => labelNodeIds.add(m.id));
      }
    }

    return {
      tier,
      visibleNodeIds,
      visibleEdgeIds,
      labelNodeIds,
      metaSlice,
      edgeSlice,
    };
    // viewportSample intentionally listed: re-samples the camera frustum.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    enabled,
    meta,
    edges,
    metaById,
    adjacency,
    atlasAnchors,
    tier,
    cfg.schoolsNodes,
    cfg.detailNodes,
    cfg.labelVisibilityRadius,
    graphRef,
    viewportSample,
  ]);

  // edgesBySource currently unused but kept for future per-edge filters.
  void edgesBySource;

  // Cleanup any pending debounce on unmount.
  useEffect(
    () => () => {
      if (debounceRef.current !== null) {
        window.clearTimeout(debounceRef.current);
      }
    },
    [],
  );

  return {
    slice,
    tier,
    zoom,
    handleZoom,
    invalidate,
  };
}
