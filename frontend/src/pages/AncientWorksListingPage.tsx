import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { BookOpen, Search, Star, RotateCcw, ChevronLeft, ChevronRight, Library, ScrollText, Quote, Network, ArrowRight, Sparkles } from 'lucide-react';
import { Typewriter } from '../components/ui/typewriter';
import { apiClient } from '../api/client';
import { cachedApiClient } from '../api/cachedClient';
import { KGNodeSelectionModal } from '../components/KGNodeSelectionModal';
import { EmptyState } from '../components/ui/EmptyState';
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

  const loadWorks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (featuredWorksFilter && stats?.featured_works && stats.featured_works.length > 0) {
        const featuredWorkIds = stats.featured_works.map((fw: FeaturedWork) => fw.work_id);
        const featuredWorks = [];
        for (const workId of featuredWorkIds) {
          try {
            const work = await cachedApiClient.getWork(workId);
            featuredWorks.push(work);
          } catch (err) {
            console.error(`Error loading work ${workId}:`, err);
          }
        }
        setWorks(featuredWorks as AncientWork[]);
        setTotalCount(featuredWorks.length);
      } else {
        const filters: Record<string, string | number> = {};
        const isPaginated = pageSize !== 'all';
        const limitValue = isPaginated ? pageSize : 500;

        filters.offset = isPaginated ? offset : 0;
        filters.limit = limitValue;

        if (categoryFilter) filters.author = categoryFilter;
        if (authorFilter) filters.search = authorFilter;
        if (languageFilter) filters.language = LANGUAGE_FILTER_MAP[languageFilter] ?? languageFilter;
        if (sortBy) filters.sort_by = sortBy;

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
  }, [categoryFilter, authorFilter, languageFilter, featuredWorksFilter, sortBy, offset, pageSize, stats, t]);

  useEffect(() => {
    loadWorks();
    loadStats();
  }, [loadWorks]);

  const loadStats = async () => {
    try {
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

  const isFiltered = categoryFilter || authorFilter || languageFilter || !featuredWorksFilter || sortBy !== 'most_cited';

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="min-h-screen bg-transparent relative z-10">

        {/* ── Hero Section ── */}
        <div className="pt-24 pb-10 px-4 sm:px-6 lg:px-8">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="text-center mb-10"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-800/5 border border-stone-300/30 text-xs font-medium text-stone-500 tracking-wide uppercase mb-5">
                <Library className="w-3.5 h-3.5" />
                {t('ancientWorks.title')}
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-semibold text-stone-800 tracking-tight mb-3">
                <Typewriter
                  text={["Ancient Works Library", "Philosophical Texts", "Classical Sources"]}
                  speed={80}
                  waitTime={3000}
                  deleteSpeed={50}
                  className="text-stone-800"
                  cursorChar="_"
                />
              </h1>
              <p className="text-base sm:text-lg text-stone-500 max-w-2xl mx-auto leading-relaxed">
                {t('ancientWorks.subtitle', { count: stats?.total_works || 0 })}
              </p>
            </motion.div>

            {/* ── Stats row ── */}
            {stats && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
                className="flex items-center justify-center gap-8 sm:gap-12 mb-10"
              >
                <div className="flex items-center gap-2.5 text-stone-600">
                  <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center">
                    <ScrollText className="w-4 h-4 text-stone-500" />
                  </div>
                  <div>
                    <div className="text-lg sm:text-xl font-semibold text-stone-800 leading-tight">{stats.total_passages?.toLocaleString() || '0'}</div>
                    <div className="text-xs text-stone-400">{t('ancientWorks.stats.passages')}</div>
                  </div>
                </div>
                <div className="w-px h-8 bg-stone-200" />
                <div className="flex items-center gap-2.5 text-stone-600">
                  <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center">
                    <Quote className="w-4 h-4 text-stone-500" />
                  </div>
                  <div>
                    <div className="text-lg sm:text-xl font-semibold text-stone-800 leading-tight">{stats.total_citations?.toLocaleString() || '0'}</div>
                    <div className="text-xs text-stone-400">{t('ancientWorks.stats.citations')}</div>
                  </div>
                </div>
                <div className="w-px h-8 bg-stone-200" />
                <div className="flex items-center gap-2.5 text-stone-600">
                  <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center">
                    <BookOpen className="w-4 h-4 text-stone-500" />
                  </div>
                  <div>
                    <div className="text-lg sm:text-xl font-semibold text-stone-800 leading-tight">{stats.total_works?.toLocaleString() || '0'}</div>
                    <div className="text-xs text-stone-400">Works</div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ── Filter bar ── */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="bg-white/60 backdrop-blur-sm border border-stone-200/60 rounded-2xl p-3 sm:p-4 shadow-sm"
            >
              <div className="flex flex-wrap gap-2 sm:gap-2.5 items-center">
                {/* Author dropdown */}
                <select
                  value={categoryFilter}
                  onChange={(e) => { setCategoryFilter(e.target.value); setOffset(0); }}
                  className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-700 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 min-h-[40px] transition-colors"
                >
                  <option value="">{t('ancientWorks.filters.allAuthors')}</option>
                  {stats?.top_authors?.map((author: AuthorStats) => (
                    <option key={author.author} value={author.author}>
                      {author.author} ({author.passage_count?.toLocaleString() || 0})
                    </option>
                  ))}
                </select>

                {/* Search input */}
                <div className="relative flex-1 min-w-[140px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-400" />
                  <input
                    type="text"
                    value={authorFilter}
                    onChange={(e) => { setAuthorFilter(e.target.value); setOffset(0); }}
                    placeholder={t('ancientWorks.filters.searchAuthorPlaceholder')}
                    className="w-full pl-8.5 pr-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-700 placeholder:text-stone-400 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 min-h-[40px] transition-colors"
                    style={{ paddingLeft: '2.125rem' }}
                  />
                </div>

                {/* Language dropdown */}
                <select
                  value={languageFilter}
                  onChange={(e) => { setLanguageFilter(e.target.value); setOffset(0); }}
                  className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-700 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 min-h-[40px] transition-colors"
                >
                  <option value="">{t('ancientWorks.filters.allLanguages')}</option>
                  <option value="Greek">{t('ancientWorks.filters.languages.greek')}</option>
                  <option value="Latin">{t('ancientWorks.filters.languages.latin')}</option>
                  <option value="English">{t('ancientWorks.filters.languages.english')}</option>
                </select>

                {/* Featured toggle */}
                <button
                  onClick={() => { setFeaturedWorksFilter(!featuredWorksFilter); setOffset(0); }}
                  className={`inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium rounded-lg transition-all duration-200 min-h-[40px] ${
                    featuredWorksFilter
                      ? 'bg-stone-800 text-white shadow-sm'
                      : 'bg-stone-50 text-stone-600 border border-stone-200/80 hover:bg-stone-100'
                  }`}
                >
                  <Star className={`w-3.5 h-3.5 ${featuredWorksFilter ? 'fill-current' : ''}`} />
                  {t('ancientWorks.filters.featured')}
                </button>

                {/* Sort dropdown */}
                <select
                  value={sortBy}
                  onChange={(e) => { setSortBy(e.target.value); setOffset(0); }}
                  className="px-3 py-2 text-sm bg-stone-50 border border-stone-200/80 rounded-lg text-stone-700 focus:outline-none focus:border-stone-400 focus:ring-1 focus:ring-stone-400/20 min-h-[40px] transition-colors"
                >
                  <option value="most_cited">{t('ancientWorks.sort.mostCited')}</option>
                  <option value="author">{t('ancientWorks.sort.byAuthor')}</option>
                  <option value="title">{t('ancientWorks.sort.byTitle')}</option>
                  <option value="passages_desc">{t('ancientWorks.sort.mostPassages')}</option>
                </select>

                {/* Reset */}
                {isFiltered && (
                  <button
                    onClick={resetFilters}
                    className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-stone-500 hover:text-stone-700 transition-colors min-h-[40px]"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    {t('ancientWorks.filters.reset')}
                  </button>
                )}
              </div>

              {/* Pagination row */}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-stone-100">
                <span className="text-xs text-stone-400">
                  {t('ancientWorks.pagination.showing', { from: showingFrom, to: showingTo, total: totalCount })}
                </span>
                {hasPagination && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={prevPage}
                      disabled={offset === 0}
                      className="p-1.5 text-stone-500 hover:text-stone-700 disabled:opacity-30 disabled:cursor-not-allowed rounded-md hover:bg-stone-100 transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                      onClick={nextPage}
                      disabled={offset + numericPageSize >= totalCount}
                      className="p-1.5 text-stone-500 hover:text-stone-700 disabled:opacity-30 disabled:cursor-not-allowed rounded-md hover:bg-stone-100 transition-colors"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>

        {/* ── Main content ── */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 px-5 py-4 bg-red-50/80 backdrop-blur-sm border border-red-200/60 text-red-700 rounded-xl text-sm"
            >
              {error}
            </motion.div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-amber-200/40" />
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-amber-600/70 animate-spin" />
              </div>
              <p className="text-sm text-stone-500 font-serif italic">{t('ancientWorks.loading')}</p>
            </div>
          ) : works.length === 0 ? (
            <EmptyState
              type="filter"
              title={t('ancientWorks.noResults')}
              description="Try broadening your search or removing filters."
              action={isFiltered ? { label: 'Reset filters', onClick: resetFilters, variant: 'outline' } : undefined}
              size="lg"
              className="py-24"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5">
              {works.map((work, index) => (
                <motion.div
                  key={work.work_id}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={{ duration: 0.45, delay: index * 0.04, ease: [0.22, 1, 0.36, 1] }}
                >
                  <TextCard
                    work={work}
                    onClick={() => navigate(`/texts/${work.work_id}`)}
                    onSeeInKG={handleSeeInKG}
                    onGoToCitation={handleGoToCitation}
                  />
                </motion.div>
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
    </div>
  );
}


/* ────────────────────────────────────────────────────────────────────────── */
/*  TextCard — individual work card                                          */
/* ────────────────────────────────────────────────────────────────────────── */

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

  const languageLabel = work.language === 'grc'
    ? 'Greek'
    : work.language === 'lat'
      ? 'Latin'
      : work.language === 'eng'
        ? 'English'
        : work.language || '?';

  const languageColor = work.language === 'grc'
    ? 'bg-blue-50 text-blue-700 border-blue-200/60'
    : work.language === 'lat'
      ? 'bg-amber-50 text-amber-700 border-amber-200/60'
      : 'bg-stone-50 text-stone-600 border-stone-200/60';

  return (
    <div
      onClick={onClick}
      className="group relative bg-white/70 backdrop-blur-sm border border-stone-200/50 rounded-xl p-5 hover:border-stone-300 hover:shadow-md hover:bg-white/90 transition-all duration-300 cursor-pointer"
    >
      {/* Top row: language badge + citations */}
      <div className="flex items-center justify-between mb-3">
        <span className={`inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-md border ${languageColor}`}>
          {languageLabel}
        </span>
        {(work.kg_citations ?? 0) > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-md bg-amber-50 text-amber-700 border border-amber-200/60">
            <Sparkles className="w-3 h-3" />
            {work.kg_citations} {t('ancientWorks.stats.citations').toLowerCase()}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="text-[15px] font-display font-semibold text-stone-800 leading-snug mb-1.5 line-clamp-2 group-hover:text-stone-900 transition-colors">
        {work.title}
      </h3>

      {/* Author */}
      <p className="text-sm text-stone-500 mb-3">{work.author}</p>

      {/* Metadata chips */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-stone-400 mb-4">
        {work.passage_count != null && (
          <span className="inline-flex items-center gap-1">
            <ScrollText className="w-3 h-3" />
            {work.passage_count.toLocaleString()} passages
          </span>
        )}
        {work.period && (
          <span>{work.period}</span>
        )}
      </div>

      {/* Actions */}
      {(work.kg_citations ?? 0) > 0 && (
        <div className="flex gap-2 pt-3 border-t border-stone-100">
          <button
            onClick={(e) => onSeeInKG(work, e)}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-500 bg-stone-50 hover:bg-stone-100 hover:text-stone-700 rounded-lg transition-colors"
          >
            <Network className="w-3 h-3" />
            {t('ancientWorks.card.actions.seeInKG')}
          </button>
          <button
            onClick={(e) => onGoToCitation(work, e)}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-500 bg-stone-50 hover:bg-stone-100 hover:text-stone-700 rounded-lg transition-colors"
          >
            <ArrowRight className="w-3 h-3" />
            {t('ancientWorks.card.actions.goToCitation')}
          </button>
        </div>
      )}
    </div>
  );
}
