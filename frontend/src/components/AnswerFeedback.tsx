import { useEffect, useRef, useState, type RefObject } from 'react';
import { Flag, Quote, Send, Star, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  getMyAnswerFeedback,
  submitAnswerFeedback,
  submitAnswerReport,
  type AnswerReportType,
} from '../api/feedback';
import { useToast } from './ui/Toast';

const RATINGS = [1, 2, 3, 4, 5] as const;
const COMMENT_MAX_LENGTH = 4_000;
const REPORT_MAX_LENGTH = 8_000;
const EXCERPT_MAX_LENGTH = 2_000;

const REPORT_TYPES: readonly AnswerReportType[] = [
  'factual_error',
  'wrong_citation',
  'missing_source',
  'ui_issue',
  'improvement',
  'other',
];

const APP_COMMIT = [
  import.meta.env.VITE_APP_COMMIT,
  import.meta.env.VITE_GIT_SHA,
].find((value): value is string => typeof value === 'string' && value.trim().length > 0);

interface AnswerFeedbackProps {
  traceId: string;
  model?: string;
  answerContainerRef: RefObject<HTMLElement | null>;
}

function selectedAnswerExcerpt(container: HTMLElement | null): string | null {
  if (!container) return null;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return null;
  const range = selection.getRangeAt(0);
  if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) {
    return null;
  }
  const excerpt = selection.toString().replace(/\s+/g, ' ').trim();
  return excerpt ? excerpt.slice(0, EXCERPT_MAX_LENGTH) : null;
}

