/**
 * Type definitions for Cosmos Mode visualization
 */

// ============================================================================
// Node Types
// ============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Attributes = Record<string, any>;

export interface CosmosNodeAttributes extends Attributes {
  // Core properties
  id: string;
  label: string;
  type: 'circle'; // Sigma's rendering program selector - must match nodeProgramClasses
  nodeType: string; // Use nodeType for our semantic type (person, concept, etc.)

  // Position
  x: number;
  y: number;

  // Visual properties
  size: number;
  color: string;

  // Metadata
  school?: string;
  period?: string;
  description?: string;
  dates?: string;

  // Computed metrics
  degree?: number;
  betweenness?: number;
  pagerank?: number;
  communityId?: number;

  // Animation state
  baseSize?: number;
  pulsePhase?: number;
  pulseFrequency?: number;
  pulseAmplitude?: number;
  glowIntensity?: number;

  // Interaction state
  highlighted?: boolean;
  dimmed?: boolean;
  selected?: boolean;
  hidden?: boolean;
}

export interface CosmosEdgeAttributes extends Attributes {
  // Core properties
  source: string;
  target: string;
  type?: 'line'; // Sigma's rendering program selector - must match edgeProgramClasses
  relation?: string;
  weight?: number;

  // Visual properties
  size?: number;
  color?: string;

  // Animation state
  particleProgress?: number;
  highlighted?: boolean;
  dimmed?: boolean;
  hidden?: boolean;

  // Edge bundling
  bundleId?: string;
  controlPoints?: Array<{ x: number; y: number }>;
}

// ============================================================================
// Particle System
// ============================================================================

export interface EdgeParticle {
  id: string;
  edgeKey: string;
  progress: number;      // 0 to 1 along edge
  speed: number;         // Progress per second
  size: number;
  opacity: number;
  color: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
}

export interface ParticleSystemConfig {
  enabled: boolean;
  maxParticlesPerEdge: number;
  spawnRate: number;     // Particles per second per edge
  baseSpeed: number;
  speedVariation: number;
  baseSize: number;
  sizeVariation: number;
  baseOpacity: number;
  opacityVariation: number;
  trailLength: number;
}

// ============================================================================
// Animation State
// ============================================================================

export interface PulseConfig {
  enabled: boolean;
  baseFrequency: number;       // Hz
  frequencyVariation: number;
  baseAmplitude: number;       // 0-1
  amplitudeVariation: number;
  importanceWeight: number;    // How much importance affects pulse
}

export interface BreathingConfig {
  enabled: boolean;
  frequency: number;           // Hz (very slow, ~0.05)
  amplitude: number;           // Position shift factor
}

export interface GlowConfig {
  enabled: boolean;
  selectedIntensity: number;
  hoveredIntensity: number;
  neighborIntensity: number;
  pathIntensity: number;
  blurRadius: number;
}

// ============================================================================
// Zoom Levels
// ============================================================================

export type NodeDetailLevel = 'dot' | 'icon' | 'label' | 'full';
export type EdgeVisibility = 'none' | 'major' | 'all';
export type LabelVisibility = 'none' | 'major' | 'all';

export interface ZoomLevel {
  minZoom: number;
  maxZoom: number;
  nodeDetail: NodeDetailLevel;
  edgeVisibility: EdgeVisibility;
  labelVisibility: LabelVisibility;
  particlesEnabled: boolean;
  glowEnabled: boolean;
  name: string;
}

// ============================================================================
// Interaction State
// ============================================================================

export interface CosmosInteractionState {
  hoveredNode: string | null;
  selectedNode: string | null;
  focusedNode: string | null;
  neighborhoodNodes: Set<string>;
  neighborhoodEdges: Set<string>;
  pathNodes: Set<string>;
  pathEdges: Set<string>;
}

// ============================================================================
// Filter State
// ============================================================================

export interface CosmosFilterState {
  nodeTypes: Set<string>;
  schools: Set<string>;
  periods: Set<string>;
  relations: Set<string>;
  searchTerm: string;
  minDegree: number;
  maxNodes: number;
  showLabels: boolean;
  showEdgeLabels: boolean;
}

// ============================================================================
// Settings
// ============================================================================

export interface CosmosSettings {
  // Layout
  layoutAlgorithm: 'forceatlas2' | 'constellation' | 'circular';
  layoutIterations: number;
  gravity: number;
  scalingRatio: number;

  // Animation
  pulse: PulseConfig;
  breathing: BreathingConfig;
  glow: GlowConfig;
  particles: ParticleSystemConfig;

  // Visual
  nodeSizeRange: [number, number];
  edgeSizeRange: [number, number];
  labelThreshold: number;
  edgeBundling: boolean;

  // Interaction
  zoomLevels: ZoomLevel[];
  hoverHighlight: boolean;
  clickSelect: boolean;

  // Performance
  renderEdgesThreshold: number;
  labelDensity: number;
}

// ============================================================================
// Component Props
// ============================================================================

export interface CosmosVisualizerProps {
  className?: string;
  onNodeClick?: (nodeId: string | null) => void;
  onNodeHover?: (nodeId: string | null) => void;
  settings?: Partial<CosmosSettings>;
}

export interface CosmosControlsProps {
  filters: CosmosFilterState;
  onFiltersChange: (filters: CosmosFilterState) => void;
  settings: CosmosSettings;
  onSettingsChange: (settings: Partial<CosmosSettings>) => void;
  stats: {
    totalNodes: number;
    totalEdges: number;
    visibleNodes: number;
    visibleEdges: number;
  };
  className?: string;
}

export interface CosmosNodeDetailProps {
  nodeId: string | null;
  onClose: () => void;
  onFocus?: (nodeId: string) => void;
  className?: string;
}
