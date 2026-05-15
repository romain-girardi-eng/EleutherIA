import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  AlertCircle,
  Loader2,
  ScrollText,
  Calendar,
  BookMarked,
} from 'lucide-react';
import {
  getCanonicalPassage,
  type CanonicalPassageDetail,
} from '../../api/canonicalPassages';
import { cn } from '../../lib/utils';

function formatDate(iso: string, locale: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

function languageBadge(language: string | null): string {
  switch (language) {
    case 'grc':
      return 'bg-blue-50 text-blue-800 border-blue-200/60';
    case 'lat':
      return 'bg-red-50 text-red-800 border-red-200/60';
    case 'hbo':
      return 'bg-emerald-50 text-emerald-800 border-emerald-200/60';
    default:
      return 'bg-stone-50 text-stone-600 border-stone-200/60';
  }
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
      </div>
    </div>
  );
}

export default function CanonicalPassageDetailPage() {
  const { passage_id: passageId } = useParams<{ passage_id: string }>();
  const { t, i18n } = useTranslation();
  const [detail, setDetail] = useState<CanonicalPassageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!passageId) {
      setError(t('canonicalPassages.errors.notFound'));
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    getCanonicalPassage(passageId)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof Error
            ? err.message
            : t('canonicalPassages.errors.loadFailed');
        setError(message);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [passageId, t]);

  return (
    <div className="min-h-screen w-full bg-transparent">
      {/* Sticky breadcrumb */}
      {/* Sticks 80px from viewport top — matches the desktop fixed
          navbar height (h-20) so it sits flush *below* it instead of
          getting clipped behind. */}
      <div className="sticky top-20 z-30 border-b border-amber-200/40 bg-parchment-50/85 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <Link
            to="/passages-canoniques"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-500 hover:text-amber-800 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            {t('canonicalPassages.detail.backToList')}
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
              <p className="font-medium">{t('canonicalPassages.errors.title')}</p>
              <p className="text-red-700/80">{error}</p>
              <Link
                to="/passages-canoniques"
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-900"
              >
                <ArrowLeft className="h-3 w-3" aria-hidden="true" />
                {t('canonicalPassages.detail.backToList')}
              </Link>
            </div>
          </div>
        )}

        {detail && !loading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-10">
            <motion.article
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="min-w-0"
            >
              {/* Hero */}
              <div className="flex flex-wrap items-start gap-3 text-xs text-stone-500">
                <span
                  className={cn(
                    'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wide',
                    languageBadge(detail.language)
                  )}
                >
                  {(detail.language ?? 'eng').toUpperCase()}
                </span>
                {detail.period && (
                  <span className="inline-flex items-center rounded-full border border-amber-200/60 bg-amber-50/70 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-800">
                    {detail.period}
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5">
                  <ScrollText className="h-3.5 w-3.5 text-amber-700/70" aria-hidden="true" />
                  {t('canonicalPassages.detail.citedIn', {
                    count: detail.distinct_answer_count,
                  })}
                </span>
              </div>

              <h1 className="mt-4 text-2xl sm:text-3xl lg:text-4xl font-display font-semibold text-stone-800 tracking-tight leading-tight">
                {detail.canonical_ref ?? detail.label}
              </h1>
              {(detail.author || detail.work_title) && (
                <p className="mt-2 text-base text-stone-600 italic">
                  {[detail.author, detail.work_title].filter(Boolean).join(' — ')}
                </p>
              )}

              {/* Full text */}
              {detail.full_text && (
                <div className="mt-8">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                    {t('canonicalPassages.detail.fullText')}
                  </h2>
                  <pre className="mt-3 whitespace-pre-wrap rounded-2xl border border-stone-200/60 bg-parchment-50/70 p-5 font-serif text-sm leading-relaxed text-stone-800">
                    {detail.full_text}
                  </pre>
                </div>
              )}

              {/* Citing answers */}
              <section className="mt-10">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                  {t('canonicalPassages.detail.citingAnswersTitle', {
                    count: detail.citing_answers.length,
                  })}
                </h2>
                <ul className="mt-3 space-y-3">
                  {detail.citing_answers.map((answer) => (
                    <li key={answer.slug}>
                      <Link
                        to={`/recherches/${encodeURIComponent(answer.slug)}`}
                        className={cn(
                          'group block rounded-xl border border-stone-200/60 bg-white/60 backdrop-blur-sm p-4',
                          'transition-all duration-200',
                          'hover:border-amber-300/70 hover:bg-amber-50/30',
                          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50'
                        )}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <h3 className="text-sm font-display font-semibold text-stone-800 leading-snug group-hover:text-amber-900 transition-colors line-clamp-2">
                            {answer.query}
                          </h3>
                          <ArrowRight
                            className="h-3.5 w-3.5 mt-0.5 shrink-0 text-stone-300 group-hover:text-amber-700 transition-colors"
                            aria-hidden="true"
                          />
                        </div>
                        <p className="mt-2 text-xs text-stone-500 leading-relaxed line-clamp-2">
                          {answer.excerpt}
                        </p>
                        <div className="mt-3 flex items-center justify-between gap-3 text-[11px] text-stone-400">
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="h-3 w-3" aria-hidden="true" />
                            {formatDate(answer.created_at, i18n.language)}
                          </span>
                          <span className="inline-flex items-center gap-1 font-mono">
                            {t('canonicalPassages.detail.occurrences', {
                              count: answer.citation_count,
                            })}
                          </span>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>

              {/* CTA back */}
              <div className="mt-10 rounded-2xl border border-amber-200/60 bg-amber-50/40 p-5 sm:p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-stone-800">
                      {t('canonicalPassages.detail.ctaTitle')}
                    </h2>
                    <p className="mt-1 text-xs text-stone-600 leading-relaxed">
                      {t('canonicalPassages.detail.ctaBody')}
                    </p>
                  </div>
                  <Link
                    to="/passages-canoniques"
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-amber-700 px-4 py-2 text-xs font-semibold text-amber-50 transition-colors hover:bg-amber-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 focus-visible:ring-offset-parchment-50"
                  >
                    {t('canonicalPassages.detail.ctaButton')}
                    <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </Link>
                </div>
              </div>
            </motion.article>

            {/* Side rail */}
            <motion.aside
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="hidden lg:block"
            >
              <div className="sticky top-28 space-y-4">
                <div className="rounded-2xl border border-stone-200/60 bg-white/50 p-4">
                  <div className="flex items-center gap-2">
                    <BookMarked className="h-4 w-4 text-amber-700" aria-hidden="true" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-700">
                      {t('canonicalPassages.detail.metadata')}
                    </h3>
                  </div>
                  <dl className="mt-3 space-y-2 text-xs">
                    {detail.author && (
                      <div>
                        <dt className="text-stone-400">
                          {t('canonicalPassages.detail.author')}
                        </dt>
                        <dd className="text-stone-700 font-medium">{detail.author}</dd>
                      </div>
                    )}
                    {detail.work_title && (
                      <div>
                        <dt className="text-stone-400">
                          {t('canonicalPassages.detail.work')}
                        </dt>
                        <dd className="text-stone-700 font-medium">
                          {detail.work_title}
                        </dd>
                      </div>
                    )}
                    {detail.period && (
                      <div>
                        <dt className="text-stone-400">
                          {t('canonicalPassages.detail.period')}
                        </dt>
                        <dd className="text-stone-700 font-medium">{detail.period}</dd>
                      </div>
                    )}
                    <div>
                      <dt className="text-stone-400">
                        {t('canonicalPassages.detail.totalCitations')}
                      </dt>
                      <dd className="text-stone-700 font-medium">
                        {detail.citation_count}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-stone-400">
                        {t('canonicalPassages.detail.distinctAnswers')}
                      </dt>
                      <dd className="text-stone-700 font-medium">
                        {detail.distinct_answer_count}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            </motion.aside>
          </div>
        )}

        {loading && (
          <div className="mt-6 flex justify-center">
            <Loader2
              className="h-5 w-5 animate-spin text-stone-400"
              aria-label={t('canonicalPassages.loading')}
            />
          </div>
        )}
      </div>
    </div>
  );
}
