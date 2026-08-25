/**
 * BilingualLocus — a facing-page unit, not a quote card.
 *
 * The conventions here are Loeb, Budé and Sources Chrétiennes, and a
 * classicist reads by them:
 *   1. the original and the translation carry comparable optical weight; the
 *      translation is not a caption underneath a decorative pull quote;
 *   2. the original is set in the reading face, never the display face, and
 *      Instrument Serif has no Greek at all, so `font-garamond` is not a
 *      preference here, it is the difference between Greek and Georgia;
 *   3. leading is asymmetric, because polytonic diacritics stack and 1.4 puts
 *      one line's breathings into the next line's ascenders;
 *   4. the reference hangs in the margin as apparatus, with the CTS URN
 *      present, selectable and copyable, which is the FAIR promise made
 *      visible and the one legitimate use of a monospace face on this page;
 *   5. the original is NEVER truncated. Slicing a primary text at a character
 *      count invents a fragment boundary no edition has.
 *
 * Below md the two halves stack, original first. That is not an amputation:
 * facing-page becomes interlinear, which is equally canonical.
 */

import { Link } from 'react-router-dom';

import { cn } from '../../utils/cn';
import { ANCIENT_LEADING, ANCIENT_MEASURE, EDITION_ORTHOGRAPHY, TONE } from './tone';
import type { Locus, LocusState, Tone } from './types';

export interface BilingualLocusProps {
  state: LocusState;
  tone: Tone;
  /** Corpus route for "continue in the edition". */
  workCanonicalId?: string;
  /** Retry the fetch. Without one, an error state is just an apology. */
  onRetry?: () => void;
  className?: string;
}

export function BilingualLocus({
  state,
  tone,
  workCanonicalId,
  onRetry,
  className,
}: BilingualLocusProps) {
  const t = TONE[tone];

  if (state.status === 'loading') {
    return <LocusSkeleton tone={tone} className={className} />;
  }

  if (state.status === 'error') {
    return (
      <LocusNotice
        className={className}
        tone={tone}
        title="The corpus did not answer."
        body="The text exists. The request did not arrive."
        action={
          onRetry ? { label: 'Ask again', onClick: onRetry } : undefined
        }
      />
    );
  }

  if (state.status === 'empty') {
    return (
      <LocusNotice
        className={className}
        tone={tone}
        title="No passage indexed at this locus yet."
        body="The argument survives. The file does not, or not here. Nothing has been withheld and nothing has been reconstructed to fill the gap."
      />
    );
  }

  const { locus } = state;
  const lang = locus.originalLang;

  return (
    <figure className={cn('relative', className)}>
      <LocusApparatus locus={locus} tone={tone} />

      <div className="grid gap-x-12 gap-y-8 md:grid-cols-2 md:items-start">
        <blockquote
          lang={lang}
          className={cn(
            'font-garamond text-[1.25rem] text-stone-900 [text-wrap:pretty]',
            ANCIENT_LEADING[lang],
            ANCIENT_MEASURE[lang],
            EDITION_ORTHOGRAPHY[lang],
            'border-l-2 pl-6',
            t.rule,
          )}
        >
          {locus.original}
        </blockquote>

        {locus.translation && (
          <p
            lang="en"
            className="max-w-[54ch] font-garamond text-[1.0625rem] leading-[1.7] text-stone-600 [text-wrap:pretty]"
          >
            {locus.translation}
          </p>
        )}
      </div>

      {locus.note && (
        <p className="mt-7 max-w-[62ch] border-t border-stone-200 pt-4 font-body text-[0.8125rem] leading-[1.6] text-stone-600">
          {locus.note}
        </p>
      )}

      {workCanonicalId && (
        <Link
          to={`/texts/${encodeURIComponent(workCanonicalId)}`}
          className={cn(
            'mt-6 inline-flex min-h-11 items-center font-body text-[0.8125rem] text-stone-500',
            'underline-offset-4 transition-colors duration-200 hover:text-stone-900 hover:underline',
            'motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          Continue in the edition
        </Link>
      )}
    </figure>
  );
}

function LocusApparatus({ locus, tone }: { locus: Locus; tone: Tone }) {
  const t = TONE[tone];
  if (!locus.reference && !locus.urn) return null;
  return (
    <figcaption className="mb-6 flex flex-wrap items-baseline gap-x-4 gap-y-1.5">
      {locus.reference && (
        <cite className={cn('font-body text-[0.8125rem] font-medium not-italic', t.ink)}>
          {locus.reference}
        </cite>
      )}
      {locus.urn && (
        <code className="select-all font-mono text-[0.6875rem] text-stone-500">
          {locus.urn}
        </code>
      )}
    </figcaption>
  );
}

/**
 * A skeleton in the shape of the thing: two columns of ruled lines with a
 * marginal reference above them. Three generic grey bars announce a paragraph
 * and then hand the reader a bilingual spread, which is a layout jump and a
 * small lie about what is coming.
 */
function LocusSkeleton({ tone, className }: { tone: Tone; className?: string }) {
  const t = TONE[tone];
  return (
    <div className={cn('relative', className)} role="status" aria-live="polite">
      <div className="mb-6 h-3 w-52 rounded-sm bg-stone-200/80" />
      <div className="grid gap-x-12 gap-y-8 md:grid-cols-2 md:items-start">
        <div className={cn('space-y-3.5 border-l-2 pl-6', t.rule)}>
          <div className="h-3 w-full rounded-sm bg-stone-200/80" />
          <div className="h-3 w-11/12 rounded-sm bg-stone-200/80" />
          <div className="h-3 w-full rounded-sm bg-stone-200/80" />
          <div className="h-3 w-4/5 rounded-sm bg-stone-200/80" />
        </div>
        <div className="space-y-3.5">
          <div className="h-3 w-full rounded-sm bg-stone-200/60" />
          <div className="h-3 w-full rounded-sm bg-stone-200/60" />
          <div className="h-3 w-3/4 rounded-sm bg-stone-200/60" />
        </div>
      </div>
      <p className="mt-6 font-body text-[0.8125rem] text-stone-500">
        Fetching the passage. It has waited seventeen centuries and can manage
        another moment.
      </p>
    </div>
  );
}

function LocusNotice({
  tone,
  title,
  body,
  action,
  className,
}: {
  tone: Tone;
  title: string;
  body: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}) {
  const t = TONE[tone];
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('border-l-2 pl-6', t.rule, className)}
    >
      <p className="font-garamond text-[1.125rem] leading-[1.55] text-stone-700">
        {title}
      </p>
      <p className="mt-2 max-w-[54ch] font-body text-[0.875rem] leading-[1.65] text-stone-600">
        {body}
      </p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className={cn(
            'mt-4 inline-flex min-h-11 items-center border-b border-stone-400 pb-0.5',
            'font-body text-[0.875rem] text-stone-700 transition-colors duration-200',
            'hover:border-stone-900 hover:text-stone-900 motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

export default BilingualLocus;
