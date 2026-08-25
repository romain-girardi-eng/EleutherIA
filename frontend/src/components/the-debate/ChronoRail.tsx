/**
 * ChronoRail — the debate drawn to scale, silence included.
 *
 * The rail is a chronological axis, not a table of contents. Marks sit at
 * their true position on the span, which means the reader learns the shape of
 * the argument before reading a word of it: a cluster of Hellenistic voices,
 * then the longest stretch of the whole rail with nobody on it, then three
 * late-antique replies crowded into the last third.
 *
 * The widest gap is computed, named, and populated with the figures who are in
 * the knowledge graph but not on this page. Naming the silence is the point:
 * an evenly-spaced dot list asserts that these eight were talking to each
 * other at a steady cadence, and they were not.
 *
 * Drawn in SVG on purpose. Percentages cannot be expressed as Tailwind classes
 * at runtime and this repo forbids inline `style`, so the coordinate system
 * lives where coordinate systems belong. The SVG is `aria-hidden` and carries
 * a full textual equivalent beneath it — which also removes the eleven tab
 * stops a clickable rail would have put in front of the content.
 */

import { useMemo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

import { cn } from '../../utils/cn';
import { TONE } from './tone';
import {
  arcPath,
  chronoScale,
  fractionOf,
  ghostsWithin,
  intervalLabel,
  largestSilence,
  type ChronoArc,
  type ChronoGhost,
  type ChronoStation,
} from './chronology';

export interface ChronoRailProps {
  stations: readonly ChronoStation[];
  /** In the graph, not on the page. They are what stands in the silence. */
  ghosts?: readonly ChronoGhost[];
  /** Attested argument reuse. `from` reuses `to`; the arc reaches backwards. */
  arcs?: readonly ChronoArc[];
  activeId?: string | null;
  orientation?: 'vertical' | 'horizontal';
  className?: string;
}

const V = { w: 288, h: 760, pad: 30, rail: 132 } as const;
const H = { w: 1000, h: 48, pad: 5, rail: 24 } as const;

export function ChronoRail({
  stations,
  ghosts = [],
  arcs = [],
  activeId = null,
  orientation = 'vertical',
  className,
}: ChronoRailProps) {
  const reduce = useReducedMotion();

  const model = useMemo(() => {
    const scale = chronoScale(stations);
    const silence = largestSilence(stations);
    return {
      scale,
      silence,
      inSilence: ghostsWithin(ghosts, silence, stations),
      byId: new Map(stations.map((s) => [s.id, s] as const)),
    };
  }, [stations, ghosts]);

  const { scale, silence, inSilence, byId } = model;
  const activeStation = activeId ? byId.get(activeId) : undefined;
  const vertical = orientation === 'vertical';
  const G = vertical ? V : H;
  const usable = (vertical ? G.h : G.w) - G.pad * 2;
  const at = (year: number) => G.pad + fractionOf(year, scale) * usable;

  return (
    <figure className={cn('relative', className)}>
      {/* Horizontal variant: the axis stretches, the marks do not. Everything
          drawn on it is a vertical line, so anisotropic scaling is exact
          rather than a distortion and the tick positions stay truthful at any
          width. It is also why no text is drawn inside it: text would stretch.
          The labels live in real HTML underneath, at a fixed size, which is
          the one thing that made this readable on a phone. */}
      <svg
        viewBox={`0 0 ${G.w} ${G.h}`}
        className={cn(vertical ? 'h-full w-auto' : 'h-12 w-full')}
        preserveAspectRatio={vertical ? 'xMinYMid meet' : 'none'}
        aria-hidden
        focusable="false"
      >
        {/* The rail, drawn as segments so the silence is a real break in the
            line rather than a dotted overlay on an unbroken one. A rail that
            runs continuously through four missing centuries is telling the
            reader the argument ran continuously, which is the claim this
            component exists to withdraw. */}
        {segments(G, usable, silence, vertical).map((seg) => (
          <line
            key={seg.key}
            x1={seg.x1}
            y1={seg.y1}
            x2={seg.x2}
            y2={seg.y2}
            className={seg.gap ? 'stroke-stone-400' : 'stroke-stone-300'}
            strokeWidth={1}
            strokeDasharray={seg.gap ? '1 6' : undefined}
            strokeLinecap={seg.gap ? 'round' : undefined}
            vectorEffect="non-scaling-stroke"
          />
        ))}

        {silence && (
          <>
            {vertical ? (
              <text
                x={G.rail + 34}
                y={G.pad + ((silence.startFraction + silence.endFraction) / 2) * usable}
                transform={`rotate(-90 ${G.rail + 34} ${
                  G.pad + ((silence.startFraction + silence.endFraction) / 2) * usable
                })`}
                textAnchor="middle"
                className="fill-stone-500 font-body text-[11px] uppercase tracking-[0.18em]"
              >
                {intervalLabel(silence.years)} unread here
              </text>
            ) : null}
          </>
        )}

        {/* Attested reuse, reaching backwards. Vertical only: on a phone these
            would be four hairlines in a 96-unit band, which is noise. */}
        {vertical &&
          arcs.map((arc) => {
            const from = byId.get(arc.from);
            const to = byId.get(arc.to);
            if (!from || !to) return null;
            const live = activeId === arc.from || activeId === arc.to;
            return (
              <motion.path
                key={`${arc.from}->${arc.to}`}
                d={arcPath(G.rail, at(from.year), at(to.year), true)}
                fill="none"
                strokeWidth={1}
                className={cn(TONE[from.tone].stroke)}
                initial={{ pathLength: reduce ? 1 : 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: live ? 0.72 : 0.16 }}
                transition={{
                  duration: reduce ? 0 : 1.15,
                  ease: [0.16, 1, 0.3, 1],
                }}
              />
            );
          })}

        {/* Ghosts: dotted leader out to the left, name set small. Present on the
            scale, absent from the page — which is exactly their status. */}
        {vertical &&
          ghosts.map((ghost) => {
            const y = at(ghost.year);
            return (
              <g key={ghost.id}>
                <line
                  x1={96}
                  y1={y}
                  x2={G.rail}
                  y2={y}
                  className="stroke-stone-300"
                  strokeWidth={1}
                  strokeDasharray="1.5 3"
                />
                <text
                  x={88}
                  y={y - 2}
                  textAnchor="end"
                  className="fill-stone-500 font-body text-[11px]"
                >
                  {ghost.label}
                </text>
                <text
                  x={88}
                  y={y + 11}
                  textAnchor="end"
                  className="fill-stone-400 font-body text-[10px] tabular-nums"
                >
                  {ghost.yearLabel}
                </text>
              </g>
            );
          })}

        {!vertical &&
          ghosts.map((ghost) => (
            <line
              key={ghost.id}
              x1={at(ghost.year)}
              y1={G.rail - 8}
              x2={at(ghost.year)}
              y2={G.rail}
              className="stroke-stone-400"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          ))}

        {/* Stations. */}
        {stations.map((station) => {
          const tone = TONE[station.tone];
          const active = station.id === activeId;
          const p = at(station.year);
          if (vertical) {
            return (
              <g key={station.id}>
                <line
                  x1={G.rail}
                  y1={p}
                  x2={G.rail + (active ? 20 : 13)}
                  y2={p}
                  className={cn(
                    active ? tone.stroke : 'stroke-stone-400',
                    'transition-[stroke] duration-500 motion-reduce:transition-none',
                  )}
                  strokeWidth={active ? 2 : 1}
                />
                <circle
                  cx={G.rail}
                  cy={p}
                  r={active ? 3.5 : 0}
                  className={cn(tone.fill)}
                />
                <text
                  x={G.rail + (active ? 30 : 23)}
                  y={p + 4}
                  className={cn(
                    'font-body text-[12.5px]',
                    active ? tone.fill : 'fill-stone-500',
                  )}
                >
                  {station.label}
                  <tspan
                    className={cn(
                      'text-[10.5px] tabular-nums',
                      active ? tone.fill : 'fill-stone-400',
                    )}
                  >
                    {'  '}
                    {station.yearLabel}
                  </tspan>
                </text>
              </g>
            );
          }
          return (
            <line
              key={station.id}
              x1={p}
              y1={G.rail}
              x2={p}
              y2={G.rail + (active ? 20 : 11)}
              className={cn(active ? tone.stroke : 'stroke-stone-400')}
              strokeWidth={active ? 2 : 1}
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

      {!vertical && (
        <div
          className="mt-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 font-body text-[0.75rem] text-stone-500"
          aria-hidden
        >
          <span className="tabular-nums">
            {stations[0]?.yearLabel} to {stations[stations.length - 1]?.yearLabel}
          </span>
          {silence && (
            <span>
              {intervalLabel(silence.years)} unread between {silence.fromLabel}{' '}
              and {silence.toLabel}
            </span>
          )}
          {activeStation && (
            <span className={cn('font-medium', TONE[activeStation.tone].ink)}>
              {activeStation.label}, {activeStation.yearLabel}
            </span>
          )}
        </div>
      )}

      {/* The textual equivalent. Not a fallback — for a chronology it is the
          better reading, so it says the intervals out loud. */}
      <figcaption className="sr-only">
        <p>
          Chronological rail, {stations.length} stations drawn to true scale
          between {stations[0]?.yearLabel} and{' '}
          {stations[stations.length - 1]?.yearLabel}. Marks are placed by the
          date of the work, not the life.
        </p>
        <ol>
          {stations.map((station) => (
            <li key={station.id}>
              {station.label}, {station.yearLabel}, {TONE[station.tone].label}
              {station.id === activeId ? ' (currently reading)' : ''}
            </li>
          ))}
        </ol>
        {silence && (
          <p>
            The longest interval on the rail is {intervalLabel(silence.years)}{' '}
            between {silence.fromLabel} and {silence.toLabel}, which is{' '}
            {Math.round(silence.share * 100)} per cent of the whole span.
            {inSilence.length > 0 && (
              <>
                {' '}
                Standing in it, in the knowledge graph but not on this page:{' '}
                {inSilence.map((g) => `${g.label} (${g.yearLabel})`).join(', ')}.
              </>
            )}
          </p>
        )}
        {arcs.length > 0 && (
          <p>
            Attested reuse of argument:{' '}
            {arcs
              .map((a) => {
                const from = byId.get(a.from);
                const to = byId.get(a.to);
                return from && to ? `${from.label} reuses ${to.label}` : null;
              })
              .filter(Boolean)
              .join('; ')}
            .
          </p>
        )}
      </figcaption>
    </figure>
  );
}

interface RailSegment {
  key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  gap: boolean;
}

/** The rail, cut at the silence. Three segments, or one when nothing is missing. */
function segments(
  G: typeof V | typeof H,
  usable: number,
  silence: { startFraction: number; endFraction: number } | null,
  vertical: boolean,
): RailSegment[] {
  const start = G.pad;
  const end = (vertical ? G.h : G.w) - G.pad;
  const seg = (key: string, a: number, b: number, gap: boolean): RailSegment =>
    vertical
      ? { key, x1: G.rail, y1: a, x2: G.rail, y2: b, gap }
      : { key, x1: a, y1: G.rail, x2: b, y2: G.rail, gap };

  if (!silence) return [seg('rail', start, end, false)];
  const from = G.pad + silence.startFraction * usable;
  const to = G.pad + silence.endFraction * usable;
  return [
    seg('before', start, from, false),
    seg('silence', from, to, true),
    seg('after', to, end, false),
  ];
}

export default ChronoRail;
