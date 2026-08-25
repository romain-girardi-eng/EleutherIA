import { describe, expect, it } from 'vitest';

import {
  inspectAtlasGraphicsCapability,
  isAtlasRendererFailure,
} from './atlasGraphicsCapability';

function canvasWith(context: Partial<WebGL2RenderingContext> | null): HTMLCanvasElement {
  return {
    getContext: () => context,
  } as unknown as HTMLCanvasElement;
}

function context(renderer: string, maxTextureSize = 8192): Partial<WebGL2RenderingContext> {
  return {
    MAX_TEXTURE_SIZE: 3379,
    getExtension: (name: string) => {
      if (name === 'WEBGL_debug_renderer_info') return { UNMASKED_RENDERER_WEBGL: 1 };
      if (name === 'WEBGL_lose_context') return { loseContext: () => undefined };
      return null;
    },
    getParameter: (parameter: number) => parameter === 1 ? renderer : maxTextureSize,
  } as unknown as Partial<WebGL2RenderingContext>;
}

describe('Atlas graphics preflight', () => {
  it('fails closed when a strict WebGL2 context is unavailable', () => {
    expect(inspectAtlasGraphicsCapability(() => canvasWith(null))).toEqual({
      status: 'unsupported',
      reason: 'webgl2_unavailable',
    });
  });

  it('rejects SwiftShader even when it exposes WebGL2 limits', () => {
    expect(
      inspectAtlasGraphicsCapability(() => canvasWith(context('ANGLE SwiftShader') as WebGL2RenderingContext)),
    ).toMatchObject({
      status: 'unsupported',
      reason: 'software_renderer',
      renderer: 'ANGLE SwiftShader',
    });
  });

  it('rejects a texture limit below the Atlas floor', () => {
    expect(
      inspectAtlasGraphicsCapability(() => canvasWith(context('Apple M1', 2048) as WebGL2RenderingContext)),
    ).toMatchObject({ status: 'unsupported', reason: 'insufficient_texture_size' });
  });

  it('accepts a hardware WebGL2 renderer with sufficient limits', () => {
    expect(
      inspectAtlasGraphicsCapability(() => canvasWith(context('Apple M1', 16384) as WebGL2RenderingContext)),
    ).toEqual({
      status: 'supported',
      renderer: 'Apple M1',
      maxTextureSize: 16384,
    });
  });

  it('recognizes renderer failures without swallowing unrelated app errors', () => {
    expect(isAtlasRendererFailure(new Error('initializeCosmos failed in luma.gl'))).toBe(true);
    expect(isAtlasRendererFailure(new Error('Cannot read maxTextureDimension2D'))).toBe(true);
    expect(isAtlasRendererFailure(new Error('unrelated search failure'))).toBe(false);
  });
});
