import { useMemo } from 'react';
import { Network } from 'lucide-react';
import { useKGWorkspace } from '../../context/KGWorkspaceContext';
import type { EvidenceLink, EvidenceNode } from '../../types';

const COLUMN_ORDER: Array<EvidenceNode['group']> = ['argument', 'ancient_source', 'modern_reception'];
const COLORS: Record<EvidenceNode['group'], string> = {
  argument: '#f87171',
  ancient_source: '#38bdf8',
  modern_reception: '#a78bfa',
};

interface PositionedNode extends EvidenceNode {
  x: number;
  y: number;
  height: number;
  value: number;
}

interface PositionedLink extends EvidenceLink {
  path: string;
  color: string;
}

interface SankeyLayout {
  nodes: PositionedNode[];
  links: PositionedLink[];
}

function computeNodeValue(node: EvidenceNode, links: EvidenceLink[]) {
  const contributions = links.filter((link) => link.source === node.id || link.target === node.id);
  return contributions.reduce((sum, link) => sum + (link.value || 1), 0) || 1;
}

function computeLayout(nodes: EvidenceNode[], links: EvidenceLink[], width: number, height: number): SankeyLayout {
  const nodeValues = new Map(nodes.map((node) => [node.id, computeNodeValue(node, links)]));
  const columnNodes: Record<string, EvidenceNode[]> = {
    argument: [],
    ancient_source: [],
    modern_reception: [],
  };

  nodes.forEach((node) => {
    columnNodes[node.group].push(node);
  });

  const horizontalPadding = 120;
  const verticalPadding = 40;
  const columnWidth = (width - horizontalPadding * 2) / (COLUMN_ORDER.length - 1 || 1);

  const positionedNodes: PositionedNode[] = [];

  COLUMN_ORDER.forEach((group, columnIndex) => {
    const column = columnNodes[group];
    if (!column || column.length === 0) {
      return;
    }

    const totalValue = column.reduce((sum, node) => sum + (nodeValues.get(node.id) || 1), 0);
    const availableHeight = height - verticalPadding * 2;
    const gap = 12;

    let cursorY = verticalPadding;
    column
      .slice()
      .sort((a, b) => (nodeValues.get(b.id) || 0) - (nodeValues.get(a.id) || 0))
      .forEach((node) => {
        const value = nodeValues.get(node.id) || 1;
        const heightRatio = value / totalValue;
        const nodeHeight = Math.max(18, availableHeight * heightRatio - gap);
        const nodeY = cursorY;
        cursorY += nodeHeight + gap;
        positionedNodes.push({
          ...node,
          value,
          height: nodeHeight,
          x: horizontalPadding + columnIndex * columnWidth - 60,
          y: nodeY,
        });
      });
  });

  const positionedLinks: PositionedLink[] = [];
  const nodeMap = new Map(positionedNodes.map((node) => [node.id, node]));

  links.forEach((link) => {
    const sourceNode = nodeMap.get(link.source);
    const targetNode = nodeMap.get(link.target);
    if (!sourceNode || !targetNode) {
      return;
    }

    const sourceX = sourceNode.x + 120;
    const targetX = targetNode.x;
    const sourceY = sourceNode.y + sourceNode.height / 2;
    const targetY = targetNode.y + targetNode.height / 2;

    const curvature = Math.max(80, Math.abs(targetX - sourceX) / 2);
    const path = `M ${sourceX} ${sourceY} C ${sourceX + curvature} ${sourceY}, ${targetX - curvature} ${targetY}, ${targetX} ${targetY}`;

    positionedLinks.push({
      ...link,
      path,
      color: COLORS[sourceNode.group] || '#94a3b8',
    });
  });

  return { nodes: positionedNodes, links: positionedLinks };
}

function formatGroupLabel(group: EvidenceNode['group']) {
  switch (group) {
    case 'argument':
      return 'Arguments';
    case 'ancient_source':
      return 'Ancient Sources';
    case 'modern_reception':
      return 'Modern Reception';
    default:
      return group;
  }
}

