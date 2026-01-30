/**
 * MorphingParticles.types.ts
 *
 * Type definitions and constants for MorphingParticles component.
 * Separated from component file to prevent HMR Fast Refresh issues.
 */

export type ShapeName =
  | 'wisdom-tree'
  | 'owl-of-athena'
  | 'philosopher'
  | 'armillary-sphere'
  | 'knowledge-graph'
  | 'semantic-paths'
  | 'reasoning-chains'
  | 'query-burst'
  | 'pyramid-of-knowledge'
  | 'attractor-of-fate';

export const SHAPE_NAMES: ShapeName[] = [
  'wisdom-tree',             // First - the stunning tree of knowledge
  'owl-of-athena',           // Second - 3Dme owl of Athena
  'philosopher',             // Third - ancient philosopher portrait
  'armillary-sphere',        // Fourth - ancient cosmic model
  'knowledge-graph',         // Fifth - clustered concepts
  'semantic-paths',          // Sixth - search expansion
  'reasoning-chains',        // Seventh - inference tendrils
  'query-burst',             // Eighth - rippling search
  'pyramid-of-knowledge',    // Ninth - ancient repository of wisdom
  'attractor-of-fate',       // Tenth - chaos/fate attractor
];

export const SHAPE_LABELS: Record<ShapeName, string> = {
  'wisdom-tree': 'Wisdom Tree',
  'owl-of-athena': 'Owl of Athena',
  'philosopher': 'Ancient Philosopher',
  'armillary-sphere': 'Armillary Sphere',
  'knowledge-graph': 'Knowledge Graph',
  'semantic-paths': 'Semantic Paths',
  'reasoning-chains': 'Reasoning Chains',
  'query-burst': 'Query Burst',
  'pyramid-of-knowledge': 'Pyramid of Knowledge',
  'attractor-of-fate': 'Attractor of Fate',
};

export interface MorphingParticlesConfig {
  particleCount?: number;
  morphDuration?: number;      // seconds between shape changes
  rotationSpeed?: number;
  particleSize?: number;
  lineOpacity?: number;
  connectionDistance?: number; // max distance for line connections
  colorScheme?: 'graphrag' | 'ancient' | 'cool' | 'warm' | 'rainbow';
  selectedShape?: ShapeName | null; // null = auto-cycle, or specific shape name

  // Visual enhancements
  enableBloom?: boolean;       // Post-processing bloom glow
  bloomIntensity?: number;     // Bloom strength (0-2)
  enableTrails?: boolean;      // Particle motion trails
  trailLength?: number;        // Trail persistence (0-1)
  enableDepthOfField?: boolean; // Blur distant particles

  // Interactivity
  enableZoom?: boolean;        // Scroll wheel zoom
  enableHover?: boolean;       // Mouse proximity highlight
  enableKeyboard?: boolean;    // Keyboard shortcuts (space, arrows)

  // Animation
  enableBreathing?: boolean;   // Subtle pulsing scale
  breathingSpeed?: number;     // Breathing cycle speed
  enableStaggeredMorph?: boolean; // Wave-based morphing
  staggerDirection?: 'radial' | 'horizontal' | 'vertical'; // Stagger pattern
}
