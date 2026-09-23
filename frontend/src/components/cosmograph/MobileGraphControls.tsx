import { useCallback, useEffect, useId, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion, useDragControls, useReducedMotion, type PanInfo } from 'framer-motion';
import { Filter as FilterIcon, Network, Route, SlidersHorizontal, Sparkles, X } from 'lucide-react';

import type { AtlasEdgeMeta, AtlasNodeMeta } from './AtlasHelpers';
import KgFilters, { type KgFilterState } from './KgFilters';
import KgSearchBar from './KgSearchBar';
import PathFinder, { type PathResult } from './PathFinder';

export type MobileTabId = 'atlas' | 'full' | 'path' | 'filter';

interface MobileGraphControlsProps {
  readonly nodes: ReadonlyArray<AtlasNodeMeta>;
  readonly activeTab: MobileTabId;
  readonly onTabChange: (tab: MobileTabId) => void;
  readonly filters: KgFilterState;
  readonly onFiltersChange: (state: KgFilterState) => void;
  readonly onPickNode: (node: AtlasNodeMeta) => void;
  readonly onOpenPathFinder: () => void;
  /** Used only when the path service omits edge relations. */
  readonly edges?: ReadonlyArray<AtlasEdgeMeta>;
  /** Lets the host highlight the computed path on the canvas. */
  readonly onPathComputed?: (path: PathResult | null) => void;
}

