import { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';
import { Play, Pause, RotateCcw, Sparkles, Search } from 'lucide-react';

interface EmbeddingPoint {
  id: string;
  label: string;
  category: string;
  position: THREE.Vector3;
  originalPosition: THREE.Vector3;
  color: string;
  size: number;
}

// Sample philosophical concepts for demo
const DEMO_CONCEPTS = [
  // Stoic cluster
  { id: 'fate', label: 'Fate (εἱμαρμένη)', category: 'Stoic', basePos: [0, 0, 0] },
  { id: 'providence', label: 'Providence (πρόνοια)', category: 'Stoic', basePos: [15, 8, 5] },
  { id: 'logos', label: 'Logos (λόγος)', category: 'Stoic', basePos: [-10, 12, -8] },
  { id: 'assent', label: 'Assent (συγκατάθεσις)', category: 'Stoic', basePos: [8, -5, 12] },
  { id: 'impression', label: 'Impression (φαντασία)', category: 'Stoic', basePos: [-5, -10, 8] },

  // Epicurean cluster
  { id: 'swerve', label: 'Swerve (clinamen)', category: 'Epicurean', basePos: [60, 20, -30] },
  { id: 'atoms', label: 'Atoms (ἄτομοι)', category: 'Epicurean', basePos: [70, 15, -25] },
  { id: 'pleasure', label: 'Pleasure (ἡδονή)', category: 'Epicurean', basePos: [55, 30, -35] },
  { id: 'ataraxia', label: 'Ataraxia (ἀταραξία)', category: 'Epicurean', basePos: [65, 25, -20] },

  // Aristotelian cluster
  { id: 'deliberation', label: 'Deliberation (βούλευσις)', category: 'Aristotelian', basePos: [-50, -30, 40] },
  { id: 'choice', label: 'Choice (προαίρεσις)', category: 'Aristotelian', basePos: [-55, -25, 35] },
  { id: 'virtue', label: 'Virtue (ἀρετή)', category: 'Aristotelian', basePos: [-45, -35, 45] },
  { id: 'practical_wisdom', label: 'Practical Wisdom (φρόνησις)', category: 'Aristotelian', basePos: [-60, -20, 50] },
  { id: 'mean', label: 'The Mean (μεσότης)', category: 'Aristotelian', basePos: [-40, -40, 38] },

  // Platonic cluster
  { id: 'soul', label: 'Soul (ψυχή)', category: 'Platonic', basePos: [30, 60, 50] },
  { id: 'forms', label: 'Forms (εἶδος)', category: 'Platonic', basePos: [25, 70, 55] },
  { id: 'justice', label: 'Justice (δικαιοσύνη)', category: 'Platonic', basePos: [35, 55, 60] },
  { id: 'reason', label: 'Reason (νοῦς)', category: 'Platonic', basePos: [40, 65, 45] },

  // Free Will central concepts
  { id: 'free_will', label: "What's up to us (ἐφ' ἡμῖν)", category: 'Core', basePos: [0, 30, 0] },
  { id: 'responsibility', label: 'Responsibility (αἰτία)', category: 'Core', basePos: [10, 35, -5] },
  { id: 'necessity', label: 'Necessity (ἀνάγκη)', category: 'Core', basePos: [-8, 25, 8] },
  { id: 'contingency', label: 'Contingency (ἐνδεχόμενον)', category: 'Core', basePos: [5, 40, 10] },
];

const CATEGORY_COLORS: Record<string, string> = {
  'Stoic': '#60a5fa',       // Blue
  'Epicurean': '#c084fc',   // Purple
  'Aristotelian': '#4ade80', // Green
  'Platonic': '#f472b6',    // Pink
  'Core': '#fbbf24',        // Amber
};

interface Props {
  className?: string;
  onConceptSelect?: (concept: { id: string; label: string; category: string }) => void;
}

export default function EmbeddingsVisualization3D({ className = '', onConceptSelect }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const composerRef = useRef<EffectComposer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const frameIdRef = useRef<number | null>(null);
  const pointsRef = useRef<Map<string, EmbeddingPoint>>(new Map());
  const meshesRef = useRef<Map<string, THREE.Mesh>>(new Map());
  const materialsRef = useRef<Map<string, THREE.MeshPhysicalMaterial>>(new Map());
  const connectionsRef = useRef<THREE.LineSegments | null>(null);
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2());

  const [isPlaying, setIsPlaying] = useState(true);
  // Store only simple data for tooltip, not Three.js objects
  const [hoveredPoint, setHoveredPoint] = useState<{ id: string; label: string; category: string; color: string } | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [highlightedCategory, setHighlightedCategory] = useState<string | null>(null);

  // Animation time ref
  const timeRef = useRef(0);
  // Track hovered mesh ID for animation loop to respect
  const hoveredIdRef = useRef<string | null>(null);
  // Track highlighted category for animation loop
  const highlightedCategoryRef = useRef<string | null>(null);

  const initScene = useCallback(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a1a);
    scene.fog = new THREE.FogExp2(0x0a0a1a, 0.003);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      60,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      2000
    );
    camera.position.set(100, 80, 150);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Post-processing with bloom
    const composer = new EffectComposer(renderer);
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(mountRef.current.clientWidth, mountRef.current.clientHeight),
      0.8,  // strength
      0.4,  // radius
      0.85  // threshold
    );
    composer.addPass(bloomPass);
    composerRef.current = composer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 50;
    controls.maxDistance = 400;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
    controlsRef.current = controls;

    // Ambient lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    // Point lights for dramatic effect
    const pointLight1 = new THREE.PointLight(0x60a5fa, 2, 300);
    pointLight1.position.set(50, 50, 50);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xc084fc, 2, 300);
    pointLight2.position.set(-50, -50, 50);
    scene.add(pointLight2);

    // Create coordinate grid (subtle)
    const gridHelper = new THREE.GridHelper(200, 20, 0x1e3a5f, 0x0f1729);
    gridHelper.position.y = -50;
    scene.add(gridHelper);

    // Create axis indicators (subtle glow lines)
    const axisMaterial = new THREE.LineBasicMaterial({
      color: 0x3b82f6,
      transparent: true,
      opacity: 0.3
    });

    // X axis
    const xGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-100, 0, 0),
      new THREE.Vector3(100, 0, 0)
    ]);
    const xAxis = new THREE.Line(xGeom, axisMaterial);
    scene.add(xAxis);

    // Y axis
    const yGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, -100, 0),
      new THREE.Vector3(0, 100, 0)
    ]);
    const yAxis = new THREE.Line(yGeom, axisMaterial);
    scene.add(yAxis);

    // Z axis
    const zGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, -100),
      new THREE.Vector3(0, 0, 100)
    ]);
    const zAxis = new THREE.Line(zGeom, axisMaterial);
    scene.add(zAxis);

    // Create embedding points
    createEmbeddingPoints(scene);

    // Create connections between related concepts
    createConnections(scene);

    // Add particle field background
    createParticleField(scene);

  }, []);

  const createEmbeddingPoints = (scene: THREE.Scene) => {
    DEMO_CONCEPTS.forEach((concept) => {
      const color = CATEGORY_COLORS[concept.category] || '#ffffff';
      const position = new THREE.Vector3(
        concept.basePos[0] + (Math.random() - 0.5) * 5,
        concept.basePos[1] + (Math.random() - 0.5) * 5,
        concept.basePos[2] + (Math.random() - 0.5) * 5
      );

      // Create glowing sphere
      const geometry = new THREE.SphereGeometry(concept.category === 'Core' ? 4 : 3, 32, 32);
      const material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(color),
        emissive: new THREE.Color(color),
        emissiveIntensity: 0.5,
        metalness: 0.3,
        roughness: 0.4,
        transparent: true,
        opacity: 0.9,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(position);
      mesh.userData = { id: concept.id, label: concept.label, category: concept.category };
      scene.add(mesh);
      meshesRef.current.set(concept.id, mesh);
      materialsRef.current.set(concept.id, material);

      // Add glow halo (separate from main mesh to avoid raycasting issues)
      const glowGeometry = new THREE.SphereGeometry(concept.category === 'Core' ? 6 : 4.5, 32, 32);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: 0.15,
        side: THREE.BackSide,
      });
      const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
      // Disable raycasting on glow mesh
      glowMesh.raycast = () => {};
      mesh.add(glowMesh);

      // Store point data
      const point: EmbeddingPoint = {
        id: concept.id,
        label: concept.label,
        category: concept.category,
        position: position.clone(),
        originalPosition: position.clone(),
        color,
        size: concept.category === 'Core' ? 4 : 3,
      };
      pointsRef.current.set(concept.id, point);
    });
  };

  const createConnections = (scene: THREE.Scene) => {
    // Define semantic connections
    const connections = [
      // Stoic internal connections
      ['fate', 'providence'], ['fate', 'logos'], ['assent', 'impression'],
      ['logos', 'assent'], ['providence', 'logos'],
      // Epicurean internal
      ['swerve', 'atoms'], ['atoms', 'pleasure'], ['pleasure', 'ataraxia'],
      // Aristotelian internal
      ['deliberation', 'choice'], ['choice', 'virtue'], ['virtue', 'practical_wisdom'],
      ['practical_wisdom', 'mean'], ['deliberation', 'practical_wisdom'],
      // Platonic internal
      ['soul', 'forms'], ['forms', 'justice'], ['soul', 'reason'], ['justice', 'reason'],
      // Core connections to schools
      ['free_will', 'assent'], ['free_will', 'choice'], ['free_will', 'swerve'],
      ['responsibility', 'choice'], ['responsibility', 'assent'],
      ['necessity', 'fate'], ['necessity', 'atoms'],
      ['contingency', 'swerve'], ['contingency', 'deliberation'],
    ];

    const positions: number[] = [];
    const colors: number[] = [];

    connections.forEach(([sourceId, targetId]) => {
      const sourceMesh = meshesRef.current.get(sourceId);
      const targetMesh = meshesRef.current.get(targetId);
      if (sourceMesh && targetMesh) {
        positions.push(
          sourceMesh.position.x, sourceMesh.position.y, sourceMesh.position.z,
          targetMesh.position.x, targetMesh.position.y, targetMesh.position.z
        );
        // Gradient color based on distance
        const color = new THREE.Color(0x3b82f6);
        colors.push(color.r, color.g, color.b, color.r, color.g, color.b);
      }
    });

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    const material = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.25,
      linewidth: 1,
    });

    const lines = new THREE.LineSegments(geometry, material);
    scene.add(lines);
    connectionsRef.current = lines;
  };

  const createParticleField = (scene: THREE.Scene) => {
    const particleCount = 500;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 400;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 400;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 400;

      const color = new THREE.Color().setHSL(0.6 + Math.random() * 0.2, 0.8, 0.6);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.4,
      sizeAttenuation: true,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);
  };

  const animate = useCallback(() => {
    if (!isPlaying) return;

    frameIdRef.current = requestAnimationFrame(animate);
    timeRef.current += 0.01;

    const currentHoveredId = hoveredIdRef.current;
    const currentHighlightedCategory = highlightedCategoryRef.current;

    // Animate points with subtle floating motion
    meshesRef.current.forEach((mesh, id) => {
      const point = pointsRef.current.get(id);
      const material = materialsRef.current.get(id);

      if (point && material) {
        const offset = Math.sin(timeRef.current + point.originalPosition.x * 0.1) * 0.5;
        mesh.position.y = point.originalPosition.y + offset;

        // Determine states
        const isDimmed = currentHighlightedCategory !== null && point.category !== currentHighlightedCategory;
        const isHovered = id === currentHoveredId;

        if (isHovered) {
          // Hovered node: brighter and larger
          material.emissiveIntensity = 1.0;
          material.opacity = 0.95;
          const hoverScale = 1.3 + Math.sin(timeRef.current * 4) * 0.05;
          mesh.scale.setScalar(hoverScale);
        } else if (isDimmed) {
          // Dimmed by category filter
          material.emissiveIntensity = 0.1;
          material.opacity = 0.2;
          const scale = 1 + Math.sin(timeRef.current * 2 + point.originalPosition.z * 0.1) * 0.02;
          mesh.scale.setScalar(scale);
        } else {
          // Normal pulse effect
          material.emissiveIntensity = 0.5;
          material.opacity = 0.9;
          const scale = 1 + Math.sin(timeRef.current * 2 + point.originalPosition.z * 0.1) * 0.05;
          mesh.scale.setScalar(scale);
        }
      }
    });

    // Update controls
    controlsRef.current?.update();

    // Render with post-processing
    if (composerRef.current) {
      composerRef.current.render();
    } else if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current);
    }
  }, [isPlaying]);

  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!mountRef.current || !cameraRef.current) return;

    const rect = mountRef.current.getBoundingClientRect();
    mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);
    const meshes = Array.from(meshesRef.current.values());
    const intersects = raycasterRef.current.intersectObjects(meshes, false);

    if (intersects.length > 0) {
      const intersected = intersects[0].object as THREE.Mesh;
      const userData = intersected.userData;
      if (userData && typeof userData.id === 'string') {
        const point = pointsRef.current.get(userData.id);
        if (point) {
          // Update ref for animation loop (hover visual effects)
          hoveredIdRef.current = userData.id;
          // Update React state for tooltip (only simple data)
          setHoveredPoint({
            id: point.id,
            label: point.label,
            category: point.category,
            color: point.color,
          });
          setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
          return;
        }
      }
    }

    // Clear hover state
    hoveredIdRef.current = null;
    setHoveredPoint(null);
    setTooltipPos(null);
  }, []);

  // Use ref for hoveredPoint in click handler to avoid recreating the callback
  const hoveredPointRef = useRef(hoveredPoint);
  hoveredPointRef.current = hoveredPoint;

  const handleClick = useCallback(() => {
    const point = hoveredPointRef.current;
    if (point && onConceptSelect) {
      onConceptSelect({
        id: point.id,
        label: point.label,
        category: point.category,
      });
    }
  }, [onConceptSelect]);

  const resetCamera = useCallback(() => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(100, 80, 150);
      controlsRef.current.target.set(0, 20, 0);
      controlsRef.current.update();
    }
  }, []);

  const toggleAutoRotate = useCallback(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = !controlsRef.current.autoRotate;
    }
  }, []);

  // Filter/highlight by category - just update refs, animation loop handles visuals
  const highlightCategory = useCallback((category: string | null) => {
    highlightedCategoryRef.current = category;
    setHighlightedCategory(category);
  }, []);

  useEffect(() => {
    initScene();

    const currentMount = mountRef.current;
    const currentMeshes = meshesRef.current;
    const currentMaterials = materialsRef.current;
    const currentPoints = pointsRef.current;
    currentMount?.addEventListener('mousemove', handleMouseMove);
    currentMount?.addEventListener('click', handleClick);

    // Handle resize
    const handleResize = () => {
      if (!mountRef.current || !cameraRef.current || !rendererRef.current || !composerRef.current) return;

      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;

      cameraRef.current.aspect = width / height;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(width, height);
      composerRef.current.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      currentMount?.removeEventListener('mousemove', handleMouseMove);
      currentMount?.removeEventListener('click', handleClick);
      window.removeEventListener('resize', handleResize);

      if (frameIdRef.current) {
        cancelAnimationFrame(frameIdRef.current);
      }

      // Clear all refs to prevent stale data on HMR
      currentMeshes.clear();
      currentMaterials.clear();
      currentPoints.clear();
      hoveredIdRef.current = null;
      highlightedCategoryRef.current = null;

      if (rendererRef.current && currentMount) {
        currentMount.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
    };
  }, [initScene, handleMouseMove, handleClick]);

  useEffect(() => {
    if (isPlaying) {
      animate();
    } else if (frameIdRef.current) {
      cancelAnimationFrame(frameIdRef.current);
    }
  }, [isPlaying, animate]);

  return (
    <div className={`relative rounded-2xl overflow-hidden ${className}`}>
      {/* 3D Canvas */}
      <div
        ref={mountRef}
        className="w-full h-full min-h-[500px]"
        style={{ cursor: hoveredPoint ? 'pointer' : 'grab' }}
      />

      {/* Tooltip */}
      {hoveredPoint && tooltipPos && (
        <div
          className="absolute pointer-events-none z-20 px-4 py-3 bg-slate-900/95 backdrop-blur-md rounded-xl border border-white/10 shadow-2xl"
          style={{
            left: tooltipPos.x + 15,
            top: tooltipPos.y - 10,
            transform: 'translateY(-50%)',
          }}
        >
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: hoveredPoint.color }}
            />
            <span className="text-white font-medium">{hoveredPoint.label}</span>
          </div>
          <span className="text-xs text-white/60">{hoveredPoint.category}</span>
        </div>
      )}

      {/* Controls Overlay */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="p-2 bg-white/10 backdrop-blur-md rounded-lg border border-white/10 text-white/80 hover:text-white hover:bg-white/20 transition-all"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>
        <button
          onClick={toggleAutoRotate}
          className="p-2 bg-white/10 backdrop-blur-md rounded-lg border border-white/10 text-white/80 hover:text-white hover:bg-white/20 transition-all"
          title="Toggle auto-rotate"
        >
          <Sparkles className="w-4 h-4" />
        </button>
        <button
          onClick={resetCamera}
          className="p-2 bg-white/10 backdrop-blur-md rounded-lg border border-white/10 text-white/80 hover:text-white hover:bg-white/20 transition-all"
          title="Reset view"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Category Filter */}
      <div className="absolute bottom-4 left-4 right-4 flex flex-wrap gap-2 justify-center">
        <button
          onClick={() => highlightCategory(null)}
          className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
            highlightedCategory === null
              ? 'bg-white text-slate-900'
              : 'bg-white/10 text-white/70 hover:bg-white/20'
          }`}
        >
          All Schools
        </button>
        {Object.entries(CATEGORY_COLORS).map(([category, color]) => (
          <button
            key={category}
            onClick={() => highlightCategory(category)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-1.5 ${
              highlightedCategory === category
                ? 'bg-white text-slate-900'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: color }}
            />
            {category}
          </button>
        ))}
      </div>

      {/* Info Panel */}
      <div className="absolute top-4 left-4 max-w-xs">
        <div className="p-4 bg-slate-900/90 backdrop-blur-md rounded-xl border border-white/10">
          <h3 className="text-white font-semibold text-sm mb-2 flex items-center gap-2">
            <Search className="w-4 h-4 text-blue-400" />
            3D Semantic Space
          </h3>
          <p className="text-white/60 text-xs leading-relaxed">
            Each point represents a philosophical concept. Proximity = semantic similarity.
            Related concepts cluster together based on 3,072-dimensional embeddings.
          </p>
        </div>
      </div>
    </div>
  );
}
