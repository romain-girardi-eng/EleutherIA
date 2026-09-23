import { ArrowLeft, ArrowRight, ChevronDown, Search } from 'lucide-react';
import { memo, useDeferredValue, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  groupRelations,
  humanize,
  typeColor,
  type RelatedNode,
  type RelationGroup,
} from './nodeDetailModel';

const GROUP_PREVIEW = 5;
const GROUP_STEP = 25;
const OPEN_GROUPS = 3;
const FILTER_THRESHOLD = 12;

interface RelationsSectionProps {
  relationships: ReadonlyArray<RelatedNode>;
  onNavigate?: (nodeId: string) => void;
}

export const RelationsSection = memo(function RelationsSection({
  relationships,
  onNavigate,
}: RelationsSectionProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const filterId = useId();

  const groups = useMemo(() => groupRelations(relationships), [relationships]);
  const visibleGroups = useMemo(() => {
    const needle = deferredQuery.trim().toLocaleLowerCase();
    if (!needle) return groups;
    return groups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => item.label.toLocaleLowerCase().includes(needle)),
      }))
      .filter((group) => group.items.length > 0);
  }, [groups, deferredQuery]);

  return (
    <div>
      {relationships.length > FILTER_THRESHOLD && (
        <div className="relative mb-3">
          <label htmlFor={filterId} className="sr-only">
            {t('kg.nodeDetail.filterRelations', 'Filter relations')}
          </label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" aria-hidden="true" />
          <input
            id={filterId}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t('kg.nodeDetail.filterRelationsPlaceholder', 'Filter by name…')}
            className="min-h-11 w-full border border-stone-300 bg-[#fffdf9] py-2 pl-9 pr-3 font-body text-sm text-stone-800 placeholder:text-stone-400 focus:border-orange-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-700/40"
          />
        </div>
      )}
      {visibleGroups.length === 0 ? (
        <p className="py-3 font-body text-sm text-stone-500">
          {t('kg.nodeDetail.noRelationMatch', 'No related record matches this filter.')}
        </p>
      ) : (
        <ul className="divide-y divide-stone-200 border-y border-stone-200">
          {visibleGroups.map((group, index) => (
            <RelationGroupBlock
              key={group.key}
              group={group}
              defaultOpen={index < OPEN_GROUPS || deferredQuery.trim().length > 0}
              onNavigate={onNavigate}
            />
          ))}
        </ul>
      )}
    </div>
  );
});

function RelationGroupBlock({
  group,
  defaultOpen,
  onNavigate,
}: {
  group: RelationGroup;
  defaultOpen: boolean;
  onNavigate?: (nodeId: string) => void;
}) {
  const { t } = useTranslation();
  const [openOverride, setOpenOverride] = useState<boolean | null>(null);
  const [limit, setLimit] = useState(GROUP_PREVIEW);
  const listId = useId();
  const isOpen = openOverride ?? defaultOpen;
  const incoming = group.direction === 'incoming';
  const label = incoming
    ? t(`kg.nodeDetail.relationInverse.${group.relation}`, {
        defaultValue: t('kg.nodeDetail.relationInverseFallback', {
          defaultValue: '{{relation}} (inverse)',
          relation: humanize(group.relation),
        }),
      })
    : t(`kg.nodeDetail.relation.${group.relation}`, { defaultValue: humanize(group.relation) });
  const shown = group.items.slice(0, limit);
  const remaining = group.items.length - shown.length;
  const step = limit === GROUP_PREVIEW ? GROUP_STEP - GROUP_PREVIEW : GROUP_STEP;
  const DirectionIcon = incoming ? ArrowLeft : ArrowRight;

  return (
    <li>
      <button
        type="button"
        aria-expanded={isOpen}
        aria-controls={listId}
        onClick={() => setOpenOverride(!isOpen)}
        className="group flex min-h-11 w-full items-center gap-2 py-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700"
      >
        <DirectionIcon className="h-3.5 w-3.5 shrink-0 text-orange-700" aria-hidden="true" />
        <span className="min-w-0 flex-1 font-body text-[11px] font-semibold uppercase tracking-[0.12em] text-orange-900 group-hover:text-orange-700">
          {label}
        </span>
        <span className="font-body text-xs tabular-nums text-stone-500">{group.items.length}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-stone-400 transition-transform duration-200 motion-reduce:transition-none ${isOpen ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>
      {isOpen && (
        <div id={listId} className="pb-2">
          <ul>
            {shown.map((rel) => (
              <li key={rel.id}>
                <button
                  type="button"
                  disabled={!onNavigate}
                  onClick={() => onNavigate?.(rel.id)}
                  className="group/item flex min-h-11 w-full items-center gap-3 py-1.5 pl-5 pr-1 text-left transition-colors hover:bg-orange-50/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700 disabled:cursor-default disabled:hover:bg-transparent"
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: typeColor(rel.type) }}
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block font-reader text-[0.97rem] leading-snug text-stone-900 group-hover/item:text-orange-900">
                      {rel.label}
                    </span>
                    <span className="block font-body text-[11px] text-stone-500">
                      {t(`kg.nodeDetail.types.${rel.type}`, { defaultValue: humanize(rel.type) })}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {remaining > 0 && (
            <button
              type="button"
              onClick={() => setLimit((current) => current + step)}
              className="ml-5 mt-1 inline-flex min-h-11 items-center font-body text-sm font-semibold text-teal-800 underline decoration-teal-700/30 underline-offset-4 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
            >
              {t('kg.nodeDetail.showMore', {
                defaultValue: 'Show {{count}} more',
                count: Math.min(remaining, step),
              })}
              <span className="ml-2 inline-block font-normal text-stone-500 no-underline">
                {t('kg.nodeDetail.shownOfTotal', {
                  defaultValue: '{{shown}} of {{total}} shown',
                  shown: shown.length,
                  total: group.items.length,
                })}
              </span>
            </button>
          )}
        </div>
      )}
    </li>
  );
}
