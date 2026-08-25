/**
 * ThinkerStation — one figure, composed as a movement rather than a slide.
 *
 * The page is a contested field, not a chain of replies, so nothing here may
 * imply succession: no arrow into the next figure, no ordinal, no "answers X"
 * chain running down the margin. What each station carries instead is what a
 * historian would actually want:
 *   stance      what they hold
 *   locus       the text it rests on, in the original, facing a translation
 *   contested   the modern disagreement about them, named and left open
 *   opponent    who they argued against, which is a fact, not a narrative
 *   inheritsFrom  attested reuse, which is drawn on the rail as an arc
 *
 * `contested` sits in the main column under the evidence, not in the sidebar,
 * because on this page it is the thesis. It is marked by the sage rule, which
 * in this palette means modern scholarship, so the categorisation is carried
 * by the colour system instead of by an uppercase eyebrow label.
 *
 * A sticky header keeps the reader's place while the section scrolls, and,
 * because two stations can be on screen at once, the page's own claim (that
 * these are positions to be compared, not steps to be taken) is finally
 * something the layout permits rather than forbids.
 */

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { cn } from '../../utils/cn';
import BilingualLocus from './BilingualLocus';
import { TONE } from './tone';
import type { LocusState, ThinkerLike } from './types';

export interface ThinkerStationProps {
  thinker: ThinkerLike;
  locus: LocusState;
  onRetryLocus?: () => void;
  /** Live knowledge-graph prose. Rendered as apparatus, never as the lede. */
  description?: ReactNode;
  /** Where the sticky header parks. Pass a Tailwind class, e.g. `top-16`. */
  stickyTopClass?: string;
  className?: string;
}

export function ThinkerStation({
  thinker,
  locus,
  onRetryLocus,
  description,
  stickyTopClass = 'top-16',
  className,
}: ThinkerStationProps) {
  const t = TONE[thinker.tone];
  const coda = thinker.coda === true;

  // The chosen locus and its transmission note live on the thinker record,
  // because they are editorial decisions, not something the API knows. The
  // corpus fills in whatever it happens to carry; the record wins where both
  // have something, and the apparatus is rendered once, in the right place.
  const resolved: LocusState =
    locus.status === 'ready'
      ? {
          status: 'ready',
          locus: {
            ...locus.locus,
            reference: thinker.passageRef ?? locus.locus.reference,
            note: locus.locus.note ?? thinker.passageNote,
          },
        }
      : locus;

  return (
    <article
      id={thinker.id}
      aria-labelledby={`${thinker.id}-name`}
      className={cn(
        'relative scroll-mt-24',
        coda && 'border-t border-stone-300 pt-16',
        className,
      )}
    >
      <header
        className={cn(
          'sticky z-20 -mx-4 mb-10 border-b border-stone-200 bg-parchment-50/95 px-4 py-3 backdrop-blur-[2px]',
          'flex flex-wrap items-baseline gap-x-5 gap-y-1',
          stickyTopClass,
        )}
      >
        <h2
          id={`${thinker.id}-name`}
          className={cn(
            'font-display text-[clamp(1.75rem,1.2rem+1.6vw,2.75rem)] leading-[1.05] tracking-[-0.015em]',
            'text-stone-900',
          )}
        >
          {thinker.name}
        </h2>
        <p className="font-body text-[0.8125rem] tabular-nums text-stone-600">
          {thinker.dates}
        </p>
        <p className="font-body text-[0.8125rem] text-stone-600">{thinker.school}</p>
        <span
          className={cn(
            'ml-auto font-body text-[0.6875rem] uppercase tracking-[0.16em]',
            t.ink,
          )}
        >
          {t.label}
        </span>
      </header>

      <div
        className={cn(
          'grid gap-x-16 gap-y-12',
          !coda && 'xl:grid-cols-[minmax(0,1fr)_minmax(0,17rem)]',
        )}
      >
        <div className={cn('min-w-0', coda && 'max-w-[62ch]')}>
          <p
            className={cn(
              'font-garamond text-[clamp(1.3125rem,1.1rem+0.6vw,1.625rem)] leading-[1.5]',
              'max-w-[40ch] text-stone-900 [text-wrap:pretty]',
            )}
          >
            {thinker.stance}
          </p>

          <BilingualLocus
            state={resolved}
            tone={thinker.tone}
            workCanonicalId={thinker.workCanonicalId}
            onRetry={onRetryLocus}
            className="mt-12"
          />

          {/* The disagreement. Sage rule, because in this palette sage is the
              modern layer. It is left open on purpose and it is not a footnote. */}
          <div
            className={cn(
              'mt-14 border-l-2 pl-6',
              TONE.meta.rule,
            )}
          >
            <p className="max-w-[58ch] font-body text-[1.0625rem] leading-[1.65] text-stone-700">
              {thinker.contested}
            </p>
          </div>
        </div>

        {!coda && (
          <aside className="min-w-0 space-y-8 xl:pt-2">
            <div className="border-t border-stone-200 pt-4">
              <p className="max-w-[36ch] font-body text-[0.875rem] leading-[1.6] text-stone-600">
                Argued against {thinker.opponent}.
              </p>
              {thinker.inheritsFrom && thinker.inheritsFrom.length > 0 && (
                <p className="mt-2.5 max-w-[36ch] font-body text-[0.875rem] leading-[1.6] text-stone-600">
                  Reuses arguments attested in {listOf(thinker.inheritsFrom)}.
                </p>
              )}
            </div>

            {description && (
              <div className="border-t border-stone-200 pt-4">
                <div className="max-w-[38ch] font-body text-[0.875rem] leading-[1.65] text-stone-600">
                  {description}
                </div>
              </div>
            )}

            <div className="border-t border-stone-200 pt-4">
              <Link
                to={`/visualizer?node=${encodeURIComponent(thinker.nodeId)}`}
                className={cn(
                  'inline-flex min-h-11 items-center font-body text-[0.8125rem] text-stone-500',
                  'underline-offset-4 transition-colors duration-200 hover:text-stone-900 hover:underline',
                  'motion-reduce:transition-none',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
                )}
              >
                {thinker.nav} in the knowledge graph
              </Link>
            </div>
          </aside>
        )}
      </div>
    </article>
  );
}

function listOf(names: readonly string[]): string {
  if (names.length === 1) return names[0];
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}

export default ThinkerStation;
