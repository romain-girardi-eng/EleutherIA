import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Filter as FilterIcon,
  Layers,
  Network,
  Route,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

import type { MobileTier } from '../../hooks/useMobileGraphTiers';
import type { AtlasNodeMeta } from './AtlasHelpers';
import KgFilters, { type KgFilterState } from './KgFilters';
import KgSearchBar from './KgSearchBar';

export type MobileTabId = 'atlas' | 'full' | 'path' | 'filter';

interface MobileGraphControlsProps {
  readonly tier: MobileTier;
  readonly visibleNodeCount: number;
  readonly nodes: ReadonlyArray<AtlasNodeMeta>;
  readonly activeTab: MobileTabId;
  readonly onTabChange: (tab: MobileTabId) => void;
  readonly filters: KgFilterState;
  readonly onFiltersChange: (state: KgFilterState) => void;
  readonly onPickNode: (node: AtlasNodeMeta) => void;
  readonly onOpenPathFinder: () => void;
}

const HINT_STORAGE_KEY = 'eleutheria.kg.mobile.hint.shown';

const TIER_LABEL: Record<MobileTier, { i18nKey: string; fallback: string }> = {
  atlas: { i18nKey: 'cosmograph.mobile.tier.atlas', fallback: 'Atlas' },
  schools: { i18nKey: 'cosmograph.mobile.tier.schools', fallback: 'Schools' },
  detail: { i18nKey: 'cosmograph.mobile.tier.detail', fallback: 'Detail' },
};

const TIER_ICON: Record<MobileTier, typeof Sparkles> = {
  atlas: Sparkles,
  schools: Layers,
  detail: Network,
};

