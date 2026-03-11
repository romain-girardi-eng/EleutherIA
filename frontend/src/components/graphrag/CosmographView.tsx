import { useDeferredValue, useMemo, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
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

  return `${label.slice(0, maxLength - 1)}…`;
}

/* ---------- small sub-components ---------- */

function SectionHeader({ step, title }: { step: string; title: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-stone-200/80 bg-white/90 px-1.5 text-[10px] font-semibold text-stone-500">
        {step}
      </span>
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-400">
        {title}
      </p>
    </div>
  );
}

/* ---------- main component ---------- */

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
  const deferredResponse = useDeferredValue(response);
  const deferredAllResponses = useDeferredValue(allResponses);

  /* ---- graph data computation (unchanged logic) ---- */

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
      if (!id) return;

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
      if (!source || !target || source === target) return;

      const key = `${source}->${target}`;
      if (linkSet.has(key)) return;

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
      if (sourceNode) sourceNode.degree += 1;
      if (targetNode) targetNode.degree += 1;
    });

    const orderedNodes = [...nodeMap.values()].sort((a, b) => {
      const aScore =
        (a.isSource ? 400 : 0) + (a.isStarting ? 250 : 0) + (a.isExpanded ? 80 : 0) + a.degree * 18 + a.occurrences * 6;
      const bScore =
        (b.isSource ? 400 : 0) + (b.isStarting ? 250 : 0) + (b.isExpanded ? 80 : 0) + b.degree * 18 + b.occurrences * 6;

      if (aScore !== bScore) return bScore - aScore;
      return a.label.localeCompare(b.label);
    });

    const idToColor = new Map<string, string>();
    const presentTypes = new Set<string>();

    const points = orderedNodes.map((node, index) => {
      const key = node.type?.toLowerCase() || 'default';
      const theme = getGraphTypeTheme(key);
      const baseSize = TYPE_SIZES[key] ?? TYPE_SIZES.default;
      const size =
        baseSize + (node.isSource ? 3.5 : 0) + (node.isStarting ? 1.5 : 0) + Math.min(node.degree * 0.3, 2);
      const labelWeight =
        (LABEL_WEIGHTS[key] ?? LABEL_WEIGHTS.default) + (node.isSource ? 0.18 : 0) + (node.isStarting ? 0.08 : 0);
      const importance = (node.isSource ? 3 : 0) + (node.isStarting ? 2 : 0) + (node.isExpanded ? 1 : 0) + node.degree;

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
        return { source: link.source, target: link.target, color: blendColors(sourceColor, targetColor) };
      })
      .filter((link) => link.source !== link.target);

    return { points, links, presentTypes: [...presentTypes] };
  }, [deferredAllResponses, deferredResponse]);

  /* ---- derived node groups ---- */

  const sourceNodes = useMemo(
    () =>
      graph.points
        .filter((p) => p.isSource)
        .sort((a, b) => (a.citationIndex ?? 0) - (b.citationIndex ?? 0))
        .slice(0, 6),
    [graph.points],
  );

  const anchorNodes = useMemo(
    () => graph.points.filter((p) => p.isStarting && !p.isSource).slice(0, 6),
    [graph.points],
  );

  const expansionNodes = useMemo(
    () => graph.points.filter((p) => p.isExpanded && !p.isSource && !p.isStarting).slice(0, 8),
    [graph.points],
  );

  const relatedNodes = useMemo(
    () => graph.points.filter((p) => !p.isSource && !p.isStarting && !p.isExpanded).slice(0, 4),
    [graph.points],
  );

  const highlightedNode = useMemo(
    () =>
      highlightedSourceIndex !== null
        ? graph.points.find((p) => p.citationIndex === highlightedSourceIndex) ?? null
        : null,
    [graph.points, highlightedSourceIndex],
  );

  /* ---- callbacks ---- */

  const emitHighlight = useCallback(
    (citationIndex: number) => { onSourceSelect?.(citationIndex); },
    [onSourceSelect],
  );

  useEffect(() => { onHighlightRef?.(emitHighlight); }, [emitHighlight, onHighlightRef]);

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

  /* ---- empty state ---- */

  if (graph.points.length === 0) {
    return (
      <div
        className={cn(
          'relative flex h-full w-full items-center justify-center overflow-hidden rounded-[24px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,248,235,0.98),_rgba(255,255,255,0.97)_45%,_rgba(247,243,235,0.98)_100%)] px-6 text-center shadow-[0_34px_90px_-52px_rgba(120,53,15,0.24)]',
          className,
        )}
      >
        <div className="absolute inset-0 opacity-50" style={{ backgroundImage: 'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        <div className="relative max-w-sm rounded-[22px] border border-stone-200/80 bg-white/88 px-5 py-5 shadow-[0_24px_60px_-40px_rgba(120,53,15,0.26)]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-stone-400">
            Answer Flow
          </p>
          <p className="mt-3 text-base font-semibold text-stone-900">
            No source graph yet.
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            Run a GraphRAG query to populate the evidence flow.
          </p>
        </div>
      </div>
    );
  }

  /* ---- main render: vertical stack ---- */

  const connectionLabel =
    graph.links.length > 0 ? `${graph.links.length} links` : 'Direct path';

  return (
    <div
      className={cn(
        'relative flex h-full w-full flex-col overflow-hidden rounded-[24px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,247,232,0.98),_rgba(255,255,255,0.97)_42%,_rgba(247,243,235,0.98)_100%)] shadow-[inset_0_1px_0_rgba(255,255,255,0.88),0_34px_90px_-52px_rgba(120,53,15,0.28)]',
        className,
      )}
    >
      {/* grid bg */}
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* header bar */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-2 border-b border-stone-200/70 px-3.5 py-2.5">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/80 bg-amber-50/88 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-800">
          <Sparkles className="h-3 w-3" />
          Answer Flow
        </span>
        <div className="flex items-center gap-1.5">
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-2.5 py-1 text-[11px] font-medium text-stone-500">
            {sourceNodes.length} sources
          </span>
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-2.5 py-1 text-[11px] font-medium text-stone-500">
            {graph.points.length} nodes
          </span>
          <span className="rounded-full border border-stone-200/80 bg-white/88 px-2.5 py-1 text-[11px] font-medium text-stone-500">
            {connectionLabel}
          </span>
        </div>
      </div>

      {/* scrollable body */}
      <div className="relative z-10 flex-1 space-y-3 overflow-y-auto p-3.5">

        {/* ---- synthesis core (query + stats) ---- */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.26 }}
          className="rounded-[20px] border border-stone-200/80 bg-white/92 p-4 shadow-[0_20px_50px_-36px_rgba(120,53,15,0.28)]"
        >
          <h3 className="text-base font-semibold leading-snug text-stone-900">
            {truncateLabel(deferredResponse?.query || 'Answer map', 80)}
          </h3>
          <div className="mt-3 grid grid-cols-4 gap-2">
            <div className="rounded-xl bg-stone-50/90 px-2.5 py-2">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-400">Sources</p>
              <p className="mt-0.5 text-sm font-semibold text-stone-900">{sourceNodes.length}</p>
            </div>
            <div className="rounded-xl bg-stone-50/90 px-2.5 py-2">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-400">Anchors</p>
              <p className="mt-0.5 text-sm font-semibold text-stone-900">{anchorNodes.length || '—'}</p>
            </div>
            <div className="rounded-xl bg-stone-50/90 px-2.5 py-2">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-400">Expanded</p>
              <p className="mt-0.5 text-sm font-semibold text-stone-900">{expansionNodes.length || '—'}</p>
            </div>
            <div className="rounded-xl bg-stone-50/90 px-2.5 py-2">
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-stone-400">Links</p>
              <p className="mt-0.5 text-sm font-semibold text-stone-900">{graph.links.length || '—'}</p>
            </div>
          </div>
        </motion.div>

        {/* ---- 01 · evidence sources ---- */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, delay: 0.04 }}
          className="rounded-[20px] border border-stone-200/80 bg-white/80 p-3.5 backdrop-blur-sm"
        >
          <SectionHeader step="01" title="Evidence Sources" />
          <div className="mt-2.5 space-y-1.5">
            {sourceNodes.map((node, index) => {
              const theme = getGraphTypeTheme(node.type);
              const isActive = highlightedNode?.id === node.id;
              const citationId = node.citationIndex !== undefined ? node.citationIndex + 1 : index + 1;
              const sourceMeta = deferredResponse?.sources?.find((s) => s.nodeId === node.id);

              return (
                <motion.button
                  key={node.id}
                  type="button"
                  onClick={() => handleNodeActivate(node)}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.03 }}
                  className={cn(
                    'flex w-full items-center gap-2.5 rounded-[14px] border px-3 py-2 text-left transition-all duration-150',
                    isActive
                      ? 'border-amber-300/80 bg-white shadow-[0_12px_30px_-20px_rgba(120,53,15,0.3)] ring-1 ring-amber-200/60'
                      : 'border-stone-200/80 bg-white/70 hover:bg-white hover:shadow-sm',
                  )}
                >
                  <span
                    className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border text-xs font-bold"
                    style={{ borderColor: theme.border, backgroundColor: theme.tint, color: theme.text }}
                  >
                    {citationId}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-stone-900">
                      {truncateLabel(node.label, 44)}
                    </p>
                    {sourceMeta?.content && (
                      <p className="mt-0.5 truncate text-xs text-stone-500">
                        {truncateLabel(sourceMeta.content, 60)}
                      </p>
                    )}
                  </div>
                  <span
                    className="shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase"
                    style={{ borderColor: theme.border, backgroundColor: theme.tint, color: theme.text }}
                  >
                    {formatGraphNodeType(node.type)}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* ---- 02 · anchor nodes ---- */}
        {anchorNodes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.24, delay: 0.08 }}
            className="rounded-[20px] border border-stone-200/80 bg-white/80 p-3.5 backdrop-blur-sm"
          >
            <SectionHeader step="02" title="Entry Nodes" />
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {anchorNodes.map((node, index) => {
                const theme = getGraphTypeTheme(node.type);
                const isActive = highlightedNode?.id === node.id;

                return (
                  <motion.button
                    key={node.id}
                    type="button"
                    onClick={() => handleNodeActivate(node)}
                    initial={{ opacity: 0, scale: 0.92 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2, delay: 0.06 + index * 0.03 }}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-medium transition-all',
                      isActive ? 'bg-white shadow-sm ring-2 ring-amber-200/70' : 'hover:shadow-sm',
                    )}
                    style={{
                      borderColor: theme.border,
                      backgroundColor: isActive ? '#ffffff' : theme.tint,
                      color: theme.text,
                    }}
                  >
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                    {truncateLabel(node.label, 28)}
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ---- 03 · expansion nodes ---- */}
        {expansionNodes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.24, delay: 0.12 }}
            className="rounded-[20px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(248,244,236,0.92))] p-3.5 backdrop-blur-sm"
          >
            <SectionHeader step="03" title="Expansion Nodes" />
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {expansionNodes.map((node, index) => {
                const theme = getGraphTypeTheme(node.type);
                const isActive = highlightedNode?.id === node.id;

                return (
                  <motion.button
                    key={node.id}
                    type="button"
                    onClick={() => handleNodeActivate(node)}
                    initial={{ opacity: 0, scale: 0.92 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2, delay: 0.08 + index * 0.02 }}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-medium transition-all',
                      isActive ? 'bg-white shadow-sm ring-2 ring-amber-200/70' : 'hover:shadow-sm',
                    )}
                    style={{
                      borderColor: theme.border,
                      backgroundColor: isActive ? '#ffffff' : theme.tint,
                      color: theme.text,
                    }}
                  >
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                    {truncateLabel(node.label, 28)}
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ---- also in frame ---- */}
        {relatedNodes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.24, delay: 0.16 }}
            className="rounded-[20px] border border-dashed border-stone-300/80 bg-stone-50/60 p-3.5"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-400">
              Also in frame
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {relatedNodes.map((node) => {
                const theme = getGraphTypeTheme(node.type);
                return (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => handleNodeActivate(node)}
                    className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs font-medium transition-all hover:shadow-sm"
                    style={{ borderColor: theme.border, backgroundColor: theme.tint, color: theme.text }}
                  >
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                    {truncateLabel(node.label, 24)}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>

      {/* ---- type legend (sticky bottom) ---- */}
      {graph.presentTypes.length > 0 && (
        <div className="relative z-10 flex flex-wrap gap-1.5 border-t border-stone-200/70 px-3.5 py-2.5">
          {graph.presentTypes.slice(0, 6).map((type) => {
            const theme = getGraphTypeTheme(type);
            return (
              <span
                key={type}
                className="inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-medium"
                style={{ borderColor: theme.border, backgroundColor: theme.tint, color: theme.text }}
              >
                <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: theme.color }} />
                {formatGraphNodeType(type)}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
