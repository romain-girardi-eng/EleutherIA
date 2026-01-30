/**
 * CosmographKGVisualizer - GPU-Powered 2D Knowledge Graph Visualization
 *
 * Ultimate graph visualization using Cosmograph v2 with ALL features:
 * - GPU-accelerated force simulation AND rendering
 * - Dynamic labels for important nodes
 * - Clustering by philosophical school
 * - Interactive controls (zoom, fit, play/pause)
 * - Hover tooltips and click selection
 * - Beautiful modern dark aesthetic
 */

import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import {
  Cosmograph,
  CosmographProvider,
  useCosmograph,
  CosmographButtonZoomInOut,
  CosmographButtonFitView,
  CosmographButtonPlayPause,
  CosmographButtonRectangularSelection,
} from '@cosmograph/react';
import type { CosmographRef, CosmographConfig } from '@cosmograph/react';
import { Search, X, Tag, Layers, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { apiClient } from '../api/client';
import type { KGNode, CytoscapeData } from '../types';
import GlassSurface from './ui/GlassSurface';

// d3-force-webgpu for GPU-accelerated collision detection
import {
  forceSimulation,
  forceCollide,
  forceManyBody,
  forceLink,
  forceCenter,
  forceX,
  forceY,
} from 'd3-force-webgpu';

// ============================================================================
// TYPES
// ============================================================================

interface RawPoint {
  index: number;
  id: string;
  label: string;
  type: string;
  school: string;
  period: string;
  description: string;
  color: string;
  size: number;
  cluster: string;
  labelWeight: number;
}

interface RawLink {
  sourceId: string;
  targetId: string;
  source: number;
  target: number;
  color: string;
  width: number;
  arrow: boolean;
  relationship?: string;  // Edge type for hierarchical layout
}

// ============================================================================
// LOD (Level of Detail) CONFIGURATION - Reserved for future zoom-based filtering
// ============================================================================
// const LOD_CONFIG = {
//   PASSAGE_SHOW_ZOOM: 1.5,
//   QUOTE_SHOW_ZOOM: 1.2,
//   HIDDEN_SIZE_MULTIPLIER: 0.15,
//   HIDDEN_OPACITY: 0.05,
// };

interface CosmographKGVisualizerProps {
  onNodeClick?: (node: KGNode | null) => void;
  selectedNodeId?: string;
  className?: string;
}

// ============================================================================
// COLOR PALETTE
// ============================================================================
// School colors - reserved for future school-based coloring mode
// const SCHOOL_COLORS: Record<string, string> = {
//   'Stoic': '#8b5cf6', 'Epicurean': '#f59e0b', 'Academic': '#06b6d4',
//   'Peripatetic': '#10b981', 'Platonist': '#ec4899', ...
// };

// Vibrant neon colors for neuronal aesthetic - ALL types from database
const TYPE_COLORS: Record<string, string> = {
  // Primary entities
  'person': '#60a5fa',       // Bright blue - philosophers/scholars
  'work': '#fbbf24',         // Golden yellow - ancient texts
  'concept': '#c084fc',      // Bright purple - philosophical ideas
  'argument': '#f472b6',     // Hot pink - arguments/proofs
  'debate': '#fb7185',       // Coral red - scholarly debates
  'school': '#4ade80',       // Bright green - philosophical schools
  'event': '#fb923c',        // Bright orange - historical events
  'quote': '#facc15',        // Yellow - direct quotations
  'reformulation': '#a78bfa', // Violet - reformulated arguments
  'passage': '#94a3b8',      // Muted slate - text passages
  // Secondary entities (from database)
  'publication': '#06b6d4',  // Cyan/teal - modern publications (79 nodes)
  'synthesis': '#10b981',    // Emerald - synthesis nodes (8 nodes)
  'controversy': '#f43f5e',  // Rose - controversies (5 nodes)
  'conceptual_evolution': '#818cf8', // Indigo - concept evolution (3 nodes)
  'group': '#84cc16',        // Lime - groups/collectives (3 nodes)
  'argument_framework': '#e879f9', // Fuchsia - argument frameworks (1 node)
  'default': '#94a3b8',
};

// Filter options for the filters panel - ALL types from database
const NODE_TYPE_FILTERS = [
  // Primary entities (high count)
  { value: 'person', label: 'Persons', color: '#60a5fa' },
  { value: 'passage', label: 'Passages', color: '#94a3b8' },
  { value: 'concept', label: 'Concepts', color: '#c084fc' },
  { value: 'argument', label: 'Arguments', color: '#f472b6' },
  { value: 'work', label: 'Works', color: '#fbbf24' },
  { value: 'publication', label: 'Publications', color: '#06b6d4' },
  { value: 'debate', label: 'Debates', color: '#fb7185' },
  { value: 'quote', label: 'Quotes', color: '#facc15' },
  { value: 'school', label: 'Schools', color: '#4ade80' },
  // Secondary entities (lower count)
  { value: 'synthesis', label: 'Syntheses', color: '#10b981' },
  { value: 'controversy', label: 'Controversies', color: '#f43f5e' },
  { value: 'reformulation', label: 'Reformulations', color: '#a78bfa' },
  { value: 'conceptual_evolution', label: 'Evolutions', color: '#818cf8' },
  { value: 'group', label: 'Groups', color: '#84cc16' },
  { value: 'event', label: 'Events', color: '#fb923c' },
  { value: 'argument_framework', label: 'Frameworks', color: '#e879f9' },
];

const SCHOOL_FILTERS = [
  { value: 'Stoic', label: 'Stoic', color: '#8b5cf6' },
  { value: 'Epicurean', label: 'Epicurean', color: '#f59e0b' },
  { value: 'Academic', label: 'Academic', color: '#06b6d4' },
  { value: 'Peripatetic', label: 'Peripatetic', color: '#10b981' },
  { value: 'Platonist', label: 'Platonist', color: '#ec4899' },
  { value: 'Christian', label: 'Christian', color: '#14b8a6' },
  { value: 'Neoplatonist', label: 'Neoplatonist', color: '#a855f7' },
  { value: 'Presocratic', label: 'Presocratic', color: '#84cc16' },
  { value: 'Contemporary', label: 'Contemporary', color: '#64748b' },
];

// ============================================================================
// GLASSMORPHISM - Now using GlassSurface component from ReactBits
// ============================================================================

function getNodeColor(node: { school?: string; type?: string }): string {
  // STRICT TYPE-BASED COLORING for consistent visual language
  // The legend shows TYPE colors, so nodes MUST match the legend
  const typeLower = node.type?.toLowerCase()?.trim();

  // Always use type color if available - this ensures legend consistency
  if (typeLower && TYPE_COLORS[typeLower]) {
    return TYPE_COLORS[typeLower];
  }

  // Fallback to default (grey/slate) - never use school colors for nodes
  // School colors are for clustering visualization only
  return TYPE_COLORS.default;
}

// ============================================================================
// COLOR UTILITIES FOR BI-COLOR EDGES
// ============================================================================

/**
 * Parse hex color to RGB components
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return { r: 148, g: 163, b: 184 }; // fallback gray
  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  };
}

/**
 * Convert RGB to hex
 */
function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => {
    const hex = Math.round(x).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('');
}

/**
 * Blend two colors - creates a 50/50 mix
 * Returns hex color (Cosmograph requires hex, not rgba)
 */
function blendColors(color1: string, color2: string): string {
  const c1 = hexToRgb(color1);
  const c2 = hexToRgb(color2);

  // Blend the colors (50/50 mix)
  const blended = {
    r: (c1.r + c2.r) / 2,
    g: (c1.g + c2.g) / 2,
    b: (c1.b + c2.b) / 2,
  };

  // Return as hex (Cosmograph doesn't support rgba)
  return rgbToHex(blended.r, blended.g, blended.b);
}

/**
 * Get edge color based on source and target node colors
 * Creates a blended color that connects the two node colors
 */
function getEdgeColor(sourceColor: string, targetColor: string): string {
  // Simple 50/50 blend of source and target colors
  return blendColors(sourceColor, targetColor);
}

// ============================================================================
// NODE SIZING
// ============================================================================
// Type weights - reserved for future weighted sizing mode
// const TYPE_WEIGHTS: Record<string, number> = {
//   'person': 1.0, 'school': 0.85, 'concept': 0.75, ...
// };

const MAJOR_FIGURES = new Set([
  'Aristotle', 'Plato', 'Chrysippus', 'Epicurus', 'Zeno of Citium',
  'Augustine', 'Plotinus', 'Origen', 'Seneca', 'Marcus Aurelius',
  'Alexander of Aphrodisias', 'Epictetus', 'Lucretius', 'Cicero',
  'Cleanthes', 'Carneades', 'Posidonius', 'Panaetius', 'Diogenes of Babylon',
  'Boethius', 'Thomas Aquinas', 'Duns Scotus', 'William of Ockham',
]);

const MAJOR_CONCEPTS = new Set([
  'Free Will', 'Determinism', 'Fate', 'Necessity', 'Providence',
  'Moral Responsibility', 'Causation', 'Agency', 'Choice', 'Deliberation',
  'Compatibilism', 'Incompatibilism', 'Libertarianism', 'Hard Determinism',
]);

function calculateNodeSize(
  label: string,
  type: string,
  _school: string | undefined,
  degree: number,
  _maxDegree: number
): number {
  // COMPACT SIZES for dense graph (2193 nodes, 8616 edges)
  // Small nodes create readable layout - matches official Cosmos examples
  // Range: 3-30px (was 6-100px)
  const typeLower = type.toLowerCase();

  const isMajorFigure = MAJOR_FIGURES.has(label);
  const isMajorConcept = MAJOR_CONCEPTS.has(label);
  const isMajorSchool = typeLower === 'school';

  // Tier 1: Major philosophers - largest, scale with importance (degree)
  if (isMajorFigure) {
    // More connections = more important = larger
    const degreeBoost = Math.min(degree / 40, 1) * 15;
    return 24 + degreeBoost; // 24-39px - visually prominent cluster centers
  }

  // Tier 2: Schools - anchor points for clusters
  if (isMajorSchool) {
    const degreeBoost = Math.min(degree / 30, 1) * 12;
    return 18 + degreeBoost; // 18-30px
  }

  // Tier 3: Major concepts
  if (isMajorConcept) {
    const degreeBoost = Math.min(degree / 30, 1) * 10;
    return 12 + degreeBoost; // 12-22px
  }

  // Tier 4: Persons (non-major philosophers) - scale with importance
  if (typeLower === 'person') {
    // Important secondary figures get larger sizes
    const degreeBoost = Math.min(degree / 15, 1) * 10;
    return 10 + degreeBoost; // 10-20px - still prominent as cluster centers
  }

  // Tier 5: Works
  if (typeLower === 'work') {
    return 5 + Math.min(degree / 20, 1) * 5; // 5-10px (was 12-20)
  }

  // Tier 6: Debates, arguments
  if (typeLower === 'debate' || typeLower === 'argument') {
    return 4 + Math.min(degree / 15, 1) * 4; // 4-8px (was 8-14)
  }

  // Tier 7: Everything else (quotes, passages, concepts)
  return 3 + Math.min(degree / 10, 1) * 2; // 3-5px (was 6-10)
}

function calculateLabelWeight(
  label: string,
  type: string,
  degree: number,
  maxDegree: number
): number {
  // HIERARCHY: School > Person > Work > Concept > Argument > Passage
  // Higher weight = label shown at more zoom levels
  const isMajorFigure = MAJOR_FIGURES.has(label);
  const isMajorConcept = MAJOR_CONCEPTS.has(label);
  const typeLower = type.toLowerCase();
  const degreeBonus = (degree / Math.max(maxDegree, 1)) * 0.15;

  // Tier 1: Schools - ALWAYS visible (highest hierarchy)
  if (typeLower === 'school') return 1.0;

  // Tier 2: Major philosophers - almost always visible
  if (isMajorFigure) return 0.95 + degreeBonus;

  // Tier 3: Other philosophers - visible at medium zoom
  if (typeLower === 'person') return 0.7 + degreeBonus;

  // Tier 4: Major concepts - visible at medium zoom
  if (isMajorConcept) return 0.65 + degreeBonus;

  // Tier 5: Works - visible when somewhat zoomed
  if (typeLower === 'work') return 0.45 + degreeBonus;

  // Tier 6: Other concepts - visible when more zoomed
  if (typeLower === 'concept') return 0.35 + degreeBonus;

  // Tier 7: Arguments/Debates - visible only when quite zoomed
  if (typeLower === 'argument' || typeLower === 'debate') return 0.2 + degreeBonus;

  // Tier 8: Quotes/Reformulations - rarely visible
  if (typeLower === 'quote' || typeLower === 'reformulation') return 0.1 + degreeBonus;

  // Tier 9: Passages - only visible when very zoomed in
  if (typeLower === 'passage') return 0.05 + degreeBonus;

  return 0.1 + degreeBonus;
}

// ============================================================================
// DATA CONVERSION
// ============================================================================

function convertCytoscapeData(data: CytoscapeData): {
  rawPoints: RawPoint[];
  rawLinks: RawLink[];
  nodeMap: Map<string, KGNode>;
  idToIndex: Map<string, number>;
  parentMap: Map<string, string>;  // child → parent for hierarchical layout
} {
  const nodeMap = new Map<string, KGNode>();
  const idToIndex = new Map<string, number>();
  const rawPoints: RawPoint[] = [];
  const rawLinks: RawLink[] = [];

  // Maps for hierarchical layout
  const parentMap = new Map<string, string>();  // child id → parent id
  const authorOfWork = new Map<string, string>(); // work id → author id
  const workOfPassage = new Map<string, string>(); // passage id → work id

  const degreeMap = new Map<string, number>();
  const cyNodes = data.elements?.nodes ?? [];
  const cyEdges = data.elements?.edges ?? [];

  // First pass: build degree map and identify hierarchical relationships
  cyEdges.forEach((edge) => {
    const source = String(edge.data.source ?? edge.data.source_id ?? '');
    const target = String(edge.data.target ?? edge.data.target_id ?? '');
    const relationship = String(edge.data.relationship ?? edge.data.label ?? '').toLowerCase();

    if (source && target) {
      degreeMap.set(source, (degreeMap.get(source) ?? 0) + 1);
      degreeMap.set(target, (degreeMap.get(target) ?? 0) + 1);

      // Identify hierarchical relationships (author → work → passage)
      // Common relationship types: authored, wrote, contains, has_passage, from_work, etc.
      if (relationship.includes('author') || relationship.includes('wrote') || relationship.includes('composed')) {
        // Person authored Work: person → work
        authorOfWork.set(target, source);
        parentMap.set(target, source);
      } else if (relationship.includes('contains') || relationship.includes('passage') || relationship.includes('excerpt') || relationship.includes('from_work') || relationship.includes('part_of')) {
        // Work contains Passage: work → passage
        workOfPassage.set(target, source);
        parentMap.set(target, source);
      }
    }
  });

  const maxDegree = Math.max(...Array.from(degreeMap.values()), 1);

  // Build node type map AND label map first for hierarchy inference and cluster naming
  const nodeTypeMap = new Map<string, string>();
  const nodeLabelMap = new Map<string, string>();  // id → label for cluster naming
  cyNodes.forEach((cyNode) => {
    const id = String(cyNode.data.id ?? cyNode.data.node_id ?? '');
    const type = String(cyNode.data.type ?? 'default').toLowerCase();
    const label = String(cyNode.data.label ?? id);
    nodeTypeMap.set(id, type);
    nodeLabelMap.set(id, label);
  });

  // Helper to extract clean name from node ID (e.g., "person_aristotle_384_322bce_xyz" → "Aristotle")
  const extractCleanName = (nodeId: string): string => {
    // Try to get a clean label from ID by removing prefix and suffix noise
    const parts = nodeId.split('_');
    if (parts.length >= 2) {
      // Skip type prefix (person_, work_, etc.) and any trailing hash
      const nameParts = parts.slice(1, -1).filter(p => !p.match(/^[a-z0-9]{6,}$/) && !p.match(/^\d+[a-z]*$/));
      if (nameParts.length > 0) {
        return nameParts.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
      }
    }
    return nodeId;
  };

  // Get cluster label, preferring clean label over raw ID
  const getClusterLabel = (nodeId: string): string => {
    const nodeLabel = nodeLabelMap.get(nodeId);
    // If label looks like an ID (contains underscore + random suffix), extract clean name
    if (nodeLabel && !nodeLabel.includes('_')) {
      return nodeLabel;
    }
    return extractCleanName(nodeId);
  };

  // Second pass: infer hierarchy from types if not found via relationships
  // If a work is connected to a person, assume author relationship
  // If a passage is connected to a work, assume contains relationship
  cyEdges.forEach((edge) => {
    const source = String(edge.data.source ?? edge.data.source_id ?? '');
    const target = String(edge.data.target ?? edge.data.target_id ?? '');
    const sourceType = nodeTypeMap.get(source) || '';
    const targetType = nodeTypeMap.get(target) || '';

    // Person → Work (person is author)
    if (sourceType === 'person' && targetType === 'work' && !authorOfWork.has(target)) {
      authorOfWork.set(target, source);
      parentMap.set(target, source);
    }
    if (targetType === 'person' && sourceType === 'work' && !authorOfWork.has(source)) {
      authorOfWork.set(source, target);
      parentMap.set(source, target);
    }

    // Work → Passage (work contains passage)
    if (sourceType === 'work' && targetType === 'passage' && !workOfPassage.has(target)) {
      workOfPassage.set(target, source);
      parentMap.set(target, source);
    }
    if (targetType === 'work' && sourceType === 'passage' && !workOfPassage.has(source)) {
      workOfPassage.set(source, target);
      parentMap.set(source, target);
    }
  });

  let nodeIndex = 0;
  cyNodes.forEach((cyNode) => {
    const id = String(cyNode.data.id ?? cyNode.data.node_id ?? '');
    if (!id) return;

    const kgNode = cyNode.data as KGNode;
    nodeMap.set(id, kgNode);
    idToIndex.set(id, nodeIndex);

    const label = String(kgNode.label ?? id);
    // Try to get type from data, falling back to inferring from ID prefix
    let type = String(kgNode.type ?? '').toLowerCase().trim();
    if (!type || type === 'default' || !TYPE_COLORS[type]) {
      // Infer type from node ID prefix (e.g., "person_seneca_123" → "person")
      const idPrefix = id.split('_')[0]?.toLowerCase();
      if (idPrefix && TYPE_COLORS[idPrefix]) {
        type = idPrefix;
      } else {
        type = 'default';
      }
    }
    const school = String(kgNode.school ?? 'Unknown');
    const period = String(kgNode.period ?? '');
    const description = String(kgNode.description ?? '');
    const degree = degreeMap.get(id) ?? 0;

    const size = calculateNodeSize(label, type, school, degree, maxDegree);
    const labelWeight = calculateLabelWeight(label, type, degree, maxDegree);

    // Clean values for DuckDB compatibility
    const cleanSchool = school && school !== '' ? school : 'Unknown';
    const cleanPeriod = period && period !== '' ? period : 'Unknown';
    const cleanDescription = description
      ? description.replace(/[\n\r]/g, ' ').substring(0, 500)
      : '';

    // Determine cluster: find the root author for hierarchical clustering
    // Works cluster around their author, passages cluster around their work's author
    const typeLower = type.toLowerCase();
    let cluster = typeLower;  // Default: cluster by type (capitalized below)

    if (typeLower === 'person') {
      // Persons are their own cluster centers - use clean label
      cluster = label.includes('_') ? extractCleanName(id) : label;
    } else if (typeLower === 'work') {
      // Works cluster around their author
      const author = authorOfWork.get(id);
      if (author) {
        cluster = getClusterLabel(author);
      }
    } else if (typeLower === 'passage') {
      // Passages cluster around their work's author
      const work = workOfPassage.get(id);
      if (work) {
        const author = authorOfWork.get(work);
        if (author) {
          cluster = getClusterLabel(author);
        }
      }
    }

    // Capitalize type-based clusters for cleaner display
    if (cluster === typeLower) {
      cluster = typeLower.charAt(0).toUpperCase() + typeLower.slice(1);
    }

    rawPoints.push({
      index: nodeIndex,
      id,
      label,
      type,
      school: cleanSchool,
      period: cleanPeriod,
      description: cleanDescription,
      color: getNodeColor({ school: cleanSchool, type }),
      size,
      cluster,
      labelWeight,
    });

    nodeIndex++;
  });

  cyEdges.forEach((cyEdge) => {
    const sourceId = String(cyEdge.data.source ?? cyEdge.data.source_id ?? '');
    const targetId = String(cyEdge.data.target ?? cyEdge.data.target_id ?? '');
    const relationship = String(cyEdge.data.relationship ?? cyEdge.data.label ?? '');

    const sourceIndex = idToIndex.get(sourceId);
    const targetIndex = idToIndex.get(targetId);

    if (sourceIndex !== undefined && targetIndex !== undefined) {
      const sourceDegree = degreeMap.get(sourceId) ?? 0;
      const targetDegree = degreeMap.get(targetId) ?? 0;
      const avgDegree = (sourceDegree + targetDegree) / 2;
      const importance = Math.log2(Math.max(1, avgDegree)) / Math.log2(Math.max(1, maxDegree));
      const width = 0.4 + importance * 1.5;

      rawLinks.push({
        sourceId,
        targetId,
        source: sourceIndex,
        target: targetIndex,
        color: '#4a5568',
        width,
        arrow: true,
        relationship,
      });
    }
  });

  return { rawPoints, rawLinks, nodeMap, idToIndex, parentMap };
}

// GraphControls removed - using built-in Cosmograph components now

// HoverTooltip removed - using Cosmograph's built-in showHoveredPointLabel

// ============================================================================
// INNER GRAPH WITH CONTROLS (uses built-in Cosmograph components)
// ============================================================================

// View mode type
type ViewMode = 'points' | 'clusters';

function InnerGraphWithControls({
  rawPoints,
  rawLinks,
  nodeMap,
  onNodeClick,
  idToIndex,
  selectedNodeId,
  doubleClickIndex,
  onDoubleClickHandled,
  containerRef: _containerRef,
  viewMode,
  onViewModeChange,
  // Filter props (lifted state)
  selectedNodeTypes,
  setSelectedNodeTypes,
  selectedSchools,
  setSelectedSchools,
}: {
  rawPoints: RawPoint[];
  rawLinks: RawLink[];
  nodeMap: Map<string, KGNode>;
  onNodeClick?: (node: KGNode | null) => void;
  idToIndex: Map<string, number>;
  selectedNodeId?: string;
  doubleClickIndex: number | null;
  onDoubleClickHandled: () => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  // Filter props
  selectedNodeTypes: Set<string>;
  setSelectedNodeTypes: React.Dispatch<React.SetStateAction<Set<string>>>;
  selectedSchools: Set<string>;
  setSelectedSchools: React.Dispatch<React.SetStateAction<Set<string>>>;
}) {
  const { cosmograph } = useCosmograph();
  const [isRectSelectMode, setIsRectSelectMode] = useState(false);
  const [focusMode, setFocusMode] = useState<{ nodeIndex: number; label: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<RawPoint[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Filters UI state (panel open/expanded - local)
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [filtersExpanded, setFiltersExpanded] = useState({ types: true, schools: false });

  // Build adjacency map for ego network (used in focus mode)
  const adjacencyMap = useMemo(() => {
    const map = new Map<number, Set<number>>();
    rawLinks.forEach(link => {
      if (!map.has(link.source)) map.set(link.source, new Set());
      if (!map.has(link.target)) map.set(link.target, new Set());
      map.get(link.source)!.add(link.target);
      map.get(link.target)!.add(link.source);
    });
    return map;
  }, [rawLinks]);

  // Search functionality
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const query = searchQuery.toLowerCase();
    const results = rawPoints
      .filter(p =>
        p.label.toLowerCase().includes(query) ||
        p.type.toLowerCase().includes(query) ||
        p.school.toLowerCase().includes(query)
      )
      .slice(0, 10); // Limit to 10 results

    setSearchResults(results);
    setShowSearchResults(results.length > 0);
  }, [searchQuery, rawPoints]);

  // Handle search result selection
  const handleSearchResultClick = useCallback((point: RawPoint) => {
    if (cosmograph) {
      cosmograph.selectPoint(point.index, false, true);
      cosmograph.zoomToPoint(point.index, 800, 1.8, true);

      const node = nodeMap.get(point.id);
      onNodeClick?.(node ?? null);
    }
    setSearchQuery('');
    setShowSearchResults(false);
    searchInputRef.current?.blur();
  }, [cosmograph, nodeMap, onNodeClick]);

  // Cinematic zoom to a specific node index
  const cinematicZoomToNode = useCallback((pointIndex: number) => {
    if (!cosmograph) return;

    // Select the point with connected nodes for context
    cosmograph.selectPoint(pointIndex, false, true);

    // zoomToPoint(index, duration, scale, canZoomOut)
    cosmograph.zoomToPoint(pointIndex, 800, 1.8, true);
  }, [cosmograph]);

  // Focus mode: zoom tight to ego network (node + 1-hop neighbors)
  const enterFocusMode = useCallback((pointIndex: number) => {
    if (!cosmograph) return;

    const neighbors = adjacencyMap.get(pointIndex) || new Set();
    const egoNetwork = [pointIndex, ...Array.from(neighbors)];

    // Select all nodes in ego network
    cosmograph.selectPoints(egoNetwork);

    // Fit view to ego network with tight padding
    cosmograph.fitViewByIndices(egoNetwork, 600, 0.2);

    // Track focus mode
    const point = rawPoints[pointIndex];
    setFocusMode({ nodeIndex: pointIndex, label: point?.label || 'Node' });
  }, [cosmograph, adjacencyMap, rawPoints]);

  // Exit focus mode
  const exitFocusMode = useCallback(() => {
    if (!cosmograph) return;

    cosmograph.selectPoints(null);
    cosmograph.fitView(500, 0.1);
    setFocusMode(null);
  }, [cosmograph]);

  // Watch for selectedNodeId changes (e.g., from panel navigation)
  useEffect(() => {
    if (selectedNodeId && cosmograph) {
      const pointIndex = idToIndex.get(selectedNodeId);
      if (pointIndex !== undefined) {
        cinematicZoomToNode(pointIndex);
      }
    }
  }, [selectedNodeId, idToIndex, cinematicZoomToNode, cosmograph]);

  // Handle double-click to enter focus mode
  useEffect(() => {
    if (doubleClickIndex !== null && cosmograph) {
      enterFocusMode(doubleClickIndex);
      onDoubleClickHandled();
    }
  }, [doubleClickIndex, cosmograph, enterFocusMode, onDoubleClickHandled]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      // Ignore if modifier keys are pressed (browser shortcuts like Cmd+R)
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          // Exit focus mode or deselect
          if (focusMode) {
            exitFocusMode();
          } else if (cosmograph) {
            cosmograph.selectPoints(null);
            onNodeClick?.(null);
          }
          break;
        case 'r':
        case 'R':
          e.preventDefault();
          // Reset view
          if (cosmograph) {
            cosmograph.selectPoints(null);
            cosmograph.fitView(500, 0.1);
            setFocusMode(null);
            onNodeClick?.(null);
          }
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          // Fit all nodes
          if (cosmograph) {
            cosmograph.fitView(300, 0.1);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cosmograph, focusMode, exitFocusMode, onNodeClick]);

  // iOS Glassmorphism button styles
  const buttonStyle = {
    background: 'rgba(255, 255, 255, 0.08)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '12px',
    color: 'rgba(255, 255, 255, 0.8)',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
  };

  const activeButtonStyle = {
    ...buttonStyle,
    background: 'rgba(139, 92, 246, 0.4)',
    border: '1px solid rgba(139, 92, 246, 0.5)',
    color: 'white',
    boxShadow: '0 0 20px rgba(139, 92, 246, 0.3)',
  };

  // Filter toggle handlers
  const toggleNodeType = (type: string) => {
    setSelectedNodeTypes(prev => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const toggleSchool = (school: string) => {
    setSelectedSchools(prev => {
      const next = new Set(prev);
      if (next.has(school)) next.delete(school);
      else next.add(school);
      return next;
    });
  };

  const clearAllFilters = () => {
    setSelectedNodeTypes(new Set());
    setSelectedSchools(new Set());
  };

  const activeFiltersCount = selectedNodeTypes.size + selectedSchools.size;

  return (
    <>
      {/* Focus Mode Banner - GlassSurface with accent */}
      {focusMode && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-40 animate-fade-in">
          <GlassSurface
            width="auto"
            height="auto"
            borderRadius={9999}
            backgroundOpacity={0.08}
            saturation={1.2}
            blur={12}
            className="!p-0 border-violet-400/30 shadow-[0_0_30px_rgba(139,92,246,0.25)]"
          >
            <div className="flex items-center gap-3 px-6 py-3">
              <div className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse shadow-lg shadow-violet-400/50" />
              <span className="text-white text-sm font-medium">
                Focus: {focusMode.label}
              </span>
              <span className="text-white/50 text-xs">
                ({(adjacencyMap.get(focusMode.nodeIndex)?.size || 0)} connections)
              </span>
              <button
                onClick={exitFocusMode}
                className="ml-2 p-1.5 hover:bg-white/[0.15] rounded-full transition-all duration-200"
                title="Exit focus mode (Esc)"
              >
                <X className="w-4 h-4 text-white/70" />
              </button>
            </div>
          </GlassSurface>
        </div>
      )}

      {/* Search Bar + Filter Button - Top Left */}
      <div className="absolute top-4 left-4 z-30 flex items-center gap-2">
        {/* Search Input */}
        <div className="relative w-72">
          <GlassSurface
            width="100%"
            height="auto"
            borderRadius={16}
            backgroundOpacity={0.06}
            saturation={1.2}
            blur={12}
            className="!p-0 focus-within:ring-2 focus-within:ring-violet-500/20 transition-all duration-300"
          >
            <div className="relative flex items-center">
              <Search className="absolute left-4 w-4 h-4 text-white/50" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => searchQuery.length >= 2 && setShowSearchResults(true)}
                placeholder="Search nodes..."
                className="w-full pl-11 pr-11 py-3 bg-transparent text-white placeholder-white/40 text-sm focus:outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setShowSearchResults(false);
                  }}
                  className="absolute right-3 p-1.5 hover:bg-white/15 rounded-full transition-all duration-200"
                >
                  <X className="w-4 h-4 text-white/50" />
                </button>
              )}
            </div>
          </GlassSurface>

          {/* Search Results Dropdown */}
          {showSearchResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 z-50">
              <div className="bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-2xl max-h-80 overflow-y-auto shadow-2xl">
                <div>
                  {searchResults.map((result) => (
                    <button
                      key={result.id}
                      onClick={() => handleSearchResultClick(result)}
                      className="w-full px-4 py-3.5 text-left hover:bg-white/[0.08] transition-all duration-200 border-b border-white/[0.08] last:border-b-0 group"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3.5 h-3.5 rounded-full flex-shrink-0 ring-2 ring-white/20"
                          style={{ backgroundColor: result.color, boxShadow: `0 0 12px ${result.color}60` }}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate group-hover:text-violet-300 transition-colors">
                            {result.label}
                          </p>
                          <p className="text-white/40 text-xs capitalize truncate">
                            {result.type} • {result.school !== 'Unknown' ? result.school : result.period}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Filter Button - Inline with search */}
        <button
          onClick={() => setIsFiltersOpen(!isFiltersOpen)}
          className={`flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 backdrop-blur-xl ${
            isFiltersOpen || activeFiltersCount > 0
              ? 'bg-violet-500/30 text-white border border-violet-400/40'
              : 'bg-slate-900/80 text-white/60 hover:text-white hover:bg-slate-800/80 border border-white/10'
          }`}
        >
          <Filter size={12} />
          <span>Filter</span>
          {activeFiltersCount > 0 && (
            <span className="px-1.5 py-0.5 bg-violet-500/60 rounded-full text-[10px] font-semibold min-w-[18px] text-center">
              {activeFiltersCount}
            </span>
          )}
        </button>
      </div>

      {/* Filters Panel - Compact */}
      {isFiltersOpen && (
        <div className="absolute top-16 left-4 z-40 w-56 animate-in slide-in-from-top-2 duration-200">
          <div className="bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
              <span className="text-white/80 text-xs font-medium">Filters</span>
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearAllFilters}
                  className="text-violet-400 hover:text-violet-300 text-[10px] font-medium"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Node Types Section */}
            <div className="border-b border-white/10">
              <button
                onClick={() => setFiltersExpanded(prev => ({ ...prev, types: !prev.types }))}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 transition-colors"
              >
                <span className="text-white/60 text-[10px] uppercase tracking-wider font-medium">Types</span>
                {filtersExpanded.types ? <ChevronUp size={12} className="text-white/40" /> : <ChevronDown size={12} className="text-white/40" />}
              </button>
              {filtersExpanded.types && (
                <div className="px-2 pb-2 flex flex-wrap gap-1">
                  {NODE_TYPE_FILTERS.map(({ value, label, color }) => (
                    <button
                      key={value}
                      onClick={() => toggleNodeType(value)}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all ${
                        selectedNodeTypes.has(value)
                          ? 'bg-white/15 text-white'
                          : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70'
                      }`}
                    >
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: color }}
                      />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Schools Section */}
            <div>
              <button
                onClick={() => setFiltersExpanded(prev => ({ ...prev, schools: !prev.schools }))}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 transition-colors"
              >
                <span className="text-white/60 text-[10px] uppercase tracking-wider font-medium">Schools</span>
                {filtersExpanded.schools ? <ChevronUp size={12} className="text-white/40" /> : <ChevronDown size={12} className="text-white/40" />}
              </button>
              {filtersExpanded.schools && (
                <div className="px-2 pb-2 flex flex-wrap gap-1">
                  {SCHOOL_FILTERS.map(({ value, label, color }) => (
                    <button
                      key={value}
                      onClick={() => toggleSchool(value)}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all ${
                        selectedSchools.has(value)
                          ? 'bg-white/15 text-white'
                          : 'bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/70'
                      }`}
                    >
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: color }}
                      />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle - Below ModeSwitcher */}
      <div className="absolute top-16 right-4 z-30">
        <div className="flex gap-1 p-1 bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-xl">
          <button
            onClick={() => onViewModeChange('points')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === 'points'
                ? 'bg-violet-500/40 text-white'
                : 'text-white/50 hover:text-white hover:bg-white/10'
            }`}
            title="Show node labels"
          >
            <Tag size={12} />
            <span>Labels</span>
          </button>
          <button
            onClick={() => onViewModeChange('clusters')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === 'clusters'
                ? 'bg-violet-500/40 text-white'
                : 'text-white/50 hover:text-white hover:bg-white/10'
            }`}
            title="Group by school"
          >
            <Layers size={12} />
            <span>Clusters</span>
          </button>
        </div>
      </div>

      {/* Built-in Control Buttons - Bottom Left */}
      <div className="absolute bottom-20 left-4 z-20 flex flex-col gap-1">
        <CosmographButtonZoomInOut style={buttonStyle} />
        <CosmographButtonFitView style={buttonStyle} />
        <CosmographButtonPlayPause
          style={buttonStyle}
          styleIsRunning={activeButtonStyle}
        />
        <CosmographButtonRectangularSelection
          style={isRectSelectMode ? activeButtonStyle : buttonStyle}
          onClick={() => setIsRectSelectMode(!isRectSelectMode)}
        />
      </div>

    </>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function CosmographKGVisualizer({
  onNodeClick,
  selectedNodeId,
  className = '',
}: CosmographKGVisualizerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawPoints, setRawPoints] = useState<RawPoint[]>([]);
  const [rawLinks, setRawLinks] = useState<RawLink[]>([]);
  const [nodeMap, setNodeMap] = useState<Map<string, KGNode>>(new Map());
  const [idToIndex, setIdToIndex] = useState<Map<string, number>>(new Map());
  const [cosmographConfig, setCosmographConfig] = useState<Partial<CosmographConfig> | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('points');
  const [baseConfig, setBaseConfig] = useState<Partial<CosmographConfig> | null>(null);

  // Filter state (lifted from InnerGraphWithControls)
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<Set<string>>(new Set());
  const [selectedSchools, setSelectedSchools] = useState<Set<string>>(new Set());

  const cosmographRef = useRef<CosmographRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rawPointsRef = useRef<RawPoint[]>([]);
  const nodeMapRef = useRef<Map<string, KGNode>>(new Map());
  const idToIndexRef = useRef<Map<string, number>>(new Map());
  const onNodeClickRef = useRef(onNodeClick);
  const [doubleClickIndex, setDoubleClickIndex] = useState<number | null>(null);

  // Track clicks for double-click detection
  const lastClickRef = useRef<{ time: number; index: number | null }>({ time: 0, index: null });
  const DOUBLE_CLICK_THRESHOLD = 350; // ms

  // Guard against React Strict Mode double-mounting
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    rawPointsRef.current = rawPoints;
  }, [rawPoints]);

  useEffect(() => {
    nodeMapRef.current = nodeMap;
  }, [nodeMap]);

  useEffect(() => {
    idToIndexRef.current = idToIndex;
  }, [idToIndex]);

  useEffect(() => {
    onNodeClickRef.current = onNodeClick;
  }, [onNodeClick]);

  // Click handler with double-click detection
  const handleClick = useCallback((
    pointIndex: number | undefined,
    _pointPosition: [number, number] | undefined,
    _event: MouseEvent
  ) => {
    const now = Date.now();
    const lastClick = lastClickRef.current;

    // Check for double-click on the same node
    if (
      pointIndex !== undefined &&
      pointIndex !== null &&
      lastClick.index === pointIndex &&
      now - lastClick.time < DOUBLE_CLICK_THRESHOLD
    ) {
      // DOUBLE-CLICK detected!
      console.log('🌌 Cosmograph: Double-click detected on node', pointIndex);
      setDoubleClickIndex(pointIndex);
      lastClickRef.current = { time: 0, index: null }; // Reset
      return;
    }

    // Update last click tracking
    lastClickRef.current = { time: now, index: pointIndex ?? null };

    // Handle click on empty space
    if (pointIndex === undefined || pointIndex === null) {
      console.log('🌌 Cosmograph: Click on empty space');
      onNodeClickRef.current?.(null);
      if (cosmographRef.current) {
        cosmographRef.current.selectPoints(null);
      }
      return;
    }

    // Single click - select and zoom
    const point = rawPointsRef.current[pointIndex];
    if (point) {
      console.log('🌌 Cosmograph: Single click on node', point.label);
      const node = nodeMapRef.current.get(point.id);
      onNodeClickRef.current?.(node ?? null);

      // Cinematic zoom on click with connected nodes highlighted
      if (cosmographRef.current) {
        cosmographRef.current.selectPoint(pointIndex, false, true);
        cosmographRef.current.zoomToPoint(pointIndex, 800, 1.8, true);
      }
    }
  }, []);

  // Hover handled by Cosmograph's built-in showHoveredPointLabel

  // Load data (with guard against React Strict Mode double-mounting)
  useEffect(() => {
    // Skip if already loaded (React Strict Mode protection)
    if (hasLoadedRef.current) {
      console.log('🌌 Cosmograph: Skipping duplicate load (Strict Mode)');
      return;
    }
    hasLoadedRef.current = true;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        console.log('🌌 Cosmograph: Fetching data...');
        const data = await apiClient.getCytoscapeData();
        console.log('🌌 Cosmograph: Data received', {
          nodes: data.elements?.nodes?.length ?? 0,
          edges: data.elements?.edges?.length ?? 0
        });

        if (!data.elements?.nodes?.length) {
          throw new Error('No graph data available');
        }

        // Convert Cytoscape data to our internal format (includes hierarchy maps)
        const { rawPoints: allPoints, rawLinks: allLinks, nodeMap: nMap, idToIndex: idx, parentMap } = convertCytoscapeData(data);
        console.log('🌌 Cosmograph: Converted data', { points: allPoints.length, links: allLinks.length, hierarchyNodes: parentMap.size });

        // Use full dataset
        const points = allPoints;
        const links = allLinks;

        // Store our metadata
        setRawPoints(points);
        setRawLinks(links);
        setNodeMap(nMap);
        setIdToIndex(idx);

        // Build id-to-index map for links
        const idToIndexMap = new Map<string, number>();
        points.forEach((p, i) => idToIndexMap.set(p.id, i));

        // Build type map for variable link distances
        const nodeTypeById = new Map<string, string>();
        points.forEach(p => nodeTypeById.set(p.id, p.type.toLowerCase()));

        // ================================================================
        // D3-FORCE-WEBGPU: HIERARCHICAL layout
        // Authors (persons) at center, works orbit authors, passages orbit works
        // ================================================================
        console.log('🌌 Cosmograph: Starting hierarchical d3-force simulation...');

        const spaceSize = 8192; // Large space to avoid boundary issues

        // Group nodes by cluster (author name or type)
        const clusterCounts = new Map<string, number>();
        points.forEach(p => {
          clusterCounts.set(p.cluster, (clusterCounts.get(p.cluster) || 0) + 1);
        });

        // Position cluster centers (authors) in a large circle
        const clusterPositions = new Map<string, { x: number; y: number; count: number }>();
        const clusters = Array.from(clusterCounts.keys());
        const clusterRadius = spaceSize * 0.35;
        clusters.forEach((cluster, i) => {
          const angle = (i / clusters.length) * 2 * Math.PI;
          clusterPositions.set(cluster, {
            x: Math.cos(angle) * clusterRadius,
            y: Math.sin(angle) * clusterRadius,
            count: 0
          });
        });

        // Create d3-force nodes with HIERARCHICAL initial positions
        interface D3Node {
          index: number;
          id: string;
          label: string;
          type: string;
          color: string;
          size: number;
          radius: number;
          x: number;
          y: number;
          vx?: number;
          vy?: number;
          cluster: string;
        }

        const d3Nodes: D3Node[] = points.map((p, i) => {
          const cluster = clusterPositions.get(p.cluster) || { x: 0, y: 0, count: 0 };
          const typeLower = p.type.toLowerCase();

          // HIERARCHICAL positioning based on node type
          let x: number, y: number;

          if (typeLower === 'person') {
            // Authors at cluster CENTER
            x = cluster.x;
            y = cluster.y;
          } else if (typeLower === 'work') {
            // Works in INNER orbit around author (close)
            const workAngle = cluster.count * 0.8;
            const workRadius = 60 + Math.random() * 40; // 60-100 from center
            x = cluster.x + Math.cos(workAngle) * workRadius;
            y = cluster.y + Math.sin(workAngle) * workRadius;
          } else if (typeLower === 'passage') {
            // Passages in TIGHT orbit around works (very close)
            const passageAngle = cluster.count * 0.3;
            const passageRadius = 15 + Math.random() * 20; // 15-35 from work
            // Offset from cluster center
            const workOffset = 80 + (cluster.count % 10) * 10;
            x = cluster.x + Math.cos(passageAngle) * workOffset + Math.cos(passageAngle * 3) * passageRadius;
            y = cluster.y + Math.sin(passageAngle) * workOffset + Math.sin(passageAngle * 3) * passageRadius;
          } else {
            // Other nodes (concepts, arguments) - spread in outer area
            const otherAngle = cluster.count * 0.5;
            const otherRadius = 150 + Math.sqrt(cluster.count) * 30;
            x = cluster.x + Math.cos(otherAngle) * otherRadius;
            y = cluster.y + Math.sin(otherAngle) * otherRadius;
          }

          cluster.count++;

          return {
            index: i,
            id: p.id,
            label: p.label,
            type: typeLower,
            color: p.color,
            size: p.size,
            radius: (p.size || 5) * 1.5,
            x,
            y,
            cluster: p.cluster,
          };
        });

        // Create d3-force links with VARIABLE distances based on relationship type
        const d3Links = links.map(l => {
          const sourceType = nodeTypeById.get(l.sourceId) || '';
          const targetType = nodeTypeById.get(l.targetId) || '';

          // Determine link distance based on node types
          let distance: number;
          if ((sourceType === 'work' && targetType === 'passage') ||
              (sourceType === 'passage' && targetType === 'work')) {
            // Work ↔ Passage: VERY short (tight orbits)
            distance = 15;
          } else if ((sourceType === 'person' && targetType === 'work') ||
                     (sourceType === 'work' && targetType === 'person')) {
            // Person ↔ Work: Medium short (works orbit authors)
            distance = 50;
          } else if (sourceType === 'passage' || targetType === 'passage') {
            // Other passage links: short
            distance = 25;
          } else {
            // Other links: medium
            distance = 100;
          }

          return {
            source: idToIndexMap.get(l.sourceId) ?? 0,
            target: idToIndexMap.get(l.targetId) ?? 0,
            distance,
          };
        }).filter(l => l.source !== l.target);

        // Create simulation with HIERARCHICAL forces - SPREAD OUT
        const simulation = forceSimulation(d3Nodes)
          .force('charge', forceManyBody().strength((d: D3Node) => {
            // STRONG repulsion to spread clusters apart
            if (d.type === 'person') return -800;  // Authors repel VERY strongly
            if (d.type === 'work') return -200;
            if (d.type === 'passage') return -50;
            return -150;
          }))
          .force('collide', forceCollide<D3Node>().radius(d => d.radius * 2).strength(0.9).iterations(3))
          .force('link', forceLink(d3Links).distance((d: { distance: number }) => d.distance).strength(0.4))
          .force('center', forceCenter(0, 0))
          .force('x', forceX(0).strength(0.005))  // Very weak center pull
          .force('y', forceY(0).strength(0.005))
          .alphaDecay(0.015)
          .velocityDecay(0.35);

        // Run simulation longer for better settling
        const maxIterations = 500;
        console.log(`🌌 Cosmograph: Running ${maxIterations} hierarchical simulation ticks...`);

        for (let i = 0; i < maxIterations; i++) {
          simulation.tick();
        }
        simulation.stop();

        console.log('🌌 Cosmograph: Hierarchical simulation complete!');

        // Extract final positions from simulation with label weights for hierarchy
        const simplePoints = d3Nodes.map((node, i) => {
          const originalPoint = points[i];
          return {
            index: i,
            id: node.id,
            label: node.label,
            color: node.color,
            size: node.size,
            x: node.x,
            y: node.y,
            labelWeight: originalPoint.labelWeight,  // For hierarchical labels
            cluster: originalPoint.cluster,          // For cluster labels (school)
          };
        });

        // Links with both ID and index references + colors for bi-color edges
        const pointColorMap = new Map<string, string>();
        points.forEach(p => pointColorMap.set(p.id, p.color));

        const simpleLinks = links.map(l => ({
          source: l.sourceId,
          target: l.targetId,
          sourceIndex: idToIndexMap.get(l.sourceId) ?? 0,
          targetIndex: idToIndexMap.get(l.targetId) ?? 0,
          sourceColor: pointColorMap.get(l.sourceId) || '#60a5fa',
          targetColor: pointColorMap.get(l.targetId) || '#60a5fa',
        })).filter(l => l.source !== l.target); // Filter self-loops

        console.log('🌌 Cosmograph: Simple data format', {
          points: simplePoints.length,
          links: simpleLinks.length,
          samplePoint: simplePoints[0],
          sampleLink: simpleLinks[0]
        });

        // Full Cosmograph v2 base config with all features
        // Simulation settings will be applied via useEffect based on viewMode
        setBaseConfig({
          points: simplePoints,
          links: simpleLinks,

          // Point identification (required - pointIndexBy is critical!)
          pointIndexBy: 'index',
          pointIdBy: 'id',
          pointColorBy: 'color',
          pointSizeBy: 'size',

          // Link identification (required - both ID and Index versions needed!)
          linkSourceBy: 'source',
          linkTargetBy: 'target',
          linkSourceIndexBy: 'sourceIndex',
          linkTargetIndexBy: 'targetIndex',

          // Link styling - thin edges
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          linkColorByFn: (l: any) => getEdgeColor(l.sourceColor, l.targetColor),
          linkDefaultWidth: 0.3,
          linkDefaultArrows: true,
          linkArrowsSizeScale: 0.3,

          // Canvas settings - Large space for hierarchical layout
          backgroundColor: '#020617',
          spaceSize: 8192,               // Large space to avoid boundary clipping
          scalePointsOnZoom: true,       // Nodes shrink when zoomed out (prevents visual overlap)
          scaleLinksOnZoom: true,        // Edges also scale with zoom
          pointSizeRange: [3, 40],       // Match our sizes (major figures up to 39px)
          pointSizeScale: 1.0,           // No additional scaling
          rescalePositions: false,       // Keep d3-force positions as-is

          // Labels - hierarchical display based on label weight
          pointLabelBy: 'label',
          pointLabelWeightBy: 'labelWeight',     // Use our hierarchy weights!
          showLabels: true,
          showDynamicLabels: true,
          showTopLabels: true,                   // Show highest-weighted labels
          showTopLabelsLimit: 50,                // Limit top labels for readability
          showHoveredPointLabel: true,
          pointLabelClassName: 'cosmograph-point-label',
          hoveredPointLabelClassName: 'cosmograph-hovered-label',

          // Cluster labels for philosophical schools
          pointClusterBy: 'cluster',

          // Interaction - enable dragging!
          enableDrag: true,
          selectPointOnClick: true,
          focusPointOnClick: true,
          renderHoveredPointRing: true,
          hoveredPointRingColor: '#8b5cf6',

          // Selection & hover behavior
          pointGreyoutOpacity: 0.15,
          linkGreyoutOpacity: 0.05,

          // Initial view
          fitViewOnInit: true,
          fitViewDelay: 200,
        });

        setIsLoading(false);
        console.log('🌌 Cosmograph: Ready!');
      } catch (err) {
        console.error('🌌 Cosmograph: Failed to load graph data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load graph');
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter points and links based on selected filters
  const { filteredPoints, filteredLinks, filteredIdToIndex } = useMemo(() => {
    // No filters active - return original data
    if (selectedNodeTypes.size === 0 && selectedSchools.size === 0) {
      return {
        filteredPoints: rawPoints,
        filteredLinks: rawLinks,
        filteredIdToIndex: idToIndex,
      };
    }

    // Filter points based on selected types and schools
    const filtered = rawPoints.filter(point => {
      const typeLower = point.type.toLowerCase();
      const matchesType = selectedNodeTypes.size === 0 || selectedNodeTypes.has(typeLower);
      const matchesSchool = selectedSchools.size === 0 || selectedSchools.has(point.school);
      return matchesType && matchesSchool;
    });

    // Create new index mapping for filtered points
    const newIdToIndex = new Map<string, number>();
    filtered.forEach((point, newIndex) => {
      newIdToIndex.set(point.id, newIndex);
    });

    // Create a set of filtered point IDs for quick lookup
    const filteredIds = new Set(filtered.map(p => p.id));

    // Filter links - only include if both source and target are in filtered points
    // Also update indices to match new filtered point indices
    const newLinks = rawLinks
      .filter(link => filteredIds.has(link.sourceId) && filteredIds.has(link.targetId))
      .map(link => ({
        ...link,
        source: newIdToIndex.get(link.sourceId) ?? 0,
        target: newIdToIndex.get(link.targetId) ?? 0,
      }));

    // Update points with new indices
    const reindexedPoints = filtered.map((point, newIndex) => ({
      ...point,
      index: newIndex,
    }));

    return {
      filteredPoints: reindexedPoints,
      filteredLinks: newLinks,
      filteredIdToIndex: newIdToIndex,
    };
  }, [rawPoints, rawLinks, idToIndex, selectedNodeTypes, selectedSchools]);

  // Build final cosmographConfig based on viewMode and filtered data
  // This allows toggling between point labels and cluster views with different simulation settings
  useEffect(() => {
    if (!baseConfig) return;
    if (filteredPoints.length === 0) return; // Don't update if no points

    // Simulation settings based on view mode
    // HIERARCHICAL LAYOUT: Authors → Works → Passages
    // d3-force already positioned nodes hierarchically - Cosmograph should PRESERVE not override
    const simulationConfig = viewMode === 'clusters'
      ? {
          // CLUSTER VIEW - Shows author clusters with their works/passages
          // Gentle center gravity like official Cosmos example (0.1)
          simulationGravity: 0.08,          // Gentle center pull to prevent drift
          simulationCluster: 0.3,           // Light clustering
          simulationRepulsion: 40,          // STRONG repulsion to spread clusters
          simulationLinkSpring: 0.1,        // Light spring
          simulationLinkDistance: 100,      // Medium-long links
          simulationFriction: 0.95,         // Very high friction to preserve positions
          simulationDecay: 8000,            // Very slow decay
          disableSimulation: false,         // Enable for interactivity
          showClusterLabels: true,          // Show cluster labels (author names)
          scaleClusterLabels: true,         // Scale cluster labels with zoom
          showTopLabels: true,              // Enable labels to show when zoomed in
          showDynamicLabels: true,          // Dynamic labels appear on zoom
          showTopLabelsLimit: 100,          // Show more labels when zoomed in
        }
      : {
          // LABELS VIEW - Shows hierarchical structure with readable labels
          // Gentle center gravity like official Cosmos example (0.1)
          simulationGravity: 0.08,          // Gentle center pull to prevent drift
          simulationRepulsion: 35,          // Strong repulsion for spread
          simulationLinkSpring: 0.08,       // Light spring
          simulationLinkDistance: 80,       // Medium links
          simulationFriction: 0.95,         // Very high friction to preserve positions
          simulationDecay: 8000,            // Very slow decay
          disableSimulation: false,         // Enable for drag interactivity
          showClusterLabels: false,         // Hide cluster labels in labels view
          scaleClusterLabels: false,
          showTopLabels: true,              // Show hierarchical labels
          showTopLabelsLimit: 50,           // Show many labels
        };

    console.log(`🌌 Cosmograph: Setting ${viewMode} view mode with ${filteredPoints.length} points, ${filteredLinks.length} links`);

    // Build config with filtered data
    // Need to create properly formatted points/links for Cosmograph
    const pointColorMap = new Map<string, string>();
    filteredPoints.forEach(p => pointColorMap.set(p.id, p.color));

    const simplePoints = filteredPoints.map((p) => ({
      index: p.index,
      id: p.id,
      label: p.label,
      color: p.color,
      size: p.size,
      x: (baseConfig.points as { x: number }[])?.[rawPoints.findIndex(rp => rp.id === p.id)]?.x ?? 0,
      y: (baseConfig.points as { y: number }[])?.[rawPoints.findIndex(rp => rp.id === p.id)]?.y ?? 0,
      labelWeight: p.labelWeight,
      cluster: p.cluster,
    }));

    const simpleLinks = filteredLinks.map(l => ({
      source: l.sourceId,
      target: l.targetId,
      sourceIndex: l.source,
      targetIndex: l.target,
      sourceColor: pointColorMap.get(l.sourceId) || '#60a5fa',
      targetColor: pointColorMap.get(l.targetId) || '#60a5fa',
    }));

    setCosmographConfig({
      ...baseConfig,
      points: simplePoints,
      links: simpleLinks,
      ...simulationConfig,
    });
  }, [baseConfig, viewMode, filteredPoints, filteredLinks, rawPoints]);

  return (
    <div ref={containerRef} className={`relative w-full h-full bg-[#030712] ${className}`}>
      {/* Loading state */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center z-50">
          <div className="flex flex-col items-center gap-6">
            <div className="relative w-24 h-24">
              <div className="absolute inset-0 rounded-full border-2 border-violet-500/30 animate-ping" />
              <div className="absolute inset-2 rounded-full border-2 border-cyan-500/40 animate-ping" style={{ animationDelay: '0.2s' }} />
              <div className="absolute inset-4 rounded-full border-2 border-violet-500/50 animate-pulse" />
              <div className="absolute inset-6 rounded-full bg-gradient-to-br from-violet-500/30 to-cyan-500/30 animate-pulse" />
              <div className="absolute inset-8 rounded-full bg-white/10 backdrop-blur" />
            </div>
            <div className="text-center">
              <p className="text-violet-400 text-lg font-medium tracking-wide animate-pulse">
                Loading Knowledge Graph
              </p>
              <p className="text-white/40 text-sm mt-2">
                Preparing GPU-accelerated visualization...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center z-50">
          <div className="flex flex-col items-center gap-6 max-w-md text-center p-8">
            <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/30">
              <svg className="w-10 h-10 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <p className="text-red-400 font-medium text-lg">Failed to Load</p>
              <p className="text-white/50 text-sm mt-2">{error}</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-red-500/20 text-red-300 rounded-xl hover:bg-red-500/30 transition-all border border-red-500/30 font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Graph visualization */}
      {!isLoading && !error && cosmographConfig && (
        <CosmographProvider>
          <Cosmograph
            ref={cosmographRef}
            {...cosmographConfig}
            onClick={handleClick}
            style={{ width: '100%', height: '100%' }}
          />
          <InnerGraphWithControls
            rawPoints={filteredPoints}
            rawLinks={filteredLinks}
            nodeMap={nodeMap}
            onNodeClick={onNodeClick}
            idToIndex={filteredIdToIndex}
            selectedNodeId={selectedNodeId}
            doubleClickIndex={doubleClickIndex}
            onDoubleClickHandled={() => setDoubleClickIndex(null)}
            containerRef={containerRef}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            selectedNodeTypes={selectedNodeTypes}
            setSelectedNodeTypes={setSelectedNodeTypes}
            selectedSchools={selectedSchools}
            setSelectedSchools={setSelectedSchools}
          />
        </CosmographProvider>
      )}

      {/* Stats pill - GlassSurface */}
      {!isLoading && !error && rawPoints.length > 0 && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
          <GlassSurface
            width="auto"
            height="auto"
            borderRadius={9999}
            backgroundOpacity={0.08}
            saturation={1.2}
            blur={12}
            className="!p-0"
          >
            <div className="flex items-center gap-4 px-6 py-3">
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse shadow-lg shadow-violet-400/50" />
                <span className="text-white font-semibold">
                  {filteredPoints.length.toLocaleString()}
                  {filteredPoints.length !== rawPoints.length && (
                    <span className="text-white/40 font-normal">/{rawPoints.length.toLocaleString()}</span>
                  )}
                </span>
                <span className="text-white/50 text-sm">nodes</span>
              </div>
              <div className="w-px h-5 bg-white/[0.15]" />
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/50" />
                <span className="text-white font-semibold">
                  {filteredLinks.length.toLocaleString()}
                  {filteredLinks.length !== rawLinks.length && (
                    <span className="text-white/40 font-normal">/{rawLinks.length.toLocaleString()}</span>
                  )}
                </span>
                <span className="text-white/50 text-sm">edges</span>
              </div>
            </div>
          </GlassSurface>
        </div>
      )}

      {/* Legend - Node Types - Compact */}
      {!isLoading && !error && rawPoints.length > 0 && (
        <div className="absolute bottom-16 right-4 z-10 hidden lg:block">
          <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-xl p-3 max-h-72 overflow-y-auto">
            <p className="text-white/40 text-[10px] uppercase tracking-wider mb-2 font-medium">Legend</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
              {Object.entries(TYPE_COLORS).filter(([k]) => k !== 'default').map(([name, color]) => (
                <div key={name} className="flex items-center gap-1.5">
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-white/60 text-[10px] capitalize">
                    {name.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Keyboard hints - Minimal */}
      {!isLoading && !error && (
        <div className="absolute bottom-3 left-14 z-10 hidden md:block">
          <div className="flex items-center gap-3 text-white/30 text-[10px]">
            <span><kbd className="px-1.5 py-0.5 bg-white/10 rounded text-white/50 font-medium">scroll</kbd> zoom</span>
            <span><kbd className="px-1.5 py-0.5 bg-white/10 rounded text-white/50 font-medium">drag</kbd> pan</span>
            <span><kbd className="px-1.5 py-0.5 bg-white/10 rounded text-white/50 font-medium">click</kbd> select</span>
          </div>
        </div>
      )}
    </div>
  );
}