export default function ArgumentEvidenceBoard() {
  const {
    state: { argumentEvidence, loading },
    updateSelection,
  } = useKGWorkspace();

  const layout = useMemo(() => {
    if (!argumentEvidence) {
      return null;
    }

    const width = 960;
    const height = 420;
    const nodes = argumentEvidence.nodes;
    const links = argumentEvidence.links;

    return {
      layout: computeLayout(nodes, links, width, height),
      width,
      height,
    };
  }, [argumentEvidence]);

  if (loading && !argumentEvidence) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">Loading argument evidence…</div>
      </div>
    );
  }

  if (!argumentEvidence) {
    return (
      <div className="academic-card">
        <div className="py-16 text-center text-academic-muted text-sm">
          No argument evidence available for the current filters.
        </div>
      </div>
    );
  }

  const topArguments = argumentEvidence.arguments.slice(0, 8);

  return (
    <div className="academic-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-academic-text uppercase">
          <Network className="w-4 h-4 text-primary-600" />
          Argument Evidence Board
        </div>
        <div className="text-xs text-academic-muted">
          {argumentEvidence.stats.totalArguments.toLocaleString()} arguments •{' '}
          {argumentEvidence.stats.totalAncientSources.toLocaleString()} ancient attestations •{' '}
          {argumentEvidence.stats.totalModernReception.toLocaleString()} modern receptions
        </div>
      </div>

      {layout && (
        <div className="overflow-x-auto">
          <svg width={layout.width} height={layout.height} className="mx-auto block">
            <defs>
              <linearGradient id="argumentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#f87171" stopOpacity="0.65" />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.65" />
              </linearGradient>
              <linearGradient id="modernGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.6" />
              </linearGradient>
            </defs>

            {layout.layout.links.map((link, index) => (
              <path
                key={`${link.source}-${link.target}-${index}`}
                d={link.path}
                stroke={link.source.startsWith('ancient') ? 'url(#modernGradient)' : 'url(#argumentGradient)'}
                strokeWidth={Math.max(1.5, Math.log(link.value + 1) * 1.5)}
                fill="none"
                opacity={0.65}
              />
            ))}

            {layout.layout.nodes.map((node) => (
              <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                <rect
                  width={120}
                  height={node.height}
                  rx={6}
                  ry={6}
                  fill={COLORS[node.group]}
                  opacity={0.2}
                  stroke={COLORS[node.group]}
                  strokeWidth={1}
                />
                <foreignObject width={120} height={node.height}>
                  <div className="h-full w-full px-3 py-2 text-xs flex flex-col justify-center">
                    <div className="font-semibold text-academic-text line-clamp-2">{node.label}</div>
                    <div className="text-[10px] text-academic-muted uppercase mt-1 tracking-wide">
                      {formatGroupLabel(node.group)}
                    </div>
                    <div className="text-[10px] text-academic-muted mt-1">
                      {node.value.toLocaleString()} link{node.value === 1 ? '' : 's'}
                    </div>
                  </div>
                </foreignObject>
              </g>
            ))}
          </svg>
        </div>
      )}

      <div className="mt-6">
        <h4 className="text-sm font-semibold text-academic-text mb-2">Top arguments by evidence depth</h4>
        <div className="grid md:grid-cols-2 gap-3">
          {topArguments.map((argument) => (
            <button
              key={argument.id}
              onClick={() =>
                updateSelection({
                  nodes: [argument.id],
                  focusNodeId: argument.id,
                })
              }
              className="text-left px-4 py-3 border border-gray-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-colors"
            >
              <div className="text-sm font-semibold text-academic-text">{argument.label}</div>
              <div className="text-xs text-academic-muted">
                {argument.ancientCount} ancient • {argument.modernCount} modern •{' '}
                {argument.totalConnections} total connections
              </div>
              {argument.period && (
                <div className="text-[11px] text-academic-muted uppercase mt-1">{argument.period}</div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
