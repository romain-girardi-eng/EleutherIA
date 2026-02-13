/**
 * Multi-hop Reasoning Synthesis Service
 *
 * Explains the philosophical connections found through graph traversal,
 * making implicit paths explicit for users.
 */

import { LLMService } from './llm';
import { getLogger } from '../utils/logger';

const logger = getLogger('MultiHopService');

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  description?: string;
  school?: string;
  period?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  description?: string;
}

export interface ReasoningPath {
  nodes: GraphNode[];
  edges: GraphEdge[];
  pathLength: number;
}

export interface ReasoningSynthesis {
  path: ReasoningPath;
  explanation: string;
  philosophicalConnection: string;
  keyInsight: string;
  synthesisTime: number;
}

export interface MultiHopResult {
  syntheses: ReasoningSynthesis[];
  summary: string;
  totalPaths: number;
  processingTime: number;
}

/**
 * Synthesize explanation for a single reasoning path
 */
export async function synthesizeReasoningPath(
  path: ReasoningPath,
  llm: LLMService
): Promise<ReasoningSynthesis> {
  const startTime = Date.now();

  if (path.nodes.length < 2) {
    return {
      path,
      explanation: 'Direct connection.',
      philosophicalConnection: 'N/A',
      keyInsight: 'N/A',
      synthesisTime: 0,
    };
  }

  // Build path description
  const startNode = path.nodes[0];
  const endNode = path.nodes[path.nodes.length - 1];

  const pathDescription = path.edges
    .map((e, i) => {
      const sourceNode = path.nodes[i];
      const targetNode = path.nodes[i + 1];
      return `${sourceNode.label} --[${e.relation}]--> ${targetNode.label}`;
    })
    .join('\n');

  const prompt = `You are an expert in ancient philosophy explaining conceptual connections.

START CONCEPT: ${startNode.label}
${startNode.description ? `Description: ${startNode.description.slice(0, 200)}` : ''}
${startNode.school ? `School: ${startNode.school}` : ''}

END CONCEPT: ${endNode.label}
${endNode.description ? `Description: ${endNode.description.slice(0, 200)}` : ''}
${endNode.school ? `School: ${endNode.school}` : ''}

CONNECTION PATH:
${pathDescription}

TASK: Explain the philosophical connection in 2-3 sentences.

Return ONLY valid JSON:
{
  "explanation": "Detailed explanation of the connection...",
  "philosophicalConnection": "Brief statement of the philosophical relationship",
  "keyInsight": "One-sentence key insight about this connection"
}`;

  try {
    const response = await llm.generate(prompt, 'gemini-3-flash-preview', true);

    let parsed: any;
    try {
      const cleanedResponse = response
        .replace(/```json\n?/g, '')
        .replace(/```\n?/g, '')
        .trim();
      parsed = JSON.parse(cleanedResponse);
    } catch {
      parsed = {
        explanation: `The path connects ${startNode.label} to ${endNode.label} through ${path.edges.length} relationship(s).`,
        philosophicalConnection: `${startNode.label} relates to ${endNode.label}`,
        keyInsight: 'Connection through graph traversal.',
      };
    }

    return {
      path,
      explanation: parsed.explanation || '',
      philosophicalConnection: parsed.philosophicalConnection || '',
      keyInsight: parsed.keyInsight || '',
      synthesisTime: Date.now() - startTime,
    };
  } catch (error) {
    logger.error('Path synthesis error', error);
    return {
      path,
      explanation: `Connection from ${startNode.label} to ${endNode.label}.`,
      philosophicalConnection: 'Connection found',
      keyInsight: 'Graph path exists.',
      synthesisTime: Date.now() - startTime,
    };
  }
}

/**
 * Synthesize multiple reasoning paths
 */
export async function synthesizeMultiplePaths(
  paths: ReasoningPath[],
  llm: LLMService,
  maxPaths: number = 5
): Promise<MultiHopResult> {
  const startTime = Date.now();

  // Limit paths to process
  const pathsToProcess = paths.slice(0, maxPaths);

  // Process paths in parallel (limit to 3 concurrent)
  const syntheses: ReasoningSynthesis[] = [];
  for (let i = 0; i < pathsToProcess.length; i += 3) {
    const batch = pathsToProcess.slice(i, i + 3);
    const batchResults = await Promise.all(
      batch.map(path => synthesizeReasoningPath(path, llm))
    );
    syntheses.push(...batchResults);
  }

  // Generate summary
  const summary = generatePathsSummary(syntheses);

  logger.info(`Multi-hop synthesis: ${syntheses.length} paths processed in ${Date.now() - startTime}ms`);

  return {
    syntheses,
    summary,
    totalPaths: paths.length,
    processingTime: Date.now() - startTime,
  };
}

