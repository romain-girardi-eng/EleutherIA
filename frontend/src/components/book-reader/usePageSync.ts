import { useMemo } from 'react';
import type { BookPage, BookSpreadData } from './types';

interface PageSyncInput {
  originalPages: BookPage[];
  translationPages: BookPage[];
}

export function usePageSync({
  originalPages,
  translationPages,
}: PageSyncInput): BookSpreadData[] {
  return useMemo(() => {
    if (originalPages.length === 0) return [];
    if (translationPages.length === 0) {
      return originalPages.map((page) => ({
        left: page,
        right: { pageNumber: page.pageNumber, passages: [] },
      }));
    }

    const spreads: BookSpreadData[] = [];
    let origIdx = 0;
    let transIdx = 0;
    let spreadNumber = 0;

    while (origIdx < originalPages.length || transIdx < translationPages.length) {
      spreadNumber++;
      const leftPageNum = spreadNumber * 2;
      const rightPageNum = leftPageNum + 1;

      const left: BookPage = origIdx < originalPages.length
        ? { ...originalPages[origIdx], pageNumber: leftPageNum }
        : { pageNumber: leftPageNum, passages: [] };

      const right: BookPage = transIdx < translationPages.length
        ? { ...translationPages[transIdx], pageNumber: rightPageNum }
        : { pageNumber: rightPageNum, passages: [] };

      spreads.push({ left, right });
      origIdx++;
      transIdx++;
    }

    return spreads;
  }, [originalPages, translationPages]);
}
