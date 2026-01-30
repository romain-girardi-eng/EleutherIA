import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { HelpCircle, Loader2, ChevronDown, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { apiClient } from '../api/client';
import { staggerContainer, staggerItem } from '../utils/animations';
import { AuroraBackground } from '../components/ui/aurora-background';
import { ShineBorder } from '../components/ui/shine-border';
import { Typewriter } from '../components/ui/typewriter';
import SearchGuideModal from '../components/SearchGuideModal';
import LemmaIntelligencePanel from '../components/LemmaIntelligencePanel';
import type { SearchResult, HybridSearchResponse } from '../types';

// Lemma suggestion type
interface LemmaSuggestion {
  lemma: string;
  lemma_latin: string;
  language: string;
  pos: string;
  count: number;
  passage_count: number;
  forms: string[];
}

// POS tag colors for visual distinction
const POS_COLORS: Record<string, { bg: string; text: string }> = {
  NOUN: { bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-700 dark:text-blue-300' },
  VERB: { bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-700 dark:text-green-300' },
  ADJ: { bg: 'bg-purple-100 dark:bg-purple-900/40', text: 'text-purple-700 dark:text-purple-300' },
  ADV: { bg: 'bg-orange-100 dark:bg-orange-900/40', text: 'text-orange-700 dark:text-orange-300' },
  PRON: { bg: 'bg-pink-100 dark:bg-pink-900/40', text: 'text-pink-700 dark:text-pink-300' },
  CONJ: { bg: 'bg-yellow-100 dark:bg-yellow-900/40', text: 'text-yellow-700 dark:text-yellow-300' },
  ADP: { bg: 'bg-teal-100 dark:bg-teal-900/40', text: 'text-teal-700 dark:text-teal-300' },
  DET: { bg: 'bg-indigo-100 dark:bg-indigo-900/40', text: 'text-indigo-700 dark:text-indigo-300' },
  PART: { bg: 'bg-gray-100 dark:bg-gray-700/40', text: 'text-gray-700 dark:text-gray-300' },
};

export default function SearchPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<HybridSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showGuideModal, setShowGuideModal] = useState(false);

  // Lemma Intelligence Panel state
  const [selectedLemmaForPanel, setSelectedLemmaForPanel] = useState<{
    lemma: string;
    language: 'grc' | 'lat';
  } | null>(null);

  // Autocomplete state
  const [suggestions, setSuggestions] = useState<LemmaSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [autocompleteLoading, setAutocompleteLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [autocompleteLimit, setAutocompleteLimit] = useState(8);
  const [hasMoreSuggestions, setHasMoreSuggestions] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const currentQueryRef = useRef<string>('');

  // Fetch autocomplete suggestions with debouncing
  const fetchSuggestions = useCallback(async (searchQuery: string, limit: number = 8, append: boolean = false) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      setHasMoreSuggestions(false);
      return;
    }

    // Store current query for "load more" functionality
    currentQueryRef.current = searchQuery;

    if (append) {
      setLoadingMore(true);
    } else {
      setAutocompleteLoading(true);
    }

    try {
      // Fetch one extra to detect if there are more results
      const response = await apiClient.autocompleteLemmas(searchQuery, {
        limit: limit + 1,
        minCount: 2,
      });

      const hasMore = response.suggestions.length > limit;
      const suggestionsToShow = hasMore ? response.suggestions.slice(0, limit) : response.suggestions;

      if (append) {
        setSuggestions(suggestionsToShow);
      } else {
        setSuggestions(suggestionsToShow);
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
  }, []);

  // Debounced query change handler
  const handleQueryChange = useCallback((value: string) => {
    setQuery(value);

    // Reset limit when query changes
    setAutocompleteLimit(8);

    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce autocomplete requests (200ms)
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(value, 8, false);
    }, 200);
  }, [fetchSuggestions]);

  // Load more suggestions
  const loadMoreSuggestions = useCallback(() => {
    const newLimit = autocompleteLimit + 8;
    setAutocompleteLimit(newLimit);
    fetchSuggestions(currentQueryRef.current, newLimit, true);
  }, [autocompleteLimit, fetchSuggestions]);

  // Handle suggestion selection
  const selectSuggestion = useCallback((suggestion: LemmaSuggestion) => {
    setQuery(suggestion.lemma);
    setShowSuggestions(false);
    setSuggestions([]);
    inputRef.current?.focus();
  }, []);

  // Keyboard navigation for suggestions
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % suggestions.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
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
  }, [showSuggestions, suggestions, selectedIndex, selectSuggestion]);

  // Close suggestions when clicking outside
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

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Search options
  const [enableFulltext, setEnableFulltext] = useState(true);
  const [enableLemmatic, setEnableLemmatic] = useState(true);
  const [enableSemantic, setEnableSemantic] = useState(true);
  const [enableAI, setEnableAI] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [resultsPerPage, setResultsPerPage] = useState(20);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setCurrentPage(1); // Reset to first page on new search

      // Check if at least one search mode is enabled
      if (!enableFulltext && !enableLemmatic && !enableSemantic) {
        setError('Please select at least one search mode');
        return;
      }

      // Fetch all results (high limit) - pagination is handled on frontend
      const response = await apiClient.hybridSearch({
        query: query.trim(),
        limit: 1000, // Fetch all results
        enable_fulltext: enableFulltext,
        enable_lemmatic: enableLemmatic,
        enable_semantic: enableSemantic,
        enable_ai_enhancements: enableAI,
      });

      setResults(response);
    } catch (err: unknown) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getAllResults = () => {
    if (!results) return [];
    // Only combined results are available now (optimized backend)
    return results.combined_results || [];
  };

  // Get paginated results for current page
  const getPaginatedResults = () => {
    const allResults = getAllResults();
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    return allResults.slice(startIndex, endIndex);
  };

  // Calculate total pages
  const totalPages = Math.ceil(getAllResults().length / resultsPerPage);

  // Handle page change
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      // Scroll to top of results
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <>
      {/* Empty state with Aurora background */}
      {!results && !loading && (
        <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
          <motion.div
            initial={{ opacity: 0.0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{
              delay: 0.3,
              duration: 0.8,
              ease: "easeInOut",
            }}
            className="relative flex flex-col gap-8 items-center justify-center px-4 w-full max-w-4xl z-10"
          >
            {/* Title with typewriter effect */}
            <div className="text-center">
              <h1 className="text-5xl md:text-7xl font-bold dark:text-white text-black mb-4">
                <Typewriter
                  text={["Hybrid", "Textual", "Lemmatic", "Semantic"]}
                  speed={120}
                  waitTime={3000}
                  deleteSpeed={70}
                  className="dark:text-white text-black"
                  cursorChar="_"
                />
                {" Search"}
              </h1>
              <p className="text-lg md:text-xl dark:text-neutral-300 text-neutral-600">
                {t('search.subtitle')}
              </p>
            </div>

            {/* Help Button */}
            <button
              onClick={() => setShowGuideModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/60 dark:bg-black/40 backdrop-blur-md text-black dark:text-white rounded-full text-sm hover:bg-white dark:hover:bg-black border border-neutral-200 dark:border-neutral-800 hover:shadow-lg transition-all"
              title="Open search guide"
            >
              <HelpCircle className="w-5 h-5" />
              <span className="hidden sm:inline">Search Guide</span>
            </button>

            {/* Search form */}
            <form onSubmit={handleSearch} className="space-y-4">
              {/* Main search input - thin pill design with autocomplete */}
              <div className="relative">
                <ShineBorder
                  className="!p-0 bg-white/95 backdrop-blur-sm"
                  borderRadius={9999}
                  color={["#60A5FA", "#3B82F6", "#93C5FD"]}
                >
                  <div className="flex gap-3 p-2">
                    <div className="relative flex-1">
                      <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => handleQueryChange(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                        placeholder="Type Greek/Latin or transliteration (boul = βούλομαι)..."
                        className="w-full px-6 py-3 text-base bg-transparent border-0 focus:outline-none focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-50 transition-all text-black dark:text-white placeholder-neutral-400"
                        data-no-ring="true"
                        autoFocus
                        autoComplete="off"
                        disabled={loading}
                      />
                      {autocompleteLoading && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                        </div>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={!query.trim() || loading}
                      className="px-8 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base font-medium whitespace-nowrap"
                    >
                      {loading ? 'Searching...' : 'Search'}
                    </button>
                  </div>
                </ShineBorder>

                {/* Autocomplete Dropdown */}
                <AnimatePresence>
                  {showSuggestions && suggestions.length > 0 && (
                    <motion.div
                      ref={suggestionsRef}
                      initial={{ opacity: 0, y: -8, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.98 }}
                      transition={{ duration: 0.15, ease: 'easeOut' }}
                      className="absolute z-50 w-full mt-2 bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-2xl overflow-hidden"
                    >
                      <div className="p-1">
                        {suggestions.map((suggestion, index) => {
                          const posColor = POS_COLORS[suggestion.pos] || { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400' };
                          return (
                            <div
                              key={`${suggestion.lemma}-${index}`}
                              className={`flex items-center gap-1 px-2 py-1 rounded-xl transition-all ${
                                selectedIndex === index
                                  ? 'bg-blue-50 dark:bg-blue-900/30'
                                  : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                              }`}
                            >
                              <button
                                type="button"
                                onClick={() => selectSuggestion(suggestion)}
                                className="flex-1 flex items-center gap-3 px-2 py-2 rounded-lg text-left"
                              >
                                {/* Greek lemma */}
                                <span className="text-lg font-medium text-black dark:text-white min-w-[120px]">
                                  {suggestion.lemma}
                                </span>

                                {/* Latin transliteration */}
                                <span className="text-sm text-neutral-500 dark:text-neutral-400 font-mono min-w-[100px]">
                                  {suggestion.lemma_latin}
                                </span>

                                {/* POS tag */}
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${posColor.bg} ${posColor.text}`}>
                                  {suggestion.pos}
                                </span>

                                {/* Occurrence count */}
                                <span className="ml-auto text-xs text-neutral-400 dark:text-neutral-500">
                                  {suggestion.count.toLocaleString()} occ.
                                </span>

                                {/* Passage count */}
                                <span className="text-xs text-neutral-400 dark:text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full">
                                  {suggestion.passage_count} passages
                                </span>
                              </button>

                              {/* Lemma Intelligence button */}
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
                                className="p-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 text-neutral-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                title="Lemma Intelligence: Dictionary, Statistics, Related words"
                              >
                                <Sparkles className="w-4 h-4" />
                              </button>
                            </div>
                          );
                        })}
                      </div>

                      {/* Show more button */}
                      {hasMoreSuggestions && (
                        <div className="px-4 py-2 border-t border-neutral-200 dark:border-neutral-700">
                          <button
                            type="button"
                            onClick={loadMoreSuggestions}
                            disabled={loadingMore}
                            className="w-full flex items-center justify-center gap-2 py-2 px-4 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all disabled:opacity-50"
                          >
                            {loadingMore ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Loading...
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-4 h-4" />
                                Show more results
                              </>
                            )}
                          </button>
                        </div>
                      )}

                      {/* Hint footer */}
                      <div className="px-4 py-2 bg-neutral-50 dark:bg-neutral-800/50 border-t border-neutral-200 dark:border-neutral-700">
                        <p className="text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-4">
                          <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600 text-[10px]">↑↓</kbd> navigate</span>
                          <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600 text-[10px]">Enter</kbd> select</span>
                          <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-neutral-700 rounded border border-neutral-300 dark:border-neutral-600 text-[10px]">Esc</kbd> close</span>
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Options - outside the main input */}
              <div className="space-y-3 px-2">
                {/* Search modes */}
                <div className="flex justify-center">
                  <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-sm bg-white/60 dark:bg-black/40 backdrop-blur-md px-4 sm:px-6 py-3 rounded-2xl sm:rounded-full border border-neutral-200 dark:border-neutral-800">
                    <span className="dark:text-neutral-300 text-neutral-700 font-medium w-full sm:w-auto text-center sm:text-left">Modes:</span>
                    <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2">
                      <input
                        type="checkbox"
                        checked={enableFulltext}
                        onChange={(e) => setEnableFulltext(e.target.checked)}
                        className="w-5 h-5 sm:w-4 sm:h-4 text-blue-600 bg-white dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="dark:text-neutral-300 text-neutral-700">Full-text</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2">
                      <input
                        type="checkbox"
                        checked={enableLemmatic}
                        onChange={(e) => setEnableLemmatic(e.target.checked)}
                        className="w-5 h-5 sm:w-4 sm:h-4 text-blue-600 bg-white dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="dark:text-neutral-300 text-neutral-700">Lemmatic</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer min-h-[44px] px-2">
                      <input
                        type="checkbox"
                        checked={enableSemantic}
                        onChange={(e) => setEnableSemantic(e.target.checked)}
                        className="w-5 h-5 sm:w-4 sm:h-4 text-blue-600 bg-white dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="dark:text-neutral-300 text-neutral-700">Semantic</span>
                    </label>
                    <div className="hidden sm:block w-px h-4 bg-neutral-300 dark:bg-neutral-700 mx-2"></div>
                    <label className={`flex items-center gap-2 cursor-pointer px-3 py-1 rounded-full transition-all min-h-[44px] ${enableAI ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'text-neutral-500 dark:text-neutral-400'}`}>
                      <input
                        type="checkbox"
                        checked={enableAI}
                        onChange={(e) => setEnableAI(e.target.checked)}
                        className="w-5 h-5 sm:w-4 sm:h-4 text-blue-600 bg-white dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="font-medium text-sm">✨ AI</span>
                    </label>
                  </div>
                </div>

                {/* RRF indicator */}
                <div className="flex flex-wrap justify-center items-center gap-2 sm:gap-4">
                  {[enableFulltext, enableLemmatic, enableSemantic].filter(Boolean).length >= 2 && (
                    <span className="text-xs text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/30 px-3 py-1 rounded-full border border-blue-200 dark:border-blue-800">
                      RRF enabled
                    </span>
                  )}
                </div>
              </div>
            </form>

            {/* Error message */}
            {error && (
              <div className="mt-6 px-6 py-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-700 dark:text-red-300 rounded-2xl text-sm text-center backdrop-blur-sm">
                {error}
              </div>
            )}

            {/* Help tips */}
            <div className="mt-8 text-center">
              <p className="text-sm dark:text-neutral-400 text-neutral-600 mb-3">Try searching for:</p>
              <div className="flex flex-wrap justify-center gap-2">
                <button
                  onClick={() => setQuery('ἐφ\' ἡμῖν')}
                  className="px-4 py-2 bg-white/60 dark:bg-black/40 backdrop-blur-md text-black dark:text-white rounded-full text-sm hover:bg-white dark:hover:bg-black border border-neutral-200 dark:border-neutral-800 hover:shadow-lg transition-all"
                >
                  ἐφ' ἡμῖν
                </button>
                <button
                  onClick={() => setQuery('liberum arbitrium')}
                  className="px-4 py-2 bg-white/60 dark:bg-black/40 backdrop-blur-md text-black dark:text-white rounded-full text-sm hover:bg-white dark:hover:bg-black border border-neutral-200 dark:border-neutral-800 hover:shadow-lg transition-all"
                >
                  liberum arbitrium
                </button>
                <button
                  onClick={() => setQuery('voluntary action')}
                  className="px-4 py-2 bg-white/60 dark:bg-black/40 backdrop-blur-md text-black dark:text-white rounded-full text-sm hover:bg-white dark:hover:bg-black border border-neutral-200 dark:border-neutral-800 hover:shadow-lg transition-all"
                >
                  voluntary action
                </button>
              </div>
            </div>
          </motion.div>
        </AuroraBackground>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center min-h-screen bg-white dark:bg-black">
          <div className="inline-block w-12 h-12 border-3 border-neutral-200 dark:border-neutral-800 border-t-blue-600 dark:border-t-blue-400 rounded-full animate-spin mb-4"></div>
          <p className="dark:text-neutral-300 text-neutral-700 text-lg">{t('search.loadingMessage')}</p>
        </div>
      )}

      {/* Results view */}
      {results && !loading && (
        <div className="min-h-screen bg-white dark:bg-black pb-32">
          {/* Pagination header */}
          {getAllResults().length > 0 && (
            <div className="sticky top-16 z-30 bg-white/80 dark:bg-black/80 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-800">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                <div className="flex items-center justify-between">
                  {/* Results info */}
                  <div className="flex items-center gap-4">
                    <span className="text-sm dark:text-neutral-300 text-neutral-700">
                      {getAllResults().length} results
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm dark:text-neutral-400 text-neutral-600">Show:</span>
                      <select
                        value={resultsPerPage}
                        onChange={(e) => {
                          setResultsPerPage(Number(e.target.value));
                          setCurrentPage(1);
                        }}
                        className="px-2 py-1 text-sm border border-neutral-300 dark:border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-neutral-900 text-black dark:text-white"
                      >
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                    </div>
                  </div>

                  {/* Pagination controls */}
                  {totalPages > 1 && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        title="Previous page"
                      >
                        <ChevronLeft className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                      </button>
                      <span className="text-sm dark:text-neutral-300 text-neutral-700 min-w-[80px] text-center">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        title="Next page"
                      >
                        <ChevronRight className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Results list */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-4">
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="space-y-4"
            >
              {getPaginatedResults().length > 0 ? (
                getPaginatedResults().map((result, index) => (
                  <SearchResultCard
                    key={result.id || `result-${index}`}
                    result={result}
                    index={(currentPage - 1) * resultsPerPage + index}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <p className="dark:text-neutral-400 text-neutral-600">{t('search.noResultsTitle')}</p>
                  <p className="text-sm dark:text-neutral-500 text-neutral-500 mt-1">{t('search.noResultsDesc')}</p>
                </div>
              )}
            </motion.div>

            {/* Bottom pagination */}
            {totalPages > 1 && getPaginatedResults().length > 0 && (
              <div className="flex justify-center mt-8">
                <div className="flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-2">
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                  </button>
                  <span className="text-sm dark:text-neutral-300 text-neutral-700 px-4">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sticky search footer at bottom */}
          <div className="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-black/80 backdrop-blur-xl border-t border-neutral-200 dark:border-neutral-800 z-40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center gap-4">
                {/* Compact search input */}
                <div className="flex-1">
                  <ShineBorder
                    className="w-full !p-0 bg-white dark:bg-neutral-900"
                    borderRadius={12}
                    color={["#60A5FA", "#3B82F6", "#93C5FD"]}
                  >
                    <form onSubmit={handleSearch} className="flex gap-2 p-1.5">
                      <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search..."
                        className="flex-1 px-4 py-2 text-sm bg-transparent border-0 focus:outline-none focus:ring-0 text-black dark:text-white placeholder-neutral-400"
                      />
                      <button
                        type="submit"
                        disabled={!query.trim()}
                        className="px-6 py-2 bg-black dark:bg-white text-white dark:text-black rounded-xl hover:bg-neutral-800 dark:hover:bg-neutral-100 disabled:opacity-50 text-sm font-semibold transition-all"
                      >
                        Search
                      </button>
                    </form>
                  </ShineBorder>
                </div>

                {/* Result count and mode info */}
                <div className="flex items-center gap-2">
                  <span className="text-sm dark:text-neutral-300 text-neutral-700 whitespace-nowrap">
                    {t('search.foundResults', { count: results.totalResults || results.combined_results?.length || 0 })}
                  </span>
                  {results.used_rrf && (
                    <span className="text-xs text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded-full border border-blue-200 dark:border-blue-800">
                      RRF
                    </span>
                  )}
                  {results.citation_match && (
                     <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full border border-blue-200 dark:border-blue-800 font-medium">
                       📌 {results.citation_match}
                     </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Guide Modal */}
      <SearchGuideModal
        isOpen={showGuideModal}
        onClose={() => setShowGuideModal(false)}
      />

      {/* Lemma Intelligence Panel */}
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

// Helper function to format full reference
function formatFullReference(result: SearchResult): string {
  // Format: "Author, Work Book:Chapter:Section"
  const parts = [result.author, result.title];

  // Build location string from book/chapter/section
  const locationParts: string[] = [];
  if (result.book) locationParts.push(result.book);
  if (result.chapter) locationParts.push(result.chapter);
  if (result.section) locationParts.push(result.section);

  const location = locationParts.join(':');

  if (location) {
    return `${parts.join(', ')} ${location}`;
  }

  // Fallback to canonical_ref if available
  if (result.canonical_ref) {
    return `${result.author}, ${result.title} ${result.canonical_ref}`;
  }

  return `${result.author}, ${result.title}`;
}

// Search Result Card Component
function SearchResultCard({ result, index }: { result: SearchResult; index: number }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleViewText = () => {
    if (result.work_id) {
      const url = result.passage_id
        ? `/texts/${result.work_id}?passage=${result.passage_id}`
        : `/texts/${result.work_id}`;
      navigate(url);
    }
  };

  return (
    <motion.div variants={staggerItem}>
      <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-xl transition-all cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            {/* Result Number & Title */}
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 text-sm font-semibold text-blue-600 dark:text-blue-400">
                #{index + 1}
              </span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold dark:text-white text-black mb-2">
                  {formatFullReference(result)}
                </h3>

                {/* Metadata */}
                <div className="flex flex-wrap gap-3 text-sm dark:text-neutral-400 text-neutral-600 mb-3">
                  {result.category && (
                    <span>
                      <strong className="dark:text-neutral-200 text-neutral-800">{t('search.category')}:</strong> {result.category}
                    </span>
                  )}
                  {result.language && (
                    <>
                      {result.category && <span>•</span>}
                      <span>
                        <strong className="dark:text-neutral-200 text-neutral-800">{t('search.language')}:</strong> {result.language}
                      </span>
                    </>
                  )}
                  {result.source && (
                    <>
                      {(result.category || result.language) && <span>•</span>}
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        result.source.includes('citation')
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium border border-blue-200 dark:border-blue-800'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
                      }`}>
                        {result.source.includes('citation') ? '📌 Citation Match' : result.source}
                      </span>
                    </>
                  )}
                </div>

                {/* Text content preview */}
                {result.text_content && !result.snippet && (
                  <div className="text-sm dark:text-neutral-300 text-neutral-700 bg-neutral-50 dark:bg-neutral-800 border-l-4 border-neutral-300 dark:border-neutral-700 p-3 mt-2 rounded line-clamp-3">
                    {result.text_content.substring(0, 300)}...
                  </div>
                )}

                {/* Snippet (with highlighting) */}
                {result.snippet && (
                  <div
                    className="text-sm dark:text-neutral-300 text-neutral-700 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 dark:border-blue-400 p-3 mt-2 rounded"
                    dangerouslySetInnerHTML={{ __html: result.snippet }}
                  />
                )}

                {/* Scores */}
                <div className="flex gap-4 mt-3 text-xs">
                  {result.rrf_score !== undefined && (
                    <span className="text-blue-600 dark:text-blue-400 font-medium">
                      RRF Score: {result.rrf_score.toFixed(4)}
                    </span>
                  )}
                  {(result as any).reranker_score !== undefined && (
                    <span className="text-indigo-600 dark:text-indigo-400 font-medium">
                      ✨ AI Score: {(result as any).reranker_score.toFixed(4)}
                    </span>
                  )}
                  {result.rank !== undefined && (
                    <span className="dark:text-neutral-500 text-neutral-500">
                      Rank: {result.rank.toFixed(4)}
                    </span>
                  )}
                  {result.canonical_ref && (
                    <span className="dark:text-neutral-500 text-neutral-500">
                      Ref: {result.canonical_ref}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* View Button */}
          <button
            onClick={handleViewText}
            disabled={!result.work_id}
            className="shrink-0 px-4 py-2 text-sm font-medium text-black dark:text-white bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 border border-neutral-200 dark:border-neutral-700 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('search.viewText')}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
