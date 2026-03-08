import { useDeferredValue, useMemo, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import GraphLegend from './GraphLegend';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';
import { formatGraphNodeType, getGraphTypeTheme } from './graphTheme';

const TYPE_SIZES: Record<string, number> = {
  person: 11,
  school: 10,
  concept: 9,
  argument: 8,
  debate: 8,
  work: 8,
  event: 7,
  quote: 7,
  publication: 7,
  synthesis: 7,
  controversy: 7,
  passage: 5,
  default: 6,
};

const LABEL_WEIGHTS: Record<string, number> = {
  person: 1.0,
  school: 0.9,
  concept: 0.82,
  argument: 0.74,
  debate: 0.68,
  work: 0.62,
  event: 0.54,
  publication: 0.5,
  quote: 0.44,
  passage: 0.24,
  default: 0.34,
};

type GraphPoint = {
  index: number;
  id: string;
  label: string;
  type: string;
  color: string;
  size: number;
  labelWeight: number;
  citationIndex?: number;
  importance: number;
  isSource: boolean;
  isStarting: boolean;
  isExpanded: boolean;
};

type GraphLink = {
  source: string;
  target: string;
  color: string;
};

type AccumulatedNode = {
  id: string;
  label: string;
  type: string;
  isSource: boolean;
  isStarting: boolean;
  isExpanded: boolean;
  citationIndex?: number;
  occurrences: number;
  degree: number;
};

type StageNode = GraphPoint & {
  x: number;
  y: number;
  width: number;
  height: number;
  radius: number;
  subtitle?: string;
};

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) {
    return { r: 138, g: 143, b: 152 };
  }

  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  };
}

function rgbToHex(r: number, g: number, b: number): string {
  return (
    '#' +
    [r, g, b]
      .map((value) => {
        const hex = Math.round(value).toString(16);
        return hex.length === 1 ? `0${hex}` : hex;
      })
      .join('')
  );
}

function blendColors(colorA: string, colorB: string): string {
  const a = hexToRgb(colorA);
  const b = hexToRgb(colorB);

  return rgbToHex(
    a.r * 0.55 + b.r * 0.45,
    a.g * 0.55 + b.g * 0.45,
    a.b * 0.55 + b.b * 0.45,
  );
}

function truncateLabel(label: string, maxLength: number) {
  if (label.length <= maxLength) {
    return label;
  }

  return `${label.slice(0, maxLength - 1)}…`;
}

function frameFor(point: GraphPoint, kind: 'source' | 'anchor' | 'expansion' | 'micro') {
  const maxLength =
    kind === 'source' ? 26 : kind === 'anchor' ? 20 : kind === 'expansion' ? 18 : 14;
  const label = truncateLabel(point.label, maxLength);
  const width =
    kind === 'source'
      ? Math.max(184, Math.min(250, label.length * 7.4 + 84))
      : kind === 'micro'
        ? Math.max(102, Math.min(140, label.length * 6.2 + 42))
        : Math.max(128, Math.min(180, label.length * 6.8 + 54));
  const height = kind === 'source' ? 74 : kind === 'micro' ? 34 : 44;
  const radius = kind === 'source' ? 22 : kind === 'micro' ? 14 : 16;

  return { label, width, height, radius };
}

function connectionPath(from: StageNode, toX: number, toY: number) {
  const deltaX = toX - from.x;
  const direction = deltaX >= 0 ? 1 : -1;
  const startX = from.x + direction * (from.width / 2 - 12);
  const controlA = startX + deltaX * 0.35;
  const controlB = toX - deltaX * 0.3;

  return `M ${startX} ${from.y} C ${controlA} ${from.y}, ${controlB} ${toY}, ${toX} ${toY}`;
}

interface CosmographViewProps {
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  highlightedSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onSourceSelect?: (citationIndex: number) => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
  showControls?: boolean;
}

