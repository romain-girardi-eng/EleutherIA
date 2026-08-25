import { describe, expect, it } from 'vitest';

import {
  atlasFilterKey,
  atlasRendererRevision,
  defaultAtlasTab,
  semanticZoomConfig,
  semanticZoomTier,
  shouldAutoFitAtlasView,
} from './atlasViewState';

describe('Atlas entry projection', () => {
  it('opens the curated Atlas instead of the complete graph on desktop', () => {
    expect(defaultAtlasTab(false)).toBe('atlas');
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
  });
});
