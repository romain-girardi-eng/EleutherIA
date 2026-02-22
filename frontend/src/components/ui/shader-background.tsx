/**
 * ShaderBackground — WebGL fragment shader overlay
 *
 * Organic flowing aurora in warm golden tones. Drifts slowly
 * across the parchment and reacts to the cursor. Rendered at
 * half resolution and composited via CSS for performance.
 *
 * Desktop only. Respects prefers-reduced-motion.
 */

import { useEffect, useRef, useCallback } from 'react';

/* ═══════════════════════════════════════════════════════════
   GLSL Sources
   ═══════════════════════════════════════════════════════════ */

const VERT = `
attribute vec2 a_position;
void main() {
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const FRAG = `
precision mediump float;

uniform float u_time;
uniform vec2  u_resolution;
uniform vec2  u_mouse;

/* ── Simplex 2D noise (Ashima Arts) ── */
vec3 mod289(vec3 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }

float snoise(vec2 v) {
  const vec4 C = vec4(
    0.211324865405187,   // (3.0-sqrt(3.0))/6.0
    0.366025403784439,   //  0.5*(sqrt(3.0)-1.0)
   -0.577350269189626,   // -1.0 + 2.0*C.x
    0.024390243902439    //  1.0/41.0
  );
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x  = 2.0 * fract(p * C.www) - 1.0;
  vec3 h  = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g;
  g.x  = a0.x  * x0.x   + h.x  * x0.y;
  g.yz = a0.yz * x12.xz  + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

/* ── Fractal Brownian Motion ── */
float fbm(vec2 p) {
  float f = 0.0;
  f += 0.5000 * snoise(p); p *= 2.01;
  f += 0.2500 * snoise(p); p *= 2.02;
  f += 0.1250 * snoise(p); p *= 2.03;
  f += 0.0625 * snoise(p);
  return f;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution;
  float t = u_time * 0.04;             // very slow drift

  /* ── Domain warping — organic distortion ── */
  vec2 q = vec2(
    fbm(uv * 2.5 + vec2(0.0, t)),
    fbm(uv * 2.5 + vec2(5.2, t * 0.8))
  );

  vec2 r = vec2(
    fbm(uv * 2.5 + 4.0 * q + vec2(1.7, 9.2) + t * 0.15),
    fbm(uv * 2.5 + 4.0 * q + vec2(8.3, 2.8) + t * 0.12)
  );

  float f = fbm(uv * 2.5 + 4.0 * r);

  /* ── Mouse influence — subtle brightening near cursor ── */
  float mouseDist = distance(uv, u_mouse);
  float mouseGlow = smoothstep(0.35, 0.0, mouseDist) * 0.15;

  /* ── Color palette — warm gold / amber / cream ── */
  vec3 c1 = vec3(0.95, 0.85, 0.65);   // warm cream
  vec3 c2 = vec3(0.90, 0.75, 0.50);   // golden amber
  vec3 c3 = vec3(0.98, 0.92, 0.78);   // pale highlight
  vec3 c4 = vec3(0.82, 0.68, 0.45);   // deep gold

  vec3 color = mix(c1, c2, clamp(f * f * 4.0, 0.0, 1.0));
  color = mix(color, c3, clamp(length(q), 0.0, 1.0));
  color = mix(color, c4, clamp(length(r.x), 0.0, 1.0) * 0.5);

  /* ── Flowing aurora bands ── */
  float bands = sin(uv.y * 8.0 + f * 6.0 + t * 2.0) * 0.5 + 0.5;
  bands = smoothstep(0.3, 0.7, bands);

  /* ── Vignette — fade edges ── */
  float vignette = smoothstep(0.0, 0.4, uv.x) * smoothstep(1.0, 0.6, uv.x)
                 * smoothstep(0.0, 0.3, uv.y) * smoothstep(1.0, 0.7, uv.y);

  float alpha = (bands * 0.5 + f * 0.3 + mouseGlow) * vignette * 0.14;

  gl_FragColor = vec4(color, alpha);
}
`;

/* ═══════════════════════════════════════════════════════════
   React Component
   ═══════════════════════════════════════════════════════════ */

function compileShader(gl: WebGLRenderingContext, type: number, src: string) {
  const s = gl.createShader(type)!;
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error('Shader compile error:', gl.getShaderInfoLog(s));
    gl.deleteShader(s);
    return null;
  }
  return s;
}

export function ShaderBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const raf = useRef(0);
  const mouse = useRef({ x: 0.5, y: 0.5 });
  const smoothMouse = useRef({ x: 0.5, y: 0.5 });

  const init = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const gl = canvas.getContext('webgl', {
      alpha: true,
      premultipliedAlpha: false,
      antialias: false,
    });
    if (!gl) return null;

    const vs = compileShader(gl, gl.VERTEX_SHADER, VERT);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return null;

    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);

    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(prog));
      return null;
    }

    gl.useProgram(prog);

    // Fullscreen quad
    const buf = gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1, 1, -1, -1, 1,
      -1, 1, 1, -1, 1, 1,
    ]), gl.STATIC_DRAW);

    const aPos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    return {
      gl,
      prog,
      uTime: gl.getUniformLocation(prog, 'u_time'),
      uRes: gl.getUniformLocation(prog, 'u_resolution'),
      uMouse: gl.getUniformLocation(prog, 'u_mouse'),
    };
  }, []);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!window.matchMedia('(hover: hover)').matches) return;

    const ctx = init();
    if (!ctx) return;

    const { gl, uTime, uRes, uMouse } = ctx;
    const canvas = canvasRef.current!;

    const resize = () => {
      // Render at half resolution
      const dpr = Math.min(window.devicePixelRatio, 2);
      const w = Math.floor(window.innerWidth * dpr * 0.5);
      const h = Math.floor(window.innerHeight * dpr * 0.5);
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    };

    const onMove = (e: MouseEvent) => {
      mouse.current = {
        x: e.clientX / window.innerWidth,
        y: 1.0 - e.clientY / window.innerHeight, // flip Y for GL
      };
    };

    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMove, { passive: true });

    const start = performance.now();

    const loop = () => {
      const t = (performance.now() - start) * 0.001;

      // Smooth mouse
      smoothMouse.current.x += (mouse.current.x - smoothMouse.current.x) * 0.05;
      smoothMouse.current.y += (mouse.current.y - smoothMouse.current.y) * 0.05;

      gl.uniform1f(uTime, t);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform2f(uMouse, smoothMouse.current.x, smoothMouse.current.y);

      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      raf.current = requestAnimationFrame(loop);
    };

    raf.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf.current);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMove);
    };
  }, [init]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 2,
      }}
    />
  );
}
