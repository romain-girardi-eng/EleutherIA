/**
 * useMobileGraphTiers — hierarchical-by-type disclosure of the KG on mobile.
 *
 * Replaces the earlier viewport-sampled tier engine (which flickered between
 * Atlas/Schools/Detail because every onZoom callback re-sampled the camera
 * frustum and shifted the visible node set). The new model is dead simple:
 *
 *   - Default zoom (≤ 1.5)  → hide DETAIL_TYPES (passages, evidence bundles,
 *                              etc.) and SUPER_DETAIL_TYPES. Show everything
 *                              else: schools, persons, concepts, works,
 *                              debates, scholars, arguments-with-degree.
 *   - Zoom 1.5 – 3.0        → also reveal DETAIL_TYPES.
 *   - Zoom > 3.0            → reveal everything including passages.
 *
 * The slice is a *pure* function of (meta, zoom). No raycasting, no
 * neighbour expansion, no per-frame state. The cosmograph re-renders only
 * when the user crosses a tier boundary.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import type { CosmographRef } from '@cosmograph/react';

import type {
  AtlasEdgeMeta,
  AtlasNodeMeta,
} from '../components/cosmograph/AtlasHelpers';

export type MobileTier = 'overview' | 'mid' | 'full';

export interface MobileTierConfig {
  /** Zoom thresholds (right-inclusive on the lower bound). */
  readonly midZoom: number;
  readonly fullZoom: number;
  /** Debounce window for zoom-driven recomputes. */
  readonly debounceMs: number;
}

const DEFAULT_CONFIG: MobileTierConfig = {
  midZoom: 1.5,
  fullZoom: 3.0,
  debounceMs: 200,
};

// Types hidden at the OVERVIEW zoom level — these are the "fine detail"
// of the corpus. Specific arguments and individual scholarly publications
// only become relevant when the user is exploring a sub-region.
const DETAIL_TYPES = new Set<string>(['argument', 'publication', 'synthesis']);

// Hidden until the user is fully zoomed in. Passages dwarf the rest of the
// graph (17k vs 2k) and they're only meaningful in close-up.
const SUPER_DETAIL_TYPES = new Set<string>([
  'passage',
  'evidence_bundle',
  'quote',
]);

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
  readonly handleZoom: (_e: unknown, _userDriven: boolean) => void;
  /** No-op; kept for API compat with the old hook. */
  readonly invalidate: () => void;
}

function classifyZoom(zoom: number, cfg: MobileTierConfig): MobileTier {
  if (zoom >= cfg.fullZoom) return 'full';
  if (zoom >= cfg.midZoom) return 'mid';
  return 'overview';
}

function nodeAllowedAtTier(node: AtlasNodeMeta, tier: MobileTier): boolean {
  const t = node.typeKey;
  if (tier === 'full') return true;
  if (SUPER_DETAIL_TYPES.has(t)) return false;
  if (tier === 'mid') return true;
  // overview: also hide DETAIL_TYPES
  if (DETAIL_TYPES.has(t)) return false;
  return true;
}

export function useMobileGraphTiers({
  enabled,
  meta,
  edges,
  config,
}: UseMobileGraphTiersOptions): UseMobileGraphTiersResult {
  const cfg = useMemo<MobileTierConfig>(
    () => ({ ...DEFAULT_CONFIG, ...config }),
    [config],
  );

  const [zoom, setZoom] = useState<number>(0.5);
  const debounceRef = useRef<number | null>(null);

  const tier = useMemo<MobileTier>(() => classifyZoom(zoom, cfg), [zoom, cfg]);

  // onZoom callback wired to Cosmograph. Debounced so a continuous pinch
  // doesn't fire one re-render per frame — only when the user lands on a
  // tier boundary do we actually flip the slice.
  const handleZoom = useCallback(
    (...args: unknown[]) => {
      // Cosmograph's onZoom signature is loosely typed across versions.
      // The numeric zoom value can live in args[0], args[1], or on a
      // detail-shaped object. Probe for a plain number.
      let next = NaN;
      for (const arg of args) {
        if (typeof arg === 'number' && Number.isFinite(arg)) {
          next = arg;
          break;
        }
        if (arg && typeof arg === 'object' && 'k' in arg && typeof (arg as { k: unknown }).k === 'number') {
          next = (arg as { k: number }).k;
          break;
        }
        if (arg && typeof arg === 'object' && 'transform' in arg) {
          const tf = (arg as { transform?: { k?: number } }).transform;
          if (tf && typeof tf.k === 'number') {
            next = tf.k;
            break;
          }
        }
      }
      if (!Number.isFinite(next)) return;

      if (debounceRef.current !== null) window.clearTimeout(debounceRef.current);
      debounceRef.current = window.setTimeout(() => {
        setZoom(next);
      }, cfg.debounceMs);
    },
    [cfg.debounceMs],
  );

  const invalidate = useCallback(() => {
    // intentionally empty — kept for caller compatibility
  }, []);

  const slice = useMemo<MobileTierSlice | null>(() => {
    if (!enabled || meta.length === 0) return null;

    try {
      const visibleNodeIds = new Set<string>();
      const metaSlice: AtlasNodeMeta[] = [];
      for (const node of meta) {
        if (nodeAllowedAtTier(node, tier)) {
          visibleNodeIds.add(node.id);
          metaSlice.push(node);
        }
      }

      const visibleEdgeIds = new Set<string>();
      const edgeSlice: AtlasEdgeMeta[] = [];
      for (const edge of edges) {
        if (visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)) {
          visibleEdgeIds.add(edge.id);
          edgeSlice.push(edge);
        }
      }

      // Labels: only on the most-connected ~40 visible nodes so the canvas
      // doesn't get carpeted with text. Sort by degree.
      const LABEL_CAP = 40;
      const labelNodeIds = new Set<string>(
        metaSlice
          .slice()
          .sort((a, b) => b.degree - a.degree)
          .slice(0, LABEL_CAP)
          .map((m) => m.id),
      );

      return {
        tier,
        visibleNodeIds,
        visibleEdgeIds,
        labelNodeIds,
        metaSlice,
        edgeSlice,
      };
    } catch (err) {
      // Defensive: a corrupted node entry shouldn't kill the page.
      console.warn('useMobileGraphTiers slice failed:', err);
      return null;
    }
  }, [enabled, meta, edges, tier]);

  return { slice, tier, zoom, handleZoom, invalidate };
}
