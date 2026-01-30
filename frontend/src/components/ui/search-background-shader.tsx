import { useRef, useEffect, Suspense } from 'react';
import * as THREE from 'three';

export function SearchBackgroundShader() {
  const mountRef = useRef<HTMLDivElement>(null);
  const lightRef = useRef<THREE.PointLight | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);
  const frameIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const currentMount = mountRef.current;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      50, // Reduced FOV for subtler effect
      currentMount.clientWidth / currentMount.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 5; // Moved further back for less prominence

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'low-power' // Optimize for battery life
    });
    renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap pixel ratio for performance
    currentMount.appendChild(renderer.domElement);

    // Create geometry with fewer subdivisions for performance
    const geometry = new THREE.IcosahedronGeometry(1.5, 32);

    // Subtle shader material with muted colors
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        pointLightPos: { value: new THREE.Vector3(0, 0, 5) },
        // Subtle purple-blue gradient matching the shine border
        color1: { value: new THREE.Color('#8B5CF6') }, // Purple
        color2: { value: new THREE.Color('#3B82F6') }, // Blue
        color3: { value: new THREE.Color('#10B981') }, // Green accent
        opacity: { value: 0.08 } // Very subtle opacity
      },
      vertexShader: `
        uniform float time;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying float vDisplacement;

        // Simplified noise for performance
        float noise(vec3 p) {
          return sin(p.x * 2.0) * sin(p.y * 2.0) * sin(p.z * 2.0);
        }

        void main() {
          vNormal = normal;
          vPosition = position;

          // Slower, subtler displacement
          float displacement = noise(position * 1.5 + time * 0.2) * 0.1;
          vDisplacement = displacement;

          vec3 newPosition = position + normal * displacement;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 color1;
        uniform vec3 color2;
        uniform vec3 color3;
        uniform vec3 pointLightPos;
        uniform float opacity;
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying float vDisplacement;

        void main() {
          vec3 normal = normalize(vNormal);
          vec3 viewDir = normalize(cameraPosition - vPosition);

          // Subtle lighting
          vec3 lightDir = normalize(pointLightPos - vPosition);
          float diffuse = max(dot(normal, lightDir), 0.0) * 0.3;

          // Gentle fresnel effect for edge glow
          float fresnel = 1.0 - dot(normal, viewDir);
          fresnel = pow(fresnel, 3.0) * 0.5;

          // Mix colors based on position and displacement
          vec3 color = mix(color1, color2, vPosition.y * 0.5 + 0.5);
          color = mix(color, color3, vDisplacement * 2.0 + 0.5);

          // Final color with lighting
          vec3 finalColor = color * (0.3 + diffuse) + color * fresnel;

          // Very low opacity for subtlety
          gl_FragColor = vec4(finalColor, opacity);
        }
      `,
      transparent: true,
      wireframe: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.y = 0; // Centered position
    meshRef.current = mesh;
    scene.add(mesh);

    // Subtle point light
    const pointLight = new THREE.PointLight(0xffffff, 0.5, 100);
    pointLight.position.set(0, 0, 5);
    lightRef.current = pointLight;
    scene.add(pointLight);

    // Ambient light for overall visibility
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.1);
    scene.add(ambientLight);

    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const animate = (t: number) => {
      // Very slow time-based animation
      material.uniforms.time.value = t * 0.0001;

      // Gentle automatic rotation
      if (meshRef.current) {
        meshRef.current.rotation.y += 0.0002;
        meshRef.current.rotation.x += 0.0001;

        // Smooth mouse following with damping
        targetX = mouseX * 0.5;
        targetY = mouseY * 0.5;
        meshRef.current.rotation.x += (targetY - meshRef.current.rotation.x) * 0.02;
        meshRef.current.rotation.y += (targetX - meshRef.current.rotation.y) * 0.02;
      }

      renderer.render(scene, camera);
      frameIdRef.current = requestAnimationFrame(animate);
    };
    animate(0);

    const handleResize = () => {
      camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;

      // Update light position for subtle interaction
      if (lightRef.current) {
        lightRef.current.position.x = mouseX * 3;
        lightRef.current.position.y = mouseY * 3;
      }
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      if (frameIdRef.current) {
        cancelAnimationFrame(frameIdRef.current);
      }
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      if (currentMount && renderer.domElement) {
        currentMount.removeChild(renderer.domElement);
      }
      renderer.dispose();
      geometry.dispose();
      material.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{
        zIndex: 0,
        opacity: 0.6 // Additional opacity control at container level
      }}
      aria-hidden="true"
    />
  );
}

export function SearchPageBackground() {
  return (
    <>
      {/* Gradient overlay for depth */}
      <div className="fixed inset-0 bg-gradient-to-br from-gray-50/50 via-white/30 to-gray-100/50 pointer-events-none" style={{ zIndex: 0 }} />

      {/* 3D Shader background */}
      <Suspense fallback={
        <div className="fixed inset-0 bg-gradient-to-br from-gray-50 to-gray-100" style={{ zIndex: 0 }} />
      }>
        <SearchBackgroundShader />
      </Suspense>

      {/* Additional subtle gradients for cohesion - removed heavy overlays */}
      <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 1 }}>
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/3 via-transparent to-blue-500/3" />
      </div>
    </>
  );
}
