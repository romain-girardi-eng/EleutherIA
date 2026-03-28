'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { cachedApiClient } from '../../api/cachedClient';
import { useLazyPassages } from '../../hooks/useLazyPassages';
import { useCalibration } from './useCalibration';
import { useBookPagination } from './useBookPagination';
import { usePageSync } from './usePageSync';
import { BookSpread } from './BookSpread';
import { BookControls } from './BookControls';
import { BookProgress } from './BookProgress';
import { MobileBookReader } from './MobileBookReader';
import {
  FONT_SIZE_MAP,
  MOBILE_BREAKPOINT,
  type FontSizePreset,
  type PageConfig,
} from './types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Work {
  work_id: string;
  canonical_id: string;
  title: string;
  author: string;
  language?: string;
  period?: string;
  metadata?: Record<string, unknown>;
}

// Passage shape coming from useLazyPassages
interface Passage {
  passage_id: string;
  canonical_ref: string;
  text_content: string;
  translation_text?: string | null;
  translation_language?: string | null;
  kg_node_count?: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FONT_PRESETS: FontSizePreset[] = ['small', 'normal', 'large'];
const LS_FONT_KEY = 'book-reader-font-size';
const DEFAULT_LINE_HEIGHT = 1.75;
const DEFAULT_FONT_FAMILY = 'EB Garamond, serif';
const RESIZE_DEBOUNCE_MS = 150;

// Page dimensions (px) — matches BookPage internal layout
const PAGE_PADDING = 80; // p-10 = 40px each side
const HEADER_HEIGHT = 60;
const FOOTER_HEIGHT = 40;
const MARGIN_REF_WIDTH = 44; // ~28px min-w + 16px gap

function readFontSize(): FontSizePreset {
  if (typeof window === 'undefined') return 'normal';
  const stored = localStorage.getItem(LS_FONT_KEY);
  if (stored && (stored === 'small' || stored === 'normal' || stored === 'large')) {
    return stored as FontSizePreset;
  }
  return 'normal';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BookReaderPage() {
  const { textId } = useParams<{ textId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // ---- State ----
  const [work, setWork] = useState<Work | null>(null);
  const [workLoading, setWorkLoading] = useState(true);
  const [fontSizePreset, setFontSizePreset] = useState<FontSizePreset>(readFontSize);
  const [isBilingual, setIsBilingual] = useState(true);
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1200,
  );
  const [containerWidth, setContainerWidth] = useState(920);
  const containerRef = useRef<HTMLDivElement>(null);

  const isMobile = windowWidth < MOBILE_BREAKPOINT;
  const fontSize = FONT_SIZE_MAP[fontSizePreset];

  // Deep-link page from ?page=N
  const initialPage = Number(searchParams.get('page')) || 1;
  const [currentPage, setCurrentPage] = useState(initialPage);

  // ---- Load work metadata ----
  useEffect(() => {
    if (!textId) return;
    let cancelled = false;

    const load = async () => {
      setWorkLoading(true);
      try {
        const data = (await cachedApiClient.getWork(textId)) as Work;
        if (!cancelled) setWork(data);
      } catch (err) {
        console.error('Failed to load work:', err);
      } finally {
        if (!cancelled) setWorkLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [textId]);

  // ---- Load ALL passages (paginated view needs them upfront) ----
  const {
    passages: rawPassages,
    loading: passagesLoading,
    hasMore,
    loadMore,
  } = useLazyPassages(textId, {
    initialLimit: 200,
    batchSize: 200,
    autoLoad: false,
  });

  // Eagerly load remaining batches
  useEffect(() => {
    if (hasMore && !passagesLoading) {
      loadMore();
    }
  }, [hasMore, passagesLoading, loadMore]);

  const passages = rawPassages as Passage[];

  // ---- Separate original / translation passages ----
  const hasBilingualContent = useMemo(
    () => passages.some((p) => p.translation_text),
    [passages],
  );

  const originalPassages = useMemo(
    () =>
      passages.map((p) => ({
        passage_id: p.passage_id,
        canonical_ref: p.canonical_ref,
        text_content: p.text_content,
        kg_node_count: p.kg_node_count,
      })),
    [passages],
  );

  const translationPassages = useMemo(
    () =>
      passages
        .filter((p) => p.translation_text)
        .map((p) => ({
          passage_id: `${p.passage_id}-trans`,
          canonical_ref: p.canonical_ref,
          text_content: p.translation_text!,
          kg_node_count: 0,
        })),
    [passages],
  );

  const translationLanguage = useMemo(() => {
    const first = passages.find((p) => p.translation_language);
    return first?.translation_language ?? 'en';
  }, [passages]);

  // ---- Page config (depends on container size and font) ----
  const pageConfig: PageConfig = useMemo(() => {
    const singlePageWidth = isMobile
      ? containerWidth - PAGE_PADDING
      : (containerWidth - PAGE_PADDING * 2) / 2; // two pages side by side
    const textWidth = singlePageWidth - MARGIN_REF_WIDTH;
    const textHeight = 560 - HEADER_HEIGHT - FOOTER_HEIGHT; // min-h-[560px] from BookPage

    return {
      width: Math.max(textWidth, 100),
      height: Math.max(textHeight, 200),
      marginRef: MARGIN_REF_WIDTH,
      fontSize,
      lineHeight: DEFAULT_LINE_HEIGHT,
      fontFamily: DEFAULT_FONT_FAMILY,
    };
  }, [containerWidth, fontSize, isMobile]);

  // ---- Calibration ----
  const { correctionRatio, calibrated, calibrate, hiddenRef } =
    useCalibration(pageConfig);

  // Trigger calibration once first passage is available
  useEffect(() => {
    if (passages.length > 0 && !calibrated) {
      calibrate(passages[0].text_content);
    }
  }, [passages, calibrated, calibrate]);

  // ---- Pagination ----
  const { pages: originalPages, totalPages: originalTotalPages } =
    useBookPagination({
      passages: originalPassages,
      config: pageConfig,
      correctionRatio: calibrated ? correctionRatio : 1,
    });

  const { pages: translationPagesList } = useBookPagination({
    passages: translationPassages,
    config: pageConfig,
    correctionRatio: calibrated ? correctionRatio : 1,
  });

  // ---- Page sync (bilingual spreads) ----
  const spreads = usePageSync({
    originalPages,
    translationPages: isBilingual ? translationPagesList : [],
  });

  const totalPages = isBilingual
    ? spreads.length * 2
    : originalTotalPages;

  // ---- Navigation helpers ----
  const clampPage = useCallback(
    (p: number) => Math.max(1, Math.min(p, totalPages || 1)),
    [totalPages],
  );

  const goToPage = useCallback(
    (page: number) => {
      const clamped = clampPage(page);
      setCurrentPage(clamped);
      setSearchParams({ page: String(clamped) }, { replace: true });
    },
    [clampPage, setSearchParams],
  );

  const goNext = useCallback(() => {
    goToPage(currentPage + (isBilingual ? 2 : 1));
  }, [currentPage, isBilingual, goToPage]);

  const goPrev = useCallback(() => {
    goToPage(currentPage - (isBilingual ? 2 : 1));
  }, [currentPage, isBilingual, goToPage]);

  // ---- Font size cycling ----
  const cycleFontSize = useCallback(() => {
    setFontSizePreset((prev) => {
      const idx = FONT_PRESETS.indexOf(prev);
      const next = FONT_PRESETS[(idx + 1) % FONT_PRESETS.length];
      localStorage.setItem(LS_FONT_KEY, next);
      return next;
    });
  }, []);

  // ---- Keyboard shortcuts ----
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault();
          goNext();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          goPrev();
          break;
        case 'Home':
          e.preventDefault();
          goToPage(1);
          break;
        case 'End':
          e.preventDefault();
          goToPage(totalPages);
          break;
        case 't':
          if (hasBilingualContent) setIsBilingual((b) => !b);
          break;
        case 'v':
        case 'Escape':
          // Navigate back to scroll reader
          if (textId) navigate(`/texts/${textId}`);
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goNext, goPrev, goToPage, totalPages, hasBilingualContent, textId, navigate]);

  // ---- Debounced resize ----
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setWindowWidth(window.innerWidth);
        if (containerRef.current) {
          setContainerWidth(containerRef.current.offsetWidth);
        }
      }, RESIZE_DEBOUNCE_MS);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Measure container on mount and when ref changes
  useEffect(() => {
    if (containerRef.current) {
      setContainerWidth(containerRef.current.offsetWidth);
    }
  }, [isMobile]);

  // ---- Current spread (for desktop) ----
  const currentSpreadIndex = Math.max(
    0,
    Math.floor((currentPage - 1) / 2),
  );
  const currentSpread = spreads[currentSpreadIndex] ?? null;

  // Current ref for progress bar
  const currentRef = useMemo(() => {
    if (isBilingual && currentSpread) {
      return currentSpread.left.passages[0]?.canonicalRef;
    }
    const page = originalPages[currentPage - 1];
    return page?.passages[0]?.canonicalRef;
  }, [isBilingual, currentSpread, originalPages, currentPage]);

  // ---- Loading state ----
  if (workLoading || passagesLoading || !work) {
    return (
      <div className="min-h-screen bg-[#1a1a1e] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-600/30 border-t-amber-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/40 text-sm font-garamond">
            Chargement de l&apos;ouvrage…
          </p>
        </div>
      </div>
    );
  }

  // ---- Render ----
  return (
    <div className="min-h-screen bg-[#1a1a1e] text-white/80 flex flex-col items-center py-8 px-4">
      {/* Hidden calibration div */}
      <div ref={hiddenRef} aria-hidden="true" />

      {/* Title */}
      <div className="text-center mb-8">
        <h1 className="font-garamond text-xl text-white/90 tracking-wide">
          {work.title}
        </h1>
        <p className="text-sm text-white/40 mt-1">{work.author}</p>
      </div>

      {/* Progress bar */}
      <BookProgress
        currentPage={currentPage}
        totalPages={totalPages}
        currentRef={currentRef}
      />

      {/* Book content */}
      <div ref={containerRef} className="w-full max-w-[920px] mx-auto mb-8">
        {isMobile ? (
          <MobileBookReader
            originalPages={originalPages}
            translationPages={translationPagesList}
            currentPage={currentPage}
            onPageChange={goToPage}
            title={work.title}
            author={work.author}
            originalLanguage={work.language ?? 'grc'}
            fontSize={fontSize}
            hasBilingual={hasBilingualContent}
          />
        ) : currentSpread ? (
          <BookSpread
            spread={currentSpread}
            title={work.title}
            author={work.author}
            originalLanguage={work.language ?? 'grc'}
            translationLanguage={translationLanguage}
            fontSize={fontSize}
          />
        ) : (
          <div className="text-center text-white/30 py-20 font-garamond">
            Aucune page à afficher.
          </div>
        )}
      </div>

      {/* Controls */}
      <BookControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPrevious={goPrev}
        onNext={goNext}
        onGoToPage={goToPage}
        fontSize={fontSizePreset}
        onFontSizeChange={(size) => {
          setFontSizePreset(size);
          localStorage.setItem(LS_FONT_KEY, size);
        }}
        isBilingual={isBilingual}
        hasBilingual={hasBilingualContent}
        onToggleBilingual={() => setIsBilingual((b) => !b)}
        isPaginated={true}
        onToggleMode={() => {
          if (textId) navigate(`/texts/${textId}`);
        }}
      />
    </div>
  );
}
