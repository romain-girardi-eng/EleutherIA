export type AtlasGraphicsStatus = 'supported' | 'unsupported';

export interface AtlasGraphicsCapability {
  status: AtlasGraphicsStatus;
  reason?:
    | 'webgl2_unavailable'
    | 'software_renderer'
    | 'insufficient_texture_size'
    | 'initialization_timeout'
    | 'initialization_error'
    | 'context_lost';
  renderer?: string;
  maxTextureSize?: number;
}

export function isAtlasRendererFailure(value: unknown): boolean {
  const message = value instanceof Error
    ? `${value.message}\n${value.stack ?? ''}`
    : String(value ?? '');
  return /cosmograph|luma\.gl|initializecosmos|maxtexturedimension2d/i.test(message);
}

type DebugRendererInfo = {
  UNMASKED_RENDERER_WEBGL: number;
};

/**
 * Reject renderers that would make the large Atlas unstable or misleadingly
 * slow before Cosmograph allocates its Arrow/DuckDB/GPU surfaces.
 *
 * `failIfMajorPerformanceCaveat` is the browser-owned signal for software or
 * otherwise unsuitable acceleration. The renderer string is a second guard
 * because some Chromium builds still return a context backed by SwiftShader.
 */
export function inspectAtlasGraphicsCapability(
  createCanvas: () => HTMLCanvasElement = () => document.createElement('canvas'),
): AtlasGraphicsCapability {
  const canvas = createCanvas();
  const gl = canvas.getContext('webgl2', {
    alpha: true,
    antialias: true,
    failIfMajorPerformanceCaveat: true,
    powerPreference: 'high-performance',
  });

  if (!gl) {
    return { status: 'unsupported', reason: 'webgl2_unavailable' };
  }

  const debug = gl.getExtension('WEBGL_debug_renderer_info') as DebugRendererInfo | null;
  const renderer = debug
    ? String(gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) ?? '')
    : '';
  const maxTextureSize = Number(gl.getParameter(gl.MAX_TEXTURE_SIZE) ?? 0);
  gl.getExtension('WEBGL_lose_context')?.loseContext();

  if (/swiftshader|software|llvmpipe/i.test(renderer)) {
    return {
      status: 'unsupported',
      reason: 'software_renderer',
      renderer: renderer || undefined,
      maxTextureSize,
    };
  }
  if (!Number.isFinite(maxTextureSize) || maxTextureSize < 4096) {
    return {
      status: 'unsupported',
      reason: 'insufficient_texture_size',
      renderer: renderer || undefined,
      maxTextureSize,
    };
  }
  return {
    status: 'supported',
    renderer: renderer || undefined,
    maxTextureSize,
  };
}
