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
const H = { w: 720, h: 96, pad: 26, rail: 52 } as const;

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
  const vertical = orientation === 'vertical';
  const G = vertical ? V : H;
  const usable = (vertical ? G.h : G.w) - G.pad * 2;
  const at = (year: number) => G.pad + fractionOf(year, scale) * usable;

  return (
    <figure className={cn('relative', className)}>
      <svg
        viewBox={`0 0 ${G.w} ${G.h}`}
        className={cn(vertical ? 'h-full w-auto' : 'h-auto w-full')}
        preserveAspectRatio={vertical ? 'xMinYMid meet' : 'xMidYMid meet'}
        aria-hidden
        focusable="false"
      >
        {/* The rail itself. One hairline, drawn once. */}
        {vertical ? (
          <line
            x1={G.rail}
            y1={G.pad}
            x2={G.rail}
            y2={G.h - G.pad}
            className="stroke-stone-300"
            strokeWidth={1}
          />
        ) : (
          <line
            x1={G.pad}
            y1={G.rail}
            x2={G.w - G.pad}
            y2={G.rail}
            className="stroke-stone-300"
            strokeWidth={1}
          />
        )}

        {/* The silence: the rail stops being a line and becomes a dotted one. */}
        {silence && (
          <>
            {vertical ? (
              <line
                x1={G.rail}
                y1={G.pad + silence.startFraction * usable}
                x2={G.rail}
                y2={G.pad + silence.endFraction * usable}
                className="stroke-stone-400"
                strokeWidth={1}
                strokeDasharray="1 6"
                strokeLinecap="round"
              />
            ) : (
              <line
                x1={G.pad + silence.startFraction * usable}
                y1={G.rail}
                x2={G.pad + silence.endFraction * usable}
                y2={G.rail}
                className="stroke-stone-400"
                strokeWidth={1}
                strokeDasharray="1 6"
                strokeLinecap="round"
              />
            )}
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
            ) : (
              <text
                x={G.pad + ((silence.startFraction + silence.endFraction) / 2) * usable}
                y={G.rail - 16}
                textAnchor="middle"
                className="fill-stone-500 font-body text-[12px] uppercase tracking-[0.16em]"
              >
                {intervalLabel(silence.years)} unread
              </text>
            )}
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
                  y={y + 3.5}
                  textAnchor="end"
                  className="fill-stone-500 font-body text-[11px]"
                >
                  {ghost.label}
                  <tspan className="fill-stone-400 tabular-nums"> {ghost.yearLabel}</tspan>
                </text>
              </g>
            );
          })}

        {!vertical &&
          ghosts.map((ghost) => (
            <line
              key={ghost.id}
              x1={at(ghost.year)}
              y1={G.rail - 7}
              x2={at(ghost.year)}
              y2={G.rail}
              className="stroke-stone-400"
              strokeWidth={1}
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
            <g key={station.id}>
              <line
                x1={p}
                y1={G.rail}
                x2={p}
                y2={G.rail + (active ? 15 : 9)}
                className={cn(active ? tone.stroke : 'stroke-stone-400')}
                strokeWidth={active ? 2 : 1}
              />
              {active && (
                <text
                  x={p}
                  y={G.rail + 34}
                  textAnchor="middle"
                  className={cn('font-body text-[13px]', tone.fill)}
                >
                  {station.label}
                  <tspan className="fill-stone-500 text-[11px] tabular-nums">
                    {'  '}
                    {station.yearLabel}
                  </tspan>
                </text>
              )}
            </g>
          );
        })}
      </svg>

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

export default ChronoRail;
