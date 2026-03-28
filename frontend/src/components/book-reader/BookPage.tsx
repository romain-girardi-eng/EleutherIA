import { BookHeader } from './BookHeader';
import { KGPassageLink } from './KGPassageLink';
import type { BookPage as BookPageData } from './types';

interface BookPageProps {
  page: BookPageData;
  headerLeft: string;
  headerRight: string;
  isGreek?: boolean;
  langLabel?: string;
  fontSize: number;
  side?: 'left' | 'right' | 'single';
}

export function BookPage({
  page,
  headerLeft,
  headerRight,
  isGreek = false,
  langLabel,
  fontSize,
  side = 'single',
}: BookPageProps) {
  const sideClasses =
    side === 'left'
      ? 'pr-8 border-r border-stone-900/[0.04]'
      : side === 'right'
        ? 'pl-8'
        : '';

  return (
    <div className={`flex-1 p-10 min-h-[560px] flex flex-col text-stone-800 ${sideClasses}`}>
      <BookHeader leftText={headerLeft} rightText={headerRight} />

      {langLabel && (
        <div className="font-sans text-[9px] tracking-[1.5px] uppercase text-stone-400 mb-5">
          {langLabel}
        </div>
      )}

      <div className="flex-1">
        {page.passages.map((passage) => (
          <div key={passage.passageId} className="group relative flex gap-4 mb-6">
            <div className="font-garamond text-[11px] text-stone-400 min-w-[28px] text-right pt-[3px] shrink-0">
              {passage.canonicalRef}
            </div>
            <div
              className={`font-garamond leading-[1.75] text-stone-700 flex-1 ${isGreek ? 'italic text-stone-800' : ''}`}
              style={{ fontSize: `${fontSize}px` }}
            >
              {passage.text}
            </div>
            <KGPassageLink passageId={passage.passageId} nodeCount={passage.kgNodeCount} />
          </div>
        ))}
      </div>

      <div className="mt-auto text-center font-garamond text-xs text-stone-400 pt-5 tracking-[1px]">
        {page.pageNumber}
      </div>
    </div>
  );
}
