import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { tArray } from '../i18n/utils';
import { useKgStats, formatCount } from '../hooks/useKgStats';
import {
  HelpCircle,
  Loader2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Search,
  Filter,
  ArrowUpRight,
  RotateCcw,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { cn } from '../lib/utils';
import { staggerContainer, staggerItem } from '../utils/animations';
import { ShineBorder } from '../components/ui/shine-border';
import { Typewriter } from '../components/ui/typewriter';
import SearchGuideModal from '../components/SearchGuideModal';
import LemmaIntelligencePanel from '../components/LemmaIntelligencePanel';
import type { SearchResult, HybridSearchResponse } from '../types';

interface LemmaSuggestion {
  lemma: string;
  lemma_latin: string;
  language: string;
  pos: string;
  count: number;
  passage_count: number;
  forms: string[];
}

type SearchSourceFilter = 'all' | 'citation' | 'fulltext' | 'lemmatic' | 'semantic';
type SearchLanguageFilter = 'all' | 'greek' | 'latin' | 'english' | 'other';

const POS_COLORS: Record<string, { bg: string; text: string }> = {
  NOUN: { bg: 'bg-blue-100', text: 'text-blue-700' },
  VERB: { bg: 'bg-green-100', text: 'text-green-700' },
  ADJ: { bg: 'bg-purple-100', text: 'text-purple-700' },
  ADV: { bg: 'bg-orange-100', text: 'text-orange-700' },
  PRON: { bg: 'bg-pink-100', text: 'text-pink-700' },
  CONJ: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  ADP: { bg: 'bg-teal-100', text: 'text-teal-700' },
  DET: { bg: 'bg-indigo-100', text: 'text-indigo-700' },
  PART: { bg: 'bg-stone-100', text: 'text-stone-600' },
};

const SOURCE_FILTER_ORDER: SearchSourceFilter[] = ['all', 'citation', 'fulltext', 'lemmatic', 'semantic'];
const LANGUAGE_FILTER_ORDER: SearchLanguageFilter[] = ['all', 'greek', 'latin', 'english', 'other'];

export default function SearchPage() {
  const { t, i18n } = useTranslation();
  const stats = useKgStats();
  const tCounts = {
    workCount: formatCount(stats.works, i18n.language),
    passageCount: formatCount(stats.passages, i18n.language),
    nodeCount: formatCount(stats.nodes, i18n.language),
    edgeCount: formatCount(stats.edges, i18n.language),
  };
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<HybridSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showGuideModal, setShowGuideModal] = useState(false);
  const [selectedLemmaForPanel, setSelectedLemmaForPanel] = useState<{
    lemma: string;
    language: 'grc' | 'lat';
  } | null>(null);

  const [suggestions, setSuggestions] = useState<LemmaSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [autocompleteLoading, setAutocompleteLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [autocompleteLimit, setAutocompleteLimit] = useState(8);
  const [hasMoreSuggestions, setHasMoreSuggestions] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const [enableFulltext, setEnableFulltext] = useState(true);
  const [enableLemmatic, setEnableLemmatic] = useState(true);
  const [enableSemantic, setEnableSemantic] = useState(true);
  const [enableAI, setEnableAI] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [resultsPerPage, setResultsPerPage] = useState(10);
  const [sourceFilter, setSourceFilter] = useState<SearchSourceFilter>('all');
  const [languageFilter, setLanguageFilter] = useState<SearchLanguageFilter>('all');
  const [activeResultKey, setActiveResultKey] = useState<string | null>(null);
  const [navHeight, setNavHeight] = useState(64);
  const [toolbarHeight, setToolbarHeight] = useState(0);

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const currentQueryRef = useRef<string>('');
  const resultsSectionRef = useRef<HTMLDivElement>(null);
  const resultsToolbarRef = useRef<HTMLDivElement>(null);
  const resultRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const fetchSuggestions = useCallback(
    async (searchQuery: string, limit: number = 8, append: boolean = false) => {
      if (searchQuery.length < 2) {
        setSuggestions([]);
        setShowSuggestions(false);
        setHasMoreSuggestions(false);
        return;
      }

      currentQueryRef.current = searchQuery;

      if (append) {
        setLoadingMore(true);
      } else {
        setAutocompleteLoading(true);
      }

      try {
        const response = await apiClient.autocompleteLemmas(searchQuery, {
          limit: limit + 1,
          minCount: 2,
        });

        const hasMore = response.suggestions.length > limit;
        const suggestionsToShow = hasMore ? response.suggestions.slice(0, limit) : response.suggestions;

        setSuggestions(suggestionsToShow);
        if (!append) {
          setSelectedIndex(-1);
        }

        setShowSuggestions(suggestionsToShow.length > 0);
        setHasMoreSuggestions(hasMore);
      } catch (err) {
        console.error('Autocomplete error:', err);
        if (!append) {
          setSuggestions([]);
          setShowSuggestions(false);
        }
        setHasMoreSuggestions(false);
      } finally {
        setAutocompleteLoading(false);
        setLoadingMore(false);
      }
    },
    []
  );

  const handleQueryChange = useCallback(
    (value: string) => {
      setQuery(value);
      setAutocompleteLimit(8);

      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        fetchSuggestions(value, 8, false);
      }, 200);
    },
    [fetchSuggestions]
  );

  const loadMoreSuggestions = useCallback(() => {
    const newLimit = autocompleteLimit + 8;
    setAutocompleteLimit(newLimit);
    fetchSuggestions(currentQueryRef.current, newLimit, true);
  }, [autocompleteLimit, fetchSuggestions]);

  const selectSuggestion = useCallback((suggestion: LemmaSuggestion) => {
    setQuery(suggestion.lemma);
    setShowSuggestions(false);
    setSuggestions([]);
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!showSuggestions || suggestions.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % suggestions.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
          break;
        case 'Enter':
          if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
            e.preventDefault();
            selectSuggestion(suggestions[selectedIndex]);
          }
          break;
        case 'Escape':
          setShowSuggestions(false);
          setSelectedIndex(-1);
          break;
      }
    },
    [showSuggestions, suggestions, selectedIndex, selectSuggestion]
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const nav = document.getElementById('navigation');
    if (!nav) return;

    const updateNavHeight = () => setNavHeight(nav.offsetHeight);
    updateNavHeight();

    const observer = new ResizeObserver(updateNavHeight);
    observer.observe(nav);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!resultsToolbarRef.current) return;

    const toolbar = resultsToolbarRef.current;
    const updateToolbarHeight = () => setToolbarHeight(toolbar.offsetHeight);
    updateToolbarHeight();

    const observer = new ResizeObserver(updateToolbarHeight);
    observer.observe(toolbar);

    return () => observer.disconnect();
  }, [results]);

  const scrollToResults = useCallback(
    (behavior: ScrollBehavior = 'smooth') => {
      if (!resultsSectionRef.current) return;

      const top = resultsSectionRef.current.getBoundingClientRect().top + window.scrollY - navHeight - 12;
      window.scrollTo({ top: Math.max(top, 0), behavior });
    },
    [navHeight]
  );

  const scheduleScrollToResults = useCallback(
    (behavior: ScrollBehavior = 'smooth') => {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          scrollToResults(behavior);
        });
      });
    },
    [scrollToResults]
  );

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setError(t('search.enterQuery'));
      return;
    }

    if (!enableFulltext && !enableLemmatic && !enableSemantic) {
      setError(t('search.enableMode'));
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setCurrentPage(1);
      setSourceFilter('all');
      setLanguageFilter('all');
      setShowSuggestions(false);

      const response = await apiClient.hybridSearch({
        query: trimmedQuery,
        limit: 1000,
        enable_fulltext: enableFulltext,
        enable_lemmatic: enableLemmatic,
        enable_semantic: enableSemantic,
        enable_ai_enhancements: enableAI,
      });

      setResults(response);
      scheduleScrollToResults('smooth');
    } catch (err: unknown) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : t('search.searchFailed'));
    } finally {
      setLoading(false);
    }
  };

  const allResults = results?.combined_results ?? [];
  const sourceCountBase = allResults.filter((result) => matchesLanguageFilter(result, languageFilter));
  const languageCountBase = allResults.filter((result) => matchesSourceFilter(result, sourceFilter));
  const sourceCounts = countSourceMatches(sourceCountBase);
  const languageCounts = countLanguageMatches(languageCountBase);
  const filteredResults = allResults.filter(
    (result) => matchesSourceFilter(result, sourceFilter) && matchesLanguageFilter(result, languageFilter)
  );

  const totalPages = Math.max(1, Math.ceil(filteredResults.length / resultsPerPage));
  const currentPageSafe = Math.min(currentPage, totalPages);
  const startIndex = (currentPageSafe - 1) * resultsPerPage;
  const paginatedResults = filteredResults.slice(startIndex, startIndex + resultsPerPage);
  const visibleRangeStart = paginatedResults.length > 0 ? startIndex + 1 : 0;
  const visibleRangeEnd = startIndex + paginatedResults.length;
  const stickyOffset = navHeight + 12;
  const cardScrollMargin = navHeight + toolbarHeight + 28;
  const hasClientFilters = sourceFilter !== 'all' || languageFilter !== 'all';
  const activeModesCount = [enableFulltext, enableLemmatic, enableSemantic].filter(Boolean).length;
  const firstVisibleResultKey = paginatedResults.length > 0 ? getResultKey(paginatedResults[0], startIndex) : null;

  useEffect(() => {
    if (currentPage !== currentPageSafe) {
      setCurrentPage(currentPageSafe);
    }
  }, [currentPage, currentPageSafe]);

  useEffect(() => {
    setActiveResultKey(firstVisibleResultKey);
  }, [currentPageSafe, firstVisibleResultKey, resultsPerPage, sourceFilter, languageFilter, results?.query]);

  const goToPage = (page: number) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
    scheduleScrollToResults('smooth');
  };

  const jumpToResult = (resultKey: string) => {
    setActiveResultKey(resultKey);
    resultRefs.current[resultKey]?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  };

  const updateSourceFilter = (nextFilter: SearchSourceFilter) => {
    setSourceFilter(nextFilter);
    setCurrentPage(1);
    scheduleScrollToResults('smooth');
  };

  const updateLanguageFilter = (nextFilter: SearchLanguageFilter) => {
    setLanguageFilter(nextFilter);
    setCurrentPage(1);
    scheduleScrollToResults('smooth');
  };

  const clearClientFilters = () => {
    setSourceFilter('all');
    setLanguageFilter('all');
    setCurrentPage(1);
    scheduleScrollToResults('smooth');
  };

  const renderSearchModes = (compact: boolean) => (
    <div className={cn('space-y-2', !compact && 'px-2')}>
      <div
        className={cn(
          'flex flex-wrap items-center gap-2 rounded-2xl border border-amber-200/60 bg-parchment-100/70 backdrop-blur-md',
          compact ? 'px-3 py-3' : 'px-4 sm:px-6 py-3'
        )}
      >
        <span className="text-sm font-medium text-stone-700">{t('search.searchModes')}:</span>

        <label className="flex min-h-[40px] items-center gap-2 px-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={enableFulltext}
            onChange={(e) => setEnableFulltext(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300 bg-white text-orange-600 focus:ring-2 focus:ring-orange-500"
          />
          <span>{t('search.modes.fullText')}</span>
        </label>

        <label className="flex min-h-[40px] items-center gap-2 px-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={enableLemmatic}
            onChange={(e) => setEnableLemmatic(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300 bg-white text-orange-600 focus:ring-2 focus:ring-orange-500"
          />
          <span>{t('search.modes.lemmatic')}</span>
        </label>

        <label className="flex min-h-[40px] items-center gap-2 px-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={enableSemantic}
            onChange={(e) => setEnableSemantic(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300 bg-white text-orange-600 focus:ring-2 focus:ring-orange-500"
          />
          <span>{t('search.modes.semantic')}</span>
        </label>

        <label
          className={cn(
            'ml-auto flex min-h-[40px] items-center gap-2 rounded-full px-3 py-1 text-sm transition-all',
            enableAI ? 'bg-orange-100 text-orange-700' : 'text-stone-500'
          )}
        >
          <input
            type="checkbox"
            checked={enableAI}
            onChange={(e) => setEnableAI(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300 bg-white text-orange-600 focus:ring-2 focus:ring-orange-500"
          />
          <span className="font-medium">{t('search.modes.ai')}</span>
        </label>
      </div>

      {activeModesCount >= 2 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-orange-200 bg-orange-100 px-3 py-1 text-xs text-orange-700">
            {t('search.rrfEnabled')}
          </span>
        </div>
      )}
    </div>
  );

  const renderSearchForm = (compact: boolean) => (
    <form onSubmit={handleSearch} className="space-y-3">
      <div className="relative">
        <ShineBorder
          className={cn('!p-0 bg-white/95 backdrop-blur-sm', compact && 'shadow-sm')}
          borderRadius={compact ? 18 : 9999}
          color={['#f97316', '#ea580c', '#fdba74']}
        >
          <div className={cn('flex gap-3', compact ? 'flex-col p-1.5 sm:flex-row' : 'p-2')}>
            <div className="relative flex-1">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder={t('search.autocompletePlaceholder')}
                className={cn(
                  'w-full min-w-0 border-0 bg-transparent text-stone-800 placeholder-stone-400 transition-all focus:outline-none focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0',
                  compact ? 'px-4 py-3 text-base' : 'px-4 sm:px-6 py-3 text-base'
                )}
                data-no-ring="true"
                autoComplete="off"
                disabled={loading}
                autoFocus={!results}
              />
              {autocompleteLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="h-4 w-4 animate-spin text-orange-500" />
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!query.trim() || loading}
              className={cn(
                'whitespace-nowrap rounded-full bg-gradient-to-br from-stone-800 to-stone-700 font-medium text-white transition-all disabled:cursor-not-allowed disabled:opacity-50',
                compact ? 'px-6 py-3 text-sm sm:text-base' : 'px-8 py-3 text-base hover:shadow-lg'
              )}
            >
              {loading ? t('search.searching') : t('search.searchButton')}
            </button>
          </div>
        </ShineBorder>

        <AnimatePresence>
          {showSuggestions && suggestions.length > 0 && (
            <motion.div
              ref={suggestionsRef}
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              className="absolute z-50 mt-2 w-full overflow-hidden rounded-2xl border border-amber-200/60 bg-white/95 shadow-2xl backdrop-blur-xl"
            >
              <div className="p-1">
                {suggestions.map((suggestion, index) => {
                  const posColor = POS_COLORS[suggestion.pos] || { bg: 'bg-stone-100', text: 'text-stone-600' };

                  return (
                    <div
                      key={`${suggestion.lemma}-${index}`}
                      className={cn(
                        'flex items-center gap-1 rounded-xl px-2 py-1 transition-all',
                        selectedIndex === index ? 'bg-orange-50' : 'hover:bg-stone-50'
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => selectSuggestion(suggestion)}
                        className="flex flex-1 min-w-0 flex-wrap items-center gap-2 sm:gap-3 rounded-lg px-2 py-2 text-left"
                      >
                        <span className="text-base sm:text-lg font-medium text-stone-800 truncate max-w-full sm:min-w-[120px]">{suggestion.lemma}</span>
                        <span className="hidden sm:inline font-mono text-sm text-stone-500 sm:min-w-[100px]">{suggestion.lemma_latin}</span>
                        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', posColor.bg, posColor.text)}>
                          {suggestion.pos}
                        </span>
                        <span className="ml-auto text-xs text-stone-400 hidden sm:inline">
                          {suggestion.count.toLocaleString()} {t('search.autocomplete.occurrencesAbbrev')}
                        </span>
                        <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-400">
                          {t('search.autocomplete.passages', { count: suggestion.passage_count })}
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLemmaForPanel({
                            lemma: suggestion.lemma,
                            language: suggestion.language === 'grc' ? 'grc' : 'lat',
                          });
                          setShowSuggestions(false);
                        }}
                        className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg p-2 text-stone-400 transition-colors hover:bg-orange-100 hover:text-orange-600"
                        title={t('search.lemmaIntelligenceTitle')}
                      >
                        <Sparkles className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>

              {hasMoreSuggestions && (
                <div className="border-t border-amber-200/60 px-4 py-2">
                  <button
                    type="button"
                    onClick={loadMoreSuggestions}
                    disabled={loadingMore}
                    className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-orange-600 transition-all hover:bg-orange-50 disabled:opacity-50"
                  >
                    {loadingMore ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        {t('search.loadingMore')}
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        {t('search.showMoreResults')}
                      </>
                    )}
                  </button>
                </div>
              )}

              <div className="hidden sm:block border-t border-amber-200/60 bg-stone-50 px-4 py-2">
                <p className="flex items-center gap-4 text-xs text-stone-500">
                  <span>
                    <kbd className="rounded border border-stone-300 bg-white px-1.5 py-0.5 text-[10px]">↑↓</kbd> {t('search.autocomplete.keyboard.navigate')}
                  </span>
                  <span>
                    <kbd className="rounded border border-stone-300 bg-white px-1.5 py-0.5 text-[10px]">Enter</kbd> {t('search.autocomplete.keyboard.select')}
                  </span>
                  <span>
                    <kbd className="rounded border border-stone-300 bg-white px-1.5 py-0.5 text-[10px]">Esc</kbd> {t('search.autocomplete.keyboard.close')}
                  </span>
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {renderSearchModes(compact)}
    </form>
  );

  return (
    <>
      {!results && !loading && (
        <div className="flex min-h-screen w-full flex-col items-center justify-center bg-transparent px-4 pb-12 pt-28">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8, ease: 'easeInOut' }}
            className="relative z-10 flex w-full max-w-4xl flex-col items-center justify-center gap-8"
          >
            <div className="text-center">
              <h1 className="mb-4 text-3xl sm:text-5xl font-display font-bold text-stone-800 md:text-7xl">
                {t('search.titlePrefix', '') ? `${t('search.titlePrefix')} ` : ''}
                <Typewriter
                  text={tArray(t, 'search.titleWords')}
                  speed={120}
                  waitTime={3000}
                  deleteSpeed={70}
                  className="text-stone-800"
                  cursorChar="_"
                />
                {t('search.titleSuffix', '') ? ` ${t('search.titleSuffix')}` : ''}
              </h1>
              <p className="text-base sm:text-lg text-stone-600 md:text-xl">{t('search.subtitle', tCounts)}</p>
            </div>

            <button
              onClick={() => setShowGuideModal(true)}
              className="flex items-center gap-2 rounded-full border border-amber-200/60 bg-parchment-100/70 px-4 py-2 text-sm text-stone-800 transition-all hover:bg-white hover:shadow-lg"
              title={t('search.searchGuide')}
            >
              <HelpCircle className="h-5 w-5" />
              <span className="hidden sm:inline">{t('search.searchGuide')}</span>
            </button>

            <div className="w-full space-y-4">{renderSearchForm(false)}</div>

            {error && (
              <div className="mt-2 rounded-2xl border border-red-300 bg-red-100 px-6 py-4 text-center text-sm text-red-700 backdrop-blur-sm">
                {error}
              </div>
            )}

            <div className="mt-4 text-center">
              <p className="mb-3 text-sm text-stone-600">{t('search.trySearchingFor')}</p>
              <div className="flex flex-wrap justify-center gap-2">
                <button
                  onClick={() => setQuery("ἐφ' ἡμῖν")}
                  className="rounded-full border border-amber-200/60 bg-parchment-100/70 px-4 py-2 text-sm text-stone-800 transition-all hover:bg-white hover:shadow-lg"
                >
                  ἐφ&apos; ἡμῖν
                </button>
                <button
                  onClick={() => setQuery('liberum arbitrium')}
                  className="rounded-full border border-amber-200/60 bg-parchment-100/70 px-4 py-2 text-sm text-stone-800 transition-all hover:bg-white hover:shadow-lg"
                >
                  liberum arbitrium
                </button>
                <button
                  onClick={() => setQuery('voluntary action')}
                  className="rounded-full border border-amber-200/60 bg-parchment-100/70 px-4 py-2 text-sm text-stone-800 transition-all hover:bg-white hover:shadow-lg"
                >
                  voluntary action
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {loading && (
        <div className="flex min-h-screen flex-col items-center justify-center bg-transparent">
          <div className="mb-4 inline-block h-12 w-12 animate-spin rounded-full border-3 border-amber-200 border-t-orange-500" />
          <p className="text-lg text-stone-600">{t('search.loadingMessage', tCounts)}</p>
        </div>
      )}

      {results && !loading && (
        <div ref={resultsSectionRef} className="min-h-screen bg-transparent pb-16">
          <div
            ref={resultsToolbarRef}
            className="sticky z-30 border-b border-amber-200/60 bg-parchment-50/85 backdrop-blur-xl"
            style={{ top: `${stickyOffset}px` }}
          >
            <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium uppercase tracking-[0.18em] text-orange-700/80">
                      {t('search.workspaceTitle')}
                    </p>
                    <h2 className="text-xl font-display font-semibold text-stone-800 sm:text-2xl">
                      {t('search.resultsFor', { query: results.query || query.trim() })}
                    </h2>
                    <p className="max-w-3xl text-sm text-stone-600">{t('search.workspaceSubtitle')}</p>
                  </div>

                  <button
                    onClick={() => setShowGuideModal(true)}
                    className="inline-flex items-center gap-2 self-start rounded-full border border-amber-200/60 bg-white/80 px-4 py-2 text-sm text-stone-700 transition-all hover:bg-white hover:shadow-md"
                    title={t('search.searchGuide')}
                  >
                    <HelpCircle className="h-4 w-4" />
                    <span>{t('search.searchGuide')}</span>
                  </button>
                </div>

                {renderSearchForm(true)}

                <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-stone-200 bg-white/80 px-3 py-1 text-sm text-stone-700">
                      {filteredResults.length > 0
                        ? t('search.showingRange', {
                            start: visibleRangeStart,
                            end: visibleRangeEnd,
                            count: filteredResults.length,
                          })
                        : t('search.results', { count: filteredResults.length })}
                    </span>

                    {allResults.length !== filteredResults.length && (
                      <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-sm text-amber-800">
                        {t('search.results', { count: allResults.length })}
                      </span>
                    )}

                    {results.used_rrf && (
                      <span className="rounded-full border border-orange-200 bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">
                        RRF
                      </span>
                    )}

                    {results.citation_match && (
                      <span className="rounded-full border border-orange-200 bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">
                        📌 {results.citation_match}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <label className="flex items-center gap-2 text-sm text-stone-700">
                      <span>{t('search.show')}:</span>
                      <select
                        value={resultsPerPage}
                        onChange={(e) => {
                          setResultsPerPage(Number(e.target.value));
                          setCurrentPage(1);
                          scheduleScrollToResults('smooth');
                        }}
                        className="rounded-lg border border-stone-300 bg-white px-2 py-1 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-orange-500"
                      >
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                    </label>

                    <PaginationControls currentPage={currentPageSafe} totalPages={totalPages} onPageChange={goToPage} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <div className="mb-6 rounded-3xl border border-amber-200/60 bg-white/65 p-4 shadow-sm backdrop-blur-sm sm:p-6">
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-medium uppercase tracking-[0.18em] text-stone-500">
                      <Filter className="h-4 w-4" />
                      <span>{t('search.refineResults')}</span>
                    </div>
                    <p className="mt-2 text-sm text-stone-600">{t('search.workspaceSubtitle')}</p>
                  </div>

                  {hasClientFilters && (
                    <button
                      onClick={clearClientFilters}
                      className="inline-flex items-center gap-2 self-start rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-sm font-medium text-stone-700 transition-all hover:bg-stone-100"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>{t('search.clearRefinements')}</span>
                    </button>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">Sources</div>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {SOURCE_FILTER_ORDER.map((filterValue) => (
                        <FilterChip
                          key={filterValue}
                          active={sourceFilter === filterValue}
                          disabled={filterValue !== 'all' && sourceCounts[filterValue] === 0}
                          label={t(`search.sourceFilters.${filterValue}`)}
                          count={sourceCounts[filterValue]}
                          onClick={() => updateSourceFilter(filterValue)}
                        />
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">Languages</div>
                    <div className="flex gap-2 overflow-x-auto pb-1">
                      {LANGUAGE_FILTER_ORDER.map((filterValue) => (
                        <FilterChip
                          key={filterValue}
                          active={languageFilter === filterValue}
                          disabled={filterValue !== 'all' && languageCounts[filterValue] === 0}
                          label={t(`search.languageFilters.${filterValue}`)}
                          count={languageCounts[filterValue]}
                          onClick={() => updateLanguageFilter(filterValue)}
                        />
                      ))}
                    </div>
                  </div>

                  {paginatedResults.length > 0 && (
                    <div className="xl:hidden">
                      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">
                        <Search className="h-4 w-4" />
                        <span>{t('search.jumpToResult')}</span>
                      </div>
                      <div className="flex gap-2 overflow-x-auto pb-1">
                        {paginatedResults.map((result, index) => {
                          const absoluteIndex = startIndex + index;
                          const resultKey = getResultKey(result, absoluteIndex);

                          return (
                            <button
                              key={resultKey}
                              onClick={() => jumpToResult(resultKey)}
                              className={cn(
                                'min-w-[160px] rounded-2xl border px-3 py-2 text-left transition-all',
                                activeResultKey === resultKey
                                  ? 'border-orange-300 bg-orange-50 text-orange-900'
                                  : 'border-stone-200 bg-white text-stone-700 hover:border-orange-200 hover:bg-orange-50/60'
                              )}
                            >
                              <div className="text-xs font-semibold text-orange-600">#{absoluteIndex + 1}</div>
                              <div className="truncate text-sm font-medium">{formatNavigatorLabel(result)}</div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
              {paginatedResults.length > 0 && (
                <ResultsNavigator
                  results={paginatedResults}
                  activeResultKey={activeResultKey}
                  currentPage={currentPageSafe}
                  pageStartIndex={startIndex}
                  stickyTop={stickyOffset + toolbarHeight + 16}
                  onJump={jumpToResult}
                />
              )}

              <div>
                {paginatedResults.length > 0 ? (
                  <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
                    {paginatedResults.map((result, index) => {
                      const absoluteIndex = startIndex + index;
                      const resultKey = getResultKey(result, absoluteIndex);

                      return (
                        <div
                          key={resultKey}
                          ref={(node) => {
                            resultRefs.current[resultKey] = node;
                          }}
                          style={{ scrollMarginTop: `${cardScrollMargin}px` }}
                        >
                          <SearchResultCard
                            result={result}
                            index={absoluteIndex}
                            isActive={activeResultKey === resultKey}
                            onActivate={() => setActiveResultKey(resultKey)}
                          />
                        </div>
                      );
                    })}
                  </motion.div>
                ) : (
                  <div className="rounded-3xl border border-amber-200/60 bg-white/70 px-6 py-12 text-center shadow-sm backdrop-blur-sm">
                    <p className="text-lg font-display font-semibold text-stone-800">
                      {allResults.length > 0 ? t('search.filterNoMatchTitle') : t('search.noResultsTitle')}
                    </p>
                    <p className="mt-2 text-sm text-stone-600">
                      {allResults.length > 0 ? t('search.filterNoMatchDesc') : t('search.noResultsDesc')}
                    </p>
                    {allResults.length > 0 && hasClientFilters && (
                      <button
                        onClick={clearClientFilters}
                        className="mt-6 inline-flex items-center gap-2 rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-sm font-medium text-stone-700 transition-all hover:bg-stone-100"
                      >
                        <RotateCcw className="h-4 w-4" />
                        <span>{t('search.clearRefinements')}</span>
                      </button>
                    )}
                  </div>
                )}

                {paginatedResults.length > 0 && totalPages > 1 && (
                  <div className="mt-8 flex justify-center">
                    <div className="rounded-2xl border border-amber-200/60 bg-parchment-100/70 px-4 py-3 shadow-sm">
                      <PaginationControls currentPage={currentPageSafe} totalPages={totalPages} onPageChange={goToPage} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <SearchGuideModal isOpen={showGuideModal} onClose={() => setShowGuideModal(false)} />

      {selectedLemmaForPanel && (
        <LemmaIntelligencePanel
          lemma={selectedLemmaForPanel.lemma}
          language={selectedLemmaForPanel.language}
          onClose={() => setSelectedLemmaForPanel(null)}
          onLemmaClick={(newLemma) => {
            setSelectedLemmaForPanel({
              lemma: newLemma,
              language: selectedLemmaForPanel.language,
            });
          }}
        />
      )}
    </>
  );
}

function FilterChip({
  active,
  disabled,
  label,
  count,
  onClick,
}: {
  active: boolean;
  disabled?: boolean;
  label: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-all',
        active
          ? 'border-orange-300 bg-orange-100 text-orange-900'
          : 'border-stone-200 bg-white text-stone-700 hover:border-orange-200 hover:bg-orange-50',
        disabled && 'cursor-not-allowed opacity-40 hover:border-stone-200 hover:bg-white'
      )}
    >
      <span>{label}</span>
      <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs text-stone-500">{count}</span>
    </button>
  );
}

function PaginationControls({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const { t } = useTranslation();
  if (totalPages <= 1) return null;

  const pageNumbers = getVisiblePageNumbers(currentPage, totalPages);

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg p-2 text-stone-600 transition-colors hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-30"
        title={t('search.pagination.previous')}
      >
        <ChevronLeft className="h-5 w-5" />
      </button>

      {pageNumbers.map((pageNumber) => (
        <button
          key={pageNumber}
          onClick={() => onPageChange(pageNumber)}
          aria-current={pageNumber === currentPage ? 'page' : undefined}
          className={cn(
            'flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg px-3 py-2 text-sm font-medium transition-all',
            pageNumber === currentPage
              ? 'bg-stone-800 text-white shadow-sm'
              : 'bg-white text-stone-700 hover:bg-stone-100'
          )}
        >
          {pageNumber}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg p-2 text-stone-600 transition-colors hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-30"
        title={t('search.pagination.next')}
      >
        <ChevronRight className="h-5 w-5" />
      </button>
    </div>
  );
}

function ResultsNavigator({
  results,
  activeResultKey,
  currentPage,
  pageStartIndex,
  stickyTop,
  onJump,
}: {
  results: SearchResult[];
  activeResultKey: string | null;
  currentPage: number;
  pageStartIndex: number;
  stickyTop: number;
  onJump: (resultKey: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <aside className="hidden xl:block">
      <div
        className="sticky rounded-3xl border border-amber-200/60 bg-white/70 p-4 shadow-sm backdrop-blur-sm"
        style={{ top: `${stickyTop}px` }}
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-stone-500">{t('search.jumpToResult')}</div>
            <div className="mt-1 text-sm text-stone-600">Page {currentPage}</div>
          </div>
          <Search className="h-4 w-4 text-stone-400" />
        </div>

        <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
          {results.map((result, index) => {
            const absoluteIndex = pageStartIndex + index;
            const resultKey = getResultKey(result, absoluteIndex);

            return (
              <button
                key={resultKey}
                onClick={() => onJump(resultKey)}
                className={cn(
                  'w-full rounded-2xl border px-3 py-3 text-left transition-all',
                  activeResultKey === resultKey
                    ? 'border-orange-300 bg-orange-50'
                    : 'border-transparent bg-stone-50/80 hover:border-amber-200 hover:bg-white'
                )}
              >
                <div className="text-xs font-semibold text-orange-600">#{absoluteIndex + 1}</div>
                <div className="mt-1 text-sm font-medium text-stone-800">{formatNavigatorLabel(result)}</div>
                <div className="mt-1 truncate text-xs text-stone-500">{result.canonical_ref || result.author}</div>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

function SearchResultCard({
  result,
  index,
  isActive,
  onActivate,
}: {
  result: SearchResult;
  index: number;
  isActive: boolean;
  onActivate: () => void;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const aiResult = result as SearchResult & { reranker_score?: number };
  const sourceTokens = getSourceTokens(result.source);

  const handleViewText = () => {
    if (result.work_id) {
      const url = result.passage_id ? `/texts/${result.work_id}?passage=${result.passage_id}` : `/texts/${result.work_id}`;
      navigate(url);
    }
  };

  return (
    <motion.article variants={staggerItem}>
      <div
        className={cn(
          'rounded-[28px] border bg-parchment-100/70 p-5 shadow-sm transition-all sm:p-6',
          isActive
            ? 'border-orange-300 shadow-xl ring-1 ring-orange-200/80'
            : 'border-amber-200/60 hover:border-orange-300 hover:shadow-lg'
        )}
        onMouseEnter={onActivate}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-orange-100 px-3 py-1 text-sm font-semibold text-orange-700">#{index + 1}</span>

              {sourceTokens.map((sourceToken) => (
                <span
                  key={sourceToken}
                  className={cn(
                    'rounded-full px-3 py-1 text-xs font-medium',
                    sourceToken === 'citation'
                      ? 'border border-orange-200 bg-orange-100 text-orange-700'
                      : 'bg-stone-100 text-stone-700'
                  )}
                >
                  {t(`search.sourceFilters.${sourceToken}`)}
                </span>
              ))}

              {result.language && (
                <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-stone-600">
                  {t(`search.languageFilters.${normalizeLanguage(result.language)}`)}
                </span>
              )}

              {result.category && (
                <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-stone-600">
                  {result.category}
                </span>
              )}
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-display font-semibold text-stone-800">{formatFullReference(result)}</h3>

              <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-stone-600">
                <span>
                  <strong className="text-stone-800">{t('search.author')}:</strong> {result.author}
                </span>
                {result.language && (
                  <span>
                    <strong className="text-stone-800">{t('search.language')}:</strong>{' '}
                    {t(`search.languageFilters.${normalizeLanguage(result.language)}`)}
                  </span>
                )}
                {result.canonical_ref && (
                  <span>
                    <strong className="text-stone-800">{t('search.resultMeta.reference')}</strong> {result.canonical_ref}
                  </span>
                )}
              </div>
            </div>

            {result.snippet ? (
              <div
                className="line-clamp-4 rounded-2xl border-l-4 border-orange-400 bg-orange-50 p-4 text-sm leading-7 text-stone-700 [&_b]:font-semibold [&_mark]:bg-orange-200 [&_mark]:px-1"
                dangerouslySetInnerHTML={{ __html: result.snippet }}
              />
            ) : result.text_content ? (
              <div className="rounded-2xl border-l-4 border-stone-300 bg-stone-50 p-4 text-sm leading-7 text-stone-700">
                <p className="line-clamp-4">
                  {result.text_content.slice(0, 340)}
                  {result.text_content.length > 340 ? '...' : ''}
                </p>
              </div>
            ) : null}

            <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-stone-500">
              {result.rrf_score !== undefined && <span className="font-medium text-orange-600">{t('search.resultMeta.rrfScore')} {result.rrf_score.toFixed(4)}</span>}
              {aiResult.reranker_score !== undefined && (
                <span className="font-medium text-amber-600">{t('search.resultMeta.aiScore')} {aiResult.reranker_score.toFixed(4)}</span>
              )}
              {result.rank !== undefined && <span>{t('search.resultMeta.rank')} {result.rank.toFixed(4)}</span>}
            </div>
          </div>

          <button
            onClick={handleViewText}
            disabled={!result.work_id}
            className="inline-flex shrink-0 items-center gap-2 self-start rounded-2xl border border-amber-200/60 bg-white px-4 py-3 text-sm font-medium text-stone-800 transition-colors hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span>{t('search.viewText')}</span>
            <ArrowUpRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.article>
  );
}

function formatFullReference(result: SearchResult): string {
  const parts = [result.author, result.title];
  const locationParts: string[] = [];

  if (result.book) locationParts.push(result.book);
  if (result.chapter) locationParts.push(result.chapter);
  if (result.section) locationParts.push(result.section);

  const location = locationParts.join(':');

  if (location) {
    return `${parts.join(', ')} ${location}`;
  }

  if (result.canonical_ref) {
    return `${result.author}, ${result.title} ${result.canonical_ref}`;
  }

  return `${result.author}, ${result.title}`;
}

function getResultKey(result: SearchResult, fallbackIndex: number): string {
  return String(result.passage_id || result.id || `${result.author}-${result.title}-${result.canonical_ref || fallbackIndex}`);
}

function getResultKeySource(source?: string): SearchSourceFilter[] {
  return getSourceTokens(source);
}

function getSourceTokens(source?: string): SearchSourceFilter[] {
  if (!source) return [];

  const normalized = source.toLowerCase();
  const tokens = new Set<SearchSourceFilter>();

  if (normalized.includes('citation')) tokens.add('citation');
  if (normalized.includes('fulltext')) tokens.add('fulltext');
  if (normalized.includes('lemmatic')) tokens.add('lemmatic');
  if (normalized.includes('semantic')) tokens.add('semantic');

  return [...tokens];
}

function normalizeLanguage(language?: string): SearchLanguageFilter {
  const normalized = language?.toLowerCase().trim() ?? '';

  if (!normalized) return 'other';
  if (normalized.includes('grc') || normalized.includes('greek')) return 'greek';
  if (normalized.includes('lat') || normalized.includes('latin')) return 'latin';
  if (normalized.includes('eng') || normalized.includes('english')) return 'english';
  return 'other';
}

function matchesSourceFilter(result: SearchResult, sourceFilter: SearchSourceFilter): boolean {
  if (sourceFilter === 'all') return true;
  return getResultKeySource(result.source).includes(sourceFilter);
}

function matchesLanguageFilter(result: SearchResult, languageFilter: SearchLanguageFilter): boolean {
  if (languageFilter === 'all') return true;
  return normalizeLanguage(result.language) === languageFilter;
}

function countSourceMatches(results: SearchResult[]): Record<SearchSourceFilter, number> {
  const counts: Record<SearchSourceFilter, number> = {
    all: results.length,
    citation: 0,
    fulltext: 0,
    lemmatic: 0,
    semantic: 0,
  };

  results.forEach((result) => {
    getResultKeySource(result.source).forEach((sourceToken) => {
      if (sourceToken !== 'all') {
        counts[sourceToken] += 1;
      }
    });
  });

  return counts;
}

function countLanguageMatches(results: SearchResult[]): Record<SearchLanguageFilter, number> {
  const counts: Record<SearchLanguageFilter, number> = {
    all: results.length,
    greek: 0,
    latin: 0,
    english: 0,
    other: 0,
  };

  results.forEach((result) => {
    counts[normalizeLanguage(result.language)] += 1;
  });

  return counts;
}

function getVisiblePageNumbers(currentPage: number, totalPages: number): number[] {
  const maxVisible = 5;
  const halfWindow = Math.floor(maxVisible / 2);

  let start = Math.max(1, currentPage - halfWindow);
  const end = Math.min(totalPages, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

function formatNavigatorLabel(result: SearchResult): string {
  if (result.canonical_ref) {
    return `${result.author}, ${result.canonical_ref}`;
  }

  return `${result.author}, ${result.title}`;
}
