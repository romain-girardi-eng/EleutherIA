import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Download,
  Loader2,
  Search,
  X,
} from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import { cn } from '../../utils/cn';
import { getDocument, getDocumentFileBlob } from '../../api/projects';
import type { ProjectDocumentDetail } from '../../api/projects';

// Worker bundled via Vite's new URL pattern — no CDN, no hardcoded path
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DocumentHighlightViewerProps {
  documentId: string;
  filename: string;
  contentType: string;
  pageCount?: number;
  initialHighlight?: string;
  initialPage?: number;
  onClose?: () => void;
}

interface MatchRef {
  page: number;
  /** index within that page's matches */
  indexOnPage: number;
  /** global index across all pages */
  globalIndex: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildMatchRegex(query: string): RegExp | null {
  const trimmed = query.trim();
  if (!trimmed) return null;
  const pattern = trimmed
    .split(/\s+/)
    .map(escapeRegex)
    .join('[\\s\\S]*?');
  try {
    return new RegExp(pattern, 'gi');
  } catch {
    return null;
  }
}

/** Count how many matches exist in a string for a given regex (resets lastIndex). */
function countMatches(text: string, regex: RegExp): number {
  regex.lastIndex = 0;
  let n = 0;
  while (regex.exec(text) !== null) n++;
  regex.lastIndex = 0;
  return n;
}

/** Given page_texts and a regex, returns an array mapping global-match-index → MatchRef */
function buildMatchMap(
  pageTexts: string[],
  query: string,
): MatchRef[] {
  const regex = buildMatchRegex(query);
  if (!regex) return [];
  const refs: MatchRef[] = [];
  pageTexts.forEach((text, pageIdx) => {
    const count = countMatches(text, regex);
    for (let i = 0; i < count; i++) {
      refs.push({
        page: pageIdx + 1,
        indexOnPage: i,
        globalIndex: refs.length,
      });
    }
  });
  return refs;
}

// ── Frame overlay ─────────────────────────────────────────────────────────────

interface FrameOverlayProps {
  targetEl: Element | null;
  containerEl: HTMLElement | null;
  visible: boolean;
}

function FrameOverlay({ targetEl, containerEl, visible }: FrameOverlayProps) {
  const [rect, setRect] = useState<{ top: number; left: number; width: number; height: number } | null>(null);

  useEffect(() => {
    if (!targetEl || !containerEl || !visible) {
      setRect(null);
      return;
    }
    const update = () => {
      const containerRect = containerEl.getBoundingClientRect();
      const targetRect = targetEl.getBoundingClientRect();
      setRect({
        top: targetRect.top - containerRect.top + containerEl.scrollTop - 6,
        left: targetRect.left - containerRect.left + containerEl.scrollLeft - 8,
        width: targetRect.width + 16,
        height: targetRect.height + 12,
      });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(targetEl);
    ro.observe(containerEl);
    return () => ro.disconnect();
  }, [targetEl, containerEl, visible]);

  if (!rect || !visible) return null;

  return (
    <motion.div
      key={`${rect.top}-${rect.left}`}
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 400, damping: 28 }}
      className="pointer-events-none absolute z-20"
      style={{
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
      }}
    >
      {/* Outer glow */}
      <div
        className="absolute inset-0 rounded-md"
        style={{
          boxShadow: '0 0 0 3px rgba(217,119,6,0.18), 0 0 16px 4px rgba(217,119,6,0.13)',
        }}
      />
      {/* Border frame */}
      <div className="absolute inset-0 rounded-md border-2 border-amber-500" />
      {/* Corner accents */}
      <span className="absolute -top-[3px] -left-[3px] h-3 w-3 border-t-2 border-l-2 border-amber-600 rounded-tl-sm" />
      <span className="absolute -top-[3px] -right-[3px] h-3 w-3 border-t-2 border-r-2 border-amber-600 rounded-tr-sm" />
      <span className="absolute -bottom-[3px] -left-[3px] h-3 w-3 border-b-2 border-l-2 border-amber-600 rounded-bl-sm" />
      <span className="absolute -bottom-[3px] -right-[3px] h-3 w-3 border-b-2 border-r-2 border-amber-600 rounded-br-sm" />
      {/* Label */}
      <motion.span
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12, duration: 0.18 }}
        className="absolute -top-6 left-0 inline-flex items-center gap-1 rounded-full bg-amber-500 px-2 py-0.5 text-[10px] font-mono font-semibold text-white shadow-sm"
      >
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-white/80" />
        source
      </motion.span>
    </motion.div>
  );
}

