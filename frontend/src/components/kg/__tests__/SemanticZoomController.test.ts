// frontend/src/components/kg/__tests__/SemanticZoomController.test.ts
import { describe, it, expect } from 'vitest';
import { getZoomLevel, shouldShowNode, shouldShowEdge } from '../SemanticZoomController';
import { ZoomLevel } from '@/types/sigma';

describe('getZoomLevel', () => {
  it('returns Overview for ratio > 1.2', () => {
    expect(getZoomLevel(1.5)).toBe(ZoomLevel.Overview);
    expect(getZoomLevel(2.0)).toBe(ZoomLevel.Overview);
  });
  it('returns Community for ratio 0.4 - 1.2', () => {
    expect(getZoomLevel(0.8)).toBe(ZoomLevel.Community);
    expect(getZoomLevel(0.4)).toBe(ZoomLevel.Community);
  });
  it('returns Neighborhood for ratio 0.08 - 0.4', () => {
    expect(getZoomLevel(0.2)).toBe(ZoomLevel.Neighborhood);
  });
  it('returns Detail for ratio < 0.08', () => {
    expect(getZoomLevel(0.05)).toBe(ZoomLevel.Detail);
  });
});

describe('shouldShowNode', () => {
  it('hides passages at Overview', () => {
    expect(shouldShowNode('passage', ZoomLevel.Overview, 5, false)).toBe(false);
  });
  it('shows high-degree nodes at Overview', () => {
    expect(shouldShowNode('person', ZoomLevel.Overview, 10, false)).toBe(true);
  });
  it('shows all non-passage nodes at Community', () => {
    expect(shouldShowNode('concept', ZoomLevel.Community, 1, false)).toBe(true);
  });
  it('shows passages at Detail', () => {
    expect(shouldShowNode('passage', ZoomLevel.Detail, 1, false)).toBe(true);
  });
});

describe('shouldShowEdge', () => {
  it('hides all edges at Overview', () => {
    expect(shouldShowEdge('argumentative', ZoomLevel.Overview, false)).toBe(false);
  });
  it('shows argumentative edges at Community', () => {
    expect(shouldShowEdge('argumentative', ZoomLevel.Community, false)).toBe(true);
  });
  it('hides structural edges at Community without hover', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Community, false)).toBe(false);
  });
  it('shows structural edges at Community on hover', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Community, true)).toBe(true);
  });
  it('shows all edges at Detail', () => {
    expect(shouldShowEdge('structural', ZoomLevel.Detail, false)).toBe(true);
  });
});
