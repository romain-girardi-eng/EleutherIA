/**
 * Knowledge Graph Analytics Service
 * Port of Python kg_analytics.py to TypeScript for Cloudflare Workers
 */

import { DatabaseService } from './database';
import { sanitizeNodePayload } from '../utils/graph';

export interface KGNode {
  id: string;
  label?: string;
  type?: string;
  period?: string;
  school?: string;
  description?: string;
  dates?: string;
  approximate_dates?: string;
  floruit?: string;
  birth?: string;
  death?: string;
  date?: string;
  year?: number;
  scholarly_role?: string;
  category?: string;
  [key: string]: any;
}

export interface KGEdge {
  id?: string;
  source: string;
  target: string;
  relation?: string;
  [key: string]: any;
}

export interface KGFilterState {
  nodeTypes?: string[];
  periods?: string[];
  schools?: string[];
  relations?: string[];
  searchTerm?: string;
}

const PERIOD_METADATA: Record<string, { label: string; start: number; end: number }> = {
  'Presocratic': { label: 'Presocratic', start: -600, end: -450 },
  'Classical Greek': { label: 'Classical Greek', start: -450, end: -323 },
  'Hellenistic Greek': { label: 'Hellenistic Greek', start: -323, end: -31 },
  'Roman Republican': { label: 'Roman Republican', start: -146, end: -27 },
  'Roman Imperial': { label: 'Roman Imperial', start: -27, end: 300 },
  'Patristic': { label: 'Patristic', start: 150, end: 450 },
  'Late Antiquity': { label: 'Late Antiquity', start: 300, end: 600 },
};

export class KGAnalyticsService {
  constructor(private db: DatabaseService) {}

