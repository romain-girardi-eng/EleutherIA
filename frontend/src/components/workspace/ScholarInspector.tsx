import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  BookmarkCheck,
  BookmarkPlus,
  Columns3,
  LoaderCircle,
  RefreshCw,
  Trash2,
  X,
} from 'lucide-react';
import { memo, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import { MAX_COMPARE } from './scholarModel';
import { useScholarLabels } from './useScholarLabels';

const RELATIONS_COLLAPSED = 8;
const eyebrow = 'font-body text-[10px] font-semibold uppercase tracking-[0.2em] text-stone-500';
const focusRing = 'outline-none focus-visible:ring-2 focus-visible:ring-orange-700';

interface ScholarInspectorProps {
  metaById: ReadonlyMap<string, AtlasNodeMeta>;
  onOpenCompare: () => void;
  onToggleThread: (id: string) => void;
}

function ScholarInspectorComponent({ metaById, onOpenCompare, onToggleThread }: ScholarInspectorProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const {
    state,
    data,
    nodeDetailStates,
    selectPrimary,
    toggleCompare,
    setEvidenceThread,
    ensureNodeDetail,
  } = useGraphWorkspace();
  const [showAllRelations, setShowAllRelations] = useState(false);
  const [relationsFor, setRelationsFor] = useState<string | null>(null);

  const primaryId = state.primarySelection;
  const selected = primaryId ? data.rawById.get(primaryId) ?? null : null;
  const selectedMeta = primaryId ? metaById.get(primaryId) ?? null : null;
  const detailState = primaryId ? nodeDetailStates.get(primaryId) : undefined;
  const relationships = useMemo(
    () => (primaryId ? data.relationships.get(primaryId) ?? [] : []),
    [data.relationships, primaryId],
  );
  const expanded = showAllRelations && relationsFor === primaryId;
  const shownRelations = expanded ? relationships : relationships.slice(0, RELATIONS_COLLAPSED);
  const inThread = primaryId ? state.evidenceThread.includes(primaryId) : false;
  const isCompared = primaryId ? state.compareIds.includes(primaryId) : false;
  const compareFull = state.compareIds.length >= MAX_COMPARE;

  const labelOf = (id: string) => metaById.get(id)?.label ?? data.rawById.get(id)?.label ?? id;

  const moveThread = (index: number, delta: number) => {
    const next = [...state.evidenceThread];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setEvidenceThread(next);
  };

  return (
    <div className="space-y-7">
      <section aria-labelledby="scholar-primary-heading" aria-busy={detailState?.loading || undefined}>
        <h2 id="scholar-primary-heading" className={eyebrow}>{t('scholar.inspector.primary')}</h2>
        {selected ? (
          <>
            <p className="mt-3 font-display text-[2rem] leading-[1.05] tracking-[-0.01em] text-stone-950">{selected.label}</p>
            {(selected.greek_term || selected.latin_term) && (
              <p className="mt-1 font-reader text-lg text-stone-600">
                {[selected.greek_term, selected.latin_term].filter(Boolean).join(' · ')}
              </p>
            )}
            <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 font-body text-xs">
              <dt className="text-stone-500">{t('scholar.table.type')}</dt>
              <dd className="text-stone-800">{selectedMeta ? labels.nodeType(selectedMeta) : selected.type}</dd>
              <dt className="text-stone-500">{t('scholar.table.period')}</dt>
              <dd className="text-stone-800">{labels.period(selectedMeta?.periodLabel ?? selected.period ?? 'Unspecified')}</dd>
              {selected.dates && (
                <>
                  <dt className="text-stone-500">{t('scholar.inspector.dates')}</dt>
                  <dd className="text-stone-800">{selected.dates}</dd>
                </>
              )}
              <dt className="text-stone-500">{t('scholar.table.school')}</dt>
              <dd className="text-stone-800">{labels.school(selectedMeta?.schoolLabel ?? selected.school ?? 'Unattached')}</dd>
              <dt className="text-stone-500">{t('scholar.table.links')}</dt>
              <dd className="tabular-nums text-stone-800">{labels.number(selectedMeta?.degree ?? relationships.length)}</dd>
            </dl>

            {detailState?.loading && (
              <p role="status" aria-live="polite" className="mt-4 flex items-center gap-2 font-body text-sm text-stone-600">
                <LoaderCircle className="h-4 w-4 text-orange-700 motion-safe:animate-spin" aria-hidden="true" />
                {t('scholar.inspector.loadingDetail')}
              </p>
            )}
            {detailState?.error && (
              <div role="alert" className="mt-4 border-l-2 border-red-800 pl-3 font-body text-sm leading-6 text-stone-700">
                <p>{t('scholar.inspector.detailError')}</p>
                <button
                  type="button"
                  onClick={() => void ensureNodeDetail(selected.id)}
                  className="mt-1 inline-flex min-h-11 items-center gap-2 font-semibold text-red-800 underline decoration-red-300 underline-offset-4 outline-none hover:decoration-red-800 focus-visible:ring-2 focus-visible:ring-red-800"
                >
                  <RefreshCw className="h-4 w-4" aria-hidden="true" /> {t('scholar.inspector.retryDetail')}
                </button>
              </div>
            )}

            <p className="mt-5 font-reader text-[17px] leading-7 text-stone-700">
              {selected.description || t('scholar.inspector.noDescription')}
            </p>
            {selected.position_on_free_will && (
              <div className="mt-4 border-t border-stone-200 pt-3">
                <p className={eyebrow}>{t('scholar.inspector.position')}</p>
                <p className="mt-1.5 font-reader text-base leading-6 text-stone-700">{selected.position_on_free_will}</p>
              </div>
            )}
            {selected.ancient_sources && selected.ancient_sources.length > 0 && (
              <div className="mt-4 border-t border-stone-200 pt-3">
                <p className={eyebrow}>{t('scholar.inspector.sources')}</p>
                <ul className="mt-1.5 space-y-1 font-reader text-[15px] leading-6 text-stone-700">
                  {selected.ancient_sources.slice(0, 8).map((source) => <li key={source}>{source}</li>)}
                </ul>
              </div>
            )}

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => onToggleThread(selected.id)}
                aria-pressed={inThread}
                className={[
                  'inline-flex min-h-11 items-center gap-2 border px-4 font-body text-sm font-semibold transition-colors',
                  focusRing,
                  inThread
                    ? 'border-orange-800 bg-orange-800 text-[#fffdf9] hover:bg-orange-900'
                    : 'border-orange-700 text-orange-800 hover:bg-orange-50',
                ].join(' ')}
              >
                {inThread ? <BookmarkCheck className="h-4 w-4" aria-hidden="true" /> : <BookmarkPlus className="h-4 w-4" aria-hidden="true" />}
                {inThread ? t('scholar.inspector.inThread') : t('scholar.inspector.addThread')}
              </button>
              <button
                type="button"
                onClick={() => toggleCompare(selected.id)}
                aria-pressed={isCompared}
                disabled={!isCompared && compareFull}
                title={!isCompared && compareFull ? t('scholar.table.compareFull') : undefined}
                className={`inline-flex min-h-11 items-center gap-2 border border-teal-700 px-4 font-body text-sm font-semibold text-teal-800 transition-colors hover:bg-teal-50 disabled:cursor-not-allowed disabled:opacity-40 ${focusRing}`}
              >
                <Columns3 className="h-4 w-4" aria-hidden="true" />
                {isCompared ? t('scholar.inspector.removeCompare') : t('scholar.inspector.addCompare')}
              </button>
            </div>

            {relationships.length > 0 && (
              <div className="mt-6">
                <p className={eyebrow}>
                  {t('scholar.inspector.relations', { shown: labels.number(relationships.length), total: labels.number(selectedMeta?.degree ?? relationships.length) })}
                </p>
                <ul className="mt-2 divide-y divide-stone-200 border-y border-stone-200">
                  {shownRelations.map((relation, index) => (
                    <li key={`${relation.direction}:${relation.relation}:${relation.id}:${index}`}>
                      <button
                        type="button"
                        onClick={() => selectPrimary(relation.id)}
                        className={`grid min-h-11 w-full grid-cols-[1rem_1fr] items-center gap-2 py-1.5 text-left font-body text-sm hover:bg-[#f7f2e9] ${focusRing}`}
                      >
                        {relation.direction === 'outgoing'
                          ? <ArrowRight className="h-3.5 w-3.5 text-stone-400" aria-label={t('scholar.inspector.outgoing')} />
                          : <ArrowLeft className="h-3.5 w-3.5 text-stone-400" aria-label={t('scholar.inspector.incoming')} />}
                        <span className="min-w-0">
                          <span className="block text-[11px] uppercase tracking-[0.08em] text-teal-800">{labels.relation(relation.relation)}</span>
                          <span className="block truncate text-stone-800">{relation.label}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                {relationships.length > RELATIONS_COLLAPSED && (
                  <button
                    type="button"
                    aria-expanded={expanded}
                    onClick={() => {
                      setRelationsFor(primaryId);
                      setShowAllRelations(!expanded);
                    }}
                    className={`mt-1 inline-flex min-h-11 items-center font-body text-xs font-semibold text-teal-800 underline decoration-teal-300 underline-offset-4 hover:decoration-teal-800 ${focusRing}`}
                  >
                    {expanded ? t('scholar.inspector.fewerRelations') : t('scholar.inspector.allRelations', { count: relationships.length })}
                  </button>
                )}
              </div>
            )}
          </>
        ) : (
          <p className="mt-3 font-reader text-lg leading-7 text-stone-600">{t('scholar.inspector.empty')}</p>
        )}
      </section>

      <section aria-labelledby="scholar-compare-heading" className="border-t border-stone-300 pt-4">
        <div className="flex items-center justify-between gap-3">
          <h2 id="scholar-compare-heading" className={eyebrow}>
            {t('scholar.compare.heading', { count: state.compareIds.length, max: MAX_COMPARE })}
          </h2>
          {state.compareIds.length >= 2 && (
            <button
              type="button"
              onClick={onOpenCompare}
              className={`inline-flex min-h-11 items-center gap-1.5 font-body text-xs font-semibold text-teal-800 underline decoration-teal-300 underline-offset-4 hover:decoration-teal-800 ${focusRing}`}
            >
              <Columns3 className="h-4 w-4" aria-hidden="true" /> {t('scholar.compare.open')}
            </button>
          )}
        </div>
        {state.compareIds.length > 0 ? (
          <ol className="mt-2 divide-y divide-stone-200">
            {state.compareIds.map((id, index) => (
              <li key={id} className="grid grid-cols-[1.5rem_1fr_auto] items-center gap-2">
                <span aria-hidden="true" className="font-display text-xl text-teal-700">{index + 1}</span>
                <button type="button" onClick={() => selectPrimary(id)} className={`min-h-11 truncate text-left font-body text-sm font-semibold text-stone-800 hover:text-orange-800 ${focusRing}`}>
                  {labelOf(id)}
                </button>
                <button
                  type="button"
                  onClick={() => toggleCompare(id)}
                  aria-label={t('scholar.table.removeCompare', { label: labelOf(id) })}
                  className={`flex h-11 w-11 items-center justify-center text-stone-500 hover:text-orange-800 ${focusRing}`}
                >
                  <X className="h-4 w-4" aria-hidden="true" />
                </button>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-3 font-reader text-base leading-6 text-stone-600">{t('scholar.compare.emptyHint')}</p>
        )}
      </section>

      <section aria-labelledby="scholar-thread-heading" className="border-t border-stone-300 pt-4">
        <div className="flex items-center justify-between gap-3">
          <h2 id="scholar-thread-heading" className={eyebrow}>
            {t('scholar.thread.heading', { count: state.evidenceThread.length })}
          </h2>
          {state.evidenceThread.length > 0 && (
            <button
              type="button"
              onClick={() => setEvidenceThread([])}
              className={`inline-flex min-h-11 items-center gap-1.5 font-body text-xs font-semibold text-stone-600 hover:text-red-800 ${focusRing}`}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" /> {t('scholar.thread.clear')}
            </button>
          )}
        </div>
        {state.evidenceThread.length > 0 ? (
          <ol className="mt-2 border-l border-orange-300 pl-3">
            {state.evidenceThread.map((id, index) => (
              <li
                key={id}
                className="relative grid grid-cols-[1fr_auto] items-center before:absolute before:-left-[1.05rem] before:top-1/2 before:h-2 before:w-2 before:-translate-y-1/2 before:rounded-full before:bg-orange-700"
              >
                <button type="button" onClick={() => selectPrimary(id)} className={`min-h-11 truncate text-left font-body text-sm text-stone-800 hover:text-orange-800 ${focusRing}`}>
                  <span className="mr-2 tabular-nums text-stone-400">{index + 1}.</span>{labelOf(id)}
                </button>
                <span className="flex">
                  <IconButton label={t('scholar.thread.moveUp', { label: labelOf(id) })} disabled={index === 0} onClick={() => moveThread(index, -1)}>
                    <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                  </IconButton>
                  <IconButton label={t('scholar.thread.moveDown', { label: labelOf(id) })} disabled={index === state.evidenceThread.length - 1} onClick={() => moveThread(index, 1)}>
                    <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                  </IconButton>
                  <IconButton label={t('scholar.thread.remove', { label: labelOf(id) })} onClick={() => onToggleThread(id)}>
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                  </IconButton>
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-3 font-reader text-base leading-6 text-stone-600">{t('scholar.thread.empty')}</p>
        )}
      </section>
    </div>
  );
}

function IconButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className={`flex h-11 w-11 items-center justify-center text-stone-500 hover:text-orange-800 disabled:opacity-25 ${focusRing}`}
    >
      {children}
    </button>
  );
}

export default memo(ScholarInspectorComponent);
