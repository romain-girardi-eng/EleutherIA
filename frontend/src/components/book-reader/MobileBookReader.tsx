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
    <div {...swipeHandlers} className="w-full">
      {hasBilingual && translationPages.length > 0 && (
        <div className="flex justify-center gap-1 mb-4">
          <button
            onClick={() => setActiveTab('original')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'original'
                ? 'bg-amber-600/20 text-amber-500'
                : 'text-white/40 hover:text-white/60'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setActiveTab('translation')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'translation'
                ? 'bg-amber-600/20 text-amber-500'
                : 'text-white/40 hover:text-white/60'
            }`}
          >
            Traduction
          </button>
        </div>
      )}

      <div className="max-w-[560px] mx-auto">
        <div className="bg-[#fdfbf7] rounded-sm shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.25)]">
          <BookPage
            page={page}
            headerLeft={title}
            headerRight={author}
            isGreek={isGreek}
            fontSize={Math.min(fontSize, 15)}
            side="single"
          />
        </div>
      </div>
    </div>
  );
}