  /**
   * Apply filters to nodes and edges
   */
  private async applyFilters(filters?: KGFilterState): Promise<{ nodes: KGNode[]; edges: KGEdge[] }> {
    const [nodesResult, edgesResult] = await Promise.all([
      this.db.getNodes(),
      this.db.getEdges(),
    ]);

    let nodes = nodesResult.rows.map(sanitizeNodePayload) as KGNode[];
    let edges = edgesResult.rows as KGEdge[];

    if (!filters) {
      return { nodes, edges };
    }

    const { nodeTypes, periods, schools, relations, searchTerm } = filters;

    // Filter nodes
    if (nodeTypes && nodeTypes.length > 0) {
      nodes = nodes.filter(n => nodeTypes.includes(n.type || ''));
    }
    if (periods && periods.length > 0) {
      nodes = nodes.filter(n => periods.includes(n.period || ''));
    }
    if (schools && schools.length > 0) {
      nodes = nodes.filter(n => schools.includes(n.school || ''));
    }
    if (searchTerm && searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      nodes = nodes.filter(n =>
        (n.label || '').toLowerCase().includes(term) ||
        (n.description || '').toLowerCase().includes(term)
      );
    }

    // Create node ID set for edge filtering
    const nodeIds = new Set(nodes.map(n => n.id));

    // Filter edges
    if (relations && relations.length > 0) {
      edges = edges.filter(e => relations.includes(e.relation || ''));
    }
    edges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));

    return { nodes, edges };
  }

  /**
   * Build timeline overview
   */
  async buildTimelineOverview(filters?: KGFilterState) {
    const { nodes, edges } = await this.applyFilters(filters);

    // Group nodes by period
    const periodMap = new Map<string, any>();
    const typeCounts: Record<string, number> = {};

    for (const node of nodes) {
      const periodKey = node.period || 'Unspecified';
      const periodMeta = PERIOD_METADATA[periodKey];

      if (!periodMap.has(periodKey)) {
        periodMap.set(periodKey, {
          key: periodKey,
          label: periodMeta?.label || periodKey,
          startYear: periodMeta?.start || null,
          endYear: periodMeta?.end || null,
          counts: {} as Record<string, number>,
          nodes: [],
        });
      }

      const period = periodMap.get(periodKey)!;
      const nodeType = node.type || 'unknown';
      period.counts[nodeType] = (period.counts[nodeType] || 0) + 1;
      typeCounts[nodeType] = (typeCounts[nodeType] || 0) + 1;

      // Get node year
      const year = this.inferNodeYear(node, period.startYear, period.endYear);

      // Find related edges
      const relatedEdges = edges.filter(e => e.source === node.id || e.target === node.id);
      const relationCounts: Record<string, number> = {};
      for (const edge of relatedEdges) {
        const rel = edge.relation || 'unknown';
        relationCounts[rel] = (relationCounts[rel] || 0) + 1;
      }
      const topRelations = Object.entries(relationCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([rel]) => rel);

      period.nodes.push({
        id: node.id,
        label: node.label,
        type: node.type,
        period: node.period,
        school: node.school,
        startYear: year,
        endYear: year,
        description: node.description,
        relationCount: relatedEdges.length,
        relatedTypes: topRelations,
      });
    }

    // Sort periods chronologically
    const periods = Array.from(periodMap.values()).sort((a, b) => {
      if (a.startYear === null) return 1;
      if (b.startYear === null) return -1;
      return a.startYear - b.startYear;
    });

    // Sort nodes within each period
    for (const period of periods) {
      period.nodes.sort((a: any, b: any) => {
        if (a.startYear === null) return 1;
        if (b.startYear === null) return -1;
        return a.startYear - b.startYear;
      });
    }

    return {
      periods,
      totals: {
        nodes: nodes.length,
        edges: edges.length,
        byType: typeCounts,
      },
      range: {
        minYear: nodes.reduce((min, n) => {
          const y = this.inferNodeYear(n);
          return y !== null && (min === null || y < min) ? y : min;
        }, null as number | null),
        maxYear: nodes.reduce((max, n) => {
          const y = this.inferNodeYear(n);
          return y !== null && (max === null || y > max) ? y : max;
        }, null as number | null),
      },
    };
  }

  /**
   * Build influence matrix
   */
  async buildInfluenceMatrix(filters?: KGFilterState, maxSchools = 12, maxRelations = 12) {
    const { nodes, edges } = await this.applyFilters(filters);

    // Count schools and relations
    const schoolCounts: Record<string, number> = {};
    const relationCounts: Record<string, number> = {};

    for (const node of nodes) {
      if (node.school) {
        schoolCounts[node.school] = (schoolCounts[node.school] || 0) + 1;
      }
    }

    for (const edge of edges) {
      if (edge.relation) {
        relationCounts[edge.relation] = (relationCounts[edge.relation] || 0) + 1;
      }
    }

    // Get top schools and relations
    const topSchools = Object.entries(schoolCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, maxSchools)
      .map(([school]) => school);

    const topRelations = Object.entries(relationCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, maxRelations)
      .map(([rel]) => rel);

    if (topSchools.length === 0 || topRelations.length === 0) {
      return {
        rows: [],
        columns: [],
        cells: [],
        totals: {
          relationsConsidered: 0,
          schoolsCovered: 0,
          edgesMapped: 0,
        },
      };
    }

    // Create node lookup by school
    const nodesBySchool = new Map<string, Set<string>>();
    for (const node of nodes) {
      if (node.school && topSchools.includes(node.school)) {
        if (!nodesBySchool.has(node.school)) {
          nodesBySchool.set(node.school, new Set());
        }
        nodesBySchool.get(node.school)!.add(node.id);
      }
    }

    // Build cell map
    const cellMap = new Map<string, any>();
    let edgesMapped = 0;

    for (const edge of edges) {
      if (!edge.relation || !topRelations.includes(edge.relation)) continue;

      // Find school for this edge
      let school: string | null = null;
      for (const [s, nodeIds] of nodesBySchool.entries()) {
        if (nodeIds.has(edge.source) || nodeIds.has(edge.target)) {
          school = s;
          break;
        }
      }

      if (!school) continue;

      const key = `${school}::${edge.relation}`;
      if (!cellMap.has(key)) {
        cellMap.set(key, {
          rowKey: school,
          columnKey: edge.relation,
          count: 0,
          sampleEdges: [],
        });
      }

      const cell = cellMap.get(key)!;
      cell.count++;
      if (cell.sampleEdges.length < 5) {
        cell.sampleEdges.push(edge.id || `${edge.source}->${edge.target}`);
      }
      edgesMapped++;
    }

    return {
      rows: topSchools.map((school, idx) => ({
        key: school,
        label: school,
        type: 'school',
        order: idx,
      })),
      columns: topRelations.map((rel, idx) => ({
        key: rel,
        label: rel.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        type: 'relation',
        order: idx,
      })),
      cells: Array.from(cellMap.values()),
      totals: {
        relationsConsidered: topRelations.length,
        schoolsCovered: topSchools.length,
        edgesMapped,
      },
    };
  }

  /**
   * Build argument evidence overview (simplified version)
   */
  async buildArgumentEvidence(filters?: KGFilterState) {
    const { nodes, edges } = await this.applyFilters(filters);

    const argumentNodes = nodes.filter(n => n.type === 'argument');

    return {
      nodes: argumentNodes.map(arg => ({
        id: arg.id,
        label: arg.label,
        group: 'argument',
        size: 1,
        metadata: { type: 'argument' },
      })),
      links: [],
      arguments: argumentNodes.map(arg => ({
        id: arg.id,
        label: arg.label,
        period: arg.period,
        school: arg.school,
        description: arg.description,
        ancientCount: 0,
        modernCount: 0,
        totalConnections: edges.filter(e => e.source === arg.id || e.target === arg.id).length,
      })),
      stats: {
        totalArguments: argumentNodes.length,
        totalAncientSources: 0,
        totalModernReception: 0,
      },
    };
  }

  /**
   * Build concept clusters (simplified version)
   */
  async buildConceptClusters(filters?: KGFilterState) {
    const { nodes } = await this.applyFilters(filters);

    const concepts = nodes.filter(n => n.type === 'concept');

    return {
      clusters: concepts.map((concept, idx) => ({
        id: `cluster_${idx}`,
        label: concept.label || `Concept ${idx + 1}`,
        size: 1,
        keywords: [],
        nodes: [{
          id: concept.id,
          label: concept.label,
          type: concept.type,
          x: 0,
          y: 0,
          period: concept.period,
          school: concept.school,
          keywords: [],
        }],
      })),
      stats: {
        totalConcepts: concepts.length,
        clusterCount: concepts.length,
      },
    };
  }

  /**
   * Infer year from node metadata
   */
  private inferNodeYear(node: KGNode, fallbackStart?: number | null, fallbackEnd?: number | null): number | null {
    // Try explicit year field
    if (typeof node.year === 'number') {
      return node.year;
    }

    // Try parsing dates field
    const dateFields = [node.dates, node.approximate_dates, node.floruit, node.birth, node.death, node.date];
    for (const field of dateFields) {
      if (field) {
        const parsed = this.parseYear(field);
        if (parsed !== null) return parsed;
      }
    }

    // Fallback to period start
    return fallbackStart !== undefined ? fallbackStart : null;
  }

  /**
   * Parse year from string (simplified version)
   */
  private parseYear(text: string | number): number | null {
    if (typeof text === 'number') return text;
    if (!text) return null;

    // Try to extract a year (e.g., "-450" or "450 BCE")
    const match = text.toString().match(/-?\d+/);
    if (match) {
      let year = parseInt(match[0]);
      if (text.toLowerCase().includes('bce') && year > 0) {
        year = -year;
      }
      return year;
    }

    return null;
  }

  /**
   * Detect communities using semantic clustering
   * Each person forms a cluster center with their works and concepts gravitating around them
   */
  async detectCommunities(algorithm: string = 'auto') {
    const { nodes, edges } = await this.applyFilters();

    // Build adjacency map for quick lookups
    const adjacency = new Map<string, Array<{ targetId: string; relation: string }>>();
    for (const edge of edges) {
      if (!adjacency.has(edge.source)) {
        adjacency.set(edge.source, []);
      }
      if (!adjacency.has(edge.target)) {
        adjacency.set(edge.target, []);
      }
      adjacency.get(edge.source)!.push({ targetId: edge.target, relation: edge.relation || 'related_to' });
      adjacency.get(edge.target)!.push({ targetId: edge.source, relation: edge.relation || 'related_to' });
    }

    // Create node lookup by type
    const nodesById = new Map(nodes.map(n => [n.id, n]));
    const personNodes = nodes.filter(n => n.type === 'person');

    const assignments = new Map<string, number>();
    let nextClusterId = 0;

    // For each person, create a cluster with their works and concepts
    for (const person of personNodes) {
      const clusterId = nextClusterId++;
      assignments.set(person.id, clusterId);

      // BFS to find related works and concepts within 2 hops
      const visited = new Set<string>([person.id]);
      const queue: Array<{ nodeId: string; depth: number }> = [{ nodeId: person.id, depth: 0 }];

      while (queue.length > 0) {
        const { nodeId, depth } = queue.shift()!;

        // Don't go beyond 2 hops
        if (depth >= 2) continue;

        const neighbors = adjacency.get(nodeId) || [];
        for (const { targetId, relation } of neighbors) {
          if (visited.has(targetId) || assignments.has(targetId)) continue;

          const neighbor = nodesById.get(targetId);
          if (!neighbor) continue;

          const neighborType = neighbor.type;

          // Add works, concepts, arguments, and quotes to this person's cluster
          if (['work', 'concept', 'argument', 'quote'].includes(neighborType || '')) {
            assignments.set(targetId, clusterId);
            visited.add(targetId);
            queue.push({ nodeId: targetId, depth: depth + 1 });
          }
        }
      }
    }

    // Handle orphaned nodes (not assigned to any cluster)
    // Group them by type and school
    const orphanedByCategory = new Map<string, string[]>();
    for (const node of nodes) {
      if (!assignments.has(node.id)) {
        const nodeType = node.type || 'unknown';
        const nodeSchool = node.school || 'unknown';
        const key = `${nodeType}_${nodeSchool}`;
        if (!orphanedByCategory.has(key)) {
          orphanedByCategory.set(key, []);
        }
        orphanedByCategory.get(key)!.push(node.id);
      }
    }

    // Assign orphaned nodes to new clusters by category
    for (const nodeIds of orphanedByCategory.values()) {
      const clusterId = nextClusterId++;
      for (const nodeId of nodeIds) {
        assignments.set(nodeId, clusterId);
      }
    }

    // Calculate quality (edges within clusters vs between clusters)
    let edgesWithin = 0;
    let edgesBetween = 0;
    for (const edge of edges) {
      const sourceCommunity = assignments.get(edge.source);
      const targetCommunity = assignments.get(edge.target);
      if (sourceCommunity !== undefined && targetCommunity !== undefined) {
        if (sourceCommunity === targetCommunity) {
          edgesWithin++;
        } else {
          edgesBetween++;
        }
      }
    }
    const totalEdges = edgesWithin + edgesBetween;
    const quality = totalEdges > 0 ? edgesWithin / totalEdges : 0;

    // Build community summaries
    const communityCounts = new Map<number, number>();
    for (const communityId of assignments.values()) {
      communityCounts.set(communityId, (communityCounts.get(communityId) || 0) + 1);
    }

    const sortedCommunities = Array.from(communityCounts.entries())
      .sort((a, b) => b[1] - a[1]); // Sort by size descending

    const communityColors = [
      '#2563eb', '#16a34a', '#db2777', '#f97316', '#0ea5e9', '#9333ea',
      '#22c55e', '#facc15', '#ef4444', '#8b5cf6', '#14b8a6', '#f59e0b',
      '#3b82f6', '#ec4899', '#10b981', '#6366f1',
    ];

    const communities = sortedCommunities.map(([id, size], index) => ({
      id,
      size,
      order: index,
      color: communityColors[index % communityColors.length],
      label: `Community ${index + 1}`,
    }));

    const colorMap: Record<number, string> = {};
    for (const community of communities) {
      colorMap[community.id] = community.color;
    }

    return {
      algorithmRequested: algorithm,
      algorithmUsed: 'semantic',
      quality,
      communities,
      nodeAssignments: Object.fromEntries(assignments),
      colors: colorMap,
      availableAlgorithms: [
        {
          name: 'semantic',
          available: true,
          description: 'Semantic clustering: groups nodes by semantic relationships. Each person forms a cluster center with their works and related concepts gravitating around them.',
        },
      ],
    };
  }
}