export default function MobileGraphControls({
  tier,
  visibleNodeCount,
  nodes,
  activeTab,
  onTabChange,
  filters,
  onFiltersChange,
  onPickNode,
  onOpenPathFinder,
}: MobileGraphControlsProps) {
  const { t } = useTranslation();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(true);
  const [hintVisible, setHintVisible] = useState(false);
  const searchInputRef = useRef<HTMLDivElement | null>(null);

  // First-visit hint
  useEffect(() => {
    try {
      const shown = window.localStorage.getItem(HINT_STORAGE_KEY);
      if (!shown) setHintVisible(true);
    } catch {
      // localStorage may throw in private mode; ignore.
    }
  }, []);

  const dismissHint = () => {
    setHintVisible(false);
    try {
      window.localStorage.setItem(HINT_STORAGE_KEY, '1');
    } catch {
      // ignore
    }
  };

  // Collapse search on first user interaction (touch/zoom outside).
  useEffect(() => {
    let collapsed = false;
    function collapseOnInteract() {
      if (collapsed) return;
      collapsed = true;
      setSearchOpen(false);
    }
    window.addEventListener('touchstart', collapseOnInteract, { passive: true, once: true });
    window.addEventListener('wheel', collapseOnInteract, { passive: true, once: true });
    return () => {
      window.removeEventListener('touchstart', collapseOnInteract);
      window.removeEventListener('wheel', collapseOnInteract);
    };
  }, []);

  const TierIcon = TIER_ICON[tier];
  const tierLabel = t(TIER_LABEL[tier].i18nKey, TIER_LABEL[tier].fallback);

  return (
    <>
      {/* === Collapsible search top-left === */}
      <div className="pointer-events-auto absolute left-3 top-3 z-30 md:hidden">
        {searchOpen ? (
          <div ref={searchInputRef} className="w-[min(82vw,22rem)]">
            <KgSearchBar
              placeholder={t(
                'cosmograph.searchPlaceholder',
                'Search a concept, thinker, work, or scholar…',
              )}
              nodes={nodes}
              onPick={(node) => {
                onPickNode(node);
                setSearchOpen(false);
              }}
              ariaLabel={t('cosmograph.searchAria', 'Search the knowledge graph')}
              emptyLabel={t('cosmograph.searchEmpty', 'No match.')}
              resultsLabel={t('cosmograph.searchResults', 'Search results')}
            />
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setSearchOpen(true)}
            aria-label={t('cosmograph.mobile.searchOpen', 'Open search')}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-slate-950/80 text-slate-200 shadow-[0_8px_24px_rgba(2,6,23,0.45)] backdrop-blur-xl transition-colors hover:text-white"
          >
            <Search className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* === Tier indicator pill (bottom-right above FAB) === */}
      <div className="pointer-events-none absolute bottom-[8.5rem] right-3 z-20 md:hidden">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/82 px-3 py-1.5 text-[11px] font-medium text-slate-200 shadow-[0_8px_24px_rgba(2,6,23,0.45)] backdrop-blur-xl">
          <TierIcon className="h-3.5 w-3.5 text-cyan-200" aria-hidden="true" />
          <span className="font-semibold">{tierLabel}</span>
          <span className="text-slate-400">·</span>
          <span>
            {t('cosmograph.mobile.nodeCount', '{{count}} nodes', {
              count: visibleNodeCount,
            })}
          </span>
        </div>
      </div>

      {/* === Single sticky FAB (bottom-right, above BottomTabNav h-16) === */}
      <button
        type="button"
        onClick={() => setSheetOpen(true)}
        aria-label={t('cosmograph.mobile.openSheet', 'Open graph tools')}
        aria-expanded={sheetOpen}
        className="pointer-events-auto absolute bottom-20 right-3 z-30 inline-flex h-14 w-14 items-center justify-center rounded-full border border-cyan-300/30 bg-gradient-to-br from-cyan-400/95 to-cyan-600/95 text-slate-950 shadow-[0_14px_32px_rgba(34,211,238,0.4)] transition-transform active:scale-95 md:hidden"
      >
        <TierIcon className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* === Pinch-to-zoom hint overlay (first visit only) === */}
      {hintVisible && (
        <div className="pointer-events-auto absolute inset-x-3 bottom-40 z-40 mx-auto max-w-sm rounded-2xl border border-cyan-300/20 bg-slate-950/92 p-4 text-[12px] text-slate-200 shadow-[0_24px_60px_rgba(2,6,23,0.6)] backdrop-blur-xl md:hidden">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-cyan-300/30 bg-cyan-300/10">
              <Sparkles className="h-4 w-4 text-cyan-200" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-white">
                {t('cosmograph.mobile.hint.title', 'Pinch to dive deeper')}
              </p>
              <p className="mt-1 leading-5 text-slate-300">
                {t(
                  'cosmograph.mobile.hint.body',
                  'You start with the 12 most central nodes. Pinch-zoom in and more thinkers, schools and arguments appear.',
                )}
              </p>
              <button
                type="button"
                onClick={dismissHint}
                className="mt-3 inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-slate-100 transition-colors hover:bg-white/[0.08]"
              >
                {t('cosmograph.mobile.hint.dismiss', 'Got it')}
              </button>
            </div>
            <button
              type="button"
              onClick={dismissHint}
              aria-label={t('common.dismiss', 'Dismiss')}
              className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:text-white"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* === Bottom-sheet (FAB target) === */}
      {sheetOpen && (
        <>
          <button
            type="button"
            aria-label={t('common.close', 'Close')}
            onClick={() => setSheetOpen(false)}
            className="absolute inset-0 z-40 cursor-default bg-slate-950/55 backdrop-blur-sm md:hidden"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t('cosmograph.mobile.sheet.title', 'Graph tools')}
            className="pointer-events-auto absolute inset-x-0 bottom-0 z-40 max-h-[min(85vh,42rem)] overflow-hidden rounded-t-3xl border-t border-white/10 bg-slate-950/95 shadow-[0_-24px_80px_rgba(2,6,23,0.6)] backdrop-blur-2xl md:hidden"
          >
            <div className="flex items-center justify-between border-b border-white/8 px-5 py-3">
              <div className="flex items-center gap-2">
                <span aria-hidden className="h-1 w-10 rounded-full bg-white/15" />
              </div>
              <button
                type="button"
                onClick={() => setSheetOpen(false)}
                aria-label={t('common.close', 'Close')}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="overflow-y-auto px-5 pb-8 pt-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {t('cosmograph.mobile.sheet.eyebrow', 'View')}
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                {(
                  [
                    {
                      id: 'atlas' as MobileTabId,
                      icon: Sparkles,
                      label: t('cosmograph.tabs.atlas', 'Atlas'),
                    },
                    {
                      id: 'full' as MobileTabId,
                      icon: Network,
                      label: t('cosmograph.tabs.full', 'Full graph'),
                    },
                    {
                      id: 'path' as MobileTabId,
                      icon: Route,
                      label: t('cosmograph.tabs.path', 'Find a path'),
                    },
                    {
                      id: 'filter' as MobileTabId,
                      icon: FilterIcon,
                      label: t('cosmograph.tabs.filter', 'Filter'),
                    },
                  ] as const
                ).map((item) => {
                  const Icon = item.icon;
                  const active = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        onTabChange(item.id);
                        if (item.id === 'path') {
                          onOpenPathFinder();
                        }
                        setSheetOpen(false);
                      }}
                      aria-pressed={active}
                      className={[
                        'inline-flex items-center gap-2.5 rounded-2xl border px-4 py-3 text-left text-sm transition-colors',
                        active
                          ? 'border-cyan-300/40 bg-cyan-300/10 text-cyan-50 shadow-[0_10px_24px_rgba(34,211,238,0.18)]'
                          : 'border-white/10 bg-white/[0.03] text-slate-200 hover:bg-white/[0.06]',
                      ].join(' ')}
                    >
                      <span
                        className={[
                          'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full',
                          active ? 'bg-cyan-300/20 text-cyan-100' : 'bg-white/[0.04] text-slate-300',
                        ].join(' ')}
                      >
                        <Icon className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <span className="font-medium leading-tight">{item.label}</span>
                    </button>
                  );
                })}
              </div>

              {activeTab === 'filter' && (
                <div className="mt-5 border-t border-white/8 pt-5">
                  <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {t('cosmograph.tabs.filter', 'Filter')}
                  </p>
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
            </div>
          </div>
        </>
      )}
    </>
  );
}
