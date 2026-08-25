/**
 * DebateOutro — the hand-off, with nothing resolved.
 *
 * The one thing this may not do is round the page off into a conclusion. The
 * page argues that the field is contested; an outro that says "and so the
 * matter was settled by Boethius" would undo eight stations of work in two
 * sentences. So the closing gesture is the rail again, whole, silence and all,
 * with no station marked active: the shape of the argument, still open.
 *
 * Boethius wrote the Consolatio awaiting execution. The coda is not where the
 * page is funny, and neither is this. The one dry line here is aimed at the
 * reader's expectation of a verdict, not at anybody's death.
 */

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { cn } from '../../utils/cn';

export interface DebateOutroProps {
  heading?: string;
  body?: string;
  /** Aimed at the expectation of a verdict. Never at a person. */
  aside?: string;
  /** A full-width ChronoRail with no active station reads best here. */
  rail?: ReactNode;
  className?: string;
}

export function DebateOutro({
  heading = 'The argument did not close.',
  body = 'It went to the Middle Ages unsettled, and the scholarship about it is unsettled too. Every figure, work, passage and citation on this page is a live record you can open, follow and cite.',
  aside = 'If you were expecting a conclusion, so were they.',
  rail,
  className,
}: DebateOutroProps) {
  return (
    <section
      className={cn('relative', className)}
      aria-labelledby="debate-outro-heading"
    >
      {rail && <div className="mb-14">{rail}</div>}

      <h2
        id="debate-outro-heading"
        className={cn(
          'font-display text-[clamp(2.25rem,1.4rem+2.8vw,4rem)] leading-[1.02] tracking-[-0.02em]',
          'max-w-[15ch] text-stone-900',
        )}
      >
        {heading}
      </h2>

      <p className="mt-6 max-w-[54ch] font-garamond text-[1.1875rem] leading-[1.65] text-stone-700">
        {body}
      </p>

      {aside && (
        <p className="mt-4 max-w-[46ch] font-body text-[0.875rem] leading-[1.6] text-stone-500">
          {aside}
        </p>
      )}

      <div className="mt-12 flex flex-wrap items-center gap-x-10 gap-y-5">
        <Link
          to="/graphrag"
          className={cn(
            'inline-flex min-h-11 items-center border-b-2 border-[#B44A12] pb-1',
            'font-body text-[1rem] font-medium text-[#B44A12]',
            'transition-colors duration-200 hover:border-stone-900 hover:text-stone-900',
            'motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          Put the question to the corpus
        </Link>
        <Link
          to="/visualizer"
          className={cn(
            'inline-flex min-h-11 items-center border-b border-stone-400 pb-1',
            'font-body text-[0.9375rem] text-stone-600',
            'transition-colors duration-200 hover:border-stone-900 hover:text-stone-900',
            'motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#B44A12]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          Open the whole graph
        </Link>
      </div>
    </section>
  );
}

export default DebateOutro;
