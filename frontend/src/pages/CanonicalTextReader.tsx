import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useLazyPassages } from '../hooks/useLazyPassages';
import { cachedApiClient } from '../api/cachedClient';
import { CitationGenerator } from '../components/CitationGenerator';

interface Citation {
  id?: string;
  text: string;
  source: string;
  citation?: string;
  url?: string;
  doi?: string;
  node_id?: string;
}

// Passage interface moved to useLazyPassages hook

interface Work {
  work_id: string;
  canonical_id: string;
  title: string;
  author: string;
  language?: string;
  period?: string;
  school?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  editor?: string;
  publisher?: string;
  publication_date?: string;
  pub_place?: string;
  doi_url?: string;
}

interface TOCEntry {
  passage_id: string;
  canonical_ref: string;
  sequence_number: number;
}

interface TOC {
  books: Record<string, { chapters: Record<string, { sections: TOCEntry[]; passages: TOCEntry[] }>; passages: TOCEntry[] }>;
  chapters: Record<string, { sections: TOCEntry[]; passages: TOCEntry[] }>;
  sections: TOCEntry[];
  flat: TOCEntry[];
}

export default function CanonicalTextReader() {
  const { t } = useTranslation();
  const { textId } = useParams<{ textId: string }>();
  const location = useLocation();

  const [work, setWork] = useState<Work | null>(null);
  const [toc, setToc] = useState<TOC | null>(null);
  const [workLoading, setWorkLoading] = useState(true);
  const [workError, setWorkError] = useState('');
  const [showTOC, setShowTOC] = useState(false);
  const [currentPassageIndex, setCurrentPassageIndex] = useState(0);
  const [referenceSearch, setReferenceSearch] = useState('');
  const [notification, setNotification] = useState('');
  const [showCitationPanel, setShowCitationPanel] = useState(false);

  const workCitations = useMemo<Citation[]>(() => {
    if (!work) return [];
    return [{
      id: work.canonical_id,
      text: `${work.title}${work.author ? ' — ' + work.author : ''}`,
      source: [
        work.author,
        work.title,
        work.editor ? `Ed. ${work.editor}` : null,
        work.publisher,
        work.publication_date,
        work.pub_place,
      ].filter(Boolean).join(', '),
      citation: [
        work.author,
        work.title,
        work.editor ? `Ed. ${work.editor}` : null,
        work.publisher,
        work.publication_date,
      ].filter(Boolean).join('. '),
      url: work.doi_url ?? undefined,
    }];
  }, [work]);

  const passageRefs = useRef<Map<string, HTMLElement>>(new Map());
  const searchInputRef = useRef<HTMLInputElement>(null);

  const locationState = location.state as { highlightPassages?: string[]; scrollToPassage?: string } | null;
  const highlightPassages = locationState?.highlightPassages || [];
  const scrollToPassage = locationState?.scrollToPassage;

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Use lazy loading for passages (dramatic egress reduction!)
  const {
    passages,
    loading: passagesLoading,
    hasMore,
    loadMore,
    loadingMore,
    totalCount,
    error: passagesError,
    sentinelRef,
    progress,
  } = useLazyPassages(textId, {
    initialLimit: 30,  // Load only 30 passages initially
    batchSize: 30,     // Load 30 more as user scrolls
    autoLoad: true,    // Auto-load on scroll
    prefetchThreshold: 10, // Prefetch when 10 passages from end
  });

  // Combined loading and error states
  const loading = workLoading || passagesLoading;
  const error = workError || passagesError || '';

  // Simple notification (auto-dismiss)
  const notify = useCallback((message: string) => {
    setNotification(message);
    setTimeout(() => setNotification(''), 2000);
  }, []);

  // Load work metadata (uses cache!)
  useEffect(() => {
    if (!textId) return;

    const loadWork = async () => {
      try {
        setWorkLoading(true);
        setWorkError('');

        // Use cached API client for work metadata
        const workData = await cachedApiClient.getWork(textId) as Work;
        setWork(workData);

        // Load TOC (not cached yet, but small)
        const tocRes = await fetch(`${API_URL}/api/works/${textId}/table-of-contents`);
        if (tocRes.ok) {
          const tocData = await tocRes.json();
          setToc(tocData.toc);
        }

        setWorkLoading(false);
      } catch (err) {
        console.error('Error loading work:', err);
        setWorkError(err instanceof Error ? err.message : 'Failed to load work');
        setWorkLoading(false);
      }
    };

    loadWork();
  }, [textId, API_URL]);

  const scrollToPassageIndex = useCallback((index: number) => {
    const passage = passages[index];
    if (passage) {
      const element = passageRefs.current.get(passage.passage_id);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setCurrentPassageIndex(index);
      }
    }
  }, [passages]);

  const navigatePassage = useCallback((direction: 'prev' | 'next') => {
    const newIndex = direction === 'prev'
      ? Math.max(0, currentPassageIndex - 1)
      : Math.min(passages.length - 1, currentPassageIndex + 1);

    if (newIndex !== currentPassageIndex) {
      scrollToPassageIndex(newIndex);
    }
  }, [currentPassageIndex, passages.length, scrollToPassageIndex]);

  // Scroll to passage on load if specified
  useEffect(() => {
    if (scrollToPassage && passages.length > 0) {
      const idx = passages.findIndex(p => p.passage_id === scrollToPassage);
      if (idx !== -1) {
        setTimeout(() => scrollToPassageIndex(idx), 300);
      }
    }
  }, [scrollToPassage, passages, scrollToPassageIndex]);

  // Keyboard shortcuts (silent)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;

      if (e.key === '/' || (e.ctrlKey && e.key === 'k')) {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        navigatePassage('prev');
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        navigatePassage('next');
      } else if (e.key === 't') {
        setShowTOC(prev => !prev);
      } else if (e.key === 'Escape') {
        if (showTOC) setShowTOC(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [navigatePassage, showTOC]);

  const handleReferenceSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!referenceSearch.trim() || !textId) return;

    try {
      const res = await fetch(
        `${API_URL}/api/works/${textId}/passages/by-reference?reference=${encodeURIComponent(referenceSearch.trim())}`
      );

      if (res.ok) {
        const data = await res.json();
        if (data.passages && data.passages.length > 0) {
          const foundPassage = data.passages[0];
          const idx = passages.findIndex(p => p.passage_id === foundPassage.passage_id);
          if (idx !== -1) {
            scrollToPassageIndex(idx);
            notify(t('textReader.notifications.found'));
          }
        } else {
          notify(t('textReader.notifications.notFound'));
        }
      }
    } catch (_err) {
      notify(t('textReader.notifications.searchFailed'));
    }
  };

  const jumpToTOCEntry = (passageId: string) => {
    const idx = passages.findIndex(p => p.passage_id === passageId);
    if (idx !== -1) {
      scrollToPassageIndex(idx);
      setShowTOC(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
        <div className="flex flex-col items-center justify-center py-20 gap-4 max-w-7xl mx-auto relative z-10">
          <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border-2 border-amber-200/40" />
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-amber-600/70 animate-spin" />
          </div>
          <p className="text-sm text-stone-500 font-serif italic">{t('textReader.loading')}</p>
        </div>
      </div>
    );
  }

  if (error || !work) {
    return (
      <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
        <div className="flex items-center justify-center min-h-screen max-w-7xl mx-auto relative z-10">
        <div className="text-center max-w-md">
          <p className="text-red-600 mb-4">{error || t('textReader.error.workNotFound')}</p>
          <Link to="/texts" className="text-sm text-orange-600 hover:underline">← {t('textReader.nav.backToLibrary')}</Link>
        </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full pt-28 pb-12 bg-transparent">
      <div className="min-h-screen relative z-10">
      {/* Minimal notification */}
      {notification && (
        <div className="fixed top-4 right-4 z-50 px-4 py-2 bg-gray-900 text-white text-sm rounded shadow-lg">
          {notification}
        </div>
      )}

      {/* Clean header */}
      <header className="sticky top-0 z-40 bg-amber-50 border-b border-amber-100">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <Link to="/texts" className="text-sm text-stone-500 hover:text-stone-800">← {t('textReader.nav.library')}</Link>
            <div className="flex items-center gap-2">
              <Link
                to={`/texts/${textId}`}
                className="flex items-center justify-center gap-1.5 min-h-[44px] min-w-[44px] px-3 py-1.5 rounded-lg text-xs text-stone-600 hover:text-stone-800 hover:bg-amber-100/40 transition"
                title="Mode livre"
              >
                <BookOpen size={14} />
                <span className="hidden sm:inline">Mode livre</span>
              </Link>
              <button
                onClick={() => setShowCitationPanel((p) => !p)}
                className="flex items-center justify-center gap-1.5 min-h-[44px] min-w-[44px] px-3 py-1.5 rounded-lg text-xs text-stone-600 hover:text-stone-800 hover:bg-amber-100/40 transition"
                title="Citations"
              >
                <FileText size={14} />
                <span className="hidden sm:inline">Citations</span>
              </button>
              <button
                onClick={() => setShowTOC(!showTOC)}
                className="text-sm text-stone-600 hover:text-stone-800 flex items-center gap-1 min-h-[44px] px-2 rounded-lg hover:bg-amber-100/40 transition"
              >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              {showTOC ? t('textReader.nav.hide') : t('textReader.nav.contents')}
            </button>
            </div>
          </div>

          <div className="mb-2">
            <h1 className="text-xl font-display font-semibold text-stone-800">{work.title}</h1>
            <p className="text-sm text-stone-600">{work.author}</p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <form onSubmit={handleReferenceSearch} className="flex gap-2 flex-1">
              <input
                ref={searchInputRef}
                type="text"
                value={referenceSearch}
                onChange={(e) => setReferenceSearch(e.target.value)}
                placeholder={t('textReader.search.placeholder')}
                className="flex-1 min-w-0 px-3 py-2 sm:py-1.5 text-base sm:text-sm border border-amber-200/60 rounded focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900"
              />
              <button
                type="submit"
                className="px-4 py-2 sm:py-1.5 text-sm bg-gray-900 text-white rounded hover:bg-gray-800 whitespace-nowrap min-h-[44px] sm:min-h-0"
              >
                {t('textReader.search.go')}
              </button>
            </form>

            <div className="flex items-center justify-between sm:justify-start gap-2 sm:border-l border-amber-200/60 sm:pl-3 pt-2 sm:pt-0 border-t sm:border-t-0">
              <button
                onClick={() => navigatePassage('prev')}
                disabled={currentPassageIndex === 0}
                className="p-2 sm:p-1.5 min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 text-stone-600 hover:text-stone-800 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center"
                title={t('textReader.nav.previous')}
              >
                <svg className="w-5 h-5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span className="text-xs text-stone-500 min-w-[60px] text-center">
                {t('textReader.nav.pageCount', { current: currentPassageIndex + 1, total: totalCount || passages.length })}
              </span>
              <button
                onClick={() => navigatePassage('next')}
                disabled={currentPassageIndex === passages.length - 1}
                className="p-2 sm:p-1.5 min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 text-stone-600 hover:text-stone-800 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center"
                title={t('textReader.nav.next')}
              >
                <svg className="w-5 h-5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Compact TOC sidebar (overlay) */}
      {showTOC && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-20 z-40"
            onClick={() => setShowTOC(false)}
          />
          <aside className="fixed left-0 top-0 bottom-0 w-64 bg-parchment-50 border-r border-amber-200/60 z-50 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-stone-800">{t('textReader.toc.title')}</h2>
                <button
                  onClick={() => setShowTOC(false)}
                  className="flex items-center justify-center min-h-[44px] min-w-[44px] -mr-2 text-stone-500 hover:text-stone-800"
                  aria-label={t('textReader.nav.hide')}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {toc && (
                <div className="space-y-1">
                  {/* Books structure */}
                  {Object.keys(toc.books).length > 0 && Object.entries(toc.books).map(([bookNum, bookData]) => (
                    <div key={bookNum} className="mb-2">
                      <div className="text-xs font-medium text-stone-800 mb-1">{t('textReader.toc.book')} {bookNum}</div>
                      {Object.entries(bookData.chapters).map(([chNum, chData]) => (
                        <div key={chNum} className="ml-2 mb-1">
                          <div className="text-xs text-gray-700">{t('textReader.toc.chapter')} {chNum}</div>
                          {chData.sections.slice(0, 8).map(section => (
                            <button
                              key={section.passage_id}
                              onClick={() => jumpToTOCEntry(section.passage_id)}
                              className="block w-full min-h-[36px] text-left text-xs text-stone-600 hover:text-stone-800 hover:bg-parchment-50 px-2 py-2 rounded flex items-center"
                            >
                              {section.canonical_ref}
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  ))}

                  {/* Chapters only */}
                  {Object.keys(toc.books).length === 0 && Object.keys(toc.chapters).length > 0 &&
                    Object.entries(toc.chapters).map(([chNum, chData]) => (
                      <div key={chNum} className="mb-2">
                        <div className="text-xs font-medium text-stone-800 mb-1">{t('textReader.toc.chapterFull')} {chNum}</div>
                        {chData.sections.slice(0, 8).map(section => (
                          <button
                            key={section.passage_id}
                            onClick={() => jumpToTOCEntry(section.passage_id)}
                            className="block w-full min-h-[36px] text-left text-xs text-stone-600 hover:text-stone-800 hover:bg-parchment-50 px-2 py-2 rounded flex items-center"
                          >
                            {section.canonical_ref}
                          </button>
                        ))}
                      </div>
                    ))
                  }

                  {/* Flat list */}
                  {Object.keys(toc.books).length === 0 && Object.keys(toc.chapters).length === 0 && toc.flat.length > 0 && (
                    <div className="space-y-0.5">
                      {toc.flat.slice(0, 30).map(entry => (
                        <button
                          key={entry.passage_id}
                          onClick={() => jumpToTOCEntry(entry.passage_id)}
                          className="block w-full min-h-[36px] text-left text-xs text-stone-600 hover:text-stone-800 hover:bg-parchment-50 px-2 py-2 rounded flex items-center"
                        >
                          {entry.canonical_ref}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>
        </>
      )}

      {/* Clean content area */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="space-y-8">
          {passages.map((passage, index) => (
            <article
              key={passage.passage_id}
              ref={(el) => {
                if (el) passageRefs.current.set(passage.passage_id, el);
              }}
              className={`scroll-mt-24 ${
                index === currentPassageIndex ? 'opacity-100' : 'opacity-70'
              } transition-opacity`}
            >
              <div className="flex items-start gap-3 mb-3">
                <span className="inline-block px-2 py-0.5 text-xs font-medium text-stone-800 bg-parchment-50 rounded">
                  {passage.canonical_ref}
                </span>
                {highlightPassages.includes(passage.passage_id) && (
                  <span className="text-xs text-orange-600">{t('textReader.referenced')}</span>
                )}
              </div>
              <div className="text-stone-800 leading-relaxed" style={{ fontSize: '17px', lineHeight: '1.7' }}>
                {passage.text_content}
              </div>
            </article>
          ))}

          {/* Infinite scroll sentinel and loading indicator */}
          {hasMore && (
            <div
              ref={sentinelRef}
              className="py-8 text-center"
            >
              {loadingMore ? (
                <div className="flex items-center justify-center gap-2 text-stone-500">
                  <div className="w-4 h-4 border-2 border-amber-200/60 border-t-gray-600 rounded-full animate-spin" />
                  <span className="text-sm">{t('textReader.loadingMore', 'Loading more passages...')}</span>
                </div>
              ) : (
                <button
                  onClick={loadMore}
                  className="px-4 py-2 text-sm text-stone-600 hover:text-stone-800 hover:bg-parchment-50 rounded transition-colors"
                >
                  {t('textReader.loadMore', 'Load more')} ({progress.loaded} / {progress.total})
                </button>
              )}
            </div>
          )}

          {/* All passages loaded indicator */}
          {!hasMore && passages.length > 0 && (
            <div className="py-4 text-center text-sm text-stone-400">
              {t('textReader.allLoaded', 'All passages loaded')} ({passages.length})
            </div>
          )}
        </div>

        {/* Footer info */}
        <footer className="mt-12 pt-6 border-t border-amber-200/60">
          <div className="text-xs text-stone-500">
            <p className="mb-1">{work.source}</p>
            {work.language && <p>{t('textReader.footer.language')}: {work.language.toUpperCase()}</p>}
          </div>
        </footer>
      </main>

      {/* Keyboard shortcuts help (bottom corner, very subtle) */}
      <div className="fixed bottom-4 left-4 text-xs text-stone-400">
        {t('textReader.shortcuts.help')}
      </div>

      {showCitationPanel && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
          onClick={() => setShowCitationPanel(false)}
        >
          <div
            className="w-full sm:max-w-2xl max-h-[80vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <CitationGenerator citations={workCitations} />
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
