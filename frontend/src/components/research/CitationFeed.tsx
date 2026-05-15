import { useTranslation } from 'react-i18next';
import { AnimatePresence } from 'framer-motion';
import { ScrollText } from 'lucide-react';
import type { CitationEntry } from '../../hooks/useResearchStream';
import { CitationCard } from './CitationCard';

interface Props {
  citations: CitationEntry[];
  /** When true, a small "live" badge appears next to the header count. */
  isLive: boolean;
  /** Called when the user clicks a citation card to open PassageViewer. */
  onOpenPassage?: (passageId: string) => void;
}

export function CitationFeed({ citations, isLive, onOpenPassage }: Props) {
  const { t } = useTranslation();

  return (
    <section
      aria-labelledby="research-citations-header"
      className="flex h-full flex-col"
    >
      <header className="flex shrink-0 items-center justify-between border-b border-stone-200/50 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <ScrollText className="h-4 w-4 text-amber-700" aria-hidden="true" />
          <h2
            id="research-citations-header"
            className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500"
          >
            {t('research.citations.title')}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-stone-100/80 px-2 py-0.5 text-[10px] font-medium text-stone-500">
            {citations.length}
          </span>
          {isLive && (
            <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
              {t('research.live')}
            </span>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        {citations.length === 0 ? (
          <p className="px-1 py-6 text-center text-[12px] italic text-stone-400">
            {t('research.citations.empty')}
          </p>
        ) : (
          <div className="space-y-2.5">
            <AnimatePresence initial={false}>
              {citations.map((c, idx) => (
                <CitationCard
                  key={c.passage_id}
                  citation={c}
                  index={idx}
                  onOpenPassage={onOpenPassage}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </section>
  );
}

export default CitationFeed;
