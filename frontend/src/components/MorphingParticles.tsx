/**
 * MorphingParticles.tsx
 *
 * Advanced morphing particle system for EleutherIA, transitions between:
 * - Knowledge Graph (clustered nodes with edges)
 * - Semantic Search Paths (query expansion from center)
 * - Reasoning Chains (branching inference paths)
 * - Embedding Space (vector cloud visualization)
 * - Query Burst (search radiating outward)
 *
 * Morphing particle effects adapted for GraphRAG visualization.
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/examples/jsm/postprocessing/BokehPass.js';

// Import types and constants from separate file to prevent HMR Fast Refresh issues
import { SHAPE_NAMES } from './MorphingParticles.types';
import type { MorphingParticlesConfig } from './MorphingParticles.types';
export type { ShapeName, MorphingParticlesConfig } from './MorphingParticles.types';

// ============================================================================
// 3DME OWL DATA CACHE (Loaded from /ParticleCloud-data.json)
// ============================================================================

interface Owl3DmeData {
  count: number;
  positions: number[];
  colors: number[];
}

// Module-level cache for 3Dme owl data
let owl3DmeCache: Owl3DmeData | null = null;
let owl3DmeLoadPromise: Promise<Owl3DmeData | null> | null = null;

/**
 * Load and cache the 3Dme owl particle data.
 * Returns cached data if already loaded.
 */
async function load3DmeOwlData(): Promise<Owl3DmeData | null> {
  // Return cached data if available
  if (owl3DmeCache) return owl3DmeCache;

  // Return existing promise if loading
  if (owl3DmeLoadPromise) return owl3DmeLoadPromise;

  // Start loading
  owl3DmeLoadPromise = fetch('/ParticleCloud-data.json')
    .then(response => {
      if (!response.ok) throw new Error(`Failed to load: ${response.status}`);
      return response.json();
    })
    .then((data: Owl3DmeData) => {
      owl3DmeCache = data;
      console.log('[MorphingParticles] 3Dme owl loaded:', data.count, 'particles');
      return data;
    })
    .catch(err => {
      console.warn('[MorphingParticles] Failed to load 3Dme owl:', err);
      return null;
    });

  return owl3DmeLoadPromise;
}

// Start loading immediately on module load
load3DmeOwlData();

// ============================================================================
// PHILOSOPHER DATA CACHE (Loaded from /philosopher-particles.json)
// ============================================================================

interface PhilosopherData {
  count: number;
  positions: number[];
  colors: number[];
}

// Module-level cache for philosopher data
let philosopherCache: PhilosopherData | null = null;
let philosopherLoadPromise: Promise<PhilosopherData | null> | null = null;

/**
 * Load and cache the philosopher particle data (depth-estimated from 2D image).
 * Returns cached data if already loaded.
 */
async function loadPhilosopherData(): Promise<PhilosopherData | null> {
  // Return cached data if available
  if (philosopherCache) return philosopherCache;

  // Return existing promise if loading
  if (philosopherLoadPromise) return philosopherLoadPromise;

  // Start loading
  philosopherLoadPromise = fetch('/philosopher-particles.json')
    .then(response => {
      if (!response.ok) throw new Error(`Failed to load: ${response.status}`);
      return response.json();
    })
    .then((data: PhilosopherData) => {
      philosopherCache = data;
      console.log('[MorphingParticles] Philosopher loaded:', data.count, 'particles');
      return data;
    })
    .catch(err => {
      console.warn('[MorphingParticles] Failed to load philosopher:', err);
      return null;
    });

  return philosopherLoadPromise;
}

// Start loading immediately on module load
loadPhilosopherData();

// ============================================================================
// PERFORMANCE DETECTION & ADAPTIVE QUALITY
// ============================================================================

interface DeviceProfile {
  isSafari: boolean;
  isMobile: boolean;
  isLowEnd: boolean;
  recommendedParticles: number;
  recommendedLines: number;
  pixelRatioLimit: number;
}

/**
 * Detect device capabilities for adaptive quality.
 * Safari/iOS needs special handling for WebGL.
 */
function detectDeviceProfile(): DeviceProfile {
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';

  const isSafari = /^((?!chrome|android).)*safari/i.test(ua);
  const isIOS = /iPad|iPhone|iPod/.test(ua);
  const isMobile = isIOS || /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(ua);

  // GPU tier detection via canvas
  let isLowEnd = false;
  if (typeof document !== 'undefined') {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl) {
        const debugInfo = (gl as WebGLRenderingContext).getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
          const renderer = (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
          // Intel integrated GPUs, Apple A-series (older), Mali, Adreno (budget)
          isLowEnd = /Intel|Mali-4|Mali-T6|Adreno 3|Adreno 4|Apple A[89]|Apple A10/.test(renderer);
        }
      }
    } catch {
      // Fallback: assume low-end for safety
      isLowEnd = isMobile;
    }
  }

  // Adaptive quality settings - MAXIMUM PARTICLES for dense cloud
  let recommendedParticles = 50000;  // VERY HIGH: Ultra-dense particle cloud
  let recommendedLines = 4000;       // LOW: Lines are expensive
  let pixelRatioLimit = 2;

  if (isLowEnd || (isMobile && isSafari)) {
    recommendedParticles = 20000;
    recommendedLines = 2000;
    pixelRatioLimit = 1.5;
  } else if (isMobile) {
    recommendedParticles = 30000;
    recommendedLines = 3000;
    pixelRatioLimit = 1.5;
  } else if (isSafari) {
    // Desktop Safari
    recommendedParticles = 40000;
    recommendedLines = 3000;
    pixelRatioLimit = 2;
  }

  return {
    isSafari,
    isMobile,
    isLowEnd,
    recommendedParticles,
    recommendedLines,
    pixelRatioLimit,
  };
}

// Cache device profile
const deviceProfile = detectDeviceProfile();
console.log('[MorphingParticles] Device profile:', deviceProfile);

// ============================================================================
// CONFIGURATION
// ============================================================================

const defaultConfig: Required<MorphingParticlesConfig> = {
  particleCount: deviceProfile.recommendedParticles, // Adaptive!
  morphDuration: 7,
  rotationSpeed: 0.15,
  particleSize: 0.7,     // SMALLER: Dense cloud of fine particles
  lineOpacity: 0.015,    // SUBTLER: Less visual noise from lines
  connectionDistance: 18, // REDUCED: Fewer line connections = better perf
  colorScheme: 'warm',
  selectedShape: null,

  // Visual enhancements
  enableBloom: false,
  bloomIntensity: 0.08,  // Minimal bloom
  enableTrails: false,
  trailLength: 0.3,
  enableDepthOfField: false, // REMOVED BOKEH AS REQUESTED

  // Interactivity
  enableZoom: true,
  enableHover: true,
  enableKeyboard: true,

  // Animation
  enableBreathing: true,
  breathingSpeed: 0.2,
  enableStaggeredMorph: true,
  staggerDirection: 'radial',
};

// Color schemes
const colorSchemes = {
  graphrag: {
    primary: new THREE.Color(0xff6b4a),   // Red/orange
    secondary: new THREE.Color(0x4ac4ff), // Cyan/blue
    accent: new THREE.Color(0xffffff),    // White
  },
  ancient: {
    primary: new THREE.Color(0xd4a574),   // Gold
    secondary: new THREE.Color(0x8b7355), // Bronze
    accent: new THREE.Color(0xf5e6d3),    // Cream
  },
  cool: {
    primary: new THREE.Color(0x667eea),   // Purple
    secondary: new THREE.Color(0x48c6ef), // Cyan
    accent: new THREE.Color(0xf093fb),    // Pink
  },
  warm: {
    primary: new THREE.Color(0xff6b6b),   // Red/coral
    secondary: new THREE.Color(0xfeca57), // Golden yellow
    accent: new THREE.Color(0xff9ff3),    // Pink
    tertiary: new THREE.Color(0x64b5f6),  // Subtle blue
  },
  rainbow: {
    primary: new THREE.Color(0xff1493),   // Deep pink
    secondary: new THREE.Color(0x00ffff), // Cyan
    accent: new THREE.Color(0x7fff00),    // Chartreuse
  },
};

// Rainbow palette for multi-color mode
const rainbowPalette = [
  new THREE.Color(0xff1493), // Deep pink
  new THREE.Color(0xff6b6b), // Coral
  new THREE.Color(0xffa500), // Orange
  new THREE.Color(0xffd700), // Gold
  new THREE.Color(0x7fff00), // Chartreuse
  new THREE.Color(0x00ff7f), // Spring green
  new THREE.Color(0x00ffff), // Cyan
  new THREE.Color(0x00bfff), // Deep sky blue
  new THREE.Color(0x8a2be2), // Blue violet
  new THREE.Color(0xff00ff), // Magenta
  new THREE.Color(0xffffff), // White
];

// ============================================================================
// SHAPE GENERATORS - GraphRAG / Semantic Search themed
// ============================================================================

type ShapeData = { pos: THREE.Vector3; normal: THREE.Vector3 };
type ShapeGenerator = (index: number, total: number) => ShapeData;

// Scale factor to make everything more compact
const SCALE = 0.6;

// ============================================================================
// NEW SHAPES: ATTRACTOR & PHILOSOPHER
// ============================================================================

// 1. AIZAWA ATTRACTOR (Deterministic Chaos / Fate)
// Pre-calculate points because it requires iteration
const calculateAizawaAttractor = (count: number) => {
  const points: ShapeData[] = [];
  let x = 0.1, y = 0, z = 0;
  const dt = 0.012;
  // Aizawa parameters
  const a = 0.95, b = 0.7, c = 0.6, d = 3.5, e = 0.25, f = 0.1;

  for(let i=0; i<count; i++) {
    const dx = (z - b) * x - d * y;
    const dy = d * x + (z - b) * y;
    const dz = c + a * z - (z*z*z)/3 - (x*x + y*y) * (1 + e * z) + f * z * x * x * x;

    x += dx * dt;
    y += dy * dt;
    z += dz * dt;

    // Scale and orient
    const pos = new THREE.Vector3(x, z, y).multiplyScalar(25 * SCALE);

    // Calculate normal based on velocity (tangent) cross up
    const velocity = new THREE.Vector3(dx, dz, dy).normalize();
    const normal = velocity.cross(new THREE.Vector3(0, 1, 0)).normalize();

    points.push({ pos, normal });
  }
  return points;
};
// Generate cache (enough for max particles)
const aizawaCache = calculateAizawaAttractor(150000);

const generateAttractorOfFate: ShapeGenerator = (index, _total) => {
  // Use modulo to loop if we have more particles than cache
  const data = aizawaCache[index % aizawaCache.length];
  return {
    pos: data.pos.clone(),
    normal: data.normal.clone()
  };
};

/** Knowledge Graph - Clustered nodes representing concepts with interconnections */
const generateKnowledgeGraph: ShapeGenerator = (index, total) => {
  const numClusters = 7; // Concept clusters
  const clusterIndex = index % numClusters;
  const indexInCluster = Math.floor(index / numClusters);
  const particlesPerCluster = Math.floor(total / numClusters);

  // Cluster centers arranged in a 3D network (like KG visualization)
  const clusterCenters = [
    new THREE.Vector3(0, 0, 0),        // Central concept (query)
    new THREE.Vector3(-50, 30, 20),    // Related concept 1
    new THREE.Vector3(50, 25, -15),    // Related concept 2
    new THREE.Vector3(-30, -40, 35),   // Related concept 3
    new THREE.Vector3(40, -35, 25),    // Related concept 4
    new THREE.Vector3(0, 50, -30),     // Related concept 5
    new THREE.Vector3(0, -50, -25),    // Related concept 6
  ];

  // Define edges between clusters (more connections for denser graph)
  const clusterEdges = [
    [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], // Central to all
    [1, 2], [2, 4], [4, 6], [6, 3], [3, 1],         // Ring connections
    [1, 5], [2, 5], [3, 5], [4, 5],                 // Top connections
    [1, 6], [2, 6], [3, 4],                         // Cross connections
  ];

  const center = clusterCenters[clusterIndex].clone().multiplyScalar(SCALE);
  const clusterRadius = (clusterIndex === 0 ? 35 : 25) * SCALE; // Central cluster larger

  // Fibonacci sphere distribution within cluster
  const phi = Math.acos(1 - 2 * (indexInCluster + 0.5) / particlesPerCluster);
  const theta = Math.PI * (1 + Math.sqrt(5)) * indexInCluster;

  const pos = new THREE.Vector3(
    center.x + clusterRadius * Math.sin(phi) * Math.cos(theta),
    center.y + clusterRadius * Math.sin(phi) * Math.sin(theta),
    center.z + clusterRadius * Math.cos(phi)
  );

  // Normal points away from cluster center (Spherical)
  const normal = pos.clone().sub(center).normalize();

  // Edges (simplified for normals - treating as cylinders/lines)
  const edgeThreshold = 0.65;
  const isEdge = indexInCluster > particlesPerCluster * edgeThreshold;
  if (isEdge) {
    const relevantEdges = clusterEdges.filter(([a, b]) => a === clusterIndex || b === clusterIndex);
    if (relevantEdges.length > 0) {
      const edgeIndex = indexInCluster % relevantEdges.length;
      const [a, b] = relevantEdges[edgeIndex];
      const targetCluster = a === clusterIndex ? b : a;
      const t = (indexInCluster - particlesPerCluster * edgeThreshold) / (particlesPerCluster * (1 - edgeThreshold));
      const targetCenter = clusterCenters[targetCluster].clone().multiplyScalar(SCALE);

      const midpoint = center.clone().lerp(targetCenter, 0.5);
      const direction = targetCenter.clone().sub(center).normalize();
      const perpendicular = new THREE.Vector3(-direction.y, direction.x, direction.z * 0.5).normalize();
      const curveAmount = 20 * SCALE * (1 + (edgeIndex % 3) * 0.3);
      const curveSign = edgeIndex % 2 === 0 ? 1 : -1;
      const controlPoint = midpoint.clone().add(perpendicular.multiplyScalar(curveAmount * curveSign));
      const oneMinusT = 1 - t;

      pos.copy(center.clone().multiplyScalar(oneMinusT * oneMinusT)
        .add(controlPoint.clone().multiplyScalar(2 * oneMinusT * t))
        .add(targetCenter.clone().multiplyScalar(t * t)));

      // Normal for edge is roughly perpendicular to direction
      normal.copy(perpendicular);
    }
  }

  return { pos, normal };
};

