import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { useDebounce } from '../hooks/useDebounce';
import { useKeyboardShortcut, formatShortcut } from '../hooks/useKeyboardShortcut';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/button';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { staggerContainer, staggerItem } from '../utils/animations';
import { AuroraBackground } from '../components/ui/aurora-background';

interface SearchFilters {
  author?: string;
  language?: string;
  period?: string;
  workId?: string;
}

interface PassageSearchResult {
  passage_id: string;
  work_id: string;
  canonical_ref: string;
  text_content: string;
  work_title: string;
  author: string;
  language: string;
  rank: number;
}

export default function AdvancedSearchPage() {
  const { t } = useTranslation();

  // Search state
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<PassageSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [selectedResult, setSelectedResult] = useState<number>(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Debounced query for real-time search
  const debouncedQuery = useDebounce(query, 300);

  // Keyboard shortcuts
  useKeyboardShortcut(
    { key: '/', ctrl: true },
    () => searchInputRef.current?.focus()
  );

  useKeyboardShortcut(
    { key: 'f', ctrl: true },
    () => setShowFilters(!showFilters)
  );

  useKeyboardShortcut(
    { key: 'ArrowDown' },
    () => setSelectedResult(prev => Math.min(prev + 1, results.length - 1)),
    results.length > 0
  );

  useKeyboardShortcut(
    { key: 'ArrowUp' },
    () => setSelectedResult(prev => Math.max(prev - 1, -1)),
    results.length > 0
  );

  useKeyboardShortcut(
    { key: 'Enter' },
    () => {
      if (selectedResult >= 0 && results[selectedResult]) {
        handleViewPassage(results[selectedResult]);
      }
    },
    selectedResult >= 0
  );

  // Perform search when debounced query or filters change
  useEffect(() => {
    if (debouncedQuery.trim().length < 2) {
      setResults([]);
      return;
    }

    performSearch(debouncedQuery, filters);
  }, [debouncedQuery, filters]);

  const performSearch = async (searchQuery: string, searchFilters: SearchFilters) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.searchWorks(searchQuery, {
        author: searchFilters.author,
        language: searchFilters.language,
        limit: 50
      });

      setResults(response.results || []);
      setSelectedResult(-1);
    } catch (err: unknown) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPassage = (result: PassageSearchResult) => {
    // Navigate to text reader
    window.location.href = `/texts/${result.work_id}#${result.canonical_ref}`;
  };

  const clearFilters = () => {
    setFilters({});
  };

  const hasActiveFilters = Object.values(filters).some(v => v);

  return (
    <AuroraBackground className="!min-h-screen !h-auto py-12">
      <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* Header */}
      <Card variant="default" padding="lg">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl">{t('advancedSearch.title')}</CardTitle>
              <CardDescription>
                {t('advancedSearch.subtitle')}
              </CardDescription>
            </div>

            {/* Keyboard Shortcuts Info */}
            <div className="text-xs text-academic-muted space-y-1 text-right">
              <div><kbd className="kbd">{formatShortcut({ key: '/', ctrl: true })}</kbd> {t('advancedSearch.shortcuts.focusSearch')}</div>
              <div><kbd className="kbd">{formatShortcut({ key: 'f', ctrl: true })}</kbd> {t('advancedSearch.shortcuts.toggleFilters')}</div>
              <div><kbd className="kbd">↑↓</kbd> {t('advancedSearch.shortcuts.navigateResults')}</div>
              <div><kbd className="kbd">Enter</kbd> {t('advancedSearch.shortcuts.openSelected')}</div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Search Input */}
      <Card variant="default" padding="lg">
        <div className="space-y-4">
          <div className="relative">
            <Input
              ref={searchInputRef}
              id="search-query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('advancedSearch.searchPlaceholder')}
              label={t('advancedSearch.searchLabel')}
              fullWidth
              autoFocus
            />

            {/* Real-time indicator */}
            {loading && (
              <div className="absolute right-3 top-10">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
              </div>
            )}

            {/* Search stats */}
            {!loading && results.length > 0 && (
              <div className="absolute right-3 top-10 text-sm text-academic-muted">
                {t('advancedSearch.resultsCount', { count: results.length })}
              </div>
            )}
          </div>

          {/* Filter Toggle */}
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              {t('advancedSearch.filters.button')} {hasActiveFilters && `(${Object.values(filters).filter(v => v).length})`}
            </Button>

            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
              >
                {t('advancedSearch.filters.clearAll')}
              </Button>
            )}
          </div>

          {/* Filters Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-academic-bg-secondary rounded-lg border border-academic-border"
              >
                {/* Author Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t('advancedSearch.filters.author')}</label>
                  <Input
                    id="filter-author"
                    type="text"
                    value={filters.author || ''}
                    onChange={(e) => setFilters({ ...filters, author: e.target.value })}
                    placeholder={t('advancedSearch.filters.authorPlaceholder')}
                  />
                </div>

                {/* Language Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t('advancedSearch.filters.language')}</label>
                  <select
                    value={filters.language || ''}
                    onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                    className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    <option value="">{t('advancedSearch.filters.languageOptions.all')}</option>
                    <option value="grc">{t('advancedSearch.filters.languageOptions.greek')}</option>
                    <option value="lat">{t('advancedSearch.filters.languageOptions.latin')}</option>
                    <option value="eng">{t('advancedSearch.filters.languageOptions.english')}</option>
                  </select>
                </div>

                {/* Period Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t('advancedSearch.filters.period')}</label>
                  <select
                    value={filters.period || ''}
                    onChange={(e) => setFilters({ ...filters, period: e.target.value })}
                    className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  >
                    <option value="">{t('advancedSearch.filters.periodOptions.all')}</option>
                    <option value="Presocratic">{t('advancedSearch.filters.periodOptions.presocratic')}</option>
                    <option value="Classical Greek">{t('advancedSearch.filters.periodOptions.classical')}</option>
                    <option value="Hellenistic">{t('advancedSearch.filters.periodOptions.hellenistic')}</option>
                    <option value="Roman Republican">Roman Republican</option>
                    <option value="Roman Imperial">{t('advancedSearch.filters.periodOptions.romanImperial')}</option>
                    <option value="Patristic">Patristic</option>
                    <option value="Late Antiquity">{t('advancedSearch.filters.periodOptions.lateAntiquity')}</option>
                    <option value="Second Temple Judaism">Second Temple Judaism</option>
                    <option value="Contemporary">Contemporary</option>
                  </select>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <ErrorState
          title={t('advancedSearch.error.title')}
          description={error}
          onRetry={() => performSearch(query, filters)}
        />
      )}

      {/* Empty state */}
      {!loading && query.trim().length < 2 && results.length === 0 && (
        <Card variant="default" padding="lg" className="bg-primary-50 border-primary-200">
          <CardHeader>
            <CardTitle className="text-lg">{t('advancedSearch.howToSearch.title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-academic-text space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">→</span>
                <span dangerouslySetInnerHTML={{ __html: t('advancedSearch.howToSearch.greek') }} />
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">→</span>
                <span dangerouslySetInnerHTML={{ __html: t('advancedSearch.howToSearch.latin') }} />
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">→</span>
                <span dangerouslySetInnerHTML={{ __html: t('advancedSearch.howToSearch.english') }} />
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">→</span>
                <span dangerouslySetInnerHTML={{ __html: t('advancedSearch.howToSearch.realtime') }} />
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-600 font-bold">→</span>
                <span dangerouslySetInnerHTML={{ __html: t('advancedSearch.howToSearch.filters') }} />
              </li>
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-3"
        >
          {results.map((result, index) => (
            <motion.div
              key={result.passage_id}
              variants={staggerItem}
              onMouseEnter={() => setSelectedResult(index)}
            >
              <Card
                variant="default"
                padding="md"
                interactive
                className={`transition-all ${
                  selectedResult === index
                    ? 'border-primary-500 bg-primary-50 shadow-md'
                    : 'hover:border-primary-300'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Rank Badge */}
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      selectedResult === index
                        ? 'bg-primary-600 text-white'
                        : 'bg-academic-bg-secondary text-academic-muted'
                    }`}>
                      {index + 1}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {/* Work & Author */}
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-academic-text">
                          {result.author}, <em>{result.work_title}</em> {result.canonical_ref}
                        </h3>
                        <div className="flex gap-3 text-xs text-academic-muted mt-1">
                          <span className="px-2 py-0.5 bg-academic-bg-secondary rounded">
                            {result.language === 'grc' ? t('advancedSearch.results.languageLabels.greek') : result.language === 'lat' ? t('advancedSearch.results.languageLabels.latin') : t('advancedSearch.results.languageLabels.english')}
                          </span>
                          <span>{t('advancedSearch.results.relevance', { percent: (result.rank * 100).toFixed(1) })}</span>
                        </div>
                      </div>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewPassage(result)}
                      >
                        {t('advancedSearch.results.viewButton')}
                      </Button>
                    </div>

                    {/* Text Content (truncated) */}
                    <div className="text-sm text-academic-text bg-white border-l-4 border-primary-200 p-3 rounded">
                      <p className="line-clamp-3">
                        {result.text_content.substring(0, 300)}
                        {result.text_content.length > 300 && '...'}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* No results */}
      {!loading && query.trim().length >= 2 && results.length === 0 && (
        <EmptyState
          title={t('advancedSearch.noResults.title')}
          description={t('advancedSearch.noResults.description', { query })}
        />
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <Card key={i} variant="default" padding="md">
              <div className="animate-pulse">
                <div className="h-4 bg-academic-bg-secondary rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-academic-bg-secondary rounded w-1/2 mb-3"></div>
                <div className="h-16 bg-academic-bg-secondary rounded"></div>
              </div>
            </Card>
          ))}
        </div>
      )}
      </div>
    </AuroraBackground>
  );
}