// ── PDF viewer ────────────────────────────────────────────────────────────────

interface PdfViewerProps {
  fileData: Uint8Array;
  numPages: number;
  query: string;
  activeMatch: MatchRef | null;
  matchMap: MatchRef[];
  onNumPages: (n: number) => void;
}

function PdfViewer({
  fileData,
  numPages,
  query,
  activeMatch,
  matchMap,
  onNumPages,
}: PdfViewerProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const [activeMarkEl, setActiveMarkEl] = useState<Element | null>(null);
  const [renderedPages, setRenderedPages] = useState<Set<number>>(new Set());

  // Stable file object so react-pdf doesn't reload on re-renders
  const file = useMemo(() => ({ data: fileData }), [fileData]);

  // Build regex for customTextRenderer
  const matchRegex = useMemo(() => buildMatchRegex(query), [query]);

  // When active match changes: scroll to the page, then find the active mark element
  useEffect(() => {
    if (!activeMatch) {
      setActiveMarkEl(null);
      return;
    }
    const pageEl = pageRefs.current[activeMatch.page];
    if (pageEl && scrollContainerRef.current) {
      pageEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    // Wait for text layer to settle then locate the right mark
    const tid = window.setTimeout(() => {
      const pageEl2 = pageRefs.current[activeMatch.page];
      if (!pageEl2) return;
      const marks = pageEl2.querySelectorAll('mark.elx-hl');
      const target = marks[activeMatch.indexOnPage] ?? marks[0] ?? null;
      setActiveMarkEl(target);
      if (target && scrollContainerRef.current) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 80);
    return () => window.clearTimeout(tid);
  }, [activeMatch]);

  // Re-locate mark when a new page finishes rendering
  useEffect(() => {
    if (!activeMatch) return;
    if (!renderedPages.has(activeMatch.page)) return;
    const pageEl = pageRefs.current[activeMatch.page];
    if (!pageEl) return;
    const marks = pageEl.querySelectorAll('mark.elx-hl');
    const target = marks[activeMatch.indexOnPage] ?? marks[0] ?? null;
    setActiveMarkEl(target);
  }, [renderedPages, activeMatch]);

  // Reset active mark when query clears
  useEffect(() => {
    if (!query.trim()) setActiveMarkEl(null);
  }, [query]);

  const customTextRenderer = useCallback(
    (textItem: { str: string }): string => {
      if (!matchRegex || !textItem.str) return textItem.str;
      matchRegex.lastIndex = 0;
      return textItem.str.replace(matchRegex, (match) => {
        return `<mark class="elx-hl">${match}</mark>`;
      });
    },
    [matchRegex],
  );

  const handlePageRenderSuccess = useCallback((page: number) => {
    setRenderedPages((prev) => new Set(prev).add(page));
  }, []);

  // Which pages have matches (for rendering priority hint)
  const pagesWithMatches = useMemo(
    () => new Set(matchMap.map((m) => m.page)),
    [matchMap],
  );

  return (
    <div
      ref={scrollContainerRef}
      className="relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-6 py-8 space-y-8 bg-stone-100/60"
    >
      <Document
        file={file}
        onLoadSuccess={({ numPages: n }) => onNumPages(n)}
        loading={
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-7 w-7 animate-spin text-amber-500" />
          </div>
        }
        error={
          <div className="flex items-center justify-center py-20 text-center">
            <div className="space-y-2">
              <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto" />
              <p className="text-sm text-stone-500">Failed to parse PDF</p>
            </div>
          </div>
        }
      >
        {numPages > 0 &&
          Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => {
            const hasMatch = pagesWithMatches.has(pageNum);
            const isActive = activeMatch?.page === pageNum;
            return (
              <div
                key={pageNum}
                ref={(el) => { pageRefs.current[pageNum] = el; }}
                className="relative"
              >
                {/* Page sheet */}
                <div
                  className={cn(
                    'relative mx-auto rounded-lg overflow-hidden',
                    'shadow-[0_4px_24px_-8px_rgba(0,0,0,0.18)]',
                    isActive && 'ring-1 ring-amber-300/60',
                    hasMatch && !isActive && 'ring-1 ring-amber-200/40',
                  )}
                  style={{ maxWidth: 720 }}
                >
                  <Page
                    pageNumber={pageNum}
                    width={Math.min(
                      typeof window !== 'undefined' ? window.innerWidth - 80 : 680,
                      720,
                    )}
                    renderTextLayer
                    renderAnnotationLayer={false}
                    customTextRenderer={customTextRenderer as never}
                    onRenderSuccess={() => handlePageRenderSuccess(pageNum)}
                    className="bg-parchment-50"
                  />

                  {/* Frame overlay for active match */}
                  <AnimatePresence>
                    {isActive && activeMarkEl && (
                      <FrameOverlay
                        key={activeMatch.globalIndex}
                        targetEl={activeMarkEl}
                        containerEl={pageRefs.current[pageNum]}
                        visible
                      />
                    )}
                  </AnimatePresence>
                </div>

                {/* Page number */}
                <div className="absolute bottom-2 right-3 font-mono text-[10px] text-stone-400 select-none">
                  {pageNum}
                </div>
              </div>
            );
          })}
      </Document>
    </div>
  );
}

// ── Text viewer ───────────────────────────────────────────────────────────────

interface TextViewerProps {
  text: string;
  query: string;
  activeMatch: MatchRef | null;
}

function TextViewer({ text, query, activeMatch }: TextViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const markRefs = useRef<HTMLElement[]>([]);
  const [activeMarkEl, setActiveMarkEl] = useState<Element | null>(null);

  // Build highlighted HTML
  const html = useMemo(() => {
    if (!query.trim()) return text.replace(/\n/g, '<br/>');
    const regex = buildMatchRegex(query);
    if (!regex) return text.replace(/\n/g, '<br/>');
    regex.lastIndex = 0;
    return text
      .replace(/\n/g, '<br/>')
      .replace(regex, (match) => `<mark class="elx-hl">${match}</mark>`);
  }, [text, query]);

  // After render, locate all marks and set active one
  useEffect(() => {
    if (!scrollRef.current) return;
    const all = Array.from(scrollRef.current.querySelectorAll('mark.elx-hl')) as HTMLElement[];
    markRefs.current = all;
    const idx = activeMatch?.globalIndex ?? 0;
    const el = all[idx] ?? null;
    setActiveMarkEl(el);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [html, activeMatch]);

  return (
    <div
      ref={scrollRef}
      className="relative flex-1 min-h-0 overflow-y-auto px-8 py-8 bg-stone-100/60"
    >
      <div
        className="relative mx-auto max-w-2xl bg-parchment-50 rounded-lg shadow-[0_4px_24px_-8px_rgba(0,0,0,0.18)] px-10 py-10"
      >
        <div
          className="font-serif text-stone-800 text-[0.9375rem] leading-[1.8] prose prose-stone max-w-none"
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <AnimatePresence>
          {activeMarkEl && query.trim() && (
            <FrameOverlay
              key={activeMatch?.globalIndex ?? 0}
              targetEl={activeMarkEl}
              containerEl={scrollRef.current}
              visible
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── Search bar ────────────────────────────────────────────────────────────────

interface SearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  totalMatches: number;
  activeIndex: number;
  onPrev: () => void;
  onNext: () => void;
}

function SearchBar({
  query,
  onQueryChange,
  totalMatches,
  activeIndex,
  onPrev,
  onNext,
}: SearchBarProps) {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) onPrev();
        else onNext();
      }
    },
    [onPrev, onNext],
  );

  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="relative flex items-center">
        <Search className="absolute left-2.5 h-3.5 w-3.5 text-stone-400 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('projects.viewer.searchPlaceholder')}
          aria-label={t('projects.viewer.searchLabel')}
          className={cn(
            'h-8 w-52 rounded-lg border pl-8 pr-3 text-xs font-sans',
            'bg-white/90 text-stone-800 placeholder:text-stone-400',
            'border-stone-200 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-300',
            'transition-colors',
          )}
        />
      </div>

      {query.trim() && (
        <motion.div
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -4 }}
          className="flex items-center gap-1"
        >
          <span className="font-mono text-[11px] text-stone-400 tabular-nums min-w-[3.5rem] text-center">
            {totalMatches === 0
              ? t('projects.viewer.noMatches')
              : `${activeIndex + 1} / ${totalMatches}`}
          </span>
          <button
            type="button"
            onClick={onPrev}
            disabled={totalMatches === 0}
            aria-label={t('projects.viewer.prevMatch')}
            className="h-7 w-7 inline-flex items-center justify-center rounded-md text-stone-400 hover:bg-amber-100/70 hover:text-amber-800 disabled:opacity-30 disabled:cursor-default transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={totalMatches === 0}
            aria-label={t('projects.viewer.nextMatch')}
            className="h-7 w-7 inline-flex items-center justify-center rounded-md text-stone-400 hover:bg-amber-100/70 hover:text-amber-800 disabled:opacity-30 disabled:cursor-default transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </motion.div>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function DocumentHighlightViewer({
  documentId,
  filename,
  contentType,
  pageCount,
  initialHighlight,
  initialPage: _initialPage,
  onClose,
}: DocumentHighlightViewerProps) {
  const { t } = useTranslation();
  const isPdf =
    contentType === 'application/pdf' || filename.toLowerCase().endsWith('.pdf');

  // ── Data loading ──────────────────────────────────────────────────────────

  const [fileData, setFileData] = useState<Uint8Array | null>(null);
  const [docDetail, setDocDetail] = useState<ProjectDocumentDetail | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(pageCount ?? 0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    const blobRef = { url: '' };

    Promise.all([
      getDocumentFileBlob(documentId),
      getDocument(documentId),
    ])
      .then(([blob, detail]) => {
        if (cancelled) return;
        setDocDetail(detail);
        const url = URL.createObjectURL(blob);
        blobRef.url = url;
        setObjectUrl(url);
        return blob.arrayBuffer();
      })
      .then((ab) => {
        if (cancelled || !ab) return;
        setFileData(new Uint8Array(ab));
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError(t('projects.viewer.loadError'));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      if (blobRef.url) URL.revokeObjectURL(blobRef.url);
    };
  }, [documentId, t]);

  // ── Search state ──────────────────────────────────────────────────────────

  const [query, setQuery] = useState(initialHighlight ?? '');
  const [debouncedQuery, setDebouncedQuery] = useState(initialHighlight ?? '');
  const debounceRef = useRef<number | undefined>(undefined);

  const handleQueryChange = useCallback((q: string) => {
    setQuery(q);
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => setDebouncedQuery(q), 250);
  }, []);

  useEffect(() => () => window.clearTimeout(debounceRef.current), []);

  // Build match map from page_texts
  const pageTexts = useMemo<string[]>(() => {
    if (!docDetail) return [];
    if (docDetail.page_texts) return docDetail.page_texts;
    if (docDetail.extracted_text) return [docDetail.extracted_text];
    return [];
  }, [docDetail]);

  const matchMap = useMemo(
    () => buildMatchMap(pageTexts, debouncedQuery),
    [pageTexts, debouncedQuery],
  );

  const [activeMatchIndex, setActiveMatchIndex] = useState(0);

  // Reset active index when query or matchMap changes
  useEffect(() => {
    setActiveMatchIndex(0);
  }, [debouncedQuery]);

  const activeMatch = matchMap[activeMatchIndex] ?? null;
  const totalMatches = matchMap.length;

  const handleNext = useCallback(() => {
    if (totalMatches === 0) return;
    setActiveMatchIndex((i) => (i + 1) % totalMatches);
  }, [totalMatches]);

  const handlePrev = useCallback(() => {
    if (totalMatches === 0) return;
    setActiveMatchIndex((i) => (i - 1 + totalMatches) % totalMatches);
  }, [totalMatches]);

  // Keyboard shortcuts
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [onClose]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Backdrop */}
      <motion.div
        key="viewer-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-[70] bg-stone-950/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <motion.aside
        key="viewer-panel"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 340, damping: 38 }}
        role="dialog"
        aria-modal="true"
        aria-label={filename}
        className={cn(
          'fixed top-0 right-0 z-[71] h-[100dvh]',
          'w-full sm:w-[620px] lg:w-[760px]',
          'flex flex-col',
          'bg-parchment-50/98 border-l border-amber-200/60',
          'shadow-[-16px_0_60px_-24px_rgba(120,53,15,0.35)]',
        )}
      >
        {/* Header */}
        <header className="shrink-0 px-5 pt-4 pb-3 border-b border-amber-200/40 bg-white/80 backdrop-blur-sm">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="min-w-0 flex-1">
              <h2 className="font-display text-base font-semibold text-stone-900 leading-tight truncate">
                {filename}
              </h2>
              <div className="flex items-center gap-3 mt-0.5">
                {(numPages > 0 || pageCount) && (
                  <span className="text-xs text-stone-400 font-mono">
                    {t('projects.viewer.pages', { count: numPages || pageCount })}
                  </span>
                )}
                {isPdf && (
                  <span className="text-xs text-stone-400 font-mono uppercase tracking-wide">PDF</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {/* Download fallback */}
              {objectUrl && (
                <a
                  href={objectUrl}
                  download={filename}
                  aria-label={t('projects.viewer.download')}
                  className="h-9 w-9 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-amber-100/60 hover:text-amber-900 transition-colors"
                >
                  <Download className="h-4 w-4" />
                </a>
              )}
              <button
                type="button"
                onClick={onClose}
                aria-label={t('projects.viewer.close')}
                className="h-9 w-9 inline-flex items-center justify-center rounded-full text-stone-400 hover:bg-amber-100/60 hover:text-amber-900 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Search bar row */}
          {!loading && !loadError && (
            <SearchBar
              query={query}
              onQueryChange={handleQueryChange}
              totalMatches={totalMatches}
              activeIndex={activeMatchIndex}
              onPrev={handlePrev}
              onNext={handleNext}
            />
          )}
        </header>

        {/* Body */}
        <div className="flex-1 min-h-0 flex flex-col relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
                <p className="text-sm text-stone-500">{t('projects.viewer.loading')}</p>
              </div>
            </div>
          )}

          {!loading && loadError && (
            <div className="absolute inset-0 flex items-center justify-center p-6">
              <div className="text-center space-y-3">
                <AlertTriangle className="h-10 w-10 text-amber-500 mx-auto" />
                <p className="text-stone-600 text-sm">{loadError}</p>
                {objectUrl && (
                  <a
                    href={objectUrl}
                    download={filename}
                    className="inline-flex items-center gap-1.5 text-sm text-amber-700 underline underline-offset-2 hover:text-amber-900"
                  >
                    <Download className="h-3.5 w-3.5" />
                    {t('projects.viewer.download')}
                  </a>
                )}
              </div>
            </div>
          )}

          {!loading && !loadError && isPdf && fileData && (
            <PdfViewer
              fileData={fileData}
              numPages={numPages}
              query={debouncedQuery}
              activeMatch={activeMatch}
              matchMap={matchMap}
              onNumPages={setNumPages}
            />
          )}

          {!loading && !loadError && !isPdf && docDetail && (
            <TextViewer
              text={docDetail.extracted_text ?? ''}
              query={debouncedQuery}
              activeMatch={activeMatch}
            />
          )}

          {/* No-match callout */}
          <AnimatePresence>
            {debouncedQuery.trim() && !loading && !loadError && totalMatches === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.18 }}
                className="absolute bottom-5 left-1/2 -translate-x-1/2 z-30 pointer-events-none"
              >
                <div className="inline-flex items-center gap-2 rounded-full border border-amber-200/60 bg-parchment-50/95 px-4 py-2 shadow-sm text-xs text-stone-500 font-sans">
                  <Search className="h-3.5 w-3.5 text-stone-400" />
                  {t('projects.viewer.noMatches')} —{' '}
                  <span className="italic text-stone-400">{debouncedQuery}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.aside>

      {/* Global mark styles — injected once, scoped by .elx-hl */}
      <style>{`
        .elx-hl {
          background: rgba(251, 191, 36, 0.35);
          border-radius: 2px;
          padding: 0 1px;
          color: inherit;
        }
        .react-pdf__Page__textContent .elx-hl {
          background: rgba(251, 191, 36, 0.45);
        }
      `}</style>
    </>
  );
}