/** Semantic Search Paths - Query expanding into multiple search directions */
const generateSemanticPaths: ShapeGenerator = (index, total) => {
  const numPaths = 12; // Search paths from query
  const pathIndex = index % numPaths;
  const indexInPath = Math.floor(index / numPaths);
  const particlesPerPath = Math.floor(total / numPaths);

  // Path angles radiating from center
  const pathAngleXY = (pathIndex / numPaths) * Math.PI * 2;
  const pathAngleZ = ((pathIndex % 3) - 1) * 0.4; // Slight z variation

  // Position along path with branching
  const t = indexInPath / particlesPerPath;
  const distance = t * 120 * SCALE;

  // Create branching effect at mid-distance
  const branchOffset = t > 0.4 ? Math.sin(indexInPath * 0.5) * t * 15 * SCALE : 0;
  const branchAngle = pathAngleXY + branchOffset * 0.02;

  // Slight spiral motion
  const spiral = t * 0.3;

  const pos = new THREE.Vector3(
    Math.cos(branchAngle + spiral) * distance,
    Math.sin(branchAngle + spiral) * distance * 0.7,
    Math.sin(pathAngleZ) * distance * 0.5 + (Math.random() - 0.5) * t * 10 * SCALE
  );

  // Normal: Roughly perpendicular to the path (outwards)
  const normal = new THREE.Vector3(
    Math.cos(branchAngle + spiral),
    Math.sin(branchAngle + spiral),
    0
  ).normalize();

  return { pos, normal };
};

/** Reasoning Chains - Elegant spiraling tendrils like a jellyfish or lotus */
const generateReasoningChains: ShapeGenerator = (index, total) => {
  // Create elegant spiraling tendrils emanating from center
  const numTendrils = 12;
  const tendrilIndex = index % numTendrils;
  const indexInTendril = Math.floor(index / numTendrils);
  const particlesPerTendril = Math.floor(total / numTendrils);

  // Base angle for this tendril
  const baseAngle = (tendrilIndex / numTendrils) * Math.PI * 2;

  // Progress along tendril (0 to 1)
  const t = indexInTendril / particlesPerTendril;

  // Spiral outward with looser winding (more spread between turns)
  const spiralTurns = 0.8; // Reduced from 1.5 for more spread between spiral arms
  const angle = baseAngle + t * Math.PI * 2 * spiralTurns;

  // Distance grows smoothly - starts slow, accelerates, then eases
  const easeOutQuart = 1 - Math.pow(1 - t, 4);
  const radius = easeOutQuart * 100 * SCALE;

  // Vertical wave - reduced frequency for more spread between waves
  const verticalWave = Math.sin(t * Math.PI * 1.5 + tendrilIndex * 0.5) * 35 * SCALE * t; // Fewer waves, more spread

  // Slight thickness variation along tendril
  const thickness = (1 - t * 0.7) * 5 * SCALE;
  const thicknessAngle = (indexInTendril * 2.399) % (Math.PI * 2); // Golden angle for distribution
  const thicknessOffset = new THREE.Vector3(
    Math.cos(thicknessAngle) * thickness,
    Math.sin(thicknessAngle) * thickness * 0.5,
    0
  );

  // Main position
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius * 0.6; // Slightly flattened
  const z = verticalWave + (tendrilIndex % 2 === 0 ? 1 : -1) * t * 15 * SCALE;

  const pos = new THREE.Vector3(
    x + thicknessOffset.x,
    y + thicknessOffset.y,
    z + thicknessOffset.z
  );

  // Normal: Outwards from the tendril spine
  const normal = thicknessOffset.clone().normalize();

  return { pos, normal };
};

/** Query Burst - Search radiating outward like ripples */
const generateQueryBurst: ShapeGenerator = (index, total) => {
  const numRings = 8;
  const ringIndex = Math.floor((index / total) * numRings);
  const indexInRing = index % Math.floor(total / numRings);
  const particlesPerRing = Math.floor(total / numRings);

  // Ring radius increases with index
  const ringRadius = (ringIndex + 1) * 15 * SCALE;
  const ringHeight = (ringIndex - numRings / 2) * 8 * SCALE;

  // Distribute particles around ring
  const angle = (indexInRing / particlesPerRing) * Math.PI * 2;
  const angleOffset = ringIndex * 0.2; // Offset each ring slightly

  // Add some thickness to rings
  const thickness = 5 * SCALE;
  const radialOffset = (Math.random() - 0.5) * thickness;

  const pos = new THREE.Vector3(
    Math.cos(angle + angleOffset) * (ringRadius + radialOffset),
    ringHeight + (Math.random() - 0.5) * thickness,
    Math.sin(angle + angleOffset) * (ringRadius + radialOffset)
  );

  // Normal: Outwards from center
  const normal = new THREE.Vector3(pos.x, 0, pos.z).normalize();

  return { pos, normal };
};

/** Wisdom Tree - Ultra-realistic fractal tree inspired by the EleutherIA logo */
const generateWisdomTree: ShapeGenerator = (index, total) => {
  // Golden ratio constants for natural growth patterns
  const PHI = 1.618033988749895;
  const GOLDEN_ANGLE = 2.399963229728653; // radians (~137.5°)

  const rootsRatio = 0.12;
  const trunkRatio = 0.06;
  const primaryBranchRatio = 0.15;
  const secondaryBranchRatio = 0.20;
  const tertiaryBranchRatio = 0.17;
  const canopyRatio = 0.30;

  const normalizedIndex = index / total;
  const treeHeight = 175 * SCALE;
  const trunkHeight = treeHeight * 0.32;
  const trunkBase = -treeHeight * 0.25;
  const rootDepth = 70 * SCALE;
  const canopySpread = 110 * SCALE;

  const noise = (seed: number) => {
    const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };

  const pos = new THREE.Vector3();
  const normal = new THREE.Vector3(0, 1, 0);

  // ========== ROOTS ==========
  if (normalizedIndex < rootsRatio) {
    const rootIndex = index;
    const rootTotal = Math.floor(total * rootsRatio);
    const numMainRoots = 6;
    const numSubRoots = 3;
    const mainRootIndex = rootIndex % numMainRoots;
    const subRootIndex = Math.floor(rootIndex / numMainRoots) % numSubRoots;
    const particleInRoot = Math.floor(rootIndex / (numMainRoots * numSubRoots));
    const particlesPerRoot = Math.floor(rootTotal / (numMainRoots * numSubRoots));
    const t = particleInRoot / Math.max(1, particlesPerRoot);

    const mainAngle = (mainRootIndex / numMainRoots) * Math.PI * 2 + noise(mainRootIndex) * 0.3;
    const subAngleOffset = (subRootIndex - 1) * 0.4 + noise(mainRootIndex + subRootIndex) * 0.2;
    const angle = mainAngle + subAngleOffset * t;

    const divePhase = Math.min(t * 2, 1);
    const spreadPhase = Math.max(0, (t - 0.3) * 1.4);
    const depth = divePhase * rootDepth * (0.7 + subRootIndex * 0.15);
    const spread = spreadPhase * spreadPhase * 50 * SCALE * (1 + noise(rootIndex) * 0.3);

    const waviness = Math.sin(t * Math.PI * 4 + mainRootIndex * PHI) * 6 * SCALE * t;
    const waviness2 = Math.cos(t * Math.PI * 3 + subRootIndex) * 4 * SCALE * t;
    const thickness = (1 - t * 0.85) * 3 * SCALE;
    const thicknessAngle = particleInRoot * GOLDEN_ANGLE;

    pos.set(
      Math.cos(angle) * spread + Math.cos(thicknessAngle) * thickness + waviness,
      trunkBase - depth + waviness2 * 0.3,
      Math.sin(angle) * spread + Math.sin(thicknessAngle) * thickness + waviness2
    );
    // Normal points outwards from root cylinder
    normal.set(Math.cos(thicknessAngle), 0, Math.sin(thicknessAngle)).normalize();
  }

  // ========== TRUNK ==========
  else if (normalizedIndex < rootsRatio + trunkRatio) {
    const trunkIndex = index - Math.floor(total * rootsRatio);
    const trunkTotal = Math.floor(total * trunkRatio);
    const t = trunkIndex / trunkTotal;
    const height = trunkBase + t * trunkHeight;
    const baseRadius = 6 * SCALE;
    const topRadius = 3 * SCALE;
    const trunkRadius = baseRadius + (topRadius - baseRadius) * t;

    const spiralAngle = t * Math.PI * 0.3 + trunkIndex * 0.15;
    const barkRipple = Math.sin(t * Math.PI * 8 + trunkIndex * 0.5) * 0.4 * SCALE;
    const barkBulge = Math.sin(t * Math.PI * 2) * 0.8 * SCALE;
    const lean = Math.sin(t * Math.PI) * 2 * SCALE;

    pos.set(
      Math.cos(spiralAngle) * (trunkRadius + barkRipple + barkBulge) + lean,
      height,
      Math.sin(spiralAngle) * (trunkRadius + barkRipple)
    );
    // Normal points outwards from trunk
    normal.set(Math.cos(spiralAngle), 0, Math.sin(spiralAngle)).normalize();
  }

  // ========== PRIMARY BRANCHES ==========
  else if (normalizedIndex < rootsRatio + trunkRatio + primaryBranchRatio) {
    const branchIndex = index - Math.floor(total * (rootsRatio + trunkRatio));
    const branchTotal = Math.floor(total * primaryBranchRatio);
    const numPrimaryBranches = 8;
    const primaryIndex = branchIndex % numPrimaryBranches;
    const indexInBranch = Math.floor(branchIndex / numPrimaryBranches);
    const particlesPerBranch = Math.floor(branchTotal / numPrimaryBranches);
    const t = indexInBranch / Math.max(1, particlesPerBranch);

    const branchHeight = trunkBase + trunkHeight * (0.45 + (primaryIndex % 4) * 0.12);
    const baseAngle = primaryIndex * GOLDEN_ANGLE + noise(primaryIndex) * 0.4;
    const reachAngle = 0.3 + noise(primaryIndex + 100) * 0.25;
    const branchLength = (55 + noise(primaryIndex) * 20) * SCALE;

    const curveUp = t * t * 0.6;
    const horizontalReach = t * branchLength * Math.cos(reachAngle + curveUp * 0.3);
    const verticalRise = t * branchLength * Math.sin(reachAngle) + t * t * 25 * SCALE;
    const sway = Math.sin(t * Math.PI * 2 + primaryIndex) * 8 * SCALE * t;
    const thickness = (1 - t * 0.7) * 4 * SCALE;
    const thicknessAngle = indexInBranch * GOLDEN_ANGLE * 0.5;

    pos.set(
      Math.cos(baseAngle) * horizontalReach + Math.cos(thicknessAngle) * thickness + sway,
      branchHeight + verticalRise,
      Math.sin(baseAngle) * horizontalReach + Math.sin(thicknessAngle) * thickness
    );
    normal.set(Math.cos(thicknessAngle), 0, Math.sin(thicknessAngle)).normalize();
  }

  // ========== SECONDARY BRANCHES ==========
  else if (normalizedIndex < rootsRatio + trunkRatio + primaryBranchRatio + secondaryBranchRatio) {
    const branchIndex = index - Math.floor(total * (rootsRatio + trunkRatio + primaryBranchRatio));
    const branchTotal = Math.floor(total * secondaryBranchRatio);
    const numPrimary = 8;
    const numSecondaryPer = 4;
    const primaryIndex = branchIndex % numPrimary;
    const secondaryIndex = Math.floor(branchIndex / numPrimary) % numSecondaryPer;
    const indexInBranch = Math.floor(branchIndex / (numPrimary * numSecondaryPer));
    const particlesPerBranch = Math.floor(branchTotal / (numPrimary * numSecondaryPer));
    const t = indexInBranch / Math.max(1, particlesPerBranch);

    const primaryT = 0.4 + secondaryIndex * 0.15;
    const primaryAngle = primaryIndex * GOLDEN_ANGLE + noise(primaryIndex) * 0.4;
    const primaryLength = (55 + noise(primaryIndex) * 20) * SCALE;
    const primaryHeight = trunkBase + trunkHeight * (0.45 + (primaryIndex % 4) * 0.12);

    const originX = Math.cos(primaryAngle) * primaryT * primaryLength * 0.85;
    const originZ = Math.sin(primaryAngle) * primaryT * primaryLength * 0.85;
    const originY = primaryHeight + primaryT * primaryT * 35 * SCALE;

    const divergeAngle = (secondaryIndex - 1.5) * 0.7 + noise(primaryIndex + secondaryIndex * 10) * 0.3;
    const secondaryAngle = primaryAngle + divergeAngle;
    const secondaryLength = (25 + noise(branchIndex) * 15) * SCALE;

    const reach = t * secondaryLength;
    const rise = t * t * 18 * SCALE;
    const flutter = Math.sin(t * Math.PI * 3 + branchIndex * 0.7) * 4 * SCALE * t;
    const thickness = (1 - t * 0.8) * 2.5 * SCALE;
    const thicknessAngle = indexInBranch * GOLDEN_ANGLE;

    pos.set(
      originX + Math.cos(secondaryAngle) * reach + Math.cos(thicknessAngle) * thickness + flutter,
      originY + rise,
      originZ + Math.sin(secondaryAngle) * reach + Math.sin(thicknessAngle) * thickness
    );
    normal.set(Math.cos(thicknessAngle), 0, Math.sin(thicknessAngle)).normalize();
  }

  // ========== TERTIARY BRANCHES ==========
  else if (normalizedIndex < 1.0 - canopyRatio) {
    const twigIndex = index - Math.floor(total * (rootsRatio + trunkRatio + primaryBranchRatio + secondaryBranchRatio));
    const twigTotal = Math.floor(total * tertiaryBranchRatio);
    const numTwigGroups = 32;
    const groupIndex = twigIndex % numTwigGroups;
    const indexInGroup = Math.floor(twigIndex / numTwigGroups);
    const particlesPerGroup = Math.floor(twigTotal / numTwigGroups);
    const t = indexInGroup / Math.max(1, particlesPerGroup);

    const groupAngle = groupIndex * GOLDEN_ANGLE;
    const groupElevation = 0.3 + noise(groupIndex) * 0.5;
    const groupRadius = (30 + noise(groupIndex + 50) * 25) * SCALE;

    const originX = Math.cos(groupAngle) * groupRadius * (0.5 + groupElevation * 0.5);
    const originZ = Math.sin(groupAngle) * groupRadius * (0.5 + groupElevation * 0.5);
    const originY = trunkBase + trunkHeight * 0.7 + groupElevation * 40 * SCALE;

    const twigAngle = groupAngle + (noise(twigIndex) - 0.5) * 1.2;
    const twigLength = (12 + noise(twigIndex + 200) * 10) * SCALE;
    const twigRise = (5 + noise(twigIndex + 300) * 8) * SCALE;
    const tremor = Math.sin(t * Math.PI * 5 + twigIndex) * 2 * SCALE * t;
    const thickness = (1 - t * 0.9) * 1.2 * SCALE;
    const thicknessAngle = indexInGroup * GOLDEN_ANGLE;

    pos.set(
      originX + Math.cos(twigAngle) * t * twigLength + Math.cos(thicknessAngle) * thickness + tremor,
      originY + t * twigRise,
      originZ + Math.sin(twigAngle) * t * twigLength + Math.sin(thicknessAngle) * thickness
    );
    normal.set(Math.cos(thicknessAngle), 0, Math.sin(thicknessAngle)).normalize();
  }

  // ========== CANOPY ==========
  else {
    const canopyIndex = index - Math.floor(total * (1 - canopyRatio));
    const canopyTotal = Math.floor(total * canopyRatio);
    const canopyCenterY = trunkBase + trunkHeight + 30 * SCALE;

    const clusterCount = 24;
    const clusterIndex = canopyIndex % clusterCount;
    const indexInCluster = Math.floor(canopyIndex / clusterCount);
    const particlesPerCluster = Math.floor(canopyTotal / clusterCount);

    const clusterAngle = clusterIndex * GOLDEN_ANGLE;
    const clusterElevation = noise(clusterIndex) * 0.8 + 0.1;
    const clusterRadiusBase = canopySpread * (0.4 + clusterElevation * 0.6);

    const clusterX = Math.cos(clusterAngle) * clusterRadiusBase * (0.3 + noise(clusterIndex + 500) * 0.7);
    const clusterZ = Math.sin(clusterAngle) * clusterRadiusBase * (0.3 + noise(clusterIndex + 600) * 0.7);
    const clusterY = canopyCenterY + (clusterElevation - 0.5) * 50 * SCALE;

    const clumpRadius = (8 + noise(clusterIndex + 100) * 6) * SCALE;
    const localT = indexInCluster / Math.max(1, particlesPerCluster);
    const phi = Math.acos(1 - 2 * (indexInCluster + 0.5) / Math.max(1, particlesPerCluster));
    const theta = Math.PI * (1 + Math.sqrt(5)) * indexInCluster;
    const leafRadius = clumpRadius * Math.pow(localT, 0.4);

    const float = Math.sin(canopyIndex * 0.08 + clusterIndex) * 1.5 * SCALE;
    const drift = Math.cos(canopyIndex * 0.05) * 1.5 * SCALE;

    const localX = Math.sin(phi) * Math.cos(theta) * leafRadius;
    const localY = Math.cos(phi) * leafRadius * 0.6;
    const localZ = Math.sin(phi) * Math.sin(theta) * leafRadius;

    pos.set(
      clusterX + localX + drift,
      clusterY + localY + float,
      clusterZ + localZ
    );
    // Leaf normal: simplified to point out from clump center
    normal.set(localX, localY, localZ).normalize();
  }

  return { pos, normal };
};

