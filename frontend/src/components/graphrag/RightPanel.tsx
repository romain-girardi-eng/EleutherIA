import { useCallback, useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Network, Quote, Sparkles, Waypoints } from 'lucide-react';
import TraversalDAG from './TraversalDAG';
import ResearchGraphPanel from './ResearchGraphPanel';
import NodeDetailCard from './NodeDetailCard';
import PassageReaderPanel from './PassageReaderPanel';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse, SourceCitation } from '../../types';
import type { PassageContext } from '../../types/graphrag';
import { formatGraphNodeType, getGraphTypeTheme } from './graphTheme';

export type RightPanelState = 'idle' | 'loading' | 'graph' | 'passage-reader';

interface RightPanelProps {
  state: RightPanelState;
  response: GraphRAGResponse | null;
  allResponses?: GraphRAGResponse[];
  activeSourceIndex: number | null;
  passageContext?: PassageContext | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onSourceSelect?: (sourceIndex: number) => void;
  onLoadMorePassages?: (direction: 'up' | 'down') => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
}

function formatMetricValue(value: number | undefined) {
  if (value === undefined || Number.isNaN(value)) {
    return '--';
  }

  return value.toLocaleString();
}

function formatConfidence(value?: number) {
  if (value === undefined || Number.isNaN(value)) {
    return '--';
  }

  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function PanelHeader({
  state,
  response,
  sourcesCount,
}: {
  state: RightPanelState;
  response: GraphRAGResponse | null;
  sourcesCount: number;
}) {
  const { t } = useTranslation();

  const stateCopy: Record<RightPanelState, string> = {
    idle: t('graphRagUi.rightPanel.states.idle'),
    loading: t('graphRagUi.rightPanel.states.loading'),
    graph: t('graphRagUi.rightPanel.states.graph'),
    'passage-reader': t('graphRagUi.rightPanel.states.passageReader'),
  };

  const nodesVal = formatMetricValue(response?.reasoning_path?.total_nodes ?? response?.nodes_used);
  const edgesVal = formatMetricValue(response?.reasoning_path?.total_edges ?? response?.edges_traversed);
  const confVal = formatConfidence(response?.quality_metrics?.confidence_score);

  return (
    <div className="shrink-0 border-b border-stone-200/70 px-4 py-2.5">
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/80 bg-amber-50/90 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-800">
          <Network className="h-3 w-3" />
          {stateCopy[state]}
        </span>
        {response?.service && (
          <span className="inline-flex rounded-full border border-stone-200/80 bg-white/80 px-2 py-0.5 text-[10px] font-medium text-stone-500">
            {response.service}
          </span>
        )}
      </div>
      <h2 className="mt-1.5 text-sm font-semibold leading-snug text-stone-900 line-clamp-1">
        {response?.query || t('graphRagUi.rightPanel.fallbackQuery')}
      </h2>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full border border-blue-200/80 bg-blue-50/90 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-blue-800">
          {t('graphRagUi.rightPanel.previewBadge')}
        </span>
        <span className="text-[11px] leading-5 text-stone-500">
          {t('graphRagUi.rightPanel.previewCopy')}
        </span>
      </div>
      {/* Compact inline stats */}
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {[
          { l: t('graphRagUi.rightPanel.metrics.sources'), v: formatMetricValue(sourcesCount) },
          { l: t('graphRagUi.rightPanel.metrics.nodes'), v: nodesVal },
          { l: t('graphRagUi.rightPanel.metrics.edges'), v: edgesVal },
          ...(confVal !== '--' ? [{ l: t('graphRagUi.rightPanel.metrics.confidence'), v: confVal }] : []),
        ].map(({ l, v }) => (
          <span
            key={l}
            className="inline-flex items-center gap-1 rounded-full border border-stone-200/70 bg-white/70 px-2 py-0.5 text-[10px] text-stone-500"
          >
            <span className="font-semibold text-stone-700">{v}</span>
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}

function SourcesDeck({
  sources,
  activeSourceIndex,
  onSourceSelect,
}: {
  sources: SourceCitation[];
  activeSourceIndex: number | null;
  onSourceSelect?: (sourceIndex: number) => void;
}) {
  const { t } = useTranslation();

  if (sources.length === 0) {
    return (
      <div className="rounded-[24px] border border-dashed border-stone-300 bg-white/72 px-4 py-5 text-sm text-stone-500">
        {t('graphRagUi.rightPanel.noSources')}
      </div>
    );
  }

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {sources.map((source, index) => {
        const theme = getGraphTypeTheme(source.nodeType);
        const isActive = activeSourceIndex === index;

        return (
          <motion.button
            key={`${source.nodeId}-${source.id}`}
            layout
            onClick={() => onSourceSelect?.(index)}
            type="button"
            className={cn(
              'group relative overflow-hidden rounded-[24px] border p-4 text-left transition-all duration-200',
              isActive
                ? 'border-amber-300/90 bg-white shadow-[0_32px_70px_-44px_rgba(120,53,15,0.35)]'
                : 'border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(252,249,244,0.96))] hover:-translate-y-0.5 hover:border-stone-300 hover:bg-white',
            )}
            whileHover={{ y: -4 }}
            transition={{ duration: 0.2 }}
          >
            <div
              className="absolute inset-x-0 top-0 h-1"
              style={{ backgroundColor: theme.color }}
            />
            <div className="flex items-start justify-between gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-stone-100 text-sm font-bold text-stone-700">
                {source.id}
              </span>
              <span
                className="inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold"
                style={{
                  borderColor: theme.border,
                  backgroundColor: theme.tint,
                  color: theme.text,
                }}
              >
                {formatGraphNodeType(source.nodeType)}
              </span>
            </div>

            <p className="mt-4 text-base font-semibold leading-6 text-stone-900 line-clamp-2">
              {source.nodeLabel}
            </p>
            <p className="mt-2 text-sm leading-6 text-stone-500 line-clamp-3">
              {source.content || t('graphRagUi.rightPanel.sourceFallback')}
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-stone-500">
              {source.metadata?.period && (
                <span className="rounded-full border border-stone-200/80 bg-stone-50/80 px-2.5 py-1">
                  {source.metadata.period}
                </span>
              )}
              {source.metadata?.school && (
                <span className="rounded-full border border-stone-200/80 bg-stone-50/80 px-2.5 py-1 italic">
                  {source.metadata.school as string}
                </span>
              )}
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

function IdleState() {
  const { t } = useTranslation();

  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.28 }}
      className="flex h-full min-h-0 flex-col gap-4 p-4"
    >
      <div className="relative flex min-h-[320px] flex-1 items-center justify-center overflow-hidden rounded-[30px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,244,227,0.95),_rgba(255,255,255,0.96)_48%,_rgba(248,243,233,0.98)_100%)] p-8">
        <div className="absolute -left-12 top-0 h-36 w-36 rounded-full bg-amber-200/30 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-40 w-40 rounded-full bg-blue-100/30 blur-3xl" />

        <div className="relative max-w-md text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-white/80 bg-white/82 shadow-[0_24px_48px_-34px_rgba(120,53,15,0.35)]">
            <Network className="h-8 w-8 text-amber-700" />
          </div>
          <h3 className="mt-6 font-display text-3xl text-stone-900">
            {t('graphRagUi.rightPanel.answerConstellation')}
          </h3>
          <p className="mt-3 text-sm leading-7 text-stone-500">
            {t('graphRagUi.rightPanel.answerConstellationBody')}
          </p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {[
          {
            icon: Quote,
            title: t('graphRagUi.rightPanel.cards.evidenceFirst.title'),
            copy: t('graphRagUi.rightPanel.cards.evidenceFirst.copy'),
          },
          {
            icon: Waypoints,
            title: t('graphRagUi.rightPanel.cards.reasoningPath.title'),
            copy: t('graphRagUi.rightPanel.cards.reasoningPath.copy'),
          },
          {
            icon: BookOpen,
            title: t('graphRagUi.rightPanel.cards.passageAccess.title'),
            copy: t('graphRagUi.rightPanel.cards.passageAccess.copy'),
          },
        ].map(({ icon: Icon, title, copy }) => (
          <div
            key={title}
            className="rounded-[24px] border border-stone-200/80 bg-white/80 p-4 shadow-[0_20px_40px_-36px_rgba(120,53,15,0.25)]"
          >
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-parchment-100 text-amber-700">
              <Icon className="h-4 w-4" />
            </div>
            <p className="mt-4 text-sm font-semibold text-stone-900">{title}</p>
            <p className="mt-2 text-sm leading-6 text-stone-500">{copy}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function LoadingState() {
  const { t } = useTranslation();

  return (
    <motion.div
      key="loading"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.28 }}
      className="flex h-full min-h-0 flex-col gap-4 p-4"
    >
      <div className="relative flex min-h-[360px] flex-1 overflow-hidden rounded-[30px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_left,_rgba(255,244,227,0.96),_rgba(255,255,255,0.98)_44%,_rgba(247,242,232,0.98)_100%)] p-6">
        <div
          className="absolute inset-0 opacity-50"
          style={{
            backgroundImage:
              'linear-gradient(rgba(148,163,184,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.08) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />

        <div className="relative flex w-full flex-col justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-[20px] border border-white/80 bg-white/86 shadow-sm">
              {[0, 1, 2].map((index) => (
                <motion.div
                  key={index}
                  className="absolute inset-0 rounded-[20px] border border-amber-300/50"
                  initial={{ scale: 0.7, opacity: 0.8 }}
                  animate={{ scale: 1.45, opacity: 0 }}
                  transition={{ duration: 2.4, repeat: Infinity, delay: index * 0.4, ease: 'easeOut' }}
                />
              ))}
              <Sparkles className="h-5 w-5 text-amber-700" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-stone-400">
                {t('graphRagUi.rightPanel.loadingBadge')}
              </p>
              <p className="mt-1 text-base font-semibold text-stone-900">
                {t('graphRagUi.rightPanel.loadingTitle')}
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            {[0, 1, 2].map((card) => (
              <motion.div
                key={card}
                className="rounded-[22px] border border-stone-200/80 bg-white/80 p-4"
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 2.6, repeat: Infinity, delay: card * 0.15 }}
              >
                <div className="h-2.5 w-20 rounded-full bg-stone-200/80" />
                <div className="mt-4 h-3 rounded-full bg-stone-200/80" />
                <div className="mt-2 h-3 w-4/5 rounded-full bg-stone-200/60" />
                <div className="mt-6 flex gap-2">
                  <div className="h-7 w-7 rounded-2xl bg-amber-100/80" />
                  <div className="h-7 w-7 rounded-2xl bg-blue-100/70" />
                  <div className="h-7 w-7 rounded-2xl bg-green-100/70" />
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-8 rounded-[24px] border border-stone-200/80 bg-white/84 p-4 shadow-[0_20px_50px_-36px_rgba(120,53,15,0.28)]">
            <div className="flex items-center gap-2 text-sm font-medium text-stone-700">
              <Waypoints className="h-4 w-4 text-amber-700" />
              {t('graphRagUi.rightPanel.loadingBody')}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function RightPanel({
  state,
  response,
  allResponses,
  activeSourceIndex,
  passageContext,
  onNodeClick: _onNodeClick,
  onCloseDetail,
  onSourceSelect,
  onLoadMorePassages,
  onHighlightRef: _onHighlightRef,
  className = '',
}: RightPanelProps) {
  const navigate = useNavigate();
  const sources: SourceCitation[] = useMemo(
    () => response?.sources ?? [],
    [response?.sources],
  );

  // Local state for which node is selected in the DAG (shows detail card)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Resolve citation text for the selected node
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const citationTexts = (response as any)?.citationTexts as
    | Record<string, { original: string; originalLanguage: string; translation: string }>
    | undefined;

  const selectedSource = useMemo(() => {
    if (!selectedNodeId) return null;
    return sources.find((s) => s.nodeId === selectedNodeId) ?? null;
  }, [selectedNodeId, sources]);

  const selectedCitationText = useMemo(() => {
    if (!selectedSource || !citationTexts) return undefined;
    return citationTexts[selectedSource.nodeLabel] ?? undefined;
  }, [selectedSource, citationTexts]);

  useEffect(() => {
    if (activeSourceIndex === null) return;
    const source = sources[activeSourceIndex];
    if (source) {
      setSelectedNodeId(source.nodeId);
    }
  }, [activeSourceIndex, sources]);

  useEffect(() => {
    if (!_onHighlightRef) return;

    const highlightSource = (citationIndex: number) => {
      const source = sources[citationIndex];
      if (source) {
        setSelectedNodeId(source.nodeId);
      }
    };

    _onHighlightRef(highlightSource);

    return () => {
      _onHighlightRef(() => {});
    };
  }, [_onHighlightRef, sources]);


  // Handle node click from the DAG
  const handleDAGNodeSelect = useCallback(
    (nodeId: string, citationIndex?: number) => {
      if (nodeId === '__query__') return;
      setSelectedNodeId(nodeId);
      if (citationIndex !== undefined) {
        onSourceSelect?.(citationIndex);
      }
    },
    [onSourceSelect],
  );

  // Handle source card click from the SourcesDeck
  const handleSourceCardSelect = useCallback(
    (sourceIndex: number) => {
      const source = sources[sourceIndex];
      if (source) {
        setSelectedNodeId(source.nodeId);
        onSourceSelect?.(sourceIndex);
      }
    },
    [sources, onSourceSelect],
  );

  // When external citation clicks happen, also select the node in our local state
  // (This is registered via onHighlightRef from the parent)
  // Note: onHighlightRef is consumed directly below in the graph render

  return (
    <div
      className={cn(
        'relative flex h-full min-h-0 flex-col overflow-hidden rounded-[30px] border border-amber-200/60 bg-[linear-gradient(180deg,rgba(255,252,247,0.98),rgba(249,244,236,0.98))] shadow-[0_38px_90px_-52px_rgba(120,53,15,0.45)]',
        className,
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
      />
      <div className="pointer-events-none absolute -left-16 top-0 h-44 w-44 rounded-full bg-amber-200/22 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-56 w-56 rounded-full bg-blue-100/26 blur-3xl" />

      <div className="relative z-10 flex h-full min-h-0 flex-col">
        <PanelHeader
          state={state}
          response={response}
          sourcesCount={sources.length}
        />

        <div className="flex-1 min-h-0 overflow-hidden">
          <AnimatePresence mode="wait">
            {state === 'idle' && <IdleState />}

            {state === 'loading' && <LoadingState />}

            {state === 'graph' && (
              <motion.div
                key="graph"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.28 }}
                className="flex h-full min-h-0 flex-col gap-3 p-4"
              >
                {/* TOP: Interactive DAG */}
                <div className="h-[34%] min-h-[220px] shrink-0">
                  <TraversalDAG
                    response={response}
                    allResponses={allResponses}
                    highlightedSourceIndex={activeSourceIndex}
                    onNodeSelect={handleDAGNodeSelect}
                    className="h-full"
                  />
                </div>

                {/* MIDDLE: Explicit reasoning trace */}
                <div className="h-[34%] min-h-[240px] shrink-0 overflow-hidden">
                  <ResearchGraphPanel
                    response={response}
                    className="h-full"
                  />
                </div>

                {/* BOTTOM: Detail card or Sources deck */}
                <div className="flex-1 min-h-[200px] overflow-y-auto">
                  <AnimatePresence mode="wait">
                    {selectedSource ? (
                      <motion.div
                        key={`detail-${selectedSource.nodeId}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.22 }}
                      >
                        <NodeDetailCard
                          source={selectedSource}
                          citationText={selectedCitationText}
                          onClose={() => setSelectedNodeId(null)}
                          onOpenInDatabase={() => {
                            if (selectedSource.nodeId && !selectedSource.nodeId.startsWith('source_')) {
                              navigate(`/node/${selectedSource.nodeId}`);
                            }
                          }}
                        />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="sources-deck"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.22 }}
                      >
                        <SourcesDeck
                          sources={sources}
                          activeSourceIndex={activeSourceIndex}
                          onSourceSelect={handleSourceCardSelect}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}

            {state === 'passage-reader' && passageContext && (
              <motion.div
                key="passage-reader"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.24 }}
                className="h-full min-h-0 p-4"
              >
                <div className="min-h-[520px] overflow-hidden rounded-[26px] border border-stone-200/80 bg-white/82 shadow-[0_28px_70px_-42px_rgba(120,53,15,0.35)]">
                  <PassageReaderPanel
                    passageContext={passageContext}
                    onClose={onCloseDetail}
                    onLoadMore={onLoadMorePassages || (() => {})}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
