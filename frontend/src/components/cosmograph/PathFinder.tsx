import { ArrowRight, Route, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../../api/client';
import type { AtlasNodeMeta, AtlasEdgeMeta } from './AtlasHelpers';
import { relationLabel } from './AtlasHelpers';
import KgSearchBar from './KgSearchBar';

interface PathFinderProps {
  nodes: ReadonlyArray<AtlasNodeMeta>;
  edges: ReadonlyArray<AtlasEdgeMeta>;
  source: AtlasNodeMeta | null;
  target: AtlasNodeMeta | null;
  onSourceChange: (node: AtlasNodeMeta | null) => void;
  onTargetChange: (node: AtlasNodeMeta | null) => void;
  onPathComputed: (path: PathResult | null) => void;
  onNavigateToNode: (id: string) => void;
  labels: {
    title: string;
    description: string;
    sourcePlaceholder: string;
    targetPlaceholder: string;
    searchAriaLabel: string;
    searchEmpty: string;
    searchResults: string;
    computing: string;
    noPath: string;
    error: string;
    pathLength: (n: number) => string;
    clear: string;
    swap: string;
  };
}

export interface PathResult {
  ids: string[];
  edges: Array<{ source: string; target: string; relation: string }>;
}

type RawPathResponse = {
  path?: ReadonlyArray<string>;
  nodes?: ReadonlyArray<{ id: string }>;
  edges?: ReadonlyArray<{ source: string; target: string; relation?: string }>;
  length?: number;
};

function buildPathEdges(
  pathIds: ReadonlyArray<string>,
  allEdges: ReadonlyArray<AtlasEdgeMeta>,
): Array<{ source: string; target: string; relation: string }> {
  const built: Array<{ source: string; target: string; relation: string }> = [];
  for (let i = 0; i < pathIds.length - 1; i += 1) {
    const a = pathIds[i];
    const b = pathIds[i + 1];
    const found =
      allEdges.find((e) => e.source === a && e.target === b) ??
      allEdges.find((e) => e.source === b && e.target === a);
    built.push({
      source: a,
      target: b,
      relation: found?.relation ?? 'related_to',
    });
  }
  return built;
}

export default function PathFinder({
  nodes,
  edges,
  source,
  target,
  onSourceChange,
  onTargetChange,
  onPathComputed,
  onNavigateToNode,
  labels,
}: PathFinderProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PathResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  useEffect(() => {
    let cancelled = false;
    setResult(null);
    setErrorMessage(null);
    onPathComputed(null);

    if (!source || !target) {
      return;
    }
    if (source.id === target.id) {
      return;
    }

    async function run() {
      const src = source as AtlasNodeMeta;
      const tgt = target as AtlasNodeMeta;
      setLoading(true);
      try {
        // Backend expects { source, target } (kg_extras.py PathRequest).
        // The frontend api client typings call this `sourceId/targetId` —
        // we cast through unknown to send the wire-correct shape.
        const wireBody = { source: src.id, target: tgt.id } as unknown as {
          sourceId: string;
          targetId: string;
        };
        const raw = (await apiClient.computeGraphPath(wireBody)) as unknown as RawPathResponse;
        if (cancelled) return;

        const ids: string[] =
          raw.path?.slice() ??
          raw.nodes?.map((n) => n.id) ??
          [];

        if (ids.length < 2) {
          setResult(null);
          setErrorMessage(labels.noPath);
          onPathComputed(null);
          return;
        }

        const pathEdges =
          raw.edges && raw.edges.length > 0
            ? raw.edges.map((e) => ({
                source: e.source,
                target: e.target,
                relation: e.relation ?? 'related_to',
              }))
            : buildPathEdges(ids, edges);

        const next: PathResult = { ids, edges: pathEdges };
        setResult(next);
        onPathComputed(next);
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : String(err);
        if (message.includes('404')) {
          setErrorMessage(labels.noPath);
        } else {
          setErrorMessage(`${labels.error}: ${message}`);
        }
        setResult(null);
        onPathComputed(null);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [source, target, edges, labels.noPath, labels.error, onPathComputed]);

  function swap() {
    const a = source;
    const b = target;
    onSourceChange(b);
    onTargetChange(a);
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/75 p-3 backdrop-blur-xl">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
        <Route className="h-3.5 w-3.5" />
        {labels.title}
      </div>
      <p className="text-[11px] leading-5 text-slate-500">{labels.description}</p>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
        <div>
          {source ? (
            <SlotPill
              node={source}
              ariaLabel={labels.sourcePlaceholder}
              onClear={() => onSourceChange(null)}
              onClick={() => onNavigateToNode(source.id)}
            />
          ) : (
            <KgSearchBar
              size="sm"
              nodes={nodes}
              onPick={onSourceChange}
              placeholder={labels.sourcePlaceholder}
              ariaLabel={labels.searchAriaLabel}
              emptyLabel={labels.searchEmpty}
              resultsLabel={labels.searchResults}
              resultLimit={6}
            />
          )}
        </div>

        <button
          type="button"
          onClick={swap}
          aria-label={labels.swap}
          disabled={!source && !target}
          className="hidden h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-slate-950/60 text-slate-300 transition-colors hover:border-cyan-300/30 hover:text-white disabled:opacity-40 sm:inline-flex"
        >
          <ArrowRight className="h-4 w-4" />
        </button>

        <div>
          {target ? (
            <SlotPill
              node={target}
              ariaLabel={labels.targetPlaceholder}
              onClear={() => onTargetChange(null)}
              onClick={() => onNavigateToNode(target.id)}
            />
          ) : (
            <KgSearchBar
              size="sm"
              nodes={nodes}
              onPick={onTargetChange}
              placeholder={labels.targetPlaceholder}
              ariaLabel={labels.searchAriaLabel}
              emptyLabel={labels.searchEmpty}
              resultsLabel={labels.searchResults}
              resultLimit={6}
            />
          )}
        </div>
      </div>

      {loading && (
        <p className="text-[11px] text-slate-400" aria-live="polite">
          {labels.computing}
        </p>
      )}

      {errorMessage && !loading && (
        <p className="rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3 py-2 text-[11px] text-amber-100" aria-live="polite">
          {errorMessage}
        </p>
      )}

      {result && !loading && (
        <div className="rounded-xl border border-white/8 bg-[#040916]/80 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-cyan-100/80">
            {labels.pathLength(result.ids.length - 1)}
          </p>
          <ol className="space-y-1.5">
            {result.ids.map((id, index) => {
              const node = nodeMap.get(id);
              const incomingEdge = index > 0 ? result.edges[index - 1] : null;
              return (
                <li key={`${id}-${index}`} className="flex flex-col gap-0.5">
                  {incomingEdge && (
                    <span className="ml-3 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                      ↓ {relationLabel(incomingEdge.relation)}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => onNavigateToNode(id)}
                    className="flex items-center gap-2 rounded-lg px-2 py-1 text-left text-[12px] text-white hover:bg-white/[0.06]"
                  >
                    <span
                      aria-hidden
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: node?.color ?? '#94a3b8' }}
                    />
                    <span className="truncate">{node?.label ?? id}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </div>
      )}

      {(source || target || result || errorMessage) && (
        <button
          type="button"
          onClick={() => {
            onSourceChange(null);
            onTargetChange(null);
            setResult(null);
            setErrorMessage(null);
          }}
          className="self-end rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] text-slate-300 transition-colors hover:border-white/20 hover:text-white"
        >
          {labels.clear}
        </button>
      )}
    </div>
  );
}

function SlotPill({
  node,
  ariaLabel,
  onClear,
  onClick,
}: {
  node: AtlasNodeMeta;
  ariaLabel: string;
  onClear: () => void;
  onClick: () => void;
}) {
  return (
    <div
      aria-label={ariaLabel}
      className="flex items-center justify-between gap-2 rounded-2xl border border-amber-300/40 bg-amber-200/[0.07] px-3 py-2"
    >
      <button
        type="button"
        onClick={onClick}
        className="flex min-w-0 flex-1 items-center gap-2 text-left"
      >
        <span
          aria-hidden
          className="h-2.5 w-2.5 shrink-0 rounded-full"
          style={{ backgroundColor: node.color }}
        />
        <span className="min-w-0 flex-1 truncate text-sm font-semibold text-white">
          {node.label}
        </span>
      </button>
      <button
        type="button"
        onClick={onClear}
        aria-label="Clear"
        className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:border-white/20 hover:text-white"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}