/**
 * Generate summary of multiple reasoning paths
 */
function generatePathsSummary(syntheses: ReasoningSynthesis[]): string {
  if (syntheses.length === 0) {
    return 'No reasoning paths found.';
  }

  if (syntheses.length === 1) {
    return syntheses[0].keyInsight;
  }

  // Extract unique key insights
  const insights = syntheses
    .map(s => s.keyInsight)
    .filter(Boolean);

  if (insights.length === 0) {
    return `Found ${syntheses.length} conceptual connections.`;
  }

  return `Key connections: ${insights.slice(0, 3).join('; ')}.`;
}

/**
 * Identify bridge nodes (intermediate concepts connecting source to target)
 */
export function identifyBridgeNodes(paths: ReasoningPath[]): {
  bridgeNodes: GraphNode[];
  bridgeFrequency: Map<string, number>;
} {
  const bridgeFrequency = new Map<string, number>();
  const bridgeNodesMap = new Map<string, GraphNode>();

  for (const path of paths) {
    // Skip first and last nodes (they're source/target, not bridges)
    for (let i = 1; i < path.nodes.length - 1; i++) {
      const node = path.nodes[i];
      const current = bridgeFrequency.get(node.id) || 0;
      bridgeFrequency.set(node.id, current + 1);
      if (!bridgeNodesMap.has(node.id)) {
        bridgeNodesMap.set(node.id, node);
      }
    }
  }

  // Sort by frequency
  const sortedIds = Array.from(bridgeFrequency.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([id]) => id);

  const bridgeNodes = sortedIds.map(id => bridgeNodesMap.get(id)!);

  return { bridgeNodes, bridgeFrequency };
}

/**
 * Extract reasoning paths from graph traversal results
 */
export function extractReasoningPaths(
  nodes: any[],
  edges: any[],
  maxPaths: number = 10
): ReasoningPath[] {
  const paths: ReasoningPath[] = [];

  // Build adjacency map
  const adjacency = new Map<string, Array<{ edge: any; targetId: string }>>();
  const nodeMap = new Map<string, any>();

  for (const node of nodes) {
    const id = node.node_id || node.id;
    nodeMap.set(id, node);
    if (!adjacency.has(id)) {
      adjacency.set(id, []);
    }
  }

  for (const edge of edges) {
    const sourceId = edge.source_id || edge.source;
    const targetId = edge.target_id || edge.target;
    if (adjacency.has(sourceId)) {
      adjacency.get(sourceId)!.push({ edge, targetId });
    }
  }

  // Find paths (simple BFS, limited depth)
  const visited = new Set<string>();
  const queue: Array<{ nodeId: string; path: string[]; edgePath: any[] }> = [];

  // Start from first few nodes
  for (const node of nodes.slice(0, 3)) {
    const id = node.node_id || node.id;
    queue.push({ nodeId: id, path: [id], edgePath: [] });
  }

  while (queue.length > 0 && paths.length < maxPaths) {
    const { nodeId, path, edgePath } = queue.shift()!;

    if (path.length >= 2) {
      // Convert to ReasoningPath
      const pathNodes: GraphNode[] = path.map(id => {
        const n = nodeMap.get(id);
        return {
          id,
          label: n?.name || n?.label || id,
          type: n?.type || 'concept',
          description: n?.description,
          school: n?.school,
          period: n?.period,
        };
      });

      const pathEdges: GraphEdge[] = edgePath.map(e => ({
        id: e.edge_id || e.id || '',
        source: e.source_id || e.source,
        target: e.target_id || e.target,
        relation: e.relation || e.type || 'relates_to',
        description: e.description,
      }));

      paths.push({
        nodes: pathNodes,
        edges: pathEdges,
        pathLength: path.length - 1,
      });
    }

    // Continue traversal (max depth 4)
    if (path.length < 4) {
      const neighbors = adjacency.get(nodeId) || [];
      for (const { edge, targetId } of neighbors) {
        if (!path.includes(targetId)) {
          queue.push({
            nodeId: targetId,
            path: [...path, targetId],
            edgePath: [...edgePath, edge],
          });
        }
      }
    }
  }

  return paths;
}