export default function CosmographView({
  response,
  allResponses,
  highlightedSourceIndex,
  onNodeClick,
  onSourceSelect,
  onHighlightRef,
  className,
}: CosmographViewProps) {
  const { t } = useTranslation();
  const deferredResponse = useDeferredValue(response);
  const deferredAllResponses = useDeferredValue(allResponses);

  const graph = useMemo(() => {
    const responses =
      deferredAllResponses && deferredAllResponses.length > 0
        ? deferredAllResponses
        : deferredResponse
          ? [deferredResponse]
          : [];

    if (responses.length === 0) {
      return {
        points: [] as GraphPoint[],
        links: [] as GraphLink[],
        presentTypes: [] as string[],
      };
    }

    const currentResponse = deferredResponse ?? responses[responses.length - 1];
    const nodeMap = new Map<string, AccumulatedNode>();
    const linkSet = new Set<string>();
    const rawLinks: Array<{ source: string; target: string }> = [];

    const upsertNode = (
      id: string,
      label: string,
      type: string,
      flags: Partial<Pick<AccumulatedNode, 'isSource' | 'isStarting' | 'isExpanded' | 'citationIndex'>>,
    ) => {
      if (!id) {
        return;
      }

      const existing = nodeMap.get(id);
      if (existing) {
        existing.occurrences += 1;
        existing.label = existing.label || label || id;
        existing.type = existing.type || type || 'default';
        existing.isSource = existing.isSource || Boolean(flags.isSource);
        existing.isStarting = existing.isStarting || Boolean(flags.isStarting);
        existing.isExpanded = existing.isExpanded || Boolean(flags.isExpanded);
        if (flags.citationIndex !== undefined && existing.citationIndex === undefined) {
          existing.citationIndex = flags.citationIndex;
        }
        return;
      }

      nodeMap.set(id, {
        id,
        label: label || id,
        type: type || 'default',
        isSource: Boolean(flags.isSource),
        isStarting: Boolean(flags.isStarting),
        isExpanded: Boolean(flags.isExpanded),
        citationIndex: flags.citationIndex,
        occurrences: 1,
        degree: 0,
      });
    };

    const addLink = (source: string, target: string) => {
      if (!source || !target) {
        return;
      }

      const key = `${source}->${target}`;
      if (linkSet.has(key)) {
        return;
      }

      linkSet.add(key);
      rawLinks.push({ source, target });
    };

    responses.forEach((resp) => {
      resp.sources?.slice(0, 28).forEach((source) => {
        const isCurrentSource = currentResponse?.sources?.some((item) => item.nodeId === source.nodeId);
        const citationIndex =
          isCurrentSource && currentResponse?.sources
            ? currentResponse.sources.findIndex((item) => item.nodeId === source.nodeId)
            : -1;

        upsertNode(source.nodeId, source.nodeLabel, source.nodeType, {
          isSource: true,
          citationIndex: citationIndex >= 0 ? citationIndex : undefined,
        });
      });

      resp.reasoning_path?.starting_nodes?.forEach((node) => {
        upsertNode(node.id, node.label, node.type, { isStarting: true });
      });

      resp.reasoning_path?.expanded_nodes?.slice(0, 18).forEach((node) => {
        upsertNode(node.id, node.label, node.type, { isExpanded: true });
      });

      resp.reasoning_path?.traversed_edges?.slice(0, 36).forEach((edge) => {
        upsertNode(edge.source, edge.source, 'default', {});
        upsertNode(edge.target, edge.target, 'default', {});
        addLink(edge.source, edge.target);
      });
    });

    rawLinks.forEach((link) => {
      const sourceNode = nodeMap.get(link.source);
      const targetNode = nodeMap.get(link.target);
      if (sourceNode) {
        sourceNode.degree += 1;
      }
      if (targetNode) {
        targetNode.degree += 1;
      }
    });

    const orderedNodes = [...nodeMap.values()].sort((a, b) => {
      const aScore =
        (a.isSource ? 400 : 0) +
        (a.isStarting ? 250 : 0) +
        (a.isExpanded ? 80 : 0) +
        a.degree * 18 +
        a.occurrences * 6;
      const bScore =
        (b.isSource ? 400 : 0) +
        (b.isStarting ? 250 : 0) +
        (b.isExpanded ? 80 : 0) +
        b.degree * 18 +
        b.occurrences * 6;

      if (aScore !== bScore) {
        return bScore - aScore;
      }

      return a.label.localeCompare(b.label);
    });

    const idToColor = new Map<string, string>();
    const presentTypes = new Set<string>();

    const points = orderedNodes.map((node, index) => {
      const key = node.type?.toLowerCase() || 'default';
      const theme = getGraphTypeTheme(key);
      const baseSize = TYPE_SIZES[key] ?? TYPE_SIZES.default;
      const size =
        baseSize +
        (node.isSource ? 3.5 : 0) +
        (node.isStarting ? 1.5 : 0) +
        Math.min(node.degree * 0.3, 2);
      const labelWeight =
        (LABEL_WEIGHTS[key] ?? LABEL_WEIGHTS.default) +
        (node.isSource ? 0.18 : 0) +
        (node.isStarting ? 0.08 : 0);
      const importance =
        (node.isSource ? 3 : 0) +
        (node.isStarting ? 2 : 0) +
        (node.isExpanded ? 1 : 0) +
        node.degree;

      idToColor.set(node.id, theme.color);
      presentTypes.add(key);

      return {
        index,
        id: node.id,
        label: node.label,
        type: node.type,
        color: theme.color,
        size,
        labelWeight,
        citationIndex: node.citationIndex,
        importance,
        isSource: node.isSource,
        isStarting: node.isStarting,
        isExpanded: node.isExpanded,
      };
    });

    const links = rawLinks
      .map((link) => {
        const sourceColor = idToColor.get(link.source) ?? getGraphTypeTheme().color;
        const targetColor = idToColor.get(link.target) ?? getGraphTypeTheme().color;
        return {
          source: link.source,
          target: link.target,
          color: blendColors(sourceColor, targetColor),
        };
      })
      .filter((link) => link.source !== link.target);

    return {
      points,
      links,
      presentTypes: [...presentTypes],
    };
  }, [deferredAllResponses, deferredResponse]);

  const highlightedNode = useMemo(
    () =>
      highlightedSourceIndex !== null
        ? graph.points.find((point) => point.citationIndex === highlightedSourceIndex) ?? null
        : null,
    [graph.points, highlightedSourceIndex],
  );

  const emitHighlight = useCallback(
    (citationIndex: number) => {
      onSourceSelect?.(citationIndex);
    },
    [onSourceSelect],
  );

  useEffect(() => {
    onHighlightRef?.(emitHighlight);
  }, [emitHighlight, onHighlightRef]);

  const stage = useMemo(() => {
    const width = 980;
    const height = 560;
    const centerX = 470;
    const centerY = 282;
    const answerCard = { x: centerX, y: centerY, width: 320, height: 170, radius: 34 };

    const sources = graph.points
      .filter((point) => point.isSource)
      .sort((a, b) => (a.citationIndex ?? 0) - (b.citationIndex ?? 0))
      .slice(0, 6);
    const anchors = graph.points
      .filter((point) => point.isStarting && !point.isSource)
      .slice(0, 4);
    const expansions = graph.points
      .filter((point) => point.isExpanded && !point.isSource && !point.isStarting)
      .slice(0, 6);
    const remainder = graph.points
      .filter((point) => !point.isSource && !point.isStarting && !point.isExpanded)
      .slice(0, 5);

    const sourceNodes: StageNode[] = sources.map((point, index) => {
      const frame = frameFor(point, 'source');
      return {
        ...point,
        x: 158 + (index % 2) * 26,
        y: 122 + index * 72,
        width: frame.width,
        height: frame.height,
        radius: frame.radius,
        subtitle: point.citationIndex !== undefined ? `Source ${point.citationIndex + 1}` : undefined,
      };
    });

    const anchorNodes: StageNode[] = anchors.map((point, index) => {
      const frame = frameFor(point, 'anchor');
      return {
        ...point,
        x: 772 + (index % 2) * 84,
        y: 142 + Math.floor(index / 2) * 78,
        width: frame.width,
        height: frame.height,
        radius: frame.radius,
      };
    });

    const expansionNodes: StageNode[] = expansions.map((point, index) => {
      const frame = frameFor(point, 'expansion');
      return {
        ...point,
        x: 752 + (index % 2) * 104 + (index >= 4 ? 34 : 0),
        y: 334 + Math.floor(index / 2) * 58,
        width: frame.width,
        height: frame.height,
        radius: frame.radius,
      };
    });

    const microNodes: StageNode[] = remainder.map((point, index) => {
      const frame = frameFor(point, 'micro');
      return {
        ...point,
        x: 445 + (index - (remainder.length - 1) / 2) * 94,
        y: 460 + (index % 2) * 24,
        width: frame.width,
        height: frame.height,
        radius: frame.radius,
      };
    });

    const stageNodes = [...sourceNodes, ...anchorNodes, ...expansionNodes, ...microNodes];
    const stageMap = new Map(stageNodes.map((node) => [node.id, node]));

    return {
      width,
      height,
      centerX,
      centerY,
      answerCard,
      sourceNodes,
      anchorNodes,
      expansionNodes,
      microNodes,
      stageNodes,
      stageMap,
    };
  }, [graph.points]);

  const visibleLinks = useMemo(() => {
    const visibleIds = new Set(stage.stageNodes.map((node) => node.id));
    return graph.links.filter((link) => visibleIds.has(link.source) && visibleIds.has(link.target));
  }, [graph.links, stage.stageNodes]);

  const handleNodeActivate = useCallback(
    (point: GraphPoint) => {
      if (point.citationIndex !== undefined && onSourceSelect) {
        onSourceSelect(point.citationIndex);
        return;
      }

      onNodeClick(point.id);
    },
    [onNodeClick, onSourceSelect],
  );

  if (graph.points.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'relative h-full w-full overflow-hidden rounded-[30px] border border-white/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,244,223,0.95),_rgba(255,255,255,0.96)_34%,_rgba(247,243,235,0.98)_100%)] shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_34px_90px_-52px_rgba(120,53,15,0.36)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)',
          backgroundSize: '26px 26px',
        }}
      />
      <div className="pointer-events-none absolute -left-16 top-0 h-56 w-56 rounded-full bg-amber-200/25 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-60 w-60 rounded-full bg-sky-100/35 blur-3xl" />

      <div className="pointer-events-none absolute left-4 top-4 z-20 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2">
        <span className="rounded-full border border-amber-200/80 bg-amber-50/92 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-800">
          Answer constellation
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1 text-[11px] font-medium text-stone-500">
          {stage.sourceNodes.length} sources
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1 text-[11px] font-medium text-stone-500">
          {graph.points.length} nodes
        </span>
        <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1 text-[11px] font-medium text-stone-500">
          {graph.links.length} links
        </span>
      </div>

      <motion.svg
        viewBox={`0 0 ${stage.width} ${stage.height}`}
        className="relative z-10 h-full w-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.45 }}
        role="img"
        aria-label={t('graphRagUi.answerMapAria')}
      >
        <defs>
          <radialGradient id="answer-core" cx="50%" cy="50%" r="65%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.98)" />
            <stop offset="100%" stopColor="rgba(255,248,235,0.94)" />
          </radialGradient>
        </defs>

        <circle cx={stage.centerX} cy={stage.centerY} r={134} fill="rgba(251,191,36,0.07)" />
        <circle cx={stage.centerX} cy={stage.centerY} r={188} fill="none" stroke="rgba(231,229,228,0.85)" strokeDasharray="5 11" />
        <circle cx={stage.centerX} cy={stage.centerY} r={246} fill="none" stroke="rgba(231,229,228,0.55)" />

        {stage.sourceNodes.map((node, index) => {
          const isActive = highlightedNode?.id === node.id;
          return (
            <motion.path
              key={`source-line-${node.id}`}
              d={connectionPath(node, stage.answerCard.x - stage.answerCard.width / 2 + 18, stage.answerCard.y)}
              fill="none"
              stroke={node.color}
              strokeWidth={isActive ? 2.5 : 1.65}
              strokeOpacity={isActive ? 0.7 : 0.24}
              strokeDasharray={isActive ? '10 10' : '6 12'}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: 1,
                strokeDashoffset: isActive ? [-24, 0] : [0, -30],
                opacity: isActive ? [0.35, 0.8, 0.35] : [0.14, 0.34, 0.14],
              }}
              transition={{
                pathLength: { duration: 0.5, delay: index * 0.05 },
                strokeDashoffset: { duration: isActive ? 1.4 : 3.8, repeat: Infinity, ease: 'linear' },
                opacity: { duration: isActive ? 1.8 : 4.2, repeat: Infinity, ease: 'easeInOut' },
              }}
            />
          );
        })}

        {[...stage.anchorNodes, ...stage.expansionNodes].map((node, index) => {
          const isActive = highlightedNode?.id === node.id;
          return (
            <motion.path
              key={`answer-link-${node.id}`}
              d={`M ${stage.answerCard.x + stage.answerCard.width / 2 - 18} ${stage.answerCard.y} C ${stage.answerCard.x + 116} ${stage.answerCard.y}, ${node.x - 94} ${node.y}, ${node.x - node.width / 2 + 12} ${node.y}`}
              fill="none"
              stroke={node.color}
              strokeWidth={isActive ? 2.2 : 1.3}
              strokeOpacity={isActive ? 0.72 : 0.22}
              strokeDasharray={isActive ? '9 9' : '5 11'}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: 1,
                strokeDashoffset: isActive ? [-18, 0] : [0, -22],
                opacity: isActive ? [0.4, 0.78, 0.4] : [0.12, 0.28, 0.12],
              }}
              transition={{
                pathLength: { duration: 0.45, delay: 0.12 + index * 0.04 },
                strokeDashoffset: { duration: isActive ? 1.5 : 4.4, repeat: Infinity, ease: 'linear' },
                opacity: { duration: isActive ? 1.9 : 4.6, repeat: Infinity, ease: 'easeInOut' },
              }}
            />
          );
        })}

        {visibleLinks.slice(0, 10).map((link, index) => {
          const source = stage.stageMap.get(link.source);
          const target = stage.stageMap.get(link.target);
          if (!source || !target) {
            return null;
          }

          const sourceX = source.x + (target.x > source.x ? source.width / 2 - 8 : -source.width / 2 + 8);
          const targetX = target.x + (source.x > target.x ? target.width / 2 - 8 : -target.width / 2 + 8);

          return (
            <motion.path
              key={`cross-link-${link.source}-${link.target}-${index}`}
              d={`M ${sourceX} ${source.y} Q ${(source.x + target.x) / 2} ${(source.y + target.y) / 2 - 26} ${targetX} ${target.y}`}
              fill="none"
              stroke={link.color}
              strokeWidth={1.1}
              strokeOpacity={0.12}
              strokeDasharray="4 12"
              animate={{ strokeDashoffset: [0, -22], opacity: [0.08, 0.18, 0.08] }}
              transition={{ duration: 5.4 + index * 0.25, repeat: Infinity, ease: 'linear' }}
            />
          );
        })}

        <motion.g
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.42 }}
        >
          <rect
            x={stage.answerCard.x - stage.answerCard.width / 2}
            y={stage.answerCard.y - stage.answerCard.height / 2}
            width={stage.answerCard.width}
            height={stage.answerCard.height}
            rx={stage.answerCard.radius}
            fill="url(#answer-core)"
            stroke="rgba(231,229,228,0.95)"
            strokeWidth={1.4}
          />
          <rect
            x={stage.answerCard.x - stage.answerCard.width / 2 + 18}
            y={stage.answerCard.y - stage.answerCard.height / 2 + 18}
            width={112}
            height={28}
            rx={14}
            fill="rgba(255,248,220,0.92)"
          />
          <text
            x={stage.answerCard.x - stage.answerCard.width / 2 + 36}
            y={stage.answerCard.y - stage.answerCard.height / 2 + 37}
            fill="#b45309"
            fontSize={11}
            fontWeight={700}
            letterSpacing="0.18em"
          >
            {t('graphRagUi.answerMap')}
          </text>
          <text
            x={stage.answerCard.x - stage.answerCard.width / 2 + 24}
            y={stage.answerCard.y - 8}
            fill="#292524"
            fontSize={26}
            fontWeight={700}
          >
            {truncateLabel(deferredResponse?.query || t('graphRagUi.answerMap'), 26)}
          </text>
          <text
            x={stage.answerCard.x - stage.answerCard.width / 2 + 24}
            y={stage.answerCard.y + 26}
            fill="#78716c"
            fontSize={14}
          >
            {stage.sourceNodes.length} sources guide the synthesis
          </text>
          <text
            x={stage.answerCard.x - stage.answerCard.width / 2 + 24}
            y={stage.answerCard.y + 50}
            fill="#78716c"
            fontSize={14}
          >
            {stage.anchorNodes.length} anchor nodes and {stage.expansionNodes.length} expansions
          </text>
          {highlightedNode && (
            <text
              x={stage.answerCard.x - stage.answerCard.width / 2 + 24}
              y={stage.answerCard.y + 74}
              fill="#b45309"
              fontSize={13}
              fontWeight={600}
            >
              Focusing on: {truncateLabel(highlightedNode.label, 28)}
            </text>
          )}
        </motion.g>

        {stage.sourceNodes.map((node, index) => {
          const theme = getGraphTypeTheme(node.type);
          const isActive = highlightedNode?.id === node.id;
          const label = truncateLabel(node.label, 24);

          return (
            <motion.g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={() => handleNodeActivate(node)}
              style={{ cursor: 'pointer' }}
              initial={{ opacity: 0, x: -18 }}
              animate={{
                opacity: 1,
                x: 0,
                y: [0, -4 - (index % 2), 0],
              }}
              transition={{
                opacity: { duration: 0.32, delay: index * 0.05 },
                x: { duration: 0.32, delay: index * 0.05 },
                y: { duration: 5.8 + index * 0.4, repeat: Infinity, ease: 'easeInOut' },
              }}
            >
              <rect
                x={-node.width / 2 - (isActive ? 5 : 0)}
                y={-node.height / 2 - (isActive ? 5 : 0)}
                width={node.width + (isActive ? 10 : 0)}
                height={node.height + (isActive ? 10 : 0)}
                rx={node.radius + (isActive ? 5 : 0)}
                fill={`${theme.glow}${isActive ? '99' : '44'}`}
              />
              <rect
                x={-node.width / 2}
                y={-node.height / 2}
                width={node.width}
                height={node.height}
                rx={node.radius}
                fill="rgba(255,255,255,0.96)"
                stroke={isActive ? theme.color : theme.border}
                strokeWidth={isActive ? 1.8 : 1.2}
              />
              <circle cx={-node.width / 2 + 20} cy={0} r={7} fill={theme.color} />
              <text x={-node.width / 2 + 36} y={-6} fill="#292524" fontSize={14} fontWeight={700}>
                {label}
              </text>
              <text x={-node.width / 2 + 36} y={14} fill="#78716c" fontSize={11}>
                {node.subtitle || formatGraphNodeType(node.type)}
              </text>
              {node.citationIndex !== undefined && (
                <text
                  x={node.width / 2 - 16}
                  y={-node.height / 2 + 18}
                  fill={theme.text}
                  fontSize={12}
                  fontWeight={700}
                  textAnchor="end"
                >
                  {node.citationIndex + 1}
                </text>
              )}
            </motion.g>
          );
        })}

        {[...stage.anchorNodes, ...stage.expansionNodes, ...stage.microNodes].map((node, index) => {
          const theme = getGraphTypeTheme(node.type);
          const isActive = highlightedNode?.id === node.id;
          const label = truncateLabel(node.label, node.height <= 34 ? 14 : 18);

          return (
            <motion.g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={() => handleNodeActivate(node)}
              style={{ cursor: 'pointer' }}
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{
                opacity: 1,
                scale: 1,
                y: [0, -3 - ((index + 1) % 2), 0],
              }}
              transition={{
                opacity: { duration: 0.28, delay: 0.14 + index * 0.03 },
                scale: { duration: 0.28, delay: 0.14 + index * 0.03 },
                y: { duration: 6.2 + index * 0.3, repeat: Infinity, ease: 'easeInOut' },
              }}
            >
              <rect
                x={-node.width / 2 - (isActive ? 4 : 0)}
                y={-node.height / 2 - (isActive ? 4 : 0)}
                width={node.width + (isActive ? 8 : 0)}
                height={node.height + (isActive ? 8 : 0)}
                rx={node.radius + (isActive ? 4 : 0)}
                fill={`${theme.glow}${isActive ? '88' : '32'}`}
              />
              <rect
                x={-node.width / 2}
                y={-node.height / 2}
                width={node.width}
                height={node.height}
                rx={node.radius}
                fill="rgba(255,255,255,0.95)"
                stroke={isActive ? theme.color : theme.border}
                strokeWidth={isActive ? 1.6 : 1.1}
              />
              <circle cx={-node.width / 2 + 14} cy={0} r={4.5} fill={theme.color} />
              <text
                x={-node.width / 2 + 28}
                y={1}
                fill="#292524"
                fontSize={node.height <= 34 ? 11 : 12}
                fontWeight={600}
                dominantBaseline="middle"
              >
                {label}
              </text>
            </motion.g>
          );
        })}
      </motion.svg>

      <div className="pointer-events-none absolute bottom-4 left-4 z-20">
        <GraphLegend types={graph.presentTypes} />
      </div>
    </div>
  );
}
