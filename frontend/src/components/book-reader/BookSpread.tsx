import { BookPage } from './BookPage';
import type { BookSpreadData } from './types';

interface BookSpreadProps {
  spread: BookSpreadData;
  title: string;
  author: string;
  originalLanguage: string;
  translationLanguage: string;
  fontSize: number;
  pageHeight?: number;
}

const LANG_LABELS: Record<string, string> = {
  grc: 'Grec ancien',
  lat: 'Latin',
  en: 'English',
  fr: 'Français',
};

export function BookSpread({
  spread,
  title,
  author,
  originalLanguage,
  translationLanguage,
  fontSize,
  pageHeight,
}: BookSpreadProps) {
  const isGreek = originalLanguage === 'grc';

  return (
    <div className="flex bg-white/70 rounded-lg shadow-sm border border-amber-200/30 overflow-hidden relative">
      <div className="absolute left-1/2 top-0 bottom-0 w-6 -translate-x-1/2 bg-gradient-to-r from-transparent via-black/[0.04] to-transparent pointer-events-none z-10" />

      <BookPage
        page={spread.left}
        headerLeft={title}
        headerRight={author}
        isGreek={isGreek}
        langLabel={LANG_LABELS[originalLanguage] ?? originalLanguage}
        fontSize={fontSize}
        side="left"
        pageHeight={pageHeight}
      />
      <BookPage
        page={spread.right}
        headerLeft={LANG_LABELS[translationLanguage] ?? translationLanguage}
        headerRight={`Livre ${spread.left.passages[0]?.canonicalRef.split('.')[0] ?? ''}`}
        isGreek={false}
        langLabel={LANG_LABELS[translationLanguage] ?? translationLanguage}
        fontSize={fontSize}
        side="right"
        pageHeight={pageHeight}
      />
    </div>
  );
}
