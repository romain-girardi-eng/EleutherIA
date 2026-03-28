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
      ? 'pr-[5%] border-r border-stone-900/[0.04]'
      : side === 'right'
        ? 'pl-[5%]'
        : '';

  // Responsive padding: smaller on narrow pages
  const paddingClass = side === 'single'
    ? 'px-[8%] py-[5%]'
    : 'px-[6%] py-[5%]';

  return (
    <div
      className={`flex-1 ${paddingClass} flex flex-col text-stone-800 overflow-hidden ${sideClasses}`}
    >
      <BookHeader leftText={headerLeft} rightText={headerRight} />

      {langLabel && (
        <div className="font-sans text-[9px] tracking-[1.5px] uppercase text-stone-400 mb-4">
          {langLabel}
        </div>
      )}

      <div className="flex-1">
        {page.passages.map((passage) => (
          <div key={passage.passageId} className="group relative flex gap-3 mb-5">
            <div
              className="font-garamond text-stone-400 text-right shrink-0"
              style={{ fontSize: `${Math.max(10, fontSize * 0.6)}px`, minWidth: `${Math.max(20, fontSize * 1.5)}px`, paddingTop: '2px' }}
            >
              {passage.canonicalRef}
            </div>
            <div
              className={`font-garamond text-stone-700 flex-1 ${isGreek ? 'italic text-stone-800' : ''}`}
              style={{ fontSize: `${fontSize}px`, lineHeight: 1.75 }}
            >
              {passage.text}
            </div>
            <KGPassageLink passageId={passage.passageId} nodeCount={passage.kgNodeCount} />
          </div>
        ))}
      </div>

      <div
        className="mt-auto text-center font-garamond text-stone-400 pt-4 tracking-[1px]"
        style={{ fontSize: `${Math.max(10, fontSize * 0.65)}px` }}
      >
        {page.pageNumber}
      </div>
    </div>
  );
}
