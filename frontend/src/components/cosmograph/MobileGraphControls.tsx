import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Filter as FilterIcon,
  Network,
  Route,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

import type { AtlasNodeMeta } from './AtlasHelpers';
import KgFilters, { type KgFilterState } from './KgFilters';
import KgSearchBar from './KgSearchBar';

export type MobileTabId = 'atlas' | 'full' | 'path' | 'filter';

interface MobileGraphControlsProps {
  readonly nodes: ReadonlyArray<AtlasNodeMeta>;
  readonly activeTab: MobileTabId;
  readonly onTabChange: (tab: MobileTabId) => void;
  readonly filters: KgFilterState;
  readonly onFiltersChange: (state: KgFilterState) => void;
  readonly onPickNode: (node: AtlasNodeMeta) => void;
  readonly onOpenPathFinder: () => void;
}

export default function MobileGraphControls({
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
  const searchInputRef = useRef<HTMLDivElement | null>(null);

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
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-stone-300 bg-[#fffdf9]/94 text-stone-700 shadow-[0_8px_24px_rgba(72,52,36,0.14)] backdrop-blur-xl transition-colors hover:border-orange-500 hover:text-orange-800"
          >
            <Search className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* === Single sticky FAB (bottom-right, above BottomTabNav h-16) === */}
      <button
        type="button"
        onClick={() => setSheetOpen(true)}
        aria-label={t('cosmograph.mobile.openSheet', 'Open graph tools')}
        aria-expanded={sheetOpen}
        className="pointer-events-auto absolute bottom-20 right-3 z-30 inline-flex h-14 w-14 items-center justify-center rounded-full border border-teal-800 bg-gradient-to-br from-teal-700 to-teal-900 text-white shadow-[0_14px_32px_rgba(15,118,110,0.28)] transition-transform active:scale-95 md:hidden"
      >
        <Network className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* === Bottom-sheet (FAB target) === */}
      {sheetOpen && (
        <>
          <button
            type="button"
            aria-label={t('common.close', 'Close')}
            onClick={() => setSheetOpen(false)}
            className="absolute inset-0 z-40 cursor-default bg-stone-900/25 backdrop-blur-sm md:hidden"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t('cosmograph.mobile.sheet.title', 'Graph tools')}
            className="pointer-events-auto absolute inset-x-0 bottom-0 z-40 max-h-[min(85vh,42rem)] overflow-hidden rounded-t-3xl border-t border-stone-300 bg-[#fffdf9]/98 text-stone-900 shadow-[0_-24px_80px_rgba(72,52,36,0.18)] backdrop-blur-2xl md:hidden"
          >
            <div className="flex items-center justify-between border-b border-stone-200 px-5 py-3">
              <div className="flex items-center gap-2">
                <span aria-hidden className="h-1 w-10 rounded-full bg-stone-300" />
              </div>
              <button
                type="button"
                onClick={() => setSheetOpen(false)}
                aria-label={t('common.close', 'Close')}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-stone-300 bg-white/70 text-stone-500 transition-colors hover:border-orange-500 hover:text-orange-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="overflow-y-auto px-5 pb-8 pt-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-500">
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
                          ? 'border-teal-700 bg-teal-50 text-teal-950 shadow-[0_10px_24px_rgba(15,118,110,0.12)]'
                          : 'border-stone-300 bg-white/70 text-stone-700 hover:border-orange-400 hover:bg-orange-50',
                      ].join(' ')}
                    >
                      <span
                        className={[
                          'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full',
                          active ? 'bg-teal-100 text-teal-800' : 'bg-stone-100 text-stone-600',
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
                <div className="mt-5 border-t border-stone-200 pt-5">
                  <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-500">
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