/** Owl of Athena - Uses 3Dme particle cloud data for high-fidelity rendering */
const generateOwlOfAthena: ShapeGenerator = (index, total) => {
  // If 3Dme data is loaded, use it
  if (owl3DmeCache) {
    const data = owl3DmeCache;
    // Sample from the 3Dme data (which has many more particles than we need)
    // Use consistent sampling so the shape is stable across frames
    const sampleIndex = Math.floor((index / total) * data.count);
    const i = sampleIndex * 3;

    // Get position from 3Dme data (scaled up for better visibility)
    const x = data.positions[i] * SCALE * 1.8;
    const y = data.positions[i + 1] * SCALE * 1.8;
    const z = data.positions[i + 2] * SCALE * 1.8;

    const pos = new THREE.Vector3(x, y, z);

    // Calculate normal as pointing outward from center of mass
    const normal = pos.clone().normalize();

    return { pos, normal };
  }

  // Fallback: simple sphere while loading
  const phi = Math.acos(1 - 2 * (index + 0.5) / total);
  const theta = Math.PI * (1 + Math.sqrt(5)) * index;
  const r = 40 * SCALE;

  const pos = new THREE.Vector3(
    r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );

  return { pos, normal: pos.clone().normalize() };
};

/** Ancient Philosopher - Uses depth-estimated particle cloud from 2D portrait */
const generatePhilosopher: ShapeGenerator = (index, total) => {
  // If philosopher data is loaded, use it
  if (philosopherCache) {
    const data = philosopherCache;
    // Sample from the depth-estimated data
    const sampleIndex = Math.floor((index / total) * data.count);
    const i = sampleIndex * 3;

    // Get position from philosopher data (scaled up for visibility)
    // The depth data is wider (portrait), so we use a larger scale
    const x = data.positions[i] * SCALE * 6.0;
    const y = data.positions[i + 1] * SCALE * 6.0;
    const z = data.positions[i + 2] * SCALE * 6.0;

    const pos = new THREE.Vector3(x, y, z);

    // Calculate normal as pointing outward from center
    const normal = pos.clone().normalize();

    return { pos, normal };
  }

  // Fallback: simple sphere while loading
  const phi = Math.acos(1 - 2 * (index + 0.5) / total);
  const theta = Math.PI * (1 + Math.sqrt(5)) * index;
  const r = 40 * SCALE;

  const pos = new THREE.Vector3(
    r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );

  return { pos, normal: pos.clone().normalize() };
};

/** Pyramid of Knowledge - Stunning yet simple pyramid */
const generatePyramidOfKnowledge: ShapeGenerator = (index, total) => {
  // Pyramid dimensions - large and majestic (increased size)
  const baseSize = 120 * SCALE;
  const height = 140 * SCALE;
  const halfBase = baseSize / 2;

  // Allocate particles: 100% to the 4 faces (no base needed for clean look)
  const particlesPerFace = Math.floor(total / 4);
  const face = Math.floor(index / particlesPerFace) % 4;
  const localIndex = index % particlesPerFace;

  // Grid dimensions for each triangular face
  const rows = 40;
  const row = Math.floor(localIndex / rows) % rows;
  const col = localIndex % rows;

  // Height position (0 = base, 1 = apex)
  const v = row / (rows - 1);

  // Width at this height (narrows toward apex)
  const widthAtHeight = 1 - v;

  // Position along the width (-0.5 to 0.5, scaled by width)
  const u = widthAtHeight > 0 ? ((col / (rows - 1)) - 0.5) * widthAtHeight : 0;

  // Calculate 3D position based on face - centered vertically
  const y = v * height - height / 2;

  // Add VOLUME/THICKNESS to avoid planar saturation (Whiteout fix)
  // Jitter the particles slightly normal to the surface
  const wallThickness = 6 * SCALE;
  const jitter = (Math.random() - 0.5) * wallThickness;

  const pos = new THREE.Vector3();
  const normal = new THREE.Vector3();

  // Slope calculation for normals
  // H = 140, Base = 60. Slope = atan(140/60)
  const ny = 60/140; // Approx
  const nz = 1.0;

  // Each face points in a different direction
  const offset = halfBase * (1 - v); // Distance from center at this height

  switch (face) {
    case 0: // Front face (-Z)
      pos.set(u * baseSize + (Math.random() - 0.5) * wallThickness, y, -offset + jitter);
      normal.set(0, ny, -nz).normalize();
      break;
    case 1: // Right face (+X)
      pos.set(offset + jitter, y, u * baseSize + (Math.random() - 0.5) * wallThickness);
      normal.set(nz, ny, 0).normalize();
      break;
    case 2: // Back face (+Z)
      pos.set(-u * baseSize + (Math.random() - 0.5) * wallThickness, y, offset + jitter);
      normal.set(0, ny, nz).normalize();
      break;
    case 3: // Left face (-X)
      pos.set(-offset + jitter, y, -u * baseSize + (Math.random() - 0.5) * wallThickness);
      normal.set(-nz, ny, 0).normalize();
      break;
  }

  // Add a little vertical jitter too for organic feel
  pos.y += (Math.random() - 0.5) * 2;

  return { pos, normal };
};

/** Clean Armillary Sphere - Elegant ancient astronomical instrument */
const generateArmillarySphere: ShapeGenerator = (index, total) => {
  const GOLDEN_ANGLE = 2.399963229728653;

  // Clean, minimal structure - only essential elements
  const outerFrameRatio = 0.22;      // 22% - main outer meridian ring (vertical frame)
  const eclipticRatio = 0.22;        // 22% - tilted ecliptic ring (sun's path)
  const equatorRatio = 0.20;         // 20% - horizontal equator ring
  const centralEarthRatio = 0.20;    // 20% - smooth Earth sphere at center
  const polarAxisRatio = 0.16;       // 16% - clean polar axis

  const normalizedIndex = index / total;

  const pos = new THREE.Vector3();
  let normal = new THREE.Vector3();

  // Clean ring generator - no ornaments, just smooth rings
  const generateCleanRing = (
    localIndex: number,
    localTotal: number,
    radius: number,
    tiltX: number,
    tiltY: number,
    thickness: number
  ): { pos: THREE.Vector3, normal: THREE.Vector3 } => {
    const t = localIndex / localTotal;
    const angle = t * Math.PI * 2;

    // Ring position
    let x = Math.cos(angle) * radius;
    let y = 0;
    let z = Math.sin(angle) * radius;

    // Apply X rotation (tilt)
    if (tiltX !== 0) {
      const cosX = Math.cos(tiltX), sinX = Math.sin(tiltX);
      const y1 = y * cosX - z * sinX;
      const z1 = y * sinX + z * cosX;
      y = y1; z = z1;
    }

    // Apply Y rotation
    if (tiltY !== 0) {
      const cosY = Math.cos(tiltY), sinY = Math.sin(tiltY);
      const x1 = x * cosY + z * sinY;
      const z1 = -x * sinY + z * cosY;
      x = x1; z = z1;
    }

    // Clean circular thickness (tube cross-section)
    const thicknessAngle = localIndex * GOLDEN_ANGLE;
    const ringNormalX = Math.cos(angle);
    const ringNormalZ = Math.sin(angle);

    // Perpendicular to ring direction for clean tube shape
    x += Math.cos(thicknessAngle) * ringNormalX * thickness;
    y += Math.sin(thicknessAngle) * thickness;
    z += Math.cos(thicknessAngle) * ringNormalZ * thickness;

    const p = new THREE.Vector3(x, y, z);
    return { pos: p, normal: p.clone().normalize() };
  };

  // ========== OUTER FRAME - Main vertical meridian ring ==========
  if (normalizedIndex < outerFrameRatio) {
    const ringIndex = index;
    const ringTotal = Math.floor(total * outerFrameRatio);
    // Vertical great circle - the main frame of the armillary
    return generateCleanRing(ringIndex, ringTotal, 60 * SCALE, Math.PI / 2, 0, 3.5 * SCALE);
  }

  // ========== ECLIPTIC - Tilted ring (23.5° like Earth's axial tilt) ==========
  if (normalizedIndex < outerFrameRatio + eclipticRatio) {
    const ringIndex = index - Math.floor(total * outerFrameRatio);
    const ringTotal = Math.floor(total * eclipticRatio);
    // Tilted at 23.5° (0.41 radians) - the sun's apparent path
    return generateCleanRing(ringIndex, ringTotal, 52 * SCALE, 0.41, 0, 3 * SCALE);
  }

  // ========== EQUATOR - Clean horizontal ring ==========
  if (normalizedIndex < outerFrameRatio + eclipticRatio + equatorRatio) {
    const ringIndex = index - Math.floor(total * (outerFrameRatio + eclipticRatio));
    const ringTotal = Math.floor(total * equatorRatio);
    // Perfectly horizontal - celestial equator
    return generateCleanRing(ringIndex, ringTotal, 48 * SCALE, 0, 0, 2.5 * SCALE);
  }

  // ========== CENTRAL EARTH - Smooth sphere ==========
  if (normalizedIndex < outerFrameRatio + eclipticRatio + equatorRatio + centralEarthRatio) {
    const sphereIndex = index - Math.floor(total * (outerFrameRatio + eclipticRatio + equatorRatio));
    const sphereTotal = Math.floor(total * centralEarthRatio);

    // Fibonacci sphere distribution for even coverage
    const phi = Math.acos(1 - 2 * (sphereIndex + 0.5) / sphereTotal);
    const theta = sphereIndex * GOLDEN_ANGLE;
    const earthRadius = 18 * SCALE;

    pos.set(
      Math.sin(phi) * Math.cos(theta) * earthRadius,
      Math.cos(phi) * earthRadius,
      Math.sin(phi) * Math.sin(theta) * earthRadius
    );
    normal = pos.clone().normalize();
    return { pos, normal };
  }

  // ========== POLAR AXIS - Clean straight line through poles ==========
  const axisIndex = index - Math.floor(total * (outerFrameRatio + eclipticRatio + equatorRatio + centralEarthRatio));
  const axisTotal = Math.floor(total * polarAxisRatio);

  const t = axisIndex / axisTotal;
  const axisLength = 72 * SCALE;
  const height = (t - 0.5) * 2 * axisLength;

  // Uniform thickness along axis
  const thickness = 2.5 * SCALE;
  const thicknessAngle = axisIndex * GOLDEN_ANGLE;

  pos.set(
    Math.cos(thicknessAngle) * thickness,
    height,
    Math.sin(thicknessAngle) * thickness
  );
  // Normal points out from axis cylinder
  normal.set(Math.cos(thicknessAngle), 0, Math.sin(thicknessAngle)).normalize();

  return { pos, normal };
};

