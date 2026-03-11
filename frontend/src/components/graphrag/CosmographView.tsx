import { useDeferredValue, useMemo, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Waypoints } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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

  return `${label.slice(0, maxLength - 1)}...`;
}

function distribute(index: number, total: number, start: number, end: number) {
  if (total <= 1) {
    return (start + end) / 2;
  }

  return start + (index * (end - start)) / (total - 1);
}

function curvePath(fromX: number, fromY: number, toX: number, toY: number) {
  const bend = Math.abs(toX - fromX) * 0.42;
  const direction = toX > fromX ? 1 : -1;
  const controlAX = fromX + bend * direction;
  const controlBX = toX - bend * direction;

  return `M ${fromX} ${fromY} C ${controlAX} ${fromY}, ${controlBX} ${toY}, ${toX} ${toY}`;
}

function LaneLabel({
  step,
  title,
  subtitle,
}: {
  step: string;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-stone-200/80 bg-white/90 px-2 text-[11px] font-semibold text-stone-500">
            {step}
          </span>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-400">
            {title}
          </p>
        </div>
        <p className="mt-2 text-sm text-stone-500">{subtitle}</p>
      </div>
    </div>
  );
}

function MiniStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-stone-200/80 bg-stone-50/88 px-2.5 py-2">
      <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-stone-400">
        {label}
      </p>
      <p className="mt-0.5 text-xs font-semibold text-stone-900">{value}</p>
    </div>
  );
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
      if (!source || !target || source === target) {
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

  const sourceNodes = useMemo(
    () =>
      graph.points
        .filter((point) => point.isSource)
        .sort((a, b) => (a.citationIndex ?? 0) - (b.citationIndex ?? 0))
        .slice(0, 6),
    [graph.points],
  );

  const anchorNodes = useMemo(
    () => graph.points.filter((point) => point.isStarting && !point.isSource).slice(0, 6),
    [graph.points],
  );

  const expansionNodes = useMemo(
    () =>
      graph.points
        .filter((point) => point.isExpanded && !point.isSource && !point.isStarting)
        .slice(0, 8),
    [graph.points],
  );

  const relatedNodes = useMemo(
    () =>
      graph.points
        .filter((point) => !point.isSource && !point.isStarting && !point.isExpanded)
        .slice(0, 4),
    [graph.points],
  );

  const highlightedNode = useMemo(
    () =>
      highlightedSourceIndex !== null
        ? graph.points.find((point) => point.citationIndex === highlightedSourceIndex) ?? null
        : null,
    [graph.points, highlightedSourceIndex],
  );

  const visibleLinks = useMemo(() => {
    const visibleIds = new Set([
      ...sourceNodes.map((node) => node.id),
      ...anchorNodes.map((node) => node.id),
      ...expansionNodes.map((node) => node.id),
    ]);

    return graph.links.filter((link) => visibleIds.has(link.source) && visibleIds.has(link.target));
  }, [anchorNodes, expansionNodes, graph.links, sourceNodes]);

  const emitHighlight = useCallback(
    (citationIndex: number) => {
      onSourceSelect?.(citationIndex);
    },
    [onSourceSelect],
  );

  useEffect(() => {
    onHighlightRef?.(emitHighlight);
  }, [emitHighlight, onHighlightRef]);

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
    return (
      <div
        className={cn(
          'relative flex h-full w-full items-center justify-center overflow-hidden rounded-[30px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,248,235,0.98),_rgba(255,255,255,0.97)_45%,_rgba(247,243,235,0.98)_100%)] px-6 text-center shadow-[0_34px_90px_-52px_rgba(120,53,15,0.24)]',
          className,
        )}
      >
        <div className="absolute inset-0 opacity-50" style={{ backgroundImage: 'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        <div className="relative max-w-sm rounded-[28px] border border-stone-200/80 bg-white/88 px-6 py-6 shadow-[0_24px_60px_-40px_rgba(120,53,15,0.26)]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-stone-400">
            Answer Flow
          </p>
          <p className="mt-3 text-lg font-semibold text-stone-900">
            No source graph is available for this answer yet.
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            Run a GraphRAG answer with citations to populate the evidence, synthesis, and traversal lanes.
          </p>
        </div>
      </div>
    );
  }

  const focusLabel = highlightedNode
    ? `Focused on ${truncateLabel(highlightedNode.label, 40)}`
    : sourceNodes[0]
      ? `Start from ${truncateLabel(sourceNodes[0].label, 40)}`
      : 'Grounded answer flow';
  const connectionLabel =
    graph.links.length > 0 ? `${graph.links.length} traversal links` : 'Direct evidence path';

  return (
    <div
      className={cn(
        'relative h-full w-full overflow-hidden rounded-[30px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,247,232,0.98),_rgba(255,255,255,0.97)_42%,_rgba(247,243,235,0.98)_100%)] shadow-[inset_0_1px_0_rgba(255,255,255,0.88),0_34px_90px_-52px_rgba(120,53,15,0.28)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-55"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />
      <div className="pointer-events-none absolute -left-12 top-0 h-52 w-52 rounded-full bg-amber-200/25 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-56 w-56 rounded-full bg-sky-100/40 blur-3xl" />

      <div className="relative z-20 flex flex-wrap items-center justify-between gap-3 border-b border-stone-200/70 px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-amber-200/80 bg-amber-50/88 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-800">
            <Sparkles className="h-3.5 w-3.5" />
            Answer Flow
          </span>
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1.5 text-xs font-medium text-stone-500">
            {connectionLabel}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1.5 text-xs font-medium text-stone-500">
            {sourceNodes.length} sources
          </span>
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-3 py-1.5 text-xs font-medium text-stone-500">
            {graph.points.length} nodes
          </span>
        </div>
      </div>

      <svg
        viewBox="0 0 100 100"
        className="pointer-events-none absolute inset-0 z-10 hidden h-full w-full lg:block"
        role="img"
        aria-label={t('graphRagUi.answerMapAria')}
        preserveAspectRatio="none"
      >
        <defs>
          <radialGradient id="answer-flow-core" cx="50%" cy="50%" r="55%">
            <stop offset="0%" stopColor="rgba(251,191,36,0.13)" />
            <stop offset="100%" stopColor="rgba(251,191,36,0)" />
          </radialGradient>
        </defs>

        <circle cx="50" cy="55" r="18" fill="url(#answer-flow-core)" />
        <circle cx="50" cy="55" r="24" fill="none" stroke="rgba(231,229,228,0.72)" strokeDasharray="1.2 2.6" />
        <circle cx="50" cy="55" r="30" fill="none" stroke="rgba(231,229,228,0.45)" />

        {sourceNodes.map((node, index) => {
          const isActive = highlightedNode?.id === node.id;
          const y = distribute(index, sourceNodes.length, 28, 78);

          return (
            <motion.path
              key={`source-line-${node.id}`}
              d={curvePath(24, y, 43.5, 52 + (index - (sourceNodes.length - 1) / 2) * 1.8)}
              fill="none"
              stroke={node.color}
              strokeWidth={isActive ? 0.42 : 0.26}
              strokeOpacity={isActive ? 0.7 : 0.24}
              strokeDasharray={isActive ? '1.8 1.8' : '1.2 2.3'}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: 1,
                strokeDashoffset: isActive ? [-10, 0] : [0, -12],
                opacity: isActive ? [0.38, 0.8, 0.38] : [0.14, 0.34, 0.14],
              }}
              transition={{
                pathLength: { duration: 0.42, delay: index * 0.05 },
                strokeDashoffset: { duration: isActive ? 1.6 : 4.2, repeat: Infinity, ease: 'linear' },
                opacity: { duration: isActive ? 1.8 : 4.6, repeat: Infinity, ease: 'easeInOut' },
              }}
            />
          );
        })}

        {anchorNodes.map((node, index) => {
          const isActive = highlightedNode?.id === node.id;
          const y = distribute(index, anchorNodes.length, 31, 49);

          return (
            <motion.path
              key={`anchor-line-${node.id}`}
              d={curvePath(56.5, 50.5 + (index - (anchorNodes.length - 1) / 2) * 1.4, 76, y)}
              fill="none"
              stroke={node.color}
              strokeWidth={isActive ? 0.36 : 0.24}
              strokeOpacity={isActive ? 0.68 : 0.22}
              strokeDasharray={isActive ? '1.8 1.6' : '1.2 2.2'}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: 1,
                strokeDashoffset: isActive ? [-8, 0] : [0, -10],
                opacity: isActive ? [0.36, 0.76, 0.36] : [0.12, 0.28, 0.12],
              }}
              transition={{
                pathLength: { duration: 0.4, delay: 0.12 + index * 0.04 },
                strokeDashoffset: { duration: isActive ? 1.7 : 4.3, repeat: Infinity, ease: 'linear' },
                opacity: { duration: isActive ? 1.9 : 4.8, repeat: Infinity, ease: 'easeInOut' },
              }}
            />
          );
        })}

        {expansionNodes.map((node, index) => {
          const isActive = highlightedNode?.id === node.id;
          const y = distribute(index, expansionNodes.length, 59, 82);

          return (
            <motion.path
              key={`expansion-line-${node.id}`}
              d={curvePath(56.5, 59 + (index - (expansionNodes.length - 1) / 2) * 1.2, 76, y)}
              fill="none"
              stroke={node.color}
              strokeWidth={isActive ? 0.34 : 0.22}
              strokeOpacity={isActive ? 0.64 : 0.18}
              strokeDasharray={isActive ? '1.7 1.5' : '1.1 2.1'}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: 1,
                strokeDashoffset: isActive ? [-7, 0] : [0, -9],
                opacity: isActive ? [0.34, 0.72, 0.34] : [0.1, 0.22, 0.1],
              }}
              transition={{
                pathLength: { duration: 0.4, delay: 0.18 + index * 0.04 },
                strokeDashoffset: { duration: isActive ? 1.8 : 4.6, repeat: Infinity, ease: 'linear' },
                opacity: { duration: isActive ? 2 : 5, repeat: Infinity, ease: 'easeInOut' },
              }}
            />
          );
        })}

        {visibleLinks.slice(0, 8).map((link, index) => {
          const sourceIndex = sourceNodes.findIndex((node) => node.id === link.source);
          const targetAnchorIndex = anchorNodes.findIndex((node) => node.id === link.target);
          const targetExpansionIndex = expansionNodes.findIndex((node) => node.id === link.target);

          if (sourceIndex === -1 || (targetAnchorIndex === -1 && targetExpansionIndex === -1)) {
            return null;
          }

          const fromY = distribute(sourceIndex, sourceNodes.length, 28, 78);
          const toY =
            targetAnchorIndex >= 0
              ? distribute(targetAnchorIndex, anchorNodes.length, 31, 49)
              : distribute(targetExpansionIndex, expansionNodes.length, 59, 82);

          return (
            <motion.path
              key={`bridge-${link.source}-${link.target}-${index}`}
              d={curvePath(24, fromY, 76, toY)}
              fill="none"
              stroke={link.color}
              strokeWidth={0.16}
              strokeOpacity={0.08}
              strokeDasharray="0.8 2.2"
              animate={{ strokeDashoffset: [0, -10], opacity: [0.05, 0.12, 0.05] }}
              transition={{ duration: 5.4 + index * 0.3, repeat: Infinity, ease: 'linear' }}
            />
          );
        })}
      </svg>

      <div className="relative z-20 grid h-[calc(100%-61px)] min-h-0 gap-3 px-3 py-3 lg:grid-cols-[minmax(0,1fr)_minmax(220px,1.2fr)_minmax(0,1fr)]">
        <motion.section
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.28 }}
          className="flex min-h-0 flex-col rounded-[22px] border border-stone-200/80 bg-white/78 p-3 shadow-[0_24px_60px_-42px_rgba(120,53,15,0.2)] backdrop-blur-sm"
        >
          <LaneLabel
            step="01"
            title="Evidence Sources"
            subtitle={`${sourceNodes.length} citations`}
          />

          <div className="mt-3 space-y-1.5 overflow-y-auto pr-1">
            {sourceNodes.map((node, index) => {
              const theme = getGraphTypeTheme(node.type);
              const isActive = highlightedNode?.id === node.id;
              const citationId = node.citationIndex !== undefined ? node.citationIndex + 1 : index + 1;
              const sourceMeta = deferredResponse?.sources?.find((source) => source.nodeId === node.id);

              return (
                <motion.button
                  key={node.id}
                  type="button"
                  onClick={() => handleNodeActivate(node)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.24, delay: index * 0.04 }}
                  className={cn(
                    'group w-full rounded-[18px] border p-2.5 text-left transition-all duration-200',
                    isActive
                      ? 'border-transparent bg-white shadow-[0_20px_54px_-34px_rgba(120,53,15,0.3)] ring-2 ring-amber-200/70'
                      : 'border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(250,247,242,0.96))] hover:-translate-y-0.5 hover:border-stone-300 hover:bg-white',
                  )}
                  style={{
                    boxShadow: isActive ? `0 22px 54px -38px ${theme.color}55` : undefined,
                  }}
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <span
                      className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border text-xs font-semibold"
                      style={{
                        borderColor: theme.border,
                        backgroundColor: theme.tint,
                        color: theme.text,
                      }}
                    >
                      {citationId}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-stone-900">
                        {truncateLabel(node.label, 28)}
                      </p>
                      <p className="truncate text-[10px] text-stone-500">
                        {sourceMeta?.metadata?.period || formatGraphNodeType(node.type)}
                      </p>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.32 }}
          className="relative flex min-h-0 items-center justify-center rounded-[24px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(250,246,239,0.92))] px-3 py-4 shadow-[0_36px_80px_-50px_rgba(120,53,15,0.3)]"
        >
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-stone-200/70" />
            <div className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-stone-200/70" />
            <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-100/35 blur-2xl" />
          </div>

          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 6.6, repeat: Infinity, ease: 'easeInOut' }}
            className="relative w-full max-w-[22rem] rounded-[24px] border border-stone-200/80 bg-white/92 p-4 shadow-[0_28px_72px_-42px_rgba(120,53,15,0.36)] backdrop-blur"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-800">
                <Sparkles className="h-3.5 w-3.5" />
                Synthesis Core
              </span>
              <span className="rounded-full border border-stone-200/80 bg-stone-50/88 px-3 py-1 text-xs font-medium text-stone-500">
                {focusLabel}
              </span>
            </div>

            <h3 className="mt-3 text-base font-semibold leading-snug text-stone-900">
              {truncateLabel(deferredResponse?.query || 'Answer map', 56)}
            </h3>

            <div className="mt-3 grid grid-cols-2 gap-2">
              <MiniStat label="Grounding" value={`${sourceNodes.length} sources`} />
              <MiniStat
                label="Entry Nodes"
                value={anchorNodes.length > 0 ? `${anchorNodes.length} anchors` : 'Direct answer'}
              />
              <MiniStat
                label="Expansion"
                value={expansionNodes.length > 0 ? `${expansionNodes.length} nodes` : 'None'}
              />
              <MiniStat label="Links" value={graph.links.length > 0 ? `${graph.links.length}` : 'Direct'} />
            </div>

            {relatedNodes.length > 0 && (
              <div className="mt-4 rounded-[22px] border border-stone-200/80 bg-stone-50/78 p-3">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400">
                  Also in frame
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {relatedNodes.map((node) => {
                    const theme = getGraphTypeTheme(node.type);

                    return (
                      <button
                        key={node.id}
                        type="button"
                        onClick={() => handleNodeActivate(node)}
                        className="inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium transition-transform hover:-translate-y-0.5"
                        style={{
                          borderColor: theme.border,
                          backgroundColor: theme.tint,
                          color: theme.text,
                        }}
                      >
                        <span className="inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: theme.color }} />
                        {truncateLabel(node.label, 20)}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </motion.div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.28 }}
          className="flex min-h-0 flex-col gap-2 rounded-[22px] border border-stone-200/80 bg-white/78 p-3 shadow-[0_24px_60px_-42px_rgba(120,53,15,0.2)] backdrop-blur-sm"
        >
          <div className="rounded-[18px] border border-stone-200/80 bg-stone-50/82 p-3">
            <LaneLabel
              step="02"
              title="Entry Nodes"
              subtitle={
                anchorNodes.length > 0
                  ? `${anchorNodes.length} nodes directly anchoring the answer`
                  : 'This answer is driven directly from the selected sources'
              }
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {anchorNodes.length === 0 && (
                <p className="text-sm leading-6 text-stone-500">
                  No distinct anchor nodes were returned for this answer.
                </p>
              )}
              {anchorNodes.map((node, index) => {
                const theme = getGraphTypeTheme(node.type);
                const isActive = highlightedNode?.id === node.id;

                return (
                  <motion.button
                    key={node.id}
                    type="button"
                    onClick={() => handleNodeActivate(node)}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.24, delay: 0.08 + index * 0.04 }}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-medium transition-all',
                      isActive ? 'bg-white shadow-sm ring-2 ring-amber-200/70' : 'hover:-translate-y-0.5',
                    )}
                    style={{
                      borderColor: theme.border,
                      backgroundColor: isActive ? '#ffffff' : theme.tint,
                      color: theme.text,
                    }}
                  >
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                    {truncateLabel(node.label, 20)}
                  </motion.button>
                );
              })}
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col rounded-[18px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(248,244,236,0.92))] p-3">
            <LaneLabel
              step="03"
              title="Expansion Nodes"
              subtitle={
                expansionNodes.length > 0
                  ? `${expansionNodes.length} supporting nodes extending the reasoning`
                  : 'No secondary expansion nodes were needed here'
              }
            />

            <div className="mt-3 grid min-h-0 gap-2 overflow-y-auto pr-1 2xl:grid-cols-2">
              {expansionNodes.length === 0 && (
                <div className="rounded-[20px] border border-dashed border-stone-300 bg-stone-50/70 px-4 py-4 text-sm leading-6 text-stone-500">
                  The answer stays close to its cited evidence without extra branching.
                </div>
              )}

              {expansionNodes.map((node, index) => {
                const theme = getGraphTypeTheme(node.type);
                const isActive = highlightedNode?.id === node.id;

                return (
                  <motion.button
                    key={node.id}
                    type="button"
                    onClick={() => handleNodeActivate(node)}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.24, delay: 0.12 + index * 0.03 }}
                    className={cn(
                      'rounded-[14px] border px-2.5 py-2 text-left transition-all duration-200',
                      isActive
                        ? 'bg-white shadow-[0_18px_42px_-34px_rgba(120,53,15,0.26)] ring-2 ring-amber-200/70'
                        : 'bg-white/90 hover:-translate-y-0.5',
                    )}
                    style={{
                      borderColor: theme.border,
                      color: theme.text,
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: theme.color }} />
                      <p className="min-w-0 truncate text-xs font-semibold text-stone-900">
                        {truncateLabel(node.label, 22)}
                      </p>
                    </div>
                  </motion.button>
                );
              })}
            </div>
          </div>

          {graph.presentTypes.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {graph.presentTypes.slice(0, 5).map((type) => {
                const theme = getGraphTypeTheme(type);

                return (
                  <span
                    key={type}
                    className="inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-medium"
                    style={{
                      borderColor: theme.border,
                      backgroundColor: theme.tint,
                      color: theme.text,
                    }}
                  >
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                    {formatGraphNodeType(type)}
                  </span>
                );
              })}
            </div>
          )}
        </motion.section>
      </div>

      <div className="pointer-events-none absolute bottom-4 left-1/2 z-20 hidden -translate-x-1/2 lg:flex">
        <div className="inline-flex items-center gap-2 rounded-full border border-stone-200/80 bg-white/88 px-4 py-2 text-xs text-stone-500 shadow-[0_16px_44px_-32px_rgba(120,53,15,0.22)]">
          <Waypoints className="h-3.5 w-3.5 text-stone-400" />
          Click any source or node to pivot the evidence view.
        </div>
      </div>
    </div>
  );
}
