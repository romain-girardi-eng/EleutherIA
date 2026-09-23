import { ArrowDown, ArrowUp, ArrowUpDown, Loader2, RotateCcw, X } from 'lucide-react';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../api/client';
import type { AtlasNodeMeta, AtlasEdgeMeta } from './AtlasHelpers';
import { useGraphVocabulary, vocabularySlug } from './graphVocabulary';
import KgSearchBar from './KgSearchBar';
import { getSearchIndex, searchGroupOf, searchNodes } from './searchIndex';

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
  /** Hide the title block when the host already provides one. */
  hideHeader?: boolean;
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

type PathStatus =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'found'; result: PathResult }
  | { kind: 'none' }
  | { kind: 'error'; message: string };

// Inverse labels that are nouns ("members") cannot sit between two steps.
const NOUN_INVERSES = new Set([
  'member_of',
  'responds_to',
  'student_of',
  'teaches',
  'contributes_to',
  'participates_in',
  'belongs_to_corpus',
]);

const EXAMPLE_ENDPOINTS: readonly [string, string] = ['Chrysippus', 'Augustine of Hippo'];

function buildPathEdges(
  pathIds: ReadonlyArray<string>,
  allEdges: ReadonlyArray<AtlasEdgeMeta>,
): Array<{ source: string; target: string; relation: string }> {
  const built: Array<{ source: string; target: string; relation: string }> = [];
  for (let i = 0; i < pathIds.length - 1; i += 1) {
    const a = pathIds[i];
    const b = pathIds[i + 1];
    const forward = allEdges.find((e) => e.source === a && e.target === b);
    const found = forward ?? allEdges.find((e) => e.source === b && e.target === a);
    built.push({
      source: found ? found.source : a,
      target: found ? found.target : b,
      // Unknown rather than a guessed 'related_to': never label a link we cannot see.
      relation: found?.relation ?? '',
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
  hideHeader = false,
}: PathFinderProps) {
  const { t } = useTranslation();
  const vocabulary = useGraphVocabulary();
  const [status, setStatus] = useState<PathStatus>({ kind: 'idle' });
  const [attempt, setAttempt] = useState(0);
  const [exampleMissing, setExampleMissing] = useState(false);

  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const inverseVerb = (relation: string) =>
    NOUN_INVERSES.has(relation)
      ? ''
      : t(`cosmograph.explore.inverse.${vocabularySlug(relation)}`, { defaultValue: '' });

  useEffect(() => {
    let cancelled = false;
    onPathComputed(null);

    if (!source || !target || source.id === target.id) {
      setStatus({ kind: 'idle' });
      return;
    }

    const src = source;
    const tgt = target;
    setStatus({ kind: 'loading' });

    async function run() {
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

        const ids: string[] = raw.path?.slice() ?? raw.nodes?.map((n) => n.id) ?? [];
        if (ids.length < 2) {
          setStatus({ kind: 'none' });
          onPathComputed(null);
          return;
        }

        const pathEdges =
          raw.edges && raw.edges.length > 0
            ? raw.edges.map((e) => ({
                source: e.source,
                target: e.target,
                relation: e.relation ?? '',
              }))
            : buildPathEdges(ids, edges);

        const next: PathResult = { ids, edges: pathEdges };
        setStatus({ kind: 'found', result: next });
        onPathComputed(next);
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : String(err);
        setStatus(message.includes('404') ? { kind: 'none' } : { kind: 'error', message });
        onPathComputed(null);
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [source, target, edges, onPathComputed, attempt]);

  function swap() {
    onSourceChange(target);
    onTargetChange(source);
  }

  function loadExample() {
    const index = getSearchIndex(nodes);
    const [from, to] = EXAMPLE_ENDPOINTS.map(
      (label) => searchNodes(index, label, { limit: 1, group: 'person' }).hits[0]?.node ?? null,
    );
    if (!from || !to) {
      setExampleMissing(true);
      return;
    }
    onSourceChange(from);
    onTargetChange(to);
  }

  const searchProps = {
    size: 'sm' as const,
    nodes,
    ariaLabel: labels.searchAriaLabel,
    emptyLabel: labels.searchEmpty,
    resultsLabel: labels.searchResults,
    resultLimit: 8,
  };

  const sameNode = Boolean(source && target && source.id === target.id);

  return (
    <div className="flex flex-col gap-4 font-body text-stone-700">
      {!hideHeader && (
        <div>
          <h2 className="font-display text-xl leading-tight text-stone-950">{labels.title}</h2>
          <p className="mt-1.5 text-[13px] leading-5 text-stone-600">{labels.description}</p>
        </div>
      )}

      <div className="relative grid grid-cols-[1.75rem_1fr] gap-x-2 gap-y-2">
        <EndpointMarker kind="source" />
        <div>
          <p className="mb-1 text-[12px] font-semibold text-stone-600">{t('cosmograph.path.from', 'From')}</p>
          {source ? (
            <SlotPill
              node={source}
              groupLabel={vocabulary.group(searchGroupOf(source))}
              clearLabel={t('cosmograph.path.clearEndpoint', { label: source.label, defaultValue: 'Remove {{label}}' })}
              onClear={() => onSourceChange(null)}
              onClick={() => onNavigateToNode(source.id)}
            />
          ) : (
            <KgSearchBar {...searchProps} onPick={onSourceChange} placeholder={labels.sourcePlaceholder} />
          )}
        </div>

        <div className="col-start-2 -my-1 flex items-center gap-2">
          <button
            type="button"
            onClick={swap}
            aria-label={labels.swap}
            title={labels.swap}
            disabled={!source && !target}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-stone-300 bg-white px-3 text-[12px] font-semibold text-stone-700 transition-colors hover:border-teal-700 hover:text-teal-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 disabled:cursor-not-allowed disabled:opacity-40 [@media(pointer:coarse)]:min-h-11"
          >
            <ArrowUpDown className="h-3.5 w-3.5" aria-hidden />
            {t('cosmograph.path.swapShort', 'Swap')}
          </button>
        </div>

        <EndpointMarker kind="target" />
        <div>
          <p className="mb-1 text-[12px] font-semibold text-stone-600">{t('cosmograph.path.to', 'To')}</p>
          {target ? (
            <SlotPill
              node={target}
              groupLabel={vocabulary.group(searchGroupOf(target))}
              clearLabel={t('cosmograph.path.clearEndpoint', { label: target.label, defaultValue: 'Remove {{label}}' })}
              onClear={() => onTargetChange(null)}
              onClick={() => onNavigateToNode(target.id)}
            />
          ) : (
            <KgSearchBar {...searchProps} onPick={onTargetChange} placeholder={labels.targetPlaceholder} />
          )}
        </div>
        <span aria-hidden className="pointer-events-none absolute bottom-6 left-[0.875rem] top-6 w-px -translate-x-1/2 border-l border-dashed border-stone-300" />
      </div>

      {!source && !target && !exampleMissing && (
        <button
          type="button"
          onClick={loadExample}
          className="self-start text-left text-[12px] text-teal-800 underline decoration-teal-700/30 underline-offset-2 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
        >
          {t('cosmograph.path.example', 'Try an example: Chrysippus to Augustine')}
        </button>
      )}

      {sameNode && (
        <p className="rounded-xl border border-stone-300 bg-stone-50 px-3 py-2 text-[13px] leading-5 text-stone-700" role="status">
          {t('cosmograph.path.same', 'Source and target are the same node. Choose a different target.')}
        </p>
      )}

      <div aria-live="polite" aria-busy={status.kind === 'loading'}>
        {status.kind === 'loading' && (
          <p className="flex items-center gap-2 text-[13px] text-stone-600">
            <Loader2 className="h-4 w-4 animate-spin text-teal-700 motion-reduce:animate-none" aria-hidden />
            {labels.computing}
          </p>
        )}

        {status.kind === 'none' && (
          <div className="rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-3 text-[13px] leading-5 text-amber-950">
            <p className="font-semibold">{t('cosmograph.path.noPathTitle', 'No connection found')}</p>
            <p className="mt-1">
              {t('cosmograph.path.noPathHelp', 'These two nodes are not linked within 6 steps. Try a more central endpoint, such as a school, a concept or the author of a work, rather than a single passage.')}
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              <GhostButton onClick={() => onTargetChange(null)}>{t('cosmograph.path.changeTarget', 'Change target')}</GhostButton>
              <GhostButton onClick={() => onSourceChange(null)}>{t('cosmograph.path.changeSource', 'Change source')}</GhostButton>
            </div>
          </div>
        )}

        {status.kind === 'error' && (
          <div className="rounded-xl border border-red-300 bg-red-50 px-3.5 py-3 text-[13px] leading-5 text-red-950">
            <p className="font-semibold">{labels.error}</p>
            <p className="mt-1 break-words text-red-900/80">{status.message}</p>
            <div className="mt-2.5">
              <GhostButton onClick={() => setAttempt((n) => n + 1)}>
                <RotateCcw className="h-3.5 w-3.5" aria-hidden />
                {t('cosmograph.path.retry', 'Try again')}
              </GhostButton>
            </div>
          </div>
        )}

        {status.kind === 'found' && (
          <section aria-label={labels.title} className="rounded-xl border border-stone-300 bg-white/80 p-3">
            <p className="mb-2 flex items-baseline justify-between gap-2 text-[12px] text-stone-600">
              <strong className="font-semibold text-teal-800">{labels.pathLength(status.result.ids.length - 1)}</strong>
              <span>{t('cosmograph.path.tapStep', 'Select a step to focus it')}</span>
            </p>
            <ol className="relative">
              {status.result.ids.map((id, index) => {
                const node = nodeMap.get(id);
                const edge = index > 0 ? status.result.edges[index - 1] : null;
                const previousId = status.result.ids[index - 1];
                const forward = edge ? edge.source === previousId : true;
                const previousLabel = nodeMap.get(previousId ?? '')?.label ?? previousId ?? '';
                const label = node?.label ?? id;
                // A backwards edge reads top-down through its inverse verb
                // ("influences") when one exists; otherwise the arrow flips.
                const inverse = forward ? '' : inverseVerb(edge?.relation ?? '');
                const readsDown = forward || inverse !== '';
                const shown = edge ? (forward ? vocabulary.relation(edge.relation) : inverse || vocabulary.relation(edge.relation)) : '';
                return (
                  <li key={`${id}-${index}`}>
                    {edge && !edge.relation && (
                      <span aria-hidden className="ml-[0.95rem] block h-4 w-px bg-stone-300" />
                    )}
                    {edge && edge.relation && (
                      <p className="flex items-center gap-1.5 py-0.5 pl-[0.6rem] text-[12px] text-stone-500">
                        <span aria-hidden className="mr-1 h-4 w-px bg-stone-300" />
                        {readsDown ? <ArrowDown className="h-3 w-3" aria-hidden /> : <ArrowUp className="h-3 w-3" aria-hidden />}
                        <span aria-hidden>{shown}</span>
                        <span className="sr-only">
                          {forward
                            ? t('cosmograph.path.stepForward', { from: previousLabel, relation: vocabulary.relation(edge.relation), to: label, defaultValue: '{{from}} {{relation}} {{to}}' })
                            : t('cosmograph.path.stepForward', { from: label, relation: vocabulary.relation(edge.relation), to: previousLabel, defaultValue: '{{from}} {{relation}} {{to}}' })}
                        </span>
                      </p>
                    )}
                    <button
                      type="button"
                      onClick={() => onNavigateToNode(id)}
                      className="group flex min-h-10 w-full items-center gap-2.5 rounded-lg px-1.5 py-1 text-left hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:min-h-11"
                    >
                      <span
                        aria-hidden
                        className="h-3 w-3 shrink-0 rounded-full ring-2 ring-white"
                        style={{ backgroundColor: node?.color ?? '#94a3b8' }}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13px] font-semibold text-stone-900 group-hover:text-orange-900">{label}</span>
                        {node && (
                          <span className="block truncate text-[11px] text-stone-500">{vocabulary.group(searchGroupOf(node))}</span>
                        )}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>

      {(source || target) && (
        <button
          type="button"
          onClick={() => {
            onSourceChange(null);
            onTargetChange(null);
          }}
          className="inline-flex min-h-9 items-center gap-1.5 self-end rounded-full border border-stone-300 bg-white px-3 text-[12px] text-stone-600 transition-colors hover:border-orange-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:min-h-11"
        >
          <X className="h-3.5 w-3.5" aria-hidden />
          {labels.clear}
        </button>
      )}
    </div>
  );
}

function EndpointMarker({ kind }: { kind: 'source' | 'target' }) {
  return (
    <span
      aria-hidden
      className={[
        'relative z-10 mt-[1.85rem] inline-flex h-7 w-7 items-center justify-center rounded-full border-2 bg-[#fffdf9]',
        kind === 'source' ? 'border-teal-700' : 'border-orange-800',
      ].join(' ')}
    >
      <span className={['h-2.5 w-2.5 rounded-full', kind === 'source' ? 'bg-teal-700' : 'bg-orange-800'].join(' ')} />
    </span>
  );
}

function GhostButton({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-stone-300 bg-white/80 px-3 text-[12px] font-semibold transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:min-h-11"
    >
      {children}
    </button>
  );
}

function SlotPill({
  node,
  groupLabel,
  clearLabel,
  onClear,
  onClick,
}: {
  node: AtlasNodeMeta;
  groupLabel: string;
  clearLabel: string;
  onClear: () => void;
  onClick: () => void;
}) {
  return (
    <div className="flex min-h-10 items-center gap-1 rounded-2xl border border-stone-300 bg-white py-1 pl-3 pr-1 [@media(pointer:coarse)]:min-h-11">
      <button
        type="button"
        onClick={onClick}
        className="flex min-w-0 flex-1 items-center gap-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
      >
        <span aria-hidden className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: node.color }} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-stone-900">{node.label}</span>
          <span className="block truncate text-[11px] text-stone-500">{groupLabel}</span>
        </span>
      </button>
      <button
        type="button"
        onClick={onClear}
        aria-label={clearLabel}
        className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-stone-500 transition-colors hover:bg-stone-100 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 [@media(pointer:coarse)]:h-11 [@media(pointer:coarse)]:w-11"
      >
        <X className="h-4 w-4" aria-hidden />
      </button>
    </div>
  );
}
