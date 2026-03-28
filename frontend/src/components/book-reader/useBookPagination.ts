import { useMemo } from 'react';
import { prepare, layout } from '@chenglou/pretext';
import type { BookPage, PageConfig, PagePassage } from './types';

interface PaginationInput {
  passages: {
    passage_id: string;
    canonical_ref: string;
    text_content: string;
    kg_node_count?: number;
  }[];
  config: PageConfig;
  correctionRatio: number;
}

interface PaginationResult {
  pages: BookPage[];
  totalPages: number;
}

export function useBookPagination({
  passages,
  config,
  correctionRatio,
}: PaginationInput): PaginationResult {
  return useMemo(() => {
    if (passages.length === 0 || config.height <= 0 || config.width <= 0) {
      return { pages: [], totalPages: 0 };
    }

    const fontString = `${config.fontSize}px ${config.fontFamily}`;
    const lineHeightPx = config.fontSize * config.lineHeight;
    const pageHeight = config.height;
    const passageGap = lineHeightPx * 1.5;

    // Measure all passages using Pretext
    const measured = passages.map((p) => {
      const prepared = prepare(p.text_content, fontString);
      const result = layout(prepared, config.width, lineHeightPx);
      return {
        ...p,
        measuredHeight: result.height * correctionRatio,
      };
    });

    // Distribute passages across pages
    const pages: BookPage[] = [];
    let currentPage: PagePassage[] = [];
    let currentHeight = 0;
    let pageNumber = 1;

    for (const passage of measured) {
      const gap = currentPage.length > 0 ? passageGap : 0;
      const neededHeight = passage.measuredHeight + gap;

      if (currentHeight + neededHeight <= pageHeight || currentPage.length === 0) {
        currentPage.push({
          passageId: passage.passage_id,
          canonicalRef: passage.canonical_ref,
          text: passage.text_content,
          kgNodeCount: passage.kg_node_count ?? 0,
        });
        currentHeight += neededHeight;
      } else {
        pages.push({ pageNumber, passages: currentPage });
        pageNumber++;
        currentPage = [
          {
            passageId: passage.passage_id,
            canonicalRef: passage.canonical_ref,
            text: passage.text_content,
            kgNodeCount: passage.kg_node_count ?? 0,
          },
        ];
        currentHeight = passage.measuredHeight;
      }
    }

    if (currentPage.length > 0) {
      pages.push({ pageNumber, passages: currentPage });
    }

    return { pages, totalPages: pages.length };
  }, [passages, config, correctionRatio]);
}
