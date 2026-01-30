import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import { cachedApiClient } from '../api/cachedClient';
import { KGNodeSelectionModal } from '../components/KGNodeSelectionModal';
import { AuroraBackground } from '../components/ui/aurora-background';
import { AILoader } from '../components/ui/ai-loader';
import type {
  WorkKGNodesResponse,
  AncientWork,
  WorksStats,
  FeaturedWork,
  AuthorStats,
  WorkKGNode
} from '../types/index';

const LANGUAGE_FILTER_MAP: Record<string, string> = {
  Greek: 'grc',
  Latin: 'lat',
  English: 'eng',
};

// Language labels (currently unused, kept for future use)
// const LANGUAGE_LABELS: Record<string, string> = {
//   grc: 'Ancient Greek',
//   lat: 'Latin',
//   eng: 'English',
// };

export default function TextExplorerPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [works, setWorks] = useState<AncientWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<WorksStats | null>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [authorFilter, setAuthorFilter] = useState<string>('');
  const [languageFilter, setLanguageFilter] = useState<string>('');
  const [featuredWorksFilter, setFeaturedWorksFilter] = useState<boolean>(true);
  const [sortBy, setSortBy] = useState<string>('most_cited');

  // Pagination
  const [offset, setOffset] = useState(0);
  const [pageSize, _setPageSize] = useState<number | 'all'>('all');
  const [totalCount, setTotalCount] = useState(0);

  // KG Node Modal
  const [showKGModal, setShowKGModal] = useState(false);
  const [selectedWorkKGData, setSelectedWorkKGData] = useState<WorkKGNodesResponse | null>(null);

  useEffect(() => {
    loadWorks();
    loadStats();
  }, [categoryFilter, authorFilter, languageFilter, featuredWorksFilter, sortBy, offset, pageSize]);

  const loadWorks = async () => {
    try {
      setLoading(true);
      setError(null);

      if (featuredWorksFilter && stats?.featured_works && stats.featured_works.length > 0) {
        const featuredWorkIds = stats.featured_works.map((fw: FeaturedWork) => fw.work_id);
        const featuredWorks = [];
        for (const workId of featuredWorkIds) {
          try {
            // Use cached API client for individual works
            const work = await cachedApiClient.getWork(workId);
            featuredWorks.push(work);
          } catch (err) {
            console.error(`Error loading work ${workId}:`, err);
          }
        }
        setWorks(featuredWorks as AncientWork[]);
        setTotalCount(featuredWorks.length);
      } else {
        const filters: Record<string, any> = {};
        const isPaginated = pageSize !== 'all';
        const limitValue = isPaginated ? pageSize : 500;

        filters.offset = isPaginated ? offset : 0;
        filters.limit = limitValue;

        if (categoryFilter) filters.author = categoryFilter;
        if (authorFilter) filters.search = authorFilter;
        if (languageFilter) filters.language = LANGUAGE_FILTER_MAP[languageFilter] ?? languageFilter;
        if (sortBy) filters.sort_by = sortBy;

        // Use cached API client for works list
        const response = await cachedApiClient.listWorks(filters);
        setWorks(response.works as AncientWork[] || []);
        setTotalCount(response.total || 0);
      }
    } catch (err: unknown) {
      console.error('Error loading works:', err);
      setError(err instanceof Error ? err.message : t('ancientWorks.errors.loadWorks'));
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      // Use cached API client for stats (cached for 24 hours)
      const statsData = await cachedApiClient.getWorksStats();
      setStats(statsData as WorksStats);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const resetFilters = () => {
    setCategoryFilter('');
    setAuthorFilter('');
    setLanguageFilter('');
    setFeaturedWorksFilter(true);
    setSortBy('most_cited');
    setOffset(0);
  };

  const hasPagination = pageSize !== 'all';
  const numericPageSize = typeof pageSize === 'number' ? pageSize : 0;

  const nextPage = () => {
    if (!hasPagination) return;
    if (offset + numericPageSize < totalCount) setOffset(offset + numericPageSize);
  };

  const prevPage = () => {
    if (!hasPagination) return;
    if (offset >= numericPageSize) setOffset(offset - numericPageSize);
  };

  const showingFrom = totalCount === 0 ? 0 : hasPagination ? offset + 1 : 1;
  const showingTo = hasPagination ? Math.min(offset + numericPageSize, totalCount) : totalCount;

  const handleSeeInKG = async (work: AncientWork, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      const kgData = await apiClient.getWorkKGNodes(work.work_id);
      setSelectedWorkKGData(kgData);
      if (kgData.kg_nodes.length === 1) {
        navigate(`/visualizer/${kgData.kg_nodes[0].kg_node_id}`);
      } else {
        setShowKGModal(true);
      }
    } catch (err) {
      console.error('Error loading KG nodes:', err);
    }
  };

  const handleGoToCitation = async (work: AncientWork, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      const kgData = await apiClient.getWorkKGNodes(work.work_id);
      if (kgData.kg_nodes.length > 0) {
        const allPassageIds = kgData.kg_nodes.flatMap((node: WorkKGNode) => node.passage_ids);
        const uniquePassageIds = Array.from(new Set(allPassageIds));
        const firstPassageId = kgData.kg_nodes[0].first_passage_id;
        navigate(`/texts/${work.work_id}`, {
          state: {
            highlightPassages: uniquePassageIds,
            scrollToPassage: firstPassageId
          }
        });
      }
    } catch (err) {
      console.error('Error loading citations:', err);
    }
  };

  return (
    <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
      <div className="min-h-screen bg-transparent relative z-10">
      {/* Clean unified header */}
      <div className="bg-gradient-to-b from-gray-50 to-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold text-gray-900 mb-2">{t('ancientWorks.title')}</h1>
              <p className="text-sm sm:text-base text-gray-600">{t('ancientWorks.subtitle', { count: stats?.total_works || 0 })}</p>
            </div>
            {stats && (
              <div className="flex gap-4 sm:gap-6 text-sm">
                <div className="text-center">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900">{stats.total_passages?.toLocaleString() || '0'}</div>
                  <div className="text-xs sm:text-sm text-gray-500">{t('ancientWorks.stats.passages')}</div>
                </div>
                <div className="text-center">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900">{stats.total_citations?.toLocaleString() || '0'}</div>
                  <div className="text-xs sm:text-sm text-gray-500">{t('ancientWorks.stats.citations')}</div>
                </div>
              </div>
            )}
          </div>

          {/* Inline filters */}
          <div className="space-y-3">
            {/* Filter controls - wrap on mobile */}
            <div className="flex flex-wrap gap-2 sm:gap-3 items-center">
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setOffset(0);
                }}
                className="flex-1 sm:flex-none min-w-[120px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 bg-white min-h-[44px]"
              >
                <option value="">{t('ancientWorks.filters.allAuthors')}</option>
                {stats?.top_authors?.map((author: AuthorStats) => (
                  <option key={author.author} value={author.author}>
                    {author.author} ({author.passage_count?.toLocaleString() || 0})
                  </option>
                ))}
              </select>

              <input
                type="text"
                value={authorFilter}
                onChange={(e) => {
                  setAuthorFilter(e.target.value);
                  setOffset(0);
                }}
                placeholder={t('ancientWorks.filters.searchAuthorPlaceholder')}
                className="flex-1 sm:flex-none min-w-[120px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 min-h-[44px]"
              />

              <select
                value={languageFilter}
                onChange={(e) => {
                  setLanguageFilter(e.target.value);
                  setOffset(0);
                }}
                className="flex-1 sm:flex-none min-w-[100px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 bg-white min-h-[44px]"
              >
                <option value="">{t('ancientWorks.filters.allLanguages')}</option>
                <option value="Greek">{t('ancientWorks.filters.languages.greek')}</option>
                <option value="Latin">{t('ancientWorks.filters.languages.latin')}</option>
                <option value="English">{t('ancientWorks.filters.languages.english')}</option>
              </select>

              <button
                onClick={() => {
                  setFeaturedWorksFilter(!featuredWorksFilter);
                  setOffset(0);
                }}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors min-h-[44px] ${
                  featuredWorksFilter
                    ? 'bg-gray-900 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {featuredWorksFilter ? '⭐ ' : ''}{t('ancientWorks.filters.featured')}
              </button>

              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setOffset(0);
                }}
                className="flex-1 sm:flex-none min-w-[120px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 bg-white min-h-[44px]"
              >
                <option value="most_cited">{t('ancientWorks.sort.mostCited')}</option>
                <option value="author">{t('ancientWorks.sort.byAuthor')}</option>
                <option value="title">{t('ancientWorks.sort.byTitle')}</option>
                <option value="passages_desc">{t('ancientWorks.sort.mostPassages')}</option>
              </select>

              <button
                onClick={resetFilters}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 font-medium min-h-[44px]"
              >
                {t('ancientWorks.filters.reset')}
              </button>
            </div>

            {/* Pagination - separate row on mobile */}
            <div className="flex items-center justify-between sm:justify-end gap-3 text-sm border-t sm:border-t-0 pt-3 sm:pt-0">
              <span className="text-gray-600 text-xs sm:text-sm">
                {t('ancientWorks.pagination.showing', { from: showingFrom, to: showingTo, total: totalCount })}
              </span>
              {hasPagination && (
                <div className="flex items-center gap-1">
                  <button
                    onClick={prevPage}
                    disabled={offset === 0}
                    className="p-2 min-w-[44px] min-h-[44px] text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <button
                    onClick={nextPage}
                    disabled={offset + numericPageSize >= totalCount}
                    className="p-2 min-w-[44px] min-h-[44px] text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 px-4 py-3 bg-red-50 border border-red-200 text-red-800 rounded-lg">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <AILoader text="Loading" size="md" />
            <p className="text-gray-500 mt-6">{t('ancientWorks.loading')}</p>
          </div>
        ) : works.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">{t('ancientWorks.noResults')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {works.map((work) => (
              <TextCard
                key={work.work_id}
                work={work}
                onClick={() => navigate(`/texts/${work.work_id}`)}
                onSeeInKG={handleSeeInKG}
                onGoToCitation={handleGoToCitation}
              />
            ))}
          </div>
        )}
      </div>

      {/* KG Node Selection Modal */}
      {selectedWorkKGData && (
        <KGNodeSelectionModal
          isOpen={showKGModal}
          onClose={() => {
            setShowKGModal(false);
            setSelectedWorkKGData(null);
          }}
          workTitle={selectedWorkKGData.work_title}
          workAuthor={selectedWorkKGData.work_author}
          nodes={selectedWorkKGData.kg_nodes}
        />
      )}
      </div>
    </AuroraBackground>
  );
}