export default function AnswerFeedback({
  traceId,
  model,
  answerContainerRef,
}: AnswerFeedbackProps) {
  const { t } = useTranslation();
  const { showToast } = useToast();
  const [rating, setRating] = useState<number | null>(null);
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);
  const [loadingExisting, setLoadingExisting] = useState(true);
  const [savingRating, setSavingRating] = useState(false);
  const [showImpression, setShowImpression] = useState(false);
  const [comment, setComment] = useState('');
  const [savingComment, setSavingComment] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportType, setReportType] = useState<AnswerReportType>('factual_error');
  const [reportText, setReportText] = useState('');
  const [answerExcerpt, setAnswerExcerpt] = useState<string | null>(null);
  const [savingReport, setSavingReport] = useState(false);
  const selectionAtOpenRef = useRef<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingExisting(true);
    setRating(null);
    setShowImpression(false);
    setComment('');
    setShowReport(false);
    setReportText('');
    setAnswerExcerpt(null);

    void getMyAnswerFeedback(traceId, controller.signal)
      .then((existing) => {
        setRating(existing.rating);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        // Existing feedback is optional UI state. A failed lookup must not
        // prevent a fresh rating or expose a noisy error before interaction.
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingExisting(false);
      });

    return () => controller.abort();
  }, [traceId]);

  const provenance = {
    ...(APP_COMMIT ? { app_commit: APP_COMMIT } : {}),
    ...(model ? { model } : {}),
  };

  const chooseRating = (value: number) => {
    if (loadingExisting || savingRating) return;
    const previous = rating;
    setRating(value);
    setShowImpression(true);
    setSavingRating(true);

    void submitAnswerFeedback({ trace_id: traceId, rating: value, ...provenance })
      .then(() => showToast(t('answerFeedback.toasts.ratingSaved'), 'success'))
      .catch(() => {
        setRating(previous);
        if (previous === null) setShowImpression(false);
        showToast(t('answerFeedback.toasts.saveFailed'), 'error');
      })
      .finally(() => setSavingRating(false));
  };

  const sendComment = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleaned = comment.trim();
    if (!cleaned || savingComment) return;
    setSavingComment(true);
    setShowImpression(false);

    void submitAnswerFeedback({ trace_id: traceId, comment: cleaned, ...provenance })
      .then(() => {
        setComment('');
        showToast(t('answerFeedback.toasts.commentSaved'), 'success');
      })
      .catch(() => {
        setShowImpression(true);
        showToast(t('answerFeedback.toasts.saveFailed'), 'error');
      })
      .finally(() => setSavingComment(false));
  };

  const rememberSelection = () => {
    selectionAtOpenRef.current = selectedAnswerExcerpt(answerContainerRef.current);
  };

  const toggleReport = () => {
    if (!showReport) {
      setAnswerExcerpt(
        selectionAtOpenRef.current ?? selectedAnswerExcerpt(answerContainerRef.current),
      );
    }
    setShowReport((visible) => !visible);
  };

  const sendReport = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleaned = reportText.trim();
    if (!cleaned || savingReport) return;
    setSavingReport(true);
    setShowReport(false);

    void submitAnswerReport({
      trace_id: traceId,
      report_type: reportType,
      report_text: cleaned,
      ...(answerExcerpt ? { answer_excerpt: answerExcerpt } : {}),
      ...provenance,
    })
      .then(() => {
        setReportText('');
        setAnswerExcerpt(null);
        showToast(t('answerFeedback.toasts.reportSent'), 'success');
      })
      .catch(() => {
        setShowReport(true);
        showToast(t('answerFeedback.toasts.reportFailed'), 'error');
      })
      .finally(() => setSavingReport(false));
  };

  const visibleRating = hoveredRating ?? rating ?? 0;

  return (
    <section
      className="border-t border-amber-200/50 pt-4"
      aria-label={t('answerFeedback.regionLabel')}
      data-testid="answer-feedback"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-medium text-stone-600">
            {t('answerFeedback.ratingLabel')}
          </p>
          {loadingExisting && (
            <span className="sr-only" role="status">
              {t('answerFeedback.loading')}
            </span>
          )}
        </div>
        <div
          className="flex items-center gap-0.5"
          role="group"
          aria-label={t('answerFeedback.ratingGroupLabel')}
          onMouseLeave={() => setHoveredRating(null)}
        >
          {RATINGS.map((value) => (
            <button
              key={value}
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-full text-stone-300 transition-colors hover:bg-amber-50 hover:text-amber-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 disabled:cursor-wait disabled:opacity-50"
              onMouseEnter={() => setHoveredRating(value)}
              onFocus={() => setHoveredRating(value)}
              onBlur={() => setHoveredRating(null)}
              onClick={() => chooseRating(value)}
              disabled={loadingExisting || savingRating}
              aria-label={t('answerFeedback.ratingValue', { value })}
              aria-pressed={rating === value}
            >
              <Star
                className={`h-5 w-5 ${
                  value <= visibleRating ? 'fill-amber-400 text-amber-500' : 'fill-transparent'
                }`}
                aria-hidden="true"
              />
            </button>
          ))}
        </div>
      </div>

      {showImpression && (
        <div className="mt-3 rounded-xl border border-amber-200/70 bg-parchment-50/70 px-4 py-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-display text-[15px] text-stone-800">
                {t('answerFeedback.impressionPrompt')}
              </p>
              <p className="mt-0.5 text-[11px] leading-4 text-stone-500">
                {t('answerFeedback.impressionHint')}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowImpression(false)}
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-stone-400 hover:bg-white hover:text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500"
              aria-label={t('answerFeedback.dismissImpression')}
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <form onSubmit={sendComment} className="mt-3">
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              maxLength={COMMENT_MAX_LENGTH}
              rows={3}
              className="block w-full resize-y rounded-lg border-amber-200 bg-white px-3 py-2 text-sm leading-5 text-stone-800 placeholder:text-stone-400 focus:border-orange-400 focus:ring-orange-400"
              placeholder={t('answerFeedback.commentPlaceholder')}
              aria-label={t('answerFeedback.commentLabel')}
            />
            <div className="mt-2 flex items-center justify-between gap-3">
              <span className="text-[10px] tabular-nums text-stone-400">
                {comment.length}/{COMMENT_MAX_LENGTH}
              </span>
              <button
                type="submit"
                disabled={!comment.trim() || savingComment}
                className="inline-flex min-h-10 items-center gap-1.5 rounded-full bg-orange-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-45"
              >
                <Send className="h-3.5 w-3.5" aria-hidden="true" />
                {savingComment
                  ? t('answerFeedback.sending')
                  : t('answerFeedback.sendImpression')}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="mt-2">
        <button
          type="button"
          onPointerDown={rememberSelection}
          onClick={toggleReport}
          className="inline-flex min-h-11 items-center gap-1.5 rounded-lg px-1 text-xs font-medium text-stone-500 underline decoration-stone-300 underline-offset-4 transition-colors hover:text-orange-700 hover:decoration-orange-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
          aria-expanded={showReport}
        >
          <Flag className="h-3.5 w-3.5" aria-hidden="true" />
          {t('answerFeedback.reportButton')}
        </button>
      </div>

      {showReport && (
        <form
          onSubmit={sendReport}
          className="mt-2 rounded-xl border border-stone-200 bg-stone-50/70 px-4 py-4"
          data-testid="answer-report-form"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-display text-base text-stone-800">
                {t('answerFeedback.reportTitle')}
              </h3>
              <p className="mt-0.5 text-[11px] leading-4 text-stone-500">
                {t('answerFeedback.reportHint')}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowReport(false)}
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-stone-400 hover:bg-white hover:text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500"
              aria-label={t('answerFeedback.closeReport')}
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          {answerExcerpt && (
            <div className="mt-3 flex gap-2 rounded-lg border border-amber-200 bg-amber-50/70 px-3 py-2">
              <Quote className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-700">
                  {t('answerFeedback.excerptLabel')}
                </p>
                <p className="mt-1 line-clamp-3 text-xs leading-5 text-stone-700">
                  {answerExcerpt}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAnswerExcerpt(null)}
                className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-amber-700 hover:bg-white"
                aria-label={t('answerFeedback.removeExcerpt')}
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </div>
          )}

          <div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]">
            <label className="text-xs font-medium text-stone-700">
              {t('answerFeedback.typeLabel')}
              <select
                value={reportType}
                onChange={(event) => setReportType(event.target.value as AnswerReportType)}
                className="mt-1 block min-h-11 w-full rounded-lg border-stone-200 bg-white px-3 py-2 text-sm text-stone-800 focus:border-orange-400 focus:ring-orange-400"
              >
                {REPORT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {t(`answerFeedback.reportTypes.${type}`)}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-medium text-stone-700">
              {t('answerFeedback.detailsLabel')}
              <textarea
                value={reportText}
                onChange={(event) => setReportText(event.target.value)}
                maxLength={REPORT_MAX_LENGTH}
                rows={4}
                required
                className="mt-1 block w-full resize-y rounded-lg border-stone-200 bg-white px-3 py-2 text-sm leading-5 text-stone-800 placeholder:text-stone-400 focus:border-orange-400 focus:ring-orange-400"
                placeholder={t('answerFeedback.reportPlaceholder')}
              />
            </label>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-[10px] tabular-nums text-stone-400">
              {reportText.length}/{REPORT_MAX_LENGTH}
            </span>
            <button
              type="submit"
              disabled={!reportText.trim() || savingReport}
              className="inline-flex min-h-10 items-center gap-1.5 rounded-full bg-stone-800 px-4 py-2 text-xs font-semibold text-stone-50 transition-colors hover:bg-stone-900 disabled:cursor-not-allowed disabled:opacity-45"
            >
              <Send className="h-3.5 w-3.5" aria-hidden="true" />
              {savingReport ? t('answerFeedback.sending') : t('answerFeedback.sendReport')}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
