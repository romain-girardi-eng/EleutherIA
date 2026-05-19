import { ChevronRight, MoreHorizontal } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import type { AtlasNodeMeta } from '../AtlasHelpers';

interface BreadcrumbProps {
  readonly trail: ReadonlyArray<string>;
  readonly metaById: Map<string, AtlasNodeMeta>;
  readonly onPick: (id: string, indexInTrail: number) => void;
}

const SHOW_LAST = 5;

export default function Breadcrumb({ trail, metaById, onPick }: BreadcrumbProps) {
  const { t } = useTranslation();
  if (trail.length === 0) return null;

  const overflow = trail.length > SHOW_LAST;
  const visible = overflow ? trail.slice(trail.length - SHOW_LAST) : trail;
  const offset = trail.length - visible.length;

  return (
    <nav
      aria-label={t('cosmograph.explore.breadcrumb', 'Exploration trail')}
      className="-mx-3 flex snap-x snap-mandatory items-center gap-1 overflow-x-auto px-3 pb-1 pt-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      {overflow && (
        <span className="inline-flex shrink-0 items-center justify-center rounded-full border border-amber-200/60 bg-amber-50/70 px-2 py-1 text-amber-800">
          <MoreHorizontal className="h-3 w-3" aria-hidden />
          <span className="sr-only">
            {t('cosmograph.explore.breadcrumbHidden', '{{count}} earlier steps hidden', {
              count: trail.length - visible.length,
            })}
          </span>
        </span>
      )}

      {visible.map((id, i) => {
        const trailIndex = i + offset;
        const isLast = trailIndex === trail.length - 1;
        const label = metaById.get(id)?.label ?? id;
        return (
          <span key={`${id}-${trailIndex}`} className="flex shrink-0 snap-start items-center gap-1">
            {i > 0 && (
              <ChevronRight aria-hidden className="h-3.5 w-3.5 shrink-0 text-amber-700/60" />
            )}
            <button
              type="button"
              onClick={() => onPick(id, trailIndex)}
              aria-current={isLast ? 'page' : undefined}
              className={[
                'max-w-[11rem] truncate rounded-full border px-2.5 py-1 text-[12px] transition-colors',
                isLast
                  ? 'border-amber-400/70 bg-amber-200/60 font-semibold text-amber-950'
                  : 'border-amber-200/60 bg-white/70 text-amber-900 hover:border-amber-300/80 hover:bg-amber-50',
              ].join(' ')}
            >
              {label}
            </button>
          </span>
        );
      })}
    </nav>
  );
}
