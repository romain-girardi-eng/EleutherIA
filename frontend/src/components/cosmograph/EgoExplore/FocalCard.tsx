import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BookOpen } from 'lucide-react';

import type { AtlasNodeMeta } from '../AtlasHelpers';
import type { KGNode } from '../../../types';
import NodeTypeIcon from './NodeTypeIcon';

interface FocalCardProps {
  readonly meta: AtlasNodeMeta;
  readonly raw: KGNode | null;
}

function clamp2Lines(text: string, max = 240): { short: string; needsClamp: boolean } {
  const trimmed = text.replace(/\s+/g, ' ').trim();
  if (trimmed.length <= max) {
    return { short: trimmed, needsClamp: false };
  }
  const cut = trimmed.slice(0, max);
  const lastSpace = cut.lastIndexOf(' ');
  return {
    short: `${(lastSpace > 80 ? cut.slice(0, lastSpace) : cut).trim()}…`,
    needsClamp: true,
  };
}

export default function FocalCard({ meta, raw }: FocalCardProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const description = (raw?.description ?? meta.description ?? '').trim();
  const { short, needsClamp } = clamp2Lines(description);

  const metaLine = [
    meta.typeLabel,
    meta.periodLabel !== 'Unspecified' ? meta.periodLabel : null,
    meta.schoolLabel !== 'Unattached' ? meta.schoolLabel : null,
    raw?.dates ?? null,
  ]
    .filter(Boolean)
    .join(' · ');

  const rawAny = raw as unknown as Record<string, unknown> | null;
  const passageCount = typeof rawAny?.passage_count === 'number' ? rawAny.passage_count : null;
  const canonicalId = typeof rawAny?.work_canonical_id === 'string' ? rawAny.work_canonical_id : null;

  return (
    <article
      aria-live="polite"
      className="relative overflow-hidden rounded-3xl border border-amber-200/50 bg-white/70 px-5 py-5 shadow-[0_18px_44px_-24px_rgba(124,77,15,0.35)] backdrop-blur-sm"
    >
      <div className="flex items-start gap-4">
        <NodeTypeIcon typeKey={meta.typeKey} layer={meta.layer} />
        <div className="min-w-0 flex-1">
          <h2 className="font-display text-xl leading-tight text-stone-900 sm:text-2xl">
            {meta.label}
          </h2>
          {metaLine && (
            <p className="mt-1 text-[11px] font-medium uppercase tracking-[0.16em] text-amber-700/85">
              {metaLine}
            </p>
          )}
          {(meta.greekTerm || meta.latinTerm) && (
            <p className="mt-1 text-sm italic text-stone-700">
              {[meta.greekTerm, meta.latinTerm].filter(Boolean).join(' · ')}
            </p>
          )}
        </div>
      </div>

      {description && (
        <div className="mt-4 text-[14px] leading-6 text-stone-700">
          <p>{expanded ? description : short}</p>
          {needsClamp && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="mt-1.5 inline-flex items-center text-[12px] font-medium text-amber-800 underline decoration-amber-300/60 underline-offset-2 transition-colors hover:text-amber-900"
            >
              {expanded
                ? t('cosmograph.explore.readLess', 'Read less')
                : t('cosmograph.explore.readMore', 'Read more')}
            </button>
          )}
        </div>
      )}

      {passageCount && passageCount > 0 && canonicalId && (
        <Link
          to={`/texts/${canonicalId}`}
          className="mt-4 inline-flex items-center gap-2 rounded-full border border-amber-300/60 bg-amber-50 px-3 py-1.5 text-[12px] font-medium text-amber-900 transition-colors hover:bg-amber-100"
        >
          <BookOpen className="h-3.5 w-3.5" aria-hidden />
          {t('cosmograph.explore.passagesIndexed', '{{count}} passages indexed', {
            count: passageCount,
          })}
        </Link>
      )}
    </article>
  );
}
