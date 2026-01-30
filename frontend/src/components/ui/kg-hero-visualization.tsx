import React, { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Big Bang animation phases
type BigBangPhase = 'singularity' | 'explosion' | 'expansion' | 'settling' | 'orbit';

interface Node {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  baseRadius: number;
  type: 'concept' | 'person' | 'argument' | 'work';
  label: string;
  greekLabel?: string;
  color: string;
  glowColor: string;
  coreColor: string;
  celestialType: 'nebulaStar' | 'planet' | 'pulsar' | 'sun';
  pulsePhase: number;
  depth: number; // 0-1 for parallax
  birthTime: number;
  // Orbital properties
  orbitRadius: number;
  orbitSpeed: number;
  orbitAngle: number;
  orbitCenterX: number;
  orbitCenterY: number;
  orbitEccentricity: number; // 0 = circle, higher = more elliptical
  orbitTilt: number; // Rotation of the ellipse
  // Animation properties for celestial effects
  rotationAngle: number;
  flarePhase: number;
  // Big bang properties
  explosionAngle: number;
  explosionSpeed: number;
  targetX: number;
  targetY: number;
}

interface Edge {
  source: string;
  target: string;
  strength: number;
  flowOffset: number;
  flowSpeed: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
  life: number;
  maxLife: number;
  type: 'sparkle' | 'star' | 'flare' | 'dust';
  rotation: number;
  rotationSpeed: number;
  twinklePhase: number;
  twinkleSpeed: number;
}

interface Ripple {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  opacity: number;
}

interface Shockwave {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  opacity: number;
  color: string;
  thickness: number;
}

interface ExplosionParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
  life: number;
  maxLife: number;
  trail: { x: number; y: number }[];
}

const NODE_TYPES = {
  concept: {
    color: '#a78bfa',
    glowColor: 'rgba(167, 139, 250, 0.8)',
    coreColor: '#e0d4ff',
    celestialType: 'nebulaStar' as const,  // Ethereal, mystical star
  },
  person: {
    color: '#60a5fa',
    glowColor: 'rgba(96, 165, 250, 0.8)',
    coreColor: '#dbeafe',
    celestialType: 'planet' as const,       // Solid planet with atmosphere
  },
  argument: {
    color: '#34d399',
    glowColor: 'rgba(52, 211, 153, 0.8)',
    coreColor: '#d1fae5',
    celestialType: 'pulsar' as const,       // Energetic pulsing star
  },
  work: {
    color: '#fbbf24',
    glowColor: 'rgba(251, 191, 36, 0.8)',
    coreColor: '#fef3c7',
    celestialType: 'sun' as const,          // Radiant sun with corona
  },
};

const SAMPLE_NODES: Omit<Node, 'x' | 'y' | 'vx' | 'vy' | 'pulsePhase' | 'depth' | 'birthTime' | 'baseRadius' | 'orbitRadius' | 'orbitSpeed' | 'orbitAngle' | 'orbitCenterX' | 'orbitCenterY' | 'orbitEccentricity' | 'orbitTilt' | 'rotationAngle' | 'flarePhase' | 'explosionAngle' | 'explosionSpeed' | 'targetX' | 'targetY'>[] = [
  { id: '1', radius: 12, type: 'concept', label: 'Free Will', greekLabel: 'ἐλευθερία', ...NODE_TYPES.concept },
  { id: '2', radius: 10, type: 'concept', label: 'Fate', greekLabel: 'εἱμαρμένη', ...NODE_TYPES.concept },
  { id: '3', radius: 11, type: 'person', label: 'Chrysippus', greekLabel: 'Χρύσιππος', ...NODE_TYPES.person },
  { id: '4', radius: 9, type: 'person', label: 'Epicurus', greekLabel: 'Ἐπίκουρος', ...NODE_TYPES.person },
  { id: '5', radius: 8, type: 'argument', label: 'Lazy Argument', ...NODE_TYPES.argument },
  { id: '6', radius: 10, type: 'concept', label: 'Determinism', ...NODE_TYPES.concept },
  { id: '7', radius: 10, type: 'person', label: 'Aristotle', greekLabel: 'Ἀριστοτέλης', ...NODE_TYPES.person },
  { id: '8', radius: 7, type: 'work', label: 'De Fato', ...NODE_TYPES.work },
  { id: '9', radius: 9, type: 'concept', label: 'ἐφ\' ἡμῖν', ...NODE_TYPES.concept },
  { id: '10', radius: 8, type: 'person', label: 'Epictetus', greekLabel: 'Ἐπίκτητος', ...NODE_TYPES.person },
  { id: '11', radius: 9, type: 'argument', label: 'Compatibilism', ...NODE_TYPES.argument },
  { id: '12', radius: 7, type: 'concept', label: 'Providence', greekLabel: 'πρόνοια', ...NODE_TYPES.concept },
  { id: '13', radius: 9, type: 'person', label: 'Augustine', ...NODE_TYPES.person },
  { id: '14', radius: 6, type: 'work', label: 'Meditations', ...NODE_TYPES.work },
  { id: '15', radius: 8, type: 'concept', label: 'Causation', greekLabel: 'αἰτία', ...NODE_TYPES.concept },
  { id: '16', radius: 7, type: 'person', label: 'Carneades', greekLabel: 'Καρνεάδης', ...NODE_TYPES.person },
  { id: '17', radius: 8, type: 'concept', label: 'Necessity', greekLabel: 'ἀνάγκη', ...NODE_TYPES.concept },
  { id: '18', radius: 7, type: 'person', label: 'Zeno', greekLabel: 'Ζήνων', ...NODE_TYPES.person },
  { id: '19', radius: 6, type: 'work', label: 'Ethics', ...NODE_TYPES.work },
  { id: '20', radius: 8, type: 'argument', label: 'Master Argument', ...NODE_TYPES.argument },
];

const SAMPLE_EDGES: Omit<Edge, 'flowOffset' | 'flowSpeed'>[] = [
  { source: '1', target: '2', strength: 0.9 },
  { source: '1', target: '3', strength: 0.95 },
  { source: '1', target: '9', strength: 0.85 },
  { source: '2', target: '6', strength: 0.7 },
  { source: '3', target: '5', strength: 0.8 },
  { source: '3', target: '11', strength: 0.85 },
  { source: '4', target: '1', strength: 0.75 },
  { source: '6', target: '5', strength: 0.6 },
  { source: '7', target: '1', strength: 0.8 },
  { source: '7', target: '9', strength: 0.7 },
  { source: '8', target: '3', strength: 0.65 },
  { source: '10', target: '3', strength: 0.75 },
  { source: '10', target: '9', strength: 0.7 },
  { source: '11', target: '6', strength: 0.8 },
  { source: '12', target: '2', strength: 0.6 },
  { source: '13', target: '1', strength: 0.7 },
  { source: '13', target: '12', strength: 0.55 },
  { source: '14', target: '10', strength: 0.6 },
  { source: '15', target: '6', strength: 0.75 },
  { source: '15', target: '2', strength: 0.65 },
  { source: '16', target: '5', strength: 0.6 },
  { source: '4', target: '6', strength: 0.5 },
  { source: '17', target: '2', strength: 0.7 },
  { source: '17', target: '6', strength: 0.75 },
  { source: '18', target: '3', strength: 0.8 },
  { source: '18', target: '2', strength: 0.65 },
  { source: '19', target: '7', strength: 0.7 },
  { source: '20', target: '17', strength: 0.75 },
  { source: '20', target: '1', strength: 0.6 },
  { source: '7', target: '19', strength: 0.8 },
];

// Floating Greek text elements
const FLOATING_TEXTS = [
  'ἐλευθερία', 'εἱμαρμένη', 'πρόνοια', 'αἰτία', 'ἀνάγκη',
  'λόγος', 'ψυχή', 'ἀρετή', 'τύχη', 'φύσις'
];

// Big Bang timing constants (in milliseconds)
const BIG_BANG_TIMING = {
  singularity: { start: 0, duration: 7000 },     // Longer, dramatic singularity
  explosion: { start: 7000, duration: 600 },     // Initial burst
  expansion: { start: 7600, duration: 2000 },    // Nodes flying outward
  settling: { start: 9600, duration: 1500 },     // Slowing down
  orbit: { start: 11100, duration: Infinity },   // Normal orbital motion
};

// Singularity sub-phases - black hole compresses to singularity then explodes
const SINGULARITY_PHASES = {
  blackHole: { start: 0, end: 0.45 },           // Stable black hole, gentle constant rotation
  compression: { start: 0.45, end: 0.85 },      // Everything compresses smaller and smaller
  singularity: { start: 0.85, end: 1.0 },       // Infinitely small bright point before explosion
};

