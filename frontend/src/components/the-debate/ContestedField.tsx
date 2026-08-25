/**
 * ContestedField — the cross-cutting band.
 *
 * The obvious way to draw "a contested field" is a scatter plot with two axes,
 * and it would be a fabrication: nobody has published coordinates for these
 * scholars, so the positions would be invented and the figure would look more
 * authoritative than the evidence behind it. So the field is drawn the way the
 * disagreement actually has a shape.
 *
 * Each open question is one hairline with a position pulling from either end
 * and a GAP in the middle where a join would be. The gap is the design: it is
 * the only mark on this page that says "unresolved" without writing the word,
 * and it is never closed, on any question, at any breakpoint.
 *
 * The cross-cutting claim is then something the reader can verify rather than
 * be told: pick a name and it lights up everywhere it appears. A small number
 * of people disagree about several of these at once, which is what makes this
 * a field and not a sequence.
 *
 * Highlighting is additive. Nothing is dimmed to make something else stand
 * out, so no text ever drops below its contrast floor to serve an interaction.
 */

import { useMemo, useState } from 'react';

import { cn } from '../../utils/cn';
import { TONE } from './tone';

export interface ContestedPosition {
  /** Stable key for cross-highlighting. One scholar, one id. */
  scholarId: string;
  /** As cited: "Bobzien 1998". */
  scholar: string;
  claim: string;
  /** Which stations this bears on, by `nav`. */
  about?: readonly string[];
}

export interface ContestedQuestion {
  id: string;
  question: string;
  /** Two, or three. Four is a literature review, not a figure. */
  positions: readonly ContestedPosition[];
}

export interface ContestedFieldProps {
  heading?: string;
  lede?: string;
  questions: readonly ContestedQuestion[];
  className?: string;
}

export function ContestedField({
  heading = 'What scholars still argue about',
  lede = 'None of these is settled, and they are not stages of one dispute. The same few people disagree about several of them at once. Choose a name to see where else it appears.',
  questions,
  className,
}: ContestedFieldProps) {
  const [pinned, setPinned] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const active = hovered ?? pinned;

  const appearances = useMemo(() => {
    const counts = new Map<string, { name: string; count: number }>();
    for (const q of questions) {
      for (const p of q.positions) {
        const entry = counts.get(p.scholarId);
        if (entry) entry.count += 1;
        else counts.set(p.scholarId, { name: p.scholar, count: 1 });
      }
    }
    return counts;
  }, [questions]);

  const activeEntry = active ? appearances.get(active) : undefined;

  return (
    <section
      className={cn('relative', className)}
      aria-labelledby="contested-heading"
    >
      <h2
        id="contested-heading"
        className={cn(
          'font-display text-[clamp(2rem,1.3rem+2.2vw,3.25rem)] leading-[1.05] tracking-[-0.015em]',
          'max-w-[16ch] text-stone-900',
        )}
      >
        {heading}
      </h2>
      <p className="mt-5 max-w-[56ch] font-garamond text-[1.125rem] leading-[1.6] text-stone-600">
        {lede}
      </p>

      <p
        role="status"
        aria-live="polite"
        className="mt-6 min-h-[1.5rem] font-body text-[0.875rem] text-stone-600"
      >
        {activeEntry
          ? `${activeEntry.name.replace(/\s+\d{4}[a-z]?$/, '')} is on ${
              activeEntry.count === 1
                ? 'one of these questions'
                : `${activeEntry.count} of these questions`
            }.`
          : ''}
      </p>

      {questions.length === 0 ? (
        <p className="mt-10 font-garamond text-[1.125rem] text-stone-600">
          Nothing contested here. Historically improbable.
        </p>
      ) : (
        <ul className="mt-12 space-y-16">
          {questions.map((q) => (
            <li key={q.id}>
              <h3 className="max-w-[34ch] font-display text-[1.5rem] leading-[1.2] text-stone-900">
                {q.question}
              </h3>

              <div
                className={cn(
                  'mt-7 grid gap-y-8',
                  q.positions.length > 2
                    ? 'md:grid-cols-[minmax(0,1fr)_2.5rem_minmax(0,1fr)_2.5rem_minmax(0,1fr)]'
                    : 'md:grid-cols-[minmax(0,1fr)_3rem_minmax(0,1fr)]',
                )}
              >
                {q.positions.map((position, i) => (
                  <PositionCell
                    key={position.scholarId + i}
                    position={position}
                    isActive={active === position.scholarId}
                    isPinned={pinned === position.scholarId}
                    onHover={setHovered}
                    onPin={(id) => setPinned((cur) => (cur === id ? null : id))}
                    withGapBefore={i > 0}
                  />
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface PositionCellProps {
  position: ContestedPosition;
  isActive: boolean;
  isPinned: boolean;
  withGapBefore: boolean;
  onHover: (id: string | null) => void;
  onPin: (id: string) => void;
}

function PositionCell({
  position,
  isActive,
  isPinned,
  withGapBefore,
  onHover,
  onPin,
}: PositionCellProps) {
  return (
    <>
      {withGapBefore && <BrokenRule />}
      <div className="min-w-0">
        <button
          type="button"
          aria-pressed={isPinned}
          onClick={() => onPin(position.scholarId)}
          onMouseEnter={() => onHover(position.scholarId)}
          onMouseLeave={() => onHover(null)}
          onFocus={() => onHover(position.scholarId)}
          onBlur={() => onHover(null)}
          className={cn(
            'inline-flex min-h-11 items-center font-body text-[0.9375rem] font-medium',
            'border-b transition-colors duration-200 motion-reduce:transition-none',
            isActive
              ? cn(TONE.meta.ink, 'border-[#44513F]')
              : 'border-transparent text-stone-700 hover:border-stone-400',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#44513F]/60 focus-visible:ring-offset-4 focus-visible:ring-offset-parchment-50',
          )}
        >
          {position.scholar}
        </button>
        <p className="mt-2 max-w-[40ch] font-garamond text-[1.0625rem] leading-[1.65] text-stone-700 [text-wrap:pretty]">
          {position.claim}
        </p>
        {position.about && position.about.length > 0 && (
          <p className="mt-2.5 font-body text-[0.8125rem] text-stone-500">
            On {position.about.join(', ')}.
          </p>
        )}
      </div>
    </>
  );
}

/**
 * The unresolved point. Two hairlines reaching for each other and stopping.
 * On a phone it turns ninety degrees and keeps the gap.
 */
function BrokenRule() {
  return (
    <div
      aria-hidden
      className="flex items-center justify-center gap-2 md:flex-col md:gap-0"
    >
      <span className="h-px flex-1 bg-stone-300 md:h-auto md:w-px md:flex-1" />
      <span className="h-px w-12 md:h-14 md:w-px" />
      <span className="h-px flex-1 bg-stone-300 md:h-auto md:w-px md:flex-1" />
    </div>
  );
}

export default ContestedField;
