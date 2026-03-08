import { useState, useEffect, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  X,
  BookOpen,
  BarChart3,
  Users,
  Link2,
  Network,
  ExternalLink,
  Loader2,
  ChevronDown,
  ChevronUp,
  Hash,
  FileText,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type {
  LemmaDictionaryResponse,
  LemmaStatsResponse,
  RelatedLemmasResponse,
  LemmaKGConnectionsResponse,
} from '../api/client';

// POS tag colors matching SearchPage
const POS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NOUN: { bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-200 dark:border-blue-800' },
  VERB: { bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-700 dark:text-green-300', border: 'border-green-200 dark:border-green-800' },
  ADJ: { bg: 'bg-purple-100 dark:bg-purple-900/40', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-200 dark:border-purple-800' },
  ADV: { bg: 'bg-orange-100 dark:bg-orange-900/40', text: 'text-orange-700 dark:text-orange-300', border: 'border-orange-200 dark:border-orange-800' },
  PRON: { bg: 'bg-pink-100 dark:bg-pink-900/40', text: 'text-pink-700 dark:text-pink-300', border: 'border-pink-200 dark:border-pink-800' },
  CONJ: { bg: 'bg-yellow-100 dark:bg-yellow-900/40', text: 'text-yellow-700 dark:text-yellow-300', border: 'border-yellow-200 dark:border-yellow-800' },
  ADP: { bg: 'bg-teal-100 dark:bg-teal-900/40', text: 'text-teal-700 dark:text-teal-300', border: 'border-teal-200 dark:border-teal-800' },
  DET: { bg: 'bg-indigo-100 dark:bg-indigo-900/40', text: 'text-indigo-700 dark:text-indigo-300', border: 'border-indigo-200 dark:border-indigo-800' },
  PART: { bg: 'bg-gray-100 dark:bg-gray-700/40', text: 'text-gray-700 dark:text-gray-300', border: 'border-gray-200 dark:border-gray-700' },
};

interface LemmaIntelligencePanelProps {
  lemma: string;
  language: 'grc' | 'lat';
  onClose: () => void;
  onLemmaClick?: (lemma: string) => void;
}

const LemmaIntelligencePanel = memo(function LemmaIntelligencePanel({
  lemma,
  language,
  onClose,
  onLemmaClick,
}: LemmaIntelligencePanelProps) {
  const { t } = useTranslation();
  // Data states
  const [dictionary, setDictionary] = useState<LemmaDictionaryResponse | null>(null);
  const [stats, setStats] = useState<LemmaStatsResponse | null>(null);
  const [related, setRelated] = useState<RelatedLemmasResponse | null>(null);
  const [kgConnections, setKgConnections] = useState<LemmaKGConnectionsResponse | null>(null);

  // Loading states
  const [loadingDict, setLoadingDict] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingRelated, setLoadingRelated] = useState(true);
  const [loadingKG, setLoadingKG] = useState(true);

  // Expansion states
  const [expandedDef, setExpandedDef] = useState(false);
  const [showAllAuthors, setShowAllAuthors] = useState(false);
  const [showAllWorks, setShowAllWorks] = useState(false);

  // Fetch all data in parallel
  useEffect(() => {
    const fetchData = async () => {
      // Reset states
      setDictionary(null);
      setStats(null);
      setRelated(null);
      setKgConnections(null);
      setLoadingDict(true);
      setLoadingStats(true);
      setLoadingRelated(true);
      setLoadingKG(true);
      setExpandedDef(false);
      setShowAllAuthors(false);
      setShowAllWorks(false);

      // Fetch dictionary
      apiClient
        .getLemmaDictionary(lemma, language)
        .then(setDictionary)
        .catch(console.error)
        .finally(() => setLoadingDict(false));

      // Fetch stats
      apiClient
        .getLemmaStats(lemma, language)
        .then(setStats)
        .catch(console.error)
        .finally(() => setLoadingStats(false));

      // Fetch related lemmas
      apiClient
        .getRelatedLemmas(lemma, { language, limit: 15 })
        .then(setRelated)
        .catch(console.error)
        .finally(() => setLoadingRelated(false));

      // Fetch KG connections
      apiClient
        .getLemmaKGConnections(lemma, language)
        .then(setKgConnections)
        .catch(console.error)
        .finally(() => setLoadingKG(false));
    };

    if (lemma) {
      fetchData();
    }
  }, [lemma, language]);

  // Calculate max values for bar charts
  const maxAuthorPassages = stats?.by_author?.length
    ? Math.max(...stats.by_author.map((a) => a.passages))
    : 1;
  const maxWorkPassages = stats?.by_work?.length
    ? Math.max(...stats.by_work.map((w) => w.passages))
    : 1;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-start justify-end pt-20"
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/30 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Panel */}
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="relative h-full w-full max-w-lg bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="flex-shrink-0 px-6 py-5 border-b border-neutral-200 dark:border-neutral-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                    {t('lemmaPanel.kicker')}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-black dark:text-white break-words">
                  {lemma}
                </h2>
                {dictionary?.lemma_latin && dictionary.lemma_latin !== lemma && (
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 font-mono mt-1">
                    {dictionary.lemma_latin}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-medium">
                    {language === 'grc' ? t('lemmaPanel.languages.greek') : t('lemmaPanel.languages.latin')}
                  </span>
                  {dictionary?.dictionary && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-medium">
                      {dictionary.dictionary}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-neutral-200/50 dark:hover:bg-neutral-700/50 rounded-xl transition-colors"
                aria-label={t('lemmaPanel.close')}
              >
                <X className="w-5 h-5 text-neutral-500" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-6">
              {/* Dictionary Definition */}
              <Section
                icon={<BookOpen className="w-4 h-4" />}
                title={t('lemmaPanel.sections.dictionary')}
                loading={loadingDict}
              >
                {dictionary?.found ? (
                  <div className="space-y-3">
                    {/* Short definition */}
                    {dictionary.short_def && (
                      <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed">
                        {dictionary.short_def}
                      </p>
                    )}

                    {/* Full definition (expandable) */}
                    {dictionary.definition && dictionary.definition.length > 300 && (
                      <div>
                        <button
                          onClick={() => setExpandedDef(!expandedDef)}
                          className="flex items-center gap-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        >
                          {expandedDef ? (
                            <>
                              <ChevronUp className="w-3.5 h-3.5" />
                              {t('lemmaPanel.showLess')}
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-3.5 h-3.5" />
                              {t('lemmaPanel.showFullDefinition')}
                            </>
                          )}
                        </button>
                        <AnimatePresence>
                          {expandedDef && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="overflow-hidden"
                            >
                              <div
                                className="mt-3 text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed max-h-60 overflow-y-auto p-3 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg border border-neutral-200 dark:border-neutral-700"
                                dangerouslySetInnerHTML={{
                                  __html: dictionary.definition,
                                }}
                              />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}

                    {/* Forms */}
                    {dictionary.forms && dictionary.forms.length > 0 && (
                      <div className="pt-2">
                        <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-2">
                          {t('lemmaPanel.sections.forms')}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {dictionary.forms.slice(0, 8).map((form, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 rounded-md"
                            >
                              {form}
                            </span>
                          ))}
                          {dictionary.forms.length > 8 && (
                            <span className="text-xs text-neutral-400">
                              {t('graphUi.cosmicPanel.more', { count: dictionary.forms.length - 8 })}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 italic">
                    {t('lemmaPanel.empty.noDefinition')}
                  </p>
                )}
              </Section>

              {/* Corpus Statistics */}
              <Section
                icon={<BarChart3 className="w-4 h-4" />}
                title={t('lemmaPanel.sections.statistics')}
                loading={loadingStats}
              >
                {stats && (stats.total_occurrences > 0 || stats.passage_count > 0) ? (
                  <div className="space-y-4">
                    {/* Summary stats */}
                    <div className="grid grid-cols-2 gap-3">
                      <StatCard
                        icon={<Hash className="w-4 h-4" />}
                        label={t('lemmaPanel.metrics.occurrences')}
                        value={stats.total_occurrences.toLocaleString()}
                      />
                      <StatCard
                        icon={<FileText className="w-4 h-4" />}
                        label={t('lemmaPanel.metrics.passages')}
                        value={stats.passage_count.toLocaleString()}
                      />
                    </div>

                    {/* By Author */}
                    {stats.by_author && stats.by_author.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-2 flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5" />
                          {t('lemmaPanel.sections.byAuthor')}
                        </p>
                        <div className="space-y-1.5">
                          {(showAllAuthors
                            ? stats.by_author
                            : stats.by_author.slice(0, 5)
                          ).map((item) => (
                            <BarChartRow
                              key={item.author}
                              label={item.author}
                              value={item.passages}
                              maxValue={maxAuthorPassages}
                              color="bg-blue-500"
                            />
                          ))}
                        </div>
                        {stats.by_author.length > 5 && (
                          <button
                            onClick={() => setShowAllAuthors(!showAllAuthors)}
                            className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                          >
                            {showAllAuthors
                              ? t('lemmaPanel.showLess')
                              : t('lemmaPanel.actions.showAllAuthors')}
                          </button>
                        )}
                      </div>
                    )}

                    {/* By Work */}
                    {stats.by_work && stats.by_work.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-2 flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5" />
                          {t('lemmaPanel.sections.byWork')}
                        </p>
                        <div className="space-y-1.5">
                          {(showAllWorks
                            ? stats.by_work
                            : stats.by_work.slice(0, 5)
                          ).map((item) => (
                            <BarChartRow
                              key={`${item.author}-${item.title}`}
                              label={`${item.title}`}
                              sublabel={item.author}
                              value={item.passages}
                              maxValue={maxWorkPassages}
                              color="bg-indigo-500"
                            />
                          ))}
                        </div>
                        {stats.by_work.length > 5 && (
                          <button
                            onClick={() => setShowAllWorks(!showAllWorks)}
                            className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                          >
                            {showAllWorks
                              ? t('lemmaPanel.showLess')
                              : t('lemmaPanel.actions.showAllWorks')}
                          </button>
                        )}
                      </div>
                    )}

                    {/* By Period */}
                    {stats.by_period && stats.by_period.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-2 flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5" />
                          {t('lemmaPanel.sections.byPeriod')}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {stats.by_period.map((item) => (
                            <span
                              key={item.period}
                              className="text-xs px-2.5 py-1.5 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 text-amber-700 dark:text-amber-300 rounded-lg border border-amber-200 dark:border-amber-800"
                            >
                              {item.period}: {item.passages}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 italic">
                    {t('lemmaPanel.empty.noStats')}
                  </p>
                )}
              </Section>

              {/* Related Lemmas */}
              <Section
                icon={<Link2 className="w-4 h-4" />}
                title={t('lemmaPanel.sections.related')}
                loading={loadingRelated}
              >
                {related?.related && related.related.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {related.related.map((item) => {
                      const posColor = POS_COLORS[item.pos] || {
                        bg: 'bg-gray-100 dark:bg-gray-800',
                        text: 'text-gray-600 dark:text-gray-400',
                        border: 'border-gray-200 dark:border-gray-700',
                      };
                      return (
                        <button
                          key={item.lemma}
                          onClick={() => onLemmaClick?.(item.lemma)}
                          className={`group flex items-center gap-2 px-3 py-1.5 ${posColor.bg} ${posColor.text} rounded-lg border ${posColor.border} hover:shadow-md transition-all text-sm`}
                        >
                          <span className="font-medium">{item.lemma}</span>
                          <span className="text-xs opacity-70">
                            {item.cooccurrences}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 italic">
                    {t('lemmaPanel.empty.noRelated')}
                  </p>
                )}
              </Section>

              {/* Knowledge Graph Connections */}
              <Section
                icon={<Network className="w-4 h-4" />}
                title={t('lemmaPanel.sections.knowledgeGraph')}
                loading={loadingKG}
              >
                {kgConnections?.kg_nodes && kgConnections.kg_nodes.length > 0 ? (
                  <div className="space-y-2">
                    {kgConnections.kg_nodes.map((node) => (
                      <div
                        key={node.node_id}
                        className="p-3 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full font-medium capitalize">
                            {node.type}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-black dark:text-white">
                              {node.label}
                            </p>
                            {node.description && (
                              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 line-clamp-2">
                                {node.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 italic">
                    {t('lemmaPanel.empty.noKgConnections')}
                  </p>
                )}
              </Section>

              {/* External Links */}
              <Section
                icon={<ExternalLink className="w-4 h-4" />}
                title={t('lemmaPanel.sections.externalResources')}
                loading={false}
              >
                <div className="grid grid-cols-2 gap-2">
                  {dictionary?.external_links?.logeion && (
                    <ExternalLinkButton
                      href={dictionary.external_links.logeion}
                      label="Logeion"
                      description="Chicago dictionary"
                    />
                  )}
                  {dictionary?.external_links?.perseus && (
                    <ExternalLinkButton
                      href={dictionary.external_links.perseus}
                      label="Perseus"
                      description="Morphology"
                    />
                  )}
                  {dictionary?.external_links?.bailly && (
                    <ExternalLinkButton
                      href={dictionary.external_links.bailly}
                      label="Bailly 2020"
                      description="Greek-French"
                    />
                  )}
                  {language === 'grc' && (
                    <ExternalLinkButton
                      href={`https://bailly.app/recherche?q=${encodeURIComponent(lemma)}`}
                      label="Bailly.app"
                      description="Greek-French"
                    />
                  )}
                </div>
              </Section>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
});

// Section component
function Section({
  icon,
  title,
  loading,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  loading: boolean;
  children: React.ReactNode;
}) {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-blue-600 dark:text-blue-400">{icon}</span>
        <h3 className="text-sm font-semibold text-black dark:text-white">
          {title}
        </h3>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 py-4">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-sm text-neutral-500">{t('common.loading')}</span>
        </div>
      ) : (
        children
      )}
    </div>
  );
}

// Stat card component
function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="p-3 bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-800/50 dark:to-neutral-800/30 rounded-xl border border-neutral-200 dark:border-neutral-700">
      <div className="flex items-center gap-2 text-neutral-500 dark:text-neutral-400 mb-1">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="text-xl font-bold text-black dark:text-white">{value}</p>
    </div>
  );
}

// Bar chart row component
function BarChartRow({
  label,
  sublabel,
  value,
  maxValue,
  color,
}: {
  label: string;
  sublabel?: string;
  value: number;
  maxValue: number;
  color: string;
}) {
  const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;

  return (
    <div className="group">
      <div className="flex items-center justify-between text-xs mb-1">
        <div className="flex-1 min-w-0">
          <span className="text-neutral-700 dark:text-neutral-300 truncate block">
            {label}
          </span>
          {sublabel && (
            <span className="text-neutral-400 dark:text-neutral-500 text-[10px] truncate block">
              {sublabel}
            </span>
          )}
        </div>
        <span className="text-neutral-500 dark:text-neutral-400 ml-2 flex-shrink-0">
          {value}
        </span>
      </div>
      <div className="h-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full ${color} rounded-full`}
        />
      </div>
    </div>
  );
}

// External link button component
function ExternalLinkButton({
  href,
  label,
  description,
}: {
  href: string;
  label: string;
  description: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 p-3 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all group"
    >
      <ExternalLink className="w-4 h-4 text-neutral-400 group-hover:text-blue-500 transition-colors flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-black dark:text-white truncate">
          {label}
        </p>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
          {description}
        </p>
      </div>
    </a>
  );
}

export default LemmaIntelligencePanel;