export function KGHeroVisualization({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const particlesRef = useRef<Particle[]>([]);
  const ripplesRef = useRef<Ripple[]>([]);
  const shockwavesRef = useRef<Shockwave[]>([]);
  const explosionParticlesRef = useRef<ExplosionParticle[]>([]);
  const infallingParticlesRef = useRef<{ x: number; y: number; angle: number; distance: number; speed: number; size: number; opacity: number }[]>([]);
  const animationRef = useRef<number>(0);
  const timeRef = useRef<number>(0);
  const bigBangStartTimeRef = useRef<number | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [grabbedNode, setGrabbedNode] = useState<Node | null>(null);
  const [connectedNodeIds, setConnectedNodeIds] = useState<Set<string>>(new Set());
  const [floatingTexts, setFloatingTexts] = useState<{ text: string; x: number; y: number; opacity: number; id: number }[]>([]);
  // bigBangPhase is used for internal tracking; setBigBangPhase updates it each frame
  const [_bigBangPhase, setBigBangPhase] = useState<BigBangPhase>('singularity');
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const lastMouseRef = useRef({ x: -1000, y: -1000 });
  const floatingTextIdRef = useRef(0);
  const starsRef = useRef<{ x: number; y: number; size: number; twinkleSpeed: number; twinklePhase: number }[]>([]);
  const singularityIntensityRef = useRef(0);
  const explosionParticlesSpawnedRef = useRef(false);
  const shockwavesSpawnedRef = useRef(0);
  const orbitCalibratedRef = useRef(false);

  // Initialize nodes with orbital properties and big bang starting positions
  useEffect(() => {
    const initNodes = () => {
      const centerX = dimensions.width / 2;
      const centerY = dimensions.height / 2;
      const maxOrbitRadius = Math.min(dimensions.width, dimensions.height) * 0.4;

      // Create orbital layers
      const orbitLayers = [
        { radius: maxOrbitRadius * 0.25, count: 4 },  // Inner orbit
        { radius: maxOrbitRadius * 0.5, count: 6 },   // Middle orbit
        { radius: maxOrbitRadius * 0.75, count: 6 },  // Outer orbit
        { radius: maxOrbitRadius * 1.0, count: 4 },   // Outermost orbit
      ];

      nodesRef.current = SAMPLE_NODES.map((node, i) => {
        // Determine which orbit layer this node belongs to
        let layerIndex = 0;
        let countSoFar = 0;
        for (let l = 0; l < orbitLayers.length; l++) {
          if (i < countSoFar + orbitLayers[l].count) {
            layerIndex = l;
            break;
          }
          countSoFar += orbitLayers[l].count;
          if (l === orbitLayers.length - 1) layerIndex = l;
        }

        const layer = orbitLayers[layerIndex];
        const positionInLayer = (i - countSoFar) / layer.count;
        const baseAngle = positionInLayer * Math.PI * 2 + (layerIndex * Math.PI / 4);

        // Randomize orbit parameters for organic feel
        const orbitRadius = layer.radius * (0.85 + Math.random() * 0.3);
        const orbitSpeed = (0.00006 + Math.random() * 0.00008) * (layerIndex % 2 === 0 ? 1 : -1);
        const orbitEccentricity = 0.1 + Math.random() * 0.3;
        const orbitTilt = Math.random() * Math.PI * 2;

        // Target position on orbit (where node will end up after big bang)
        const initialAngle = baseAngle + Math.random() * 0.5;
        const targetX = centerX + Math.cos(initialAngle) * orbitRadius * (1 + orbitEccentricity * Math.cos(orbitTilt));
        const targetY = centerY + Math.sin(initialAngle) * orbitRadius * (1 - orbitEccentricity * 0.5);

        // Big bang explosion properties
        const explosionAngle = Math.atan2(targetY - centerY, targetX - centerX) + (Math.random() - 0.5) * 0.3;
        const explosionSpeed = 8 + Math.random() * 6 + layerIndex * 2; // Outer layers faster

        return {
          ...node,
          baseRadius: node.radius,
          // Start at center for big bang
          x: centerX,
          y: centerY,
          vx: 0,
          vy: 0,
          pulsePhase: Math.random() * Math.PI * 2,
          depth: 0.3 + Math.random() * 0.7,
          birthTime: BIG_BANG_TIMING.explosion.start + i * 30, // Staggered explosion
          orbitRadius,
          orbitSpeed,
          orbitAngle: initialAngle,
          orbitCenterX: centerX + (Math.random() - 0.5) * 20,
          orbitCenterY: centerY + (Math.random() - 0.5) * 20,
          orbitEccentricity,
          orbitTilt,
          rotationAngle: Math.random() * Math.PI * 2,
          flarePhase: Math.random() * Math.PI * 2,
          explosionAngle,
          explosionSpeed,
          targetX,
          targetY,
        };
      });

      edgesRef.current = SAMPLE_EDGES.map((edge) => ({
        ...edge,
        flowOffset: Math.random() * 100,
        flowSpeed: 0.1 + Math.random() * 0.2,
      }));

      // Reset big bang state
      bigBangStartTimeRef.current = null;
      setBigBangPhase('singularity');
      singularityIntensityRef.current = 0;
      shockwavesRef.current = [];
      explosionParticlesRef.current = [];
      infallingParticlesRef.current = [];
      explosionParticlesSpawnedRef.current = false;
      shockwavesSpawnedRef.current = 0;
      orbitCalibratedRef.current = false;
    };

    initNodes();
  }, [dimensions]);

  // Handle resize and initialize stars
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current?.parentElement) {
        const { clientWidth, clientHeight } = canvasRef.current.parentElement;
        setDimensions({ width: clientWidth, height: clientHeight });

        // Initialize background stars
        starsRef.current = Array.from({ length: 80 }, () => ({
          x: Math.random() * clientWidth,
          y: Math.random() * clientHeight,
          size: 0.3 + Math.random() * 1.2,
          twinkleSpeed: 0.01 + Math.random() * 0.03,
          twinklePhase: Math.random() * Math.PI * 2,
        }));
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Spawn floating Greek text periodically - SLOWER & LESS FREQUENT
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const text = FLOATING_TEXTS[Math.floor(Math.random() * FLOATING_TEXTS.length)];
        const id = floatingTextIdRef.current++;
        setFloatingTexts(prev => [...prev, {
          text,
          x: 10 + Math.random() * 80,
          y: 100 + Math.random() * 20,
          opacity: 0,
          id
        }]);

        // Remove after animation
        setTimeout(() => {
          setFloatingTexts(prev => prev.filter(t => t.id !== id));
        }, 20000);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Mouse tracking with ripple effect
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const newX = e.clientX - rect.left;
      const newY = e.clientY - rect.top;

      // Create ripple on significant movement (only when not grabbing)
      if (!grabbedNode) {
        const dx = newX - lastMouseRef.current.x;
        const dy = newY - lastMouseRef.current.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 50) {
          ripplesRef.current.push({
            x: newX,
            y: newY,
            radius: 0,
            maxRadius: 100 + Math.random() * 50,
            opacity: 0.3,
          });
          lastMouseRef.current = { x: newX, y: newY };
        }
      }

      mouseRef.current = { x: newX, y: newY };
    }
  }, [grabbedNode]);

  // Handle mouse down - grab node and select it
  const handleMouseDown = useCallback((_e: React.MouseEvent<HTMLCanvasElement>) => {
    if (canvasRef.current) {
      if (hoveredNode) {
        setGrabbedNode(hoveredNode);

        // Toggle selection or select new node
        if (selectedNode?.id === hoveredNode.id) {
          // Clicking same node - deselect
          setSelectedNode(null);
          setConnectedNodeIds(new Set());
        } else {
          // Select new node
          setSelectedNode(hoveredNode);

          // Find all connected nodes
          const connected = new Set<string>();
          edgesRef.current.forEach(edge => {
            if (edge.source === hoveredNode.id) {
              connected.add(edge.target);
            } else if (edge.target === hoveredNode.id) {
              connected.add(edge.source);
            }
          });
          setConnectedNodeIds(connected);
        }
      } else {
        // Clicking empty space - deselect
        setSelectedNode(null);
        setConnectedNodeIds(new Set());
      }
    }
  }, [hoveredNode, selectedNode]);

  // Handle mouse up - release grab (but keep selection)
  const handleMouseUp = useCallback(() => {
    setGrabbedNode(null);
    // Don't clear selection or connected nodes here
  }, []);

  // Spawn ambient light particles
  const spawnParticle = useCallback((x?: number, y?: number, forceType?: Particle['type']) => {
    const colors = ['#e0d4ff', '#c4b5fd', '#a5b4fc', '#93c5fd', '#6ee7b7', '#fcd34d', '#f0abfc'];
    const types: Particle['type'][] = ['sparkle', 'star', 'flare', 'dust'];
    const type = forceType ?? types[Math.floor(Math.random() * types.length)];

    particlesRef.current.push({
      x: x ?? Math.random() * dimensions.width,
      y: y ?? Math.random() * dimensions.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3 - 0.1,
      size: type === 'dust' ? 0.2 + Math.random() * 0.4 : 0.4 + Math.random() * 0.8,
      opacity: type === 'flare' ? 0.4 + Math.random() * 0.3 : 0.2 + Math.random() * 0.4,
      color: colors[Math.floor(Math.random() * colors.length)],
      life: 0,
      maxLife: 300 + Math.random() * 500,
      type,
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.02,
      twinklePhase: Math.random() * Math.PI * 2,
      twinkleSpeed: 0.05 + Math.random() * 0.1,
    });
  }, [dimensions]);

  // Draw a light sparkle/star shape - SMALL
  const drawSparkle = useCallback((ctx: CanvasRenderingContext2D, x: number, y: number, size: number, rotation: number, alpha: number, color: string) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotation);
    ctx.globalAlpha = alpha;

    // Create gradient for glow
    const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, size * 1.5);
    gradient.addColorStop(0, '#ffffff');
    gradient.addColorStop(0.2, color);
    gradient.addColorStop(0.6, color.replace(')', ', 0.2)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, 'transparent');

    // Draw soft glow
    ctx.beginPath();
    ctx.arc(0, 0, size * 1.5, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw 4-point star rays - thin and delicate
    ctx.beginPath();
    const rayLength = size * 2.5;

    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI) / 2;
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(angle) * rayLength, Math.sin(angle) * rayLength);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 0.5;
    ctx.shadowColor = color;
    ctx.shadowBlur = size;
    ctx.stroke();

    // Bright center dot
    ctx.beginPath();
    ctx.arc(0, 0, size * 0.3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    ctx.restore();
  }, []);

  // Draw a 6-point star - SMALL
  const drawStar = useCallback((ctx: CanvasRenderingContext2D, x: number, y: number, size: number, rotation: number, alpha: number, color: string) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotation);
    ctx.globalAlpha = alpha;

    // Soft glow
    const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, size * 2);
    gradient.addColorStop(0, '#ffffff');
    gradient.addColorStop(0.3, color);
    gradient.addColorStop(0.7, color.replace(')', ', 0.15)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, 'transparent');

    ctx.beginPath();
    ctx.arc(0, 0, size * 2, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // 6-point star rays as lines
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (i * Math.PI) / 3;
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(angle) * size * 1.8, Math.sin(angle) * size * 1.8);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 0.4;
    ctx.shadowColor = color;
    ctx.shadowBlur = size;
    ctx.stroke();

    // Bright center
    ctx.beginPath();
    ctx.arc(0, 0, size * 0.25, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    ctx.restore();
  }, []);

  // Draw a lens flare - SMALL
  const drawFlare = useCallback((ctx: CanvasRenderingContext2D, x: number, y: number, size: number, alpha: number, color: string) => {
    ctx.save();
    ctx.globalAlpha = alpha;

    // Main flare gradient - smaller
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 2);
    gradient.addColorStop(0, '#ffffff');
    gradient.addColorStop(0.2, color);
    gradient.addColorStop(0.5, color.replace(')', ', 0.3)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, 'transparent');

    ctx.beginPath();
    ctx.arc(x, y, size * 2, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Horizontal lens streak - shorter
    const streakGradient = ctx.createLinearGradient(x - size * 3, y, x + size * 3, y);
    streakGradient.addColorStop(0, 'transparent');
    streakGradient.addColorStop(0.3, color.replace(')', ', 0.2)').replace('rgb', 'rgba'));
    streakGradient.addColorStop(0.5, color.replace(')', ', 0.4)').replace('rgb', 'rgba'));
    streakGradient.addColorStop(0.7, color.replace(')', ', 0.2)').replace('rgb', 'rgba'));
    streakGradient.addColorStop(1, 'transparent');

    ctx.fillStyle = streakGradient;
    ctx.fillRect(x - size * 3, y - size * 0.15, size * 6, size * 0.3);

    ctx.restore();
  }, []);

  // ==================== CELESTIAL BODY DRAWING FUNCTIONS ====================

  // Draw a SUN - radiant with corona and solar flares
  const drawSunNode = useCallback((
    ctx: CanvasRenderingContext2D,
    node: Node,
    scale: number,
    time: number,
    isHighlighted: boolean
  ) => {
    const { x, y, radius, color, coreColor, glowColor, flarePhase, rotationAngle } = node;
    const r = radius * scale;
    const intensity = isHighlighted ? 1.5 : 1;

    ctx.save();

    // Outer corona - large soft glow
    const coronaRadius = r * 6 * intensity;
    const corona = ctx.createRadialGradient(x, y, r * 0.5, x, y, coronaRadius);
    corona.addColorStop(0, glowColor.replace('0.8', '0.6'));
    corona.addColorStop(0.2, glowColor.replace('0.8', '0.3'));
    corona.addColorStop(0.5, glowColor.replace('0.8', '0.1'));
    corona.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, coronaRadius, 0, Math.PI * 2);
    ctx.fillStyle = corona;
    ctx.fill();

    // Solar flares/prominences - animated wavy rays
    const flareCount = 12;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotationAngle + time * 0.00003);

    for (let i = 0; i < flareCount; i++) {
      const angle = (i / flareCount) * Math.PI * 2;
      const flareLength = r * (2 + Math.sin(flarePhase + i * 0.7 + time * 0.001) * 0.8) * intensity;
      const flareWidth = r * 0.3;

      ctx.save();
      ctx.rotate(angle);

      // Create tapered flare
      const flareGrad = ctx.createLinearGradient(r * 0.8, 0, r * 0.8 + flareLength, 0);
      flareGrad.addColorStop(0, color);
      flareGrad.addColorStop(0.3, glowColor.replace('0.8', '0.5'));
      flareGrad.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.moveTo(r * 0.8, -flareWidth * 0.5);
      ctx.quadraticCurveTo(r * 0.8 + flareLength * 0.5, -flareWidth * 0.3 + Math.sin(time * 0.002 + i) * 3, r * 0.8 + flareLength, 0);
      ctx.quadraticCurveTo(r * 0.8 + flareLength * 0.5, flareWidth * 0.3 + Math.sin(time * 0.002 + i + 1) * 3, r * 0.8, flareWidth * 0.5);
      ctx.closePath();
      ctx.fillStyle = flareGrad;
      ctx.fill();

      ctx.restore();
    }
    ctx.restore();

    // Middle glow layer
    const midGlow = ctx.createRadialGradient(x, y, 0, x, y, r * 2.5);
    midGlow.addColorStop(0, coreColor);
    midGlow.addColorStop(0.3, color);
    midGlow.addColorStop(0.7, glowColor.replace('0.8', '0.4'));
    midGlow.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, r * 2.5, 0, Math.PI * 2);
    ctx.fillStyle = midGlow;
    ctx.fill();

    // Core with limb darkening effect (edges darker than center)
    const coreGrad = ctx.createRadialGradient(x - r * 0.2, y - r * 0.2, 0, x, y, r);
    coreGrad.addColorStop(0, '#ffffff');
    coreGrad.addColorStop(0.2, coreColor);
    coreGrad.addColorStop(0.6, color);
    coreGrad.addColorStop(0.9, color.replace(')', ', 0.9)').replace('#', 'rgba(').replace(/[a-f0-9]{6}/i, (m) => {
      const r = parseInt(m.slice(0,2), 16);
      const g = parseInt(m.slice(2,4), 16);
      const b = parseInt(m.slice(4,6), 16);
      return `${r * 0.7}, ${g * 0.7}, ${b * 0.7}`;
    }));
    coreGrad.addColorStop(1, glowColor.replace('0.8', '0.6'));

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.shadowColor = color;
    ctx.shadowBlur = r * 2 * intensity;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Surface granulation (subtle spots)
    ctx.globalAlpha = 0.15;
    for (let i = 0; i < 5; i++) {
      const spotAngle = (i / 5) * Math.PI * 2 + time * 0.0001;
      const spotDist = r * 0.4 * (0.5 + Math.sin(spotAngle * 3) * 0.3);
      const spotX = x + Math.cos(spotAngle) * spotDist;
      const spotY = y + Math.sin(spotAngle) * spotDist;
      const spotR = r * 0.15;

      const spotGrad = ctx.createRadialGradient(spotX, spotY, 0, spotX, spotY, spotR);
      spotGrad.addColorStop(0, 'rgba(0,0,0,0.3)');
      spotGrad.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(spotX, spotY, spotR, 0, Math.PI * 2);
      ctx.fillStyle = spotGrad;
      ctx.fill();
    }

    ctx.restore();
  }, []);

  // Draw a PLANET - solid with atmosphere and 3D shading
  const drawPlanetNode = useCallback((
    ctx: CanvasRenderingContext2D,
    node: Node,
    scale: number,
    time: number,
    isHighlighted: boolean
  ) => {
    const { x, y, radius, color, coreColor, glowColor } = node;
    const r = radius * scale;
    const intensity = isHighlighted ? 1.4 : 1;

    ctx.save();

    // Outer atmospheric glow
    const atmosRadius = r * 3 * intensity;
    const atmos = ctx.createRadialGradient(x, y, r, x, y, atmosRadius);
    atmos.addColorStop(0, glowColor.replace('0.8', '0.5'));
    atmos.addColorStop(0.3, glowColor.replace('0.8', '0.2'));
    atmos.addColorStop(0.6, glowColor.replace('0.8', '0.05'));
    atmos.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, atmosRadius, 0, Math.PI * 2);
    ctx.fillStyle = atmos;
    ctx.fill();

    // Atmospheric rim light (thin bright edge)
    ctx.beginPath();
    ctx.arc(x, y, r * 1.15, 0, Math.PI * 2);
    ctx.strokeStyle = glowColor.replace('0.8', `${0.4 * intensity}`);
    ctx.lineWidth = r * 0.1;
    ctx.shadowColor = color;
    ctx.shadowBlur = r * intensity;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Planet body with 3D shading
    const lightAngle = -Math.PI / 4; // Light from top-left
    const lightX = x + Math.cos(lightAngle) * r * 0.4;
    const lightY = y + Math.sin(lightAngle) * r * 0.4;

    const planetGrad = ctx.createRadialGradient(lightX, lightY, 0, x, y, r * 1.2);
    planetGrad.addColorStop(0, coreColor);
    planetGrad.addColorStop(0.3, color);
    planetGrad.addColorStop(0.7, color.replace(')', ', 0.9)').replace('#', 'rgba(').replace(/[a-f0-9]{6}/i, (m) => {
      const r = parseInt(m.slice(0,2), 16);
      const g = parseInt(m.slice(2,4), 16);
      const b = parseInt(m.slice(4,6), 16);
      return `${r * 0.6}, ${g * 0.6}, ${b * 0.6}`;
    }));
    planetGrad.addColorStop(1, 'rgba(0,0,0,0.8)');

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = planetGrad;
    ctx.fill();

    // Surface bands (like Jupiter/Saturn) - subtle horizontal stripes
    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.clip();

    ctx.globalAlpha = 0.15;
    const bandCount = 4;
    for (let i = 0; i < bandCount; i++) {
      const bandY = y - r + (i + 0.5) * (r * 2 / bandCount);
      const bandHeight = r * 0.15;
      const waveOffset = Math.sin(time * 0.0002 + i) * 2;

      ctx.beginPath();
      ctx.moveTo(x - r, bandY + waveOffset);
      ctx.quadraticCurveTo(x, bandY - bandHeight * 0.5, x + r, bandY + waveOffset);
      ctx.lineTo(x + r, bandY + bandHeight + waveOffset);
      ctx.quadraticCurveTo(x, bandY + bandHeight * 1.5, x - r, bandY + bandHeight + waveOffset);
      ctx.closePath();
      ctx.fillStyle = i % 2 === 0 ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.2)';
      ctx.fill();
    }
    ctx.restore();

    // Specular highlight (shiny spot)
    const specX = x - r * 0.35;
    const specY = y - r * 0.35;
    const specGrad = ctx.createRadialGradient(specX, specY, 0, specX, specY, r * 0.4);
    specGrad.addColorStop(0, 'rgba(255,255,255,0.6)');
    specGrad.addColorStop(0.5, 'rgba(255,255,255,0.1)');
    specGrad.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(specX, specY, r * 0.4, 0, Math.PI * 2);
    ctx.fillStyle = specGrad;
    ctx.fill();

    // Terminator shadow gradient (day/night line)
    const shadowGrad = ctx.createLinearGradient(x - r, y, x + r, y);
    shadowGrad.addColorStop(0, 'transparent');
    shadowGrad.addColorStop(0.6, 'transparent');
    shadowGrad.addColorStop(0.8, 'rgba(0,0,0,0.3)');
    shadowGrad.addColorStop(1, 'rgba(0,0,0,0.5)');
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = shadowGrad;
    ctx.fill();

    ctx.restore();
  }, []);

  // Draw a NEBULA STAR - ethereal with diffraction spikes
  const drawNebulaStarNode = useCallback((
    ctx: CanvasRenderingContext2D,
    node: Node,
    scale: number,
    time: number,
    isHighlighted: boolean
  ) => {
    const { x, y, radius, color, coreColor, glowColor, rotationAngle, pulsePhase } = node;
    const r = radius * scale;
    const intensity = isHighlighted ? 1.5 : 1;
    const pulse = 1 + Math.sin(pulsePhase + time * 0.001) * 0.1;

    ctx.save();

    // Large nebula-like glow
    const nebulaRadius = r * 5 * intensity * pulse;
    const nebula = ctx.createRadialGradient(x, y, 0, x, y, nebulaRadius);
    nebula.addColorStop(0, glowColor.replace('0.8', '0.7'));
    nebula.addColorStop(0.15, glowColor.replace('0.8', '0.4'));
    nebula.addColorStop(0.4, glowColor.replace('0.8', '0.15'));
    nebula.addColorStop(0.7, glowColor.replace('0.8', '0.05'));
    nebula.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, nebulaRadius, 0, Math.PI * 2);
    ctx.fillStyle = nebula;
    ctx.fill();

    // Diffraction spikes (4-point star pattern like telescope images)
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rotationAngle + time * 0.00002);

    const spikeLength = r * 4 * intensity * pulse;
    const spikeWidth = r * 0.15;

    for (let i = 0; i < 4; i++) {
      ctx.save();
      ctx.rotate((i / 4) * Math.PI * 2);

      // Main spike
      const spikeGrad = ctx.createLinearGradient(0, 0, spikeLength, 0);
      spikeGrad.addColorStop(0, coreColor);
      spikeGrad.addColorStop(0.1, color);
      spikeGrad.addColorStop(0.4, glowColor.replace('0.8', '0.3'));
      spikeGrad.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(spikeLength, -spikeWidth * 0.1);
      ctx.lineTo(spikeLength, spikeWidth * 0.1);
      ctx.closePath();
      ctx.fillStyle = spikeGrad;
      ctx.fill();

      // Secondary shorter spike (offset)
      ctx.rotate(Math.PI / 8);
      const shortSpike = spikeLength * 0.4;
      ctx.globalAlpha = 0.5;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(shortSpike, -spikeWidth * 0.05);
      ctx.lineTo(shortSpike, spikeWidth * 0.05);
      ctx.closePath();
      ctx.fillStyle = spikeGrad;
      ctx.fill();

      ctx.restore();
    }
    ctx.restore();

    // Inner glow
    const innerGlow = ctx.createRadialGradient(x, y, 0, x, y, r * 2);
    innerGlow.addColorStop(0, '#ffffff');
    innerGlow.addColorStop(0.2, coreColor);
    innerGlow.addColorStop(0.5, color);
    innerGlow.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, r * 2, 0, Math.PI * 2);
    ctx.fillStyle = innerGlow;
    ctx.fill();

    // Bright core
    const coreGrad = ctx.createRadialGradient(x, y, 0, x, y, r * 0.8);
    coreGrad.addColorStop(0, '#ffffff');
    coreGrad.addColorStop(0.5, coreColor);
    coreGrad.addColorStop(1, color);
    ctx.beginPath();
    ctx.arc(x, y, r * 0.8, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.shadowColor = '#ffffff';
    ctx.shadowBlur = r * 2 * intensity;
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.restore();
  }, []);

  // Draw a PULSAR - energetic with rotating beams
  const drawPulsarNode = useCallback((
    ctx: CanvasRenderingContext2D,
    node: Node,
    scale: number,
    time: number,
    isHighlighted: boolean
  ) => {
    const { x, y, radius, color, coreColor, glowColor, flarePhase } = node;
    const r = radius * scale;
    const intensity = isHighlighted ? 1.5 : 1;

    ctx.save();

    // Outer energy field
    const fieldRadius = r * 4 * intensity;
    const field = ctx.createRadialGradient(x, y, r * 0.5, x, y, fieldRadius);
    field.addColorStop(0, glowColor.replace('0.8', '0.5'));
    field.addColorStop(0.3, glowColor.replace('0.8', '0.2'));
    field.addColorStop(0.6, glowColor.replace('0.8', '0.05'));
    field.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(x, y, fieldRadius, 0, Math.PI * 2);
    ctx.fillStyle = field;
    ctx.fill();

    // Pulsing ring waves
    ctx.globalAlpha = 0.3;
    for (let i = 0; i < 3; i++) {
      const ringPhase = (flarePhase + i * 0.7 + time * 0.002) % (Math.PI * 2);
      const ringRadius = r * (1.5 + ringPhase * 0.8);
      const ringAlpha = Math.max(0, 1 - ringPhase / (Math.PI * 2)) * 0.4;

      ctx.beginPath();
      ctx.arc(x, y, ringRadius, 0, Math.PI * 2);
      ctx.strokeStyle = glowColor.replace('0.8', `${ringAlpha}`);
      ctx.lineWidth = r * 0.1 * (1 - ringPhase / (Math.PI * 2));
      ctx.stroke();
    }

    // Core with internal energy
    ctx.globalAlpha = 1;
    const coreGrad = ctx.createRadialGradient(x, y, 0, x, y, r);
    coreGrad.addColorStop(0, '#ffffff');
    coreGrad.addColorStop(0.3, coreColor);
    coreGrad.addColorStop(0.7, color);
    coreGrad.addColorStop(1, glowColor.replace('0.8', '0.8'));

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = coreGrad;
    ctx.shadowColor = color;
    ctx.shadowBlur = r * 2 * intensity;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Bright center point
    ctx.beginPath();
    ctx.arc(x, y, r * 0.3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    ctx.restore();
  }, []);

  // ==================== BIG BANG DRAWING FUNCTIONS ====================

  // Draw the singularity - dramatic multi-phase build-up before explosion
  const drawSingularity = useCallback((
    ctx: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    progress: number, // 0-1 progress through singularity phase
    time: number,
    maxRadius: number
  ) => {
    ctx.save();

    // Determine which sub-phase we're in
    const inBlackHole = progress >= SINGULARITY_PHASES.blackHole.start && progress < SINGULARITY_PHASES.blackHole.end;
    const inCompression = progress >= SINGULARITY_PHASES.compression.start && progress < SINGULARITY_PHASES.compression.end;
    const inSingularity = progress >= SINGULARITY_PHASES.singularity.start;

    // Calculate sub-phase progress (0-1 within each phase)
    const getSubProgress = (phase: { start: number; end: number }) => {
      if (progress < phase.start) return 0;
      if (progress > phase.end) return 1;
      return (progress - phase.start) / (phase.end - phase.start);
    };

    // Very subtle, slow pulsing - much less dramatic
    const pulseSpeed = 0.002; // Very slow
    const pulseIntensity = 0.03; // Very subtle
    const pulse = 1 + Math.sin(time * pulseSpeed) * pulseIntensity;

    // === INFALLING PARTICLES - Matter being pulled toward the black hole ===
    // Spawn new particles (more during compression)
    const spawnRate = inBlackHole ? 0.03 : inCompression ? 0.15 : 0;
    if (Math.random() < spawnRate && !inSingularity) {
      const angle = Math.random() * Math.PI * 2;
      const distance = maxRadius * (1.2 + Math.random() * 0.5); // Start from outside
      infallingParticlesRef.current.push({
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance,
        angle,
        distance,
        speed: 0.3 + Math.random() * 0.5,
        size: 1 + Math.random() * 2,
        opacity: 0.3 + Math.random() * 0.4,
      });
    }

    // Update and draw infalling particles
    const compressionSpeed = inCompression ? 1 + getSubProgress(SINGULARITY_PHASES.compression) * 2 : 1;
    infallingParticlesRef.current = infallingParticlesRef.current.filter((p) => {
      // Move toward center with acceleration
      p.distance -= p.speed * compressionSpeed;
      p.speed += 0.02 * compressionSpeed; // Accelerate as they fall in

      // Slight spiral effect
      p.angle += 0.002;

      // Update position
      p.x = centerX + Math.cos(p.angle) * p.distance;
      p.y = centerY + Math.sin(p.angle) * p.distance;

      // Fade in as they approach
      if (p.distance < maxRadius * 0.8) {
        p.opacity = Math.min(0.8, p.opacity + 0.01);
      }

      // Draw the particle with a small trail
      if (p.distance > 5) {
        // Trail
        const trailLength = Math.min(30, p.speed * 15);
        const trailEndX = p.x + Math.cos(p.angle + Math.PI) * trailLength;
        const trailEndY = p.y + Math.sin(p.angle + Math.PI) * trailLength;

        const trailGrad = ctx.createLinearGradient(p.x, p.y, trailEndX, trailEndY);
        trailGrad.addColorStop(0, `rgba(255, 200, 100, ${p.opacity})`);
        trailGrad.addColorStop(1, 'transparent');

        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(trailEndX, trailEndY);
        ctx.strokeStyle = trailGrad;
        ctx.lineWidth = p.size;
        ctx.stroke();

        // Particle head
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 220, 150, ${p.opacity})`;
        ctx.fill();
      }

      // Remove if reached center
      return p.distance > 5;
    });

    // Clear particles when entering singularity phase
    if (inSingularity && infallingParticlesRef.current.length > 0) {
      // Rapidly absorb remaining particles
      infallingParticlesRef.current = infallingParticlesRef.current.filter((p) => {
        p.distance -= p.speed * 5;
        p.opacity *= 0.9;
        return p.distance > 3 && p.opacity > 0.05;
      });
    }

    // === PHASE 1: BLACK HOLE - Gentle rotation from the start ===
    if (inBlackHole) {
      const bhProgress = getSubProgress(SINGULARITY_PHASES.blackHole);

      // Quick fade in (first 15% of phase), then stable
      const fadeIn = Math.min(1, bhProgress * 6.5);

      const eventHorizonRadius = maxRadius * 0.4 * fadeIn * pulse;
      const photonSphereRadius = eventHorizonRadius * 1.5;
      const accretionDiskOuterRadius = eventHorizonRadius * 3.5;
      const accretionDiskInnerRadius = eventHorizonRadius * 1.2;

      // Outer glow - gravitational lensing effect
      const outerGlow = ctx.createRadialGradient(centerX, centerY, accretionDiskOuterRadius * 0.8, centerX, centerY, accretionDiskOuterRadius * 1.5);
      outerGlow.addColorStop(0, `rgba(80, 60, 120, ${0.15 * fadeIn})`);
      outerGlow.addColorStop(0.5, `rgba(40, 30, 80, ${0.08 * fadeIn})`);
      outerGlow.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(centerX, centerY, accretionDiskOuterRadius * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = outerGlow;
      ctx.fill();

      // Accretion disk - constant gentle rotation speed
      ctx.save();
      ctx.translate(centerX, centerY);

      // Constant gentle rotation - no acceleration
      const diskRotation = time * 0.0002;
      ctx.rotate(diskRotation);

      const diskTilt = 0.3;
      ctx.scale(1, diskTilt);

      // Outer accretion disk glow
      const diskGrad = ctx.createRadialGradient(0, 0, accretionDiskInnerRadius, 0, 0, accretionDiskOuterRadius);
      diskGrad.addColorStop(0, `rgba(255, 150, 50, ${0.6 * fadeIn})`);
      diskGrad.addColorStop(0.3, `rgba(255, 100, 30, ${0.4 * fadeIn})`);
      diskGrad.addColorStop(0.6, `rgba(200, 60, 20, ${0.2 * fadeIn})`);
      diskGrad.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.arc(0, 0, accretionDiskOuterRadius, 0, Math.PI * 2);
      ctx.fillStyle = diskGrad;
      ctx.fill();

      // Inner hot ring (photon sphere glow)
      const innerRingGrad = ctx.createRadialGradient(0, 0, eventHorizonRadius, 0, 0, photonSphereRadius);
      innerRingGrad.addColorStop(0, 'transparent');
      innerRingGrad.addColorStop(0.5, `rgba(255, 200, 100, ${0.7 * fadeIn})`);
      innerRingGrad.addColorStop(0.8, `rgba(255, 255, 200, ${0.9 * fadeIn})`);
      innerRingGrad.addColorStop(1, `rgba(255, 180, 80, ${0.3 * fadeIn})`);

      ctx.beginPath();
      ctx.arc(0, 0, photonSphereRadius, 0, Math.PI * 2);
      ctx.fillStyle = innerRingGrad;
      ctx.fill();

      ctx.restore();

      // The event horizon - pure black center
      const eventHorizonGrad = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, eventHorizonRadius);
      eventHorizonGrad.addColorStop(0, `rgba(0, 0, 0, ${fadeIn})`);
      eventHorizonGrad.addColorStop(0.7, `rgba(0, 0, 0, ${fadeIn})`);
      eventHorizonGrad.addColorStop(0.9, `rgba(5, 5, 10, ${0.9 * fadeIn})`);
      eventHorizonGrad.addColorStop(1, `rgba(20, 15, 30, ${0.5 * fadeIn})`);

      ctx.beginPath();
      ctx.arc(centerX, centerY, eventHorizonRadius, 0, Math.PI * 2);
      ctx.fillStyle = eventHorizonGrad;
      ctx.fill();

      // Photon ring - bright ring at the edge
      ctx.beginPath();
      ctx.arc(centerX, centerY, eventHorizonRadius * 1.05, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(255, 220, 150, ${0.6 * fadeIn})`;
      ctx.lineWidth = 2;
      ctx.shadowColor = 'rgba(255, 200, 100, 0.8)';
      ctx.shadowBlur = 15;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // === PHASE 2: COMPRESSION - Everything gets pulled in and compressed ===
    if (inCompression) {
      const compProgress = getSubProgress(SINGULARITY_PHASES.compression);

      // Use easeInQuad for accelerating compression (slow start, fast end)
      const easeIn = compProgress * compProgress;

      // Shrink from full size toward near-zero
      const shrinkFactor = 1 - easeIn * 0.95;
      const eventHorizonRadius = Math.max(3, maxRadius * 0.4 * shrinkFactor);
      const photonSphereRadius = eventHorizonRadius * 1.5;
      const accretionDiskOuterRadius = eventHorizonRadius * 3;

      // Accretion disk - SAME rotation speed, just shrinking
      ctx.save();
      ctx.translate(centerX, centerY);
      const diskRotation = time * 0.0002; // Same constant speed as black hole phase
      ctx.rotate(diskRotation);

      // Disk gets absorbed - shrinks and fades
      const diskOpacity = 1 - easeIn * 0.8;
      const diskTilt = 0.3 * (1 - easeIn * 0.7);
      ctx.scale(1, Math.max(0.1, diskTilt));

      const diskGrad = ctx.createRadialGradient(0, 0, eventHorizonRadius * 0.5, 0, 0, accretionDiskOuterRadius);
      diskGrad.addColorStop(0, `rgba(255, 200, 100, ${0.6 * diskOpacity})`);
      diskGrad.addColorStop(0.4, `rgba(255, 150, 50, ${0.4 * diskOpacity})`);
      diskGrad.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.arc(0, 0, accretionDiskOuterRadius, 0, Math.PI * 2);
      ctx.fillStyle = diskGrad;
      ctx.fill();

      // Inner photon ring - gets brighter as it compresses
      const ringBrightness = 0.7 + easeIn * 0.3;
      const innerRingGrad = ctx.createRadialGradient(0, 0, eventHorizonRadius * 0.8, 0, 0, photonSphereRadius);
      innerRingGrad.addColorStop(0, 'transparent');
      innerRingGrad.addColorStop(0.5, `rgba(255, 220, 150, ${ringBrightness})`);
      innerRingGrad.addColorStop(0.8, `rgba(255, 255, 220, ${ringBrightness})`);
      innerRingGrad.addColorStop(1, `rgba(255, 200, 100, ${ringBrightness * 0.5})`);

      ctx.beginPath();
      ctx.arc(0, 0, photonSphereRadius, 0, Math.PI * 2);
      ctx.fillStyle = innerRingGrad;
      ctx.fill();

      ctx.restore();

      // Event horizon - dark center, shrinking
      const eventHorizonGrad = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, eventHorizonRadius);
      eventHorizonGrad.addColorStop(0, 'rgba(0, 0, 0, 1)');
      eventHorizonGrad.addColorStop(0.7, 'rgba(0, 0, 0, 1)');
      eventHorizonGrad.addColorStop(1, 'rgba(20, 15, 30, 0.7)');

      ctx.beginPath();
      ctx.arc(centerX, centerY, eventHorizonRadius, 0, Math.PI * 2);
      ctx.fillStyle = eventHorizonGrad;
      ctx.fill();

      // Photon ring - bright edge getting more intense
      const ringIntensity = 0.6 + easeIn * 0.4;
      ctx.beginPath();
      ctx.arc(centerX, centerY, eventHorizonRadius * 1.05, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(255, 240, 200, ${ringIntensity})`;
      ctx.lineWidth = Math.max(1, 2 - easeIn);
      ctx.shadowColor = `rgba(255, 220, 150, ${ringIntensity})`;
      ctx.shadowBlur = 15 + easeIn * 10;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // === PHASE 3: SINGULARITY - Infinitely small bright point ===
    if (inSingularity) {
      const singProgress = getSubProgress(SINGULARITY_PHASES.singularity);

      // Tiny point that gets smaller and brighter
      const pointRadius = Math.max(2, maxRadius * 0.02 * (1 - singProgress * 0.5));
      const intensity = 0.8 + singProgress * 0.2;

      // Outer glow - concentrated energy
      const glowRadius = pointRadius * (4 - singProgress * 2);
      const glow = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, glowRadius);
      glow.addColorStop(0, `rgba(255, 255, 255, ${intensity})`);
      glow.addColorStop(0.3, `rgba(255, 250, 230, ${intensity * 0.7})`);
      glow.addColorStop(0.6, `rgba(255, 220, 180, ${intensity * 0.3})`);
      glow.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.arc(centerX, centerY, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.shadowColor = '#ffffff';
      ctx.shadowBlur = 20 + singProgress * 20;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Bright white core - the singularity
      ctx.beginPath();
      ctx.arc(centerX, centerY, pointRadius, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = '#ffffff';
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    ctx.restore();
  }, []);

  // Draw explosion flash
  const drawExplosionFlash = useCallback((
    ctx: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    progress: number, // 0-1
    maxRadius: number
  ) => {
    ctx.save();

    // Bright flash that fades
    const flashIntensity = Math.max(0, 1 - progress * 1.5);
    if (flashIntensity > 0) {
      const flashRadius = maxRadius * (0.3 + progress * 0.7);
      const flash = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, flashRadius);
      flash.addColorStop(0, `rgba(255, 255, 255, ${flashIntensity})`);
      flash.addColorStop(0.2, `rgba(255, 240, 220, ${flashIntensity * 0.8})`);
      flash.addColorStop(0.5, `rgba(255, 200, 150, ${flashIntensity * 0.4})`);
      flash.addColorStop(0.8, `rgba(200, 150, 255, ${flashIntensity * 0.2})`);
      flash.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(centerX, centerY, flashRadius, 0, Math.PI * 2);
      ctx.fillStyle = flash;
      ctx.fill();
    }

    ctx.restore();
  }, []);

  // Spawn explosion particles
  const spawnExplosionParticles = useCallback((centerX: number, centerY: number, count: number) => {
    const colors = ['#ffffff', '#e0d4ff', '#c4b5fd', '#a5b4fc', '#93c5fd', '#fbbf24', '#f472b6'];
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 3 + Math.random() * 8;
      explosionParticlesRef.current.push({
        x: centerX,
        y: centerY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 1 + Math.random() * 3,
        opacity: 0.8 + Math.random() * 0.2,
        color: colors[Math.floor(Math.random() * colors.length)],
        life: 0,
        maxLife: 80 + Math.random() * 120,
        trail: [],
      });
    }
  }, []);

  // Spawn shockwave
  const spawnShockwave = useCallback((centerX: number, centerY: number, color: string, maxRadius: number) => {
    shockwavesRef.current.push({
      x: centerX,
      y: centerY,
      radius: 0,
      maxRadius,
      opacity: 0.8,
      color,
      thickness: 4,
    });
  }, []);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let lastTime = performance.now();

    const animate = (currentTime: number) => {
      const deltaTime = currentTime - lastTime;
      lastTime = currentTime;
      timeRef.current += deltaTime;
      const time = timeRef.current;

      // Initialize big bang start time
      if (bigBangStartTimeRef.current === null) {
        bigBangStartTimeRef.current = time;
      }
      const bigBangTime = time - bigBangStartTimeRef.current;

      // Determine current phase
      let currentPhase: BigBangPhase = 'singularity';
      if (bigBangTime >= BIG_BANG_TIMING.orbit.start) {
        currentPhase = 'orbit';
      } else if (bigBangTime >= BIG_BANG_TIMING.settling.start) {
        currentPhase = 'settling';
      } else if (bigBangTime >= BIG_BANG_TIMING.expansion.start) {
        currentPhase = 'expansion';
      } else if (bigBangTime >= BIG_BANG_TIMING.explosion.start) {
        currentPhase = 'explosion';
      }
      setBigBangPhase(currentPhase);

      const centerX = dimensions.width / 2;
      const centerY = dimensions.height / 2;

      ctx.clearRect(0, 0, dimensions.width, dimensions.height);

      // === BACKGROUND LAYERS ===

      // Base gradient
      const baseGradient = ctx.createRadialGradient(
        dimensions.width * 0.3,
        dimensions.height * 0.3,
        0,
        dimensions.width * 0.5,
        dimensions.height * 0.5,
        dimensions.width
      );
      baseGradient.addColorStop(0, 'rgba(30, 27, 75, 1)');
      baseGradient.addColorStop(0.4, 'rgba(23, 23, 55, 1)');
      baseGradient.addColorStop(1, 'rgba(10, 10, 25, 1)');
      ctx.fillStyle = baseGradient;
      ctx.fillRect(0, 0, dimensions.width, dimensions.height);

      // Animated aurora/nebula effect - SLOW
      const auroraGradient1 = ctx.createRadialGradient(
        dimensions.width * (0.3 + Math.sin(time * 0.00005) * 0.1),
        dimensions.height * (0.4 + Math.cos(time * 0.00004) * 0.1),
        0,
        dimensions.width * 0.5,
        dimensions.height * 0.5,
        dimensions.width * 0.6
      );
      auroraGradient1.addColorStop(0, `rgba(139, 92, 246, ${0.08 + Math.sin(time * 0.0002) * 0.03})`);
      auroraGradient1.addColorStop(0.5, 'rgba(139, 92, 246, 0.02)');
      auroraGradient1.addColorStop(1, 'transparent');
      ctx.fillStyle = auroraGradient1;
      ctx.fillRect(0, 0, dimensions.width, dimensions.height);

      const auroraGradient2 = ctx.createRadialGradient(
        dimensions.width * (0.7 + Math.cos(time * 0.00004) * 0.15),
        dimensions.height * (0.6 + Math.sin(time * 0.00006) * 0.1),
        0,
        dimensions.width * 0.5,
        dimensions.height * 0.5,
        dimensions.width * 0.5
      );
      auroraGradient2.addColorStop(0, `rgba(59, 130, 246, ${0.06 + Math.cos(time * 0.00015) * 0.02})`);
      auroraGradient2.addColorStop(0.6, 'rgba(59, 130, 246, 0.01)');
      auroraGradient2.addColorStop(1, 'transparent');
      ctx.fillStyle = auroraGradient2;
      ctx.fillRect(0, 0, dimensions.width, dimensions.height);

      // === BACKGROUND STAR FIELD ===
      starsRef.current.forEach((star) => {
        star.twinklePhase += star.twinkleSpeed;
        const twinkle = 0.3 + 0.7 * Math.pow(Math.sin(star.twinklePhase), 2);
        const alpha = twinkle * 0.8;

        // Draw star with subtle glow
        ctx.save();
        ctx.globalAlpha = alpha;

        // Soft glow
        const starGlow = ctx.createRadialGradient(star.x, star.y, 0, star.x, star.y, star.size * 4);
        starGlow.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        starGlow.addColorStop(0.2, 'rgba(200, 200, 255, 0.3)');
        starGlow.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size * 4, 0, Math.PI * 2);
        ctx.fillStyle = starGlow;
        ctx.fill();

        // Bright core
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size * 0.5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        // Tiny cross rays for larger stars
        if (star.size > 0.8) {
          ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.5})`;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(star.x - star.size * 2, star.y);
          ctx.lineTo(star.x + star.size * 2, star.y);
          ctx.moveTo(star.x, star.y - star.size * 2);
          ctx.lineTo(star.x, star.y + star.size * 2);
          ctx.stroke();
        }

        ctx.restore();
      });

      // === BIG BANG EFFECTS ===

      // Singularity phase - draw pulsing central light
      if (currentPhase === 'singularity') {
        const singularityProgress = bigBangTime / BIG_BANG_TIMING.singularity.duration;
        singularityIntensityRef.current = Math.min(1, singularityProgress * 1.2);
        const maxSingularityRadius = Math.min(dimensions.width, dimensions.height) * 0.15;
        drawSingularity(ctx, centerX, centerY, singularityProgress, time, maxSingularityRadius);
      }

      // Explosion phase - spawn particles and shockwaves, draw flash
      if (currentPhase === 'explosion') {
        const explosionProgress = (bigBangTime - BIG_BANG_TIMING.explosion.start) / BIG_BANG_TIMING.explosion.duration;

        // Spawn explosion particles at start
        if (!explosionParticlesSpawnedRef.current) {
          spawnExplosionParticles(centerX, centerY, 100);
          explosionParticlesSpawnedRef.current = true;
        }

        // Spawn multiple shockwaves with delays
        const maxShockwaves = 4;
        const shockwaveInterval = 0.15; // 15% of explosion duration per shockwave
        while (shockwavesSpawnedRef.current < maxShockwaves && explosionProgress > shockwavesSpawnedRef.current * shockwaveInterval) {
          const colors = ['rgba(255, 255, 255, 0.8)', 'rgba(200, 180, 255, 0.6)', 'rgba(139, 92, 246, 0.5)', 'rgba(96, 165, 250, 0.4)'];
          const maxRadius = Math.min(dimensions.width, dimensions.height) * (0.6 + shockwavesSpawnedRef.current * 0.15);
          spawnShockwave(centerX, centerY, colors[shockwavesSpawnedRef.current], maxRadius);
          shockwavesSpawnedRef.current++;
        }

        // Draw explosion flash
        drawExplosionFlash(ctx, centerX, centerY, explosionProgress, Math.min(dimensions.width, dimensions.height) * 0.8);

        // Fading singularity (shrinks as explosion progresses)
        const fadingIntensity = Math.max(0, 1 - explosionProgress * 2);
        if (fadingIntensity > 0) {
          const fadingMaxRadius = Math.min(dimensions.width, dimensions.height) * 0.15 * fadingIntensity;
          drawSingularity(ctx, centerX, centerY, 1, time, fadingMaxRadius);
        }
      }

      // Draw and update shockwaves
      shockwavesRef.current = shockwavesRef.current.filter((sw) => {
        sw.radius += 8; // Expansion speed
        sw.opacity *= 0.97; // Fade out
        sw.thickness = Math.max(1, sw.thickness * 0.98);

        if (sw.opacity > 0.02 && sw.radius < sw.maxRadius) {
          ctx.beginPath();
          ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
          ctx.strokeStyle = sw.color.replace(/[\d.]+\)$/, `${sw.opacity})`);
          ctx.lineWidth = sw.thickness;
          ctx.shadowColor = sw.color;
          ctx.shadowBlur = 20 * sw.opacity;
          ctx.stroke();
          ctx.shadowBlur = 0;
          return true;
        }
        return false;
      });

      // Draw and update explosion particles with trails
      explosionParticlesRef.current = explosionParticlesRef.current.filter((p) => {
        p.life++;
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.98; // Slow down over time
        p.vy *= 0.98;

        // Add to trail
        p.trail.push({ x: p.x, y: p.y });
        if (p.trail.length > 8) p.trail.shift();

        const lifeRatio = p.life / p.maxLife;
        const alpha = p.opacity * (1 - lifeRatio);

        if (alpha > 0.01) {
          // Draw trail
          if (p.trail.length > 1) {
            ctx.beginPath();
            ctx.moveTo(p.trail[0].x, p.trail[0].y);
            for (let i = 1; i < p.trail.length; i++) {
              ctx.lineTo(p.trail[i].x, p.trail[i].y);
            }
            const trailGrad = ctx.createLinearGradient(
              p.trail[0].x, p.trail[0].y,
              p.trail[p.trail.length - 1].x, p.trail[p.trail.length - 1].y
            );
            trailGrad.addColorStop(0, 'transparent');
            trailGrad.addColorStop(1, p.color.replace(')', `, ${alpha * 0.5})`).replace('rgb', 'rgba').replace('#', 'rgba(').replace(/^rgba\(([a-f0-9]{6})/, (_, hex) => {
              const r = parseInt(hex.slice(0, 2), 16);
              const g = parseInt(hex.slice(2, 4), 16);
              const b = parseInt(hex.slice(4, 6), 16);
              return `rgba(${r}, ${g}, ${b}`;
            }));
            ctx.strokeStyle = p.color.replace(')', `, ${alpha * 0.3})`).replace('rgb', 'rgba');
            ctx.lineWidth = p.size * 0.5;
            ctx.stroke();
          }

          // Draw particle head
          const headGlow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
          headGlow.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
          headGlow.addColorStop(0.3, p.color.replace(')', `, ${alpha * 0.8})`).replace('rgb', 'rgba'));
          headGlow.addColorStop(1, 'transparent');
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
          ctx.fillStyle = headGlow;
          ctx.fill();

          return true;
        }
        return false;
      });

      // === LIGHT PARTICLES ===

      // Spawn new particles occasionally (only after explosion)
      if (currentPhase !== 'singularity' && Math.random() > 0.97) {
        spawnParticle();
      }

      // Update and draw particles as light effects
      particlesRef.current = particlesRef.current.filter((p) => {
        p.life += 0.4;
        p.x += p.vx * 0.25;
        p.y += p.vy * 0.25;
        p.vy -= 0.0002; // Gentle upward drift
        p.rotation += p.rotationSpeed;
        p.twinklePhase += p.twinkleSpeed;

        const lifeRatio = p.life / p.maxLife;
        const fadeIn = Math.min(p.life / 50, 1);
        const fadeOut = 1 - Math.pow(lifeRatio, 3);
        const twinkle = 0.7 + 0.3 * Math.sin(p.twinklePhase); // Twinkling effect
        const alpha = p.opacity * fadeIn * fadeOut * twinkle;

        if (alpha > 0.01) {
          switch (p.type) {
            case 'sparkle':
              drawSparkle(ctx, p.x, p.y, p.size, p.rotation, alpha, p.color);
              break;
            case 'star':
              drawStar(ctx, p.x, p.y, p.size * 0.8, p.rotation, alpha, p.color);
              break;
            case 'flare':
              drawFlare(ctx, p.x, p.y, p.size * 0.6, alpha * 0.7, p.color);
              break;
            case 'dust':
              // Tiny glowing dots for dust
              ctx.save();
              ctx.globalAlpha = alpha;
              const dustGradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2);
              dustGradient.addColorStop(0, '#ffffff');
              dustGradient.addColorStop(0.3, p.color);
              dustGradient.addColorStop(1, 'transparent');
              ctx.beginPath();
              ctx.arc(p.x, p.y, p.size * 2, 0, Math.PI * 2);
              ctx.fillStyle = dustGradient;
              ctx.fill();
              ctx.restore();
              break;
          }
        }

        return p.life < p.maxLife;
      });

      // === RIPPLES ===

      ripplesRef.current = ripplesRef.current.filter((r) => {
        r.radius += 0.8; // SLOWER ripple expansion
        r.opacity *= 0.985;

        if (r.opacity > 0.01) {
          ctx.beginPath();
          ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(167, 139, 250, ${r.opacity})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        return r.radius < r.maxRadius && r.opacity > 0.01;
      });

      // === NODES & EDGES ===

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      let newHovered: Node | null = null;

      // Update node positions based on current big bang phase
      nodes.forEach((node) => {
        // During singularity, keep all nodes at center and invisible
        if (currentPhase === 'singularity') {
          node.x = centerX;
          node.y = centerY;
          node.radius = 0;
          return;
        }

        // Check if this node has been "born" yet (staggered during explosion)
        const nodeBirthTime = bigBangStartTimeRef.current! + node.birthTime;
        if (time < nodeBirthTime) {
          node.x = centerX;
          node.y = centerY;
          node.radius = 0;
          return;
        }

        const timeSinceBirth = time - nodeBirthTime;
        const birthProgress = Math.min(timeSinceBirth / 800, 1); // 800ms birth animation
        const easeOut = 1 - Math.pow(1 - birthProgress, 3);

        // Pulsing radius
        node.pulsePhase += 0.005;
        node.rotationAngle += 0.0003;
        node.flarePhase += 0.008;
        const pulse = 1 + Math.sin(node.pulsePhase) * 0.06;
        node.radius = node.baseRadius * pulse * easeOut;

        // === BIG BANG MOVEMENT PHASES ===

        if (currentPhase === 'explosion' || currentPhase === 'expansion') {
          // Explosion phase: nodes fly outward from center
          const explosionPhaseProgress = (bigBangTime - BIG_BANG_TIMING.explosion.start) /
            (BIG_BANG_TIMING.settling.start - BIG_BANG_TIMING.explosion.start);

          // Initial explosion velocity (only apply once at birth)
          if (timeSinceBirth < 50) {
            node.vx = Math.cos(node.explosionAngle) * node.explosionSpeed;
            node.vy = Math.sin(node.explosionAngle) * node.explosionSpeed;
          }

          // Gradually pull towards target position
          const pullStrength = 0.01 + explosionPhaseProgress * 0.03;
          node.vx += (node.targetX - node.x) * pullStrength;
          node.vy += (node.targetY - node.y) * pullStrength;

          // Apply velocity with less damping during explosion
          node.x += node.vx;
          node.y += node.vy;
          node.vx *= 0.96;
          node.vy *= 0.96;

        } else if (currentPhase === 'settling') {
          // Settling phase: slow down and move towards target
          const settlingProgress = (bigBangTime - BIG_BANG_TIMING.settling.start) / BIG_BANG_TIMING.settling.duration;
          const easeSettling = settlingProgress * settlingProgress; // Quadratic ease-in

          // Strong pull towards target position
          const pullStrength = 0.02 + easeSettling * 0.05;
          node.vx += (node.targetX - node.x) * pullStrength;
          node.vy += (node.targetY - node.y) * pullStrength;

          // Apply velocity with increasing damping
          node.x += node.vx;
          node.y += node.vy;
          node.vx *= 0.90 - easeSettling * 0.05;
          node.vy *= 0.90 - easeSettling * 0.05;

        } else {
          // Orbit phase: gentle orbital motion from current position

          // On first frame of orbit phase, calibrate orbital parameters to match current position
          // This prevents the sudden jump when transitioning from settling to orbit
          if (!orbitCalibratedRef.current) {
            // Update orbit center to be the screen center
            node.orbitCenterX = centerX;
            node.orbitCenterY = centerY;

            // Calculate the angle from center to current position
            const dx = node.x - centerX;
            const dy = node.y - centerY;
            node.orbitAngle = Math.atan2(dy, dx);

            // Update orbit radius to match current distance from center
            node.orbitRadius = Math.sqrt(dx * dx + dy * dy);

            // Reset velocity for smooth transition
            node.vx = 0;
            node.vy = 0;
          }

          // Gentle orbital motion - very slow rotation
          node.orbitAngle += node.orbitSpeed * deltaTime;

          const cosAngle = Math.cos(node.orbitAngle);
          const sinAngle = Math.sin(node.orbitAngle);

          // Simple circular orbit from current radius
          const orbitTargetX = node.orbitCenterX + cosAngle * node.orbitRadius;
          const orbitTargetY = node.orbitCenterY + sinAngle * node.orbitRadius;

          // Very gentle interpolation to orbital position
          const orbitStrength = 0.008; // Reduced from 0.02 for smoother motion
          node.vx += (orbitTargetX - node.x) * orbitStrength;
          node.vy += (orbitTargetY - node.y) * orbitStrength;

          // Mouse interaction (only in orbit phase)
          const mdx = mouseRef.current.x - node.x;
          const mdy = mouseRef.current.y - node.y;
          const dist = Math.sqrt(mdx * mdx + mdy * mdy);
          const isBeingHovered = dist < node.radius + 20;
          const isGrabbed = grabbedNode?.id === node.id;

          if (isGrabbed) {
            node.x = mouseRef.current.x;
            node.y = mouseRef.current.y;
            node.vx = 0;
            node.vy = 0;
          } else if (isBeingHovered) {
            node.vx = 0;
            node.vy = 0;
          }

          // Apply velocity with damping
          node.x += node.vx;
          node.y += node.vy;
          node.vx *= 0.95; // Increased damping for smoother motion
          node.vy *= 0.95;
        }

        // Node-to-node repulsion (already past singularity at this point due to early return)
        nodes.forEach((other) => {
          if (other.id === node.id || other.radius === 0) return;
          const odx = node.x - other.x;
          const ody = node.y - other.y;
          const odist = Math.sqrt(odx * odx + ody * ody);
          const minDist = (node.radius + other.radius) * 3;

          if (odist < minDist && odist > 0) {
            const repelForce = (1 - odist / minDist) * 0.15;
            node.vx += (odx / odist) * repelForce;
            node.vy += (ody / odist) * repelForce;
          }
        });

        // Keep within bounds
        const margin = 30;
        node.x = Math.max(margin, Math.min(dimensions.width - margin, node.x));
        node.y = Math.max(margin, Math.min(dimensions.height - margin, node.y));

        // Check hover (only visible nodes in orbit phase)
        if (currentPhase === 'orbit' && node.radius > 0) {
          const mouseDist = Math.sqrt(
            Math.pow(mouseRef.current.x - node.x, 2) + Math.pow(mouseRef.current.y - node.y, 2)
          );
          if (mouseDist < node.radius + 15) {
            newHovered = node;
          }
        }
      });

      // Mark orbital calibration as done after first orbit phase frame
      if (currentPhase === 'orbit' && !orbitCalibratedRef.current) {
        orbitCalibratedRef.current = true;
      }

      setHoveredNode(newHovered);

      // Draw edges with animated flow - EDGES FIRST so nodes render on top
      // Only draw edges after singularity phase and when both nodes are visible
      if (currentPhase !== 'singularity') {
        edges.forEach((edge) => {
          const source = nodes.find((n) => n.id === edge.source);
          const target = nodes.find((n) => n.id === edge.target);
          if (!source || !target) return;

          // Check if both nodes are visible (radius > 0)
          if (source.radius === 0 || target.radius === 0) return;

          // Calculate edge alpha based on node visibility and phase
          const baseAlpha = Math.min(source.radius / source.baseRadius, target.radius / target.baseRadius);
          // Edges fade in more slowly during expansion
          const phaseMultiplier = currentPhase === 'orbit' ? 1 :
            currentPhase === 'settling' ? 0.7 :
            currentPhase === 'expansion' ? 0.4 : 0.2;
          const edgeAlpha = baseAlpha * phaseMultiplier;

        const isHighlighted =
          hoveredNode && (hoveredNode.id === source.id || hoveredNode.id === target.id);

        // Calculate control point for bezier curve (subtle curve)
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const curvature = Math.min(0.15, 30 / dist); // Less curve for longer edges
        const perpX = -dy * curvature;
        const perpY = dx * curvature;
        const ctrlX = midX + perpX;
        const ctrlY = midY + perpY;

        // Draw edge glow (outer)
        if (isHighlighted) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.quadraticCurveTo(ctrlX, ctrlY, target.x, target.y);
          ctx.strokeStyle = `rgba(167, 139, 250, ${0.3 * edgeAlpha})`;
          ctx.lineWidth = 6;
          ctx.shadowColor = 'rgba(167, 139, 250, 0.8)';
          ctx.shadowBlur = 20;
          ctx.stroke();
          ctx.shadowBlur = 0;
        }

        // Main edge line - MORE VISIBLE
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.quadraticCurveTo(ctrlX, ctrlY, target.x, target.y);

        // Gradient stroke for edges
        const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y);
        if (isHighlighted) {
          gradient.addColorStop(0, source.glowColor.replace('0.8', `${0.9 * edgeAlpha}`));
          gradient.addColorStop(0.5, `rgba(200, 180, 255, ${0.8 * edgeAlpha})`);
          gradient.addColorStop(1, target.glowColor.replace('0.8', `${0.9 * edgeAlpha}`));
          ctx.lineWidth = 3;
        } else {
          gradient.addColorStop(0, source.glowColor.replace('0.8', `${0.4 * edge.strength * edgeAlpha}`));
          gradient.addColorStop(0.5, `rgba(150, 140, 200, ${0.35 * edge.strength * edgeAlpha})`);
          gradient.addColorStop(1, target.glowColor.replace('0.8', `${0.4 * edge.strength * edgeAlpha}`));
          ctx.lineWidth = 1.5;
        }

        ctx.strokeStyle = gradient;
        ctx.stroke();

        // Animated flow dots along edge - small but bright
        if (edgeAlpha > 0.3) {
          edge.flowOffset += edge.flowSpeed * 1.2;
          const flowCount = isHighlighted ? 6 : 4;

          for (let i = 0; i < flowCount; i++) {
            const t = ((edge.flowOffset + i * (100 / flowCount)) % 100) / 100;
            const t2 = t * t;
            const mt = 1 - t;
            const mt2 = mt * mt;

            // Quadratic bezier point
            const px = mt2 * source.x + 2 * mt * t * ctrlX + t2 * target.x;
            const py = mt2 * source.y + 2 * mt * t * ctrlY + t2 * target.y;

            const dotAlpha = Math.sin(t * Math.PI) * (isHighlighted ? 1 : 0.8) * edgeAlpha;
            const dotSize = isHighlighted ? 1.8 : 1.2; // Smaller particles

            // Outer glow - larger and brighter
            ctx.beginPath();
            ctx.arc(px, py, dotSize * 4, 0, Math.PI * 2);
            const glowGrad = ctx.createRadialGradient(px, py, 0, px, py, dotSize * 4);
            glowGrad.addColorStop(0, `rgba(255, 255, 255, ${dotAlpha * 0.9})`);
            glowGrad.addColorStop(0.2, `rgba(200, 180, 255, ${dotAlpha * 0.6})`);
            glowGrad.addColorStop(0.5, `rgba(167, 139, 250, ${dotAlpha * 0.3})`);
            glowGrad.addColorStop(1, 'transparent');
            ctx.fillStyle = glowGrad;
            ctx.fill();

            // Bright core
            ctx.beginPath();
            ctx.arc(px, py, dotSize, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${dotAlpha})`;
            ctx.shadowColor = 'rgba(220, 200, 255, 1)';
            ctx.shadowBlur = 15;
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        }
        });
      } // End of if (currentPhase !== 'singularity') for edge drawing

      // Draw nodes as celestial bodies
      nodes.forEach((node) => {
        // Skip invisible nodes (during singularity or before birth)
        if (node.radius === 0) return;

        // Calculate birth progress based on big bang timing
        const nodeBirthTime = bigBangStartTimeRef.current! + node.birthTime;
        const timeSinceBirth = time - nodeBirthTime;
        const birthProgress = Math.min(timeSinceBirth / 800, 1);
        const easeOut = 1 - Math.pow(1 - birthProgress, 3);
        const isHovered = hoveredNode?.id === node.id;
        const isSelected = selectedNode?.id === node.id;
        const isGrabbed = grabbedNode?.id === node.id;
        const isConnectedToSelected = connectedNodeIds.has(node.id);
        const isHighlighted = isGrabbed || isSelected || isHovered || isConnectedToSelected;
        const scale = isGrabbed ? 1.6 : isSelected ? 1.5 : isHovered ? 1.4 : isConnectedToSelected ? 1.3 : 1;

        // Apply birth animation
        ctx.save();
        ctx.globalAlpha = easeOut;

        // Draw the appropriate celestial body based on node type
        switch (node.celestialType) {
          case 'sun':
            drawSunNode(ctx, node, scale, time, isHighlighted);
            break;
          case 'planet':
            drawPlanetNode(ctx, node, scale, time, isHighlighted);
            break;
          case 'nebulaStar':
            drawNebulaStarNode(ctx, node, scale, time, isHighlighted);
            break;
          case 'pulsar':
            drawPulsarNode(ctx, node, scale, time, isHighlighted);
            break;
        }

        ctx.restore();

        // Highlight ring for hovered, selected, grabbed, or connected
        if (isHighlighted) {
          const ringRadius = node.radius * scale * 1.8;
          ctx.beginPath();
          ctx.arc(node.x, node.y, ringRadius, 0, Math.PI * 2);
          ctx.strokeStyle = isGrabbed
            ? 'rgba(255, 255, 255, 0.9)'
            : isSelected
            ? 'rgba(255, 255, 255, 0.85)'
            : isConnectedToSelected
            ? 'rgba(255, 255, 255, 0.6)'
            : 'rgba(255, 255, 255, 0.5)';
          ctx.lineWidth = isGrabbed ? 3 : isSelected ? 3 : 2;
          ctx.shadowColor = node.color;
          ctx.shadowBlur = 15;
          ctx.stroke();
          ctx.shadowBlur = 0;

          // Spawn light particles around selected/grabbed/hovered node
          if ((isGrabbed || isSelected || isHovered) && Math.random() > 0.88) {
            const angle = Math.random() * Math.PI * 2;
            const dist = node.radius * scale * 2.5 + Math.random() * 15;
            const particleType = Math.random() > 0.6 ? 'sparkle' : Math.random() > 0.5 ? 'dust' : 'star';
            spawnParticle(
              node.x + Math.cos(angle) * dist,
              node.y + Math.sin(angle) * dist,
              particleType as 'sparkle' | 'star' | 'dust'
            );
          }
        }
      });

      // === OVERLAY EFFECTS ===

      // Subtle vignette
      const vignette = ctx.createRadialGradient(
        dimensions.width / 2,
        dimensions.height / 2,
        dimensions.height * 0.3,
        dimensions.width / 2,
        dimensions.height / 2,
        dimensions.width * 0.8
      );
      vignette.addColorStop(0, 'transparent');
      vignette.addColorStop(1, 'rgba(0, 0, 0, 0.4)');
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, dimensions.width, dimensions.height);

      animationRef.current = requestAnimationFrame(animate);
    };

    animate(performance.now());

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [dimensions, hoveredNode, selectedNode, grabbedNode, connectedNodeIds, spawnParticle, drawSparkle, drawStar, drawFlare, drawSunNode, drawPlanetNode, drawNebulaStarNode, drawPulsarNode, drawSingularity, drawExplosionFlash, spawnExplosionParticles, spawnShockwave]);

  return (
    <div className={`relative w-full h-full overflow-hidden ${className || ''}`}>
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        style={{ cursor: hoveredNode ? (grabbedNode ? 'grabbing' : 'grab') : 'default' }}
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          mouseRef.current = { x: -1000, y: -1000 };
          setGrabbedNode(null);
          // Keep selection and connected nodes when mouse leaves
        }}
      />

      {/* Floating Greek Text - SLOW */}
      <AnimatePresence>
        {floatingTexts.map((ft) => (
          <motion.div
            key={ft.id}
            initial={{ opacity: 0, y: 20, x: `${ft.x}%` }}
            animate={{ opacity: 0.12, y: -dimensions.height * 0.5, x: `${ft.x}%` }}
            exit={{ opacity: 0 }}
            transition={{ duration: 20, ease: 'linear' }}
            className="absolute text-2xl md:text-4xl font-serif text-violet-300 pointer-events-none select-none"
            style={{ top: `${ft.y}%` }}
          >
            {ft.text}
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Tooltip - Fixed top right - shows hovered or selected node */}
      <AnimatePresence>
        {(hoveredNode || selectedNode) && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className="absolute top-4 right-4 pointer-events-none px-5 py-3 bg-black/60 backdrop-blur-xl rounded-xl border border-white/20 text-white shadow-2xl min-w-[140px]"
          >
            {/* Show hovered node if hovering, otherwise show selected */}
            {(() => {
              const displayNode = hoveredNode || selectedNode;
              if (!displayNode) return null;
              return (
                <>
                  <div className="font-semibold text-base">{displayNode.label}</div>
                  {displayNode.greekLabel && (
                    <div className="text-violet-300 text-sm font-serif mt-1">{displayNode.greekLabel}</div>
                  )}
                  <div className="text-white/50 text-xs capitalize mt-2 flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: displayNode.color }}
                    />
                    {displayNode.type}
                    {selectedNode?.id === displayNode.id && !hoveredNode && (
                      <span className="ml-1 text-violet-400">(selected)</span>
                    )}
                  </div>
                  {selectedNode && connectedNodeIds.size > 0 && selectedNode.id === displayNode.id && (
                    <div className="text-white/40 text-xs mt-2 pt-2 border-t border-white/10">
                      {connectedNodeIds.size} connection{connectedNodeIds.size !== 1 ? 's' : ''}
                    </div>
                  )}
                </>
              );
            })()}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Legend */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 0.8 }}
        className="absolute bottom-4 left-4 flex flex-wrap gap-3 text-xs text-white/70"
      >
        {Object.entries(NODE_TYPES).map(([type, { color }]) => (
          <div key={type} className="flex items-center gap-1.5 bg-black/30 backdrop-blur-sm px-2 py-1 rounded-full">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
            />
            <span className="capitalize">{type}s</span>
          </div>
        ))}
      </motion.div>

      {/* Stats overlay */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 2, duration: 0.8 }}
        className="absolute bottom-4 right-4 text-right text-xs text-white/50"
      >
        <div className="bg-black/30 backdrop-blur-sm px-3 py-2 rounded-lg">
          <div><span className="text-white/80 font-medium">{SAMPLE_NODES.length}</span> nodes</div>
          <div><span className="text-white/80 font-medium">{SAMPLE_EDGES.length}</span> edges</div>
        </div>
      </motion.div>

      {/* Decorative grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />
    </div>
  );
}
