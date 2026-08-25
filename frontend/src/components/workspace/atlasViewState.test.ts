import { describe, expect, it } from 'vitest';

import {
  atlasRendererRevision,
  defaultAtlasTab,
  semanticZoomConfig,
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

  it('keeps the authored Atlas config fixed across camera tiers', () => {
    expect(semanticZoomConfig('atlas', 'overview', false)).toEqual(
      semanticZoomConfig('atlas', 'close', false),
    );
    expect(semanticZoomConfig('atlas', 'mid', true).showTopLabelsLimit).toBe(6);
  });

  it('reveals the complete graph progressively without changing its data', () => {
    expect(semanticZoomConfig('full', 'overview', false)).toEqual({
      linkVisibilityDistanceRange: [60, 200],
      linkVisibilityMinTransparency: 0.02,
      showTopLabelsLimit: 12,
    });
    expect(semanticZoomConfig('full', 'mid', false)).toEqual({
      linkVisibilityDistanceRange: [40, 140],
      linkVisibilityMinTransparency: 0.05,
      showTopLabelsLimit: 36,
    });
    expect(semanticZoomConfig('full', 'close', false)).toEqual({
      linkVisibilityDistanceRange: [20, 90],
      linkVisibilityMinTransparency: 0.09,
      showTopLabelsLimit: 120,
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
