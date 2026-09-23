import { describe, expect, it } from 'vitest';

import {
  atlasFilterKey,
  atlasFitZoom,
  atlasPositionBounds,
  atlasTabPersistsCamera,
  nearestAtlasIndices,
  resolveAtlasCameraRestore,
  atlasRendererRevision,
  defaultAtlasTab,
  semanticZoomConfig,
  semanticZoomTier,
  shouldAutoFitAtlasView,
} from './atlasViewState';

describe('Atlas entry projection', () => {
  it('opens the complete graph on desktop', () => {
    expect(defaultAtlasTab(false)).toBe('full');
  });

  it('opens the relational non-hairball Explore surface on mobile', () => {
    expect(defaultAtlasTab(true)).toBe('explore');
  });
});

describe('Atlas semantic zoom renderer config', () => {
  it('uses projection-relative thresholds for both curated and complete fits', () => {
    expect(semanticZoomTier(1, 1)).toBe('overview');
    expect(semanticZoomTier(2, 1)).toBe('mid');
    expect(semanticZoomTier(5, 1)).toBe('close');
    expect(semanticZoomTier(0.07, 0.07)).toBe('overview');
    expect(semanticZoomTier(0.14, 0.07)).toBe('mid');
    expect(semanticZoomTier(0.35, 0.07)).toBe('close');
  });
  it('keeps camera-only workspace updates out of the dataset identity', () => {
    const first = atlasFilterKey({
      periods: ['Roman', 'Classical'],
      types: ['concept'],
      schools: [],
    });
    const recreated = atlasFilterKey({
      periods: ['Classical', 'Roman'],
      types: ['concept'],
      schools: [],
    });
    expect(recreated).toBe(first);
    expect(atlasFilterKey({
      periods: ['Roman'],
      types: ['concept'],
      schools: [],
    })).not.toBe(first);
  });

  it('binds heavy renderer revision only to the committed dataset and device class', () => {
    const dataset = { release: 'one' };
    expect(atlasRendererRevision(dataset, false)).toEqual({
      dataset,
      isMobile: false,
    });
    expect(Object.keys(atlasRendererRevision(dataset, false)).sort()).toEqual([
      'dataset',
      'isMobile',
    ]);
  });

  it('reveals more authored Atlas detail without changing its dataset', () => {
    expect(semanticZoomConfig('atlas', 'overview', false).showTopLabelsLimit).toBe(14);
    expect(semanticZoomConfig('atlas', 'close', false).showTopLabelsLimit).toBe(42);
    expect(semanticZoomConfig('atlas', 'mid', true).showTopLabelsLimit).toBe(8);
    expect(semanticZoomConfig('atlas', 'close', false).showDynamicLabels).toBe(true);
  });

  it('reveals the complete graph progressively without changing its data', () => {
    expect(semanticZoomConfig('full', 'overview', false)).toEqual({
      linkVisibilityDistanceRange: [86, 260],
      linkVisibilityMinTransparency: 0.012,
      showTopLabelsLimit: 18,
      showDynamicLabels: false,
      showDynamicLabelsLimit: 0,
      pointSamplingDistance: 110,
      pointSizeScale: 0.72,
      linkWidthScale: 0.1,
    });
    expect(semanticZoomConfig('full', 'mid', false)).toEqual({
      linkVisibilityDistanceRange: [34, 132],
      linkVisibilityMinTransparency: 0.06,
      showTopLabelsLimit: 64,
      showDynamicLabels: true,
      showDynamicLabelsLimit: 54,
      pointSamplingDistance: 34,
      pointSizeScale: 1.08,
      linkWidthScale: 0.7,
    });
    expect(semanticZoomConfig('full', 'close', false)).toEqual({
      linkVisibilityDistanceRange: [16, 84],
      linkVisibilityMinTransparency: 0.12,
      showTopLabelsLimit: 180,
      showDynamicLabels: true,
      showDynamicLabelsLimit: 140,
      pointSamplingDistance: 16,
      pointSizeScale: 1.45,
      linkWidthScale: 1,
    });
  });
});

