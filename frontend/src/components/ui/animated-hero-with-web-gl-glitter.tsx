import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useMemo, useRef } from "react";
import { cn } from "../../utils/cn";

// ============================================================================
// WEBGL GLITTER EFFECT
// ============================================================================

// Vertex shader - passes UV coordinates to fragment shader
const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Fragment shader - creates the glitter effect
const fragmentShader = `
  uniform float iTime;
  uniform vec2 iResolution;
  uniform sampler2D iChannel0;
  varying vec2 vUv;

  void main() {
    vec2 uv = vUv;
    float result = 0.0;

    // Sample noise texture at different scales and speeds
    result += texture2D(iChannel0, uv * 1.1 + vec2(iTime * -0.005)).r;
    result *= texture2D(iChannel0, uv * 0.9 + vec2(iTime * 0.005)).g;

    // Power function creates sharp, defined sparkles
    result = pow(result, 12.0);

    // Amplify the result for visibility
    gl_FragColor = vec4(vec3(5.0) * result, 1.0);
  }
`;

/**
 * Generate a random noise texture for the glitter effect
 */
function generateNoiseTexture(size = 512): THREE.DataTexture {
  const data = new Uint8Array(size * size * 4);

  for (let i = 0; i < size * size; i++) {
    const stride = i * 4;
    const r = Math.random() * 255;
    const g = Math.random() * 255;
    const b = Math.random() * 255;

    data[stride] = r;
    data[stride + 1] = g;
    data[stride + 2] = b;
    data[stride + 3] = 255;
  }

  const texture = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.needsUpdate = true;

  return texture;
}

interface SparklesPlaneProps {
  speed?: number;
  intensity?: number;
}

/**
 * SparklesPlane - Renders plane with shader material
 */
function SparklesPlane({ speed = 1, intensity: _intensity = 5.0 }: SparklesPlaneProps) {
  const meshRef = useRef<THREE.Mesh>(null!);
  const noiseTexture = useMemo(() => generateNoiseTexture(512), []);

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        iTime: { value: 0 },
        iResolution: {
          value: new THREE.Vector2(
            typeof window !== "undefined" ? window.innerWidth : 1920,
            typeof window !== "undefined" ? window.innerHeight : 1080
          ),
        },
        iChannel0: { value: noiseTexture },
      },
      vertexShader,
      fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
    });
  }, [noiseTexture]);

  useFrame((state) => {
    if (meshRef.current && meshRef.current.material instanceof THREE.ShaderMaterial) {
      meshRef.current.material.uniforms.iTime.value = state.clock.elapsedTime * speed;
      meshRef.current.material.uniforms.iResolution.value.set(
        state.size.width,
        state.size.height
      );
    }
  });

  return (
    <mesh ref={meshRef} material={material}>
      <planeGeometry args={[10, 10]} />
    </mesh>
  );
}

interface GlitterFinalProps {
  speed?: number;
  intensity?: number;
  className?: string;
}

/**
 * GlitterFinal Component
 * WebGL shader-based glitter effect overlay
 */
export function GlitterFinal({
  speed = 1,
  intensity = 5.0,
  className = "",
}: GlitterFinalProps) {
  return (
    <div
      className={cn(
        "fixed scale-125 inset-0 w-full h-full mix-blend-screen pointer-events-none",
        className
      )}
      style={{ width: "100vw", height: "100vh", zIndex: 0 }}
    >
      <Canvas
        camera={{ position: [0, 0, 8], fov: 35 }}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
        }}
        gl={{ powerPreference: "high-performance", alpha: true }}
      >
        <SparklesPlane speed={speed} intensity={intensity} />
      </Canvas>
    </div>
  );
}

// ============================================================================
// GLITTER BACKGROUND COMPONENT
// ============================================================================

interface GlitterBackgroundProps {
  /**
   * Speed of the glitter animation (default: 0.75)
   * Higher values = faster animation
   */
  speed?: number;
  /**
   * Intensity of the glitter effect (default: 5.0)
   * Higher values = brighter sparkles
   */
  intensity?: number;
  /**
   * Additional CSS classes for the container
   */
  className?: string;
}

/**
 * Component - WebGL Glitter Background
 *
 * Full-screen animated background with WebGL shader-based sparkles.
 * Perfect for hero sections, landing pages, or any area needing visual interest.
 *
 * @example
 * ```tsx
 * <GlitterBackground speed={0.75} intensity={5.0} />
 * ```
 */
export const GlitterBackground = ({
  speed = 0.75,
  intensity = 5.0,
  className = "",
}: GlitterBackgroundProps) => {
  return (
    <div className={cn("min-w-screen h-screen min-h-screen relative", className)}>
      {/* GlitterFinal background effect - WebGL shader-based sparkles */}
      <GlitterFinal speed={speed} intensity={intensity} />
    </div>
  );
};

export default GlitterBackground;
