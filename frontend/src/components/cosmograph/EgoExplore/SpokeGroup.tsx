import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import type { AtlasNodeMeta } from '../AtlasHelpers';
import NodeTypeIcon from './NodeTypeIcon';
import type { RelationGroup } from './relationGrouping';
import { relationDisplayLabel } from './relationGrouping';

interface SpokeGroupProps {
  readonly group: RelationGroup;
  readonly metaById: Map<string, AtlasNodeMeta>;
  readonly onPick: (id: string) => void;
}

const COLLAPSED_LIMIT = 12;
const DENSITY_CAP = 24;

export default function SpokeGroup({ group, metaById, onPick }: SpokeGroupProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);

  const total = group.neighbors.length;
  const needsCollapse = total > DENSITY_CAP;
  const visible = expanded || !needsCollapse
    ? group.neighbors
    : group.neighbors.slice(0, COLLAPSED_LIMIT);
  const hiddenCount = total - visible.length;

  return (
    <section className="relative">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">
          {relationDisplayLabel(group.relation, group.direction)}
        </h3>
        <span className="rounded-full bg-amber-100/70 px-2 py-0.5 text-[10px] font-medium text-amber-900">
          {total}
        </span>
      </div>

      <div className="-mx-1 flex snap-x snap-mandatory gap-2 overflow-x-auto pb-1 pl-1 pr-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {visible.map((n) => {
          const meta = metaById.get(n.id);
          const typeKey = meta?.typeKey ?? 'unknown';
          const layer = meta?.layer ?? 'ancient';
          return (
            <button
              key={`${group.key}:${n.id}`}
              type="button"
              onClick={() => onPick(n.id)}
              className="group flex max-w-[14rem] shrink-0 snap-start items-center gap-2 rounded-2xl border border-amber-200/55 bg-white/70 px-3 py-2 text-left shadow-[0_4px_14px_-10px_rgba(124,77,15,0.4)] transition-all hover:border-amber-300/80 hover:bg-amber-50/80 hover:shadow-[0_8px_24px_-14px_rgba(124,77,15,0.5)] focus:outline-none focus-visible:border-amber-400 focus-visible:ring-2 focus-visible:ring-amber-300/40"
            >
              <NodeTypeIcon typeKey={typeKey} layer={layer} size="sm" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[13px] font-medium leading-tight text-stone-800 group-hover:text-stone-900">
                  {n.label}
                </span>
                {meta && (
                  <span className="mt-0.5 block truncate text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    {meta.typeLabel}
                    {meta.periodLabel !== 'Unspecified' ? ` · ${meta.periodLabel}` : ''}
                  </span>
                )}
              </span>
            </button>
          );
        })}

        {needsCollapse && !expanded && hiddenCount > 0 && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="inline-flex shrink-0 snap-start items-center gap-1.5 rounded-2xl border border-dashed border-amber-300/70 bg-amber-50/60 px-3 py-2 text-[12px] font-medium text-amber-900 transition-colors hover:border-amber-400 hover:bg-amber-100/70"
          >
            <ChevronDown className="h-3.5 w-3.5" aria-hidden />
            {t('cosmograph.explore.moreSpokes', '+ {{count}} more', { count: hiddenCount })}
          </button>
        )}
      </div>
    </section>
  );
}