const EMPTY_EDGES: ReadonlyArray<AtlasEdgeMeta> = [];
const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function MobileGraphControls({
  nodes,
  activeTab,
  onTabChange,
  filters,
  onFiltersChange,
  onPickNode,
  onOpenPathFinder,
  edges = EMPTY_EDGES,
  onPathComputed,
}: MobileGraphControlsProps) {
  const { t } = useTranslation();
  const reduceMotion = useReducedMotion();
  const dragControls = useDragControls();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [pathSource, setPathSource] = useState<AtlasNodeMeta | null>(null);
  const [pathTarget, setPathTarget] = useState<AtlasNodeMeta | null>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const toolsButtonRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  const closeSheet = useCallback(() => {
    setSheetOpen(false);
    toolsButtonRef.current?.focus();
  }, []);

  const handlePathComputed = useCallback(
    (path: PathResult | null) => onPathComputed?.(path),
    [onPathComputed],
  );

  useEffect(() => {
    if (!sheetOpen) return;
    sheetRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeSheet();
        return;
      }
      if (event.key !== 'Tab' || !sheetRef.current) return;
      const focusables = [...sheetRef.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === sheetRef.current)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [sheetOpen, closeSheet]);

  const views = [
    { id: 'atlas' as const, icon: Sparkles, label: t('cosmograph.tabs.atlas', 'Atlas'), hint: t('cosmograph.mobile.atlasHint', 'The curated core') },
    { id: 'full' as const, icon: Network, label: t('cosmograph.tabs.full', 'Full graph'), hint: t('cosmograph.mobile.fullHint', 'Every node') },
    { id: 'filter' as const, icon: FilterIcon, label: t('cosmograph.tabs.filter', 'Filter'), hint: t('cosmograph.mobile.filterHint', 'Kind, period, school') },
    { id: 'path' as const, icon: Route, label: t('cosmograph.tabs.path', 'Find a path'), hint: t('cosmograph.mobile.pathHint', 'Link two nodes') },
  ];

  const activeFilterCount = filters.periods.length + filters.types.length + filters.schools.length;

  const onDragEnd = (_event: PointerEvent | MouseEvent | TouchEvent, info: PanInfo) => {
    if (info.offset.y > 90 || info.velocity.y > 600) closeSheet();
  };

  const sheetMotion = reduceMotion
    ? { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.12 } }
    : {
        initial: { y: '100%' },
        animate: { y: 0 },
        exit: { y: '100%' },
        transition: { type: 'spring' as const, stiffness: 420, damping: 40, mass: 0.9 },
      };

  return (
    <>
      {/* Bottom dock: search and tools stay within thumb reach and never
          collide with the top-right Explore/Map toggle. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-30 px-[max(0.75rem,env(safe-area-inset-left))] pb-[calc(2rem+env(safe-area-inset-bottom))] md:hidden">
        <div className="pointer-events-auto flex items-center gap-2">
          <div className="min-w-0 flex-1">
            <KgSearchBar
              size="sm"
              dropUp
              clearOnPick
              placeholder={t('cosmograph.search.placeholderShort', 'Search the graph…')}
              nodes={nodes}
              onPick={onPickNode}
              ariaLabel={t('cosmograph.searchAria', 'Search the knowledge graph')}
              emptyLabel={t('cosmograph.searchEmpty', 'No match.')}
              resultsLabel={t('cosmograph.searchResults', 'Search results')}
            />
          </div>
          <button
            ref={toolsButtonRef}
            type="button"
            onClick={() => setSheetOpen(true)}
            aria-label={t('cosmograph.mobile.openSheet', 'Open graph tools')}
            aria-haspopup="dialog"
            aria-expanded={sheetOpen}
            className="relative inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-teal-900 bg-teal-800 text-white shadow-[0_12px_28px_rgba(15,118,110,0.28)] transition-transform active:scale-95 motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2"
          >
            <SlidersHorizontal className="h-5 w-5" aria-hidden />
            {activeFilterCount > 0 && (
              <span className="absolute -right-1 -top-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-[#fffdf9] bg-orange-700 px-1 font-body text-[10px] font-bold">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {sheetOpen && (
          <>
            <motion.button
              key="scrim"
              type="button"
              tabIndex={-1}
              aria-hidden
              onClick={closeSheet}
              className="absolute inset-0 z-[45] cursor-default bg-stone-900/30 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: reduceMotion ? 0.1 : 0.2 }}
            />
            <motion.div
              key="sheet"
              ref={sheetRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              tabIndex={-1}
              drag={reduceMotion ? false : 'y'}
              dragConstraints={{ top: 0, bottom: 0 }}
              dragElastic={{ top: 0, bottom: 0.6 }}
              dragListener={false}
              dragControls={dragControls}
              dragSnapToOrigin
              onDragEnd={onDragEnd}
              {...sheetMotion}
              className="absolute inset-x-0 bottom-0 z-50 flex max-h-[88dvh] flex-col rounded-t-3xl border-t border-stone-300 bg-[#fffdf9] text-stone-900 shadow-[0_-24px_80px_rgba(72,52,36,0.2)] outline-none md:hidden"
            >
              <SheetHeader
                titleId={titleId}
                title={t('cosmograph.mobile.sheet.title', 'Graph tools')}
                closeLabel={t('common.close', 'Close')}
                onClose={closeSheet}
                onHandlePointerDown={reduceMotion ? undefined : (event) => dragControls.start(event)}
              />

              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-[calc(1.5rem+env(safe-area-inset-bottom))] pt-1">
                <div className="grid grid-cols-2 gap-2" role="group" aria-label={t('cosmograph.mobile.sheet.eyebrow', 'View')}>
                  {views.map((item) => {
                    const Icon = item.icon;
                    const active = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        aria-pressed={active}
                        onClick={() => {
                          onTabChange(item.id);
                          if (item.id === 'path') onOpenPathFinder();
                          if (item.id === 'atlas' || item.id === 'full') closeSheet();
                        }}
                        className={[
                          'flex min-h-14 items-center gap-2.5 rounded-2xl border px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700',
                          active
                            ? 'border-teal-700 bg-teal-50 text-teal-950'
                            : 'border-stone-300 bg-white text-stone-800 active:bg-stone-100',
                        ].join(' ')}
                      >
                        <span
                          className={[
                            'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
                            active ? 'bg-teal-700 text-white' : 'bg-stone-100 text-stone-600',
                          ].join(' ')}
                        >
                          <Icon className="h-4 w-4" aria-hidden />
                        </span>
                        <span className="min-w-0">
                          <span className="block font-body text-sm font-semibold leading-tight">{item.label}</span>
                          <span className="mt-0.5 line-clamp-2 font-body text-[12px] leading-4 text-stone-500">{item.hint}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>

                {activeTab === 'filter' && (
                  <div className="mt-5 border-t border-stone-200 pt-4">
                    <KgFilters
                      state={filters}
                      nodes={nodes}
                      onChange={onFiltersChange}
                      labels={{
                        period: t('cosmograph.filters.period', 'Period'),
                        type: t('cosmograph.filters.type', 'Type'),
                        school: t('cosmograph.filters.school', 'School'),
                        clear: t('cosmograph.filters.clear', 'Clear filters'),
                      }}
                    />
                  </div>
                )}

                {activeTab === 'path' && (
                  <div className="mt-5 border-t border-stone-200 pt-4">
                    <PathFinder
                      nodes={nodes}
                      edges={edges}
                      source={pathSource}
                      target={pathTarget}
                      onSourceChange={setPathSource}
                      onTargetChange={setPathTarget}
                      onPathComputed={handlePathComputed}
                      onNavigateToNode={(id) => {
                        const node = nodes.find((candidate) => candidate.id === id);
                        if (!node) return;
                        onPickNode(node);
                        closeSheet();
                      }}
                      labels={{
                        title: t('cosmograph.path.title', 'Find a path between two nodes'),
                        description: t('cosmograph.path.description', 'Choose two nodes. Their shortest route through the graph is traced step by step.'),
                        sourcePlaceholder: t('cosmograph.path.source', 'Source, e.g. Chrysippus'),
                        targetPlaceholder: t('cosmograph.path.target', 'Target, e.g. Augustine'),
                        searchAriaLabel: t('cosmograph.path.searchAria', 'Search for a node'),
                        searchEmpty: t('cosmograph.searchEmpty', 'No match.'),
                        searchResults: t('cosmograph.searchResults', 'Search results'),
                        computing: t('cosmograph.path.computing', 'Computing the shortest path…'),
                        noPath: t('cosmograph.path.noPath', 'No path within 6 hops.'),
                        error: t('cosmograph.path.error', 'Could not compute path'),
                        pathLength: (n) => t('cosmograph.path.length', { count: n, defaultValue: '{{count}} hops' }),
                        clear: t('cosmograph.path.clear', 'Clear'),
                        swap: t('cosmograph.path.swap', 'Swap source and target'),
                      }}
                    />
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

function SheetHeader({
  titleId,
  title,
  closeLabel,
  onClose,
  onHandlePointerDown,
}: {
  titleId: string;
  title: string;
  closeLabel: string;
  onClose: () => void;
  onHandlePointerDown?: (event: ReactPointerEvent<HTMLDivElement>) => void;
}) {
  // The header row is the only drag surface, so scrolling the sheet body
  // never fights the swipe-to-dismiss gesture.
  return (
    <div
      className="relative flex shrink-0 touch-none items-center justify-between px-4 pb-2 pt-2"
      onPointerDown={onHandlePointerDown}
    >
      <span aria-hidden className="absolute left-1/2 top-2 h-1 w-10 -translate-x-1/2 rounded-full bg-stone-300" />
      <h2 id={titleId} className="pt-3 font-display text-lg leading-none text-stone-950">
        {title}
      </h2>
      <button
        type="button"
        onClick={onClose}
        onPointerDown={(event) => event.stopPropagation()}
        aria-label={closeLabel}
        className="mt-1 inline-flex h-11 w-11 items-center justify-center rounded-full text-stone-500 transition-colors hover:bg-stone-100 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
      >
        <X className="h-5 w-5" aria-hidden />
      </button>
    </div>
  );
}
