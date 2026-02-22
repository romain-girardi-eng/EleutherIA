import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { AILoader } from '../components/ui/ai-loader';
import type { AncientWork, WorksStats, FeaturedWork, AuthorStats } from '../types/index';

const LANGUAGE_FILTER_MAP: Record<string, string> = {
  Greek: 'grc',
  Latin: 'lat',
  English: 'eng',
};

const LANGUAGE_LABELS: Record<string, string> = {
  grc: 'Ancient Greek',
  lat: 'Latin',
  eng: 'English',
};

export default function TextExplorerPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [works, setWorks] = useState<AncientWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<WorksStats | null>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [authorFilter, setAuthorFilter] = useState<string>('');
  const [languageFilter, setLanguageFilter] = useState<string>('');
  const [featuredWorksFilter, setFeaturedWorksFilter] = useState<boolean>(true); // DEFAULT: show featured
  const [sortBy, setSortBy] = useState<string>('most_cited'); // DEFAULT: most cited (by KG nodes)

  // Pagination
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState<number | 'all'>('all');
  const [totalCount, setTotalCount] = useState(0);

  const loadWorks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // If featured works filter is active and we have the data
      if (featuredWorksFilter && stats?.featured_works && stats.featured_works.length > 0) {
        const featuredWorkIds = stats.featured_works.map((fw: FeaturedWork) => fw.work_id);

        // Fetch all featured works individually
        const featuredWorks = [];
        for (const workId of featuredWorkIds) {
          try {
            const work = await apiClient.getWork(workId);
            featuredWorks.push(work);
          } catch (err) {
            console.error(`Error loading work ${workId}:`, err);
          }
        }

        setWorks(featuredWorks);
        setTotalCount(featuredWorks.length);
      } else {
        // Regular filtering
        const filters: Record<string, string | number | boolean> = {};
        const isPaginated = pageSize !== 'all';
        const limitValue = isPaginated ? pageSize : 500;

        filters.offset = isPaginated ? offset : 0;
        filters.limit = limitValue;

        if (categoryFilter) {
          filters.author = categoryFilter;
        }
        if (authorFilter) {
          filters.search = authorFilter;
        }
        if (languageFilter) {
          filters.language = LANGUAGE_FILTER_MAP[languageFilter] ?? languageFilter;
        }
        if (sortBy) {
          filters.sort_by = sortBy;
        }

        const response = await apiClient.listWorks(filters);
        setWorks(response.works || []);
        setTotalCount(response.total || 0);
      }
    } catch (err: unknown) {
      console.error('Error loading works:', err);
      setError(err instanceof Error ? err.message : 'Failed to load works');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, authorFilter, languageFilter, featuredWorksFilter, sortBy, offset, pageSize, stats]);

  useEffect(() => {
    loadWorks();
    loadStats();
  }, [loadWorks]);

  const loadStats = async () => {
    try {
      const statsData = await apiClient.getWorksStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const resetFilters = () => {
    setCategoryFilter('');
    setAuthorFilter('');
    setLanguageFilter('');
    setFeaturedWorksFilter(true); // Reset to default: show featured
    setSortBy('most_cited'); // Reset to default: most cited
    setOffset(0);
  };

  const hasPagination = pageSize !== 'all';
  const numericPageSize = typeof pageSize === 'number' ? pageSize : 0;

  const nextPage = () => {
    if (!hasPagination) {
      return;
    }
    if (offset + numericPageSize < totalCount) {
      setOffset(offset + numericPageSize);
    }
  };

  const prevPage = () => {
    if (!hasPagination) {
      return;
    }
    if (offset >= numericPageSize) {
      setOffset(offset - numericPageSize);
    }
  };

  const showingFrom = totalCount === 0 ? 0 : hasPagination ? offset + 1 : 1;
  const showingTo = hasPagination ? Math.min(offset + numericPageSize, totalCount) : totalCount;

  return (
    <div className="min-h-screen w-full pt-20 pb-12 bg-transparent">
      <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* TEST: Confirm new code is loaded */}
      <div style={{ backgroundColor: 'red', color: 'white', padding: '20px', fontSize: '24px', fontWeight: 'bold', textAlign: 'center' }}>
        ✅ NEW VERSION LOADED - UPDATED CODE IS RUNNING
      </div>

      {/* Header */}
      <div className="academic-card">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-serif font-display font-bold mb-2">{t('texts.title')}</h1>
              <p className="text-academic-muted">
                {t('texts.subtitle', { count: stats?.total_works || 0 })}
              </p>
            </div>

            {stats && (
              <div className="flex space-x-6 text-center">
                <div>
                  <div className="text-2xl font-bold text-primary-600">
                    {stats.total_works?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-academic-muted">{t('texts.totalWorks', { count: stats.total_works || 0 }).split(' ')[1]}</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-primary-600">
                    {stats.total_passages?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-academic-muted">{t('texts.passages')}</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-primary-600">
                    {stats.total_citations?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-academic-muted">{t('texts.citations')}</div>
                </div>
              </div>
            )}
          </div>
        </div>

      {/* Featured Works Info Banner */}
      {featuredWorksFilter && (
        <div className="academic-card bg-primary-50 border-primary-200">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⭐</span>
            <div>
              <h3 className="font-semibold text-primary-900 mb-1">⭐ Featured Works - Most Cited in Knowledge Graph</h3>
              <p className="text-sm text-primary-800">
                These are the most important works for free will research, selected based on how many unique
                knowledge graph nodes cite them. <strong>{stats?.featured_works?.length || 0} featured works</strong> shown.
              </p>
              <button
                onClick={() => setFeaturedWorksFilter(false)}
                className="text-sm text-primary-600 hover:text-primary-800 underline mt-1 font-medium"
              >
                {t('texts.browseWorks')} {stats?.total_works || 0} works instead →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="academic-card">
        <h3 className="font-semibold mb-3">Filter & Sort Texts</h3>
        <div className="space-y-4">
          {/* First Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Top Authors Filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('texts.byAuthor')}</label>
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{t('texts.allAuthors')}</option>
                {stats?.top_authors?.map((author: AuthorStats) => (
                  <option key={author.author} value={author.author}>
                    {author.author} ({author.passage_count?.toLocaleString() || 0} passages)
                  </option>
                ))}
              </select>
            </div>

            {/* Author Search Filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('texts.searchAuthor')}</label>
              <input
                type="text"
                value={authorFilter}
                onChange={(e) => {
                  setAuthorFilter(e.target.value);
                  setOffset(0);
                }}
                placeholder="e.g., Aristotle, Paul..."
                className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Language Filter */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('common.language')}</label>
              <select
                value={languageFilter}
                onChange={(e) => {
                  setLanguageFilter(e.target.value);
                  setOffset(0);
                }}
                className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">{t('texts.allLanguages')}</option>
                <option value="Greek">{t('texts.greek')}</option>
                <option value="Latin">{t('texts.latin')}</option>
                <option value="English">{t('texts.english')}</option>
              </select>
            </div>

            {/* Featured Works Toggle */}
            <div>
              <label className="block text-sm font-medium mb-1">
                {t('texts.featured')} ⭐
              </label>
              <button
                onClick={() => {
                  setFeaturedWorksFilter(!featuredWorksFilter);
                  setOffset(0);
                }}
                className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors ${
                  featuredWorksFilter
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-academic-text border-academic-border hover:bg-academic-muted'
                }`}
                title="Works most cited in the free will knowledge graph"
              >
                {featuredWorksFilter ? '✓ ' : ''}{t('texts.featured')}
              </button>
            </div>
          </div>

          {/* Second Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium mb-1">{t('common.sort')}</label>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setOffset(0);
                }}
                className="w-full px-3 py-2 border border-academic-border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="most_cited">⭐ {t('texts.mostCited')}</option>
                <option value="author">{t('texts.byAuthor')}</option>
                <option value="title">{t('texts.byTitle')}</option>
                <option value="passages_desc">{t('texts.mostPassages')}</option>
                <option value="passages_asc">Fewest Passages</option>
              </select>
            </div>

            {/* Spacer */}
            <div></div>
            <div></div>

            {/* Reset Button */}
            <div className="flex items-end">
              <button onClick={resetFilters} className="academic-button-outline w-full">
                {t('texts.reset')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="academic-card bg-red-50 border-red-200 text-red-800">
          <p className="font-medium">Error: {error}</p>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="academic-card text-center py-12">
          <AILoader text="Loading" size="lg" />
          <p className="text-academic-muted mt-6">{t('texts.loadingWorks')}</p>
        </div>
      ) : (
        <>
          {/* Pagination Info */}
          <div className="academic-card">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-academic-muted">
                {totalCount > 0
                  ? `Showing ${showingFrom} - ${showingTo} of ${totalCount} works`
                  : 'No works to display'}
              </p>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:space-x-3">
                <div className="flex items-center space-x-2">
                  <label htmlFor="page-size" className="text-sm text-academic-muted">
                    Results per page
                  </label>
                  <select
                    id="page-size"
                    value={pageSize === 'all' ? 'all' : String(pageSize)}
                    onChange={(event) => {
                      const value = event.target.value;
                      setOffset(0);
                      if (value === 'all') {
                        setPageSize('all');
                      } else {
                        setPageSize(Number(value));
                      }
                    }}
                    className="rounded-md border border-academic-border bg-academic-paper px-3 py-1.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                  >
                    <option value="all">All</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                </div>
                {hasPagination && (
                  <div className="flex space-x-2">
                    <button
                      onClick={prevPage}
                      disabled={!hasPagination || offset === 0}
                      className="academic-button-outline disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ← Previous
                    </button>
                    <button
                      onClick={nextPage}
                      disabled={!hasPagination || offset + numericPageSize >= totalCount}
                      className="academic-button-outline disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Works Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {works.map((work) => (
              <TextCard
                key={work.work_id}
                work={work}
                onClick={() => {
                  const targetId = work.work_id;
                  if (targetId) {
                    navigate(`/texts/${targetId}`);
                  }
                }}
              />
            ))}
          </div>

          {works.length === 0 && (
            <div className="academic-card text-center py-12">
              <p className="text-academic-muted">{t('texts.noWorksFound')}</p>
            </div>
          )}
        </>
      )}

      </div>
    </div>
  );
}

// Work Card Component
function TextCard({ work, onClick }: { work: AncientWork; onClick: () => void }) {
  const { t } = useTranslation();
  const languageLabel =
    LANGUAGE_LABELS[work.language] ??
    (work.language ? work.language.charAt(0).toUpperCase() + work.language.slice(1) : 'Unknown');

  return (
    <div
      onClick={onClick}
      className="academic-card hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold line-clamp-2 flex-1">{work.title}</h3>
        {(work.kg_citations ?? 0) > 0 && (
          <span
            className="ml-2 px-2 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold flex-shrink-0"
            title={`Cited in ${work.kg_citations} knowledge graph node${(work.kg_citations ?? 0) > 1 ? 's' : ''}`}
          >
            ⭐ {work.kg_citations}
          </span>
        )}
      </div>

      <div className="space-y-1 text-sm text-academic-muted mb-3">
        <div>
          <strong>{t('texts.authorLabel')}</strong> {work.author}
        </div>
        <div>
          <strong>{t('common.language')}:</strong> {languageLabel}
        </div>
        <div>
          <strong>{t('texts.passagesLabel')}</strong> {work.passage_count?.toLocaleString() ?? '—'}
        </div>
        {(work.kg_citations ?? 0) > 0 && (
          <div className="text-primary-700 font-medium">
            <strong>{t('texts.citations')}:</strong> {work.kg_citations} node{(work.kg_citations ?? 0) > 1 ? 's' : ''}
          </div>
        )}
        {work.period && (
          <div>
            <strong>{t('texts.periodLabel')}</strong> {work.period}
          </div>
        )}
        {work.source && (
          <div>
            <strong>Source:</strong> {work.source.toUpperCase()}
          </div>
        )}
      </div>
      <p className="text-xs text-academic-muted">
        Canonical ID: <span className="font-mono">{work.canonical_id}</span>
      </p>
    </div>
  );
}
