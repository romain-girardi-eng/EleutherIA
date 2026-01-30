import { useRef, useEffect, Suspense } from 'react';
import * as THREE from 'three';

interface NeuralNode {
  position: THREE.Vector3;
  connections: number[];
  activation: number;
  pulsePhase: number;
}

export function GraphRAGNeuralNetwork({ isQuerying = false }: { isQuerying?: boolean }) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const nodesRef = useRef<NeuralNode[]>([]);
  const particlesRef = useRef<THREE.Points | null>(null);
  const connectionLinesRef = useRef<THREE.LineSegments | null>(null);
  const frameIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const currentMount = mountRef.current;
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      60,
      currentMount.clientWidth / currentMount.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 0, 30);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    currentMount.appendChild(renderer.domElement);

    // Create neural network nodes
    const nodeCount = 50;
    const nodes: NeuralNode[] = [];
    const nodePositions = new Float32Array(nodeCount * 3);
    const nodeColors = new Float32Array(nodeCount * 3);
    const nodeSizes = new Float32Array(nodeCount);

    for (let i = 0; i < nodeCount; i++) {
      const radius = 15;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      nodes.push({
        position: new THREE.Vector3(x, y, z),
        connections: [],
        activation: Math.random(),
        pulsePhase: Math.random() * Math.PI * 2
      });

      nodePositions[i * 3] = x;
      nodePositions[i * 3 + 1] = y;
      nodePositions[i * 3 + 2] = z;

      // Initial colors - purple to blue gradient
      const t = i / nodeCount;
      nodeColors[i * 3] = 0.545 + t * 0.2;     // R
      nodeColors[i * 3 + 1] = 0.361 - t * 0.2; // G
      nodeColors[i * 3 + 2] = 0.965;           // B

      nodeSizes[i] = Math.random() * 3 + 2;
    }

    // Create connections between nodes
    const connectionCount = nodeCount * 3;
    const connectionPositions = new Float32Array(connectionCount * 6);
    const connectionColors = new Float32Array(connectionCount * 6);
    let connectionIndex = 0;

    for (let i = 0; i < nodeCount; i++) {
      const numConnections = Math.floor(Math.random() * 4) + 2;
      for (let j = 0; j < numConnections; j++) {
        const targetIndex = Math.floor(Math.random() * nodeCount);
        if (targetIndex !== i && connectionIndex < connectionCount) {
          nodes[i].connections.push(targetIndex);

          // Line start point
          connectionPositions[connectionIndex * 6] = nodes[i].position.x;
          connectionPositions[connectionIndex * 6 + 1] = nodes[i].position.y;
          connectionPositions[connectionIndex * 6 + 2] = nodes[i].position.z;

          // Line end point
          connectionPositions[connectionIndex * 6 + 3] = nodes[targetIndex].position.x;
          connectionPositions[connectionIndex * 6 + 4] = nodes[targetIndex].position.y;
          connectionPositions[connectionIndex * 6 + 5] = nodes[targetIndex].position.z;

          // Connection colors - subtle blue
          for (let k = 0; k < 6; k++) {
            connectionColors[connectionIndex * 6 + k] = k % 3 === 2 ? 0.8 : 0.3;
          }

          connectionIndex++;
        }
      }
    }

    nodesRef.current = nodes;

    // Create node particles
    const nodeGeometry = new THREE.BufferGeometry();
    nodeGeometry.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3));
    nodeGeometry.setAttribute('color', new THREE.BufferAttribute(nodeColors, 3));
    nodeGeometry.setAttribute('size', new THREE.BufferAttribute(nodeSizes, 1));

    const nodeMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        activeQuery: { value: 0.0 }
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        varying float vActivation;
        uniform float time;
        uniform float activeQuery;

        void main() {
          vColor = color;

          // Pulsing effect
          float pulse = sin(time * 2.0 + position.x * 0.5) * 0.5 + 0.5;
          vActivation = pulse * activeQuery + (1.0 - activeQuery) * 0.5;

          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = size * (300.0 / -mvPosition.z) * (1.0 + vActivation * 0.5);
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vActivation;

        void main() {
          vec2 center = gl_PointCoord - vec2(0.5);
          float dist = length(center);

          if (dist > 0.5) discard;

          float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
          alpha *= 0.3 + vActivation * 0.5;

          vec3 finalColor = vColor + vec3(0.2, 0.3, 0.5) * vActivation;
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const nodePoints = new THREE.Points(nodeGeometry, nodeMaterial);
    particlesRef.current = nodePoints;
    scene.add(nodePoints);

    // Create connection lines
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(connectionPositions.slice(0, connectionIndex * 6), 3));
    lineGeometry.setAttribute('color', new THREE.BufferAttribute(connectionColors.slice(0, connectionIndex * 6), 3));

    const lineMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.1,
      blending: THREE.AdditiveBlending
    });

    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    connectionLinesRef.current = lines;
    scene.add(lines);

    // Create flowing particles along connections
    const flowParticleCount = 100;
    const flowPositions = new Float32Array(flowParticleCount * 3);
    const flowVelocities = new Float32Array(flowParticleCount * 3);
    const flowColors = new Float32Array(flowParticleCount * 3);

    for (let i = 0; i < flowParticleCount; i++) {
      const nodeIndex = Math.floor(Math.random() * nodes.length);
      const node = nodes[nodeIndex];

      flowPositions[i * 3] = node.position.x;
      flowPositions[i * 3 + 1] = node.position.y;
      flowPositions[i * 3 + 2] = node.position.z;

      if (node.connections.length > 0) {
        const targetNode = nodes[node.connections[0]];
        const direction = new THREE.Vector3()
          .subVectors(targetNode.position, node.position)
          .normalize()
          .multiplyScalar(0.05);

        flowVelocities[i * 3] = direction.x;
        flowVelocities[i * 3 + 1] = direction.y;
        flowVelocities[i * 3 + 2] = direction.z;
      }

      // Bright colors for flow particles
      flowColors[i * 3] = 0.4;     // R
      flowColors[i * 3 + 1] = 0.8; // G
      flowColors[i * 3 + 2] = 1.0; // B
    }

    const flowGeometry = new THREE.BufferGeometry();
    flowGeometry.setAttribute('position', new THREE.BufferAttribute(flowPositions, 3));
    flowGeometry.setAttribute('velocity', new THREE.BufferAttribute(flowVelocities, 3));
    flowGeometry.setAttribute('color', new THREE.BufferAttribute(flowColors, 3));

    const flowMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        activeQuery: { value: 0.0 }
      },
      vertexShader: `
        attribute vec3 velocity;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float time;
        uniform float activeQuery;

        void main() {
          vColor = color;

          vec3 pos = position + velocity * time * activeQuery * 10.0;

          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = (200.0 / -mvPosition.z) * (0.5 + activeQuery * 2.0);
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        uniform float activeQuery;

        void main() {
          vec2 center = gl_PointCoord - vec2(0.5);
          float dist = length(center);

          if (dist > 0.5) discard;

          float alpha = (1.0 - smoothstep(0.0, 0.5, dist)) * activeQuery * 0.8;
          gl_FragColor = vec4(vColor, alpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const flowPoints = new THREE.Points(flowGeometry, flowMaterial);
    scene.add(flowPoints);

    // Animation
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    const animate = (time: number) => {
      const t = time * 0.001;

      // Update shader uniforms
      if (nodeMaterial.uniforms) {
        nodeMaterial.uniforms.time.value = t;
        nodeMaterial.uniforms.activeQuery.value = isQuerying ? 1.0 : 0.0;
      }

      if (flowMaterial.uniforms) {
        flowMaterial.uniforms.time.value = t % 1;
        flowMaterial.uniforms.activeQuery.value = isQuerying ? 1.0 : 0.0;
      }

      // Rotate the entire network
      if (nodePoints) {
        nodePoints.rotation.y += 0.0005;
        nodePoints.rotation.x = Math.sin(t * 0.2) * 0.1;
      }

      if (lines) {
        lines.rotation.y += 0.0005;
        lines.rotation.x = Math.sin(t * 0.2) * 0.1;
      }

      if (flowPoints) {
        flowPoints.rotation.y += 0.0005;
        flowPoints.rotation.x = Math.sin(t * 0.2) * 0.1;
      }

      // Smooth mouse following
      targetRotationX = mouseY * 0.2;
      targetRotationY = mouseX * 0.2;

      if (scene.rotation) {
        scene.rotation.x += (targetRotationX - scene.rotation.x) * 0.05;
        scene.rotation.y += (targetRotationY - scene.rotation.y) * 0.05;
      }

      // Pulse connections when querying
      if (isQuerying && lineMaterial) {
        lineMaterial.opacity = 0.1 + Math.sin(t * 3) * 0.05;
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
    };
  }, [isQuerying]);

  return (
    <div
      ref={mountRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{
        zIndex: 0,
        opacity: 0.7
      }}
      aria-hidden="true"
    />
  );
}

export function GraphRAGBackground({ isQuerying = false }: { isQuerying?: boolean }) {
  return (
    <>
      {/* Base gradient for depth */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-purple-950/20 to-blue-950/30" style={{ zIndex: 0 }} />

      {/* Neural network visualization */}
      <Suspense fallback={
        <div className="fixed inset-0 bg-gradient-to-br from-slate-950 to-blue-950/30" style={{ zIndex: 0 }} />
      }>
        <GraphRAGNeuralNetwork isQuerying={isQuerying} />
      </Suspense>

      {/* Overlay gradients for atmosphere */}
      <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 1 }}>
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/30" />
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 via-transparent to-blue-900/10" />

        {/* Vignette effect */}
        <div className="absolute inset-0" style={{
          background: 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.4) 100%)'
        }} />
      </div>
    </>
  );
}
