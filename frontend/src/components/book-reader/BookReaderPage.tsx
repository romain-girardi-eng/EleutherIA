'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { AlignJustify } from 'lucide-react';
import { cachedApiClient } from '../../api/cachedClient';
import { useLazyPassages } from '../../hooks/useLazyPassages';
import { useCalibration } from './useCalibration';
import { useBookPagination } from './useBookPagination';
import { usePageSync } from './usePageSync';
import { BookSpread } from './BookSpread';
import { BookPage } from './BookPage';
import { BookControls } from './BookControls';
import { BookProgress } from './BookProgress';
import { MobileBookReader } from './MobileBookReader';
import {
  FONT_SIZE_DEFAULT,
  FONT_SIZE_MIN,
  FONT_SIZE_MAX,
  MOBILE_BREAKPOINT,
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

const LS_FONT_KEY = 'book-reader-font-size';
const DEFAULT_LINE_HEIGHT = 1.75;
const DEFAULT_FONT_FAMILY = 'EB Garamond, serif';
const RESIZE_DEBOUNCE_MS = 150;

// Layout chrome heights (px) — header row + running header + page number + padding
const HEADER_CHROME = 50;   // BookHeader + lang label
const FOOTER_CHROME = 30;   // page number
const PAGE_VERTICAL_PAD = 40; // top + bottom padding (~5% estimated)
const REF_COLUMN_RATIO = 0.08; // ref column takes ~8% of page width

// Sticky header height (approx)
const SITE_HEADER_HEIGHT = 120;
// Controls + progress below the book
const CONTROLS_HEIGHT = 100;

function readFontSize(): number {
  if (typeof window === 'undefined') return FONT_SIZE_DEFAULT;
  const stored = localStorage.getItem(LS_FONT_KEY);
  if (stored) {
    const n = Number(stored);
    if (n >= FONT_SIZE_MIN && n <= FONT_SIZE_MAX) return n;
  }
  return FONT_SIZE_DEFAULT;
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
  const [fontSize, setFontSize] = useState(readFontSize);
  const [isBilingual, setIsBilingual] = useState(true);
  const [dimensions, setDimensions] = useState({
    windowWidth: typeof window !== 'undefined' ? window.innerWidth : 1200,
    windowHeight: typeof window !== 'undefined' ? window.innerHeight : 800,
  });
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  const isMobile = dimensions.windowWidth < MOBILE_BREAKPOINT;

  const initialPage = Number(searchParams.get('page')) || 1;
  const [currentPage, setCurrentPage] = useState(initialPage);

  // ---- Measure container ----
  useEffect(() => {
    const measure = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };
    measure();
    // Re-measure after fonts load
    if (document.fonts) {
      document.fonts.ready.then(measure);
    }
  }, [isMobile, dimensions.windowWidth]);

  // ---- Responsive page dimensions derived from viewport ----
  const availableHeight = dimensions.windowHeight - SITE_HEADER_HEIGHT - CONTROLS_HEIGHT;
  const pageHeight = Math.max(400, availableHeight);

  const pageConfig: PageConfig = useMemo(() => {
    const effectiveContainerWidth = containerWidth || dimensions.windowWidth * 0.92;
    // In bilingual mode each page gets half; in single mode full width
    const singlePageWidth = isMobile
      ? effectiveContainerWidth
      : isBilingual
        ? effectiveContainerWidth / 2
        : Math.min(effectiveContainerWidth, 640); // single column capped for readability
    const refWidth = Math.max(24, singlePageWidth * REF_COLUMN_RATIO);
    const horizontalPad = singlePageWidth * 0.12; // ~6% each side
    const textWidth = singlePageWidth - refWidth - horizontalPad;
    const textHeight = pageHeight - HEADER_CHROME - FOOTER_CHROME - PAGE_VERTICAL_PAD;

    return {
      width: Math.max(textWidth, 100),
      height: Math.max(textHeight, 200),
      marginRef: refWidth,
      fontSize,
      lineHeight: DEFAULT_LINE_HEIGHT,
      fontFamily: DEFAULT_FONT_FAMILY,
    };
  }, [containerWidth, dimensions.windowWidth, fontSize, isMobile, isBilingual, pageHeight]);

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
    return () => { cancelled = true; };
  }, [textId]);

  // ---- Load ALL passages ----
  const {
    passages: rawPassages,
    loading: passagesLoading,
    hasMore,
    loadMore,
  } = useLazyPassages(textId, { initialLimit: 200, batchSize: 200, autoLoad: false });

  useEffect(() => {
    if (hasMore && !passagesLoading) loadMore();
  }, [hasMore, passagesLoading, loadMore]);

  const passages = rawPassages as Passage[];

  // ---- Separate original / translation ----
  const hasBilingualContent = useMemo(() => passages.some((p) => p.translation_text), [passages]);

  const originalPassages = useMemo(
    () => passages.map((p) => ({
      passage_id: p.passage_id,
      canonical_ref: p.canonical_ref,
      text_content: p.text_content,
      kg_node_count: p.kg_node_count,
    })),
    [passages],
  );

  const translationPassages = useMemo(
    () => passages.filter((p) => p.translation_text).map((p) => ({
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

  // ---- Calibration ----
  const { correctionRatio, calibrated, calibrate, hiddenRef } = useCalibration(pageConfig);

  useEffect(() => {
    if (passages.length > 0 && !calibrated) calibrate(passages[0].text_content);
  }, [passages, calibrated, calibrate]);

  // ---- Pagination ----
  const { pages: originalPages, totalPages: originalTotalPages } = useBookPagination({
    passages: originalPassages,
    config: pageConfig,
    correctionRatio: calibrated ? correctionRatio : 1,
  });

  const { pages: translationPagesList } = useBookPagination({
    passages: translationPassages,
    config: pageConfig,
    correctionRatio: calibrated ? correctionRatio : 1,
  });

  // ---- Page sync ----
  const spreads = usePageSync({
    originalPages,
    translationPages: isBilingual ? translationPagesList : [],
  });

  const totalPages = isBilingual ? spreads.length * 2 : originalTotalPages;

  // ---- Navigation ----
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

  const goNext = useCallback(() => goToPage(currentPage + (isBilingual ? 2 : 1)), [currentPage, isBilingual, goToPage]);
  const goPrev = useCallback(() => goToPage(currentPage - (isBilingual ? 2 : 1)), [currentPage, isBilingual, goToPage]);

  // ---- Keyboard ----
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key) {
        case 'ArrowRight': e.preventDefault(); goNext(); break;
        case 'ArrowLeft': e.preventDefault(); goPrev(); break;
        case 'Home': e.preventDefault(); goToPage(1); break;
        case 'End': e.preventDefault(); goToPage(totalPages); break;
        case 't': if (hasBilingualContent) setIsBilingual((b) => !b); break;
        case 'v': case 'Escape': if (textId) navigate(`/texts/${textId}`); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goNext, goPrev, goToPage, totalPages, hasBilingualContent, textId, navigate]);

  // ---- Resize ----
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setDimensions({ windowWidth: window.innerWidth, windowHeight: window.innerHeight });
        if (containerRef.current) setContainerWidth(containerRef.current.offsetWidth);
      }, RESIZE_DEBOUNCE_MS);
    };
    window.addEventListener('resize', handleResize);
    return () => { clearTimeout(timeoutId); window.removeEventListener('resize', handleResize); };
  }, []);

  // ---- Font size persistence ----
  const handleFontSizeChange = useCallback((size: number) => {
    const clamped = Math.max(FONT_SIZE_MIN, Math.min(FONT_SIZE_MAX, size));
    setFontSize(clamped);
    localStorage.setItem(LS_FONT_KEY, String(clamped));
  }, []);

  // ---- Current spread ----
  const currentSpreadIndex = Math.max(0, Math.floor((currentPage - 1) / 2));
  const currentSpread = spreads[currentSpreadIndex] ?? null;

  const currentRef = useMemo(() => {
    if (isBilingual && currentSpread) return currentSpread.left.passages[0]?.canonicalRef;
    return originalPages[currentPage - 1]?.passages[0]?.canonicalRef;
  }, [isBilingual, currentSpread, originalPages, currentPage]);

  // ---- Loading ----
  if (workLoading || passagesLoading || !work) {
    return (
      <div className="h-svh w-full flex items-center justify-center bg-transparent">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-amber-200/60 border-t-gray-900 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-stone-500 text-sm">Chargement de l&apos;ouvrage…</p>
        </div>
      </div>
    );
  }

  // ---- Render — h-svh, no scroll ----
  return (
    <div className="h-svh w-full flex flex-col overflow-hidden bg-transparent">
      {/* Hidden calibration div */}
      <div ref={hiddenRef} aria-hidden="true" style={{ position: 'absolute', visibility: 'hidden' }} />

      {/* Header — compact, fixed height */}
      <header className="shrink-0 bg-amber-50 border-b border-amber-100 z-40">
        <div className="max-w-6xl mx-auto px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/texts" className="text-sm text-stone-500 hover:text-stone-800">←</Link>
            <div>
              <h1 className="text-base font-display font-semibold text-stone-800 leading-tight">{work.title}</h1>
              <p className="text-xs text-stone-500">{work.author}</p>
            </div>
          </div>
          <button
            onClick={() => { if (textId) navigate(`/texts/${textId}`); }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-stone-600 hover:text-stone-800 hover:bg-amber-100/40 transition"
            title="Mode scroll"
          >
            <AlignJustify size={14} />
            <span className="hidden sm:inline">Mode scroll</span>
          </button>
        </div>
      </header>

      {/* Book — takes ALL remaining vertical space */}
      <main ref={containerRef} className="flex-1 min-h-0 flex flex-col px-4 sm:px-6 lg:px-8">
        <div className="flex-1 min-h-0 max-w-[1200px] w-full mx-auto flex flex-col py-3">
          {/* Book pages — fills all available space */}
          <div className="flex-1 min-h-0">
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
              <div className="h-full">
                <BookSpread
                  spread={currentSpread}
                  title={work.title}
                  author={work.author}
                  originalLanguage={work.language ?? 'grc'}
                  translationLanguage={translationLanguage}
                  fontSize={fontSize}

                />
              </div>
            ) : originalPages[currentPage - 1] ? (
              <div className="h-full max-w-[640px] mx-auto">
                <div className="h-full bg-white/70 rounded-lg shadow-sm border border-amber-200/30">
                  <BookPage
                    page={originalPages[currentPage - 1]}
                    headerLeft={work.title}
                    headerRight={work.author}
                    isGreek={work.language === 'grc'}
                    fontSize={fontSize}
                    side="single"
  
                  />
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-stone-400 font-garamond">
                Aucune page à afficher.
              </div>
            )}
          </div>

          {/* Progress + Controls — compact, pinned to bottom */}
          <div className="shrink-0 pt-2">
            <BookProgress currentPage={currentPage} totalPages={totalPages} currentRef={currentRef} />
            <BookControls
              currentPage={currentPage}
              totalPages={totalPages}
              onPrevious={goPrev}
              onNext={goNext}
              onGoToPage={goToPage}
              fontSize={fontSize}
              onFontSizeChange={handleFontSizeChange}
              isBilingual={isBilingual}
              hasBilingual={hasBilingualContent}
              onToggleBilingual={() => setIsBilingual((b) => !b)}
              onToggleMode={() => { if (textId) navigate(`/texts/${textId}`); }}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