describe('Atlas startup camera ownership', () => {
  it('allows startup fit only while the landing overview is untouched', () => {
    expect(shouldAutoFitAtlasView({
      cameraTransitionActive: false,
      focusedNodeId: null,
      focusedConstellation: null,
    })).toBe(true);

    expect(shouldAutoFitAtlasView({
      cameraTransitionActive: true,
      focusedNodeId: null,
      focusedConstellation: null,
    })).toBe(false);
    expect(shouldAutoFitAtlasView({
      cameraTransitionActive: false,
      focusedNodeId: 'person_chrysippus',
      focusedConstellation: null,
    })).toBe(false);
    expect(shouldAutoFitAtlasView({
      cameraTransitionActive: false,
      focusedNodeId: null,
      focusedConstellation: 'stoic',
    })).toBe(false);
    expect(shouldAutoFitAtlasView({
      cameraTransitionActive: false,
      focusedNodeId: null,
      focusedConstellation: null,
      cameraRestored: true,
    })).toBe(false);
  });
});

describe('Atlas camera permalinks', () => {
  const positions = [100, 200, 300, 400, 250, 260, Number.NaN, 5];

  it('bounds only finite interleaved positions', () => {
    expect(atlasPositionBounds(positions)).toEqual({
      minX: 100, minY: 200, maxX: 300, maxY: 400,
    });
    expect(atlasPositionBounds([])).toBeNull();
    expect(atlasPositionBounds(undefined)).toBeNull();
    expect(atlasPositionBounds([Number.NaN, Number.NaN])).toBeNull();
  });

  it('restores a space-coordinate centre that lies inside the release', () => {
    const bounds = atlasPositionBounds(positions);
    expect(resolveAtlasCameraRestore({ x: 180, y: 320, zoom: 2.5 }, bounds))
      .toEqual({ x: 180, y: 320, zoom: 2.5 });
  });

  it('ignores legacy d3 translates and malformed cameras', () => {
    const bounds = atlasPositionBounds(positions);
    expect(resolveAtlasCameraRestore({ x: -1840, y: -2210, zoom: 0.07 }, bounds)).toBeNull();
    expect(resolveAtlasCameraRestore({ x: 180, y: 320, zoom: 0 }, bounds)).toBeNull();
    expect(resolveAtlasCameraRestore({ x: Number.NaN, y: 320, zoom: 1 }, bounds)).toBeNull();
    expect(resolveAtlasCameraRestore(null, bounds)).toBeNull();
    expect(resolveAtlasCameraRestore({ x: 180, y: 320, zoom: 1 }, null)).toBeNull();
  });

  it('computes the zoom a padded fit would reach', () => {
    const bounds = { minX: 0, minY: 0, maxX: 800, maxY: 400 };
    expect(atlasFitZoom(bounds, [1000, 1000], 0.1)).toBeCloseTo(1);
    expect(atlasFitZoom(bounds, [1000, 300], 0)).toBeCloseTo(0.75);
  });

  it('persists the camera only where the coordinate space is stable', () => {
    expect(atlasTabPersistsCamera('full')).toBe(true);
    expect(atlasTabPersistsCamera('path')).toBe(true);
    expect(atlasTabPersistsCamera('filter')).toBe(false);
    expect(atlasTabPersistsCamera('atlas')).toBe(false);
    expect(atlasTabPersistsCamera('explore')).toBe(false);
  });
});

describe('Complete-graph constellation dive', () => {
  it('keeps the hub first and picks its spatial neighbours', () => {
    const flat = [0, 0, 50, 0, 5, 0, 1000, 1000, 2, 1];
    expect(nearestAtlasIndices(flat, 0, [0, 1, 2, 3, 4], 3)).toEqual([0, 4, 2]);
  });

  it('falls back to the hub alone when it has no position', () => {
    expect(nearestAtlasIndices([Number.NaN, 0, 1, 1], 0, [1], 4)).toEqual([0]);
  });
});