// Work Card Component
function TextCard({
  work,
  onClick,
  onSeeInKG,
  onGoToCitation
}: {
  work: AncientWork;
  onClick: () => void;
  onSeeInKG: (work: AncientWork, event: React.MouseEvent) => void;
  onGoToCitation: (work: AncientWork, event: React.MouseEvent) => void;
}) {
  const { t } = useTranslation();

  // Language icon
  const getLanguageIcon = () => {
    switch (work.language) {
      case 'grc':
        return <span className="text-base" title={t('ancientWorks.languageIcons.ancientGreek')}>Ω</span>;
      case 'lat':
        return <span className="text-base" title={t('ancientWorks.languageIcons.latin')}>Ⅎ</span>;
      case 'eng':
        return <span className="text-base" title={t('ancientWorks.languageIcons.english')}>A</span>;
      default:
        return <span className="text-base" title={t('ancientWorks.languageIcons.unknown')}>?</span>;
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-lg p-5 hover:border-gray-400 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1">{work.title}</h3>
        <div className="flex items-center gap-2 ml-2 flex-shrink-0">
          <span className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-xs font-semibold">
            {getLanguageIcon()}
          </span>
          {(work.kg_citations ?? 0) > 0 && (
            <span
              className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-xs font-semibold"
              title={t('ancientWorks.card.citedInKG', { count: work.kg_citations })}
            >
              ⭐ {work.kg_citations}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1 text-sm text-gray-600 mb-4">
        <div><strong className="text-gray-900">{t('ancientWorks.card.author')}:</strong> {work.author}</div>
        <div><strong className="text-gray-900">{t('ancientWorks.card.passages')}:</strong> {work.passage_count?.toLocaleString() ?? '—'}</div>
        {work.period && <div><strong className="text-gray-900">{t('ancientWorks.card.period')}:</strong> {work.period}</div>}
      </div>

      {(work.kg_citations ?? 0) > 0 && (
        <div className="flex gap-2 pt-3 border-t border-gray-200">
          <button
            onClick={(e) => onSeeInKG(work, e)}
            className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded transition-colors"
          >
            {t('ancientWorks.card.actions.seeInKG')}
          </button>
          <button
            onClick={(e) => onGoToCitation(work, e)}
            className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded transition-colors"
          >
            {t('ancientWorks.card.actions.goToCitation')}
          </button>
        </div>
      )}

    </div>
  );
}
