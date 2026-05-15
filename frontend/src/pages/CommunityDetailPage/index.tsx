import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  AlertCircle,
  Loader2,
  Sparkles,
  Coins,
  CircuitBoard,
  Calendar,
  ScrollText,
  ArrowRight,
  BookOpenText,
} from 'lucide-react';
import {
  getCommunityQuery,
  type CommunityDetail,
} from '../../api/community';
import { CitationRenderer, SourcesPanel } from '../../components/CitationRenderer';
import { cn } from '../../lib/utils';

function formatDate(iso: string, locale: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(date);
}

function formatCostUsd(cost: number): string {
  if (cost === 0) return '$0.000';
  if (cost < 0.001) return '<$0.001';
  return `$${cost.toFixed(3)}`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-hidden="true">
      <div className="h-6 w-32 rounded bg-stone-200/60" />
      <div className="h-10 w-3/4 rounded bg-stone-200/60" />
      <div className="h-6 w-1/2 rounded bg-stone-200/60" />
      <div className="space-y-3">
        <div className="h-4 w-full rounded bg-stone-100" />
        <div className="h-4 w-11/12 rounded bg-stone-100" />
        <div className="h-4 w-10/12 rounded bg-stone-100" />
        <div className="h-4 w-9/12 rounded bg-stone-100" />
      </div>
    </div>
  );
}

function PassageCitationBadges({ entries }: { entries: CommunityDetail['passage_citations'] }) {
  const { t } = useTranslation();
  if (!entries || entries.length === 0) return null;
  return (
    <div className="mt-8">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
        {t('recherches.detail.passageCitations')}
      </h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {entries.map((entry, idx) => {
          const ref = entry.ref ?? `P${idx + 1}`;
          const label = entry.label ?? entry.id ?? '';
          return (
            <span
              key={`${ref}-${idx}`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200/60 bg-amber-50/60 px-2.5 py-1 text-[11px] font-medium text-amber-900"
            >
              <span className="font-mono text-amber-700">{ref}</span>
              {label && <span className="text-amber-800/80">·</span>}
              {label && <span className="truncate max-w-[260px]">{label}</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default function CommunityDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<CommunityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!slug) {
      setError(t('recherches.errors.notFound'));
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    getCommunityQuery(slug)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : t('recherches.errors.loadFailed');
        setError(message);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug, t]);

  const handleReproduce = () => {
    if (!detail) return;
    navigate(`/graphrag?q=${encodeURIComponent(detail.query)}`);
  };

  return (
    <div className="min-h-screen w-full bg-transparent">
      {/* Sticky breadcrumb */}
      <div className="sticky top-12 z-30 border-b border-amber-200/40 bg-parchment-50/85 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <Link
            to="/recherches"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-500 hover:text-amber-800 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            {t('recherches.detail.backToList')}
          </Link>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20 relative z-10">
        {loading && <DetailSkeleton />}

        {error && !loading && (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/70 p-5 text-sm text-red-800"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <div>
              <p className="font-medium">{t('recherches.errors.title')}</p>
              <p className="text-red-700/80">{error}</p>
              <Link
                to="/recherches"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-900"
              >
                <ArrowLeft className="h-3 w-3" aria-hidden="true" />
                {t('recherches.detail.backToList')}
              </Link>
            </div>
          </div>
        )}

        {detail && !loading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-10">
            <motion.article
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="min-w-0"
            >
              {/* Topic tags */}
              {detail.topic_tags.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-1.5">
                  {detail.topic_tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center rounded-full border border-amber-200/60 bg-amber-50/70 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Question */}
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-display font-semibold text-stone-800 tracking-tight leading-tight">
                {detail.query}
              </h1>

              {/* Meta row */}
              <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-stone-500">
                <span className="inline-flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-stone-400" aria-hidden="true" />
                  {formatDate(detail.created_at, i18n.language)}
                </span>
                {detail.model && (
                  <span className="inline-flex items-center gap-1.5">
                    <CircuitBoard className="h-3.5 w-3.5 text-stone-400" aria-hidden="true" />
                    <span className="font-mono">{detail.model}</span>
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5">
                  <Coins className="h-3.5 w-3.5 text-stone-400" aria-hidden="true" />
                  {formatCostUsd(detail.total_cost_usd)}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-stone-400" aria-hidden="true" />
                  {t('recherches.detail.tokens', { count: detail.total_tokens, formatted: formatTokens(detail.total_tokens) })}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <ScrollText className="h-3.5 w-3.5 text-stone-400" aria-hidden="true" />
                  {t('recherches.detail.citations', { count: detail.citation_count })}
                </span>
              </div>

              {/* Answer */}
              <div className={cn('prose prose-stone prose-sm xl:prose-base max-w-none mt-8')}>
                <CitationRenderer
                  content={detail.answer}
                  sources={detail.sources ?? []}
                  passageCitations={detail.passage_citations ?? []}
                />
              </div>

              {/* Passage citation badges (static reference list) */}
              <PassageCitationBadges entries={detail.passage_citations ?? []} />

              {/* CTA */}
              <div className="mt-10 rounded-2xl border border-amber-200/60 bg-amber-50/40 p-5 sm:p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-stone-800">
                      {t('recherches.detail.cta.title')}
                    </h2>
                    <p className="mt-1 text-xs text-stone-600 leading-relaxed">
                      {t('recherches.detail.cta.body')}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleReproduce}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-amber-700 px-4 py-2 text-xs font-semibold text-amber-50 transition-colors hover:bg-amber-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50"
                  >
                    {t('recherches.detail.cta.button')}
                    <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </motion.article>

            {/* Sources side rail (lg+) */}
            <motion.aside
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="hidden lg:block"
            >
              <div className="sticky top-28">
                <div className="rounded-2xl border border-stone-200/60 bg-white/50 p-4">
                  <div className="flex items-center gap-2">
                    <BookOpenText className="h-4 w-4 text-amber-700" aria-hidden="true" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-700">
                      {t('recherches.detail.sources')}
                    </h3>
                  </div>
                  {detail.sources && detail.sources.length > 0 ? (
                    <SourcesPanel sources={detail.sources} className="!border-t-0 !mt-2 !pt-2" />
                  ) : (
                    <p className="mt-3 text-xs text-stone-400">
                      {t('recherches.detail.noSources')}
                    </p>
                  )}
                </div>
              </div>
            </motion.aside>
          </div>
        )}

        {loading && (
          <div className="mt-6 flex justify-center">
            <Loader2
              className="h-5 w-5 animate-spin text-stone-400"
              aria-label={t('recherches.loading')}
            />
          </div>
        )}
      </div>
    </div>
  );
}
