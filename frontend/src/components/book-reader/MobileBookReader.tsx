import { useState } from 'react';
import { BookPage } from './BookPage';
import { useSwipeNavigation } from '../../hooks/useSwipeNavigation';
import type { BookPage as BookPageData } from './types';

interface MobileBookReaderProps {
  originalPages: BookPageData[];
  translationPages: BookPageData[];
  currentPage: number;
  onPageChange: (page: number) => void;
  title: string;
  author: string;
  originalLanguage: string;
  fontSize: number;
  hasBilingual: boolean;
}

export function MobileBookReader({
  originalPages,
  translationPages,
  currentPage,
  onPageChange,
  title,
  author,
  originalLanguage,
  fontSize,
  hasBilingual,
}: MobileBookReaderProps) {
  const [activeTab, setActiveTab] = useState<'original' | 'translation'>('original');
  const pages = activeTab === 'original' ? originalPages : translationPages;
  const page = pages[currentPage - 1];
  const isGreek = originalLanguage === 'grc' && activeTab === 'original';

  const swipeHandlers = useSwipeNavigation({
    onSwipeLeft: () => {
      if (currentPage < pages.length) onPageChange(currentPage + 1);
    },
    onSwipeRight: () => {
      if (currentPage > 1) onPageChange(currentPage - 1);
    },
  });

  if (!page) return null;

  return (
    <div {...swipeHandlers} className="w-full h-full flex flex-col">
      {hasBilingual && translationPages.length > 0 && (
        <div className="flex justify-center gap-1 mb-4">
          <button
            onClick={() => setActiveTab('original')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'original'
                ? 'bg-amber-600/15 text-amber-700'
                : 'text-stone-400 hover:text-stone-600'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setActiveTab('translation')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'translation'
                ? 'bg-amber-600/15 text-amber-700'
                : 'text-stone-400 hover:text-stone-600'
            }`}
          >
            Traduction
          </button>
        </div>
      )}

      <div className="flex-1 min-h-0 bg-white/70 rounded-lg shadow-sm border border-amber-200/30 overflow-hidden">
        <BookPage
          page={page}
          headerLeft={title}
          headerRight={author}
          isGreek={isGreek}
          fontSize={fontSize}
          side="single"
        />
      </div>
    </div>
  );
}