const shapes: ShapeGenerator[] = [
  generateWisdomTree,           // First - the stunning tree of knowledge
  generateOwlOfAthena,          // Second - 3Dme owl of Athena (powered by 3Dme)
  generatePhilosopher,          // Third - ancient philosopher portrait (depth-estimated)
  generateArmillarySphere,      // Fourth - ancient cosmic model
  generateKnowledgeGraph,       // Fifth - clustered concepts
  generateSemanticPaths,        // Sixth - search expansion
  generateReasoningChains,      // Seventh - inference tendrils
  generateQueryBurst,           // Eighth - rippling search
  generatePyramidOfKnowledge,   // Ninth - ancient repository of wisdom
  generateAttractorOfFate,      // Tenth - Chaos/Fate attractor
];

// ============================================================================
// COMPONENT
// ============================================================================

interface MorphingParticlesProps extends MorphingParticlesConfig {
  className?: string;
  style?: React.CSSProperties;
}

export function MorphingParticles(props: MorphingParticlesProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number | null>(null);

  // Memoize config to prevent re-creating the object on every render,
  // which would cause the heavy THREE.js scene to reinitialize unnecessarily.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const config = useMemo(() => ({ ...defaultConfig, ...props }), [
    props.particleCount,
    props.morphDuration,
    props.rotationSpeed,
    props.particleSize,
    props.lineOpacity,
    props.connectionDistance,
    props.colorScheme,
    props.selectedShape,
    props.enableBloom,
    props.bloomIntensity,
    props.enableTrails,
    props.trailLength,
    props.enableDepthOfField,
    props.enableZoom,
    props.enableHover,
    props.enableKeyboard,
    props.enableBreathing,
    props.breathingSpeed,
    props.enableStaggeredMorph,
    props.staggerDirection,
  ]);

  const initScene = useCallback(() => {
    console.log('[MorphingParticles] initScene called');
    if (!containerRef.current) {
      console.log('[MorphingParticles] No container ref!');
      return;
    }

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;
    console.log('[MorphingParticles] Container size:', width, 'x', height);

    // Guard against zero-size containers (can happen with clip-path animations)
    if (width === 0 || height === 0) {
      console.log('[MorphingParticles] Zero size, retrying in 100ms...');
      // Retry after a short delay
      setTimeout(() => initScene(), 100);
      return;
    }

    // Scene with solid black background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a); // Near-black to match bg-zinc-950

    // Camera - closer for compact visualization
    const camera = new THREE.PerspectiveCamera(60, width / height, 1, 1000);
    camera.position.z = 200;

    // Renderer - alpha:false to prevent gray overlay artifacts with EffectComposer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
      alpha: false,  // Disabled - was causing gray overlay with post-processing
    });
    renderer.setSize(width, height);
    // ADAPTIVE: Limit pixel ratio based on device capability for consistent performance
    const effectivePixelRatio = Math.min(window.devicePixelRatio, deviceProfile.pixelRatioLimit);
    renderer.setPixelRatio(effectivePixelRatio);
    console.log('[MorphingParticles] Using pixel ratio:', effectivePixelRatio);
    // SOLID black background - using alpha:0 causes gray overlay artifacts with EffectComposer
    renderer.setClearColor(0x000000, 1);
    container.appendChild(renderer.domElement);
    console.log('[MorphingParticles] Renderer created and added to DOM');

    // Mouse drag rotation with momentum (left-click)
    let isDragging = false;
    let previousMouseX = 0;
    let previousMouseY = 0;
    let userRotationY = 0;
    let userRotationX = 0;
    let velocityY = 0;
    let velocityX = 0;
    let autoRotationPaused = false;
    let autoRotationResumeTimeout: ReturnType<typeof setTimeout> | null = null;
    const friction = 0.95; // How quickly momentum slows down
    const sensitivity = 0.005;

    // Right-click panning
    let isPanning = false;
    let panX = 0;
    let panY = 0;
    const panSensitivity = 0.5;

    const onMouseDown = (e: MouseEvent) => {
      previousMouseX = e.clientX;
      previousMouseY = e.clientY;

      if (e.button === 2) {
        // Right-click: panning
        isPanning = true;
        renderer.domElement.style.cursor = 'move';
      } else if (e.button === 0) {
        // Left-click: rotation
        isDragging = true;
        velocityY = 0;
        velocityX = 0;
        autoRotationPaused = true;
        if (autoRotationResumeTimeout) clearTimeout(autoRotationResumeTimeout);
        renderer.domElement.style.cursor = 'grabbing';
      }
    };

    const onMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - previousMouseX;
      const deltaY = e.clientY - previousMouseY;

      if (isPanning) {
        // Right-click drag: pan the view
        panX += deltaX * panSensitivity;
        panY -= deltaY * panSensitivity; // Invert Y for natural feel
        previousMouseX = e.clientX;
        previousMouseY = e.clientY;
      } else if (isDragging) {
        // Left-click drag: rotate
        velocityY = deltaX * sensitivity;
        velocityX = deltaY * sensitivity;

        userRotationY += velocityY;
        userRotationX += velocityX;
        userRotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, userRotationX));

        previousMouseX = e.clientX;
        previousMouseY = e.clientY;
      }
    };

    const onMouseUp = () => {
      if (isPanning) {
        isPanning = false;
        renderer.domElement.style.cursor = 'grab';
      }
      if (isDragging) {
        isDragging = false;
        renderer.domElement.style.cursor = 'grab';
        // Don't resume auto-rotation immediately - let momentum play out
        autoRotationResumeTimeout = setTimeout(() => {
          autoRotationPaused = false;
        }, 3000);
      }
    };

    const onMouseLeave = () => {
      if (isDragging || isPanning) {
        isDragging = false;
        isPanning = false;
        renderer.domElement.style.cursor = 'grab';
        autoRotationResumeTimeout = setTimeout(() => {
          autoRotationPaused = false;
        }, 3000);
      }
    };

    // Prevent context menu on right-click
    const onContextMenu = (e: MouseEvent) => {
      e.preventDefault();
    };

    renderer.domElement.style.cursor = 'grab';
    renderer.domElement.addEventListener('mousedown', onMouseDown);
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mouseup', onMouseUp);
    renderer.domElement.addEventListener('mouseleave', onMouseLeave);
    renderer.domElement.addEventListener('contextmenu', onContextMenu);

    // ── TOUCH EVENTS (mobile interaction) ──────────────────────────────────
    const onTouchStart = (e: TouchEvent) => {
      e.preventDefault();
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        previousMouseX = touch.clientX;
        previousMouseY = touch.clientY;
        isDragging = true;
        velocityY = 0;
        velocityX = 0;
        autoRotationPaused = true;
        if (autoRotationResumeTimeout) clearTimeout(autoRotationResumeTimeout);
      }
    };

    const onTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        const deltaX = touch.clientX - previousMouseX;
        const deltaY = touch.clientY - previousMouseY;

        velocityY = deltaX * sensitivity;
        velocityX = deltaY * sensitivity;

        userRotationY += velocityY;
        userRotationX += velocityX;
        userRotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, userRotationX));

        previousMouseX = touch.clientX;
        previousMouseY = touch.clientY;

        // Also drive the particle hover/swirl effect with the touch position
        const rect = renderer.domElement.getBoundingClientRect();
        targetMouseX = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
        targetMouseY = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
        isMouseOverCanvas = true;
        hoverInfluence = 1;
      }
    };

    const onTouchEnd = () => {
      if (isDragging) {
        isDragging = false;
        autoRotationResumeTimeout = setTimeout(() => {
          autoRotationPaused = false;
        }, 3000);
      }
      isMouseOverCanvas = false;
      hoverInfluence = 0;
    };

    renderer.domElement.addEventListener('touchstart', onTouchStart, { passive: false });
    renderer.domElement.addEventListener('touchmove', onTouchMove, { passive: false });
    renderer.domElement.addEventListener('touchend', onTouchEnd);

    // ========================================================================
    // POST-PROCESSING
    // ========================================================================

    // Create proper render target for EffectComposer to avoid gray overlay artifacts
    const renderTarget = new THREE.WebGLRenderTarget(width, height, {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      format: THREE.RGBAFormat,
      colorSpace: THREE.SRGBColorSpace,
    });
    const composer = new EffectComposer(renderer, renderTarget);
    const renderPass = new RenderPass(scene, camera);
    renderPass.clear = true;
    renderPass.clearDepth = true;
    composer.addPass(renderPass);

    // Bloom effect - OPTIMIZATION: Reduced intensity and higher threshold for performance
    let bloomPass: UnrealBloomPass | null = null;
    if (config.enableBloom) {
      bloomPass = new UnrealBloomPass(
        new THREE.Vector2(width, height),
        config.bloomIntensity * 0.8,  // Slightly reduced strength
        0.3,                          // Smaller radius = faster
        0.9                           // Higher threshold = fewer pixels processed
      );
      composer.addPass(bloomPass);
    }

    // Depth of Field effect
    let bokehPass: BokehPass | null = null;
    if (config.enableDepthOfField) {
      bokehPass = new BokehPass(scene, camera, {
        focus: 200,
        aperture: 0.00025,
        maxblur: 0.01,
      });
      composer.addPass(bokehPass);
    }

    // ========================================================================
    // BACKGROUND STAR FIELD
    // ========================================================================

    const starCount = 2000;
    const starPositions = new Float32Array(starCount * 3);
    const starColors = new Float32Array(starCount * 3);
    const starSizes = new Float32Array(starCount);
    // OPTIMIZATION: Store twinkle params as attributes for GPU-based twinkling
    const starTwinkleOffsets = new Float32Array(starCount);
    const starTwinkleSpeeds = new Float32Array(starCount);

    // Star color palette (realistic stellar colors)
    const starColorPalette = [
      new THREE.Color(0xffffff), // White
      new THREE.Color(0xe8f4ff), // Cool white
      new THREE.Color(0xaaddff), // Light blue (A-type)
      new THREE.Color(0x88bbff), // Blue (B-type)
      new THREE.Color(0xffd4a3), // Warm yellow
      new THREE.Color(0xffaa77), // Orange (K-type)
    ];

    for (let i = 0; i < starCount; i++) {
      // Spread stars across a wide area behind the morphing shapes
      starPositions[i * 3] = (Math.random() - 0.5) * 1500;
      starPositions[i * 3 + 1] = (Math.random() - 0.5) * 1000;
      starPositions[i * 3 + 2] = -200 - Math.random() * 600; // Behind the shapes

      // Random color from palette
      const color = starColorPalette[Math.floor(Math.random() * starColorPalette.length)];
      starColors[i * 3] = color.r;
      starColors[i * 3 + 1] = color.g;
      starColors[i * 3 + 2] = color.b;

      // Size with power distribution (more small stars)
      const sizeT = Math.pow(Math.random(), 2);
      starSizes[i] = 0.5 + sizeT * 3;

      // Twinkle parameters - now stored as attributes for GPU
      starTwinkleOffsets[i] = Math.random() * Math.PI * 2;
      starTwinkleSpeeds[i] = 0.5 + Math.random() * 2;
    }

    const starGeometry = new THREE.BufferGeometry();
    starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));
    starGeometry.setAttribute('size', new THREE.BufferAttribute(starSizes, 1));
    // OPTIMIZATION: Pass twinkle params to GPU
    starGeometry.setAttribute('twinkleOffset', new THREE.BufferAttribute(starTwinkleOffsets, 1));
    starGeometry.setAttribute('twinkleSpeed', new THREE.BufferAttribute(starTwinkleSpeeds, 1));

    // OPTIMIZATION: GPU-based twinkling - no CPU loop needed!
    const starMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: renderer.getPixelRatio() },
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        attribute float twinkleOffset;
        attribute float twinkleSpeed;
        varying vec3 vColor;
        varying float vSize;
        uniform float uTime;
        uniform float uPixelRatio;

        void main() {
          vColor = color;
          // OPTIMIZATION: Twinkling calculated on GPU
          float twinkle = sin(uTime * twinkleSpeed + twinkleOffset) * 0.5 + 0.5;
          float animatedSize = size * (0.6 + twinkle * 0.8);
          vSize = animatedSize;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = animatedSize * uPixelRatio * (300.0 / -mvPosition.z);
          gl_PointSize = max(1.0, gl_PointSize);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vSize;

        void main() {
          vec2 uv = gl_PointCoord * 2.0 - 1.0;
          float dist = length(uv);

          // Star shape with soft glow
          float core = smoothstep(0.8, 0.0, dist);
          float glow = smoothstep(1.0, 0.3, dist) * 0.5;

          // Cross-shaped diffraction spikes for larger stars
          float spikes = 0.0;
          if (vSize > 2.0) {
            float spike1 = smoothstep(0.15, 0.0, abs(uv.x)) * smoothstep(1.0, 0.0, abs(uv.y));
            float spike2 = smoothstep(0.15, 0.0, abs(uv.y)) * smoothstep(1.0, 0.0, abs(uv.x));
            spikes = (spike1 + spike2) * 0.3 * (vSize - 2.0) / 4.0;
          }

          float alpha = core + glow + spikes;
          if (alpha < 0.01) discard;

          gl_FragColor = vec4(vColor, alpha);
        }
      `,
      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    });

    const stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);

    // OPTIMIZATION: updateStars now just updates the uniform - GPU does the work
    const updateStars = (t: number) => {
      starMaterial.uniforms.uTime.value = t;
    };

    // ========================================================================
    // SHOOTING STARS
    // ========================================================================

    interface ShootingStar {
      line: THREE.Line;
      startPos: THREE.Vector3;
      direction: THREE.Vector3;
      speed: number;
      length: number;
      progress: number;
      active: boolean;
    }

    const shootingStars: ShootingStar[] = [];
    const maxShootingStars = 3;
    let shootingStarTimer = 0;
    const shootingStarInterval = 4000; // ms

    const createShootingStar = (): ShootingStar => {
      const trailLength = 30;
      const positions = new Float32Array(trailLength * 3);
      const alphas = new Float32Array(trailLength);

      for (let i = 0; i < trailLength; i++) {
        alphas[i] = 1 - i / trailLength;
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));

      const material = new THREE.ShaderMaterial({
        uniforms: {
          uOpacity: { value: 0 },
          uColor: { value: new THREE.Color(0xffffff) },
        },
        vertexShader: `
          attribute float alpha;
          varying float vAlpha;
          void main() {
            vAlpha = alpha;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform float uOpacity;
          uniform vec3 uColor;
          varying float vAlpha;
          void main() {
            gl_FragColor = vec4(uColor, vAlpha * uOpacity);
          }
        `,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });

      const line = new THREE.Line(geometry, material);
      line.visible = false;
      scene.add(line);

      return {
        line,
        startPos: new THREE.Vector3(),
        direction: new THREE.Vector3(),
        speed: 0,
        length: 80 + Math.random() * 120,
        progress: 0,
        active: false,
      };
    };

    // Pre-create shooting stars
    for (let i = 0; i < maxShootingStars; i++) {
      shootingStars.push(createShootingStar());
    }

    const launchShootingStar = () => {
      const inactive = shootingStars.find((s) => !s.active);
      if (!inactive) return;

      // Random start position at edge
      const side = Math.floor(Math.random() * 2);
      if (side === 0) {
        inactive.startPos.set(
          (Math.random() - 0.5) * 1200,
          300 + Math.random() * 200,
          -300 - Math.random() * 200
        );
      } else {
        inactive.startPos.set(
          500 + Math.random() * 200,
          (Math.random() - 0.5) * 600,
          -300 - Math.random() * 200
        );
      }

      // Direction: generally down-left
      inactive.direction.set(
        -0.5 - Math.random() * 0.5,
        -0.3 - Math.random() * 0.4,
        0.1
      ).normalize();

      inactive.speed = 15 + Math.random() * 10;
      inactive.length = 80 + Math.random() * 120;
      inactive.progress = 0;
      inactive.active = true;
      inactive.line.visible = true;

      // Random warm color
      const starColor = new THREE.Color().setHSL(
        0.1 + Math.random() * 0.1,
        0.3,
        0.9 + Math.random() * 0.1
      );
      (inactive.line.material as THREE.ShaderMaterial).uniforms.uColor.value = starColor;
    };

    const updateShootingStars = (deltaTime: number) => {
      shootingStarTimer += deltaTime * 1000;
      if (shootingStarTimer > shootingStarInterval) {
        launchShootingStar();
        shootingStarTimer = 0;
      }

      shootingStars.forEach((star) => {
        if (!star.active) return;

        star.progress += star.speed * deltaTime;
        const t = star.progress / star.length;

        if (t >= 1) {
          star.active = false;
          star.line.visible = false;
          return;
        }

        // Update trail positions
        const positions = star.line.geometry.attributes.position.array as Float32Array;
        const trailLength = positions.length / 3;

        for (let i = 0; i < trailLength; i++) {
          const trailT = i / trailLength;
          const pos = star.startPos
            .clone()
            .add(star.direction.clone().multiplyScalar(star.progress - trailT * 30));
          positions[i * 3] = pos.x;
          positions[i * 3 + 1] = pos.y;
          positions[i * 3 + 2] = pos.z;
        }

        star.line.geometry.attributes.position.needsUpdate = true;

        // Fade in/out
        let opacity = 1;
        if (t < 0.1) {
          opacity = t / 0.1;
        } else if (t > 0.8) {
          opacity = 1 - (t - 0.8) / 0.2;
        }
        (star.line.material as THREE.ShaderMaterial).uniforms.uOpacity.value = opacity;
      });
    };

    // ========================================================================
    // ZOOM CONTROLS
    // ========================================================================

    let zoomLevel = 200; // Initial camera Z
    const minZoom = 80;
    const maxZoom = 400;

    const onWheel = (e: WheelEvent) => {
      if (!config.enableZoom) return;
      e.preventDefault();
      const zoomSpeed = 0.1;
      zoomLevel += e.deltaY * zoomSpeed;
      zoomLevel = Math.max(minZoom, Math.min(maxZoom, zoomLevel));
      camera.position.z = zoomLevel;
    };

    if (config.enableZoom) {
      renderer.domElement.addEventListener('wheel', onWheel, { passive: false });
    }

    // ========================================================================
    // HOVER EFFECTS
    // ========================================================================

    let targetMouseX = 0;
    let targetMouseY = 0;
    let currentMouseX = 0;
    let currentMouseY = 0;
    let hoverInfluence = 0;

    let isMouseOverCanvas = false;

    const onHoverMove = (e: MouseEvent) => {
      if (!config.enableHover) return;
      const rect = renderer.domElement.getBoundingClientRect();
      targetMouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      targetMouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      isMouseOverCanvas = true;
      hoverInfluence = 1;
    };

    const onHoverLeave = () => {
      isMouseOverCanvas = false;
      hoverInfluence = 0;
    };

    if (config.enableHover) {
      renderer.domElement.addEventListener('mousemove', onHoverMove);
      renderer.domElement.addEventListener('mouseleave', onHoverLeave);
    }

    // ========================================================================
    // KEYBOARD SHORTCUTS
    // ========================================================================

    let isPaused = false;
    let keyRotationY = 0;
    let keyRotationX = 0;

    const onKeyDown = (e: KeyboardEvent) => {
      if (!config.enableKeyboard) return;
      switch (e.key) {
        case ' ':
          e.preventDefault();
          isPaused = !isPaused;
          break;
        case 'ArrowLeft':
          keyRotationY -= 0.1;
          break;
        case 'ArrowRight':
          keyRotationY += 0.1;
          break;
        case 'ArrowUp':
          keyRotationX -= 0.05;
          break;
        case 'ArrowDown':
          keyRotationX += 0.05;
          break;
        case 'r':
        case 'R':
          // Reset rotation
          userRotationY = 0;
          userRotationX = 0;
          keyRotationY = 0;
          keyRotationX = 0;
          zoomLevel = 200;
          camera.position.z = zoomLevel;
          break;
      }
    };

    if (config.enableKeyboard) {
      window.addEventListener('keydown', onKeyDown);
    }

    const colors = colorSchemes[config.colorScheme];

    // ========================================================================
    // PARTICLES
    // ========================================================================

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(config.particleCount * 3);
    const normals = new Float32Array(config.particleCount * 3); // Current Normals
    const targetPositions = new Float32Array(config.particleCount * 3);
    const targetNormals = new Float32Array(config.particleCount * 3); // Target Normals
    const startPositions = new Float32Array(config.particleCount * 3);
    const startNormals = new Float32Array(config.particleCount * 3); // Start Normals
    const particleColors = new Float32Array(config.particleCount * 3);
    const sizes = new Float32Array(config.particleCount);

    // Determine initial shape index
    const initialShapeIndex = config.selectedShape
      ? SHAPE_NAMES.indexOf(config.selectedShape)
      : 0;

    // ========================================================================
    // ENTRANCE ANIMATION - Particles emerge from the void
    // ========================================================================

    // Generate void positions - compressed singularity with slight chaos
    const voidPositions = new Float32Array(config.particleCount * 3);
    for (let i = 0; i < config.particleCount; i++) {
      const i3 = i * 3;
      // Golden ratio spiral for initial distribution in tiny space
      const phi = i * 2.399963229728653; // Golden angle
      const r = Math.sqrt(i / config.particleCount) * 2; // Very small radius
      const y = (i / config.particleCount - 0.5) * 3; // Slight vertical spread

      // Add chaotic noise for organic feel
      const noise = Math.sin(i * 0.1) * 0.5;

      voidPositions[i3] = Math.cos(phi) * r + noise;
      voidPositions[i3 + 1] = y + Math.sin(i * 0.05) * 0.3;
      voidPositions[i3 + 2] = Math.sin(phi) * r + Math.cos(i * 0.07) * 0.4;
    }

    // Initialize with void positions (particles start invisible in center)
    for (let i = 0; i < config.particleCount; i++) {
      const data = shapes[initialShapeIndex](i, config.particleCount);
      const i3 = i * 3;

      // Start from void (singularity)
      positions[i3] = voidPositions[i3];
      positions[i3 + 1] = voidPositions[i3 + 1];
      positions[i3 + 2] = voidPositions[i3 + 2];

      // Normals start random or zero
      normals[i3] = 0; normals[i3+1] = 1; normals[i3+2] = 0;

      // Target is the first shape
      targetPositions[i3] = data.pos.x;
      targetPositions[i3 + 1] = data.pos.y;
      targetPositions[i3 + 2] = data.pos.z;

      targetNormals[i3] = data.normal.x;
      targetNormals[i3 + 1] = data.normal.y;
      targetNormals[i3 + 2] = data.normal.z;

      // Start positions for morphing (will be updated after entrance)
      startPositions[i3] = voidPositions[i3];
      startPositions[i3 + 1] = voidPositions[i3 + 1];
      startPositions[i3 + 2] = voidPositions[i3 + 2];

      startNormals[i3] = 0; startNormals[i3+1] = 1; startNormals[i3+2] = 0;

      // Color based on target position (adjusted for compact scale)
      let color: THREE.Color;
      if (config.colorScheme === 'rainbow') {
        // Use rainbow palette - pick color based on particle index for variety
        color = rainbowPalette[i % rainbowPalette.length].clone();
        // Add some variation
        const variation = (Math.random() - 0.5) * 0.2;
        color.offsetHSL(variation, 0, 0);
      } else if (config.colorScheme === 'warm') {
        // Warm with subtle pink/blue gradient
        const colorMix = (data.pos.y + 80) / 160;
        const xMix = (data.pos.x + 80) / 160; // Use x position for pink/blue variation
        color = colors.primary.clone().lerp(colors.secondary, Math.max(0, Math.min(1, colorMix)));
        // Add pink touches
        if (Math.random() < 0.15) {
          color.lerp(colors.accent, 0.4);
        }
        // Add subtle blue touches based on position
        if (xMix > 0.6 && Math.random() < 0.12) {
          const warmColors = colorSchemes.warm as { tertiary: THREE.Color };
          color.lerp(warmColors.tertiary, 0.25);
        }
      } else {
        const colorMix = (data.pos.y + 80) / 160;
        color = colors.primary.clone().lerp(colors.secondary, Math.max(0, Math.min(1, colorMix)));
        // Add some accent
        if (Math.random() < 0.1) {
          color.lerp(colors.accent, 0.5);
        }
      }

      particleColors[i3] = color.r;
      particleColors[i3 + 1] = color.g;
      particleColors[i3 + 2] = color.b;

      sizes[i] = config.particleSize * (0.5 + Math.random() * 0.5);
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // GPU MORPHING: Store start and target positions as attributes
    const startPositionAttr = new THREE.BufferAttribute(new Float32Array(startPositions), 3);
    const targetPositionAttr = new THREE.BufferAttribute(new Float32Array(targetPositions), 3);
    const startNormalAttr = new THREE.BufferAttribute(new Float32Array(startNormals), 3);
    const targetNormalAttr = new THREE.BufferAttribute(new Float32Array(targetNormals), 3);
    const staggerAttr = new THREE.BufferAttribute(new Float32Array(config.particleCount), 1);

    // Initialize stagger values for radial morphing
    for (let i = 0; i < config.particleCount; i++) {
      const i3 = i * 3;
      const dist = Math.sqrt(
        targetPositions[i3] ** 2 + targetPositions[i3 + 1] ** 2 + targetPositions[i3 + 2] ** 2
      );
      staggerAttr.array[i] = dist / 150; // Normalized stagger offset
    }

    geometry.setAttribute('aStartPosition', startPositionAttr);
    geometry.setAttribute('aTargetPosition', targetPositionAttr);
    geometry.setAttribute('aStartNormal', startNormalAttr);
    geometry.setAttribute('aTargetNormal', targetNormalAttr);
    geometry.setAttribute('aStagger', staggerAttr);

    // HIGH-QUALITY GPU-BASED PARTICLE SHADER
    // Based on Codrops GPGPU techniques + soft particle rendering
    const particleMaterial = new THREE.ShaderMaterial({
      uniforms: {
        pixelRatio: { value: renderer.getPixelRatio() },
        uTime: { value: 0 },
        uMorphProgress: { value: 1.0 },  // GPU morphing!
        uEnableStagger: { value: config.enableStaggeredMorph ? 1.0 : 0.0 },
        uBreathing: { value: config.enableBreathing ? 1.0 : 0.0 },
        uBreathingSpeed: { value: config.breathingSpeed },
        uHoverPos: { value: new THREE.Vector2(0, 0) },
        uHoverInfluence: { value: 0.0 },
        uMouseForce: { value: 2.0 },   // Softer swirl force
        uMouseRadius: { value: 0.32 }, // Comfortable radius
        // ✨ AURORA SHIMMER - Elegant color waves across particles
        uAuroraIntensity: { value: 0.35 },    // Subtle but visible
        uAuroraSpeed: { value: 0.15 },        // Slow, dreamy
        // ✨ SPARKLE EFFECT - Random particles briefly flash
        uSparkleIntensity: { value: 0.6 },    // Occasional bright sparkles
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        attribute vec3 aStartPosition;
        attribute vec3 aTargetPosition;
        attribute float aStagger;

        varying vec3 vColor;
        varying float vHover;
        varying float vDepth;
        varying float vDistortion;
        varying float vRandom;

        uniform float pixelRatio;
        uniform float uTime;
        uniform float uMorphProgress;
        uniform float uEnableStagger;
        uniform float uBreathing;
        uniform float uBreathingSpeed;
        uniform vec2 uHoverPos;
        uniform float uHoverInfluence;
        uniform float uMouseForce;
        uniform float uMouseRadius;
        uniform float uAuroraIntensity;
        uniform float uAuroraSpeed;
        uniform float uSparkleIntensity;

        varying float vAurora;
        varying float vSparkle;

        float easeInOutCubic(float t) {
          return t < 0.5 ? 4.0 * t * t * t : 1.0 - pow(-2.0 * t + 2.0, 3.0) / 2.0;
        }

        // Deep Spectrum Palette (Rich Gold -> Deep Red -> Electric Blue)
        vec3 deepPalette(float t) {
          vec3 a = vec3(0.5, 0.5, 0.5);
          vec3 b = vec3(0.5, 0.5, 0.5);
          vec3 c = vec3(1.0, 1.0, 1.0);
          vec3 d = vec3(0.00, 0.15, 0.20);
          return a + b * cos(6.28318 * (c * t + d));
        }

        // Curl Noise for idle drift
        vec3 curlNoise(vec3 p) {
          float t = uTime * 0.1; // Slower drift
          vec3 n = vec3(0.0);
          n.x = sin(p.y * 0.08 + t) * cos(p.z * 0.08 + t);
          n.y = sin(p.z * 0.08 + t) * cos(p.x * 0.08 + t);
          n.z = sin(p.x * 0.08 + t) * cos(p.y * 0.08 + t);
          return n;
        }

        void main() {
          // GPU MORPHING
          float staggeredProgress = uMorphProgress;
          if (uEnableStagger > 0.5) {
            staggeredProgress = clamp((uMorphProgress - aStagger * 0.5) * 2.0, 0.0, 1.0);
          }
          float easedProgress = easeInOutCubic(staggeredProgress);
          vec3 morphedPosition = mix(aStartPosition, aTargetPosition, easedProgress);

          // Standard Effects
          float dist = length(morphedPosition);
          vRandom = fract(sin(dot(aStartPosition.xy, vec2(12.9898, 78.233))) * 43758.5453);

          // IDLE DRIFT
          vec3 idleDrift = curlNoise(morphedPosition * 0.02 + uTime * 0.1) * 2.0;
          vec3 finalPosition = morphedPosition + idleDrift;

          vColor = color;

          // ✨ AURORA SHIMMER - Ethereal color bands (de-synced with per-particle offset to prevent white-out during morph)
          float auroraTime = uTime * uAuroraSpeed;
          // Use START position for wave calculation so it doesn't sync during morphing
          // Plus per-particle random offset to prevent all particles hitting peaks together
          float particlePhase = vRandom * 6.28318; // Random phase offset per particle
          float wave1 = sin(aStartPosition.x * 0.02 + aStartPosition.y * 0.015 + auroraTime + particlePhase) * 0.5 + 0.5;
          float wave2 = sin(aStartPosition.y * 0.018 - aStartPosition.z * 0.02 + auroraTime * 1.3 + particlePhase * 0.7) * 0.5 + 0.5;
          // Multiply waves (not add) to create natural dark bands between aurora streaks
          vAurora = wave1 * wave2 * uAuroraIntensity;

          // ✨ SPARKLE - Rare random particles briefly flash like stars (very selective)
          float sparklePhase = fract(sin(dot(aStartPosition.xy, vec2(127.1, 311.7))) * 43758.5453);
          float sparkleTime = uTime * 0.25 + sparklePhase * 100.0;
          float sparkleWave = pow(max(0.0, sin(sparkleTime)), 60.0); // Very sharp peaks
          // VERY selective - only ~2% of particles can sparkle at any time
          float sparkleMask = step(0.98, fract(sparklePhase * 13.7 + uTime * 0.03));
          vSparkle = sparkleWave * sparkleMask * uSparkleIntensity;

          // FIRST PASS: Project to get screen position for mouse distance
          vec4 mvPositionInitial = modelViewMatrix * vec4(finalPosition, 1.0);
          vec4 projectedInitial = projectionMatrix * mvPositionInitial;
          vec2 screenPos = projectedInitial.xy / projectedInitial.w;

          vec2 toMouse = screenPos - uHoverPos;
          float mouseDist = length(toMouse);

          // HOVER EFFECT: SWIRL VORTEX
          float hoverRadius = uMouseRadius;
          float influence = smoothstep(hoverRadius, 0.0, mouseDist) * uHoverInfluence;

          if (influence > 0.001) {
             // Get direction from mouse
             vec2 mouseDir2D = normalize(toMouse + vec2(0.0001));

             // SWIRL: Rotate around cursor (perpendicular to mouse direction)
             vec2 swirlDir2D = vec2(-mouseDir2D.y, mouseDir2D.x);

             // Add outward push component
             vec3 outwardDir = normalize(finalPosition + vec3(0.001));

             // Combine swirl rotation + gentle outward push
             vec3 swirlDir3D = vec3(swirlDir2D.x, swirlDir2D.y, 0.0);
             vec3 displaceDir = normalize(swirlDir3D * 0.7 + outwardDir * 0.3);

             // SOFTER FORCE - particles drift more gently
             float pushStrength = influence * uMouseForce * 4.0;

             // Flowing motion - smooth sine wave
             float flow = sin(uTime * 2.0 + vRandom * 6.28) * 0.3 + 0.7;

             // Apply swirl displacement
             finalPosition += displaceDir * pushStrength * flow;

             // Add slight lift on Z for 3D feel
             finalPosition.z += influence * 3.0 * sin(uTime * 1.5 + mouseDist * 5.0);

             // Brightness boost
             vColor *= 1.0 + influence * 0.25;
          }

          vDistortion = influence;

          // SECOND PASS: Final projection with displacement applied
          vec4 mvPosition = modelViewMatrix * vec4(finalPosition, 1.0);
          vDepth = -mvPosition.z;

          gl_Position = projectionMatrix * mvPosition;

          // SIZING
          // Slower shimmer
          float shimmer = 0.8 + 0.3 * sin(uTime * 1.0 + vRandom * 20.0);
          float sizeBoost = 1.0 + influence * 1.5;

          // ✨ BREATHING - Gentle global pulse that makes shape feel alive
          float breathe = 1.0 + 0.08 * sin(uTime * 0.4); // Very slow, subtle

          // ✨ SPARKLE SIZE BOOST - Sparkling particles grow briefly
          float sparkleSize = 1.0 + vSparkle * 0.5;

          gl_PointSize = size * shimmer * sizeBoost * breathe * sparkleSize * pixelRatio * (350.0 / -mvPosition.z);
          gl_PointSize = max(1.5, gl_PointSize);
        }
      `,
            fragmentShader: `
              varying vec3 vColor;
              varying float vDistortion;
              varying float vDepth;
              varying float vRandom;
              varying float vAurora;
              varying float vSparkle;

              uniform float uTime;

              // Aurora color palette - ethereal cyan/purple/gold
              vec3 auroraColor(float t) {
                vec3 c1 = vec3(0.1, 0.8, 0.9);  // Cyan
                vec3 c2 = vec3(0.6, 0.2, 0.8);  // Purple
                vec3 c3 = vec3(0.9, 0.7, 0.3);  // Gold
                float phase = fract(t + uTime * 0.03);
                if (phase < 0.33) return mix(c1, c2, phase * 3.0);
                if (phase < 0.66) return mix(c2, c3, (phase - 0.33) * 3.0);
                return mix(c3, c1, (phase - 0.66) * 3.0);
              }

              void main() {
                vec2 uv = gl_PointCoord * 2.0 - 1.0;
                float dist = length(uv);
                float edgeWidth = fwidth(dist) * 2.0; // Sharper anti-aliasing

                // SHARPER CORE: Tighter smoothstep
                float sharpCore = 1.0 - smoothstep(0.15 - edgeWidth, 0.15 + edgeWidth, dist);
                float innerRing = 1.0 - smoothstep(0.35 - edgeWidth, 0.45 + edgeWidth, dist);
                float outerGlow = 1.0 - smoothstep(0.5, 1.0, dist);

                // Combined intensity - Focused on core
                float intensity = sharpCore * 1.5 + innerRing * 0.6 + outerGlow * 0.1;

                if (intensity < 0.02) discard;

                // Slower, subtle twinkle
                float twinkle = sin(uTime * 0.5 + vRandom * 15.0) * 0.5 + 0.5;
                float brightness = 0.5 + twinkle * 0.15;

                vec3 finalColor = vColor * brightness;

                // ✨ AURORA SHIMMER - Subtle ethereal color tint (not additive to avoid white-out)
                vec3 aurora = auroraColor(vRandom);
                // Use multiply-blend instead of add to avoid washing out
                finalColor = mix(finalColor, finalColor * (1.0 + aurora * 0.3), vAurora * 0.6);

                // ✨ SPARKLE - Rare bright flash on random particles
                finalColor += vec3(1.0, 0.95, 0.8) * vSparkle * 0.8;

                // RIM LIGHT BOOST (Fake Fresnel)
                // Since we don't have normals yet in this version, we simulate "solidity" via alpha
                // High alpha = solid object look

                // Depth Fog
                float fogFactor = smoothstep(600.0, 150.0, vDepth);

                // HIGHER ALPHA for solid look
                float alpha = min(1.0, intensity * fogFactor * 1.5);

                // DEEP CONTRAST: Higher gamma makes it less luminous overall
                finalColor = pow(finalColor, vec3(1.3));

                gl_FragColor = vec4(finalColor, alpha);
              }
            `,      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    });

    const particles = new THREE.Points(geometry, particleMaterial);
    scene.add(particles);

    // ========================================================================
    // CONNECTION LINES
    // ========================================================================

    const lineGeometry = new THREE.BufferGeometry();
    const maxLines = deviceProfile.recommendedLines; // Adaptive line count
    const linePositions = new Float32Array(maxLines * 6); // 2 points per line, 3 coords each
    const lineColors = new Float32Array(maxLines * 6);
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    lineGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

    const lineMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: config.lineOpacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      depthTest: false,
    });

    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    // ========================================================================
    // MOTION TRAILS
    // ========================================================================

    // Number of history frames based on trail length (5-30 frames)
    const trailFrames = config.enableTrails ? Math.floor(5 + config.trailLength * 25) : 0;
    // Sample fewer particles for trails to maintain performance
    const trailSampleRate = Math.max(1, Math.floor(config.particleCount / 800));
    const trailParticleCount = config.enableTrails ? Math.floor(config.particleCount / trailSampleRate) : 0;

    // Position history buffer - circular buffer of past positions
    const positionHistory: Float32Array[] = [];
    for (let f = 0; f < trailFrames; f++) {
      positionHistory.push(new Float32Array(trailParticleCount * 3));
    }
    let historyIndex = 0;

    // Trail geometry - lines connecting historical positions
    // Ensure maxTrailLines is never negative (when trails disabled, trailFrames=0, so (0-1)*n = negative)
    const maxTrailLines = config.enableTrails ? trailParticleCount * Math.max(0, trailFrames - 1) : 1;
    const trailGeometry = new THREE.BufferGeometry();
    const trailPositions = new Float32Array(maxTrailLines * 6);
    const trailColors = new Float32Array(maxTrailLines * 6);
    trailGeometry.setAttribute('position', new THREE.BufferAttribute(trailPositions, 3));
    trailGeometry.setAttribute('color', new THREE.BufferAttribute(trailColors, 3));

    const trailMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      depthTest: false,
    });

    const trails = new THREE.LineSegments(trailGeometry, trailMaterial);
    if (config.enableTrails) {
      scene.add(trails);
    }

    // Function to update trail history and render
    const updateTrails = () => {
      if (!config.enableTrails || trailFrames === 0) return;

      const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute;
      const colorAttr = geometry.getAttribute('color') as THREE.BufferAttribute;

      // Store current positions in history buffer
      const currentHistory = positionHistory[historyIndex];
      for (let i = 0; i < trailParticleCount; i++) {
        const srcIdx = i * trailSampleRate;
        const i3 = i * 3;
        const src3 = srcIdx * 3;
        currentHistory[i3] = posAttr.array[src3];
        currentHistory[i3 + 1] = posAttr.array[src3 + 1];
        currentHistory[i3 + 2] = posAttr.array[src3 + 2];
      }

      // Render trails connecting historical positions
      const trailPosAttr = trailGeometry.getAttribute('position') as THREE.BufferAttribute;
      const trailColAttr = trailGeometry.getAttribute('color') as THREE.BufferAttribute;

      let trailIdx = 0;
      for (let i = 0; i < trailParticleCount && trailIdx < maxTrailLines; i++) {
        const srcIdx = i * trailSampleRate;
        const baseColor = new THREE.Color(
          colorAttr.array[srcIdx * 3],
          colorAttr.array[srcIdx * 3 + 1],
          colorAttr.array[srcIdx * 3 + 2]
        );

        // Connect consecutive history frames
        for (let f = 0; f < trailFrames - 1 && trailIdx < maxTrailLines; f++) {
          const currentFrame = (historyIndex - f + trailFrames) % trailFrames;
          const previousFrame = (historyIndex - f - 1 + trailFrames) % trailFrames;

          const curr = positionHistory[currentFrame];
          const prev = positionHistory[previousFrame];

          const i3 = i * 3;
          const li = trailIdx * 6;

          // Check if positions are valid (not all zeros from initialization)
          if (Math.abs(prev[i3]) > 0.001 || Math.abs(prev[i3 + 1]) > 0.001) {
            // Fade based on age (older = more transparent)
            const age = f / (trailFrames - 1);
            const opacity = (1 - age) * config.trailLength;

            trailPosAttr.array[li] = curr[i3];
            trailPosAttr.array[li + 1] = curr[i3 + 1];
            trailPosAttr.array[li + 2] = curr[i3 + 2];
            trailPosAttr.array[li + 3] = prev[i3];
            trailPosAttr.array[li + 4] = prev[i3 + 1];
            trailPosAttr.array[li + 5] = prev[i3 + 2];

            // Color with fade
            trailColAttr.array[li] = baseColor.r * opacity;
            trailColAttr.array[li + 1] = baseColor.g * opacity;
            trailColAttr.array[li + 2] = baseColor.b * opacity;
            trailColAttr.array[li + 3] = baseColor.r * opacity * 0.7;
            trailColAttr.array[li + 4] = baseColor.g * opacity * 0.7;
            trailColAttr.array[li + 5] = baseColor.b * opacity * 0.7;

            trailIdx++;
          }
        }
      }

      // Clear remaining trail segments
      for (let i = trailIdx * 6; i < maxTrailLines * 6; i++) {
        trailPosAttr.array[i] = 0;
        trailColAttr.array[i] = 0;
      }

      trailPosAttr.needsUpdate = true;
      trailColAttr.needsUpdate = true;
      trailGeometry.setDrawRange(0, trailIdx * 2);

      // Advance history buffer index
      historyIndex = (historyIndex + 1) % trailFrames;
    };

    // ========================================================================
    // OPTIMIZATION: Spatial Hash Grid for O(n) line connections (was O(n²))
    // ========================================================================
    const cellSize = config.connectionDistance; // Cell size = max connection distance
    const spatialGrid = new Map<string, number[]>(); // Cell key -> particle indices

    // Reusable arrays to avoid allocations
    const breathedPositions = new Float32Array(config.particleCount * 3);
    let lineUpdateFrame = 0; // Frame counter for skipping

    // Pre-compute cell key (avoid string allocation in hot loop)
    const getCellKey = (x: number, y: number, z: number): string => {
      const cx = Math.floor(x / cellSize);
      const cy = Math.floor(y / cellSize);
      const cz = Math.floor(z / cellSize);
      return `${cx},${cy},${cz}`;
    };

    // Easing function for line position calculation (must match GPU shader)
    const easeInOutCubicCPU = (t: number): number => {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };

    // Function to update line connections with spatial hashing
    const updateLines = (currentTime: number, currentMorphProgress: number) => {
      // OPTIMIZATION: Update lines every 2nd frame (imperceptible, 50% less work)
      lineUpdateFrame++;
      if (lineUpdateFrame % 2 !== 0) return;

      // GPU MORPHING FIX: Read from start/target attributes and interpolate
      const startAttr = geometry.getAttribute('aStartPosition') as THREE.BufferAttribute;
      const targetAttr = geometry.getAttribute('aTargetPosition') as THREE.BufferAttribute;
      const staggerAttrGPU = geometry.getAttribute('aStagger') as THREE.BufferAttribute;
      const colorAttr = geometry.getAttribute('color') as THREE.BufferAttribute;
      const linePositionAttr = lineGeometry.getAttribute('position') as THREE.BufferAttribute;
      const lineColorAttr = lineGeometry.getAttribute('color') as THREE.BufferAttribute;

      const maxDist = config.connectionDistance;
      const maxDistSq = maxDist * maxDist;

      // Breathing parameters
      const breathingEnabled = config.enableBreathing ? 1.0 : 0.0;
      const breathingSpeed = config.breathingSpeed;

      // Sample rate for which particles to include in line calculations
      // OPTIMIZATION: Calc sample rate to get ~1500 line nodes regardless of particle count
      const sampleRate = Math.max(1, Math.floor(config.particleCount / 1500));
      const sampledCount = Math.ceil(config.particleCount / sampleRate);

      // OPTIMIZATION: Pre-compute morphed+breathed positions (matching GPU shader logic)
      for (let i = 0; i < config.particleCount; i += sampleRate) {
        const i3 = i * 3;
        const sampledI3 = Math.floor(i / sampleRate) * 3;

        // Calculate staggered progress (same as GPU shader)
        let staggeredProgress = currentMorphProgress;
        if (config.enableStaggeredMorph) {
          const stagger = staggerAttrGPU.array[i];
          staggeredProgress = Math.max(0, Math.min(1, (currentMorphProgress - stagger * 0.5) * 2));
        }
        const easedProgress = easeInOutCubicCPU(staggeredProgress);

        // Interpolate between start and target (same as GPU shader)
        let x = startAttr.array[i3] + (targetAttr.array[i3] - startAttr.array[i3]) * easedProgress;
        let y = startAttr.array[i3 + 1] + (targetAttr.array[i3 + 1] - startAttr.array[i3 + 1]) * easedProgress;
        let z = startAttr.array[i3 + 2] + (targetAttr.array[i3 + 2] - startAttr.array[i3 + 2]) * easedProgress;

        // Apply breathing
        if (breathingEnabled > 0) {
          const dist = Math.sqrt(x * x + y * y + z * z);
          const breathe = 1.0 + breathingEnabled * Math.sin(currentTime * breathingSpeed * 2.0 + dist * 0.02) * 0.08;
          x *= breathe;
          y *= breathe;
          z *= breathe;
        }

        breathedPositions[sampledI3] = x;
        breathedPositions[sampledI3 + 1] = y;
        breathedPositions[sampledI3 + 2] = z;
      }

      // Build spatial hash grid
      spatialGrid.clear();
      for (let i = 0; i < sampledCount; i++) {
        const i3 = i * 3;
        const key = getCellKey(breathedPositions[i3], breathedPositions[i3 + 1], breathedPositions[i3 + 2]);
        let cell = spatialGrid.get(key);
        if (!cell) {
          cell = [];
          spatialGrid.set(key, cell);
        }
        cell.push(i);
      }

      // Find connections using spatial grid - only check neighboring cells
      let lineIndex = 0;
      const checkedPairs = new Set<string>(); // Avoid duplicate pairs

      for (let i = 0; i < sampledCount && lineIndex < maxLines; i++) {
        const i3 = i * 3;
        const ix = breathedPositions[i3];
        const iy = breathedPositions[i3 + 1];
        const iz = breathedPositions[i3 + 2];

        // Get cell coordinates
        const cx = Math.floor(ix / cellSize);
        const cy = Math.floor(iy / cellSize);
        const cz = Math.floor(iz / cellSize);

        // Check current cell and 26 neighbors (3x3x3 cube)
        for (let dx = -1; dx <= 1 && lineIndex < maxLines; dx++) {
          for (let dy = -1; dy <= 1 && lineIndex < maxLines; dy++) {
            for (let dz = -1; dz <= 1 && lineIndex < maxLines; dz++) {
              const neighborKey = `${cx + dx},${cy + dy},${cz + dz}`;
              const neighborCell = spatialGrid.get(neighborKey);
              if (!neighborCell) continue;

              for (const j of neighborCell) {
                if (j <= i) continue; // Only check each pair once

                // Skip if already checked
                const pairKey = i < j ? `${i}-${j}` : `${j}-${i}`;
                if (checkedPairs.has(pairKey)) continue;
                checkedPairs.add(pairKey);

                const j3 = j * 3;
                const jx = breathedPositions[j3];
                const jy = breathedPositions[j3 + 1];
                const jz = breathedPositions[j3 + 2];

                const ddx = ix - jx;
                const ddy = iy - jy;
                const ddz = iz - jz;
                const distSq = ddx * ddx + ddy * ddy + ddz * ddz;

                if (distSq < maxDistSq && lineIndex < maxLines) {
                  const li = lineIndex * 6;
                  const origI = i * sampleRate;
                  const origJ = j * sampleRate;

                  linePositionAttr.array[li] = ix;
                  linePositionAttr.array[li + 1] = iy;
                  linePositionAttr.array[li + 2] = iz;
                  linePositionAttr.array[li + 3] = jx;
                  linePositionAttr.array[li + 4] = jy;
                  linePositionAttr.array[li + 5] = jz;

                  const opacity = 1 - Math.sqrt(distSq) / maxDist;
                  lineColorAttr.array[li] = colorAttr.array[origI * 3] * opacity;
                  lineColorAttr.array[li + 1] = colorAttr.array[origI * 3 + 1] * opacity;
                  lineColorAttr.array[li + 2] = colorAttr.array[origI * 3 + 2] * opacity;
                  lineColorAttr.array[li + 3] = colorAttr.array[origJ * 3] * opacity;
                  lineColorAttr.array[li + 4] = colorAttr.array[origJ * 3 + 1] * opacity;
                  lineColorAttr.array[li + 5] = colorAttr.array[origJ * 3 + 2] * opacity;

                  lineIndex++;
                }
              }
            }
          }
        }
      }

      // Clear remaining lines (only what's needed, not entire buffer)
      const clearStart = lineIndex * 6;
      const clearEnd = Math.min(clearStart + 600, maxLines * 6); // Clear small batch
      for (let i = clearStart; i < clearEnd; i++) {
        linePositionAttr.array[i] = 0;
        lineColorAttr.array[i] = 0;
      }

      linePositionAttr.needsUpdate = true;
      lineColorAttr.needsUpdate = true;
      lineGeometry.setDrawRange(0, lineIndex * 2);
    };

    // ========================================================================
    // ANIMATION
    // ========================================================================

    let currentShapeIndex = initialShapeIndex;
    let morphProgress = 1;
    let lastMorphTime = 0;
    let time = 0;

    // Entrance animation state
    let entranceProgress = 0;
    let entranceComplete = false;
    const entranceDuration = 2.5; // seconds for entrance animation
    const entranceDelay = 0.3; // Brief pause before animation starts

    const positionAttr = geometry.getAttribute('position') as THREE.BufferAttribute;

    // OPTIMIZATION: Precompute target distances for entrance animation (avoid sqrt per frame)
    const targetDistances = new Float32Array(config.particleCount);
    const maxTargetDist = 120; // Approximate max distance
    for (let i = 0; i < config.particleCount; i++) {
      const i3 = i * 3;
      targetDistances[i] = Math.sqrt(
        targetPositions[i3] ** 2 +
        targetPositions[i3 + 1] ** 2 +
        targetPositions[i3 + 2] ** 2
      );
    }

    // Elastic ease-out for dramatic emergence
    const easeOutElastic = (t: number): number => {
      if (t === 0 || t === 1) return t;
      const p = 0.4;
      return Math.pow(2, -10 * t) * Math.sin((t - p / 4) * (2 * Math.PI) / p) + 1;
    };

    // Exponential ease-out for smooth deceleration
    const easeOutExpo = (t: number): number => {
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    };

    const animate = () => {
      time += 0.016; // ~60fps

      // ========================================================================
      // ENTRANCE ANIMATION - Emergence from the void
      // ========================================================================
      if (!entranceComplete) {
        const entranceTime = Math.max(0, time - entranceDelay);

        if (entranceTime > 0) {
          entranceProgress = Math.min(1, entranceTime / entranceDuration);

          // Staggered emergence - particles emerge in waves from center outward
          // OPTIMIZATION: Use precomputed targetDistances (no sqrt per frame!)
          for (let i = 0; i < config.particleCount; i++) {
            const i3 = i * 3;

            // Use precomputed distance (was: Math.sqrt() per particle per frame)
            const particleDelay = (targetDistances[i] / maxTargetDist) * 0.4;

            // Individual particle progress with stagger
            const particleProgress = Math.max(0, Math.min(1,
              (entranceProgress - particleDelay) / (1 - particleDelay * 0.8)
            ));

            // Use elastic easing for dramatic "pop" effect
            const easedProgress = particleProgress < 0.7
              ? easeOutExpo(particleProgress / 0.7) * 0.85
              : 0.85 + easeOutElastic((particleProgress - 0.7) / 0.3) * 0.15;

            // Interpolate from void to target
            positions[i3] = voidPositions[i3] + (targetPositions[i3] - voidPositions[i3]) * easedProgress;
            positions[i3 + 1] = voidPositions[i3 + 1] + (targetPositions[i3 + 1] - voidPositions[i3 + 1]) * easedProgress;
            positions[i3 + 2] = voidPositions[i3 + 2] + (targetPositions[i3 + 2] - voidPositions[i3 + 2]) * easedProgress;
          }

          positionAttr.needsUpdate = true;

          // Check if entrance is complete
          if (entranceProgress >= 1) {
            entranceComplete = true;
            lastMorphTime = time; // Reset morph timer after entrance

            // Update start positions to current for future morphing
            for (let i = 0; i < config.particleCount * 3; i++) {
              startPositions[i] = targetPositions[i];
              positions[i] = targetPositions[i];
            }
            positionAttr.needsUpdate = true;
          }
        }

        // Update lines and trails during entrance
        updateLines(time, morphProgress);
        updateTrails();

        // Update background stars and shooting stars
        updateStars(time);
        updateShootingStars(0.016);

        // Update shader uniforms
        particleMaterial.uniforms.uTime.value = time;

        // ✨ HOVER DURING ENTRANCE - Enable interactivity from the start!
        if (config.enableHover) {
          currentMouseX = targetMouseX;
          currentMouseY = targetMouseY;

          particleMaterial.uniforms.uHoverPos.value.set(currentMouseX, currentMouseY);
          particleMaterial.uniforms.uHoverInfluence.value = hoverInfluence;

          // Decay influence when mouse leaves
          if (isMouseOverCanvas) {
            hoverInfluence = Math.max(0.7, hoverInfluence * 0.98);
          } else {
            hoverInfluence *= 0.9; // Decay to 0
          }

        }

        // Slight camera pull-back effect during entrance for drama
        const entranceCameraOffset = (1 - entranceProgress) * 50;
        camera.position.z = zoomLevel + entranceCameraOffset;

        // Apply rotation
        particles.rotation.y = userRotationY;
        particles.rotation.x = userRotationX + Math.sin(time * 0.1) * 0.05;
        lines.rotation.y = particles.rotation.y;
        lines.rotation.x = particles.rotation.x;
        trails.rotation.y = particles.rotation.y;
        trails.rotation.x = particles.rotation.x;

        // Apply panning (right-click drag)
        particles.position.x = panX;
        particles.position.y = panY;
        lines.position.x = panX;
        lines.position.y = panY;
        trails.position.x = panX;
        trails.position.y = panY;
        stars.position.x = panX * 0.3; // Stars move slower for parallax
        stars.position.y = panY * 0.3;

        // Render
        const usePostProcessing = config.enableBloom || config.enableDepthOfField;
        if (usePostProcessing) {
          composer.render();
        } else {
          renderer.render(scene, camera);
        }

        animationRef.current = requestAnimationFrame(animate);
        return; // Skip normal animation during entrance
      }

      // Reset camera after entrance
      camera.position.z = zoomLevel;

      // Check for shape transition (only if auto-cycling is enabled)
      const shouldAutoCycle = config.selectedShape === null;

      // Reset timer when morph completes (so duration counts from when shape is fully formed)
      if (morphProgress >= 1 && morphProgress < 1.01) {
        lastMorphTime = time;
        morphProgress = 1.01; // Mark as "timer started"
      }

      if (shouldAutoCycle && time - lastMorphTime > config.morphDuration && morphProgress >= 1) {
        // Start new morph
        morphProgress = 0;
        particleMaterial.uniforms.uMorphProgress.value = 0;

        // GPU MORPHING: Copy current target to start, generate new target
        const startAttr = geometry.getAttribute('aStartPosition') as THREE.BufferAttribute;
        const targetAttr = geometry.getAttribute('aTargetPosition') as THREE.BufferAttribute;
        const startNormalAttr = geometry.getAttribute('aStartNormal') as THREE.BufferAttribute;
        const targetNormalAttr = geometry.getAttribute('aTargetNormal') as THREE.BufferAttribute;
        const staggerAttrGPU = geometry.getAttribute('aStagger') as THREE.BufferAttribute;

        // Generate new target shape
        currentShapeIndex = (currentShapeIndex + 1) % shapes.length;

        for (let i = 0; i < config.particleCount; i++) {
          const i3 = i * 3;

          // Copy old target to new start (for GPU morphing)
          startAttr.array[i3] = targetAttr.array[i3];
          startAttr.array[i3 + 1] = targetAttr.array[i3 + 1];
          startAttr.array[i3 + 2] = targetAttr.array[i3 + 2];

          startNormalAttr.array[i3] = targetNormalAttr.array[i3];
          startNormalAttr.array[i3 + 1] = targetNormalAttr.array[i3 + 1];
          startNormalAttr.array[i3 + 2] = targetNormalAttr.array[i3 + 2];

          // Also update CPU arrays for line calculations
          startPositions[i3] = targetPositions[i3];
          startPositions[i3 + 1] = targetPositions[i3 + 1];
          startPositions[i3 + 2] = targetPositions[i3 + 2];

          // Generate new target
          const data = shapes[currentShapeIndex](i, config.particleCount);

          targetAttr.array[i3] = data.pos.x;
          targetAttr.array[i3 + 1] = data.pos.y;
          targetAttr.array[i3 + 2] = data.pos.z;

          targetNormalAttr.array[i3] = data.normal.x;
          targetNormalAttr.array[i3 + 1] = data.normal.y;
          targetNormalAttr.array[i3 + 2] = data.normal.z;

          targetPositions[i3] = data.pos.x;
          targetPositions[i3 + 1] = data.pos.y;
          targetPositions[i3 + 2] = data.pos.z;

          // Update stagger based on current position (radial from center)
          const x = startAttr.array[i3], y = startAttr.array[i3 + 1], z = startAttr.array[i3 + 2];
          if (config.staggerDirection === 'radial') {
            staggerAttrGPU.array[i] = Math.sqrt(x * x + y * y + z * z) / 150;
          } else if (config.staggerDirection === 'horizontal') {
            staggerAttrGPU.array[i] = (x + 100) / 200;
          } else if (config.staggerDirection === 'vertical') {
            staggerAttrGPU.array[i] = (y + 100) / 200;
          }

          // Update colors based on new positions
          let color: THREE.Color;
          if (config.colorScheme === 'rainbow') {
            color = rainbowPalette[i % rainbowPalette.length].clone();
            const variation = (Math.random() - 0.5) * 0.2;
            color.offsetHSL(variation, 0, 0);
          } else if (config.colorScheme === 'warm') {
            const colorMix = (data.pos.y + 80) / 160;
            const xMix = (data.pos.x + 80) / 160;
            color = colors.primary.clone().lerp(colors.secondary, Math.max(0, Math.min(1, colorMix)));
            if (Math.random() < 0.15) {
              color.lerp(colors.accent, 0.4);
            }
            if (xMix > 0.6 && Math.random() < 0.12) {
              const warmColors = colorSchemes.warm as { tertiary: THREE.Color };
              color.lerp(warmColors.tertiary, 0.25);
            }
          } else {
            const colorMix = (data.pos.y + 80) / 160;
            color = colors.primary.clone().lerp(colors.secondary, Math.max(0, Math.min(1, colorMix)));
            if (Math.random() < 0.1) {
              color.lerp(colors.accent, 0.5);
            }
          }
          particleColors[i3] = color.r;
          particleColors[i3 + 1] = color.g;
          particleColors[i3 + 2] = color.b;
        }

        // Mark GPU attributes as needing update
        startAttr.needsUpdate = true;
        targetAttr.needsUpdate = true;
        startNormalAttr.needsUpdate = true;
        targetNormalAttr.needsUpdate = true;
        staggerAttrGPU.needsUpdate = true;
        (geometry.getAttribute('color') as THREE.BufferAttribute).needsUpdate = true;
      }

      // GPU MORPH ANIMATION - Just update the uniform! (was 20,000 calculations on CPU)
      if (morphProgress < 1) {
        morphProgress = Math.min(1, morphProgress + 0.003); // ~5 second transition
        // GPU does all the interpolation work via uMorphProgress uniform
        particleMaterial.uniforms.uMorphProgress.value = morphProgress;
      }

      // Update line connections
      updateLines(time, morphProgress);

      // Update motion trails
      updateTrails();

      // Update background stars and shooting stars
      updateStars(time);
      updateShootingStars(0.016);

      // Update shader uniforms
      particleMaterial.uniforms.uTime.value = time;

      // Update hover uniforms - INSTANT RESPONSE, no lerp
      if (config.enableHover) {
        // DIRECT mouse position - no smoothing for instant reactivity
        currentMouseX = targetMouseX;
        currentMouseY = targetMouseY;

        particleMaterial.uniforms.uHoverPos.value.set(currentMouseX, currentMouseY);
        particleMaterial.uniforms.uHoverInfluence.value = hoverInfluence;

        // Decay influence when mouse leaves canvas
        if (isMouseOverCanvas) {
          hoverInfluence = Math.max(0.7, hoverInfluence * 0.98);
        } else {
          hoverInfluence *= 0.9;
        }


        // PERMANENT COLOR CHANGE - Update particle colors when hovered
        if (hoverInfluence > 0.1) {
          const colorAttr = geometry.getAttribute('color') as THREE.BufferAttribute;
          const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute;
          const hoverRadiusWorld = 35; // World-space radius for color change

          // Get mouse position in world space using proper raycasting
          const colorMouseNDC = new THREE.Vector3(currentMouseX, currentMouseY, 0.5);
          colorMouseNDC.unproject(camera);
          const colorDir = colorMouseNDC.sub(camera.position).normalize();
          const colorDist = -camera.position.z / colorDir.z;
          const mouseWorld = camera.position.clone().add(colorDir.multiplyScalar(colorDist));
          mouseWorld.sub(particles.position);

          let colorsChanged = false;

          // Sample particles for performance (every 3rd particle)
          for (let i = 0; i < config.particleCount; i += 3) {
            const i3 = i * 3;
            const px = posAttr.array[i3];
            const py = posAttr.array[i3 + 1];

            // Distance from mouse in XY plane
            const dx = px - mouseWorld.x;
            const dy = py - mouseWorld.y;
            const distSq = dx * dx + dy * dy;

            if (distSq < hoverRadiusWorld * hoverRadiusWorld) {
              // RAINBOW COLOR based on angle + time
              const angle = Math.atan2(dy, dx);
              const hue = (angle / (Math.PI * 2) + 0.5 + time * 0.1) % 1;

              // HSV to RGB (vibrant rainbow)
              const h = hue * 6;
              const c = 1.0;
              const x = c * (1 - Math.abs(h % 2 - 1));
              let r = 0, g = 0, b = 0;

              if (h < 1) { r = c; g = x; }
              else if (h < 2) { r = x; g = c; }
              else if (h < 3) { g = c; b = x; }
              else if (h < 4) { g = x; b = c; }
              else if (h < 5) { r = x; b = c; }
              else { r = c; b = x; }

              // Boost saturation and add sparkle
              const sparkle = Math.random() * 0.2;
              r = Math.min(1, r + 0.1 + sparkle);
              g = Math.min(1, g + 0.1 + sparkle);
              b = Math.min(1, b + 0.1 + sparkle);

              // Blend with existing color (80% new, 20% old for smooth transition)
              colorAttr.array[i3] = colorAttr.array[i3] * 0.2 + r * 0.8;
              colorAttr.array[i3 + 1] = colorAttr.array[i3 + 1] * 0.2 + g * 0.8;
              colorAttr.array[i3 + 2] = colorAttr.array[i3 + 2] * 0.2 + b * 0.8;

              // Also color neighbors for fuller effect
              if (i + 1 < config.particleCount) {
                colorAttr.array[i3 + 3] = colorAttr.array[i3];
                colorAttr.array[i3 + 4] = colorAttr.array[i3 + 1];
                colorAttr.array[i3 + 5] = colorAttr.array[i3 + 2];
              }
              if (i + 2 < config.particleCount) {
                colorAttr.array[i3 + 6] = colorAttr.array[i3];
                colorAttr.array[i3 + 7] = colorAttr.array[i3 + 1];
                colorAttr.array[i3 + 8] = colorAttr.array[i3 + 2];
              }

              colorsChanged = true;
            }
          }

          if (colorsChanged) {
            colorAttr.needsUpdate = true;
          }
        }
      }

      // Apply momentum when not dragging
      if (!isDragging) {
        // Apply remaining velocity with friction
        if (Math.abs(velocityY) > 0.0001 || Math.abs(velocityX) > 0.0001) {
          userRotationY += velocityY;
          userRotationX += velocityX;
          userRotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, userRotationX));
          velocityY *= friction;
          velocityX *= friction;
        }

        // Auto-rotation (only when momentum is nearly zero and not paused)
        if (!autoRotationPaused && !isPaused && Math.abs(velocityY) < 0.001) {
          userRotationY += config.rotationSpeed * 0.01;
        }
      }

      // Apply keyboard rotation
      userRotationY += keyRotationY;
      userRotationX += keyRotationX;
      keyRotationY *= 0.9; // Smooth decay
      keyRotationX *= 0.9;
      userRotationX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, userRotationX));

      // Apply combined rotation
      particles.rotation.y = userRotationY;
      particles.rotation.x = userRotationX + Math.sin(time * 0.1) * 0.05;
      lines.rotation.y = particles.rotation.y;
      lines.rotation.x = particles.rotation.x;
      trails.rotation.y = particles.rotation.y;
      trails.rotation.x = particles.rotation.x;

      // Apply panning (right-click drag)
      particles.position.x = panX;
      particles.position.y = panY;
      lines.position.x = panX;
      lines.position.y = panY;
      trails.position.x = panX;
      trails.position.y = panY;
      stars.position.x = panX * 0.3; // Stars move slower for parallax
      stars.position.y = panY * 0.3;

      // Render with post-processing or direct
      const usePostProcessing = config.enableBloom || config.enableDepthOfField;
      if (usePostProcessing) {
        composer.render();
      } else {
        renderer.render(scene, camera);
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    // Resize handler
    const handleResize = () => {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
      renderTarget.setSize(newWidth, newHeight);
      composer.setSize(newWidth, newHeight);
      if (bloomPass) {
        bloomPass.resolution.set(newWidth, newHeight);
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (autoRotationResumeTimeout) {
        clearTimeout(autoRotationResumeTimeout);
      }
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      renderer.domElement.removeEventListener('mousemove', onMouseMove);
      renderer.domElement.removeEventListener('mouseup', onMouseUp);
      renderer.domElement.removeEventListener('mouseleave', onMouseLeave);
      renderer.domElement.removeEventListener('contextmenu', onContextMenu);
      renderer.domElement.removeEventListener('touchstart', onTouchStart);
      renderer.domElement.removeEventListener('touchmove', onTouchMove);
      renderer.domElement.removeEventListener('touchend', onTouchEnd);
      if (config.enableZoom) {
        renderer.domElement.removeEventListener('wheel', onWheel);
      }
      if (config.enableHover) {
        renderer.domElement.removeEventListener('mousemove', onHoverMove);
        renderer.domElement.removeEventListener('mouseleave', onHoverLeave);
      }
      if (config.enableKeyboard) {
        window.removeEventListener('keydown', onKeyDown);
      }
      window.removeEventListener('resize', handleResize);
      container.removeChild(renderer.domElement);
      geometry.dispose();
      particleMaterial.dispose();
      lineGeometry.dispose();
      lineMaterial.dispose();
      trailGeometry.dispose();
      trailMaterial.dispose();
      // Clean up star field
      starGeometry.dispose();
      starMaterial.dispose();
      // Clean up shooting stars
      shootingStars.forEach((star) => {
        star.line.geometry.dispose();
        (star.line.material as THREE.ShaderMaterial).dispose();
      });
      renderTarget.dispose();
      composer.dispose();
      renderer.dispose();
    };
  }, [config]);

  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, [initScene]);

  return (
    <div
      ref={containerRef}
      className={props.className}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
        ...props.style,
      }}
    />
  );
}

export default MorphingParticles;
